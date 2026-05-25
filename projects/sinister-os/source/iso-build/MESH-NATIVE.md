# MESH-NATIVE — Tailscale on the Sinister OS install (systemd-native path)

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Status:** SCAFFOLDED. Files ship in this commit; nothing's been baked into an ISO and nothing's been booted yet.
> **Sibling:** `../docker-stack/compose.mesh.yml` (FLEET-CONTAINERIZED) — same tailnet, different envelope.

## What this is

The M5 mesh has two envelopes:

| Path | Envelope | Use when |
|---|---|---|
| `source/docker-stack/compose.mesh.yml` | **FLEET-CONTAINERIZED** — Tailscale runs as a `tailscale/tailscale:stable` sidecar inside the docker stack. | The host is running the Sinister docker stack and the operator wants tailnet membership tied to stack lifecycle. |
| `source/iso-build/airootfs/etc/systemd/system/tailscaled.service.d/sinister.conf` (this file's companions) | **FLEET-NATIVE** — `tailscaled` is the upstream Arch package's systemd unit, patched by a Sinister drop-in. | The host is a Sinister OS install — the NY/FL home servers, the operator's laptop. No docker dependency. |

Both join the SAME tailnet under the SAME ACL (`config/tailscale/acl.json` in docker-stack). The ACL doesn't care about the envelope.

## Files in this commit

| Path | Role |
|---|---|
| `airootfs/etc/systemd/system/tailscaled.service.d/sinister.conf` | Drop-in override layered on the package's base unit. Sets `TS_USERSPACE=false`, wires `Wants=network-online.target`, calls the firstboot helper as `ExecStartPost`, bumps `RestartSec=10s`. |
| `airootfs/etc/sinister/tailscale-authkey` | Placeholder file (single newline). Operator drops a real `tskey-auth-...` key here before first boot (mode `600 root:root`) OR uses a cloud-init style first-boot pickup. |
| `airootfs/usr/local/sbin/sinister-tailscale-firstboot.sh` | Bash helper (set -euo pipefail). No-op if authkey is empty/absent. Reads optional `TS_EXTRA_ARGS` from `/etc/sinister/eve.toml`. Runs `tailscale up`. Self-deletes the authkey on confirmed join. |
| `packages.x86_64` (patched) | Added `tailscale` to the networking section so `mkarchiso` pulls the package into the ISO. |

## How the ISO bake picks this up

`archiso`/`mkarchiso` copies the entire `airootfs/` tree onto the live ISO root. The drop-in lives at `/etc/systemd/system/tailscaled.service.d/sinister.conf` on the booted system, which `systemd` merges with the package-shipped `/usr/lib/systemd/system/tailscaled.service` automatically. No `systemctl daemon-reload` needed — systemd reads drop-ins on every start.

`tailscaled.service` is **not enabled** by default by the Arch package. To enable on first boot, operator (or a future `sinister-first-boot.sh` line) runs:

```bash
systemctl enable --now tailscaled.service
```

The drop-in's `ExecStartPost` then fires the firstboot helper, which auto-joins iff the authkey file is non-empty.

## How the operator seeds the authkey

Two paths:

1. **Pre-bake:** edit `airootfs/etc/sinister/tailscale-authkey` before `mkarchiso` — every booted instance shares the same (reusable) key. Burn after first boot via the self-delete in the helper.
2. **Per-boot drop:** boot the ISO, mount the install target, write the key to `/etc/sinister/tailscale-authkey` with mode 600, then `systemctl restart tailscaled.service`.

Path 2 is safer for distributing the ISO; path 1 is fine for the operator's own NY/FL boxes.

## What this DOES NOT do (honest deferrals)

- **Does not enable `tailscaled.service` on first boot.** Operator or `sinister-first-boot.sh` does that explicitly — keeps the live ISO mesh-quiet by default.
- **Does not push ACLs.** Same as the docker-stack path — paste `config/tailscale/acl.json` into the admin console.
- **Does not configure exit-node advertising automatically.** Set `ts_extra_args = "--advertise-exit-node ..."` in `/etc/sinister/eve.toml` per node.
- **Does not handle Headscale.** Same caveat as `MESH-DEPLOY.md § Option B`.
- **Has not been smoke-tested on a real boot.** This is scaffold-only — the parent `BAKE-PANEL-NOTES.md` and PROGRESS log will reflect when a real ISO build verifies the wiring.

## Verification gates passed in this commit

- `bash -n usr/local/sbin/sinister-tailscale-firstboot.sh` exits 0 (parse-clean).
- `sinister.conf` is a syntactically valid systemd drop-in: only `[Unit]` + `[Service]` sections, valid directives (`Wants=`, `After=`, `Environment=`, `RestartSec=`, `ExecStartPost=`), `-` prefix on the ExecStartPost path so a no-op exit is non-fatal.
- File-existence on all four delivered paths: confirmed.
- `tailscale` is present in `packages.x86_64` networking block.

## Honesty ledger

- Not booted. Not joined to a tailnet. No `tailscale status` output captured. The wiring is plausible; the proof is the next ISO bake + VM boot.
- The drop-in is intentionally minimal — does not override `ExecStart=` so package upgrades that change the base command continue to work. Only patches behavior `systemd` allows additively.
- The firstboot helper's TOML parse is regex-only (sed). If `eve.toml` ever grows multi-line strings or nested tables for `ts_extra_args`, swap to a real parser. For a single string key this is fine.
