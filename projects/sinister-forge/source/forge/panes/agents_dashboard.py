# Sinister Forge :: panes/agents_dashboard.py — Agents tab content (NEW)
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Operator 2026-05-21 (image 28 = Sinister Panel dashboard reference):
#   *"agents (system we are building out with tabs per project, tab to view
#   all, all things like that i asked for)"*.
#
# The Agents tab content. Holds:
#   1. Sub-tab strip (top): `[All N] [Sanctum] [Forge] [Panel] [Term] [Kernel
#      APK] [RKOJ] [Freeze] [...]` (one per project from session-templates/
#      projects.json).
#   2. Live status row: `4 live · 18 known projects · sanctum has 2 panes`
#   3. The existing NiriWorkspaceGrid (filtered by the active sub-tab).
#
# Sub-tab semantics:
#   - "All"   = no filter — all workspaces visible (default)
#   - <key>   = visually dim/hide WorkspaceColumns whose first AgentPane has a
#               project_key != <key>
#
# Filter strategy: toggle `.display` on workspaces rather than re-mount panes —
# subprocesses keep running, scroll position survives sub-tab switches.

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widgets import Static

from forge.projects import load_projects
from forge.panes.niri_workspace import NiriWorkspaceGrid
from forge.theme import (
    BG, BG_GLASS_1, BG_GLASS_2, BG_GLOW, BORDER_GLASS,
    PURPLE_DARK, PURPLE_DEEP, PURPLE_ACCENT, PURPLE_HALO,
    LIGHT_PURPLE, SOFT, DIM, GREEN_ACCENT,
)

if TYPE_CHECKING:
    from forge.panes.agent_pane import AgentPane


# Sub-tab key reserved for the "show everything" view. Anything else is
# matched against AgentPane.project_key (which matches projects.json keys).
ALL_TAB_KEY = "__all__"


class SubTab(Static):
    """A single project sub-tab pill (Sinister Panel chip style)."""

    DEFAULT_CSS = f"""
    SubTab {{
        height: 3;
        padding: 1 2;
        margin: 0 1 0 0;
        background: {BG_GLASS_1};
        border: round {BORDER_GLASS};
        color: {SOFT};
        text-align: center;
    }}
    SubTab.-active {{
        background: {BG_GLOW};
        color: {PURPLE_HALO};
        border: round {PURPLE_ACCENT};
        text-style: bold;
    }}
    SubTab:hover {{
        border: round {PURPLE_ACCENT};
    }}
    """

    def __init__(self, key: str, label: str) -> None:
        super().__init__(f"[bold]{label}[/]")
        self.sub_key = key

    def set_active(self, active: bool) -> None:
        if active:
            self.add_class("-active")
        else:
            self.remove_class("-active")

    def set_label(self, label: str) -> None:
        self.update(f"[bold]{label}[/]")


class AgentsDashboard(Vertical):
    """Container that mounts inside the right-of-sidebar area when the
    operator clicks the AGENTS sidebar tab.

    Composition:
        ┌──────────────────────────────────────────────────────────────┐
        │ [All N] [Sanctum] [Forge] [Panel] [Term] [Kernel APK] [...] │  ← sub-tab strip
        ├──────────────────────────────────────────────────────────────┤
        │ 4 live · 18 known projects · sanctum has 2 panes             │  ← status row
        ├──────────────────────────────────────────────────────────────┤
        │ NiriWorkspaceGrid (filtered by active sub-tab)               │
        │                                                              │
        └──────────────────────────────────────────────────────────────┘
    """

    DEFAULT_CSS = f"""
    AgentsDashboard {{
        background: {BG};
        padding: 0;
    }}
    AgentsDashboard #agents-subtab-strip {{
        dock: top;
        height: 3;
        padding: 0 1;
        background: {BG};
        border-bottom: solid {BORDER_GLASS};
    }}
    AgentsDashboard #agents-status-row {{
        dock: top;
        height: 1;
        padding: 0 2;
        background: {BG_GLASS_1};
        color: {SOFT};
        border-bottom: solid {BORDER_GLASS};
    }}
    AgentsDashboard #agents-grid-host {{
        height: 1fr;
        width: 1fr;
    }}
    """

    class SubTabChanged(Message):
        def __init__(self, sub_key: str) -> None:
            self.sub_key = sub_key
            super().__init__()

    def __init__(self) -> None:
        super().__init__()
        self._active_sub: str = ALL_TAB_KEY
        self._sub_tabs: dict[str, SubTab] = {}
        self._strip: Horizontal | None = None
        self._status_row: Static | None = None
        self._grid: NiriWorkspaceGrid | None = None
        self._grid_host: Vertical | None = None
        # Cache the projects.json load (cheap but called repeatedly).
        self._projects = load_projects()

    @property
    def grid(self) -> NiriWorkspaceGrid | None:
        """Expose the internal NiriWorkspaceGrid so ForgeApp can keep using
        `self._tabs.add_pane(...)` etc. without knowing the dashboard wraps it."""
        return self._grid

    def compose(self) -> ComposeResult:
        # Sub-tab strip (top dock)
        self._strip = Horizontal(id="agents-subtab-strip")
        yield self._strip
        # Status row
        self._status_row = Static("", id="agents-status-row")
        yield self._status_row
        # Grid host (bottom expanding)
        self._grid_host = Vertical(id="agents-grid-host")
        yield self._grid_host

    async def on_mount(self) -> None:
        # Build sub-tabs from session-templates/projects.json. Always lead
        # with "All", then one tab per project (display name).
        assert self._strip is not None
        all_tab = SubTab(ALL_TAB_KEY, "All 0")
        all_tab.set_active(True)
        self._sub_tabs[ALL_TAB_KEY] = all_tab
        await self._strip.mount(all_tab)
        for p in self._projects:
            if not p.key or not p.display:
                continue
            # Short display: split on space/dash, take last meaningful word
            short = self._short_label(p.display)
            tab = SubTab(p.key, short)
            self._sub_tabs[p.key] = tab
            await self._strip.mount(tab)
        # Mount the actual NiriWorkspaceGrid
        assert self._grid_host is not None
        self._grid = NiriWorkspaceGrid()
        await self._grid_host.mount(self._grid)
        # Initial render of the status row + sub-tab counts
        self._refresh_counts()
        # Periodically refresh counts (every 3s — cheap, just iterates panes).
        self.set_interval(3.0, self._refresh_counts)

    @staticmethod
    def _short_label(display: str) -> str:
        """Compact 'Sinister Forge + Term (workbench)' → 'Forge'."""
        # Drop common "Sinister " prefix, strip parenthetical suffix
        s = display
        if s.startswith("Sinister "):
            s = s[len("Sinister "):]
        if " (" in s:
            s = s.split(" (", 1)[0]
        # Take first 2 words max
        parts = s.split()
        return " ".join(parts[:2]) if parts else display

    def on_click(self, event) -> None:
        target = event.widget
        node = target
        while node is not None and not getattr(node, "sub_key", None):
            node = getattr(node, "parent", None)
        if node is None:
            return
        key = getattr(node, "sub_key", None)
        if not key or key == self._active_sub:
            return
        self.select_sub(key)

    def select_sub(self, key: str) -> None:
        if key not in self._sub_tabs or key == self._active_sub:
            return
        self._sub_tabs[self._active_sub].set_active(False)
        self._sub_tabs[key].set_active(True)
        self._active_sub = key
        self._apply_filter()
        self._refresh_counts()
        self.post_message(self.SubTabChanged(key))

    def _apply_filter(self) -> None:
        """Show/hide WorkspaceColumns based on the active sub-tab."""
        if self._grid is None:
            return
        if self._active_sub == ALL_TAB_KEY:
            # Show every workspace
            for ws in self._grid.workspaces:
                ws.display = True
            return
        # Filter: show only workspaces whose first pane matches the active key.
        # Workspaces with no panes are always shown (empty placeholders).
        for ws in self._grid.workspaces:
            if not ws.panes:
                ws.display = True
                continue
            first_key = getattr(ws.panes[0], "project_key", "")
            ws.display = (first_key == self._active_sub)

    def _refresh_counts(self) -> None:
        """Update the status row + the `All N` sub-tab label with live counts."""
        if self._grid is None or self._status_row is None:
            return
        all_panes = self._grid.panes
        total = len(all_panes)
        # live = panes whose subprocess is in 'running' state (best-effort)
        live = sum(
            1 for p in all_panes if getattr(p, "_status", "") == "running"
        )
        known = len([p for p in self._projects if p.key])
        # Active sub-tab additional info
        cur_extra = ""
        if self._active_sub != ALL_TAB_KEY:
            count = sum(
                1 for p in all_panes
                if getattr(p, "project_key", "") == self._active_sub
            )
            disp = next(
                (p.display for p in self._projects if p.key == self._active_sub),
                self._active_sub,
            )
            cur_extra = f"  ·  {disp.lower()} has [bold]{count}[/] pane{'s' if count != 1 else ''}"
        live_color = GREEN_ACCENT if live > 0 else DIM
        self._status_row.update(
            f"[{live_color}]{live}[/] live  ·  "
            f"[bold]{total}[/] total panes  ·  "
            f"[dim]{known} known projects[/]"
            f"{cur_extra}"
        )
        # Update the "All N" tab label
        all_tab = self._sub_tabs.get(ALL_TAB_KEY)
        if all_tab is not None:
            all_tab.set_label(f"All {total}")
