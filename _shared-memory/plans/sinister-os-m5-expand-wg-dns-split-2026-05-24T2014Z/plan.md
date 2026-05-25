> Author: RKOJ-ELENO :: 2026-05-24T20:14Z
> Lane: sinister-os
> Branch (cross-lane state): agent/sinister-os-mobile/p0-spec-2026-05-24
> Mode: swarm=on, loop=on

# Plan — Sinister OS M5 EXPAND: WG fallback + split-horizon DNS + verify-smoke + deep-merge

## RESUME context (from resume-point 2026-05-24T18:42Z + 18:07Z)

- M5 Layer 1 (Tailscale mesh): SCAFFOLDED 17:30Z (compose.mesh.yml, acl.json, MESH-DEPLOY.md, eve mesh CLI, geo-mesh-routing.md Layer 1 flipped).
- M5 Layer 2 (DoH per-node): SCAFFOLDED — compose.doh.yml + cloudflared/config.yml + DOH-DEPLOY.md + eve doh subcommand (verified by grep + Read this turn).
- M5 Layer 3 (per-app proxy CLI): SCAFFOLDED — routes.json + eve proxy CLI + PROXY-DESIGN.md (config-only, no enforcement).
- Tailscaled systemd unit (ISO native path): SCAFFOLDED — `source/iso-build/airootfs/etc/systemd/system/tailscaled.service` + sinister-tailscale-firstboot.service.

**Resume-point queue stale.** Reads suggested L2 + L3 + tailscaled-unit + PROXY-DESIGN were OPEN; on disk-verification they are all SCAFFOLDED. Queue rebased below.

## REVIEW — sibling agents (from heartbeats/)

- `kernel-apk` (20:04Z FRESH): brain hygiene + leak-audit script fix; source-tree blocker. Non-overlapping with sinister-os.
- `sinister-os-mobile` (17:15Z, 3h stale): bluejay kernel clone + sepolicy + cvd budget. Non-overlapping (mobile OS lane).
- `sanctum` (recent): fleet doctrine + mesh-coordinator + auto-update. Composes — provides mesh-coord lock primitive for sinister-os to call before risky edits.

## REVIEW — prior plans for sinister-os lane

- `plans/master-plan-2026-05-24.md` (29 KB): full Sinister OS phase plan P0→P5.
- `plans/mesh-os-master-plan-2026-05-24.md` (20 KB): mesh-OS specific roadmap.
- `SESSION-HANDOFF-2026-05-24T1442Z.md`: prior session handoff w/ 6-item queue (most items now shipped).

## REVIEW — operator utterances this lane

Six unread; ZERO addressed to `sinister-os` slug as a direct ask. One agent-mode-set row (18:05:13Z) flipped swarm+loop on — already acted on (heartbeat carries swarm_mode block). Other rows are `sanctum`/`kernel-apk`/`diagnose`/`test-modes` — surfaced in end-of-turn, NOT executed (per sanctum-scope-discipline; sinister-os-scope mirror).

## PLAN — iterations this turn (loop mode)

### ITER 1 — Deep-merge validation + verify-smokes (no docker daemon needed)
- Compose deep-merge via Python yaml.safe_load: base + hardened + mesh + doh — assert no key-collision under `services.*`.
- Run `bash source/docker-stack/eve mesh verify` — expect exit 0.
- Run `bash source/docker-stack/eve doh verify` — expect exit 0.
- Run `bash source/docker-stack/eve proxy verify` — expect exit 0.
- Run `bash -n source/docker-stack/eve` — expect exit 0.

### ITER 2 — CONTRADICTION-EXPANSION: WireGuard direct-peer fallback overlay
Prior plan: "Tailscale is V1, WireGuard is V2 deferred until free-tier wall." Contradiction: this leaves the mesh single-vendor-fragile. Tailscale control-plane outage = no new peer joins; free-tier device-cap (100) is closer than fleet thinks (operator already runs ~7 nodes + Leo + 3+ phone APK builds + each docker container = 10-15 today).
Ship: `compose.wg-fallback.yml` + `WG-FALLBACK.md` runbook. Profile-gated (`docker compose --profile wg-fallback up`). YAML parse PASS gate.
**Counter-arg log row** in `_shared-memory/counter-arguments.jsonl` explaining why this expansion challenges prior "V2 deferred" stance.

### ITER 3 — Split-horizon DNS doctrine — DoH vs MagicDNS conflict
DoH per-node forwards EVERY query to Cloudflare. Tailscale MagicDNS lives at 100.100.100.100 and answers `.ts.net` suffixes. If both run, the loser depends on `/etc/resolv.conf` order — undefined behavior across NY/FL/laptop nodes.
Ship: `source/docker-stack/DNS-SPLIT-HORIZON.md` — doctrine + concrete `systemd-resolved` config snippet + `cloudflared` per-zone exclude config. Add `DNS-SPLIT-HORIZON.md` ref to `DOH-DEPLOY.md` § Caveats.

### ITER 4 — Compose key-collision deep-merge validator script
Ship `source/docker-stack/validate-merge.sh` — Python-backed yaml deep-merge that flags any service-level key shadowed by an overlay. Idempotent, no docker, runnable in CI.

### ITER 5 — Resume-point + PROGRESS log row + heartbeat refresh
Write fresh resume-point reflecting current truth + open_for_next_iter rebased.

## OPEN-FOR-NEXT-LANE (post-loop carry)

- Bake real Panel via `bake-panel.sh` (blocked on docker daemon up + operator hands).
- Live `tailscale ping` between NY/FL/laptop (blocked on operator account + auth-key + hardware deploy).
- nftables/netns enforcement layer for `eve proxy` (deferred per PROXY-DESIGN.md § 5).
- VM smoke-test of ISO with tailscaled.service enabled (blocked on building the ISO in QEMU).
- M5+ Headscale self-host (deferred until fleet outgrows Tailscale free tier — WG fallback this turn buys runway).

## STOP CONDITION

Queue (iters 1-5) empty OR ScheduleWakeup-eligible blocker hit (docker daemon, operator hands, build failure I can't fix in-turn). Composes with no-bullshit rule 8 (quality-degradation signals): if any iter introduces parse-fail / regression in `eve verify` / contradiction-cascade, STOP + consolidate.
