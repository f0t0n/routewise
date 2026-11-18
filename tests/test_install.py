"""routewise/install on a throwaway project."""

import shutil
import subprocess
from pathlib import Path

import pytest
from conftest import COPY, HOME, run

ROLES = ["auditor.md", "explore.md", "judge.md", "log-reader.md", "reviewer.md", "web-reader.md"]


def front(path: Path) -> str:
    return path.read_text(encoding="utf-8").split("---\n")[1]


def set_config(root: Path, old: str, new: str) -> None:
    path = root / "routewise.toml"
    path.write_text(path.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")


def test_first_run_sets_up_claude_code(project: Path):
    result = run(project, "install")

    assert result.returncode == 0, result.stderr
    assert (project / "routewise.toml").exists()
    assert (project / "ROUTING-BINDING.md").exists()
    assert (project / "logs" / "delegation-misses.jsonl").read_text() == ""
    assert sorted(p.name for p in (project / ".claude" / "agents").iterdir()) == ROLES
    assert not (project / ".agents").exists()
    agents_md = (project / "AGENTS.md").read_text()
    assert "at most 5" in agents_md
    assert "`routewise/bin/miss-log add --mode dev" in agents_md
    assert "does the work itself" in agents_md
    assert not (project / "CLAUDE.md").exists()
    assert "note:" not in result.stdout and "warning:" not in result.stdout


def test_roles_get_model_effort_and_tool_names(project: Path):
    run(project, "install")
    agents = project / ".claude" / "agents"

    explore = front(agents / "explore.md")
    assert "name: Explore" in explore
    assert "model: haiku" in explore
    assert "effort:" not in explore
    assert "tools: Read, Glob, Grep" in explore
    assert "tier:" not in explore
    assert "description: >-" in explore
    assert "model: sonnet\neffort: medium" in front(agents / "reviewer.md")
    assert "model: opus\neffort: high" in front(agents / "auditor.md")
    assert "tools: WebSearch, WebFetch, Read" in front(agents / "web-reader.md")


def test_second_run_changes_nothing(project: Path):
    run(project, "install")

    again = run(project, "install")
    check = run(project, "install", "--check")

    assert again.stdout.strip() == "routewise: nothing to change"
    assert check.returncode == 0


def test_check_reports_drift_and_install_fixes_it(project: Path):
    run(project, "install")
    set_config(project, "cap = 5", "cap = 3")

    check = run(project, "install", "--check")
    assert check.returncode == 1
    assert "drift AGENTS.md" in check.stdout
    assert "at most 5" in (project / "AGENTS.md").read_text()

    run(project, "install")
    assert "at most 3" in (project / "AGENTS.md").read_text()


def test_keeps_existing_instructions_and_uninstall_restores_them(project: Path):
    (project / "AGENTS.md").write_text("# My project\n\nKeep this.\n")

    run(project, "install")
    text = (project / "AGENTS.md").read_text()
    assert text.startswith("# My project\n\nKeep this.\n\n<!-- routewise:start")

    result = run(project, "install", "--uninstall")
    assert result.returncode == 0, result.stderr
    assert (project / "AGENTS.md").read_text() == "# My project\n\nKeep this.\n"
    assert list((project / ".claude" / "agents").iterdir()) == []
    assert (project / "ROUTING-BINDING.md").exists()


def test_refuses_to_overwrite_an_agent_it_did_not_write(project: Path):
    agents = project / ".claude" / "agents"
    agents.mkdir(parents=True)
    (agents / "reviewer.md").write_text("---\nname: reviewer\n---\nmine\n")

    result = run(project, "install")

    assert result.returncode == 2
    assert ".claude/agents/reviewer.md exists and was not written by routewise" in result.stderr
    assert (agents / "reviewer.md").read_text() == "---\nname: reviewer\n---\nmine\n"


def test_antigravity_gets_agents_without_model_and_one_block(project: Path):
    (project / ".agents").mkdir()
    (project / "AGENTS.md").write_text("# Rules\n")
    (project / "CLAUDE.md").symlink_to("AGENTS.md")

    result = run(project, "install")

    assert result.returncode == 0, result.stderr
    explore = front(project / ".agents" / "agents" / "explore.md")
    assert "tools: [view_file, list_dir, find_by_name, grep_search]" in explore
    assert "model:" not in explore
    assert "effort:" not in front(project / ".agents" / "agents" / "reviewer.md")
    assert (project / "AGENTS.md").read_text().count("routewise:start") == 1
    assert (project / "CLAUDE.md").is_symlink()


def test_tier_override_pins_a_model(project: Path):
    run(project, "install")
    set_config(project, '# fast = "claude-haiku-5-5"', 'fast = "claude-haiku-5-5"')

    run(project, "install")

    assert "model: claude-haiku-5-5" in front(project / ".claude" / "agents" / "explore.md")


def test_the_judge_follows_the_frontier_tier_and_its_skills_setting(project: Path):
    """R13: a project changes the judge's model with [tiers] and its skills with [skills]."""
    run(project, "install")
    judge = project / ".claude" / "agents" / "judge.md"
    assert "\nmodel: fable\neffort: medium\n" in front(judge)

    set_config(project, '# fast = "claude-haiku-5-5"', 'frontier = "claude-fable-5-2"')
    set_config(project, "[skills]\n", '[skills]\njudge = ["my-decisions"]\n')
    run(project, "install")

    assert "model: claude-fable-5-2" in front(judge)
    assert "skills: my-decisions" in front(judge)
    assert "`Checklist: my-decisions <loaded or missing>`" in judge.read_text()


def test_removes_a_generated_agent_whose_role_is_gone(project: Path):
    run(project, "install")
    (project / "routewise" / "roles" / "auditor.md").unlink()

    result = run(project, "install")

    assert "remove .claude/agents/auditor.md" in result.stdout
    assert not (project / ".claude" / "agents" / "auditor.md").exists()


def test_assistant_fragment(project: Path):
    run(project, "install")
    set_config(project, 'fragment = "dev"', 'fragment = "assistant"')

    run(project, "install")

    text = (project / "AGENTS.md").read_text()
    assert "## Delegation (assistant mode)" in text
    assert "does the work itself" in text
    assert "--mode assistant --role web-reader" in text
    assert "`Explore`" not in text


def test_rejects_an_unknown_harness(project: Path):
    run(project, "install")
    set_config(project, 'harnesses = ["cc"]', 'harnesses = ["cc", "vim"]')

    result = run(project, "install")

    assert result.returncode == 2
    assert "harness 'vim' is not one of cc, agy" in result.stderr


# --- review and audit findings (2026-11-14) -------------------------------------------------


@pytest.mark.parametrize("name", ["AGENTS.md", "CLAUDE.md", ".claude/CLAUDE.md"])
def test_a_lone_start_marker_is_refused_and_the_text_kept(project: Path, name: str):
    start = "<!-- routewise:start (generated: edit routewise.toml and re-run routewise/install) -->"
    text = f"# Mine\n\n{start}\nIMPORTANT USER TEXT\n"
    (project / name).parent.mkdir(exist_ok=True)
    (project / name).write_text(text)

    first = run(project, "install")
    second = run(project, "install", "--uninstall")

    assert (first.returncode, second.returncode) == (2, 2)
    assert "fix the markers by hand" in first.stderr
    assert (project / name).read_text() == text
    assert not (project / "routewise.toml").exists()


def test_a_failed_run_writes_nothing(project: Path):
    agents = project / ".claude" / "agents"
    agents.mkdir(parents=True)
    (agents / "reviewer.md").write_text("mine\n")

    run(project, "install")

    assert not (project / "routewise.toml").exists()
    assert not (project / "AGENTS.md").exists()


def test_check_without_settings_reports_drift(project: Path):
    result = run(project, "install", "--check")

    assert result.returncode == 1
    assert "drift routewise.toml" in result.stdout
    assert not (project / "routewise.toml").exists()


def test_uninstall_removes_an_agents_md_it_created_and_check_sees_drift(project: Path):
    run(project, "install")

    run(project, "install", "--uninstall")

    assert not (project / "AGENTS.md").exists()
    assert run(project, "install", "--check").returncode == 1


def test_a_renamed_copy_of_a_generated_agent_is_kept(project: Path):
    run(project, "install")
    agents = project / ".claude" / "agents"
    copy = agents / "strict-reviewer.md"
    copy.write_text((agents / "reviewer.md").read_text().replace("name: reviewer", "name: strict"))

    run(project, "install")
    run(project, "install", "--uninstall")

    assert copy.exists()


def test_dropping_a_harness_removes_its_agents(project: Path):
    (project / ".agents").mkdir()
    run(project, "install")
    set_config(project, 'harnesses = ["cc", "agy"]', 'harnesses = ["cc"]')

    run(project, "install")

    assert list((project / ".agents" / "agents").iterdir()) == []


@pytest.mark.parametrize("name", ["AGENTS.md", "CLAUDE.md"])
def test_a_symlink_out_of_the_project_is_refused(project: Path, tmp_path: Path, name: str):
    outside = tmp_path / "outside.md"
    (project / name).symlink_to(outside)  # dangling

    result = run(project, "install")

    assert result.returncode == 2
    assert "leads outside the project" in result.stderr
    assert not outside.exists()


def test_a_symlinked_agents_folder_out_of_the_project_is_refused(project: Path, tmp_path: Path):
    (tmp_path / "shared").mkdir()
    (project / ".claude").mkdir()
    (project / ".claude" / "agents").symlink_to(tmp_path / "shared")

    result = run(project, "install")

    assert result.returncode == 2
    assert list((tmp_path / "shared").iterdir()) == []


def test_a_symlinked_routewise_installs_into_the_project(tmp_path: Path, project: Path):
    other = tmp_path / "other"
    other.mkdir()
    (other / "routewise").symlink_to(project / "routewise")

    result = run(other, "install")

    assert result.returncode == 0, result.stderr
    assert (other / "AGENTS.md").exists()
    assert not (project / "AGENTS.md").exists()


def test_crlf_instructions_keep_their_line_ends(project: Path):
    for name in ("AGENTS.md", "CLAUDE.md"):
        (project / name).write_bytes(b"# Mine\r\n\r\nKeep.\r\n")

    run(project, "install")
    for name in ("AGENTS.md", "CLAUDE.md"):
        data = (project / name).read_bytes()
        assert b"routewise:start" in data
        assert b"\n" not in data.replace(b"\r\n", b"")

    run(project, "install", "--uninstall")
    for name in ("AGENTS.md", "CLAUDE.md"):
        assert (project / name).read_bytes() == b"# Mine\r\n\r\nKeep.\r\n"


def test_a_tier_value_cannot_add_frontmatter(project: Path):
    run(project, "install")
    set_config(project, '# fast = "claude-haiku-5-5"', 'fast = "haiku\\ntools: Write"')

    result = run(project, "install")

    assert result.returncode == 2
    assert "must be a model name" in result.stderr
    assert "Write" not in (project / ".claude" / "agents" / "explore.md").read_text()


# --- second review and audit (2026-11-14) ---------------------------------------------------


def test_uninstall_keeps_a_symlinked_claude_md_and_cleans_its_target(project: Path):
    (project / "CLAUDE.md").symlink_to("AGENTS.md")
    set_up = run(project, "install")
    assert set_up.returncode == 0, set_up.stderr
    assert (project / "AGENTS.md").read_text().count("routewise:start") == 1

    result = run(project, "install", "--uninstall")

    assert result.returncode == 0, result.stderr
    assert (project / "CLAUDE.md").is_symlink()
    assert "routewise:start" not in (project / "AGENTS.md").read_text()
    assert run(project, "install").returncode == 0
    assert (project / "CLAUDE.md").is_symlink()


def test_a_read_only_instruction_file_stops_the_run_before_any_write(project: Path):
    claude = project / "AGENTS.md"
    claude.write_text("# Mine\n")
    claude.chmod(0o444)
    try:
        result = run(project, "install")
    finally:
        claude.chmod(0o644)

    assert result.returncode == 2
    assert "cannot be written" in result.stderr
    assert not (project / "routewise.toml").exists()
    assert not (project / ".claude").exists()
    assert claude.read_text() == "# Mine\n"


def test_a_project_that_does_not_hold_routewise_is_refused(project: Path, tmp_path: Path):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()

    result = run(project, "install", "--project", str(elsewhere))
    log = run(project, "bin/miss-log", "--project", str(elsewhere), "report")

    assert (result.returncode, log.returncode) == (2, 2)
    assert "copy routewise/ into the project first" in result.stderr
    assert list(elsewhere.iterdir()) == []


def test_a_harness_tier_cannot_add_frontmatter(project: Path):
    harness = project / "routewise" / "harness.toml"
    harness.write_text(
        harness.read_text().replace('fast = "haiku"', 'fast = "haiku\\npermissionMode: x"')
    )

    result = run(project, "install")

    assert result.returncode == 2
    assert "must be a model name" in result.stderr
    assert not (project / ".claude").exists()


def test_a_role_with_no_tools_is_refused(project: Path):
    role = project / "routewise" / "roles" / "zz.md"
    role.write_text("---\nname: zz\ndescription: x\ntools: [ , ]\ntier: fast\n---\nBody\n")

    result = run(project, "install")

    assert result.returncode == 2
    assert "tools is empty" in result.stderr


# --- AGENTS.md as the home of the block, CLAUDE.md as an import (claude_md) -----------------

START = "<!-- routewise:start (generated: edit routewise.toml and re-run routewise/install) -->"
END = "<!-- routewise:end -->"


def import_block(line: str = "@AGENTS.md") -> str:
    return f"{START}\n{line}\n{END}\n"


def settings_file(root: Path, text: str) -> None:
    (root / "routewise.toml").write_text(text)


def test_claude_md_present_gets_an_import_block(project: Path):
    (project / "CLAUDE.md").write_text("# Mine\n")

    result = run(project, "install")

    assert result.returncode == 0, result.stderr
    assert (project / "CLAUDE.md").read_text() == "# Mine\n\n" + import_block()
    assert "## Delegation" in (project / "AGENTS.md").read_text()
    assert "note:" not in result.stdout
    assert run(project, "install", "--check").returncode == 0

    (project / "CLAUDE.md").write_text("# Mine\n")
    check = run(project, "install", "--check")
    assert check.returncode == 1
    assert "drift CLAUDE.md" in check.stdout

    run(project, "install")
    run(project, "install", "--uninstall")
    assert (project / "CLAUDE.md").read_text() == "# Mine\n"
    assert not (project / "AGENTS.md").exists()


@pytest.mark.parametrize("line", ["@AGENTS.md", "@./AGENTS.md"])
def test_claude_md_that_already_imports_agents_md_is_left_alone(project: Path, line: str):
    text = f"# Mine\n\n{line}\n"
    (project / "CLAUDE.md").write_text(text)

    result = run(project, "install")

    assert result.returncode == 0, result.stderr
    assert (project / "CLAUDE.md").read_text() == text
    assert run(project, "install", "--check").returncode == 0
    run(project, "install", "--uninstall")
    assert (project / "CLAUDE.md").read_text() == text


def test_an_import_in_code_does_not_count(project: Path):
    text = "# Mine\n\n```\n@AGENTS.md\n```\n"
    (project / "CLAUDE.md").write_text(text)

    run(project, "install")

    assert (project / "CLAUDE.md").read_text() == text + "\n" + import_block()


def test_an_import_added_by_hand_replaces_the_block(project: Path):
    (project / "CLAUDE.md").write_text("# Mine\n")
    run(project, "install")
    claude = project / "CLAUDE.md"
    claude.write_text("@AGENTS.md\n\n" + claude.read_text())

    assert run(project, "install", "--check").returncode == 1
    run(project, "install")

    assert claude.read_text() == "@AGENTS.md\n\n# Mine\n"


def test_dot_claude_claude_md_imports_from_its_own_folder(project: Path):
    (project / ".claude").mkdir()
    nested = project / ".claude" / "CLAUDE.md"
    nested.write_text("# Mine\n")

    result = run(project, "install")

    assert result.returncode == 0, result.stderr
    assert nested.read_text() == "# Mine\n\n" + import_block("@../AGENTS.md")
    assert not (project / "CLAUDE.md").exists()
    assert run(project, "install", "--check").returncode == 0
    run(project, "install", "--uninstall")
    assert nested.read_text() == "# Mine\n"


def test_only_the_first_claude_md_gets_the_import(project: Path):
    (project / ".claude").mkdir()
    (project / ".claude" / "CLAUDE.md").write_text("# Nested\n")
    (project / "CLAUDE.md").write_text("# Root\n")

    run(project, "install")

    assert "@AGENTS.md" in (project / "CLAUDE.md").read_text()
    assert (project / ".claude" / "CLAUDE.md").read_text() == "# Nested\n"


def test_claude_local_md_alone_is_not_touched_and_a_note_is_printed(project: Path):
    local = project / "CLAUDE.local.md"
    local.write_text("# Personal\n")

    result = run(project, "install")
    check = run(project, "install", "--check")

    assert result.returncode == 0, result.stderr
    assert local.read_text() == "# Personal\n"
    assert not (project / "CLAUDE.md").exists()
    for out in (result.stdout, check.stdout):
        assert "note: CLAUDE.local.md stops Claude Code from reading AGENTS.md" in out
        assert "claude-md-and-agents-md" in out
    assert check.returncode == 0
    run(project, "install", "--uninstall")
    assert local.read_text() == "# Personal\n"


def test_claude_md_import_creates_claude_md_and_uninstall_removes_it(project: Path):
    settings_file(project, 'claude_md = "import"\n')

    result = run(project, "install")

    assert result.returncode == 0, result.stderr
    assert (project / "CLAUDE.md").read_text() == import_block()
    assert run(project, "install", "--check").returncode == 0
    run(project, "install", "--uninstall")
    assert not (project / "CLAUDE.md").exists()
    assert not (project / "AGENTS.md").exists()


def test_claude_md_import_uses_an_existing_dot_claude_claude_md(project: Path):
    settings_file(project, 'claude_md = "import"\n')
    (project / ".claude").mkdir()
    (project / ".claude" / "CLAUDE.md").write_text("# Mine\n")

    run(project, "install")

    assert "@../AGENTS.md" in (project / ".claude" / "CLAUDE.md").read_text()
    assert not (project / "CLAUDE.md").exists()


def test_claude_md_none_leaves_claude_md_alone(project: Path):
    settings_file(project, 'claude_md = "none"\n')
    (project / "CLAUDE.md").write_text("# Mine\n")

    result = run(project, "install")
    check = run(project, "install", "--check")

    assert result.returncode == 0, result.stderr
    assert (project / "CLAUDE.md").read_text() == "# Mine\n"
    assert "## Delegation" in (project / "AGENTS.md").read_text()
    assert check.returncode == 0
    assert "note: CLAUDE.md stops Claude Code from reading AGENTS.md" in check.stdout
    run(project, "install", "--uninstall")
    assert (project / "CLAUDE.md").read_text() == "# Mine\n"


def test_switching_to_none_keeps_the_import_and_uninstall_still_removes_it(project: Path):
    (project / "CLAUDE.md").write_text("# Mine\n")
    run(project, "install")
    set_config(project, 'claude_md = "auto"', 'claude_md = "none"')

    assert run(project, "install", "--check").returncode == 0
    run(project, "install", "--uninstall")

    assert (project / "CLAUDE.md").read_text() == "# Mine\n"


def test_claude_md_listed_in_instructions_gets_the_full_block(project: Path):
    settings_file(project, 'instructions = ["AGENTS.md", "CLAUDE.md"]\n')
    (project / "CLAUDE.md").write_text("# Mine\n")

    run(project, "install")

    claude = (project / "CLAUDE.md").read_text()
    assert claude.count("routewise:start") == 1
    assert "## Delegation" in claude
    assert "@AGENTS.md" not in claude


@pytest.mark.parametrize("name", ["CLAUDE.md", ".claude/CLAUDE.md", "CLAUDE.local.md"])
def test_a_claude_file_above_the_project_is_warned_about(project: Path, tmp_path: Path, name: str):
    above = tmp_path / name
    above.parent.mkdir(exist_ok=True)
    above.write_text("# Parent\n")

    result = run(project, "install")
    check = run(project, "install", "--check")

    assert result.returncode == 0, result.stderr
    for out in (result.stdout, check.stdout):
        assert f"warning: {above} " in out
        assert 'claude_md = "import"' in out
    assert above.read_text() == "# Parent\n"
    assert check.returncode == 0

    set_config(project, 'claude_md = "auto"', 'claude_md = "import"')
    imported = run(project, "install")
    assert "warning:" not in imported.stdout
    assert above.read_text() == "# Parent\n"
    run(project, "install", "--uninstall")
    assert not (project / "CLAUDE.md").exists()


# --- S9: the project holds routewise directly, or is it (routewise on its own repo) ---------


def test_installs_on_the_routewise_folder_itself(project: Path):
    home = project / "routewise"

    result = run(project, "install", "--project", str(home))

    assert result.returncode == 0, result.stderr
    assert "`bin/miss-log --project . add --mode dev" in (home / "AGENTS.md").read_text()
    assert sorted(p.name for p in (home / ".claude" / "agents").iterdir()) == ROLES
    marker = (home / ".claude" / "agents" / "explore.md").read_text().splitlines()[1]
    assert marker.startswith("# generated by routewise from roles/explore.md;")
    assert "](spec/SPEC-model-routing.md)" in (home / "ROUTING-BINDING.md").read_text()
    assert (home / "logs" / "delegation-misses.jsonl").exists()
    assert not (project / "AGENTS.md").exists() and not (project / ".claude").exists()

    again = run(project, "install", "--project", str(home))
    assert again.stdout.strip() == "routewise: nothing to change"
    assert run(project, "install", "--project", str(home), "--check").returncode == 0

    run(project, "install", "--project", str(home), "--uninstall")
    assert list((home / ".claude" / "agents").iterdir()) == []
    assert not (home / "AGENTS.md").exists()


def test_miss_log_works_on_the_routewise_folder_itself(project: Path):
    home = project / "routewise"
    run(project, "install", "--project", str(home))

    add = run(
        project, "bin/miss-log", "--project", str(home),
        "add", "--mode", "dev", "--role", "reviewer", "--task", "review", "--what", "missed a case",
    )  # fmt: skip
    report = run(project, "bin/miss-log", "--project", str(home), "report")

    assert add.returncode == 0, add.stderr
    assert "misses: 1" in report.stdout
    assert (home / "logs" / "delegation-misses.jsonl").read_text().count("\n") == 1


def test_self_install_miss_log_command_runs_as_written(project: Path):
    """R10: the block's command, typed from the repo root, writes the repo's own log."""
    home = project / "routewise"
    run(project, "install", "--project", str(home))
    line = next(x for x in (home / "AGENTS.md").read_text().splitlines() if "--mode dev" in x)
    command = line.split("`")[1].replace("--role R --task T --what W", "")
    command += "--role reviewer --task review --what 'missed a case'"

    result = subprocess.run(
        ["bash", "-c", command], capture_output=True, text=True, check=False, cwd=home
    )

    assert result.returncode == 0, result.stderr
    assert (home / "logs" / "delegation-misses.jsonl").read_text().count("\n") == 1
    assert not (project / "logs").exists()
    binding = (home / "ROUTING-BINDING.md").read_text()
    assert "`bin/miss-log --project . add`" in binding
    assert "`bin/miss-log --project . report`" in binding


def test_a_folder_above_the_project_is_refused(project: Path, tmp_path: Path):
    before = sorted(p.name for p in tmp_path.iterdir())

    result = run(project, "install", "--project", str(tmp_path))
    log = run(project, "bin/miss-log", "--project", str(tmp_path), "report")

    assert (result.returncode, log.returncode) == (2, 2)
    assert "copy routewise/ into the project first" in result.stderr
    assert sorted(p.name for p in tmp_path.iterdir()) == before


# --- S9 / R12: a vendored copy never installs into a routewise repo -------------------------

REPO_MARKERS = ("install", "lib/install.py", "roles", "harness.toml")
REFUSED = (
    "is a routewise repo, so {name}/ inside it is not its installer; run ./install --project ."
)


def make_repo(project: Path, self_install: bool = True) -> Path:
    """Turn the fixture's project root into a routewise repo holding a release in routewise/."""
    copy = project / "routewise"
    for name in COPY:
        source = copy / name
        if source.is_dir():
            shutil.copytree(source, project / name)
        else:
            shutil.copy2(source, project / name)
    if self_install:
        own = own_install(project)
        assert own.returncode == 0, own.stderr
    return project


def own_install(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(repo / "install"), "--project", ".", *args],
        capture_output=True,
        text=True,
        check=False,
        cwd=repo,
    )


def snapshot(root: Path) -> dict[str, bytes]:
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file() and not p.is_symlink()
    }


@pytest.mark.parametrize(
    "args",
    [(), ("--project", "."), ("--check",), ("--uninstall",)],
    ids=["default", "explicit-project", "check", "uninstall"],
)
def test_a_vendored_copy_refuses_a_routewise_repo(project: Path, args: tuple[str, ...]):
    repo = make_repo(project)
    before = snapshot(repo)
    if args[:1] == ("--project",):
        args = ("--project", str(repo))

    result = run(repo, "install", *args)

    assert result.returncode == 2, result.stdout
    assert result.stderr.startswith(f"routewise: {repo} ")
    assert REFUSED.format(name="routewise") in result.stderr
    assert snapshot(repo) == before


def test_a_refused_first_run_in_a_routewise_repo_writes_nothing(project: Path):
    repo = make_repo(project, self_install=False)
    before = snapshot(repo)

    result = run(repo, "install")

    assert result.returncode == 2
    assert snapshot(repo) == before
    for name in ("routewise.toml", "ROUTING-BINDING.md", "AGENTS.md", "logs"):
        assert not (repo / name).exists()


def test_a_symlinked_copy_is_refused_in_a_routewise_repo(project: Path, tmp_path: Path):
    repo = make_repo(project)
    release = tmp_path / "release"
    (repo / "routewise").rename(release)
    (repo / "routewise").symlink_to(release)
    before = snapshot(repo)

    result = run(repo, "install")

    assert result.returncode == 2
    assert REFUSED.format(name="routewise") in result.stderr
    assert snapshot(repo) == before


@pytest.mark.parametrize("spelling", ["{repo}/", "{repo}/routewise/..", "routewise/.."])
def test_other_spellings_of_the_repo_are_refused(project: Path, spelling: str):
    repo = make_repo(project)
    before = snapshot(repo)

    result = run(repo, "install", "--project", spelling.format(repo=repo))

    assert result.returncode == 2
    assert REFUSED.format(name="routewise") in result.stderr
    assert snapshot(repo) == before


def test_a_repo_reached_through_a_symlink_is_refused(project: Path, tmp_path: Path):
    repo = make_repo(project)
    link = tmp_path / "link"
    link.symlink_to(repo)
    before = snapshot(repo)

    result = run(link, "install")

    assert result.returncode == 2
    assert REFUSED.format(name="routewise") in result.stderr
    assert snapshot(repo) == before


def test_the_message_names_the_copy_as_it_is_called(project: Path):
    repo = make_repo(project)
    (repo / "routewise").rename(repo / "rw-0.2.1")

    result = subprocess.run(
        [str(repo / "rw-0.2.1" / "install")], capture_output=True, text=True, check=False, cwd=repo
    )

    assert result.returncode == 2
    assert REFUSED.format(name="rw-0.2.1") in result.stderr
    assert "delete rw-0.2.1/ if a download put it there" in result.stderr


@pytest.mark.parametrize("missing", REPO_MARKERS)
def test_a_root_missing_one_marker_is_an_ordinary_project(project: Path, missing: str):
    repo = make_repo(project, self_install=False)
    target = repo / missing
    if target.is_dir():
        shutil.rmtree(target)
    else:
        target.unlink()

    result = run(repo, "install")

    assert result.returncode == 0, result.stderr
    assert "`routewise/bin/miss-log add" in (repo / "AGENTS.md").read_text()


def test_a_routewise_repo_still_installs_on_itself_and_its_copy(project: Path):
    repo = make_repo(project)

    again = own_install(repo, "--check")
    copy = run(repo, "install", "--project", str(repo / "routewise"))

    assert again.returncode == 0, again.stdout + again.stderr
    assert copy.returncode == 0, copy.stderr
    assert (repo / "routewise" / "AGENTS.md").exists()


def test_a_vendored_miss_log_still_writes_the_repo_log(project: Path):
    repo = make_repo(project)

    add = run(
        repo, "bin/miss-log",
        "add", "--mode", "dev", "--role", "reviewer", "--task", "review", "--what", "missed a case",
    )  # fmt: skip

    assert add.returncode == 0, add.stderr
    assert (repo / "logs" / "delegation-misses.jsonl").read_text().count("\n") == 1


# --- R3: commands spelled for the project ---------------------------------------------------

OWN = "./install --project ."


def agent_marker(folder: Path) -> str:
    return (folder / ".claude" / "agents" / "explore.md").read_text().splitlines()[1]


def test_vendored_markers_name_routewise_install(project: Path):
    run(project, "install")

    assert agent_marker(project).endswith("; edit that file and re-run routewise/install")
    assert (project / "AGENTS.md").read_text().startswith(START + "\n")


def test_self_install_markers_name_its_own_command(project: Path):
    home = project / "routewise"

    run(project, "install", "--project", str(home))

    assert agent_marker(home).endswith(f"; edit that file and re-run {OWN}")
    text = (home / "AGENTS.md").read_text()
    assert text.startswith(START.replace("routewise/install", OWN) + "\n")
    assert "routewise/install" not in text


def test_old_marker_text_is_recognised_and_rewritten_once(project: Path):
    home = project / "routewise"
    run(project, "install", "--project", str(home))
    old = {}
    for path in [home / "AGENTS.md", *(home / ".claude" / "agents").iterdir()]:
        old[path] = path.read_text()
        path.write_text(old[path].replace(OWN, "routewise/install"))

    result = run(project, "install", "--project", str(home))

    assert result.returncode == 0, result.stderr
    assert all(path.read_text() == text for path, text in old.items())
    assert run(project, "install", "--project", str(home), "--check").returncode == 0


def test_binding_paths_are_spelled_from_the_project_root(project: Path):
    home = project / "routewise"
    run(project, "install")
    run(project, "install", "--project", str(home))

    vendored = (project / "ROUTING-BINDING.md").read_text()
    own = (home / "ROUTING-BINDING.md").read_text()

    for text in (vendored, own):
        assert "{{" not in text
    assert "Generated by `routewise/install` from `routewise/roles/`" in vendored
    assert "`routewise/harness.toml`, with overrides" in vendored
    assert "written only by `routewise/bin/miss-log add`" in vendored
    assert f"Generated by `{OWN}` from `roles/`" in own
    assert "`harness.toml`, with overrides" in own
    assert (
        "written only by `bin/miss-log --project . add`; `bin/miss-log --project . report`" in own
    )
    assert "routewise/" not in own


def test_settings_name_the_projects_own_install_command(project: Path):
    home = project / "routewise"
    run(project, "install")
    run(project, "install", "--project", str(home))

    assert "re-run `routewise/install`" in (project / "routewise.toml").read_text()
    own = (home / "routewise.toml").read_text()
    assert f"re-run `{OWN}`" in own
    assert "routewise/" not in own


# --- review findings (2026-11-14) -----------------------------------------------------------


def test_the_home_folder_is_never_a_project(project: Path):
    (project / ".claude").mkdir()
    personal = project / ".claude" / "CLAUDE.md"
    personal.write_text("# my personal rules\n")
    before = sorted(str(p) for p in project.rglob("*") if "routewise" not in p.parts)

    # routewise unpacked straight into the home folder: ~/routewise/install
    result = run(project, "install", home=project)
    log = run(project, "bin/miss-log", "report", home=project)
    above = run(project, "install", "--project", str(project), home=project / "routewise")

    assert (result.returncode, log.returncode, above.returncode) == (2, 2, 2)
    assert "is your home folder" in result.stderr
    assert personal.read_text() == "# my personal rules\n"
    assert sorted(str(p) for p in project.rglob("*") if "routewise" not in p.parts) == before


def test_self_install_through_a_symlinked_routewise_is_refused(project: Path, tmp_path: Path):
    shared = project / "routewise"  # a copy that several projects link to
    other = tmp_path / "other"
    other.mkdir()
    (other / "routewise").symlink_to(shared)
    before = sorted(p.name for p in shared.iterdir())

    result = run(other, "install", "--project", str(other / "routewise"))

    assert result.returncode == 2
    assert "is a symlink" in result.stderr
    assert sorted(p.name for p in shared.iterdir()) == before
    assert run(other, "install").returncode == 0  # installing into `other` itself still works


@pytest.mark.parametrize("name", ["rw-->x", "rw\npermissionMode: x"])
def test_a_routewise_folder_name_that_breaks_markers_is_refused(
    project: Path, tmp_path: Path, name: str
):
    host = tmp_path / "host"
    host.mkdir()
    (project / "routewise").rename(host / name)

    result = subprocess.run(
        [str(host / name / "install")], capture_output=True, text=True, check=False, cwd=host
    )

    assert result.returncode == 2
    assert "cannot be written into the markers" in result.stderr
    assert sorted(p.name for p in host.iterdir()) == [name]


def test_shipped_skills_reach_the_agent_and_settings_replace_them(project: Path):
    """R8: [skills] replaces a role's own list; [] removes the line; other roles keep theirs."""
    run(project, "install")
    agents = project / ".claude" / "agents"
    shipped = front(agents / "auditor.md")
    set_config(project, "[skills]\n", '[skills]\nreviewer = ["my-review"]\nexplore = []\n')

    result = run(project, "install")

    assert result.returncode == 0, result.stderr
    assert "skills: my-review\n" in front(agents / "reviewer.md")
    assert "Skills listed for you: `my-review`." in (agents / "reviewer.md").read_text()
    assert "`Checklist: my-review <loaded or missing>`" in (agents / "reviewer.md").read_text()
    set_config(project, 'reviewer = ["my-review"]', "reviewer = []")
    run(project, "install")
    assert "- First line: `Checklist: none`." in (agents / "reviewer.md").read_text()
    assert "skills:" not in front(agents / "explore.md")
    assert front(agents / "auditor.md") == shipped


def test_skills_for_an_unknown_role_stop_the_run(project: Path):
    run(project, "install")
    before = (project / ".claude" / "agents" / "reviewer.md").read_text()
    set_config(project, "[skills]\n", '[skills]\nreveiwer = ["my-review"]\n')

    result = run(project, "install")

    assert result.returncode == 2
    assert "routewise: routewise.toml: [skills] reveiwer is not a role" in result.stderr
    assert (project / ".claude" / "agents" / "reviewer.md").read_text() == before


def test_dev_block_runs_mutation_suggestions_and_reports_a_missing_checklist(project: Path):
    """R8: the main session runs reviewer's mutation suggestions and says when no skill loaded."""
    run(project, "install")
    dev = (project / "AGENTS.md").read_text()
    set_config(project, 'fragment = "dev"', 'fragment = "assistant"')
    run(project, "install")
    assistant = (project / "AGENTS.md").read_text()

    for rule in ("mutation suggestions", "as `missing`"):
        assert rule in dev
        assert rule not in assistant


STAND_INS = '[stand_ins]\nreviewer = ["code-reviewer"]\nauditor = ["security-auditor"]\n'


def with_stand_ins(project: Path, harnesses: str = '["cc"]') -> None:
    run(project, "install")
    set_config(project, "[stand_ins]\n", STAND_INS)
    set_config(project, 'harnesses = ["cc"]', f"harnesses = {harnesses}")


def test_stand_ins_render_the_role_under_the_plugin_name(project: Path):
    """R9: a stand-in equals its role's agent but for marker, name and description."""
    with_stand_ins(project, '["cc", "agy"]')

    result = run(project, "install")

    assert result.returncode == 0, result.stderr
    for folder in (project / ".claude" / "agents", project / ".agents" / "agents"):
        names = sorted(p.name for p in folder.iterdir())
        assert names == sorted([*ROLES, "code-reviewer.md", "security-auditor.md"])
        own, stand_in = (
            (folder / "reviewer.md").read_text(),
            (folder / "code-reviewer.md").read_text(),
        )
        assert stand_in.split("---\n", 2)[2] == own.split("---\n", 2)[2]
        assert "name: code-reviewer" in front(folder / "code-reviewer.md")
    assert run(project, "install").stdout.strip() == "routewise: nothing to change"


def test_stand_ins_drift_removal_and_uninstall(project: Path):
    with_stand_ins(project)
    run(project, "install")
    agents = project / ".claude" / "agents"
    (agents / "code-reviewer.md").write_text((agents / "code-reviewer.md").read_text() + "x\n")

    assert run(project, "install", "--check").returncode == 1
    set_config(project, 'auditor = ["security-auditor"]\n', "")
    run(project, "install")
    assert not (agents / "security-auditor.md").exists()
    assert (agents / "code-reviewer.md").read_text().endswith("approve or request changes.\n")

    run(project, "install", "--uninstall")
    assert not (agents / "code-reviewer.md").exists()


def test_a_users_own_agent_of_that_name_stops_the_run(project: Path):
    with_stand_ins(project)
    mine = project / ".claude" / "agents" / "code-reviewer.md"
    mine.write_text("---\nname: code-reviewer\n---\nMine\n")

    result = run(project, "install")

    assert result.returncode == 2
    assert "code-reviewer.md exists and was not written by routewise" in result.stderr
    assert mine.read_text() == "---\nname: code-reviewer\n---\nMine\n"
    assert not (project / ".claude" / "agents" / "security-auditor.md").exists()


@pytest.mark.parametrize(
    ("table", "message"),
    [
        ('reveiwer = ["code-reviewer"]', "[stand_ins] reveiwer is not a role"),
        ('reviewer = ["auditor"]', "stand-in name 'auditor' is a role"),
        ('reviewer = ["explore"]', "stand-in name 'explore' is a role"),
    ],
)
def test_bad_stand_ins_stop_the_run(project: Path, table: str, message: str):
    run(project, "install")
    set_config(project, "[stand_ins]\n", f"[stand_ins]\n{table}\n")

    before = {
        p: p.read_bytes()
        for p in project.rglob("*")
        if p.is_file() and "routewise" not in p.relative_to(project).parts
    }

    result = run(project, "install")

    assert result.returncode == 2
    assert message in result.stderr
    after = {
        p: p.read_bytes()
        for p in project.rglob("*")
        if p.is_file() and "routewise" not in p.relative_to(project).parts
    }
    assert after == before  # S2: a refused setting writes nothing


def test_block_names_stand_ins_only_when_set(project: Path):
    """R9: the session starts the project's stand-in, never the plugin agent of that name."""
    run(project, "install")
    plain = (project / "AGENTS.md").read_text()
    with_stand_ins(project)

    run(project, "install")
    block = (project / "AGENTS.md").read_text()

    assert "{{" not in plain and "stand-in" not in plain
    line = next(x for x in block.splitlines() if "stand-in" in x)
    assert "`code-reviewer` (for `reviewer`)" in line
    assert "`security-auditor` (for `auditor`)" in line
    assert "`<plugin>:code-reviewer`" in line and "/ship" in line
    assert "agent-skills" not in line  # the setting is not tied to one plugin
    assert block.replace(line + "\n", "") == plain


def test_a_stand_in_cannot_take_a_roles_agent_name(project: Path):
    """R9: a role whose agent name differs from its file name keeps that name to itself."""
    roles = project / "routewise" / "roles"
    text = (roles / "reviewer.md").read_text().replace("name: reviewer", "name: Deep-Check")
    (roles / "deep.md").write_text(text)
    run(project, "install")
    set_config(project, "[stand_ins]\n", '[stand_ins]\nreviewer = ["deep-check"]\n')

    result = run(project, "install")

    assert result.returncode == 2
    assert "stand-in name 'deep-check' is a role" in result.stderr


def test_no_placeholder_is_left_in_any_agent(project: Path):
    """A misspelled placeholder in a role would ship as literal text; drift checks cannot see it."""
    run(project, "install")
    set_config(project, "[stand_ins]\n", '[stand_ins]\nreviewer = ["code-reviewer"]\n')
    set_config(project, 'harnesses = ["cc"]', 'harnesses = ["cc", "agy"]')
    run(project, "install")

    folders = (project / ".claude" / "agents", project / ".agents" / "agents")
    for agent in [path for folder in folders for path in folder.iterdir()]:
        assert "{{" not in agent.read_text(), agent.name


JUDGE_BLOCK = (
    "Start `judge` only when the person asks for one on a decision",
    "but not the one you favour",
    "then wait",
    "run it again with the same brief",
    "never the person's choice or approval",
)


def test_both_blocks_start_the_judge_only_when_the_person_asks(project: Path):
    """R13: the same rule in the dev and the assistant block; never started on its own."""
    run(project, "install")
    dev = (project / "AGENTS.md").read_text()
    set_config(project, 'fragment = "dev"', 'fragment = "assistant"')
    run(project, "install")
    assistant = (project / "AGENTS.md").read_text()

    for rule in JUDGE_BLOCK:
        assert rule in dev, rule
        assert rule in assistant, rule
    for quoted in ("quoted with its source and author", "take exact values from the source again"):
        assert quoted in assistant, quoted
        assert quoted not in dev, quoted
    assert "Only two things may go to a subagent: reading a public web page" in assistant
    for kept in ("reading messages, mail or documents", "drafts, sends, memory writes"):
        assert kept in assistant, kept


def test_the_rules_spec_fragment_matches_the_dev_judge_rule():
    rules = (HOME / "spec" / "SPEC-model-routing.md").read_text()
    dev = (HOME / "templates" / "fragment-dev.md").read_text()
    line = next(x for x in dev.splitlines() if x.startswith("- Start `judge`"))

    assert line in rules


def test_a_new_binding_records_the_judge(project: Path):
    """R13: the judge's frontier tier is approved by adopting rules spec version 4 (section 12)."""
    run(project, "install")
    binding = (project / "ROUTING-BINDING.md").read_text()

    row = next(x for x in binding.splitlines() if x.startswith("| `judge` |"))
    assert "`frontier` at `medium` (R-A7)" in row
    assert "only when the person asks" in row
