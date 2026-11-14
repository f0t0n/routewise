"""routewise/bin/miss-log on a throwaway project."""

import json
from pathlib import Path

from conftest import run

ADD = ("bin/miss-log", "add", "--mode", "dev", "--task", "review")


def lines(path: Path) -> list[dict[str, str]]:
    return [json.loads(line) for line in path.read_text().splitlines()]


def test_add_stamps_time_and_reads_tier_and_effort(project: Path):
    result = run(project, *ADD, "--role", "Reviewer", "--what", "missed a None check")

    assert result.returncode == 0, result.stderr
    [record] = lines(project / "logs" / "delegation-misses.jsonl")
    assert record["role"] == "reviewer"
    assert record["tier"] == "balanced"
    assert record["effort"] == "medium"
    assert record["at"].endswith("Z")
    assert record["what"] == "missed a None check"


def test_role_without_effort_records_default(project: Path):
    run(project, *ADD, "--role", "explore", "--what", "wrong path")

    [record] = lines(project / "logs" / "delegation-misses.jsonl")
    assert (record["role"], record["tier"], record["effort"]) == ("Explore", "fast", "default")


def test_uses_the_log_named_in_settings(project: Path):
    (project / "routewise.toml").write_text('miss_log = "var/misses.jsonl"\n')

    run(project, *ADD, "--role", "auditor", "--what", "missed a leaked token")

    assert len(lines(project / "var" / "misses.jsonl")) == 1


def test_refuses_private_data_and_unknown_roles(project: Path):
    url = run(project, *ADD, "--role", "reviewer", "--what", "see https://example.com/x")
    mail = run(project, *ADD, "--role", "reviewer", "--what", "ask someone@example.com")
    role = run(project, *ADD, "--role", "planner", "--what", "x")

    assert (url.returncode, mail.returncode, role.returncode) == (2, 2, 2)
    assert "holds a URL" in url.stderr
    assert "holds an e-mail address" in mail.stderr
    assert "unknown role 'planner'" in role.stderr
    assert not (project / "logs" / "delegation-misses.jsonl").exists()


def test_refuses_a_dotless_address_and_a_link_without_a_scheme(project: Path):
    """Both got into the committed log in 0.1.0 (R5); a file path still goes in."""
    log = project / "logs" / "delegation-misses.jsonl"
    mail = run(project, *ADD, "--role", "reviewer", "--what", "mailed me@localhost")
    url = run(project, *ADD, "--role", "reviewer", "--what", "see jira.corp.net/browse/X-1")
    assert (mail.returncode, url.returncode) == (2, 2)
    assert "holds an e-mail address" in mail.stderr
    assert "holds a URL" in url.stderr
    assert not log.exists()

    path = run(project, *ADD, "--role", "reviewer", "--what", "edited lib/privacy.py and src/a.ts/")

    assert path.returncode == 0, path.stderr
    assert [r["what"] for r in lines(log)] == ["edited lib/privacy.py and src/a.ts/"]


def test_errors_start_with_the_routewise_prefix(project: Path):
    """Like every routewise error (R6): a refused entry, and a log that cannot be read."""
    refused = run(project, *ADD, "--role", "reviewer", "--what", "ask someone@example.com")
    (project / "logs" / "delegation-misses.jsonl").mkdir(parents=True)
    unreadable = run(project, "bin/miss-log", "report")

    assert (refused.returncode, unreadable.returncode) == (2, 2)
    assert refused.stderr.startswith("routewise: what holds an e-mail address"), refused.stderr
    assert unreadable.stderr.startswith("routewise: cannot read or write a file"), unreadable.stderr


def test_report_counts_by_role_tier_and_effort(project: Path):
    run(project, *ADD, "--role", "reviewer", "--what", "one")
    run(project, *ADD, "--role", "reviewer", "--what", "two")
    run(project, *ADD, "--role", "explore", "--what", "three")

    result = run(project, "bin/miss-log", "report")

    assert result.stdout.splitlines() == [
        "misses: 3",
        "by role: reviewer 2, Explore 1",
        "by tier: balanced 2, fast 1",
        "by effort: medium 2, default 1",
    ]


def test_report_refuses_a_line_that_is_not_an_object(project: Path):
    log = project / "logs" / "delegation-misses.jsonl"
    log.parent.mkdir()
    log.write_text("[1]\n")

    result = run(project, "bin/miss-log", "report")

    assert result.returncode == 2
    assert "line 1 is not a JSON object" in result.stderr


def test_the_log_must_not_be_a_symlink(project: Path, tmp_path: Path):
    (project / "logs").mkdir()
    target = project / "logs" / "real.jsonl"
    target.write_text("")
    (project / "logs" / "delegation-misses.jsonl").symlink_to(target)

    result = run(project, *ADD, "--role", "reviewer", "--what", "one")

    assert result.returncode == 2
    assert target.read_text() == ""
