# Tasks: copy-paste install in the README (R4)

Plan: [plan.md](plan.md). Spec: [SPEC.md](../SPEC.md). `make check` green before each commit (the pre-commit hook enforces it).

## Task 1: README install block and the version test

**Description:** Test first: `tests/test_release.py` gains a test that the README's install block names the `pyproject.toml` version; it fails while the block does not exist. Then add the block at the top of "## Install into a project".

**Acceptance criteria:**
- [x] The test fails before the README change ("no `v=` line in the install block"), passes after, and fails if either version is changed alone (checked by hand, then reverted).
- [x] The README block matches the plan (`v=0.1.0`, curl, `tar -xz`, `mv "routewise-$v" routewise`, `routewise/install`) and the prose steps after it are unchanged.
- [x] `CHANGELOG.md` gets an entry under a new `## Unreleased` section.

**Verification:**
- [x] `uv run pytest tests/test_release.py` red, then green
- [x] `make check` green

Note: the block starts at `v=` with "From the project root:" above it, instead of the planned `cd your-project` line, so it runs as pasted (Verify runs it literally).

**Dependencies:** the spec change and this plan committed first
**Files:** `tests/test_release.py`, `README.md`, `CHANGELOG.md`, `tasks/todo.md`, `tasks/plan.md`
**Scope:** S. Commit: `docs: add a copy-paste install to the README`

## Checkpoint
- [x] `make check` green

## Verify
- [ ] The block copied out of `README.md` and run as a script in an empty git repo installs routewise 0.1.0 from GitHub: 9 files, a second run changes nothing, `--check` exits 0

## Review
- [ ] `reviewer` brief (role body, sonnet, medium) on the README diff and the test
- [ ] Findings fixed or answered

## Ship
- [ ] Maintainer pushes `main` from the host (no tag: the change ships in the next release)
