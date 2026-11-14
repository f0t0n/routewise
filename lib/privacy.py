"""What a miss-log entry must not hold (spec M1): clear leaks of addresses, IDs, links and secrets.

High precision by design: every pattern matches only text that is almost surely private, so
normal descriptions of code (logger.info, @property, GPT-4, a git SHA, a long test name) pass.
It cannot catch a person's name, a bare host name or an internal ID; the agent is told to
describe the miss in its own words. Text is normalised first (NFKC, invisible characters
removed, an ideographic full stop read as a dot, %40 and &#64; read as @), so a full-width
or small at sign, a full stop, an encoded @ or a split token does not hide a leak.
"""

import re
import unicodedata

# Invisible characters that can split a token or an address: zero-width, LRM/RLM, word joiner
# and invisible operators, BOM, soft hyphen, Mongolian vowel separator, grapheme joiner.
INVISIBLE = re.compile("[\u200b-\u200f\u2060-\u2064\ufeff\u00ad\u180e\u034f]")
ENCODED_AT = re.compile("%40|&#64;")
CARD = re.compile(r"\b\d(?:[ -]?\d){12,18}\b")
LETTER = r"[^\W\d_]"  # any letter, not only ASCII: anna@корп is an address too
# A version or package tag after @ (HEAD@{1}, pkg@latest, actions/checkout@v4), when it is the
# whole name: v2-gateway or master-01 is a host.
TAG = r"(?:v\d+|latest|next|beta|alpha|canary|rc|stable|lts|main|master)(?![\w-])"
# A link without a scheme ends its host with a TLD, maybe a port, then a path, query or anchor
# (a "?" that ends a question is not one).
TLD = LETTER + r"{2,63}"
LINK_END = r"(?::\d{1,5})?(?:/|[?#]\S)"
# File types that are also TLDs: README.md/ or lib.rs/ is a path; wiki.acme.md/ is a link.
SOURCE_TYPES = (
    "md|py|rs|ts|tsx|js|jsx|mjs|cjs|json|toml|yaml|yml|txt|lock|cfg|ini|html|css|sh|rb|kt|go"
    "|java|cpp|hpp"
)
# A host with two or more dots (jira.corp.net), or one dot not before a source file type
# (example.com, not README.md).
DEEP_HOST = r"[\w-]+(?:\.[\w-]+)+\." + TLD
SHALLOW_HOST = r"[\w-]+\.(?!(?:" + SOURCE_TYPES + r")(?![\w-]))" + TLD

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
    # An e-mail: a word right before the @ (so @property and @mentions pass), maybe quoted or
    # escaped ("anna"@, anna\@, **anna**@), and a dotted domain with a letter in it (so
    # react@18.3.1 passes).
    (
        re.compile(r"\w[\w.+-]*[\\\"'*]{0,2}\s?@\s?(?=[\w.-]*" + LETTER + r")[\w-]+(?:\.[\w-]+)+"),
        "an e-mail address",
    ),
    # One without a dot (me@localhost): the domain starts with a letter and is not a tag. No
    # space around the @ here, so "used @property" passes.
    (re.compile(r"\w[\w.+-]*@(?!" + TAG + ")" + LETTER + r"[\w-]*"), "an e-mail address"),
    (
        re.compile(
            r"\w+\s*(?:\(at\)|\[at\]|\{at\}|\sat\s)\s*[\w-]+"
            r"\s*(?:\(dot\)|\[dot\]|\{dot\}|\sdot\s)\s*\w+",
            re.IGNORECASE,
        ),
        "an e-mail address",
    ),
    (re.compile(r"\b[a-z][a-z0-9+.-]*://|\bwww\.\w", re.IGNORECASE), "a URL"),
    # A link without a scheme (example.com/page, //host.corp:8080/x): a host that starts a
    # word. One with a single dot must not follow a lone slash (src/a.ts/) or end in a source
    # file type (README.md/); one with more dots may (proxy/jira.corp.net/x).
    (
        re.compile(
            r"(?<![\w@-])(?:" + DEEP_HOST + r"|(?<![^/]/)" + SHALLOW_HOST + ")" + LINK_END,
            re.IGNORECASE,
        ),
        "a URL",
    ),
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
    """The text as the patterns see it: a disguised character reads as the plain one."""
    text = INVISIBLE.sub("", unicodedata.normalize("NFKC", text)).replace("\u3002", ".")
    return ENCODED_AT.sub("@", text)


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
