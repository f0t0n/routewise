"""A release archive ships only the runtime files (spec R1), and they are the files tested."""

import subprocess

import pytest
from conftest import COPY, HOME, SHIPPED_DOCS


def git(*args: str, stdin: str | None = None) -> str:
    result = subprocess.run(
        ["git", "-C", str(HOME), *args], input=stdin, capture_output=True, text=True, check=True
    )
    return result.stdout


def test_a_release_archive_ships_exactly_the_runtime_files():
    if not (HOME / ".git").exists():
        pytest.skip("not a git checkout (for example an extracted archive)")
    top = sorted({path.split("/")[0] for path in git("ls-files").splitlines()})

    attributes = git("check-attr", "export-ignore", "--stdin", stdin="\n".join(top) + "\n")
    shipped = {
        line.split(": ")[0] for line in attributes.splitlines() if line.endswith(": unspecified")
    }

    assert shipped == set(COPY) | set(SHIPPED_DOCS)
