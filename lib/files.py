"""Writing and deleting project files safely.

- `preflight` checks that every target can be written before anything is, so a run that
  would fail on a read-only file writes nothing.
- `replace` writes a temporary file next to the target and renames it over the target, so a
  full disk never leaves a half-written or empty instruction file.
- Every write and delete checks the path is still inside the project right before acting,
  and the final rename or unlink never follows a symlink.
"""

import os
import tempfile
from pathlib import Path

from paths import PathError, inside, label


def nearest_folder(path: Path) -> Path:
    """The closest existing folder at or above `path`'s parent."""
    folder = path.parent
    while not folder.exists():
        folder = folder.parent
    return folder


def writable(path: Path) -> bool:
    if path.is_symlink() or path.exists():
        target = Path(os.path.realpath(path))
        return target.is_file() and os.access(target, os.W_OK) and os.access(target.parent, os.W_OK)
    folder = nearest_folder(path)
    return folder.is_dir() and os.access(folder, os.W_OK | os.X_OK)


def preflight(root: Path, writes: list[Path], removes: list[Path]) -> None:
    for path in [*writes, *removes]:
        inside(root, path)
        if not writable(path):
            raise PathError(f"{label(path, root)} cannot be written; check its permissions")


def replace(root: Path, path: Path, text: str) -> None:
    inside(root, path)
    path.parent.mkdir(parents=True, exist_ok=True)
    inside(root, path.parent)
    handle, temp = tempfile.mkstemp(dir=path.parent, prefix=".routewise-", suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="") as out:
            out.write(text)
        if path.exists():
            os.chmod(temp, path.stat().st_mode & 0o777)
        os.replace(temp, path)
    except BaseException:
        os.unlink(temp)
        raise


def remove(root: Path, path: Path) -> None:
    inside(root, path.parent)
    path.unlink()


def append(root: Path, path: Path, line: str) -> None:
    """Append one line; the log itself must not be a symlink."""
    inside(root, path)
    path.parent.mkdir(parents=True, exist_ok=True)
    inside(root, path.parent)
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    handle = os.open(path, flags, 0o644)
    with os.fdopen(handle, "a", encoding="utf-8") as out:
        out.write(line)
