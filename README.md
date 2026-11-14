# routewise

Model routing and delegation for coding and assistant agents, set up by rules instead of the agent's mood.

routewise gives a project:

- **Five subagents without write or edit tools**, each on the cheapest model that does its job well: `Explore` (file sweeps) on `haiku`, `log-reader` and `web-reader` on `haiku`, `reviewer` on `sonnet` at `medium`, `auditor` on `opus` at `high`. The main session keeps the decisions and the edits. `log-reader`, `reviewer` and `auditor` keep `Bash` to run tests and read logs; their instructions allow only commands that read, but nothing sandboxes them.
- **A delegation block** in the project's `AGENTS.md`: what to delegate, what never to delegate, a parallel cap (5 by default), and an escalation ladder (add a check, then raise effort, then move one tier up).
- **A miss log** (`routewise/bin/miss-log`) that records each delegated result that was wrong or redone, so roles change on evidence, not taste.

The rules are in [spec/SPEC-model-routing.md](spec/SPEC-model-routing.md). It is based on Addy Osmani's article ["Which Claude model should you build with?"](https://claude.dev/blog/which-claude-model-should-you-build-with/) (claude.dev, 2026-11-09).

Supported harnesses: Claude Code (`cc`) and Antigravity CLI (`agy`; its agents follow the session model, since agy agent files cannot set one).

## Requirements

- Python 3.11 or newer (standard library only) and `bash`.

## Install into a project

From the project root, for a first install (it stops if `routewise/` already exists; to update, see [Updating](#updating)):

```sh
v=0.1.1
mkdir routewise && curl -fsSL "https://github.com/f0t0n/routewise/archive/refs/tags/v$v.tar.gz" | tar -xz --strip-components=1 -C routewise && routewise/install
```

If the download fails, delete the empty `routewise/` folder it leaves before you try again. The first run writes `routewise.toml`: review it and re-run `routewise/install` if you change it, fill in `ROUTING-BINDING.md`, commit, and open a new agent session. The same, in detail and with alternatives:

1. Put a release into the project root as `routewise/`: the block above does it from the release's "Source code" archive, or unpack that archive yourself, or run `git archive` on a tag. The archive holds only what a project needs: `install`, `bin/`, `lib/`, `roles/`, `harness.toml`, `templates/`, `spec/` and the docs. A git submodule or subtree works too, but brings this repo's development files (tests, `SPEC.md`, `AGENTS.md`, its own agents); make sure your test runner and linters skip `routewise/`.
2. From the project root, run:

   ```sh
   routewise/install
   ```

   The first run writes:

   | Path | What |
   |---|---|
   | `routewise.toml` | Settings: harnesses, instruction files, `claude_md`, `dev` or `assistant` mode, parallel cap, miss-log path, model pins. |
   | `ROUTING-BINDING.md` | The binding (spec section 9): fill in who approved it and the first miss-log review date. |
   | `.claude/agents/*.md` | The five roles for Claude Code (and `.agents/agents/` for agy). |
   | `AGENTS.md` | The delegation block, between `routewise:start` and `routewise:end` markers. Created if missing; the rest of the file is kept. |
   | `CLAUDE.md` or `.claude/CLAUDE.md` | Only when one already exists (or with `claude_md = "import"`): a routewise block holding just an `@AGENTS.md` import line. See below. |
   | `logs/delegation-misses.jsonl` | The empty miss log. |

3. Review `routewise.toml`, re-run `routewise/install` if you changed it, fill in `ROUTING-BINDING.md`, and commit.
4. Open a **new** agent session: an open session keeps the instructions it loaded.

### Claude Code and AGENTS.md

Claude Code reads `AGENTS.md` by itself from v2.1.277 (v2.1.281 for sessions on Amazon Bedrock or with telemetry off), but by default only when there is no `CLAUDE.md`, `.claude/CLAUDE.md` or `CLAUDE.local.md` in the working directory or any folder above it (`~/.claude/CLAUDE.md` does not count). The documented way to keep both is a `CLAUDE.md` with an `@AGENTS.md` import line, which never loads `AGENTS.md` twice ([Claude Code docs: memory](https://code.claude.com/docs/en/memory)). `claude_md` in `routewise.toml` sets what routewise does:

| `claude_md` | What routewise does |
|---|---|
| `"auto"` (default) | If `CLAUDE.md` or `.claude/CLAUDE.md` exists, adds an import block to the first of them, unless it already has the import line. Never creates `CLAUDE.md`. Leaves `CLAUDE.local.md` alone (it is personal) and prints a note when that file alone would hide `AGENTS.md`. |
| `"import"` | Always keeps the import block, creating `CLAUDE.md` if needed. Use it for Claude Code before v2.1.277, sessions that read `CLAUDE.md` only, or a `CLAUDE.md` in a folder above the project. |
| `"none"` | Never touches `CLAUDE.md`. |

Imports resolve from the importing file's folder, so `.claude/CLAUDE.md` gets `@../AGENTS.md`. routewise never writes above the project: a `CLAUDE.md`, `.claude/CLAUDE.md` or `CLAUDE.local.md` in a parent folder only gets a warning. Antigravity CLI and most other tools read `AGENTS.md` directly.

Or tell your agent: *"Adopt routewise: follow routewise/ADOPT.md."* It asks the choices, runs the installer and checks the result.

## Day to day

```sh
routewise/install            # after editing routewise.toml, or after updating routewise/
routewise/install --check    # exit 1 if generated files drifted (use in CI or a pre-commit hook)
routewise/install --uninstall  # keeps routewise.toml, ROUTING-BINDING.md and the miss log
routewise/bin/miss-log add --mode dev --role reviewer --task review --what "missed a None check"
routewise/bin/miss-log report
```

Review the miss log two weeks after install, then monthly. Change a role's tier or effort only with a cost check: run one real task both ways, each in its own session, and compare usage (spec section 8).

## Updating

Replace the `routewise/` folder with a newer release and run `routewise/install`. From the project root (the old folder is replaced only after the download succeeded):

```sh
v=0.1.1
mkdir routewise.new && curl -fsSL "https://github.com/f0t0n/routewise/archive/refs/tags/v$v.tar.gz" | tar -xz --strip-components=1 -C routewise.new && rm -rf routewise && mv routewise.new routewise && routewise/install
```

Set `v` to the release you want. Project choices live outside `routewise/` (`routewise.toml`, `ROUTING-BINDING.md`), so nothing is lost.

## Safety

- Every write stays inside the project. Paths in `routewise.toml` must be relative, a symlink that leads out of the project is refused, and each path is checked again right before it is written. Do not run routewise while another program is rewriting the project.
- `routewise/` must sit directly in the project root it sets up: `--project` must be the folder that holds `routewise/`, or `routewise/` itself (so routewise can run on its own repo). Any other folder is refused, and so are your home folder and every folder above it, even when routewise sits at `~/routewise`: agents and `CLAUDE.md` there apply to every session. So generated files never hold absolute paths and never land in global config.
- A generated agent file starts with a `# generated by routewise from routewise/roles/<same name>.md` line. The installer rewrites or deletes only such files, and refuses to overwrite any other file in its way.
- The delegation block sits between a `routewise:start` line and a `routewise:end` line. Markers count only as whole lines outside fenced code, so text that mentions them is safe. Broken or duplicated markers stop the run, so you fix them by hand instead of losing text. Text outside the block keeps its line ends (CRLF too); only the blank lines right next to the block are normalised.
- routewise never creates a symlink: Claude Code's Edit and Write tools refuse to write through one, and Windows checks a committed symlink out as a one-line file. An existing symlinked instruction file (`CLAUDE.md` -> `AGENTS.md`) is edited through its target and never deleted.
- `CLAUDE.local.md` and files above the project are never written. Uninstall removes the routewise blocks from `AGENTS.md` and `CLAUDE.md`, and deletes either file only when nothing else is left in it.
- Before writing, the installer checks that every target can be written, and each file is written to a temporary file first and then renamed into place, so a failed run does not leave a half-written or empty file.
- Roles get no write or edit tools (spec R-A1): role files may hold only `name`, `description`, `tools`, `tier` and `effort`; a role needs at least one tool, and only each harness's known read and search tools, its shell and its web tools can be granted. A shell (`Bash`) can still change files: roles that have one are told to run only commands that read, which is an instruction, not a sandbox.
- `miss-log` refuses clear leaks: e-mail addresses (also spelled out or without a dot, `me@localhost`), URLs (also without a scheme, `example.com/page`), IP addresses, UUIDs and chat IDs, home folder paths, phone and card numbers, and common token and key formats. It lets normal code words pass (`logger.info`, `@property`, `GPT-4`), so it cannot catch a name, a bare host name or an internal ID: the agent writes the miss in its own words.

## Changing the rules

- A project choice (cap, harness, a pinned model, assistant mode): `routewise.toml`.
- A project-specific role: write your own agent file under another name. If you start from a copy of a generated file, it is still treated as yours (its marker names the original file), but delete the marker line to make that plain.
- A change for every project: change `roles/`, `templates/` or the spec here, and release a new version.

## Development

```sh
uv sync
make check   # lint, format check, typecheck, secret scan (gitleaks), tests, self-install drift
make hooks   # once per clone: run `make check` before every commit
make self    # routewise runs on its own repo: re-install after changing roles/, templates/ or harness.toml
```

In this repo never run a bare `./install`: its default project is the folder above. `make self` runs `./install --project .`. The rules for working here are in [AGENTS.md](AGENTS.md) and [SPEC.md](SPEC.md).

`make check` needs `uv`, `shellcheck` and `gitleaks` on the `PATH`.

## License

MIT; see [LICENSE](LICENSE).
