# Author: RKOJ-ELENO :: 2026-05-23
"""Workstation HTTP API server (127.0.0.1:5077) — agents call this to
get phone status / claim phones / run shell commands / take screenshots
without going through brittle shell pipelines.

stdlib-only (http.server) so PyInstaller doesn't need to bundle Flask
or FastAPI. JSON in / JSON out. Bound to loopback only — no external
network exposure.

Endpoints:
    GET  /api/health                       — { ok: true, ver, uptime_s }
    GET  /api/phones                       — list ADB devices + claim owner
    POST /api/phones/<serial>/claim        — body { agent_id, agent_display }
    POST /api/phones/<serial>/release      — body { agent_id? }
    POST /api/phones/<serial>/screenshot   — saves PNG to Desktop, returns path
    POST /api/phones/<serial>/shell        — body { cmd } — runs adb shell cmd
    GET  /api/agents                       — list claim-owners + counts
    GET  /api/version                      — sinister_rkoj_qt + manifest
"""

from __future__ import annotations

import json
import shutil
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from . import state


API_HOST = "127.0.0.1"
API_PORT = 5077      # operator-reserved port per CLAUDE.md (RKOJ workbench)
_CREATE_NO_WINDOW = 0x08000000


def _find_adb() -> str | None:
    on_path = shutil.which("adb") or shutil.which("adb.exe")
    if on_path:
        return on_path
    winget = Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Packages"
    for pkg in winget.glob("Genymobile.scrcpy_*"):
        for sub in pkg.glob("scrcpy-win*"):
            cand = sub / "adb.exe"
            if cand.exists():
                return str(cand)
    return None


_API_STARTED_AT = time.time()


class _Handler(BaseHTTPRequestHandler):
    """Minimal JSON handler. All routes inline for clarity — under
    300 LoC and operator can `Grep '/api/'` to find every endpoint."""

    server_version = "EVE-Workstation-API/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        # Silence default per-request stderr noise. Errors are surfaced
        # via the JSON response body instead.
        pass

    def _send_json(self, code: int, body: dict) -> None:
        payload = json.dumps(body, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)

    def _read_json(self) -> dict:
        try:
            ln = int(self.headers.get("Content-Length", "0") or 0)
            if ln <= 0:
                return {}
            data = self.rfile.read(ln)
            return json.loads(data.decode("utf-8"))
        except Exception:
            return {}

    # ── Route table ────────────────────────────────────────────────────
    def do_GET(self) -> None:
        p = self.path.rstrip("/")
        if p == "/api/health":
            return self._send_json(200, {
                "ok": True,
                "service": "EVE Workstation API",
                "version": "1.0",
                "uptime_s": int(time.time() - _API_STARTED_AT),
            })
        if p == "/api/version":
            try:
                from . import __version__
                return self._send_json(200, {"sinister_rkoj_qt": __version__})
            except Exception:
                return self._send_json(200, {"sinister_rkoj_qt": "?"})
        if p == "/api/phones":
            devs = state.list_adb_devices()
            out = []
            for d in devs:
                owner = state.who_owns(d.serial)
                out.append({
                    "serial": d.serial,
                    "model": d.model,
                    "state": d.state,
                    "transport": d.transport,
                    "owner": owner,
                })
            return self._send_json(200, {"devices": out, "count": len(out)})
        if p == "/api/agents":
            claims = state.all_claims()
            by_agent: dict[str, list[str]] = {}
            for serial, rec in claims.items():
                aid = rec.get("agent_id", "?")
                by_agent.setdefault(aid, []).append(serial)
            return self._send_json(200, {
                "agents": [
                    {"agent_id": aid, "owned_phones": phones,
                     "phone_count": len(phones)}
                    for aid, phones in by_agent.items()
                ],
                "total_claimed_phones": len(claims),
            })
        return self._send_json(404, {"error": f"unknown route: {p}"})

    def do_POST(self) -> None:
        p = self.path.rstrip("/")
        body = self._read_json()
        # /api/phones/<serial>/claim
        if p.startswith("/api/phones/") and p.endswith("/claim"):
            serial = p[len("/api/phones/"):-len("/claim")]
            agent_id = body.get("agent_id", "").strip()
            if not agent_id:
                return self._send_json(400, {"error": "agent_id required"})
            ok = state.claim_phone(serial, agent_id,
                                   body.get("agent_display", ""))
            owner = state.who_owns(serial)
            return self._send_json(200 if ok else 409, {
                "claimed": ok, "serial": serial, "owner": owner,
            })
        if p.startswith("/api/phones/") and p.endswith("/release"):
            serial = p[len("/api/phones/"):-len("/release")]
            state.release_phone(serial, body.get("agent_id") or None)
            return self._send_json(200, {"released": serial})
        if p.startswith("/api/phones/") and p.endswith("/screenshot"):
            serial = p[len("/api/phones/"):-len("/screenshot")]
            adb = _find_adb()
            if not adb:
                return self._send_json(500, {"error": "adb not found"})
            # Owner check — must hold the claim
            req_aid = body.get("agent_id", "")
            cur = state.who_owns(serial)
            if cur and cur.get("agent_id") != req_aid:
                return self._send_json(403, {
                    "error": "phone is claimed by another agent",
                    "owner": cur,
                })
            ts = time.strftime("%Y%m%dT%H%M%S")
            out_fp = Path.home() / "Desktop" / f"eve-{serial}-{ts}.png"
            try:
                with open(out_fp, "wb") as fh:
                    r = subprocess.run(
                        [adb, "-s", serial, "exec-out", "screencap", "-p"],
                        stdout=fh, stderr=subprocess.PIPE, timeout=15,
                        creationflags=_CREATE_NO_WINDOW,
                    )
                if r.returncode != 0:
                    return self._send_json(500, {
                        "error": "screencap failed",
                        "stderr": r.stderr.decode("utf-8", "replace")[:200],
                    })
                return self._send_json(200, {"path": str(out_fp)})
            except Exception as exc:
                return self._send_json(500, {"error": str(exc)})
        if p.startswith("/api/phones/") and p.endswith("/shell"):
            serial = p[len("/api/phones/"):-len("/shell")]
            cmd = body.get("cmd", "").strip()
            if not cmd:
                return self._send_json(400, {"error": "cmd required"})
            adb = _find_adb()
            if not adb:
                return self._send_json(500, {"error": "adb not found"})
            req_aid = body.get("agent_id", "")
            cur = state.who_owns(serial)
            if cur and cur.get("agent_id") != req_aid:
                return self._send_json(403, {
                    "error": "phone is claimed by another agent",
                    "owner": cur,
                })
            try:
                r = subprocess.run(
                    [adb, "-s", serial, "shell", cmd],
                    capture_output=True, timeout=30,
                    creationflags=_CREATE_NO_WINDOW,
                )
                return self._send_json(200, {
                    "stdout": r.stdout.decode("utf-8", "replace"),
                    "stderr": r.stderr.decode("utf-8", "replace"),
                    "returncode": r.returncode,
                })
            except subprocess.TimeoutExpired:
                return self._send_json(504, {"error": "shell timeout 30s"})
            except Exception as exc:
                return self._send_json(500, {"error": str(exc)})
        return self._send_json(404, {"error": f"unknown route: {p}"})


_server: ThreadingHTTPServer | None = None
_thread: threading.Thread | None = None


def start_api_server() -> str:
    """Idempotent. Returns "started" / "running" / "failed: <reason>"."""
    global _server, _thread
    if _server is not None:
        return "running"
    try:
        _server = ThreadingHTTPServer((API_HOST, API_PORT), _Handler)
    except OSError as exc:
        _server = None
        return f"failed: {exc}"
    _thread = threading.Thread(
        target=_server.serve_forever, name="eve-api", daemon=True,
    )
    _thread.start()
    return "started"


def stop_api_server() -> None:
    global _server, _thread
    if _server is None:
        return
    try:
        _server.shutdown()
        _server.server_close()
    except Exception:
        pass
    _server = None
    _thread = None


def api_status() -> dict:
    return {
        "running": _server is not None,
        "host": API_HOST,
        "port": API_PORT,
        "url": f"http://{API_HOST}:{API_PORT}",
    }
