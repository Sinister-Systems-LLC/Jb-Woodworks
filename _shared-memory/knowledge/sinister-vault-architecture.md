<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Sinister Vault — 3-tier collaborative storage layer (repos + sync + snapshots + multi-account + MCP)

**Slug:** sinister-vault-architecture
**First discovered:** 2026-05-19 06:50 by Sinister Sanctum master agent (Claude)
**Last updated:** 2026-05-19 06:50 by Sinister Sanctum master agent (Claude)
**Status:** fixed
**Tags:** vault, storage, gitea, syncthing, mcp, multi-account, collaboration, leo, sanctum-purple, rkoj

## Problem

Operator and Leo need to work on the same projects, on different machines, without stepping on each other's files (git push races, lost notes, no audit of who pushed what). GitHub.com rate-limits, costs scope dances per repo, and has nothing comparable to Tresorit-style real-time file sync. The existing Custodian backup (`tools/sinister-vault/` historical sense) is one-way + drive-loss-only — it does not enable two-way collaboration.

Concrete operator ask (verbatim, 2026-05-19): "reserve 1000 gb of my d drive and make the storage server that connects all with mcp so that we can add that to the exe and leo and i can work on same thing at same time and not interfere with each other ... auto start when pc launch ... simple ui control system using our ui system ... multi google claude account support and a way for leo and i to have different commit each time we upload ... make it so we can sync files like tresorit so leo can see and have the exact same file to work out of."

## Why it happens

Three orthogonal storage needs that no single tool covers cleanly:

1. **Versioned source code** (text, mergeable, per-author commits) — wants git.
2. **Real-time large blobs** (assets, recordings, builds, scratch) — wants Tresorit/Dropbox-style sync.
3. **Point-in-time backups + a single audit log + a single quota** — wants a custom daemon.

Mixing them (git for binaries, sync for source) burns either bandwidth or merge-sanity. Splitting them is the answer; gluing them together under one quota + one audit log + one MCP surface is the new Sanctum-native piece.

Plus per-user billing: every Claude API call needs to land on the right user's invoice. Cannot let Leo's prompts hit operator's Anthropic account or vice versa — separate env-var-scoped API keys per profile.

## Fix or workaround — architecture

```
D:\sinister-vault\                        ← root, 1 TB soft quota
├── repos/        ← Gitea data-dir (operator + leo Gitea identities)
├── sync/         ← Syncthing peer-to-peer shared folder
├── snapshots/    ← daemon-managed point-in-time captures
├── audit/        ← <UTC-date>.jsonl, every commit/push/sync/snapshot/warn
├── accounts/     ← per-user profiles (operator.json, leo.json, _TEMPLATE.json)
├── gitea/        ← container data root (after setup-vault-data-dir.ps1)
└── _quota.json   ← daemon's running usage tally
```

### Tier 1 — Repos (Gitea-backed, port 3000)

- Gitea data-dir relocated under the vault by `tools/sanctum-git/setup-vault-data-dir.ps1` so every byte Gitea writes hits the vault quota.
- `bootstrap-users.py` provisions `operator` (admin) + `leo` (collaborator, `must_change_password=true`) with their SSH keys.
- Commit-as-upload pattern: drop a file → `git add` → `git commit` → `git push` → bytes land in `D:\sinister-vault\gitea\data\repositories\<user>\<repo>.git\` → vault daemon's file-watcher writes a `commit` event to the audit stream → RKOJ Vault drawer surfaces it with the author chip.
- Per-agent branch rule (existing DIRECTIVES 2026-05-19) still holds: every session pushes `agent/<slug>/<topic>`, never to `main`.

### Tier 2 — Sync (Syncthing peer-to-peer, ports 22000/21027/8384)

- Real-time, encrypted (TLS 1.3, device-pinned certs), no central server, no per-seat fees.
- `D:\sinister-vault\sync\` is the shared root. Anything dropped there replicates between paired devices in seconds.
- Conflict policy: never overwrite — keep both as `<file>.sync-conflict-<UTC>-<short-device-id>.<ext>`; merge manually. Rare because round-trip is seconds.
- NOT for source (no merge) — that's what tier 1 is for. Use sync for assets, builds, scratch, design files, recordings.
- LAN-fast (local discovery via UDP 21027); WAN-capable (NAT traversal + relay fallback).

### Tier 3 — Snapshots + audit + quota (vault daemon, port 5078)

- FastAPI daemon at `tools/sinister-vault/daemon.py`, loopback-only, port-distinct from RKOJ's :5077.
- Auto-starts at logon via `Get-ScheduledTask SinisterVault` (registered by `install-vault-task.ps1`).
- HTTP surface (see `tools/sinister-vault/README.md` for full table):
  - `GET /api/vault/health` — liveness + headline used/cap
  - `GET /api/vault/quota` — per-subtree breakdown
  - `GET /api/vault/audit` — tail JSONL audit stream (`limit`, `since`)
  - `POST /api/vault/audit` — append a custom event
  - `GET /api/vault/list` — sandboxed recursive listing
  - `POST /api/vault/snapshot` — robocopy a sub-tree into `snapshots/<UTC-iso>-…/`
- Audit-event shape (one JSON per line, UTC ISO): `{"ts","kind","actor","path","message","meta"}`. Canonical `kind`: `commit`, `push`, `pull`, `sync`, `snapshot`, `warn`, `error`, `info`.
- Background asyncio task recomputes usage every 60s, persists `_quota.json`.
- Heartbeat: touches `_shared-memory/heartbeats/sinister-vault.beat` every 60s. Other agents probe mtime — older than 120s = stuck/dead.

### Quota guardrails

- `--max-gb` (default 1024): hard cap. Above it, write endpoints (`/api/vault/snapshot`, `POST /api/vault/audit`) return **HTTP 507 Insufficient Storage**. Reads stay live.
- `--warn-gb` (default 950): on first crossing, daemon emits a one-shot `warn` event into the audit stream; re-arms on drop below.
- D: free is currently ~4.4 TB so the 1 TB reservation fits comfortably and leaves drive-headroom unaffected.

### Multi-account (per-user billing, identity, accents)

- Each user has a profile at `D:\sinister-vault\accounts\<name>.json` (operator, leo, future).
- Profile fields: `name`, `display`, `anthropic_api_key_env` (NAMED env var — never the key itself), `default_agent_identity`, `default_accent_color`, `default_model`, `gitea_user`, `syncthing_device_id`, `hwid_bound`, `bound_at`, `created_at`, `notes`. Schema: `vault/account/v1`.
- Env-var binding:
  - operator → `ANTHROPIC_API_KEY` (operator's user env)
  - leo → `LEO_ANTHROPIC_API_KEY` (Leo's user env on Leo's machine)
  - future user `alice` → `ALICE_ANTHROPIC_API_KEY`
- The vault daemon NEVER reads or stores the actual API key. It hands the env-var NAME to the calling RKOJ session, which then reads `os.environ[…]` at prompt-build time.
- HWID-bound on first login — operator profile cannot be lifted onto Leo's laptop (or vice versa) without explicit re-binding.

### MCP server (`agents/vault/`)

- Wraps the vault for any Claude session in the fleet. Tools: `commit`, `push`, `pull`, `list`, `search`, `sync_status`, `accounts`, `snapshot`, `audit`, `health`.
- Registered by re-running `install-fleet.ps1` (operator action, pending). Once registered, any agent can read/write the vault via `vault.*` MCP calls without shelling out to git.

### RKOJ workbench integration

- RKOJ (port 5077) proxies `/api/vault/{quota,audit,health,accounts}` so the workbench's **Vault drawer** in the dev-tools rail shows quota meter + recent audit feed + sync status + account picker — no CORS dance.
- Vault drawer surfaces:
  - Quota meter (used GB / max GB, color shifts warn/critical at thresholds)
  - Recent audit (most-recent at top, click → opens repo at sha or sync conflict resolution UI)
  - Sync status (Syncthing peer list + last-sync timestamps)
  - Account picker (switches active identity + accent color + env-var binding)
- Ribbon tile in **AUTOMATE** group: "Commit to Vault" → opens commit-as-upload modal.

### Auto-start

- `install-vault-task.ps1` registers a `SinisterVault` scheduled task triggered at logon (per-user, not cold-boot — daemon needs the user's session to bind to the right profile).
- `vault-daemon.bat` keeps `daemon.py` alive via 3s restart loop with 5/hour inner cap; outer task adds `RestartCount=5, RestartInterval=1min` cap.
- Per-launch log: `tools/sinister-vault/_daemon-logs/vault-<UTC>.log`. Persistent log: `_daemon-logs/daemon.log`. Audit stream: `D:\sinister-vault\audit\<UTC-date>.jsonl`.

### Operator actions still pending (post-shipment)

1. Run `install-vault-task.ps1` (registers SinisterVault scheduled task).
2. Run `install.ps1` in `tools/sinister-vault/syncthing/` (Syncthing service + NSSM wrap).
3. Run `setup-vault-data-dir.ps1` in `tools/sanctum-git/` (moves Gitea data into the vault).
4. Run `bootstrap-users.py --leo-key-file <path>` once Leo's SSH `.pub` is in hand.
5. Re-run `install-fleet.ps1` to register the vault MCP server in `~/.claude/.mcp.json`.

## Discoveries (append-only log, most-recent at top)

### 2026-05-19 06:50 by Sinister Sanctum master agent (Claude)
Initial design + 5-parallel-agent fan-out shipped (SV-A daemon, SV-B Gitea integration, SV-C Syncthing, SV-D MCP, SV-E auto-start + multi-account). D: free ~4.4 TB; 1 TB reservation fits with comfortable headroom. RKOJ already proxies `/api/vault/{quota,audit,health}` (IR-A wiring). Docs swept (this entry + DIRECTIVES prepend + WORKSTATION + SANCTUM + 05-PROJECT-OVERVIEW + 01-NETWORK + tools/_INDEX + PROGRESS) by IR-C this turn.

## Related topics

- [rkoj-workbench-architecture](./rkoj-workbench-architecture.md) — the EXE the vault drawer lives in
- [gitea-self-host](./gitea-self-host.md) — why we self-host the git server the vault wraps
- [per-agent-branch-convention](./per-agent-branch-convention.md) — branch rule that keeps Leo + operator's pushes from racing
- [panel-localhost-routing](./panel-localhost-routing.md) — loopback-first pattern the vault daemon also follows
