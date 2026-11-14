"""What a miss-log entry must not hold (spec M1): clear leaks of addresses, IDs, links and secrets.

High precision by design: every pattern matches only text that is almost surely private, so
normal descriptions of code (logger.info, @property, GPT-4, a git SHA, a long test name) pass.
It cannot catch a person's name, a bare host name or an internal ID; the agent is told to
describe the miss in its own words. Text is normalised first (NFKC, zero-width characters
removed), so a full-width or small at sign or a split token does not hide a leak.
"""

import re
import unicodedata

ZERO_WIDTH = re.compile("[​-‍⁠﻿­]")
CARD = re.compile(r"\b\d(?:[ -]?\d){12,18}\b")

PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            r"\b(?:gh[pousr]_|github_pat_|sk-|sk_live_|sk_test_|rk_live_|pk_live_|xox[abposr]-"
            r"|glpat-|npm_|AIza)[A-Za-z0-9_-]{8,}"
        ),
        "a token or key",
    ),
    (re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"), "a token or key"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\."), "a token or key"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "a token or key"),
    # An e-mail: a word right before the @ (so @property and @mentions pass), a dotted domain.
    (re.compile(r"\w[\w.+-]*\s?@\s?[\w-]+(?:\.[\w-]+)+"), "an e-mail address"),
    (
        re.compile(
            r"\w+\s*(?:\(at\)|\[at\]|\{at\}|\sat\s)\s*[\w-]+"
            r"\s*(?:\(dot\)|\[dot\]|\{dot\}|\sdot\s)\s*\w+",
            re.IGNORECASE,
        ),
        "an e-mail address",
    ),
    (re.compile(r"\b[a-z][a-z0-9+.-]*://|\bwww\.\w", re.IGNORECASE), "a URL"),
    (
        re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b"),
        "an IP address",
    ),
    # IPv6: the full eight groups, or a shortened form with "::" and a digit (not 10:30:00,
    # not Rust paths such as Add::add).
    (re.compile(r"\b(?:[0-9a-f]{1,4}:){7}[0-9a-f]{1,4}\b", re.IGNORECASE), "an IP address"),
    (
        re.compile(
            r"(?<![\w:])(?=[0-9a-f:]*::)(?=[0-9a-f:]*\d)[0-9a-f]{0,4}(?::[0-9a-f]{0,4}){2,7}"
            r"(?![\w:])",
            re.IGNORECASE,
        ),
        "an IP address",
    ),
    (re.compile(r"\b[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\b", re.IGNORECASE), "an ID"),
    (re.compile(r"\b[UWCDGTB](?=[A-Z0-9]*\d)(?=[A-Z0-9]*[A-Z])[A-Z0-9]{8,}\b"), "a chat ID"),
    (
        re.compile(r"(?:/home/|/Users/|[A-Za-z]:\\Users\\|~)[A-Za-z_][\w.-]*|/root\b"),
        "a home folder path",
    ),
    (re.compile(r"\+\d[\d\s().-]{7,}\d"), "a phone number"),
)


def normal(text: str) -> str:
    return ZERO_WIDTH.sub("", unicodedata.normalize("NFKC", text))


def luhn(digits: str) -> bool:
    total = 0
    for index, char in enumerate(reversed(digits)):
        value = int(char) * (2 if index % 2 else 1)
        total += value - 9 if value > 9 else value
    return total % 10 == 0


def has_card(text: str) -> bool:
    return any(luhn(re.sub(r"\D", "", m.group())) for m in CARD.finditer(text))


def finding(text: str) -> str | None:
    """What kind of private data `text` holds, or None."""
    text = normal(text)
    for pattern, what in PATTERNS:
        if pattern.search(text):
            return what
    return "a card number" if has_card(text) else None
