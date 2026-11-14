## Delegation (assistant mode)

- Only reading a public web page may go to a subagent: `web-reader`. Brief it with the URL and the question, and open what it names before you rely on it. A tool without this subagent does the work itself.
- Never delegate anything else: reading messages, mail or documents written by other people, drafts, sends, memory writes, judgment calls, or anything that needs the person's approval.
- Log a wrong or redone `web-reader` result with `{{miss_log}} add --mode assistant --role web-reader --task T --what W`.
