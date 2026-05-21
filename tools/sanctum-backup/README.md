# sanctum-backup

> **Author:** RKOJ-ELENO :: 2026-05-21
> **License:** AGPL-3.0-or-later
> **Pattern:** sinister-cli subcommand (see `_shared-memory/knowledge/sinister-cli-subcommand-pattern.md`)

Recurring Sinister Sanctum backups. Daily robocopy snapshots of `D:/Sinister Sanctum/` to `D:/sinister-sanctum-backups/<YYYY-MM-DD>/`, with 7-day retention and a per-backup `_BACKUP-MANIFEST.md`.

## Install

```bash
pip install -e "D:/Sinister Sanctum/tools/sanctum-backup"
```

After install, three callable surfaces exist:

- direct shim: `sanctum-backup <subcommand>` (entry-point in pyproject)
- module:     `python -m sanctum_backup <subcommand>`
- umbrella:   `sinister sanctum-backup <subcommand>` (via `tools/sinister-cli/`)
- RKOJ.exe:   `RKOJ.exe sanctum-backup <subcommand>` once the spec hidden-imports `sanctum_backup`

## Subcommands

| Command | Purpose |
|---|---|
| `now` | Run a backup right now (or `--dry-run` for a no-op trace). |
| `list` | List existing snapshot dirs with size + file count + manifest presence. |
| `verify <date>` | Re-check a snapshot's manifest + on-disk state. |
| `prune` | Delete backups older than `--keep N` (default 7). |
| `install-task` | Register the daily Windows scheduled task (default 03:00 local). |
| `excludes` | Print the default exclude lists. |

All subcommands accept `--help` and most accept `--json` for machine-readable output.

## Environment variables

| Var | Default | Meaning |
|---|---|---|
| `SANCTUM_ROOT` | `D:/Sinister Sanctum` | Source path being backed up. |
| `SANCTUM_BACKUP_ROOT` | `D:/sinister-sanctum-backups` | Destination root. |

## Excludes

Directories (`/XD`):

```
.swarm, .claude/worktrees, __pycache__, build, dist, node_modules,
.pytest_cache, .venv, venv, .mypy_cache, .ruff_cache
```

Files (`/XF`):

```
*.pyc, *.pyo
```

Junctions are skipped via `/XJ` (Sanctum's `projects/*/source/` are junctions to external repos).

## Robocopy exit-code semantics

Codes 0..7 = success (combinations of "copied / extra / mismatch"); codes ≥ 8 = at least one failure.

## Manifest

Each snapshot directory contains `_BACKUP-MANIFEST.md` with:

- Date + branch + HEAD subject
- Source path, size, file count
- Destination path, size, file count
- Exclude lists
- Robocopy argv + exit code
- Any errors

## Scheduling — operator-gated

The scheduled task is **never** auto-installed. The operator runs:

```powershell
sanctum-backup install-task                       # default: 03:00 daily
sanctum-backup install-task --time 02:30          # custom time
sanctum-backup install-task --task-name MyBackup  # custom Task name
sanctum-backup install-task --dry-run             # show invocation, install nothing
```

The helper `install-task.ps1` registers / replaces a Windows scheduled task that calls `sanctum-backup now` daily.

## Tests

```bash
pytest tools/sanctum-backup/tests/ -v
```

All tests mock robocopy (no real backup is performed during CI / install).
