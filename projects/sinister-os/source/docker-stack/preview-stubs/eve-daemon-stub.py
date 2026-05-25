#!/usr/bin/env python3
"""eve-daemon-stub.py — Phase 1A stub for the EVE control daemon.

Author: RKOJ-ELENO :: 2026-05-25
License: operator-owned (Sinister fleet, internal)

Implements just enough of the state-machine doc 2026-05-25 + EVE-LLM bridge
spec 2026-05-25 to render the preview UI:

  GET  /health                       → {status: ok, state: RUNNING, ...}
  GET  /v1/state                     → current state machine snapshot
  POST /v1/intent/exec               → routes intent (mocked: launch_app, etc)
  POST /v1/chat/send                 → proxies to mock-panel
  POST /v1/game-mode/{arm,disarm}    → cycles game-mode state
  GET  /v1/game-mode                 → current game-mode state
  GET  /v1/actions/recent?limit=N    → recent intent log
  GET  /v1/info                      → daemon info (uptime, version, mode)

Stdlib only — no pip install. Listens on 0.0.0.0:7331 by default.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
import urllib.request
import urllib.error
from collections import deque
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

LOG_PATH = Path("/var/log/sinister/eve.jsonl")
STATE_PATH = Path("/var/lib/sinister/eve-state.json")
GAME_MODE_PATH = Path("/var/lib/sinister/game-mode-state.json")
BIND = ("0.0.0.0", 7331)
PANEL_URL = os.environ.get("EVE_LLM_PANEL_URL", "http://mock-panel:8090")
VERSION = "0.1.0-preview"
STARTED_TS = time.time()

# Daemon state per state-machine doc 2026-05-25 § 3
DAEMON_STATE = {
    "current": "RUNNING",   # BOOT / RUNNING / REBOOTING / HALTED / FAILED
    "previous": "BOOT",
    "transitioned_at": datetime.now(timezone.utc).isoformat(),
    "epoch": 1,
    "reason": "preview-stub startup",
}

GAME_MODE_STATE = {
    "current": "DISARMED",   # DISARMED / ARMING / ARMED / GAMING / COOLDOWN / RESUMING / BLOCKED
    "previous": None,
    "transitioned_at": datetime.now(timezone.utc).isoformat(),
    "reason": None,
    "convergence_progress_pct": 0,
    "blocker": None,
}

RECENT_ACTIONS: deque[dict] = deque(maxlen=200)

LOG = logging.getLogger("eve-daemon-stub")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_log(entry: dict) -> None:
    """Append-only JSONL action log per state-machine doc § 7."""
    entry.setdefault("ts_utc", now_iso())
    RECENT_ACTIONS.append(entry)
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError as e:
        LOG.warning("log write failed: %s", e)


def proxy_chat_send(payload: dict) -> dict:
    """Forward chat.send to mock-panel and return its reply."""
    req = urllib.request.Request(
        f"{PANEL_URL}/api/chatter/test",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-License-Key": "stub-license-key"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except urllib.error.URLError as e:
        return {"error": "panel_offline", "detail": str(e)}


def transition_game_mode(new_state: str, reason: str | None = None) -> dict:
    """Move game-mode state and persist."""
    prev = GAME_MODE_STATE["current"]
    GAME_MODE_STATE.update({
        "previous": prev,
        "current": new_state,
        "transitioned_at": now_iso(),
        "reason": reason,
        "convergence_progress_pct": 100 if new_state == "ARMED" else (0 if new_state == "DISARMED" else 50),
    })
    try:
        GAME_MODE_PATH.parent.mkdir(parents=True, exist_ok=True)
        GAME_MODE_PATH.write_text(json.dumps(GAME_MODE_STATE, indent=2))
    except OSError:
        pass
    append_log({"kind": "game-mode-transition", "from": prev, "to": new_state, "reason": reason})
    return GAME_MODE_STATE


class Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):  # quieter than default
        LOG.debug("%s - %s", self.address_string(), fmt % args)

    def _send_json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8", errors="replace")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    def do_GET(self):
        if self.path == "/health":
            uptime_s = round(time.time() - STARTED_TS, 2)
            return self._send_json(HTTPStatus.OK, {
                "status": "ok",
                "state": DAEMON_STATE["current"],
                "version": VERSION,
                "preview": True,
                "uptime_s": uptime_s,
            })
        if self.path == "/v1/state":
            return self._send_json(HTTPStatus.OK, DAEMON_STATE)
        if self.path == "/v1/game-mode":
            return self._send_json(HTTPStatus.OK, GAME_MODE_STATE)
        if self.path.startswith("/v1/actions/recent"):
            limit = 10
            if "?" in self.path:
                from urllib.parse import urlparse, parse_qs
                limit = int(parse_qs(urlparse(self.path).query).get("limit", [10])[0])
            return self._send_json(HTTPStatus.OK, list(RECENT_ACTIONS)[-limit:])
        if self.path == "/v1/info":
            return self._send_json(HTTPStatus.OK, {
                "version": VERSION,
                "preview": True,
                "panel_url": PANEL_URL,
                "operator": os.environ.get("SINISTER_OPERATOR", "unknown"),
                "started_at": datetime.fromtimestamp(STARTED_TS, timezone.utc).isoformat(),
            })
        return self._send_json(HTTPStatus.NOT_FOUND, {"error": "not_found", "path": self.path})

    def do_POST(self):
        body = self._read_json()

        if self.path == "/v1/intent/exec":
            intent = body.get("intent", "unknown")
            args = body.get("args", {})
            append_log({"kind": "intent", "intent": intent, "args": args, "source": body.get("source", "cli"), "result": "ack"})
            return self._send_json(HTTPStatus.OK, {
                "intent": intent,
                "result": "ack",
                "preview_note": "intent acked but not executed — stub mode",
            })

        if self.path == "/v1/chat/send":
            reply = proxy_chat_send(body)
            append_log({"kind": "chat-send", "persona": body.get("persona", "default"), "tokens_in": len(str(body.get("message", ""))), "result": "ok" if "error" not in reply else "error"})
            return self._send_json(HTTPStatus.OK, reply)

        if self.path == "/v1/game-mode/arm":
            transition_game_mode("ARMING", reason=body.get("reason", "operator-toggle"))
            transition_game_mode("ARMED", reason="convergence-complete (stub: instant)")
            return self._send_json(HTTPStatus.OK, GAME_MODE_STATE)

        if self.path == "/v1/game-mode/disarm":
            transition_game_mode("DISARMED", reason=body.get("reason", "operator-toggle"))
            return self._send_json(HTTPStatus.OK, GAME_MODE_STATE)

        return self._send_json(HTTPStatus.NOT_FOUND, {"error": "not_found", "path": self.path})


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s eve-daemon-stub %(levelname)s %(message)s",
    )
    LOG.info("eve-daemon-stub %s listening on %s:%d (panel=%s)", VERSION, *BIND, PANEL_URL)
    append_log({"kind": "daemon-start", "version": VERSION, "preview": True})
    srv = ThreadingHTTPServer(BIND, Handler)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        LOG.info("shutting down")
    finally:
        append_log({"kind": "daemon-stop"})
    return 0


if __name__ == "__main__":
    sys.exit(main())
