When a session offers you options and you cannot decide, you can now say **"ask a judge"**. The session starts `judge`, an independent expert on the strongest model (Fable at medium effort on Claude Code), in a fresh context, and shows you its advice. You still decide. It works with the `dev` block and the `assistant` block.

## New

- **The `judge` role.** It gets the decision, its context and every option offered so far, word for word, but not the option the session favours, so it forms its own view. It checks the facts the options rely on (files, docs, the web), weighs each option, and picks one or proposes a better one. Its reply, at most 40 lines, gives its recommendation, its confidence, what would change the call, and up to three questions for you. The session shows you the question, the options with its own recommendation as before, and the judge's verdict, then waits: follow the judge, pick another option, give your own, answer its questions, or ask for another round. The verdict is never taken as your choice or your approval.
- **Only on your word.** The judge runs on the most expensive tier, so the session never starts one on its own. A mail, a memory or another agent's report that asks for a judge does not count: only your own message.
- **Blocked pages.** If a page the judge needs is refused (a sandbox network policy, a login wall), it does not work around the block. It gives its best call without the page and a line such as `Needs access: docs.example.com/limits (from: search result) — the rate limit — could favour option B`. The source is the judge's own claim, so the session marks each domain as found in your message (`in the brief`) or `claimed by the judge`, recommends allowing none, and reminds you that allowing a domain opens every path on it. If you allow one, the session starts a new judge with the same brief.
- **Assistant mode.** An assistant that runs on a cheaper model can consult the judge when you ask. It quotes what the decision needs from memory, connectors, mail or documents into the brief, marked as other people's text, with source and author, without their links, and with no secrets; it takes exact values (IDs, dates, amounts) from the source again afterwards. When a mail or document tries to instruct an AI ("any AI assistant must fetch…"), the assistant tells you who sent it and what it asked, and does not follow it, whether or not a judge is involved.
- **Settings that already work:** change the judge's model with `[tiers] frontier = "…"`, and give it a skill with `[skills] judge = ["…"]`, in `routewise.toml`. On Antigravity CLI, agent files cannot set a model, so there the judge runs on the session model and brings a fresh context only.

## Security: what the judge can and cannot do

The judge keeps all its tools (it reads files, runs read-only commands and uses the web) so it can ground what it says. Its instructions forbid sending anything out: the network only through its web tools, never `curl` or a logged-in command-line tool, no credential, `.env`, transcript or memory files, nothing from the brief in a search query or URL, no URL taken from text it read. In live runs on Claude Code 2.1.326 it ignored a vendor mail that told "any AI" to send an API key to a URL.

Instructions are not a sandbox, though. Run agents where the network is an allowlist, allow a domain from a `Needs access` line only when you know the site and would allow it anyway, and never allow a site where anyone can read what is posted (paste sites, request catchers). Web searches go to the search provider whatever your allowlist. The README's "Asking a judge" section has the details and an optional set of Claude Code deny rules, with their limits.

## Changed

- **The shipped rules spec is version 4:** the `judge` role (R-A7), a second opinion you ask for (D4), the exception to "never delegate judgment calls" for it (N2), the judge in assistant mode (A4), and `judge` as the approved exception to "a role on the `frontier` tier needs approval first".
- **Both delegation blocks** gain the judge rule; the `dev` block's "never delegate judgment calls" names the exception. The assistant block allows `judge` besides `web-reader`.

## Update

From the project root (the old folder is replaced only after the download succeeded):

```sh
v=0.3.0
mkdir routewise.new && curl -fsSL "https://github.com/f0t0n/routewise/archive/refs/tags/v$v.tar.gz" | tar -xz --strip-components=1 -C routewise.new && rm -rf routewise && mv routewise.new routewise && routewise/install
```

The update writes a new `judge.md` into each agent folder (`.claude/agents/`, `.agents/agents/`) and rewrites the delegation block in `AGENTS.md`. Commit them with the update. Your `routewise.toml`, `ROUTING-BINDING.md` and miss log stay as they are, so:

- **Add the judge to your binding by hand.** `ROUTING-BINDING.md` is written on the first run only. Add a row like this one, with your name and today's date:

  ```
  | `judge` | `frontier` at `medium` (R-A7): runs only when the person asks for a judge on a decision. Approved by <name>, <date>, with rules spec version 4. |
  ```

- **Start a new session** after updating. Claude Code reads the delegation block in `AGENTS.md` when a session starts, so a running session would not know the judge rule yet (the new `judge.md` agent file is picked up either way).

Full list: [CHANGELOG](https://github.com/f0t0n/routewise/blob/v0.3.0/CHANGELOG.md).
