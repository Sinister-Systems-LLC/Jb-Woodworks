# Sinister Forge :: panes/toolbar.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Top toolbar — jcode chrome parity (one-line, height=1).
# Renders:
#   [◈ EVE]  [version]  [branch]  [head]  [model]  [/help]
#
# Read-only — every data lookup is wrapped in try/except and falls back to
# `--` so the toolbar never crashes the TUI when a helper file is missing
# (cold-start, offline, junction broken, etc.).

from __future__ import annotations

from pathlib import Path

from textual.widgets import Static

from forge import __version__ as _FORGE_VERSION
from forge.theme import PURPLE_BRIGHT, SOFT


SANCTUM_ROOT = Path("D:/Sinister Sanctum")

# Sinister Panel purple chrome (jcode-parity)
TOOLBAR_BG = "#0E0A14"
TOOLBAR_BORDER = "#3A2A55"
TOOLBAR_ACCENT = "#A06EFF"   # [◈ EVE]
TOOLBAR_TEXT = "#999AB0"     # everything else


def _read_branch() -> str:
    try:
        head = SANCTUM_ROOT / ".git" / "HEAD"
        if not head.exists():
            return "--"
        raw = head.read_text(encoding="utf-8").strip()
        if raw.startswith("ref: refs/heads/"):
            return raw.removeprefix("ref: refs/heads/")
        return raw[:7]
    except Exception:
        return "--"


def _read_head() -> str:
    """Short HEAD SHA, 7 chars."""
    try:
        head = SANCTUM_ROOT / ".git" / "HEAD"
        if not head.exists():
            return "--"
        raw = head.read_text(encoding="utf-8").strip()
        if raw.startswith("ref: "):
            ref = raw.removeprefix("ref: ").strip()
            ref_file = SANCTUM_ROOT / ".git" / ref
            if ref_file.exists():
                return ref_file.read_text(encoding="utf-8").strip()[:7]
            # packed-refs fallback
            packed = SANCTUM_ROOT / ".git" / "packed-refs"
            if packed.exists():
                for line in packed.read_text(encoding="utf-8").splitlines():
                    if line.endswith(" " + ref):
                        return line.split()[0][:7]
            return "--"
        return raw[:7]
    except Exception:
        return "--"


def _read_model() -> str:
    """Best-effort: ANTHROPIC_MODEL env or fallback label."""
    import os
    return (os.environ.get("ANTHROPIC_MODEL")
            or os.environ.get("CLAUDE_MODEL")
            or "opus-4.7").strip() or "opus-4.7"


class Toolbar(Static):
    """One-line top toolbar — jcode chrome parity.

    Updates branch/head every 5s; the rest are static for the session.
    """

    DEFAULT_CSS = f"""
    Toolbar {{
        dock: top;
        height: 1;
        background: {TOOLBAR_BG};
        color: {TOOLBAR_TEXT};
        border-bottom: solid {TOOLBAR_BORDER};
        padding: 0 1;
    }}
    """

    def __init__(self) -> None:
        super().__init__("", id="forge-toolbar", markup=True)
        self._version = _FORGE_VERSION
        self._branch = "--"
        self._head = "--"
        self._model = _read_model()

    def on_mount(self) -> None:
        self._refresh()
        # Re-poll branch + head every 5s (cheap file reads).
        self.set_interval(5.0, self._refresh)

    def _refresh(self) -> None:
        try:
            self._branch = _read_branch()
            self._head = _read_head()
        except Exception:
            self._branch = "--"
            self._head = "--"
        self.update(
            f"[{TOOLBAR_ACCENT} bold]◈ EVE[/]"
            f"  [{TOOLBAR_TEXT}]v{self._version}[/]"
            f"  [{TOOLBAR_TEXT}]{self._branch}[/]"
            f"  [{TOOLBAR_TEXT}]{self._head}[/]"
            f"  [{TOOLBAR_TEXT}]{self._model}[/]"
            f"  [{TOOLBAR_TEXT}]/help[/]"
        )
