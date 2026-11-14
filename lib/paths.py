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
    """Refuse a project root that is neither this routewise folder nor the folder holding it.

    Generated files name routewise paths relative to the project; from outside, they would
    hold absolute paths, and a folder further up (`--project ~`) would write global config.
    The routewise folder itself is a project too: routewise runs on its own repo (spec S9).
    """
    if root not in (home, home.parent):
        raise PathError(
            f"{root} must hold {home} directly, or be it; copy routewise/ into the project first"
        )
    if root == home and home.is_symlink():
        raise PathError(
            f"{home} is a symlink, so its files belong to every project that links to it; "
            "install into the project that holds it, or run in the real routewise folder"
        )
    if is_home_or_above(root):
        raise PathError(
            f"{root} is your home folder or above it, where agents and CLAUDE.md are global; "
            "copy routewise/ into a project folder instead"
        )


def is_home_or_above(root: Path) -> bool:
    """`root` is the user's home folder or a folder above it (compared as typed and resolved)."""
    try:
        user = Path(os.path.abspath(Path.home()))
    except RuntimeError:  # no home folder can be determined: nothing to protect
        return False
    for mine, theirs in (
        (root, user),
        (Path(os.path.realpath(root)), Path(os.path.realpath(user))),
    ):
        if mine == theirs or mine in theirs.parents:
            return True
    return False


def plain_name(home: Path) -> None:
    """Refuse a routewise folder name that would break the lines routewise writes.

    The name is spelled into agent frontmatter, the block markers and routewise.toml: a line
    break or control character would add lines there, and `-->` would end the marker early.
    """
    name = home.name
    if "-->" in name or any(ord(char) < 32 or ord(char) == 127 for char in name):
        raise PathError(
            f"the folder name {name!r} cannot be written into the markers routewise writes; "
            "rename the folder (routewise/ is the usual name)"
        )


def label(path: Path, root: Path) -> str:
    """A path as the user should type it: relative to the project root when inside it."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()
