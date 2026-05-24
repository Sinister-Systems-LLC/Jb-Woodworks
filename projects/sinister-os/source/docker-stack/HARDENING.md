# Ghost-server hardening — compose.hardened.yml

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Operator directive (verbatim):** *"i need all safety features you can offer with still having speed so that each one of my servers is a complete ghost"*
> **Scope:** The always-on baseline. Opt-in paranoia (per-server score, network segmentation, egress-deny, falco, eBPF) layers on later as `compose.paranoid.yml`.

## What this overlay applies

| Field | Effect | Risk it mitigates |
|---|---|---|
| `security_opt: [no-new-privileges:true]` | Process tree cannot gain new privileges via setuid binaries | Container escape via setuid in image |
| `cap_drop: [ALL]` | Drops every Linux capability (chown, dac_override, net_admin, sys_admin, etc.) | Privilege escalation if a process inside the container is compromised |
| `read_only: true` | Root filesystem is mounted read-only | Persistent modification of binaries, dropping a webshell at `/usr/bin/x` |
| `tmpfs: /tmp` | Scratch space for services that need /tmp under a read-only root | Service breakage when read_only is too strict |
| `pids_limit` | Caps total processes per container | Fork bomb DoS |
| `mem_limit` / `cpus` | Bounds memory + CPU | Resource exhaustion DoS |
| `logging.max-size` / `max-file` | Rotates JSON logs at 5–20 MB × 3 files | Log-flood filling disk |

## How to apply

```bash
cd projects/sinister-os/source/docker-stack
docker compose -f docker-compose.yml -f compose.hardened.yml up -d
```

The `-f` flags deep-merge so the base service definition stays intact and these fields layer on. Compose merges arrays additively (cap_drop arrays append), so this overlay is safe to combine with future overlays.

## Verification (no daemon required)

```bash
# Parse the overlay alone
python -c "import yaml; yaml.safe_load(open('compose.hardened.yml'))"

# Merge with base + render effective config
docker compose -f docker-compose.yml -f compose.hardened.yml config --services
docker compose -f docker-compose.yml -f compose.hardened.yml config > /tmp/effective.yml

# Spot-check a hardened field landed
docker compose -f docker-compose.yml -f compose.hardened.yml config \
  | python -c "import sys,yaml; d=yaml.safe_load(sys.stdin); print(d['services']['gitea']['security_opt'])"
```

## Per-service tolerance audit

The Linux-best-practice "drop ALL caps + read-only root + no-new-priv" baseline is universal here. The deltas below explain where `read_only: true` is **NOT** applied and why — these services would break under a read-only root filesystem.

| Service | `read_only` | Mem | CPU | Rationale |
|---|---|---|---|---|
| gitea | ❌ writable | 1g | 1.0 | Git operations write packfiles + temp objects to internal scratch paths outside `/data` volume. Setting read-only requires multiple tmpfs mounts to identify; deferred to a future tighter overlay. |
| syncthing | ❌ writable | 1g | 1.0 | Index rebuilds, ignore caches, badger DB pages write to many subpaths. |
| nats | ✅ read-only | 512m | 0.5 | Pure pub/sub; only state is the JetStream `/data` volume. |
| yjs | ✅ read-only | 256m | 0.5 | LevelDB persistence inside `/app/data` volume; nothing else needs root write. |
| ollama | ❌ writable | 8g | 4.0 | Model downloads, embeddings caches, CUDA scratch. |
| vault-api | ✅ read-only | 256m | 0.5 | FastAPI; serves `/vault` volume read-mostly. |
| panel | ❌ writable | 512m | 1.0 | Placeholder writes `/tmp/panel/server.js`; once `bake-panel.sh` ships the real standalone build, this flips to read-only (with `/tmp` tmpfs already declared). |
| rocketchat-mongo | ❌ writable | 2g | 2.0 | DB engine writes WAL + journal at runtime. |
| rocketchat-mongo-init | ✅ read-only | 128m | 0.25 | One-shot init script; nothing persists. |
| rocketchat | ❌ writable | 2g | 2.0 | Meteor builds + log spool + session cache write inside container. |
| guacd | ✅ read-only | 512m | 1.0 | Proxy daemon; no persistent local state. |
| guacamole | ❌ writable | 1g | 1.0 | Tomcat writes `/usr/local/tomcat/temp` + `/usr/local/tomcat/work` at runtime. |
| filebrowser | ✅ read-only | 256m | 0.5 | DB at `/data` volume + content at `/srv` volume; rest immutable. |

**Read-only services: 6 / 13** (46%). The remaining 7 keep writable root but still gain cap_drop + no-new-priv + pids/mem/cpu/log limits.

## What this overlay does NOT do (intentionally — would hurt speed or operator ergonomics)

| Skipped hardening | Why deferred |
|---|---|
| Custom AppArmor / SELinux profiles | Per-distro complexity; Docker Desktop on Windows uses the default profile which is already restrictive. Linux deploys can layer `security_opt: [apparmor=...]` in a future `compose.paranoid.yml`. |
| User namespace remapping (`userns_mode: keep-id`) | Some images (gitea, ollama) hard-code UID 1000 / root expectations; remapping breaks volume permissions. Per-service opt-in via paranoid overlay. |
| Per-service dedicated networks | Currently every service is on `mesh`. Network segmentation (e.g. `comms-net` vs `data-net`) is M2 work — needs the mesh routing matrix defined first. |
| `--security-opt seccomp=` custom profile | Default Docker seccomp is sufficient for baseline; custom profiles per-service are paranoid-overlay material. |
| Egress firewall (drop unsolicited outbound) | Requires per-container `iptables` rules in a wrapping layer (Cilium / firewalld) or `network_mode: none` + manual NAT. Operator's "still having speed" constraint means we don't add an egress firewall until we have measured the cost. |
| Image content trust / cosign verification | The supply-chain layer. Belongs in a separate doctrine (planned for M4). |

## What the operator can do RIGHT NOW

```bash
# Bring up the hardened stack
cd projects/sinister-os/source/docker-stack
docker compose -f docker-compose.yml -f compose.hardened.yml up -d

# Verify hardening applied to a live container
docker inspect sinister-gitea --format '{{.HostConfig.SecurityOpt}}'    # -> [no-new-privileges:true]
docker inspect sinister-gitea --format '{{.HostConfig.CapDrop}}'        # -> [ALL]
docker inspect sinister-nats --format '{{.HostConfig.ReadonlyRootfs}}'  # -> true

# Verify resource limits land
docker stats --no-stream
```

## Where this composes with

- `docker-compose.yml` — base service definitions (this overlay is a partner, not a replacement)
- `plans/mesh-os-master-plan-2026-05-24.md § M3` — security milestone
- Future `compose.paranoid.yml` — opt-in tighter hardening per server-score
- Future `compose.network-segmented.yml` — splits services across `comms-net` / `data-net` / `mesh`
- Future `compose.eve-isolated.yml` — runs the EVE daemon in a separate gVisor sandbox

## Operator action required: NONE for the baseline

This overlay is opt-in via the second `-f` flag. The base `docker compose up -d` continues to work unchanged.

To make hardening the default, the next iteration can add a `docker-compose.override.yml` symlink to `compose.hardened.yml` (Compose auto-loads `docker-compose.override.yml`), or update the bring-up shortcut in the lane's README.
