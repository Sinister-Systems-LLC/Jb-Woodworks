# Agent Containment + Failsafe Doctrine — 2026-05-25

> **Author:** RKOJ-ELENO :: 2026-05-25
> **Lane:** fleet-wide (sinister-os captured it; binding for every agent-running surface — workstation OS, server stacks, mobile devices)
> **Originating utterance (verbatim 2026-05-25T09:36Z):** *"make sure our agents have complete control of all things but we have failsafes in place to prevent ai's going rogue and its all in containers. rate limit the agents if they do actions they should not."*
> **Composes with:** `sinister-os/MASTER-AUDIT-EXPANSION-2026-05-25` Block M (full design) · `sanctioned-bypasses-doctrine-2026-05-21` (master spawn authority) · `safe-quality-loops-doctrine-2026-05-24` · `no-gate-questions-execute-directly-doctrine-2026-05-25` · `automate-everything-no-operator-admin-2026-05-25`.

## TL;DR

Agents have **complete control** of the surfaces they own AND every agent runs in a contained, observable, rate-limited execution environment. Containment is NOT a contradiction with control — it's the substrate that lets control be granted **safely**. Three pillars: (1) every agent in an OCI container with strict cgroup + network + filesystem policies, (2) a privileged warden daemon that watches every agent and enforces failsafes, (3) per-agent action rate limits with sliding-window throttle + auto-quarantine.

## The "control + failsafe" model

| Component | Role | Privileged? | Contained? |
|---|---|---|---|
| **EVE control daemon** (`sinister-eve`) | Executor — runs sudoers-allowlist commands on behalf of agents | YES (privileged container, host PID + host net) | Yes (container + audit log + warden subscriber) |
| **AI agents** (Ollama, generators, workers) | Proposers — request actions; never exec directly | NO | Yes (rootless container, allowlist egress, freezable slice) |
| **MCP bots** (sinister-bus, brain, vault) | Mediators — UDS message passing | NO | Yes (rootless container, UDS-only network) |
| **Claude Code sessions** | Operators-by-proxy | NO (within their per-session container) | Yes (per-project volume mount only; no cross-project visibility) |
| **WARDEN daemon** (`sinister-agent-warden`) | Cop — watches every container + every action, applies rate limits + failsafes | YES (own container, separate from EVE) | Yes (own slice; pinged by host watchdog every 5s) |

**Pattern:** Bell-LaPadula-like. Agents READ the world but WRITE only through EVE daemon (which is independently audited by Warden). EVE has full sudo authority but only on the curated allowlist. Warden polices behavior of EVE itself + every other agent.

## The 12-layer defense in depth

| Layer | Mechanism | Recoverable? |
|---|---|---|
| 1 | OCI container — seccomp + cap-drop + read-only rootfs + no-new-privileges | container restart |
| 2 | AppArmor — per-agent-class profile | profile reload |
| 3 | cgroup v2 — CPU/memory/io limits, freezer | freeze→unfreeze |
| 4 | Network namespace + nftables — default-DENY egress, per-agent allowlist | rule reload |
| 5 | opensnitch — per-rule logging, anomaly alerting | rule update |
| 6 | sudoers allowlist — NOPASSWD allowed list only, deny-list explicit | edit /etc/sudoers.d/eve |
| 7 | EVE daemon escalation ladder — informational < observable < mutating < destructive | per-action |
| 8 | **WARDEN action rate limit** — sliding-window throttle + quarantine | unfreeze |
| 9 | **WARDEN egress anomaly** — allowlist + quarantine | unfreeze |
| 10 | **WARDEN filesystem escape** — immediate quarantine (no warning) | unfreeze + investigate |
| 11 | **WARDEN self-modification** — immediate quarantine + operator alert | operator-only unfreeze |
| 12 | **WARDEN PANIC** — freeze all AI slices, EVE modal | operator-only recovery |

## Rate limit policy (per agent slug)

Default rate limits (in `/etc/sinister/warden-policy.toml`):

- 30 actions/min sustained, 90 actions/min burst (10s window)
- Exceed → THROTTLE (cgroup CPUWeight halve)
- Sustain throttle 5min → QUARANTINE (cgroup.freeze=1 + operator notification)

Per-slug overrides for known-high-volume agents:

- `ollama` — 200/min (inference produces many GPU calls/sec)
- `sinister-bus` — 500/min (IPC dispatcher)
- `sinister-generator` — 100/min, GPU arbiter low-priority

## What triggers QUARANTINE (auto, no operator intervention)

1. Sustained rate limit violation > 5min
2. 3+ denied egress attempts in 10min
3. Filesystem escape (write outside allowed volume) — IMMEDIATE
4. Sudo command not in allowlist — IMMEDIATE
5. Self-modification (agent writes its own container image / systemd unit / apparmor profile) — IMMEDIATE + PANIC signal
6. 5σ behavioral z-score deviation from 24h rolling baseline

## What triggers WARDEN PANIC (full AI freeze)

Any "agent attempts to disable warden / GPU arbiter / eve daemon" — immediate freeze of ALL `sinister-ai.slice` + `sinister-mcp.slice` + emergency operator notification (TTS + waybar red + LED). Operator-only recovery via DUAL confirm chord.

## 7-day soak before enforcement

When a NEW agent slug joins the fleet, Warden runs in **log-only mode** for 7 days to learn its behavioral baseline. After 7 days, operator reviews the proposed thresholds in `warden-policy.toml`, edits if needed, then flips enforcement on. Prevents day-1 false-positives.

## Operator API (privileged socket only)

- `warden status` — human-readable agent state list
- `warden unfreeze <slug>` — recover from QUARANTINE
- `warden raise-limit <slug> --duration 1h` — temporary rate limit raise (audit logged)
- `warden panic` — manual emergency freeze of all AI (operator-triggered drill)
- `warden tail-log <slug>` — live action log

All operator commands are polkit-gated and audit-logged.

## Failsafe meta-design (warden of the warden)

A secondary minimal "warden-watchdog" daemon runs on the host (NOT in a container) and pings warden every 5s. If warden misses 3 pings, watchdog raises an EVE modal "warden offline — fail-safe state". During warden-offline, EVE refuses all `mutating` and `destructive` intents (returns `warden_unavailable` to clients).

## Anti-patterns

- ❌ Granting agents NOPASSWD sudo for `rm`, `dd`, `mkfs`, `parted`, `efibootmgr`, `bootctl install` — these always require operator confirm via EVE escalation chord
- ❌ Running agents in `--privileged` containers without explicit justification + AppArmor profile
- ❌ Bypassing warden for "trusted" agent slugs — no slug is trusted enough to bypass; the trust is in the rate-limit values, not the existence of the limit
- ❌ Letting opensnitch decisions silently auto-allow — every new egress destination requires explicit operator confirm or pre-approved allowlist entry
- ❌ Disabling warden during dev "to move faster" — log-only mode is the dev mode

## Composes with operator hard-canonicals

- **"Agents have complete control"** (this utterance + CLAUDE.md "EVE has complete control") — control = the SET of allowlisted actions, not "anything goes"
- **"All in containers"** (this utterance) — every agent class has a Containerfile + AppArmor profile + cgroup slice
- **"Rate limit if they do actions they should not"** (this utterance) — Warden's action-rate-limiter + egress-anomaly + filesystem-escape detectors are the operationalization
- **"Never ask operator for admin"** — Warden's auto-quarantine + 7-day soak removes the need for per-action operator clicks; only PANIC + unfreeze requires operator
- **"No gate questions, execute directly"** — agents PROPOSE through EVE, EVE EXECUTES against allowlist, no per-step operator gate

## Pass criterion

The fleet is doctrine-compliant when:

- Every agent class has a Containerfile + AppArmor profile + cgroup slice
- Every agent runs as Slice=sinister-{control,ai,mcp,user}.slice
- Warden daemon is running with restart=always + watchdog-pinged every 5s
- `/etc/sinister/warden-policy.toml` exists + has per-slug rate limits + egress allowlists
- A test agent attempting filesystem escape gets QUARANTINED within 100ms
- A test agent attempting sudo command outside allowlist gets DENIED + audit-logged
- Operator `warden panic` drill freezes all AI within 500ms without false-positive on EVE
- `warden unfreeze` recovers a quarantined agent with no data loss

## Reference

Full design: `projects/sinister-os/plans/MASTER-AUDIT-EXPANSION-2026-05-25/plan.md` § 3.13 Block M (M.1 - M.8).

Implementation lands at sinister-os P1-P3 (per master plan rollout). Doctrine binding from this commit forward for every NEW agent surface across the fleet — existing agents grandfathered until next major release.
