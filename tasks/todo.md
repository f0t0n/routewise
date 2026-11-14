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

**Round 2 (2026-11-14):** fresh `reviewer` and `auditor` on `1aa6725`. `reviewer`: approve (Optional only). `auditor`: not ready, two regressions introduced by `1aa6725`. An automated security check on the commit raised the same two classes as the auditor's Required items. Every finding was reproduced against `1aa6725^` and `1aa6725` before triage. The maintainer approved the calls below; R5 amended in `51c13dc`.

| # | From | Finding | Answer |
|---|---|---|---|
| R1 | auditor, Required, **regression** | Removing LRM etc. joins a token to the word before it: `x<LRM>AKIA…`, `שלום<LRM>ghp_…`, `כתובת<LRM>10.0.0.1`, `שלום<LRM>https://…`, `id<LRM><uuid>` refused before, pass now | Two views of the text: split view turns invisible characters into spaces (Task 8) |
| R2 | auditor, Required, **regression** | Decoding `%40` hides a link after it: `redirect=%40host.com/path`, `(%40example.com/x)` | Split view does not decode (Task 8) |
| R3 | auditor, Required + security check | Bidi controls not removed: `anna<U+2066>@corp.com`, U+202A, U+061C | Remove every Cf character, in both views (Task 8) |
| R4 | auditor, Optional + security check | Variation selectors, tag characters split an address | Remove U+FE00–FE0F; tags are Cf (Task 8) |
| R5 | auditor, Optional | NFKC before removal: `jose<ZWSP><U+0301>@corp.com` passes | NFKC again after removal in the joined view (Task 8) |
| R6 | auditor, Optional + security check | `\u0040`, `&#x40;`, `&#064;`, `&commat;` pass | Decode them in the joined view (Task 8) |
| R7 | auditor + reviewer, Optional + security check | `` `anna`@ ``, `[anna]@`, `<anna>@`, `anna***@`, `anna@**corp.com**` pass | Up to three markup characters before and after the `@`, dotted only (Task 8) |
| R8 | auditor, Optional | Defanged `anna[@]corp[.]com` passes | Kept gap, in R5 |
| R9 | reviewer, Optional | U+2063, U+2064 not tested (range mutation stays green) | A test per invisible class and per old code point (Task 8) |
| R10 | reviewer, Optional | The markup limit is not pinned (`{0,2}`→`{0,3}` green) | Pin the new limit of three (Task 8) |
| R11 | reviewer, Optional | The markup class is hard to read inside `r"…"` | Name it (Task 8) |
| R12 | reviewer, Optional | Notes clause "common in text pasted from a web page" is not in the CHANGELOG | Bring notes and CHANGELOG in line (Task 8) |
| R13 | reviewer, Optional | `%2540` (double encoding) is not decoded | Kept gap, in R5 |
| – | reviewer | Its control run reported 59 passed, against 131 cases in the file | Its mutation results are re-run by hand in Task 8, with a control |

## Task 8: Fix the re-review findings

**Description:** One `fix:` commit for R1–R7 and R9–R12, built test first. `lib/privacy.py` `finding()` checks a split view and a joined view (SPEC.md R5, "Normalisation, two views of the text"); invisible characters are every Cf character plus U+034F and U+FE00–FE0F; the joined view decodes the six forms of `@` and runs NFKC again; the markup before and after the `@` of a dotted address is named and allows up to three characters.

**Acceptance criteria:**
- [x] Red shown on HEAD for: the 7 regression inputs (R1, R2), the bidi, variation-selector and tag cases (R3, R4), the accent case (R5), the four `@` encodings (R6) and the markup cases (R7); green after.
- [x] A guard test: every refused case (secrets, leaks, 0.1.1 leaks) stays refused with `x` + an invisible character put in front of it, for LRM, U+2066 and ZWSP; every allowed case stays allowed with an invisible character inserted after its first word (assumption 2 of the R5 amendment).
- [x] A test per invisible class (Cf sample from each range, U+034F, U+FE0F) and for every code point of the old list, U+2063 and U+2064 included; the markup limit of three is pinned (four passes, three is refused).
- [x] The markup classes are named constants; no allowed case removed or moved.
- [x] Mutations re-run with an unmutated control, including round 2's survivors (`\u2060-\u2063`, `{0,2}`→`{0,3}`); survivors named here.
- [x] CHANGELOG 0.1.1, README Safety bullet and `tasks/release-0.1.1.md` say what is refused now; the notes add nothing the CHANGELOG lacks.

**Verification:**
- [x] `uv run pytest tests/test_privacy.py` red, then green; `make check` green

**Dependencies:** Task 7 round 2, R5 amended (`51c13dc`). **Files:** `lib/privacy.py`, `tests/test_privacy.py`, `CHANGELOG.md`, `README.md`, `tasks/release-0.1.1.md`, `tasks/todo.md`. **Scope:** M. Commit: `fix: check two views of miss-log text so invisible characters cannot hide a leak`

**Result (2026-11-14):**

- **Red on HEAD (`4e797a4`):** all 26 new leak cases (7 regression inputs of `1aa6725`, bidi, variation-selector, tag, accent, 4 encodings, 8 markup); 16 of 30 invisible characters (every one outside the old list; the old 14, U+2063 and U+2064 included, pass as guards); 94 guard cases (a leak right after LRM, LRI or ZWSP). The allowed-with-invisible guard passed on HEAD and after (no false positive from an inserted invisible character).
- **Green:** `views()` gives the split view (invisible → space, nothing decoded) and the joined view (invisible removed, six `@` encodings decoded, `。` → `.`, NFKC again); `finding()` refuses if either matches. Invisible is category Cf plus U+034F and U+FE00–FE0F. `MARKUP_BEFORE_AT` and `MARKUP_AFTER_AT` are named, three each. No allowed case removed or moved.
- **Found during the build:** the guard failed for `ghp<LRM>_…` (a round-1 case) with an invisible character in front: disguised twice, neither view sees it. The maintainer chose to keep it as a gap; R5 amended (`docs(spec): keep a leak disguised twice…`). The guard skips inputs that already hold an invisible character; its docstring says why. CHANGELOG and notes list the gap.
- **Mutations:** 18 run on a scratch copy with an unmutated control (522 passed, survived); all 18 killed, among them each view alone, removing instead of spacing in the split view, no second NFKC, each encoding, both markup limits ({0,3}→{0,4} and →{0,2}), and round 2's survivors (Cf ranges, the markup limit).
- **Docs:** CHANGELOG 0.1.1, README Safety bullet and the notes name markup, encodings, invisible characters, the two views and the kept gaps; the clause the CHANGELOG lacked (R12) is gone. `make check`: 642 passed.

## Task 9: Re-review the second fix

**Description:** Fresh `reviewer` and `auditor` together on the Task 8 commit against R5 as amended in `51c13dc`, briefed with the diff and spec, not earlier findings; the auditor compares against the commit before it on fuzzed input. Fix or answer every finding; a new R5 decision goes to the maintainer first.

**Acceptance criteria:**
- [ ] Every finding fixed or answered and listed here; no open Critical or Required; no regression against `1aa6725^` or `1aa6725`.

**Verification:**
- [ ] `make check` green after any fix

**Dependencies:** Task 8. **Files:** `tasks/todo.md` (and fixes). **Scope:** XS–S. Commit: `docs(tasks): record round 3 of the 0.1.1 review`

**Round 3 (2026-11-14):** fresh `reviewer` and `auditor` on `d84fadf`. `reviewer`: request changes (one Required); its control matched the repo (522 = 522), so its mutation results stand. `auditor`: not ready, one regression of `d84fadf`. Every finding reproduced against `1aa6725^`, `1aa6725` and `d84fadf`. The maintainer approved the calls below; R5 amended in `818d7da`.

| # | From | Finding | Answer |
|---|---|---|---|
| T1 | auditor, Required, **regression** | Decoding `@` and reading `。` only in the joined view hid a link: `redirect=&#x40;example。com/x`, `(&commat;corp。com/x)` (refused by `1aa6725^` and `1aa6725`); `redirect=%40example。com/path`, `redirect=%40example.co<ZWSP>m/path`, `redirect=%40example.com#<LRM>X-1`, `שלום<LRM>10。0。0。1` (refused by `1aa6725^`) | Four views; steps that only add evidence apply to all (Task 10) |
| T2 | reviewer, Required + auditor | Not invisible yet: U+E0100–E01EF, U+180B–180D (Mn), U+2800, U+17B4, U+2065, U+FFF0, Hangul fillers inside a token, IP or path | Cf ∪ Default_Ignorable_Code_Point ∪ U+2800 (Task 10) |
| T3 | auditor, Optional | `anna\x40corp.com` passes | Decode `\x40`; not `=40` (Task 10) |
| T4 | auditor, Optional | `{anna}@corp.com`, `anna@"corp.com"`, `anna@'corp.com'` pass | `}` before, `{ " '` after (Task 10); `**anna **@`, HTML around `@` kept gaps |
| T5 | reviewer, Optional | Green mutations: split view keeping raw characters, first NFKC removed, `IGNORECASE` on encodings, single markup characters `~` `)` `[` | Pin each (Task 10) |
| T6 | reviewer, Nit | `invisible()`, `first_match()` lack a docstring | Add (Task 10) |
| T7 | reviewer, Nit | `` `icon`@2x.png `` refused | No change: `icon@2x.png` refused since 0.1.0, a dotted domain with a letter |
| T8 | auditor, Nit | Worst case 80 ms (two views) at the CLI limits | No change |
| T9 | auditor, Optional | `&#64` without `;`, `%u0040`, `\u{40}`, `=40` | Kept gaps, in R5 |

## Task 10: Fix the round-3 findings

**Description:** One `fix:` commit for T1–T6, built test first. First, `web-reader` checks the Default_Ignorable_Code_Point ranges written in R5 against Unicode's published `DerivedCoreProperties.txt`; I open the file's lines myself before any range is used, and a wrong range goes back to the maintainer as an R5 correction. Then `views()` returns the four combinations of {invisible as space, removed} × {`@` decoded, not}, with NFKC and `。` in all; the invisible set is the R5 one; `\x40` is decoded; the markup classes gain `}` and `{ " '`.

**Acceptance criteria:**
- [x] The R5 ranges match the Unicode file (or a correction was approved first).
- [x] Red shown on HEAD for the T1 regression inputs, one character per T2 range (Hangul fillers inside a token, an IP and a path too), `\x40`, the T4 markup and the T5 pins that are not already green; green after.
- [x] A guard test: for every encoding of `@`, a link after it (with `.` and with `。`) is refused, and with an invisible character inside the host or the anchor.
- [x] The guard tests of Task 8 still pass; every allowed case stays allowed, also with invisible characters inserted; no allowed case removed or moved.
- [x] Mutations re-run with an unmutated control whose count equals the repo's; every view, each lossy step, each new range and each markup character killed, or the survivor named here.
- [x] Worst-case time at the CLI limits measured and recorded.
- [x] CHANGELOG 0.1.1, README Safety bullet and the notes in line with R5; the notes add nothing the CHANGELOG lacks.

**Verification:**
- [x] `uv run pytest tests/test_privacy.py` red, then green; `make check` green

**Dependencies:** Task 9 round 3, R5 amended (`818d7da`). **Files:** `lib/privacy.py`, `tests/test_privacy.py`, `CHANGELOG.md`, `README.md`, `tasks/release-0.1.1.md`, `tasks/todo.md`. **Scope:** M. Commit: `fix: check four views of miss-log text so decoding cannot hide a link`

**Result (2026-11-14):**

- **Ranges:** unicode.org returned 403 to `curl` and to `web-reader` (four URLs). Unicode's own copy in the ICU repository (`raw.githubusercontent.com/unicode-org/icu/main/icu4c/source/data/unidata/DerivedCoreProperties.txt`, header `DerivedCoreProperties-18.0.0.txt`, dated 2026-08-07) was read directly: its 27 Default_Ignorable_Code_Point lines, merged where adjacent, are exactly the 17 ranges in R5, and add up to its `Total code points: 4174`. No correction needed.
- **Red on HEAD (`c455cbe`):** 72 failed: the 6 T1 regression inputs, `\x40`, `{anna}@`, `anna@"…"`, `anna@'…'`, `anna@{…}` (11 leak cases, 24 more behind an invisible character), 13 new invisible characters, 12 Hangul-filler cases (token, IP, path) and 12 encoded-`@` link guards. The first draft of the link guard used two-dot hosts and never failed: `corp.io/x` inside `wiki.corp.io/x` is a link by itself; it uses one-dot hosts now.
- **Green:** four views ({invisible as space, removed} × {`@` decoded, not}); NFKC first (so `％40` decodes and `ＡＫＩＡ` joins) and again in each view, with `。` read as a dot; invisible is Cf plus the R5 ranges plus U+2800; `\x40` decoded; `}` before and `{ " '` after the `@`; docstrings on `invisible()` and `first_match()`. No allowed case removed or moved; the allowed-with-invisible guard still passes.
- **Mutations:** control 643 = repo 643. 32 run: 25 killed at once; three more killed after test fixes (no first NFKC: added `anna％40corp.com`; `~` before and after the `@`: the tests used `~anna` and `@~corp`, which the home-folder rule refuses anyway; now `anna~@corp.com` and `anna@~~1password.com~~`); one equivalent dropped (`。` before the views, every view reads it). Four equivalent survivors kept as R5 lists them: U+3164 and U+FFA0 (NFKC maps both to U+1160, in the set), U+1BCA0–1BCA3 and U+1D173–1D17A (already Cf).
- **Time** (best of 5, 200 characters): 200 × U+3316 159 ms (NFKC grows it to 1200 word characters), 200 × U+FDFA 7 ms, 200 × `a` 4 ms, normal text 0.1 ms.
- **Docs:** CHANGELOG 0.1.1, README Safety bullet and the notes name the four views, the invisible set, `\x40`, the new markup and the new kept gaps. `make check`: 767 passed.

## Task 11: Round-4 review of the third fix

**Description:** Fresh `reviewer` and `auditor` together on the Task 10 commit against R5 as amended in `818d7da`, briefed with the diff and spec, not earlier findings. The reviewer reports its control count next to the repo's. The auditor compares against `1aa6725^`, `1aa6725` and `d84fadf` on fuzzed input. Fix or answer every finding; a new R5 decision goes to the maintainer first.

**Acceptance criteria:**
- [ ] Every finding fixed or answered and listed here; no open Critical or Required; no regression against any earlier version.

**Verification:**
- [ ] `make check` green after any fix

**Dependencies:** Task 10. **Files:** `tasks/todo.md` (and fixes). **Scope:** XS–S. Commit: `docs(tasks): record round 4 of the 0.1.1 review`

**Round 4 (2026-11-14):** fresh `reviewer` and `auditor` on `ab90528`. `reviewer`: approve; control 647 = repo 647. `auditor`: no regression against any earlier version on 6.6 million fuzzed variants except one Nit; two false positives against 0.1.0. Every finding reproduced against 0.1.0, `50f9de1` and `d84fadf`. Pattern noted: each widening of the filter caused the next round's findings, so the maintainer approved fixing only what 0.1.1 broke (success criterion 10) and moving gaps 0.1.0 also had to 0.1.2. R5 amended in `8378252`.

| # | From | Finding | Answer |
|---|---|---|---|
| U1 | reviewer | CJK prose refused since `d84fadf`: `修复路由。然后改a/b`, `已修复。lib/x.py`, `ルーティングを修正。次にsrc/a.tsを確認` (`。` read as a dot makes a clause a host) | `。` is a dot only between ASCII letters or digits (Task 12) |
| U2 | auditor | Code refused since round 2 or 3: `f"{user}@{cfg.domain}"`, `{{user}}@{{site.domain}}`, `obj@"pkg.json"`, `x@'a.b'`; also `a[i]@m.T`, `f(x)@w.T` | Markup only Markdown and quotes before, Markdown after (Task 12); brackets, braces, angle brackets, quotes after the `@` kept gaps |
| G1 | auditor, Required | A CJK or Hebrew letter touching a leak hides it (`\b`): `服务器在10.0.0.12上`, `key AKIA…が漏れた`, `见www.example.com`; also in 0.1.0 | 0.1.2 (R7), listed in R5 |
| G2 | auditor | URL-encoded link `next=https%3A%2F%2Fjira.corp.net%2F…`; also in 0.1.0 | 0.1.2, listed in R5 |
| G3 | auditor | `me\@localhost`; also in 0.1.0 | 0.1.2, listed in R5 |
| G4 | auditor, Nit, regression vs `d84fadf` only | `me\<U+3164>@localhost`: caught by `d84fadf` by accident (filler as a letter); 0.1.0 never did | Covered by G3 |
| V1 | reviewer | Four identical views for normal text | Drop duplicates (Task 12) |
| V2 | reviewer | `<` and `(` after the `@` untested | Moot: removed by U2 |
| V3 | reviewer | No test pins `100%40 off` as allowed | Add (Task 12) |
| – | reviewer | Equivalent survivors: Cf ranges, U+3164/U+FFA0, `_` | No change |
| – | reviewer, auditor | `# fmt: skip` on the table; worst case 167 ms | No change |

## Task 12: Fix what 0.1.1 broke (round 4)

**Description:** One `fix:` commit for U1, U2, V1, V3, test first. Every round-4 false positive becomes an allowed test; the leak cases that relied on brackets, braces, angle brackets or quotes after the `@` move to a pinned "kept gap" list so the change is visible.

**Acceptance criteria:**
- [ ] Red on HEAD for each U1 and U2 phrase as an allowed test; green after.
- [ ] `jira。corp。net/x`, `10。0。0。1`, `redirect=%40example。com/path` and every other leak still refused; the encoded-`@` and invisible-character guards still pass.
- [ ] The cases `{anna}@`, `[anna]@`, `<anna>@`, `(anna)@`, `anna@"…"`, `anna@'…'`, `anna@{…}`, `anna@[…]`, `anna@<…>` move from the refused lists to a `KEPT_GAPS` list that asserts they pass (R5), so a later change to them is deliberate; none is silently deleted.
- [ ] `views()` returns no duplicate; `100%40 off foo.bar` is an allowed test.
- [ ] Mutations re-run with a control equal to the repo; survivors named.
- [ ] CHANGELOG 0.1.1, README Safety bullet and the notes match R5 (markup list, `。` rule, kept gaps, gaps for 0.1.2).

**Verification:**
- [ ] `uv run pytest tests/test_privacy.py` red, then green; `make check` green

**Dependencies:** Task 11 round 4, R5 amended (`8378252`). **Files:** `lib/privacy.py`, `tests/test_privacy.py`, `CHANGELOG.md`, `README.md`, `tasks/release-0.1.1.md`, `tasks/todo.md`. **Scope:** S. Commit: `fix: stop the miss-log filter refusing code and CJK text that 0.1.0 allowed`

## Task 13: Round-5 review, scoped to what 0.1.1 broke

**Description:** Fresh `reviewer` and `auditor` together on the Task 12 commit against R5 as amended in `8378252`. Scope, given in the brief: (1) nothing 0.1.0 allowed is refused now (success criterion 10), checked on a corpus of plausible developer text including code, templates, Markdown, CJK and RTL prose; (2) no regression against 0.1.0, `1aa6725^`, `1aa6725`, `d84fadf` or `ab90528` on fuzzed leaks; (3) the code, tests and docs match R5. A gap of a kind 0.1.0 also had is recorded for 0.1.2 (R7), not fixed in 0.1.1. Fix or answer every in-scope finding; a new R5 decision goes to the maintainer first.

**Acceptance criteria:**
- [ ] Every finding fixed, answered or recorded for 0.1.2, and listed here; no open Critical or Required in scope.

**Verification:**
- [ ] `make check` green after any fix

**Dependencies:** Task 12. **Files:** `tasks/todo.md` (and fixes). **Scope:** XS–S. Commit: `docs(tasks): record round 5 of the 0.1.1 review`

## Follow-up (not in 0.1.1)

- [ ] R7 for 0.1.2: G1–G3 (and whatever round 5 records), with its own Define, Plan and false-positive check.


## Checkpoint: reviewed
- [ ] No open Critical or Required finding; maintainer has seen the findings

## Task 14: Ship checks and the tag commands

**Description:** Check the release contents on the final commit and give the maintainer the exact tag and push commands.

**Acceptance criteria:**
- [ ] `pyproject.toml`, `uv.lock` and every README `v=` say `0.1.1`; `CHANGELOG.md` has `## 0.1.1 (2026-11-14)` with the R5 and R6 lines and no `Unreleased` section.
- [ ] `git archive --prefix=routewise-0.1.1/ HEAD | tar -t` holds exactly the 11 R1 entries, and its `lib/privacy.py` and `lib/miss_log.py` equal the working tree's.
- [ ] `tasks/release-0.1.1.md` still matches `CHANGELOG.md` 0.1.1 after any review fix.
- [ ] The maintainer gets: `git tag -a v0.1.1 -m "routewise 0.1.1" <final commit>`, `git push origin main v0.1.1` and `gh release create v0.1.1 --title "routewise 0.1.1" --notes-file tasks/release-0.1.1.md`.

**Verification:**
- [ ] `make check` green on the final commit

**Dependencies:** Task 13. **Files:** `tasks/todo.md`. **Scope:** XS. Commit: `docs(tasks): record the ship check of 0.1.1`

## Ship (maintainer, from the host)
- [ ] `git tag -a v0.1.1 -m "routewise 0.1.1" <final commit>`
- [ ] `git push origin main v0.1.1`
- [ ] `gh release create v0.1.1 --title "routewise 0.1.1" --notes-file tasks/release-0.1.1.md`
