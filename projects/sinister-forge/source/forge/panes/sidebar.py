# Sinister Forge :: panes/sidebar.py — Sinister Panel-style left rail
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Operator 2026-05-21: *"sidebar: two tabs one called agents that has infi
# scroll and everything we built here... then other tab for adb. just simple
# need to see devices"*.

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import Static


class Sidebar(Vertical):
    """Two-tab left rail. Posts a TabSelected message when the operator clicks."""

    DEFAULT_CSS = """
    Sidebar {
        width: 18;
        background: #0E0A14;
        border-right: solid #3A2A55;
        padding: 1 0;
    }
    Sidebar .sidebar-tab {
        height: 3;
        margin: 0 1 1 1;
        padding: 1 1 0 2;
        background: #15131A;
        border: round #3A2A55;
        color: #999AB0;
    }
    Sidebar .sidebar-tab.-active {
        background: #2A1F3D;
        color: #A06EFF;
        border: round #A06EFF;
        text-style: bold;
    }
    Sidebar #sidebar-brand {
        height: 3;
        margin: 0 1 1 1;
        padding: 1 1 0 2;
        color: #A06EFF;
        text-style: bold;
        background: #1C1626;
        border: round #7A3DD4;
    }
    Sidebar #sidebar-footer {
        dock: bottom;
        height: 1;
        margin: 0 1;
        color: #6E6E84;
    }
    """

    TABS = ("agents", "adb")

    class TabSelected(Message):
        def __init__(self, tab: str) -> None:
            self.tab = tab
            super().__init__()

    def __init__(self, active: str = "agents") -> None:
        super().__init__()
        self.active = active if active in self.TABS else "agents"

    def compose(self) -> ComposeResult:
        yield Static("[bold]◈ EVE[/]\n[dim]operator[/]", id="sidebar-brand")
        self._tab_widgets = {}
        for name in self.TABS:
            label = self._label_for(name)
            w = Static(label, classes="sidebar-tab")
            w.tab_name = name  # type: ignore[attr-defined]
            if name == self.active:
                w.add_class("-active")
            self._tab_widgets[name] = w
            yield w
        yield Static("[dim]/help · ctrl+p[/]", id="sidebar-footer")

    @staticmethod
    def _label_for(name: str) -> str:
        # Add icon + label, two lines so the tab feels chunky like Sinister Panel.
        icons = {"agents": "👤", "adb": "📱"}
        return f"[bold]{name.upper()}[/]\n[dim]{icons.get(name, '·')}[/]"

    def on_click(self, event) -> None:
        target = event.widget
        # Bubble up to find the .sidebar-tab ancestor
        node = target
        while node is not None and not getattr(node, "tab_name", None):
            node = getattr(node, "parent", None)
        if node is None:
            return
        name = getattr(node, "tab_name", None)
        if not name or name == self.active:
            return
        self.select(name)

    def select(self, name: str) -> None:
        if name not in self.TABS or name == self.active:
            return
        # toggle highlight
        self._tab_widgets[self.active].remove_class("-active")
        self._tab_widgets[name].add_class("-active")
        self.active = name
        self.post_message(self.TabSelected(name))
