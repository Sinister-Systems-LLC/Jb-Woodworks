# MESH-DEPLOY — Sinister M5 mesh rollout runbook

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Status:** SCAFFOLDED. Compose overlay + ACL template + CLI subcommand land in this commit; no fleet machines are joined yet. The operator runs steps 1–6 below to actually light up the mesh.
> **Composes with:** `docs/geo-mesh-routing.md` (the design), `compose.hardened.yml` (per-node baseline), `compose.mesh.yml` (this overlay), `config/tailscale/acl.json` (ACL template), `eve mesh` (CLI).

## Why this exists

Operator (verbatim 2026-05-24):
> *"i need to be able to be in thailand and download my exe file or have the os on the PC and i can connect to my servers i setup in new york and servers i setup in florida with no speed issues or anything like that. all routing needs to pristine and efficient"*

This runbook is the honest delta between the design (`docs/geo-mesh-routing.md`) and a working mesh: every step the operator runs, with exact commands.

## What's in this commit (verified)

| Artifact | Verification |
|---|---|
| `compose.mesh.yml` — Tailscale sidecar overlay | `python -c "import yaml; yaml.safe_load(open('compose.mesh.yml'))"` exit 0 (see verify section below) |
| `config/tailscale/acl.json` — ACL policy template with `tag:operator`/`tag:server`/`tag:agent`/`tag:exit` | `python -c "import json; json.load(open('config/tailscale/acl.json'))"` exit 0 (comments are leading-underscore JSON; valid) |
| `MESH-DEPLOY.md` — this file | exists at the path above |
| `eve mesh` subcommand in `eve` CLI | `bash -n eve` exit 0; `eve mesh --help` PASS |

## What the operator runs

### Step 1 — Tailscale account + auth keys

1. Operator opens https://login.tailscale.com/start, signs in via Google/Microsoft/GitHub (Tailscale is free for personal use up to 100 nodes; the Sinister fleet is < 20 nodes).
2. Generate a reusable auth key per node at https://login.tailscale.com/admin/settings/keys :
   - One key for the NY home server (reusable, no expiry within 90 days).
   - One key for the FL home server (same).
   - One **ephemeral** key per dev/laptop/phone (so a lost device drops off the tailnet automatically).

### Step 2 — Apply ACL policy

1. Open https://login.tailscale.com/admin/acls .
2. Paste the contents of `config/tailscale/acl.json` (the Tailscale admin UI tolerates the leading-underscore `_comment*` fields and strips them on save).
3. Save. The ACL becomes active immediately for every future node.

### Step 3 — Bring up the mesh sidecar on a Linux node (e.g. the NY home server)

```bash
# On the NY home server, in the sinister-os checkout:
cd projects/sinister-os/source/docker-stack

# Per-node env (NY is an exit node; FL is too; the laptop is not):
export TS_AUTHKEY=tskey-auth-...       # paste the NY auth key from step 1
export TS_HOSTNAME=sinister-mesh-ny
export TS_EXTRA_ARGS="--advertise-exit-node --advertise-tags=tag:server"

# Bring up the stack with hardening + mesh overlays
docker compose -f docker-compose.yml -f compose.hardened.yml -f compose.mesh.yml up -d

# Or via the CLI shortcut:
./eve mesh up
```

### Step 4 — Verify peer-to-peer connectivity

```bash
# From the NY server:
docker exec sinister-tailscale tailscale status
docker exec sinister-tailscale tailscale ping sinister-mesh-fl

# From the laptop (running native Tailscale client — see Windows path below):
tailscale status
tailscale ping sinister-mesh-ny
```

Acceptance: `tailscale ping` returns `direct` (P2P) or `via DERP` (relayed). Both work; direct is faster.

### Step 5 — Toggle exit-node from the laptop (the Thailand scenario)

```bash
# On the laptop (Linux/macOS):
tailscale up --exit-node=sinister-mesh-ny
curl https://ifconfig.me   # should print the NY home IP

# To return to direct routing:
tailscale up --exit-node=
```

On Windows: the official Tailscale client has a tray-icon menu "Exit node" → pick `sinister-mesh-ny`.

### Step 6 — Measure (replace doc estimates with real numbers)

```bash
# On the NY server, install iperf3 if needed:
sudo apt install -y iperf3 || sudo pacman -S --noconfirm iperf3
iperf3 -s -p 5201

# On the laptop in Thailand:
iperf3 -c sinister-mesh-ny -p 5201 -t 30

# Record TCP throughput + RTT (ping sinister-mesh-ny -c 10) into docs/geo-mesh-routing.md.
```

When step 6 lands with real numbers, the relevant rows in `docs/geo-mesh-routing.md § Honest status summary` flip from PROPOSED to MEASURED.

## Windows host path (operator's Sanctum dev box)

`compose.mesh.yml` uses `network_mode: host` + `cap_add: [NET_ADMIN]` + `/dev/net/tun`. None of these work on Docker Desktop for Windows. The Windows path:

1. Install the official Tailscale Windows client: https://tailscale.com/download/windows
2. Sign in with the same Tailscale account.
3. Pick a hostname (e.g. `sinister-dev-box-zonia`).
4. Tag the device as `tag:operator` via the admin console (`Devices` → pick row → `Edit tags...`).
5. Done. The Sanctum docker stack on this Windows host stays reachable from the tailnet via the regular Tailscale Windows client; the `tailscale` service in `compose.mesh.yml` is **not** brought up on this host.

## Sinister OS path (eventual)

When the ISO bake lands (`source/iso-build/`), tailscaled ships as a real systemd unit on the installed OS — no sidecar needed. The unit file template lives at `source/iso-build/airootfs/etc/systemd/system/tailscaled.service` (added in a future iteration).

## Verification commands (run anywhere; no docker daemon required)

```bash
cd projects/sinister-os/source/docker-stack

# 1. YAML parse of the overlay
python -c "import yaml; yaml.safe_load(open('compose.mesh.yml')); print('mesh overlay parse OK')"

# 2. JSON parse of the ACL template
python -c "import json; json.load(open('config/tailscale/acl.json')); print('acl template parse OK')"

# 3. Bash syntax check of eve CLI
bash -n eve && echo "eve syntax OK"

# 4. Help text renders
./eve mesh --help
```

When docker is up, also:

```bash
# 5. Effective config render with all three overlays
docker compose -f docker-compose.yml -f compose.hardened.yml -f compose.mesh.yml config --services
```

## What's intentionally deferred

| Deferred | Why |
|---|---|
| Headscale self-hosted control plane | Adds a separate Go service to maintain. Doctrine: switch to Headscale only after the operator's "complete anonymity" goal explicitly outranks Tailscale convenience. Tracked in `docs/geo-mesh-routing.md § Option B`. |
| `eve mesh exit-node <name>` automation | Requires API token; M5+ work. Operator uses the Tailscale client tray icon or `tailscale up --exit-node=` for now. |
| ACL policy push-via-API | Same — needs Tailscale API token. Manual paste into admin console for now. |
| WireGuard alternative path | Stays on the bench unless Tailscale free tier limits hit. Doctrine in `docs/geo-mesh-routing.md § Option B`. |
| Per-app proxy routing (`eve proxy`) | Layer 3 of the 3-layer anonymity model. Belongs to a separate iteration; needs polkit/nftables wrapping on the Linux host. |

## What this overlay does NOT change

- Existing stack ports + bindings: unchanged.
- The hardened overlay's `read_only` / `cap_drop` settings: unchanged for the other 13 services.
- Operator's existing Tailscale account (if any): unchanged — this overlay joins as a new node.

## End-of-runbook honesty ledger

- `compose.mesh.yml` validated by YAML parse, **not** verified end-to-end with a real `docker compose up` against a live Tailscale account.
- `acl.json` validated by JSON parse, **not** tested against Tailscale's ACL evaluator.
- `eve mesh` subcommand syntax-checked, **not** integration-tested against a running tailnet.
- No latency/throughput numbers measured from the operator's actual links — those land when step 6 runs.
- This is M5 **scaffold**, not M5 **deployed**.
