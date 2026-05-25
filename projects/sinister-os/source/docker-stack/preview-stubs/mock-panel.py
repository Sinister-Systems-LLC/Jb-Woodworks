#!/usr/bin/env python3
"""mock-panel.py — canned-reply replacement for snap.sinijkr.com/chatter.

Author: RKOJ-ELENO :: 2026-05-25
License: operator-owned (Sinister fleet, internal)

Phase 1A stub. Stands in for the real chatbot lane panel so the EVE-LLM
bridge surfaces can be exercised without burning Anthropic tokens or
needing the operator's real license key during preview.

Endpoints (subset of EVE-LLM bridge SPEC-2026-05-25.md § 4):
  GET  /health                  → ok
  POST /api/chatter/test        → canned reply (echo + persona stamp + latency_ms)
  GET  /api/chatter/groups      → 3 canned personas
  POST /api/chatter/tweak       → echoes the instruction
  GET  /api/chatter/events      → empty list (long-poll stub)
"""

from __future__ import annotations

import json
import logging
import random
import sys
import time
import uuid
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BIND = ("0.0.0.0", 8090)
VERSION = "0.1.0-mock"
STARTED_TS = time.time()

PERSONAS = [
    {"id": "default", "label": "Default", "description": "Helpful, terse, operator-tuned", "accent": "#c084fc"},
    {"id": "slack-tone", "label": "Slack tone", "description": "Casual, short sentences", "accent": "#6366f1"},
    {"id": "code-review", "label": "Code review", "description": "Direct, cite line numbers", "accent": "#22d3ee"},
]

CANNED_REPLIES = [
    "Acknowledged. Standing by.",
    "Got it — what next?",
    "Reading… looks good. Anything specific you want me to check?",
    "Done. Preview is up at http://localhost:6080.",
    "I see what you mean. The fix is straightforward — want me to ship it?",
    "Confirmed. Running the test now.",
    "That's the right approach. Proceeding.",
    "Mock-panel here — real reply lands when the bridge connects to snap.sinijkr.com.",
]

LOG = logging.getLogger("mock-panel")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        LOG.debug("%s - %s", self.address_string(), fmt % args)

    def _send_json(self, code: int, payload: dict | list) -> None:
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
            return self._send_json(HTTPStatus.OK, {"status": "ok", "version": VERSION, "uptime_s": round(time.time() - STARTED_TS, 2)})
        if self.path == "/api/chatter/groups":
            return self._send_json(HTTPStatus.OK, {"personas": PERSONAS, "cached_at_ts": now_iso()})
        if self.path.startswith("/api/chatter/events"):
            return self._send_json(HTTPStatus.OK, {"events": [], "since_ts": now_iso()})
        return self._send_json(HTTPStatus.NOT_FOUND, {"error": "not_found", "path": self.path})

    def do_POST(self):
        body = self._read_json()
        if self.path == "/api/chatter/test":
            persona = body.get("persona", "default")
            message = body.get("message", "")
            reply = random.choice(CANNED_REPLIES)
            if message.strip():
                reply = f"[stub] You said: \"{message[:60]}...\" — {reply}" if len(message) > 60 else f"[stub] You said: \"{message}\" — {reply}"
            latency_ms = random.randint(80, 350)
            time.sleep(latency_ms / 1000.0)
            return self._send_json(HTTPStatus.OK, {
                "reply": reply,
                "persona_used": persona,
                "model": "mock-panel-canned",
                "tokens": {"in": len(message.split()), "out": len(reply.split())},
                "latency_ms": latency_ms,
                "panel_event_id": f"evt_{uuid.uuid4().hex[:12]}",
            })
        if self.path == "/api/chatter/tweak":
            persona = body.get("persona", "default")
            instruction = body.get("instruction", "")
            return self._send_json(HTTPStatus.OK, {
                "persona": persona,
                "new_prompt": f"[stub-tweaked] {instruction}",
                "diff": f"+ {instruction}",
                "daily_remaining": 99,
            })
        return self._send_json(HTTPStatus.NOT_FOUND, {"error": "not_found", "path": self.path})


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s mock-panel %(levelname)s %(message)s",
    )
    LOG.info("mock-panel %s listening on %s:%d", VERSION, *BIND)
    srv = ThreadingHTTPServer(BIND, Handler)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        LOG.info("shutting down")
    return 0


if __name__ == "__main__":
    sys.exit(main())
