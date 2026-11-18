# Tasks: a vendored copy refuses to install into the routewise repo (R12), release 0.2.1

Plan: [plan.md](plan.md). Spec: [SPEC.md](../SPEC.md), R12, S9, criterion 17. `make check` green before each commit (the pre-commit hook enforces it). Each task: failing test first, shown red; then the code; a `CHANGELOG.md` line under `## Unreleased` for each user-visible change; one Conventional Commit.

## Task 1: installer refuses a vendored install into a routewise repo

**Description:** A new check in `lib/paths.py`, called by `lib/install.py` `run` after `holds` and before `build_plan`: when `root == home.parent` and the root holds `install` (file), `lib/install.py`, `roles/` (folder) and `harness.toml`, raise `PathError` with the R12 message, the copy named by `label(home, root)`.

**Acceptance criteria (tests under the S9 heading in `tests/test_install.py`, on a repo-shaped root with a self-install done first):**
- [x] `routewise/install` (default project), `routewise/install --project <root>`, `--check` and `--uninstall` each exit 2; stderr is the R12 message naming `./install --project .`; every file under the root is byte-identical afterwards.
- [x] On a repo-shaped root with no self-install, the refusal creates no `routewise.toml`, `ROUTING-BINDING.md` or miss log.
- [x] A copy reached through a symlink (`routewise -> ../release`) is refused the same way; a copy in a folder named other than `routewise` is named by that name in the message.
- [x] With any one of the four paths removed (parametrised), the vendored install runs and exits 0.
- [x] `./install --project .` on the root and `routewise/install --project routewise` still exit 0.
- [x] `routewise/bin/miss-log add …` from the root still appends one line to the root's log.
- [x] Existing vendored-install tests unchanged and green.
- [x] `CHANGELOG.md` `## Unreleased`: one line, including that a refused update leaves the unpacked folder to delete.

**Verification:** `uv run pytest tests/test_install.py -k "S9 or routewise_repo"`; tests shown red before the code; `make check`.

**Dependencies:** none. **Files:** `lib/paths.py`, `lib/install.py`, `tests/test_install.py`, `CHANGELOG.md`. **Scope:** M.

## Task 2: docs: README "Safety", `AGENTS.md` S1–S9

**Description:** README "Safety" (the `--project` bullet) states that a folder which is itself a routewise repo is refused and names `./install --project .`. `AGENTS.md` names the safety rules S1–S9 in its intro and "Keep the safety rules" (hand-edited text, outside the generated block).

**Acceptance criteria:**
- [x] README's `--project` bullet no longer says the holding folder is always accepted.
- [x] `grep -n "S1–S8" AGENTS.md README.md SPEC.md` finds nothing outside history records.
- [x] `make self` reports nothing to change (the generated block is untouched).

**Verification:** `make check`.

**Dependencies:** Task 1. **Files:** `README.md`, `AGENTS.md`. **Scope:** XS.

## Checkpoint A: review (after Task 2)

- [x] `make check` green on the whole change.
- [x] `reviewer` on the R12 commits, `auditor` on S9 and the check; Critical and Required fixed (one more round scoped to a fix), Optional and Nit answered in this file; mutation suggestions run and recorded.

**Review record (round 1, 2026-11-17).** `reviewer` (Checklist: `agent-skills:code-review-and-quality` loaded) approve; `auditor` (Checklist: `agent-skills:security-and-hardening` loaded) no Critical or Required. Round ends here (stopping rule).

- Mutations run: (1) drop `root != home.parent` → killed (`…installs_on_itself_and_its_copy`); (2) `and` → `or` in `is_repo` → killed (`…missing_one_marker…`); (3) the check moved after `build_plan` → survives, as predicted: planning only builds the plan in memory and the first write is in `apply`, so S2 holds either way; kept as is (informational).
- auditor Optional 1 (no test for a symlinked root or other `--project` spellings): fixed, tests for `<repo>/`, `<repo>/routewise/..`, relative `routewise/..` and a root reached through a symlink.
- auditor Optional 2 (only copies from 0.2.1 on carry the check; a pinned `v=0.2.0` still does the damage): answered in the 0.2.1 release notes (Task 3).
- auditor Nit 3 (message tells an unrelated project with all four files to run its `./install`): kept; the wording is R12's, and SPEC.md names the one known match.
- auditor Nit 4 (folder name printed before `plain_name`): kept; `holds` already prints it, and the user names the folder.
- auditor Nit 5 (a fresh clone's nested `miss-log` creates the default log): kept; it stays inside the project, as R12's miss-log decision says.
- reviewer Nit 1 (README line 125 too long): fixed, the repo case is its own bullet.
- reviewer Nit 2 (snapshot ignores empty folders): kept; nothing is created before planning, and the first-run test checks `logs` by name.
- reviewer Nit 3 (no `s9_` test name): kept; the section header names S9 / R12, as the other S9 tests are grouped.
- reviewer Nit 4 (`not_a_repo` naming): kept; it reads as the rule it enforces, like `holds`.

## Task 3: Ship 0.2.1

**Description:** Version `0.2.1` in `pyproject.toml` and every README `v=`; `## Unreleased` becomes `## 0.2.1 (<date>)`; `tasks/release-0.2.1.md` drafted for users (what changed, how to update) and checked by `reviewer` against the code; `git archive HEAD` holds only R1's runtime files; annotated tag `v0.2.1` when the maintainer asks; publish commands from `AGENTS.md` handed over filled in.

**Acceptance criteria:**
- [x] `make check` green (R4's version test passes with `0.2.1`).
- [x] Release notes reviewed; archive contents checked.
- [x] Tag created only on request; publish steps given.

**Ship record (2026-11-17).** Released as `7b86e65`; `git archive HEAD` holds only R1's runtime files (`ADOPT.md CHANGELOG.md LICENSE README.md bin harness.toml install lib roles spec templates`); roles, templates, `harness.toml`, `bin` unchanged since v0.2.0. `reviewer` (Checklist: `agent-skills:code-review-and-quality` loaded) approved the release notes and changelog against the code, no Critical or Required. Optional 1 ("prints nothing to change" only when in step) fixed; Optional 3 (changelog lacks "since 0.1.0") fixed; Optional 2 ("no new session needed" unbacked) kept with its reason (agents and block unchanged); Nit (non-maintainers can ignore) answered by the opening paragraph. Tag `v0.2.1` on request.

**Verification:** `make check`; `git archive HEAD | tar -t`.

**Dependencies:** Checkpoint A. **Files:** `pyproject.toml`, `README.md`, `CHANGELOG.md`, `tasks/release-0.2.1.md`. **Scope:** S.
