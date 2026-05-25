# Sinister Sanctum — Troubleshooting

**Author:** RKOJ-ELENO :: 2026-05-25

Every known first-run + day-2 failure mode, root cause, and one-line fix.
Compiled from `docs/LEO-MISSING-SOURCES.md`,
`_shared-memory/knowledge/leo-first-run-issues-and-fixes-2026-05-25.md`,
and the LINK / Vault troubleshooting matrices.

If you hit something not in here, run
`automations\sinister-doctor.ps1 -Html` and attach the report to your
report to the operator.

---

## 1. EVE.exe won't open

### Symptom
Double-clicking `EVE.exe` does nothing, OR a window flashes and disappears.

### Causes + fixes

**(a) Defender quarantined it.** PyInstaller bundles trip first-launch heuristics.

```powershell
# Confirm quarantine:
Get-MpThreatDetection | Where-Object Resources -match 'EVE.exe'

# Self-heal: rebuild + auto-restore + add exclusion via the build script:
automations\eve-launcher\build-eve-exe.bat
```

The build script self-heals quarantine per the doctrine in
`_shared-memory/knowledge/automate-everything-no-operator-admin-2026-05-25.md`
(operator never clicks UAC).

**(b) Zero-byte / corrupt bundle.** Cold-cache extract sometimes leaves
EVE.exe in a half-state.

```powershell
# Force-kill any orphan:
taskkill /IM EVE.exe /F

# Rebuild:
automations\eve-launcher\build-eve-exe.bat
```

**(c) Stale build vs current eve.py.** The bat probes
`EVE.exe --version` with a 3 s timeout; if it fails the launcher falls
through to the PS1 picker (slower boot but identical menu).

To force a rebuild:

```powershell
powershell -File "D:\Sinister Sanctum\automations\verify-eve-features.ps1" `
    -AutoRebuild -SyncMirror
```

---

## 2. mintty exit 126 / "no spawn-capable shell found"

### Symptom
Picker spawns a window that closes immediately with `exit 126`, or the
launcher prints `[WARN] no spawn-capable shell found`.

### Root cause
Git for Windows is missing or installed to a non-default path. The bat
probes (lines 76-89 of `tools/session-launcher/Sinister Start.bat`):

```
C:\Program Files\Git\usr\bin\mintty.exe
C:\Program Files\Git\git-bash.exe
C:\Program Files\Git\bin\bash.exe
```

### Fix
Reinstall Git for Windows from <https://gitforwindows.org> to
`C:\Program Files\Git` (accept defaults). Reboot is NOT required; new
launcher invocations will probe-pass.

If you must install elsewhere (custom drive layout), symlink the expected
paths OR set `SINISTER_GIT_ROOT` (User scope) to point at your install.

---

## 3. Defender quarantine

### Symptom
- `EVE.exe` disappears mid-session.
- `Get-MpThreatDetection` lists EVE.exe / a PyInstaller bundle.
- A "Threat detected" toast pops in the system tray.

### Self-heal (no admin clicks)

```powershell
automations\eve-launcher\build-eve-exe.bat
```

This script:
1. Restores from quarantine via `Restore-MpThreat` if the threat ID is known.
2. Adds the build output dir to Defender exclusions via `Add-MpPreference -ExclusionPath` (auto-elevates UAC ONLY for this one call).
3. Rebuilds the bundle from `automations/eve-launcher/eve.py`.
4. Syncs the new EVE.exe to the repo root + `deploy/`.

Doctrine: `_shared-memory/knowledge/automate-everything-no-operator-admin-2026-05-25.md`.
Operator hard-canonical 2026-05-25: agent finds an automated workaround;
operator never clicks UAC.

---

## 4. Git push permission denied

### 4.1 SSH "Permission denied (publickey)"

```powershell
# Generate a key:
ssh-keygen -t ed25519 -C your-email@example.com
type "$env:USERPROFILE\.ssh\id_ed25519.pub"   # copy this

# Paste at https://github.com/settings/keys
```

Re-run your push.

### 4.2 HTTPS auth failure

Mint a personal access token at <https://github.com/settings/tokens>
(scope: `repo` + `workflow`) and store it as User-scope env var:

```powershell
[Environment]::SetEnvironmentVariable('GH_TOKEN','<your-token>','User')
```

Restart your shell so the env var lands. `git push` will now use the token
automatically (GitHub CLI + git both read `GH_TOKEN`).

### 4.3 "Repository not found" / "not authorized"

The org `Sinister-Systems-LLC` must have invited your GitHub account.
Confirm at <https://github.com/Sinister-Systems-LLC/people> or ask the
operator to invite you.

### 4.4 Single-repo push policy violation (`exit 13`)

Sanctum's pre-push hook (`automations/sanctum-push-policy.ps1`) blocks
pushes from any repo other than Sanctum + the 3 carve-outs (LetsText,
Showmasters, JB Woodworks). If your push exits 13:

```powershell
# Audit:
powershell -File "D:\Sinister Sanctum\automations\sanctum-push-policy.ps1" `
    -Action Audit

# Confirm you're on the right branch convention:
git rev-parse --abbrev-ref HEAD
# Expect: agent/<project-key>/<short-topic>-<utc-date>
```

Doctrine: `_shared-memory/knowledge/single-repo-push-policy-2026-05-25.md`.

### 4.5 `index.lock` from a crashed git process

```powershell
Get-Process git -ErrorAction SilentlyContinue          # confirm none
Remove-Item "D:\Sinister Sanctum\.git\index.lock" -Force
```

---

## 5. Claude OAuth login failure

### 5.1 Browser opens but never returns

Cause: stale OAuth state on the local machine. Wipe + retry:

```powershell
Remove-Item "$env:USERPROFILE\.claude\oauth.json" -Force -ErrorAction SilentlyContinue
claude
# OAuth flow re-fires; complete in browser
```

### 5.2 `Cannot login in non-interactive mode`

Every fleet agent spawns with `claude --dangerously-skip-permissions`,
which disables TTY allocation. CLIs whose `login` opens a browser
(`railway login`, `gh auth login`, `vercel login`, etc.) die with this
error.

**Fix:** mint a token via the service dashboard once, store as User-scope
env var. The CLI auto-picks it up.

| CLI | Env var | Mint location |
|---|---|---|
| Railway | `RAILWAY_TOKEN` or `RAILWAY_API_TOKEN` | <https://railway.com/account/tokens> |
| GitHub CLI | `GH_TOKEN` | <https://github.com/settings/tokens> |
| Vercel | `VERCEL_TOKEN` | <https://vercel.com/account/tokens> |
| npm | `NPM_TOKEN` (also `~/.npmrc`) | <https://www.npmjs.com/settings/~/tokens> |
| Supabase | `SUPABASE_ACCESS_TOKEN` | <https://supabase.com/dashboard/account/tokens> |
| Firebase | `FIREBASE_TOKEN` (run `firebase login:ci` once on a real workstation) | n/a |
| DigitalOcean | `DIGITALOCEAN_ACCESS_TOKEN` | <https://cloud.digitalocean.com/account/api/tokens> |
| Fly.io | `FLY_API_TOKEN` | `flyctl auth token` |
| Heroku | `HEROKU_API_KEY` | <https://dashboard.heroku.com/account> |
| Expo | `EXPO_TOKEN` | <https://expo.dev/accounts/[user]/settings/access-tokens> |
| Cloudflare | `CLOUDFLARE_API_TOKEN` | <https://dash.cloudflare.com/profile/api-tokens> |
| Netlify | `NETLIFY_AUTH_TOKEN` | <https://app.netlify.com/user/applications#personal-access-tokens> |

Full table + doctrine in `docs/ENV-VARIABLES.md`.

### 5.3 Rate limit ("429 Too Many Requests")

Multi-account rotation should handle this. Verify the watchdog is running:

```powershell
schtasks /Query /TN SinisterAccountWatchdog
```

If missing, install:

```powershell
powershell -ExecutionPolicy Bypass -File `
  "D:\Sinister Sanctum\automations\install-account-watchdog-task.ps1"
```

Manually mark the current account rate-limited so rotation skips it:

```powershell
powershell -File "D:\Sinister Sanctum\automations\claude-accounts.ps1" `
    -Action RateLimited -Name leo
```

---

## 6. Sinister Link pairing fails

| Symptom | Cause | Fix |
|---|---|---|
| Header stuck on `STALE` | Peer machine offline / Tailscale down | `tailscale ping <peer-ip>`; restart Tailscale; manual `-Action Sync` |
| `peer git head: (none on origin yet)` | Peer hasn't pushed any `agent/<slug>/*` branch yet | Wait for first auto-push (30 min) OR peer runs `git push -u origin agent/<slug>/...` |
| `git fetch failed` warning | No network / no GitHub auth | `git fetch origin` manually to see real error; fix auth (see Section 4) |
| Invite expired | Default TTL 60 min | Operator generates new with longer `-ExpiresMin` (e.g. 480 for 8 h) |
| Want to switch transport | Currently a re-pair | `Unlink`, then re-`GenerateInvite -Transport vault` |
| Both peers paired but not seeing each other | sanctum-auto-push not running | `schtasks /Query /TN SinisterSanctumAutoPush`; reinstall if missing |
| Header reads `unlinked` after sucessful pair | Operator broadcast `[LINK-UNLINK]` via fleet-update | Re-pair from scratch |

Re-install the link poller:

```powershell
powershell -File "D:\Sinister Sanctum\automations\install-sinister-link-poller.ps1"
```

Uninstall:

```powershell
powershell -File "D:\Sinister Sanctum\automations\install-sinister-link-poller.ps1" -Uninstall
```

---

## 7. Sinister Vault issues

| Symptom | Cause | Fix |
|---|---|---|
| `Connection refused` on `:5078` | Port collision | `Get-NetTCPConnection -LocalPort 5078` → kill owner, OR `setx SINISTER_VAULT_PORT 5079` and re-wire |
| Files not syncing between Leo + operator | Syncthing folder ID mismatch | Both sides must use the SAME folder ID — check `http://127.0.0.1:8384` → Folders → ID column |
| `vault.*` MCP tools missing in Claude | Proposal not merged, OR Claude Code not restarted | Merge `_vault\mcp-vault-entry-PROPOSED.json` into `~/.claude/.mcp.json`, then quit + reopen Claude Code desktop app |
| Mode B: `Invoke-RestMethod` times out | Tailscale ACL blocks port 5078 | Operator opens `tcp:5078` for Leo's device in tailnet ACL |
| `[FATAL] venv python not found` | `.venv` never created | `cd 'D:\Sinister Sanctum\tools\sinister-vault'; python -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt` |
| `Register-ScheduledTask: Access denied` | `-RunLevel Highest` needs admin | Re-run PowerShell as Administrator (one-time) |
| Daemon `State = Disabled` | Manually disabled | `Enable-ScheduledTask -TaskName SinisterVault` |
| Heartbeat stale (>120 s) but task Running | uvicorn worker stuck | Read `_daemon-logs\vault-*.log`; kill `python.exe`; bat restart loop respawns it |

---

## 8. Plugin install appears hung

```powershell
Get-Content "$env:USERPROFILE\.claude\sanctum-plugin-check.log" -Tail 40 -Wait
```

Background install can take 10-30 s on a cold cache. If actually wedged,
kill any orphaned `powershell.exe` running `check-required-plugins.ps1`
and re-run the bat.

---

## 9. Per-project `[missing root]` badge in picker

### Symptom
Picker shows `[missing root]` next to Sinister Panel / Kernel APK /
Snap-API-EMU / TikTok-API-EMU, and the spawn aborts with
"sanctum sub-projects are missing their source/ content".

### Root cause
Operator's box uses NTFS directory junctions to other `D:\` paths that
don't exist on yours. Your Sanctum clone is fine — per-project source
folders just need to be cloned from their own GitHub repos.

### Fix (one command)

```powershell
cd "D:\Sinister Sanctum"
powershell -ExecutionPolicy Bypass -File automations\clone-missing-sources.ps1
```

Or **double-click** `automations\Clone-Missing-Sources.bat`. Targets every
project with a `github` field in `projects.json` whose `root` is missing.
Falls back from SSH to HTTPS (uses `GH_TOKEN` if set). Total clone size:
50-200 MB; time: 30 s - 2 min on normal connection.

Retry individual project:

```powershell
.\automations\clone-missing-sources.ps1 -Only kernel-apk
```

---

## 10. EVE first-run check returns exit 1 / 2

### Exit code meaning

- **0** = all green
- **2** = soft-warns only (still usable — Test-Connection blocked by
  sandbox, MCP count just informational, etc.)
- **1** = hard blockers — read the report

### Common hard blockers

| Blocker | Fix |
|---|---|
| `sanctum-root-missing-or-incomplete` | Confirm `D:\Sinister Sanctum\` exists + has CLAUDE.md / automations / etc. |
| `claude-cli-missing` | `npm i -g @anthropic-ai/claude-code` |
| `node-missing` | Install Node.js LTS first |
| `network_reachable = FAIL` (real machine, not sandbox) | Check internet; try `Test-NetConnection api.anthropic.com -Port 443` |
| `anthropic-api-key-missing` | `setx ANTHROPIC_API_KEY "sk-ant-..."` (User scope) |

Run the check:

```powershell
powershell -File "D:\Sinister Sanctum\automations\eve-first-run-check.ps1" `
    -Format text
```

---

## 11. Claude can't find the project

### Symptom
Cold-start references `D:\Sinister Sanctum\...` files that don't exist
on your box.

### Fix

```powershell
# Confirm clone landed at default path:
Test-Path "D:\Sinister Sanctum\CLAUDE.md"

# OR confirm env override is set:
[Environment]::GetEnvironmentVariable('SINISTER_SANCTUM_ROOT','User')

# If you set the env var, restart the shell (env is cached at spawn time):
exit
# ...reopen PowerShell, retry launcher.
```

---

## 12. PATH not refreshed after `npm i -g`

### Symptom
Leo installs Node via the .msi, opens existing PowerShell, runs
`npm i -g @anthropic-ai/claude-code`, npm reports success — but `claude`
command not found.

### Root cause
Windows PATH updates require a NEW shell. PowerShell sessions started
before the install don't see the new npm-global bin dir.

### Fix
Close that PowerShell window. Open a fresh one. Re-run.

Setup Wizard's primer prompt explicitly tells the user this; the Setup
Wizard agent will also try `Get-Command claude.exe` first AND fall back
to `%APPDATA%\npm\claude.cmd` if PATH lookup fails.

---

## 13. Where to look when nothing in here helps

| Surface | What it tells you |
|---|---|
| `_shared-memory/status/index.html` | live dashboard (P1-P9, per-project, brain, inbox, recent ships, PP scoreboard) |
| `_shared-memory/sinister-doctor-<UTC>.html` | timestamped daily health report |
| `_shared-memory/telemetry/_latest.json` | machine-readable rollup |
| `_shared-memory/OPERATOR-ACTION-QUEUE.md` | open operator-clicked items |
| `_shared-memory/PROGRESS/Sinister Sanctum.md` | sanctum-lane append-only ship log |
| `_shared-memory/knowledge/_INDEX.md` | brain doctrine catalog (grep before risky action) |
| `_shared-memory/cross-agent/` | cross-lane broadcast messages |
| `%USERPROFILE%\.claude\sanctum-plugin-check.log` | plugin install log |
| `_shared-memory/setup/leo-bots-install-<utc>.log` | Docker bot install log |
| `_daemon-logs\vault-*.log` | vault daemon log |

If genuinely stuck: pair via Sinister LINK (Section 6) and the operator's
agents will see your `_shared-memory/inbox/<slug>/` messages in real time.
