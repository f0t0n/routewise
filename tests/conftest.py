"""A throwaway project with a copy of routewise/ inside, for each test."""

import shutil
import subprocess
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parent.parent
COPY = ("install", "harness.toml", "bin", "lib", "roles", "spec", "templates")
# Shipped in a release archive beside COPY (spec R1); everything else is export-ignore.
SHIPPED_DOCS = ("README.md", "ADOPT.md", "LICENSE", "CHANGELOG.md")


@pytest.fixture
def project(tmp_path: Path) -> Path:
    root = tmp_path / "app"
    target = root / "routewise"
    target.mkdir(parents=True)
    for name in COPY:
        source = HOME / name
        if source.is_dir():
            shutil.copytree(source, target / name, ignore=shutil.ignore_patterns("__pycache__"))
        else:
            shutil.copy2(source, target / name)
    return root


def run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(root / "routewise" / args[0]), *args[1:]],
        capture_output=True,
        text=True,
        check=False,
        cwd=root,
    )
