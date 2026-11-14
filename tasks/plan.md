# Implementation Plan: miss-log privacy fix and error prefix, release 0.1.1 (R5, R6)

Spec: [SPEC.md](../SPEC.md), R5, S7, success criterion 10 (approved 2026-11-14); R6, success criterion 11 and the Ship row (release notes for every release), approved 2026-11-14 after Task 2. Tasks: [todo.md](todo.md). Earlier plans: [done/](done/).

## Overview

A catch-up plan. The fix (`44376cb`) and the release bump (`bcc480f`) were built before Define and Plan, which were skipped; the spec (`4290752`) has since been approved. This plan does not rebuild the code. It closes what the workflow still owes before the tag: proof that the tests were written to fail first, an end-to-end check of `bin/miss-log`, a review and audit of the final change, and the ship checks. Any fix found on the way is a new `fix:` commit made test first; history is not rewritten.

Extended after Task 2: R6 (bin/miss-log printed `miss-log: ` instead of `routewise: `) is built here, test first, before the review, so the review covers it; and 0.1.1 gets release notes, which the Ship row now asks for every release.

## Architecture Decisions

- **Red is proven against the old code, not by reverting the repo.** Task 1 runs today's `tests/test_privacy.py` against `lib/privacy.py` from `v0.1.0` and from `50f9de1` (the first fix, before review; squashed into `44376cb`, still reachable), each copied into a scratch folder, so the working tree is never changed.
- **Review covers the whole change** `v0.1.0..HEAD` restricted to `lib/`, `tests/`, `README.md`, `CHANGELOG.md` and `SPEC.md`, with a fresh `reviewer` and a fresh `auditor` (S7 is a safety rule), started together. Neither is told the earlier findings, so they are not anchored on them.
- **R6 is two strings in `lib/miss_log.py` `main`**, pinned by a test that asserts the prefix (the existing tests only check the text after it). The file-error branch (`OSError`) is covered by a test that makes the log path a folder, if that reaches the branch without a symlink or permission trick; otherwise it is checked by reading the code and named in the record.
- **Release notes are reviewed with the change:** `reviewer` in Task 5 also reads `tasks/release-0.1.1.md` against `CHANGELOG.md` and the code, so they are drafted before the review (Task 10 re-checks them after any fix).
- **The tag goes on the last commit of this plan** (decision 6 of the spec gate). `SPEC.md` and `tasks/` are `export-ignore`, so commits after `bcc480f` do not change what the archive ships unless a fix lands.
- **The maintainer tags and pushes** from the host; this plan only states the exact commands.

## Task List

- [x] Task 1: Prove the new tests fail first
- [x] Task 2: End-to-end check of `bin/miss-log`
- [x] Checkpoint: verified
- [x] Task 3: R6, one error prefix in `bin/miss-log`
- [x] Task 4: Draft the 0.1.1 release notes
- [ ] Task 5: Review and audit of the final change and the notes
- [x] Task 6: Fix the review findings
- [ ] Task 7: Re-review the fix
- [ ] Task 8: Fix the re-review findings
- [ ] Task 9: Re-review the second fix
- [ ] Checkpoint: reviewed
- [ ] Task 10: Ship checks and the tag commands

Extended after round 1 of the review (2026-11-14): Task 6 fixes the findings the maintainer approved (R5 amended in `6665dff`), Task 7 re-reviews that fix, since it changes the filter again.

Extended after round 2 (2026-11-14): `1aa6725` introduced two regressions (removing an invisible character joined a token to the word before it; decoding `%40` hid a link). Task 8 replaces the single normalised copy with two views (R5 amended in `51c13dc`), and Task 9 re-reviews; the auditor compares against both earlier versions.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| A post-review test already passes on `50f9de1` (no red) | Low | Recorded as a regression guard, not a test-first proof; it must still fail on `v0.1.0` or be named in the record |
| Review or audit finds a new leak or false positive | Med | Fix in a new `fix:` commit, test first with red shown; a change to an R5 or R6 decision goes back to the spec gate first |
| A fix after `bcc480f` changes shipped files | Low | Task 10 re-checks the archive and `make check` on the final commit; the CHANGELOG 0.1.1 line is updated in the same fix commit |
| `50f9de1` is garbage-collected | Low | Task 1 runs first; the commit is in the reflog |
| A review fix loosens the filter or breaks an allowed phrase | Med | No allowed case is removed or moved; red shown for each new leak; Tasks 7 and 9 re-audit |
| A normalisation step hides what another step would find (happened in `1aa6725`) | High | Two views, refuse if either matches; a guard test runs every refused case behind invisible characters; Task 9 compares against both earlier versions on fuzzed input |
| The notes promise something the code does not do | Med | `reviewer` checks every claim against the code; the update steps are the README's, which R4's test keeps on the current version |

## Open Questions

None. (Release notes: answered by the Ship row change; they are drafted for every release.)
