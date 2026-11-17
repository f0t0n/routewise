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
        ('[tiers]\nfast = "haiku\\n"', "must be a model name"),
        ("cap = [", "routewise.toml"),
        ('skills = ["x"]', r"\[skills\] must be a table"),
        ('[skills]\nreviewer = "my-review"', "reviewer must be a list of skill names"),
        ("[skills]\nreviewer = [1]", "reviewer must be a list of skill names"),
        ('[skills]\nreviewer = ["My Review"]', "skill name 'My Review'"),
        ('[skills]\nreviewer = ["a\\ntools: Write"]', "skill name"),
        ('[skills]\nreviewer = ["a\\n"]', "skill name"),
        ('[skills]\nreviewer = ["a", "a"]', "skill name 'a' is listed twice"),
        ('stand_ins = ["x"]', r"\[stand_ins\] must be a table"),
        ('[stand_ins]\nreviewer = "code-reviewer"', "reviewer must be a list of agent names"),
        ('[stand_ins]\nreviewer = ["Code-Reviewer"]', "stand-in name 'Code-Reviewer'"),
        ('[stand_ins]\nreviewer = ["../x"]', "stand-in name"),
        ('[stand_ins]\nreviewer = ["a"]\nauditor = ["a"]', "stand-in name 'a' is listed twice"),
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


def test_skills_table_is_kept_per_role():
    chosen = parse('[skills]\nreviewer = ["my-review"]\nauditor = []')

    assert chosen.skills == {"reviewer": ("my-review",), "auditor": ()}
    assert parse("").skills == {}


def test_skills_setting_allows_32_names_and_refuses_33():
    many = ", ".join(f'"s{n}"' for n in range(33))
    few = ", ".join(f'"s{n}"' for n in range(32))

    assert len(parse(f"[skills]\nreviewer = [{few}]").skills["reviewer"]) == 32
    with pytest.raises(SettingsError, match="at most 32 skills"):
        parse(f"[skills]\nreviewer = [{many}]")


def test_stand_ins_are_off_by_default_and_kept_per_role():
    assert parse("").stand_ins == {}
    chosen = parse('[stand_ins]\nreviewer = ["code-reviewer"]\nauditor = ["security-auditor"]')
    assert chosen.stand_ins == {"reviewer": ("code-reviewer",), "auditor": ("security-auditor",)}


@pytest.mark.parametrize(
    "model", ["haiku", "claude-haiku-5-5", "fable", "sonnet[1m]", "us.anthropic.claude-opus-5-5:0"]
)
def test_model_names_accepted_before_still_pass(model: str):
    """R11 changes only the trailing line break; every name 0.1.2 accepted still passes."""
    assert parse(f'[tiers]\nfast = "{model}"').tiers == {"fast": model}
