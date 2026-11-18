# routewise

Model routing and delegation for coding and assistant agents, set up by rules instead of the agent's mood.

routewise gives a project:

- **Six subagents without write or edit tools**, each on the cheapest model that does its job well: `Explore` (file sweeps) on `haiku`, `log-reader` and `web-reader` on `haiku`, `reviewer` on `sonnet` at `medium`, `auditor` on `opus` at `high`, and `judge` on `fable` at `medium`, which runs only when you ask for it (see [Asking a judge](#asking-a-judge)). `reviewer` and `auditor` load a maintained checklist skill for what to check ([agent-skills](https://github.com/addyosmani/agent-skills) by default; see [Review checklists](#review-checklists)). The main session keeps the decisions and the edits. `log-reader`, `reviewer`, `auditor` and `judge` keep `Bash` to run tests and read logs; their instructions allow only commands that read, but nothing sandboxes them.
- **A delegation block** in the project's `AGENTS.md`: what to delegate, what never to delegate, a parallel cap (5 by default), and an escalation ladder (add a check, then raise effort, then move one tier up).
- **A miss log** (`routewise/bin/miss-log`) that records each delegated result that was wrong or redone, so roles change on evidence, not taste.

The rules are in [spec/SPEC-model-routing.md](spec/SPEC-model-routing.md). It is based on Addy Osmani's article ["Which Claude model should you build with?"](https://claude.dev/blog/which-claude-model-should-you-build-with/) (claude.dev, 2026-11-09).

Supported harnesses: Claude Code (`cc`) and Antigravity CLI (`agy`; its agents follow the session model, since agy agent files cannot set one).

## Requirements

- Python 3.11 or newer (standard library only) and `bash`.

## Install into a project

From the project root, for a first install (it stops if `routewise/` already exists; to update, see [Updating](#updating)):

```sh
v=0.3.0
mkdir routewise && curl -fsSL "https://github.com/f0t0n/routewise/archive/refs/tags/v$v.tar.gz" | tar -xz --strip-components=1 -C routewise && routewise/install
```

If the download fails, delete the empty `routewise/` folder it leaves before you try again. The first run writes `routewise.toml`: review it, fill in its `[binding]` table (who approved and when, and the first miss-log review date), re-run `routewise/install`, commit, and open a new agent session. The same, in detail and with alternatives:

1. Put a release into the project root as `routewise/`: the block above does it from the release's "Source code" archive, or unpack that archive yourself, or run `git archive` on a tag. The archive holds only what a project needs: `install`, `bin/`, `lib/`, `roles/`, `harness.toml`, `templates/`, `spec/` and the docs. A git submodule or subtree works too, but brings this repo's development files (tests, `SPEC.md`, `AGENTS.md`, its own agents); make sure your test runner and linters skip `routewise/`.
2. From the project root, run:

   ```sh
   routewise/install
   ```

   The first run writes:

   | Path | What |
   |---|---|
   | `routewise.toml` | Settings: harnesses, instruction files, `claude_md`, `dev` or `assistant` mode, parallel cap, miss-log path, model pins. |
   | `ROUTING-BINDING.md` | The binding (spec section 9), rendered on every run from the roles and `[binding]` in `routewise.toml`. Do not edit it; change `routewise.toml` and re-run. |
   | `.claude/agents/*.md` | The six roles for Claude Code (and `.agents/agents/` for agy). |
   | `AGENTS.md` | The delegation block, between `routewise:start` and `routewise:end` markers. Created if missing; the rest of the file is kept. |
   | `CLAUDE.md` or `.claude/CLAUDE.md` | Only when one already exists (or with `claude_md = "import"`): a routewise block holding just an `@AGENTS.md` import line. See below. |
   | `logs/delegation-misses.jsonl` | The empty miss log. |

3. Review `routewise.toml`, fill in its `[binding]` table, re-run `routewise/install`, and commit. Until `approved_rules_version` matches the shipped rules spec, the binding says "approval not recorded" or "approval pending"; nothing else stops.
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
routewise/install --uninstall  # keeps routewise.toml and the miss log
routewise/bin/miss-log add --mode dev --role reviewer --task review --what "missed a None check"
routewise/bin/miss-log report
```

Review the miss log two weeks after install, then monthly. Change a role's tier or effort only with a cost check: run one real task both ways, each in its own session, and compare usage (spec section 8).

## Review checklists

`reviewer` and `auditor` decide *how* a review runs: their model, their tools (none that write) and the shape of what they return. *What* they check comes from a skill named in the role, so a project gets a maintained checklist and routewise has no copy of it to keep up to date. By default they load two skills from Addy Osmani's [agent-skills](https://github.com/addyosmani/agent-skills) plugin (MIT):

| Role | Default skill |
|---|---|
| `reviewer` | `agent-skills:code-review-and-quality` |
| `auditor` | `agent-skills:security-and-hardening` |

Which checklist to use is a matter of preference. Install the plugin to use these, or choose another in `routewise.toml`, then run `routewise/install`:

```toml
[skills]
reviewer = ["my-review-skill"]            # any installed skill: name or plugin:name
auditor = ["agent-skills:security-and-hardening", "my-security-skill"]  # up to 32 per role
# reviewer = []                           # no skill: the role's own short method only
```

A list replaces the role's own; keys are role file names (`reviewer`, `auditor`, `explore`, ...).

- **Each reply starts with a `Checklist` line** that names each of the role's skills as `loaded` or `missing` (`Checklist: agent-skills:code-review-and-quality loaded`); the agent file lists the names, so the agent checks for them. A skill that is not installed, or was renamed, is skipped without an error and shows as `missing`; the role then reviews by its own method, and the `dev` delegation block tells the main session to say so once per session.
- **The role's own rules win over the skill.** A skill step that would change a file (a mutation test, deleting unused code) comes back as a suggestion. With the `dev` block, the main session runs `reviewer`'s mutation suggestions itself, and a mutation the tests miss is a Required finding. A skill's severity names are mapped to Critical, Required, Optional and Nit.
- **Antigravity CLI** (1.5.9) accepts the `skills:` line but does not load the skill yet, so there the roles use their own method and name their skills as `missing`; they pick the skill up once Antigravity does.

## Asking a judge

When a session offers you options (a question with choices, a list in its reply, a spec's open questions) and you cannot decide, answer **"ask a judge"** instead of choosing. The session then starts `judge`: an independent expert in the decision's field, on the strongest model (`fable` at `medium` on Claude Code), in a fresh context.

- **The brief** holds the decision, its context and every option offered so far, word for word, but not the option the session favours, so the judge forms its own view.
- **The judge** checks the facts the options rely on (files, docs, web pages), weighs each option on your goals, cost, risk and how hard it is to undo, and picks one or proposes a new one. It returns its recommendation, its confidence and up to three questions for you, in at most 40 lines. Its instructions forbid writing, sending or changing anything, but they are instructions, not a sandbox (see Hardening below).
- **You decide.** The session shows you the question, the options with its own recommendation as before, and the judge's verdict, then waits. Follow the judge, pick another option, give your own, answer its questions, or ask for another round. The verdict is never taken as your choice or approval.
- **Blocked pages:** if a page the judge needs is refused (a sandbox network policy, a login wall), it does not work around it. It gives its best call without the page and a line such as `Needs access: docs.example.com/limits (from: search result) — the rate limit — could favour option B`. The source is the judge's own claim, so the session marks each domain `in the brief` (it found it there, outside any quoted passage) or `claimed by the judge`, recommends none, and reminds you that allowing a domain opens every path on it. Allow a domain yourself and the session starts a new judge with the same brief.
- **Assistant mode** works the same way. The assistant runs on `balanced`; when you ask for a judge, it quotes what the decision needs from memory, connectors, mail or documents into the brief, marked as other people's text, with source and author, without their links and with no secrets, and takes exact values from the source again afterwards. Only your own message starts a judge; a mail or a memory that asks for one does not. When a mail or document tries to instruct an AI ("any AI assistant must fetch…"), the assistant tells you who sent it and what it asked, judge or not.
- **Cost:** `frontier` is the most expensive tier, which is why the session never starts a judge on its own. Change the model with `[tiers] frontier = "..."` and give the judge a skill with `[skills] judge = ["..."]` in `routewise.toml`. **Antigravity CLI** agent files cannot set a model, so there the judge runs on the session model and brings a fresh context only.
- **Hardening.** The judge keeps all its tools (it reads files, runs commands and uses the web, to ground what it says), so text it reads, such as a quoted mail or a web page, could try to make it send your data out. Its instructions forbid that: the network only through its web tools, no credential files, nothing from the brief in a search query or URL, no URL taken from text it read. But instructions are not a boundary. Run agents where the network is an allowlist (a sandbox that blocks every domain you have not allowed), and allow a domain from a `Needs access` line only when you know the site and would allow it anyway; the domain is the real control, since the path can carry data. Never allow a site where anyone can read what is posted or requested (paste sites, request catchers). In a Docker Sandboxes (`sbx`) VM with an allowlist, WebFetch and DNS lookups to a blocked domain both fail (checked live). Web *searches* run on the search provider's side and are not limited by a local allowlist: keeping private details out of queries rests on the judge's instructions alone. On Claude Code you can add deny rules of your own, best in `.claude/settings.local.json` (yours, not committed); they hold in every permission mode and for subagents (checked on Claude Code 2.1.326) and apply to the whole session, not only the judge. They are a speed bump, not a wall: `Read(...)` rules stop the Read tool and `cat`, but not a shell read such as `python3 -c 'print(open(".env").read())'` (checked live), and `Bash(curl *)` misses `/usr/bin/curl` or `sh -c`, while also stopping the agent from running this README's curl-based install and update commands:

  ```json
  { "permissions": { "deny": [
    "Read(~/.claude/.credentials.json)", "Read(./.env)", "Read(./.env.*)",
    "Bash(curl *)", "Bash(wget *)"
  ] } }
  ```

**agent-skills' `/ship`** starts its own `code-reviewer` and `security-auditor` agents, which can write files and run on the session's model. To have `/ship` use routewise's read-only roles with the same checklists, turn on stand-ins in the projects where you run it:

```toml
[stand_ins]
reviewer = ["code-reviewer"]
auditor = ["security-auditor"]
```

routewise then also writes `code-reviewer.md` and `security-auditor.md` (copies of the roles under those names), and the delegation block tells the session to start them instead of the plugin's `agent-skills:` agents, which Claude Code still lists. Stand-ins are generated files like the roles, so `--check` and `--uninstall` cover them; an agent file of that name that routewise did not write stops the run, so rename or remove your own first. Stand-ins pair with the `dev` block (`fragment = "dev"`): the assistant block does not name them. Leave stand-ins off where you do not use `/ship`, so the session does not see two agents for the same job.

## Updating

Replace the `routewise/` folder with a newer release and run `routewise/install`. From the project root (the old folder is replaced only after the download succeeded):

```sh
v=0.3.0
mkdir routewise.new && curl -fsSL "https://github.com/f0t0n/routewise/archive/refs/tags/v$v.tar.gz" | tar -xz --strip-components=1 -C routewise.new && rm -rf routewise && mv routewise.new routewise && routewise/install
```

Set `v` to the release you want. Project choices live outside `routewise/`, in `routewise.toml`, so nothing is lost; `ROUTING-BINDING.md` is rendered again from it, with any new role. When a release ships a newer rules spec, the binding says "approval pending" until you set `approved_rules_version` in `[binding]`.

**From 0.3.x or older:** the first run stops, because the old `ROUTING-BINDING.md` was hand-filled. Move its "Approved by", assistant pins and review date into `[binding]` in `routewise.toml`, delete `ROUTING-BINDING.md`, and run `routewise/install` again.

## Safety

- Every write stays inside the project. Paths in `routewise.toml` must be relative, a symlink that leads out of the project is refused, and each path is checked again right before it is written. Do not run routewise while another program is rewriting the project.
- `routewise/` must sit directly in the project root it sets up: `--project` must be the folder that holds `routewise/`, or `routewise/` itself (so routewise can run on its own repo). Any other folder is refused, and so are your home folder and every folder above it, even when routewise sits at `~/routewise`: agents and `CLAUDE.md` there apply to every session. So generated files never hold absolute paths and never land in global config.
- A folder that is itself a routewise repo (a clone or fork of routewise) is refused when a copy inside it runs the install, for example after the update command above: run `./install --project .` there instead, and delete the unpacked `routewise/`.
- A generated agent file starts with a `# generated by routewise from routewise/roles/<same name>.md` line (a stand-in's line names its own file after `as`: `… roles/reviewer.md as code-reviewer.md; …`). The installer rewrites or deletes only such files, and refuses to overwrite any other file in its way.
- The delegation block sits between a `routewise:start` line and a `routewise:end` line. Markers count only as whole lines outside fenced code, so text that mentions them is safe. Broken or duplicated markers stop the run, so you fix them by hand instead of losing text. Text outside the block keeps its line ends (CRLF too); only the blank lines right next to the block are normalised.
- routewise never creates a symlink: Claude Code's Edit and Write tools refuse to write through one, and Windows checks a committed symlink out as a one-line file. An existing symlinked instruction file (`CLAUDE.md` -> `AGENTS.md`) is edited through its target and never deleted.
- `CLAUDE.local.md` and files above the project are never written. Uninstall removes the routewise blocks from `AGENTS.md` and `CLAUDE.md`, and deletes either file only when nothing else is left in it.
- Before writing, the installer checks that every target can be written, and each file is written to a temporary file first and then renamed into place, so a failed run does not leave a half-written or empty file.
- Roles get no write or edit tools (spec R-A1): role files may hold only `name`, `description`, `tools`, `tier`, `effort` and `skills` (a skill adds no tool); a role needs at least one tool, and only each harness's known read and search tools, its shell and its web tools can be granted. A shell (`Bash`) can still change files: roles that have one are told to run only commands that read and to create no file, not even a temporary one, which is an instruction, not a sandbox. A skill a role loads cannot add a tool, but a skill's own `allowed-tools` can pre-approve one the role already has (its shell), so name in `[skills]` only skills you trust.
- `miss-log` refuses clear leaks: e-mail addresses (also spelled out, encoded as `%40` or `&#64;`, in Markdown or quotes, split by an invisible character, or without a dot, `me@localhost`), URLs (also without a scheme, `example.com/page`, or URL-encoded), IP addresses, UUIDs and chat IDs, home folder paths, phone and card numbers, and common token and key formats, also right next to text in another script (`服务器在10.0.0.12上`). It lets normal code words pass (`logger.info`, `@property`, `GPT-4`), so it cannot catch a name, a bare host name or an internal ID: the agent writes the miss in its own words.

## Changing the rules

- A project choice (cap, harness, a pinned model, assistant mode, review checklists, stand-ins): `routewise.toml`.
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
