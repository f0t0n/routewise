# Implementation Plan: release archive (R1), routewise on its own repo (R2), commands spelled per project (R3), workflow docs

Spec: [SPEC.md](../../SPEC.md), approved 2026-11-14 (R1, R2, S9, success criteria 5–8, decisions 1–5); amended the same day with R3 (Tasks 5–6), found while building R2. Tasks: [r1-r3-todo.md](r1-r3-todo.md).

## Overview

Four small changes, built in the order that keeps every commit green: commit the approved spec and this plan; record the 2026-11-14 live check of the `@AGENTS.md` bridge in rules spec section 13; let the installer and the miss log accept the routewise folder itself as the project (S9) and install routewise on this repo (R2); then mark every development file `export-ignore` with a test that ties the shipped files to the tested ones (R1). Then Verify, Review and Ship per the workflow.

## Architecture Decisions

- **S9 is one line in `paths.holds`:** accept `root == home` as well as `root in home.parents`. Both tools already call `holds`, and every path is built relative to `root`, so a self-install spells `bin/miss-log` and `roles/x.md` with no other change. `--project ~` and any unrelated folder stay refused.
- **Self-install is always explicit: `./install --project .`, wrapped as `make self`.** The default project is the folder that holds routewise/ (right for vendored copies), which in this repo is the folder above it. No auto-detection: a submodule and a source clone look alike, and guessing wrong would write outside the repo. `AGENTS.md` and SPEC.md say never to run a bare `./install` here.
- **Drift check in the hook:** a `self` target writes, a `selfcheck` target (`./install --project . --check`) joins `make check`, so the pre-commit hook blocks a role, template or `harness.toml` change that was not re-installed.
- **One list of runtime files:** `tests/conftest.py` `COPY` (plus the four shipped docs) is the source of truth. A new `tests/test_release.py` compares it with `git ls-files` minus `export-ignore` (via `git check-attr`), so the shipped set cannot drift from the tested set. The test skips outside a git checkout (for example an extracted archive).
- **Self-install settings:** `harnesses = ["cc"]` (no `.agents/` here), `fragment = "dev"`, `cap = 5`, `claude_md = "auto"` (no CLAUDE.md in the repo, so no import block), the default miss log `logs/delegation-misses.jsonl`, committed.
- **Review without the new agents in this session:** generated agents load when a Claude Code session starts, so this session cannot start `reviewer` or `auditor` by name. The review briefs a subagent with the role file's body and its tier as the model (`reviewer`: sonnet, `auditor`: opus), which is what the generated agent would be.

- **R3: one function spells the re-install command,** `rerun(root)` in `install.py`: `./install --project .` when the project is the routewise folder, otherwise `label(HOME / "install", root)` (normally `routewise/install`). `block.start_line(command)` builds the start marker and `block.START` stays as `start_line("routewise/install")`, so the vendored output and every existing test are byte-identical; `block.insert` takes the start line as an argument with `START` as the default. `roles.render` takes the command for the agent marker. Detection (`START_KEY`, `MARKER_LINE`) does not change.
- **R3 in the binding:** `templates/binding.md` gets `{{install}}`, `{{roles}}`, `{{harness}}` and `{{miss_log}}` placeholders, filled in `plan_first_run` with the same `label(...)` calls already used for `{{spec}}`. The binding is written on the first run only, so this repo's hand-corrected binding is untouched.

## Task List

### Phase 1: Foundation
- [x] Task 0: Commit the approved spec, agent instructions and plan
- [x] Task 1: Record the `@AGENTS.md` live check in rules spec section 13

### Checkpoint A
- [x] `make check` green; two commits on `main`

### Phase 2: routewise on its own repo
- [x] Task 2: S9, accept the routewise folder itself as the project (install and miss-log)
- [x] Task 3: Install routewise on this repo (`make self`, drift check in `make check`)

### Checkpoint B
- [x] `make check` green including the self drift check; a deliberately unre-installed role change fails it (then reverted)

### Phase 3: Release archive
- [x] Task 4: `export-ignore` every development file, one-list test, README install from the archive

### Phase 4: Commands spelled per project (R3)
- [x] Task 5: The start marker and the agent marker name the project's own re-install command
- [x] Task 6: The binding template spells routewise paths from the project root

### Checkpoint C (end of Build)
- [x] `make check` green; all SPEC.md success criteria for R1, R2 and R3 met

### Verify, Review, Ship
- [x] Verify: `make check`; `git archive HEAD | tar -t` lists exactly the R1 runtime files; a fresh project installed from that archive passes success criterion 2
- [x] Review: `reviewer` (sonnet, medium) on the whole change; `auditor` (opus, high) on S9 and `.gitattributes`; every Critical and Required finding fixed in its own commit
- [x] Ship: `CHANGELOG.md` complete, archive contents confirmed, commits ready; the maintainer pushes from the host

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| A bare `./install` in this repo writes into the folder above | High | `make self` only; SPEC.md and `AGENTS.md` forbid the bare command; Task 3 verifies `git status` of the parent is untouched |
| S9 loosens the rule that keeps writes away from `--project ~` | High | Only `root == home` is added; the existing refusal test stays, and `auditor` reviews the change |
| A new development file is committed without `export-ignore` and ships | Med | `test_release.py` fails on any tracked file that is neither runtime nor ignored |
| The self drift check makes every commit slower | Low | One extra `--check` run, under a second |
| CLAUDE files above the maintainer's clone print warnings during `make check` | Low | Warnings do not change the exit code; noted, not suppressed |
| `.claude/agents/` in this repo changes the agents a Claude Code session here uses | Low | Intended (dogfooding): the generated `Explore` replaces the built-in one, as the live checks showed |
| R3 changes the marker text of files already written | Low | Only the trailing command changes; detection keys are untouched and tested (an old-format agent and block are still recognised and rewritten once) |

## Open Questions

None. (Approver confirmed: `f0t0n (maintainer), 2026-11-14`. No history rewrite for the `.obsidian/` files committed in `c7a9b93`.)
