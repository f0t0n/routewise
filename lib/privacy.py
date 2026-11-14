"""What a miss-log entry must not hold (spec M1): clear leaks of addresses, IDs, links and secrets.

High precision by design: every pattern matches only text that is almost surely private, so
normal descriptions of code (logger.info, @property, GPT-4, a git SHA, a long test name) pass.
It cannot catch a person's name, a bare host name or an internal ID; the agent is told to
describe the miss in its own words. The patterns run on four normalised views of the text
(spec R5), and the text is refused if any matches. A step that only adds evidence (NFKC, an
ideographic full stop read as a dot) is in every view; a step that can also hide text gets a
view with it and one without: invisible characters as spaces (they end the word before a leak)
or removed (they cannot split one), and an encoded @ decoded (it cannot split an address) or
not (it cannot hide the link after it).
"""

import re
import unicodedata

# Invisible besides the format characters (category Cf): Unicode's Default_Ignorable_Code_Point
# (DerivedCoreProperties 18.0; variation selectors, Hangul fillers, ...) and the braille blank.
DEFAULT_IGNORABLE = (
    (0x00AD, 0x00AD), (0x034F, 0x034F), (0x061C, 0x061C), (0x115F, 0x1160), (0x17B4, 0x17B5),
    (0x180B, 0x180F), (0x200B, 0x200F), (0x202A, 0x202E), (0x2060, 0x206F), (0x3164, 0x3164),
    (0xFE00, 0xFE0F), (0xFEFF, 0xFEFF), (0xFFA0, 0xFFA0), (0xFFF0, 0xFFF8), (0x1BCA0, 0x1BCA3),
    (0x1D173, 0x1D17A), (0xE0000, 0xE0FFF),
)  # fmt: skip
OTHER_INVISIBLE = frozenset(
    chr(c) for low, high in DEFAULT_IGNORABLE for c in range(low, high + 1)
) | {"\u2800"}
ENCODED_AT = re.compile(r"%40|&#0*64;|&#x0*40;|&commat;|\\u0040|\\x40", re.IGNORECASE)
CARD = re.compile(r"\b\d(?:[ -]?\d){12,18}\b")
LETTER = r"[^\W\d_]"  # any letter, not only ASCII: anna@корп is an address too
# A version, commit SHA (7 to 40 hex digits, one a digit) or package tag after @, in any ASCII
# case, when it is the whole name (HEAD@{1}, pkg@latest, foo@Latest, actions/checkout@v4,
# user/repo@e83a1b2): v2-gateway, master-01, user@deadbeef and anna@maın are hosts.
TAG = (
    r"(?ai:v\d+|(?=[a-f]*\d)[0-9a-f]{7,40}"
    r"|latest|next|beta|alpha|canary|rc|stable|lts|main|master)(?![\w-])"
)
# A link without a scheme ends its host with a TLD, maybe a port, then a path, or a query or
# anchor that goes on with a URL character (a "?" that ends a question, also "?)" or "?!", is
# not one).
TLD = LETTER + r"{2,63}"
LINK_END = r"(?::\d{1,5})?(?:/|[?#][\w%=&/~+-])"
# File types that are also TLDs: README.md/ or lib.rs/ is a path; wiki.acme.md/ is a link.
SOURCE_TYPES = (
    "md|py|rs|ts|tsx|js|jsx|mjs|cjs|json|toml|yaml|yml|txt|lock|cfg|ini|html|css|sh|rb|kt|go"
    "|java|cpp|hpp"
)
# A host with two or more dots (jira.corp.net), or one dot not before a source file type
# (example.com, not README.md).
DEEP_HOST = r"[\w-]+(?:\.[\w-]+)+\." + TLD
SHALLOW_HOST = r"[\w-]+\.(?!(?:" + SOURCE_TYPES + r")(?![\w-]))" + TLD
# Markdown, quotes or an escape around the @ of a dotted address: "anna"@, anna\@, `anna`@,
# ***anna***@, anna@**corp.com**. Up to three each side. Not brackets, braces or quotes after
# the @: those are code (a[i]@m.T, f"{user}@{cfg.domain}", obj@"pkg.json").
MARKUP_BEFORE_AT = r"""[\\"'*`_~]{0,3}"""
MARKUP_AFTER_AT = r"[*`_~]{0,3}"
# An ideographic full stop between letters or digits of any script but CJK and Hangul is a dot
# (jira。corp。net, пример。рф); next to CJK or Hangul text it ends a sentence.
# (NFKC maps all 58 half-width katakana into these; it leaves some compatibility ideographs such
# as U+FA11 alone, so U+F900-FAFF stays.)
CJK = "\u2e80-\u9fff\uac00-\ud7af\uf900-\ufaff\U00020000-\U0003ffff"
DOT_STOP = re.compile(f"(?<=[^\\W_{CJK}])\u3002(?=[^\\W_{CJK}])")

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
    # An e-mail: a word right before the @ (so @property and @mentions pass), maybe with markup
    # around the @, and a dotted domain with a letter in it (so react@18.3.1 passes).
    (
        re.compile(
            r"\w[\w.+-]*"
            + MARKUP_BEFORE_AT
            + r"\s?@\s?"
            + MARKUP_AFTER_AT
            + r"(?=[\w.-]*"
            + LETTER
            + r")[\w-]+(?:\.[\w-]+)+"
        ),
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


def invisible(char: str) -> bool:
    """Whether `char` does not show (spec R5): a format character or a default-ignorable one."""
    return unicodedata.category(char) == "Cf" or char in OTHER_INVISIBLE


def views(text: str) -> list[str]:
    """The four views of the text (spec R5); see the module docstring."""
    text = unicodedata.normalize("NFKC", text)  # first, so ％40 decodes and ＡＫＩＡ joins
    out = []
    for gap in (" ", ""):
        spaced = "".join(gap if invisible(c) else c for c in text)
        for decoded in (spaced, ENCODED_AT.sub("@", spaced)):
            out.append(DOT_STOP.sub(".", unicodedata.normalize("NFKC", decoded)))
    return list(dict.fromkeys(out))  # normal text gives four equal views


def first_match(text: str) -> str | None:
    """The first kind of private data a pattern finds in `text`, or None."""
    for pattern, what in PATTERNS:
        if pattern.search(text):
            return what
    return "a card number" if has_card(text) else None


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
    return next((found for view in views(text) if (found := first_match(view))), None)
