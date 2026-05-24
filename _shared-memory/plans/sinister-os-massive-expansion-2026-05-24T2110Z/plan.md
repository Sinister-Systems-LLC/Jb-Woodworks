> Author: RKOJ-ELENO :: 2026-05-24T21:10Z
> Lane: sinister-os
> Branch (cross-lane state): agent/sinister-os-mobile/p0-spec-2026-05-24
> Mode: swarm=on (4 parallel research agents launched), loop=on
> Composes-with prior plans:
>   - `_shared-memory/plans/sinister-os-m5-expand-panel-shell-2026-05-24T2034Z/plan.md` (M5-EXPAND + panel-shell)
>   - `projects/sinister-os/plans/master-plan-2026-05-24.md` (P0→P5 baseline)
>   - `projects/sinister-os/plans/mesh-os-master-plan-2026-05-24.md` (mesh-OS roadmap)

# Plan — Sinister OS MASSIVE EXPANSION (operator interrupt 2026-05-24T~21:08Z)

## Operator directive (verbatim)

> *"complete everything you can in parrallel. make sure i loose no function that i use on this pc. all my agents have the most direct efficent control of things. we need a ui based versioin of this with desktop etc for my main pcs. but we also need a server based system that is all just no ui based and all things you need to see are dontrolled from our sinister web panel. Maybbe we can take this as fasr as creating our own coding languge to make our servers and everything as effcient as they can be. resaerch this in parralle and create a plan to create and test everything i said then we will dockerr test, then laptop then main pc I want to be able to actively change things like ui look add things etc without a reboot. if reboot required then have banner for it. think fo all the rick possibilties we could add"*

## Eight directive components (decomposed)

| # | Directive | Initial response |
|---|---|---|
| 1 | "complete everything you can in parallel" | 4 sub-agents spawned (lang feasibility / Windows feature-parity / hot-reconfig / variant-split) |
| 2 | "make sure i loose no function that i use on this pc" | Feature-parity audit agent (B) running; output → research/feature-parity-audit-2026-05-24.md |
| 3 | "all my agents have the most direct efficient control of things" | Composes with existing CLAUDE.md "EVE-as-OS-shell design constraints" (root-equivalent, sudoers NOPASSWD allowlist, sinister-eve.service privileged daemon) |
| 4 | "UI version with desktop" (main PCs) | New variant: `sinister-desktop` — Hyprland + Sinister Panel kiosk + native apps (Steam, IDEs) |
| 5 | "server-based, NO UI, controlled from Sinister Web Panel" | New variant: `sinister-headless` — multi-user.target only, panel served on mesh |
| 6 | "create our own coding language" | Agent A returned VERDICT: PARTIALLY PURSUE — Janet embed + CUE schema DSL, no full new compiler. Ship Janet-in-EVE first (week 1), defer `.sin` config DSL until 20+ services |
| 7 | "test docker → laptop → main PC" | Three-phase rollout: P0a docker-test → P0b laptop VM-test → P0c main-PC dual-boot test (each operator-gated) |
| 8 | "live UI change without reboot + reboot banner" | Hot-reconfig pipeline (agent C running): inotify config watcher + change-classifier + banner emitter at /var/lib/sinister/reboot-required.json |

## Plan (12 ITERS — loop mode continues)

### ITER 8 — DONE this turn (interrupted from prior plan's iter 6/7)

- Operator utterance logged + this plan written.
- 4 research agents spawned (A: lang, B: Windows-parity, C: hot-reconfig, D: variant-split).
- Agent A returned (Janet+CUE recommendation).

### ITER 9 — Ship two variant compose overlays (depends on agent D output)

- `source/docker-stack/compose.desktop.yml` — desktop variant overlay (X11/Wayland forward / audio bridge / controller passthrough).
- `source/docker-stack/compose.headless.yml` — headless variant overlay (no GUI services; explicit `sinister-mode=headless` env).
- `source/docker-stack/eve` patched with `eve mode get|set desktop|headless`.

**Gate:** yaml parse + `validate-merge.sh` 0 FAIL across all 8 overlays.

### ITER 10 — Reboot-banner MVP pipeline (depends on agent C output)

- `source/sinister-control/reboot-required.sh` — write-side; emits to `/var/lib/sinister/reboot-required.json` with reason + ts.
- `source/sinister-control/reboot-banner-watch.sh` — inotify watcher → notifies panel via vault-api KV at `mesh/banner/reboot-required`.
- `source/sinister-control/hot-reconfig-classifier.py` — diff classifier: takes pre/post `/etc/sinister/*.toml` snapshot, decides hot vs reboot.
- `source/docker-stack/config/sinister-control/README.md` — pipeline docs.

**Gate:** `bash -n` on shell; `python -m py_compile` on Python; sample diff classified correctly.

### ITER 11 — Janet/CUE language scaffold (research-led; no production code yet)

- `source/sinister-lang/DSL-DESIGN-2026-05-24.md` — designs the `.sin` config format (1-week MVP per agent A) + EVE Janet embed plan.
- `source/sinister-lang/example.sin` — sample service definition.
- `source/sinister-lang/sample-output/` — what the transpiler would emit (systemd unit + compose fragment + JSON).

**Gate:** docs only; no runtime ship this iter.

### ITER 12 — Three-phase rollout doctrine

- `docs/rollout-doctrine-2026-05-24.md` — P0a (docker) → P0b (laptop VM) → P0c (main PC dual-boot). Each phase has acceptance criteria, rollback criteria, operator-gate.
- Reference master-plan-2026-05-24.md § 12 phase board with cross-links to this new doctrine.

### ITER 13 — Feature-parity audit + windows-feature-mapping (depends on agent B output)

- `research/feature-parity-audit-2026-05-24.md` — comprehensive table of what operator uses on Windows + Linux replacement status.
- `docs/no-function-loss-doctrine-2026-05-24.md` — every Windows feature → Linux replacement + status.

### ITER 14 — GitHub-prior-art integration plan

- `docs/integration-phasing-2026-05-24.md` — phase-by-phase plan to consume Bazzite + Hyprland + archiso + kiosk-linux per github-prior-art sweep.

### ITER 15 — End-of-turn: commit + heartbeat + PROGRESS + new resume-point

- Compose all turn deliverables into one commit on `agent/sinister-os-mobile/p0-spec-2026-05-24`.
- Refresh `_shared-memory/PROGRESS/Sinister OS.md` with massive-expansion row.
- Fresh resume-point at `_shared-memory/resume-points/Sinister OS/<utc>.json`.

## "Rich possibilities" brainstorm (operator-prompted)

Sinister OS is the operator-private + AI-first OS. Possibilities unique to having an AI as the shell:

1. **Predictive cache pre-warm** — EVE watches operator's daily-driver routine; prefetches assets/services before request.
2. **Voice-driven workflow recording** — operator dictates "from now on, every Monday 8am, do X" → EVE records, schedules, replays.
3. **Agent-driven backup decisions** — agents evaluate file diff value, decide tier (hot/warm/cold/archive) per object.
4. **Per-app proxy routing** — already scaffolded via `eve proxy` (Layer 3 of geo-mesh anonymity).
5. **AI-guided git rebase** — EVE proposes conflict resolutions; operator accepts/rejects/edits with one keypress.
6. **Cross-machine session resume** — operator closes Hyprland on laptop, opens on main PC — every window restored exactly.
7. **Hot-swap accent token** — operator says "change theme to crimson" → EVE writes `--accent: #dc2626` to skeleton tokens → live propagates to every running UI surface.
8. **Workload migration** — heavy build job runs on NY server transparently; results appear in operator's panel as if local.
9. **Real-time mesh-status overlay** — Hyprland statusbar shows: ⬆ tailnet · ⬇ DoH · 🛡 hardened · 🎮 gamescope · 7 agents alive.
10. **One-keystroke install rollback** — btrfs snapper + `eve rollback` rolls system to last known good in <30 s without reboot.

## STOP CONDITION

Iter 8-15 complete OR genuine blocker hit (npm-install hang in panel-shell / yaml parse fail / merge conflict / operator interrupt). Reboot to ScheduleWakeup only if explicitly needed; cap at 270 s.

## Risk register (per safe-quality-loops doctrine guardrails)

1. **Scope explosion** — operator dumped 8 directives at once. Mitigation: parallel agents handle research; main thread ships scaffolds; commits per iter to avoid losing work.
2. **Plan-vs-disk drift** — prior plan claimed L2+L3 SCAFFOLDED but iters 2-4 had not actually been written to disk. This plan re-verifies disk state before every claim.
3. **Cross-lane contention** — sister agents (sanctum, kernel-apk, mobile) running. Verified non-overlapping at iter 1; this plan stays in `projects/sinister-os/**` + `_shared-memory/**` per sinister-os scope discipline.
4. **Quality degradation signals** (no-bullshit rule 8) — re-check at iter 15: brain row count, PROGRESS size, plans active, docfile count.
