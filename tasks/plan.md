# Implementation Plan: miss-log gaps, release 0.1.2 (R7)

Spec: [SPEC.md](../SPEC.md), R7, success criterion 12 (approved 2026-11-14), with R5's rules and the Review stopping rule. Tasks: [todo.md](todo.md). Earlier plans: [done/](done/).

## Overview

0.1.1 shipped with a list of gaps for 0.1.2. R7 closes six of them, each a small change to `lib/privacy.py`, and keeps every other R5 rule as it is. The bar: nothing 0.1.1 refuses passes, and nothing it allows is refused, except what R7 names. Lessons from 0.1.1 shape the plan: one item per task, red shown against 0.1.1 before each fix, a differential check of 0.1.1 against HEAD on the whole test set at the checkpoint, Unicode claims checked on every code point, mutations with an unmutated control and each mutant checked to import, and one review round under the stopping rule.

## Architecture Decisions

- **One task per R7 item, riskiest first** (maintainer, at the spec gate): G1 changes about eight patterns; the others touch one pattern or the link end each.
- **ASCII boundaries as named constants** (G1): `WORD_START = r"(?<![A-Za-z0-9_])"` and `WORD_END = r"(?![A-Za-z0-9_])"` replace `\b` in the patterns R7 lists, so the rule reads once and every pattern uses it.
- **No new view and no new normalisation step.** G2 is a pattern change, G4 (JWT) reads `。` inside the token rule only, and the link end is one character class. R5's views stay as they are, so the regressions of 0.1.1's rounds 2 and 3 cannot come back through R7.
- **Differential check against 0.1.1:** a small script in the scratchpad (not in the repo) loads the `lib/privacy.py` of `daa469d` (tagged `v0.1.1` on the host; the tag is not in this sandbox) and HEAD's and runs both on every input in `tests/test_privacy.py`; each difference must be an R7 item. It runs at the checkpoint and in the review.
- **The 0.1.1 test lists keep their meaning:** a case moves only when R7 says so (the full-width `？` phrases move from `REFUSED_CODE_WORDS` to allowed; `wiki.corp.io#Раздел` goes to `KEPT_GAPS`).
- **Release:** `0.1.2` with a dated CHANGELOG section, notes in `tasks/release-0.1.2.md`, README `v=` lines bumped; the maintainer tags and pushes.

## Task List

- [x] Task 1: G1, ASCII word boundaries
- [x] Task 2: G2, URL-encoded scheme
- [x] Task 3: G3, a backslash before a dotless `@`
- [x] Task 4: a JWT written with `。`
- [x] Task 5: link ends `$`, `!/`, `:~:`, ASCII after `?` and `#`
- [ ] Checkpoint: verified (make check, differential check against 0.1.1)
- [ ] Task 6: Docs and release notes for 0.1.2
- [ ] Task 7: Release bump to 0.1.2
- [ ] Task 8: Review, one round under the stopping rule
- [ ] Checkpoint: reviewed
- [ ] Task 9: Ship checks and the tag commands

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| ASCII boundaries refuse text 0.1.1 allowed beyond what R7 names (accented Latin before a number, for example) | Med | The differential check lists every such case; each is named in the CHANGELOG or the boundary is narrowed; R7 already names `café10.0.0.12`-style text |
| A fix of one item breaks another 0.1.1 rule | Med | One item per task, the whole test set after each, the differential check at the checkpoint |
| The review loop grows again | Med | Stopping rule: one round; Optional findings and old gaps go to the next release |
| A Unicode or mutation result is wrong because of the check itself (happened four times in 0.1.1) | Med | Unicode claims checked on every code point; mutants checked to import; a control equal to the repo; one case per character |

## Open Questions

None. (Scope and order were set at the spec gate.)
