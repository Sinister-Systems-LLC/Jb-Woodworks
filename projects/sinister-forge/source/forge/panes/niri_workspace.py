# Sinister Forge :: panes/niri_workspace.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# v1.1.0 of niri-scrollable-column-pattern (see
# `_shared-memory/knowledge/niri-scrollable-column-pattern.md`).
#
# Where v1 (panes/columns.py) gave us ONE-PANE-PER-COLUMN, this module ships
# the full niri-wm model the operator asked for: WORKSPACE COLUMNS that each
# hold 1..N stacked panes (niri's "column-with-stacked-windows" gesture).
#
# Concept port from:
#   - https://github.com/YaLTeR/niri          (scrollable-tiling Wayland WM)
#   - https://github.com/1jehuang/niri-workspaces-rs (workspace navigator)
#
# Workspace == one Vertical column of width=80 holding 1..N AgentPanes stacked
#              vertically. Multiple workspaces sit side-by-side inside a
#              horizontally-scrollable strip with snap-to-column.
#
# Keybindings (mounted at the App level, forwarded here):
#   Ctrl+Left  / Ctrl+Right        — move focus between workspaces
#   Ctrl+Shift+Left / Ctrl+Right   — move active pane between workspaces
#   Ctrl+1..9                      — jump to workspace N (1-indexed)
#   Ctrl+T                         — open a new (empty) workspace
#   Ctrl+W                         — close current workspace (defers to App for
#                                    Sanctum's Ctrl+W = spawn convention)
#
# Status row at top renders: `[ws 1] [ws 2] · [ws 3*] · [ws 4]` (active *).
#
# Pure Python + textual — niri-workspaces-rs concept ported without Rust.

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import ScrollableContainer, Vertical
from textual.message import Message
from textual.widgets import Static

from forge.theme import (
    BORDER_GLASS,
    PROJECT_BORDER_PALETTE,
    PURPLE_BRIGHT,
    PURPLE_DEEP,
)

if TYPE_CHECKING:
    from forge.panes.agent_pane import AgentPane


WORKSPACE_WIDTH = 80


class WorkspaceColumn(Vertical):
    """One workspace = one Vertical column holding 1..N AgentPanes stacked.

    Mirrors niri's column-of-stacked-windows. Panes inside flex equally on the
    vertical axis (Textual `height: 1fr` per child) so 1 pane fills the column,
    2 panes split it in half, 3 panes into thirds, etc.

    Width is REACTIVE on workspace count (operator directive 2026-05-21):
      - 1 workspace total → width 1fr (expand to fill agent tab)
      - 2+ workspaces      → width WORKSPACE_WIDTH=80 (niri snap columns)
    The grid calls `set_solo(True|False)` whenever the workspace count crosses
    the 1↔2 boundary so the single-console UX is "console fills the tab".
    """

    DEFAULT_CSS = f"""
    WorkspaceColumn {{
        width: {WORKSPACE_WIDTH};
        min-width: 60;
        height: 1fr;
        margin: 0 1;
        padding: 0;
        border: round {BORDER_GLASS};
        background: $surface;
    }}
    WorkspaceColumn.-solo {{
        width: 1fr;
        min-width: 0;
        margin: 0;
    }}
    WorkspaceColumn.-active {{
        border: round {PURPLE_BRIGHT};
    }}
    WorkspaceColumn > AgentPane {{
        height: 1fr;
        width: 1fr;
        margin: 0;
    }}
    """

    def __init__(self, index: int, title: str | None = None) -> None:
        super().__init__()
        self.workspace_index = index
        self.title = title or f"ws {index + 1}"
        self.panes: list["AgentPane"] = []
        self.border_title = f"  {self.title}  "

    def set_active(self, active: bool) -> None:
        if active:
            self.add_class("-active")
            self.border_title = f"  {self.title} *  "
        else:
            self.remove_class("-active")
            self.border_title = f"  {self.title}  "

    def set_solo(self, solo: bool) -> None:
        """Toggle full-width 'console fills the tab' mode (operator directive).

        Called by NiriWorkspaceGrid whenever the workspace count transitions
        across the 1↔2 boundary so the only-workspace looks like a real
        console, not a niri snap-column.
        """
        if solo:
            self.add_class("-solo")
        else:
            self.remove_class("-solo")

    async def attach_pane(self, pane: "AgentPane") -> None:
        self.panes.append(pane)
        await self.mount(pane)

    async def detach_pane(self, pane: "AgentPane") -> "AgentPane | None":
        if pane not in self.panes:
            return None
        self.panes.remove(pane)
        # Detach from DOM but DO NOT remove() — caller will re-mount it elsewhere.
        try:
            pane.remove()
        except Exception:
            pass
        return pane


class WorkspaceStatusRow(Static):
    """Top-of-strip status indicator: `[ws 1] [ws 2] · [ws 3*] · [ws 4]`.

    AUTO-HIDES when workspace count <= 1 (operator directive 2026-05-21:
    "agents tab = ONE console view"). The strip only earns its dock space
    once a SECOND workspace appears (Ctrl+T), so the default Agents tab is
    a single console without confusing dead-space rectangles.
    """

    DEFAULT_CSS = f"""
    WorkspaceStatusRow {{
        dock: top;
        height: 1;
        padding: 0 1;
        background: $surface-darken-1;
        color: {PURPLE_BRIGHT};
    }}
    WorkspaceStatusRow.-hidden {{
        display: none;
    }}
    """

    def render_status(self, count: int, active: int) -> None:
        # Auto-hide when 0 or 1 workspaces — operator wants console-only by default.
        if count <= 1:
            self.add_class("-hidden")
        else:
            self.remove_class("-hidden")
        if count == 0:
            self.update("[dim]no workspaces · Ctrl+T to open[/]")
            return
        parts: list[str] = []
        for i in range(count):
            mark = "*" if i == active else " "
            if i == active:
                parts.append(f"[b][ws {i + 1}{mark}][/]")
            else:
                parts.append(f"[dim][ws {i + 1}{mark}][/]")
        self.update(" · ".join(parts))


class NiriWorkspaceGrid(ScrollableContainer):
    """niri-style horizontally-scrollable workspace strip.

    Children = WorkspaceColumn instances. Each WorkspaceColumn can hold 1..N
    AgentPanes stacked vertically. The grid snaps focused workspace into view
    via `scroll_to_widget(center=True)`.

    Caller-facing surface (compatible-ish with TabbedMultiPane to ease swap):
      - add_pane(pane, project_key, project_display)  ← appends to active ws
      - panes                                          ← all panes flattened
      - current_pane / current_idx                     ← active ws's first pane
      - cycle(delta) / swap_focused(delta)             ← workspace nav / pane move
      - new_workspace() / close_workspace()
      - jump_to(n)
    """

    BINDINGS = [
        Binding("ctrl+right", "next_workspace", "ws→", show=False),
        Binding("ctrl+left", "prev_workspace", "ws←", show=False),
        Binding("ctrl+shift+right", "move_pane_right", "pane→", show=False),
        Binding("ctrl+shift+left", "move_pane_left", "pane←", show=False),
        Binding("ctrl+t", "new_workspace", "new ws", show=False),
    ] + [
        Binding(f"ctrl+{n}", f"jump_to_{n}", f"ws{n}", show=False)
        for n in range(1, 10)
    ]

    DEFAULT_CSS = f"""
    NiriWorkspaceGrid {{
        height: 1fr;
        width: 1fr;
        background: $surface;
        scrollbar-size-horizontal: 1;
        overflow-x: auto;
        overflow-y: hidden;
    }}
    NiriWorkspaceGrid .empty-grid {{
        width: 1fr;
        height: 1fr;
        content-align: center middle;
        color: {BORDER_GLASS};
        text-style: italic;
    }}
    """

    class WorkspaceChanged(Message):
        def __init__(self, index: int) -> None:
            self.index = index
            super().__init__()

    def __init__(self) -> None:
        super().__init__()
        self.workspaces: list[WorkspaceColumn] = []
        self._active_idx: int = -1
        self._status_row: WorkspaceStatusRow = WorkspaceStatusRow()
        self._placeholder: Static | None = None
        # Compat shims for callers written against TabbedMultiPane. They let
        # forge/app.py call `self._tabs._columns.remove_focused()` and inspect
        # `self._tabs._tabbed.active` without crashing when the niri grid is
        # in place of the older tab container.
        self._columns = self  # remove_focused() is provided below
        self._tabbed = None

    # ---- lifecycle ----

    def compose(self) -> ComposeResult:
        # Operator directive 2026-05-21: "agents tab = ONE console view with
        # all jcode features". Default to a single solo workspace ready for the
        # first pane — no empty workspace strip, no 6-ws dead-space. Strip
        # auto-appears when Ctrl+T opens a second workspace.
        yield self._status_row
        first = WorkspaceColumn(index=0, title="ws 1")
        first.set_solo(True)
        first.set_active(True)
        self.workspaces.append(first)
        self._active_idx = 0
        yield first
        # Render status (will auto-hide since count == 1)
        self._status_row.render_status(1, 0)

    # ---- public state ----

    @property
    def active_idx(self) -> int:
        return self._active_idx

    @property
    def active_workspace(self) -> WorkspaceColumn | None:
        if 0 <= self._active_idx < len(self.workspaces):
            return self.workspaces[self._active_idx]
        return None

    @property
    def panes(self) -> list["AgentPane"]:
        """All panes across every workspace in left-to-right, top-to-bottom order."""
        out: list["AgentPane"] = []
        for ws in self.workspaces:
            out.extend(ws.panes)
        return out

    @property
    def current_pane(self) -> "AgentPane | None":
        ws = self.active_workspace
        if ws and ws.panes:
            return ws.panes[0]
        return None

    @property
    def current_idx(self) -> int:
        return self._active_idx

    # ---- mutation ----

    async def new_workspace(self, title: str | None = None) -> WorkspaceColumn:
        """Append a new (empty) workspace and focus it.

        When the count crosses 1→2 we drop the `-solo` full-width class from
        the existing first workspace so both fit niri's snap-column model.
        """
        if self._placeholder is not None:
            try:
                await self._placeholder.remove()
            except Exception:
                pass
            self._placeholder = None
        # Crossing 1→2: revoke solo on existing workspace(s) so they collapse
        # back to the snap-column WORKSPACE_WIDTH=80.
        if len(self.workspaces) == 1:
            self.workspaces[0].set_solo(False)
        idx = len(self.workspaces)
        ws = WorkspaceColumn(index=idx, title=title)
        self.workspaces.append(ws)
        await self.mount(ws)
        self._set_active(idx)
        return ws

    async def close_workspace(self, index: int | None = None) -> None:
        """Close the workspace at `index` (default: active). Panes inside are
        removed too — caller is expected to terminate any subprocesses first.

        When the count crosses 2→1 we re-apply `-solo` to the last remaining
        workspace so the operator gets the full-width console view back.
        """
        if not self.workspaces:
            return
        target = self._active_idx if index is None else index
        if not (0 <= target < len(self.workspaces)):
            return
        ws = self.workspaces.pop(target)
        try:
            ws.remove()
        except Exception:
            pass
        # re-title remaining workspaces so labels stay 1-indexed contiguous
        for i, w in enumerate(self.workspaces):
            w.workspace_index = i
            w.title = f"ws {i + 1}"
        if not self.workspaces:
            self._active_idx = -1
            self._placeholder = Static(
                "no workspaces · Ctrl+T to open · Ctrl+W to spawn agent",
                classes="empty-grid",
            )
            try:
                await self.mount(self._placeholder)
            except Exception:
                pass
            self._status_row.render_status(0, -1)
            return
        # Crossing 2→1: the sole survivor gets solo full-width treatment.
        if len(self.workspaces) == 1:
            self.workspaces[0].set_solo(True)
        new_idx = min(target, len(self.workspaces) - 1)
        self._set_active(new_idx)

    async def add_pane(
        self, pane: "AgentPane", project_key: str = "", project_display: str = ""
    ) -> None:
        """Compat with TabbedMultiPane.add_pane — appends pane to the active
        workspace (or creates one if none exist)."""
        ws = self.active_workspace
        if ws is None:
            ws = await self.new_workspace(title=project_display or None)
        await ws.attach_pane(pane)
        self._set_active(self.workspaces.index(ws))

    async def move_active_pane(self, delta: int) -> None:
        """Move the FIRST pane of the active workspace to the adjacent ws.

        niri semantics: Ctrl+Shift+←/→ moves the focused window to the
        previous/next column. We approximate "focused pane within active
        workspace" as `ws.panes[0]` (top-most) since the textual port has no
        per-pane focus tracking yet.
        """
        if not self.workspaces or self._active_idx < 0:
            return
        ws = self.active_workspace
        if ws is None or not ws.panes:
            return
        target_idx = self._active_idx + delta
        if target_idx < 0 or target_idx >= len(self.workspaces):
            # niri: moving past the edge spawns a new workspace there
            if target_idx < 0:
                # prepend — count is about to grow, revoke solo from existing
                # workspaces so the new pair share niri snap-column widths.
                if len(self.workspaces) == 1:
                    self.workspaces[0].set_solo(False)
                new_ws = WorkspaceColumn(index=0, title="ws 1")
                self.workspaces.insert(0, new_ws)
                await self.mount(new_ws)
                # reindex
                for i, w in enumerate(self.workspaces):
                    w.workspace_index = i
                    w.title = f"ws {i + 1}"
                target_idx = 0
                self._active_idx += 1  # active shifted right because we prepended
            else:
                new_ws = await self.new_workspace()
                target_idx = self.workspaces.index(new_ws)
        target = self.workspaces[target_idx]
        pane = ws.panes[0]
        detached = await ws.detach_pane(pane)
        if detached is not None:
            await target.attach_pane(detached)
        self._set_active(target_idx)

    # ---- nav ----

    def cycle(self, delta: int = 1) -> None:
        if not self.workspaces:
            return
        new_idx = (self._active_idx + delta) % len(self.workspaces)
        self._set_active(new_idx)

    def swap_focused(self, delta: int = 1) -> None:
        """Compat shim: rebrands as 'move active pane' to match niri semantics."""
        # Schedule the async move; Textual allows fire-and-forget via call_later.
        try:
            self.call_later(self.move_active_pane, delta)
        except Exception:
            pass

    def jump_to(self, index_1_based: int) -> None:
        idx = index_1_based - 1
        if 0 <= idx < len(self.workspaces):
            self._set_active(idx)

    # ---- internal ----

    def _set_active(self, idx: int) -> None:
        if not self.workspaces:
            self._active_idx = -1
            self._status_row.render_status(0, -1)
            return
        idx = max(0, min(idx, len(self.workspaces) - 1))
        if self._active_idx == idx:
            # still re-render status to reflect rename/index changes
            self._status_row.render_status(len(self.workspaces), idx)
            return
        # toggle active class
        for i, ws in enumerate(self.workspaces):
            ws.set_active(i == idx)
        self._active_idx = idx
        self._status_row.render_status(len(self.workspaces), idx)
        self._scroll_active_into_view()
        try:
            self.post_message(self.WorkspaceChanged(idx))
        except Exception:
            pass

    def _scroll_active_into_view(self) -> None:
        ws = self.active_workspace
        if ws is None:
            return
        try:
            # snap=True isn't part of Textual's scroll_to_widget kwargs, but
            # center=True+animate=False approximates niri's snap-to-column.
            self.scroll_to_widget(ws, animate=True, center=True)
        except Exception:
            pass

    # ---- actions (bound at this widget OR forwarded from App) ----

    async def action_next_workspace(self) -> None:
        self.cycle(1)

    async def action_prev_workspace(self) -> None:
        self.cycle(-1)

    async def action_move_pane_right(self) -> None:
        await self.move_active_pane(1)

    async def action_move_pane_left(self) -> None:
        await self.move_active_pane(-1)

    async def action_new_workspace(self) -> None:
        await self.new_workspace()

    # ---- TabbedMultiPane compat surface ----

    def remove_focused(self) -> None:
        """Compat with ScrollableColumns.remove_focused() — closes the active
        workspace, which drops every pane in it. Used by app.action_close_agent.
        """
        try:
            self.call_later(self.close_workspace)
        except Exception:
            pass

    def panes_for_project(self, project_key: str) -> list["AgentPane"]:
        out: list["AgentPane"] = []
        for ws in self.workspaces:
            for pane in ws.panes:
                if getattr(pane, "project_key", None) == project_key:
                    out.append(pane)
        return out

    def current_project_key(self) -> str | None:
        cur = self.current_pane
        return getattr(cur, "project_key", None) if cur else None


# Generate `action_jump_to_<n>` methods for n in 1..9 so the Ctrl+<n>
# bindings declared in BINDINGS resolve to real callables. Done at module
# import so the methods exist before Textual binds them.
def _install_jump_actions() -> None:
    for _n in range(1, 10):
        def _make(idx: int):
            async def _action(self) -> None:  # type: ignore[no-redef]
                self.jump_to(idx)
            return _action
        setattr(NiriWorkspaceGrid, f"action_jump_to_{_n}", _make(_n))


_install_jump_actions()
