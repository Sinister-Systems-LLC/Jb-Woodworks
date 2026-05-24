# Sinister Mesh OS — Service Map (live ports)

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Generated from:** smoke-test 2026-05-24T13:18Z on operator's Docker Desktop 29.1.3.

| Service | Host port | URL | Verified |
|---|---|---|---|
| Sinister Panel (placeholder) | 3081 | http://127.0.0.1:3081/ | ✅ HTTP 200 |
| Gitea (self-hosted git) | 8030 / 8022 | http://127.0.0.1:8030/ | ✅ `{"status":"OK"}` |
| Syncthing (file replication) | 28384 | http://127.0.0.1:28384/ | ✅ HTTP 200 |
| NATS (mesh pub/sub) | 4222 / 8222 | http://127.0.0.1:8222/healthz | ✅ `{"status":"ok"}` |
| Yjs (CRDT websocket) | 1234 | ws://127.0.0.1:1234/ + http /healthz | ✅ `{"status":"ok","service":"sinister-yjs"}` |
| Ollama (local LLM) | 11434 | http://127.0.0.1:11434/ | ✅ `Ollama is running` |
| Vault API (host daemon) | 5078 | http://127.0.0.1:5078/api/vault/health | ✅ (existing daemon — container redundant) |
| Rocket.Chat (self-hosted chat) | 8050 | http://127.0.0.1:8050/ | 🟡 Mongo replset reconfigured; RC restarting |
| Apache Guacamole (remote desktop) | 8060 | http://127.0.0.1:8060/guacamole/ | ✅ HTTP 200 |
| Filebrowser (file viewer) | 8090 | http://127.0.0.1:8090/ | ✅ HTTP 200 |

## Why ports are non-conventional

- Conventional 3000 (Gitea) and 8384 (Syncthing) are taken on this host (existing sanctum-git + Windows excluded port). The Sinister-friendly remap above co-exists with everything else running on the operator's machine.

## How to bring up / tear down

```bash
cd projects/sinister-os/source/docker-stack
docker compose -p sinister-mesh up -d
docker compose -p sinister-mesh ps
docker compose -p sinister-mesh logs -f <service>
docker compose -p sinister-mesh down       # keep data
docker compose -p sinister-mesh down -v    # WIPE data
```

## First-time Gitea setup (manual, ~2 min)

1. Open http://127.0.0.1:8030/
2. The install lock is pre-set, so it skips the wizard.
3. Click **Sign In** → first registration creates the admin user.
4. (Tip: if registration is disabled, create the admin via CLI: `docker exec sinister-gitea gitea admin user create --username operator --password SinisterMesh!1 --email ezekielromero314@gmail.com --admin`)

## First-time Rocket.Chat setup

1. Wait until `curl http://127.0.0.1:8050/api/info` returns JSON (~60-120 s after first start).
2. Open http://127.0.0.1:8050/
3. Setup wizard creates first admin.

## First-time Guacamole setup

1. Open http://127.0.0.1:8060/guacamole/
2. Login: `operator` / `sinister-change-me` (configured in `config/guacamole/user-mapping.xml`)
3. Add a remote-desktop connection (SSH/RDP/VNC) via the admin UI.

## Theme compliance (M2 work)

All web UIs above are currently default-themed. M2 ships `docs/sinister-theme-pack.md` with per-service CSS / config that rebrands every UI to match the operator's Sinister Panel screenshot (background `#0e0a1f`, accent `#c084fc`).

## Mobile / phone access (M5 work)

Today: every web service is reachable from any device on LAN via http://<operator-PC-LAN-IP>:<port>/.

Tomorrow (M5):
- Tailscale node on the phone → mesh IP routing
- Sinister mobile app (Android, built off `projects/sinister-kernel-apk/`) bundles WebViews for Panel + Rocket.Chat + Guacamole + EVE chat
