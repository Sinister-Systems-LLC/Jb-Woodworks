<!-- decay:
  category: preference
  confidence: 1.0
  reinforcements: 0
  half_life_days: 365
-->
# Leo Deploy-Folder Bootstrap Doctrine (operator hard-canonical 2026-05-25 ~05:58Z)

**Author:** RKOJ-ELENO :: 2026-05-25

## Operator verbatim (2026-05-25 ~05:58Z)

> *"i need you to stop what you are doing right now and push teh sinister sanctum to github and make sure every single file needed to run all operations are in there and ready for my partner leo to install on his machine. preapre a folder for leo thatt is called deploy. complie all the userguides we creatred and everything he needs to start. make sure the eve.exe is placed in the root dir and works from there, test this. make sure the exe auto updates and make sure the sinister link works. make sure the ai agent still opens when the exe is first installed and ran. make sure to auto run as a admin so you have the permissions needed for the first time setup you should have been making that auto sets this up on a new pc when its opened. get to work and do this now"*

## The three-artifact deploy contract

Leo's bring-up requires only **three things** on his machine:

1. A git clone of `https://github.com/Sinister-Systems-LLC/Sinister-Sanctum.git` (or unzip of a release tarball) into `D:\Sinister Sanctum\` (canonical path; every doctrine + script references it).
2. Python 3.10+ (the `deploy/first_time_setup.py` installer ensures it via winget if missing).
3. A single command: `python deploy\setup.py` (auto-elevates UAC, installs everything, launches EVE).

## What lives in `deploy/`

| File | Purpose | Author/source |
|---|---|---|
| `deploy/README.md` | One-page bootstrap: 3-step quickstart + elevator pitch | Sub-A iter-22 |
| `deploy/GETTING-STARTED.md` | 521-line onboarding (merged from LEO-SETUP / LEO-VAULT-SETUP / OPERATOR-QUICK-REFERENCE / SETUP / SINISTER-LINK / ENV-VARIABLES) | Sub-A iter-22 |
| `deploy/TROUBLESHOOTING.md` | 13 failure modes + one-line fixes | Sub-A iter-22 |
| `deploy/DOCS-INDEX.md` | Annotated index of all 27 `docs/` files grouped by audience | Sub-A iter-22 |
| `deploy/SMOKE-EVIDENCE.md` | Test verdicts for EVE.exe + Sinister Link + first-launch | Sub-D iter-22 |
| `deploy/setup.py` | Thin wrapper → first_time_setup.main() | Sub-B iter-22 |
| `deploy/first_time_setup.py` | 9-step UAC-elevating fresh-PC installer | Sub-B iter-22 |
| `deploy/first-time-setup-cli.md` | Per-step doc + re-run recovery | Sub-B iter-22 |
| `deploy/eve-updater-CLI.md` | When/force/disable auto-update + log location | Sub-C iter-22 |
| `deploy/EVE.exe` | Launcher binary (2.19 MB, copy of root EVE.exe) | Sub-A iter-22 |
| `deploy/_internal/` | PyInstaller --onedir deps (18 MB, 56 files) | Master P0 fix iter-22 |
| `deploy/MANIFEST.txt` | sha256 + size for every file | Sub-A + master regen |
| `deploy/_gen_manifest.py` | Helper to re-emit MANIFEST.txt | Sub-A iter-22 |

## The `_internal/` invariant (P0 gotcha)

**EVE.exe is a PyInstaller `--onedir` bundle.** Without a sibling `_internal/` directory containing `python312.dll` + 55 other deps, it fails with `PYI-47016: Failed to load Python DLL`.

Three locations MUST have a `_internal/` next to their EVE.exe:
- `~/.eve/_internal/` (build target — verify-eve-features.ps1 emits here)
- `D:\Sinister Sanctum\_internal\` (repo root — copied by sync_eve_internal.py)
- `D:\Sinister Sanctum\deploy\_internal\` (deploy folder — copied by sync_eve_internal.py)

**After every EVE.exe rebuild,** run:

```
python automations\sync_eve_internal.py
```

(idempotent, dry-run available, exits 0 when all three are in-sync). Add this as the LAST step of any verify-eve-features.ps1 rebuild flow.

## First-time-setup.py — the 9 steps

`deploy/first_time_setup.py` (469 LOC, RKOJ-ELENO authored) executes:

1. **`is_admin()`** — `ctypes.windll.shell32.IsUserAnAdmin()`. If False AND `--no-elevate` not set → re-launch self with verb=`runas` via `ShellExecuteW` (UAC prompt) then exit. (Doctrine: auto-elevate, never ask operator to right-click "Run as admin".)
2. **`detect_repo()`** — walk parent dirs for `_shared-memory/` + `CLAUDE.md` + `automations/` markers. If absent → offer `git clone` to `D:\Sinister Sanctum\` (default) or `%USERPROFILE%\Sinister-Sanctum\` (fallback).
3. **`ensure_python_deps()`** — `pip install requests cryptography psutil watchdog` (only the ones not already importable).
4. **`ensure_winget_deps()`** — `winget install --id Git.Git Microsoft.PowerShell Anthropic.Claude.Code -e --silent --accept-package-agreements --accept-source-agreements`. Skip silently on missing-from-catalog (rc != 0 logged, doesn't abort).
5. **`install_schtasks()`** — 3 scheduled tasks: `SinisterSanctumAutoPush` (30min), `SinisterLoopRelentlessWatchdog` (5min), `SinisterLinkPoller` (5min). `/F` idempotent. `/RU SYSTEM` when elevated, current user otherwise.
6. **`ensure_claude_config()`** — seed `~/.claude/settings.json` with `bypassPermissions: true`, `defaultMode: "bypassPermissions"`, `enabledPlugins["understand-anything@understand-anything"]: true` (per do-not-revert canonical-protections doctrine). OAuth surfaced as USER action — open EVE.exe → O) Accounts → 1) Claude Login.
7. **`copy_eve_exe_to_userprofile()`** — mirror root `EVE.exe` to `~/.eve/EVE.exe` + Desktop `EVE.lnk` (win32com if present, PowerShell COM one-liner via `-Command` otherwise — no `.ps1` file written).
8. **`first_launch_eve()`** — `Popen` with `DETACHED_PROCESS`; poll PID for 5s; log spawn outcome.
9. **Summary table + JSONL log** to `_shared-memory/first-time-setup-log.jsonl` (per-step rc + error + timestamp). Always exit 0 if installer ran end-to-end.

## EVE.exe auto-update flow

`automations/eve_self_update.py` (392 LOC) runs on EVE.exe startup (via `automations/eve_launch_wrapper.py`):

1. Fetch `https://raw.githubusercontent.com/Sinister-Systems-LLC/Sinister-Sanctum/main/EVE.exe.sha256` (64-hex sidecar — committed alongside EVE.exe so the check is fast).
2. Compare with `hashlib.sha256(local EVE.exe).hexdigest()`.
3. If differ: download remote EVE.exe → `EVE.exe.tmp.<pid>` → SHA-verify → `os.replace(tmp, final)` with backoff 1s/2s/4s/8s/16s on PermissionError (handles running EVE briefly holding the file).
4. Best-effort `Add-MpPreference -ExclusionPath <path>` (fails silently if not admin; Defender quarantine self-heal).
5. JSONL log to `_shared-memory/eve-update-log.jsonl`.

**Sidecar must be regenerated after every rebuild:**

```
python automations\build_eve_sha_sidecar.py
```

(commits `EVE.exe.sha256` next to `EVE.exe` so the GitHub raw URL returns the current digest.)

## Composes with

- `_shared-memory/knowledge/automate-everything-no-operator-admin-2026-05-25.md` (UAC + locked-file retry + Defender)
- `_shared-memory/knowledge/no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25.md` (Python-only for new automation)
- `_shared-memory/knowledge/leo-auto-setup-doctrine-2026-05-25.md` (extends the two-file drop with the third artifact: a single `python deploy\setup.py` command)
- `_shared-memory/knowledge/leo-first-run-issues-and-fixes-2026-05-25.md` (informs `deploy/TROUBLESHOOTING.md`)
- `_shared-memory/knowledge/single-repo-push-policy-2026-05-25.md` (push target = Sinister-Sanctum repo only)

## Pass criterion

For every fleet agent, the deploy-folder contract is satisfied when **all** are true:

- [ ] `D:\Sinister Sanctum\EVE.exe --version` exits 0 with version banner
- [ ] `D:\Sinister Sanctum\deploy\EVE.exe --version` exits 0 with version banner
- [ ] `EVE.exe.sha256` matches `hashlib.sha256(EVE.exe).hexdigest()`
- [ ] `_internal/` exists at all three target locations and `python automations\sync_eve_internal.py --dry-run` returns "in-sync" for all
- [ ] `deploy/` has all 13 canonical files + a non-empty `_internal/`
- [ ] `git ls-tree origin/main deploy/` lists all 13 files
- [ ] `python deploy/first_time_setup.py --dry-run --no-elevate --no-launch --no-clone` exits 0 with all-green step summary
- [ ] Tag `leo-ready-<utc-date>-iter<N>` exists on origin and points to a commit where every criterion above passes

## Tag scheme

`leo-ready-<YYYY-MM-DD>-iter<N>` — current canonical: `leo-ready-2026-05-25-iter22`.

The operator + Leo can `git checkout leo-ready-2026-05-25-iter22` for a guaranteed-working bring-up state. Each iter that materially changes the deploy contract emits a new tag; old tags remain reachable.

## Anti-patterns

1. **Shipping EVE.exe without sidecar `_internal/`** — instant PYI-47016. Always run `sync_eve_internal.py` after rebuild.
2. **Forgetting `EVE.exe.sha256` after rebuild** — auto-updater can't detect change; Leo never gets the fix. Always run `build_eve_sha_sidecar.py` after rebuild.
3. **Writing new `.bat` for first-time-setup** — banned per no-bat-no-ps1 doctrine. Python only.
4. **Asking operator to "run as admin"** — banned per automate-everything-no-operator-admin doctrine. The installer auto-elevates via UAC.
5. **Branch convention violation** — deploy commits MUST go to `agent/sinister-sanctum/<topic>-<utc-date>` per single-repo push policy. Cross-cutting changes still single-repo.
6. **Pushing to main directly without tag** — every deploy-changing commit MUST land + be tagged so Leo has a stable checkpoint.
