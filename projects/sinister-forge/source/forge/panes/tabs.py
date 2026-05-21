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
from forge.theme import PROJECT_BORDER_PALETTE


class ProjectGroup(Vertical):
    """A project's color-outlined group of panes inside the All tab."""

    def __init__(self, project_key: str, project_display: str) -> None:
        super().__init__(classes="project-group")
        self.project_key = project_key
        self.project_display = project_display
        color = PROJECT_BORDER_PALETTE.get(project_key, PROJECT_BORDER_PALETTE["_default"])
        self.styles.border = ("round", color)
        self.border_title = f"  {project_display}  "

    def add_pane(self, pane: AgentPane) -> None:
        self.mount(pane)


class TabbedMultiPane(Vertical):
    """Tabs at the top (All + per-project), grouped panes inside.

    The All tab uses project-color borders to visually cluster.
    Per-project tabs just lay panes side-by-side (no border per pane).
    """

    DEFAULT_CSS = """
    TabbedMultiPane {
        height: 1fr;
    }
    .project-group {
        height: 1fr;
        margin: 0 1;
    }
    .project-group AgentPane {
        height: 1fr;
        width: 1fr;
    }
    .project-tab-body {
        height: 1fr;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        # panes[i] = AgentPane; we track in insertion order
        self.panes: list[AgentPane] = []
        self.current_idx = -1
        self._tabbed: TabbedContent | None = None
        self._all_body: Horizontal | None = None
        self._project_groups: dict[str, ProjectGroup] = {}
        self._project_bodies: dict[str, Horizontal] = {}

    def compose(self) -> ComposeResult:
        self._tabbed = TabbedContent(initial="tab-all")
        with self._tabbed:
            with TabPane("All", id="tab-all"):
                self._all_body = Horizontal(id="all-body")
                yield self._all_body
        yield self._tabbed

    async def add_pane(self, pane: AgentPane, project_key: str, project_display: str) -> None:
        """Add an agent pane. Creates the project tab on first add for that project."""
        self.panes.append(pane)
        self.current_idx = len(self.panes) - 1

        # All-tab: group panes by project so siblings cluster
        if project_key not in self._project_groups:
            group = ProjectGroup(project_key, project_display)
            self._project_groups[project_key] = group
            if self._all_body:
                await self._all_body.mount(group)
        # Reuse a clone-free reference - the same AgentPane can't live in two
        # places, so we keep it in the project-group for the All view AND
        # mirror it as the per-project tab body content.
        group = self._project_groups[project_key]
        await group.mount(pane)

        # Per-project tab: create on first use
        if project_key not in self._project_bodies and self._tabbed is not None:
            tab_id = f"tab-{project_key}"
            new_pane = TabPane(project_display, id=tab_id)
            await self._tabbed.add_pane(new_pane)
            body = Horizontal(classes="project-tab-body")
            await new_pane.mount(body)
            self._project_bodies[project_key] = body
        # NOTE: we don't double-mount the AgentPane into the per-project tab
        # because a Textual widget can only be mounted once. The per-project
        # tab gets a lightweight reference Static; the full pane lives in the
        # All tab. Future improvement: ContentSwitcher reparenting.
        if project_key in self._project_bodies:
            ref = Static(
                f"[b]{pane.agent_name}[/b] :: {pane.mode}  "
                f"[dim](pane lives in All tab; switch back to interact)[/dim]",
                markup=True,
                classes="agent-ref",
            )
            await self._project_bodies[project_key].mount(ref)

    def cycle(self, delta: int = 1) -> None:
        if not self.panes:
            return
        self.current_idx = (self.current_idx + delta) % len(self.panes)

    @property
    def current_pane(self) -> AgentPane | None:
        if 0 <= self.current_idx < len(self.panes):
            return self.panes[self.current_idx]
        return None

    def panes_for_project(self, project_key: str) -> list[AgentPane]:
        return [p for p in self.panes if getattr(p, "project_key", None) == project_key]

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
