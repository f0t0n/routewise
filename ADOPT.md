# Adopting routewise (instructions for the agent)

The person asked you to adopt routewise in this project. Follow these steps in order. Do not edit files under `routewise/`, and do not edit generated files by hand: the installer owns them.

1. **Check the place.** `routewise/` must be at the project root. Run `python3 --version` (3.11 or newer is needed). If either fails, stop and say what is missing.
2. **Ask the person, in one message,** and wait for the answers:
   - Which harnesses: Claude Code, Antigravity CLI, or both?
   - Is this agent a developer of the project (`dev`) or a user-facing assistant (`assistant`, which may delegate only web-page reading)?
   - Is the parallel cap of 5 subagents at once fine?
   - Which instruction files should get the delegation block (default `CLAUDE.md`, plus `AGENTS.md` if it exists)?
3. **Run `routewise/install`.** On the first run it writes `routewise.toml`. Edit `routewise.toml` to match the answers, then run `routewise/install` again. Show the person its output. If it exits with code 2, nothing was written: show the error and stop. For example, an agent file it did not write is in the way, or the delegation markers in an instruction file are broken; the person decides how to fix it.
4. **Fill in `ROUTING-BINDING.md`:** "Approved by" (the person's name and today's date), the assistant pins (A3) or "not an assistant project", and the first miss-log review date (two weeks from today; get today's date from `date +%F`, do not guess it).
5. **Verify:** `routewise/install --check` exits 0, and `routewise/bin/miss-log report` prints `misses: 0`.
6. **Tell the person the live check:** in a *new* session (an open one keeps its old instructions), ask for a file search that starts `Explore`, then confirm it ran on the `fast` model: in Claude Code, the subagent's `.meta.json` under `~/.claude/projects/<folder>/<session>/subagents/` shows `"isBuiltIn": false` and a Haiku model. This is spec section 11, item 4.
7. **Offer to commit** `routewise/`, `routewise.toml`, `ROUTING-BINDING.md`, the agent folders, the instruction files and `logs/delegation-misses.jsonl`, using the project's commit conventions. Commit only if the person agrees.

From then on, the delegation block in the instruction file is the rule set. The full reasoning is in `routewise/spec/SPEC-model-routing.md`.
