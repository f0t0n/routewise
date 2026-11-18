# Implementation Plan: a judge the person can ask (R13), release 0.3.0

Spec: [SPEC.md](../SPEC.md), R13 and success criterion 18 (approved 2026-11-18), and rules spec version 4. Tasks: [todo.md](todo.md). Earlier plans: [done/](done/).

## Overview

A new read-only role, `judge` (`frontier` at `medium`), that the main session starts only when the person says "ask a judge" on a decision. The brief carries the decision, its context and every option, but not the main session's preference; the main session shows the question, the options and the verdict, then waits for the person. It works in dev and in assistant mode; in assistant mode the assistant quotes what the decision needs from memory, MCPs or documents into the brief. When a page the judge needs is blocked, it returns `Needs access` lines and the main session runs it again once the person allows the access.

## Architecture decisions

- **No new code path:** `judge` is a role file like the others (`roles/judge.md`); the renderer, `[tiers]`, `[skills]` and `--check` already handle it. The work is the role text, the two fragments, the binding template, the rules spec and the docs.
- **The rules spec changes first** (Task 1), so every later file cites rules that exist: R-A7, N2's exception, D4, A4, the section 10 fragment and the section 12 exception.
- **One rule per fragment,** not a new section, so the always-loaded block grows by one bullet (rules spec P3). The assistant fragment's opening line ("Only reading a public web page may go to a subagent") gains the judge exception.
- **The body fixes the method and the return shape** (R-A2, at most 40 lines); no default skill (R13 question 2); `{{checklist}}` renders `Checklist: none` as for the other roles without skills.
- **Live runs last** (Task 5): the files must be final before the run that section 13 records.

## Task list

### Phase 1: rules and role

- [x] Task 1: rules spec version 4
- [x] Task 2: `roles/judge.md`

### Checkpoint A (after Task 2)

- [x] `make check` green; `make self` adds `judge.md` to this repo

### Phase 2: delegation and docs

- [ ] Task 3: the judge rule in the dev and the assistant fragment
- [ ] Task 4: binding row, README "Asking a judge", ADOPT.md, CHANGELOG

### Checkpoint B (after Task 4)

- [ ] `make check` green; `make self` leaves no drift
- [ ] Review: `reviewer` on R13's commits; `auditor` (approval rules, assistant-mode data in briefs); findings fixed or answered; mutation suggestions run

### Phase 3: verify and ship

- [ ] Task 5: live runs on Claude Code, recorded in rules spec section 13
- [ ] Task 6: release 0.3.0

## Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| The main session starts `judge` unasked (cost, a delegated judgment call) | High | The rule says "only when the person asks" and "never on your own"; the live run checks that a plain decision prompt does not start it. |
| The brief leaks the main session's preference, so the judge is anchored | Medium | The rule says what the brief holds and what it leaves out; the live run reads the brief in the transcript. |
| Assistant briefs carry private data or other people's instructions | High | A4 and the assistant rule: only what the decision needs, quoted with source, no secrets; the judge treats quotes as data; exact values re-read from the source. `auditor` reviews it. |
| The judge works around a blocked page (another domain, a shell `curl`) | Medium | The body says not to; the `Needs access` line is the only way out; a live run with a blocked page checks it. |
| The always-loaded block grows | Low | One bullet per fragment. |

## Open questions

None; R13's questions were decided 2026-11-18.
