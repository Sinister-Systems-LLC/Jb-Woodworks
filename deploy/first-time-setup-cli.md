<!-- Author: RKOJ-ELENO :: 2026-05-25 -->
# Sinister Sanctum — first-time setup CLI

One-command fresh-PC installer. Self-elevates via UAC (one click on the standard
Windows consent prompt). No `.bat` / `.ps1` files are produced; everything runs
through `python deploy/first_time_setup.py`.

Operator hard-canonical 2026-05-25: the installer never asks you to "run elevated",
"add a Defender exclusion", or "click anything in an admin console". The only
prompt you should ever see is the standard Windows UAC dialog and (later) a
browser OAuth window for Claude.

## Usage

```text
python deploy/first_time_setup.py            # full install
python deploy/first_time_setup.py --dry-run  # show what would happen, change nothing
python deploy/first_time_setup.py --no-elevate  # stay non-admin (some steps degrade)
python deploy/first_time_setup.py --no-clone --no-launch
python deploy/first_time_setup.py --target "D:\Sinister Sanctum"
```

`deploy/setup.py` is a thin wrapper that just calls `first_time_setup.main()` so
operators can type whichever entry-point they remember.

## What each step does

| # | Step | What it does | Failure mode |
|---|---|---|---|
| 1 | `is_admin` / self-elevate | Checks `IsUserAnAdmin`. If not admin and `--no-elevate` is absent, re-launches itself via `ShellExecuteW(verb="runas")` → standard UAC prompt → exits the non-elevated copy. | Logs WARN, continues; admin-only sub-steps will degrade. |
| 2 | `detect_repo` | Walks up from CWD looking for `_shared-memory/` + `CLAUDE.md` + `automations/`. If absent and `--no-clone` is absent, clones `Sinister-Systems-LLC/Sinister-Sanctum` to `--target` (default `D:\Sinister Sanctum\`). | Stops cleanly with FAIL log; exits 0. |
| 3 | `ensure_python_deps` | `import` each of `requests`, `cryptography`, `psutil`, `watchdog`; pip-installs anything missing. | Individual pkgs log `install-fail rc=N`; rest proceeds. |
| 4 | `ensure_winget_deps` | Checks then `winget install --silent` for `Git.Git`, `Microsoft.PowerShell`, `Anthropic.Claude.Code` (the last is OK to be missing from the catalog — it logs `install-skipped`). | Logs `_winget: not-available; skipped` if winget itself is absent. |
| 5 | `install_schtasks` | Creates three scheduled tasks via `schtasks /Create /F`: `SinisterSanctumAutoPush` (30 min), `SinisterLoopRelentlessWatchdog` (5 min), `SinisterLinkPoller` (5 min). Idempotent (`/F` forces overwrite). Runs as `SYSTEM` when elevated, current user otherwise. | Individual tasks log `fail rc=N`; rest proceeds. |
| 6 | `ensure_claude_config` | Seeds `~/.claude/settings.json` with the canonical-protection block (`bypassPermissions=true`, `defaultMode="bypassPermissions"`, `enabledPlugins["understand-anything@understand-anything"]=true`). If `~/.claude/.credentials.json` is missing, logs a `USER-OAUTH-REQUIRED` row — the operator OAuths via EVE.exe (allowed user-class action per doctrine). | Merge failures log and continue. |
| 7 | `copy_eve_exe_to_userprofile` | Mirrors `<repo>\EVE.exe` to `%USERPROFILE%\.eve\EVE.exe` and drops `EVE.lnk` on the Desktop (via `win32com` if present, else PowerShell COM one-liner — no `.ps1` written). | Logs `copy-fail` / `shortcut-fail` and continues. |
| 8 | `first_launch_eve` | `subprocess.Popen` of `<repo>\EVE.exe` with `DETACHED_PROCESS`; polls PID for 5 s; logs `spawned pid=N` or `died rc=N`. Skip via `--no-launch`. | Logs `spawn-fail`; rest proceeds. |
| 9 | summary | Prints PASS/FAIL/WARN/SKIP table and exits 0. | (always 0 if the installer itself ran) |

## Logs

Every step appends a JSON row to:

```
<repo>\_shared-memory\first-time-setup-log.jsonl
```

Rows look like:

```json
{"ts": "2026-05-25T05:14:00Z", "step": "5_schtasks", "status": "PASS",
 "results": {"SinisterSanctumAutoPush": "created", ...}}
```

## Re-running

The installer is **idempotent** — re-running is the supported recovery path.

- `pip install` is skipped for already-importable packages.
- `winget install` is skipped for `already-present` IDs.
- `schtasks /Create /F` overwrites existing tasks (no need to delete first).
- `~/.claude/settings.json` is merged, not overwritten — operator edits survive,
  but the three canonical-protection keys are re-asserted.
- `EVE.exe` mirror uses `shutil.copy2` (overwrites timestamp + content).

To force a clean install of just one step, delete the relevant artifact and re-run:

| To redo... | Delete... |
|---|---|
| schtasks | `schtasks /Delete /TN SinisterSanctumAutoPush /F` (and the other two) |
| Claude settings | `~/.claude/settings.json` |
| EVE mirror | `%USERPROFILE%\.eve\EVE.exe` |
| Repo (full reset) | the clone directory |

## `--no-elevate` semantics

With `--no-elevate`, the installer skips the UAC self-launch and runs in your
current user context. Consequences:

- `schtasks /RU SYSTEM` falls back to `/RU <current user>` — tasks still install,
  they just run as you instead of SYSTEM.
- All other steps work identically (pip / winget / user-scope writes are all
  non-admin).

Use this when running inside CI, a constrained shell, or any environment where
the UAC prompt would block forever.

## Exit codes

The installer always returns `0` once it has started running (per spec — it
reports per-step PASS/FAIL in the summary instead of failing the process). The
authoritative status is the JSONL log + stdout summary.

## Doctrine references

- `_shared-memory/knowledge/automate-everything-no-operator-admin-2026-05-25.md`
- `_shared-memory/knowledge/no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25.md`
- `_shared-memory/knowledge/do-not-revert-operator-canonical-protections-2026-05-23.md`
- `_shared-memory/knowledge/sanctioned-bypasses-doctrine-2026-05-21.md`
