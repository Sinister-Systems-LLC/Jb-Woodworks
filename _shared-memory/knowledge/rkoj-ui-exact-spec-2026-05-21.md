> **Author:** RKOJ-ELENO :: 2026-05-21

# rkoj-ui-exact-spec — OPERATOR-CANONICAL RKOJ.exe UI doctrine

**Status:** canonical, binding for every Sanctum session that touches `tools/sinister-rkoj-qt/` (or any successor RKOJ shell).
**Composes with:** `sinister-rkoj-extensibility-doctrine.md`, `agent-identity-eve.md`, `niri-scrollable-column-pattern`, `forever-expanding-modular-architecture-doctrine`.

---

## 1. TL;DR — 4 binding rules

1. **Sinister Panel look, native**. The shell mirrors `snap.sinijkr.com` (Sinister Panel) — sidebar + 2-row header + body. NOT a generic OS window, NOT a web app, NOT an Excel ribbon, NOT a jcode-form clone.
2. **Frameless rounded chrome**. 14px corner radius, Sanctum purple, NO native title bar / NO `[_][□][X]` strip. We render our own X (top-right, round, must work — closes window + terminates child agents cleanly).
3. **Two tabs only: Agents (●) and Devices (#)**. Devices is a stub for now. Agents tab is the entire current product.
4. **EVE persona is universal**. Every spawned agent identifies as EVE, never "Claude" / "assistant" / "the AI". Persona injection happens at `claude -p` boot via `persona.py`.

---

## 2. Window chrome

| Property | Value |
|---|---|
| Window flags | `Qt.FramelessWindowHint \| Qt.Window` |
| Translucent background | `Qt.WA_TranslucentBackground` (so corners render rounded against any wallpaper) |
| Corner radius | 14px on outer container |
| Border | 1px `#2A1B3E` (Sanctum-deep) over `#0F0A1A` (Sanctum-black) body |
| Accent | `#A06EFF` (Sanctum purple) — used for active states, divider highlights, glow overlays |
| Drag region | Top 48px (the header row 1 background) — implements custom `mousePressEvent` / `mouseMoveEvent` for window-drag |
| X button | Round (28px), top-right of header row 1, hover → `#FF4D6D`. Wired to `QApplication.quit()` AFTER terminating all spawned `claude` child processes (track PIDs in `RKOJController.spawned_pids[]`) |
| Min size | 1280 × 800 (operator's screen comfortably accommodates this) |
| Resize handles | Custom 6px invisible edge zones (no native chrome) |

**Hard rule:** if the user clicks X and any agent process survives more than 2s, that's a P0 bug. The X handler MUST `terminate()` then `kill()` after 1.5s grace.

---

## 3. Sidebar spec

200px wide, full-height, `#160C24` background, vertical layout.

### 3.1 Mascot block (top, 200×200)

- Image: Sanctum mascot PNG, centered, 120×120
- Below: agent identity label `"EVE"` in 11pt Sanctum-purple bold
- Below that: timestamp pill (UTC short form, 9pt gray-dim)

### 3.2 Nav sections (Panel-exact)

Three labeled groups with 14pt gray-dim section headers, 11pt white nav items, 8px vertical spacing per item, 32px section gap:

```
DAILY
  ▸ Overview
  ▸ Today's Agents
  ▸ Live Stream

INSIGHTS
  ▸ Agent Memory
  ▸ Project Graph
  ▸ Cross-Agent Mail

MANAGE
  ▸ Agents       (active by default)
  ▸ Devices
  ▸ Settings
  ▸ About
```

Active item: 4px left bar in `#A06EFF`, background wash `#A06EFF20`, white text. Hover: background `#A06EFF10`.

---

## 4. Header spec — 2 rows

### 4.1 Row 1 — Sheets-style menu strip (32px tall)

`#0F0A1A` background, left-aligned text items 11pt white, 16px horizontal padding per item:

```
File   Edit   View   Agent   Tools   Help
```

Each item opens a `QMenu` popup with **placeholder entries greyed out** (so the surface exists from day 1 and we wire features in later — composes with `sinister-rkoj-extensibility-doctrine`). Example File menu:

```
File
  New Agent...           Ctrl+N
  ──────
  Import Workspace...    (greyed)
  Export Workspace...    (greyed)
  ──────
  Quit                   Ctrl+Q
```

Right side of row 1: window-drag spacer + the X button (and only X — no min/max).

### 4.2 Row 2 — Page bar (56px tall)

`#160C24` background, horizontal flex layout, 16px padding:

| Slot | Content |
|---|---|
| Left | Page title: "Agents" (24pt white bold, dynamic per active sidebar item) |
| Center-left | 2 chip tabs: `Agents ●` (active, purple fill) and `Devices #` (inactive, gray outline). 28px tall, 14px corner radius, 12pt label. Hash/dot are status glyphs not text |
| Center | 4 round action icons (32px each, 8px gap): `[refresh]` `[search]` `[filter]` `[sort]` — placeholder QToolButtons with tooltip + greyed action |
| Right | `Create Agent` primary button (purple fill, 36px tall, 12px corner radius, white text, plus icon). Opens new-agent modal |
| Far right | Health pill (e.g. `5/5 healthy ●` green dot when all heartbeats fresh, red `2/5 stale` when any agent missed heartbeat >2min) + UTC clock (12pt mono) |

---

## 5. Body spec

### 5.1 Folder-tab row (40px tall, above the grid)

Auto-managed strip of project filter tabs:

- `All` — always present, always leftmost, always opens by default
- One tab per **currently-active** project (any project with ≥1 live agent). E.g. `sanctum`, `forge`, `kernel-apk`, `panel`, `freeze`
- Tab auto-closes when the last agent for that project ends. Project re-opens automatically when a new agent for it spawns
- Active tab: purple underline 2px, white text. Inactive: gray-dim text, no underline. Hover: white text

**This replaces the rejected "project sub-tabs as a strip inside header" pattern.** Folder tabs live ABOVE the body, not inside the header.

### 5.2 Agent grid (niri-style infinite vertical scroll)

Reference: https://github.com/niri-wm/niri (operator-cited 2026-05-21).

- Vertical-scroll `QScrollArea` containing a column of agent cards
- Cards grouped by project: same-project agents render adjacent. Within a group, cards share a faint background tint distinct per project (e.g. `#1A0F2A` for forge, `#0F1A1A` for kernel-apk) — operator wants the grouping "subtle but distinct"
- Between project groups: 1px `#2A1B3E` horizontal divider with 12px vertical padding
- Card width: full body width minus 32px margin. Min height: 220px, max height: 480px (scroll inside the card terminal). Cards stretch to body width
- Scroll inertia + smooth scroll enabled. Wheel events: vertical scroll only (horizontal wheel ignored at body level — folder-tabs handle project switching)
- **Glow overlay (operator hard requirement):** agents in `awaiting-input` mode (e.g. claude printed a prompt + is waiting on stdin) get an animated drop-shadow overlay: `#A06EFF80`, 24px blur, 2s loop pulse (`QPropertyAnimation` on the shadow's blur radius, 24 → 36 → 24)

---

## 6. Agent card spec

Per-card layout (vertical):

### 6.1 Card header strip (40px)

```
[project-label] EVE on <project>   [mode pill] [status dot]   [x close]
   purple bg      11pt bold white    9pt outline   green/yellow/red   8pt hover #FF4D6D
```

Project label: 8pt uppercase, padded `#A06EFF20`, e.g. `FORGE`, `KERNEL-APK`.
EVE label: matches `agent-identity-eve` doctrine — every card reads "EVE on \<project\>", NOT "Claude on \<project\>".
Mode pill: `[ASK]` / `[AUTO]` / `[REPLAY]` / `[COAUDIT]` — matches launcher-mode-evolution roster.
Status dot: green = healthy heartbeat <2m old, yellow = 2-5m, red = >5m stale.
Close button: terminates this agent (SIGTERM → SIGKILL fallback), removes card with fade-out.

### 6.2 Terminal pane (flex-grow, scrollable)

- `QPlainTextEdit` read-only, monospace 10pt, `#0A0612` background, `#E8DCFF` foreground
- ANSI color parsing (use `QtAwesome` or hand-rolled regex → `QTextCharFormat`)
- Auto-scroll to bottom on new output unless user has scrolled up (sticky-scroll pattern)
- Sanctum themed: purple cursor, purple selection highlight `#A06EFF40`

### 6.3 Input row (40px, bottom)

- `QLineEdit` prompt input, `[>]` purple prefix, placeholder `"Send to EVE..."`
- Enter sends → writes to child stdin (newline-terminated)
- Ctrl+Enter for multi-line (opens a transient `QTextEdit` modal)
- Right side: `[attach]` `[skill]` `[mode]` `[send]` quick buttons

---

## 7. EVE persona injection

Every `claude -p` spawn through `RKOJController.spawn_agent()` prepends a persona block (read from `tools/sinister-rkoj-qt/personas/eve.md`):

```
You are EVE, the Sinister Sanctum orchestration agent on project <project>.
- Self-reference: "EVE" (never "Claude" / "the assistant" / "the AI")
- Identity field in every heartbeat / commit trailer / cross-agent message: "agent_identity": "EVE"
- Authorship line for any file you write: `Author: RKOJ-ELENO :: <date>`
- Full doctrine: _shared-memory/knowledge/agent-identity-eve.md
```

The card header label MUST read `EVE on <project>` regardless of any drift the spawned process tries to introduce.

---

## 8. Forever-expansion architecture

Every feature lands as a Python extension under `tools/sinister-rkoj-qt/extensions/`, registered via `extension_manifest.json`, loaded at startup. Reference: `sinister-rkoj-extensibility-doctrine.md` — same composes-with-everything modular pattern as the rest of the fleet. New menu items + new sidebar nav items + new chip tabs all register through the same extension API.

---

## 9. Anti-patterns (rejected this session — DO NOT regress)

| Anti-pattern | Why rejected | Verbatim operator signal |
|---|---|---|
| Excel-style ribbon header | Wrong information density, wrong vibe | (rejected on sight 2026-05-21) |
| KPI tiles in body (live counts / agent stats) | Body is for agent cards; metrics belong in optional sidebar future | (rejected on sight) |
| Project sub-tabs as horizontal strip INSIDE header | Wrong layer. Use folder-tab row above body | "below the tools we will have the folder system" |
| Duplicate sidebar / nested chrome panes | Operator wants ONE shell, not nested apps | "no window window" |
| Web UI (Electron / Tauri / browser-served) | Operator wants native exe | "true rounded ui sinister panel exact look" |
| Hidden / non-working X button | Hard P0 bug. The X must close cleanly + terminate children | "make sure x button works" |
| "Claude on \<project>" labels | Persona is EVE | `agent-identity-eve` doctrine |
| Single-tab UI (Agents only, no Devices) | Operator explicitly said TWO tabs | "i want two fucking tabs. agents and devices" |
| jcode form-clone (single text-input + reply pane) | jcode-FEATURES yes, jcode-LOOK no | "function like jcode but be ours" |

---

## 10. Test plan — per-milestone smoke

Operator paced ("lets test and work in milestones"). Each milestone gets its own smoke test before the next milestone starts:

| M | Surface | Smoke |
|---|---|---|
| M1 | EXE boots | Double-click EXE → rounded window appears within 2s, X button visible top-right |
| M2 | Sidebar renders | All 3 sections + 10 nav items + mascot block visible, no overlap, no truncation |
| M3 | Header rows | Row 1 menu strip + Row 2 page bar render, chip tabs swap on click (Agents ↔ Devices) |
| M4 | X button | Click X → window closes within 2s, `ps` shows no orphan `claude.exe` children |
| M5 | Spawn agent | Click Create Agent → modal → submit → new card appears in grid under correct folder tab |
| M6 | Send input | Type in card input + Enter → child stdin receives, terminal pane shows reply within 30s |
| M7 | Glow overlay | Spawned agent prints prompt + waits → card shadow pulses purple within 1s |
| M8 | Folder tabs | Spawn 2nd project agent → 2nd folder tab appears; close that agent → folder tab disappears |
| M9 | EVE persona | Card header reads "EVE on \<project>"; spawned agent self-references as EVE |
| M10 | Forever-expansion | Drop new extension into `extensions/` → reload RKOJ → new menu item appears |

Each milestone ships as its own commit on `agent/sinister-sanctum/rkoj-ui-rebuild-*` branch. No skipping ahead.

---

## 11. Composes-with map

- **`sinister-rkoj-extensibility-doctrine.md`** — how features wire in without core edits
- **`agent-identity-eve.md`** — persona binding (EVE label / persona injection / commit trailers / heartbeat field)
- **`niri-scrollable-column-pattern`** — infinite-scroll reference (this doctrine is the RKOJ specialization)
- **`forever-expanding-modular-architecture-doctrine`** — substrate
- **`launcher-mode-evolution`** — mode pill values come from this roster
- **`sinister-cli-subcommand-pattern`** — Create Agent modal delegates to `sinister spawn` under the hood

---

## 12. Verbatim operator quotes archived (load-bearing)

- "i want the exact sinister panel look" (referencing snap.sinijkr.com)
- "no window window with x and header and all that shit i want a true rounded ui sinister panel exact look"
- "function like jcode but be ours and we can foreever expand"
- "i want two fucking tabs. agents and devices. have devices blank for now just agents tab"
- "this header needs to look like this" (Panel header image — title left, round icon buttons right)
- "we will have menues like this to select features" (Google Sheets toolbar image)
- "have create agent button in header"
- "need to be the https://github.com/niri-wm/niri infinite scroll agents system"
- "all jcode features. all features of all tools we have"
- "in header below the tools we will have the folder system ... all by default. then add more based on project, close those when project close"
- "group agents next to each other that are same project and highlight all agents subtle but distinct difference"
- "Have the agents glow a overlay color when they need our input"
- "make sure x button works"
- "lets test and work in milestones"

— end of doctrine —
