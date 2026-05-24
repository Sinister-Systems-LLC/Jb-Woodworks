# WG-FALLBACK.md — WireGuard direct-peer escape hatch

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Status:** SCAFFOLDED — yaml + runbook ready. No live tunnel rollout yet (needs operator-generated keys + port-forward).
> **Companion:** `compose.wg-fallback.yml`
> **Composes-with:** `MESH-DEPLOY.md` (Tailscale primary), `DOH-DEPLOY.md` (DNS layer), `HARDENING.md` (security baseline), `DNS-SPLIT-HORIZON.md` (DNS coexistence).

## Why this exists

The primary Sinister Mesh runs on Tailscale (`compose.mesh.yml`). Tailscale is operator-friendly, NAT-traversing, and cheap — but it has three structural risks:

1. **Control-plane single point of failure.** Existing peer-to-peer tunnels keep working for ~24h if the Tailscale control plane goes down, but no new peers can join. A multi-day outage is a real risk.
2. **Free-tier device cap (100).** The fleet already runs ~7 fixed nodes + Leo machine + N phone APK builders + each per-project docker container that joins the mesh. Cap proximity is closer than the master plan assumes.
3. **Single-vendor dependency.** Any future Tailscale pricing, policy, or acquisition shift impacts the entire fleet's mesh layer.

WireGuard direct-peer fallback gives the fleet a zero-control-plane escape hatch: pre-shared public keys, fixed endpoints, no SaaS dependency. Slower to set up; bulletproof once running.

## When to use this overlay

| Scenario | Use WG-fallback? |
|---|---|
| Tailscale working fine, < 50 fleet devices | **No** — Tailscale alone. Less ops burden. |
| Tailscale device-cap approaching | **Yes** — WG-fallback for non-interactive bots; keep Tailscale for operator-facing nodes. |
| Tailscale control-plane outage in progress | **Yes** — emergency cutover; key exchange may be needed via vault. |
| Building Sinister OS native install with no SaaS dependency | **Yes** — bake WG-fallback into airootfs systemd units. |
| Phone APK builders behind CGNAT | **No** — WG needs port-forward; Tailscale's DERP relays still better here. |

## Operator runbook — first-time setup

### 1. Generate keypairs (per node)

On each Linux node (NY server, FL server, laptop, etc.):

```bash
mkdir -p ~/.config/sinister-wg
cd ~/.config/sinister-wg
wg genkey | tee privatekey | wg pubkey > publickey
chmod 600 privatekey
```

On Windows nodes, install WireGuard for Windows (https://www.wireguard.com/install/) and use the GUI key-gen, then export.

### 2. Stash public keys in the Sinister Vault

```bash
# On each node:
HOST=$(hostname -s)
curl -X POST \
  --data-binary @publickey \
  http://localhost:5078/v1/kv/put?key=mesh/wg/${HOST}.pub
```

### 3. Pick fallback subnet addresses

The vanilla WG fallback uses **10.42.0.0/24** to avoid colliding with Tailscale's 100.64.0.0/10 CGNAT space. Assign one IP per node:

| Node | WG address | Endpoint |
|---|---|---|
| NY server | 10.42.0.1/24 | NY-public-ip:51820 |
| FL server | 10.42.0.2/24 | FL-public-ip:51820 |
| Operator laptop (Windows) | 10.42.0.3/24 | dynamic (no listen) |
| Leo machine | 10.42.0.4/24 | dynamic (no listen) |

### 4. Render env on each node

```bash
export WG_PRIVATE_KEY="$(cat ~/.config/sinister-wg/privatekey)"
export WG_LISTEN_PORT=51820
export WG_INTERNAL_SUBNET=10.42.0.0/24
export WG_ALLOWED_IPS=10.42.0.0/24
export WG_SERVER_URL=auto    # uses public IP detection
```

### 5. Bring up the overlay

```bash
cd projects/sinister-os/source/docker-stack
docker compose -f docker-compose.yml \
                -f compose.hardened.yml \
                -f compose.wg-fallback.yml \
                --profile wg-fallback \
                up -d wg-fallback
```

The `--profile wg-fallback` flag is required — without it, `up` skips this overlay entirely (intentional dual-mesh-safety gate).

### 6. Smoke-test

```bash
# In the wg-fallback container:
docker exec -it sinister-wg-fallback wg show

# Expect: interface: wg0 + a `peer:` block per remote node + handshake timestamp recent.

# From the host:
ping -c 3 10.42.0.1   # NY
ping -c 3 10.42.0.2   # FL
```

## Honesty ledger

What this overlay DOES:

- Starts a `linuxserver/wireguard` container with config rendered from env.
- Persists WG state in named volume `sinister-wg-fallback-config`.
- Healthchecks `wg show` every 60 s.
- Profile-gated so it doesn't activate on stock `docker compose up`.

What this overlay does NOT do:

- Auto-generate keys (operator does this once per node).
- Auto-rotate keys (operator runs `wg-rotate.sh` quarterly — NOT YET WRITTEN).
- NAT-traverse for nodes behind CGNAT (use Tailscale's DERP for those).
- Replace Tailscale — both can coexist (belt-and-suspenders mode).
- Manage cross-node DNS — that's `DNS-SPLIT-HORIZON.md`.

## Operator-action gates (M5+ readiness)

1. Decide which subset of fleet nodes get WG-fallback (recommended: NY + FL + Leo + operator laptop).
2. Generate + distribute keys via vault.
3. Open UDP/51820 on NY + FL public endpoints (cloud SG rule or home router port-forward).
4. Run the up-command on one pair (NY ↔ operator laptop) and verify handshake.
5. Roll to remaining nodes.

Until step 5 completes, the file `eve mesh status` continues to report Tailscale state only.

## See also

- `MESH-DEPLOY.md` — Tailscale primary path.
- `DNS-SPLIT-HORIZON.md` — when WG + Tailscale + DoH all run, this doctrine prevents resolver chaos.
- `compose.wg-fallback.yml` — the YAML this runbook drives.
