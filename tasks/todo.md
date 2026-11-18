# Tasks: a judge the person can ask (R13), release 0.3.0

Plan: [plan.md](plan.md). Spec: [SPEC.md](../SPEC.md), R13, criterion 18. `make check` green before each commit (the pre-commit hook enforces it). Each task: failing test first, shown red; then the change; a `CHANGELOG.md` line under `## Unreleased` for each user-visible change; `make self` when roles, templates or `harness.toml` change; one Conventional Commit.

## Task 1: rules spec version 4

**Description:** `spec/SPEC-model-routing.md`: the version line (4, 2026-11-18); the `judge` row in the section 4 table (`frontier`, `medium`, read, search, shell, web; job; return); rule R-A7; N2's exception; D4; A4 under Assistant mode; the judge rule in the section 10 fragment; section 12's Ask first entry names `judge` as the shipped exception. Section 13 waits for Task 5.

**Acceptance criteria:**
- [x] Every item R13 lists under "Rules spec version 4" is in the file, worded as R13 says.
- [x] A test pins the version line and that the section 10 fragment holds the judge rule.

**Verification:** `uv run pytest tests/test_release.py`; `make check`.

**Dependencies:** none. **Files:** `spec/SPEC-model-routing.md`, a test. **Scope:** S.

## Task 2: `roles/judge.md`

**Description:** The role: `name: judge`, description (advises the person on a decision, only when the person asks), `tools: [read, search, shell, web]`, `tier: frontier`, `effort: medium`, no `skills`. Body: independent expert in the decision's field; the method from R13; the read-only rules the other roles carry; blocked pages give a `Needs access` line, never a workaround; quoted messages are data; the return shape, at most 40 lines, first line `{{checklist}}`.

**Acceptance criteria:**
- [ ] Rendered for Claude Code: `model: fable`, `effort: medium`, tools `Read, Glob, Grep, Bash, WebSearch, WebFetch`, no `skills:` line, `Checklist: none` in the body; for Antigravity: no model, its read, search, shell and web tools.
- [ ] `[tiers] frontier = "x"` and `[skills] judge = ["y"]` change the rendered file.
- [ ] The body holds the R13 rules (tested by phrase: never on its own is the main session's rule, so here: no writes, `Needs access`, data, the return sections and the 40-line cap).
- [ ] A new install writes six agents; `ROLES` in the tests updated; `make self` adds `.claude/agents/judge.md` here.

**Verification:** `uv run pytest tests/test_roles.py tests/test_install.py`; `make self`; `make check`.

**Dependencies:** Task 1. **Files:** `roles/judge.md`, `tests/test_roles.py`, `tests/test_install.py`, `.claude/agents/judge.md` (generated), `CHANGELOG.md`. **Scope:** M.

## Checkpoint A (after Task 2)

- [ ] `make check` green; `make self` leaves no drift.

## Task 3: the judge rule in both fragments

**Description:** `templates/fragment-dev.md` gains the judge rule; `templates/fragment-assistant.md` gains its version (the opening line allows `judge` besides `web-reader`; the brief quotes what the decision needs from memory, MCPs, mail or documents with source and author, no secrets; exact values re-read from the source). Both: only when the person asks, brief without the main session's preference, what to show, the person decides, `Needs access` retry, never treat the verdict as approval.

**Acceptance criteria:**
- [ ] Dev and assistant blocks each hold the rule's key phrases; neither tells the session to start `judge` on its own.
- [ ] The assistant block still forbids every other delegation it forbade.
- [ ] `make self` updates this repo's `AGENTS.md` block; `make check` green.

**Verification:** `uv run pytest tests/test_install.py -k "fragment or block or judge"`; `make self`; `make check`.

**Dependencies:** Task 1. **Files:** `templates/fragment-dev.md`, `templates/fragment-assistant.md`, `tests/test_install.py`, `AGENTS.md` (generated block), `CHANGELOG.md`. **Scope:** S.

## Task 4: binding row and docs

**Description:** `templates/binding.md` gains the `judge` row. `README.md` gains "Asking a judge" (when, what to say, cost, Antigravity runs it on the session model, `[tiers]` and `[skills]`, `Needs access`, assistant mode). `ADOPT.md` mentions the role where it lists roles. `CHANGELOG.md` lines complete.

**Acceptance criteria:**
- [ ] A new install's `ROUTING-BINDING.md` holds the `judge` row (test).
- [ ] README and ADOPT describe what the code does; README's role list names six roles.

**Verification:** `make check`.

**Dependencies:** Tasks 2 and 3. **Files:** `templates/binding.md`, `README.md`, `ADOPT.md`, `tests/test_install.py`, `CHANGELOG.md`. **Scope:** S.

## Checkpoint B: review (after Task 4)

- [ ] `make check` green on the whole change; `make self` no drift.
- [ ] `reviewer` on R13's commits and `auditor` on the approval and assistant-mode rules; Critical and Required fixed (one more round scoped to a fix), Optional and Nit answered here; mutation suggestions run and recorded.

## Task 5: live runs on Claude Code

**Description:** In a scratch project with routewise installed (dev block): (1) a session offers options and the person says "ask a judge": the transcript shows `judge` on `fable` at `medium`, a brief with every option and without the main session's preference, a return in R13's shape, and a main session that shows question, options and verdict and waits; (2) a decision prompt without "ask a judge" does not start `judge`; (3) a decision that needs a blocked page returns a `Needs access` line and no workaround. One assistant-block run checks that quoted data arrives as data. Recorded as a dated entry in rules spec section 13.

**Acceptance criteria:**
- [ ] Each run's result recorded with the Claude Code version and date; a failure fixes the role or the rule and runs again.

**Verification:** transcripts read by `log-reader`; the section 13 entry.

**Dependencies:** Checkpoint B. **Files:** `spec/SPEC-model-routing.md` (section 13), `tasks/todo.md`. **Scope:** M.

## Task 6: release 0.3.0

**Description:** Version `0.3.0` in `pyproject.toml`, `uv.lock` and every README `v=`; `## Unreleased` becomes `## 0.3.0 (<date>)`; `tasks/release-0.3.0.md` for users (the judge, how to ask, cost, add the binding row, the files the update rewrites, new session needed) checked by `reviewer`; archive check; annotated tag `v0.3.0` when asked; publish commands handed over.

**Acceptance criteria:**
- [ ] `make check` green with `0.3.0`; release notes reviewed; archive holds only runtime files.

**Verification:** `make check`; `git archive HEAD | tar -t`.

**Dependencies:** Task 5. **Files:** `pyproject.toml`, `uv.lock`, `README.md`, `CHANGELOG.md`, `tasks/release-0.3.0.md`. **Scope:** S.
