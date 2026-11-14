# Implementation Plan: miss-log privacy fix, release 0.1.1 (R5)

Spec: [SPEC.md](../SPEC.md), R5, S7, success criterion 10 (approved 2026-11-14). Tasks: [todo.md](todo.md). Earlier plans: [done/](done/).

## Overview

A catch-up plan. The fix (`44376cb`) and the release bump (`bcc480f`) were built before Define and Plan, which were skipped; the spec (`4290752`) has since been approved. This plan does not rebuild the code. It closes what the workflow still owes before the tag: proof that the tests were written to fail first, an end-to-end check of `bin/miss-log`, a review and audit of the final change, and the ship checks. Any fix found on the way is a new `fix:` commit made test first; history is not rewritten.

## Architecture Decisions

- **Red is proven against the old code, not by reverting the repo.** Task 1 runs today's `tests/test_privacy.py` against `lib/privacy.py` from `v0.1.0` and from `50f9de1` (the first fix, before review; squashed into `44376cb`, still reachable), each copied into a scratch folder, so the working tree is never changed.
- **Review covers the whole change** `v0.1.0..HEAD` restricted to `lib/`, `tests/`, `README.md`, `CHANGELOG.md` and `SPEC.md`, with a fresh `reviewer` and a fresh `auditor` (S7 is a safety rule), started together. Neither is told the earlier findings, so they are not anchored on them.
- **The tag goes on the last commit of this plan** (decision 6 of the spec gate). `SPEC.md` and `tasks/` are `export-ignore`, so commits after `bcc480f` do not change what the archive ships unless a fix lands.
- **The maintainer tags and pushes** from the host; this plan only states the exact commands.

## Task List

- [ ] Task 1: Prove the new tests fail first
- [ ] Task 2: End-to-end check of `bin/miss-log`
- [ ] Checkpoint: verified
- [ ] Task 3: Review and audit of the final change
- [ ] Checkpoint: reviewed
- [ ] Task 4: Ship checks and the tag commands

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| A post-review test already passes on `50f9de1` (no red) | Low | Recorded as a regression guard, not a test-first proof; it must still fail on `v0.1.0` or be named in the record |
| Review or audit finds a new leak or false positive | Med | Fix in a new `fix:` commit, test first with red shown; a change to an R5 decision goes back to the spec gate first |
| A fix after `bcc480f` changes shipped files | Low | Task 4 re-checks the archive and `make check` on the final commit; the CHANGELOG 0.1.1 line is updated in the same fix commit |
| `50f9de1` is garbage-collected | Low | Task 1 runs first; the commit is in the reflog |

## Open Questions

1. Draft release notes in `tasks/release-0.1.1.md` (as for 0.1.0), or does the CHANGELOG entry suffice?
