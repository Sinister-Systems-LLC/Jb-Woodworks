> **Author:** RKOJ-ELENO :: 2026-05-24

# Ghost-server hardening — narrative + roadmap

> **Operator directive (verbatim 2026-05-24):** *"i need all safety features you can offer with still having speed so that each one of my servers is a complete ghost"*
>
> **Scope.** This doc is the higher-level narrative. The mechanical specifics — every flag, every service tolerance, every `docker inspect` verification command — live in [`source/docker-stack/HARDENING.md`](../source/docker-stack/HARDENING.md). Read that first if you want to deploy the overlay today.
>
> **Companions:** [qol-features.md](qol-features.md) (the operator-facing QoL surface), [geo-mesh-routing.md](geo-mesh-routing.md) (network-layer anonymity), [live-dev-workflow.md](live-dev-workflow.md) (HMR workflow that must coexist with hardening).

## "Ghost server" — definition glossary

| Term | Meaning |
|---|---|
| **Ghost server** | A Sinister service that exposes ONLY the surface the operator chose to expose, runs with the minimum capability set required, leaves no resident traces on the host root filesystem, and cannot be enumerated trivially from outside the mesh. |
| **Always-on baseline** | The hardening that ships by default in [`compose.hardened.yml`](../source/docker-stack/compose.hardened.yml) — cap_drop, no-new-priv, read-only-where-tolerated, resource caps, log rotation. Zero operator-tunable knobs. |
| **Opt-in paranoia** | The next layer in `compose.paranoid.yml` (PROPOSED) — per-container AppArmor profiles, custom seccomp, userns remapping, network segmentation, egress firewall. Operator opts in per-server based on the per-server score. |
| **Per-server score (0–10)** | A computed integer summarising how hard a single service is to attack. See § per-server score below. |
| **Egress-deny** | A firewall stance where a container can RECEIVE on its declared ports but cannot INITIATE outbound connections except to a named allowlist. Sinister applies this to leaf services that should never call home (filebrowser, guacd). |
| **Network segmentation** | Splitting services across `comms-net` / `data-net` / `mesh` so a compromise of one tier cannot pivot laterally to another. |

## Always-on baseline (what ships today)

The full mechanics are in [`source/docker-stack/HARDENING.md`](../source/docker-stack/HARDENING.md). One-line summary of what is applied to every service in the Sinister stack the moment the operator runs:

```bash
docker compose -f docker-compose.yml -f compose.hardened.yml up -d
```

- `security_opt: [no-new-privileges:true]` — setuid escalation blocked
- `cap_drop: [ALL]` — every Linux capability removed (then individually granted back if a service truly needs one; currently zero re-grants in the baseline)
- `read_only: true` where the service tolerates it (6 of 13 services today — see [HARDENING.md per-service tolerance audit](../source/docker-stack/HARDENING.md))
- `tmpfs: /tmp` for the read-only services
- `pids_limit`, `mem_limit`, `cpus` — resource caps
- `logging.max-size` / `max-file` — per-service log rotation

The operator's "still having speed" constraint is honored: zero overlays add per-syscall interception, zero overlays add per-packet firewall rules in the baseline.

## Per-server hardening score (PROPOSED — not yet computed)

A 0–10 integer summarising how hard a given service is to attack. Computed from the flags actually set on the live container (introspected via `docker inspect`), not from what `compose.hardened.yml` claims.

| Bit | Worth | Earned when |
|---|---|---|
| `no-new-privileges` | +1 | `SecurityOpt` contains `no-new-privileges:true` |
| `cap_drop_all` | +1 | `CapDrop` contains `ALL` AND `CapAdd` is empty |
| `read_only_root` | +2 | `HostConfig.ReadonlyRootfs == true` |
| `mem_limit_set` | +1 | `Memory` > 0 |
| `cpu_limit_set` | +1 | `NanoCpus` > 0 |
| `pids_limit_set` | +1 | `PidsLimit` > 0 |
| `log_rotation_set` | +1 | `LogConfig.Config.max-size` present |
| `apparmor_profile_custom` | +1 | `AppArmorProfile` ≠ `docker-default` and ≠ empty |
| `egress_allowlist` | +1 | Container in network with explicit egress rules (proposed via `compose.paranoid.yml`) |

**Today's expected scores (from baseline alone):**

| Service | Score | Why under 10 |
|---|---|---|
| nats, yjs, vault-api, guacd, filebrowser, rocketchat-mongo-init | **8 / 10** | Missing custom AppArmor + egress allowlist |
| gitea, syncthing, ollama, panel, rocketchat-mongo, rocketchat, guacamole | **6 / 10** | All of the above PLUS no `read_only` (service intolerant) |

A future `eve status --hardening` will print this table on demand by parsing live `docker inspect` output. PROPOSED, not built.

## Opt-in paranoia roadmap (PROPOSED)

`compose.paranoid.yml` — applied via a third `-f` flag for operator-gated rollout:

```bash
docker compose -f docker-compose.yml \
               -f compose.hardened.yml \
               -f compose.paranoid.yml up -d
```

What it would layer on (see [HARDENING.md § What this overlay does NOT do](../source/docker-stack/HARDENING.md) for the reasons each is deferred):

1. **Custom AppArmor profiles** per service (Linux deploys only — Docker Desktop on Windows uses the kernel default).
2. **Userns remapping** for services that tolerate it (excludes gitea + ollama which hard-code UID expectations).
3. **Per-tier networks** — `comms-net` for chat / matrix-like surfaces, `data-net` for DB + storage, `mesh` for inter-service.
4. **Custom seccomp** filter narrower than the Docker default.
5. **Egress-deny + named allowlist** — leaf services (filebrowser, guacd) get an egress-deny rule with no allowlist; gateway services (rocketchat, gitea) get a named allowlist (matrix federation, S3 backup).
6. **Image content trust** — `cosign verify` against the Sinister signing key before pull. M4 milestone.

## How "ghost" composes with the other docs

| If you want to … | Read |
|---|---|
| Know exactly what flags are on each service today | [`source/docker-stack/HARDENING.md`](../source/docker-stack/HARDENING.md) |
| Hide the servers from outside the mesh entirely (Tailscale ACLs, exit-node routing) | [geo-mesh-routing.md](geo-mesh-routing.md) |
| Edit the Panel UI live without breaking hardening | [live-dev-workflow.md](live-dev-workflow.md) — `panel-dev` runs unhardened in dev mode; production `panel` runs under hardened overlay |
| Clear container caches without rebooting an agent session | [qol-features.md § 1 soft-reboot](qol-features.md) |

## Honest status

- Always-on baseline: **SHIPPED** ([`compose.hardened.yml`](../source/docker-stack/compose.hardened.yml) exists, parses clean, documented in [HARDENING.md](../source/docker-stack/HARDENING.md)).
- Per-server score: **PROPOSED** — described above; `eve status --hardening` does not yet print it.
- `compose.paranoid.yml`: **PROPOSED** — not on disk yet.
- Network segmentation (`comms-net` / `data-net`): **PROPOSED** — every service still on the single `mesh` network.
- Image content trust (cosign): **DEFERRED to M4**.

## Operator action required: NONE for the baseline

The baseline is opt-in via `-f compose.hardened.yml`. Once the operator confirms the stack still functions with the overlay (every URL in [SESSION-HANDOFF-2026-05-24T1442Z.md § Service status](../SESSION-HANDOFF-2026-05-24T1442Z.md) still returns HTTP 200), we can flip the bring-up shortcut in the lane README to load the overlay by default.
