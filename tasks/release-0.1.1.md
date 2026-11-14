A bug-fix release: the miss log's privacy filter now refuses private text that 0.1.0 let through: an e-mail address without a dot in the domain, a link without a scheme, and an address that is quoted, encoded or split by an invisible character. Update if your project commits `logs/delegation-misses.jsonl`, since an entry that gets in stays in git history.

## Fixed

- **The miss log refuses an e-mail address without a dot in the domain:** `me@localhost`, `anna@corp`, `deploy@main-db`. Package and git references still pass: `pkg@latest`, `actions/checkout@v4`, `HEAD@{1}`.
- **The miss log refuses a link without a scheme or `www.`:** `example.com/page`, `jira.corp.net/browse/X-1`, also with a port (`host.corp:8080/x`), in capitals, with a Unicode host, as `//host.com/x`, or followed by `?…` or `#…`. File paths, versions and ratios still pass: `lib/privacy.py`, `src/a.ts/`, `README.md/`, `docs/v0.1.0/`, `3.5/5`.
- **The miss log refuses an address in Markdown or quotes, or with an encoded `@`:** `"anna"@corp.com`, `anna\@corp.com`, `` `anna`@corp.com ``, `[anna]@corp.com`, `{anna}@corp.com`, `anna@**corp.com**`, `anna%40corp.com`, `anna&#x40;corp.com`, `anna\u0040corp.com`, `anna\x40corp.com`. A link after an encoded `@` is still refused (`redirect=%40example.com/path`).
- **The miss log refuses a leak hidden by an invisible character,** such as a left-to-right mark, a bidi control, a variation selector or a Hangul filler, whether it sits inside an address or token or right before one (not both at once).
- **A version made only of digits and dots after `@` now passes** (`react@18.3.1`); 0.1.0 refused it as an address. A version with a letter (`pkg@v1.2.3`, `actions/checkout@v4.1.0`) is still refused, as in 0.1.0.
- **`bin/miss-log` prints its errors as `routewise: <message>`**, like every other routewise command, instead of `miss-log: <message>`. The exit code (2) and the message text are unchanged.

## Newly refused code words

A few code words read exactly like a link or an address, so the miss log now refuses them: a dotted name before a slash whose last part is all letters (`logger.info/debug`, `os.path/join`, `ASP.NET/Core`) and `a@b`. Write them with a space or "and" (`logger.info and logger.debug`). `logger.info`, `@property` and `GPT-4` on their own still pass.

The filter still cannot catch a name, a bare host name without a path, or an internal ID; the agent describes a miss in its own words. Not caught yet either: a host without a dot before a port and a path (`localhost:3000/admin`), `//jenkins/x`, a host with one dot after a slash (`proxy/jira.com/x`), a defanged address (`anna[@]corp[.]com`), a double-encoded `@` (`%2540`), a leak with one invisible character right before it and another inside it, markup inside the local part or HTML around the `@`, and rare forms of `@` (`&#64` without `;`, `%u0040`, `\u{40}`, `=40`).

## Also new

- The README's "Install into a project" opens with a copy-paste install of the current release, and "Updating" has the same for a newer one. Both stop on an HTTP error and never run an older copy.

## Update

From the project root (the old folder is replaced only after the download succeeded):

```sh
v=0.1.1
mkdir routewise.new && curl -fsSL "https://github.com/f0t0n/routewise/archive/refs/tags/v$v.tar.gz" | tar -xz --strip-components=1 -C routewise.new && rm -rf routewise && mv routewise.new routewise && routewise/install
```

No generated file changes in this release: on a 0.1.0 install, `routewise/install` prints `routewise: nothing to change`. Your `routewise.toml`, `ROUTING-BINDING.md` and miss log stay as they are. Entries already in the miss log are not re-checked.

Full list: [CHANGELOG](https://github.com/f0t0n/routewise/blob/v0.1.1/CHANGELOG.md).
