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
- [x] Version line, R-A6, table cells and two section 13 records present; nothing else in the rules spec changes (diff reviewed), except section 10's fragment, which gains the two R8 lines of the dev template (mutation suggestions, `Checklist: none`) so the portable block stays in step.

**Verification:** `git diff spec/`; `make check`.

**Dependencies:** none (approved with R8); done after Task 7 so the records match what was built. **Files:** `spec/SPEC-model-routing.md`, `CHANGELOG.md`. **Scope:** S.

## Task 9: README section on checklists and preference; ADOPT.md and template notes

**Description:** `README.md` gets a section: `reviewer` and `auditor` load agent-skills' `code-review-and-quality` and `security-and-hardening` by default (credit, link, MIT); a matter of preference; how to change it (`[skills]` with another installed skill, `[]` for routewise's own method, then re-run the install); a missing skill shows as `Checklist: none`; Antigravity ignores `skills:` for now; `[stand_ins]` for projects that use agent-skills' `/ship`. `ADOPT.md` mentions the choice in its review-settings step.

**Acceptance criteria:**
- [x] README section covers each point above with a copy-paste `routewise.toml` example for each choice; ADOPT.md points to it.
- [x] `reviewer` checks the doc diff against the code (2026-11-17, the generated `reviewer` with its skill loaded: approve, no Critical or Required; Optional 1-2 and Nits 3-4 applied, Nit 5 needs no change).

**Verification:** read the rendered README; `make check`.

**Dependencies:** Tasks 2, 6. **Files:** `README.md`, `ADOPT.md`, `CHANGELOG.md`. **Scope:** S.

## Review record (2026-11-17)

Run headless with the agent files as fixed in Verify. Stopping rule: ended after round 3 (no open Critical or Required).

- **Round 1, `ec46ea3..778d1b9`:** `reviewer` approve, `auditor` no Critical or Required. Fixed: a fake `SKILL.md` in a reviewed diff could pass as loaded (`d0e4485`); the stand-in line names no particular plugin (`ca4e847`); a skill listed twice is refused, and a refused `[stand_ins]` is tested to write nothing (`65131ff`); README notes on stand-ins with the dev block and a skill's `allowed-tools` (`37e26c1`). Mutation suggestions: 1 of 3 survived (a stand-in taking a role's agent name), test added (`8e31ca3`). Answered: single-line description test (no such role ships), case-only renames on macOS (true for roles before this change), `git status` refreshing `.git/index` (benign).
- **Round 2, scoped to the round-1 fixes:** both approve, but `reviewer` replied `Checklist: none` with its skill loaded: the wording made the agent judge where the skill text sat (3 wrong of 7 live runs; Required). R8 amended with the maintainer's approval: the installer writes the skill names and the exact `Checklist` line (`eeba5e7`, `8b861f6`, live-checked: `loaded`, `missing`, fake skill as data); small items (`cd3f381`). Mutation suggestions: 3 of 3 killed. Answered: a skill's own reference files read with a tool are data (safe trade-off); the role-text test covers `roles/*.md`, and the generated copies are covered by the self-install drift check.
- **Round 3, scoped to the amendment (`8e31ca3..8b861f6`):** both approve. Fixed: "Skills listed for you", end-to-end tests of the `none` form and of leftover placeholders (`4d69b79`). Mutation suggestions: 3 of 3 killed. Answered: a mid-task message or skill text the main session pastes into the brief could count as loaded (the main session is trusted, and the body still wins); the multi-skill reply form has no example (unambiguous, tested in `test_roles.py`); `str.replace` fills every placeholder (each used once).
- **Misses logged:** 4 for `reviewer`, all found by these live runs (a probe script and bytecode written; three wrong `Checklist` lines), each fixed above.

## Task 10: the self-install's miss-log command works (R10)

**Description:** in a self-install, `{{miss_log}}` in the dev and assistant fragments and in a new `ROUTING-BINDING.md` becomes `bin/miss-log --project .`; vendored installs keep `routewise/bin/miss-log`. This repo's hand-edited `ROUTING-BINDING.md` is corrected by hand.

**Acceptance criteria:**
- [x] On a temporary self-install copy, the block and a new binding name `bin/miss-log --project . add` and `report`, and running the block's command from the repo root appends to the repo's own log.
- [x] A vendored install still names `routewise/bin/miss-log` (existing tests unchanged).
- [x] `make self` updates this repo's block; `ROUTING-BINDING.md` fixed by hand; `--check` clean.

**Verification:** `uv run pytest tests/test_install.py -k self`; `make self`; `make check`.

**Files:** `lib/install.py`, `tests/test_install.py`, `AGENTS.md` (generated block), `ROUTING-BINDING.md`, `CHANGELOG.md`. **Scope:** S.

## Task 11: `MODEL` uses `fullmatch` (R11)

**Description:** `lib/roles.py` checks model names with `MODEL.fullmatch`, in `model_lines` and in `settings.tiers`.

**Acceptance criteria:**
- [ ] `[tiers] fast = "haiku\n"` and a harness tier `"haiku\n"` are refused with the existing message; red on HEAD.
- [ ] Every model name accepted before still passes (`haiku`, `claude-haiku-5-5`, `fable`, names with `.`, `:`, `[1m]`).

**Verification:** `uv run pytest tests/test_roles.py tests/test_settings.py`; `make check`.

**Files:** `lib/roles.py`, `lib/settings.py`, `tests/test_roles.py`, `tests/test_settings.py`, `CHANGELOG.md`. **Scope:** XS.

## Checkpoint C

- [ ] `make check` green; `reviewer` on Tasks 10 and 11, `auditor` on Task 11.

## Found 2026-11-17, now Task 11 (R11): `MODEL` accepts a trailing line break

**Found:** 2026-11-17, while testing Task 5. `MODEL` in `lib/roles.py` is used with `.match` and ends in `$`, which also matches just before a final newline, so `[tiers] fast = "haiku\n"` (or a `harness.toml` tier with one) passes the check and renders `model: haiku` plus a blank frontmatter line. A line break followed by more text is still refused, so no key can be injected; the effect is a malformed but harmless line. 0.1.x has the same behaviour.

**Fix:** use `fullmatch` for `MODEL` (as R8 does for skill and stand-in names); a test with a trailing `\n` in `[tiers]` and in a harness tier. Goes through its own Define step (a one-line spec note) after 0.2.0, or into 0.2.0 if the maintainer asks.

## Found 2026-11-17, now Task 10 (R10): the self-install's miss-log command needs `--project .`

**Found:** 2026-11-17, logging the Verify miss. In routewise's own repo the delegation block says `bin/miss-log add …` (R3 spelling for a self-install), but `bin/miss-log` defaults to the folder that holds the routewise folder, which here is the folder above the repo, so the command fails (`Permission denied` on `../logs`). It works with `bin/miss-log --project . add …`. Vendored projects are not affected (`routewise/bin/miss-log` finds the project). Breaks success criterion 7 for the self-install only; present since 0.1.0.

**Fix:** spell the self-install's miss-log command with `--project .` (as `./install --project .`), with a test on the self-install block and `ROUTING-BINDING.md`; or make `bin/miss-log` default to the repo itself when run from inside the routewise folder. Own Define step.
