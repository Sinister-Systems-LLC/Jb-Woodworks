# sinister-diagnose

> **Author:** RKOJ-ELENO :: 2026-05-21
> **License:** AGPL-3.0-or-later
> **Status:** v0.1.0 — first cut

RKOJ / Sanctum health checker. Like `npm doctor` or `brew doctor`. Runs ~14
read-only environment probes and prints a colored report (or JSON for
scripting).

## Install

```bash
pip install -e "D:/Sinister Sanctum/tools/sinister-diagnose"
```

After install you can call it three ways:

```bash
sinister-diagnose                    # full health check, colored report
sinister-diagnose run --json         # JSON for scripting
sinister-diagnose check python       # one check only
sinister-diagnose list               # enumerate every slug
sinister diagnose                    # via the umbrella dispatcher
```

## What it checks

| slug           | what                                                       | severity  |
|----------------|------------------------------------------------------------|-----------|
| `python`       | Python >= 3.11                                             | fail < 3.11 |
| `pyinstaller`  | PyInstaller importable + version                           | fail      |
| `anthropic`    | `anthropic` SDK importable + `ANTHROPIC_API_KEY` set       | fail/warn |
| `claude-cli`   | `claude.exe` on PATH or under `~/.local/bin/`              | fail      |
| `rust`         | `rustc --version` succeeds                                 | warn      |
| `sanctum-root` | `D:\Sinister Sanctum\` exists + has `CLAUDE.md`            | fail      |
| `backups`      | `D:\Backups\` exists, has `MANIFEST.md`, recent dated dir  | fail/warn |
| `vault`        | TCP probe on `localhost:5078`                              | info      |
| `mcp`          | `~/.claude/.mcp.json` exists + parses                      | fail/warn |
| `git-config`   | `user.name` + `user.email` both set                        | fail/warn |
| `disk`         | `D:\` has >= 50 GB free (warn < 50, fail < 10)             | fail/warn |
| `rkoj-exe`     | Desktop `RKOJ.exe` mtime within 7 days                     | warn      |
| `branch`       | current branch is `agent/sinister-sanctum/cli-dispatcher-*`| warn      |
| `heartbeats`   | every `_shared-memory/heartbeats/*.json` < 24h             | warn      |

## Output

Default report (colored via `rich`):

```
[ok]   Python version  3.12.10
[ok]   PyInstaller     6.20.0
[warn] Anthropic SDK   installed 0.30.0 but ANTHROPIC_API_KEY not set
                       fix: set the env var (see docs/ENV-VARIABLES.md)
[fail] Rust toolchain  not found
                       fix: install rustup-init.exe from rustup.rs
...
summary: WARN  (10 ok, 3 warn, 1 fail, 1 info)
```

JSON (`--json`):

```json
{
  "tool": "sinister-diagnose",
  "version": "0.1.0",
  "generated_at": "2026-05-21T14:00:00Z",
  "overall": "warn",
  "checks": [
    {
      "name": "Python version",
      "status": "ok",
      "message": "3.12.10",
      "fix_hint": ""
    }
  ]
}
```

Exit codes:
- `0` everything ok (or `info` only)
- `1` at least one warn (none fail)
- `2` at least one fail (or unknown slug)

Pass `--strict` to make warn exit `2` as well.

## Env overrides

For testability (and for non-Sanctum environments), every host-path constant
is overridable via env var:

| env                  | default                  | used by                        |
|----------------------|--------------------------|--------------------------------|
| `SANCTUM_ROOT`       | `D:\Sinister Sanctum`    | `sanctum-root`, `heartbeats`   |
| `SANCTUM_BACKUPS`    | `D:\Backups`             | `backups`                      |
| `SANCTUM_DRIVE`      | `D:\`                    | `disk`                         |
| `ANTHROPIC_API_KEY`  | (unset)                  | `anthropic`                    |
| `USERPROFILE`        | system-set               | `rkoj-exe`                     |

## Design constraints

- Stdlib + `click` + `rich` + (optional) `psutil` only.
- Every check is a pure function returning a 4-key dict (`name`, `status`,
  `message`, `fix_hint`). No globals, no side effects.
- subprocess calls always have `timeout=5` to avoid hanging on broken
  toolchains.
- Network probes are TCP-only and short (400 ms) — `vault` is info-only.
- The full report runs in well under 1 second on a healthy workstation.

## Tests

```bash
cd "D:/Sinister Sanctum/tools/sinister-diagnose"
python -m unittest discover -s tests -v
```

Pytest also works (the test files use stdlib `unittest`, which pytest collects
natively):

```bash
pytest tests -v
```

## Composes with

- `tools/sinister-cli/sinister_cli/__main__.py` — adds the `diagnose` row to
  `SUBCOMMAND_MAP`, so `sinister diagnose ...` works.
- `automations/build/forge-exe/RKOJ.spec` — adds `sinister_diagnose` to
  PyInstaller hiddenimports + pathex so the RKOJ.exe bundle ships the
  checker alongside the rest of the umbrella tools.
- `_shared-memory/knowledge/sinister-cli-subcommand-pattern.md` — the canonical
  5-file pattern this tool follows.
