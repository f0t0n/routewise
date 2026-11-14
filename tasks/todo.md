# Tasks: release archive (R1), routewise on its own repo (R2), workflow docs

Plan: [plan.md](plan.md). Spec: [SPEC.md](../SPEC.md). One Conventional Commit per task; `make check` green before each commit (the pre-commit hook enforces it). Tick a box in the same commit that completes it.

## Task 0: Commit the approved spec, agent instructions and plan

**Description:** Put the Define and Plan outputs under version control before any code changes, so every later commit traces to them.

**Acceptance criteria:**
- [x] `SPEC.md` (status approved, the `--project .` correction), `AGENTS.md` (guard, workflow, commands) and `tasks/plan.md`, `tasks/todo.md` are committed together.

**Verification:**
- [x] `make check` green (via the pre-commit hook)
- [x] `git show --stat HEAD` lists exactly those four files

**Dependencies:** None
**Files:** `SPEC.md`, `AGENTS.md`, `tasks/plan.md`, `tasks/todo.md`
**Scope:** XS. Commit: `docs: add the tool spec, agent workflow and first plan`

## Task 1: Record the `@AGENTS.md` live check in rules spec section 13

**Description:** Add a dated subsection under the 2.1.325 entry in `spec/SPEC-model-routing.md` section 13 with the five probes of 2026-11-14 (SPEC.md decision 3). A record of a test: no rule or version line changes.

**Acceptance criteria:**
- [x] One table (Check | Probe | Result) with five rows: native read (`4`), plain `CLAUDE.md` hides `AGENTS.md` (`NONE`), root import block (`7`), `.claude/CLAUDE.md` with `@../AGENTS.md` (`8`), `.claude/CLAUDE.md` with plain `@AGENTS.md` (`NONE`, imports resolve from the file's folder); method: real `routewise/install` per probe, `claude -p --model haiku`, a different cap per probe.
- [x] The spec's version line is unchanged; `CHANGELOG.md` gets one line.

**Verification:**
- [x] `git diff` touches only section 13 and `CHANGELOG.md`
- [x] `make check` green

**Dependencies:** Task 0
**Files:** `spec/SPEC-model-routing.md`, `CHANGELOG.md`
**Scope:** XS. Commit: `docs(spec): record the live check of the AGENTS.md import`

## Checkpoint A
- [x] `make check` green; Tasks 0–1 committed

## Task 2: S9, accept the routewise folder itself as the project

**Description:** `paths.holds` accepts `root == home` as well as a root that holds routewise, for both `install` and `bin/miss-log`. Test first on a temporary copy, never on this repo.

**Acceptance criteria:**
- [x] `install --project <copy>/routewise` succeeds on a fresh copy: `AGENTS.md` there holds the block with `` `bin/miss-log add`` paths, five agents in `<copy>/routewise/.claude/agents/` carry `roles/<name>.md` markers, `ROUTING-BINDING.md` links `spec/SPEC-model-routing.md`; a second run prints `routewise: nothing to change`; `--check` exits 0; `--uninstall` removes agents and block.
- [x] `bin/miss-log --project <copy>/routewise add … ` and `report` work there.
- [x] An unrelated folder and the folder above the project are refused for both tools (existing test kept; the folder above was accepted before and is now refused, per S9).

**Verification:**
- [x] New tests fail before the change, pass after: `uv run pytest tests/test_install.py -k self`
- [x] `make check` green

**Dependencies:** Task 0
**Files:** `lib/paths.py`, `tests/test_install.py`, `README.md` (Safety: `--project`), `CHANGELOG.md`
**Scope:** S. Commit: `feat: let routewise install on its own folder`

## Task 3: Install routewise on this repo

**Description:** Add this repo's `routewise.toml` (plan's settings), a `self` and a `selfcheck` target in the Makefile (`selfcheck` in `check`), run `make self`, fill in `ROUTING-BINDING.md`, and tell agents how to keep it current.

**Acceptance criteria:**
- [x] `make self` writes `routewise.toml`-driven files only inside the repo: `.claude/agents/*.md` (5), `ROUTING-BINDING.md`, `logs/delegation-misses.jsonl`, and the delegation block appended to `AGENTS.md` (`bin/miss-log` paths); the folder above the repo is untouched.
- [x] `make check` runs `./install --project . --check`; editing a role without `make self` makes it fail (checked by hand, then reverted).
- [x] `ROUTING-BINDING.md` filled in (approver and review date confirmed at the plan gate); `AGENTS.md` "How to work here" says to run `make self` after changing roles, templates or `harness.toml`.

**Verification:**
- [x] `make check` green; `git status` shows only the files above
- [x] Manual: role edit → `make check` fails at `selfcheck` → revert → green

**Dependencies:** Task 2
**Files:** `Makefile`, `routewise.toml`, `ROUTING-BINDING.md`, `AGENTS.md`, `logs/delegation-misses.jsonl`, `.claude/agents/*.md` (generated)
**Scope:** M (six hand-touched files; the agents are generated). Commit: `build: run routewise on its own repo`

## Checkpoint B
- [x] `make check` green including `selfcheck`; Tasks 2–3 committed

## Task 4: Release archive: `export-ignore` and one list of runtime files

**Description:** `.gitattributes` marks every development file `export-ignore` (SPEC.md project structure: `SPEC.md`, `AGENTS.md`, `tasks/`, `tests/`, `Makefile`, `pyproject.toml`, `uv.lock`, `pyrightconfig.json`, `.githooks/`, `.gitignore`, `.gitattributes`, `routewise.toml`, `ROUTING-BINDING.md`, `.claude/`, `logs/`). A test ties the shipped set to the tested set. README recommends the archive.

**Acceptance criteria:**
- [ ] `tests/test_release.py`: top-level entries of `git ls-files` without `export-ignore` equal `conftest.COPY` plus `README.md`, `ADOPT.md`, `LICENSE`, `CHANGELOG.md`; skipped outside a git checkout. Fails before `.gitattributes` exists.
- [ ] README "Install into a project" step 1: download the release's "Source code" archive (or `git archive`) into `routewise/`; a submodule or subtree works but brings the development files. `ADOPT.md` step 1 unchanged in substance.
- [ ] `CHANGELOG.md` line for R1.

**Verification:**
- [ ] `uv run pytest tests/test_release.py` fails first, then passes
- [ ] `git archive --worktree-attributes HEAD | tar -t` (before commit) shows only runtime files
- [ ] `make check` green

**Dependencies:** Task 3 (so the self-install files exist and are covered)
**Files:** `.gitattributes`, `tests/test_release.py`, `tests/conftest.py` (export the shipped-docs list beside `COPY`), `README.md`, `CHANGELOG.md`
**Scope:** M. Commit: `build: ship only runtime files in release archives`

## Checkpoint C (end of Build)
- [ ] `make check` green; SPEC.md success criteria 1, 4, 5, 6 met

## Verify
- [ ] `make check` on the final tree
- [ ] `git archive HEAD | tar -t` lists exactly the R1 runtime files
- [ ] Extract that archive into a fresh project's `routewise/`, run `routewise/install`: success criterion 2 holds

## Review
- [ ] `reviewer` brief (role body, sonnet, medium) on `git diff <Task 0 commit>^..HEAD`
- [ ] `auditor` brief (role body, opus, high) on `lib/paths.py` (S9), `.gitattributes`, the Makefile targets
- [ ] Every Critical and Required finding fixed in its own commit, or answered

## Ship
- [ ] `CHANGELOG.md` covers R1, R2, S9 and the section 13 record
- [ ] Release archive contents confirmed again after review fixes
- [ ] Maintainer pushes from the host
