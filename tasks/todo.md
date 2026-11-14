# Tasks: miss-log privacy fix and error prefix, release 0.1.1 (R5, R6)

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

## Task 3: R6, one error prefix in `bin/miss-log`

**Description:** Test first: `tests/test_miss_log.py` asserts that a refused entry's stderr starts with `routewise: `; it fails while `lib/miss_log.py` prints `miss-log: `. Then change both prints in `main` and add a `CHANGELOG.md` line under 0.1.1.

**Acceptance criteria:**
- [x] The new assertion fails on HEAD before the fix (red shown), passes after.
- [x] Both error branches of `lib/miss_log.py` `main` print `routewise: `; the file-error branch is tested if a log path that is a folder reaches it, otherwise checked by reading and named here.
- [x] Exit code 2 and the message text after the prefix are unchanged (existing tests still pass); argparse usage errors unchanged.
- [x] `CHANGELOG.md` 0.1.1 has one line for R6.

**Verification:**
- [x] `uv run pytest tests/test_miss_log.py` red, then green; `make check` green

**Dependencies:** None. **Files:** `lib/miss_log.py`, `tests/test_miss_log.py`, `CHANGELOG.md`, `tasks/todo.md`. **Scope:** XS. Commit: `fix: print miss-log errors with the routewise: prefix`

**Result (2026-11-14):** `test_errors_start_with_the_routewise_prefix` failed on HEAD before the fix (`'miss-log: what holds an e-mail address; ...'.startswith('routewise: what holds an e-mail address')` is False) and passes after. The file-error branch is tested: `report` on a log path that is a folder raises `IsADirectoryError`, which reaches the `OSError` branch, no symlink or permission trick needed. `grep '"miss-log:' lib bin` finds nothing left; argparse usage errors still read `miss-log add: error: ...`. All 9 tests in `tests/test_miss_log.py` pass.

## Task 4: Draft the 0.1.1 release notes

**Description:** Write `tasks/release-0.1.1.md` for users, in the shape of `tasks/release-0.1.0.md`: what 0.1.1 fixes (R5, R6, and R4's README install block), what is newly refused and how to reword it, how to update (the README's "Updating" block with `v=0.1.1`), and links to `CHANGELOG.md` and the README.

**Acceptance criteria:**
- [x] Every claim matches `CHANGELOG.md` 0.1.1 and the code; nothing in it is missing from the CHANGELOG.
- [x] The update commands are copied from the README, not retyped.

**Verification:**
- [x] Read against `CHANGELOG.md` and `README.md`; checked again by `reviewer` in Task 5; `make check` green

**Dependencies:** Task 3. **Files:** `tasks/release-0.1.1.md`, `tasks/todo.md`. **Scope:** XS. Commit: `docs(tasks): draft the 0.1.1 release notes`

**Result (2026-11-14):** `tasks/release-0.1.1.md` drafted. Each claim was checked against `CHANGELOG.md` 0.1.1 and `privacy.finding()`; the one claim the CHANGELOG lacked (`#` after a host) was added to the CHANGELOG, since code and tests cover it. The update block is byte-identical to the README's "Updating" block (checked by script). "No generated file changes" was checked: a project installed from `git archive v0.1.0`, updated to HEAD, prints `routewise: nothing to change`. `reviewer` still checks the notes in Task 5.

## Task 5: Review and audit of the final change and the notes

**Description:** Start `reviewer` and `auditor` together on `v0.1.0..HEAD` (`lib/privacy.py`, `lib/miss_log.py`, `tests/test_privacy.py`, `tests/test_miss_log.py`, `README.md`, `CHANGELOG.md`, `SPEC.md` R5, R6 and S7); `reviewer` also checks `tasks/release-0.1.1.md` against the code. Fix or answer every finding.

**Acceptance criteria:**
- [ ] Every finding is fixed (new `fix:` commit, failing test first, CHANGELOG line updated) or answered with a reason, and listed here.
- [ ] A fix that changes an R5 or R6 decision is taken to the maintainer before it is built.
- [ ] No open Critical or Required finding.

**Verification:**
- [ ] `make check` green after each fix

**Dependencies:** Tasks 1–4. **Files:** `tasks/todo.md`; for fixes `lib/privacy.py`, `lib/miss_log.py`, their tests, `CHANGELOG.md`, `SPEC.md`, `tasks/release-0.1.1.md`. **Scope:** S. Commit: `docs(tasks): record the review of R5 and R6`

**Round 1 (2026-11-14):** `reviewer` and `auditor` started together, briefed with the spec and the diff, not with earlier findings. Every finding was reproduced by hand before triage. No Critical. `auditor`: OK to ship; `reviewer`: request changes (one Required). The maintainer saw all findings and approved the calls below; R5 was amended for A–E (`6665dff`).

| # | From | Finding | Answer |
|---|---|---|---|
| 1 | reviewer, Required | CHANGELOG and notes: "`react@18.3.1` and other versions after `@` now pass"; `checkout@v4.1.0`, `pkg@v1.2.3`, `tsc@5.4.x` are still refused (as in 0.1.0) | Fix the wording (Task 6); honouring the tag list in the dotted rule would let `anna@main.corp.com` through |
| 2 | reviewer, Optional | `v\d+(?:\.\d+)*` in `TAG` is dead (mutation to `v\d+` stays green) | Simplify to `v\d+` (Task 6) |
| 3 | reviewer, Optional | Green mutations: tag words `rc`/`lts`/`stable`/`master`, a 5-digit port, the 2-letter TLD minimum, most `SOURCE_TYPES` | Pin with tests (Task 6) |
| 4 | reviewer, Optional/Nit | String-built host patterns lack an example; `normal()` lacks a why | Comments and one docstring line (Task 6) |
| A | auditor, Optional | LRM/RLM, U+2061–2064, U+180E, U+034F not stripped: `anna\u200f@corp.com`, a token split by LRM pass | Strip them (Task 6, R5 amended) |
| B | auditor, Optional | `anna%40corp.com`, `anna&#64;corp.com` pass | Read `%40` and `&#64;` as `@` (Task 6, R5 amended) |
| C | auditor, Optional | `anna\@corp.com`, `"anna"@corp.com`, `**anna**@corp.com` pass | Up to two of `\ " ' *` before the `@` of a dotted address (Task 6, R5 amended) |
| D | auditor + reviewer, Optional | `localhost:3000/admin`, `jenkins-prod:8080/job/x`, `//jenkins/job/x`, `proxy/jira.com/x` pass (also in 0.1.0) | Kept gap, listed in R5; follow-up needs its own false-positive check |
| E | auditor, Nit | Combining marks / vowel signs: `सीता@corp.com`, `कंपनी.भारत/x` pass | Kept gap, listed in R5 (`re` has no `\p{M}`) |
| F | auditor, Nit | NFKC can grow 200 characters to 3600; worst case 44 ms (34 ms in 0.1.0) | No change |
| – | auditor | Only regression: a domain without a letter (`user@10.0.1`) passes | Documented in R5 "Also changed" |
| – | auditor | R6 changes only the two stderr prefixes; write path, fields, exit codes unchanged | Nothing to do |

## Task 6: Fix the review findings

**Description:** One `fix:` commit for findings 1–4 and A–C. Test first: add the A–C leaks and the finding-3 pins to `tests/test_privacy.py`, show which fail on HEAD, then change `lib/privacy.py`; update the CHANGELOG 0.1.1 line and `tasks/release-0.1.1.md` (finding 1 and the new refusals).

**Acceptance criteria:**
- [x] The A–C cases fail on HEAD before the fix (red shown) and pass after; the finding-3 pins are recorded as guards (they pass on HEAD by nature) and each one fails under the mutation the reviewer named.
- [x] `TAG` is `v\d+` plus the words; every case allowed before still passes (no test removed or moved).
- [x] CHANGELOG 0.1.1 and the notes say "a version made only of digits and dots"; both name the new refusals (markup before `@`, `%40`, invisible characters); the notes still add nothing the CHANGELOG lacks.

**Verification:**
- [x] `uv run pytest tests/test_privacy.py` red, then green; mutations re-run in a scratch copy; `make check` green

**Dependencies:** Task 5 round 1. **Files:** `lib/privacy.py`, `tests/test_privacy.py`, `CHANGELOG.md`, `tasks/release-0.1.1.md`, `tasks/todo.md`. **Scope:** S. Commit: `fix: close the gaps found in the review of the 0.1.1 filter`

**Result (2026-11-14):**

- **Red:** 11 new A–C cases in `tests/test_privacy.py` failed on HEAD (`451aaf5`): `anna\@`, `"anna"@`, `**anna**@`, `'anna'@`, `%40`, `&#64;`, RLM before `@`, LRM inside `ghp_`, U+2062, U+180E, U+034F before `@`. A first draft put U+2062/180E/034F inside the local part, where `na@corp.com` is refused anyway; moved before the `@` so they test the split. Green after the fix (131 privacy tests).
- **Pins (finding 3):** tag words `rc` … `canary`, `root@master`/`me@main`, `host.corp:65535/x`, `a.b/c`, a 64-letter TLD, `anna@v`, and every R5 source type (listed in the test, not imported, so dropping one from the code is caught). Mutations run on a scratch copy with an unmutated control (130 passed, survived): all 10 killed, `v\d+`→`v\d*` after adding `anna@v`. A first run reported every mutation killed because `uv run` could not find the project from the scratch folder; the control exposed it.
- **Code:** `ZERO_WIDTH` → `INVISIBLE` (adds U+200E/F, U+2061–2064, U+180E, U+034F), `ENCODED_AT` read as `@` in `normal()` (with a docstring), up to two of `\ " ' *` before the `@` of a dotted address, `TAG` uses `v\d+`, host patterns have examples. No allowed case removed or moved.
- **Docs:** CHANGELOG 0.1.1 and the notes say "a version made only of digits and dots", name the new refusals and the kept gaps. Found while writing them: both claimed `//host/x` is refused, but a dotless host is a kept gap; changed to `//host.com/x` (checked: `//host/x` passes, `//host.com/x` is refused). README Safety bullet names encoded addresses.

## Task 7: Re-review the fix

**Description:** Fresh `reviewer` and `auditor` together on the Task 6 commit (with R5 as amended), briefed with the diff and spec, not the round-1 findings. Fix or answer every finding as in Task 5; a new R5 decision goes to the maintainer first.

**Acceptance criteria:**
- [ ] Every finding fixed or answered and listed here; no open Critical or Required.

**Verification:**
- [ ] `make check` green after any fix

**Dependencies:** Task 6. **Files:** `tasks/todo.md` (and fixes). **Scope:** XS–S. Commit: `docs(tasks): record the review of R5 and R6`


## Checkpoint: reviewed
- [ ] No open Critical or Required finding; maintainer has seen the findings

## Task 8: Ship checks and the tag commands

**Description:** Check the release contents on the final commit and give the maintainer the exact tag and push commands.

**Acceptance criteria:**
- [ ] `pyproject.toml`, `uv.lock` and every README `v=` say `0.1.1`; `CHANGELOG.md` has `## 0.1.1 (2026-11-14)` with the R5 and R6 lines and no `Unreleased` section.
- [ ] `git archive --prefix=routewise-0.1.1/ HEAD | tar -t` holds exactly the 11 R1 entries, and its `lib/privacy.py` and `lib/miss_log.py` equal the working tree's.
- [ ] `tasks/release-0.1.1.md` still matches `CHANGELOG.md` 0.1.1 after any review fix.
- [ ] The maintainer gets: `git tag -a v0.1.1 -m "routewise 0.1.1" <final commit>`, `git push origin main v0.1.1` and `gh release create v0.1.1 --title "routewise 0.1.1" --notes-file tasks/release-0.1.1.md`.

**Verification:**
- [ ] `make check` green on the final commit

**Dependencies:** Task 7. **Files:** `tasks/todo.md`. **Scope:** XS. Commit: `docs(tasks): record the ship check of 0.1.1`

## Ship (maintainer, from the host)
- [ ] `git tag -a v0.1.1 -m "routewise 0.1.1" <final commit>`
- [ ] `git push origin main v0.1.1`
- [ ] `gh release create v0.1.1 --title "routewise 0.1.1" --notes-file tasks/release-0.1.1.md`
