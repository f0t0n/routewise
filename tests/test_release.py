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


def readme() -> str:
    return (HOME / "README.md").read_text(encoding="utf-8")


def install_block() -> str:
    """The shell block with the download in the README's "Install into a project" section."""
    heading = "\n## Install into a project\n"
    assert heading in readme(), "README: no '## Install into a project' section"
    section = readme().split(heading, 1)[1].split("\n## ", 1)[0]
    blocks = [b for b in re.findall(r"```sh\n(.*?)```", section, re.DOTALL) if "curl " in b]
    assert len(blocks) == 1, "README: the install section needs exactly one shell block with curl"
    return blocks[0]


def test_the_readme_installs_the_current_version():
    block = install_block()
    version = tomllib.loads((HOME / "pyproject.toml").read_text(encoding="utf-8"))["project"][
        "version"
    ]

    assert re.findall(r"^v=(\S+)$", block, re.MULTILINE) == [version], block
    assert "/archive/refs/tags/v$v.tar.gz" in block, block
    assert set(re.findall(r"^\s*v=(\S+)$", readme(), re.MULTILINE)) == {version}


def test_the_readme_install_never_runs_an_older_copy():
    chain = install_block().strip().splitlines()[-1]

    assert chain.startswith("mkdir routewise && curl -fsSL "), chain
    assert chain.endswith(" && routewise/install"), chain
    assert " mv " not in chain, chain


def test_the_readme_never_maps_a_release_to_an_approved_version():
    """R14 audit: the version to approve comes from the person, never from a release number."""
    updating = readme().split("\n## Updating\n", 1)[1].split("\n## ", 1)[0]

    assert "approved_rules_version" in updating
    assert "for 0.2.x" not in updating and "for 0.3.x" not in updating
    assert "ask the person" in updating
    assert "judge` row" not in updating
