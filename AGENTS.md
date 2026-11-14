# AGENTS.md: developing routewise

> **In a project that vendors `routewise/`?** These instructions are for developing routewise itself and do not apply to you. Do not edit files under `routewise/`; to adopt or update it, follow `routewise/ADOPT.md`, and follow the delegation block in the project's own `AGENTS.md`.

routewise installs model routing and delegation rules into a project: read-only subagents per tier, a delegation block in the instruction file, and a miss log. [SPEC.md](SPEC.md) is the contract for the tool (behaviour, safety rules S1–S8, boundaries). [spec/SPEC-model-routing.md](spec/SPEC-model-routing.md) is the rules spec the tool ships to projects; it is not the spec of this code.

## Workflow: every request, every phase

Follow the [agent-skills](https://github.com/addyosmani/agent-skills) lifecycle for every change, scaled to its size but never skipped, and stop at each gate for the maintainer's approval (details in SPEC.md, "Development workflow"):

1. **Define** (`/spec`, `spec-driven-development`): update SPEC.md first; list assumptions and open questions. Gate.
2. **Plan** (`/plan`, `planning-and-task-breakdown`): `tasks/plan.md` and `tasks/todo.md`, small ordered tasks with acceptance criteria and a verify step. Gate.
3. **Build** (`/build`, `incremental-implementation` + `test-driven-development`): one task at a time, failing test first, `make check` green, one commit per task.
4. **Verify** (`/test`): `make check` on the whole change; harness facts by a live run recorded in `spec/SPEC-model-routing.md` section 13.
5. **Review** (`/review`, `code-review-and-quality`): delegate to the `reviewer` subagent, and to `auditor` for anything touching safety rules S1–S9; fix or answer every finding.
6. **Ship** (`/ship`, `shipping-and-launch`): version, `CHANGELOG.md`, release archive contents checked; the maintainer pushes and tags from the host.

## Commands

```sh
uv sync          # once: dev environment from uv.lock
make check       # lint, typecheck, gitleaks, tests: must pass before every commit
make test        # or: uv run pytest tests/test_install.py -k <name>
make fmt         # ruff format and autofix
make hooks       # once per clone: pre-commit runs make check
```

## Where things are

- `lib/`: one module per job (`install`, `block`, `roles`, `settings`, `paths`, `files`, `miss_log`, `privacy`); `install` and `bin/miss-log` are bash wrappers around them.
- `roles/`, `harness.toml`, `templates/`: what gets rendered into projects.
- `tests/`: pytest; `conftest.py` copies routewise into a temporary project per test, and `test_install.py` drives the real scripts end to end.

## How to work here

- **Test first.** Write or update the failing test, then the code. Every behaviour in SPEC.md, and every safety rule, keeps a test.
- **Standard library only** at run time, Python 3.11. Adding any dependency, runtime or dev, needs the maintainer's approval.
- **Keep the safety rules** (SPEC.md S1–S8): writes only inside the project, re-checked before each write; plan everything, then write atomically, so a failed run writes nothing; touch only files routewise generated; broken markers stop the run; never create symlinks; roles stay read-only.
- **Style:** small plain functions, a one- or two-line docstring that says what and why, errors as one exception per module printed as `routewise: <message>` with exit code 2. Ruff at line length 100 with complexity limits; pyright with zero warnings. Messages name the file and the fix.
- **Docs move with behaviour:** a user-visible change updates `CHANGELOG.md` (one line under the current version), and `README.md`, `ADOPT.md` or the templates when they describe it.
- **The rules spec** (`spec/SPEC-model-routing.md`) changes only with approval. Its version line changes only when a rule changes; a live-run result goes in section 13 as a dated record.
- **Commits:** Conventional Commits (`feat:`, `fix:`, `docs(spec):`, `build:`). Commit only when asked; never push from the sandbox: the maintainer pushes from the host.

## Ask first

A new harness, role or setting; a changed default; a change to the marker text, the generated-file marker or exit codes (projects depend on them); any rule change in the rules spec.

## Never

Give a role a write, edit, send or commit tool; write outside the project or through a symlink that leads out; delete a file routewise did not create; commit secrets or tokens.
