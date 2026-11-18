# Tasks: the binding is generated (R14), release 0.4.0

Plan: [plan.md](plan.md). Spec: [SPEC.md](../SPEC.md), R14, criteria 2, 3, 19. `make check` green before each commit (the pre-commit hook enforces it). Each task: failing test first, shown red; then the code; a `CHANGELOG.md` line under `## Unreleased` for each user-visible change; `make self` when roles, templates or `harness.toml` change; one Conventional Commit.

## Task 1: `[binding]` in `routewise.toml`

**Description:** `lib/settings.py` reads an optional `[binding]` table into `Settings.binding` (`approved_by`, `approved_on`, `approved_rules_version`, `assistant_pins`, `review_from`). `templates/routewise.toml` gains the table with empty values and a comment per key, and its header comment says the binding is rendered from this file.

**Acceptance criteria:**
- [x] Valid values are read; a missing table or missing keys give empty values (no error).
- [x] Refused with `routewise: routewise.toml: [binding] <key> …` and exit 2, nothing written: a non-string text, a line break or other control character, `|`, `-->`, 201 characters, a date that is not `YYYY-MM-DD`, a version that is not a whole number of at least 1, an unknown key.
- [x] A new install's `routewise.toml` holds the commented `[binding]` table.

**Verification:** `uv run pytest tests/test_settings.py tests/test_install.py -k binding`; `make check`.

**Dependencies:** none. **Files:** `lib/settings.py`, `templates/routewise.toml`, `tests/test_settings.py`, `tests/test_install.py`. **Scope:** M.

## Task 2: `lib/binding.py` renders the binding

**Description:** Functions: `rules_version(spec_text) -> int`; `is_generated(text) -> bool`; `render(template, roles, harness map, settings, rules version, paths) -> str`. The template gets placeholders for the marker, the approval line and the role rows; the "Installed <date>" line goes.

**Acceptance criteria:**
- [ ] The first line is the marker, spelled for the project (`routewise/templates/binding.md`, `routewise/install` vendored; `templates/binding.md`, `./install --project .` here).
- [ ] One row per role, from its tier and effort; a new role gets a row; a changed tier changes the row.
- [ ] Approval: no values → "approval not recorded"; values with `approved_rules_version` equal to the rules version → "Approved by … on … for rules spec version N"; lower → "approval pending: rules spec version N (approved: M)" and `frontier` rows marked pending.
- [ ] `rules_version` reads `Version 4, …` from the shipped spec; a spec without the line is an error naming the file.

**Verification:** `uv run pytest tests/test_binding.py`; `make check`.

**Dependencies:** Task 1. **Files:** `lib/binding.py`, `templates/binding.md`, `tests/test_binding.py`. **Scope:** M.

## Checkpoint A (after Task 2)

- [ ] `make check` green.

## Task 3: the installer writes the binding every run

**Description:** `lib/install.py` plans `ROUTING-BINDING.md` on every install run (not only the first), from `lib/binding.py`; an existing unmarked binding raises an error before planning in install and `--check`; `--uninstall` removes a marked binding and keeps an unmarked one with a note; the output prints "approval pending: …" when pending.

**Acceptance criteria:**
- [ ] Every case in success criterion 19 has an end-to-end test (`tests/test_install.py`): first install, approval values, pending (with `--check` exiting 0 when nothing else drifted), a new role file, a changed tier, an unmarked binding (install and `--check` exit 2, files byte-identical, fix in the message), `--uninstall` both ways, a hand edit as drift.
- [ ] Success criteria 2 and 3 updated in their tests (`ROUTING-BINDING.md` generated; removed by `--uninstall`).

**Verification:** `uv run pytest tests/test_install.py`; `make check`.

**Dependencies:** Task 2. **Files:** `lib/install.py`, `tests/test_install.py`, `CHANGELOG.md`. **Scope:** M.

## Task 4: this repo migrates; docs

**Description:** This repo's values go into its `routewise.toml` `[binding]` (approved by f0t0n, 2026-11-14 → rules spec 4 approved 2026-11-18; review from 2026-11-28; not an assistant project); its old `ROUTING-BINDING.md` is deleted and `make self` renders the new one. README (first-run table, the binding, updating), ADOPT.md step 4 (fill `[binding]`), the `install --help` text, CHANGELOG.

**Acceptance criteria:**
- [ ] `make self` renders this repo's binding with its approval line and no pending; `make check` covers it.
- [ ] README and ADOPT describe the generated binding and `[binding]`; no doc says to edit `ROUTING-BINDING.md` by hand.

**Verification:** `make self`; `make check`; `grep -rn "fill in ROUTING-BINDING\|fill in the binding" README.md ADOPT.md lib/` finds nothing stale.

**Dependencies:** Task 3. **Files:** `routewise.toml`, `ROUTING-BINDING.md` (generated), `README.md`, `ADOPT.md`, `lib/install.py` (help text), `CHANGELOG.md`. **Scope:** S.

## Checkpoint B: review (after Task 4)

- [ ] `make check` green; `make self` no drift.
- [ ] `reviewer` on R14's commits; `auditor` on S2 and S3; Critical and Required fixed (one more round scoped to a fix), Optional and Nit answered here; mutation suggestions run and recorded.

## Task 5: verify the update path

**Description:** In a scratch project installed from `v0.3.0`, run the update to the release tree: the run stops with exit 2 and the fix; follow the fix (values into `[binding]`, delete the binding), re-run: the binding renders with the approval line; set `approved_rules_version = 3` and see "approval pending". Recorded in `tasks/todo.md`.

**Acceptance criteria:**
- [ ] Each step behaves as R14 says; a failure fixes the code and runs again.

**Verification:** the recorded commands and outputs.

**Dependencies:** Checkpoint B. **Files:** `tasks/todo.md`. **Scope:** S.

## Task 6: release 0.4.0

**Description:** Version `0.4.0` in `pyproject.toml`, `uv.lock` and every README `v=`; `## Unreleased` becomes `## 0.4.0 (<date>)`; `tasks/release-0.4.0.md` for users (what changed, the one-time migration step, approval) checked by `reviewer`; archive check; annotated tag `v0.4.0` when asked; publish commands handed over.

**Acceptance criteria:**
- [ ] `make check` green with `0.4.0`; release notes reviewed; archive holds only runtime files.

**Verification:** `make check`; `git archive HEAD | tar -t`.

**Dependencies:** Task 5. **Files:** `pyproject.toml`, `uv.lock`, `README.md`, `CHANGELOG.md`, `tasks/release-0.4.0.md`. **Scope:** S.
