# source/docker-stack/

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Status:** M0 (spec) shipped; M1 (compose stack) shipped 2026-05-24, smoke-test running.

The Sinister Mesh OS foundation stack. Brings up 7 services every Mesh OS node runs locally. Designed so any device (operator PC, Leo PC, dedicated Vault box, future phone edge node) can `docker compose up -d` from this directory and join the mesh.

## What ships up

| Service | Port | Purpose | Image |
|---|---|---|---|
| **gitea** | 3000 (web), 2222 (ssh) | Self-hosted git; replaces GitHub | `gitea/gitea:1.22.6` |
| **syncthing** | 8384 (web), 22000 (sync) | File replication across nodes | `syncthing/syncthing:1.30` |
| **nats** | 4222 (client), 8222 (monitor) | Mesh pub/sub (JetStream enabled) | `nats:2.10-alpine` |
| **yjs** | 1234 | CRDT WebSocket relay for concurrent dev | built from `yjs-server/` |
| **ollama** | 11434 | Local LLM substrate | `ollama/ollama:0.5.7` |
| **vault-api** | 5078 | HTTP wrapper around the file tree + audit log | built from `vault-api/` |
| **panel** | 3080 | Sinister Panel dashboard kiosk | `node:22-alpine` + mounted bundle |

## Bring it up

```bash
cd projects/sinister-os/source/docker-stack
docker compose up -d --build
docker compose ps
```

Expected output: 7 containers, all `running` / `healthy` within ~60 s of pull completion.

## Verify health

```bash
curl -fsS http://127.0.0.1:3000/api/healthz       # gitea
curl -fsS http://127.0.0.1:8384/rest/noauth/health # syncthing
curl -fsS http://127.0.0.1:8222/healthz            # nats
curl -fsS http://127.0.0.1:1234/healthz            # yjs
curl -fsS http://127.0.0.1:11434/                  # ollama
curl -fsS http://127.0.0.1:5078/api/vault/health   # vault-api
curl -fsS http://127.0.0.1:3080/                   # panel
```

All seven should return 200. (Panel returns a placeholder page if `bake-panel.sh` has not been run yet; the placeholder still demonstrates the Sinister purple theme so you know the service is up.)

## What's NOT in this stack (and why)

- **Tailscale / WireGuard** — joining the actual mesh overlay across machines. Per-machine install (out of compose scope); see `docs/mesh-bootstrap.md` (M3).
- **The Mesh dashboard tab** — Panel UI work (M2; Sinister Panel lane adds the `/mesh` route).
- **EVE daemon** — single-machine OS work (P3 from `master-plan-2026-05-24.md`); not mesh-layer.
- **Sinister bot fleet (13 MCPs)** — Python MCP servers; bring up via Sanctum's existing launcher rather than re-containerizing.

## Tearing down

```bash
docker compose down            # stop + remove containers, keep data volumes
docker compose down -v         # ALSO wipe ./data/* (DANGEROUS — loses gitea repos)
```

## Data persistence

All service state lives under `./data/`:

```
data/
├── gitea/        gitea repos, db, ssh keys
├── syncthing/    syncthing config
├── sync/         syncthing-managed sync folders
├── nats/         jetstream message store
├── yjs/          yjs.level CRDT persistence
├── ollama/       ollama model store (can grow large)
└── vault/        vault file tree + audit log + snapshots
```

`./data/` is `.gitignore`'d. Operator must back this up separately (P-M3 will add `restic` automation).

## Doctrine

Per no-bullshit doctrine: every service in this compose file has a healthcheck. Stack is "shipped" only when `docker compose ps` shows all services healthy. Until then, status is `claimed-but-unverified`.
