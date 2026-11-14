"""routewise.toml is checked before anything is written."""

import pytest

from paths import PathError, relative
from settings import SettingsError, parse


def test_defaults():
    chosen = parse("")

    assert (chosen.harnesses, chosen.cap, chosen.fragment) == (["cc"], 5, "dev")
    assert (chosen.instructions, chosen.claude_md) == (["AGENTS.md"], "auto")


@pytest.mark.parametrize("value", ["auto", "import", "none"])
def test_claude_md_values(value: str):
    assert parse(f'claude_md = "{value}"').claude_md == value


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ('cap = "five"', "cap must be a whole number"),
        ("cap = 0", "cap must be a whole number"),
        ("cap = true", "cap must be a whole number"),
        ('harnesses = "cc"', "harnesses must be a list"),
        ('harnesses = ["vim"]', "harness 'vim' is not one of cc, agy"),
        ('fragment = "chat"', "fragment 'chat' is not one of"),
        ('claude_md = "always"', "claude_md 'always' is not one of auto, import, none"),
        ("claude_md = true", "claude_md must be a string"),
        ('[tiers]\nfats = "haiku"', "'fats' is not one of"),
        ('[tiers]\nfast = "haiku\\ntools: Write"', "must be a model name"),
        ("cap = [", "routewise.toml"),
    ],
)
def test_refuses_bad_settings(source: str, message: str):
    with pytest.raises(SettingsError, match=message):
        parse(source)


@pytest.mark.parametrize(
    "source",
    [
        'miss_log = "/tmp/log.jsonl"',
        'miss_log = "../log.jsonl"',
        'instructions = ["../outside/notes.md"]',
        'instructions = ["/abs/CLAUDE.md"]',
    ],
)
def test_refuses_paths_outside_the_project(source: str):
    with pytest.raises(PathError, match="must be a path inside the project"):
        parse(source)


def test_accepts_a_pinned_model():
    assert parse('[tiers]\nfast = "claude-haiku-5-5"').tiers == {"fast": "claude-haiku-5-5"}


@pytest.mark.parametrize("name", [".", "logs/", "a\x00b", ""])
def test_refuses_a_log_path_that_is_not_a_file(name: str):
    with pytest.raises(PathError):
        relative(name, "miss_log")
