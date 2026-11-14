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
