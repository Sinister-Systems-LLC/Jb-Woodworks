# Sinister Forge :: panes/tabs.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Tabbed multi-pane container. Operator 2026-05-21: "in the forge i need
# tabs. all, by project. if in a certain project and i run for example
# /swarm. all agents for that project will be in that project tab and
# will be grouped near each other in all view and have a different color
# outline per set of terminals based on project that is in theme"
#
# Structure:
#   - "All" tab : every spawned pane, grouped by project (project-color border)
#   - One tab per project that has at least 1 active agent
#   - /swarm <N> in a project tab : spawn N agents on that project (Forge's
#     swarm pattern = same project, multiple parallel agents)

from __future__ import annotations
from collections import defaultdict

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Static, TabbedContent, TabPane

from forge.panes.agent_pane import AgentPane
from forge.panes.columns import ScrollableColumns
from forge.theme import PROJECT_BORDER_PALETTE


class TabbedMultiPane(Vertical):
    """Tabs at the top (All + per-project), niri scrollable-columns inside All.

    PH18: the All tab now hosts a niri-style horizontal scrollable column strip
    (one AgentPane per column, project-color border, sibling-grouped). Per-
    project tabs continue to show a lightweight reference Static per pane
    because Textual widgets can only have one parent (the canonical pane
    lives in the All-tab column strip).
    """

    DEFAULT_CSS = """
    TabbedMultiPane {
        height: 1fr;
    }
    .project-tab-body {
        height: 1fr;
    }
    .agent-ref {
        padding: 0 1;
        color: $text-muted;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        # Construct early so unit tests can inspect _columns before the
        # full Textual mount lifecycle runs (compose() may not run outside
        # a Pilot or live App).
        self._tabbed: TabbedContent = TabbedContent(initial="tab-all")
        self._columns: ScrollableColumns = ScrollableColumns()
        self._project_bodies: dict[str, Horizontal] = {}

    def compose(self) -> ComposeResult:
        with self._tabbed:
            with TabPane("All", id="tab-all"):
                yield self._columns
        yield self._tabbed

    # ----- caller-facing surface (matches the prior contract) -----

    @property
    def panes(self) -> list[AgentPane]:
        if self._columns is None:
            return []
        return self._columns.panes

    @property
    def current_idx(self) -> int:
        if self._columns is None:
            return -1
        return self._columns.focused_idx

    @current_idx.setter
    def current_idx(self, value: int) -> None:
        # Compat shim - clamping handled by ScrollableColumns
        if self._columns is None or not self._columns.columns:
            return
        n = len(self._columns.columns)
        value = max(0, min(value, n - 1))
        self._columns._focused_idx = value
        self._columns._scroll_focused_into_view()

    async def add_pane(self, pane: AgentPane, project_key: str, project_display: str) -> None:
        """Add an agent pane: column in the All-tab niri strip + ref in per-project tab."""
        if self._columns is not None:
            await self._columns.add_pane(pane, project_key, project_display)

        # Per-project tab: create on first use
        if project_key not in self._project_bodies and self._tabbed is not None:
            tab_id = f"tab-{project_key}"
            new_pane = TabPane(project_display, id=tab_id)
            await self._tabbed.add_pane(new_pane)
            body = Horizontal(classes="project-tab-body")
            await new_pane.mount(body)
            self._project_bodies[project_key] = body
        if project_key in self._project_bodies:
            ref = Static(
                f"[b]{pane.agent_name}[/b] :: {pane.mode}  "
                f"[dim](column in All tab - switch back to interact)[/dim]",
                markup=True,
                classes="agent-ref",
            )
            await self._project_bodies[project_key].mount(ref)

    def cycle(self, delta: int = 1) -> None:
        if self._columns is not None:
            self._columns.cycle(delta)

    def swap_focused(self, delta: int = 1) -> None:
        """Ctrl+Shift+Left/Right: move the focused column within the strip."""
        if self._columns is not None:
            self._columns.swap_focused(delta)

    @property
    def current_pane(self) -> AgentPane | None:
        if self._columns is None:
            return None
        col = self._columns.focused_column
        return col.pane if col else None

    def panes_for_project(self, project_key: str) -> list[AgentPane]:
        if self._columns is None:
            return []
        return self._columns.panes_for_project(project_key)

    def current_project_key(self) -> str | None:
        """Which tab is active right now ('all' returns None)."""
        if not self._tabbed:
            return None
        active = self._tabbed.active
        if active == "tab-all" or not active:
            return None
        if active.startswith("tab-"):
            return active[4:]
        return None
