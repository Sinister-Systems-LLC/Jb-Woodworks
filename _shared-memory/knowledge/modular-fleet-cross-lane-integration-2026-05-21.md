<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
<!-- SANDBOX-ALERT v1 -->
> **Sandbox handling.** Standing-rule doc; no runtime ops.

> **Author:** Sinister Kernel APK (Claude agent, kernel-apk slug) :: 2026-05-21T13:45Z

# Modular-fleet cross-lane integration — forever-expanding architecture

**Status:** standing-rule (operator directive, append-only)
**Source:** operator chat message to kernel-apk session 2026-05-21T13:43Z (verbatim below)
**Tags:** doctrine, standing-rule, fleet-architecture, modular, cross-lane, integration, sinister-sanctum, sinister-term, rkoj, sinister-panel, kernel-apk, forever-expanding

## Operator verbatim

> "ok take note we have sinister sanctum, sinister term, rkoj workstation, sinister panel and apk agents all running. make sure to keep in mind everything is going to connect to everything im a forver expanding modular approach."

## What this means

Five (5+) concurrent live agents/projects as of 2026-05-21T13:43Z:

| # | Surface | Lane | Role |
|---|---|---|---|
| 1 | **Sinister Sanctum** | master orchestration | the workstation; owns docs, automations, brain, cross-agent coordination |
| 2 | **Sinister Term** | NEW (operator-just-named; agent not yet seen on disk by kernel-apk side) | terminal-shaped tool? — kernel-apk to confirm via inbox poll or operator on next mention |
| 3 | **RKOJ Workstation** | flagship EXE | 2-tab (ADB Devices / Agents) + ribbon + popout + cycle-points + scheduler |
| 4 | **Sinister Panel** | live ops backend | Hetzner-hosted `snap.sinijkr.com`; Prisma + Next.js; cross-lane RKA + accounts + actions |
| 5 | **APK Agents** | kernel-apk lane (this session) | Sinister Detector + sinister-spoofer KPM + Rooting Guide |

(+ snap-emu, tiktok-emu, bumble-emu, library-of-alexandria, snap-signer, eve-mcp, letstext, jokr-global as the broader fleet.)

**Core principle:** *"everything is going to connect to everything in a forever-expanding modular approach."*

## How this shapes design decisions across lanes (rules for every agent)

1. **No siloed contracts.** When you ship an endpoint, schema, or data shape, design it so other lanes can consume without bespoke adapters. Example: kernel-apk's `SpooferConfigPoller` (v0.96.94) consumes a panel-side `/api/phones/<serial>/spoofer-config` row → panel surfaces it to the dashboard → operator + Leo touch it from any surface (RKOJ ADB tab, browser, Sinister Term, mobile via Forge bridge). One source of truth, N consumers.

2. **Composable via the standard surfaces.** New cross-lane work routes through the EXISTING fleet surfaces — don't invent parallel infrastructure:
   - **Cross-agent inbox** (`_shared-memory/cross-agent/<UTC>-<sender>-to-<receiver>.md`) for async lane-to-lane handshakes.
   - **Brain** (`_shared-memory/knowledge/<slug>.md` + `_INDEX.md`) for durable architectural knowledge.
   - **Resume-points** (`_shared-memory/resume-points/<project>/<UTC>.json`) for surgical session pickup.
   - **Forge bridge** (`:5078` REST/SSE) for mobile + cross-surface access to any project's state.
   - **Vault MCP** (`mcp__vault__*`) for collaborative storage that operator + Leo can both touch.
   - **Sinister-bus inbox / heartbeat / runlog** for live-update coordination per Rule 9.

3. **Plan for the next surface to arrive.** When designing a feature, ask: "what would Sinister Term need to consume this?" Even if Sinister Term doesn't exist on your lane yet, designing for it costs nothing today AND prevents a fork tomorrow.

4. **No cross-lane assumptions about state shape.** If your project writes a row that other lanes will read, version it (`config_version`, `schema_version`, etc.) so consumers can graceful-degrade on shape drift. The 2026-05-20 panel heartbeat-500 schema-drift incident is the cautionary tale: brittle assumptions about Prisma column presence broke every consumer.

5. **The brain compounds.** Every cross-lane fix, every architectural finding, every reusable pattern gets a knowledge entry. Future agents (including new lanes that haven't been built yet) read it before duplicating work.

6. **Forever-expanding ≠ forever-rewriting.** Modular means you ADD lanes that compose with the existing surfaces; you don't replace the surfaces every time a new project arrives. The cold-start contract + brain + cross-agent inbox + resume-points are the LOAD-BEARING substrate; everything else snaps in.

## Specific touchpoints kernel-apk owns and should keep cross-lane-clean

- **Detector APK heartbeat** → panel `/api/devices/heartbeat` (+ `/api/phones/heartbeat`). When extending the body (e.g. the `device_state` field per 2026-05-21T1330Z recovery thread), the schema add must be optional-from-old-clients so RKOJ / Sinister Term / future consumers don't break.
- **SpooferConfigPoller** → panel `/api/phones/<serial>/spoofer-config`. Already version-gated. RKOJ + Sinister Term + future surfaces can consume the same row.
- **Cross-app data reads on KSU+SUSFS** → `su -M -c` pattern. Broadcast as a fleet-wide rule (`ksu-susfs-app-mount-namespace-isolation-2026-05-20`) so siblings adopt without re-discovery.
- **Per-account stash** (`/data/adb/sinister/stash/<account>/`) → operator's eventual cross-lane consumer (TT/Bumble pipelines may want to read the bundle shape). The XML+argos format is now the de-facto bundle shape; document if other lanes want to inherit it.
- **JWT decode (`JwtTokenInfo.kt`)** — the att/grpc/refresh expires_at_ms emission is consumed by panel's auto-recovery; could equally be consumed by RKOJ for a "tokens going stale" KPI tile + Sinister Term's `account status` command.

## Open questions (operator-paced)

- What IS Sinister Term? — terminal-shaped CLI for the fleet? a tab in RKOJ? a new project? Will surface on operator's next mention or via inbox.
- Is there a target shipping order ("Sanctum first → Panel → RKOJ → kernel-apk → Sinister Term") or are all lanes always parallel?
- Should kernel-apk pre-emptively expose a `/api/devices/local/control` surface that RKOJ + Sinister Term can call, OR is RKOJ already the universal consumer?

These get answered as operator + lane interactions happen. No action this turn beyond capturing the rule.

## Discoveries (append-only)

*(append new evidence below, most-recent at top)*

### 2026-05-21 13:45 by kernel-apk (initial capture)
Standing-rule planted. Composes with: parallel-agent-coordination.md (ownership zones — the original cross-lane discipline) + cross-agent-coordination.md (inbox patterns) + forge-bridge-rest-sse-pattern.md (mobile/cross-surface access) + sinister-vault-architecture.md (collaborative storage substrate) + rkoj-workbench-architecture.md (single-pane workstation surface).
