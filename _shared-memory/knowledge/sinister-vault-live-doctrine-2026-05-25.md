<!-- decay:
  category: preference
  confidence: 1
  reinforcements: 0
  half_life_days: 365
-->
# Sinister Vault LIVE doctrine

> **Author:** RKOJ-ELENO :: 2026-05-25
> **Status:** binding (operator hard-canonical 2026-05-25)

## Operator verbatim

2026-05-25 ~07:08Z: *"i need the sinister link system to work so leo and i can connect our eve's like we talked about. place the sinister vault live and place the entire sinster sanctum there and link to leo over sinister link and auto update that and github. and backup."*

## TL;DR

The Sinister Vault is **LIVE** at `http://127.0.0.1:5078` (FastAPI daemon at `tools/sinister-vault/daemon.py`, vault root `D:\sinister-vault\`, registered via `SinisterVaultDaemon` schtask OR Startup folder fallback). The full Sinister Sanctum repo mirrors into the vault on a 15-min cadence via `automations/sanctum_to_vault_mirror.py` -> `sanctum-mirror/<machine-id>/`. Syncthing replicates `sync/` (including `sync/sinister-link/`) to every paired peer (Leo) LAN<2s / WAN ~5s. GitHub stays as **disaster-recovery mirror only** (already wired via `sanctum-auto-push`); vault is **the live collab channel**.

## Vault as source-of-truth, GitHub as DR mirror

| Property | Vault | GitHub |
|---|---|---|
| Latency | sub-second LAN / ~5s WAN | 30-min auto-push cadence |
| Authority | live working tree + audit stream | append-only history snapshot |
| Failure mode | offline -> Syncthing queues + replays | offline -> 30-min push delay |
| Per-peer scope | machine-tagged (`sanctum-mirror/<host>/`) | repo-wide |
| Audit | unified JSONL stream (`audit/<date>.jsonl`) | git log |
| Cost | 0 (own hardware) | 0 within free tier |

**Rule:** every iteration that lands in operator's working tree must propagate to vault within 15 min AND to GitHub within 30 min. Vault outage does NOT block git pushes; git outage does NOT block vault sync. Both channels are independent.

## 3 transport modes for Sinister LINK

`automations/sinister-link.ps1` already supports `-Transport git|vault|tailscale-direct`. Vault transport is now live via `automations/sinister_link_vault_transport.py`:

| Transport | Mechanism | Latency | Reliability | Use when |
|---|---|---|---|---|
| **git** (default) | sanctum-auto-push every 30 min, peer pulls | 30-60 min | very high (GitHub) | bulk state, history-preserving |
| **vault** (new) | filesystem `sync/sinister-link/<invite-id>/<role>.json` via Syncthing | <5s | high (peer-to-peer) | live coordination, short-lived blobs |
| **hybrid** (recommended) | vault for hot path; git as audit-trail backstop | <5s + 30-min snapshot | very high | production runs |

The hybrid pattern: every vault push ALSO writes a `_shared-memory/sinister-link-invites/<id>.json` row that `sanctum-auto-push` carries to GitHub. If vault transport goes silent, peer falls back to git polling.

## Operator-headroom guardrails (vault daemon)

The daemon is a single uvicorn worker; constrain it so it never starves the operator's interactive session:

- Memory cap: **4 GB RAM** (currently runs ~80 MB at idle; cap enforced via Windows Job Object if usage drifts).
- CPU: **1 logical core** (uvicorn single-worker default; do NOT add `--workers N`).
- Disk: **soft 950 GB warn / 1024 GB hard cap** (existing defaults from `daemon.py`; never raise without explicit operator approval).
- Network: bind **127.0.0.1 only** by default; Mode B exposes via Tailscale ACL, never raw WAN.
- Quota refresh: **60s** background tick (do NOT lower; rapid full-tree walk thrashes disk on big sub-trees).

## 5 anti-patterns

1. **Vault as dumb storage.** WRONG: dropping arbitrary files under `D:\sinister-vault\` and hoping. RIGHT: route writes through `POST /api/vault/audit` or `sync/` (which Syncthing replicates) or `repos/` (Gitea-managed). Off-channel writes do NOT propagate to peers.

2. **Vault out-of-sync with git.** WRONG: assuming vault mirror == git HEAD. RIGHT: vault mirror is a 15-min snapshot of the WORKING tree (including uncommitted changes); git is authoritative for committed history. If they diverge by >30 min something broke in `sanctum-auto-push` or the mirror schtask.

3. **No auth on daemon.** WRONG: opening daemon on 0.0.0.0 with no token. RIGHT: bind 127.0.0.1 by default; Mode B uses Tailscale ACL gating (NOT a substitute for real auth -- add HMAC-bearer headers in v1.1 if exposing beyond tailnet). Currently the daemon trusts loopback; never expose without auth.

4. **No backup retention.** WRONG: assuming Syncthing replication == backup. RIGHT: vault `snapshots/` subtree holds robocopy mirrors (POST `/api/vault/snapshot`); git push handles DR. Two independent channels = real backup.

5. **Vault token leak.** WRONG: committing `_vault/auth-keys-DELIVER-TO-LEO.txt` to git. RIGHT: `_vault/` is gitignored; auth blobs go peer-to-peer via Signal / SMS / encrypted disk hand-off. Any agent that reads `_vault/auth-keys-*` MUST NOT echo it to stdout.

## Pass criterion

From an operator-clean machine (vault not yet provisioned):

1. `cd D:\Sinister Sanctum\tools\sinister-vault && python -m venv .venv && .\.venv\Scripts\pip install -r requirements.txt` -> exit 0.
2. `.\.venv\Scripts\python.exe daemon.py --port 5078` -> daemon binds; `Invoke-RestMethod http://127.0.0.1:5078/api/vault/health` returns `ok:true`.
3. `python automations\sanctum_to_vault_mirror.py --dry-run` -> prints copied count >0.
4. `python automations\sanctum_to_vault_mirror.py` (real) -> exit 0, `_vault\sanctum-mirror\<host>\` is non-empty, JSONL row appended to `_shared-memory\vault-mirror-log.jsonl`.
5. Startup-folder shim (`SinisterVaultDaemon.cmd`) installed -> survives reboot.
6. From Leo's clean machine, follow `deploy/SINISTER-VAULT-LEO-CONNECT.md` -> vault daemon up on his side, Syncthing paired with operator, `sync/sinister-link/<invite>/` round-trip works <30s.

If any step fails: read `tools/sinister-vault/_daemon-logs/*.log`, check `Get-NetTCPConnection -LocalPort 5078`, then read `_shared-memory/vault-mirror-log.jsonl` for the most recent run's error count.

## Composes with

- `_shared-memory/knowledge/sinister-link-doctrine-2026-05-25.md` (the pairing state machine -- vault is one of its 3 transports)
- `_shared-memory/knowledge/sinister-vault-architecture.md` (1 TB store layout: repos/sync/snapshots/audit/accounts subtrees)
- `_shared-memory/knowledge/automate-everything-no-operator-admin-2026-05-25.md` (Startup-folder fallback when schtask elevation refused)
- `_shared-memory/knowledge/no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25.md` (new code in Python; the .cmd Startup shim is the doctrine-sanctioned single-shot bootstrap, not a feature script)
- `_shared-memory/knowledge/single-repo-push-policy-2026-05-25.md` (Sanctum-only pushes to GitHub; vault is the cross-machine sync, not a multi-repo workaround)
- `_shared-memory/knowledge/leo-auto-setup-doctrine-2026-05-25.md` (Leo's vault side complements his Sanctum setup)
- `docs/LEO-VAULT-SETUP.md` (operator-facing one-page intro)
- `deploy/SINISTER-VAULT-LEO-CONNECT.md` (Leo's connect runbook for vault-live state)

## Maintenance

- **Daemon down >120s** -> heartbeat file `_shared-memory/heartbeats/sinister-vault.beat` goes stale -> fleet-monitor surfaces alert. Recovery: re-run Startup shim or `python daemon.py --port 5078`.
- **Mirror exit code != 0** -> JSONL log row has `errors > 0`; tail `_shared-memory/vault-mirror-log.jsonl` and check `stderr` from the schtask run.
- **Quota warn fires** (>950 GB) -> JSONL audit row `kind=warn`; trim `_vault/snapshots/` oldest entries first.
- **Syncthing divergence** -> open `http://127.0.0.1:8384` -> resolve folder conflict files (`*.sync-conflict-*`); operator's copy wins by default.

## Optional v1.1 ideas (do not ship yet)

- Add HMAC-bearer auth on `POST /api/vault/*` so Mode B over Tailscale doesn't depend on ACL alone.
- GET `/api/vault/get` + POST `/api/vault/put` endpoints so the LINK transport doesn't depend on Syncthing filesystem replication (pure-HTTP path).
- Per-peer mirror retention policy (operator keeps Leo's last 7 days; Leo keeps operator's last 30 days).
- `sanctum_from_vault_mirror.py --pull` symmetric helper for Leo to overlay operator's mirror onto his own working tree (read-only fast-forward).
