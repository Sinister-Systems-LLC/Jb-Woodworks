> Author: RKOJ-ELENO :: 2026-05-24T20:34Z
> Lane: sinister-os
> Branch (cross-lane state): agent/sinister-os-mobile/p0-spec-2026-05-24
> Mode: swarm=on, loop=on (operator-set 18:05:13Z)
> Composes-with prior plan: `_shared-memory/plans/sinister-os-m5-expand-wg-dns-split-2026-05-24T2014Z/plan.md`

# Plan — Sinister OS M5-EXPAND + PANEL-AS-SHELL (cold-start RESUME+REVIEW)

## RESUME (from resume-point 2026-05-24T18:07Z + 18:42Z + plan 20:14Z)

- M5 Layer 1 (Tailscale): SCAFFOLDED (compose.mesh.yml + acl.json + MESH-DEPLOY.md + eve mesh CLI).
- M5 Layer 2 (DoH per-node): SCAFFOLDED (compose.doh.yml + cloudflared config + DOH-DEPLOY.md + eve doh CLI).
- M5 Layer 3 (per-app proxy CLI): SCAFFOLDED (routes.json + eve proxy CLI + PROXY-DESIGN.md, config-only).
- Tailscaled systemd unit (ISO native path): SCAFFOLDED (source/iso-build/airootfs/etc/systemd/system/tailscaled.service).
- **Prior plan iters 2-4 NOT yet shipped despite plan being written** (verified by on-disk grep: no `compose.wg-fallback.yml`, no `WG-FALLBACK.md`, no `DNS-SPLIT-HORIZON.md`, no `validate-merge.sh`).

## REVIEW — sibling agents (heartbeats/, ts as of 20:34Z)

- `kernel-apk` (20:04Z FRESH) — brain hygiene + leak-audit script; source-tree blocker — NON-OVERLAPPING.
- `sinister-os-mobile` (17:15Z stale) — bluejay kernel clone + sepolicy + cvd budget — NON-OVERLAPPING (mobile lane).
- `sanctum` (20:15Z+ FRESH) — fleet-autostart logon task + drop-link ingest + memory audit vs Ruflo/JCODE/UA/Obsidian; per-lane master-plan scaffolded — COMPOSES (provides mesh-coord lock primitive for risky shared-file edits; provides bot-fleet quick-reference per cold-start).

## REVIEW — prior plans (sinister-os lane)

- `plans/master-plan-2026-05-24.md` (29 KB) — full P0→P5 phase plan (operator-gated transitions).
- `plans/mesh-os-master-plan-2026-05-24.md` (20 KB) — mesh-OS specific roadmap.
- `plans/sinister-os-m5-expand-wg-dns-split-2026-05-24T2014Z/plan.md` — prior /loop plan; iter 1 (deep-merge) done in-doc, iters 2-4 NOT shipped.
- `SESSION-HANDOFF-2026-05-24T1442Z.md` — 6-item queue; M5 mesh item (#6) and panel-bake item (#1) the open survivors.

## REVIEW — operator utterances (this lane scope)

Tail-50 scan; **direct sinister-os asks** still `status:new`:

1. **2026-05-24T12:47:52Z** (slug `test-os`, tags include `sinister-os`,`priority`,`ship-now`,`panel-as-shell`,`docker-test`):
   > *"get this working how i want so we have a perfect operating system to run claude on and be my own open source operating system that i can forever expand that i have complete control of and ai is complete integrated. review github and see what all you can compile from other repos. and complete the entire thing and lets get to testing in docker to all this for me and make everything look like my sinister panel here. grab the exact code from the sinister panel project folder and lets use that and the lets text look as the main OS look. call everything SINISTER and have all our systems direct in the operating system. make sure i have full options i use from my pc like playing steam games and such."*

   **UNADDRESSED to date.** Mesh-infrastructure work has been the lane's recent focus; this operator-direct utterance has NO concrete deliverable yet on disk.

2. **2026-05-24T18:05:13Z** (mode-flip `swarm=on loop=on`) — already-acted; heartbeat carries swarm_mode block.

Other recent utterances (sanctum / kernel-apk / diagnose / test-modes) are out-of-scope per sanctum-scope-discipline (sinister-os mirror): they belong to their owning lanes.

## PLAN — iterations this turn

### ITER 1 — Heartbeat + plan written (DONE this turn)

`_shared-memory/heartbeats/sinister-os.json` refreshed with siblings + plan path.
`_shared-memory/plans/sinister-os-m5-expand-panel-shell-2026-05-24T2034Z/plan.md` written (this file).

### ITER 2 — WireGuard direct-peer fallback overlay (PRIOR-PLAN CARRYOVER)

Prior plan iter 2 spec restored:

- `source/docker-stack/compose.wg-fallback.yml` — WireGuard sidecar profile-gated overlay.
- `source/docker-stack/WG-FALLBACK.md` — when-to-use runbook + key-rotation cookbook.
- Add `eve wg` subcommand (status / verify only; up/down out-of-scope until profile gating tested with daemon up).

**Gate:** `python -c "import yaml; yaml.safe_load(open('compose.wg-fallback.yml'))"` exit 0.
**Why this matters:** Tailscale free-tier device cap (100) + control-plane outage = single-vendor-fragility. Counter-arg log row.

### ITER 3 — DNS-SPLIT-HORIZON doctrine (PRIOR-PLAN CARRYOVER)

`source/docker-stack/DNS-SPLIT-HORIZON.md` — concrete `/etc/resolv.conf` ordering rule, `systemd-resolved` `.ts.net` split-zone config, `cloudflared` per-zone exclude. Cross-link from `DOH-DEPLOY.md § Caveats` + `MESH-DEPLOY.md § Coexistence`.

**Gate:** file exists + reachable from both DOH-DEPLOY.md and MESH-DEPLOY.md (grep verification).

### ITER 4 — `validate-merge.sh` deep-merge collision checker (PRIOR-PLAN CARRYOVER)

`source/docker-stack/validate-merge.sh` — pure-Python yaml backend (no docker daemon). Loads N compose files; deep-merges with last-wins semantics; emits WARN for any `services.<name>.<key>` shadowed by a later overlay, FAIL for incompatible `network_mode` collisions. Idempotent. CI-runnable.

**Gate:** `bash validate-merge.sh docker-compose.yml compose.hardened.yml compose.mesh.yml compose.doh.yml compose.wg-fallback.yml compose.panel-shell.yml` exit 0 with at most WARN-level findings (no FAIL).

### ITER 5 — CONTRADICTION-EXPANSION: panel-as-shell docker scaffold

**Goes BEYOND any prior plan.** Operator's 12:47Z verbatim ask: *"make everything look like my sinister panel here. grab the exact code from the sinister panel project folder and lets use that and the lets text look as the main OS look."*

Prior plans built the OS bottom-up (kernel → compositor → eve daemon → shell). Operator's ask inverts this: **start from the existing Sinister Panel app + Let's Text look, dockerize it as the OS shell, iterate inside docker** — the OS becomes "a hardened Linux that boots into Sinister Panel as the shell." Massively faster to operator-test.

- `source/docker-stack/compose.panel-shell.yml` — overlay pulling `projects/sinister-panel/` (mounted as build context or junction-referenced) as a containerized service exposing the Panel UI on a fixed port for browser-based operator-test of "what the OS shell will look like."
- `source/docker-stack/PANEL-SHELL-DEPLOY.md` — runbook with up-command, ACK of operator 12:47Z utterance, scope ledger (what's panel UI vs what's real OS work).
- Acknowledge utterance 2026-05-24T12:47:52Z via `automations/ack-operator-utterance.ps1` with deliverable pointing at the panel-shell scaffold.
- Counter-arg row: bottom-up-OS-build vs panel-shell-first.

**Gate:** `python -c "import yaml; yaml.safe_load(open('compose.panel-shell.yml'))"` exit 0 + utterance status flips from `new` → `acknowledged`.

### ITER 6 — `eve panel` subcommand + `eve wg verify` patch

Patch `source/docker-stack/eve` to add:
- `eve panel up|down|status|verify` — wraps the panel-shell overlay.
- `eve wg status|verify` — minimal WG status (full up/down deferred to docker-live turn).

**Gate:** `bash -n eve` exit 0 + `eve panel verify` exit 0 + `eve wg verify` exit 0.

### ITER 7 — Refresh PROGRESS + counter-arguments + resume-point

- Prepend new row to `_shared-memory/PROGRESS/Sinister OS.md` with this turn's verified shipments.
- Append 2 rows to `_shared-memory/counter-arguments.jsonl`: (a) WG-fallback challenges "Tailscale-only V1" stance; (b) panel-as-shell challenges "bottom-up OS build" stance.
- Write fresh resume-point via `automations\resume-point-write.ps1 -ProjectKey sinister-os -AgentName sinister-os -Mode resume`.

## OPEN-FOR-NEXT-LANE (post-loop carry)

- Bake real Panel image via `bake-panel.sh` (blocked on docker daemon up + operator hands).
- Live `tailscale ping` between NY/FL/laptop (blocked on operator Tailscale signup + auth-key).
- `tailscale up` smoke for the new Tailscaled systemd unit inside QEMU ISO boot (blocked on building ISO).
- nftables/netns enforcement layer for `eve proxy` (deferred per PROXY-DESIGN.md § 5).
- Live docker-up smoke of compose.panel-shell.yml (blocked on docker daemon up + sinister-panel build context resolution — Windows junction limitations).
- Steam-on-Linux compat audit (deferred to P3+; tracked in master-plan.md § 5 anti-cheat compat table).

## STOP CONDITION

Iter 1-7 complete OR genuine blocker hit (parse-fail in critical file / docker-daemon-required test that cannot proceed / operator interrupt). Re-checked each iter per LOOP MODE rule 6. Composes with `no-bullshit` rule 8: degradation signals (PROGRESS >300 KB, plans >12 active, doctrine with >5 composes-with links, end-of-turn >40 lines) trigger consolidate-instead-of-expand.

## QUALITY GUARDRAILS (per safe-quality-loops doctrine)

1. **Read-or-measure precondition** — every iter starts with a Read tool call to verify on-disk state, not memory.
2. **Reversibility wall** — no edits outside `projects/sinister-os/**` + `_shared-memory/**`. No firmware. No `main` branch direct push.
3. **Scope freeze** — only the 7 iters above; no scope creep.
4. **Idempotency check** — every `.md` + `.yml` + `.sh` created this turn must be re-runnable without side effects.
5. **Diff-before-write** — Read before Edit/Write; Write only for new files.
6. **Heartbeat liveness** — heartbeat refreshed at iter 1 and iter 7 minimum.
7. **Sister-agent coordination** — verified non-overlap with kernel-apk + mobile + sanctum at iter 1.
8. **Operator-interrupt priority** — fresh operator utterances scanned at iter 5; new directives swap queue position.
9. **Compaction watchdog** — end-of-turn ≤ 25 lines.
