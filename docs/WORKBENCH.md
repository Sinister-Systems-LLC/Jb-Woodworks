> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# RKOJ.exe — the operator's workbench

`RKOJ.exe` is the Sanctum's flagship operator window. One binary, two tabs, an Excel-style ribbon, dev-tools rails, a popout system, cycle points, a scheduler, a command palette, and the Sinister Vault drawer — all wrapped in Sanctum purple + Liquid Glass.

This page is the **operator one-pager**. For architecture deep-dive see `_shared-memory/knowledge/rkoj-workbench-architecture.md`. For the source tree see `automations/window-manager/`.

---

## What RKOJ is

- **Built from:** `D:\Sinister Sanctum\automations\window-manager\` (FastAPI server + vanilla JS frontend + pywebview window shell)
- **Output binary:** `D:\Sinister Sanctum\automations\window-manager\dist\RKOJ\RKOJ.exe`
- **Spec file:** `automations/window-manager/RKOJ.spec` (the `name='RKOJ'` flag drives the binary name; renamed 2026-05-19 from `Sanctum-Console.spec` as part of the HR-B bundle fix)
- **Window title:** `RKOJ :: Workbench`
- **Server port:** `127.0.0.1:5077` (loopback only by default; `Sanctum-LAN.bat` exposes on LAN with bearer-token auth + QR code)
- **Frontend:** desktop at `/` (index.html / app.js / theme.css / tokens.css); mobile at `/m/` (mobile.html / mobile.css / mobile.js — iOS blue per design doctrine)
- **Auth:** HWID-bound per key (operator + Leo); keys at `_vault/auth-keys.json`
- **Replaces:** `Sanctum-Console.exe` (same source folder, same endpoints, only the binary name + window title + chrome strings changed)

---

## The two tabs

### Tab 1 — ADB Devices

- Header strip with **lane filter** + Refresh + status pill
- **Device grid:** one `.lg-card` per phone (serial + model header, state badge, lane chip, viewer pill, battery, attestation, proxy)
- Per-card actions: **VIEW** (scrcpy launches with `--display-id 0` per anti-detect rule), **STOP**, **Push**, **Notes**, **Run cmd**, **Frida install**
- Per-card collapsible **cmd history** (persists in `localStorage.adb_history_<serial>`)
- Empty state when no phones attached
- Per-tab dev-tools rail: refresh interval slider, scrcpy options, default push paths, bulk actions ("Scan all phones in parallel", "Push file to all phones in lane X"), audit log viewer

### Tab 2 — Agents Workbench

- **Sessions strip** — one `.lg-card` chip per online agent: avatar + accent ring + name + project tag + model badge; inline buttons for intelligence, inbox, nudge, cycle-point save, popout
- **Project workspace** — project picker + mode picker (`overview` / `dev` / `audit` / `deploy` / `push` / `debug` / `explore`) + Fast toggle + custom-prompt textarea + LAUNCH button (calls existing `/api/launcher/spawn`)
- **Recent launches** + **Cycle points list**
- **Activity feed** — merged Progress + Inbox-tails + Operator-Requests, most-recent at top, filterable, click-to-act
- Per-tab dev-tools rail: **Memory** / **Codex** / **Knowledge** / **Settings** / **Schedule** / **Vault** drawers

---

## The Excel-style ribbon

Sticky two-row top strip. **Row 1:** logo + `RKOJ :: WORKBENCH` brand + 2-tab pill + global icons (bell with operator-requests count, settings, Cmd+K, health pill, clock). **Row 2:** tab-specific groups of icon+label tiles.

| Group | Tiles |
|---|---|
| **VIEW** | Split-view toggle · Popout current pane · Toggle dev-tools rail · Layout presets |
| **SPAWN** | New agent (Launcher wizard) · Spawn from cycle point · Send inbox to all · Codex review |
| **AUTOMATE** | Cycle points list · Scheduler · Run script · Run schedule entry · **Commit to Vault** |
| **MAINTAIN** | Fix Claude memory · Build RKOJ.exe · Health probe · Restart console |

Tab pill uses `.lg-pill-active` (Sanctum purple bloom + border + glow); ribbon tiles use `.lg-button` (Liquid Glass background, accent border, press-scale 0.97).

---

## Cycle points (one-click resume)

Saves the full state of a working project so the operator can pause and resume EXACTLY where they left off (same agent name, same model, same mode, same files open, same recent context).

- **Save:** click `[💾 cycle point]` on a session card → name it ("snap-api SS03 hypothesis 3") + add note → POST `/api/cycle-points` writes JSON to `_shared-memory/cycle-points/<project>/<slug>.json`
- **Resume:** Agents tab → Cycle points list → click row → POST `/api/cycle-points/{slug}/resume` reads the JSON and calls `/api/launcher/spawn` with captured agent + model + mode + custom_prompt + open-files hint
- **Append-only:** new cycle = new file. Never overwrite.
- **Index:** `_shared-memory/cycle-points/_INDEX.md` (catalog: slug · project · name · last-updated · 1-line note)
- **Schema:** `rkoj/cycle-point/v1` (slug, project, name, note, created_at, created_by, agent.{name, model, fast, accent, mode, custom_prompt}, context.{branch, open_files, last_inbox_tail, recent_progress})

---

## Scheduler (cron-like project automation)

Cron entries that run forever — "every Monday 9am run secret-scrub on snap-emu", "every 4hr Custodian backup probe", "every night at 2am: nudge inbox-poll to every online agent".

- **File:** `_shared-memory/schedule.json` (array of entries)
- **Daemon:** asyncio task inside RKOJ server, 30s tick, `asyncio.Semaphore(5)` concurrency cap, cron parsed via `croniter`
- **Action kinds:**
  - `script` — runs a whitelisted bus script (`check-hetzner-state`, `verify-backups`, `memory-garden`, `aggregate-gotchas`, `prepare-for-migration-dryrun`)
  - `spawn-agent` — hits `/api/launcher/spawn`
  - `inbox` — broadcasts a message to one agent or all online
  - `resume-cycle` — fires a saved cycle point
  - `http` — generic localhost call
- **Endpoints:** `GET/POST /api/schedule`, `PATCH /api/schedule/{id}`, `DELETE /api/schedule/{id}`, `POST /api/schedule/{id}/run-now`
- **UI:** Schedule drawer in Agents tab — list of entries with name · cron expression · last-run badge · next-run countdown · enable/disable · Run Now · Edit / Delete; `+ NEW SCHEDULE` modal with cron presets (hourly / daily / weekly / monthly / custom) + kind-specific action forms

---

## Popout system

Any panel in the workbench can be torn off into its own browser window. Operator can have RKOJ on monitor 1 + the Device grid on monitor 2 + a per-phone cmd console on monitor 3 — all the same session, no duplicate auth.

- **Mechanism:** `[↗ popout]` button → `window.open()` with `#popout=<view>&state=<base64-json>` fragment
- **Popout-mode flag:** `document.body.classList.add('rkoj-popout')` hides ribbon + tabs, shows just the requested view full-screen
- **Cross-window sync:** `BroadcastChannel('rkoj-state')` — local card update → broadcast `{type, view, state}` → other windows re-render. Fallback: `localStorage` storage event.
- **Tracked in:** `localStorage.rkoj.popouts` (persists across refresh). Ribbon Popout button shows count + dropdown of open popouts (click to focus / close).
- **Soft cap:** 8 popouts (override in global settings)

---

## Vault drawer (Sinister Vault integration)

The Vault drawer in the Agents-tab dev-tools rail surfaces the live state of the **Sinister Vault** (`D:\sinister-vault\`, 1 TB soft quota, daemon on `localhost:5078`). RKOJ proxies the vault endpoints so the drawer has no CORS dance.

- **Quota meter** — used GB / max GB, color shifts to warn at 950 GB and critical at 1024 GB
- **Recent audit feed** — most-recent at top, per-event `kind` chip (commit / push / pull / sync / snapshot / warn / error / info) + actor chip (operator / leo) + path + message; click → opens repo at sha (for commits) or sync-conflict resolution UI (for syncs)
- **Sync status** — Syncthing peer list + per-peer last-sync timestamp + connection state (LAN / WAN / relay)
- **Account picker** — switches active identity + accent color + env-var binding without restart
- **Commit-to-Vault modal** (from the AUTOMATE ribbon group) — pick repo + add files + write commit message + push → vault daemon audit-logs the commit → drawer refreshes automatically

See `tools/sinister-vault/README.md` (daemon overview) and `_shared-memory/knowledge/sinister-vault-architecture.md` (3-tier design).

---

## Command palette (Cmd+K)

For everything not foregrounded on a primary tab. Fuzzy search across:

- All projects (jump to launch flow)
- All agents (jump to inbox)
- All knowledge slugs (open in Knowledge drawer)
- All skill / tool / invention slugs (open markdown reader)
- All cycle points (jump to resume)
- All schedule entries (jump to edit / run-now)
- All ribbon actions (run without clicking)

Backend: existing `/api/skills`, `/api/tools`, `/api/inventions`, `/api/knowledge`, `/api/sessions`, `/api/cycle-points`, `/api/schedule` → aggregated and ranked client-side.

---

## Multi-account picker

Top-right of the ribbon. Reads accounts from `GET /api/vault/accounts` (proxied through RKOJ at `/api/vault/accounts` on port 5077). Switching account swaps:

- Active **identity** ("Sinister Sanctum" / "Sinister Leo" / future)
- **Accent color** (purple / magenta / cyan)
- **Env-var binding** for Anthropic API key (operator → `ANTHROPIC_API_KEY`, leo → `LEO_ANTHROPIC_API_KEY`)
- **Gitea user** that signs commits
- **Syncthing device ID** that pairs sync

Profiles live at `D:\sinister-vault\accounts\<name>.json`. See `tools/sinister-vault/ACCOUNTS.md` for the schema and the "add a new account" runbook.

---

## HWID auth (operator + Leo keys)

- Keys stored at `_vault/auth-keys.json` (off-limits to bot reads unless operator explicitly OKs)
- First-use of a key binds it to the machine's HWID — same key on a different machine = denied
- Two keys ship by default: **operator** + **leo**
- LAN mode (`Sanctum-LAN.bat`) layers bearer-token auth on top of HWID for the QR-code phone-pairing flow
- Lock-out recovery: operator-only manual edit of `auth-keys.json` to clear `hwid_bound` field

---

## Mobile surface (`/m/` deep links)

Phone-friendly surface at `http://localhost:5077/m/` (or the LAN equivalent after `Sanctum-LAN.bat`). Hand-ported iOS-blue tokens + Liquid Glass primitives + sticky header + 5-tab bottom-nav (Dashboard / Sessions / Phones / Knowledge / Settings). Pull-to-refresh + 20s pollers. `@media (prefers-reduced-motion)` honored.

The mobile surface is intentionally **separate from the desktop tabs** — phone use cases (quick status check, approve an operator request, kill an agent) are different from desktop use cases (build a project, debug a phone, write a schedule).

---

## How to launch

```text
C:\Users\Zonia\Desktop\RKOJ.bat
```

That's it. The bat kills any stale RKOJ process, spawns `RKOJ.exe` (the pywebview window), and waits. If the EXE isn't built yet, it falls back to source-mode python on `:5077` so the operator still has a working workbench.

For the always-on path (daemon mode that restarts on crash):

```text
C:\Users\Zonia\Desktop\Start-Sanctum-Console.bat
```

That spawns `console-daemon.bat` which keeps the python server up 24/7 with a 5/hour restart cap. Heartbeat at `_shared-memory/heartbeats/sanctum-console.beat`.

---

## How to rebuild

```text
C:\Users\Zonia\Desktop\Build-Sanctum-Console.bat
```

The bat invokes `automations/window-manager/build-sanctum-console.sh` (a 10-step warm-probe pipeline):

1. Pre-flight checks (venv, requirements, spec file)
2. `pip install -r requirements.txt --disable-pip-version-check` (warm path skips if already installed)
3. PyInstaller build via `RKOJ.spec` (binary name = `RKOJ` per the `name='RKOJ'` flag)
4. Output to `dist/RKOJ/RKOJ.exe`
5. PowerShell-wrapped robocopy of the dist tree to Desktop (avoids MSYS path-mangling of `/MIR` → `C:/Program Files/Git/MIR`)
6. Smoke probe: launch the new EXE, hit `/api/health`, kill, verify exit code 0
7. Build log to `automations/window-manager/_build-logs/build-<UTC>.log`
8. Runlog to `runtime-state/script-runs/build-sanctum-console-<UTC>.json`
9. PROGRESS entry append
10. Warm-flag write (so the next rebuild can skip steps 1–2)

Warm rebuild target: < 30 s. Cold rebuild target: < 90 s. Honor `set -o pipefail`. `croniter` is a required dep (new since the scheduler shipped) — make sure `requirements.txt` lists it.

---

## Source-mode live-update workflow

The dev surface is source-mode python on `:5077`:

```bash
cd "D:/Sinister Sanctum/automations/window-manager"
python desktop_app.py
```

Edits to `web/*.{html,css,js}` are live (browser refresh picks them up). Edits to `server.py` or `sanctum_shared/*.py` require a Python process restart (Ctrl+C + relaunch). The frozen `RKOJ.exe` is the deploy artifact — rebuild periodically with `Build-Sanctum-Console.bat` once you've stabilized.

---

## See also

- `_shared-memory/knowledge/rkoj-workbench-architecture.md` — full architecture brain entry (Problem / Why / Fix / Discoveries)
- `_shared-memory/knowledge/sinister-vault-architecture.md` — Vault 3-tier design
- `_shared-memory/DIRECTIVES.md` — standing rules every cold-start agent reads (RKOJ + Vault rules near the top)
- `automations/window-manager/BUILD.md` — build pipeline details
- `automations/window-manager/AUTOSTART.md` — `SanctumConsole` / `RKOJ` scheduled task lifecycle
- `tools/sinister-vault/README.md` — Vault daemon overview + HTTP surface
- `tools/sinister-vault/ACCOUNTS.md` — multi-account schema + add-new-account runbook
- `tools/sanctum-git/vault-integration.md` — Gitea-side commit-as-upload pattern
- `docs/UI-DESIGN-SYSTEM.md` — Liquid Glass + Sanctum purple binding for master surfaces
