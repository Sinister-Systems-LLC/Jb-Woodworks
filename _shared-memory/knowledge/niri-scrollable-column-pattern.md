# niri-scrollable-column-pattern — fleet UI doctrine for multi-pane surfaces

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Origin:** Operator image 2026-05-21T11:43Z (niri-wm/niri reference for Sinister Forge multi-pane layout). Forge HELLO-ACK 2026-05-21T11:45Z absorbed it for their lane. Sanctum 1228Z ACK promised this brain entry FIRST so Mind / Claw / Term / RKOJ can mirror the same vocabulary before any single project locks in tabs.
> **Status:** **v1.1.0 SHIPPED in Sinister Forge** (NiriWorkspaceGrid, 2026-05-21). Doctrine still authoritative for fleet-wide adoption — Mind / Claw / Term / RKOJ continue to compose against this entry.

## v1.1.0 SHIP — Sinister Forge NiriWorkspaceGrid (2026-05-21)

Operator directive 2026-05-21 (verbatim): *"i want our windows to function just like fucking jcode... inside that a system like this: https://github.com/niri-wm/niri embeded in the agents tab. With full control like jcode has it here: https://github.com/1jehuang/niri-workspaces-rs"*.

Implementation: **`projects/sinister-forge/source/forge/panes/niri_workspace.py`** — `NiriWorkspaceGrid(ScrollableContainer)`.

Concept upgrade vs v1 (`panes/columns.py`):

| Aspect | v1 (`columns.py`) | v1.1.0 (`niri_workspace.py`) |
|---|---|---|
| Column == | one AgentPane | one Workspace holding 1..N stacked AgentPanes |
| Width | 64 cells | 80 cells |
| New-content gesture | append column | append pane to active ws (or Ctrl+T = new ws) |
| Pane move | swap entire column position | move pane between workspaces (Ctrl+Shift+←/→) |
| Indexing | none | Ctrl+1..9 jumps to workspace N |
| Status row | none | `[ws 1] [ws 2] · [ws 3*] · [ws 4]` (active *) |

Mapping back to the 7 primitives:
1. Horizontal scroll region — `ScrollableContainer` with `overflow-x: auto`
2. Always-one-visible — placeholder Static when no workspaces (`"no workspaces · Ctrl+T to open · Ctrl+W to spawn agent"`)
3. Per-column metadata strip — `WorkspaceColumn.border_title` + global `WorkspaceStatusRow` docked top
4. Keyboard navigation — `Ctrl+←/→` cycle, `Ctrl+Shift+←/→` move pane across workspaces, `Ctrl+1..9` jump, `Ctrl+T` new
5. Mousewheel — Textual default (horizontal wheel scrolls strip; vertical wheel scrolls inside focused pane's RichLog)
6. Spawn-policy — `add_pane()` appends to active workspace; `move_active_pane(delta)` past the edge auto-creates a new workspace there (matches niri WM behavior)
7. Persistence — left for caller (`active_idx` / `workspaces[i].panes` enumerable, ready for resume-point write)

Wiring in app.py:
- `from forge.panes.niri_workspace import NiriWorkspaceGrid` (TabbedMultiPane stays imported as legacy fallback)
- `self._tabs = NiriWorkspaceGrid()` — replaces the old `TabbedMultiPane()` mount under the Agents sidebar tab
- Compat shims on `NiriWorkspaceGrid` (`_columns`, `_tabbed`, `remove_focused`, `panes_for_project`, `current_project_key`) keep the existing app.py action handlers working unchanged
- Sidebar ADB tab unaffected (display-toggle approach preserved)

Test contract:
```sh
python -c "from forge.panes.niri_workspace import NiriWorkspaceGrid; print('ok')"
# → ok
```

Status: doctrine, fleet-wide. Forge has shipped v1.1.0; Mind / Claw / Term / RKOJ continue PH-future per the adoption table below.
> **Composes with:** sinister-forge-harness-pattern · rkoj-workstation-ui-layout · forever-expanding-modular-architecture-doctrine · agent-browser-bridge-pattern · jcode-feature-matrix

## What "niri-style" means in 30 seconds

niri (the scrollable-tiling Wayland compositor) renders open windows as a horizontally-scrollable column strip:

- Each window is a full-height **column**. New windows append to the right (or split a column vertically into stacked rows).
- The current column is always centered/visible; other columns are off-screen but always one keyboard-flick or one mouse-wheel scroll away.
- There are NO tabs to click and NO "minimize" — every open thing has a permanent geographic place on the infinite horizontal strip.
- Spatial memory replaces taxonomic memory: the operator remembers "Forge is two columns left of Term," not "Forge is in tab 3 of 7."

For Sinister surfaces this maps cleanly onto: each agent pane / each project view / each chat thread = one column.

## When this pattern wins over tabs

| Trait | Tabs | niri scrollable-columns |
|---|---|---|
| Max items the operator can keep mental-model of | ~7 (Miller's law on visible labels) | ~30 (spatial memory of left/right) |
| Cost to peek at a sibling | click + paint + remember to click back | scroll-wheel + parallax (sibling never fully hidden) |
| Cost to add a 12th item | "Tab bar overflow" (hidden ⋯ menu) | append → just keep scrolling |
| Cost to compare two items side-by-side | impossible without splitting | native (they're adjacent columns) |
| Mouse-free navigation | Ctrl+1..Ctrl+9 (collapses after 9) | Ctrl+←/→ scales infinitely |
| Best for | low-N (≤7) heterogeneous views | high-N (≥10) homogeneous panes (agents, chats, projects) |

**Decision rule:** if the count is bounded ≤7 AND items are categorically different (e.g. "Console / Settings / About"), use tabs. If the count grows unbounded AND items are categorically the same (every "thing" is a different instance of the same kind — an agent pane, a chat, a project view), use niri-columns.

## Fleet adoption surfaces

| Surface | Today | niri-pattern fit | Phase |
|---|---|---|---|
| Sinister Forge (TUI panes per agent) | **NiriWorkspaceGrid (shipped v1.1.0)** | **strong fit** (panes are homogeneous; operator wants ≥5 at once) | **SHIPPED 2026-05-21** — `panes/niri_workspace.py` |
| Sinister Claw (mobile, agent screens) | bottom-tab nav (Sanctum/Forge/Mind/Settings) | **partial** — bottom-tabs are categorically different (≤7), good for them. But INSIDE the Forge screen, the agent list could be a niri-style strip. | Claw PH-future |
| Sinister Mind (browser viz @ :5079) | unknown — likely SPA with tabs | **strong fit** if Mind shows per-namespace memory graphs (each ns = one column) | Mind PH-future |
| Sinister Term (PTY split-pane future) | none yet (single shell) | **strong fit** when split-pane lands (each pane = one column; horizontal scroll = niri-style; Ctrl+Shift+←/→ to scroll) | Term PH-future |
| RKOJ workstation (Agents tab) | 3-row header + 2 tabs + agents-table | **partial** — agents-table already shows N agents in one view, but a per-agent detail pane could open as a niri-column rather than a modal | RKOJ PH-future |
| Sinister Panel (web admin) | sidebar nav + tabular pages | tabs/sidebar correct (categorically different sections). Agents/accounts/devices lists could scroll horizontally if they ever want side-by-side compare. | Panel PH-future |

## Implementation primitives (language-agnostic checklist)

Each surface that adopts the pattern must provide:

1. **Column container** — a horizontally-scrollable region with snap-to-column behavior (CSS `scroll-snap-type: x mandatory` / Textual `Horizontal` widget with custom snap / SwiftUI `ScrollView(.horizontal)` with `.scrollTargetBehavior(.viewAligned)`).
2. **Always-one-visible invariant** — never paint the chrome with zero columns visible. If the strip is empty, show the "spawn new column" placeholder centered.
3. **Per-column metadata strip** — top edge of each column shows: column title + lane color (per project accent in `automations/session-templates/agent-prefs.json`) + close × + drag-to-reorder handle.
4. **Keyboard navigation** — Ctrl+← / Ctrl+→ scroll one column; Ctrl+Shift+← / Ctrl+Shift+→ move the focused column itself in the strip; Ctrl+W close focused column; Ctrl+T new column.
5. **Mouse-wheel scrolling** — horizontal wheel scrolls the strip; vertical wheel scrolls inside the focused column (NOT the strip — otherwise users lose context).
6. **Spawn-policy** — new columns append to the right of the focused column by default. Modifier (Shift+spawn) splits the focused column vertically into stacked rows (niri's "S-window" gesture).
7. **Persist column order across restart** — every column's identity + position written to per-surface resume-point. The pre_warm read picks the same strip back up.

## Composes with existing fleet doctrine

- **`sinister-forge-harness-pattern`** — Forge already wraps each agent as subprocess; adopting niri-columns just changes the rendering of the existing pane registry. The harness contract is preserved.
- **`rkoj-workstation-ui-layout`** — RKOJ's 3-row header / 2-tab / agents-table doctrine still holds; this brain entry only suggests where a NEW detail-pane surface should adopt niri rather than modal-popup.
- **`forever-expanding-modular-architecture-doctrine`** — niri-columns are inherently slug-namespaced (one column per slug) and append-only (new agents = new columns) — both already mandated properties.
- **`agent-browser-bridge-pattern`** — if/when the Browser-Bridge adds an operator-side UI tab for the WebSocket-host status, multiple connected browsers = one column each. Natural fit.

## Anti-patterns

- **Don't force niri onto ≤4 panes** — overkill; tabs are fine when N is small + heterogeneous.
- **Don't paginate the strip** — there are no "page boundaries" in niri; if you find yourself adding "next 10 columns →" you've defeated the spatial-memory benefit.
- **Don't hide the off-screen columns entirely** — always show a parallax slice (1-5% of the next column edge visible) so the operator sees there's more.
- **Don't reorder columns automatically** — operator owns spatial layout; auto-sort by "most-recently-active" defeats spatial memory.
- **Don't put unrelated kinds of things in the same strip** — keep the categorical homogeneity (agent strip ≠ project strip; one strip per concept).
- **Don't lose the focused column on resize** — if the chrome reflows (window resize, mobile rotate), the focused column must remain centered, not jump to position 0.

## Lane handoff at brain-entry write-time

Per CONTRACT 5 + Sanctum's 1228Z ACK to Forge: **Sanctum owns this doctrine entry; Forge claims PH-N implementation in their TUI when ready.** Mind/Claw/Term/RKOJ pickup-in-their-own-phase via [ASK] in their inbox if they want to adopt — none of those lanes is blocked on this entry existing.

If Forge wants to push back on any of the 7 implementation primitives above, drop `[DISCUSS]` at `_shared-memory/inbox/sanctum/<UTC>-niri-discuss-from-forge.json`.

## Cross-references

- Operator image 2026-05-21T11:43Z — niri-wm screenshot directing Forge
- `_shared-memory/inbox/sanctum/2026-05-21T1145Z-hello-ack-from-forge.json` — Forge absorption note + 2 open questions (answered in 1228Z ACK)
- `_shared-memory/cross-agent/2026-05-21T1228Z-sanctum-to-forge-jcode-cli-ack.md` — Sanctum ACK promising brain-entry-first
- `_shared-memory/knowledge/jcode-feature-parity-targets.md` (mentions "niri-style scrollable multi-pane" as parity target)
- `_shared-memory/knowledge/sinister-forge-harness-pattern.md` (subprocess-pane registry that niri-columns will render)
- `_shared-memory/knowledge/rkoj-workstation-ui-layout.md` (existing fleet UI doctrine — niri composes alongside, doesn't replace)
- niri upstream: https://github.com/YaLTeR/niri (operator-referenced, vocabulary source)
