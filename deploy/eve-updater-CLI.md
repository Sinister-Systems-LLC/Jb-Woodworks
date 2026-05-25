# EVE.exe Auto-Updater — Operator Quick Reference

> Author: RKOJ-ELENO :: 2026-05-25
> Doctrine: `_shared-memory/knowledge/automate-everything-no-operator-admin-2026-05-25.md`
> Doctrine: `_shared-memory/knowledge/no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25.md`

EVE.exe self-updates from GitHub raw so Leo and every operator workstation
stays current without manual rebuilds. The updater requires zero operator
clicks and never asks for admin elevation — per the canonical 2026-05-25
"automate everything" + "no operator admin actions" doctrines.

## Components

| File | Purpose |
|---|---|
| `automations/eve_self_update.py` | Compares local vs remote SHA, downloads, verifies, atomically swaps. |
| `automations/build_eve_sha_sidecar.py` | Regenerates `EVE.exe.sha256` after every EVE.exe build. |
| `automations/eve_launch_wrapper.py` | Recommended launcher — runs update (10s cap, non-blocking) then EVE.exe. |
| `EVE.exe.sha256` (repo root) | Published 64-hex sidecar that drives the update decision. |
| `_shared-memory/eve-update-log.jsonl` | Append-only audit log of every check + action. |

## When it runs

- **Automatic:** whenever EVE.exe is launched via `eve_launch_wrapper.py`.
  Update check is capped at 10 seconds; failure never blocks launch.
- **Manual:** `python automations/eve_self_update.py` any time.
- **CI / after-build:** `python automations/build_eve_sha_sidecar.py`
  regenerates the published sidecar. Commit the resulting
  `EVE.exe.sha256` alongside the new `EVE.exe`.

## How to force an update

```
python automations/eve_self_update.py --force
```

This bypasses the SHA-equality check and re-downloads + swaps even if local
and remote already match (useful to recover from corruption).

## How to dry-run (no writes)

```
python automations/eve_self_update.py --dry-run
```

Prints `in-sync`, `would-replace`, `would-install`, or `skipped (remote-unreachable)`.
Network-free environments report `remote-unreachable` and exit 0 — never crash.

## How to target a custom location

```
python automations/eve_self_update.py --path "C:\\Tools\\EVE.exe"
```

Repeatable; default targets are the repo root EVE.exe and `~/.eve/EVE.exe`.

## How to disable the auto-check on launch

```
python automations/eve_launch_wrapper.py --no-update
```

Or invoke `EVE.exe` directly — the wrapper is opt-in.

## Log location

Every check appends one JSON object per line to
`_shared-memory/eve-update-log.jsonl`. Schema:

| Field | Meaning |
|---|---|
| `ts_utc` | ISO-8601 UTC timestamp |
| `event` | `check_and_update`, `download_failed`, `atomic_swap_locked`, etc. |
| `path` | Local EVE.exe path |
| `local_sha_before` | SHA-256 before the check (null if absent) |
| `remote_sha` | SHA-256 reported by sidecar / full binary hash |
| `remote_source` | `sidecar` / `full-binary` / `unreachable` |
| `action` | `in-sync` / `replaced` / `would-replace` / `would-install` / `skipped` / `failed` |
| `reason` | Human-readable reason when `action=skipped` |
| `exit` | Process exit code contribution |
| `defender` | Result of best-effort `Add-MpPreference` (or `skipped-*`) |

## Locked-file handling (EVE.exe currently running)

`atomic_swap` retries `os.replace` up to 5 times with exponential backoff
(1 / 2 / 4 / 8 / 16 seconds). If still locked, the temp file is cleaned up
and the result is logged as `skipped: locked-eve-running` with exit 0 — the
next launch will pick up the update once EVE.exe is closed.

## Defender + Program Files notes

`defender_self_heal()` attempts `Add-MpPreference -ExclusionPath` against
the target. Non-admin invocations silently fail (returncode logged, not
fatal). For Program-Files-protected installs, future iterations may copy
to `%LOCALAPPDATA%\Sinister\EVE.exe` as a fallback path; currently the
recommended install dirs (`D:\Sinister Sanctum\` and `~/.eve/`) are
user-writable so this is not yet wired.

## Recommended invocation in launcher

The canonical entry point that supersedes any direct `EVE.exe` call:

```
python "D:\\Sinister Sanctum\\automations\\eve_launch_wrapper.py" [eve-args...]
```

`Start-Sinister-Session.bat` and the active `start-sinister-session.ps1`
remain the operator-facing trigger; whenever they touch the EVE.exe launch
path next, switch the call to the wrapper above (deferred — see report).
