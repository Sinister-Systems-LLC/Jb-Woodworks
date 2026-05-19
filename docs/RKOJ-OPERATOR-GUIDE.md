> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# RKOJ Operator Guide

Everything you need to use the workbench, vault, and agent fleet. Read once, run the system.

This guide supersedes `docs/WORKBENCH.md` (older, lighter). For deep architecture see `_shared-memory/knowledge/rkoj-workbench-architecture.md` and `_shared-memory/knowledge/sinister-vault-architecture.md`.

---

## 0. First time setup (one-time)

1. Double-click `C:\Users\Zonia\Desktop\RKOJ.bat` once — launches `RKOJ.exe` (or falls back to source-mode python on `:5077` if the EXE isn't built yet).
2. The pywebview window opens at `/login` — paste your HWID-bound operator key (stored in `_vault\auth-keys.json`; Leo gets his own key). First-use binds the key to this machine's HWID; same key on a second machine = denied.
3. From an **elevated PowerShell**: `cd 'D:\Sinister Sanctum\tools\sinister-vault'; .\install-vault-task.ps1` — registers the `SinisterVault` scheduled task → vault daemon (port 5078) auto-starts on logon.
4. Install Syncthing: `D:\Sinister Sanctum\tools\sinister-vault\syncthing\install.ps1` — installs Syncthing as a Windows service (UDP 22000 + 21027 open in firewall, web UI at `http://localhost:8384`).
5. Relocate Gitea data into the vault: `powershell -ExecutionPolicy Bypass -File 'D:\Sinister Sanctum\tools\sanctum-git\setup-vault-data-dir.ps1'` — moves Gitea data to `D:\sinister-vault\gitea\` so every push counts toward the 1 TB quota + audit log.
6. Provision Gitea users: `python "D:\Sinister Sanctum\tools\sanctum-git\bootstrap-users.py" --leo-key-file <path-to-leo.pub>` — idempotently creates `operator` (admin) + `leo` (collaborator, must-change-password on first login) and installs SSH keys.
7. (Optional) Re-run `install-fleet.ps1` so the **vault MCP server** (`bots/agents/vault/`) gets registered in `~/.claude/.mcp.json` — agents then call `vault.commit / push / pull / list / search / sync_status / accounts / snapshot / audit / health` directly.
8. Send Leo: (a) his operator key, (b) the onboarding doc at `D:\Sinister Sanctum\tools\sinister-vault\syncthing\onboard-leo.md`, (c) a link to this guide.

---

## 1. Daily flow

- **Launch:** double-click `C:\Users\Zonia\Desktop\RKOJ.bat`. Pywebview window opens titled **RKOJ :: Workbench**.
- **Always-on path:** `C:\Users\Zonia\Desktop\Start-Sanctum-Console.bat` spawns `console-daemon.bat`, which keeps the server up 24/7 (5/hour restart cap, heartbeat at `_shared-memory\heartbeats\sanctum-console.beat`).
- **Login:** paste your HWID-bound key once per machine.
- **Browse:** two top tabs across the main pane — **ADB Devices** and **Agents** (plus the **Vault drawer** in the Agents-tab dev-tools rail).

---

## 2. Anatomy of the workbench

### Sidebar (left, after UI-A redesign)
- **DAILY:** Overview · Progress · Accounts · Control Center
- **INSIGHTS:** Analytics · Library · Codex · Memory
- **MANAGE:** Phones · Agents · Vault · Scheduler · Cycle points · Settings

### Top tabs (inside main pane)
- **Fleet (ADB Devices)** — device grid + per-device detail
- **Agents** — sessions strip + launcher wizard + recent launches + cycle points + activity feed
- **Vault** (in dev-tools rail) — quota meter + audit feed + sync status + commit/snapshot actions

### Top-right icon row (ribbon Row 1)
- **!** — bell with operator-requests pending count + `[ASK]` count for the active agent
- **bell** — notifications (broadcasts + cross-agent inbox)
- **home** — reset to default view
- **star** — Ctrl+K command palette (fuzzy search across everything)
- **● online** — RKOJ health pill (probes `/api/health`)
- **clock** — current local time

### Hero KPI row (per tab)
Four stat cards refresh every ~15 s: **PHONES ONLINE / AGENTS ONLINE / VAULT USED / PENDING REQUESTS**.

### Excel-style ribbon (Row 2, tab-specific)
| Group | Tiles |
|---|---|
| **VIEW** | Split-view toggle · Popout current pane · Toggle dev-tools rail · Layout presets |
| **SPAWN** | New agent (Launcher wizard) · Spawn from cycle point · Broadcast · Codex review |
| **AUTOMATE** | Cycle points list · Scheduler · Run script · Run schedule entry · **Commit to Vault** |
| **MAINTAIN** | Fix Claude memory · Build RKOJ.exe · Health probe · Restart console · **Ping all (heartbeat)** |

---

## 3. Daily actions

### Spawn a new Claude agent
Agents tab → **"Spawn a new agent session"** → pick project + mode (`overview / dev / audit / deploy / push / debug / explore`) → optional Fast toggle + custom-prompt textarea → **LAUNCH**. A git-bash window opens with Claude already started + cold-start phrase injected. Calls `/api/launcher/spawn`.

### Save a cycle point (resume later, exactly)
Agents tab → session card → **`[cycle point]`** → name it (e.g. `snap-api SS03 hyp-3`) + add note → Save. POSTs `/api/cycle-points`; writes JSON snapshot to `_shared-memory/cycle-points/<project>/<slug>.json`. Schema `rkoj/cycle-point/v1`. Snapshot captures: agent name + model + mode + accent + Fast flag + custom prompt + branch + open files + last inbox tail + recent progress. Append-only: new save = new file. Catalog at `_shared-memory/cycle-points/_INDEX.md`.

### Resume a cycle point
Agents tab → Cycle points list → click row → **Resume**. POST `/api/cycle-points/{slug}/resume` reads the JSON, calls `/api/launcher/spawn` with captured params + a synthetic prompt: "resume cycle X, read these files, continue from Y."

### Set an agent's intelligence level (no kill, no respawn)
Agents tab → session card → **`[Intelligence]`** → pick **Opus 4.7 / Opus 4.6 / Sonnet 4.6 / Haiku 4.5** + optional Fast → Apply. POST `/api/agents/{name}/intelligence`. Two tracks fire at once:
- **Persistent:** writes `_shared-memory/agent-prefs.json` → next launcher spawn boots at the new level (`start-sinister-session.ps1` reads it + injects `--model <name>`).
- **Live:** drops `[CONFIG] model=<X> fast=<Y> — call /model now, ack, continue.` into the agent's inbox. Per DIRECTIVES Rule 9, the agent's next `inbox_poll` will `/model <X>` itself and continue prior task. Worst-case swap lands on next turn boundary.

### Schedule a recurring task
Agents tab → dev-tools rail → **Schedule drawer** → **`+ NEW SCHEDULE`**. Pick a cron preset (hourly / daily / weekly / monthly / custom) + kind:
- `script` — whitelisted bus scripts (`check-hetzner-state`, `verify-backups`, `memory-garden`, `aggregate-gotchas`, `prepare-for-migration-dryrun`)
- `spawn-agent` — calls `/api/launcher/spawn`
- `inbox` — broadcasts a message to one agent or all online
- `resume-cycle` — fires a saved cycle point
- `http` — generic loopback call

Entries persist to `_shared-memory/schedule.json`. Daemon = asyncio task inside RKOJ server, 30 s tick, `asyncio.Semaphore(5)` concurrency cap, parsed via `croniter`. Endpoints: `GET/POST /api/schedule`, `PATCH/DELETE /api/schedule/{id}`, `POST /api/schedule/{id}/run-now`.

### Save the current spawn as a recurring schedule
After the Spawn flow exits, the launcher asks: "Save this spawn as a scheduled entry? Y/N". Pick a cron preset + name → POSTs to `/api/schedule` automatically.

### View a phone's screen inline (no scrcpy popup)
Fleet tab → device card → **`EMBED SCREEN`**. Renders inline at ~2 fps via MJPEG (`GET /api/devices/{serial}/screen.mjpeg?fps=<0.2..10>`). Backed by `adb -s <serial> exec-out screencap -p` — no `--display-id`, no `--new-display` flags (operator's spoofing is upstream; `screencap` doesn't create a VirtualDisplay). Close with `✕`, reconnect with `⟳`. Agent-visible: any LLM hitting `/api/devices/{serial}/screen` (single-shot PNG) sees the same framebuffer. Default cap **2 fps**, max **10 fps**.

### Use scrcpy (full window + audio + touch)
Fleet tab → device card → **`VIEW`**. Spawns scrcpy in its own native window with `--display-id 0` (anti-detect rule from `scrcpy-virtual-display-detected.md`).

### Run an ADB command on a specific phone (containerized)
Fleet tab → device card → cmd input row → type e.g. `shell pm list packages | head -5` → **RUN**. Output appears in the cmd-history pane below; history persists across reload in `localStorage.adb_history_<serial>`.

### Push a file to a phone
Fleet tab → device card → **`PUSH FILE`** → src path + dst path → **SEND**.

### Bulk phone actions
Fleet tab → dev-tools rail → **Bulk actions** → "Scan all phones in parallel" or "Push file to all phones in lane X".

### Commit a file to the vault
Vault drawer (Agents tab dev-tools rail) or the ribbon **AUTOMATE → Commit to Vault** tile → pick repo + file path + commit message + account (operator/leo) → **Commit**. Backend creates git commit + pushes to Gitea → vault daemon's file-watcher writes a `commit` audit event → drawer feed refreshes within ~15 s.

### Sync files real-time with Leo (Tresorit-like)
Drop any file into `D:\sinister-vault\sync\`. Leo (paired via Syncthing, see `tools/sinister-vault/syncthing/onboard-leo.md`) sees it within seconds. End-to-end encrypted (TLS 1.3, device-pinned certs), peer-to-peer, no central server. Conflict policy: never overwrite → keep both as `<file>.sync-conflict-<UTC>-<short-device-id>.<ext>`.

**Source code does NOT go here.** Use Gitea for anything text + mergeable; `sync/` is for assets, builds, recordings, scratch.

### Pop out a pane into its own window
Any card / drawer / detail view with **`[↗ popout]`** in its header → click → new browser window with just that view. Mechanism: `window.open()` with `#popout=<view>&state=<base64-json>` fragment + `document.body.classList.add('rkoj-popout')` hides ribbon/tabs. Cross-window sync via `BroadcastChannel('rkoj-state')` (fallback: `localStorage` storage event). Open popouts persist in `localStorage.rkoj.popouts`; ribbon Popout button shows count. Soft cap 8 (overridable in Settings).

### Hot-reload (ship updates while RKOJ runs, agents don't lose context)
Edit any `web/*.{html,css,js,png,svg,ico}` and save:
- **CSS / images:** SSE pushes change → RKOJ swaps the `<link href>` or `<img src>` in place with `?v=<mtime-ms>` — zero page reload, zero state loss.
- **JS / HTML:** SSE fires a "click toast to reload" nag — operator picks the moment (preserves popout cursor, form drafts).

Backend uses `watchdog` on `./web/` + per-path 400 ms debounce → fans out to every SSE subscriber via `loop.call_soon_threadsafe`. Endpoint: `GET /api/sse/changes?t=<token>` (token in query since EventSource can't send `Authorization:` headers). Source-mode also supports `python desktop_app.py --reload` for backend `uvicorn --reload` (frozen EXE prints a warning and ignores — bundled module has no `__file__`).

### Ping all agents (heartbeat)
Ribbon → **MAINTAIN → Ping all (heartbeat)**. POSTs `/api/inbox/update-ping` with `{subkind: "noop"}` → broadcasts `[UPDATE] noop` to every online agent → agents `[ACK alive uptime=<s>]` within ~30 s. Sessions strip shows `last_inbox_check` + `last_turn_marker` mtimes so you can tell ALIVE (recent inbox cursor write) from STALE (process up, no recent turn).

### Cross-agent coordination (agents help agents)
Per DIRECTIVES standing rule, agents talk directly via 5 patterns:
- **`[ASK]` / `[ANSWER]` / `[PASS]`** — tag-based handshake, one-to-one
- **`[DISCOVERY]`** — broadcast via `POST /api/inbox/broadcast` (browser helper: `RkojHelpers.broadcastToAllAgents(body, tags, from_agent?, exclude?)`)
- **`[DELEGATE]` / `[ACK]` / `[DONE]` / `[DECLINE]`** — cross-lane work hand-off (gates on operator OK per Rule 9/10)
- **Knowledge-share** — durable brain entries in `_shared-memory/knowledge/` (inbox is rolling-tail; brain is permanent)
- **`[UPDATE]` subkinds** — `refresh-prefs / branch-switch / palette-rebuild / knowledge-recheck / noop`, dispatched by `POST /api/inbox/update-ping`

The ribbon bell counts pending `[ASK]` for the active agent. All cross-agent traffic surfaces in the Activity Feed (filter by tag `cross-agent`).

### Command Palette (Ctrl+K)
Press **Ctrl+K** anywhere. Fuzzy search across: projects · agents · knowledge slugs · skills · tools · inventions · cycle points · schedule entries · ribbon actions. Enter to invoke. Aggregated client-side from existing `/api/skills`, `/api/tools`, `/api/inventions`, `/api/knowledge`, `/api/sessions`, `/api/cycle-points`, `/api/schedule`.

### Multi-account (operator + Leo + future)
Each user has `D:\sinister-vault\accounts\<name>.json` (schema `vault/account/v1`). Per-user fields: `display`, `anthropic_api_key_env`, `default_agent_identity`, `default_accent_color`, `default_model`, `gitea_user`, `syncthing_device_id`, `hwid_bound`, `bound_at`. Picker is in the ribbon top-right (reads `/api/vault/accounts`, proxied through RKOJ from port 5078 → 5077).

Switching account swaps the active **identity** ("Sinister Sanctum" / "Sinister Leo"), **accent color** (purple / magenta / cyan), **env-var binding** (`ANTHROPIC_API_KEY` for operator, `LEO_ANTHROPIC_API_KEY` for Leo), **Gitea user** signing commits, and **Syncthing device ID** for pairing.

**Add a new account:**
```powershell
Copy-Item D:\sinister-vault\accounts\_TEMPLATE.json D:\sinister-vault\accounts\alice.json
# Edit alice.json: name=alice, display=Alice, default_agent_identity="Sinister Alice",
# default_accent_color=cyan, anthropic_api_key_env=ALICE_ANTHROPIC_API_KEY
setx ALICE_ANTHROPIC_API_KEY "sk-ant-..."
# Append a row to D:\sinister-vault\accounts\_INDEX.md
Stop-ScheduledTask -TaskName SinisterVault; Start-ScheduledTask -TaskName SinisterVault
```

The vault daemon **never** reads or stores the actual API key — it hands the env-var NAME to the calling RKOJ session, which reads `os.environ[…]` at prompt-build time.

### LAN access (phone pairing via QR)
Run `C:\Users\Zonia\Desktop\Sanctum-LAN.bat` to expose `:5077` on LAN with bearer-token auth + QR code. Mobile surface at `http://<host>:5077/m/` (iOS-blue tokens, 5-tab bottom-nav: Dashboard / Sessions / Phones / Knowledge / Settings, pull-to-refresh, 20 s pollers).

---

## 4. Maintenance

### Rebuild RKOJ.exe
`C:\Users\Zonia\Desktop\Build-Sanctum-Console.bat` (filename kept for back-compat; output binary is `RKOJ.exe`). Invokes `automations/window-manager/build-sanctum-console.sh` (10-step warm-probe pipeline: pre-flight → pip → PyInstaller via `RKOJ.spec` → robocopy to Desktop → smoke probe `/api/health` → build log → runlog → PROGRESS append → warm-flag). Warm rebuild target **< 30 s**, cold **< 90 s**. Requires `croniter` + `watchdog>=4.0` in `requirements.txt`.

### Health probes
- RKOJ: `curl http://127.0.0.1:5077/api/health`
- Vault daemon: `curl http://127.0.0.1:5078/api/vault/health`
- Gitea: `curl http://localhost:3000`
- Syncthing: `curl http://localhost:8384`

### Auto-start verification
```powershell
Get-ScheduledTask -TaskName RKOJ                # RKOJ console (always-on path)
Get-ScheduledTask -TaskName SinisterVault       # Vault daemon
Get-ScheduledTask -TaskName SinisterCustodian   # Custodian backup
```
Expected `State`: **`Ready`** between logons, **`Running`** while logged in.

### Heartbeats
- RKOJ: `_shared-memory\heartbeats\sanctum-console.beat`
- Vault: `_shared-memory\heartbeats\sinister-vault.beat`
- Rule of thumb: mtime older than 120 s = stuck/dead.

### Logs
- RKOJ: `D:\Sinister Sanctum\automations\window-manager\_daemon-logs\` + `C:\Users\Zonia\Desktop\RKOJ\_exe-runtime.log`
- Vault per-launch: `D:\Sinister Sanctum\tools\sinister-vault\_daemon-logs\vault-<UTC>.log`
- Vault persistent: `D:\Sinister Sanctum\tools\sinister-vault\_daemon-logs\daemon.log`
- Vault audit: `D:\sinister-vault\audit\<YYYY-MM-DD>.jsonl` (one line per event: `commit / push / pull / sync / snapshot / warn / error / info`)
- Build: `D:\Sinister Sanctum\automations\window-manager\_build-logs\build-<UTC>.log`
- Scheduler: `D:\Sinister Sanctum\automations\window-manager\_daemon-logs\scheduler.log`

### Quota guardrails
- `--max-gb 1024` (hard cap) — above it, write endpoints return **HTTP 507 Insufficient Storage**; reads stay live.
- `--warn-gb 950` — one-shot `warn` event into audit stream on crossing, re-arms on drop below.
- Background asyncio task recomputes usage every 60 s, persists `_quota.json`.

### Source-mode dev loop
```bash
cd "D:/Sinister Sanctum/automations/window-manager"
python desktop_app.py --reload
```
Edits to `web/*.{html,css,js}` are live (SSE pushes). Edits to `server.py` or `sanctum_shared/*.py` get auto-reloaded by uvicorn. Frozen EXE is the deploy artifact — rebuild periodically with `Build-Sanctum-Console.bat`.

---

## 5. Troubleshooting

| Symptom | Fix |
|---|---|
| Browser shows `{ok:false,error:"redirect",redirect:"/login"}` JSON instead of login page | Old build with pre-fix middleware — rebuild RKOJ.exe |
| EXE process alive but `/api/health` doesn't respond | `sys.stdout/stderr None` bug in `console=False` build — already patched; rebuild if you still see it |
| EXE crashes immediately with "Failed to load Python DLL python312.dll" | Incomplete Desktop copy — re-run robocopy from `dist/RKOJ/` (rerun `Build-Sanctum-Console.bat`) |
| Launcher pre-flight stalls at "files good to go?" | Slow venv probe — already optimized in SS-D; rebuild launcher if you still see this |
| Phone card empty / no devices | Check `adb devices` from cmd; if 0, plug USB + accept "allow USB debugging" on phone |
| Schedule entry not firing | Vault daemon down — `Get-ScheduledTask SinisterVault` + `Start-ScheduledTask` |
| Cycle-point resume fails | Check `_shared-memory/cycle-points/<project>/<slug>.json` exists; check `GET /api/cycle-points` returns it |
| `SinisterVault` task `State = Queued` > 60 s | `Get-Process python` to see what's running; `Stop-ScheduledTask` + `Start-ScheduledTask` |
| Vault heartbeat stale > 120 s but task `Running` | Read latest `_daemon-logs/vault-*.log`; kill `python.exe` manually — the bat restart loop respawns it |
| `/api/vault/health` connection refused | Port 5078 in use — `Get-NetTCPConnection -LocalPort 5078`, kill owner, restart task |
| Syncthing devices never connect | UDP 22000 + 21027 must be open on both sides — re-run `install.ps1`; Leo opens those ports in Windows Defender Firewall |
| `.sync-conflict-*` file appears | Both sides edited same file before sync caught up — open both, merge manually, delete conflict copy |
| Agent ignored `[CONFIG] model=X` swap | Agent missed `inbox_poll` — Ping all (heartbeat); if no ack, restart that one agent and re-issue intelligence change |
| `Register-ScheduledTask: "Access is denied"` | Right-click PowerShell → Run as Administrator, re-run `install-vault-task.ps1` |

---

## 6. What's where (file map)

- `D:\Sinister Sanctum\automations\window-manager\` — RKOJ source (`server.py`, `desktop_app.py`, `RKOJ.spec`, `web/`, `sanctum_shared/`)
- `D:\Sinister Sanctum\automations\start-sinister-session.ps1` — agent spawn launcher (reads `agent-prefs.json`, injects `--model`)
- `D:\Sinister Sanctum\tools\sinister-vault\` — vault daemon (`daemon.py`), scripts (`install-vault-task.ps1`, `vault-daemon.bat`), `syncthing/` install
- `D:\Sinister Sanctum\tools\sanctum-git\` — Gitea integration (`setup-vault-data-dir.ps1`, `bootstrap-users.py`, `docker-compose.yml`, `vault-integration.md`)
- `D:\Sinister Sanctum\tools\sinister-phone-viewer\` — `viewer.py` (ADB primitives + `capture_screen`)
- `D:\Sinister Sanctum\bots\agents\vault\` — Vault MCP server
- `D:\sinister-vault\` — 1 TB vault tree (`repos/`, `sync/`, `snapshots/`, `audit/`, `accounts/`, `gitea/`, `_quota.json`)
- `D:\Sinister Sanctum\_shared-memory\` — shared brain (`DIRECTIVES.md`, `PROGRESS/<agent>.md`, `knowledge/`, `cycle-points/<project>/<slug>.json`, `schedule.json`, `agent-prefs.json`, `_inbox/<agent>/messages.jsonl`, `heartbeats/`)
- `D:\Sinister Sanctum\_vault\` — HWID auth keys (`auth-keys.json`; operator-only; gitignored)
- `C:\Users\Zonia\Desktop\` — operator entry bats (`RKOJ.bat`, `Build-Sanctum-Console.bat`, `Start-Sanctum-Console.bat`, `Start-Sinister-Session.bat`, `Sanctum-LAN.bat`, `Sanctum-Vault-Start.bat`)

---

## 7. See also

- `_shared-memory/DIRECTIVES.md` — standing operator rules (canonical 13)
- `_shared-memory/knowledge/_INDEX.md` — brain catalog
- `_shared-memory/knowledge/rkoj-workbench-architecture.md` — full RKOJ architecture
- `_shared-memory/knowledge/sinister-vault-architecture.md` — Vault 3-tier design
- `_shared-memory/knowledge/agent-intelligence-control.md` — `[CONFIG]` two-track pattern
- `_shared-memory/knowledge/rkoj-hot-reload-pattern.md` — SSE + `[UPDATE]` inbox pattern
- `_shared-memory/knowledge/rkoj-embedded-device-viewer.md` — MJPEG embedded screen
- `_shared-memory/knowledge/cross-agent-coordination.md` — 5 cross-agent patterns
- `docs/UI-DESIGN-SYSTEM.md` — design doctrine (Sanctum purple, Liquid Glass, motion)
- `docs/PANEL-INTEGRATION.md` — panel localhost routing
- `docs/WORKBENCH.md` — older, lighter operator one-pager (this guide supersedes it)
- `tools/sinister-vault/README.md` — Vault daemon overview + HTTP surface
- `tools/sinister-vault/ACCOUNTS.md` — multi-account schema + add-new-account runbook
- `tools/sinister-vault/AUTOSTART.md` — `SinisterVault` scheduled task lifecycle
- `tools/sinister-vault/syncthing/onboard-leo.md` — Leo's Syncthing onboarding (send him this)
- `tools/sanctum-git/vault-integration.md` — Gitea-side commit-as-upload pattern
- `automations/window-manager/AUTOSTART.md` — `RKOJ` scheduled task lifecycle
- `automations/window-manager/BUILD.md` — build pipeline details
