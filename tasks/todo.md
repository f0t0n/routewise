# Tasks: release routewise 0.1.0

Plan: [plan.md](plan.md). Spec: [SPEC.md](../SPEC.md). `make check` green before each commit (the pre-commit hook enforces it). Tick a box in the same commit that completes it, or in the next commit for work that is not a commit (the tag, the verification).

## Task 1: Date the changelog and draft the release notes

**Description:** Change `## 0.1.0 (unreleased)` to `## 0.1.0 (2026-11-14)` in `CHANGELOG.md` and write `tasks/release-0.1.0.md`, the GitHub release body, from the changelog and README.

**Acceptance criteria:**
- [ ] `CHANGELOG.md` has `## 0.1.0 (2026-11-14)` and no `unreleased`.
- [ ] The notes say what routewise does, how to install from the release archive (unpack as `routewise/`, run `routewise/install`), the requirements (Python 3.11+, bash; Claude Code 2.1.277+ for native `AGENTS.md`), what is in 0.1.0 (harnesses, five roles, `AGENTS.md` + `claude_md`, `--check`/`--uninstall`, miss log, safety rules), and link the rules spec and README.
- [ ] Every claim in the notes matches the changelog and the code.

**Verification:**
- [ ] `make check` green (hook)
- [ ] `git show --stat HEAD` lists `CHANGELOG.md`, `tasks/release-0.1.0.md` (and the ticked task files)

**Dependencies:** the spec change and this plan committed first
**Files:** `CHANGELOG.md`, `tasks/release-0.1.0.md`, `tasks/todo.md`, `tasks/plan.md`
**Scope:** S. Commit: `docs: prepare the 0.1.0 release`

## Task 2: Create the annotated tag `v0.1.0`

**Description:** `git tag -a v0.1.0 -m "routewise 0.1.0"` on the Task 1 commit. Local only; not pushed.

**Acceptance criteria:**
- [ ] `git tag -l` shows `v0.1.0`; `git cat-file -t v0.1.0` is `tag` (annotated); `git rev-list -n1 v0.1.0` is the Task 1 commit.

**Verification:**
- [ ] The three commands above

**Dependencies:** Task 1
**Files:** none (a git ref)
**Scope:** XS

## Task 3: Verify the archive of `v0.1.0`

**Description:** Check the release archive as users will get it.

**Acceptance criteria:**
- [ ] `git archive --prefix=routewise-0.1.0/ v0.1.0 | tar -t` holds exactly the 11 R1 entries under `routewise-0.1.0/`.
- [ ] Unpacked into a fresh project as `routewise/`, `routewise/install` writes the 9 files of success criterion 2, a second run changes nothing, `--check` exits 0, and the installed `CHANGELOG.md` says `0.1.0 (2026-11-14)`.

**Verification:**
- [ ] The commands above, output recorded here

**Dependencies:** Task 2
**Files:** `tasks/todo.md` (results)
**Scope:** XS

## Checkpoint
- [ ] `make check` green; `v0.1.0` on the release commit; archive verified

## Review
- [ ] `reviewer` brief (role body, sonnet, medium): the notes against `CHANGELOG.md`, `README.md` and the code
- [ ] Findings fixed (re-tag if the release commit moves) or answered

## Ship
- [ ] Maintainer, from the host: `git push origin main v0.1.0`
- [ ] Maintainer: `gh release create v0.1.0 --title "routewise 0.1.0" --notes-file tasks/release-0.1.0.md`
- [ ] Maintainer: download the release's "Source code" archive and check it holds the 11 runtime entries
