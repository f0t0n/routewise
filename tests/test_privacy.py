"""The miss-log privacy filter (spec M1): clear leaks refused, normal code words allowed."""

import unicodedata

import pytest

from privacy import finding

SECRETS = [
    "ghp_" + "a1B2c3D4e5F6g7H8i9J0",
    "sk-ant-api03-" + "abcdEFGH1234",
    "sk_live_" + "abcdEFGH1234",
    "xoxb-" + "1234567890-abcdef",
    "AKIA" + "IOSFODNN7EXAMPLE",
    "eyJhbGciOi.eyJzdWIiOi.x",
    "-----BEGIN RSA " + "PRIVATE KEY-----",
    "ghp_" + "a1B2c3D4​e5F6g7H8i9J0",  # split by a zero-width space
]
LEAKS = [
    "ask jane@example.com",
    "ask jane @ example.com",
    "ask jane＠example.com",  # full-width at sign
    "ask jane﹫example.pl",  # small at sign
    "ask jane at example dot com",
    "ask jane(at)example(dot)com",
    "ask jane[at]corp[dot]io",
    "see https://example.com/x",
    "see www.example.com",
    "server 10.0.0.12:8080",
    "server 2001:db8::1",
    "server 2001:0db8:85a3:0000:0000:8a2e:0370:7334",
    "id 123e4567-e89b-12d3-a456-426614174000",
    "user U012AB3CD4",
    "file /home/jane/x",
    "file /Users/jane/x",
    "file ~jane/x",
    "key in /root/.ssh",
    "call +1 (555) 123-4567",
    "card 4111 1111 1111 1111",
    # Refused by the tool routewise was extracted from; kept refused.
    "asked anna@example.com to retry",
    "see https://example.com/page",
    "see ftp://host.example/x",
    "channel C01ABCDEF2G",
    "user U01ABCDEF2G",
]
# Let through by 0.1.0: an address without a dot in the domain, a link without a scheme or www.
LEAKS_SINCE_0_1_1 = [
    "mailed me@localhost",
    "ask anna@competera",
    "see example.com/page",
    "web-reader misread jira.example.net/browse/PRC-12",
    "docs.google.com/document/d/abc",
    "(see wiki.corp.internal/x)",
    "See Example.com/page",
    # Found in review and audit.
    "ask jane@пример.рф",
    "ask anna@корп",
    "anna@v1host",
    "jenkins@master-01 and deploy@main-db",
    "ops@v2-gateway",
    "JIRA.CORP.NET/browse/X-1",
    "jira.corp.Net/x",
    "host.corp:8080/x",
    "proxy/jira.corp.net/browse/X-1",
    "//host.com/x",
    "see …jira.corp.net/x",
    "build_server.corp.net/x",
    "jira.корп.рф/x",
    "jira。corp。net/x",
    "jira.corp.net?id=1",
    "jira.corp.net#X-1",
    "git.company.sh/repo and wiki.acme.md/page",
    "host.corp:65535/x",
    "ssh anna@v",  # only v<digits> is a tag (R5)
    # Found in the review and audit of 0.1.1 (R5 amended): markup before the @, an encoded @,
    # invisible characters inside an address or a token.
    "ask anna\\@corp.com",
    'ask "anna"@corp.com',
    "ask **anna**@corp.com",
    "ask 'anna'@corp.com",
    "ask anna%40corp.com",
    "ask anna&#64;corp.com",
    "ask anna\u200f@corp.com",
    "ghp\u200e_" + "a1B2c3D4e5F6g7H8i9J0",
    "ask anna\u2062@corp.com",
    "ask anna\u180e@corp.com",
    "ask anna\u034f@corp.com",
    # Found in the re-audit of 0.1.1 (R5, two views of the text). Regressions of 1aa6725: an
    # invisible character removed joined a leak to the word before it; a decoded %40 hid a link.
    "x\u200eAKIA" + "ABCDEFGHIJKLMNOP",
    "שלום\u200eghp_" + "abcdefgh12345678",
    "כתובת\u200e10.0.0.1",
    "שלום\u200ehttps://example.com",
    "id\u200e123e4567-e89b-12d3-a456-426614174000",
    "redirect=%40host.com/path",
    "(%40example.com/x)",
    # Bidi controls, variation selectors and tag characters; an accent split from its letter.
    "ask anna\u2066@corp.com",
    "ask anna\u202a@corp.com",
    "ask anna\u061c@corp.com",
    "ask anna\u2066@localhost",
    "ask anna\ufe0f@corp.com",
    "ask anna\U000e0041@corp.com",
    "ask jose\u200b\u0301@corp.com",
    # Other ways to write @, and markup around it.
    "ask anna\\u0040corp.com",
    "ask anna&#x40;corp.com",
    "ask anna&#064;corp.com",
    "ask anna&commat;corp.com",
    "ask `anna`@corp.com",
    "ask anna***@corp.com",
    "ask ***anna***@corp.com",
    "ask anna@**corp.com**",
    "ask anna@`corp.com`",
    "ask anna@***corp.com",
    # Found in round 3 of the 0.1.1 review (R5, four views). Regressions of d84fadf: a decoded @
    # or a full stop read in only one view hid a link or an IP.
    "redirect=&#x40;example。com/x",
    "(&commat;corp。com/x)",
    "redirect=%40example。com/path",
    "redirect=%40example.co\u200bm/path",
    "redirect=%40example.com#\u200eX-1",
    "שלום\u200e10。0。0。1",
    # \x40, more markup, and pins for each lossy step and markup character.
    "ask anna\\x40corp.com",
    "ask anna~@corp.com",  # not ~anna: that is a home folder path and hides the case
    "ask anna@~~1password.com~~",  # a digit after ~, so the home folder rule does not fire
    "ask anna％40corp.com",  # a full-width % becomes %40 only after NFKC
    "ask anna&#X40;corp.com",
    "ask anna&COMMAT;corp.com",
    "jane\u200eat\u200eexample\u200edot\u200ecom",
    "jane\u200e(at)\u200eexample\u200e(dot)\u200ecom",
    "x\u200eＡＫＩＡ" + "ABCDEFGHIJKLMNOP",
    # Round 5: 。 is a dot beside any letter or digit but CJK and Hangul (R5); 。 in a decoded
    # view and after an invisible character.
    "see пример。рф/x",
    "see café。com/x",
    "see ελ。gr/x",
    "ip ١٠。٠。٠。١",
    "ask anna@**пример。рф**",
    "ask anna%40corp。com",
    "server 1\u200b0。0。0。1",
    "ssh anna@" + "deadbeef" * 5 + "a",  # 41 hex digits, no digit (R5: a SHA has one)
    "ssh anna@a1" + "a" * 39,  # 41 hex digits with a digit: a SHA is at most 40 (R5)
    # Round 6: case folds in ASCII only, and a SHA has a digit (R5).
    "ask anna@ma\u0131n",
    "ask anna@ma\u0130n",
    "ssh user@deadbeef",
    "ssh admin@facadeb",
    # A query or anchor that goes on with each URL character R5 names, one per case.
    "see wiki.corp.io#%E2%9C%93",
    "see wiki.corp.io#-section",
    "see wiki.corp.io#/settings",
    "see wiki.corp.io?=x",
    "see wiki.corp.io?&a=1",
    "see wiki.corp.io#~1",  # not #~x: ~ and a letter is a home folder path
    "see wiki.corp.io?+q",
    "see wiki.corp.io#_top",
]
# Code words refused on purpose since 0.1.1: they read exactly like a link or an address.
REFUSED_CODE_WORDS = [
    "logger.info/debug calls",  # .info is a TLD: write "logger.info and logger.debug"
    "os.path/join and json.loads/dumps",  # likewise any dotted name with a letter-only last part
    "ASP.NET/Core",
    "matrix product a@b",  # reads as user@host: write "a @ b"
    "pip install foo@git",
    # Named after round 5 (R5): a dotted name before ? or # with text, and an ASCII word, 。 and
    # an ASCII path after CJK text, which cannot be told from jira。corp。net/x.
    "Class.method#overload and config.key#section",
    "repo.name#123",
    "ticket abc.def?x=1",
    # Named after round 6: two-dot file names, a 6-digit SHA, a number before 。 after CJK, and
    # 。 between words of another script with no space.
    "see foo.test.ts#L10 and jquery.min.js?v=1",
    "pinned foo@abc123",
    "修复了问题1。src/a.ts",
    "Привет。Мир/x",
    "改了config。lib/x.py",
    "路由用了GPT-4。Next.js/React",
]
CLEAN = [
    "missed an unchecked return value in the parser",
    "logger.info call was dropped",
    "used @property decorator wrongly",
    "confused GPT-4 with AES-256 and HTTP-2 in the notes",
    "test_handles_utf8_input_with_bom_marker failed",
    "src/components/auth/login_form_v2/index was not found",
    "wrong commit 3f9a1c2e4b5d6f708192a3b4c5d6e7f8091a2b3c",
    "misread the UTF-8 and SHA-256 notes in miss_log.py",
    "called Add::add instead of Sub::sub",
    "run took 10:30:00 and returned 40 lines, cap is 30",
    "self.app and config.dev were mixed up",
    "version 1.2.3 of the parser",
    "looked at the cache and then at the log",
]
# Code words that look like a dotless address or a link without a scheme (0.1.1): file paths,
# versions, ratios, package and git references, and a source file name before a slash.
CLEAN_SINCE_0_1_1 = [
    "edited lib/privacy.py and tests/test_privacy.py",
    "looked in src/a.ts/ for the handler",
    "wrote under docs/v0.1.0/ by mistake",
    "path v1.25/notes was wrong",
    "rated 3.5/5 and 3.14/2 in the notes",
    "compared README.md/CHANGELOG.md and lib.rs/main.rs",
    "mixed up Next.js/React and Vue.js/Svelte",
    "did it call os.path? yes, and logger.info?",
    "node_modules/lodash.merge/index was missing",
    "my_module.py/run was not found",
    "installed react@18.3.1 and pkg@latest",
    "pinned actions/checkout@v4 and org/action@main",
    "reset to HEAD@{1} and dropped stash@{0}",
    "used @property and @types/node",
    "pinned pkg@rc, pkg@lts, pkg@stable, pkg@next, pkg@beta, pkg@alpha, pkg@canary",
    "ssh root@master and me@main still pass (R5 kept gap)",
    "a.b/c is too short a TLD",
    "x." + "a" * 64 + "/y is too long a TLD",
    "anna****@corp.com and anna@****corp.com: markup is up to three characters (R5)",
    'printf %40s, 100%40 done, a["k"]@b, he said "hi"@ noon',
]
# Kept gaps since round 4 (R5): brackets, braces, angle brackets and quotes after the @ are code
# (a[i]@m.T, f"{user}@{cfg.domain}"), so these pass. Moving one back to the refused lists is an R5
# change, not a cleanup.
KEPT_GAPS = [
    "ask [anna]@corp.com",
    "ask <anna>@corp.com",
    "ask {anna}@corp.com",
    "ask (anna)@corp.com",
    'ask anna@"corp.com"',
    "ask anna@'corp.com'",
    "ask anna@{corp.com}",
    "ask anna@[corp.com]",
    "ask anna@<corp.com>",
]
# Text 0.1.0 allowed that rounds 2 to 4 refused for a while (success criterion 10).
CLEAN_SINCE_ROUND_4 = [
    "修复路由。然后改a/b",
    "已修复。lib/x.py",
    "ルーティングを修正。次にsrc/a.tsを確認",
    "updated config。然后改a/b",  # 。 after ASCII but before CJK ends a sentence
    'built the address as f"{user}@{cfg.domain}"',
    "template {{user}}@{{site.domain}}",
    "f-string {x}@{y.T} for matmul",
    'set obj@"pkg.json"',
    "wrote x@'a.b' in the test",
    "computed a[i]@m.T and f(x)@w.T",
    "100%40 off foo.bar",
    # Round 5: SHA pins and tags in any case (R5).
    "pinned user/repo@e83a1b2 and foo@Latest",
    "uses actions/checkout@8f4b7f84864484a7bf31766abe9204da3cbe65b3",
    "Привет, это тест",  # Cyrillic prose, no 。
    "pinned user/repo@b4ffde65f46336ab88eb53be808477a3936bae11",  # 40 hex, starts with a letter
    # 。 next to each CJK or Hangul range ends a sentence (R5).
    "라우팅을 고쳤다。lib/x.py",
    "豈。lib/x.py",
    "ﾃｽﾄ。lib/x.py",
    "\U00020000。lib/x.py",
    # Round 6: a compatibility ideograph NFKC leaves alone, the edges of the CJK ranges, and a
    # question that ends with ?) ?! or ?, (R5).
    "山\ufa11。lib/x.py",
    "人々。lib/x.py",  # 々 (U+3005) is a letter near the start of the CJK range
    "\uac00。lib/x.py",
    "\U00030000。lib/x.py",
    "(what is foo.bar?) and foo.bar?! and did foo.bar?, then",
    "pinned admin@facade0",  # hex with a digit is a SHA (R5)
    "renamed foo_。bar/x",  # 。 after _ is not between letters or digits (R5)
]
# Every character R5 counts as invisible, one per range and every one 0.1.1 listed first.
INVISIBLE = [
    *"\u200b\u200c\u200d\u200e\u200f\u2060\u2061\u2062\u2063\u2064\ufeff\u00ad\u180e\u034f",
    *"\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069\u061c\u0600",
    *"\ufe00\ufe0f\U000e0001\U000e0041\U000e007f",
    # Default_Ignorable_Code_Point (Unicode 18.0 DerivedCoreProperties): both ends of each range
    # that is not all Cf; and the braille blank.
    *"\u17b4\u17b5\u180b\u180d\u180f\u2065\u206f\uffa0\ufff0\ufff8",
    *"\U0001bca0\U0001bca3\U0001d173\U0001d17a\U000e0000\U000e0100\U000e01ef\U000e0fff",
    "\u2800",
]
# Hangul fillers are letters, so one before an @ joins the local part; inside a token, an IP
# or a path they must not hide it.
FILLERS = ["\u115f", "\u1160", "\u3164", "\uffa0"]
# A host with one dot that ends in a source file type is a path (R5: the full list).
SOURCE_TYPES = (
    "md py rs ts tsx js jsx mjs cjs json toml yaml yml txt lock cfg ini html css sh rb kt go java"
    " cpp hpp"
).split()


@pytest.mark.parametrize("text", SECRETS + LEAKS + LEAKS_SINCE_0_1_1 + REFUSED_CODE_WORDS)
def test_refuses_clear_leaks(text: str):
    assert finding(text) is not None


@pytest.mark.parametrize("text", CLEAN + CLEAN_SINCE_0_1_1 + CLEAN_SINCE_ROUND_4 + KEPT_GAPS)
def test_allows_normal_code_words(text: str):
    assert finding(text) is None


@pytest.mark.parametrize("ext", SOURCE_TYPES)
def test_allows_a_source_file_before_a_slash(ext: str):
    assert finding(f"see name.{ext}/x") is None


@pytest.mark.parametrize("char", INVISIBLE, ids=lambda c: f"U+{ord(c):04X}")
def test_refuses_an_address_split_by_an_invisible_character(char: str):
    assert finding(f"ask anna{char}@corp.com") is not None


ENCODED_AT = ["%40", "&#64;", "&#064;", "&#x40;", "&commat;", "\\u0040", "\\x40"]


# One dot only: in wiki.corp.io/x the inner corp.io/x is a link by itself, which hides the bug.
@pytest.mark.parametrize("host", ["corp.io/x", "corp。io/x", "co\u200brp.io/x", "corp.io#\u200ex"])
@pytest.mark.parametrize("at", ENCODED_AT)
def test_refuses_a_link_after_an_encoded_at(at: str, host: str):
    """Decoding an @ must not hide the link after it (R5, four views)."""
    assert finding(f"redirect={at}{host}") is not None


@pytest.mark.parametrize("char", FILLERS, ids=lambda c: f"U+{ord(c):04X}")
@pytest.mark.parametrize(
    "template", ["ghp_{}a1B2c3D4e5F6g7H8i9J0", "server 10.0.0{}.12", "file /home/{}jane/x"]
)
def test_refuses_a_leak_split_by_a_hangul_filler(template: str, char: str):
    assert finding(template.format(char)) is not None


def visible(text: str) -> bool:
    return not any(unicodedata.category(c) == "Cf" or c in INVISIBLE + FILLERS for c in text)


@pytest.mark.parametrize("char", ["\u200e", "\u2066", "\u200b"], ids=["LRM", "LRI", "ZWSP"])
@pytest.mark.parametrize("text", [t for t in SECRETS + LEAKS + LEAKS_SINCE_0_1_1 if visible(t)])
def test_refuses_a_leak_right_after_an_invisible_character(text: str, char: str):
    """An invisible character must not join a leak to the word before it (R5, split view).

    A leak that is also split by one inside it is not covered by either view (see SPEC R5).
    """
    assert finding("x" + char + text) is not None


@pytest.mark.parametrize("char", ["\u200e", "\u2066", "\u200b"], ids=["LRM", "LRI", "ZWSP"])
@pytest.mark.parametrize("text", CLEAN + CLEAN_SINCE_0_1_1 + CLEAN_SINCE_ROUND_4)
def test_allows_normal_text_with_an_invisible_character(text: str, char: str):
    first, _, rest = text.partition(" ")
    assert finding(f"{first}{char} {rest}") is None
