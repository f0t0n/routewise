# Tasks: release routewise 0.1.0

Plan: [release-0.1.0-plan.md](release-0.1.0-plan.md). Spec: [SPEC.md](../../SPEC.md). `make check` green before each commit (the pre-commit hook enforces it). Tick a box in the same commit that completes it, or in the next commit for work that is not a commit (the tag, the verification).

## Task 1: Date the changelog and draft the release notes

**Description:** Change `## 0.1.0 (unreleased)` to `## 0.1.0 (2026-11-14)` in `CHANGELOG.md` and write `tasks/release-0.1.0.md`, the GitHub release body, from the changelog and README.

**Acceptance criteria:**
- [x] `CHANGELOG.md` has `## 0.1.0 (2026-11-14)` and no `unreleased`.
- [x] The notes say what routewise does, how to install from the release archive (unpack as `routewise/`, run `routewise/install`), the requirements (Python 3.11+, bash; Claude Code 2.1.277+ for native `AGENTS.md`), what is in 0.1.0 (harnesses, five roles, `AGENTS.md` + `claude_md`, `--check`/`--uninstall`, miss log, safety rules), and link the rules spec and README.
- [x] Every claim in the notes matches the changelog and the code.

**Verification:**
- [x] `make check` green (hook)
- [x] `git show --stat HEAD` lists `CHANGELOG.md`, `tasks/release-0.1.0.md` (and the ticked task files)

**Dependencies:** the spec change and this plan committed first
**Files:** `CHANGELOG.md`, `tasks/release-0.1.0.md`, `tasks/todo.md`, `tasks/plan.md`
**Scope:** S. Commit: `docs: prepare the 0.1.0 release`

## Task 2: Create the annotated tag `v0.1.0`

**Description:** `git tag -a v0.1.0 -m "routewise 0.1.0"` on the Task 1 commit. Local only; not pushed.

**Acceptance criteria:**
- [x] `git tag -l` shows `v0.1.0`; `git cat-file -t v0.1.0` is `tag` (annotated); `git rev-list -n1 v0.1.0` is the Task 1 commit.

**Verification:**
- [x] The three commands above

**Dependencies:** Task 1
**Files:** none (a git ref)
**Scope:** XS

## Task 3: Verify the archive of `v0.1.0`

**Description:** Check the release archive as users will get it.

**Acceptance criteria:**
- [x] `git archive --prefix=routewise-0.1.0/ v0.1.0 | tar -t` holds exactly the 11 R1 entries under `routewise-0.1.0/`.
- [x] Unpacked into a fresh project as `routewise/`, `routewise/install` writes the 9 files of success criterion 2, a second run changes nothing, `--check` exits 0, and the installed `CHANGELOG.md` says `0.1.0 (2026-11-14)`.

**Verification:**
- [x] The commands above, output recorded here

Results 2026-11-14: tag `v0.1.0` is annotated (`git cat-file -t` → `tag`), tagger f0t0n, on `8dc5d4d`. The archive holds exactly `ADOPT.md CHANGELOG.md LICENSE README.md bin harness.toml install lib roles spec templates`; unpacked as `routewise/` in a fresh project, install wrote 9 files, a second run and `--check` were clean, and the shipped CHANGELOG reads `0.1.0 (2026-11-14)`.

**Dependencies:** Task 2
**Files:** `tasks/todo.md` (results)
**Scope:** XS

## Checkpoint
- [x] `make check` green; `v0.1.0` on the release commit; archive verified

## Review
- [x] `reviewer` brief (role body, sonnet, medium): the notes against `CHANGELOG.md`, `README.md` and the code
- [x] Findings fixed (re-tag if the release commit moves) or answered

Reviewed 2026-11-14 (`reviewer`, sonnet): four Required and three Optional findings, all fixed in `a1a4678`: "read-only" corrected to "no write or edit tools" with the `Bash` caveat (notes, README, CHANGELOG, SPEC S6); Explore on Haiku in 11 of 12 entries; the miss-log categories in CHANGELOG match `lib/privacy.py`; the README install table row indented; `--uninstall` says what it keeps; the `CLAUDE.md` caveat and the source of the version floors; CHANGELOG in the present tense. The fourth Optional (publish only after pushing the tag) was already the Ship order. The local tag was deleted (it was on `8dc5d4d`, never pushed) and re-created on `a1a4678`; its archive passed the Task 3 checks again.

## Ship
- [x] Maintainer, from the host: `git push origin main v0.1.0`
- [x] Maintainer: `gh release create v0.1.0 --title "routewise 0.1.0" --notes-file tasks/release-0.1.0.md`
- [x] Maintainer: download the release's "Source code" archive and check it holds the 11 runtime entries

Shipped 2026-11-14: the maintainer pushed `main` and `v0.1.0`, published the GitHub release "routewise 0.1.0" with these notes, and confirmed the downloaded "Source code" archive holds `routewise-0.1.0/` with the 11 runtime entries.
