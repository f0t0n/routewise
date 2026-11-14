# Implementation Plan: release routewise 0.1.0

Spec: [SPEC.md](../SPEC.md), "Development workflow", Ship row (amended 2026-11-14: the agent tags locally and drafts the notes when asked). Tasks: [todo.md](todo.md). Earlier plans: [done/](done/).

## Overview

routewise 0.1.0 has been "unreleased" in `CHANGELOG.md` since the first commit; everything in it is on `main` and pushed. This release dates the changelog section, drafts the GitHub release notes, creates the annotated tag `v0.1.0` locally, and checks that the tag's archive is exactly what users should get. The maintainer pushes the tag and publishes the release from the host.

## Architecture Decisions

- **Tag `v0.1.0`, annotated** (maintainer's choice): the usual name for GitHub releases; an annotated tag records who tagged and when. Message: `routewise 0.1.0`. No signing (`commit.gpgsign = false` in the sandbox; the maintainer can re-tag signed on the host if wanted).
- **Version stays `0.1.0`** in `pyproject.toml`; only `CHANGELOG.md` changes from `(unreleased)` to `(2026-11-14)`.
- **Release notes in `tasks/release-0.1.0.md`**, committed with the dated changelog in one commit, so the tag points at a tree that holds both. `tasks/` is `export-ignore`, so the notes never ship in the archive. They are written for users: what routewise does, how to install from the archive, what is in 0.1.0 (condensed from the changelog), requirements, and the link to the rules spec.
- **The tag goes on that commit**, which must pass `make check` (the hook) before it is tagged.

## Task List

- [x] Task 1: Date the changelog and draft the release notes
- [x] Task 2: Create the annotated tag `v0.1.0`
- [x] Task 3: Verify the archive of `v0.1.0`

### Checkpoint
- [x] `make check` green; tag on the release commit; archive verified

### Review, Ship
- [ ] Review: `reviewer` reads the notes against `CHANGELOG.md`, `README.md` and the code (claims true, install steps work)
- [ ] Ship: maintainer runs `git push origin main v0.1.0` and `gh release create v0.1.0 --title "routewise 0.1.0" --notes-file tasks/release-0.1.0.md` from the host, then checks the GitHub "Source code" archive

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| A review fix after tagging moves the release commit | Med | Review runs before Ship; if a fix is needed, delete the local tag (`git tag -d v0.1.0`, never pushed yet) and re-tag the new commit |
| Notes promise something the code does not do | Med | `reviewer` checks every claim; install steps are the ones Task 3 runs |
| GitHub's archive differs from `git archive` | Low | Both honour `export-ignore`; the maintainer checks the downloaded archive after publishing |

## Open Questions

None.
