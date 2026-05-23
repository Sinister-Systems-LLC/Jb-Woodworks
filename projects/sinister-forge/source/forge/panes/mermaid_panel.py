# Sinister Forge :: panes/mermaid_panel.py
# Author: RKOJ-ELENO :: 2026-05-23
# License: AGPL-3.0-or-later
#
# In-TUI Mermaid diagram surface — flips jcode-parity matrix row 15 from
# 🚧 → ✅. Walks the same render cache that the `/mermaid` slash + the
# `forge.mermaid_render` wrapper write into, lists the most recent renders,
# and lets the operator open one in the OS image viewer with a click.
#
# Cache layout (per `forge/commands.py:_mermaid_renders_dir`):
#   _shared-memory/forge-memory/mermaid-renders/<UTC>.<ext>
#
# The slash + wrapper write .png + .html + .mmd siblings per render. This
# panel groups them by stem and shows one row per group, picking the most
# user-friendly target file when the operator opens.
#
# Toggle: Ctrl+D (bound in `forge/app.py`). Sits in the overlay layer next
# to MemoryPanel.

from __future__ import annotations

import os
import platform
import subprocess
import time
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static

from forge.theme import PURPLE_HALO, CYAN, GREEN, SOFT, DIM, LIGHT_PURPLE


SANCTUM_ROOT = Path("D:/Sinister Sanctum")
RENDERS_DIR = SANCTUM_ROOT / "_shared-memory" / "forge-memory" / "mermaid-renders"

# Display the N most-recent renders.
_MAX_ROWS = 12
# Order in which file extensions are preferred when opening a render group.
_OPEN_PRIORITY = (".png", ".svg", ".html", ".mmd")


def _open_with_os_viewer(path: Path) -> None:
    """Open *path* in the OS's default viewer (cross-platform best effort)."""
    try:
        if platform.system() == "Windows":
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except Exception:
        pass


def _human_age(secs: float) -> str:
    """`120` → `2m`, `7200` → `2h`, `90000` → `1d`."""
    if secs < 90:
        return f"{int(secs)}s"
    if secs < 5400:
        return f"{int(secs / 60)}m"
    if secs < 90000:
        return f"{int(secs / 3600)}h"
    return f"{int(secs / 86400)}d"


def _scan_render_groups() -> list[tuple[str, Path, float]]:
    """Walk RENDERS_DIR and return up to _MAX_ROWS groups, newest first.

    Each entry: ``(stem, primary_file_to_open, mtime)``. Stems are grouped so a
    single render (which writes .png + .html + .mmd siblings) shows as ONE row.
    """
    if not RENDERS_DIR.exists():
        return []
    # Group siblings by stem, picking the freshest file as the group's mtime.
    groups: dict[str, list[Path]] = {}
    try:
        for fp in RENDERS_DIR.iterdir():
            if not fp.is_file():
                continue
            if fp.suffix.lower() not in _OPEN_PRIORITY:
                continue
            groups.setdefault(fp.stem, []).append(fp)
    except OSError:
        return []

    rows: list[tuple[str, Path, float]] = []
    for stem, files in groups.items():
        # Pick the highest-priority extension for the "open" target.
        primary = next(
            (f for ext in _OPEN_PRIORITY for f in files if f.suffix.lower() == ext),
            files[0],
        )
        mtime = max(f.stat().st_mtime for f in files)
        rows.append((stem, primary, mtime))
    rows.sort(key=lambda r: r[2], reverse=True)
    return rows[:_MAX_ROWS]


class MermaidPanel(VerticalScroll):
    """Live list of recently-rendered Mermaid diagrams.

    Click a row to open the render in the OS image viewer. Auto-refreshes
    every 15s to surface new renders the operator just made via /mermaid.
    """

    DEFAULT_CSS = ""

    def __init__(self) -> None:
        super().__init__(id="mermaid-panel")
        self._rows_cache: list[tuple[str, Path, float]] = []

    def compose(self) -> ComposeResult:
        yield Static("◈ DIAGRAMS", classes="memory-title", id="mermaid-title")
        yield Static("(scanning…)", classes="memory-row", id="mermaid-empty")

    def on_mount(self) -> None:
        self.refresh_content()
        self.set_interval(15.0, self.refresh_content)

    def refresh_content(self) -> None:
        for child in list(self.children):
            if isinstance(child, Static) and child.id != "mermaid-title":
                child.remove()

        rows = _scan_render_groups()
        self._rows_cache = rows

        if not rows:
            self.mount(Static(
                f"[{SOFT}]no renders yet[/] [{DIM}]({RENDERS_DIR.name})[/]\n"
                f"[{DIM}]use /mermaid file <path>  or  /mermaid render <inline>[/]",
                classes="memory-row", markup=True,
            ))
            return

        now = time.time()
        for stem, primary, mtime in rows:
            age = _human_age(now - mtime)
            ext_label = primary.suffix.lstrip(".") or "?"
            label = stem[:34]
            self.mount(Static(
                f"[{LIGHT_PURPLE}]◆[/] [{SOFT}]{ext_label:>4}[/]  "
                f"[{CYAN}]{label}[/]  [{DIM}]{age}[/]",
                classes="memory-row", markup=True,
            ))

    def on_click(self, event) -> None:
        # Map vertical click position to the row index. Each row is one Static
        # under the title. Textual coordinates are document-relative; the title
        # is row 0 inside this scroll.
        y = max(event.y - 1, 0)
        if y >= len(self._rows_cache):
            return
        stem, primary, _ = self._rows_cache[y]
        _open_with_os_viewer(primary)
        try:
            self.app.notify(f"opened {primary.name}", timeout=3)
        except Exception:
            pass


__all__ = ["MermaidPanel"]
