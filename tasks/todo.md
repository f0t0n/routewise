# Tasks: miss-log privacy fix, release 0.1.1 (R5)

Plan: [plan.md](plan.md). Spec: [SPEC.md](../SPEC.md). `make check` green before each commit (the pre-commit hook enforces it). Tick a box in the commit that records the task.

## Task 1: Prove the new tests fail first

**Description:** Run today's `tests/test_privacy.py` against `lib/privacy.py` from `v0.1.0` and from `50f9de1`, each in a scratch copy, and record which tests fail.

**Acceptance criteria:**
- [ ] On `v0.1.0`: every case in `LEAKS_SINCE_0_1_1` and `REFUSED_CODE_WORDS` fails, plus `react@18.3.1` in the allowed list; every other case passes (success criterion 10: nothing 0.1.0 allowed is refused now except the named trade-offs).
- [ ] On `50f9de1`: each case added after review fails, or is named in the record as a regression guard.
- [ ] The result (counts and any exceptions) is recorded in this file.

**Verification:**
- [ ] `uv run pytest <scratch>/test_privacy.py` with `PYTHONPATH` pointing at each scratch `lib/`; working tree unchanged (`git status` clean)

**Dependencies:** None. **Files:** `tasks/todo.md`. **Scope:** XS. Commit: `docs(tasks): record the red check of R5`

## Task 2: End-to-end check of `bin/miss-log`

**Description:** In a temporary project with a copy of routewise installed, `bin/miss-log add` refuses one dotless address and one scheme-less link and allows one code word that R5 keeps passing.

**Acceptance criteria:**
- [ ] `--what "mailed me@localhost"` and `--what "see jira.corp.net/browse/X-1"` exit 2 with a `routewise:` message naming the kind of leak, and the log is unchanged.
- [ ] `--what "edited lib/privacy.py and src/a.ts/"` exits 0 and appends one line.
- [ ] If `tests/test_miss_log.py` has no end-to-end refusal test for the new kinds, one is added test first (red shown on `v0.1.0`'s `lib/privacy.py`).

**Verification:**
- [ ] Commands and outputs recorded here; `make check` green

**Dependencies:** None. **Files:** `tasks/todo.md`, maybe `tests/test_miss_log.py`. **Scope:** XS–S. Commit: `docs(tasks): record the miss-log check of R5` (or `test:` if a test is added)

## Checkpoint: verified
- [ ] `make check` green; Tasks 1–2 recorded

## Task 3: Review and audit of the final change

**Description:** Start `reviewer` and `auditor` together on `v0.1.0..HEAD` (`lib/privacy.py`, `tests/test_privacy.py`, `README.md`, `CHANGELOG.md`, `SPEC.md` R5 and S7). Fix or answer every finding.

**Acceptance criteria:**
- [ ] Every finding is fixed (new `fix:` commit, failing test first, CHANGELOG line updated) or answered with a reason, and listed here.
- [ ] A fix that changes an R5 decision is taken to the maintainer before it is built.
- [ ] No open Critical or Required finding.

**Verification:**
- [ ] `make check` green after each fix

**Dependencies:** Tasks 1–2. **Files:** `tasks/todo.md`; for fixes `lib/privacy.py`, `tests/test_privacy.py`, `CHANGELOG.md`, `SPEC.md`. **Scope:** S. Commit: `docs(tasks): record the review of R5`

## Checkpoint: reviewed
- [ ] No open Critical or Required finding; maintainer has seen the findings

## Task 4: Ship checks and the tag commands

**Description:** Check the release contents on the final commit and give the maintainer the exact tag and push commands.

**Acceptance criteria:**
- [ ] `pyproject.toml`, `uv.lock` and every README `v=` say `0.1.1`; `CHANGELOG.md` has `## 0.1.1 (2026-11-14)` with the R5 line and no `Unreleased` section.
- [ ] `git archive --prefix=routewise-0.1.1/ HEAD | tar -t` holds exactly the 11 R1 entries, and its `lib/privacy.py` equals the working tree's.
- [ ] Release notes drafted in `tasks/release-0.1.1.md` if the maintainer asks (open question 1).
- [ ] The maintainer gets: `git tag -a v0.1.1 -m "routewise 0.1.1" <final commit>` and `git push origin main v0.1.1`.

**Verification:**
- [ ] `make check` green on the final commit

**Dependencies:** Task 3. **Files:** `tasks/todo.md`, maybe `tasks/release-0.1.1.md`. **Scope:** XS. Commit: `docs(tasks): record the ship check of R5`

## Ship (maintainer, from the host)
- [ ] `git tag -a v0.1.1 -m "routewise 0.1.1" <final commit>`
- [ ] `git push origin main v0.1.1`
