# Implementation Plan: a vendored copy refuses to install into the routewise repo (R12), release 0.2.1

Spec: [SPEC.md](../SPEC.md), R12, S9 and success criterion 17 (approved 2026-11-17). Tasks: [todo.md](todo.md). Earlier plans: [done/](done/).

## Overview

`routewise/install` run inside a routewise repo (a clone, a fork, an older checkout) treats the repo as an ordinary project and rewrites its agents and delegation block with vendored spelling. R12 makes the installer refuse that case before planning, in every mode, with exit 2 and a message naming `./install --project .`. One code task, one docs task, then the 0.2.1 release.

## Architecture decisions

- **A new function in `lib/paths.py`** (`not_a_repo(root, home)` or similar), called by `lib/install.py` `run` right after `holds(root, HOME)` and before `build_plan`, so all three modes stop with nothing planned (S2). Not inside `holds`: `bin/miss-log` shares it and keeps today's behaviour (R12).
- **It applies only when `root == home.parent`** (vendored mode): the self-install (`root == home`) never reaches the four-file check, so `./install --project .` and `routewise/install --project routewise` stay allowed.
- **Detection by four paths, following symlinks:** `root/install` is a file, `root/lib/install.py` exists, `root/roles` is a folder, `root/harness.toml` exists (`Path.is_file` / `is_dir` follow links).
- **Message uses `label(home, root)`** for the copy's name, so a copy named other than `routewise` is named as the user reached it.
- **Existing `PathError`, exit 2, prefix `routewise: `**: no new error class, no exit code or marker change.
- **Tests build a repo-shaped root:** the `project` fixture's `routewise/` copy plus the same runtime files copied into the root, then `./install --project .` on the root, so the snapshot holds a real self-install that the refused run must leave byte-identical.

## Task list

### Phase 1: R12

- [x] Task 1: installer refuses a vendored install into a routewise repo
- [x] Task 2: docs: README "Safety", `AGENTS.md` S1–S9

### Checkpoint A (after Task 2)

- [ ] `make check` green; `make self` leaves no drift
- [ ] Review: `reviewer` on the R12 commits, `auditor` (S9 changed); every finding fixed or answered; mutation suggestions run

### Phase 2: Ship 0.2.1

- [ ] Task 3: version 0.2.1, dated changelog, release notes, archive check, local tag when asked

## Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| An ordinary project matches the four paths | Medium (a wrong refusal) | Four specific paths; the one known match (a release archive unpacked at the root beside `routewise/`) is refused on purpose and the message's command is right there. |
| The check runs after planning and a partial plan is written | High | It sits before `build_plan`; a test asserts no `routewise.toml` or `ROUTING-BINDING.md` appears in a fresh repo-shaped root. |
| A test passes for the wrong reason (refused by `holds`, not R12) | Medium | Tests assert the R12 message text, and the "one marker removed" tests show the same setup installs without it. |

## Open questions

None; the spec's R12 questions were decided 2026-11-17.
