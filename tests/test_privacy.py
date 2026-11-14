"""The miss-log privacy filter (spec M1): clear leaks refused, normal code words allowed."""

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
]
# Code words refused on purpose since 0.1.1: they read exactly like a link or an address.
REFUSED_CODE_WORDS = [
    "logger.info/debug calls",  # .info is a TLD: write "logger.info and logger.debug"
    "os.path/join and json.loads/dumps",  # likewise any dotted name with a letter-only last part
    "ASP.NET/Core",
    "matrix product a@b",  # reads as user@host: write "a @ b"
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
]
# A host with one dot that ends in a source file type is a path (R5: the full list).
SOURCE_TYPES = (
    "md py rs ts tsx js jsx mjs cjs json toml yaml yml txt lock cfg ini html css sh rb kt go java"
    " cpp hpp"
).split()


@pytest.mark.parametrize("text", SECRETS + LEAKS + LEAKS_SINCE_0_1_1 + REFUSED_CODE_WORDS)
def test_refuses_clear_leaks(text: str):
    assert finding(text) is not None


@pytest.mark.parametrize("text", CLEAN + CLEAN_SINCE_0_1_1)
def test_allows_normal_code_words(text: str):
    assert finding(text) is None


@pytest.mark.parametrize("ext", SOURCE_TYPES)
def test_allows_a_source_file_before_a_slash(ext: str):
    assert finding(f"see name.{ext}/x") is None
