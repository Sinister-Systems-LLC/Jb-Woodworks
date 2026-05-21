# Sinister Forge :: panes/columns.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# PH18 niri-style scrollable-columns container per
# _shared-memory/knowledge/niri-scrollable-column-pattern.md.
#
# Each AgentPane becomes one full-height column in a horizontally-scrollable
# strip. The currently-focused column is centered; the column to either side
# remains partially visible (parallax slice) so the operator never loses
# spatial awareness that more agents exist off-screen.
#
# This is the operator-asked replacement for the All-tab Horizontal child
# (per-project tabs remain unchanged - they fit the bounded-categorical-
# heterogeneous decision rule from the brain entry).

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import HorizontalScroll, Vertical
from textual.widgets import Static

from forge.panes.agent_pane import AgentPane
from forge.theme import PROJECT_BORDER_PALETTE, PURPLE_BRIGHT


class AgentColumn(Vertical):
    """One niri-column: project-tinted top strip + the AgentPane underneath.

    The column owns the AgentPane (Textual widgets can only live in one
    parent at a time, so this is the canonical location). The per-project
    tab body holds only a lightweight reference Static (see tabs.py).
    """

    def __init__(self, pane: AgentPane, project_key: str, project_display: str) -> None:
        super().__init__(classes="agent-column")
        self.pane = pane
        self.project_key = project_key
        self.project_display = project_display
        color = PROJECT_BORDER_PALETTE.get(project_key, PROJECT_BORDER_PALETTE["_default"])
        self.styles.border = ("round", color)
        # Top metadata strip per niri-primitive #3
        self.border_title = (
            f"  {project_display}  ::  {pane.agent_name}  "
        )

    def compose(self) -> ComposeResult:
        yield self.pane


class ScrollableColumns(HorizontalScroll):
    """niri-style scrollable column strip. Each child = one full-height column.

    Implements the 7 primitives from `niri-scrollable-column-pattern.md`:
      1. Horizontal scroll region (HorizontalScroll provides snap-on-scroll-to)
      2. Always-one-visible invariant (placeholder when empty)
      3. Per-column metadata strip (border_title with project color)
      4. Ctrl+Left/Right scroll one column; Ctrl+Shift+Left/Right move column
      5. Vertical mousewheel scrolls the pane RichLog, horizontal scrolls strip
         (Textual's default for HorizontalScroll inside scrollable child)
      6. Spawn-policy: appends to the right, grouped by project so siblings
         stay adjacent (matches the prior All-tab project-group behavior)
      7. Resume-point persistence via app-level callback (left for caller)
    """

    DEFAULT_CSS = """
    ScrollableColumns {
        height: 1fr;
        background: $surface;
        scrollbar-size-horizontal: 1;
    }
    .agent-column {
        height: 1fr;
        width: 64;
        min-width: 48;
        margin: 0 1;
        padding: 0;
    }
    .agent-column AgentPane {
        height: 1fr;
        width: 1fr;
        margin: 0;
    }
    .empty-strip {
        width: 1fr;
        height: 1fr;
        content-align: center middle;
        color: $text-muted;
        text-style: italic;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.columns: list[AgentColumn] = []
        self._focused_idx: int = -1
        self._placeholder: Static | None = None

    def compose(self) -> ComposeResult:
        # Primitive #2: always-one-visible invariant - show placeholder while empty
        self._placeholder = Static(
            "no agents · Ctrl+W to spawn",
            classes="empty-strip",
        )
        yield self._placeholder

    @property
    def focused_idx(self) -> int:
        return self._focused_idx

    @property
    def focused_column(self) -> AgentColumn | None:
        if 0 <= self._focused_idx < len(self.columns):
            return self.columns[self._focused_idx]
        return None

    async def add_pane(self, pane: AgentPane, project_key: str, project_display: str) -> None:
        """Add a new column. Sibling-grouping policy: insert adjacent to the
        last existing column with the same project_key; otherwise append.
        """
        column = AgentColumn(pane, project_key, project_display)
        # remove placeholder once a real column joins
        if self._placeholder is not None:
            try:
                await self._placeholder.remove()
            except Exception:
                pass
            self._placeholder = None
        # Find last index for this project_key to maintain grouping
        insert_after = -1
        for i, c in enumerate(self.columns):
            if c.project_key == project_key:
                insert_after = i
        if insert_after == -1:
            self.columns.append(column)
            await self.mount(column)
        else:
            self.columns.insert(insert_after + 1, column)
            # Textual: re-mount in order is heavy; mount then reorder via DOM moves
            await self.mount(column)
            # Move into position. children is read-only tuple; we use move_child.
            try:
                ref_widget = self.columns[insert_after + 2] if insert_after + 2 < len(self.columns) else None
                if ref_widget is not None:
                    self.move_child(column, before=ref_widget)
            except Exception:
                pass
        self._focused_idx = self.columns.index(column)
        self._scroll_focused_into_view()

    def cycle(self, delta: int = 1) -> AgentColumn | None:
        if not self.columns:
            return None
        self._focused_idx = (self._focused_idx + delta) % len(self.columns)
        self._scroll_focused_into_view()
        return self.focused_column

    def swap_focused(self, delta: int) -> None:
        """Move the focused column +/- delta within the strip (primitive #4 second half)."""
        if not self.columns or self._focused_idx < 0:
            return
        new_idx = (self._focused_idx + delta) % len(self.columns)
        if new_idx == self._focused_idx:
            return
        col = self.columns.pop(self._focused_idx)
        self.columns.insert(new_idx, col)
        # Reorder DOM
        try:
            if new_idx + 1 < len(self.columns):
                self.move_child(col, before=self.columns[new_idx + 1])
            else:
                self.move_child(col, after=self.columns[-2] if len(self.columns) > 1 else None)
        except Exception:
            pass
        self._focused_idx = new_idx
        self._scroll_focused_into_view()

    def remove_focused(self) -> AgentColumn | None:
        if not self.columns or self._focused_idx < 0:
            return None
        col = self.columns.pop(self._focused_idx)
        try:
            col.remove()
        except Exception:
            pass
        if self._focused_idx >= len(self.columns):
            self._focused_idx = len(self.columns) - 1
        if not self.columns:
            # Restore placeholder
            self._placeholder = Static(
                "no agents · Ctrl+W to spawn",
                classes="empty-strip",
            )
            try:
                self.mount(self._placeholder)
            except Exception:
                pass
        else:
            self._scroll_focused_into_view()
        return col

    def panes_for_project(self, project_key: str) -> list[AgentPane]:
        return [c.pane for c in self.columns if c.project_key == project_key]

    @property
    def panes(self) -> list[AgentPane]:
        """All AgentPanes in column-order (alias for caller compat with TabbedMultiPane)."""
        return [c.pane for c in self.columns]

    def _scroll_focused_into_view(self) -> None:
        col = self.focused_column
        if col is None:
            return
        # Textual: scroll_to_widget centers the child as best it can
        try:
            self.scroll_to_widget(col, animate=True, center=True)
        except Exception:
            pass
