First release of **routewise**: model routing and delegation for coding and assistant agents, set up by rules instead of the agent's mood.

routewise gives a project:

- **Five subagents without write or edit tools**, each on the cheapest model that does its job well: `Explore` (file sweeps; it replaces Claude Code's built-in one), `log-reader` and `web-reader`, all on `haiku`; `reviewer` on `sonnet` at `medium` effort, `auditor` on `opus` at `high`. The main session keeps the decisions and the edits. `log-reader`, `reviewer` and `auditor` keep `Bash` to run tests and read logs; their instructions allow only commands that read, but nothing sandboxes them.
- **A delegation block** in the project's `AGENTS.md`: what to delegate, what never to delegate, a parallel cap (5 by default) and an escalation ladder.
- **A miss log** (`routewise/bin/miss-log`) that records each delegated result that was wrong or redone, so roles change on evidence, not taste.

The rules are in [`spec/SPEC-model-routing.md`](https://github.com/f0t0n/routewise/blob/v0.1.0/spec/SPEC-model-routing.md), based on Addy Osmani's article ["Which Claude model should you build with?"](https://claude.dev/blog/which-claude-model-should-you-build-with/).

## Install

Requirements: Python 3.11 or newer and `bash`. No other dependencies.

```sh
cd your-project
curl -L https://github.com/f0t0n/routewise/archive/refs/tags/v0.1.0.tar.gz | tar -xz
mv routewise-0.1.0 routewise
routewise/install
```

Then review `routewise.toml`, fill in `ROUTING-BINDING.md`, commit, and open a new agent session. The archive holds only the runtime files. Full steps: [README](https://github.com/f0t0n/routewise/blob/v0.1.0/README.md); to let an agent do it: [ADOPT.md](https://github.com/f0t0n/routewise/blob/v0.1.0/ADOPT.md).

## What's in 0.1.0

- **Harnesses:** Claude Code (`cc`, model and effort per agent) and Antigravity CLI (`agy`, agents follow the session model).
- **`AGENTS.md` first.** The delegation block goes into `AGENTS.md`. Per [Claude Code's docs](https://code.claude.com/docs/en/memory), Claude Code reads `AGENTS.md` natively from v2.1.277 (v2.1.281 for Bedrock or telemetry-off sessions), but only when no `CLAUDE.md`, `.claude/CLAUDE.md` or `CLAUDE.local.md` sits in the project or above it. So the `claude_md` setting (`auto`, `import`, `none`) adds an `@AGENTS.md` import block to an existing `CLAUDE.md`, and warns about the cases it cannot fix; routewise never creates symlinks.
- **`routewise/install --check`** reports drift and exits 1, for CI or a pre-commit hook; **`--uninstall`** removes the agents and blocks it generated; it keeps `routewise.toml`, `ROUTING-BINDING.md`, the miss log and the `routewise/` folder, and the rest of your files as they were (only the blank lines next to a block are normalised).
- **Safety:** every write stays inside the project; your home folder is never a project; a failed run writes nothing; only files routewise generated are rewritten or deleted; broken markers stop the run instead of losing text; roles get no write or edit tools; the miss log refuses clear leaks (addresses, URLs, tokens, home paths).
- **Verified live** on Claude Code 2.1.325: the generated `Explore` replaces the built-in one and runs on Haiku (11 of 12 transcript entries; one ran on the main session's model), and `AGENTS.md` is read natively and through the `@AGENTS.md` import blocks routewise writes (rules spec section 13). The version floors above come from Claude Code's docs and were not tested live.

Full list: [CHANGELOG](https://github.com/f0t0n/routewise/blob/v0.1.0/CHANGELOG.md).
