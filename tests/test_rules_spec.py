"""The rules spec shipped to projects holds the rules the roles and blocks cite (R13)."""

from conftest import HOME

RULES = (HOME / "spec" / "SPEC-model-routing.md").read_text(encoding="utf-8")


def section(number: int) -> str:
    start = RULES.index(f"\n## {number}. ")
    return RULES[start : RULES.index(f"\n## {number + 1}. ", start)]


def test_version_4_names_the_judge():
    line = RULES.splitlines()[2]
    assert line.startswith("Version 4, 2026-11-18 ("), line
    assert "R-A7" in line


def test_the_roles_table_and_rule_r_a7_define_the_judge():
    roles = section(4)
    row = next(x for x in roles.splitlines() if x.startswith("| `judge` |"))
    assert "| `frontier` | `medium` | read, search, shell, web |" in row
    assert "Needs access" in row
    assert "- **R-A7." in roles
    for phrase in (
        "only when the person asks",
        "not which option",
        "never approval",
        "network use goes through the web tools only",
        "nothing from the brief or from files into a query or URL",
        "claimed by the judge",
        "WebSearch",
        "a residual risk the maintainer accepted",
    ):
        assert phrase in roles, phrase


def test_n2_d4_and_a4_allow_the_judge_only_on_request():
    when = section(5)
    n2 = next(x for x in when.splitlines() if x.startswith("- **N2.**"))
    assert "except advice from `judge` when the person asks for it (R-A7)" in n2
    assert "- **D4." in when
    assert "- **A4." in when
    assert "a link the decision is about is given as a starting point outside the quote" in when


def test_the_fragment_and_boundaries_name_the_judge():
    assert "Start `judge` only when the person's own message asks" in section(10)
    ask_first = next(x for x in section(12).splitlines() if x.startswith("- **Ask first:**"))
    assert "`judge`" in ask_first
