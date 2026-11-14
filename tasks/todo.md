# Tasks: miss-log gaps, release 0.1.2 (R7)

Plan: [plan.md](plan.md). Spec: [SPEC.md](../SPEC.md), R7. `make check` green before each commit (the pre-commit hook enforces it). For each fix task: red shown against HEAD before the change, the whole `tests/test_privacy.py` green after, a CHANGELOG line under `## Unreleased`.

## Task 1: G1, ASCII word boundaries

**Description:** Test first: the G1 leaks (`服务器在10.0.0.12上`, `key AKIA…が漏れた`, `见www.example.com`, `见https://example.com`, `ב10.0.0.12`, `令牌eyJ…`, `id <uuid>を使った`, `主机2001:db8::1`, and a chat ID and a card number touched by a CJK letter) fail on HEAD. Then `WORD_START` and `WORD_END` replace `\b` in the token, key, scheme, `www.`, IPv4, IPv6, UUID, chat-ID and card patterns.

**Acceptance criteria:**
- [ ] Each G1 leak red on HEAD, green after; `xAKIA…` and `v10.0.0.12` keep their 0.1.1 result.
- [ ] Every other case in `tests/test_privacy.py` keeps its result; any text 0.1.1 allowed and now refused (accented Latin before a number, for example) is listed here and named in the CHANGELOG.
- [ ] Mutations: each boundary in each changed pattern, with a control equal to the repo and each mutant checked to import; survivors named.

**Verification:** `uv run pytest tests/test_privacy.py` red, then green; `make check` green.

**Dependencies:** None. **Files:** `lib/privacy.py`, `tests/test_privacy.py`, `CHANGELOG.md`, `tasks/todo.md`. **Scope:** S. Commit: `fix: catch a leak touched by a letter of another script (R7 G1)`

## Task 2: G2, URL-encoded scheme

**Description:** Test first: `next=https%3A%2F%2Fjira.corp.net%2F…` and the lower-case form fail on HEAD. Then the scheme rule also takes `%3A%2F%2F` (any case).

**Acceptance criteria:**
- [ ] Both red on HEAD, green after; `100%3A` or `a%3Ab` alone stays allowed (an allowed test).
- [ ] Mutations on the new alternative and its case flag; survivors named.

**Verification:** as Task 1. **Dependencies:** Task 1. **Files:** as Task 1. **Scope:** XS. Commit: `fix: catch a URL-encoded link (R7 G2)`

## Task 3: G3, a backslash before a dotless `@`

**Description:** Test first: `me\@localhost` fails on HEAD. Then the dotless rule allows one backslash before the `@`.

**Acceptance criteria:**
- [ ] Red on HEAD, green after; `"x"@property`, `used @property` and `jane \@ example.com` (spaces stay a kept gap, pinned in `KEPT_GAPS`) keep their 0.1.1 result.
- [ ] Mutations; survivors named.

**Verification:** as Task 1. **Dependencies:** Task 2. **Files:** as Task 1. **Scope:** XS. Commit: `fix: catch an escaped @ without a dot in the domain (R7 G3)`

## Task 4: a JWT written with `。`

**Description:** Test first: `eyJ…。eyJ…。_Qx9` and `eyJ…。eyJ…。` (no signature) fail on HEAD. Then the JWT rule reads `[.。]` as its dots.

**Acceptance criteria:**
- [ ] Both red on HEAD, green after; the existing JWT cases keep their result.
- [ ] Mutations; survivors named.

**Verification:** as Task 1. **Dependencies:** Task 3. **Files:** as Task 1. **Scope:** XS. Commit: `fix: catch a JWT written with 。 (R7)`

## Task 5: link ends `$`, `!/`, `:~:`, ASCII after `?` and `#`

**Description:** Test first: `api.corp.net?$top=5`, `app.corp.io#!/users/1`, `docs.corp.io#:~:text=x` fail on HEAD as leaks; `为什么用foo.bar？因为快`, `foo.bar?为什么`, `한국어 foo.bar?그래서` fail on HEAD as allowed (moved from `REFUSED_CODE_WORDS`). Then `LINK_END` takes `?` or `#` before an ASCII URL character, `$`, `!/` or `:~:`.

**Acceptance criteria:**
- [ ] All six red on HEAD, green after; `foo.bar?:x` allowed; `wiki.corp.io#Раздел` pinned in `KEPT_GAPS`; each character of the class still has its own case (from 0.1.1).
- [ ] Mutations on each new alternative and on the ASCII class; survivors named.

**Verification:** as Task 1. **Dependencies:** Task 4. **Files:** as Task 1. **Scope:** XS. Commit: `fix: read more link ends and stop reading CJK after ? as a query (R7)`

## Checkpoint: verified
- [ ] `make check` green.
- [ ] Differential check: `daa469d` (the commit tagged `v0.1.1`)'s `lib/privacy.py` and HEAD's on every input of `tests/test_privacy.py`; every difference is an R7 item; listed here.
- [ ] Worst-case time at the CLI limits measured.

## Task 6: Docs and release notes for 0.1.2

**Description:** CHANGELOG `## Unreleased` holds one line per R7 item (from Tasks 1–5) and names any new refusal of Task 1; README Safety bullet still true; `tasks/release-0.1.2.md` drafted for users, with the update block from the README.

**Acceptance criteria:**
- [ ] Every example in the CHANGELOG and the notes probed against `finding()`; every behaviour claim in the notes is in the CHANGELOG; R5's "for 0.1.2" list in SPEC.md marked as done by R7 where it is.

**Verification:** `make check` green. **Dependencies:** checkpoint. **Files:** `CHANGELOG.md`, `README.md`, `SPEC.md` (the R5 list only), `tasks/release-0.1.2.md`, `tasks/todo.md`. **Scope:** XS. Commit: `docs: describe 0.1.2 and draft its release notes`

## Task 7: Release bump to 0.1.2

**Description:** `pyproject.toml`, `uv.lock`, both README `v=` lines to `0.1.2`; CHANGELOG `## Unreleased` becomes `## 0.1.2 (<date>)`.

**Acceptance criteria:**
- [ ] The R4 version test passes; `make check` green.

**Dependencies:** Task 6. **Files:** `pyproject.toml`, `uv.lock`, `README.md`, `CHANGELOG.md`. **Scope:** XS. Commit: `build: release 0.1.2`

## Task 8: Review, one round under the stopping rule

**Description:** Fresh `reviewer` and `auditor` together on `daa469d..HEAD` (`v0.1.1` is tagged on the host only), briefed with R7 and its bar: nothing 0.1.1 refuses passes, nothing it allows is refused except what R7 names; code, tests and docs match R7. The reviewer reports its control count next to the repo's. Findings are fixed (one more round scoped to the fix, if Critical or Required) or recorded for the next release.

**Acceptance criteria:**
- [ ] Every finding fixed, answered or recorded, and listed here; no open Critical or Required in scope.

**Dependencies:** Task 7. **Files:** `tasks/todo.md` (and fixes). **Scope:** XS–S. Commit: `docs(tasks): record the review of R7`

## Checkpoint: reviewed
- [ ] No open Critical or Required finding; maintainer has seen the findings.

## Task 9: Ship checks and the tag commands

**Description:** On the final commit: versions, CHANGELOG, archive (11 R1 entries; `lib/privacy.py` equal to the working tree), notes match the CHANGELOG, update and rollback on a project installed from `daa469d` (`v0.1.1`); then the maintainer gets the tag, push and `gh release create` commands.

**Acceptance criteria:**
- [ ] All of the above checked and recorded here.

**Dependencies:** Task 8. **Files:** `tasks/todo.md`. **Scope:** XS. Commit: `docs(tasks): record the ship check of 0.1.2`

## Ship (maintainer, from the host)
- [ ] `git tag -a v0.1.2 -m "routewise 0.1.2" <final commit>`
- [ ] `git push origin main v0.1.2`
- [ ] `gh release create v0.1.2 --title "routewise 0.1.2" --notes-file tasks/release-0.1.2.md`
