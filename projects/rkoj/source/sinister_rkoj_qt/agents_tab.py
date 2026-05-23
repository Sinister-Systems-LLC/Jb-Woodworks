# Author: RKOJ-ELENO :: 2026-05-21
"""Agents view — folder-tab row (All + per-project) + niri-style vertical scroll
of EVE agent cards.

Each AgentCard embeds a jcode-form terminal (QPlainTextEdit + QLineEdit +
QProcess streaming `claude --dangerously-skip-permissions -p ...` subprocess).
EVE persona injected verbatim from persona.py on first send.

The folder-tab strip:
    - "All" chip selected by default
    - One chip auto-added per active project_key
    - Chip auto-removed when no cards remain for that project_key

Cards are sorted by project_key so same-project cards render adjacent, with
a 1px purple-deep divider between different projects.

"Needs input" GLOW: when `card.session.status == "awaiting-input"`, the card
gets a soft purple QGraphicsDropShadowEffect (operator brief).
"""

from __future__ import annotations

import difflib
import json
import os
import re
import shutil
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QEvent, QProcess, QProcessEnvironment, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QKeyEvent, QKeySequence, QShortcut, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QLineEdit,
    QPlainTextEdit, QPushButton, QScrollArea, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget,
)

from . import state
from .persona import build_opening_prompt, eve_label
from .theme import (
    AMBER_ACCENT, BORDER, DIM, ELEVATED, FG, GREEN_ACCENT, MONO_FONT, MUTED_FG,
    PURPLE_ACCENT, PURPLE_PRIMARY, SPACINGS, nav_icon,
)


# ANSI escape sequences claude sometimes emits when its output piper thinks
# stdout is a TTY. Strip them so they don't render as `\x1b[32m` junk.
_ANSI_RE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


# v1.6.33 — per-project color for the left-stripe on agent cards.
# Curated palette for known projects + deterministic hash fallback for
# anything else. Operator scans colors at a glance to know which card
# is which project without reading the project_label text.
_PROJECT_COLORS: dict[str, str] = {
    "sanctum":             "#BF5AF2",  # Sanctum purple (primary)
    "sinister-panel":      "#30D158",  # green (live Hetzner panel)
    "kernel-apk":          "#FF9F0A",  # amber (warn — sensitive kernel work)
    "sinister-emulator":   "#0A84FF",  # iOS blue
    "snap-emulator-api":   "#FFCC00",  # yellow (Snapchat brand)
    "tiktok-emulator-api": "#FF453A",  # red (TikTok)
    "bumble-emulator-api": "#FFD60A",  # honey (Bumble)
    "sinister-forge":      "#C39DFF",  # purple-halo
    "sinister-mind":       "#A78BFA",  # purple-light
    "rkoj-workstation":    "#BF5AF2",  # purple primary (self-reference)
    "sinister-jokr":       "#5AC8FA",  # cyan
    "sinister-letstext":   "#FF2D55",  # pink
    "sinister-eve":        "#BF5AF2",  # purple primary
}


def _project_color(project_key: str) -> str:
    """Return a stable hex color for a project_key. Curated palette for
    known projects; deterministic HSV-from-hash for unknown ones so a
    new project always gets the SAME color across runs."""
    if project_key in _PROJECT_COLORS:
        return _PROJECT_COLORS[project_key]
    import colorsys
    h = (abs(hash(project_key)) % 360) / 360.0
    r, g, b = colorsys.hsv_to_rgb(h, 0.55, 0.95)
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"


# v1.6.17 — slash command autocomplete registry. Each tuple is
# (command, one-line description). The autocomplete popup filters this
# list as operator types after `/`. New /commands added to _maybe_intercept
# should be added here too so the popup discovers them.
# v1.6.60 — canned TL;DR ask shared by /summarize + /summarize-all so
# both produce identically-formatted recaps across the fleet.
_SUMMARIZE_PROMPT = (
    "Give me a TL;DR of our conversation so far. Format:\n"
    "1) goal: what are we trying to do? (1 sentence)\n"
    "2) working: what's confirmed working? (2-3 bullets)\n"
    "3) blocked: what's stuck or unclear? (2-3 bullets)\n"
    "4) next: what should we try next? (1-3 bullets)\n"
    "Be concrete — reference specific files / errors / decisions."
)


# v1.6.70 — token-budget warning threshold. claude opus typically has
# 200k effective context; warning at 100k gives operator runway to
# /summarize or fork via /clone before truncation pressure.
_TOKEN_WARN_THRESHOLD = 100_000


SLASH_COMMANDS: list[tuple[str, str]] = [
    ("/help",     "show all slash commands"),
    ("/broadcast","send the same message to all live cards"),
    ("/budget",   "show token-budget gauge vs warn threshold"),
    ("/cancel",   "kill the in-flight turn (Esc) — keeps card alive"),
    ("/clear",    "clear terminal scrollback (Ctrl+L)"),
    ("/clone",    "spawn a sibling card with the same project + mode"),
    ("/copy",     "copy the most recent EVE reply to clipboard"),
    ("/cost",     "cumulative spend breakdown for THIS card"),
    ("/api",      "print workstation API surface (127.0.0.1:5077 endpoints)"),
    ("/devices",  "list connected ADB devices inline"),
    ("/diff",     "unified diff between two assistant replies (/diff A B)"),
    ("/export",   "export conversation to a markdown file"),
    ("/export-all","write every live card's transcript to a bundle dir"),
    ("/fleet",    "per-card table — `/fleet cost|turns|uptime|project|...` to sort"),
    ("/font-down","shrink terminal font (this card)"),
    ("/font-reset","restore default terminal font size"),
    ("/font-up",  "enlarge terminal font (this card)"),
    ("/forget-n", "drop user turn #N locally — `/forget-n <N>` (claude server-side keeps it)"),
    ("/goto-card","focus card by exact pane_id prefix — `/goto-card <prefix>`"),
    ("/jump",     "scroll terminal cursor to first <pattern> match (no highlight)"),
    ("/uptime-all","fleet aggregate: total lifetime + turns + cost across all cards"),
    ("/wrap",     "toggle soft line-wrap in this card's terminal"),
    ("/focus",    "focus the input box"),
    ("/forget-last","drop last user+reply locally (claude server-side still remembers)"),
    ("/expand-all", "expand every collapsed card in the grid"),
    ("/find",     "scroll the grid to a card matching <text> (project/agent)"),
    ("/find-next","cycle to the next /find match (uses last query)"),
    ("/grep",     "highlight matching text in the terminal (yellow bg)"),
    ("/grep-clear", "remove /grep highlights"),
    ("/grep-next", "scroll to the next /grep match (F3)"),
    ("/grep-prev", "scroll to the previous /grep match (Shift+F3)"),
    ("/minimize-all", "collapse every expanded card in the grid"),
    ("/history",  "show recent turns with previews"),
    ("/memory",   "forge-memory-bridge BM25 recall"),
    ("/mcp",      "list MCP servers from ~/.claude/.mcp.json"),
    ("/model",    "show or change model (claude / haiku / opus)"),
    ("/needs",    "toggle awaiting-input glow (visual test)"),
    ("/note",     "drop a dim contextual annotation (not sent to EVE)"),
    ("/notes",    "list all notes accumulated in this card"),
    ("/todo",     "add a TODO item to this card's task list (jcode parity)"),
    ("/todos",    "show the TODO list (pending + done)"),
    ("/done",     "mark TODO #N as done — `/done <N>`"),
    ("/open",     "print shell commands to open agent paths"),
    ("/open-folder","open this agent's project root in Explorer (no cmd)"),
    ("/open-resume","open this agent's resume-points folder in Explorer"),
    ("/persona",  "print identity (slug / uuid / paths)"),
    ("/pin",      "pin (or unpin) this card to top of grid"),
    ("/plan",     "toggle plan-only mode (EVE proposes, doesn't edit)"),
    ("/reset-budget","clear cumulative cost + token tally for this card"),
    ("/ping",     "fan a canned status-check to all (or filtered) cards"),
    ("/rename",   "change the agent display name on this card"),
    ("/replay",   "re-run user turn #N verbatim (1-indexed; see /history)"),
    ("/retry",    "resend the most recent operator message"),
    ("/save",     "write resume-point JSON to disk"),
    ("/session",  "print just the session uuid"),
    ("/shortcuts","print every keyboard binding + click affordance"),
    ("/show",     "print full text of user turn #N (prompt + reply)"),
    ("/skill",    "load + send a saved skill .md as a turn"),
    ("/skills",   "list Sanctum skills (.md files)"),
    ("/stats",    "RKOJ fleet snapshot (agents / inbox / brain / devices)"),
    ("/summarize","ask EVE for a TL;DR of this card's conversation"),
    ("/summarize-all","fan /summarize to every card with prior turns"),
    ("/tag",      "add a label chip to this card (also matched by /find)"),
    ("/tags",     "fleet-wide tag census (which tags + which cards carry them)"),
    ("/timer",    "show elapsed time of the in-flight turn (or last duration)"),
    ("/untag",    "remove a label chip from this card"),
    ("/uptime",   "card lifetime + turn count + last activity"),
    ("/usage",    "cross-card RKOJ spend totals (from disk)"),
    ("/vault",    "Sinister Vault disk usage + daemon port"),
]


class _SlashPopup(QFrame):
    """jcode-style autocomplete popup — appears above the input when
    operator types `/`. Listens for filter() calls + Up/Down navigation
    forwarded from the input's keyPressEvent."""

    completed = pyqtSignal(str)   # full command name (incl. leading /)

    def __init__(self, parent: QWidget | None = None) -> None:
        # Tooltip flag makes it auto-dismiss on focus-out + render above
        # without grabbing input focus from the operator.
        super().__init__(
            parent,
            Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        from .theme import BORDER as _B, ELEVATED as _E, MUTED_FG as _M
        self.setStyleSheet(
            f"QFrame {{ background-color: {_E}; border: 1px solid {_B}; "
            f"border-radius: 8px; padding: 4px; }}"
            f"QListWidget {{ background-color: transparent; color: white; "
            f"border: none; outline: none; font-family: 'JetBrains Mono', "
            f"monospace; font-size: 12px; }}"
            f"QListWidget::item {{ background-color: transparent; "
            f"border-radius: 5px; padding: 6px 10px; }}"
            f"QListWidget::item:hover {{ background-color: rgba(191,90,242,30); }}"
            f"QListWidget::item:selected {{ background-color: rgba(191,90,242,90); "
            f"color: white; }}"
        )
        # QListWidget inside a frame
        from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QVBoxLayout as _V
        self._list = QListWidget(self)
        self._list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._list.itemClicked.connect(self._on_item_clicked)
        v = _V(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.addWidget(self._list)
        self.setMinimumWidth(360)
        # Track full SLASH_COMMANDS so filter() can rebuild
        self._all = list(SLASH_COMMANDS)
        self._populate(self._all)

    def _populate(self, items: list[tuple[str, str]]) -> None:
        from PyQt6.QtWidgets import QListWidgetItem
        self._list.clear()
        for cmd, desc in items:
            li = QListWidgetItem(f"{cmd:<10}  {desc}")
            li.setData(Qt.ItemDataRole.UserRole, cmd)
            self._list.addItem(li)
        if self._list.count() > 0:
            self._list.setCurrentRow(0)

    def filter(self, query: str) -> int:
        """Filter visible commands by prefix match. Returns count of matches."""
        q = (query or "").lower().strip()
        matches = [(c, d) for c, d in self._all if c.lower().startswith(q)]
        self._populate(matches)
        # Auto-size to roughly 5 rows visible
        n = min(len(matches), 7)
        self._list.setFixedHeight(max(36, 32 * n + 8))
        return len(matches)

    def select_next(self) -> None:
        row = self._list.currentRow()
        self._list.setCurrentRow((row + 1) % max(1, self._list.count()))

    def select_prev(self) -> None:
        row = self._list.currentRow()
        n = max(1, self._list.count())
        self._list.setCurrentRow((row - 1) % n)

    def selected_command(self) -> str | None:
        it = self._list.currentItem()
        if it is None:
            return None
        return it.data(Qt.ItemDataRole.UserRole)

    def _on_item_clicked(self, item) -> None:
        cmd = item.data(Qt.ItemDataRole.UserRole)
        if cmd:
            self.completed.emit(cmd)

    def show_above(self, anchor: QWidget) -> None:
        """Position the popup adjacent to the anchor widget.

        v1.6.20 — try above first; if that would fall off-screen, flip
        to below. Always clamp X to the screen's available geometry so
        a popup near the right edge doesn't truncate.
        """
        from PyQt6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen()
        screen_geo = screen.availableGeometry() if screen else None
        top = anchor.mapToGlobal(anchor.rect().topLeft())
        bot = anchor.mapToGlobal(anchor.rect().bottomLeft())
        # Force a layout pass so sizeHint() is realistic before move().
        self.adjustSize()
        h = self.sizeHint().height()
        w = self.sizeHint().width()
        # Try above; flip below if we'd clip the top of the screen.
        above_y = top.y() - h - 4
        if screen_geo and above_y < screen_geo.y():
            y = bot.y() + 4
        else:
            y = above_y
        # Clamp X
        x = top.x()
        if screen_geo:
            max_x = screen_geo.x() + screen_geo.width() - w - 4
            if x > max_x:
                x = max(screen_geo.x(), max_x)
        self.move(x, y)
        self.show()


class _MultiLineInput(QPlainTextEdit):
    """jcode-style input: Enter sends, Shift+Enter inserts newline.

    Auto-resizes vertically up to a 5-line cap so a long prompt doesn't
    blow up the card. Emits `submit` (pyqtSignal[str]) when the operator
    presses Enter without Shift held.

    v1.6.17 — slash_popup attribute (optional): when set, typing `/` at
    cursor-start shows it; Up/Down/Enter/Esc are intercepted to drive it.
    """

    submit = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("MultiLineInput")
        # Behave like a single-line field by default — auto-grow when content
        # wraps or contains newlines.
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.setTabChangesFocus(True)
        self.document().documentLayout().documentSizeChanged.connect(self._fit_height)
        self._min_h = 36
        self._max_h = 132
        self.setFixedHeight(self._min_h)
        # v1.6.17 popup (set by AgentCard after construction)
        self.slash_popup: _SlashPopup | None = None
        # v1.6.62 — Up/Down history recall. AgentCard sets
        # _history_callback to return a fresh list of prior user-turn
        # strings each time we cycle. _history_idx tracks position
        # in the most-recent-first cycle; _history_pending_text
        # buffers whatever the operator was typing when they started
        # navigating so Down past the end restores it.
        self._history_callback = None  # type: ignore[assignment]
        self._history_idx: int = -1
        self._history_pending_text: str = ""

    def _fit_height(self, *_args) -> None:
        h = int(self.document().size().height()) + 12
        h = max(self._min_h, min(self._max_h, h))
        if h != self.height():
            self.setFixedHeight(h)
            self.setVerticalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAsNeeded if h >= self._max_h
                else Qt.ScrollBarPolicy.ScrollBarAlwaysOff
            )

    def _popup_visible(self) -> bool:
        return self.slash_popup is not None and self.slash_popup.isVisible()

    def insertFromMimeData(self, source) -> None:  # type: ignore[override]
        """v1.6.79 — jcode parity: paste an image from clipboard. We
        save it to %TEMP%\\eve-paste-<ts>.png and reference the path in
        the input so claude's Read tool can pick it up. Falls back to
        default text paste when no image is present."""
        if source.hasImage():
            try:
                from PyQt6.QtGui import QImage
                img = QImage(source.imageData())
                if not img.isNull():
                    ts = time.strftime("%Y%m%dT%H%M%S")
                    out = Path(os.environ.get("TEMP", ".")) / f"eve-paste-{ts}.png"
                    img.save(str(out), "PNG")
                    cur = self.textCursor()
                    cur.insertText(f"[image saved: {out}] ")
                    return
            except Exception:
                pass
        super().insertFromMimeData(source)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        # v1.6.17 — when the slash popup is visible, hijack arrow/enter/esc.
        if self._popup_visible():
            k = event.key()
            if k == Qt.Key.Key_Down:
                self.slash_popup.select_next(); event.accept(); return
            if k == Qt.Key.Key_Up:
                self.slash_popup.select_prev(); event.accept(); return
            if k == Qt.Key.Key_Escape:
                self.slash_popup.hide(); event.accept(); return
            if k in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Tab):
                # Complete the highlighted command — replace the entire
                # input text with the command (operator can then keep
                # typing args after it).
                cmd = self.slash_popup.selected_command()
                if cmd:
                    self.setPlainText(cmd + " ")
                    # Move cursor to end
                    cur = self.textCursor()
                    cur.movePosition(QTextCursor.MoveOperation.End)
                    self.setTextCursor(cur)
                    self.slash_popup.hide()
                    event.accept()
                    return

        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                # Shift+Enter → newline (default QPlainTextEdit behavior)
                super().keyPressEvent(event)
                return
            # Plain Enter (and Ctrl+Enter) → submit
            text = self.toPlainText().rstrip()
            self.submit.emit(text)
            # v1.6.62 — reset history cursor after dispatch.
            self._history_idx = -1
            self._history_pending_text = ""
            return
        # v1.6.62 — Up/Down history recall when slash popup not active.
        # Only kicks in if input is single-line (no newlines yet) — that
        # keeps multi-line edits using Up/Down for cursor navigation.
        if (event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down)
                and not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
                and "\n" not in self.toPlainText()
                and self._history_callback is not None):
            if self._handle_history_arrow(event.key() == Qt.Key.Key_Up):
                event.accept()
                return
        super().keyPressEvent(event)
        # v1.6.17 — after any normal keystroke, refresh popup visibility
        # based on current text.
        self._maybe_update_popup()

    def _handle_history_arrow(self, going_up: bool) -> bool:
        """v1.6.62 — return True if we consumed the arrow press.
        Walks history most-recent-first (Up = older). On entry
        (idx == -1) saves whatever's typed as pending_text. Down past
        the most-recent entry restores pending_text + resets idx."""
        history = self._history_callback() if self._history_callback else []
        if not history:
            return False
        if going_up:
            if self._history_idx == -1:
                # First Up: stash current draft + load most-recent entry.
                self._history_pending_text = self.toPlainText()
                self._history_idx = 0
            elif self._history_idx < len(history) - 1:
                self._history_idx += 1
            else:
                # Already at the oldest entry — stop.
                return True
            self.setPlainText(history[-1 - self._history_idx])
        else:
            if self._history_idx <= 0:
                # At most-recent or not navigating — restore pending.
                self._history_idx = -1
                self.setPlainText(self._history_pending_text)
                self._history_pending_text = ""
                cur = self.textCursor()
                cur.movePosition(QTextCursor.MoveOperation.End)
                self.setTextCursor(cur)
                return True
            self._history_idx -= 1
            self.setPlainText(history[-1 - self._history_idx])
        cur = self.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.End)
        self.setTextCursor(cur)
        return True

    def _maybe_update_popup(self) -> None:
        if self.slash_popup is None:
            return
        text = self.toPlainText()
        # Only show when text starts with `/` and there's no newline yet
        # (multi-line composition shouldn't trigger autocomplete).
        if text.startswith("/") and "\n" not in text:
            # Filter by the slash-token (up to first space)
            token = text.split(None, 1)[0]
            n_matches = self.slash_popup.filter(token)
            if n_matches > 0:
                self.slash_popup.show_above(self)
            else:
                self.slash_popup.hide()
        else:
            if self.slash_popup.isVisible():
                self.slash_popup.hide()

    def focusOutEvent(self, event) -> None:
        # Hide popup when input loses focus (clicking elsewhere shouldn't
        # leave it floating).
        if self._popup_visible():
            self.slash_popup.hide()
        super().focusOutEvent(event)

try:
    from PyQt6.QtSvgWidgets import QSvgWidget  # type: ignore
    _HAS_SVG = True
except Exception:  # pragma: no cover
    _HAS_SVG = False

# Status -> hex color (mirrors Panel STATUS_COLOR map)
_STATUS_COLOR: dict[str, str] = {
    "online": GREEN_ACCENT,
    "busy": AMBER_ACCENT,
    "awaiting-input": PURPLE_ACCENT,
    "offline": DIM,
    "idle": DIM,
}


# ── Session record ──────────────────────────────────────────────────────
@dataclass
class AgentSession:
    pane_id: str
    project_key: str
    project_display: str
    agent_name: str
    mode: str = "claude"
    accent: str = "purple"
    status: str = "idle"  # idle | busy | online | offline | awaiting-input
    turns: list[dict] = field(default_factory=list)
    created_at: str = ""
    # Phase-1 memory bootstrap (populated by _bootstrap_agent_memory)
    slug: str = ""
    display_name: str = ""
    heartbeat_path: str = ""
    progress_path: str = ""
    resume_dir: str = ""
    inbox_dir: str = ""
    # v1.6.3 — claude session continuity via `--session-id` + `--resume`
    session_uuid: str = ""
    # v1.6.28 — pin state (toggled via star button or /pin); pinned cards
    # render at the top of the niri-scroll grid regardless of project order.
    pinned: bool = False
    # v1.6.45 — operator-defined tags for this card (e.g. "wip", "blocked",
    # "research"). Rendered as small chips in the header; /find matches
    # against them too. Stored as a flat list — no per-tag color logic.
    tags: list[str] = field(default_factory=list)
    # v1.6.59 — half-typed operator message preserved across close + resume.
    # Live-updated by textChanged signal; cleared on _on_send dispatch.
    input_draft: str = ""


def _find_claude_executable() -> Optional[str]:
    """Locate the `claude` CLI on PATH. Returns None if not installed."""
    return shutil.which("claude")


def _bootstrap_agent_memory(sess: AgentSession) -> None:
    """Phase-1 memory wire-up: pre-create dirs + write initial heartbeat.

    Per `_shared-memory/plans/Sanctum-deepclean-2026-05-21T2300Z/memory-jcode-integration-audit.md`
    section 4. Fills the AgentSession's bootstrap fields and creates on-disk
    presence so siblings can discover the new agent within seconds.
    """
    sm = state.SHARED_MEMORY
    sess.slug = f"{sess.project_key}-{sess.pane_id[:6]}"
    sess.display_name = f"EVE on {sess.project_display}"
    # v1.6.3 — full UUID4 for claude --session-id (per-pane session continuity)
    if not sess.session_uuid:
        sess.session_uuid = str(uuid.uuid4())
    sess.heartbeat_path = str(sm / "heartbeats" / f"{sess.slug}.json")
    sess.progress_path = str(sm / "PROGRESS" / f"{sess.display_name}.md")
    sess.resume_dir = str(sm / "resume-points" / sess.display_name)
    sess.inbox_dir = str(sm / "inbox" / sess.slug)
    try:
        for p in (
            Path(sess.heartbeat_path).parent,
            Path(sess.progress_path).parent,
            Path(sess.resume_dir),
            Path(sess.inbox_dir),
        ):
            p.mkdir(parents=True, exist_ok=True)
        # Initial heartbeat
        Path(sess.heartbeat_path).write_text(json.dumps({
            "schema_version": "sinister.heartbeat.v1",
            "agent_identity": "EVE",
            "agent": sess.display_name,
            "agent_display": sess.display_name,
            "slug": sess.slug,
            "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "branch": f"agent/{sess.project_key}/<topic>",
            "mode": sess.mode,
            "session_status": "spawned-by-rkoj",
            "via": "rkoj-qt",
            "pane_id": sess.pane_id,
            "project_key": sess.project_key,
        }, indent=2), encoding="utf-8")
        # Seed PROGRESS only if file is new
        pp = Path(sess.progress_path)
        if not pp.exists():
            pp.write_text(
                f"# Agent: {sess.display_name}\n\n"
                f"Append-only progress log. Most recent at top.\n\n---\n\n"
                f"## {time.strftime('%Y-%m-%d %H:%M', time.gmtime())} — spawned\n"
                f"Spawned by RKOJ.exe (PyQt6). slug={sess.slug} project={sess.project_key} mode={sess.mode}.\n\n",
                encoding="utf-8",
            )
    except Exception:
        # Memory bootstrap is best-effort; never block agent spawn on disk hiccups.
        pass


def _refresh_heartbeat(sess: AgentSession, session_status: str = "online") -> None:
    """Re-write the per-agent heartbeat with a fresh timestamp."""
    if not sess.heartbeat_path:
        return
    try:
        hp = Path(sess.heartbeat_path)
        if not hp.parent.exists():
            return
        payload = {
            "schema_version": "sinister.heartbeat.v1",
            "agent_identity": "EVE",
            "agent": sess.display_name,
            "agent_display": sess.display_name,
            "slug": sess.slug,
            "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "branch": f"agent/{sess.project_key}/<topic>",
            "mode": sess.mode,
            "session_status": session_status,
            "via": "rkoj-qt",
            "pane_id": sess.pane_id,
            "project_key": sess.project_key,
            "turn_count": len(sess.turns),
        }
        hp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except Exception:
        pass


def _make_child_env(sess: AgentSession) -> QProcessEnvironment:
    """Build a QProcessEnvironment with SINISTER_* identity env vars so the
    spawned claude child knows its slug/display/paths.

    v1.6.75 — mirrors Sinister Start.bat's env-export block exactly so
    spawned agents see the same identity surface whether they're booted
    from RKOJ or the .bat. Added AGENT_NAME, ACCENT_COLOR, MODE.
    """
    qenv = QProcessEnvironment.systemEnvironment()
    qenv.insert("SINISTER_AGENT_NAME", sess.agent_name or "")           # v1.6.75 (.bat parity)
    qenv.insert("SINISTER_AGENT_DISPLAY", sess.display_name or sess.agent_name)
    qenv.insert("SINISTER_AGENT_SLUG", sess.slug or sess.project_key)
    qenv.insert("SINISTER_PANE_ID", sess.pane_id)
    qenv.insert("SINISTER_PROJECT_KEY", sess.project_key)
    qenv.insert("SINISTER_HEARTBEAT_PATH", sess.heartbeat_path)
    qenv.insert("SINISTER_PROGRESS_PATH", sess.progress_path)
    qenv.insert("SINISTER_RESUME_DIR", sess.resume_dir)
    qenv.insert("SINISTER_INBOX_DIR", sess.inbox_dir)
    qenv.insert("SINISTER_AGENT_IDENTITY", "EVE")
    qenv.insert("SINISTER_AUTHORSHIP", "RKOJ-ELENO")
    qenv.insert("SINISTER_ACCENT_COLOR", sess.accent or "purple")        # v1.6.75 (.bat parity)
    qenv.insert("SINISTER_MODE", sess.mode or "claude")                  # v1.6.75 (.bat parity)
    return qenv


def _project_root(project_key: str) -> str:
    """v1.6.75 — resolve a project_key to its on-disk root via
    automations/session-templates/projects.json. Returns repo root if
    not found so QProcess.setWorkingDirectory always has a valid path."""
    try:
        from . import state as _state
        for p in _state.load_projects():
            if (getattr(p, "key", None) == project_key
                    or p.get("key") == project_key if isinstance(p, dict) else False):
                root = (p.root if hasattr(p, "root") else p.get("root", ""))
                if root and Path(root).exists():
                    return root
    except Exception:
        pass
    return str(state.SHARED_MEMORY.parent) if hasattr(state, "SHARED_MEMORY") else r"D:\Sinister Sanctum"


def _pretrust_project(project_root: str) -> None:
    """v1.6.75 — Sinister Start.bat parity: ensure the project root is
    pre-trusted in ~/.claude.json so claude doesn't pop the first-run
    'do you trust this folder' dialog on every fresh agent spawn."""
    try:
        cfg_fp = Path.home() / ".claude.json"
        if not cfg_fp.exists():
            return
        import json as _json
        cfg = _json.loads(cfg_fp.read_text(encoding="utf-8"))
        root_key = project_root.replace("\\", "/")
        cfg.setdefault("projects", {})
        proj = cfg["projects"].setdefault(root_key, {
            "allowedTools": [],
            "mcpContextUris": [],
            "mcpServers": {},
            "enabledMcpjsonServers": [],
            "disabledMcpjsonServers": [],
        })
        proj["hasTrustDialogAccepted"] = True
        proj["hasClaudeMdExternalIncludesApproved"] = True
        proj["hasClaudeMdExternalIncludesWarningShown"] = True
        proj["hasCompletedProjectOnboarding"] = True
        proj.setdefault("projectOnboardingSeenCount", 1)
        cfg_fp.write_text(_json.dumps(cfg, indent=2), encoding="utf-8")
    except Exception:
        # Non-fatal — claude will just prompt once if pretrust fails.
        pass


def _agent_prefs_model(agent_name: str) -> str | None:
    """v1.6.75 — Sinister Start.bat parity: read
    _shared-memory/agent-prefs.json and return the per-agent model
    override (if any). Operator can set intelligence-level chip in
    Sanctum Console which writes here; we honor it on spawn."""
    try:
        prefs_fp = state.SHARED_MEMORY / "agent-prefs.json"
        if not prefs_fp.exists():
            return None
        import json as _json
        prefs = _json.loads(prefs_fp.read_text(encoding="utf-8"))
        entry = prefs.get(agent_name) or {}
        m = entry.get("model")
        return m if isinstance(m, str) and m else None
    except Exception:
        return None


# ── Clickable tag chip ──────────────────────────────────────────────────
# v1.6.58 — palette + semantic-reserved map. Hashing the tag name into
# the palette gives stable colors per-tag across cards. Common tags get
# reserved colors so 'blocked' is always red, 'wip' always yellow, etc.
_TAG_PALETTE: list[tuple[str, str, str]] = [
    # (fg, bg, border) — alpha 30 / 120 keeps chips subtle
    ("#BF5AF2", "rgba(191,90,242,30)",  "rgba(191,90,242,120)"),   # purple
    ("#0A84FF", "rgba(10,132,255,30)",  "rgba(10,132,255,120)"),   # blue
    ("#64D2FF", "rgba(100,210,255,30)", "rgba(100,210,255,120)"),  # cyan
    ("#FF9F0A", "rgba(255,159,10,30)",  "rgba(255,159,10,120)"),   # orange
    ("#FF6482", "rgba(255,100,130,30)", "rgba(255,100,130,120)"),  # pink
    ("#5E5CE6", "rgba(94,92,230,30)",   "rgba(94,92,230,120)"),    # indigo
    ("#AC8FFF", "rgba(172,143,255,30)", "rgba(172,143,255,120)"),  # lavender
]
_TAG_RESERVED: dict[str, tuple[str, str, str]] = {
    "blocked": ("#FF453A", "rgba(255,69,58,30)",  "rgba(255,69,58,120)"),   # red
    "wip":     ("#FFD60A", "rgba(255,214,10,30)", "rgba(255,214,10,120)"),  # yellow
    "todo":    ("#FFD60A", "rgba(255,214,10,30)", "rgba(255,214,10,120)"),  # yellow
    "done":    ("#30D158", "rgba(48,209,88,30)",  "rgba(48,209,88,120)"),   # green
    "shipped": ("#30D158", "rgba(48,209,88,30)",  "rgba(48,209,88,120)"),   # green
    "review":  ("#FF9F0A", "rgba(255,159,10,30)", "rgba(255,159,10,120)"),  # orange
}


def _parse_skill_frontmatter(text: str) -> tuple[dict, str]:
    """v1.6.69 — jcode-parity YAML frontmatter parser. Returns
    (frontmatter_dict, body). Frontmatter must be the first block in
    the file, delimited by `---` on its own line. Recognized keys:
    `name`, `description`, `allowed-tools`. Values are parsed as
    flat strings or comma-separated lists. No PyYAML dependency.

    If no frontmatter is present, returns ({}, text) unchanged so
    existing raw-content skills keep working."""
    if not text.startswith("---"):
        return {}, text
    lines = text.split("\n")
    # Find the closing ---
    end_idx = None
    for i in range(1, min(40, len(lines))):  # cap scan to ~40 lines
        if lines[i].strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        return {}, text
    fm: dict = {}
    for ln in lines[1:end_idx]:
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        if ":" not in ln:
            continue
        key, _, val = ln.partition(":")
        key = key.strip().lower()
        val = val.strip()
        # Strip surrounding quotes
        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
            val = val[1:-1]
        # Parse comma-separated lists for allowed-tools-like keys
        if "," in val and key in ("allowed-tools", "tools", "tags"):
            fm[key] = [v.strip() for v in val.split(",") if v.strip()]
        else:
            fm[key] = val
    body = "\n".join(lines[end_idx + 1:]).lstrip()
    return fm, body


def _tag_colors(tag: str) -> tuple[str, str, str]:
    """v1.6.58 — return (fg, bg, border) for a tag. Reserved names win;
    others hash-index into the palette deterministically so 'foo' always
    gets the same color across cards + sessions."""
    key = tag.strip().lower()
    if key in _TAG_RESERVED:
        return _TAG_RESERVED[key]
    # Python hash() is salted per-process — use a stable hash so colors
    # are consistent across RKOJ launches.
    h = 0
    for ch in key:
        h = (h * 131 + ord(ch)) & 0x7fffffff
    return _TAG_PALETTE[h % len(_TAG_PALETTE)]


class _ClickPill(QLabel):
    """v1.6.63 — generic clickable header pill. Left-click fires a slash
    command on the parent AgentCard via _maybe_intercept so existing
    intercept logic + history feedback + heartbeat / cost updates run
    uniformly. Used for turn-count (→ /history) + cost (→ /cost) pills."""

    def __init__(self, text: str, card: "AgentCard", *, intercept: str) -> None:
        super().__init__(text)
        self._card = card
        self._intercept = intercept
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, ev) -> None:  # type: ignore[override]
        if ev.button() == Qt.MouseButton.LeftButton:
            try:
                self._card._maybe_intercept(self._intercept)
            except Exception:
                pass
        super().mousePressEvent(ev)


class _TagChip(QLabel):
    """v1.6.52 — clickable tag chip in the card header. Clicking emits
    `find_requested` on the parent AgentCard with this chip's text, so
    the grid scrolls to the next card carrying the same tag (the
    standard /find-next cycle wraps if there are multiple matches).
    v1.6.61 — right-click opens a context menu with Untag + Find
    actions so operators can remove tags without typing /untag."""

    def __init__(self, text: str, card: "AgentCard") -> None:
        super().__init__(text)
        self._card = card
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(
            f"Left-click: /find cards tagged '{text}' · "
            f"Right-click: menu"
        )

    def mousePressEvent(self, ev) -> None:  # type: ignore[override]
        if ev.button() == Qt.MouseButton.LeftButton:
            try:
                self._card.find_requested.emit(
                    self._card.session.pane_id, self.text()
                )
            except Exception:
                pass
        super().mousePressEvent(ev)

    def contextMenuEvent(self, ev) -> None:  # type: ignore[override]
        from PyQt6.QtWidgets import QMenu
        from .theme import BORDER as _B, ELEVATED as _E, PURPLE_PRIMARY as _P
        menu = QMenu(self)
        menu.setStyleSheet(
            f"QMenu {{ background-color: {_E}; color: white; "
            f"border: 1px solid {_B}; border-radius: 6px; padding: 4px; }}"
            f"QMenu::item {{ padding: 5px 14px; border-radius: 4px; }}"
            f"QMenu::item:selected {{ background-color: rgba(191,90,242,80); }}"
        )
        find_action = menu.addAction(f"Find cards tagged '{self.text()}'")
        untag_action = menu.addAction(f"Remove tag '{self.text()}' from this card")
        chosen = menu.exec(ev.globalPos())
        if chosen is find_action:
            try:
                self._card.find_requested.emit(
                    self._card.session.pane_id, self.text()
                )
            except Exception:
                pass
        elif chosen is untag_action:
            try:
                # Reuses the existing /untag intercept which handles
                # session.tags mutation + _rebuild_tags + persist.
                self._card._maybe_intercept(f"/untag {self.text()}")
            except Exception:
                pass


# ── Agent card ──────────────────────────────────────────────────────────
class AgentCard(QFrame):
    """Single agent card with embedded terminal + input line + QProcess."""

    closed = pyqtSignal(str)  # pane_id
    status_changed = pyqtSignal(str, str)  # pane_id, new_status
    # v1.6.28 — emitted when operator toggles pin state; AgentsView listens
    # + re-sorts the grid so pinned cards stay at top.
    pin_changed = pyqtSignal(str)  # pane_id
    # v1.6.30 — /broadcast intercept emits this with the message body
    # (no /broadcast prefix). AgentsView fans it to every live card.
    broadcast_requested = pyqtSignal(str)
    # v1.6.36 — /minimize-all + /expand-all bulk toggles for the grid.
    minimize_all_requested = pyqtSignal()
    expand_all_requested = pyqtSignal()
    # v1.6.41 — /clone emits (project_key, mode) so AgentsView spawns a
    # sibling card with the same setup but a fresh session UUID.
    clone_requested = pyqtSignal(str, str)
    # v1.6.42 — /find emits (pane_id_of_invoker, query) so AgentsView
    # can scroll the grid to a matching card + echo feedback back.
    find_requested = pyqtSignal(str, str)
    # v1.6.51 — /tags emits invoker pane_id; AgentsView replies with
    # a fleet-wide tag census echoed into the invoker's terminal.
    tags_census_requested = pyqtSignal(str)
    # v1.6.55 — /export-all emits invoker pane_id; AgentsView writes
    # every card's transcript to a bundle dir + echoes summary back.
    export_all_requested = pyqtSignal(str)
    # v1.6.60 — /summarize-all emits invoker pane_id; AgentsView stages
    # the canned TL;DR prompt into every non-empty card + fires _on_send.
    summarize_all_requested = pyqtSignal(str)
    # v1.6.66 — /fleet emits (invoker_id, sort_key). sort_key is one of:
    # "" (default: pinned, project, agent), "project", "agent", "mode",
    # "turns", "cost", "status", "uptime". v1.6.67 added the sort arg.
    fleet_table_requested = pyqtSignal(str, str)
    # v1.6.68 — /uptime-all aggregate.
    uptime_all_requested = pyqtSignal(str)

    # Braille spinner for the "thinking" indicator (jcode-style).
    _SPINNER = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

    def __init__(self, session: AgentSession, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.session = session
        self.setObjectName("AgentCard")
        self.setProperty("needs_input", False)
        self.setMinimumHeight(280)
        # v1.6.33 — per-project color left-stripe (3px). Operator scans
        # colors to identify project at a glance without reading labels.
        # Composed with the existing #AgentCard QSS (1px hairline border)
        # by overriding only the left edge to a 3px tinted line.
        _stripe_color = _project_color(session.project_key)
        self.setStyleSheet(
            f"QFrame#AgentCard {{ border-left: 3px solid {_stripe_color}; }}"
        )
        self._proc: Optional[QProcess] = None
        self._first_turn = True
        self._glow_effect: Optional[QGraphicsDropShadowEffect] = None
        self._reply_started = False  # have we emitted the "<< EVE:" prefix?
        self._spinner_idx = 0
        self._thinking_start_ts: float = 0.0
        # v1.6.11 stream-json parsing state
        self._stream_buf: str = ""
        self._stream_text_started: bool = False
        self._stream_tools_run: list[str] = []
        # v1.6.12 cumulative cost + token tally across all turns in this card
        self._total_cost_usd: float = 0.0
        self._total_in_tokens: int = 0
        self._total_out_tokens: int = 0
        # v1.6.16 — track where each turn's reply text starts in the document
        # so we can apply markdown formatting (code fences, inline code, bold)
        # at end-of-turn without re-scanning the whole terminal.
        self._reply_start_pos: int = 0
        # v1.6.18 — current tool name (set when a tool_use block opens,
        # cleared on result event); displayed in the spinner instead of
        # the generic "EVE is thinking" so operator sees the LIVE step.
        self._current_tool: str | None = None
        # v1.6.18 — placeholder hint rotation (cycles ~every 5s while idle).
        self._placeholder_idx = 0
        # v1.6.27 — collapsed state (toggled via chevron button or Ctrl+M).
        # When True, hides terminal + thinking label + input row; only
        # the 40px header strip remains. Useful when running 5+ cards.
        self._collapsed: bool = False
        # v1.6.35 — /grep state: last pattern + cursor positions of every
        # match + current index (wraps with /grep-next + /grep-prev).
        self._grep_pattern: str = ""
        self._grep_positions: list[int] = []
        self._grep_idx: int = -1
        # v1.6.38 — turn timing: monotonic start of in-flight turn (None
        # when idle) + duration of the last completed turn. /timer reads
        # both; /cancel + _on_finished clear/update them.
        self._turn_started_ts: float | None = None
        self._last_turn_seconds: float | None = None
        # v1.6.54 — card spawn time (monotonic) for /uptime. Set once at
        # construction so it survives mode pivots, message sends, etc.
        self._spawn_ts: float = time.monotonic()
        # v1.6.54 — wall-clock timestamp of last send (turn dispatch) so
        # /uptime can show "last activity 3m ago".
        self._last_send_ts: float | None = None
        # v1.6.68 — terminal font-size state (/font-up + /font-down +
        # /font-reset). Tracked on the card so each card can have its
        # own zoom level (not a global preference).
        self._terminal_font_size: int = 10  # matches QFont("Cascadia Mono", 10) default
        # v1.6.70 — token-budget warning state. Surfaces a one-shot
        # yellow line when (in + out) cumulative tokens cross the
        # warn threshold. Reset by /clear and /forget-last is intentionally
        # NOT a reset trigger (claude --resume still has the context).
        self._token_warning_shown: bool = False
        self._build()
        # v1.6.45 — render any restored tags after build.
        self._rebuild_tags()
        # Phase-1 memory: heartbeat refresh every 30s while card alive
        self._hb_timer = QTimer(self)
        self._hb_timer.setInterval(30_000)
        self._hb_timer.timeout.connect(lambda: _refresh_heartbeat(self.session, self.session.status))
        self._hb_timer.start()
        # Thinking spinner — 100ms tick while busy. Re-uses _thinking_label.
        self._spinner_timer = QTimer(self)
        self._spinner_timer.setInterval(100)
        self._spinner_timer.timeout.connect(self._tick_spinner)
        # v1.6.12 — Ctrl+L clears the terminal (jcode keyboard parity)
        QShortcut(QKeySequence("Ctrl+L"), self, activated=self._on_clear_shortcut)
        # v1.6.27 — Ctrl+M toggles card collapse
        QShortcut(QKeySequence("Ctrl+M"), self, activated=self._toggle_collapsed)
        # v1.6.36 — F3 / Shift+F3 jump between /grep matches (operator
        # stays in keyboard; mirrors standard editor "find next" binding).
        QShortcut(QKeySequence("F3"), self,
                  activated=lambda: self._grep_cycle("next"))
        QShortcut(QKeySequence("Shift+F3"), self,
                  activated=lambda: self._grep_cycle("prev"))
        # v1.6.37 — Esc kills in-flight turn cleanly (same as /cancel).
        # Silently no-ops when no turn running so Esc-mashing isn't noisy.
        # Scoped to this card so Esc on other widgets isn't intercepted.
        from PyQt6.QtCore import Qt as _Qt
        _esc = QShortcut(QKeySequence("Esc"), self,
                         activated=self._cancel_if_running)
        _esc.setContext(_Qt.ShortcutContext.WidgetWithChildrenShortcut)
        # v1.6.18 — rotate the input placeholder every 5s while idle so
        # operator discovers the keybinds (/help, Shift+Enter, Ctrl+L)
        # without having to read the README.
        self._placeholder_timer = QTimer(self)
        self._placeholder_timer.setInterval(5_000)
        self._placeholder_timer.timeout.connect(self._rotate_placeholder)
        self._placeholder_timer.start()

    # ── UI ────────────────────────────────────────────────────────────
    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(SPACINGS["md"], SPACINGS["sm"], SPACINGS["md"], SPACINGS["sm"])
        root.setSpacing(SPACINGS["sm"])

        # Header strip
        hdr = QHBoxLayout()
        hdr.setSpacing(SPACINGS["sm"])

        # Status dot — SVG (no glyph). Tinted in code via setStyleSheet
        # because Qt's SVG renderer won't honour CSS currentColor on
        # standalone shapes. We re-tint on _set_status().
        # v1.6.65 — clickable: fires /persona for identity dump.
        self.status_dot = _ClickPill("", self, intercept="/persona")
        self.status_dot.setObjectName("StatusDot")
        self.status_dot.setProperty("state", "idle")
        self.status_dot.setFixedSize(12, 12)
        self.status_dot.setStyleSheet(
            f"background-color: {DIM}; border-radius: 6px;"
        )
        self.status_dot.setToolTip("Click → /persona (identity dump)")

        # v1.6.64 — project label is clickable: fires /find <project>
        # so operator can fan to all sibling cards on the same project.
        project_label = _ClickPill(
            self.session.project_display.upper(), self,
            intercept=f"/find {self.session.project_display}",
        )
        project_label.setObjectName("AgentProject")
        project_label.setToolTip(
            f"Click → /find {self.session.project_display}"
        )

        # v1.6.44 — kept as self._title_label so /rename can update it.
        self._title_label = QLabel(eve_label(self.session.agent_name, ""))
        self._title_label.setObjectName("AgentTitle")
        title = self._title_label  # local alias to keep existing hdr.addWidget refs working

        # v1.6.65 — mode pill clickable: fires /model (show/change model).
        mode_pill = _ClickPill(self.session.mode, self, intercept="/model")
        mode_pill.setObjectName("ModePill")
        mode_pill.setToolTip("Click → /model (show/change model)")

        # v1.6.9 — turn counter pill (updates after each /send completes)
        # v1.6.63 — clickable: fires /history. Wrap in _ClickPill.
        self._turn_pill = _ClickPill("0 turns", self, intercept="/history")
        self._turn_pill.setObjectName("ModePill")
        self._turn_pill.setStyleSheet(
            f"color: {MUTED_FG}; background-color: transparent; "
            f"border: 1px solid {BORDER}; border-radius: 10px; "
            f"padding: 2px 9px; font-size: 10px; font-weight: 600;"
        )
        self._turn_pill.setToolTip("Click → /history")

        # v1.6.12 — cumulative cost pill (updates after each turn's result event)
        # v1.6.63 — clickable: fires /cost.
        self._cost_pill = _ClickPill("$0.0000", self, intercept="/cost")
        self._cost_pill.setObjectName("ModePill")
        self._cost_pill.setStyleSheet(
            f"color: {PURPLE_PRIMARY}; background-color: transparent; "
            f"border: 1px solid {BORDER}; border-radius: 10px; "
            f"padding: 2px 9px; font-size: 10px; font-weight: 600; "
            f"font-family: 'JetBrains Mono', monospace;"
        )
        self._cost_pill.setToolTip(
            "Cumulative claude API cost across all turns in this card. "
            "Click for full breakdown (same as /cost)."
        )

        # v1.6.39 — live elapsed-time pill. Only visible during in-flight
        # turns. Updates every 1s from a QTimer reading _turn_started_ts.
        # Operators can see at a glance whether a turn is hung (e.g. 5m+
        # with no streaming) and reach for Esc / /cancel reflexively.
        # v1.6.64 — clickable: fires /timer for the full report.
        self._elapsed_pill = _ClickPill("--", self, intercept="/timer")
        self._elapsed_pill.setObjectName("ModePill")
        self._elapsed_pill.setStyleSheet(
            f"color: #f0a020; background-color: transparent; "
            f"border: 1px solid {BORDER}; border-radius: 10px; "
            f"padding: 2px 9px; font-size: 10px; font-weight: 600; "
            f"font-family: 'JetBrains Mono', monospace;"
        )
        self._elapsed_pill.setToolTip(
            "Elapsed time of the in-flight turn. Esc or /cancel kills "
            "it. Click for /timer report (or type /timer)."
        )
        self._elapsed_pill.hide()
        self._elapsed_timer = QTimer(self)
        self._elapsed_timer.setInterval(1000)
        self._elapsed_timer.timeout.connect(self._refresh_elapsed_pill)

        # v1.6.45 — tag chips container. Hidden when no tags. /tag adds,
        # /untag removes. Rebuilt entirely on every mutation (cheap; chips
        # are stateless QLabels).
        self._tags_host = QWidget()
        _th = QHBoxLayout(self._tags_host)
        _th.setContentsMargins(0, 0, 0, 0)
        _th.setSpacing(4)
        self._tags_layout = _th
        self._tags_host.hide()

        # v1.6.28 — pin star (left of chevron). Toggles session.pinned;
        # AgentsView listens for pin_changed and re-sorts the grid so
        # pinned cards render at the top.
        self._pin_btn = QPushButton("☆")
        self._pin_btn.setObjectName("CardCloseBtn")  # reuse styling
        self._pin_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._pin_btn.setFixedSize(22, 22)
        self._pin_btn.setStyleSheet(
            f"QPushButton {{ color: {MUTED_FG}; background: transparent; "
            f"border: none; font-size: 16px; font-weight: 700; }}"
            f"QPushButton:hover {{ color: {PURPLE_PRIMARY}; }}"
        )
        self._pin_btn.setToolTip("Pin to top of grid (/pin)")
        self._pin_btn.clicked.connect(self._toggle_pin)

        # v1.6.27 — collapse chevron (left of close-X)
        self._collapse_btn = QPushButton("▾")
        self._collapse_btn.setObjectName("CardCloseBtn")  # reuse styling
        self._collapse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._collapse_btn.setFixedSize(22, 22)
        self._collapse_btn.setStyleSheet(
            f"QPushButton {{ color: {MUTED_FG}; background: transparent; "
            f"border: none; font-size: 16px; font-weight: 700; }}"
            f"QPushButton:hover {{ color: {PURPLE_PRIMARY}; }}"
        )
        self._collapse_btn.setToolTip("Collapse / expand this card (Ctrl+M)")
        self._collapse_btn.clicked.connect(self._toggle_collapsed)

        # Close button — SVG x-mark, no glyph
        close_btn = QPushButton()
        close_btn.setObjectName("CardCloseBtn")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setFixedSize(22, 22)
        if _HAS_SVG:
            close_layout = QHBoxLayout(close_btn)
            close_layout.setContentsMargins(0, 0, 0, 0)
            close_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            close_layout.addWidget(nav_icon("xmark", size=12))
        close_btn.clicked.connect(self._on_close)

        hdr.addWidget(self.status_dot)
        hdr.addWidget(project_label)
        hdr.addWidget(title)
        hdr.addWidget(mode_pill)
        hdr.addWidget(self._turn_pill)
        hdr.addWidget(self._cost_pill)
        hdr.addWidget(self._elapsed_pill)
        hdr.addWidget(self._tags_host)
        hdr.addStretch(1)
        hdr.addWidget(self._pin_btn)
        hdr.addWidget(self._collapse_btn)
        hdr.addWidget(close_btn)
        root.addLayout(hdr)

        # Terminal — v1.6.13 bumped min-height 170 → 240 for breathing room
        # (operator was scrolling within a tiny window during long replies).
        self.terminal = QPlainTextEdit()
        self.terminal.setObjectName("Terminal")
        self.terminal.setReadOnly(True)
        font = QFont("Cascadia Mono", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.terminal.setFont(font)
        self.terminal.setMinimumHeight(240)
        root.addWidget(self.terminal, stretch=1)

        # Input row — multi-line, Enter to send, Shift+Enter for newline
        input_row = QHBoxLayout()
        input_row.setSpacing(SPACINGS["sm"])
        self.input = _MultiLineInput()
        # v1.6.59 — mirror the input contents into session.input_draft so
        # _write_resume_point can persist a half-typed message. Live-
        # tracking is cheap (small string assignment per keystroke); we
        # only pay disk on /save or auto-save on close.
        self.input.textChanged.connect(self._sync_input_draft)
        # v1.6.62 — Up/Down arrow history recall. Provider returns a
        # fresh list each time so notes / forget-last / replay don't
        # leave stale entries.
        self.input._history_callback = lambda: [
            (t.get("user") or "")
            for t in self.session.turns
            if t.get("user") and t.get("kind") != "note"
        ]
        self.input.setPlaceholderText(
            f"Talk to {eve_label(self.session.agent_name, self.session.project_key)} — "
            f"Enter to send · Shift+Enter for newline · /help"
        )
        # Style the multi-line input to match the prior QLineEdit look
        # (Terminal already has its own QSS rule via #TerminalInput; we
        # alias the object name so both pick up the same theme).
        self.input.setStyleSheet(
            f"QPlainTextEdit#MultiLineInput {{"
            f"  background-color: {ELEVATED};"
            f"  color: {FG};"
            f"  border: 1px solid {BORDER};"
            f"  border-radius: 7px;"
            f"  padding: 7px 10px;"
            f"  font-family: {MONO_FONT};"
            f"  font-size: 12px;"
            f"}}"
            f"QPlainTextEdit#MultiLineInput:focus {{"
            f"  border-color: {PURPLE_PRIMARY};"
            f"}}"
        )
        self.input.submit.connect(self._on_input_submit)
        # v1.6.17 — attach slash-command autocomplete popup. Owned by the
        # card so Qt can clean it up; positioned above the input on demand.
        self._slash_popup = _SlashPopup(self)
        self._slash_popup.completed.connect(self._on_slash_completed)
        self.input.slash_popup = self._slash_popup
        self.send_btn = QPushButton("Send")
        self.send_btn.setObjectName("SendBtn")
        self.send_btn.clicked.connect(self._on_send)
        input_row.addWidget(self.input, stretch=1)
        input_row.addWidget(self.send_btn, alignment=Qt.AlignmentFlag.AlignBottom)
        root.addLayout(input_row)

        # Thinking indicator — visible only while waiting on `claude -p`.
        self._thinking_label = QLabel("")
        self._thinking_label.setObjectName("ThinkingLabel")
        self._thinking_label.setStyleSheet(
            f"color: {PURPLE_ACCENT}; background: transparent; "
            f"font-family: 'JetBrains Mono', 'Cascadia Mono', monospace; "
            f"font-size: 11px; padding: 0 4px;"
        )
        self._thinking_label.setVisible(False)
        root.addWidget(self._thinking_label)

        # Seed banner
        self._append_terminal(
            f"  ▸ {eve_label(self.session.agent_name, self.session.project_key)}\n"
            f"    pane_id={self.session.pane_id}   mode={self.session.mode}\n"
            f"    session_uuid={self.session.session_uuid or '(generated on first send)'}\n"
            f"    created {self.session.created_at}\n"
            f"\n"
            f"    Type a message to begin. /help for slash commands.\n"
            f"\n"
        )

    def _append_terminal(self, text: str) -> None:
        # v1.6.14 — sticky-scroll: if the operator has scrolled up to read
        # earlier output, don't yank them back to the bottom when new
        # tokens stream in. Only auto-scroll when the scrollbar was already
        # at (or within 6px of) the bottom.
        sb = self.terminal.verticalScrollBar()
        was_at_bottom = sb is None or sb.value() >= sb.maximum() - 6
        # v1.6.25 — insert at end with the DEFAULT char format (clear any
        # prior dim format from the cursor) so a /retry or fresh stream
        # doesn't inherit the timestamp's muted color.
        cursor = self.terminal.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.setCharFormat(QTextCharFormat())
        cursor.insertText(text)
        self.terminal.setTextCursor(cursor)
        if was_at_bottom and sb is not None:
            sb.setValue(sb.maximum())

    def _append_dim(self, text: str) -> None:
        """v1.6.25 — append text rendered in MUTED_FG (timestamp gutter,
        etc). Preserves sticky-scroll behavior."""
        sb = self.terminal.verticalScrollBar()
        was_at_bottom = sb is None or sb.value() >= sb.maximum() - 6
        cursor = self.terminal.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(MUTED_FG))
        cursor.setCharFormat(fmt)
        cursor.insertText(text)
        # Reset format so the next _append_terminal call starts clean
        cursor.setCharFormat(QTextCharFormat())
        self.terminal.setTextCursor(cursor)
        if was_at_bottom and sb is not None:
            sb.setValue(sb.maximum())

    def _set_status(self, state_str: str) -> None:
        self.session.status = state_str
        self.status_dot.setProperty("state", state_str)
        color = _STATUS_COLOR.get(state_str, DIM)
        self.status_dot.setStyleSheet(
            f"background-color: {color}; border-radius: 6px;"
        )
        needs_glow = (state_str == "awaiting-input")
        self.setProperty("needs_input", needs_glow)
        self.style().unpolish(self)
        self.style().polish(self)
        if needs_glow:
            self._apply_glow()
        else:
            self._remove_glow()
        self.status_changed.emit(self.session.pane_id, state_str)

    def _apply_glow(self) -> None:
        if self._glow_effect is None:
            eff = QGraphicsDropShadowEffect(self)
            eff.setBlurRadius(20)
            color = QColor(PURPLE_ACCENT)
            color.setAlpha(128)
            eff.setColor(color)
            eff.setOffset(0, 0)
            self._glow_effect = eff
        self.setGraphicsEffect(self._glow_effect)

    def _remove_glow(self) -> None:
        self.setGraphicsEffect(None)

    def _sync_input_draft(self) -> None:
        """v1.6.59 — keep session.input_draft in lockstep with the input
        contents so resume-point auto-save captures whatever's typed."""
        try:
            self.session.input_draft = self.input.toPlainText()
        except Exception:
            pass

    def _rebuild_tags(self) -> None:
        """v1.6.45 — render tag chips in the header. Called after /tag,
        /untag, or on construction if resume-point restored tags.
        v1.6.52 — chips are clickable: clicking emits find_requested
        with the chip text so the grid scrolls to the next match (same
        wrap-around cycle as /find-next)."""
        # Wipe existing chips
        while self._tags_layout.count():
            item = self._tags_layout.takeAt(0)
            w = item.widget() if item else None
            if w is not None:
                w.setParent(None)
                w.deleteLater()
        tags = self.session.tags or []
        if not tags:
            self._tags_host.hide()
            return
        for t in tags:
            chip = _TagChip(t, self)
            # v1.6.58 — hash-stable per-tag color (or semantic-reserved
            # color for common tag names like blocked/wip/done).
            fg, bg, border = _tag_colors(t)
            chip.setStyleSheet(
                f"color: {fg}; background-color: {bg}; "
                f"border: 1px solid {border}; border-radius: 10px; "
                f"padding: 2px 9px; font-size: 10px; font-weight: 600;"
            )
            self._tags_layout.addWidget(chip)
        self._tags_host.show()

    def _flash_for_find(self, ms: int = 1500) -> None:
        """v1.6.43 — temporary bright purple drop-shadow so operator can
        see which card /find landed on. Restores the previous effect
        (awaiting-input glow or None) after `ms`. Does not interfere
        with the persistent status-glow because it uses a fresh effect
        instance and reads `session.status` at restore time."""
        eff = QGraphicsDropShadowEffect(self)
        eff.setBlurRadius(32)
        color = QColor(PURPLE_ACCENT)
        color.setAlpha(220)
        eff.setColor(color)
        eff.setOffset(0, 0)
        self.setGraphicsEffect(eff)
        def _restore() -> None:
            if self.session.status == "awaiting-input":
                self._apply_glow()
            else:
                self._remove_glow()
        QTimer.singleShot(ms, _restore)

    # ── Thinking spinner (jcode-style busy indicator) ─────────────────
    def _start_thinking(self) -> None:
        import time as _t
        self._spinner_idx = 0
        self._thinking_start_ts = _t.time()
        self._thinking_label.setVisible(True)
        self._spinner_timer.start()
        self._tick_spinner()
        # Disable input while turn is in flight.
        self.input.setEnabled(False)
        self.send_btn.setEnabled(False)

    def _stop_thinking(self) -> None:
        self._spinner_timer.stop()
        self._thinking_label.setVisible(False)
        self._thinking_label.setText("")
        self.input.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.input.setFocus()

    def _on_clear_shortcut(self) -> None:
        """Ctrl+L → mirror /clear (jcode keybinding parity)."""
        self.terminal.clear()
        self._append_terminal("[cleared via Ctrl+L]\n")

    def _refresh_elapsed_pill(self) -> None:
        """v1.6.39 — QTimer callback (1Hz) while a turn is in flight.
        Pulls live elapsed from _turn_started_ts and updates the pill
        text. The pill is shown/hidden by _start_elapsed/_stop_elapsed."""
        if self._turn_started_ts is None:
            return
        elapsed = time.monotonic() - self._turn_started_ts
        self._elapsed_pill.setText(f"{self._fmt_duration(elapsed)}")

    def _start_elapsed(self) -> None:
        """v1.6.39 — show the pill + tick the 1Hz timer. Called from
        _on_send right after _turn_started_ts is set."""
        self._elapsed_pill.setText("0.0s")
        self._elapsed_pill.show()
        self._elapsed_timer.start()

    def _stop_elapsed(self) -> None:
        """v1.6.39 — stop the timer + hide pill. Called from
        _on_finished and /cancel after _last_turn_seconds is captured."""
        self._elapsed_timer.stop()
        self._elapsed_pill.hide()

    @staticmethod
    def _fmt_duration(seconds: float | None) -> str:
        """v1.6.38 — human-readable duration. <60s = `Xs`; <1h = `Mm Ss`;
        else `Hh Mm`. None → `--`."""
        if seconds is None or seconds < 0:
            return "--"
        s = int(seconds)
        if s < 60:
            return f"{seconds:.1f}s"
        if s < 3600:
            return f"{s // 60}m {s % 60}s"
        return f"{s // 3600}h {(s % 3600) // 60}m"

    def _cancel_if_running(self) -> None:
        """v1.6.37 — Esc shortcut entry point. Forwards to /cancel only
        when a turn is in-flight; silently no-ops otherwise so Esc-mashing
        in an idle card doesn't spam the terminal."""
        if self._proc is None or self._proc.state() == QProcess.ProcessState.NotRunning:
            return
        self._maybe_intercept("/cancel")

    def _grep_cycle(self, direction: str, verbose: bool = False) -> None:
        """v1.6.36 — shared cycle helper used by both /grep-next /
        /grep-prev slash commands AND F3 / Shift+F3 shortcuts.
        verbose=True prints a status line; verbose=False stays silent
        (keyboard shortcut shouldn't spam the terminal)."""
        if not self._grep_positions:
            if verbose:
                self._append_terminal(
                    "[/grep-*] no active /grep — run `/grep <pattern>` first\n"
                )
            return
        n = len(self._grep_positions)
        step = 1 if direction == "next" else -1
        self._grep_idx = (self._grep_idx + step) % n
        pos = self._grep_positions[self._grep_idx]
        cur = QTextCursor(self.terminal.document())
        cur.setPosition(pos)
        self.terminal.setTextCursor(cur)
        self.terminal.ensureCursorVisible()
        if verbose:
            self._append_terminal(
                f"[/grep-{direction}] match {self._grep_idx + 1} / {n} "
                f"for '{self._grep_pattern}'\n"
            )

    def _toggle_pin(self) -> None:
        """v1.6.28 — toggle this card's pin state. Pinned cards float
        to the top of the AgentsView grid regardless of project_key
        sort. Visually: hollow ☆ → filled ★, gray → purple."""
        self.session.pinned = not self.session.pinned
        if self.session.pinned:
            self._pin_btn.setText("★")
            self._pin_btn.setStyleSheet(
                f"QPushButton {{ color: {PURPLE_PRIMARY}; "
                f"background: transparent; border: none; font-size: 16px; "
                f"font-weight: 700; }}"
                f"QPushButton:hover {{ color: {PURPLE_PRIMARY}; }}"
            )
        else:
            self._pin_btn.setText("☆")
            self._pin_btn.setStyleSheet(
                f"QPushButton {{ color: {MUTED_FG}; background: transparent; "
                f"border: none; font-size: 16px; font-weight: 700; }}"
                f"QPushButton:hover {{ color: {PURPLE_PRIMARY}; }}"
            )
        self.pin_changed.emit(self.session.pane_id)

    def _toggle_collapsed(self) -> None:
        """v1.6.27 — collapse / expand the card body (terminal + input).
        Header stays visible so operator can still see project / status /
        cost / turn-count and click + to expand. Useful with 5+ active
        cards stacked in the niri-scroll grid."""
        self._collapsed = not self._collapsed
        # Toggle child visibility
        self.terminal.setVisible(not self._collapsed)
        if self._collapsed:
            self._thinking_label.setVisible(False)
        self.input.setVisible(not self._collapsed)
        self.send_btn.setVisible(not self._collapsed)
        # Swap chevron glyph
        self._collapse_btn.setText("▸" if self._collapsed else "▾")
        # Adjust min-height: 40px header strip vs 280px full
        if self._collapsed:
            self.setMinimumHeight(40)
            self.setMaximumHeight(54)   # tight strip
        else:
            self.setMaximumHeight(16777215)  # QWIDGETSIZE_MAX
            self.setMinimumHeight(280)

    def _on_slash_completed(self, cmd: str) -> None:
        """Operator picked a slash command from the autocomplete popup.
        Replace the input text with the command + trailing space so the
        operator can immediately type any args."""
        self.input.setPlainText(cmd + " ")
        cur = self.input.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.End)
        self.input.setTextCursor(cur)
        self.input.setFocus()

    # ── v1.6.16 markdown post-stream formatting ───────────────────────
    # Applied once per turn after _on_finished. We don't try to format
    # mid-stream because the closing ``` / ` markers may not have arrived
    # yet — easier to do one pass at end with QTextCursor + QTextCharFormat.
    def _apply_markdown_format(self, start: int, end: int) -> None:
        """Format markdown spans in the [start, end) document range:
          - ``` ... ``` triple-backtick blocks → mono + darker bg
          - `inline code`                      → mono + subtle bg + purple
          - **bold**                            → bold weight
        """
        from PyQt6.QtGui import QTextCharFormat
        doc = self.terminal.document()
        # Select the reply text (Qt uses   for newline in selectedText,
        # but positions are 1:1 with the underlying document chars).
        sel = QTextCursor(doc)
        sel.setPosition(start)
        sel.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        text = sel.selectedText().replace(' ', '\n')

        def apply_fmt(s: int, e: int, fmt: QTextCharFormat) -> None:
            c = QTextCursor(doc)
            c.setPosition(s)
            c.setPosition(e, QTextCursor.MoveMode.KeepAnchor)
            c.mergeCharFormat(fmt)

        # ``` code block ``` — DOTALL across newlines
        fence_fmt = QTextCharFormat()
        fence_font = QFont("JetBrains Mono", 10)
        fence_font.setStyleHint(QFont.StyleHint.Monospace)
        fence_fmt.setFont(fence_font)
        fence_fmt.setBackground(QColor("#08060c"))
        fence_fmt.setForeground(QColor("#E8D6FF"))
        for m in re.finditer(r"```[\w-]*\n?(.*?)```", text, re.DOTALL):
            apply_fmt(start + m.start(), start + m.end(), fence_fmt)

        # `inline code` — single-line only (no newline allowed inside)
        inline_fmt = QTextCharFormat()
        inline_font = QFont("JetBrains Mono", 10)
        inline_font.setStyleHint(QFont.StyleHint.Monospace)
        inline_fmt.setFont(inline_font)
        inline_fmt.setBackground(QColor("#1c1c1e"))
        inline_fmt.setForeground(QColor("#C39DFF"))
        for m in re.finditer(r"(?<!`)`([^`\n]+)`(?!`)", text):
            apply_fmt(start + m.start(), start + m.end(), inline_fmt)

        # **bold** — single-line emphasis
        bold_fmt = QTextCharFormat()
        bold_fmt.setFontWeight(QFont.Weight.Bold)
        for m in re.finditer(r"\*\*([^*\n]+)\*\*", text):
            apply_fmt(start + m.start(), start + m.end(), bold_fmt)

    def _tick_spinner(self) -> None:
        import time as _t
        ch = self._SPINNER[self._spinner_idx % len(self._SPINNER)]
        self._spinner_idx += 1
        elapsed = _t.time() - self._thinking_start_ts
        # v1.6.18 — show the current tool if one is active, else generic.
        if self._current_tool:
            label = f"● {self._current_tool}…"
        else:
            label = "EVE is thinking…"
        self._thinking_label.setText(
            f"{ch}  {label}  ({elapsed:.1f}s)"
        )

    # v1.6.18 — rotating placeholder hints. Cycles a small set of
    # operator-discoverable hints in the input's placeholderText.
    _PLACEHOLDERS_TEMPLATE = [
        "Talk to {who} — Enter to send · Shift+Enter for newline · /help",
        "Type / to autocomplete a slash command · /help lists all 14",
        "Ctrl+L clears scrollback · /save writes a resume-point",
        "Shift+Enter = multi-line · /retry resends the last message",
        "/cost shows cumulative spend · /persona prints identity",
        "/skills lists Sanctum skills · /vault shows vault status",
    ]

    def _rotate_placeholder(self) -> None:
        if not hasattr(self, "input"):
            return
        # Skip rotation when input has text or busy turn — don't distract.
        try:
            if self.input.toPlainText():
                return
            if self._proc is not None and self._proc.state() != QProcess.ProcessState.NotRunning:
                return
        except Exception:
            return
        idx = self._placeholder_idx % len(self._PLACEHOLDERS_TEMPLATE)
        self._placeholder_idx += 1
        who = eve_label(self.session.agent_name, self.session.project_key)
        self.input.setPlaceholderText(
            self._PLACEHOLDERS_TEMPLATE[idx].format(who=who)
        )

    # ── Slash-command intercept ───────────────────────────────────────
    def _maybe_intercept(self, text: str) -> bool:
        cmd = text.strip()
        if not cmd.startswith("/"):
            return False
        head = cmd.split(None, 1)[0].lower()
        if head == "/help":
            # v1.6.57 — auto-generate from SLASH_COMMANDS so /help can't
            # rot out of sync with the registry as new commands ship.
            # Sorted alphabetically; aligned at the widest command name.
            self._append_terminal(
                f"[/help]  {len(SLASH_COMMANDS)} slash commands "
                "(RKOJ-side intercepts):\n"
            )
            width = max(len(cmd) for cmd, _ in SLASH_COMMANDS)
            for cmd_name, desc in sorted(SLASH_COMMANDS):
                self._append_terminal(
                    f"  {cmd_name:<{width}}  {desc}\n"
                )
            self._append_terminal(
                "\n"
                "  Any other text is forwarded to EVE as a turn in this session.\n"
                "  Session continuity: `claude --session-id <uuid>` on first turn +\n"
                "  `--resume <uuid>` on every subsequent turn (claude tracks the\n"
                "  conversation server-side; each turn only sends the latest message).\n"
                "  See also: /shortcuts for keyboard bindings + click affordances.\n"
            )
            return True
        if head == "/skill":
            # v1.6.20 — load a saved skill .md and send its content as a turn.
            parts = cmd.split(None, 1)
            if len(parts) < 2 or not parts[1].strip():
                self._append_terminal(
                    "[/skill] usage: /skill <name>\n"
                    "  Loads `<name>.md` (or `<name>/SKILL.md`) from your skill\n"
                    "  roots and sends its content as if you typed it. Use /skills\n"
                    "  to list what's available.\n"
                )
                return True
            name = parts[1].strip()
            roots = [
                Path(r"D:\Sinister Sanctum\skills"),
                Path.home() / ".sinister" / "skills",
                Path.home() / ".claude" / "skills",
            ]
            found_fp = None
            for r in roots:
                for cand in (r / f"{name}.md", r / name / "SKILL.md"):
                    if cand.exists():
                        found_fp = cand
                        break
                if found_fp:
                    break
            if not found_fp:
                self._append_terminal(
                    f"[/skill] no skill `{name}` found in:\n"
                    + "\n".join(f"  - {r}" for r in roots) + "\n"
                )
                return True
            try:
                skill_text = found_fp.read_text(encoding="utf-8")
            except Exception as exc:
                self._append_terminal(f"[/skill] failed to read {found_fp}: {exc}\n")
                return True
            # v1.6.69 — parse jcode-style YAML frontmatter if present.
            fm, body = _parse_skill_frontmatter(skill_text)
            send_text = body if fm else skill_text
            meta_parts: list[str] = []
            if fm.get("name"):
                meta_parts.append(f"name={fm['name']}")
            if fm.get("description"):
                d = fm["description"]
                meta_parts.append(f"description={d[:60]}{'…' if len(d) > 60 else ''}")
            if fm.get("allowed-tools"):
                tools = fm["allowed-tools"]
                if isinstance(tools, list):
                    meta_parts.append(f"allowed-tools=[{', '.join(tools)}]")
                else:
                    meta_parts.append(f"allowed-tools={tools}")
            meta = " · ".join(meta_parts) if meta_parts else "(no frontmatter)"
            self._append_terminal(
                f"[/skill] loaded {found_fp.name} ({len(skill_text):,} chars)\n"
                f"  {meta}\n"
                f"  → sending {len(send_text):,} chars as a turn…\n"
            )
            self.input.setPlainText(send_text)
            cur = self.input.textCursor()
            cur.movePosition(QTextCursor.MoveOperation.End)
            self.input.setTextCursor(cur)
            # Schedule the send on the next event-loop tick (0ms timer) so
            # the terminal updates render before claude starts.
            QTimer.singleShot(0, self._on_send)
            return True
        if head == "/skills":
            from pathlib import Path
            roots = [
                Path(r"D:\Sinister Sanctum\skills"),
                Path.home() / ".sinister" / "skills",
                Path.home() / ".claude" / "skills",
            ]
            # v1.6.69 — parse frontmatter to enrich the listing with
            # name + description (jcode parity). Falls back to the
            # filename for skills with no frontmatter.
            found: list[tuple[Path, dict]] = []
            for r in roots:
                if not r.exists():
                    continue
                for p in list(r.glob("*.md")) + list(r.glob("*/SKILL.md")):
                    try:
                        fm, _ = _parse_skill_frontmatter(
                            p.read_text(encoding="utf-8", errors="ignore")[:4096]
                        )
                    except Exception:
                        fm = {}
                    found.append((p, fm))
            if not found:
                self._append_terminal(
                    "[/skills] no .md skills found in:\n"
                    + "\n".join(f"  - {r}" for r in roots) + "\n"
                )
            else:
                self._append_terminal(f"[/skills] {len(found)} skill(s):\n")
                for fp, fm in found[:30]:
                    short = fp.stem if fp.name != "SKILL.md" else fp.parent.name
                    name = fm.get("name") or short
                    desc = fm.get("description") or ""
                    if desc:
                        desc = f" — {desc[:60]}{'…' if len(desc) > 60 else ''}"
                    self._append_terminal(f"  /skill {name}{desc}\n")
                if len(found) > 30:
                    self._append_terminal(f"  ... ({len(found) - 30} more)\n")
            return True
        if head == "/mcp":
            from pathlib import Path
            mcp_paths = [
                Path.home() / ".claude" / ".mcp.json",
                Path.home() / ".claude.json",
            ]
            mp = next((p for p in mcp_paths if p.exists()), None)
            if not mp:
                self._append_terminal(
                    "[/mcp] no MCP config found at ~/.claude/.mcp.json or ~/.claude.json\n"
                )
                return True
            try:
                with open(mp, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                servers = data.get("mcpServers", {}) if isinstance(data, dict) else {}
                self._append_terminal(
                    f"[/mcp] {len(servers)} server(s) from {mp.name}:\n"
                )
                for name in sorted(servers.keys()):
                    cfg = servers.get(name, {})
                    cmd = cfg.get("command") or cfg.get("url") or "(no command/url)"
                    self._append_terminal(f"  - {name}: {str(cmd)[:80]}\n")
            except Exception as exc:
                self._append_terminal(f"[/mcp] parse failed: {exc}\n")
            return True
        if head == "/vault":
            from pathlib import Path
            vault_dir = Path(r"D:\sinister-vault")
            if not vault_dir.exists():
                self._append_terminal(
                    "[/vault] vault dir not found at D:\\sinister-vault\n"
                    "  Install: see tools/sinister-vault/INSTALL-MCP.md\n"
                )
                return True
            try:
                import shutil as _sh
                usage = _sh.disk_usage(str(vault_dir))
                used_pct = (1 - usage.free / usage.total) * 100 if usage.total else 0
                self._append_terminal(
                    f"[/vault] D:\\sinister-vault\n"
                    f"  total : {usage.total / (1024**3):.1f} GB\n"
                    f"  used  : {(usage.total - usage.free) / (1024**3):.1f} GB ({used_pct:.1f}%)\n"
                    f"  free  : {usage.free / (1024**3):.1f} GB\n"
                    f"  daemon: expected at http://127.0.0.1:5078 (use `sinister vault status`)\n"
                )
            except Exception as exc:
                self._append_terminal(f"[/vault] disk usage failed: {exc}\n")
            return True
        if head == "/memory":
            self._append_terminal(
                "[/memory] forge-memory-bridge BM25 recall is shipped at\n"
                "  D:\\Sinister Sanctum\\tools\\forge-memory-bridge\\\n"
                "  Use the bundled API: from forge_memory_bridge import api; api.recall('...')\n"
                "  Phase-2: this slash will invoke the bridge in-process from RKOJ.\n"
            )
            return True
        if head == "/open":
            self._append_terminal(
                f"[/open]\n"
                f"  PROGRESS log    : start \"\" \"{self.session.progress_path}\"\n"
                f"  resume-points   : explorer \"{self.session.resume_dir}\"\n"
                f"  heartbeat       : start \"\" \"{self.session.heartbeat_path}\"\n"
                f"  inbox           : explorer \"{self.session.inbox_dir}\"\n"
                f"  brain index     : start \"\" \"D:\\Sinister Sanctum\\_shared-memory\\knowledge\\_INDEX.md\"\n"
                f"  master plan     : start \"\" \"D:\\Sinister Sanctum\\_shared-memory\\MASTER-PLAN.md\"\n"
            )
            return True
        if head == "/open-folder":
            # v1.6.77 — silent Explorer popup at project root (no cmd flash).
            try:
                from . import state as _state
                proj_root = None
                for p in _state.load_projects():
                    if p.key == self.session.project_key:
                        proj_root = p.root
                        break
                if not proj_root or not Path(proj_root).exists():
                    proj_root = str(state.SHARED_MEMORY.parent)
                import os as _os
                _os.startfile(proj_root)
                self._append_terminal(f"[/open-folder] opened {proj_root}\n")
            except Exception as exc:
                self._append_terminal(f"[/open-folder] failed: {exc}\n")
            return True
        if head == "/open-resume":
            try:
                target = self.session.resume_dir
                if not target or not Path(target).exists():
                    target = str(state.SHARED_MEMORY / "resume-points")
                import os as _os
                _os.startfile(target)
                self._append_terminal(f"[/open-resume] opened {target}\n")
            except Exception as exc:
                self._append_terminal(f"[/open-resume] failed: {exc}\n")
            return True
        if head == "/cancel":
            # v1.6.37 — kill the in-flight turn cleanly without taking down
            # the card. Keeps session_uuid intact so the next message just
            # resumes via --resume <uuid>. Esc keyboard shortcut also routes
            # here. No-op (with hint) when nothing is running.
            if self._proc is None or self._proc.state() == QProcess.ProcessState.NotRunning:
                self._append_terminal("[/cancel] no active turn to cancel\n")
                return True
            # v1.6.38 — freeze elapsed for the cancelled turn so /timer
            # can still report "last turn took Xs (cancelled)".
            elapsed = None
            if self._turn_started_ts is not None:
                elapsed = time.monotonic() - self._turn_started_ts
                self._last_turn_seconds = elapsed
                self._turn_started_ts = None
            try:
                self._proc.kill()
                self._proc.waitForFinished(1500)
            except Exception as exc:
                self._append_terminal(f"[/cancel] kill failed: {exc}\n")
                return True
            self._stop_thinking()
            # v1.6.39 — hide the live elapsed pill on cancel too.
            self._stop_elapsed()
            # Apply markdown to whatever streamed before the cancel so
            # partial output stays readable.
            try:
                end_pos = self.terminal.textCursor().position()
                if self._reply_started and end_pos > self._reply_start_pos:
                    self._apply_markdown_format(self._reply_start_pos, end_pos)
            except Exception:
                pass
            self._proc = None
            self._set_status("online")
            tail = f" after {self._fmt_duration(elapsed)}" if elapsed is not None else ""
            self._append_terminal(
                f"\n[/cancel] turn cancelled{tail} — session still resumable\n"
            )
            return True
        if head == "/clear":
            self.terminal.clear()
            self._append_terminal("[cleared]\n")
            return True
        if head == "/budget":
            combined = self._total_in_tokens + self._total_out_tokens
            pct = (combined / _TOKEN_WARN_THRESHOLD) * 100 if _TOKEN_WARN_THRESHOLD else 0
            bar_width = 30
            filled = min(bar_width, int(bar_width * combined / _TOKEN_WARN_THRESHOLD)) if _TOKEN_WARN_THRESHOLD else 0
            bar = "█" * filled + "░" * (bar_width - filled)
            self._append_terminal(
                f"[/budget] cumulative tokens (in+out):\n"
                f"  {bar}  {combined:,} / {_TOKEN_WARN_THRESHOLD:,} ({pct:.0f}%)\n"
                f"  in     : {self._total_in_tokens:,}\n"
                f"  out    : {self._total_out_tokens:,}\n"
                f"  cost   : ${self._total_cost_usd:.4f}\n"
            )
            if combined >= _TOKEN_WARN_THRESHOLD:
                self._append_terminal(
                    "  ! at/over warn threshold — consider /summarize or /clone\n"
                )
            return True
        if head in ("/clone", "/dup"):
            # v1.6.41 — spawn a sibling card with the same project + mode
            # but a fresh session UUID. Useful when one agent is set up
            # well and operator wants a parallel session on a related
            # task without re-picking from the New Agent dialog.
            pk = self.session.project_key or "sanctum"
            mode = self.session.mode or "claude"
            self._append_terminal(
                f"[/clone] spawning sibling card → project={self.session.project_display} mode={mode}\n"
            )
            self.clone_requested.emit(pk, mode)
            return True
        if head == "/copy":
            # v1.6.33 — copy the most recent EVE reply to the clipboard
            # so operator can paste it into a PR, an Obsidian note, etc.
            # without selecting text in the terminal manually.
            from PyQt6.QtWidgets import QApplication
            last = next(
                (t for t in reversed(self.session.turns) if t.get("assistant")),
                None,
            )
            if not last:
                self._append_terminal(
                    "[/copy] no EVE reply yet — send a message first\n"
                )
                return True
            text = (last.get("assistant") or "").strip()
            if not text:
                self._append_terminal("[/copy] last reply was empty\n")
                return True
            try:
                cb = QApplication.clipboard()
                cb.setText(text)
                preview = text.replace("\n", " ")[:60]
                self._append_terminal(
                    f"[/copy] copied {len(text):,} chars to clipboard\n"
                    f"  preview: {preview}…\n"
                )
            except Exception as exc:
                self._append_terminal(f"[/copy] failed: {exc}\n")
            return True
        if head == "/cost":
            n_turns = len([t for t in self.session.turns if t.get("user")])
            avg_cost = (self._total_cost_usd / n_turns) if n_turns else 0.0
            self._append_terminal(
                f"[/cost]  cumulative spend for this card:\n"
                f"  turns      : {n_turns}\n"
                f"  input tok  : {self._total_in_tokens:,}\n"
                f"  output tok : {self._total_out_tokens:,}\n"
                f"  total cost : ${self._total_cost_usd:.4f}\n"
                f"  avg / turn : ${avg_cost:.4f}\n"
            )
            return True
        if head == "/focus":
            # v1.6.19 — re-focus the input box. Useful if operator clicked
            # into the terminal scrollback to copy text + lost typing focus.
            self.input.setFocus()
            self._append_terminal("[/focus] input refocused\n")
            return True
        if head == "/forget-last":
            # v1.6.56 — drop the last user/assistant pair from local
            # session.turns. CAVEAT: claude --resume retains the turn
            # server-side; this only affects RKOJ's local UI state +
            # /history + /replay numbering + resume-point JSON.
            # Notes (kind=note) are skipped — we want to remove the
            # last real turn, not the last annotation.
            last_idx = None
            for i in range(len(self.session.turns) - 1, -1, -1):
                t = self.session.turns[i]
                if t.get("kind") == "note":
                    continue
                if t.get("user"):
                    last_idx = i
                    break
            if last_idx is None:
                self._append_terminal(
                    "[/forget-last] no prior user turn to forget\n"
                )
                return True
            removed = self.session.turns.pop(last_idx)
            preview = (removed.get("user") or "").rstrip().replace("\n", " ")[:60]
            # Refresh the turn pill since the user-turn count decreased.
            try:
                n_now = len([t for t in self.session.turns if t.get("user")])
                self._turn_pill.setText(f"{n_now} turn{'s' if n_now != 1 else ''}")
            except Exception:
                pass
            try:
                self._write_resume_point(save_reason="forget-last")
            except Exception:
                pass
            self._append_terminal(
                f"[/forget-last] dropped locally: '{preview}{'…' if len(preview) >= 60 else ''}'\n"
                f"  NOTE: claude --resume still has this turn server-side.\n"
                f"  This only affects /history + /replay numbering + resume-point JSON.\n"
            )
            return True
        if head == "/jump":
            # v1.6.68 — cursor-only navigation: scroll to first <pattern>
            # match without setting any highlight overlay. Lighter than
            # /grep when operator just wants to find their place.
            parts = cmd.split(None, 1)
            if len(parts) < 2 or not parts[1].strip():
                self._append_terminal("[/jump] usage: /jump <pattern>\n")
                return True
            pattern = parts[1].strip()
            doc = self.terminal.document()
            cursor = doc.find(pattern)
            if cursor.isNull():
                self._append_terminal(f"[/jump] no match for '{pattern}'\n")
                return True
            self.terminal.setTextCursor(cursor)
            self.terminal.ensureCursorVisible()
            self._append_terminal(f"[/jump] cursor at first match for '{pattern}'\n")
            return True
        if head == "/font-up":
            self._terminal_font_size = min(36, self._terminal_font_size + 1)
            f = QFont("Cascadia Mono", self._terminal_font_size)
            f.setStyleHint(QFont.StyleHint.Monospace)
            self.terminal.setFont(f)
            self._append_terminal(f"[/font-up] terminal font: {self._terminal_font_size}pt\n")
            return True
        if head == "/font-down":
            self._terminal_font_size = max(6, self._terminal_font_size - 1)
            f = QFont("Cascadia Mono", self._terminal_font_size)
            f.setStyleHint(QFont.StyleHint.Monospace)
            self.terminal.setFont(f)
            self._append_terminal(f"[/font-down] terminal font: {self._terminal_font_size}pt\n")
            return True
        if head == "/font-reset":
            self._terminal_font_size = 10
            f = QFont("Cascadia Mono", 10)
            f.setStyleHint(QFont.StyleHint.Monospace)
            self.terminal.setFont(f)
            self._append_terminal("[/font-reset] terminal font: 10pt\n")
            return True
        if head == "/wrap":
            cur = self.terminal.lineWrapMode()
            if cur == QPlainTextEdit.LineWrapMode.NoWrap:
                self.terminal.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
                self._append_terminal("[/wrap] soft-wrap ON\n")
            else:
                self.terminal.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
                self._append_terminal("[/wrap] soft-wrap OFF\n")
            return True
        if head == "/forget-n":
            # v1.6.68 — pop a specific user turn (1-indexed). Same
            # caveat as /forget-last: claude --resume keeps it server-side.
            parts = cmd.split(None, 1)
            user_idx_pairs = [
                (i, t) for i, t in enumerate(self.session.turns)
                if t.get("user") and t.get("kind") != "note"
            ]
            if not user_idx_pairs:
                self._append_terminal("[/forget-n] no user turns to forget\n")
                return True
            if len(parts) < 2:
                self._append_terminal(
                    f"[/forget-n] usage: /forget-n <N>  (1..{len(user_idx_pairs)})\n"
                )
                return True
            try:
                n = int(parts[1].strip())
            except ValueError:
                self._append_terminal(f"[/forget-n] N must be an integer\n")
                return True
            if n < 1 or n > len(user_idx_pairs):
                self._append_terminal(
                    f"[/forget-n] N={n} out of range (1..{len(user_idx_pairs)})\n"
                )
                return True
            real_idx, removed = user_idx_pairs[n - 1]
            self.session.turns.pop(real_idx)
            preview = (removed.get("user") or "").rstrip().replace("\n", " ")[:60]
            try:
                n_now = len([t for t in self.session.turns if t.get("user")])
                self._turn_pill.setText(f"{n_now} turn{'s' if n_now != 1 else ''}")
            except Exception:
                pass
            try:
                self._write_resume_point(save_reason="forget-n")
            except Exception:
                pass
            self._append_terminal(
                f"[/forget-n] dropped local turn #{n}: '{preview}{'…' if len(preview) >= 60 else ''}'\n"
                f"  NOTE: claude --resume still has it server-side.\n"
            )
            return True
        if head == "/goto-card":
            # v1.6.68 — exact pane_id prefix focus (different from /find
            # which does substring across project+agent+id+tags).
            parts = cmd.split(None, 1)
            if len(parts) < 2 or not parts[1].strip():
                self._append_terminal(
                    f"[/goto-card] usage: /goto-card <pane_id-prefix>\n"
                    f"  This card's pane_id: {self.session.pane_id}\n"
                )
                return True
            # Fan via find_requested — _focus_find's haystack already
            # includes pane_id; substring-match within IDs (which are
            # 12-char hex) is effectively a prefix match.
            self.find_requested.emit(self.session.pane_id, parts[1].strip())
            return True
        if head == "/uptime-all":
            self.uptime_all_requested.emit(self.session.pane_id)
            return True
        if head == "/grep":
            # v1.6.34 — highlight matching text via QTextEdit.ExtraSelection
            # overlay so the document's underlying char formats (markdown
            # code blocks, dim timestamp gutter) stay intact. /grep-clear
            # removes the overlay without touching anything else.
            # v1.6.35 — also stores match positions so /grep-next /
            # /grep-prev can cycle through without re-searching.
            parts = cmd.split(None, 1)
            # v1.6.47 — /grep with no arg reuses _grep_pattern if present
            # (restored from resume-point on card spawn). Useful workflow:
            # close card → re-open → type /grep → highlights re-apply.
            if len(parts) < 2 or not parts[1].strip():
                if self._grep_pattern:
                    pattern = self._grep_pattern
                    self._append_terminal(
                        f"[/grep] re-applying stored pattern: '{pattern}'\n"
                    )
                else:
                    self._append_terminal(
                        "[/grep] usage: /grep <pattern>\n"
                        "  Highlights matching text with yellow background.\n"
                        "  /grep-next + /grep-prev cycle through matches.\n"
                        "  /grep-clear removes the highlights.\n"
                    )
                    return True
            else:
                pattern = parts[1].strip()
            try:
                from PyQt6.QtWidgets import QTextEdit
                doc = self.terminal.document()
                extras: list = []
                positions: list[int] = []
                cursor = QTextCursor(doc)
                hl_fmt = QTextCharFormat()
                hl_fmt.setBackground(QColor("#FFCC00"))
                hl_fmt.setForeground(QColor("#000000"))
                while True:
                    cursor = doc.find(pattern, cursor)
                    if cursor.isNull():
                        break
                    sel = QTextEdit.ExtraSelection()
                    sel.cursor = cursor
                    sel.format = hl_fmt
                    extras.append(sel)
                    positions.append(cursor.position())
                self.terminal.setExtraSelections(extras)
                self._grep_pattern = pattern
                self._grep_positions = positions
                self._grep_idx = 0 if positions else -1
                if extras:
                    first = doc.find(pattern)
                    if not first.isNull():
                        self.terminal.setTextCursor(first)
                    self._append_terminal(
                        f"[/grep] {len(extras)} match(es) for '{pattern}' "
                        f"— /grep-next + /grep-prev cycle; /grep-clear removes\n"
                    )
                else:
                    self._append_terminal(
                        f"[/grep] no matches for '{pattern}'\n"
                    )
            except Exception as exc:
                self._append_terminal(f"[/grep] failed: {exc}\n")
            return True
        if head == "/grep-clear":
            try:
                self.terminal.setExtraSelections([])
                self._grep_pattern = ""
                self._grep_positions = []
                self._grep_idx = -1
                self._append_terminal("[/grep-clear] highlights cleared\n")
            except Exception as exc:
                self._append_terminal(f"[/grep-clear] failed: {exc}\n")
            return True
        if head in ("/grep-next", "/grep-prev"):
            direction = "next" if head == "/grep-next" else "prev"
            self._grep_cycle(direction, verbose=True)
            return True
        if head == "/minimize-all":
            self._append_terminal("[/minimize-all] collapsing all cards…\n")
            self.minimize_all_requested.emit()
            return True
        if head == "/expand-all":
            self._append_terminal("[/expand-all] expanding all cards…\n")
            self.expand_all_requested.emit()
            return True
        if head == "/find":
            # v1.6.42 — fan to AgentsView, which scrolls the grid to a
            # card whose project_display / agent_name / pane_id prefix
            # matches <text>. Echoes feedback via this card's terminal.
            parts = cmd.split(None, 1)
            if len(parts) < 2 or not parts[1].strip():
                self._append_terminal(
                    "[/find] usage: /find <text>\n"
                    "  Scrolls the grid to the first card matching <text>\n"
                    "  (case-insensitive substring of project / agent / id).\n"
                    "  v1.6.43: use /find-next to cycle further matches.\n"
                )
                return True
            self.find_requested.emit(self.session.pane_id, parts[1].strip())
            return True
        if head == "/find-next":
            # v1.6.43 — empty query reuses AgentsView's _last_find_query
            # and advances idx by 1 (wraps). Bright flash on the new match.
            self.find_requested.emit(self.session.pane_id, "")
            return True
        if head == "/model":
            # v1.6.19 — show or change the model alias for subsequent turns.
            # Note: claude --resume is locked to the original model. To
            # actually pick a different model the operator should start a
            # fresh card via + Create Agent (the dialog has the picker).
            # This slash only affects NEW sessions / future first-turn sends.
            parts = cmd.split(None, 1)
            if len(parts) == 1:
                self._append_terminal(
                    f"[/model] current mode: {self.session.mode}\n"
                    f"  Aliases (set with /model <alias>):\n"
                    f"    claude        — default Claude Code model\n"
                    f"    claude-haiku  — fast (--model haiku)\n"
                    f"    claude-opus   — deep (--model opus)\n"
                    f"  Note: changing mid-session has no effect — claude\n"
                    f"  --resume is locked to the model the session was created\n"
                    f"  with. To switch, open a new card via + Create Agent.\n"
                )
                return True
            alias = parts[1].strip().lower()
            valid = {"claude", "claude-haiku", "claude-opus"}
            if alias not in valid:
                self._append_terminal(
                    f"[/model] unknown alias `{alias}`. "
                    f"Valid: {', '.join(sorted(valid))}\n"
                )
                return True
            self.session.mode = alias
            # v1.6.77 — persist to agent-prefs.json so the operator's
            # pick survives close → reopen (Sinister Start.bat reads
            # this file on spawn; we now write to it on /model).
            try:
                import json as _json
                prefs_fp = state.SHARED_MEMORY / "agent-prefs.json"
                prefs_fp.parent.mkdir(parents=True, exist_ok=True)
                prefs = {}
                if prefs_fp.exists():
                    try:
                        prefs = _json.loads(prefs_fp.read_text(encoding="utf-8"))
                    except Exception:
                        prefs = {}
                entry = prefs.setdefault(self.session.agent_name, {})
                # Map mode alias → claude --model arg
                model_arg = {"claude-haiku": "haiku",
                             "claude-opus": "opus"}.get(alias)
                if model_arg:
                    entry["model"] = model_arg
                else:
                    entry.pop("model", None)
                prefs_fp.write_text(_json.dumps(prefs, indent=2), encoding="utf-8")
            except Exception:
                pass
            self._append_terminal(
                f"[/model] mode -> {alias} (persisted to agent-prefs.json)\n"
                f"  Will take effect on the NEXT session you spawn for this agent\n"
                f"  (claude --resume locks the model to the session's original).\n"
            )
            return True
        if head == "/api":
            # v1.6.83 — print the workstation API surface so EVE knows
            # what endpoints are available without having to read source.
            try:
                from . import api_server
                st = api_server.api_status()
            except Exception:
                st = {"running": False, "url": "http://127.0.0.1:5077"}
            self._append_terminal(
                f"[/api]  workstation API "
                f"{'(LIVE)' if st['running'] else '(offline)'} "
                f"-> {st['url']}\n"
                f"  Endpoints (use any HTTP client):\n"
                f"    GET  /api/health                       service uptime + version\n"
                f"    GET  /api/version                      sinister_rkoj_qt version\n"
                f"    GET  /api/phones                       adb devices + claim owners\n"
                f"    POST /api/phones/<serial>/claim        {{agent_id, agent_display}}\n"
                f"    POST /api/phones/<serial>/release      {{agent_id?}}\n"
                f"    POST /api/phones/<serial>/screenshot   {{agent_id}} -> Desktop PNG\n"
                f"    POST /api/phones/<serial>/shell        {{agent_id, cmd}}\n"
                f"    POST /api/phones/<serial>/install-apk  {{agent_id, apk_path, replace?}}\n"
                f"    GET  /api/agents                       claim-owners + counts\n"
                f"  Owner-check enforced on shell + screenshot + install-apk.\n"
                f"  Loopback-only (127.0.0.1) - no external exposure.\n"
            )
            return True
        if head == "/devices":
            # v1.6.18 — adb device list inline (mirrors Devices tab).
            devs = state.list_adb_devices()
            if not devs:
                self._append_terminal(
                    "[/devices] no ADB devices connected\n"
                    "  Plug a phone in (USB) or run `adb connect <ip>:5555`.\n"
                )
            else:
                self._append_terminal(f"[/devices] {len(devs)} device(s):\n")
                for d in devs:
                    self._append_terminal(
                        f"  {d.state:14s}  {d.serial:24s}  {d.model or '(no model)'}\n"
                    )
            return True
        if head == "/diff":
            # v1.6.50 — unified diff between two assistant replies. Uses
            # the same 1-indexed user-turn numbering as /replay + /show.
            # Pairs with /clone: run the same prompt in sibling cards,
            # /diff the replies to see how the models diverged.
            parts = cmd.split()
            user_turns = [t for t in self.session.turns if t.get("user")]
            if len(user_turns) < 2:
                self._append_terminal(
                    "[/diff] need at least 2 prior user turns with replies\n"
                )
                return True
            if len(parts) < 3:
                self._append_terminal(
                    f"[/diff] usage: /diff <A> <B>  (1..{len(user_turns)})\n"
                    "  Unified diff between assistant reply A and reply B.\n"
                )
                return True
            try:
                a_idx = int(parts[1])
                b_idx = int(parts[2])
            except ValueError:
                self._append_terminal(
                    f"[/diff] A and B must be integers 1..{len(user_turns)}\n"
                )
                return True
            for label, n in (("A", a_idx), ("B", b_idx)):
                if n < 1 or n > len(user_turns):
                    self._append_terminal(
                        f"[/diff] {label}={n} out of range (1..{len(user_turns)})\n"
                    )
                    return True
            if a_idx == b_idx:
                self._append_terminal("[/diff] A == B (no diff)\n")
                return True
            a_text = (user_turns[a_idx - 1].get("assistant") or "").rstrip()
            b_text = (user_turns[b_idx - 1].get("assistant") or "").rstrip()
            if not a_text or not b_text:
                self._append_terminal(
                    "[/diff] one or both replies are empty (cancelled / no reply captured)\n"
                )
                return True
            a_lines = a_text.splitlines(keepends=True)
            b_lines = b_text.splitlines(keepends=True)
            udiff = difflib.unified_diff(
                a_lines, b_lines,
                fromfile=f"reply #{a_idx}",
                tofile=f"reply #{b_idx}",
                n=2,
            )
            self._append_terminal(f"[/diff] reply {a_idx} -> reply {b_idx}:\n")
            wrote = False
            for line in udiff:
                if not line.endswith("\n"):
                    line += "\n"
                self._append_terminal(line)
                wrote = True
            if not wrote:
                self._append_terminal("  (replies are identical)\n")
            return True
        if head == "/export":
            # v1.6.18 — write the full transcript to a markdown file under
            # the agent's resume_dir so operator can share or grep it.
            # v1.6.55 — body extracted to _export_to_markdown so AgentsView
            # /export-all can call it on every card.
            try:
                fp = self._export_to_markdown()
                self._append_terminal(f"[/export] wrote {fp}\n")
            except Exception as exc:
                self._append_terminal(f"[/export] failed: {exc}\n")
            return True
        if head == "/export-all":
            # v1.6.55 — fan-out to AgentsView which exports every card
            # into one timestamped bundle dir + echoes a summary back.
            self.export_all_requested.emit(self.session.pane_id)
            return True
        if head == "/fleet":
            # v1.6.66 — per-card table fan-out to AgentsView.
            # v1.6.67 — optional sort key: project|agent|mode|turns|cost|status.
            parts = cmd.split(None, 1)
            sort_key = parts[1].strip().lower() if len(parts) > 1 else ""
            self.fleet_table_requested.emit(self.session.pane_id, sort_key)
            return True
        if head == "/history":
            n = len(self.session.turns)
            self._append_terminal(f"[/history] {n} entr(y/ies):\n")
            # v1.6.46 — pre-compute user-turn index map so /replay N annotation
            # is visible inline (notes interleave but don't count for /replay).
            user_idx = 0
            visible = self.session.turns[-10:]
            start = max(1, n - 9)
            # Walk the head we're skipping just to advance user_idx correctly.
            for t in self.session.turns[:start - 1]:
                if t.get("user") and t.get("kind") != "note":
                    user_idx += 1
            for i, t in enumerate(visible, start=start):
                if t.get("kind") == "note":
                    txt = (t.get("text") or "").strip().replace("\n", " ")[:60]
                    self._append_terminal(f"  {i:2d}. ·· {txt}\n")
                    continue
                u = (t.get("user") or "").strip().replace("\n", " ")[:60]
                a = (t.get("assistant") or "").strip().replace("\n", " ")[:60]
                if u:
                    user_idx += 1
                    tag = f"replay:{user_idx}"
                    self._append_terminal(f"  {i:2d}. ({tag}) >> {u}\n      << {a}\n")
                else:
                    self._append_terminal(f"  {i:2d}. >> {u}\n      << {a}\n")
            return True
        if head == "/tag":
            # v1.6.45 — add a label chip to this card. Chips are also
            # included in /find's haystack so operators can search by tag.
            parts = cmd.split(None, 1)
            if len(parts) < 2 or not parts[1].strip():
                current = ", ".join(self.session.tags) if self.session.tags else "(none)"
                self._append_terminal(
                    f"[/tag] usage: /tag <label>\n  current tags: {current}\n"
                )
                return True
            label = parts[1].strip().lower()[:24]  # bound chip width
            if label in self.session.tags:
                self._append_terminal(f"[/tag] '{label}' already present\n")
                return True
            self.session.tags.append(label)
            self._rebuild_tags()
            try:
                self._write_resume_point(save_reason="tag")
            except Exception:
                pass
            self._append_terminal(f"[/tag] +{label}\n")
            return True
        if head == "/untag":
            parts = cmd.split(None, 1)
            if len(parts) < 2 or not parts[1].strip():
                self._append_terminal(
                    "[/untag] usage: /untag <label>  (or /untag * to clear all)\n"
                )
                return True
            arg = parts[1].strip().lower()
            if arg == "*":
                n = len(self.session.tags)
                self.session.tags.clear()
                self._rebuild_tags()
                try:
                    self._write_resume_point(save_reason="untag")
                except Exception:
                    pass
                self._append_terminal(f"[/untag] cleared {n} tag(s)\n")
                return True
            if arg not in self.session.tags:
                self._append_terminal(f"[/untag] '{arg}' not present\n")
                return True
            self.session.tags.remove(arg)
            self._rebuild_tags()
            try:
                self._write_resume_point(save_reason="untag")
            except Exception:
                pass
            self._append_terminal(f"[/untag] -{arg}\n")
            return True
        if head == "/tags":
            # v1.6.51 — fan to AgentsView, which walks every card +
            # builds a tag census echoed back to this card's terminal.
            self.tags_census_requested.emit(self.session.pane_id)
            return True
        if head == "/uptime":
            # v1.6.54 — card lifetime + turn count + last activity.
            now = time.monotonic()
            lifetime = now - self._spawn_ts
            n_turns = len([t for t in self.session.turns if t.get("user")])
            if self._last_send_ts is None:
                last_act = "(no turns sent yet)"
            else:
                last_act = self._fmt_duration(now - self._last_send_ts) + " ago"
            if self._turn_started_ts is not None:
                live = self._fmt_duration(now - self._turn_started_ts)
                status_line = f"in-flight ({live} elapsed)"
            else:
                status_line = f"idle (last turn took {self._fmt_duration(self._last_turn_seconds)})"
            self._append_terminal(
                f"[/uptime]\n"
                f"  card lifetime : {self._fmt_duration(lifetime)}\n"
                f"  turns sent    : {n_turns}\n"
                f"  last activity : {last_act}\n"
                f"  current state : {status_line}\n"
            )
            return True
        if head == "/rename":
            # v1.6.44 — change the agent display name. Updates the
            # header title label + session.agent_name. Persists on
            # next _write_resume_point (autosave on close / shutdown).
            parts = cmd.split(None, 1)
            if len(parts) < 2 or not parts[1].strip():
                self._append_terminal(
                    "[/rename] usage: /rename <new-name>\n"
                    "  Current name: " + (self.session.agent_name or "(none)") + "\n"
                )
                return True
            new_name = parts[1].strip()
            # Sanity bound — avoid pathological 1000-char header inputs.
            if len(new_name) > 60:
                new_name = new_name[:60]
            old_name = self.session.agent_name
            self.session.agent_name = new_name
            try:
                self._title_label.setText(eve_label(new_name, ""))
            except Exception:
                pass
            # Write to disk immediately so the rename survives crashes.
            try:
                self._write_resume_point(save_reason="rename")
            except Exception:
                pass
            self._append_terminal(
                f"[/rename] {old_name!r} -> {new_name!r}\n"
            )
            return True
        if head == "/replay":
            # v1.6.46 — re-run user turn #N verbatim. Unlike /retry which
            # pops the previous turn (assumed-failed), /replay stages an
            # old prompt without touching history. claude --resume already
            # has the full server-side context, so the replayed message
            # just becomes a fresh turn referring back to the prior one.
            parts = cmd.split(None, 1)
            user_turns = [t for t in self.session.turns if t.get("user")]
            if not user_turns:
                self._append_terminal("[/replay] no prior user turns to replay\n")
                return True
            if len(parts) < 2 or not parts[1].strip():
                self._append_terminal(
                    f"[/replay] usage: /replay <N>  (1..{len(user_turns)})\n"
                    "  Re-runs the N-th user turn verbatim. /history lists them.\n"
                )
                return True
            try:
                idx = int(parts[1].strip())
            except ValueError:
                self._append_terminal(
                    f"[/replay] N must be an integer 1..{len(user_turns)}\n"
                )
                return True
            if idx < 1 or idx > len(user_turns):
                self._append_terminal(
                    f"[/replay] N={idx} out of range (1..{len(user_turns)})\n"
                )
                return True
            target = user_turns[idx - 1]
            text = (target.get("user") or "").strip()
            if not text:
                self._append_terminal(f"[/replay] turn {idx} has empty user text\n")
                return True
            preview = text.replace("\n", " ")[:60]
            self._append_terminal(
                f"[/replay] re-sending turn {idx}: {preview}{'…' if len(text) > 60 else ''}\n"
            )
            self.input.setPlainText(text)
            self._on_send()
            return True
        if head == "/summarize":
            # v1.6.53 — canned TL;DR prompt sent to EVE. Useful for long
            # sessions when operator needs a "where are we" recap. Doesn't
            # need any turn-history math — claude --resume already has
            # the full context server-side.
            user_turns = [t for t in self.session.turns if t.get("user")]
            if not user_turns:
                self._append_terminal(
                    "[/summarize] no prior turns yet — send a message first\n"
                )
                return True
            self._append_terminal(
                "[/summarize] asking EVE for a TL;DR…\n"
            )
            self.input.setPlainText(_SUMMARIZE_PROMPT)
            self._on_send()
            return True
        if head == "/summarize-all":
            # v1.6.60 — fan /summarize to every card with prior turns.
            self.summarize_all_requested.emit(self.session.pane_id)
            return True
        if head == "/retry":
            last = next((t for t in reversed(self.session.turns) if t.get("user")), None)
            if not last:
                self._append_terminal("[/retry] no prior turn to retry\n")
                return True
            self._append_terminal(f"[/retry] resending last operator message\n")
            # v1.6.9 — input is QPlainTextEdit now; setPlainText not setText.
            self.input.setPlainText(last["user"])
            # Drop the previous (failed?) turn so /retry doesn't double-record
            try:
                self.session.turns.pop()
            except Exception:
                pass
            self._on_send()
            return True
        if head == "/persona":
            self._append_terminal(
                "[/persona]\n"
                f"  identity:    EVE on {self.session.project_display}\n"
                f"  slug:        {self.session.slug or '(not bootstrapped)'}\n"
                f"  session id:  {self.session.session_uuid or '(none)'}\n"
                f"  authorship:  RKOJ-ELENO\n"
                f"  branch hint: agent/{self.session.project_key}/<topic>\n"
                f"  heartbeat:   {self.session.heartbeat_path or '(none)'}\n"
                f"  progress:    {self.session.progress_path or '(none)'}\n"
                f"  resume dir:  {self.session.resume_dir or '(none)'}\n"
            )
            return True
        if head == "/session":
            uid = self.session.session_uuid or "(none — first turn not sent yet)"
            self._append_terminal(
                f"[/session] {uid}\n"
                f"  Resume from any terminal:\n"
                f"  claude --dangerously-skip-permissions -r {uid} -p 'your message'\n"
            )
            return True
        if head == "/show":
            # v1.6.49 — print full prompt + reply for user-turn #N.
            # /history shows previews; /show pulls the full text so
            # operator doesn't have to scroll the terminal scrollback.
            parts = cmd.split(None, 1)
            user_turns = [t for t in self.session.turns if t.get("user")]
            if not user_turns:
                self._append_terminal("[/show] no prior user turns to show\n")
                return True
            if len(parts) < 2 or not parts[1].strip():
                self._append_terminal(
                    f"[/show] usage: /show <N>  (1..{len(user_turns)})\n"
                    "  Prints the full prompt + reply for that user turn.\n"
                )
                return True
            try:
                idx = int(parts[1].strip())
            except ValueError:
                self._append_terminal(
                    f"[/show] N must be an integer 1..{len(user_turns)}\n"
                )
                return True
            if idx < 1 or idx > len(user_turns):
                self._append_terminal(
                    f"[/show] N={idx} out of range (1..{len(user_turns)})\n"
                )
                return True
            target = user_turns[idx - 1]
            u = (target.get("user") or "").rstrip()
            a = (target.get("assistant") or "").rstrip()
            self._append_terminal(
                f"[/show] turn {idx}/{len(user_turns)}:\n"
                f"────── prompt ──────\n{u}\n"
                f"────── reply ──────\n{a if a else '(no reply captured)'}\n"
                f"────── end ──────\n"
            )
            return True
        if head == "/shortcuts":
            # v1.6.48 — operator-facing keyboard + click cheat sheet.
            # v1.6.62 added Up/Down history recall.
            # v1.6.63 added clickable pills (turn → /history, cost → /cost).
            self._append_terminal(
                "[/shortcuts]  keyboard:\n"
                "  Ctrl+L      clear this card's terminal (jcode parity)\n"
                "  Ctrl+M      collapse / expand this card\n"
                "  F3          scroll to next /grep match\n"
                "  Shift+F3    scroll to previous /grep match\n"
                "  Esc         cancel the in-flight turn (same as /cancel)\n"
                "  Shift+Enter newline in input (Enter alone sends)\n"
                "  Up / Down   recall prior user turns in input (when empty)\n"
                "\n"
                "[/shortcuts]  card header click affordances:\n"
                "  ☆ / ★       pin/unpin (pinned cards float to top of grid)\n"
                "  ▾ / ▸       collapse / expand chevron (same as Ctrl+M)\n"
                "  ✕           close this card (autosaves resume-point first)\n"
                "  status dot  click → /persona\n"
                "  PROJECT     click → /find <project>\n"
                "  mode pill   click → /model\n"
                "  N turns     click → /history\n"
                "  $X.XXXX     click → /cost\n"
                "  elapsed   click → /timer\n"
                "  tag chip    L-click → /find <tag>, R-click → menu\n"
                "\n"
                "\n"
                "[/shortcuts]  v1.6.68 additions:\n"
                "  /jump <pat>     scroll cursor to first match (no highlight)\n"
                "  /font-up/-down/-reset   per-card terminal font zoom\n"
                "  /wrap           toggle soft line-wrap in terminal\n"
                "  /forget-n N     drop a specific user turn (server-side keeps)\n"
                "  /goto-card pfx  focus card by pane_id prefix\n"
                "  /uptime-all     fleet aggregate (lifetime + turns + cost)\n"
                "  /fleet uptime   sort table by oldest cards first\n"
                "\n"
                "[/shortcuts]  see /help for the full slash command list.\n"
            )
            return True
        if head == "/save":
            try:
                fp = self._write_resume_point(save_reason="manual")
                self._append_terminal(f"[/save] wrote {fp}\n")
            except Exception as exc:
                self._append_terminal(f"[/save] failed: {exc}\n")
            return True
        if head == "/usage":
            # v1.6.21 — aggregate spend + tokens across ALL saved
            # resume-points in `_shared-memory/resume-points/EVE on */*.json`.
            # Operator's RKOJ-wide spend at a glance.
            try:
                self._render_usage_totals()
            except Exception as exc:
                self._append_terminal(f"[/usage] failed: {exc}\n")
            return True
        if head == "/timer":
            # v1.6.38 — report in-flight turn elapsed, or last completed
            # duration when idle. Pairs with /cancel: operator can see
            # "this has been running 4m17s" before deciding to kill it.
            if self._turn_started_ts is not None:
                live = time.monotonic() - self._turn_started_ts
                self._append_terminal(
                    f"[/timer] in-flight turn: {self._fmt_duration(live)} elapsed "
                    f"(use /cancel or Esc to kill)\n"
                )
            elif self._last_turn_seconds is not None:
                self._append_terminal(
                    f"[/timer] no active turn · last turn took "
                    f"{self._fmt_duration(self._last_turn_seconds)}\n"
                )
            else:
                self._append_terminal(
                    "[/timer] no active turn · no completed turns yet\n"
                )
            return True
        if head == "/stats":
            # v1.6.23 — RKOJ fleet snapshot. Reuses state.snapshot() which
            # already drives the bottom status bar.
            try:
                snap = state.snapshot()
                self._append_terminal(
                    f"[/stats] RKOJ fleet snapshot:\n"
                    f"  heartbeats  : {snap.agents_online} online / "
                    f"{snap.agents_total} total\n"
                    f"  inbox       : {snap.inbox_count} unread messages\n"
                    f"  brain       : {snap.brain_count} doctrine entries\n"
                    f"  devices     : {snap.phones_online} online · "
                    f"{snap.phones_offline} offline · "
                    f"{snap.phones_needs_auth} unauth\n"
                    f"  vault used  : {snap.vault_used_pct:.1f}%\n"
                    f"  pending ops : {snap.pending_requests} in inbox/sanctum/\n"
                )
            except Exception as exc:
                self._append_terminal(f"[/stats] failed: {exc}\n")
            return True
        if head == "/broadcast":
            # v1.6.30 — fan-out send: emit the rest of the message so
            # AgentsView can route it to every live card. The originating
            # card also receives the message (so operator gets a record
            # in this card too).
            parts = cmd.split(None, 1)
            if len(parts) < 2 or not parts[1].strip():
                self._append_terminal(
                    "[/broadcast] usage: /broadcast <message>\n"
                    "  Fans the message to every live agent card.\n"
                )
                return True
            msg = parts[1].strip()
            self._append_terminal(
                f"[/broadcast] fanning to all live cards…\n"
            )
            self.broadcast_requested.emit(msg)
            return True
        if head == "/ping":
            # v1.6.32 — canned status-check broadcast. Optional project
            # filter as arg: `/ping kernel-apk` only pings cards on that
            # project. With no arg, pings ALL live cards. Body of the
            # message is a short status template so EVE knows to give a
            # quick status, not a long-form reply.
            parts = cmd.split(None, 1)
            project_filter = parts[1].strip().lower() if len(parts) > 1 else None
            template = (
                "STATUS CHECK: one short paragraph — what are you working on, "
                "any blockers, last operator-visible action you took. Keep it "
                "under 60 words."
            )
            self._append_terminal(
                f"[/ping] sending canned status-check"
                + (f" to project={project_filter}" if project_filter else " to ALL live cards")
                + "…\n"
            )
            # Emit a broadcast_requested with a sentinel prefix that
            # AgentsView understands — we use a special signal-suffix
            # convention so the AgentsView.broadcast can pick up the
            # filter without us needing a second signal.
            if project_filter:
                self.broadcast_requested.emit(
                    f"__PING_PROJECT__{project_filter}__:{template}"
                )
            else:
                self.broadcast_requested.emit(template)
            return True
        if head == "/pin":
            # v1.6.28 — mirror the star button click. Operator can pin
            # from the chat without aiming for the small button.
            self._toggle_pin()
            self._append_terminal(
                f"[/pin] {'pinned' if self.session.pinned else 'unpinned'} this card "
                f"({'★' if self.session.pinned else '☆'})\n"
            )
            return True
        if head == "/reset-budget":
            old_cost = self._total_cost_usd
            old_in = self._total_in_tokens
            old_out = self._total_out_tokens
            self._total_cost_usd = 0.0
            self._total_in_tokens = 0
            self._total_out_tokens = 0
            self._token_warning_shown = False
            try:
                self._cost_pill.setText("$0.0000")
            except Exception:
                pass
            self._append_terminal(
                f"[/reset-budget] cleared cumulative tally\n"
                f"  was: ${old_cost:.4f} · {old_in:,} in · {old_out:,} out\n"
                f"  now: $0.0000 · 0 in · 0 out\n"
            )
            return True
        if head == "/plan":
            # v1.6.76 — toggle plan-only mode (jcode parity). When on,
            # the next turn's user message is prefixed with a PLAN-ONLY
            # directive that asks EVE to propose changes without
            # executing edits / writes / commands.
            self._plan_mode = not getattr(self, "_plan_mode", False)
            self._append_terminal(
                f"[/plan] plan-only mode {'ON' if self._plan_mode else 'OFF'}\n"
                f"  When ON, the next turn asks EVE to propose changes\n"
                f"  without running edits/writes/commands. Toggle again to resume.\n"
            )
            return True
        if head == "/needs":
            new_state = "awaiting-input" if self.session.status != "awaiting-input" else "online"
            self._set_status(new_state)
            self._append_terminal(f"[/needs] status -> {new_state}\n")
            return True
        if head == "/note":
            # v1.6.40 — drop a contextual annotation into the terminal.
            # NOT sent to EVE; stored on session.turns with kind="note"
            # so resume-point JSON serializes it. /retry + turn-pill
            # already filter via `t.get("user")` so notes don't pollute.
            parts = cmd.split(None, 1)
            if len(parts) < 2 or not parts[1].strip():
                self._append_terminal(
                    "[/note] usage: /note <text>\n"
                    "  Drops a dim annotation line into the terminal and\n"
                    "  persists it with the session (visible via /notes).\n"
                )
                return True
            note_text = parts[1].strip()
            ts = datetime.now().strftime("%H:%M:%S")
            iso = datetime.now().isoformat()
            self._append_dim(f"[{ts}] · note · {note_text}\n")
            self.session.turns.append({
                "kind": "note",
                "ts": iso,
                "text": note_text,
            })
            return True
        if head == "/notes":
            # v1.6.40 — list every note in this card's session.turns.
            notes = [t for t in self.session.turns if t.get("kind") == "note"]
            if not notes:
                self._append_terminal(
                    "[/notes] no notes yet — drop one with `/note <text>`\n"
                )
                return True
            self._append_terminal(f"[/notes] {len(notes)} note(s):\n")
            for i, n in enumerate(notes, start=1):
                ts = (n.get("ts") or "")[:19].replace("T", " ")
                self._append_terminal(f"  {i:2d}. [{ts}] {n.get('text', '')}\n")
            return True
        if head == "/todo":
            # v1.6.75 — jcode parity: TODO tracking. Stored as a
            # `kind="todo"` entry on session.turns with done:bool flag.
            # Persisted via the same resume-point JSON path as notes.
            parts = cmd.split(None, 1)
            if len(parts) < 2 or not parts[1].strip():
                self._append_terminal(
                    "[/todo] usage: /todo <text>\n"
                    "  Adds a pending TODO. /todos lists; /done N marks done.\n"
                )
                return True
            text = parts[1].strip()
            iso = datetime.now().isoformat()
            self.session.turns.append({
                "kind": "todo",
                "ts": iso,
                "text": text,
                "done": False,
            })
            try:
                self._write_resume_point(save_reason="todo-add")
            except Exception:
                pass
            self._append_dim(f"[+todo] {text}\n")
            return True
        if head == "/todos":
            todos = [t for t in self.session.turns if t.get("kind") == "todo"]
            if not todos:
                self._append_terminal(
                    "[/todos] empty — add one with `/todo <text>`\n"
                )
                return True
            pending = [t for t in todos if not t.get("done")]
            done = [t for t in todos if t.get("done")]
            self._append_terminal(
                f"[/todos] {len(pending)} pending · {len(done)} done\n"
            )
            for i, t in enumerate(todos, start=1):
                mark = "[x]" if t.get("done") else "[ ]"
                ts = (t.get("ts") or "")[:19].replace("T", " ")
                self._append_terminal(
                    f"  {i:2d}. {mark} {t.get('text', '')}    ({ts})\n"
                )
            return True
        if head == "/done":
            parts = cmd.split(None, 1)
            todos = [t for t in self.session.turns if t.get("kind") == "todo"]
            if not todos:
                self._append_terminal(
                    "[/done] no TODOs — add one with `/todo <text>`\n"
                )
                return True
            if len(parts) < 2:
                self._append_terminal(
                    f"[/done] usage: /done <N>  (1..{len(todos)})\n"
                )
                return True
            try:
                n = int(parts[1].strip())
            except ValueError:
                self._append_terminal("[/done] N must be an integer\n")
                return True
            if n < 1 or n > len(todos):
                self._append_terminal(
                    f"[/done] N={n} out of range (1..{len(todos)})\n"
                )
                return True
            todo = todos[n - 1]
            if todo.get("done"):
                self._append_terminal(
                    f"[/done] #{n} already marked done: {todo.get('text', '')}\n"
                )
                return True
            todo["done"] = True
            todo["done_ts"] = datetime.now().isoformat()
            try:
                self._write_resume_point(save_reason="todo-done")
            except Exception:
                pass
            self._append_dim(f"[done] #{n} {todo.get('text', '')}\n")
            return True
        return False

    # ── Send / process I/O ────────────────────────────────────────────
    # v1.6.3 — session continuity via `--session-id` (first turn) +
    # `--resume <uuid>` (subsequent turns). No history-replay; claude
    # tracks the conversation server-side.

    def _on_input_submit(self, text: str) -> None:
        """Bridge: _MultiLineInput.submit → _on_send. The signal carries
        the already-trimmed text, so we just stage it back into the input
        and call _on_send (which handles intercepts + spawn)."""
        # We rely on _on_send pulling from self.input rather than the
        # signal payload, so just delegate.
        self._on_send()

    def _on_send(self) -> None:
        # v1.6.9 — input is now a multi-line QPlainTextEdit; use toPlainText
        # not text(). Trim whitespace + strip trailing newlines.
        text = self.input.toPlainText().strip()
        if not text:
            return
        if self._maybe_intercept(text):
            self.input.clear()
            return

        if self._proc is not None and self._proc.state() != QProcess.ProcessState.NotRunning:
            self._append_terminal("[busy] previous turn still running; waiting…\n")
            return

        # v1.6.24 — timestamp gutter so the operator can scan the
        # conversation chronologically and time-bound debug.
        # v1.6.25 — render the timestamp + operator-prefix in dim color
        # so the actual message body stands out.
        ts = datetime.now().strftime("%H:%M:%S")
        self._append_terminal("\n")
        self._append_dim(f"[{ts}] >> ")
        self._append_terminal(f"{text}\n")
        self.input.clear()
        self.session.turns.append({"user": text, "assistant": ""})
        self._reply_started = False

        claude = _find_claude_executable()
        if not claude:
            self._append_terminal(
                "[error] claude CLI not found on PATH.\n"
                "  Install Claude Code: https://claude.ai/download (CLI bundle)\n"
                "  Or verify: open a terminal and run `claude --version`.\n"
            )
            self._set_status("offline")
            return

        # v1.6.11 — stream-json output for true jcode parity (token-by-token
        # streaming, thinking blocks, tool_use display, cost per turn).
        # All operator messages now go through --output-format=stream-json
        # --include-partial-messages --verbose.
        # v1.6.3 args — first turn vs continuation.
        # v1.6.4 — mode picker can request a specific claude model via alias.
        args: list[str] = [
            "--dangerously-skip-permissions",
            "--output-format", "stream-json",
            "--include-partial-messages",
            "--verbose",
        ]
        # v1.6.76 — /plan mode prefix
        if getattr(self, "_plan_mode", False):
            text = (
                "[PLAN-ONLY MODE: do NOT run any edits, writes, bash, or "
                "tool calls that mutate state. Propose the change as a "
                "plan + diff preview only. Operator will toggle plan off "
                "when ready to apply.]\n\n"
            ) + text
        # v1.6.75 — Sinister Start.bat parity: agent-prefs.json model
        # override wins over the mode picker (operator sets intelligence
        # level per agent; this honors it on every spawn).
        prefs_model = _agent_prefs_model(self.session.agent_name)
        if prefs_model:
            args += ["--model", prefs_model]
        elif self.session.mode == "claude-haiku":
            args += ["--model", "haiku"]
        elif self.session.mode == "claude-opus":
            args += ["--model", "opus"]
        # "claude" (default model) + "anthropic-sdk" (Phase-2 stub) → no extra flag
        if self._first_turn:
            persona = build_opening_prompt(
                project_key=self.session.project_key,
                agent_name=self.session.agent_name,
                mode=self.session.mode,
                accent=self.session.accent,
            )
            args += [
                "--session-id", self.session.session_uuid,
                "--system-prompt", persona,
                "-p", text,
            ]
            self._first_turn = False
        else:
            args += [
                "--resume", self.session.session_uuid,
                "-p", text,
            ]
        # Reset stream-json parsing state for the new turn.
        self._stream_buf = ""
        self._stream_text_started = False
        self._stream_tools_run: list[str] = []

        proc = QProcess(self)
        proc.setProgram(claude)
        proc.setArguments(args)
        # Phase-1 memory bootstrap: pass SINISTER_* env vars so the child
        # learns its identity (slug / display / paths / persona).
        proc.setProcessEnvironment(_make_child_env(self.session))
        # v1.6.75 — Sinister Start.bat parity: cd to the project root
        # before claude spawns + pre-trust it in ~/.claude.json so no
        # first-run dialog blocks the first turn.
        proj_root = _project_root(self.session.project_key)
        if proj_root and Path(proj_root).exists():
            proc.setWorkingDirectory(proj_root)
        _pretrust_project(proj_root)
        # v1.6.10 — redirect child's stdin to the null device so claude
        # doesn't wait 3s for stdin data + print:
        #   "[stderr] Warning: no stdin data received in 3s, proceeding..."
        # That warning was leaking into the terminal and looking like a bug.
        proc.setStandardInputFile(QProcess.nullDevice())
        proc.readyReadStandardOutput.connect(self._on_stdout)
        proc.readyReadStandardError.connect(self._on_stderr)
        proc.finished.connect(self._on_finished)
        proc.errorOccurred.connect(self._on_error)
        self._proc = proc
        self._set_status("busy")
        self._start_thinking()
        # v1.6.38 — record turn start for /timer.
        self._turn_started_ts = time.monotonic()
        # v1.6.54 — update last activity timestamp for /uptime.
        self._last_send_ts = self._turn_started_ts
        # v1.6.39 — show + tick the live elapsed pill in the header.
        self._start_elapsed()
        try:
            proc.start()
        except Exception as exc:
            self._append_terminal(f"[error] failed to start claude: {exc}\n")
            self._stop_thinking()
            self._set_status("offline")

    def _on_stdout(self) -> None:
        """v1.6.11 — parses claude's `--output-format=stream-json` NDJSON
        stream and renders each event type with jcode-style formatting:

          - content_block_delta + text_delta → stream text into terminal
          - content_block_delta + thinking_delta → spinner text shows
            current thought head (60-char preview)
          - content_block_start + tool_use   → `● Tool(input)` header
          - tool_result via user/content_block → `✓ <result preview>`
          - result event → token usage + cost summary in card footer
        """
        if not self._proc:
            return
        raw = bytes(self._proc.readAllStandardOutput()).decode("utf-8", errors="replace")
        if not raw:
            return
        # Buffer + line-split (stream-json is NDJSON, one event per line,
        # but Qt may give us a partial line).
        self._stream_buf += _strip_ansi(raw)
        while "\n" in self._stream_buf:
            line, self._stream_buf = self._stream_buf.split("\n", 1)
            line = line.strip()
            if not line:
                continue
            # Try JSON; if it doesn't parse, treat as plain text.
            if line.startswith("{") and line.endswith("}"):
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    self._render_plain_chunk(line + "\n")
                    continue
                self._handle_stream_event(event)
            else:
                self._render_plain_chunk(line + "\n")

    def _render_plain_chunk(self, text: str) -> None:
        """Fallback when output isn't JSON (e.g., pre-stream init text)."""
        if not self._stream_text_started:
            self._stop_thinking()
            ts = datetime.now().strftime("%H:%M:%S")
            self._append_dim(f"[{ts}] << ")
            self._stream_text_started = True
            self._reply_started = True
        self._append_terminal(text)
        if self.session.turns:
            self.session.turns[-1]["assistant"] += text

    def _handle_stream_event(self, event: dict) -> None:
        t = event.get("type")
        if t == "stream_event":
            e = event.get("event", {})
            et = e.get("type")
            if et == "content_block_delta":
                delta = e.get("delta", {})
                dt = delta.get("type")
                if dt == "text_delta":
                    text = delta.get("text", "")
                    if text:
                        if not self._stream_text_started:
                            self._stop_thinking()
                            # v1.6.24 — timestamp gutter on EVE's reply too.
                            # v1.6.25 — render dim.
                            ts = datetime.now().strftime("%H:%M:%S")
                            self._append_dim(f"[{ts}] << ")
                            # v1.6.16 — record position AFTER "<< " prefix
                            # so markdown formatting only touches EVE's
                            # reply, not our own prefix.
                            self._reply_start_pos = (
                                self.terminal.textCursor().position()
                            )
                            self._stream_text_started = True
                            self._reply_started = True
                        self._append_terminal(text)
                        if self.session.turns:
                            self.session.turns[-1]["assistant"] += text
                elif dt == "thinking_delta":
                    # Live-update the spinner text with a thinking preview.
                    text = (delta.get("thinking") or "").strip()
                    if text and self._spinner_timer.isActive():
                        preview = text.replace("\n", " ")[:60]
                        ch = self._SPINNER[self._spinner_idx % len(self._SPINNER)]
                        self._thinking_label.setText(
                            f"{ch}  > {preview}"
                        )
            elif et == "content_block_start":
                cb = e.get("content_block", {})
                if cb.get("type") == "tool_use":
                    tool = cb.get("name", "")
                    self._stream_tools_run.append(tool)
                    # v1.6.18 — surface the active tool in the spinner so
                    # operator sees the LIVE step (Bash / Read / Edit / ...)
                    # not a generic "EVE is thinking".
                    self._current_tool = tool
                    # Tool args preview — strip to 80 chars
                    inp = cb.get("input", {})
                    try:
                        inp_str = json.dumps(inp, ensure_ascii=False)[:80]
                    except Exception:
                        inp_str = str(inp)[:80]
                    if not self._stream_text_started:
                        self._stop_thinking()
                        self._stream_text_started = True
                        self._reply_started = True
                    self._append_terminal(f"\n● {tool}({inp_str})\n")
                elif cb.get("type") == "thinking":
                    # Begin a thinking block — keep the spinner running but
                    # change its prefix so the operator knows EVE is reasoning.
                    if self._spinner_timer.isActive():
                        ch = self._SPINNER[self._spinner_idx % len(self._SPINNER)]
                        self._thinking_label.setText(f"{ch}  thinking…")
        elif t == "user":
            # tool_result emitted by claude after a tool runs.
            msg = event.get("message", {}) or {}
            for block in msg.get("content") or []:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    raw = block.get("content")
                    if isinstance(raw, list):
                        text = " ".join(
                            (b.get("text") or "") for b in raw if isinstance(b, dict)
                        )
                    else:
                        text = str(raw or "")
                    preview = text.replace("\n", " ").strip()[:120]
                    if preview:
                        self._append_terminal(f"  ✓ {preview}\n")
        elif t == "result":
            # v1.6.18 — clear active tool name (the spinner will go back to
            # generic "EVE is thinking" if more text streams in, though
            # typically the spinner is stopped by now).
            self._current_tool = None
            # Final summary: tokens + cost + duration in a footer line.
            usage = event.get("usage", {}) or {}
            in_tok = usage.get("input_tokens", 0) or 0
            out_tok = usage.get("output_tokens", 0) or 0
            cache_read = usage.get("cache_read_input_tokens", 0) or 0
            cost = event.get("total_cost_usd", 0) or 0
            dur = (event.get("duration_ms", 0) or 0) / 1000
            tools_note = (
                f" · tools: {', '.join(self._stream_tools_run)}"
                if self._stream_tools_run else ""
            )
            self._append_terminal(
                f"\n  ▸ {in_tok:,} in + {out_tok:,} out tokens "
                f"(cache_read={cache_read:,}) · ${cost:.4f} · {dur:.1f}s{tools_note}\n"
            )
            # v1.6.12 — accumulate + refresh the header cost pill.
            self._total_cost_usd += float(cost)
            self._total_in_tokens += int(in_tok)
            self._total_out_tokens += int(out_tok)
            try:
                self._cost_pill.setText(f"${self._total_cost_usd:.4f}")
                self._cost_pill.setToolTip(
                    f"Cumulative cost across all turns in this card.\n"
                    f"Total in:  {self._total_in_tokens:,} tokens\n"
                    f"Total out: {self._total_out_tokens:,} tokens\n"
                    f"Total cost: ${self._total_cost_usd:.4f}\n"
                    f"Type /cost in the chat for the full breakdown."
                )
            except Exception:
                pass
            # v1.6.70 — one-shot token-budget warning when combined
            # in+out crosses the threshold. Operator gets runway to
            # /summarize or /clone before truncation pressure hits.
            combined = self._total_in_tokens + self._total_out_tokens
            if (not self._token_warning_shown
                    and combined >= _TOKEN_WARN_THRESHOLD):
                self._token_warning_shown = True
                self._append_dim(
                    f"\n  ! token budget: {combined:,} cumulative tokens "
                    f"(≥{_TOKEN_WARN_THRESHOLD:,}). Consider /summarize, "
                    f"/clone fresh, or /export-all + start a new card.\n"
                )
        elif t == "system":
            # System events (init / status / hook_started / hook_response).
            # We don't render these to keep the terminal quiet — too verbose.
            return
        elif t == "rate_limit_event":
            # v1.6.20 — surface non-OK rate limit info inline. Suppress the
            # always-fires `status: allowed` case (no signal). When status
            # is `warning` / `exceeded` / anything else, print a one-line
            # warning so the operator isn't surprised by a hard wall.
            info = event.get("rate_limit_info", {}) or {}
            status = (info.get("status") or "").lower()
            if status and status != "allowed":
                reset_ts = info.get("resetsAt")
                kind = info.get("rateLimitType") or "rate-limit"
                reset_str = ""
                if isinstance(reset_ts, (int, float)):
                    try:
                        reset_str = (
                            "  resets at "
                            + datetime.fromtimestamp(reset_ts, tz=timezone.utc)
                                .strftime("%Y-%m-%d %H:%M UTC")
                        )
                    except Exception:
                        reset_str = ""
                self._append_terminal(
                    f"\n  ! rate-limit {status} ({kind}){reset_str}\n"
                )

    # v1.6.10 — benign stderr lines from claude that look like bugs in the
    # terminal but are info-level / harmless. Suppressed silently; real
    # errors still surface.
    _BENIGN_STDERR_RE = re.compile(
        r"(?:no stdin data received|redirect stdin explicitly|"
        r"piping from a slow command|wait longer)",
        re.IGNORECASE,
    )

    def _on_stderr(self) -> None:
        if not self._proc:
            return
        data = bytes(self._proc.readAllStandardError()).decode("utf-8", errors="replace")
        data = _strip_ansi(data)
        if not data.strip():
            return
        # Filter out benign info-level stderr noise so the terminal stays
        # clean. Anything that doesn't match the benign regex is shown
        # as a real error.
        if self._BENIGN_STDERR_RE.search(data):
            return
        self._append_terminal(f"\n[stderr] {data}")

    def _on_finished(self, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        # v1.6.38 — freeze turn duration for /timer before any UI work.
        if self._turn_started_ts is not None:
            self._last_turn_seconds = time.monotonic() - self._turn_started_ts
            self._turn_started_ts = None
        # v1.6.39 — stop ticking the live elapsed pill + hide it.
        self._stop_elapsed()
        if not self._reply_started:
            # Process exited with no stdout — show a meaningful error.
            self._stop_thinking()
            self._append_terminal(
                f"<< [no reply] claude exited with code {exit_code} and no output. "
                f"Try /retry, or verify `claude --version` in a terminal.\n"
            )
        else:
            self._append_terminal("\n")
            # v1.6.16 — apply markdown formatting to this turn's reply text
            # (code fences + inline code + bold). End_pos is the cursor
            # position right before the trailing newline we just appended.
            try:
                end_pos = self.terminal.textCursor().position() - 1
                if end_pos > self._reply_start_pos:
                    self._apply_markdown_format(self._reply_start_pos, end_pos)
            except Exception:
                pass
        if exit_code != 0:
            self._append_terminal(f"  (exit {exit_code})\n")
        self._set_status("online")
        # v1.6.9 — bump the turn-count pill in the card header so operator
        # sees the conversation length at a glance.
        try:
            n = len([t for t in self.session.turns if t.get("user")])
            self._turn_pill.setText(f"{n} turn{'s' if n != 1 else ''}")
        except Exception:
            pass
        self._proc = None

    def _on_error(self, err: QProcess.ProcessError) -> None:
        self._stop_thinking()
        # QProcess.ProcessError values: 0=FailedToStart 1=Crashed 2=Timedout
        # 3=WriteError 4=ReadError 5=UnknownError
        names = {0: "FailedToStart", 1: "Crashed", 2: "Timedout",
                 3: "WriteError", 4: "ReadError", 5: "UnknownError"}
        try:
            err_int = int(err) if hasattr(err, "__int__") else int(err.value)
        except Exception:
            err_int = -1
        name = names.get(err_int, str(err))
        self._append_terminal(f"\n[process error: {name}]\n")
        self._set_status("offline")

    def _on_close(self) -> None:
        if self._proc is not None and self._proc.state() != QProcess.ProcessState.NotRunning:
            self._proc.kill()
            self._proc.waitForFinished(2000)
        # v1.6.21 — auto-save resume-point on card close so the session
        # never silently vanishes. Operator can re-open via the empty-state
        # recent-sessions list (v1.6.15) or sidebar Sessions picker.
        try:
            self._write_resume_point(save_reason="autoclose")
        except Exception:
            pass
        try:
            self._hb_timer.stop()
            _refresh_heartbeat(self.session, "ended")
        except Exception:
            pass
        self.closed.emit(self.session.pane_id)

    def shutdown(self) -> None:
        """Called from main window closeEvent — kill child cleanly + autosave."""
        if self._proc is not None and self._proc.state() != QProcess.ProcessState.NotRunning:
            self._proc.kill()
            self._proc.waitForFinished(1500)
        # v1.6.21 — also auto-save on full-app shutdown (main RKOJ window
        # closing while cards are alive).
        try:
            self._write_resume_point(save_reason="app-shutdown")
        except Exception:
            pass
        try:
            self._hb_timer.stop()
            _refresh_heartbeat(self.session, "ended")
        except Exception:
            pass

    # v1.6.21 — single resume-point writer shared by /save, autoclose,
    # and app-shutdown paths. Skips if no turns happened yet (don't
    # litter the picker with empty sessions).
    def _export_to_markdown(self, target_dir: Path | None = None) -> Path:
        """v1.6.55 — write this card's full transcript to a markdown file.
        Extracted from /export so /export-all (fleet-wide) can call it
        on every card with a uniform output shape. Returns the file path.
        Raises on I/O failure (callers should catch + report)."""
        exp_dir = target_dir or Path(
            self.session.resume_dir or (state.SHARED_MEMORY / "exports")
        )
        exp_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
        # Include pane_id in filename so /export-all bundles don't collide
        # when multiple cards share a project resume_dir.
        fp = exp_dir / f"{ts}-{self.session.pane_id}-export.md"
        lines: list[str] = [
            f"# {self.session.display_name or self.session.agent_name}",
            "",
            f"- pane_id: `{self.session.pane_id}`",
            f"- session_uuid: `{self.session.session_uuid}`",
            f"- project_key: `{self.session.project_key}`",
            f"- mode: `{self.session.mode}`",
            f"- exported_at: {datetime.now(timezone.utc).isoformat()}",
            f"- turns: {len(self.session.turns)}",
            f"- total_cost: ${self._total_cost_usd:.4f}",
            "",
            "---",
            "",
        ]
        for i, t in enumerate(self.session.turns, 1):
            if t.get("kind") == "note":
                lines += [
                    f"## Note {i}",
                    "",
                    f"> {t.get('text', '')}",
                    "",
                ]
                continue
            lines += [
                f"## Turn {i}",
                "",
                "### Operator",
                "",
                "```",
                (t.get("user") or "").rstrip(),
                "```",
                "",
                "### EVE",
                "",
                (t.get("assistant") or "").rstrip(),
                "",
            ]
        fp.write_text("\n".join(lines), encoding="utf-8")
        return fp

    def _write_resume_point(self, save_reason: str = "manual") -> Path | None:
        if not any(t.get("user") for t in self.session.turns):
            return None  # skip empty cards
        if self.session.resume_dir:
            resume_dir = Path(self.session.resume_dir)
        else:
            resume_dir = state.SHARED_MEMORY / "rkoj-qt" / "resume-points"
        resume_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
        suffix = f"-{save_reason}" if save_reason != "manual" else ""
        fp = resume_dir / f"{ts}{suffix}.json"
        payload = {
            "schema_version": "sinister.resume-point.v1",
            "agent_identity": "EVE",
            "agent_display": self.session.display_name,
            "slug": self.session.slug,
            "pane_id": self.session.pane_id,
            "session_uuid": self.session.session_uuid,
            "project_key": self.session.project_key,
            "project_display": self.session.project_display,
            "agent_name": self.session.agent_name,
            "mode": self.session.mode,
            "turns": self.session.turns,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "save_reason": save_reason,
            # v1.6.21 — include cost telemetry so /usage can aggregate
            # without re-running each conversation.
            "total_cost_usd": self._total_cost_usd,
            "total_in_tokens": self._total_in_tokens,
            "total_out_tokens": self._total_out_tokens,
            # v1.6.31 — persist pin state so it survives close + re-spawn
            "pinned": self.session.pinned,
            # v1.6.45 — persist tag chips
            "tags": list(self.session.tags),
            # v1.6.47 — persist last /grep pattern so highlights re-apply
            # when the card is resumed (caveat: scrollback is fresh so
            # the pattern is stored on session.grep_pattern but the
            # actual highlight rebuild happens on first reply re-render).
            "grep_pattern": self._grep_pattern or "",
            # v1.6.59 — half-typed operator message so resume restores it
            "input_draft": self.session.input_draft or "",
            "resume_cmd": (
                f"claude --dangerously-skip-permissions "
                f"-r {self.session.session_uuid} -p 'your message'"
            ),
        }
        with open(fp, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        return fp

    def _render_usage_totals(self) -> None:
        """Walk _shared-memory/resume-points/EVE on */*.json and print
        per-project + grand totals. Newer saves overwrite older counts
        from the same session_uuid so multiple autosaves don't double-
        count (we keep the highest cost per uuid).

        v1.6.31 — also breaks out cost by mode (claude / haiku / opus)
        so operator can see which model is eating their budget."""
        rp_root = state.SHARED_MEMORY / "resume-points"
        if not rp_root.exists():
            self._append_terminal("[/usage] no resume-points dir yet\n")
            return
        # By session_uuid → keep the highest cost / token counts seen
        # (later saves typically have ≥ earlier counts since cost is
        # cumulative within a card's lifetime).
        per_uuid: dict[str, dict] = {}
        for proj_dir in rp_root.iterdir():
            if not proj_dir.is_dir():
                continue
            for fp in proj_dir.glob("*.json"):
                try:
                    with open(fp, "r", encoding="utf-8") as fh:
                        d = json.load(fh)
                except Exception:
                    continue
                uid = d.get("session_uuid") or ""
                if not uid:
                    continue
                cost = float(d.get("total_cost_usd", 0) or 0)
                in_tok = int(d.get("total_in_tokens", 0) or 0)
                out_tok = int(d.get("total_out_tokens", 0) or 0)
                prev = per_uuid.get(uid)
                if prev is None or cost > prev["cost"]:
                    per_uuid[uid] = {
                        "project": d.get("project_display") or proj_dir.name.replace("EVE on ", ""),
                        "mode": d.get("mode", "claude"),
                        "cost": cost,
                        "in_tok": in_tok,
                        "out_tok": out_tok,
                        "turns": len(d.get("turns", [])),
                    }
        if not per_uuid:
            self._append_terminal(
                "[/usage] no saved sessions with cost data yet.\n"
                "  Cost telemetry was added in v1.6.21 — older saves\n"
                "  may not have it. Spawn + chat + close some cards to\n"
                "  populate.\n"
            )
            return
        # Group by project
        per_proj: dict[str, dict] = {}
        for v in per_uuid.values():
            p = per_proj.setdefault(v["project"], {
                "sessions": 0, "cost": 0.0, "in_tok": 0, "out_tok": 0, "turns": 0
            })
            p["sessions"] += 1
            p["cost"] += v["cost"]
            p["in_tok"] += v["in_tok"]
            p["out_tok"] += v["out_tok"]
            p["turns"] += v["turns"]
        # Render
        self._append_terminal("[/usage] RKOJ session totals (from disk):\n\n")
        tot_cost = 0.0
        tot_in = 0
        tot_out = 0
        tot_sess = 0
        tot_turns = 0
        for proj in sorted(per_proj.keys(), key=lambda p: -per_proj[p]["cost"]):
            p = per_proj[proj]
            self._append_terminal(
                f"  {proj:<22s} "
                f"· {p['sessions']:>2d} sess "
                f"· {p['turns']:>3d} turns "
                f"· ${p['cost']:>7.4f} "
                f"· {p['in_tok']:>7,} in "
                f"· {p['out_tok']:>5,} out\n"
            )
            tot_cost += p["cost"]
            tot_in += p["in_tok"]
            tot_out += p["out_tok"]
            tot_sess += p["sessions"]
            tot_turns += p["turns"]
        self._append_terminal(
            f"  {'─' * 22} "
            f"{'─' * 9} "
            f"{'─' * 10} "
            f"{'─' * 10} "
            f"{'─' * 11} "
            f"{'─' * 8}\n"
            f"  {'TOTAL':<22s} "
            f"· {tot_sess:>2d} sess "
            f"· {tot_turns:>3d} turns "
            f"· ${tot_cost:>7.4f} "
            f"· {tot_in:>7,} in "
            f"· {tot_out:>5,} out\n"
        )
        # v1.6.31 — per-mode breakdown (which model is eating budget?)
        per_mode: dict[str, dict] = {}
        for v in per_uuid.values():
            m = per_mode.setdefault(v["mode"], {
                "sessions": 0, "cost": 0.0, "in_tok": 0, "out_tok": 0,
            })
            m["sessions"] += 1
            m["cost"] += v["cost"]
            m["in_tok"] += v["in_tok"]
            m["out_tok"] += v["out_tok"]
        if len(per_mode) > 1 or any(m for m in per_mode if m != "claude"):
            self._append_terminal("\n  By model:\n")
            for mode in sorted(per_mode.keys(), key=lambda m: -per_mode[m]["cost"]):
                m = per_mode[mode]
                self._append_terminal(
                    f"  {mode:<22s} "
                    f"· {m['sessions']:>2d} sess "
                    f"· {' ' * 8} "
                    f"· ${m['cost']:>7.4f} "
                    f"· {m['in_tok']:>7,} in "
                    f"· {m['out_tok']:>5,} out\n"
                )


# ── Agents view (folder-tab row + niri-scroll grid) ────────────────────
class NiriScrollGrid(QScrollArea):
    """Vertical infinite scroll container — grows as cards are added."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._host = QWidget()
        self._layout = QVBoxLayout(self._host)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(SPACINGS["md"])
        self._layout.addStretch(1)
        self.setWidget(self._host)

    @property
    def host(self) -> QWidget:
        return self._host

    @property
    def layout_(self) -> QVBoxLayout:
        return self._layout

    def clear_widgets(self) -> None:
        """Remove all cards + dividers (keeps trailing stretch)."""
        # Walk in reverse, skip the final stretch item
        i = self._layout.count() - 1
        while i >= 0:
            item = self._layout.itemAt(i)
            w = item.widget() if item else None
            if w is not None:
                w.setParent(None)
                w.deleteLater()
            i -= 1


class AgentsView(QWidget):
    """Folder-tab row + NiriScrollGrid + empty-state hint."""

    # v1.6.23 — emitted whenever the live card count changes. app.py
    # connects this to Sidebar.set_agents_count for the nav-row badge.
    cards_changed = pyqtSignal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._cards: dict[str, AgentCard] = {}
        self._project_filter: Optional[str] = None  # None = "All"
        self._folder_chips: dict[str, QPushButton] = {}
        # v1.6.43 — /find state. _last_find_query is reused by /find-next
        # (empty query on the signal advances idx instead of resetting).
        self._last_find_query: str = ""
        self._last_find_idx: int = -1
        self._build()
        self._rebuild_folder_chips()
        self._rebuild_grid()

    # Backward-compat alias
    @property
    def spawn_requested(self):  # pragma: no cover — kept for older wiring
        return None

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, SPACINGS["sm"], 20, SPACINGS["md"])
        root.setSpacing(SPACINGS["sm"])

        # Folder-tab strip
        self._chips_host = QWidget(self)
        self._chips_layout = QHBoxLayout(self._chips_host)
        self._chips_layout.setContentsMargins(0, 0, 0, 0)
        self._chips_layout.setSpacing(6)
        self._chips_layout.addStretch(1)
        root.addWidget(self._chips_host)

        # Niri-scroll grid
        self.grid = NiriScrollGrid(self)
        root.addWidget(self.grid, stretch=1)

        # Empty state — Panel-styled hero card centered when zero agents.
        # v1.6.9 — replaces the prior plain "No agents yet" label.
        self.empty_panel = QFrame(self)
        self.empty_panel.setObjectName("EmptyHero")
        self.empty_panel.setStyleSheet(
            f"QFrame#EmptyHero {{"
            f"  background: transparent;"
            f"}}"
        )
        empty_layout = QVBoxLayout(self.empty_panel)
        empty_layout.setContentsMargins(40, 40, 40, 40)
        empty_layout.setSpacing(14)
        empty_layout.addStretch(1)

        hero_title = QLabel("No agents yet")
        hero_title.setStyleSheet(
            f"color: {PURPLE_PRIMARY}; background: transparent; "
            f"font-size: 28px; font-weight: 800; letter-spacing: -0.5px;"
        )
        hero_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(hero_title)

        hero_sub = QLabel(
            "Click  + Create Agent  in the header to spawn EVE on any project,\n"
            "or open the Sessions tab in the sidebar to resume a saved session."
        )
        hero_sub.setStyleSheet(
            f"color: {MUTED_FG}; background: transparent; "
            f"font-size: 13px; line-height: 1.6;"
        )
        hero_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(hero_sub)

        # Three tips below the hero — small reminders of what this surface does.
        tips_row = QHBoxLayout()
        tips_row.setSpacing(20)
        tips_row.setContentsMargins(0, 16, 0, 0)
        for emoji, label in [
            ("●", "Per-agent session memory (claude --resume)"),
            ("●", "Folder tabs auto-group cards by project"),
            ("●", "/help inside any card lists slash commands"),
        ]:
            tip_box = QFrame()
            tip_box.setStyleSheet(
                f"QFrame {{ background-color: {ELEVATED}; border: 1px solid {BORDER}; "
                f"border-radius: 10px; padding: 14px; }}"
            )
            tb = QHBoxLayout(tip_box)
            tb.setContentsMargins(12, 10, 12, 10)
            tb.setSpacing(8)
            dot = QLabel(emoji)
            dot.setStyleSheet(
                f"color: {PURPLE_PRIMARY}; background: transparent; "
                f"font-size: 14px; font-weight: 700;"
            )
            tb.addWidget(dot)
            l = QLabel(label)
            l.setStyleSheet(
                f"color: {MUTED_FG}; background: transparent; font-size: 11px;"
            )
            l.setWordWrap(True)
            tb.addWidget(l, stretch=1)
            tips_row.addWidget(tip_box, stretch=1)
        empty_layout.addLayout(tips_row)

        # v1.6.15 — recent saved sessions list inside the empty state, so
        # operator gets one-click resume without the sidebar→Sessions
        # detour. Rebuilt every time the empty state is shown.
        self._recent_sessions_host = QFrame()
        self._recent_sessions_layout = QVBoxLayout(self._recent_sessions_host)
        self._recent_sessions_layout.setContentsMargins(0, 24, 0, 0)
        self._recent_sessions_layout.setSpacing(6)
        empty_layout.addWidget(self._recent_sessions_host)

        # v1.6.29 — MASTER-PLAN / OPERATOR-ACTION-QUEUE urgent rows
        # surfaced INSIDE RKOJ's empty state so operator sees Sanctum-wide
        # actionable items without leaving the chat.
        self._actions_host = QFrame()
        self._actions_layout = QVBoxLayout(self._actions_host)
        self._actions_layout.setContentsMargins(0, 16, 0, 0)
        self._actions_layout.setSpacing(6)
        empty_layout.addWidget(self._actions_host)

        # v1.6.35 — project-color legend so the v1.6.33 left-stripe
        # colors are self-documenting. Shown only if at least one
        # project from the curated palette is known.
        self._legend_host = self._build_color_legend()
        if self._legend_host is not None:
            empty_layout.addWidget(self._legend_host)

        empty_layout.addStretch(2)
        root.addWidget(self.empty_panel)
        self._rebuild_recent_sessions()
        self._rebuild_operator_actions()

        # Backward-compat alias — _rebuild_grid toggles visibility on this.
        self.empty_label = self.empty_panel

    # ── Recent saved sessions block (inside empty state) ──────────────
    def _rebuild_recent_sessions(self) -> None:
        """Scan _shared-memory/resume-points/EVE on */*.json, render the
        5 newest as one-click resume rows. No-op if the layout doesn't
        exist yet (init order safety)."""
        layout = getattr(self, "_recent_sessions_layout", None)
        if layout is None:
            return
        # Clear prior rows
        while layout.count():
            it = layout.takeAt(0)
            w = it.widget() if it else None
            if w is not None:
                w.setParent(None)
                w.deleteLater()
        sessions = self._scan_recent_sessions(limit=5)
        if not sessions:
            return
        title = QLabel("Recent saved sessions")
        title.setStyleSheet(
            f"color: {MUTED_FG}; background: transparent; "
            f"font-size: 11px; font-weight: 600; letter-spacing: 1px; "
            f"text-transform: uppercase; padding: 0 4px 6px 4px;"
        )
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        for s in sessions:
            row = self._build_recent_session_row(s)
            layout.addWidget(row)

    def _scan_recent_sessions(self, limit: int = 5) -> list[dict]:
        sessions: list[dict] = []
        rp_root = state.SHARED_MEMORY / "resume-points"
        if not rp_root.exists():
            return sessions
        try:
            for proj_dir in rp_root.iterdir():
                if not proj_dir.is_dir():
                    continue
                for fp in proj_dir.glob("*.json"):
                    try:
                        with open(fp, "r", encoding="utf-8") as fh:
                            data = json.load(fh)
                    except Exception:
                        continue
                    suid = data.get("session_uuid") or ""
                    if not suid:
                        continue
                    sessions.append({
                        "project_display": proj_dir.name.replace("EVE on ", ""),
                        "project_key": data.get("project_key", "sanctum"),
                        "agent_name": data.get("agent_name", ""),
                        "mode": data.get("mode", "claude"),
                        "session_uuid": suid,
                        "saved_at": data.get("saved_at", ""),
                        "turns": len(data.get("turns", [])),
                        "save_reason": data.get("save_reason", "manual"),
                    })
        except Exception:
            pass
        sessions.sort(key=lambda s: s.get("saved_at", ""), reverse=True)
        return sessions[:limit]

    def _build_recent_session_row(self, s: dict) -> QFrame:
        row = QFrame()
        row.setObjectName("RecentRow")
        row.setStyleSheet(
            f"QFrame#RecentRow {{ background-color: {ELEVATED}; "
            f"border: 1px solid {BORDER}; border-radius: 8px; }}"
            f"QFrame#RecentRow:hover {{ border-color: {PURPLE_PRIMARY}; }}"
        )
        hb = QHBoxLayout(row)
        hb.setContentsMargins(12, 8, 12, 8)
        hb.setSpacing(12)
        # Project + meta
        meta = QLabel(
            f"<span style='color:{PURPLE_PRIMARY};font-weight:700'>"
            f"{s['project_display']}</span>  "
            f"<span style='color:{MUTED_FG}'>· "
            f"{s['turns']} turn(s) · {s.get('save_reason', 'manual')}</span>"
        )
        meta.setStyleSheet("background: transparent; font-size: 12px;")
        meta.setTextFormat(Qt.TextFormat.RichText)
        hb.addWidget(meta)
        # Saved-at preview
        ts = (s.get("saved_at") or "")[:19].replace("T", " ")
        when = QLabel(ts or "(no timestamp)")
        when.setStyleSheet(
            f"color: {MUTED_FG}; background: transparent; "
            f"font-family: 'JetBrains Mono', monospace; font-size: 10px;"
        )
        hb.addWidget(when)
        hb.addStretch(1)
        # Resume button
        btn = QPushButton("Resume")
        btn.setObjectName("SendBtn")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(28)
        btn.clicked.connect(
            lambda _checked=False, sess=s: self._on_resume_recent(sess)
        )
        hb.addWidget(btn)
        return row

    def _on_resume_recent(self, sess: dict) -> None:
        self.spawn_agent(
            project_key=sess.get("project_key", "sanctum"),
            agent_name=sess.get("agent_name") or None,
            mode=sess.get("mode", "claude"),
            session_uuid=sess.get("session_uuid"),
        )

    # v1.6.35 — project-color legend in the empty state. Renders a single
    # wrapping row of small color-chip + project-display pairs so the
    # v1.6.33 left-stripe colors are self-documenting.
    def _build_color_legend(self) -> QFrame | None:
        # Show only the projects from the curated palette (deterministic
        # hash colors are too many to list).
        projects = state.load_projects()
        proj_by_key = {p.key: p for p in projects}
        rows: list[tuple[str, str]] = []
        for key, color in _PROJECT_COLORS.items():
            if key in proj_by_key:
                rows.append((proj_by_key[key].display, color))
        if not rows:
            return None
        host = QFrame()
        host.setStyleSheet("QFrame { background: transparent; }")
        outer = QVBoxLayout(host)
        outer.setContentsMargins(0, 20, 0, 0)
        outer.setSpacing(8)
        title = QLabel("Project color stripe legend")
        title.setStyleSheet(
            f"color: {MUTED_FG}; background: transparent; "
            f"font-size: 11px; font-weight: 600; letter-spacing: 1px; "
            f"text-transform: uppercase; padding: 0 4px;"
        )
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(title)
        # Flow of chips — use a single horizontal layout (wraps via Qt's
        # automatic line-break on narrow widths if we set wordWrap on
        # the labels; close enough for a row of ~13 chips at 240px each).
        flow = QHBoxLayout()
        flow.setContentsMargins(0, 0, 0, 0)
        flow.setSpacing(12)
        flow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        for display, color in rows:
            chip = QLabel(
                f"<span style='color:{color};font-weight:800;font-size:14px'>●</span> "
                f"<span style='color:{MUTED_FG};font-size:11px'>{display}</span>"
            )
            chip.setTextFormat(Qt.TextFormat.RichText)
            chip.setStyleSheet("background: transparent;")
            flow.addWidget(chip)
        flow_wrap = QFrame()
        flow_wrap.setLayout(flow)
        outer.addWidget(flow_wrap)
        return host

    # ── v1.6.29 operator-action urgent rows in empty state ─────────────
    def _rebuild_operator_actions(self) -> None:
        """Scan `_shared-memory/OPERATOR-ACTION-QUEUE.md` for unchecked
        Critical (🔴) and High (🟠) items + surface up to 3 in the empty
        state. Operator sees actionable Sanctum-wide items inside RKOJ."""
        layout = getattr(self, "_actions_layout", None)
        if layout is None:
            return
        # Clear prior rows
        while layout.count():
            it = layout.takeAt(0)
            w = it.widget() if it else None
            if w is not None:
                w.setParent(None)
                w.deleteLater()
        items = self._scan_urgent_actions(limit=3)
        if not items:
            return
        title = QLabel("Operator-action queue · urgent")
        title.setStyleSheet(
            f"color: {MUTED_FG}; background: transparent; "
            f"font-size: 11px; font-weight: 600; letter-spacing: 1px; "
            f"text-transform: uppercase; padding: 0 4px 6px 4px;"
        )
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        for it in items:
            layout.addWidget(self._build_action_row(it))

    def _scan_urgent_actions(self, limit: int = 3) -> list[dict]:
        """Parse OPERATOR-ACTION-QUEUE.md for unchecked items under
        🔴 Critical / 🟠 High sections. Returns up to `limit` items."""
        fp = state.SHARED_MEMORY / "OPERATOR-ACTION-QUEUE.md"
        if not fp.exists():
            return []
        try:
            text = fp.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return []
        lines = text.splitlines()
        items: list[dict] = []
        current_severity: str | None = None
        # Severity → emoji + display label
        sev_map = {
            "critical": ("🔴", "CRITICAL"),
            "high":     ("🟠", "HIGH"),
        }
        section_re = re.compile(r"^##+\s*(🔴|🟠)\s*(\w+)", re.IGNORECASE)
        item_re = re.compile(r"^-\s+\[\s\]\s+(?:(🔴|🟠)\s+)?\*\*([^*]+)\*\*(?:\s*[—-]\s*(.*))?")
        for line in lines:
            m_sec = section_re.match(line)
            if m_sec:
                sev_word = m_sec.group(2).lower()
                if sev_word.startswith("critical"):
                    current_severity = "critical"
                elif sev_word.startswith("high"):
                    current_severity = "high"
                else:
                    current_severity = None
                continue
            m_item = item_re.match(line)
            if m_item:
                # Inline severity (in the item itself) wins over section.
                inline_emoji = m_item.group(1)
                title = (m_item.group(2) or "").strip()
                detail = (m_item.group(3) or "").strip()
                severity = (
                    "critical" if inline_emoji == "🔴"
                    else "high" if inline_emoji == "🟠"
                    else current_severity
                )
                if severity not in sev_map:
                    continue
                items.append({
                    "severity": severity,
                    "emoji": sev_map[severity][0],
                    "title": title,
                    "detail": detail[:140],
                })
                if len(items) >= limit:
                    break
        return items

    def _build_action_row(self, item: dict) -> QFrame:
        row = QFrame()
        row.setObjectName("OperatorActionRow")
        # Severity-tinted border
        border_color = "#FF453A" if item["severity"] == "critical" else "#FF9F0A"
        row.setStyleSheet(
            f"QFrame#OperatorActionRow {{"
            f"  background-color: {ELEVATED};"
            f"  border: 1px solid {BORDER};"
            f"  border-left: 3px solid {border_color};"
            f"  border-radius: 8px;"
            f"}}"
        )
        hb = QHBoxLayout(row)
        hb.setContentsMargins(14, 9, 14, 9)
        hb.setSpacing(10)
        # Emoji
        emj = QLabel(item["emoji"])
        emj.setStyleSheet("background: transparent; font-size: 14px;")
        hb.addWidget(emj)
        # Title + detail (rich text in a single label)
        body = QLabel(
            f"<span style='color:white;font-weight:600'>{item['title']}</span> "
            f"<span style='color:{MUTED_FG}'>— {item['detail']}</span>"
        )
        body.setTextFormat(Qt.TextFormat.RichText)
        body.setStyleSheet("background: transparent; font-size: 12px;")
        body.setWordWrap(True)
        hb.addWidget(body, stretch=1)
        return row

    # ── Folder tab management ─────────────────────────────────────────
    def _active_project_keys(self) -> list[str]:
        keys = sorted({c.session.project_key for c in self._cards.values()})
        return keys

    def _rebuild_folder_chips(self) -> None:
        # Wipe and rebuild
        while self._chips_layout.count():
            item = self._chips_layout.takeAt(0)
            w = item.widget() if item else None
            if w is not None:
                w.setParent(None)
                w.deleteLater()
        self._folder_chips.clear()

        # "All" chip
        active_keys = self._active_project_keys()
        n_total = len(self._cards)
        all_btn = QPushButton(f"All  {n_total}")
        all_btn.setObjectName("FolderTab")
        all_btn.setProperty("active", self._project_filter is None)
        all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        all_btn.clicked.connect(lambda: self._set_filter(None))
        self._folder_chips["__all__"] = all_btn
        self._chips_layout.addWidget(all_btn)

        projects = {p.key: p for p in state.load_projects()}
        for k in active_keys:
            display = projects[k].display if k in projects else k
            n = sum(1 for c in self._cards.values() if c.session.project_key == k)
            chip = QPushButton(f"{display}  {n}")
            chip.setObjectName("FolderTab")
            chip.setProperty("active", self._project_filter == k)
            chip.setCursor(Qt.CursorShape.PointingHandCursor)
            chip.clicked.connect(lambda _checked=False, key=k: self._set_filter(key))
            self._folder_chips[k] = chip
            self._chips_layout.addWidget(chip)

        self._chips_layout.addStretch(1)

    def _set_filter(self, key: Optional[str]) -> None:
        self._project_filter = key
        for k, btn in self._folder_chips.items():
            is_active = (k == "__all__" and key is None) or (k == key)
            btn.setProperty("active", is_active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self._rebuild_grid()

    # ── Grid layout (cards sorted by project + divider between groups) ──
    def _rebuild_grid(self) -> None:
        self.grid.clear_widgets()
        # collect visible cards
        cards = list(self._cards.values())
        if self._project_filter is not None:
            cards = [c for c in cards if c.session.project_key == self._project_filter]
        # v1.6.28 — pinned cards bubble to the top, then by project_key
        # so pinned-from-same-project still group together.
        cards.sort(key=lambda c: (
            not c.session.pinned,
            c.session.project_key,
            c.session.created_at,
        ))

        last_key: Optional[str] = None
        # insertWidget at count()-1 inserts before the trailing stretch
        for c in cards:
            if last_key is not None and c.session.project_key != last_key:
                div = QFrame(self.grid.host)
                div.setObjectName("ProjectDivider")
                div.setFixedHeight(1)
                self.grid.layout_.insertWidget(self.grid.layout_.count() - 1, div)
            self.grid.layout_.insertWidget(self.grid.layout_.count() - 1, c)
            c.setVisible(True)
            last_key = c.session.project_key

        # Empty state visibility
        empty_now = (len(self._cards) == 0)
        self.empty_label.setVisible(empty_now)
        self.grid.setVisible(not empty_now)
        # v1.6.15 — refresh recent-sessions list whenever empty state shows
        # (e.g., after the last card closes), so it always reflects disk.
        if empty_now:
            try:
                self._rebuild_recent_sessions()
            except Exception:
                pass
            # v1.6.29 — also refresh operator-action urgent rows
            try:
                self._rebuild_operator_actions()
            except Exception:
                pass

    # ── Public API ────────────────────────────────────────────────────
    def spawn_agent(self, project_key: str = "sanctum",
                    agent_name: str | None = None,
                    mode: str = "claude",
                    session_uuid: str | None = None) -> str:
        """Add a new card and return its pane_id.

        Phase-1 memory bootstrap: pre-creates heartbeat / inbox / PROGRESS /
        resume-points entries on disk so the spawned agent is discoverable
        to siblings within seconds.

        v1.6.8 — `session_uuid` arg: if provided, the card starts in
        resume mode (next operator message uses `claude --resume <uuid>`
        instead of creating a fresh session). Used by the saved-sessions
        picker so resumed sessions appear inline in the Agents tab body
        — operator wants everything in the main window, not floating.
        """
        projects = {p.key: p for p in state.load_projects()}
        proj = projects.get(project_key)
        display = proj.display if proj else project_key
        sess = AgentSession(
            pane_id=uuid.uuid4().hex[:12],
            project_key=project_key,
            project_display=display,
            agent_name=agent_name or display,
            mode=mode,
            created_at=datetime.now(timezone.utc).isoformat(),
            session_uuid=session_uuid or "",
        )
        _bootstrap_agent_memory(sess)
        card = AgentCard(sess, parent=self.grid.host)
        if session_uuid:
            # Skip first-turn persona — claude already has the session.
            card._first_turn = False
            # v1.6.31 — restore pin state + cumulative cost from the
            # latest saved resume-point for this session_uuid so the
            # card looks like the same one you closed.
            self._restore_card_state_from_disk(card, session_uuid)
            card._append_terminal(
                f"  ▸ RESUMED session (session_uuid={session_uuid[:12]}…)\n"
                f"    Next message uses `claude -r {session_uuid} -p ...`\n"
                f"    Claude has the full conversation history server-side.\n"
                f"\n"
            )
        card.closed.connect(self._remove_card)
        # v1.6.28 — re-sort grid when operator pins/unpins a card so
        # pinned cards float to top
        card.pin_changed.connect(lambda *_: self._rebuild_grid())
        # v1.6.30 — route /broadcast to AgentsView fan-out helper
        card.broadcast_requested.connect(self.broadcast)
        # v1.6.36 — route /minimize-all + /expand-all to grid-wide toggles
        card.minimize_all_requested.connect(self.collapse_all)
        card.expand_all_requested.connect(self.expand_all)
        # v1.6.41 — /clone fans into spawn_agent for a fresh sibling card.
        card.clone_requested.connect(
            lambda pk, m: self.spawn_agent(project_key=pk, mode=m)
        )
        # v1.6.42 — /find fans to AgentsView focus helper.
        card.find_requested.connect(self._focus_find)
        # v1.6.51 — /tags fans to AgentsView fleet-wide census.
        card.tags_census_requested.connect(self._print_tags_census)
        # v1.6.55 — /export-all fans to AgentsView bundle writer.
        card.export_all_requested.connect(self._export_all_transcripts)
        # v1.6.60 — /summarize-all fans the canned TL;DR ask to every card.
        card.summarize_all_requested.connect(self._summarize_all)
        # v1.6.66 — /fleet table fan-out.
        card.fleet_table_requested.connect(self._print_fleet_table)
        # v1.6.68 — /uptime-all fan-out.
        card.uptime_all_requested.connect(self._print_uptime_all)
        self._cards[sess.pane_id] = card
        self._rebuild_folder_chips()
        self._rebuild_grid()
        # v1.6.13 — auto-focus the input so operator can immediately type
        # without clicking. Use a 0ms timer so focus lands after Qt has
        # finished laying out the new card.
        try:
            QTimer.singleShot(0, card.input.setFocus)
        except Exception:
            pass
        # v1.6.23 — emit the new card count so the sidebar Agents-row
        # badge stays in sync without polling.
        self.cards_changed.emit(len(self._cards))
        return sess.pane_id

    def _remove_card(self, pane_id: str) -> None:
        card = self._cards.pop(pane_id, None)
        if card:
            card.setParent(None)
            card.deleteLater()
        # If the active filter no longer has any cards, fall back to All
        if self._project_filter is not None and not any(
            c.session.project_key == self._project_filter for c in self._cards.values()
        ):
            self._project_filter = None
        self._rebuild_folder_chips()
        self._rebuild_grid()
        # v1.6.23 — emit updated count after removal
        self.cards_changed.emit(len(self._cards))

    def shutdown_all(self) -> None:
        for card in list(self._cards.values()):
            card.shutdown()

    # v1.6.36 — bulk toggles. Fired from any card's /minimize-all or
    # /expand-all slash command via the corresponding signal.
    def collapse_all(self) -> int:
        n = 0
        for c in self._cards.values():
            if not c._collapsed:
                c._toggle_collapsed()
                n += 1
        return n

    def expand_all(self) -> int:
        n = 0
        for c in self._cards.values():
            if c._collapsed:
                c._toggle_collapsed()
                n += 1
        return n

    # v1.6.42 — /find handler. Caller emits (invoker_pane_id, query);
    # we scroll grid to a matching card + echo feedback in the caller's
    # terminal so operator stays in their typing card.
    # v1.6.43 — empty query reuses _last_find_query and advances idx
    # (so /find-next can cycle). Bright flash on the focused match.
    def _focus_find(self, invoker_id: str, query: str) -> None:
        invoker = self._cards.get(invoker_id)
        if invoker is None:
            return
        is_advance = (query.strip() == "")
        if is_advance:
            q = self._last_find_query
            if not q:
                invoker._append_terminal(
                    "[/find-next] no previous /find — run `/find <text>` first\n"
                )
                return
        else:
            q = query.strip().lower()
            self._last_find_query = q
            self._last_find_idx = -1
        matches: list[AgentCard] = []
        for c in self._cards.values():
            hay = " ".join((
                c.session.project_display or "",
                c.session.agent_name or "",
                c.session.project_key or "",
                c.session.pane_id or "",
                " ".join(c.session.tags or ()),  # v1.6.45 — tags included
            )).lower()
            if q in hay:
                matches.append(c)
        if not matches:
            invoker._append_terminal(
                f"[/find] no card matches '{q}' (searched project / agent / id)\n"
            )
            return
        if is_advance:
            self._last_find_idx = (self._last_find_idx + 1) % len(matches)
        else:
            self._last_find_idx = 0
        match = matches[self._last_find_idx]
        if match._collapsed:
            match._toggle_collapsed()
        self.grid.ensureWidgetVisible(match)
        match._flash_for_find()
        label = "/find-next" if is_advance else "/find"
        invoker._append_terminal(
            f"[{label}] match {self._last_find_idx + 1}/{len(matches)} → "
            f"{match.session.project_display} :: {match.session.agent_name} "
            f"(pane_id={match.session.pane_id})\n"
        )

    # v1.6.60 — fleet-wide /summarize. Stages the canned TL;DR ask into
    # every card with prior turns + fires _on_send via singleShot so each
    # card's spinner/streaming/cost path runs uniformly (same pattern as
    # /broadcast). Skips cards mid-turn to avoid clobbering an in-flight
    # EVE response.
    def _summarize_all(self, invoker_id: str) -> None:
        invoker = self._cards.get(invoker_id)
        if invoker is None:
            return
        fanned = 0
        skipped_empty = 0
        skipped_busy = 0
        for c in self._cards.values():
            if not any(t.get("user") for t in c.session.turns):
                skipped_empty += 1
                continue
            if c._proc is not None and c._proc.state() != QProcess.ProcessState.NotRunning:
                skipped_busy += 1
                continue
            c.input.setPlainText(_SUMMARIZE_PROMPT)
            QTimer.singleShot(0, c._on_send)
            fanned += 1
        invoker._append_terminal(
            f"[/summarize-all] fanned to {fanned} card(s)\n"
        )
        if skipped_empty:
            invoker._append_terminal(
                f"  (skipped {skipped_empty} empty card(s))\n"
            )
        if skipped_busy:
            invoker._append_terminal(
                f"  (skipped {skipped_busy} card(s) mid-turn)\n"
            )

    # v1.6.68 — fleet uptime aggregate. Sums lifetime + turns + cost
    # across every live card. Operator gets workstation-wide totals.
    def _print_uptime_all(self, invoker_id: str) -> None:
        invoker = self._cards.get(invoker_id)
        if invoker is None:
            return
        if not self._cards:
            invoker._append_terminal("[/uptime-all] no cards in the grid\n")
            return
        now = time.monotonic()
        total_lifetime = 0.0
        total_turns = 0
        total_cost = 0.0
        oldest_card = None
        oldest_age = 0.0
        for c in self._cards.values():
            up = now - c._spawn_ts
            total_lifetime += up
            total_turns += len([t for t in c.session.turns if t.get("user")])
            total_cost += c._total_cost_usd
            if up > oldest_age:
                oldest_age = up
                oldest_card = c
        avg_lifetime = total_lifetime / len(self._cards)
        oldest_name = (oldest_card.session.agent_name if oldest_card else "?")
        invoker._append_terminal(
            f"[/uptime-all] fleet aggregate ({len(self._cards)} card(s)):\n"
            f"  total lifetime : {AgentCard._fmt_duration(total_lifetime)}\n"
            f"  avg per card   : {AgentCard._fmt_duration(avg_lifetime)}\n"
            f"  oldest card    : {oldest_name} ({AgentCard._fmt_duration(oldest_age)})\n"
            f"  total turns    : {total_turns}\n"
            f"  total cost     : ${total_cost:.4f}\n"
        )

    # v1.6.66 — per-card table. Columns: project, mode, turns, cost,
    # status, tags. Aligned with `max(len(col))` per-column widths so
    # wide names don't break the layout. Echoes to invoker.
    # v1.6.67 — accepts optional sort_key: project, agent, mode, turns,
    # cost, status. Default sorts pinned-first, then project, then agent.
    def _print_fleet_table(self, invoker_id: str, sort_key: str = "") -> None:
        invoker = self._cards.get(invoker_id)
        if invoker is None:
            return
        if not self._cards:
            invoker._append_terminal("[/fleet] no cards in the grid\n")
            return
        # Build row tuples plus a parallel list of typed sort tuples so
        # numeric columns sort numerically.
        now = time.monotonic()
        rows: list[tuple[str, str, str, str, str, str, str, str]] = []
        numeric_data: list[tuple[int, float, float]] = []  # (turns, cost, uptime_sec)
        cards_in_order = list(self._cards.values())
        for c in cards_in_order:
            sess = c.session
            n_turns = len([t for t in sess.turns if t.get("user")])
            cost = c._total_cost_usd
            pin = "★" if sess.pinned else " "
            up_sec = now - c._spawn_ts
            rows.append((
                pin,
                sess.project_display or sess.project_key or "?",
                sess.agent_name or sess.pane_id[:8],
                sess.mode or "?",
                str(n_turns),
                f"${cost:.4f}",
                sess.status or "?",
                AgentCard._fmt_duration(up_sec),  # v1.6.68 uptime col
            ))
            numeric_data.append((n_turns, cost, up_sec))
        paired = list(zip(rows, numeric_data))
        valid_keys = {"", "project", "agent", "mode", "turns", "cost", "status", "uptime"}
        if sort_key not in valid_keys:
            invoker._append_terminal(
                f"[/fleet] unknown sort '{sort_key}' — using default. "
                f"Valid: {', '.join(sorted(k for k in valid_keys if k))}\n"
            )
            sort_key = ""
        if sort_key == "":
            paired.sort(key=lambda p: (p[0][0] != "★", p[0][1].lower(), p[0][2].lower()))
        elif sort_key == "project":
            paired.sort(key=lambda p: p[0][1].lower())
        elif sort_key == "agent":
            paired.sort(key=lambda p: p[0][2].lower())
        elif sort_key == "mode":
            paired.sort(key=lambda p: p[0][3].lower())
        elif sort_key == "turns":
            paired.sort(key=lambda p: p[1][0], reverse=True)
        elif sort_key == "cost":
            paired.sort(key=lambda p: p[1][1], reverse=True)
        elif sort_key == "status":
            paired.sort(key=lambda p: p[0][6].lower())
        elif sort_key == "uptime":
            paired.sort(key=lambda p: p[1][2], reverse=True)
        rows = [p[0] for p in paired]
        # Pre-pend a header row + ruler. 8 cols incl. UPTIME (v1.6.68).
        header = ("", "PROJECT", "AGENT", "MODE", "TURNS", "COST", "STATUS", "UPTIME")
        all_rows = [header] + rows
        widths = [max(len(r[i]) for r in all_rows) for i in range(8)]
        sort_note = f" sorted by {sort_key}" if sort_key else ""
        invoker._append_terminal(
            f"[/fleet] {len(rows)} card(s){sort_note}:\n"
        )
        for i, r in enumerate(all_rows):
            line = "  " + "  ".join(r[k].ljust(widths[k]) for k in range(8))
            invoker._append_terminal(line.rstrip() + "\n")
            if i == 0:
                ruler = "  " + "  ".join("-" * widths[k] for k in range(8))
                invoker._append_terminal(ruler + "\n")
        # Optional tags footer (full width — tags often span multi-line)
        any_tags = any(c.session.tags for c in self._cards.values())
        if any_tags:
            invoker._append_terminal("  ─── tags ───\n")
            for c in self._cards.values():
                if c.session.tags:
                    label = c.session.agent_name or c.session.pane_id[:8]
                    invoker._append_terminal(
                        f"  {label}: " + ", ".join(c.session.tags) + "\n"
                    )

    # v1.6.55 — fleet-wide /export. Writes every card's transcript into
    # a single timestamped bundle dir + echoes summary to invoker. Skips
    # cards with no user turns (empty-state guard).
    def _export_all_transcripts(self, invoker_id: str) -> None:
        invoker = self._cards.get(invoker_id)
        if invoker is None:
            return
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
        bundle_dir = state.SHARED_MEMORY / "rkoj-qt" / "exports" / f"{ts}-bundle"
        bundle_dir.mkdir(parents=True, exist_ok=True)
        written: list[str] = []
        skipped = 0
        failed: list[str] = []
        for c in self._cards.values():
            if not any(t.get("user") for t in c.session.turns):
                skipped += 1
                continue
            try:
                fp = c._export_to_markdown(target_dir=bundle_dir)
                written.append(fp.name)
            except Exception as exc:
                failed.append(f"{c.session.agent_name}: {exc}")
        invoker._append_terminal(
            f"[/export-all] wrote {len(written)} transcript(s) to:\n"
            f"  {bundle_dir}\n"
        )
        for name in written:
            invoker._append_terminal(f"  - {name}\n")
        if skipped:
            invoker._append_terminal(f"  (skipped {skipped} card(s) with no turns)\n")
        for err in failed:
            invoker._append_terminal(f"  [FAILED] {err}\n")

    # v1.6.51 — fleet-wide tag census. Echoes back into the invoker's
    # terminal so operator stays in their typing context.
    def _print_tags_census(self, invoker_id: str) -> None:
        invoker = self._cards.get(invoker_id)
        if invoker is None:
            return
        # tag -> list of agent_name|project_display references
        from collections import defaultdict
        census: dict[str, list[str]] = defaultdict(list)
        total_cards = 0
        for c in self._cards.values():
            total_cards += 1
            for t in (c.session.tags or ()):
                label = c.session.agent_name or c.session.pane_id[:8]
                census[t].append(f"{c.session.project_display}:{label}")
        if not census:
            invoker._append_terminal(
                f"[/tags] no tags across {total_cards} card(s) — try `/tag <label>` first\n"
            )
            return
        invoker._append_terminal(
            f"[/tags] {len(census)} tag(s) across {total_cards} card(s):\n"
        )
        # Sort tags alphabetically; longest-first within (operator scans top-down)
        for tag in sorted(census.keys()):
            members = census[tag]
            invoker._append_terminal(
                f"  '{tag}' x{len(members):2d} :: " + ", ".join(members) + "\n"
            )

    # v1.6.31 — restore card state (pin + cumulative cost) from the most
    # recent saved resume-point matching session_uuid. Called from
    # spawn_agent when session_uuid is provided.
    def _restore_card_state_from_disk(self, card: AgentCard,
                                       session_uuid: str) -> None:
        rp_root = state.SHARED_MEMORY / "resume-points"
        if not rp_root.exists():
            return
        latest_ts = ""
        latest_data: dict | None = None
        try:
            for proj_dir in rp_root.iterdir():
                if not proj_dir.is_dir():
                    continue
                for fp in proj_dir.glob("*.json"):
                    try:
                        with open(fp, "r", encoding="utf-8") as fh:
                            d = json.load(fh)
                    except Exception:
                        continue
                    if d.get("session_uuid") != session_uuid:
                        continue
                    ts = d.get("saved_at", "")
                    if ts > latest_ts:
                        latest_ts = ts
                        latest_data = d
        except Exception:
            return
        if latest_data is None:
            return
        # Restore pin
        if bool(latest_data.get("pinned", False)):
            try:
                card._toggle_pin()  # flips False → True + updates visual
            except Exception:
                pass
        # Restore cumulative cost telemetry so the cost pill shows the
        # carried total instead of $0.0000 from a fresh resume.
        try:
            card._total_cost_usd = float(latest_data.get("total_cost_usd", 0))
            card._total_in_tokens = int(latest_data.get("total_in_tokens", 0))
            card._total_out_tokens = int(latest_data.get("total_out_tokens", 0))
            card._cost_pill.setText(f"${card._total_cost_usd:.4f}")
        except Exception:
            pass
        # v1.6.45 — restore tag chips
        try:
            tags = latest_data.get("tags") or []
            if isinstance(tags, list):
                card.session.tags = [str(t)[:24] for t in tags if t]
                card._rebuild_tags()
        except Exception:
            pass
        # v1.6.47 — restore last /grep pattern. Scrollback is fresh on
        # resume, so we just seed the field — first new reply re-renders
        # and operator can hit F3 (or /grep <same>) to re-highlight.
        try:
            gp = latest_data.get("grep_pattern") or ""
            if gp:
                card._grep_pattern = gp
                card._append_terminal(
                    f"  ▸ /grep pattern restored from last session: '{gp}'\n"
                    f"    Type `/grep {gp}` (or just /grep) to re-apply highlights\n"
                )
        except Exception:
            pass
        # v1.6.59 — restore the half-typed input draft. The textChanged
        # signal will auto-update session.input_draft as soon as operator
        # types, so the restore is self-maintaining from then on.
        try:
            draft = latest_data.get("input_draft") or ""
            if draft:
                card.session.input_draft = draft
                card.input.setPlainText(draft)
                preview = draft.replace("\n", " ")[:60]
                card._append_terminal(
                    f"  ▸ input draft restored ({len(draft)} chars): "
                    f"'{preview}{'…' if len(draft) > 60 else ''}'\n"
                )
        except Exception:
            pass

    # v1.6.30 — broadcast a message to every live card. Called when any
    # card emits `broadcast_requested`. We stage the message into each
    # card's input + fire `_on_send` on the next event-loop tick so
    # the existing spinner+streaming+cost paths run uniformly per card.
    # v1.6.32 — supports the `__PING_PROJECT__<key>__:<msg>` sentinel
    # from `/ping <project>` to filter to a project.
    def broadcast(self, msg: str) -> int:
        project_filter: str | None = None
        if msg.startswith("__PING_PROJECT__"):
            try:
                _, rest = msg.split("__PING_PROJECT__", 1)
                key, body = rest.split("__:", 1)
                project_filter = key.strip().lower() or None
                msg = body
            except ValueError:
                project_filter = None
        n = 0
        for card in self._cards.values():
            try:
                if project_filter is not None:
                    pk = (card.session.project_key or "").lower()
                    pd = (card.session.project_display or "").lower()
                    if project_filter not in (pk, pd):
                        continue
                # Skip cards mid-turn — don't queue a clobber.
                if (card._proc is not None
                        and card._proc.state() != QProcess.ProcessState.NotRunning):
                    continue
                card.input.setPlainText(msg)
                cur = card.input.textCursor()
                cur.movePosition(QTextCursor.MoveOperation.End)
                card.input.setTextCursor(cur)
                QTimer.singleShot(0, card._on_send)
                n += 1
            except Exception:
                continue
        return n


# Backward-compat alias — older modules import AgentsTab.
AgentsTab = AgentsView
ClaudeRunner = AgentCard
