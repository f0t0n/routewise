"""Paths the installer and the miss log may touch: always inside the project root.

Every path is checked when the run is planned and again right before each write or delete.
A process that swaps a folder for a symlink in the moment between that check and the write
can still win the race; routewise is not meant to run while another program rewrites the
project.
"""

import os
from pathlib import Path, PurePosixPath


class PathError(Exception):
    """A path that would leave the project root, or a project that does not hold routewise."""


def where(file: str) -> Path:
    """The routewise folder, as the user reached it (a symlinked routewise/ is not followed)."""
    return Path(os.path.abspath(file)).parent.parent


def relative(name: str, what: str) -> PurePosixPath:
    """A setting that names a file: relative, with no `..` part, and not the project itself."""
    path = PurePosixPath(name)
    bad = not name or "\x00" in name or path.is_absolute() or ".." in path.parts
    if bad or name.endswith("/") or path.name in ("", "."):
        raise PathError(f"{what} {name!r} must be a path inside the project, such as logs/x")
    return path


def inside(root: Path, path: Path) -> Path:
    """`path` when it, and every symlink on the way to it, stays inside `root`.

    A dangling symlink is followed too, so a write cannot create a file outside the project.
    """
    real_root = Path(os.path.realpath(root))
    real = Path(os.path.realpath(path))
    if real != real_root and real_root not in real.parents:
        raise PathError(f"{label(path, root)} leads outside the project (to {real})")
    return path


def holds(root: Path, home: Path) -> None:
    """Refuse a project root that does not hold this routewise folder.

    Generated files name routewise paths relative to the project; from outside, they would
    hold absolute paths (often a home folder), and `--project ~` would write global config.
    """
    if root not in home.parents:
        raise PathError(f"{root} does not hold {home}; copy routewise/ into the project first")


def label(path: Path, root: Path) -> str:
    """A path as the user should type it: relative to the project root when inside it."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()
