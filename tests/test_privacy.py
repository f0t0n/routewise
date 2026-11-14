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


@pytest.mark.parametrize("text", SECRETS + LEAKS)
def test_refuses_clear_leaks(text: str):
    assert finding(text) is not None


@pytest.mark.parametrize("text", CLEAN)
def test_allows_normal_code_words(text: str):
    assert finding(text) is None
