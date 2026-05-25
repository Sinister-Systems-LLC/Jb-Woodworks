# Sinister Sanctum — Annotated Docs Index

**Author:** RKOJ-ELENO :: 2026-05-25

Every file in `D:\Sinister Sanctum\docs\` with a one-line "what it's for"
and target audience. Use this to pick the right deep-dive for what you're
trying to do.

Audience tags:
- **L** = Leo / new operator onboarding
- **O** = Day-to-day operator reference
- **D** = Developer / agent contributor
- **R** = Reference (read once, link to often)

---

## For Leo / new operators (L)

| Doc | One-line description |
|---|---|
| `docs/LEO-SETUP.md` | **L · R** — one-page bring-up: prereqs, clone, first-run sequence, common pitfalls, verification commands. |
| `docs/LEO-VAULT-SETUP.md` | **L · R** — joining the Sinister Vault for real-time sync (Mode A: own daemon · Mode B: Tailscale to operator's daemon). |
| `docs/LEO-MISSING-SOURCES.md` | **L** — one-command fix when per-project `source/` folders are missing (`[missing root]` badge in picker). |
| `docs/SETUP.md` | **L · O** — original fresh-machine bootstrap (junction projects, activate bots, secret-scrub). |
| `docs/SINISTER-LINK.md` | **L · O** — cross-machine pairing with operator (invite codes, sync, mesh-coord peer flags). |

---

## For day-to-day operator use (O)

| Doc | One-line description |
|---|---|
| `docs/OPERATOR-QUICK-REFERENCE.md` | **O** — every operator-runnable script with one-line description + invocation (Fleet-Tour, doctor, PP checks, brain housekeeping). |
| `docs/RKOJ-OPERATOR-GUIDE.md` | **O** — operator one-pager for RKOJ.exe (2 tabs / ribbon / cycle points / scheduler / popouts / Vault drawer). |
| `docs/WORKBENCH.md` | **O** — RKOJ workbench feature tour (the flagship workstation binary built from `automations/window-manager/`). |
| `docs/DEPLOYMENT.md` | **O** — per-project deploy checklist + table (Panel, RKA, Snap-Signer, EMUs, Kernel-SU). |
| `docs/PANEL-INTEGRATION.md` | **O · D** — how Sinister Panel consumes Sanctum + the live dashboard at snap.sinijkr.com. |
| `docs/THEMED-SESSION-LAUNCHER.md` | **O** — reusable launcher recipe (theming, banner, status pill row). |
| `docs/ROUND-ROBIN-ACCOUNT-ONBOARDING.md` | **O** — multi-account Claude rotation playbook (4-slot starter, infinite per 2026-05-24 doctrine). |
| `docs/MULTI-OPERATOR-COLLABORATION.md` | **L · O** — coordinating Leo + operator + future collaborators (lane ownership, no-collision protocols). |

---

## For developers / agent contributors (D)

| Doc | One-line description |
|---|---|
| `docs/ARCHITECTURE.md` | **D · R** — overall system shape: 3-layer model (bots / projects / shared infra) + data flows. |
| `docs/AGENT-BOOTSTRAP.md` | **D · R** — read-this-first for every fleet agent: roster, MCP tool catalog, memory layout, escalation ladder, sinister-bus comms, hard rules. |
| `docs/AGENT-MESSAGING.md` | **D** — sinister-bus inbox/outbox + `[DELEGATE]` tag protocol + cross-agent JSON schemas. |
| `docs/ALIVE-ARCHITECTURE.md` | **D · R** — the "alive" multi-process model: heartbeats, watchdogs, auto-restart, daemon lifecycles. |
| `docs/BOT-MEMORY-PROTOCOL.md` | **D · R** — how `absorb()` / `learn` / `forget` works in the 13 MCP bots; operator-curated learning protocol. |
| `docs/MCP-NETWORK.md` | **D · R** — bot ↔ base MCP server integration map (19 endpoints when fully loaded). |
| `docs/MCP-NEW-SERVERS.md` | **D** — adding a new MCP server to `~/.claude/.mcp.json` (operator-gated). |
| `docs/MEMORY-CODEC-AND-CRYPTO.md` | **D · R** — token codec + at-rest vault Fernet encryption details. |
| `docs/BRANCH-CONVENTION.md` | **D · R** — `agent/<project-key>/<topic>-<utc-date>` convention + sanctum-push-policy hook (exit 13 on violation). |
| `docs/UI-DESIGN-SYSTEM.md` | **D · R** — `dashboard-skeleton` inheritance, Liquid Glass tokens, 16 primitives, type scale, forbidden patterns. Operator hard-canonical 2026-05-24: every UI EXPANDS the skeleton, never forks. |

---

## Reference / read-once-link-often (R)

| Doc | One-line description |
|---|---|
| `docs/README.md` | Public-facing one-pager — what Sanctum is, layout, install, lane discipline. |
| `docs/ENV-VARIABLES.md` | **R** — every env var Sanctum reads, what each unlocks, exact set command, cross-reference to consumers. The auth table for non-interactive CLI tokens lives here too. |
| `docs/DRIVE-ENCRYPTION.md` | **R** — VeraCrypt container plan for the operator's auth keys + sensitive blobs. |
| `docs/HARDWARE-ROADMAP.md` | **R** — operator's planned hardware additions (multi-GPU, second workstation, Tailscale mesh nodes). |

---

## Quick "I need to do X" lookup

| Goal | Doc |
|---|---|
| Set up a brand-new box | `deploy/README.md` + `deploy/GETTING-STARTED.md` + `docs/LEO-SETUP.md` |
| Add a Claude account | `docs/LEO-SETUP.md` §1.5 + `docs/ROUND-ROBIN-ACCOUNT-ONBOARDING.md` |
| Pair with operator over WAN | `docs/SINISTER-LINK.md` + `docs/LEO-VAULT-SETUP.md` (Mode B) |
| Fix `[missing root]` badge | `docs/LEO-MISSING-SOURCES.md` |
| Audit env vars | `docs/ENV-VARIABLES.md` (quick-check script at bottom) |
| Run fleet health check | `docs/OPERATOR-QUICK-REFERENCE.md` |
| Understand the bot fleet | `docs/AGENT-BOOTSTRAP.md` + `docs/MCP-NETWORK.md` + `docs/BOT-MEMORY-PROTOCOL.md` |
| Build a new UI | `docs/UI-DESIGN-SYSTEM.md` (operator hard-canonical: EXPAND `dashboard-skeleton`, never fork) |
| Deploy a project | `docs/DEPLOYMENT.md` |
| Write an MCP server | `docs/MCP-NEW-SERVERS.md` |
| Recover from session crash | `SESSION-START/05-RECOVERY.md` (in repo root, not docs/) |
| See doctrine catalog | `_shared-memory/knowledge/_INDEX.md` (the brain — 150-entry ceiling) |

---

## Total doc count

- `docs/`: 27 files
- `deploy/`: 4 .md files + `setup.py` + `EVE.exe` + `MANIFEST.txt`
- `SESSION-START/`: 7 files (00-06) — auto-loaded on cold start
- `_shared-memory/knowledge/`: ~140 brain entries (ceiling 150)

Last verified: 2026-05-25.
