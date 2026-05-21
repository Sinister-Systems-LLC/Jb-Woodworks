# Sinister Forge :: panes/sidebar.py — Sinister Panel-style left rail (v2)
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Operator 2026-05-21 (image 28 = Sinister Panel dashboard reference):
#   *"two tabs: agents (system we are building out with tabs per project, tab
#   to view all, all things like that i asked for) and phones (all adb support
#   and what not)"*  +  *"why do you keep failing to do this"*.
#
# v2 Sinister Panel parity (matches snap.sinijkr.com sidebar):
#   - Mascot header (purple-bg block, 3-line ASCII devil + "EVE" label)
#   - Section header `WORKSPACES` (bold/dim)
#   - 2 nav items: Agents `[●]`, Phones `[#]`. Active = purple bg + bright text.
#   - Section header `STATUS` (dim)
#   - 3 read-only status rows: agents / inbox / brain (live counters refreshed
#     every 5s via the same heartbeat/inbox helpers the bottom statusbar uses).
#   - Footer: `/help · ctrl+p`
#   - Width 22 cols (was 18 — fits the nav labels comfortably).
#
# Back-compat: TabSelected(Message) + select(tab) public API unchanged.
# TABS tuple updated to ("agents", "phones") per operator (adb → phones).

from __future__ import annotations

import time
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import Static

from forge.theme import (
    BG, BG_GLASS_1, BG_GLASS_2, BG_GLOW, BORDER_GLASS,
    PURPLE_DARK, PURPLE_DEEP, PURPLE_ACCENT, PURPLE_HALO,
    LIGHT_PURPLE, SOFT, DIM, GREEN_ACCENT,
)


SANCTUM_ROOT = Path("D:/Sinister Sanctum")
HEARTBEATS_DIR = SANCTUM_ROOT / "_shared-memory" / "heartbeats"
INBOX_DIR = SANCTUM_ROOT / "_shared-memory" / "inbox"
KNOWLEDGE_DIR = SANCTUM_ROOT / "_shared-memory" / "knowledge"

HEARTBEAT_ALIVE_SEC = 1800  # 30 min — matches statusbar.py


def _count_agents_live() -> int:
    try:
        if not HEARTBEATS_DIR.exists():
            return 0
        now = time.time()
        return sum(
            1 for hb in HEARTBEATS_DIR.glob("*.json")
            if (now - hb.stat().st_mtime) < HEARTBEAT_ALIVE_SEC
        )
    except Exception:
        return 0


def _count_inbox() -> int:
    try:
        if not INBOX_DIR.exists():
            return 0
        return sum(1 for _ in INBOX_DIR.rglob("*.json"))
    except Exception:
        return 0


def _count_brain() -> int:
    try:
        if not KNOWLEDGE_DIR.exists():
            return 0
        return sum(1 for _ in KNOWLEDGE_DIR.glob("*.md"))
    except Exception:
        return 0


# 3-line stylized purple devil mascot (box-drawing). Renders inside the
# mascot block in the sidebar header — a tiny purple devil silhouette
# made from box-drawing glyphs (no emoji — operator screenshot 27 showed
# emoji glyphs rendering as empty rectangles in the console font).
MASCOT_ART = (
    "[bold]  ▄▀█▀▄  [/]\n"
    "[bold] █ ◉ ◉ █ [/]\n"
    "[bold]  ▀▄▄▄▀  [/]"
)


class Sidebar(Vertical):
    """Sinister Panel-style left rail (v2).

    Layout (top → bottom):
        ┌──────────────────┐
        │   mascot block   │   (purple-dark bg, accent-purple border)
        │      "EVE"       │
        ├──────────────────┤
        │  WORKSPACES      │   (dim section header)
        │  [●] Agents      │   (nav item — active = purple wash)
        │  [#] Phones      │   (nav item)
        ├──────────────────┤
        │  STATUS          │   (dim section header)
        │  agents: N live  │
        │  inbox: N        │
        │  brain: N        │
        ├──────────────────┤
        │  /help · ctrl+p  │   (footer, docked bottom)
        └──────────────────┘
    """

    DEFAULT_CSS = f"""
    Sidebar {{
        width: 22;
        background: {BG};
        border-right: solid {BORDER_GLASS};
        padding: 0;
    }}

    /* ===== Mascot header ===== */
    Sidebar #sidebar-mascot {{
        height: 5;
        margin: 1 1 0 1;
        padding: 0 0;
        background: {PURPLE_DARK};
        border: round {PURPLE_ACCENT};
        color: {PURPLE_HALO};
        content-align: center middle;
        text-align: center;
    }}
    Sidebar #sidebar-mascot-label {{
        height: 1;
        margin: 0 1 1 1;
        color: {PURPLE_ACCENT};
        text-style: bold;
        text-align: center;
    }}

    /* ===== Section headers ===== */
    Sidebar .sidebar-section {{
        height: 1;
        margin: 1 2 0 2;
        color: {DIM};
        text-style: bold;
    }}

    /* ===== Nav items ===== */
    Sidebar .sidebar-nav {{
        height: 3;
        margin: 0 1 0 1;
        padding: 1 1 1 2;
        background: {BG_GLASS_1};
        border: round {BORDER_GLASS};
        color: {SOFT};
        text-align: left;
    }}
    Sidebar .sidebar-nav.-active {{
        background: {BG_GLOW};
        color: {PURPLE_HALO};
        border: round {PURPLE_ACCENT};
        text-style: bold;
    }}
    Sidebar .sidebar-nav:hover {{
        border: round {PURPLE_ACCENT};
    }}

    /* ===== Status rows ===== */
    Sidebar .sidebar-status {{
        height: 1;
        margin: 0 2 0 2;
        color: {LIGHT_PURPLE};
    }}
    Sidebar .sidebar-status.-fresh {{
        color: {GREEN_ACCENT};
    }}

    /* ===== Footer ===== */
    Sidebar #sidebar-footer {{
        dock: bottom;
        height: 1;
        margin: 0 2 1 2;
        color: {DIM};
        text-align: left;
    }}
    """

    # Operator 2026-05-21: tabs renamed adb→phones. workstation tab dropped
    # from the sidebar (still reachable via /workstation command + RKOJ.exe).
    TABS = ("agents", "phones")

    # Display glyph + label for each tab. Plain ASCII glyphs (no emoji — see
    # operator screenshot 27 where emoji rendered as rectangles in console font).
    _NAV_DEF = {
        "agents": ("●", "Agents"),
        "phones": ("#", "Phones"),
    }

    class TabSelected(Message):
        def __init__(self, tab: str) -> None:
            self.tab = tab
            super().__init__()

    def __init__(self, active: str = "agents") -> None:
        super().__init__()
        self.active = active if active in self.TABS else "agents"
        self._tab_widgets: dict[str, Static] = {}
        self._status_widgets: dict[str, Static] = {}

    def compose(self) -> ComposeResult:
        # Mascot header: 3-line ASCII devil + "EVE" label below
        yield Static(MASCOT_ART, id="sidebar-mascot")
        yield Static("EVE", id="sidebar-mascot-label")

        # Section: WORKSPACES
        yield Static("WORKSPACES", classes="sidebar-section")
        for name in self.TABS:
            label = self._label_for(name)
            w = Static(label, classes="sidebar-nav")
            w.tab_name = name  # type: ignore[attr-defined]
            if name == self.active:
                w.add_class("-active")
            self._tab_widgets[name] = w
            yield w

        # Section: STATUS — read-only live counters
        yield Static("STATUS", classes="sidebar-section")
        self._status_widgets["agents"] = Static("", classes="sidebar-status")
        self._status_widgets["inbox"] = Static("", classes="sidebar-status")
        self._status_widgets["brain"] = Static("", classes="sidebar-status")
        yield self._status_widgets["agents"]
        yield self._status_widgets["inbox"]
        yield self._status_widgets["brain"]

        # Footer
        yield Static("[dim]/help · ctrl+p[/]", id="sidebar-footer")

    def on_mount(self) -> None:
        self._refresh_status()
        # Refresh status counters every 5s — matches the bottom statusbar cadence.
        self.set_interval(5.0, self._refresh_status)

    def _refresh_status(self) -> None:
        agents = _count_agents_live()
        inbox = _count_inbox()
        brain = _count_brain()
        agents_w = self._status_widgets.get("agents")
        inbox_w = self._status_widgets.get("inbox")
        brain_w = self._status_widgets.get("brain")
        if agents_w:
            agents_w.update(f"agents: [bold]{agents}[/] live")
            if agents > 0:
                agents_w.add_class("-fresh")
            else:
                agents_w.remove_class("-fresh")
        if inbox_w:
            inbox_w.update(f"inbox: [bold]{inbox}[/]")
        if brain_w:
            brain_w.update(f"brain: [bold]{brain}[/]")

    @classmethod
    def _label_for(cls, name: str) -> str:
        glyph, label = cls._NAV_DEF.get(name, ("·", name.capitalize()))
        # `[X]  Label` — glyph in halo purple, label in current row color
        # (the .-active class re-colors both via parent CSS).
        return f"[{PURPLE_HALO}][{glyph}][/]  [bold]{label}[/]"

    def on_click(self, event) -> None:
        target = event.widget
        # Bubble up to find the .sidebar-nav ancestor
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
        if self.active in self._tab_widgets:
            self._tab_widgets[self.active].remove_class("-active")
        if name in self._tab_widgets:
            self._tab_widgets[name].add_class("-active")
        self.active = name
        self.post_message(self.TabSelected(name))
