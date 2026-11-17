`reviewer` and `auditor` now load a maintained checklist skill for what to check, [agent-skills](https://github.com/addyosmani/agent-skills) by Addy Osmani by default, while routewise keeps deciding how a review runs: its model, its tools (none that write) and the shape of what it returns. Projects that use agent-skills' `/ship` can have it run these read-only roles instead of the plugin's own agents. Two bugs from 0.1.0 are fixed.

## New

- **Review checklists from skills.** `reviewer` loads `agent-skills:code-review-and-quality` and `auditor` loads `agent-skills:security-and-hardening`. Claude Code puts each skill's full text into the subagent when it starts, so a project always gets the plugin's current checklist and routewise keeps no copy of it. Install the agent-skills plugin to use them. Which checklist to use is a matter of preference: choose another installed skill, or none, in `routewise.toml`:

  ```toml
  [skills]
  reviewer = ["my-review-skill"]   # any installed skill: name or plugin:name, up to 32 per role
  auditor = []                     # no skill: the role's own short method only
  ```

- **A `Checklist` line in every review.** The agent file names the role's skills, and each reply starts with `Checklist: agent-skills:code-review-and-quality loaded` (or `missing`). A skill that is not installed or was renamed is skipped without an error, and the main session tells you once per session.
- **Stand-ins for agent-skills' `/ship`.** `/ship` starts the plugin's `code-reviewer` and `security-auditor`, which can write files and run on the session's model. With

  ```toml
  [stand_ins]
  reviewer = ["code-reviewer"]
  auditor = ["security-auditor"]
  ```

  routewise also writes `code-reviewer.md` and `security-auditor.md` as copies of its read-only roles, and the delegation block tells the session to start them, not the plugin's. Off by default; turn it on only where you run `/ship`. An agent file of that name that routewise did not write stops the run.

## Changed

- **The review roles' instructions.** A skill says what to check; the role still decides how to behave and what to return, and wins where they disagree. A skill step that would change a file (a mutation test, deleting unused code) comes back as a suggestion. Running code counts as writing: the roles create no file anywhere, not even a temporary one, and run code only so that it writes nothing (`python3 -B -c`). Skill text found in a reviewed file or diff, or under another name, is data. A skill's severity names are mapped to Critical, Required, Optional and Nit.
- **Mutation suggestions.** `reviewer` returns up to 3 conditions it expects the tests to miss; with the `dev` delegation block, the main session inverts each, runs the tests and restores the file, and one the tests miss is a Required finding.
- **Rules spec version 3:** rule R-A6 (a role may load skills for what to check), the `Checklist` line and mutation suggestions in the review returns and in the section 10 block, and the live checks behind them in section 13.
- **Antigravity CLI** (1.5.9) accepts the new `skills:` line but does not load the skill yet; there the roles use their own method and show their skills as `missing`.

## Fixed

- **A model name ending in a line break is refused** (`[tiers] fast = "haiku\n"`); it used to leave a blank line in the agent's frontmatter. No key could be added. (Since 0.1.0.)
- **routewise's own repo only:** the miss-log command in its delegation block is now `bin/miss-log --project .`; plain `bin/miss-log` wrote to the folder above the repo. Projects that hold `routewise/` are not affected. (Since 0.1.0.)

## Update

From the project root (the old folder is replaced only after the download succeeded):

```sh
v=0.2.0
mkdir routewise.new && curl -fsSL "https://github.com/f0t0n/routewise/archive/refs/tags/v$v.tar.gz" | tar -xz --strip-components=1 -C routewise.new && rm -rf routewise && mv routewise.new routewise && routewise/install
```

This release rewrites generated files: `reviewer.md` and `auditor.md` in each agent folder (`.claude/agents/`, `.agents/agents/`) and the delegation block in `AGENTS.md`. Commit them with the update. Your `routewise.toml`, `ROUTING-BINDING.md` and miss log stay as they are. An existing `routewise.toml` has no `[skills]` or `[stand_ins]` table, so the defaults apply: the agent-skills checklists, no stand-ins. Add either table yourself to change that (examples above; the comments in a new install's `routewise.toml` show both), then run `routewise/install` again. Start a new session afterwards; Claude Code picks up changed agent files at once, but an open session keeps its old instruction file.

Full list: [CHANGELOG](https://github.com/f0t0n/routewise/blob/v0.2.0/CHANGELOG.md).
