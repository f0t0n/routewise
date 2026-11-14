"""routewise/install: set up model routing and delegation in the project that holds this folder.

Writes the role agents for each harness, the delegation block in the instruction files, and,
on the first run only, routewise.toml, ROUTING-BINDING.md and an empty miss log. The whole run
is planned and checked first, including write access to every target; then each file is
written through a temporary file and a rename. Every path stays inside the project, and only
files routewise generated are rewritten or deleted.

Exit codes: 0 done (or no drift with --check), 1 drift found by --check, 2 a clear error.
"""

import argparse
import os
import sys
import tomllib
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import files

import block
import settings
from paths import PathError, holds, inside, label, relative, where
from roles import Harness, Role, RoleError, is_generated, read_roles, render
from settings import Settings, SettingsError

HOME = where(__file__)
BINDING = "ROUTING-BINDING.md"

EXAMPLE = """\
examples:
  routewise/install              set up, or update after editing routewise.toml
  routewise/install --check      report drift and write nothing (exit 1 on drift)
  routewise/install --uninstall  remove generated agents and the delegation block;
                                 keeps routewise.toml, ROUTING-BINDING.md and the miss log

first run writes routewise.toml (settings) and ROUTING-BINDING.md (approvals); fill in the
binding, then commit everything routewise wrote.
"""


class Fail(Exception):
    """A clear error for the user: printed on stderr, exit code 2."""


@dataclass
class Plan:
    """What the run would write or remove, keyed by path."""

    root: Path
    writes: dict[Path, str] = field(default_factory=dict)
    removes: list[Path] = field(default_factory=list)

    def write(self, path: Path, text: str) -> None:
        self.writes[inside(self.root, path)] = text

    def remove(self, path: Path) -> None:
        self.removes.append(inside(self.root, path))


# --- settings and harnesses -----------------------------------------------------------------


def default_settings_text(root: Path) -> str:
    harnesses = ["cc"]
    if (root / ".agents").is_dir() or (root / "GEMINI.md").exists():
        harnesses.append("agy")
    instructions = ["CLAUDE.md"]
    if (root / "AGENTS.md").exists():
        instructions.append("AGENTS.md")
    text = (HOME / "templates" / settings.NAME).read_text(encoding="utf-8")
    text = text.replace("{{harnesses}}", toml_list(harnesses))
    return text.replace("{{instructions}}", toml_list(instructions))


def toml_list(items: list[str]) -> str:
    return "[" + ", ".join(f'"{item}"' for item in items) + "]"


def all_harnesses(overrides: dict[str, str]) -> dict[str, Harness]:
    data = tomllib.loads((HOME / "harness.toml").read_text(encoding="utf-8"))
    harnesses = {}
    for key, table in data.items():
        tiers = dict(table.get("tiers", {}))
        if tiers:
            tiers.update(overrides)
        relative(table["dir"], f"harness.toml {key} dir")
        efforts = tuple(table.get("efforts", ()))
        harnesses[key] = Harness(key, table["dir"], dict(table["tools"]), tiers, efforts)
    return harnesses


# --- planning -------------------------------------------------------------------------------


def generated_files(folder: Path) -> list[Path]:
    if not folder.is_dir():
        return []
    return [p for p in sorted(folder.glob("*.md")) if p.is_file() and is_generated(p)]


def plan_agents(plan: Plan, roles: list[Role], harness: Harness) -> None:
    folder = plan.root / harness.dir
    wanted = set()
    for role in roles:
        target = folder / role.source.name
        if (target.exists() or target.is_symlink()) and not is_generated(target):
            name = label(target, plan.root)
            raise Fail(f"{name} exists and was not written by routewise; move it")
        plan.write(target, render(role, harness, label(role.source, plan.root)))
        wanted.add(target)
    for stale in generated_files(folder):
        if stale not in wanted:
            plan.remove(stale)


def fragment_text(root: Path, chosen: Settings) -> str:
    text = (HOME / "templates" / f"fragment-{chosen.fragment}.md").read_text(encoding="utf-8")
    text = text.replace("{{cap}}", str(chosen.cap))
    return text.replace("{{miss_log}}", label(HOME / "bin" / "miss-log", root))


@dataclass(frozen=True)
class Instruction:
    """One instruction file, after following symlinks (CLAUDE.md -> AGENTS.md)."""

    target: Path  # the real file, inside the project
    linked: bool  # some listed name is a symlink to it: never delete it


def instruction_files(root: Path, chosen: Settings) -> list[Instruction]:
    found: dict[Path, bool] = {}
    for name in chosen.instructions:
        path = inside(root, root / name)
        target = Path(os.path.realpath(path))
        found[target] = found.get(target, False) or path.is_symlink()
    return [Instruction(target, linked) for target, linked in found.items()]


def read_exact(path: Path) -> str:
    """The file's text with its own line ends (CRLF stays CRLF)."""
    if not path.exists():
        return ""
    with path.open(encoding="utf-8", newline="") as handle:
        return handle.read()


def plan_instructions(plan: Plan, chosen: Settings, install: bool) -> None:
    text = fragment_text(plan.root, chosen)
    real_root = Path(os.path.realpath(plan.root))
    for item in instruction_files(plan.root, chosen):
        path = plan.root / item.target.relative_to(real_root)
        old = read_exact(path)
        try:
            new = block.insert(old, text) if install else block.remove(old)
        except block.BlockError as err:
            raise Fail(f"{label(path, plan.root)}: {err}") from err
        if new == old:
            continue
        if new == "" and not install and not item.linked:
            plan.remove(path)
        else:
            plan.write(path, new)


def plan_first_run(plan: Plan, chosen: Settings, harnesses: list[Harness]) -> None:
    binding = plan.root / BINDING
    if not binding.exists():
        text = (HOME / "templates" / "binding.md").read_text(encoding="utf-8")
        dirs = ", ".join(f"`{h.dir}/` ({h.key})" for h in harnesses)
        text = text.replace("{{spec}}", label(HOME / "spec" / "SPEC-model-routing.md", plan.root))
        text = text.replace("{{date}}", date.today().isoformat()).replace("{{agent_dirs}}", dirs)
        plan.write(binding, text)
    log = plan.root / chosen.miss_log
    if not log.exists():
        plan.write(log, "")


def plan_install(plan: Plan, chosen: Settings) -> None:
    harnesses = all_harnesses(chosen.tiers)
    roles = read_roles(HOME / "roles")
    active = [harnesses[key] for key in chosen.harnesses]
    for harness in active:
        plan_agents(plan, roles, harness)
    for key, harness in harnesses.items():
        if key not in chosen.harnesses:
            for stale in generated_files(plan.root / harness.dir):
                plan.remove(stale)
    plan_first_run(plan, chosen, active)
    plan_instructions(plan, chosen, install=True)


def plan_uninstall(plan: Plan, chosen: Settings) -> None:
    for harness in all_harnesses({}).values():
        for path in generated_files(plan.root / harness.dir):
            plan.remove(path)
    plan_instructions(plan, chosen, install=False)


def build_plan(root: Path, uninstall: bool) -> Plan:
    plan = Plan(root)
    chosen = settings.read(root)
    if uninstall:
        plan_uninstall(plan, chosen or Settings(instructions=["CLAUDE.md", "AGENTS.md"]))
        return plan
    if chosen is None:
        text = default_settings_text(root)
        plan.write(root / settings.NAME, text)
        chosen = settings.parse(text)
    plan_install(plan, chosen)
    return plan


# --- applying -------------------------------------------------------------------------------


def changed(plan: Plan) -> tuple[list[Path], list[Path]]:
    writes = [p for p, text in plan.writes.items() if read_exact(p) != text or not p.exists()]
    return writes, [p for p in plan.removes if p.exists()]


def apply(plan: Plan, writes: list[Path], removes: list[Path]) -> None:
    files.preflight(plan.root, writes, removes)
    for path in writes:
        files.replace(plan.root, path, plan.writes[path])
    for path in removes:
        files.remove(plan.root, path)


def report(root: Path, writes: list[Path], removes: list[Path], verb: str) -> str:
    lines = [f"{verb} {label(p, root)}" for p in writes]
    lines += [f"remove {label(p, root)}" for p in removes]
    if any(p.name == settings.NAME for p in writes) and verb == "write":
        lines.append(f"first run: review {settings.NAME}, then fill in {BINDING}")
    return "\n".join(lines) or "routewise: nothing to change"


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="routewise/install",
        description="Set up model routing and delegation (agents, instructions, miss log).",
        epilog=EXAMPLE,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--project",
        type=Path,
        default=HOME.parent,
        help="project root (default: the folder that holds routewise/)",
    )
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="report drift, write nothing")
    mode.add_argument("--uninstall", action="store_true", help="remove what install generated")
    return ap


def run(args: argparse.Namespace) -> tuple[int, str]:
    root = Path(os.path.abspath(args.project))
    if not root.is_dir():
        raise Fail(f"{root} is not a folder")
    holds(root, HOME)
    plan = build_plan(root, args.uninstall)
    writes, removes = changed(plan)
    if args.check:
        return (1 if writes or removes else 0), report(root, writes, removes, "drift")
    apply(plan, writes, removes)
    return 0, report(root, writes, removes, "write")


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        code, out = run(args)
    except (Fail, RoleError, SettingsError, PathError) as err:
        print(f"routewise: {err}", file=sys.stderr)
        return 2
    except (OSError, ValueError, tomllib.TOMLDecodeError, KeyError) as err:
        print(f"routewise: cannot read or write a file: {err}", file=sys.stderr)
        return 2
    print(out)
    return code


if __name__ == "__main__":
    sys.exit(main())
