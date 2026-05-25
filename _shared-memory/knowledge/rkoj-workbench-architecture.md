<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# RKOJ.exe — workbench architecture (2-tab + ribbon + popout + cycle-points + scheduler)

**Status:** fixed
**Tags:** rkoj, workbench, ui, 2-tab, ribbon, popout, cycle-points, scheduler, liquid-glass, sanctum-purple
**Related:** `exe-silent-crash-no-popup.md`, `agent-intelligence-control.md`, `console-phone-viewer-integration.md`

## Problem

The Sanctum-Console UI accumulated 11 sidebar entries + multiple top-bar buttons over a single sprint. Operator declared it too cluttered for daily use — wanted the layout consolidated to match the Sinister Panel + LetsText (rounded, sleek, efficient) with two primary tabs.

## Why

A daily-driver workstation can't ask the operator to remember 11 names. The 2-tab pattern (Devices / Agents) covers the two activities the operator does most. Other features (Memory / Codex / Knowledge / Skills / Tools / Inventions / Settings) move into dev-tools-rail drawers or the Cmd+K palette — present, not foregrounded.

Plus the operator added cycle-points (one-click project resume) and a scheduler (cron-like project automation) as flagship features.

## Fix — architecture summary

**Tab 1: ADB Devices** — device grid with lane filter, per-card actions (VIEW/STOP/Push/Notes/Run cmd/Frida), per-pane cmd history + push picker. Dev-tools rail: refresh interval, scrcpy options, bulk actions.

**Tab 2: Agents** — sessions strip with per-agent chips (model badge + intelligence + cycle-point save + popout), launcher wizard, recent launches, cycle-points list, activity feed (merged progress + inbox + requests). Dev-tools rail: Memory + Codex + Knowledge + Settings + Schedule drawers.

**Ribbon** — Excel-style two-row sticky top bar. Row 1: brand + 2-tab pill + global icons (alerts bell, settings, Cmd+K, health, clock). Row 2: tab-specific button groups (VIEW / SPAWN / AUTOMATE / MAINTAIN), each tile = icon stacked over label.

**Popout system** — `[↗ popout]` on every surface. `window.open()` with `#popout=<view>&state=<base64>` fragment. Cross-window sync via `BroadcastChannel('rkoj-state')`. Popouts tracked in `localStorage.rkoj.popouts`.

**Cycle points** — POST `/api/cycle-points` saves a JSON snapshot (project + agent meta + open files + last inbox tail + recent progress + custom note). POST `/api/cycle-points/{slug}/resume` reads the snapshot and POSTs `/api/launcher/spawn` with the captured params + a custom_prompt that says "resume cycle X: read these files, continue from Y".

**Scheduler** — `_shared-memory/schedule.json` array of entries (id, name, cron, kind, action, enabled, last_run, next_run). Daemon = asyncio task started at server boot, 30s tick, Semaphore(5) concurrency. Kinds: `script` (whitelisted bus scripts), `spawn-agent` (calls launcher), `inbox` (broadcasts message), `resume-cycle`, `http` (generic call). Cron parsing via `croniter`.

**Design language** — Liquid Glass primitives (`.lg-card` 16px radius, `.lg-card-hero` 18px+breathe, `.lg-rail`, `.lg-popover`, `.lg-pill[-active]`, `.lg-button`, `.lg-input`) hand-ported from dashboard-skeleton. Sanctum purple `--sanctum-primary: #7A3DD4` stays the accent (master-surface rule).

## Reuse map (what stays — DON'T reimplement)

- All `app.js` helpers ($, qs, qsa, el, toast, fetchJson, _authHeaders, openAgentActions, _renderDeviceCard, history helpers, etc.)
- All server.py endpoints (auth, inbox, progress, memory, codex, knowledge, devices, launcher, intelligence, requests)
- `viewer.py` async ADB primitives (serial_run, enrich_devices_parallel, exec_adb, install_frida)
- `auth.py` HWID binding
- `memory_sanitizer.py` poisoning defense
- mobile.html / mobile.css / mobile.js (phone surface, iOS blue)

## Discoveries

### 2026-05-19 by Sinister Sanctum
Initial design + plan landed. Parallel implementation in 7 agents.
