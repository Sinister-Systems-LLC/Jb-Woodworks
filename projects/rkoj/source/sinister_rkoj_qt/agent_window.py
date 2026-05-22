# Author: RKOJ-ELENO :: 2026-05-22
"""AgentWindow — each spawned EVE agent gets its own top-level window.

Operator (verbatim, 2026-05-21): *"When i click new agent it will be like
we click the jcode exe and openeed a window."*

This is the canonical "click + Create Agent" path as of v1.6.6. The
inline-card grid in AgentsView stays for legacy /spawn paths but is
no longer the primary surface.

Layout (each window):

    ┌───────────────────────────────────────────────┐  ◀── frameless,
    │  ●  EVE on <project>   slug · session uuid    │      rounded
    │                                          [X]  │      (18px)
    ├───────────────────────────────────────────────┤
    │                                               │
    │  AgentCard (terminal + spinner + input)       │
    │                                               │
    └───────────────────────────────────────────────┘

Cascade-offset positioning so opening N windows fans them out instead of
stacking. Each window owns its own QProcess + heartbeat + resume_dir.
Closing the window kills the subprocess cleanly.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import (
    QGuiApplication, QIcon, QMouseEvent, QPainterPath, QRegion,
)
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QMainWindow, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget,
)

try:
    from PyQt6.QtSvgWidgets import QSvgWidget  # type: ignore
    _HAS_SVG = True
except Exception:  # pragma: no cover
    _HAS_SVG = False

from . import state
from .agents_tab import AgentCard, AgentSession, _bootstrap_agent_memory
from .theme import (
    BORDER, MUTED_FG, OUTER_PADDING, PANEL_BG, PURPLE_PRIMARY,
    WINDOW_RADIUS, nav_icon,
)


class _MiniHeader(QWidget):
    """56px header strip for an AgentWindow — title + uuid + close-X."""

    def __init__(self, display_name: str, slug: str, session_uuid: str,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("AgentWindowHeader")
        self.setFixedHeight(56)
        self._drag_origin: Optional[QPoint] = None
        self._build(display_name, slug, session_uuid)

    def _build(self, display_name: str, slug: str, session_uuid: str) -> None:
        row = QHBoxLayout(self)
        row.setContentsMargins(20, 0, 12, 0)
        row.setSpacing(14)

        # Live status dot (always green for now; AgentCard will repaint when
        # it gets its own _set_status wired to this — Phase-2).
        dot = QLabel()
        dot.setFixedSize(10, 10)
        dot.setStyleSheet(
            f"background-color: {PURPLE_PRIMARY}; border-radius: 5px;"
        )
        row.addWidget(dot)

        # Title
        title = QLabel(display_name)
        title.setStyleSheet(
            f"color: {PURPLE_PRIMARY}; background: transparent; "
            f"font-size: 18px; font-weight: 700; letter-spacing: -0.3px;"
        )
        row.addWidget(title)

        # Slug · session_uuid (short)
        meta = QLabel(f"{slug}  ·  {session_uuid[:8]}…")
        meta.setStyleSheet(
            f"color: {MUTED_FG}; background: transparent; "
            f"font-family: 'JetBrains Mono', 'Cascadia Mono', monospace; "
            f"font-size: 11px;"
        )
        row.addWidget(meta)

        row.addStretch(1)

        # Frameless close-X
        self.btn_close = QPushButton()
        self.btn_close.setObjectName("WinCtlClose")
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setFixedSize(32, 32)
        layout = QHBoxLayout(self.btn_close)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if _HAS_SVG:
            layout.addWidget(nav_icon("win-close", size=14))
        row.addWidget(self.btn_close)

    # ── Drag-to-move (frameless support — anywhere on the strip) ───────
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            win = self.window()
            if win is not None:
                self._drag_origin = (
                    event.globalPosition().toPoint() - win.frameGeometry().topLeft()
                )
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_origin is not None and event.buttons() & Qt.MouseButton.LeftButton:
            win = self.window()
            if win is not None:
                win.move(event.globalPosition().toPoint() - self._drag_origin)
                event.accept()
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_origin = None
        super().mouseReleaseEvent(event)


class AgentWindow(QMainWindow):
    """Top-level frameless rounded window hosting a single AgentCard.

    Operator clicks `+ Create Agent` (or `Resume Saved Session`) in the main
    RKOJ window → a new AgentWindow opens. Closing it kills the subprocess
    + writes a final heartbeat with `session_status: ended`.
    """

    # Class-level cascade counter so successive windows fan out instead of
    # opening at the exact same screen position.
    _cascade_counter = 0

    def __init__(self,
                 project_key: str,
                 agent_name: Optional[str] = None,
                 mode: str = "claude",
                 session_uuid: Optional[str] = None,
                 parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window
        )
        self.setMinimumSize(720, 540)
        self.resize(880, 680)
        self._cascade_position()

        # ── Build the session + bootstrap memory ───────────────────────
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
        self.session = sess
        self.setWindowTitle(f"EVE on {display}")

        # ── Chrome ─────────────────────────────────────────────────────
        body = QWidget()
        body.setObjectName("OuterBody")
        self.setCentralWidget(body)
        outer = QVBoxLayout(body)
        outer.setContentsMargins(
            OUTER_PADDING, OUTER_PADDING, OUTER_PADDING, OUTER_PADDING
        )
        outer.setSpacing(0)

        # Single rounded card containing header + AgentCard.
        main_card = QWidget()
        main_card.setObjectName("MainCard")
        main_layout = QVBoxLayout(main_card)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Mini header
        self.header = _MiniHeader(
            display_name=sess.display_name,
            slug=sess.slug,
            session_uuid=sess.session_uuid,
            parent=main_card,
        )
        self.header.btn_close.clicked.connect(self.close)
        main_layout.addWidget(self.header)

        # The AgentCard (full terminal + input + spinner) — reused from
        # agents_tab.py without modification. Its own internal close-X
        # also fires `closed` which we route to the window close.
        self.card = AgentCard(sess, parent=main_card)
        if session_uuid:
            # Resume mode — next send uses `--resume <uuid>` (no first-turn
            # persona block; claude has the session already).
            self.card._first_turn = False
            self.card._append_terminal(
                f"  ▸ RESUMED session (session_uuid={session_uuid[:12]}…)\n"
                f"    Next message uses `claude -r {session_uuid} -p ...`\n"
                f"    Claude has the full conversation history server-side.\n"
                f"\n"
            )
        self.card.closed.connect(lambda *_: self.close())
        main_layout.addWidget(self.card, stretch=1)

        outer.addWidget(main_card, stretch=1)

    def _cascade_position(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            offset = (AgentWindow._cascade_counter * 32) % 320
            x = geo.x() + 140 + offset
            y = geo.y() + 90 + offset
            self.move(x, y)
        AgentWindow._cascade_counter += 1

    # ── Rounded outer mask (chrome corners) ────────────────────────────
    def resizeEvent(self, event) -> None:
        path = QPainterPath()
        path.addRoundedRect(0.0, 0.0, float(self.width()), float(self.height()),
                            float(WINDOW_RADIUS), float(WINDOW_RADIUS))
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)
        super().resizeEvent(event)

    # ── Clean shutdown (auto-save resume-point + kill child) ──────────
    def closeEvent(self, event) -> None:
        # v1.6.7 — auto-save the session to a resume-point JSON so the
        # operator never loses a conversation just because they closed the
        # window. Always writes (even if no turns happened) so the slot
        # exists for /resume later.
        try:
            self._auto_save_resume_point()
        except Exception:
            pass
        try:
            self.card.shutdown()
        except Exception:
            pass
        event.accept()
        super().closeEvent(event)

    def _auto_save_resume_point(self) -> None:
        """Write a final resume-point JSON to sess.resume_dir on close.

        Same shape as the /save slash command writes — so the picker
        treats both identically. Filename format: `<ts>.json` (UTC).
        """
        import json
        from pathlib import Path
        sess = self.session
        if not sess.resume_dir:
            return
        try:
            d = Path(sess.resume_dir)
            d.mkdir(parents=True, exist_ok=True)
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
            fp = d / f"{ts}-autoclose.json"
            payload = {
                "schema_version": "sinister.resume-point.v1",
                "agent_identity": "EVE",
                "agent_display": sess.display_name,
                "slug": sess.slug,
                "pane_id": sess.pane_id,
                "session_uuid": sess.session_uuid,
                "project_key": sess.project_key,
                "project_display": sess.project_display,
                "agent_name": sess.agent_name,
                "mode": sess.mode,
                "turns": sess.turns,
                "saved_at": datetime.now(timezone.utc).isoformat(),
                "save_reason": "autoclose",
                "resume_cmd": (
                    f"claude --dangerously-skip-permissions "
                    f"-r {sess.session_uuid} -p 'your message'"
                ),
            }
            with open(fp, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2)
        except Exception:
            pass
