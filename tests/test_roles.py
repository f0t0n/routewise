"""Role files: only known keys, read-only tools (spec R-A1), and the generated marker."""

from pathlib import Path

import pytest

from roles import Harness, RoleError, is_generated, read_role, read_roles, render

HOME = Path(__file__).resolve().parent.parent
CC = Harness(
    key="cc",
    dir=".claude/agents",
    tools={"read": ["Read"], "search": ["Glob", "Grep"], "shell": ["Bash"], "web": ["WebFetch"]},
    tiers={"fast": "haiku", "balanced": "sonnet", "deep": "opus", "frontier": "fable"},
    efforts=("low", "medium", "high"),
)
GOOD = "---\nname: x\ndescription: >-\n  Two\n  lines.\ntools: [read]\ntier: fast\n---\nBody\n"


def role(tmp_path: Path, text: str, name: str = "x.md") -> Path:
    path = tmp_path / name
    path.write_text(text)
    return path


def test_shipped_roles_are_read_only():
    for shipped in read_roles(HOME / "roles"):
        rendered = render(shipped, CC, "routewise/roles/" + shipped.source.name)
        tools = next(line for line in rendered.splitlines() if line.startswith("tools:"))
        for forbidden in ("Write", "Edit", "NotebookEdit"):
            assert forbidden not in tools


def test_renders_the_description_block(tmp_path: Path):
    rendered = render(read_role(role(tmp_path, GOOD)), CC, "routewise/roles/x.md")

    assert "name: x\ndescription: >-\n  Two\n  lines.\ntools: Read\nmodel: haiku\n---" in rendered


@pytest.mark.parametrize(
    "line",
    [
        "permissionMode: bypassPermissions",
        "tools : [read]",
        "hooks:",
        "mcpServers: x",
    ],
)
def test_refuses_any_other_frontmatter_key(tmp_path: Path, line: str):
    path = role(tmp_path, GOOD.replace("tier: fast\n", f"tier: fast\n{line}\n"))

    with pytest.raises(RoleError, match="not allowed"):
        read_role(path)


@pytest.mark.parametrize("tools", ["[read, write]", "[edit]"])
def test_refuses_write_tools(tmp_path: Path, tools: str):
    path = role(tmp_path, GOOD.replace("tools: [read]", f"tools: {tools}"))

    with pytest.raises(RoleError, match="read-only"):
        read_role(path)


def test_refuses_a_harness_that_maps_to_a_write_tool(tmp_path: Path):
    harness = Harness("cc", ".claude/agents", {"read": ["Read", "Write"]}, CC.tiers, CC.efforts)

    with pytest.raises(RoleError, match="not allowed"):
        render(read_role(role(tmp_path, GOOD)), harness, "x")


def test_refuses_bad_values(tmp_path: Path):
    with pytest.raises(RoleError, match="unknown tier"):
        read_role(role(tmp_path, GOOD.replace("tier: fast", "tier: huge")))
    with pytest.raises(RoleError, match="no frontmatter"):
        read_role(role(tmp_path, "Body only\n"))
    with pytest.raises(RoleError, match="must be one word"):
        read_role(role(tmp_path, GOOD.replace("name: x", "name: x y")))
    maxed = read_role(role(tmp_path, GOOD.replace("tier: fast", "tier: fast\neffort: max")))
    with pytest.raises(RoleError, match="not offered"):
        render(maxed, CC, "x")


def test_marker_must_name_the_file_itself(tmp_path: Path):
    text = render(read_role(role(tmp_path, GOOD)), CC, "routewise/roles/reviewer.md")

    assert is_generated(role(tmp_path, text, "reviewer.md"))
    assert not is_generated(role(tmp_path, text, "strict-reviewer.md"))


@pytest.mark.parametrize("tools", ["[]", "[ , ]"])
def test_refuses_an_empty_tools_list(tmp_path: Path, tools: str):
    # An empty tools line gives a Claude Code agent every tool, write tools included.
    with pytest.raises(RoleError, match="tools is empty"):
        read_role(role(tmp_path, GOOD.replace("tools: [read]", f"tools: {tools}")))


def test_allows_only_known_read_only_harness_tools(tmp_path: Path):
    for name in ("mcp__fs__write_file", "TodoWrite"):
        harness = Harness("cc", ".claude/agents", {"read": ["Read", name]}, CC.tiers, CC.efforts)
        with pytest.raises(RoleError, match="not allowed"):
            render(read_role(role(tmp_path, GOOD)), harness, "x")
    empty = Harness("cc", ".claude/agents", {"read": []}, CC.tiers, CC.efforts)
    with pytest.raises(RoleError, match="empty list means every tool"):
        render(read_role(role(tmp_path, GOOD)), empty, "x")


def test_refuses_a_harness_tier_that_is_not_a_model_name(tmp_path: Path):
    tiers = {**CC.tiers, "fast": "haiku\npermissionMode: bypassPermissions"}
    harness = Harness("cc", ".claude/agents", CC.tools, tiers, CC.efforts)

    with pytest.raises(RoleError, match="must be a model name"):
        render(read_role(role(tmp_path, GOOD)), harness, "x")


def test_marker_with_a_space_in_the_path(tmp_path: Path):
    text = render(read_role(role(tmp_path, GOOD)), CC, "my tools/roles/reviewer.md")

    assert is_generated(role(tmp_path, text, "reviewer.md"))


AGY = Harness(
    key="agy",
    dir=".agents/agents",
    tools={"read": ["view_file"]},
    tiers={},
    efforts=(),
)
TWO = "[agent-skills:code-review-and-quality, my-skill]"


def test_renders_skills_for_each_harness(tmp_path: Path):
    """R8: a role's skills reach the agent; cc reads a comma string, agy a YAML list."""
    shipped = read_role(role(tmp_path, GOOD.replace("tier: fast", f"tier: fast\nskills: {TWO}")))

    assert "\nskills: agent-skills:code-review-and-quality, my-skill\n" in render(shipped, CC, "x")
    assert f"\nskills: {TWO}\n" in render(shipped, AGY, "x")


@pytest.mark.parametrize("value", ["[]", "[ , ]"])
def test_no_skills_line_without_skills(tmp_path: Path, value: str):
    plain = read_role(role(tmp_path, GOOD))
    empty = read_role(role(tmp_path, GOOD.replace("tier: fast", f"tier: fast\nskills: {value}")))

    for each in (plain, empty):
        assert each.skills == ()
        assert "skills:" not in render(each, CC, "x")


@pytest.mark.parametrize(
    "value",
    [
        "[Code-Review]",
        "[code review]",
        "[a:b:c]",
        "[:a]",
        "[a:]",
        "[-a]",
        "[a/b]",
        "[..]",
        "[a..b]",
        "code-review",
        "[" + ", ".join(f"s{n}" for n in range(33)) + "]",
    ],
)
def test_refuses_a_bad_skills_value(tmp_path: Path, value: str):
    """R8, S6: a skill name cannot carry a path, a space or another frontmatter key."""
    path = role(tmp_path, GOOD.replace("tier: fast", f"tier: fast\nskills: {value}"))

    with pytest.raises(RoleError, match="skills must be a list|skill name|at most 32 skills"):
        read_role(path)


def test_a_line_break_cannot_smuggle_a_key_through_skills(tmp_path: Path):
    path = role(tmp_path, GOOD.replace("tier: fast", "tier: fast\nskills: [a,\n  b]"))

    with pytest.raises(RoleError):
        read_role(path)


SKILL_RULES = (
    "this file wins",  # a skill and the body disagree
    "report it as a suggestion",  # a skill step that would change a file
    "High is Required",  # severity mapping
    "report template",  # the skill's template is not used
    "`Checklist: <skill names> loaded`",
    "`Checklist: none`",
)


@pytest.mark.parametrize(
    ("name", "skill"),
    [
        ("reviewer", "agent-skills:code-review-and-quality"),
        ("auditor", "agent-skills:security-and-hardening"),
    ],
)
def test_review_roles_load_a_checklist_skill_and_keep_their_rules(name: str, skill: str):
    """R8: the skill says what to check; the body keeps behaviour, tools and return shape."""
    shipped = read_role(HOME / "roles" / f"{name}.md")

    assert shipped.skills == (skill,)
    for rule in SKILL_RULES:
        assert rule in shipped.body, rule
    assert "Every Critical and Required finding" in shipped.body


def test_reviewer_returns_mutation_suggestions():
    assert "Mutation suggestions" in read_role(HOME / "roles" / "reviewer.md").body


def test_other_roles_load_no_skills():
    for shipped in read_roles(HOME / "roles"):
        if shipped.source.stem not in ("reviewer", "auditor"):
            assert shipped.skills == (), shipped.source.name
