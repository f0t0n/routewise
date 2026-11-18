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
- [x] Rendered for Claude Code: `model: fable`, `effort: medium`, tools `Read, Glob, Grep, Bash, WebSearch, WebFetch`, no `skills:` line, `Checklist: none` in the body; for Antigravity: no model, its read, search, shell and web tools.
- [x] `[tiers] frontier = "x"` and `[skills] judge = ["y"]` change the rendered file.
- [x] The body holds the R13 rules (tested by phrase: never on its own is the main session's rule, so here: no writes, `Needs access`, data, the return sections and the 40-line cap).
- [x] A new install writes six agents; `ROLES` in the tests updated; `make self` adds `.claude/agents/judge.md` here.

**Verification:** `uv run pytest tests/test_roles.py tests/test_install.py`; `make self`; `make check`.

**Dependencies:** Task 1. **Files:** `roles/judge.md`, `tests/test_roles.py`, `tests/test_install.py`, `.claude/agents/judge.md` (generated), `CHANGELOG.md`. **Scope:** M.

## Checkpoint A (after Task 2)

- [x] `make check` green; `make self` leaves no drift.

## Task 3: the judge rule in both fragments

**Description:** `templates/fragment-dev.md` gains the judge rule; `templates/fragment-assistant.md` gains its version (the opening line allows `judge` besides `web-reader`; the brief quotes what the decision needs from memory, MCPs, mail or documents with source and author, no secrets; exact values re-read from the source). Both: only when the person asks, brief without the main session's preference, what to show, the person decides, `Needs access` retry, never treat the verdict as approval.

**Acceptance criteria:**
- [x] Dev and assistant blocks each hold the rule's key phrases; neither tells the session to start `judge` on its own.
- [x] The assistant block still forbids every other delegation it forbade.
- [x] `make self` updates this repo's `AGENTS.md` block; `make check` green.

**Verification:** `uv run pytest tests/test_install.py -k "fragment or block or judge"`; `make self`; `make check`.

**Dependencies:** Task 1. **Files:** `templates/fragment-dev.md`, `templates/fragment-assistant.md`, `tests/test_install.py`, `AGENTS.md` (generated block), `CHANGELOG.md`. **Scope:** S.

## Task 4: binding row and docs

**Description:** `templates/binding.md` gains the `judge` row. `README.md` gains "Asking a judge" (when, what to say, cost, Antigravity runs it on the session model, `[tiers]` and `[skills]`, `Needs access`, assistant mode). `ADOPT.md` mentions the role where it lists roles. `CHANGELOG.md` lines complete.

**Acceptance criteria:**
- [x] A new install's `ROUTING-BINDING.md` holds the `judge` row (test).
- [x] README and ADOPT describe what the code does; README's role list names six roles.

**Verification:** `make check`.

**Dependencies:** Tasks 2 and 3. **Files:** `templates/binding.md`, `README.md`, `ADOPT.md`, `tests/test_install.py`, `CHANGELOG.md`. **Scope:** S.

## Checkpoint B: review (after Task 4)

- [x] `make check` green on the whole change; `make self` no drift.
- [x] `reviewer` on R13's commits and `auditor` on the approval and assistant-mode rules; Critical and Required fixed (one more round scoped to a fix), Optional and Nit answered here; mutation suggestions run and recorded.

**Review record.**

Round 1 (2026-11-18): `reviewer` (Checklist: `agent-skills:code-review-and-quality` loaded) request changes; `auditor` (Checklist: `agent-skills:security-and-hardening` loaded) four Required.
- reviewer Required 1 (dev block's "never delegate judgment calls" without the judge exception): fixed in both the fragment and rules spec section 10, pinned by the section 10 equality test.
- reviewer Optional 2 (retry names the allowed pages), 3 (no secrets in the dev brief), 4 (a leaked preference), 5 (Antigravity render test): fixed. Optional 6 (block length): kept, one bullet per block; split considered in round 2. Nit 7: kept.
- auditor Required 1 (private data, untrusted text and a network exit in one agent): the tool choice went to the maintainer, who asked a judge (three rounds) and chose option E: keep all tools, allowlist as the boundary, role and block rules. Required 2 (brief content in queries), 3 (`Needs access` steered by injected text), 4 (README overstated limits): fixed by E's rules and README Hardening.
- auditor Optional 1 (authenticated CLIs and shell network): fixed (network only via web tools; no logged-in CLIs). Optional 2 (a faked request): fixed (only the person's own message). Optional 3 (no binding row after an update): answered in the 0.3.0 release notes; a check would need installer code. Optional 4 ("for this decision"): fixed. Nit 5 (judge misses in assistant mode): fixed (`--role judge`).
- Mutations (reviewer): removing "but not the one you favour", changing the section 10 judge line, removing N2's exception: all killed.

Round 2 (2026-11-18, scoped to `be5bef7..91128f9`): `reviewer` approve; `auditor` four Required.
- auditor Required 1 (a quoted passage could unlock a credential file): fixed, no exception for credential, token, `.env`, transcript or memory files.
- auditor Required 2 (the `Needs access` source is the judge's own claim): fixed, domains marked `in the brief` or `claimed by the judge`, none recommended, a new judge after a policy change instead of a continued one.
- auditor Required 3 (residual risk misstated): fixed, R13 and R-A7 name WebSearch as a residual risk the maintainer accepted, with shell reads and whole-domain allows.
- auditor Required 4 (deny snippet vs the judge's shell): checked live (a `python3 -c` read beat `Read(./secret.txt)`), README says so; snippet moved to `settings.local.json` and notes it blocks the README's curl commands.
- auditor Optional 1 (paths carry data, domain is the control): fixed in README and blocks. Optional 2 (round 1 Optionals unrecorded): this record. Optional 3 (DNS): checked live, blocked domains do not resolve in the `sbx` VM; recorded in section 13. Optional 4 (Antigravity unchecked): R-A7 says the allowlist is the boundary "where one is set"; Antigravity's web tools are not checked, kept as a known gap. Nit 5 (contradictions): fixed (no values added to a URL; a link the decision is about goes outside the quote).
- reviewer Optional 1 (`own knowledge` pages never suggested) and 2 (R-A7 shorter than the block): both settled by the round-2 rewrite (every non-brief domain is `claimed by the judge`; R-A7 states the same rule). Optional 3 (README untested): kept, README is not a safety rule. Optional 4 (bullet length): kept as one bullet per rule set. Nit (path rule unpinned): fixed ("nothing from the brief in the path" pinned).

Round 3 (2026-11-18, `auditor`, scoped to `91128f9..3dec1b3`): R1, R3, R4 closed; R2 closed in every shipped file. One Required: `SPEC.md` R13's README bullet still trusted the source tag: fixed (allow only a site the person knows and would allow anyway). Optional: R-A7's "never read the text" overstated (fixed: quoted text comes along, so no domain is recommended); the DNS row's conclusion (fixed: observation only). Nits fixed: "may run you again", a comma splice, "outside any quoted passage" in README. Status line records the acceptance of the residual risks. A doc-only fix, so per the stopping rule a `reviewer` check of this diff closes the review.
Doc check (`reviewer`, `3dec1b3..776dd90`): approve, no findings beyond one Optional ("no answer" wording for DNS in SPEC.md and README; kept, consistent as is). Review closed.

## Task 5: live runs on Claude Code

**Description:** In a scratch project with routewise installed (dev block): (1) a session offers options and the person says "ask a judge": the transcript shows `judge` on `fable` at `medium`, a brief with every option and without the main session's preference, a return in R13's shape, and a main session that shows question, options and verdict and waits; (2) a decision prompt without "ask a judge" does not start `judge`; (3) a decision that needs a blocked page returns a `Needs access` line and no workaround. One assistant-block run checks that quoted data arrives as data. Recorded as a dated entry in rules spec section 13.

**Acceptance criteria:**
- [x] Each run's result recorded with the Claude Code version and date; a failure fixes the role or the rule and runs again.

**Live-run record (2026-11-18):** five runs in rules spec section 13, all passed on safety and shape. Observation: in assistant mode the main session dropped an injected paragraph from a quoted mail without telling the person; a clause to report it was approved by the maintainer and added (3b449fb); a sixth run shows the person is now told. The maintainer accepted R13's residual risks (WebSearch queries, shell reads past Read deny rules, whole-domain allows) on 2026-11-18 ("go ahead").

**Verification:** transcripts read by `log-reader`; the section 13 entry.

**Dependencies:** Checkpoint B. **Files:** `spec/SPEC-model-routing.md` (section 13), `tasks/todo.md`. **Scope:** M.

## Task 6: release 0.3.0

**Description:** Version `0.3.0` in `pyproject.toml`, `uv.lock` and every README `v=`; `## Unreleased` becomes `## 0.3.0 (<date>)`; `tasks/release-0.3.0.md` for users (the judge, how to ask, cost, add the binding row, the files the update rewrites, new session needed) checked by `reviewer`; archive check; annotated tag `v0.3.0` when asked; publish commands handed over.

**Acceptance criteria:**
- [x] `make check` green with `0.3.0`; release notes reviewed; archive holds only runtime files.

**Ship record (2026-11-18).** Released as `3384454`; `git archive HEAD` holds only R1's runtime files (with `roles/judge.md`). `reviewer` (Checklist: `agent-skills:code-review-and-quality` loaded) approved the release notes, the changelog and the reporting rule (`3b449fb`), no Critical or Required. Optional: name `judge.md` in the new-session reason (fixed); the reporting rule read as judge-only (fixed: a bullet of its own in the assistant block, A4 and R13 say it holds for any text; README says so); README lacked the rule (fixed). Nits kept: the binding row in the notes asks for a name and date, unlike the template; the tag comes with Ship. Mutations: removing the rule from the assistant block, removing it from A4: both killed. Tag `v0.3.0` at the maintainer's request ("spec, plan, build and ship").

**Verification:** `make check`; `git archive HEAD | tar -t`.

**Dependencies:** Task 5. **Files:** `pyproject.toml`, `uv.lock`, `README.md`, `CHANGELOG.md`, `tasks/release-0.3.0.md`. **Scope:** S.
