# Tasks: miss-log privacy fix, release 0.1.1 (R5)

Plan: [plan.md](plan.md). Spec: [SPEC.md](../SPEC.md). `make check` green before each commit (the pre-commit hook enforces it). Tick a box in the commit that records the task.

## Task 1: Prove the new tests fail first

**Description:** Run today's `tests/test_privacy.py` against `lib/privacy.py` from `v0.1.0` and from `50f9de1`, each in a scratch copy, and record which tests fail.

**Acceptance criteria:**
- [x] On `v0.1.0`: every case in `LEAKS_SINCE_0_1_1` and `REFUSED_CODE_WORDS` fails, plus `react@18.3.1` in the allowed list; every other case passes (success criterion 10: nothing 0.1.0 allowed is refused now except the named trade-offs).
- [x] On `50f9de1`: each case added after review fails, or is named in the record as a regression guard.
- [x] The result (counts and any exceptions) is recorded in this file.

**Verification:**
- [x] `uv run pytest <scratch>/test_privacy.py` with `PYTHONPATH` pointing at each scratch `lib/`; working tree unchanged (`git status` clean)

**Result (2026-11-14):** today's `tests/test_privacy.py` (88 cases), run in a scratch copy with `lib/privacy.py` from each commit; `git status` clean before and after.

- `v0.1.0`: 28 failed, 60 passed. Failed: 23 of the 24 `LEAKS_SINCE_0_1_1` cases, all 4 `REFUSED_CODE_WORDS`, and `react@18.3.1` in the allowed list. The one that passes, `ask jane@пример.рф`, is a regression guard: 0.1.0 refused it and `50f9de1` broke it. Every case 0.1.0 allowed or refused before still passes (no regression in the old tests).
- `50f9de1`: 18 failed, 70 passed. Failed: all 17 leak cases added after review, and `ASP.NET/Core` (allowed there, refused on purpose since). Regression guards, which cannot fail first by nature: `os.path/join and json.loads/dumps` (already refused at `50f9de1`, pinned when the rule changed) and the allowed cases added after review (`did it call os.path? ...`, `node_modules/lodash.merge/...`, `Next.js/React and Vue.js/Svelte`).

**Dependencies:** None. **Files:** `tasks/todo.md`. **Scope:** XS. Commit: `docs(tasks): record the red check of R5`

## Task 2: End-to-end check of `bin/miss-log`

**Description:** In a temporary project with a copy of routewise installed, `bin/miss-log add` refuses one dotless address and one scheme-less link and allows one code word that R5 keeps passing.

**Acceptance criteria:**
- [x] `--what "mailed me@localhost"` and `--what "see jira.corp.net/browse/X-1"` exit 2 with a message naming the kind of leak, and the log is unchanged.
- [x] `--what "edited lib/privacy.py and src/a.ts/"` exits 0 and appends one line.
- [x] If `tests/test_miss_log.py` has no end-to-end refusal test for the new kinds, one is added test first (red shown on `v0.1.0`'s `lib/privacy.py`).

**Verification:**
- [x] Commands and outputs recorded here; `make check` green

**Dependencies:** None. **Files:** `tasks/todo.md`, maybe `tests/test_miss_log.py`. **Scope:** XS–S. Commit: `docs(tasks): record the miss-log check of R5` (or `test:` if a test is added)

**Result (2026-11-14):**

- `tests/test_miss_log.py` had no end-to-end case for the new kinds, so `test_refuses_a_dotless_address_and_a_link_without_a_scheme` was added. With `v0.1.0`'s `lib/privacy.py` copied in, it fails (`assert (0, 0) == (2, 2)`: both were written to the log); `lib/privacy.py` was restored with `git checkout`, and the test passes on HEAD.
- By hand, on a fresh project unpacked from `git archive HEAD` and installed with `routewise/install`:
  - `mailed me@localhost` → `miss-log: what holds an e-mail address; describe the miss without it`, exit 2
  - `see jira.corp.net/browse/X-1` → `miss-log: what holds a URL; describe the miss without it`, exit 2
  - `edited lib/privacy.py and src/a.ts/` → exit 0; the log holds exactly that one line
- Noticed, not touched: the message starts with `miss-log:`, not `routewise:` as AGENTS.md's style asks. That predates R5, so the criterion above dropped the prefix; a separate change if wanted.

## Checkpoint: verified
- [x] `make check` green; Tasks 1–2 recorded

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
