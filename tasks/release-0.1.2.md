A bug-fix release: the miss log's privacy filter closes the gaps 0.1.1 listed as planned for 0.1.2. Update if your project commits `logs/delegation-misses.jsonl`.

## Fixed

- **A leak right next to text in another script is refused:** `服务器在10.0.0.12上`, `key AKIA…が漏れた`, `见www.example.com`, `ב10.0.0.12`, an ID or token right after Chinese or Japanese text. Text 0.1.1 already refused after a space is now also refused right after such a letter (`版本1.2.3.4`, as `version 1.2.3.4` was; `café10.0.0.12`). An ASCII letter or digit still joins the word, so `xAKIA…` and `v10.0.0.12` pass as before.
- **A URL-encoded link is refused:** a scheme followed by `%3A%2F%2F`, in any case (`next=https%3A%2F%2Fjira.corp.net%2F…`). An encoded `:` or `/` on its own still passes (`100%3A`, `C%3A%2Ftemp`).
- **An escaped `@` without a dot in the domain is refused:** `me\@localhost`. Spaces around a dotless `@` still pass.
- **A JWT written with `。` is refused,** whatever follows it (`eyJ…。eyJ…。_Qx9`).
- **More link ends after a host:** `?$`, `#!/` and `#:~:` start a query or anchor (`api.corp.net?$top=5`, `app.corp.io#!/users/1`, `docs.corp.io#:~:text=x`).
- **A Chinese, Japanese or Korean question right after `?` or `？` passes again** (`为什么用foo.bar？因为快`, refused by 0.1.1), as do `foo.bar?!` and Kotlin's `foo.bar?:x`: a query or anchor must start with an ASCII character.

## Still not caught

A non-ASCII anchor right after a host with no path (`wiki.corp.io#Раздел`; a copied link has a `/` before it and is refused), spaces around a dotless `@`, and the other gaps listed for 0.1.1. The filter still cannot catch a name, a bare host name without a path, or an internal ID; the agent describes a miss in its own words.

## Update

From the project root (the old folder is replaced only after the download succeeded):

```sh
v=0.1.2
mkdir routewise.new && curl -fsSL "https://github.com/f0t0n/routewise/archive/refs/tags/v$v.tar.gz" | tar -xz --strip-components=1 -C routewise.new && rm -rf routewise && mv routewise.new routewise && routewise/install
```

No generated file changes in this release: on a 0.1.1 install, `routewise/install` prints `routewise: nothing to change`. Your `routewise.toml`, `ROUTING-BINDING.md` and miss log stay as they are. Entries already in the miss log are not re-checked.

Full list: [CHANGELOG](https://github.com/f0t0n/routewise/blob/v0.1.2/CHANGELOG.md).
