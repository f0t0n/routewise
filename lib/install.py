"""routewise/install: set up model routing and delegation in the project that holds this folder.

Writes the role agents for each harness, the delegation block in the instruction files
(AGENTS.md by default), an `@AGENTS.md` import block in CLAUDE.md when Claude Code needs one
(`claude_md`), and, on the first run only, routewise.toml, ROUTING-BINDING.md and an empty
miss log. It never creates a symlink and never writes outside the project. The whole run
is planned and checked first, including write access to every target; then each file is
written through a temporary file and a rename. Every path stays inside the project, and only
files routewise generated are rewritten or deleted.

Exit codes: 0 done (or no drift with --check), 1 drift found by --check, 2 a clear error.
"""

import argparse
import os
import sys
import tomllib
from dataclasses import dataclass, field, replace
from pathlib import Path

import binding
import files

import block
import settings
from paths import PathError, holds, inside, label, not_a_repo, plain_name, relative, where
from roles import Harness, Role, RoleError, is_generated, read_roles, render
from settings import Settings, SettingsError

HOME = where(__file__)
BINDING = "ROUTING-BINDING.md"
AGENTS_MD = "AGENTS.md"
# Each of these stops Claude Code from reading AGENTS.md (in the project or any folder above).
CLAUDE_FILES = ("CLAUDE.md", ".claude/CLAUDE.md")
CLAUDE_LOCAL = "CLAUDE.local.md"

EXAMPLE = """\
examples:
  routewise/install              set up, or update after editing routewise.toml
  routewise/install --check      report drift and write nothing (exit 1 on drift)
  routewise/install --uninstall  remove generated agents, the binding and the delegation
                                 block; keeps routewise.toml and the miss log

first run writes routewise.toml (settings, approvals in [binding]); ROUTING-BINDING.md is
rendered from it on every run. Fill in [binding], re-run, then commit what routewise wrote.
"""


class Fail(Exception):
    """A clear error for the user: printed on stderr, exit code 2."""


@dataclass
class Plan:
    """What the run would write or remove, keyed by path."""

    root: Path
    writes: dict[Path, str] = field(default_factory=dict)
    removes: list[Path] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def write(self, path: Path, text: str) -> None:
        self.writes[inside(self.root, path)] = text

    def remove(self, path: Path) -> None:
        self.removes.append(inside(self.root, path))


# --- settings and harnesses -----------------------------------------------------------------


def default_settings_text(root: Path) -> str:
    harnesses = ["cc"]
    if (root / ".agents").is_dir() or (root / "GEMINI.md").exists():
        harnesses.append("agy")
    text = (HOME / "templates" / settings.NAME).read_text(encoding="utf-8")
    text = text.replace("{{install}}", rerun(root))
    return text.replace("{{harnesses}}", toml_list(harnesses))


def rerun(root: Path) -> str:
    """The re-install command as typed from the project root (spec R3)."""
    if root == HOME:
        return "./install --project ."
    return label(HOME / "install", root)


def miss_log_command(root: Path) -> str:
    """The miss-log command as typed from the project root (spec R3, R10).

    In routewise's own repo `bin/miss-log` alone would use the folder above the repo.
    """
    if root == HOME:
        return "bin/miss-log --project ."
    return label(HOME / "bin" / "miss-log", root)


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


def agent_files(
    roles: list[Role], stand_ins: dict[str, tuple[str, ...]]
) -> list[tuple[str, Role, str | None]]:
    """(file name, role, stand-in name or None) for each agent to write: roles, then stand-ins."""
    files: list[tuple[str, Role, str | None]] = [(role.source.name, role, None) for role in roles]
    for role in roles:
        files += [(f"{name}.md", role, name) for name in stand_ins.get(role.source.stem, ())]
    return files


def plan_agents(
    plan: Plan, roles: list[Role], harness: Harness, stand_ins: dict[str, tuple[str, ...]]
) -> None:
    folder = plan.root / harness.dir
    wanted = set()
    for file_name, role, stand_in in agent_files(roles, stand_ins):
        target = folder / file_name
        if (target.exists() or target.is_symlink()) and not is_generated(target):
            name = label(target, plan.root)
            raise Fail(f"{name} exists and was not written by routewise; move it")
        source = label(role.source, plan.root)
        plan.write(target, render(role, harness, source, rerun(plan.root), stand_in))
        wanted.add(target)
    for stale in generated_files(folder):
        if stale not in wanted:
            plan.remove(stale)


def stand_ins_line(stand_ins: dict[str, tuple[str, ...]]) -> str:
    """The block's line about stand-ins (spec R9), or nothing when none are set."""
    pairs = [(name, role) for role, names in stand_ins.items() for name in names]
    if not pairs:
        return ""
    named = ", ".join(f"`{name}` (for `{role}`)" for name, role in pairs)
    example = f"`<plugin>:{pairs[0][0]}`"
    return (
        f"- This project's stand-in agents: {named}. For these names, also inside a plugin "
        f"command such as `/ship`, start the project agent, never a plugin agent of the same "
        f"name (listed as {example}).\n"
    )


def fragment_text(root: Path, chosen: Settings) -> str:
    text = (HOME / "templates" / f"fragment-{chosen.fragment}.md").read_text(encoding="utf-8")
    text = text.replace("{{cap}}", str(chosen.cap))
    text = text.replace("{{stand_ins}}", stand_ins_line(chosen.stand_ins))
    return text.replace("{{miss_log}}", miss_log_command(root))


@dataclass(frozen=True)
class Instruction:
    """One instruction file, after following symlinks (CLAUDE.md -> AGENTS.md)."""

    target: Path  # the real file, inside the project
    linked: bool  # some listed name is a symlink to it: never delete it


def present(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def resolve(root: Path, names: list[str]) -> list[Instruction]:
    found: dict[Path, bool] = {}
    for name in names:
        path = inside(root, root / name)
        target = Path(os.path.realpath(path))
        found[target] = found.get(target, False) or path.is_symlink()
    return [Instruction(target, linked) for target, linked in found.items()]


def in_project(root: Path, real: Path) -> Path:
    """A real path inside the project, spelled from the project root as the user reached it."""
    return root / real.relative_to(Path(os.path.realpath(root)))


def read_exact(path: Path) -> str:
    """The file's text with its own line ends (CRLF stays CRLF)."""
    if not path.exists():
        return ""
    with path.open(encoding="utf-8", newline="") as handle:
        return handle.read()


def plan_block(plan: Plan, path: Path, body: str | None, linked: bool) -> None:
    """Put `body` in the file's routewise block, or remove the block when `body` is None.

    A file left empty by a removal is deleted (routewise created it), unless a symlink
    leads to it.
    """
    old = read_exact(path)
    try:
        start = block.start_line(rerun(plan.root))
        new = block.insert(old, body, start) if body is not None else block.remove(old)
    except block.BlockError as err:
        raise Fail(f"{label(path, plan.root)}: {err}") from err
    if new == old:
        return
    if new == "" and body is None and not linked:
        plan.remove(path)
    else:
        plan.write(path, new)


def plan_instructions(plan: Plan, chosen: Settings) -> set[Path]:
    """The delegation block in each instruction file; returns their real paths."""
    text = fragment_text(plan.root, chosen)
    items = resolve(plan.root, chosen.instructions)
    for item in items:
        plan_block(plan, in_project(plan.root, item.target), text, item.linked)
    return {item.target for item in items}


# --- CLAUDE.md and AGENTS.md ------------------------------------------------------------------


def import_line(root: Path, path: Path) -> str:
    """`@AGENTS.md` as written in `path`: Claude Code resolves imports from the file's folder."""
    return "@" + Path(os.path.relpath(root / AGENTS_MD, path.parent)).as_posix()


def imports(text: str, line: str) -> bool:
    """`text` has the import as a line of its own, outside fenced code."""
    wanted = {line, "@./" + line[1:]}
    fenced = False
    for raw in text.splitlines():
        bare = raw.strip()
        if bare.startswith(block.FENCES):
            fenced = not fenced
        elif not fenced and bare in wanted:
            return True
    return False


def plan_import(plan: Plan, chosen: Settings, covered: set[Path]) -> None:
    """A routewise block holding `@AGENTS.md` in the first CLAUDE.md, per `claude_md`.

    Skipped when that file already imports AGENTS.md outside the block, or is itself an
    instruction file. Stale import blocks in the other CLAUDE.md files are removed.
    """
    if chosen.claude_md == "none" or AGENTS_MD not in chosen.instructions:
        return
    paths = [plan.root / name for name in CLAUDE_FILES]
    existing = [path for path in paths if present(path)]
    target = existing[0] if existing else None
    if target is None and chosen.claude_md == "import":
        target = paths[0]
    seen = set(covered)
    for path in paths:
        if path != target and not present(path):
            continue
        real = Path(os.path.realpath(inside(plan.root, path)))
        if real in seen:
            continue
        seen.add(real)
        file = in_project(plan.root, real)
        line = import_line(plan.root, path)
        old = read_exact(file)
        try:
            by_hand = imports(block.remove(old), line)
        except block.BlockError as err:
            raise Fail(f"{label(file, plan.root)}: {err}") from err
        body = line if path == target and not by_hand else None
        plan_block(plan, file, body, path.is_symlink())


def planned_text(plan: Plan, path: Path) -> str | None:
    """The file's text after the run, or None when it is missing or leads out of the project."""
    try:
        file = in_project(plan.root, Path(os.path.realpath(inside(plan.root, path))))
    except PathError:
        return None
    if file in plan.writes:
        return plan.writes[file]
    if file in plan.removes or not present(path):
        return None
    return read_exact(file)


def claude_notes(plan: Plan, chosen: Settings, covered: set[Path]) -> list[str]:
    """Notes on CLAUDE files that would stop Claude Code from reading AGENTS.md."""
    if AGENTS_MD not in chosen.instructions:
        return []
    root = plan.root
    for name in CLAUDE_FILES:
        path = root / name
        text = planned_text(plan, path)
        linked = present(path) and Path(os.path.realpath(path)) in covered
        if linked or (text is not None and imports(text, import_line(root, path))):
            return []  # Claude Code reaches AGENTS.md through this file
    notes = []
    found = [name for name in (*CLAUDE_FILES, CLAUDE_LOCAL) if present(root / name)]
    if found == [CLAUDE_LOCAL]:
        notes.append(
            f"note: {CLAUDE_LOCAL} stops Claude Code from reading {AGENTS_MD}; add an "
            f"`@{AGENTS_MD}` line to it, or set Project instructions to "
            "claude-md-and-agents-md in /config"
        )
    elif found:
        notes.append(
            f"note: {found[0]} stops Claude Code from reading {AGENTS_MD}; set "
            f'claude_md = "auto" in {settings.NAME}, or add an `@{AGENTS_MD}` line to it'
        )
    personal = Path.home() / ".claude" / "CLAUDE.md"  # does not stop AGENTS.md
    for folder in root.parents:
        for name in (*CLAUDE_FILES, CLAUDE_LOCAL):
            path = folder / name
            if path != personal and present(path):
                notes.append(
                    f"warning: {path} is above the project, so Claude Code reads it instead "
                    f'of {AGENTS_MD}; set claude_md = "import" in {settings.NAME}'
                )
    return notes


def binding_values(root: Path, harnesses: list[Harness]) -> dict[str, str]:
    """The paths and commands the binding names, spelled from the project root (R3)."""
    return {
        "{{template}}": label(HOME / "templates" / "binding.md", root),
        "{{spec}}": label(HOME / "spec" / "SPEC-model-routing.md", root),
        "{{install}}": rerun(root),
        "{{roles}}": label(HOME / "roles", root) + "/",
        "{{harness}}": label(HOME / "harness.toml", root),
        "{{miss_log}}": miss_log_command(root),
        "{{agent_dirs}}": ", ".join(f"`{h.dir}/` ({h.key})" for h in harnesses),
    }


def own_binding(root: Path) -> bool | None:
    """None when there is no binding, else whether routewise generated it (spec S3, R14)."""
    path = root / BINDING
    if not present(path):
        return None
    return binding.is_generated(read_exact(inside(root, path)))


def plan_binding(plan: Plan, chosen: Settings, harnesses: list[Harness], roles: list[Role]) -> None:
    """Render ROUTING-BINDING.md from the roles and [binding]; never over a file of the user's."""
    if own_binding(plan.root) is False:
        raise Fail(
            f"{BINDING} was not written by routewise (it was hand-filled before 0.4.0); "
            f"move its approval, assistant pins and review date into [binding] in "
            f"{settings.NAME}, delete {BINDING}, and re-run {rerun(plan.root)}"
        )
    spec = (HOME / "spec" / "SPEC-model-routing.md").read_text(encoding="utf-8")
    try:
        version = binding.rules_version(spec)
        text = binding.render(
            (HOME / "templates" / "binding.md").read_text(encoding="utf-8"),
            binding_values(plan.root, harnesses),
            roles,
            chosen.binding,
            version,
        )
    except binding.BindingError as err:
        raise Fail(str(err)) from err
    plan.write(plan.root / BINDING, text)
    if binding.status(chosen.binding, version) == "pending":
        plan.notes.append(
            f"approval pending: rules spec version {version} "
            f"(approved: {chosen.binding.approved_rules_version}); when you approve, set "
            f"[binding] approved_rules_version = {version} in {settings.NAME} and re-run"
        )


def plan_first_run(plan: Plan, chosen: Settings) -> None:
    log = plan.root / chosen.miss_log
    if not log.exists():
        plan.write(log, "")


def chosen_roles(chosen: Settings) -> list[Role]:
    """The shipped roles, with each role's skills replaced by [skills] where it sets them."""
    roles = read_roles(HOME / "roles")
    known = {role.source.stem for role in roles}
    roles_list = ", ".join(sorted(known))
    for table, keys in (("skills", chosen.skills), ("stand_ins", chosen.stand_ins)):
        for key in keys:
            if key not in known:
                raise Fail(
                    f"{settings.NAME}: [{table}] {key} is not a role; use one of {roles_list}"
                )
    taken = known | {role.name.lower() for role in roles}
    for names in chosen.stand_ins.values():
        for name in names:
            if name in taken:
                raise Fail(f"{settings.NAME}: [stand_ins] stand-in name {name!r} is a role")
    return [
        replace(role, skills=chosen.skills.get(role.source.stem, role.skills)) for role in roles
    ]


def plan_install(plan: Plan, chosen: Settings) -> None:
    harnesses = all_harnesses(chosen.tiers)
    roles = chosen_roles(chosen)
    active = [harnesses[key] for key in chosen.harnesses]
    for harness in active:
        plan_agents(plan, roles, harness, chosen.stand_ins)
    for key, harness in harnesses.items():
        if key not in chosen.harnesses:
            for stale in generated_files(plan.root / harness.dir):
                plan.remove(stale)
    plan_first_run(plan, chosen)
    plan_binding(plan, chosen, active, roles)
    covered = plan_instructions(plan, chosen)
    plan_import(plan, chosen, covered)
    plan.notes = claude_notes(plan, chosen, covered) + plan.notes


def leads_inside(root: Path, name: str) -> bool:
    try:
        inside(root, root / name)
    except PathError:
        return False
    return True


def plan_uninstall(plan: Plan, chosen: Settings) -> None:
    """Remove generated agents and every routewise block, whatever `claude_md` says now.

    A CLAUDE.md that leads out of the project cannot hold a block (install refuses it).
    """
    for harness in all_harnesses({}).values():
        for path in generated_files(plan.root / harness.dir):
            plan.remove(path)
    claude = [n for n in CLAUDE_FILES if present(plan.root / n) and leads_inside(plan.root, n)]
    for item in resolve(plan.root, [*chosen.instructions, *claude]):
        plan_block(plan, in_project(plan.root, item.target), None, item.linked)
    owned = own_binding(plan.root)
    if owned:
        plan.remove(plan.root / BINDING)
    elif owned is False:
        plan.notes.append(f"kept {BINDING}: routewise did not write it")


def build_plan(root: Path, uninstall: bool) -> Plan:
    plan = Plan(root)
    chosen = settings.read(root)
    if uninstall:
        plan_uninstall(plan, chosen or Settings())
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


def report(plan: Plan, writes: list[Path], removes: list[Path], verb: str) -> str:
    lines = [f"{verb} {label(p, plan.root)}" for p in writes]
    lines += [f"remove {label(p, plan.root)}" for p in removes]
    if any(p.name == settings.NAME for p in writes) and verb == "write":
        lines.append(
            f"first run: review {settings.NAME}, then fill in [binding] in {settings.NAME}"
        )
    return "\n".join((lines or ["routewise: nothing to change"]) + plan.notes)


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
    not_a_repo(root, HOME)
    plain_name(HOME)
    plan = build_plan(root, args.uninstall)
    writes, removes = changed(plan)
    if args.check:
        return (1 if writes or removes else 0), report(plan, writes, removes, "drift")
    apply(plan, writes, removes)
    return 0, report(plan, writes, removes, "write")


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
