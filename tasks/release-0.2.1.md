A bug-fix release: a routewise copy no longer installs into a clone of routewise itself. Projects that hold `routewise/` work as before, and updating changes none of their files.

## Fixed

- **`routewise/install` refuses to run inside a routewise repo.** If a folder holds routewise's own files at its root (`install`, `lib/install.py`, `roles/` and `harness.toml`: a clone, a fork or an older checkout) and a copy of routewise sits inside it, for example after running the README's install or update command there, `routewise/install` now stops with exit code 2 and writes nothing, also with `--check` and `--uninstall`:

  ```
  routewise: /path/to/clone is a routewise repo, so routewise/ inside it is not its installer; run ./install --project . there (make self in a clone), and delete routewise/ if a download put it there
  ```

  Before, it treated the clone as an ordinary project and rewrote its agent files and the delegation block in `AGENTS.md` with `routewise/install` and `routewise/bin/miss-log` commands. If that happened to you, restore those files from git. A refused update leaves the unpacked `routewise/` folder behind: delete it. (Since 0.1.0.)

  Only copies from 0.2.1 on have this check: the same command with `v=0.2.0` or older still does the damage.

`bin/miss-log` is not affected: run from such a copy, it still appends to the log the clone's `routewise.toml` names.

## Update

From the project root (the old folder is replaced only after the download succeeded):

```sh
v=0.2.1
mkdir routewise.new && curl -fsSL "https://github.com/f0t0n/routewise/archive/refs/tags/v$v.tar.gz" | tar -xz --strip-components=1 -C routewise.new && rm -rf routewise && mv routewise.new routewise && routewise/install
```

Roles, templates and `harness.toml` are unchanged since 0.2.0, so the install rewrites none of your generated files (in a project in step with 0.2.0 it prints `routewise: nothing to change`), and there is nothing to commit apart from the `routewise/` folder itself. No new session is needed: the agents and the delegation block stay the same.

Full list: [CHANGELOG](https://github.com/f0t0n/routewise/blob/v0.2.1/CHANGELOG.md).
