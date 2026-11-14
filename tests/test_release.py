"""A release archive ships only the runtime files (spec R1), and they are the files tested.

The check works on top-level entries: a new file inside a shipped folder (lib/, roles/, ...)
ships by design, and a folder marked export-ignore drops everything inside it.
"""

import re
import subprocess
import tomllib

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


def install_block() -> str:
    """The first shell block of the README's "Install into a project" section."""
    readme = (HOME / "README.md").read_text(encoding="utf-8")
    section = readme.split("## Install into a project", 1)[-1].split("\n## ", 1)[0]
    found = re.search(r"```sh\n(.*?)```", section, re.DOTALL)
    assert found, "README: no shell block in the install section"
    return found.group(1)


def test_the_readme_installs_the_current_version():
    lines = re.findall(r"^v=(\S+)$", install_block(), re.MULTILINE)
    project = tomllib.loads((HOME / "pyproject.toml").read_text(encoding="utf-8"))

    assert len(lines) == 1, "README: the install block needs exactly one v=<version> line"
    assert lines[0] == project["project"]["version"]
