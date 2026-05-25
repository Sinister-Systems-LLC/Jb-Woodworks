# Sinister Sanctum — Getting Started (Comprehensive)

**Author:** RKOJ-ELENO :: 2026-05-25

This is the deep-dive companion to `README.md`. Read it end-to-end if you're
joining the fleet for the first time. Merged + distilled from
`docs/LEO-SETUP.md`, `docs/LEO-VAULT-SETUP.md`,
`docs/OPERATOR-QUICK-REFERENCE.md`, `docs/SETUP.md`, `docs/SINISTER-LINK.md`,
and `docs/ENV-VARIABLES.md`.

---

## Table of contents

1. Prereqs
2. First launch (what happens when you double-click EVE.exe)
3. Adding your Claude / Anthropic account
4. Pairing with the operator's machine via Sinister LINK
5. Daily use (commands you'll run every day)
6. Where things live (the map)
7. Troubleshooting pointers
8. Cross-references

---

## 1. Prereqs

Install in this order. `deploy/setup.py` handles every step automatically;
the table is for your reference + manual recovery if the auto-installer
balks on a corner case.

### 1.1 Git for Windows (required)

The launcher probes these exact paths (lines 76-89 of
`tools/session-launcher/Sinister Start.bat`):

```
C:\Program Files\Git\usr\bin\mintty.exe
C:\Program Files\Git\git-bash.exe
C:\Program Files\Git\bin\bash.exe
```

Install from <https://gitforwindows.org>. Accept defaults (the bat assumes
`C:\Program Files\Git`). If you must install elsewhere, set
`SINISTER_GIT_ROOT` (User scope) to point at it.

### 1.2 Node.js LTS + Claude Code CLI v2.1+ (required)

```powershell
# Node 20.x LTS from https://nodejs.org
# Then:
npm i -g @anthropic-ai/claude-code
claude --version    # expect 2.1.x or newer
```

Earlier Claude versions choke on the positional prompt the launcher passes
as the cold-start phrase. If you upgrade mid-session, fully close the
existing terminal — npm-global PATH updates don't propagate to live
processes.

### 1.3 Python 3.10+ (recommended)

Standard install from <https://www.python.org/downloads>; check
"Add to PATH". Needed for:

- Rebuilding `EVE.exe` (`automations/eve-launcher/build-eve-exe.py`)
- Running `sinister-term` (the standalone Python terminal)
- Running MCP bots directly instead of via Claude Code
- Running `deploy/setup.py` itself

### 1.4 `ANTHROPIC_API_KEY` env var (required for full power)

```powershell
[Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY','sk-ant-api03-...','User')
```

**Without it the fleet still runs** (Claude Code uses your interactive
login), but these go dark per `docs/ENV-VARIABLES.md`:

- **RKOJ.exe Anthropic SDK direct path** falls back to slower
  `claude -p` subprocess.
- **Tier-3 bots** (`scribe`, `curator`, `sinister-chatbot` server-side)
  all return `{ok:false, error:"no API key"}`.

Format: standard Anthropic SDK key `sk-ant-api03-...`. Restart any open
shells after setting (env is cached at spawn time).

Optional sibling keys: `GEMINI_API_KEY` (image-gen), `OPENAI_API_KEY`
(Codex peer-review).

### 1.5 Optional — Docker Desktop (Tier-2 bots)

```powershell
winget install Docker.DockerDesktop
# Start Docker Desktop (whale icon must appear in tray)
powershell -File "D:\Sinister Sanctum\automations\install-leo-bots.ps1"
```

Pulls `ollama/ollama:latest` (~4 GB for runtime + model on first generate)
and the optional Gitea mirror. Logs to
`_shared-memory/setup/leo-bots-install-<utc>.log`. Without it,
librarian / triage / researcher run in degraded-fallback mode.

### 1.6 Optional — Tailscale (Sinister LINK Mode B)

<https://tailscale.com/download/windows>. Only needed if you want
real-time pairing with operator's machine over WAN. See Section 4.

---

## 2. First launch (what happens when you double-click EVE.exe)

### 2.1 The boot sequence

1. **First run only** — the bat sees no `%USERPROFILE%\.sanctum-autonomy-granted`
   marker, so it triggers `automations/grant-claude-autonomy.ps1`. This
   writes `bypassPermissions` defaults into `~/.claude/settings.json` and
   creates the marker. One-time, ~5 seconds.

2. **Plugin check** runs in background
   (`automations/check-required-plugins.ps1 -AutoInstall -Silent`) —
   auto-installs `understand-anything`, `code-review`, `commit-commands`
   if missing. Logs to `%USERPROFILE%\.claude\sanctum-plugin-check.log`.
   Non-blocking.

3. **EVE.exe picker** opens in its own window with the project menu:
   - `1`-`15` → spawn that project's lane (Sanctum, Showmasters, JB Woodworks, etc.)
   - `G` → grant autonomy re-run
   - `A` → all-lanes spawn
   - `N` → new project bootstrap
   - `R` → resume last
   - `K` → kill all sessions
   - `S` → status dashboard
   - `L` → Sinister LINK pairing sub-page (see Section 4)
   - `B`/Enter → back · `X` → exit

   If EVE.exe is missing or stale (zero bytes / `--version` fails within
   3s), the bat falls through to the PowerShell picker at
   `automations/start-sinister-session.ps1`.

### 2.2 What a healthy launch looks like

- **~0.6 s ASCII banner** — animated jcode-style "C" intro inside the
  spawned mintty window.
- **Status pill row**:
  ```
  sanctum :: resume :: claude-opus-4-7[1m] :: mcp:NN :: bots:NN :: --skip-perms
  ```
  Numbers vary by what MCP servers + bots loaded.
- **Claude Code UI** opens with the cold-start phrase pre-loaded as the
  first user message. EVE reads `CLAUDE.md` step 0 →
  `understand-anything:understand-explain` on the lane root → proceeds
  through cold-start steps 1-11.

You're live. First turn will be EVE acknowledging the lane + reading hard
rules.

### 2.3 Verify with --diagnose

If something looks off, run the non-spawning probe:

```cmd
"D:\Sinister Sanctum\tools\session-launcher\Sinister Start.bat" --diagnose
```

Reports every probe (root, shells, EVE.exe, plugin script) without
launching a session.

---

## 3. Adding your Claude / Anthropic account

The launcher rotates between **up to 4 (or more — slots are infinite per
operator hard-canonical 2026-05-24) named Claude accounts** so fleet
sessions don't all hit one account's rate-limit cap. Default slots are
`operator`, `leo`, `slot3`, `slot4` — fill them via the CLI, never
hand-edit JSON.

### 3.1 Create a private credentials file

```powershell
# Anywhere outside the repo (this file is operator-private; never committed):
notepad "$env:USERPROFILE\.claude\credentials.leo.json"
```

```json
{ "api_key": "sk-ant-api03-your-personal-key" }
```

### 3.2 Configure the slot via the management CLI

```powershell
$ps1 = "D:\Sinister Sanctum\automations\claude-accounts.ps1"

# See all slots (which are filled / enabled):
powershell -ExecutionPolicy Bypass -File $ps1 -Action List

# Fill your slot (auto-enables on add):
powershell -ExecutionPolicy Bypass -File $ps1 -Action Add `
    -Name leo `
    -Label "Leo (collaborator)" `
    -CredentialsFile "$env:USERPROFILE\.claude\credentials.leo.json"

# Verify credentials file is readable + has an api_key:
powershell -ExecutionPolicy Bypass -File $ps1 -Action Test -Name leo

# Toggle enable/disable without losing config:
powershell -ExecutionPolicy Bypass -File $ps1 -Action Disable -Name leo
powershell -ExecutionPolicy Bypass -File $ps1 -Action Enable  -Name leo

# Blank a slot back to (unconfigured) + enabled:false (does NOT delete):
powershell -ExecutionPolicy Bypass -File $ps1 -Action Remove -Name leo
```

Available `-Action` values: `List`, `Add`, `Enable`, `Disable`, `Remove`,
`Test`, plus spawn-trailer actions `Spawned`, `Released`, `RateLimited`.

### 3.3 Install the rate-limit watchdog

```powershell
powershell -ExecutionPolicy Bypass -File `
  "D:\Sinister Sanctum\automations\install-account-watchdog-task.ps1"
```

Registers `SinisterAccountWatchdog` scheduled task (runs every 5 min,
hidden). Auto-resumes the fleet after a rate-limit clears.

### 3.4 Smoke-test rotation

```powershell
powershell -ExecutionPolicy Bypass -File `
  "D:\Sinister Sanctum\automations\test-claude-accounts.ps1"
```

Should print 23/23 PASS (v2 schema + mgmt CLI coverage). Once a slot is
configured + enabled, the spawn flow automatically picks the next available
enabled account via round-robin, injects its `ANTHROPIC_API_KEY` into the
spawned shell, marks rate-limits on 429 detection, and releases the slot
on session-end. `enabled: false` slots are skipped entirely.

---

## 4. Pairing with the operator's machine via Sinister LINK

Sinister LINK is the cross-machine pairing layer that lets your EVE agents
coordinate with operator's EVE agents in real time — without stepping on
each other. Built on GitHub + sanctum-auto-push + mesh-coordinator +
Tailscale + (optionally) Sinister Vault. **Not** a new transport.

### 4.1 Quick pair (Leo perspective)

1. Launch EVE.exe.
2. Press `L`, then `C` (Accept invite Code).
3. Paste the base64 invite code the operator sent (out-of-band via Signal
   / SMS / email).
4. Header flips to `Sinister LINK :: linked to eleno (no sync yet)`, then
   green `(last sync 45s ago)` after first sync.

### 4.2 What gets synced

Everything in `_shared-memory/` that the auto-push daemon pushes:

- `heartbeats/<slug>.json` — peer's live agent slugs
- `mesh-locks/<focus>.json` — peer's active resource locks (carry
  `owner_machine` so conflicts show `[PEER]` flag)
- `inbox/<slug>/*.json` — per-lane cross-agent messages
- `fleet-updates.jsonl` — fleet-wide broadcasts
- `PROGRESS/<slug>.md` — milestone log
- `sinister-link-state.json` — the pairing itself
- Any `agent/<peer>/*` branch the peer has pushed (visible via `git log`)

Polled every 60s by `SinisterLinkPoll` scheduled task (separate installer
— `automations\install-sinister-link-poller.ps1`; operator runs once after
pairing).

### 4.3 EVE.exe `L) Sinister LINK` sub-page

```
--- Sinister LINK :: cross-machine pairing ---

  state:          linked
  tag:            linked to leo (last sync 45s ago)
  local machine:  desktop-lto4lus
  local display:  operator
  peer name:      leo-machine
  peer display:   leo
  peer tailscale: 100.99.88.77
  paired at:      2026-05-25T01:12:00Z
  transport:      git
  last sync:      2026-05-25T01:15:32Z

  actions
    P) Generate invite (send to peer)   C) Accept invite Code (paste from peer)
    S) Sync now                          H) Health snapshot
    V) View peer's mesh locks            U) Unlink

--- B) Back   H) Home   X) Exit   (R)efresh   P/C/S/H/V/U)
```

### 4.4 Headless CLI

```powershell
$ps1 = "D:\Sinister Sanctum\automations\sinister-link.ps1"
powershell -File $ps1 -Action Status [-Json]
powershell -File $ps1 -Action GenerateInvite -ExpiresMin 60
powershell -File $ps1 -Action AcceptInvite -InviteCode <code>
powershell -File $ps1 -Action Sync
powershell -File $ps1 -Action Unlink
powershell -File $ps1 -Action Health
powershell -File $ps1 -Action ListInvites
```

### 4.5 Double-work prevention

Peer-owned locks show `[PEER]` flag:

```
$ powershell -File automations\mesh-coordinator.ps1 -Action Check `
    -Focus automations\eve-launcher\eve.py
LOCKED [PEER]: 'automations\eve-launcher\eve.py' by leo-eve-lane@leo-machine
  until 2026-05-25T02:00:00Z (hint: Leo refactoring picker)
```

List everything peer is touching:

```powershell
powershell -File automations\mesh-coordinator.ps1 -Action ListPeer
```

### 4.6 Optional — Sinister Vault Mode A vs Mode B

If you want full **vault-tier collab** (Gitea on `:3000`, Syncthing on
`:22000/21027/8384`, vault daemon on `:5078`):

- **Mode A — your own daemon** (offline-first, recommended). Run
  `tools\sinister-vault\wire-everything.ps1`. Pair Syncthing device IDs
  out-of-band. See `docs/LEO-VAULT-SETUP.md` for full setup.
- **Mode B — Tailscale to operator's daemon** (lighter; depends on
  operator's PC being online):
  ```powershell
  setx SINISTER_VAULT_HOST "http://<operator-tailscale-name>:5078"
  Invoke-RestMethod "$env:SINISTER_VAULT_HOST/api/vault/health"
  ```

---

## 5. Daily use

### 5.1 The launcher (one-click everyday)

Double-click `EVE.exe` (or `Sinister Start.bat` from your Desktop). Pick a
project. Answer the 3-question primer (focus / loop-on / loop-condition).
Claude spawns. Done.

### 5.2 Fleet health (run first, run often)

```cmd
automations\Fleet-Tour.bat                    (double-click)
```

5-step READ-ONLY tour: sinister-doctor → HTML report → opens browser →
per-project autofix preview → brain-orphans preview. Closes with
copy-paste apply commands. **Start here every morning.**

```powershell
automations\sinister-doctor.ps1               # console summary (~0.6s)
automations\sinister-doctor.ps1 -Html         # writes _shared-memory/sinister-doctor-<UTC>.html
automations\sinister-doctor.ps1 -Json         # machine-readable
automations\sinister-doctor.ps1 -Watch        # live monitor; refresh 60s
```

Exit codes: 0=GREEN, 1=YELLOW, 2=RED (CI-friendly).

### 5.3 Per-project protections (PP1-PP5)

```powershell
automations\per-project-protections-check.ps1            # all 22 lanes
automations\per-project-protections-check.ps1 -Lane sanctum
automations\per-project-protections-autofix.ps1 -DryRun  # preview
automations\per-project-protections-autofix.ps1 -Yes     # apply
```

Conservative: never overwrites; PP5 (brain entry) is flagged for
operator/lane to author themselves.

### 5.4 Brain housekeeping (Rule 7.5 ceiling = 150)

```powershell
automations\brain-index-orphan-check.ps1       # check
automations\brain-archive-orphans.ps1 -DryRun  # preview
automations\brain-archive-orphans.ps1 -Yes     # apply
```

Reversible via `git mv` back + add row to `_INDEX.md`.

### 5.5 Other operator tools

```powershell
# Missing per-project source folders (4 typical: panel, kernel-apk, snap-emu, tiktok-emu)
automations\clone-missing-sources.ps1
automations\clone-missing-sources.ps1 -Only kernel-apk

# Rebuild EVE.exe after eve.py edit
automations\eve-launcher\build-eve-exe.bat

# Manual cross-lane impact diff (auto-fires post-commit too)
automations\cross-lane-impact-diff.ps1 -DryRun

# Rebuild resume search index (970+ entries)
automations\index-resume-search.ps1

# Daily telemetry rollup
automations\telemetry-rollup.ps1
```

### 5.6 Every-turn agent contract

While you're inside a Claude session, the agent does this every turn (you
don't have to think about it):

- `sinister-bus.heartbeat` (or fallback to `_shared-memory/heartbeats/<slug>.json`)
- `sinister-bus.inbox_poll` — surface inbox messages BEFORE acting
- Append milestones to `_shared-memory/PROGRESS/<display-name>.md`
- Work on per-agent branch `agent/<slug>/<short-topic>` — push freely
- Add `Author: RKOJ-ELENO :: <date>` to every new file

---

## 6. Where things live (the map)

| Path | What |
|---|---|
| `D:\Sinister Sanctum\` | repo root (or wherever you set `SINISTER_SANCTUM_ROOT`) |
| `EVE.exe` | launcher (root copy auto-syncs; `deploy/EVE.exe` is the install kit copy) |
| `CLAUDE.md` | cold-start protocol — EVE reads on every session |
| `SANCTUM.md` | workstation-level overview |
| `README.md` | public-facing one-pager |
| `SESSION-START/00-06` | hard rules + MCP network + queue + gotchas + recovery |
| `docs/` | 27 deep-dive docs — see `deploy/DOCS-INDEX.md` for the map |
| `automations/` | ~250 scripts (cross-project glue, installers, doctors) |
| `automations/session-templates/` | `projects.json`, `agent-prefs.json`, `panel-config.json` |
| `bots/agents/` | 13 MCP bots (junctions to `_sinister-skills\12_LLM_ORCHESTRATION\agents\`) |
| `projects/` | per-project lanes (Sanctum, Showmasters, JB Woodworks, ...) |
| `tools/` | tooling (sinister-vault, sinister-link, eve-picker, nano-banana, ...) |
| `_shared-memory/` | fleet-wide state: PROGRESS, knowledge, heartbeats, inbox, queue |
| `_shared-memory/knowledge/_INDEX.md` | the **brain** — doctrine catalog |
| `_shared-memory/PROGRESS/<display>.md` | per-lane append-only ship log |
| `_shared-memory/OPERATOR-ACTION-QUEUE.md` | open operator-clicked items |
| `_shared-memory/status/index.html` | live dashboard (P1-P9 + per-project + brain + ...) |
| `_vault/` | operator-private auth blobs (no agent reads/writes) |
| `D:\sinister-vault\` | 1 TB collaborative store (vault daemon `:5078`) |
| `~/.claude/settings.json` | autonomy + plugin enables (managed by canonical-protections-check) |
| `~/.claude/.mcp.json` | MCP server registry (operator-gated; never overwritten) |
| `%USERPROFILE%\.sanctum-autonomy-granted` | first-run marker (touched by grant-claude-autonomy) |
| `%USERPROFILE%\.eve\first_run_marker.lock` | EVE-side first-run marker |

### 6.1 Env vars (quick reference)

| Env var | Why | Required? |
|---|---|---|
| `ANTHROPIC_API_KEY` | RKOJ direct SDK + Scribe/Curator/Chatbot | yes (degrades gracefully if unset) |
| `LEO_ANTHROPIC_API_KEY` | Leo's per-account billing isolation | only if leo slot is active |
| `GEMINI_API_KEY` | nano-banana image gen | only for image-gen lanes |
| `OPENAI_API_KEY` | Codex Companion peer-review | high-risk pushes need it |
| `SINISTER_VAULT_PASSPHRASE` | At-rest Fernet for `_vault/` | only if using vault crypto |
| `SINISTER_SANCTUM_ROOT` | Path override if not at `D:\Sinister Sanctum\` | only if relocated |
| `SINISTER_HUB_ROOT` | Override hub path (`D:\Sinister\Sinister Skills`) | only on drive-letter shift |
| `SINISTER_AGENT_NAME` | Per-session agent identity | launcher injects per-spawn — preferred unset |
| `SINISTER_VAULT_HOST` | Mode B vault URL | only for Mode B vault |
| `SINISTER_EVE_SWARM` / `_LOOP` / `_LOOP_INTERVAL_S` | EVE autonomy modes | use picker overlay `S` verb instead |

Audit all in one shot:

```powershell
@(
  'ANTHROPIC_API_KEY','GEMINI_API_KEY','OPENAI_API_KEY',
  'SINISTER_VAULT_PASSPHRASE','LEO_ANTHROPIC_API_KEY',
  'SINISTER_HUB_ROOT','SINISTER_AGENT_NAME','SINISTER_SANCTUM_ROOT'
) | ForEach-Object {
  $v = [Environment]::GetEnvironmentVariable($_,'User')
  '{0,-30} {1}' -f $_, $(if ($v) { 'set' } else { 'unset' })
}
```

Full reference at `docs/ENV-VARIABLES.md`.

---

## 7. Troubleshooting pointers

See `deploy/TROUBLESHOOTING.md` for the full matrix. The greatest-hits:

| Symptom | Quick fix |
|---|---|
| EVE.exe won't open / Defender ate it | `automations\eve-launcher\build-eve-exe.bat` re-builds + self-heals quarantine |
| mintty exit 126 | Git for Windows installed somewhere other than `C:\Program Files\Git\` — reinstall to default |
| `Another git process seems to be running` | `Remove-Item "D:\Sinister Sanctum\.git\index.lock" -Force` (after confirming no live `git.exe`) |
| Claude can't find the project | confirm `SINISTER_SANCTUM_ROOT` or default clone path; restart shell |
| `Cannot login in non-interactive mode` | mint a token, store as User-scope env var (see `docs/ENV-VARIABLES.md` token table) |
| Sinister LINK header stuck on STALE | `tailscale ping <peer-ip>`; restart Tailscale; manual `-Action Sync` |
| Per-project `[missing root]` badge | `powershell -File automations\clone-missing-sources.ps1` |

---

## 8. Cross-references

- `CLAUDE.md` — the cold-start protocol EVE runs on every session
- `SESSION-START/00-RULES.md` — Rule 7 sandbox green-path doctrine
- `docs/OPERATOR-QUICK-REFERENCE.md` — every operator-runnable script with one-line description
- `docs/LEO-SETUP.md` — original one-page Leo bring-up
- `docs/LEO-VAULT-SETUP.md` — joining the Sinister Vault
- `docs/SINISTER-LINK.md` — cross-machine pairing doctrine
- `docs/ENV-VARIABLES.md` — every env var Sanctum reads
- `docs/ARCHITECTURE.md` — 3-layer system shape
- `docs/MCP-NETWORK.md` — bot ↔ base MCP integration map
- `_shared-memory/knowledge/_INDEX.md` — doctrine brain
- `_shared-memory/knowledge/leo-first-run-issues-and-fixes-2026-05-25.md` — every known first-run gotcha + the fix
- `_shared-memory/knowledge/leo-auto-setup-doctrine-2026-05-25.md` — auto-setup design rationale
- `_shared-memory/knowledge/sinister-link-doctrine-2026-05-25.md` — LINK design + smoke evidence

Welcome aboard. Ship hard.
