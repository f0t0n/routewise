# Implementation Plan: copy-paste install in the README (R4)

Spec: [SPEC.md](../SPEC.md), R4, success criterion 9, Ship row (approved 2026-11-14, after the 0.1.0 release). Tasks: [todo.md](todo.md). Earlier plans: [done/](done/).

## Overview

The 0.1.0 release notes have a four-line install; the README only describes it in prose. Add the same block to the top of the README's "Install into a project", with the version in one `v=` variable, and a test that keeps that version equal to `pyproject.toml`. Docs only; it reaches users in the next release's archive (the 0.1.0 notes already carry the commands).

## Architecture Decisions

- **The test reads the README** (`tests/test_release.py`, next to the archive test): find the `v=<version>` line inside the shell block under "## Install into a project", compare with `version` from `pyproject.toml` (read with `tomllib`). No templating, no generated README. The test skips nothing: both files are in every checkout.
- **Block content** follows the release notes, with `$v`: "From the project root:" then `v=0.1.0`, `curl -L "https://github.com/f0t0n/routewise/archive/refs/tags/v$v.tar.gz" | tar -xz`, `mv "routewise-$v" routewise`, `routewise/install`. The existing step 1 prose stays as the explanation (archive contents, submodule caveat), and the steps after it are unchanged.
- **No new tag.** The change rides with the next release; the maintainer pushes `main`.

## Task List

- [x] Task 1: README install block and the version test

### Checkpoint
- [x] `make check` green

### Verify, Review, Ship
- [ ] Verify: the block, copied from the README and run literally in an empty git repo, installs routewise 0.1.0 from GitHub (9 files, `--check` exit 0)
- [ ] Review: `reviewer` on the README diff and the test
- [ ] Ship: maintainer pushes `main` from the host

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| The test finds the wrong `v=` line, or none | Med | It requires exactly one `v=` line inside the first shell block of the install section, and fails with a clear message otherwise |
| `curl \| tar` differs between macOS and Linux | Low | Both ship bsdtar or GNU tar with `-xz`; Verify runs it on Linux, and the maintainer already unpacked the archive on macOS |
| The block is run inside an existing install (`routewise/` exists) | Low | `mv` then fails without overwriting; updating is a separate README section ("Updating") |

## Open Questions

None.
