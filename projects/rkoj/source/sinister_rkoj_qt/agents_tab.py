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
from PyQt6.QtGui import QColor, QFont, QKeyEvent, QKeySequence, QShortcut, QTextCursor
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


class _MultiLineInput(QPlainTextEdit):
    """jcode-style input: Enter sends, Shift+Enter inserts newline.

    Auto-resizes vertically up to a 5-line cap so a long prompt doesn't
    blow up the card. Emits `submit` (pyqtSignal[str]) when the operator
    presses Enter without Shift held.
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

    def _fit_height(self, *_args) -> None:
        h = int(self.document().size().height()) + 12
        h = max(self._min_h, min(self._max_h, h))
        if h != self.height():
            self.setFixedHeight(h)
            self.setVerticalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAsNeeded if h >= self._max_h
                else Qt.ScrollBarPolicy.ScrollBarAlwaysOff
            )

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                # Shift+Enter → newline (default QPlainTextEdit behavior)
                super().keyPressEvent(event)
                return
            # Plain Enter (and Ctrl+Enter) → submit
            text = self.toPlainText().rstrip()
            self.submit.emit(text)
            return
        super().keyPressEvent(event)

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
    """
    qenv = QProcessEnvironment.systemEnvironment()
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
    return qenv


# ── Agent card ──────────────────────────────────────────────────────────
class AgentCard(QFrame):
    """Single agent card with embedded terminal + input line + QProcess."""

    closed = pyqtSignal(str)  # pane_id
    status_changed = pyqtSignal(str, str)  # pane_id, new_status

    # Braille spinner for the "thinking" indicator (jcode-style).
    _SPINNER = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

    def __init__(self, session: AgentSession, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.session = session
        self.setObjectName("AgentCard")
        self.setProperty("needs_input", False)
        self.setMinimumHeight(280)
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
        self._build()
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
        self.status_dot = QLabel()
        self.status_dot.setObjectName("StatusDot")
        self.status_dot.setProperty("state", "idle")
        self.status_dot.setFixedSize(12, 12)
        self.status_dot.setStyleSheet(
            f"background-color: {DIM}; border-radius: 6px;"
        )

        project_label = QLabel(self.session.project_display.upper())
        project_label.setObjectName("AgentProject")

        title = QLabel(eve_label(self.session.agent_name, ""))
        title.setObjectName("AgentTitle")

        mode_pill = QLabel(self.session.mode)
        mode_pill.setObjectName("ModePill")

        # v1.6.9 — turn counter pill (updates after each /send completes)
        self._turn_pill = QLabel("0 turns")
        self._turn_pill.setObjectName("ModePill")
        self._turn_pill.setStyleSheet(
            f"color: {MUTED_FG}; background-color: transparent; "
            f"border: 1px solid {BORDER}; border-radius: 10px; "
            f"padding: 2px 9px; font-size: 10px; font-weight: 600;"
        )

        # v1.6.12 — cumulative cost pill (updates after each turn's result event)
        self._cost_pill = QLabel("$0.0000")
        self._cost_pill.setObjectName("ModePill")
        self._cost_pill.setStyleSheet(
            f"color: {PURPLE_PRIMARY}; background-color: transparent; "
            f"border: 1px solid {BORDER}; border-radius: 10px; "
            f"padding: 2px 9px; font-size: 10px; font-weight: 600; "
            f"font-family: 'JetBrains Mono', monospace;"
        )
        self._cost_pill.setToolTip(
            "Cumulative claude API cost across all turns in this card. "
            "Type /cost in the chat for the full breakdown."
        )

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
        hdr.addStretch(1)
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
        self.terminal.moveCursor(QTextCursor.MoveOperation.End)
        self.terminal.insertPlainText(text)
        if was_at_bottom:
            self.terminal.moveCursor(QTextCursor.MoveOperation.End)
            if sb is not None:
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

    def _tick_spinner(self) -> None:
        import time as _t
        ch = self._SPINNER[self._spinner_idx % len(self._SPINNER)]
        self._spinner_idx += 1
        elapsed = _t.time() - self._thinking_start_ts
        self._thinking_label.setText(
            f"{ch}  EVE is thinking…  ({elapsed:.1f}s)"
        )

    # ── Slash-command intercept ───────────────────────────────────────
    def _maybe_intercept(self, text: str) -> bool:
        cmd = text.strip()
        if not cmd.startswith("/"):
            return False
        head = cmd.split(None, 1)[0].lower()
        if head == "/help":
            self._append_terminal(
                "[/help]  Slash commands (RKOJ-side intercepts):\n"
                "  /help        show this list\n"
                "  /clear       clear terminal scrollback\n"
                "  /save        write resume-point JSON (incl. session uuid) to disk\n"
                "  /history     show all prior turns (count + truncated previews)\n"
                "  /retry       resend the most recent operator message\n"
                "  /persona     print identity (display, slug, session uuid, paths)\n"
                "  /session     print just the session uuid (for `claude -r <uuid>` later)\n"
                "  /skills      list available Sanctum skills (~/.sinister/skills + repo)\n"
                "  /mcp         list MCP servers configured in ~/.claude/.mcp.json\n"
                "  /vault       Sinister Vault status (disk usage + daemon port :5078)\n"
                "  /memory      forge-memory-bridge BM25 recall (if available)\n"
                "  /open        print path commands to open agent PROGRESS / resume-points\n"
                "  /needs       toggle awaiting-input glow (visual test)\n"
                "\n"
                "  Any other text is forwarded to claude as a turn in this session.\n"
                "  v1.6.3 uses real session continuity (claude --session-id then\n"
                "  --resume <uuid>) — claude tracks the conversation server-side,\n"
                "  so each turn only sends your latest message (no history replay).\n"
            )
            return True
        if head == "/skills":
            from pathlib import Path
            roots = [
                Path(r"D:\Sinister Sanctum\skills"),
                Path.home() / ".sinister" / "skills",
                Path.home() / ".claude" / "skills",
            ]
            found = []
            for r in roots:
                if not r.exists():
                    continue
                for p in r.glob("*.md"):
                    found.append((str(r), p.name))
                for p in r.glob("*/SKILL.md"):
                    found.append((str(r), p.parent.name + "/SKILL.md"))
            if not found:
                self._append_terminal(
                    "[/skills] no .md skills found in:\n"
                    + "\n".join(f"  - {r}" for r in roots) + "\n"
                )
            else:
                self._append_terminal(f"[/skills] {len(found)} skill(s):\n")
                for root, name in found[:30]:
                    self._append_terminal(f"  {root}\\{name}\n")
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
        if head == "/clear":
            self.terminal.clear()
            self._append_terminal("[cleared]\n")
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
        if head == "/history":
            n = len(self.session.turns)
            self._append_terminal(f"[/history] {n} turn(s):\n")
            for i, t in enumerate(self.session.turns[-10:], start=max(1, n - 9)):
                u = (t.get("user") or "").strip().replace("\n", " ")[:60]
                a = (t.get("assistant") or "").strip().replace("\n", " ")[:60]
                self._append_terminal(f"  {i:2d}. >> {u}\n      << {a}\n")
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
        if head == "/save":
            # Write to the canonical resume-point dir (per agent display name).
            try:
                if self.session.resume_dir:
                    resume_dir = Path(self.session.resume_dir)
                else:
                    resume_dir = state.SHARED_MEMORY / "rkoj-qt" / "resume-points"
                resume_dir.mkdir(parents=True, exist_ok=True)
                ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
                fp = resume_dir / f"{ts}.json"
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
                    "resume_cmd": (
                        f"claude --dangerously-skip-permissions "
                        f"-r {self.session.session_uuid} -p 'your message'"
                    ),
                }
                with open(fp, "w", encoding="utf-8") as fh:
                    json.dump(payload, fh, indent=2)
                self._append_terminal(f"[/save] wrote {fp}\n")
            except Exception as exc:
                self._append_terminal(f"[/save] failed: {exc}\n")
            return True
        if head == "/needs":
            new_state = "awaiting-input" if self.session.status != "awaiting-input" else "online"
            self._set_status(new_state)
            self._append_terminal(f"[/needs] status -> {new_state}\n")
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

        self._append_terminal(f"\n>> {text}\n")
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
        if self.session.mode == "claude-haiku":
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
            self._append_terminal("<< ")
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
                            self._append_terminal("<< ")
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
                            f"{ch}  💭 {preview}"
                        )
            elif et == "content_block_start":
                cb = e.get("content_block", {})
                if cb.get("type") == "tool_use":
                    tool = cb.get("name", "")
                    self._stream_tools_run.append(tool)
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
                        self._thinking_label.setText(f"{ch}  💭 thinking…")
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
        elif t == "system":
            # System events (init / status / hook_started / hook_response).
            # We don't render these to keep the terminal quiet — too verbose.
            return

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
        if not self._reply_started:
            # Process exited with no stdout — show a meaningful error.
            self._stop_thinking()
            self._append_terminal(
                f"<< [no reply] claude exited with code {exit_code} and no output. "
                f"Try /retry, or verify `claude --version` in a terminal.\n"
            )
        else:
            self._append_terminal("\n")
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
        try:
            self._hb_timer.stop()
            _refresh_heartbeat(self.session, "ended")
        except Exception:
            pass
        self.closed.emit(self.session.pane_id)

    def shutdown(self) -> None:
        """Called from main window closeEvent — kill child cleanly."""
        if self._proc is not None and self._proc.state() != QProcess.ProcessState.NotRunning:
            self._proc.kill()
            self._proc.waitForFinished(1500)
        try:
            self._hb_timer.stop()
            _refresh_heartbeat(self.session, "ended")
        except Exception:
            pass


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

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._cards: dict[str, AgentCard] = {}
        self._project_filter: Optional[str] = None  # None = "All"
        self._folder_chips: dict[str, QPushButton] = {}
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

        empty_layout.addStretch(2)
        root.addWidget(self.empty_panel)
        self._rebuild_recent_sessions()

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
        cards.sort(key=lambda c: (c.session.project_key, c.session.created_at))

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
            card._append_terminal(
                f"  ▸ RESUMED session (session_uuid={session_uuid[:12]}…)\n"
                f"    Next message uses `claude -r {session_uuid} -p ...`\n"
                f"    Claude has the full conversation history server-side.\n"
                f"\n"
            )
        card.closed.connect(self._remove_card)
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

    def shutdown_all(self) -> None:
        for card in list(self._cards.values()):
            card.shutdown()


# Backward-compat alias — older modules import AgentsTab.
AgentsTab = AgentsView
ClaudeRunner = AgentCard
