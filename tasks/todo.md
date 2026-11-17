# Tasks: review roles load checklist skills, stand-ins for /ship (R8, R9), release 0.2.0

Plan: [plan.md](plan.md). Spec: [SPEC.md](../SPEC.md), R8, R9. `make check` green before each commit (the pre-commit hook enforces it). Each task: failing test first, shown red; then the code; a `CHANGELOG.md` line under `## Unreleased` for each user-visible change; `make self` when roles, templates or `harness.toml` change; one Conventional Commit.

## Task 1: `skills` key in role files, rendered for both harnesses

**Description:** `lib/roles.py` reads an optional `skills: [a, b]` line, checks each name, and renders `skills:` for Claude Code (comma-separated) and Antigravity (YAML list) when the list is not empty. S6 allows the key.

**Acceptance criteria:**
- [x] A role with `skills: [agent-skills:code-review-and-quality, my-skill]` renders `skills: agent-skills:code-review-and-quality, my-skill` (cc) and `skills: [agent-skills:code-review-and-quality, my-skill]` (agy); a role with none or `[]` renders no line.
- [x] Refused with `routewise: <file>: …` and exit 2, nothing written: upper case, a space, a line break, two `:`, a leading `:` or `-`, `/`, `..`, an empty name, 33 names, a value that is not a list. (Unit tests on `RoleError`; the exit-2 path is the one every role error already takes.)
- [x] Before the format is fixed: a live probe shows a Claude Code subagent with a two-skill line gets both skills (scratch folder, as on 2026-11-17).

**Verification:** `uv run pytest tests/test_roles.py`; `make check`.

**Dependencies:** none. **Files:** `lib/roles.py`, `tests/test_roles.py`, `CHANGELOG.md`. **Scope:** S.

## Task 2: `[skills]` setting overrides a role's list

**Description:** `routewise.toml` may hold `[skills]` with `role = ["name", …]`; it replaces that role's list, `[]` removes the line. Types and names are checked in `lib/settings.py`, unknown roles in `lib/install.py`. The template shows the table commented out.

**Acceptance criteria:**
- [x] `[skills] reviewer = ["my-review"]` renders `skills: my-review` for `reviewer` only; `reviewer = []` renders no line; no `[skills]` keeps the role's list.
- [x] An unknown role, a non-list, a bad name stop the run with a message naming `routewise.toml` and the fix; nothing written.
- [x] `templates/routewise.toml` documents `[skills]` (commented example); a new install still writes the same files as before apart from that comment.

**Verification:** `uv run pytest tests/test_settings.py tests/test_install.py -k skills`; `make check`.

**Dependencies:** Task 1. **Files:** `lib/settings.py`, `lib/install.py`, `templates/routewise.toml`, `tests/test_settings.py`, `tests/test_install.py`. **Scope:** M.

## Task 3: `reviewer` and `auditor` load the agent-skills checklists; body rules

**Description:** `roles/reviewer.md` gets `skills: [agent-skills:code-review-and-quality]`, `roles/auditor.md` `skills: [agent-skills:security-and-hardening]`. Both bodies add: a skill says what to check, the body how to behave and what to return; the body wins where they disagree; a skill step that would change a file is reported as a suggestion with `path:line`; severity names mapped to Critical, Required, Optional, Nit; the skill's report template is not used; the reply starts with `Checklist: <names> loaded` or `Checklist: none`. The existing method stays.

**Acceptance criteria:**
- [x] A test reads the shipped roles and finds each rule (one phrase each), the `Checklist:` line in the return, the skill names; the read-only test still passes.
- [x] Other roles list no skills.
- [x] `make self` regenerates `.claude/agents/` and `.agents/agents/`; `--check` clean.

**Verification:** `uv run pytest tests/test_roles.py`; `make self`; `make check`.

**Dependencies:** Task 1. **Files:** `roles/reviewer.md`, `roles/auditor.md`, `tests/test_roles.py`, generated agents, `CHANGELOG.md`. **Scope:** M.

## Task 4: delegation block: mutation suggestions and `Checklist: none`

**Description:** `templates/fragment-dev.md` says: try the mutation suggestions `reviewer` returns (invert, run the tests, restore); one that stays green is a Required finding; when a role that lists a skill returns `Checklist: none`, tell the person once per session. The assistant fragment is unchanged.

**Acceptance criteria:**
- [x] A test finds both rules in a dev install's block and neither in an assistant install's block.
- [x] `make self` updates this repo's `AGENTS.md` block; `--check` clean.

**Verification:** `uv run pytest tests/test_install.py -k fragment`; `make self`; `make check`.

**Dependencies:** Task 3. **Files:** `templates/fragment-dev.md`, `tests/test_install.py`, `AGENTS.md` (generated block), `CHANGELOG.md`. **Scope:** S.

## Checkpoint A

- [x] `make check` green, `make self` no drift.
- [x] One live `reviewer` call in this repo: reply opens with `Checklist: agent-skills:code-review-and-quality loaded` (2026-11-17, review of `ec46ea3..470711c`: approve, no Critical or Required; `git status` clean). Its 3 mutation suggestions were run: 2 killed, 1 survived (`len(names) >= MAX_SKILLS`), fixed by `a3ce128` (32 allowed, 33 refused, also in `[skills]`). Other findings answered: `[skills]` is keyed by role file name on purpose (the error lists them; README says so in Task 9); the repeated agy list check and duplicate names are left as they are.
- [x] Maintainer look before R9 (approved 2026-11-17).

## Task 5: stand-in marker and rendering under another name

**Description:** `render` takes an optional agent name; the stand-in file's marker reads `… from <role source> as <name>.md; edit that file …`, and `name:` and the description say which role it stands in for. `is_generated` accepts a marker with `as <file name>`, and keeps today's rule for markers without `as`. Waits for the marker approval (plan open question 1).

**Acceptance criteria:**
- [x] A role file's rendering is byte-identical to before (golden test on `reviewer`). Also found while writing the tests: `SKILL.match` with `$` accepted a trailing line break (`"a\n"` in `[skills]`); both patterns now use `fullmatch`, with a test.
- [x] `code-reviewer.md` with a stand-in marker for itself counts as generated; a renamed copy (`my-reviewer.md` holding that marker) does not; an old-style marker keeps its result.
- [x] A name with `/`, `..`, a space, upper case or a line break is refused.

**Verification:** `uv run pytest tests/test_roles.py`; `make check`.

**Dependencies:** Task 3, marker approval. **Files:** `lib/roles.py`, `tests/test_roles.py`. **Scope:** S.

## Task 6: `[stand_ins]` setting, install, check and uninstall

**Description:** `routewise.toml` `[stand_ins]` maps a role to extra agent names; `install.py` plans one stand-in file per name and active harness, keeps it in the wanted set (so it is not removed as stale), and removes it when the setting drops it, on `--uninstall`, or when its harness is dropped. Off by default; the template shows `reviewer = ["code-reviewer"]` and `auditor = ["security-auditor"]` commented out.

**Acceptance criteria:**
- [x] With both stand-ins set, install writes `code-reviewer.md` and `security-auditor.md` in each harness folder, equal to the role's file but for the marker, `name` and description; a second run prints `routewise: nothing to change`; `--check` reports a hand-edited stand-in as drift.
- [x] Removing a stand-in from the setting removes its file; `--uninstall` removes all; a user's own `code-reviewer.md` stops the run (S3) with nothing written.
- [x] Refused: unknown role, a name equal to a role, the same name twice, a bad name.

**Verification:** `uv run pytest tests/test_install.py -k stand_in tests/test_settings.py`; `make check`.

**Dependencies:** Tasks 2 and 5. **Files:** `lib/settings.py`, `lib/install.py`, `templates/routewise.toml`, `tests/test_settings.py`, `tests/test_install.py`. **Scope:** M.

## Task 7: delegation block line for stand-ins

**Description:** `{{stand_ins}}` in `templates/fragment-dev.md` becomes one line when stand-ins are set: for those names, also inside `/ship`, start the project agent, never the `agent-skills:` one (named per stand-in). Nothing when none are set.

**Acceptance criteria:**
- [x] With stand-ins, the block has the line naming each stand-in; without, the block equals Task 4's output.
- [x] This repo's `AGENTS.md` (no stand-ins) is unchanged by `make self`.

**Verification:** `uv run pytest tests/test_install.py -k stand_in`; `make self`; `make check`.

**Dependencies:** Tasks 4 and 6. **Files:** `templates/fragment-dev.md`, `lib/install.py`, `tests/test_install.py`, `CHANGELOG.md`. **Scope:** S.

## Checkpoint B

- [x] `make check` green; criterion 14's tests pass.

## Task 8: rules spec version 3

**Description:** `spec/SPEC-model-routing.md`: version line 3 (2026-11-17, R-A6 and the review returns); rule R-A6 in section 4 (a role may load skills for what to check; its body fixes behaviour, tools and return shape; a skill never adds a tool or a write); the `Checklist` line in the `reviewer` and `auditor` returns; section 13 records of the 2026-11-17 probes (Claude Code 2.1.326: namespaced and bare skills injected, missing skipped, no tool added, same-name project agent wins but `agent-skills:` stays reachable; Antigravity 1.5.9: `skills:` accepted and ignored, project agent hides the plugin's).

**Acceptance criteria:**
- [ ] Version line, R-A6, table cells and two section 13 records present; nothing else in the rules spec changes (diff reviewed).

**Verification:** `git diff spec/`; `make check`.

**Dependencies:** none (approved with R8); done after Task 7 so the records match what was built. **Files:** `spec/SPEC-model-routing.md`, `CHANGELOG.md`. **Scope:** S.

## Task 9: README section on checklists and preference; ADOPT.md and template notes

**Description:** `README.md` gets a section: `reviewer` and `auditor` load agent-skills' `code-review-and-quality` and `security-and-hardening` by default (credit, link, MIT); a matter of preference; how to change it (`[skills]` with another installed skill, `[]` for routewise's own method, then re-run the install); a missing skill shows as `Checklist: none`; Antigravity ignores `skills:` for now; `[stand_ins]` for projects that use agent-skills' `/ship`. `ADOPT.md` mentions the choice in its review-settings step.

**Acceptance criteria:**
- [ ] README section covers each point above with a copy-paste `routewise.toml` example for each choice; ADOPT.md points to it.
- [ ] `reviewer` checks the doc diff against the code.

**Verification:** read the rendered README; `make check`.

**Dependencies:** Tasks 2, 6. **Files:** `README.md`, `ADOPT.md`, `CHANGELOG.md`. **Scope:** S.
