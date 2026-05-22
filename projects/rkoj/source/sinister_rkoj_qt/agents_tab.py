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
import shutil
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QProcess, QProcessEnvironment, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QTextCursor
from PyQt6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QLineEdit,
    QPlainTextEdit, QPushButton, QScrollArea, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget,
)

from . import state
from .persona import build_opening_prompt, eve_label
from .theme import (
    AMBER_ACCENT, DIM, GREEN_ACCENT, PURPLE_ACCENT, SPACINGS, nav_icon,
)

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
        hdr.addStretch(1)
        hdr.addWidget(close_btn)
        root.addLayout(hdr)

        # Terminal
        self.terminal = QPlainTextEdit()
        self.terminal.setObjectName("Terminal")
        self.terminal.setReadOnly(True)
        font = QFont("Cascadia Mono", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.terminal.setFont(font)
        self.terminal.setMinimumHeight(170)
        root.addWidget(self.terminal, stretch=1)

        # Input row
        input_row = QHBoxLayout()
        input_row.setSpacing(SPACINGS["sm"])
        self.input = QLineEdit()
        self.input.setObjectName("TerminalInput")
        self.input.setPlaceholderText(
            f"Talk to {eve_label(self.session.agent_name, self.session.project_key)} — Enter to send, /help"
        )
        self.input.returnPressed.connect(self._on_send)
        self.send_btn = QPushButton("Send")
        self.send_btn.setObjectName("SendBtn")
        self.send_btn.clicked.connect(self._on_send)
        input_row.addWidget(self.input, stretch=1)
        input_row.addWidget(self.send_btn)
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
        self.terminal.moveCursor(QTextCursor.MoveOperation.End)
        self.terminal.insertPlainText(text)
        self.terminal.moveCursor(QTextCursor.MoveOperation.End)

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
                "  /needs       toggle awaiting-input glow (visual test)\n"
                "\n"
                "  Any other text is forwarded to claude as a turn in this session.\n"
                "  v1.6.3 uses real session continuity (claude --session-id then\n"
                "  --resume <uuid>) — claude tracks the conversation server-side,\n"
                "  so each turn only sends your latest message (no history replay).\n"
            )
            return True
        if head == "/clear":
            self.terminal.clear()
            self._append_terminal("[cleared]\n")
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
            self.input.setText(last["user"])
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

    def _on_send(self) -> None:
        text = self.input.text().strip()
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

        # v1.6.3 args — first turn vs continuation.
        args: list[str] = ["--dangerously-skip-permissions"]
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

        proc = QProcess(self)
        proc.setProgram(claude)
        proc.setArguments(args)
        # Phase-1 memory bootstrap: pass SINISTER_* env vars so the child
        # learns its identity (slug / display / paths / persona).
        proc.setProcessEnvironment(_make_child_env(self.session))
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
        if not self._proc:
            return
        data = bytes(self._proc.readAllStandardOutput()).decode("utf-8", errors="replace")
        if not data:
            return
        # First chunk of EVE's reply — stop the thinking spinner and prefix.
        if not self._reply_started:
            self._stop_thinking()
            self._append_terminal("<< ")
            self._reply_started = True
        self._append_terminal(data)
        if self.session.turns:
            self.session.turns[-1]["assistant"] += data

    def _on_stderr(self) -> None:
        if not self._proc:
            return
        data = bytes(self._proc.readAllStandardError()).decode("utf-8", errors="replace")
        if data.strip():
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

        # Empty state label (replaces grid when zero cards)
        self.empty_label = QLabel("No agents yet — click Create Agent to spawn EVE.")
        self.empty_label.setObjectName("AgentMeta")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.empty_label)

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
        self.empty_label.setVisible(len(self._cards) == 0)
        self.grid.setVisible(len(self._cards) > 0)

    # ── Public API ────────────────────────────────────────────────────
    def spawn_agent(self, project_key: str = "sanctum",
                    agent_name: str | None = None,
                    mode: str = "claude") -> str:
        """Add a new card and return its pane_id.

        Phase-1 memory bootstrap: pre-creates heartbeat / inbox / PROGRESS /
        resume-points entries on disk so the spawned agent is discoverable
        to siblings within seconds. Fully wired per
        `_shared-memory/plans/Sanctum-deepclean-2026-05-21T2300Z/memory-jcode-integration-audit.md`.
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
        )
        _bootstrap_agent_memory(sess)
        card = AgentCard(sess, parent=self.grid.host)
        card.closed.connect(self._remove_card)
        self._cards[sess.pane_id] = card
        self._rebuild_folder_chips()
        self._rebuild_grid()
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
