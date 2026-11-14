"""routewise/bin/miss-log: the delegation miss log (spec section 8, M1).

`add` appends one JSON line for a delegated result that was wrong or had to be redone; the
command stamps the time and reads tier and effort from the role file in routewise/roles/, so
the agent never writes a time or a malformed line itself. `report` prints the misses per role,
tier and effort. Python standard library only.

Exit codes: 0 done, 2 a clear error on stderr (nothing written).
"""

import argparse
import json
import os
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import files

import privacy
import settings
from paths import PathError, holds, inside, where
from roles import RoleError, read_roles
from settings import SettingsError

HOME = where(__file__)
MAX_WHAT = 200
MAX_TASK = 60

EXAMPLE = """\
example:
  routewise/bin/miss-log add --mode dev --role reviewer --task review \\
      --what "missed an unchecked return value in the parser"
  routewise/bin/miss-log report

record (one JSON object per line in the log named by `miss_log` in routewise.toml):
  at (UTC, stamped), mode, role, tier, effort, task, what
  tier and effort come from the role file; a role with no effort records "default".

refused with exit code 2, and nothing is written: an unknown role; an empty `what` or one
over 200 characters; in `what` or `task`: an e-mail address (also "name (at) host (dot) com"),
a URL, an IP address, a UUID or chat ID, a home folder path, a phone or card number, or a
token or key. The filter catches clear leaks only, so it does not get in the way of normal
code words (logger.info, @property, GPT-4). It cannot catch a name, a bare host name or an
internal ID: describe the miss in your own words and never quote other people, messages,
IDs or secrets.
"""


class Fail(Exception):
    """A clear error for the user: printed on stderr, exit code 2."""


def log_path(root: Path) -> Path:
    """The log named in routewise.toml (or the default), checked to be inside the project."""
    chosen = settings.read(root) or settings.Settings()
    return inside(root, root / chosen.miss_log)


def role_fields(name: str) -> dict[str, str]:
    roles = {role.name.lower(): role for role in read_roles(HOME / "roles")}
    role = roles.get(name.lower())
    if role is None:
        valid = ", ".join(r.name for r in roles.values())
        raise Fail(f"unknown role {name!r}; valid roles: {valid}")
    return {"role": role.name, "tier": role.tier, "effort": role.effort}


def check_text(label: str, text: str, limit: int) -> str:
    """The trimmed text, or a Fail when it is empty, too long or holds private data."""
    text = text.strip()
    if not text:
        raise Fail(f"{label} is empty")
    if len(text) > limit:
        raise Fail(f"{label} is {len(text)} characters; the limit is {limit}")
    found = privacy.finding(text)
    if found:
        raise Fail(f"{label} holds {found}; describe the miss without it")
    return text


def build_record(args: argparse.Namespace) -> dict[str, str]:
    now = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return {
        "at": now,
        "mode": args.mode,
        **role_fields(args.role),
        "task": check_text("task", args.task, MAX_TASK),
        "what": check_text("what", args.what, MAX_WHAT),
    }


def read_records(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    records = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as err:
            raise Fail(f"{path.name} line {number} is not valid JSON: {err.msg}") from err
        if not isinstance(record, dict):
            raise Fail(f"{path.name} line {number} is not a JSON object")
        records.append(record)
    return records


def summary(records: list[dict[str, str]]) -> str:
    out = [f"misses: {len(records)}"]
    for key in ("role", "tier", "effort"):
        counts = Counter(r.get(key, "?") for r in records)
        row = ", ".join(f"{name} {count}" for name, count in counts.most_common()) or "-"
        out.append(f"by {key}: {row}")
    return "\n".join(out)


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="miss-log",
        description="Record and summarise delegated results that were wrong or redone.",
        epilog=EXAMPLE,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--project",
        type=Path,
        default=HOME.parent,
        help="project root (default: the folder that holds routewise/)",
    )
    sub = ap.add_subparsers(dest="command", required=True)
    add = sub.add_parser("add", help="append one miss")
    add.add_argument("--mode", required=True, choices=["dev", "assistant"])
    add.add_argument("--role", required=True, help="the subagent's name, e.g. reviewer")
    add.add_argument("--task", required=True, help=f"short task type, up to {MAX_TASK} characters")
    add.add_argument("--what", required=True, help=f"what went wrong, up to {MAX_WHAT} characters")
    sub.add_parser("report", help="print misses per role, tier and effort")
    return ap


def run(args: argparse.Namespace) -> str:
    root = Path(os.path.abspath(args.project))
    holds(root, HOME)
    path = log_path(root)
    if args.command == "add":
        record = build_record(args)
        files.append(root, path, json.dumps(record, ensure_ascii=False) + "\n")
        return json.dumps(record, ensure_ascii=False)
    return summary(read_records(path))


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        print(run(args))
    except (Fail, RoleError, SettingsError, PathError) as err:
        print(f"routewise: {err}", file=sys.stderr)
        return 2
    except (OSError, ValueError) as err:
        print(f"routewise: cannot read or write a file: {err}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
