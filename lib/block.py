"""The delegation block inside an instruction file, between two marker lines.

A marker counts only as a whole line of its own, outside fenced code, so a file that mentions
the markers in prose or in a code example is never cut. Text outside the block is kept as it
is, with its own line ends (CRLF stays CRLF); only the blank lines right next to the block are
normalised to one. Anything but zero markers, or one start line followed by one end line, is
refused: a guess could delete the user's text.
"""

START = "<!-- routewise:start (generated: edit routewise.toml and re-run routewise/install) -->"
END = "<!-- routewise:end -->"
START_KEY = "<!-- routewise:start"
FENCES = ("```", "~~~")


class BlockError(Exception):
    """Markers that routewise cannot edit safely."""


def newline(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def marker_lines(text: str) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    """(start, end) character offsets of start-marker lines and end-marker lines."""
    starts: list[tuple[int, int]] = []
    ends: list[tuple[int, int]] = []
    offset = 0
    fenced = False
    for line in text.splitlines(keepends=True):
        bare = line.strip()
        if bare.startswith(FENCES):
            fenced = not fenced
        elif not fenced and bare.startswith(START_KEY) and bare.endswith("-->"):
            starts.append((offset, offset + len(line.rstrip("\r\n"))))
        elif not fenced and bare == END:
            ends.append((offset, offset + len(line.rstrip("\r\n"))))
        offset += len(line)
    return starts, ends


def span(text: str) -> tuple[int, int] | None:
    """(start of the start marker, end of the end marker), or None when there is no block."""
    starts, ends = marker_lines(text)
    if not starts and not ends:
        return None
    if len(starts) != 1 or len(ends) != 1 or ends[0][0] < starts[0][1]:
        raise BlockError(
            "needs exactly one routewise:start line followed by one routewise:end line; "
            "fix the markers by hand"
        )
    return starts[0][0], ends[0][1]


def render(block: str, nl: str) -> str:
    body = block.replace("\r\n", "\n").rstrip("\n").replace("\n", nl)
    return START + nl + body + nl + END


def insert(text: str, block: str) -> str:
    """`text` with the block replaced, or appended after one blank line."""
    nl = newline(text)
    found = span(text)
    if found is not None:
        return text[: found[0]] + render(block, nl) + text[found[1] :]
    lead = text.rstrip("\r\n") + nl + nl if text.strip() else ""
    return lead + render(block, nl) + nl


def remove(text: str) -> str:
    """`text` without the block; one blank line stays between the text before and after it."""
    found = span(text)
    if found is None:
        return text
    nl = newline(text)
    head = text[: found[0]].rstrip("\r\n")
    tail = text[found[1] :].lstrip("\r\n")
    if head and tail:
        return head + nl + nl + tail
    if head:
        return head + nl
    return tail
