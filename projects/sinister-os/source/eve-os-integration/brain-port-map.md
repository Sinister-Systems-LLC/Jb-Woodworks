# Brain Port Map — `_shared-memory/` → `/var/lib/sinister/memory/`

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Scope:** Mapping of the Sanctum brain (Windows host) onto Sinister OS (Layer 1 of the EVE-OS-integration daemon).
> **Companion:** `DESIGN.md` § 3, `scaffold/sinister-eve-mcp-bridge.py` (the prototype that creates these dirs in --dev mode).

The Sanctum brain is the operator's lived memory across every fleet agent. Porting it into Sinister OS is what gives "EVE on the OS" continuity with "EVE on Windows." This file is the authoritative mapping.

## 1. Top-level mapping

| Sanctum (Windows host) | Sinister OS path | Owner | Mode |
|---|---|---|---|
| `_shared-memory/heartbeats/<slug>.json` | `/var/lib/sinister/memory/heartbeats/<slug>.json` | `eve:sinister` | 0640 |
| `_shared-memory/knowledge/*.md` + `_INDEX.md` | `/var/lib/sinister/memory/knowledge/` | `eve:sinister` | 0640 / 0750 |
| `_shared-memory/resume-points/<lane>/*.json` | `/var/lib/sinister/memory/resume-points/<lane>/` | `eve:sinister` | 0640 |
| `_shared-memory/inbox/<slug>/*.json` | `/var/lib/sinister/memory/inbox/<slug>/` | `eve:sinister` | 0640 |
| `_shared-memory/cross-agent/*.md` | `/var/lib/sinister/memory/cross-agent/` | `eve:sinister` | 0640 |
| `_shared-memory/PROGRESS/<lane>.md` | `/var/lib/sinister/memory/PROGRESS/<lane>.md` | `eve:sinister` | 0640 |
| `_shared-memory/operator-utterances.jsonl` | `/var/lib/sinister/memory/operator-utterances.jsonl` | `eve:sinister` | 0640 |
| `_shared-memory/DIRECTIVES.md` | `/var/lib/sinister/memory/DIRECTIVES.md` | `root:sinister` | 0640 (read-only to eve) |
| `_shared-memory/WORK-TOWARD.md` | `/var/lib/sinister/memory/WORK-TOWARD.md` | `root:sinister` | 0640 |
| `_shared-memory/OPERATOR-ACTION-QUEUE.md` | `/var/lib/sinister/memory/OPERATOR-ACTION-QUEUE.md` | `eve:sinister` | 0660 (operator writes too) |

## 2. Per-slot read/write/sync detail

For each slot: what reads it, what writes it, when, how often, and how it syncs to the optional vault mirror.

### 2.1 `heartbeats/<slug>.json`

| Aspect | Detail |
|---|---|
| **Reader** | EVE daemon `/health`, the `eve status` CLI, any app polling for fleet liveness. |
| **Writer** | Every registered app on `POST /v1/heartbeat` (slug + payload). Daemon serializes. |
| **Cadence** | One write per app per heartbeat interval (default 60 s). Reads on demand. |
| **Sync** | **Local-only.** Heartbeats are machine-specific; mirroring would be misleading. |
| **Retention** | Last-write-wins. Stale (> 5 min) flagged as DEGRADED in `/health`. |

### 2.2 `knowledge/`

| Aspect | Detail |
|---|---|
| **Reader** | EVE daemon at LLM-context-build time; `eve memory-get knowledge/<file>.md` from CLI; the LLM through tool-use. |
| **Writer** | EVE daemon when it learns a new doctrine; operator via direct edit; sync from Sanctum on bootstrap. |
| **Cadence** | Bursty. Days of read-only operation, then a write burst when a new doctrine lands. |
| **Sync** | **Vault-mirror (both ways).** The brain is the operator's lived knowledge — should follow him across machines. Conflict resolution: last-write-wins + the vault keeps a `.history/` per file. |
| **Retention** | Forever. The brain is append-mostly. |

### 2.3 `resume-points/<lane>/<ts>.json`

| Aspect | Detail |
|---|---|
| **Reader** | EVE daemon on cold-start (most-recent per lane), then on operator request via `eve memory-get`. |
| **Writer** | EVE daemon every time a lane closes a session OR every N minutes of activity. |
| **Cadence** | Frequent during active sessions (every few minutes). Idle when no agent runs. |
| **Sync** | **Vault-mirror (one-way: this machine → vault).** Resume points are produced here; we don't pull other machines' resume points into our session. |
| **Retention** | Keep last 20 per lane; older roll into `_archive/` via the existing `clean-resume-points.ps1` pattern ported to bash. |

### 2.4 `inbox/<slug>/<ts>.json`

| Aspect | Detail |
|---|---|
| **Reader** | The receiving slug's agent on `inbox-poll` (Sanctum Rule 9). EVE daemon surfaces unread count via `/health.inbox`. |
| **Writer** | Any agent sending a message — `POST /v1/inbox/send { to_slug, payload }`. |
| **Cadence** | Bursty during multi-agent collaboration; idle solo. |
| **Sync** | **Vault-mirror (both ways).** Inbox is cross-agent; an agent on the laptop should see a message from an agent on the desktop. |
| **Retention** | After read, message moves to `inbox/<slug>/_read/`. After 30 days, `_read/` rotates. |

### 2.5 `cross-agent/<ts>-<topic>.md`

| Aspect | Detail |
|---|---|
| **Reader** | All agents, on demand. Broadcast log. |
| **Writer** | Any agent issuing a broadcast. |
| **Cadence** | A few times per day max. |
| **Sync** | **Vault-mirror (both ways).** Broadcasts must reach the whole fleet. |
| **Retention** | Forever. Search via fulltext index. |

### 2.6 `PROGRESS/<lane>.md`

| Aspect | Detail |
|---|---|
| **Reader** | The operator on review; future EVE sessions on cold-start for context. |
| **Writer** | Each lane's agent appends milestones (append-only, most-recent at top per Sanctum convention). |
| **Cadence** | A handful per active session. |
| **Sync** | **Vault-mirror (both ways).** Operator wants a single timeline across machines. |
| **Retention** | Forever. Rotates to `PROGRESS/_archive/<lane>-YYYYMM.md` once > 300 KB. |

### 2.7 `operator-utterances.jsonl`

| Aspect | Detail |
|---|---|
| **Reader** | EVE daemon on cold-start (last 10 unresolved rows); CLI `eve utterances --tail 10`. |
| **Writer** | EVE daemon on every operator interaction (voice, chat, CLI `eve say`). |
| **Cadence** | Every operator interaction. |
| **Sync** | **Vault-mirror (both ways).** Operator utterances must persist across machines. Append-only — conflicts resolved by sort-by-ts + dedupe-by-id. |
| **Retention** | Forever. Indexed for grep + future ML training. |

### 2.8 `DIRECTIVES.md` + `WORK-TOWARD.md`

| Aspect | Detail |
|---|---|
| **Reader** | Every agent on cold-start; EVE daemon at LLM-context-build time. |
| **Writer** | Operator + Sanctum master only. Per-lane EVE never writes. |
| **Cadence** | Rare (operator-driven). |
| **Sync** | **Vault-mirror (one-way: vault → this machine).** Authoritative copy lives in the vault / Sanctum. |
| **Retention** | Forever. Version-controlled via the surrounding git repo. |

### 2.9 `OPERATOR-ACTION-QUEUE.md`

| Aspect | Detail |
|---|---|
| **Reader** | Operator on review; every agent on cold-start to surface open rows. |
| **Writer** | EVE daemon on behalf of any agent (`POST /v1/queue/add`); operator on direct edit. |
| **Cadence** | Frequent during active work. |
| **Sync** | **Vault-mirror (both ways).** Operator should see queued items regardless of which machine they were filed from. |
| **Retention** | Forever. Closed rows move to `OPERATOR-ACTION-QUEUE-archive.md` quarterly. |

## 3. Conflict resolution rules

When vault sync is on and the same file is modified on two machines between syncs:

| File type | Rule |
|---|---|
| `*.jsonl` (append-only) | Sort by `ts` field, dedupe by `id`. |
| `heartbeats/*.json` | Last-write-wins (the freshest heartbeat is the only one that matters). |
| `inbox/*/*.json` | Both win (each is a distinct message); the receiver's `_read/` move idempotent. |
| `knowledge/*.md` | Last-write-wins on the file. Pre-sync version archived to `.history/<file>.<ts>.md`. |
| `PROGRESS/*.md` | Merged via three-way diff (vault keeps last-synced version as base). |
| `resume-points/*/*.json` | Per-machine subfolder — `<lane>/<machine>/<ts>.json` — so no conflict possible. |
| `OPERATOR-ACTION-QUEUE.md` | Merged via three-way diff; on conflict, daemon writes both versions and flags `OPERATOR-ACTION-QUEUE.conflict-<ts>.md` for operator to reconcile. |

## 4. Bootstrap procedure (first boot of Sinister OS with brain port)

The `sinister-eve-postinstall` script (ships with the package) runs once:

```
1. install -d -m 0750 -o eve -g sinister /var/lib/sinister/memory
2. for sub in heartbeats knowledge resume-points inbox cross-agent PROGRESS:
       install -d -m 0750 -o eve -g sinister /var/lib/sinister/memory/$sub
3. touch /var/lib/sinister/memory/operator-utterances.jsonl
4. if [[ -n "$SINISTER_VAULT_URL" ]]; then
       sinister-vault pull --into /var/lib/sinister/memory --paths knowledge,DIRECTIVES.md,WORK-TOWARD.md,operator-utterances.jsonl,cross-agent
   fi
5. systemctl enable --now sinister-eve.service
```

After bootstrap the daemon owns the dir; nothing else writes to it except via the daemon's REST surface (or the operator with `sudo -u eve`).

## 5. What we deliberately do NOT port

| Sanctum thing | Why not |
|---|---|
| `_shared-memory/_archive/` | Historical; the Sanctum git repo is the canonical history. Vault sync can include it on operator request. |
| `_shared-memory/heartbeats/test-os.json` | Test fixture; lives in Sanctum only. |
| `_shared-memory/forge-bridge-token.txt` | Sanctum-only IPC token; Sinister OS has its own. |
| `_shared-memory/canonical-protections-violations.log` | Sanctum self-audit log; the OS daemon emits its own to journald. |
| `agent-prefs.json` / `panel-config.json` | Sanctum-host UI prefs; replaced by `~/.config/sinister-panel/` on the OS. |

## 6. Verification

After bootstrap completes:

```
$ ls -la /var/lib/sinister/memory/
$ stat -c '%U:%G %a %n' /var/lib/sinister/memory/*
$ curl -s http://127.0.0.1:7331/v1/memory/list?prefix=knowledge | python -m json.tool | head -30
$ curl -s http://127.0.0.1:7331/health | python -m json.tool
```

Expected: every subdir owned by `eve:sinister`, mode 0750; knowledge list returns the ported brain entries; health reports `memory_root: /var/lib/sinister/memory`.
