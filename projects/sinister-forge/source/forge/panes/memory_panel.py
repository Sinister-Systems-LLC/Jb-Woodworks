# Sinister Forge :: panes/memory_panel.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Side panel showing the agent's recent memory (last brain entries,
# cross-agent messages, resume-points relevant to the current project).
# Toggled with Ctrl+M. Sits in the overlay layer.

from __future__ import annotations

import json
import time
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static

from forge.theme import PURPLE_HALO, CYAN, GREEN, SOFT, DIM, LIGHT_PURPLE


SANCTUM_ROOT = Path("D:/Sinister Sanctum")
BRAIN_INDEX = SANCTUM_ROOT / "_shared-memory" / "knowledge" / "_INDEX.md"
CROSS_AGENT = SANCTUM_ROOT / "_shared-memory" / "cross-agent"
RESUME_DIR = SANCTUM_ROOT / "_shared-memory" / "resume-points"


class MemoryPanel(VerticalScroll):
    """Live mini brain-feed for the current agent's project context."""

    DEFAULT_CSS = ""

    def __init__(self) -> None:
        super().__init__(id="memory-panel")
        self._project_key = ""
        self._project_display = ""

    def compose(self) -> ComposeResult:
        yield Static("◈ MEMORY", classes="memory-title", id="memory-title")
        yield Static("(no project selected)", classes="memory-row", id="memory-empty")

    def on_mount(self) -> None:
        self.set_interval(15.0, self.refresh_content)

    def set_project(self, key: str, display: str) -> None:
        self._project_key = key
        self._project_display = display
        self.refresh_content()

    def refresh_content(self) -> None:
        # Wipe existing rows (except title)
        for child in list(self.children):
            if isinstance(child, Static) and child.id != "memory-title":
                child.remove()

        rows: list[tuple[str, str]] = []
        # Brain entries tagged with project
        if self._project_key and BRAIN_INDEX.exists():
            text = BRAIN_INDEX.read_text(encoding="utf-8", errors="replace")
            hits = 0
            for line in text.splitlines():
                if not line.startswith("| "):
                    continue
                if self._project_key.lower() in line.lower():
                    parts = [p.strip() for p in line.strip("| ").split("|")]
                    if parts and parts[0] not in ("Slug", "---"):
                        rows.append(("brain", parts[0][:34]))
                        hits += 1
                if hits >= 5:
                    break

        # Recent cross-agent messages mentioning the project
        if self._project_key and CROSS_AGENT.exists():
            files = sorted(CROSS_AGENT.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
            hits = 0
            for f in files[:30]:
                if self._project_key in f.stem.lower():
                    rows.append(("xa", f.stem[:34]))
                    hits += 1
                if hits >= 5:
                    break

        # Latest resume-point
        if self._project_display:
            rdir = RESUME_DIR / self._project_display
            if rdir.exists():
                rpts = sorted(rdir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
                if rpts:
                    rows.append(("resume", rpts[0].stem[:34]))

        if not rows:
            self.mount(Static(
                f"[{SOFT}]no memory for[/] [{PURPLE_HALO}]{self._project_display or '(none)'}[/]",
                classes="memory-row", markup=True,
            ))
            return

        seen: set[str] = set()
        for kind, label in rows:
            if label in seen:
                continue
            seen.add(label)
            color = {"brain": LIGHT_PURPLE, "xa": CYAN, "resume": GREEN}.get(kind, SOFT)
            icon = {"brain": "◆", "xa": "▸", "resume": "★"}.get(kind, "·")
            self.mount(Static(
                f"[{color}]{icon}[/] [{SOFT}]{kind}[/]  {label}",
                classes="memory-row", markup=True,
            ))
