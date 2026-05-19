# Sinister Vault

> **Author:** Sinister Sanctum SV-A agent (Claude) :: 2026-05-19

The Sinister Vault is a 1 TB soft-quota storage reservation at
`D:\sinister-vault\` plus a tiny FastAPI daemon (port **5078**) that
monitors usage, exposes per-subtree breakdowns, and maintains a unified
audit log every other Sanctum storage citizen (Gitea, Syncthing, the
Vault MCP server) writes into.

## Tree

```
D:\sinister-vault\
├── repos\          ← Gitea data-dir            (owner: SV-B)
├── sync\           ← Syncthing shared folder   (owner: SV-C)
├── snapshots\      ← daemon's periodic snapshots (POST /api/vault/snapshot)
├── audit\          ← daemon's audit log (one YYYY-MM-DD.jsonl per UTC day)
├── accounts\       ← multi-account profiles    (owner: SV-E)
├── _quota.json     ← daemon's running quota state
└── README.md       ← operator overview
```

## Run

Foreground (operator):
```
Sanctum-Vault-Start.bat
```

Headless / auto-start on logon:
```
powershell -ExecutionPolicy Bypass -File install-vault-task.ps1
```

Manual / scripted:
```
pip install -r requirements.txt
python daemon.py --port 5078 --max-gb 1024 --warn-gb 950
```

## HTTP surface (port 5078, localhost only)

| Method | Path                     | Purpose                                                |
| ------ | ------------------------ | ------------------------------------------------------ |
| GET    | `/api/vault/health`      | Liveness, uptime, headline used/cap stats              |
| GET    | `/api/vault/quota`       | Full breakdown by subtree (bytes + human + percent)    |
| GET    | `/api/vault/audit`       | Tail JSONL audit stream (`limit`, `since`)             |
| POST   | `/api/vault/audit`       | Append a custom event (`kind, actor, path, message`)   |
| GET    | `/api/vault/list`        | Sandboxed recursive listing (`path`, `depth`, cap=1000)|
| POST   | `/api/vault/snapshot`    | Robocopy a sub-tree into `snapshots/<UTC-iso>-…/`      |

RKOJ (window-manager on port 5077) proxies `/api/vault/{health,quota,audit}`
so the Sanctum Console's Vault drawer never needs CORS.

## Audit-event shape

One JSON object per line, UTC ISO timestamps:

```json
{"ts":"2026-05-19T06:42:11+00:00","kind":"commit","actor":"leo",
 "path":"/repos/snap-emu/main","message":"feat: …","meta":{}}
```

Canonical `kind` values: `commit`, `push`, `pull`, `sync`, `snapshot`,
`warn`, `error`, `info`. Anything else is accepted but logged at info level.

## Quotas

- `--max-gb` (default 1024): hard cap. Above it, the daemon returns
  **507 Insufficient Storage** from any write endpoint (snapshot, audit
  append). Reads stay live.
- `--warn-gb` (default 950): when total usage crosses this threshold the
  daemon emits a one-shot `warn` event into the audit stream (it
  re-arms once usage drops back below).
- A background asyncio task recomputes usage every 60s and persists
  `_quota.json`.

## Lane discipline

The vault daemon **only** writes to `D:\sinister-vault\audit\`,
`D:\sinister-vault\_quota.json`, and `D:\sinister-vault\snapshots\`. It
never deletes user data, never touches files outside its tree, and
never opens a non-loopback socket.
