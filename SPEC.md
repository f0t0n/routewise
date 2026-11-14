# Spec: routewise (the tool)

Status: approved 2026-11-14 (R3 approved the same day); R4 added and approved after the 0.1.0 release; R5 (the 0.1.1 miss-log fix) approved 2026-11-14, after it was built (catch-up: Define and Plan had been skipped); R6 and the Ship row change (release notes for every release) approved 2026-11-14; R5 amended after review and audit, approved 2026-11-14; amended again after the re-audit (two views of the text), approved 2026-11-14; one kept gap added during its build, approved 2026-11-14; amended after round 3 (four views, the invisible set), approved 2026-11-14; amended after round 4 (no false positives from markup or `。`, gaps for 0.1.2), approved 2026-11-14; amended after round 5 (`。` beside non-CJK letters, SHA pins, trade-offs named), approved 2026-11-14; amended after round 6 (SHA needs a digit, ASCII case only, `?` and `#` need a URL character, trade-off examples), approved 2026-11-14; round 7's findings moved to 0.1.2 and a stopping rule for review rounds added to the workflow, approved 2026-11-14. Describes routewise 0.1.0 as built, plus three additions: a clean release archive (R1), routewise running on its own repo (R2), and commands spelled for the project they are written into (R3). R7 (the 0.1.2 miss-log gaps) approved 2026-11-14; amended after its review (G3 and paths, card edges), approved 2026-11-14.

This file specifies the **tool**: the installer, the miss log, the role files and templates, the safety rules they keep, and how this repo is developed. The **rules** the tool installs (tiers, roles, delegation, escalation, measurement) are a separate, project-agnostic document, [spec/SPEC-model-routing.md](spec/SPEC-model-routing.md), shipped unchanged into every project. When the two disagree on a rule, the rules spec wins; when they disagree on how a file is written, this spec wins.

## Objective

routewise turns the rules spec into files an agent harness actually loads, so model routing and delegation are set by rules instead of the agent's mood.

Users:

- **Project maintainer:** copies `routewise/` into a project, runs `routewise/install`, reviews `routewise.toml`, fills in `ROUTING-BINDING.md`, commits.
- **An agent adopting it for a person:** follows [ADOPT.md](ADOPT.md) step by step.
- **The agent working in the project afterwards:** reads the delegation block in `AGENTS.md`, starts the generated subagents, records misses with `routewise/bin/miss-log`.
- **routewise maintainer** (and the agents helping): develops this repo by the workflow below; projects replace `routewise/` wholesale on update.

What it must do:

1. **Agents.** Render each neutral role in `roles/*.md` into the agent format of each chosen harness (`cc`: `.claude/agents/`, `agy`: `.agents/agents/`), with the tier mapped to a model and the effort set where the harness supports it (`harness.toml`, overrides in `routewise.toml` `[tiers]`).
2. **Delegation block.** Write the fragment (`templates/fragment-dev.md` or `fragment-assistant.md`) between `routewise:start` and `routewise:end` markers in each instruction file (default `AGENTS.md`).
3. **Claude Code bridge.** Per `claude_md` (`auto`, `import`, `none`), keep a routewise block holding an `@AGENTS.md` import in `CLAUDE.md`, or `@../AGENTS.md` in `.claude/CLAUDE.md`, so Claude Code reads `AGENTS.md`; note a lone `CLAUDE.local.md` and warn about CLAUDE files above the project. Verified live on Claude Code 2.1.325 (rules spec section 13).
4. **First run.** Write `routewise.toml` (settings), `ROUTING-BINDING.md` (approvals, rules spec section 9) and an empty miss log, never overwriting them later.
5. **Drift and removal.** `--check` reports what a run would change and writes nothing; `--uninstall` removes generated agents and every routewise block, keeping settings, binding and miss log.
6. **Miss log.** `bin/miss-log add` appends one validated JSON line per wrong or redone delegated result, stamping time, tier and effort itself; `report` summarises by role, tier and effort.
7. **R1: Clean release archive.** A release archive (GitHub's "Source code" download for a tag, or `git archive`) holds only the runtime files: `install`, `bin/`, `lib/`, `roles/`, `harness.toml`, `templates/`, `spec/`, `README.md`, `ADOPT.md`, `LICENSE`, `CHANGELOG.md`. Every development file is marked `export-ignore` in `.gitattributes`. The README recommends installing from a release archive; a submodule or subtree still works but carries the development files, and `AGENTS.md` keeps a guard for agents in a host project.
8. **R2: routewise on its own repo.** The installer also accepts the routewise folder itself as the project root, so this repo runs `./install --project .` (`make self`) on itself: its own `routewise.toml`, `ROUTING-BINDING.md`, `.claude/agents/`, miss log and a delegation block in this repo's `AGENTS.md`, with paths spelled from the repo root (`bin/miss-log`). `make check` runs `./install --project . --check`, so a change to roles, templates or `harness.toml` that is not re-installed fails the pre-commit hook.
9. **R3: Commands spelled for the project.** Every routewise command or path that the installer writes into a project is spelled from that project's root: the delegation block's start marker, the generated-agent marker line, `ROUTING-BINDING.md` (re-install command, roles folder, `harness.toml`, miss-log command) and the comment at the top of `routewise.toml` (re-install command; added after review). In a project that holds `routewise/` they read `routewise/install`, `routewise/roles/`, `routewise/harness.toml`, `routewise/bin/miss-log`; in routewise's own repo `./install --project .`, `roles/`, `harness.toml`, `bin/miss-log`. Detection does not change: a block is still found by its `<!-- routewise:start` prefix and a generated agent by `# generated by routewise from <file>; edit that file`, so existing files are recognised and simply rewritten once. The installer's own `--help` text is out of scope (it is not written into a project).
10. **R4: Copy-paste install in the README.** `README.md` "Install into a project" opens with a command block that installs the current release from its GitHub archive: set `v=<version>`, then one `&&` chain that creates `routewise/` (and stops if it exists), downloads `https://github.com/f0t0n/routewise/archive/refs/tags/v$v.tar.gz` with `curl -f` (and stops on an HTTP error), unpacks it into `routewise/` and runs `routewise/install`, so the block never runs an older copy. "Updating" has the same chain for a newer release, which replaces the folder only after the download succeeded. Every `v=` in the README equals `version` in `pyproject.toml`, and the install block downloads `v$v`; a test fails otherwise, so a release cannot ship a README that installs an older version (block made safe after review). The prose steps (review settings, fill in the binding, commit, new session) follow the block.
11. **R5: Miss-log filter catches dotless addresses and links without a scheme (0.1.1, bug fix).** 0.1.0 let `me@localhost`, `anna@corp` and links such as `example.com/page` or `jira.corp.net/browse/X-1` into the committed miss log. The filter (`lib/privacy.py`) also refuses:
    - **An e-mail address without a dot in the domain:** a word, `@` with no space around it, then a name that starts with a letter of any script (`anna@корп`). A version or package tag that is the whole name passes, in any ASCII case (so `anna@maın` with a dotless i is still an address): `v<digits>`, a commit SHA of 7 to 40 hex digits with at least one digit (so `user@deadbeef` is still an address), `latest`, `next`, `beta`, `alpha`, `canary`, `rc`, `stable`, `lts`, `main`, `master` (`pkg@latest`, `foo@Latest`, `actions/checkout@v4`, `user/repo@e83a1b2`; SHA pins added after round 5); a longer name that starts with one does not (`deploy@main-db`, `ops@v2-gateway`).
    - **A link without a scheme or `www.`:** a host with a TLD of 2 to 63 letters (any case or script), an optional port, then `/`, or `?` or `#` followed by a letter, digit or one of `_ % = & / ~ + -` (so `(what is foo.bar?)` and `foo.bar?!` pass; tightened after round 6). A host with two or more dots is refused wherever it starts a word, also after a slash (`proxy/jira.corp.net/x`). A host with one dot must also not follow a lone slash (`src/a.ts/` passes, `//host.com/x` is refused) and must not end in a source file type (`md`, `py`, `rs`, `ts`, `tsx`, `js`, `jsx`, `mjs`, `cjs`, `json`, `toml`, `yaml`, `yml`, `txt`, `lock`, `cfg`, `ini`, `html`, `css`, `sh`, `rb`, `kt`, `go`, `java`, `cpp`, `hpp`), so `README.md/` and `Next.js/` pass.
    - **A dotted address with Markdown or quotes around the `@`:** up to three of `\` `"` `'` `*` `` ` `` `_` `~` right before the `@`, and up to three of `*` `` ` `` `_` `~` right after it (`anna\@corp.com`, `"anna"@corp.com`, `***anna***@corp.com`, `` `anna`@corp.com ``, `anna~@corp.com`, `anna@**corp.com**`, `` anna@`corp.com` ``); only when the domain has a dot. Brackets, braces, angle brackets, and quotes after the `@` are not markup here: they are code (`a[i]@m.T`, `f(x)@w.T`, `f"{user}@{cfg.domain}"`, `obj@"pkg.json"`), and refusing them broke success criterion 10 (added after audit; widened after re-audit and round 3; narrowed after round 4).
    - **Normalisation, four views of the text:** a step that only adds evidence applies to every view: NFKC, and an ideographic full stop (`。`) between two letters or digits of any script except CJK and Hangul (CJK including the compatibility ideographs U+F900–FAFF, some of which NFKC leaves as they are, such as `﨑`) read as a dot (`jira。corp。net/x`, `10。0。0。1`, `пример。рф/x`, `١٠。٠。٠。١`); one next to CJK or Hangul text ends a sentence, so `修复路由。然后改a/b` passes (narrowed after round 4, widened to non-CJK scripts after round 5). A step that can also hide text gets a view with it and a view without it: invisible characters are either spaces or removed, and an encoded `@` is either decoded or left as it is. The patterns run on all four combinations, and the text is refused if any matches. So an invisible character still ends the word before a leak (`שלום<LRM>ghp_…`, `שלום<LRM>10。0。0。1`), an invisible character or an encoding cannot split an address or a token, and a decoded `@` cannot hide a link after it (`redirect=%40example。com/path`). NFKC runs again after a character is removed, so a letter split from its accent recombines. *Encoded `@`:* `%40`, `&#64;`, `&#064;`, `&#x40;`, `&commat;` (any case), a literal `\u0040` or `\x40`; not quoted-printable `=40`, since `width=40px` would read as `width@px`. *Invisible characters:* every format character (Unicode category Cf), every Unicode Default_Ignorable_Code_Point (U+00AD, U+034F, U+061C, U+115F–1160, U+17B4–17B5, U+180B–180F, U+200B–200F, U+202A–202E, U+2060–206F, U+3164, U+FE00–FE0F, U+FEFF, U+FFA0, U+FFF0–FFF8, U+1BCA0–1BCA3, U+1D173–1D17A, U+E0000–E0FFF), and the braille blank U+2800 (added after audit; split into views after re-audit, which found that removing them alone joined a token to the word before it; four views and the Default_Ignorable set after round 3, which found that decoding in the only view that read `。` or removed invisible characters hid a link).
    - **Also changed:** a dotted domain must hold a letter (any script), so a version made only of digits and dots passes (`react@18.3.1`, also `user@10.0.1`) while `anna@1password.com` and `jane@пример.рф` stay refused. A version with a letter is still refused as an address, as in 0.1.0 (`actions/checkout@v4.1.0`, `pkg@v1.2.3`, `tsc@5.4.x`).
    - **Still passing:** file paths, versions and ratios (`lib/privacy.py`, `docs/v0.1.0/`, `v1.25/`, `3.5/5`), `HEAD@{1}`, `@property`, every phrase 0.1.0 let through on purpose.
    - **Known trade-offs, refused on purpose:** a dotted name whose last part is all letters, before a slash or before `?` or `#` with text after it (`logger.info/debug`, `os.path/join`, `ASP.NET/Core`, `Class.method#overload`, `config.key#section`, `abc.def?x=1`; also a file name with two dots, `foo.test.ts#L10`, `jquery.min.js?v=1`), `a@b` (also `pip install foo@git`, and a 6-digit SHA such as `foo@abc123`), an ASCII word or number, `。` and an ASCII path after CJK text (`改了config。lib/x.py`, `修复了问题1。src/a.ts`), `。` between words of a non-CJK script with no space (`Привет。Мир/x`), and a dotted name before a full-width `？` and CJK or Hangul text with no space (`为什么用foo.bar？因为快`; NFKC reads `？` as `?`; to be fixed in 0.1.2), since they read exactly like a link or an address (`jira。corp。net/x`); the agent writes them with a space or "and" (trade-offs named after round 5).
    - **Known gaps, kept:** `me @localhost` (a space around a dotless `@` would refuse `used @property`), `root@master` and `me@main` (tag words), a bare host without a path (as in 0.1.0). Found in review and audit, kept for a follow-up because a rule for them needs its own false-positive check: a host without a dot followed by a port and a path (`localhost:3000/admin`, `jenkins-prod:8080/job/x`; a `name:port/` rule would refuse `page:12/40`), `//jenkins/job/x`, and a host with one dot after a lone slash (`proxy/jira.com/x`; it cannot be told from `src/a.ts/`). A local part or TLD with combining marks or vowel signs (`सीता@corp.com`, `कंपनी.भारत/x`): Python's `re` has no `\p{M}`; a Devanagari domain without a dot is refused. Also kept after re-audit: a defanged address (`anna[@]corp[.]com`) and a double-encoded `@` (`%2540`). Kept while building the two views: a leak disguised twice, with an invisible character right before or after it and another inside it (`x<LRM>ghp<LRM>_…`); the split view breaks the token and the joined view joins it to the word before, and catching it means trying every mix of spaced and removed characters (2^n views). Kept after round 3: markup inside the local part or HTML around the `@` (`**anna **@corp.com`, `anna<b>@</b>corp.com`), and `@` written in other rare forms (`&#64` without a semicolon, `%u0040`, `\u{40}`, quoted-printable `=40`). Kept after round 4: brackets, braces and angle brackets before or after the `@`, and quotes after it (`[anna]@corp.com`, `{anna}@corp.com`, `<anna>@corp.com`, `anna@"corp.com"`), since they are code. For 0.1.2 (also missed by 0.1.0, so not part of this fix; all done in 0.1.2 by R7 except where marked): a leak touched by a CJK or Hebrew letter, since `\b` counts those as word characters (`服务器在10.0.0.12上`, `key AKIA…が漏れた`, `见www.example.com`); a URL-encoded link (`next=https%3A%2F%2Fjira.corp.net%2F…`); markup before a dotless `@` (`me\@localhost`, also with a Hangul filler); a dot right before the `@` (`foo.@bar`, already refused in 0.1.1); a JWT written with `。` whose second `。` is not followed by a letter or digit (a signature starting with `-` or `_`, or none). Found in round 7: `#:~:`, `?$` and `#!` after a host with no path (`docs.corp.io#:~:text=x`, `api.corp.net?$top=5`, `app.corp.io#!/users/1`), and the full-width `？` trade-off above. A leak touched by a CJK or Hangul letter on the other side of a `。` (`see example。中国/x`) was listed as part of the first item, but is not covered by R7: a `。` next to CJK text ends a sentence by R5's rule, so it stays with the `。` trade-offs.
12. **R6: One error prefix (0.1.1, bug fix).** Every error message routewise prints starts with `routewise: ` (Code Style), also those of `bin/miss-log`, which printed `miss-log: ` from Python in 0.1.0 while its bash wrapper printed `routewise: `. Exit code 2 and the message text after the prefix do not change. Usage errors from argparse keep its own form (`<prog>: error: ...`), as for `install`.
13. **R7: Miss-log gaps 0.1.1 named for 0.1.2 (0.1.2, bug fix).** Closes the gaps R5 lists "for 0.1.2" and the round-7 trade-off, without widening anything else. Each item keeps the R5 rules (four views, invisible characters, markup, tags) as they are.
    - **G1, a leak touched by a CJK, Hebrew or other non-ASCII letter:** the patterns that start or end at a word boundary (tokens and keys, a scheme or `www.` link, IPv4, IPv6, UUID, chat ID, card number) use ASCII boundaries instead of `\b`, so a letter or digit of another script right before or after a leak no longer hides it (`服务器在10.0.0.12上`, `key AKIA…が漏れた`, `见www.example.com`, `ב10.0.0.12`, `令牌eyJ…`, `id <uuid>を使った`, `主机2001:db8::1`). An ASCII letter or digit still counts as part of the word, so `xAKIA…` and `v10.0.0.12` read as before.
    - **G2, a URL-encoded link:** a scheme followed by `%3A%2F%2F` (any case) is a link like `://` (`next=https%3A%2F%2Fjira.corp.net%2F…`).
    - **G3, an escaped `@` without a dot in the domain:** a backslash right before the `@` counts like no markup (`me\@localhost`), unless a path goes on after the name with `\` or `/`, which makes it a Windows path with a scoped package (`node_modules\@types\node`, `src\@angular\core` pass, as in 0.1.1; found in review). No other markup is added to the dotless rule, and spaces around the `@` stay a kept gap.
    - **Card numbers keep every 0.1.1 catch:** a card is looked for with both the ASCII edges and 0.1.1's word edges, and refused if either finds a valid number, so a stray digit group next to a letter of another script cannot join the card and hide it (`card 4111 1111 1111 1111 2次`, `第1 4111 1111 1111 1111`; found in review).
    - **JWT with `。`:** the token rule reads `。` as a dot inside a JWT wherever it sits, so a signature starting with `-` or `_`, or none, no longer hides it (`eyJ…。eyJ…。_Qx9`, `eyJ…。eyJ…。`).
    - **Link ends found in round 7:** after `?` or `#`, also `$`, `!/` and `:~:` start a query or anchor (`api.corp.net?$top=5`, `app.corp.io#!/users/1`, `docs.corp.io#:~:text=x`). A bare `:` does not, so Kotlin's `foo.bar?:x` passes.
    - **Full-width `？` trade-off of 0.1.1, removed:** the character after `?` or `#` must be ASCII, so `为什么用foo.bar？因为快`, `foo.bar?为什么` and `한국어 foo.bar?그래서` pass again. New kept gap: a query or anchor that starts with a non-ASCII character right after a host with no path (`wiki.corp.io#Раздел`); a link copied from a browser has a `/` before it and is still refused.
    - **Dropped from the list:** `foo.@bar` is already refused in 0.1.1 (the round-5 note was wrong).
    - **Still kept (not in R7):** a leak disguised twice (2^n views), the R5 kept gaps, and the R5 trade-offs other than the full-width `？`; `see example。中国/x` stays with R5's `。` trade-offs, and `wiki.corp.io#Раздел` stays a kept gap rather than excluding only CJK after `?` and `#`, which would refuse `Почему foo.bar?Потому` (decided after review).
    - **For the next release (found in review, kept by the stopping rule):** two backslashes before a dotless `@` (`me\\@localhost`); a card with a stray digit group and only ASCII around it (`x 1 4111 1111 1111 1111`, also missed by 0.1.1); `foo.bar?İstanbul` refused because `İ` folds to ASCII (also in 0.1.1); tests that pin the ASCII side of `WORD_END` and an ASCII letter before `eyJ`.
    - **Bar for 0.1.2:** nothing 0.1.1 refuses passes, and nothing 0.1.1 allows is refused, except what R7 names; checked by tests and by one review round under the stopping rule.

## Development workflow (every request)

Every request to change this repo, from a typo to a new harness, goes through the [agent-skills](https://github.com/addyosmani/agent-skills) lifecycle by Addy Osmani. Each phase is scaled to the change (a one-line fix has a one-line spec and a one-task plan) but none is skipped, and each ends at a human gate: the maintainer approves before the next phase starts.

```
  DEFINE          PLAN           BUILD          VERIFY         REVIEW          SHIP
 ┌──────┐      ┌──────┐      ┌──────┐      ┌──────┐      ┌──────┐      ┌──────┐
 │ Idea │ ───▶ │ Spec │ ───▶ │ Code │ ───▶ │ Test │ ───▶ │  QA  │ ───▶ │  Go  │
 │Refine│      │  PRD │      │ Impl │      │Debug │      │ Gate │      │ Live │
 └──────┘      └──────┘      └──────┘      └──────┘      └──────┘      └──────┘
  /spec          /plan          /build        /test         /review       /ship
```

| Phase | Skills | In this repo | Gate |
|---|---|---|---|
| **Define** (`/spec`) | `spec-driven-development`; `interview-me` or `idea-refine` when the ask is vague | Update this file first (objective, requirement, safety rule or success criterion), list assumptions and open questions. | Maintainer approves the spec change. |
| **Plan** (`/plan`) | `planning-and-task-breakdown` | `tasks/plan.md` and `tasks/todo.md`: small tasks in dependency order, each with acceptance criteria, a verify step and the files it touches. | Maintainer approves the plan. |
| **Build** (`/build`) | `incremental-implementation`, `test-driven-development`; `source-driven-development` when a harness behaviour is involved | One task at a time: failing test, code, `make check` green, one Conventional Commit per task. Docs and `CHANGELOG.md` move with the behaviour. | Each task green before the next. |
| **Verify** (`/test`) | `test-driven-development`, `debugging-and-error-recovery` | `make check` on the whole change; for a harness fact, a live run recorded in rules spec section 13. A failure is debugged to its root cause, never skipped. | All checks green, evidence shown. |
| **Review** (`/review`) | `code-review-and-quality` (five axes), `security-and-hardening` for paths, files and the miss log | Delegated per this repo's own delegation block: the `reviewer` subagent for the change, `auditor` for anything touching safety rules S1–S9. Findings fixed or answered. **Stopping rule:** review rounds end when a round leaves no open Critical or Required finding in its scope. Optional findings, Nits, and gaps the previous release also had are recorded for the next release instead of starting another round. A fix for a Critical or Required finding gets one more round, scoped to that fix. Doc-only edits after the last round get a `reviewer` check of the doc diff only. (Added after seven rounds on 0.1.1, where every fix of an Optional finding reshaped the filter and the next round found what the reshaping broke.) | No open Critical or Required finding. |
| **Ship** (`/ship`) | `shipping-and-launch`, `git-workflow-and-versioning` | No deployment: version (`pyproject.toml` and the README install block, kept equal by a test) and `CHANGELOG.md` updated, release archive contents checked (R1), commits ready. For every release the agent dates the `CHANGELOG.md` section, checks the archive of the release commit, and drafts the release notes in `tasks/release-<version>.md` (for users: what changed and how to update, condensed from `CHANGELOG.md`), which `reviewer` checks against the code. When the maintainer asks, the agent also creates the annotated tag locally. The maintainer pushes commits and tags and publishes the GitHub release from the host; agents never push from the sandbox. | Maintainer's go. |

## Tech Stack

- Python 3.11+ standard library only at run time (`tomllib`, `argparse`, `dataclasses`, `pathlib`). No third-party runtime dependency, no YAML library: role frontmatter is parsed by a strict line parser.
- `bash` entry points (`install`, `bin/miss-log`) that check the Python version and run `python3 -B lib/<module>.py`.
- Development only: `uv`, `pytest` (pinned in `uv.lock`), `ruff`, `pyright`, `shellcheck`, `gitleaks`; the agent-skills plugin for the workflow.

## Commands

```sh
uv sync                       # dev environment (.venv, from uv.lock)
make check                    # lint, typecheck, secrets, tests, self-install drift (R2); the pre-commit hook
make lint                     # ruff check, ruff format --check, shellcheck
make typecheck                # pyright in the project environment
make secrets                  # gitleaks: history, then staged changes
make test                     # uv run pytest
uv run pytest tests/test_install.py -k claude_md   # one area
make fmt                      # ruff format + ruff check --fix
make hooks                    # once per clone: use .githooks/pre-commit
make self                     # ./install --project . : re-install routewise on this repo (R2)
                              # never a bare ./install here: its default project is the folder above
git archive --format=tar HEAD | tar -t   # what a release archive ships (R1)
```

Tool commands, run from a project that holds `routewise/`:

```sh
routewise/install                 # set up or update
routewise/install --check         # exit 1 on drift, write nothing
routewise/install --uninstall
routewise/install --project PATH  # PATH must hold this routewise/ folder, or be it
routewise/bin/miss-log add --mode dev --role reviewer --task review --what "missed a None check"
routewise/bin/miss-log report
```

Exit codes for both tools: `0` done (or no drift), `1` drift (`--check` only), `2` a clear error on stderr with nothing written.

## Project Structure

```
Runtime (shipped in the release archive):
install, bin/miss-log  → bash entry points (version check, then python3 -B)
lib/install.py         → plan and apply an install, check or uninstall
lib/block.py           → the marker-delimited block inside an instruction file
lib/roles.py           → parse neutral roles, render per-harness agent files
lib/settings.py        → parse and validate routewise.toml
lib/paths.py           → every path stays inside the project
lib/files.py           → preflight, atomic replace, safe remove and append
lib/miss_log.py        → miss-log add and report
lib/privacy.py         → what a miss-log entry must not contain
roles/*.md             → the five neutral roles (explore, log-reader, web-reader, reviewer, auditor)
harness.toml           → per-harness folder, tier → model, efforts, tool names
templates/             → routewise.toml, ROUTING-BINDING.md, the two delegation fragments
spec/                  → the rules spec, shipped to projects unchanged
README.md, ADOPT.md, LICENSE, CHANGELOG.md

Development only (export-ignore):
SPEC.md, AGENTS.md     → this spec; agent instructions (with routewise's own delegation block)
tasks/                 → plan.md and todo.md of the current change
tests/                 → pytest; conftest.py builds a throwaway project per test
Makefile, pyproject.toml, uv.lock, pyrightconfig.json, .githooks/, .gitignore, .gitattributes
routewise.toml, ROUTING-BINDING.md, .claude/agents/, logs/   → routewise installed on itself (R2)
```

## Code Style

Short modules, one job each, plain functions over classes, a docstring that says what and why in one or two sentences. Errors are one exception type per module, caught once in `main` and printed as `routewise: <message>` with exit code 2. Paths go through `paths.inside` before any write.

```python
def plan_block(plan: Plan, path: Path, body: str | None, linked: bool) -> None:
    """Put `body` in the file's routewise block, or remove the block when `body` is None."""
    old = read_exact(path)
    try:
        new = block.insert(old, body) if body is not None else block.remove(old)
    except block.BlockError as err:
        raise Fail(f"{label(path, plan.root)}: {err}") from err
    if new == old:
        return
    ...
```

- Ruff, line length 100, rules `E F I UP B` plus complexity limits (McCabe 10, 12 branches, 50 statements, 6 arguments). Pyright `standard`, zero warnings.
- Messages and docs: plain British English, short sentences, name the file and the fix (`AGENTS.md: needs exactly one routewise:start line ...; fix the markers by hand`).
- Imports: `lib/` modules import each other by bare name (`import block`); `pyproject.toml` lists them as first-party.

## Testing Strategy

- `pytest` under `tests/`, one file per module (`test_block.py`, `test_roles.py`, `test_settings.py`, `test_privacy.py`, `test_miss_log.py`) plus `test_install.py` for end-to-end runs.
- End-to-end tests use the `project` fixture: a temporary project with a copy of `routewise/` inside, driven through the real `install` and `bin/miss-log` scripts as subprocesses. Assert on files, stdout, stderr and exit codes.
- Test-first for every behaviour change and bug fix. Each safety rule below has at least one test that fails if it is broken; each `claude_md` case is covered for install, `--check` and `--uninstall`.
- One version: a test checks that the README install block names the version in `pyproject.toml` (R4).
- One list of runtime files: a test checks that the files a release archive ships (tracked files without `export-ignore`) equal the runtime set that `conftest.py` copies into test projects (R1).
- Self-install (R2) is tested on a temporary copy, never by writing into this repo from a test.
- Harness behaviour (model aliases, the `Explore` override, the `@AGENTS.md` import) is not unit-testable: it is checked by live runs and recorded in rules spec section 13.
- No coverage percentage target; the bar is "every requirement in this spec has a test". Tests must not depend on files outside the temporary folder (no CLAUDE files above `/tmp`).

## Safety rules (each one tested)

- **S1 Inside the project.** Every write, delete and append stays inside the project root; paths in settings are relative with no `..`; a symlink that leads out is refused; paths are checked again right before each write.
- **S2 All or nothing.** The whole run is planned and every target checked for write access first; files are written to a temporary file and renamed. A failed run writes nothing.
- **S3 Only its own files.** Generated agents carry a `# generated by routewise from ...` marker; only such files are rewritten or deleted, and anything else in the way stops the run.
- **S4 Markers.** Markers count only as whole lines outside fenced code; anything but zero or one well-formed pair stops the run. Text outside the block keeps its bytes and line ends. A routewise folder name that would break a line routewise writes (a line break, a control character or `-->`) stops the run before anything is planned (found in review).
- **S5 No symlinks created.** Existing symlinked instruction files are edited through their target and never deleted.
- **S6 Read-only roles.** Role files may hold only `name`, `description`, `tools`, `tier`, `effort`; tools come from an allowlist of each harness's read, search, shell and web tools, never a write or edit tool (a shell can still change files; roles that have one are told to run only commands that read); a setting cannot inject frontmatter.
- **S7 Private miss log.** `miss-log` refuses clear leaks (addresses, also without a dot in the domain; URLs, also without a scheme; IPs, UUIDs, home paths, tokens, card numbers; R5) and never follows a symlinked log.
- **S8 Personal files.** `CLAUDE.local.md` and files above the project are never written.
- **S9 The project holds routewise.** The project root must hold the routewise folder directly or be it (R2); any other root is refused, so generated files never hold absolute paths. The home folder and every folder above it are never a project, even with routewise at `~/routewise`: agents and `CLAUDE.md` there are global. A routewise folder that is a symlink is never its own project, since its files belong to every project that links to it (both found in review).

## Boundaries

- **Always:** follow the development workflow above, phase by phase, with its gates; keep runtime code standard-library only; run `make check` before a commit; add a test with each change; add a `CHANGELOG.md` line for each user-visible change; keep `ADOPT.md`, `README.md` and the templates in step with behaviour; re-run `make self` after changing roles, templates or `harness.toml`; mark new development files `export-ignore`.
- **Ask first:** changing a rule or the version line in `spec/SPEC-model-routing.md`; adding a harness, a role or a setting; changing a default; adding any dependency (runtime or dev); changing the exit codes, the marker text or the generated-file marker (projects already depend on them); raising this repo's own parallel cap or tiers.
- **Never:** skip a workflow phase or its gate; let a role gain a write, edit, send or commit tool; write outside the project or through a symlink that leads out; delete a file routewise did not create; edit generated files (`.claude/agents/`, the delegation block) by hand; run a bare `./install` in this repo (it would write into the folder above); commit secrets; push from the sandbox.

## Success Criteria

1. `make check` passes on a clean clone after `uv sync`, including `./install --project . --check` on this repo.
2. On an empty project, `routewise/install` writes exactly `routewise.toml`, `ROUTING-BINDING.md`, the miss log, five files in `.claude/agents/` and `AGENTS.md`; a second run prints `routewise: nothing to change` and `--check` exits 0.
3. `--uninstall` after install leaves only the files the user owns plus `routewise.toml`, `ROUTING-BINDING.md` and the miss log; files the user had before are byte-identical to before.
4. Every safety rule S1–S9 has a named test that fails when the rule is removed.
5. `git archive HEAD` lists exactly the runtime files of R1, and a test fails if a tracked file is neither runtime nor `export-ignore`.
6. This repo's `AGENTS.md` holds routewise's own delegation block with `bin/miss-log` paths, and changing a role without re-running `make self` makes `make check` fail.
7. (R3) In a vendored install, the start marker, the agent marker and the binding name `routewise/install` and `routewise/…` paths; in a self-install they name `./install --project .` and paths without `routewise/`; no file written by the installer names a command that does not work from that project's root.
8. Live runs on the current Claude Code show the generated `Explore` on the `fast` model and `AGENTS.md` reached through each `claude_md` import, recorded in rules spec section 13.
9. (R4) The README's install block, run as written in an empty project, installs the version in `pyproject.toml`; a test fails if the two versions differ.
10. (R5) `tests/test_privacy.py` refuses each leak named in R5 (the five reported cases, the old tool's refused list, and the gaps found in review and audit) and fails on 0.1.0; it allows each code word R5 keeps passing, and pins each trade-off R5 refuses on purpose. Every phrase allowed before 0.1.1 is still allowed, except the trade-offs R5 names.
11. (R6) A test runs `bin/miss-log` into a refused entry and checks that stderr starts with `routewise: `; the file-error branch prints the same prefix.
12. (R7) `tests/test_privacy.py` refuses each leak named in R7 and those cases fail on 0.1.1; the full-width `？` phrases are allowed and fail on 0.1.1; every other case of 0.1.1's tests keeps its result.

## Decisions (from the open questions of draft 1)

1. **Development files in host projects:** release archive with `export-ignore` (R1), one tested list of runtime files, README recommends the archive, `AGENTS.md` keeps its guard for submodule users. A separate release branch (`git subtree split`) is not needed now.
2. **Dogfooding:** yes (R2), kept current by `./install --project . --check` in `make check`. Found while planning: a bare `./install` here would target the folder above the repo, so self-install always passes `--project .` (`make self`).
3. **Live check of the `@AGENTS.md` bridge:** done 2026-11-14 on Claude Code 2.1.325, five probes, each with a different parallel cap that the session had to quote: no CLAUDE files → `4` (native read); plain `CLAUDE.md` → `NONE` (it hides `AGENTS.md`); `CLAUDE.md` with the routewise import block → `7`; `.claude/CLAUDE.md` with `@../AGENTS.md` → `8`; `.claude/CLAUDE.md` with a plain `@AGENTS.md` → `NONE` (imports resolve from the importing file's folder). To be recorded in rules spec section 13 during Build.

4. **`tasks/` in git:** `tasks/plan.md` and `tasks/todo.md` are committed with each change, as a record of how it was planned, and marked `export-ignore` so they never ship.
5. **Marker text (R3):** the maintainer asked on 2026-11-14 for the command in the start marker and the agent marker to follow the project (an "Ask first" change, approved by that request). Only the command at the end changes; the parts used for detection stay fixed.

## Open Questions

None.
