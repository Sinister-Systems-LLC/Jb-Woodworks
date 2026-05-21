# Sinister Term :: ipc.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# JSON-over-TCP-localhost IPC server. Loosely modeled on handterm's
# `handterm @ <command>` socket protocol (open-window / send-text / get-text /
# send-key / set-title / close / ls) — see canonical-20 attribution to
# Justin Huang / handterm at github.com/1jehuang/handterm. Re-implementation
# in our codebase is AGPL-3.0-or-later, RKOJ-ELENO authored.
#
# Wire protocol:
#     request : {"cmd": "<name>", "token": "<bearer>", "args": {...}}\n
#     response: {"ok": bool, "result": {...}, "error": "<msg>"}\n
#
# Connection: one request → one response → close. Plain TCP, newline-delimited
# JSON. No keep-alive. No SSE in v1 (planned PH-SUBSCRIBE).

from __future__ import annotations

import json
import os
import secrets
import socket
import threading
import time
from collections import deque
from pathlib import Path
from typing import Any, Callable, Optional

from term.commands import SANCTUM_ROOT, dispatch


HOST = "127.0.0.1"
DEFAULT_PORT = 5081
TOKEN_PATH = SANCTUM_ROOT / "_shared-memory" / "sterm-ipc-token.txt"
SESSIONS_DIR = SANCTUM_ROOT / "_shared-memory" / "sterm-ipc-sessions"


# In-process state shared with the prompt main loop
_pending_inject: "deque[str]" = deque()
_close_requested = threading.Event()


def pop_pending_inject() -> Optional[str]:
    """Called by the main prompt loop to consume any IPC-injected text."""
    try:
        return _pending_inject.popleft()
    except IndexError:
        return None


def close_requested() -> bool:
    return _close_requested.is_set()


# ── token management ────────────────────────────────────────────────────────

def _ensure_token() -> str:
    """Generate (or read existing) bearer token and persist to disk."""
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    if TOKEN_PATH.exists():
        try:
            tok = TOKEN_PATH.read_text(encoding="utf-8").strip()
            if tok:
                return tok
        except OSError:
            pass
    tok = secrets.token_urlsafe(32)
    TOKEN_PATH.write_text(tok, encoding="utf-8")
    return tok


def _record_session(pid: int, port: int) -> Path:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    path = SESSIONS_DIR / f"sterm-{pid}.json"
    path.write_text(json.dumps({
        "_author": "RKOJ-ELENO :: 2026-05-21",
        "pid": pid,
        "port": port,
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "cwd": str(Path.cwd()),
    }, indent=2), encoding="utf-8")
    return path


def _clear_session(pid: int) -> None:
    path = SESSIONS_DIR / f"sterm-{pid}.json"
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


# ── command handlers ────────────────────────────────────────────────────────

def _h_health(_args: dict) -> dict:
    from term import __version__
    return {
        "alive": True,
        "version": __version__,
        "pid": os.getpid(),
        "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "cwd": str(Path.cwd()),
    }


def _h_state(_args: dict) -> dict:
    from term.status import (
        detect_project_for_cwd,
        freshest_sibling_heartbeat,
        git_branch,
        pending_inbox_count,
        short_cwd_relative_to_project,
    )
    hb = freshest_sibling_heartbeat()
    return {
        "cwd": str(Path.cwd()),
        "cwd_short": short_cwd_relative_to_project(),
        "project": detect_project_for_cwd(),
        "branch": git_branch(),
        "inbox_count": pending_inbox_count(),
        "freshest_heartbeat": {"agent": hb[0], "age_min": hb[1]} if hb else None,
        "pid": os.getpid(),
        "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def _h_dispatch(args: dict) -> dict:
    line = args.get("text") or ""
    if not line:
        return {"_error": "missing 'text' arg"}
    result = dispatch(line)
    return {
        "handled": result.handled,
        "output": result.output,
        "exit_term": result.exit_term,
    }


def _h_send_text(args: dict) -> dict:
    """Queue text to be dispatched on the next prompt iteration."""
    text = args.get("text") or ""
    if not text:
        return {"_error": "missing 'text' arg"}
    _pending_inject.append(text)
    return {"queued": True, "queue_depth": len(_pending_inject)}


def _h_get_prompt(_args: dict) -> dict:
    from term.app import _prompt_text
    parts = [{"class": cls, "text": txt} for cls, txt in _prompt_text()]
    return {"segments": parts}


def _h_get_toolbar(_args: dict) -> dict:
    from term.app import _bottom_toolbar
    parts = [{"class": cls, "text": txt} for cls, txt in _bottom_toolbar()]
    return {"segments": parts}


def _h_get_history(args: dict) -> dict:
    limit = int(args.get("limit") or 20)
    hist = SANCTUM_ROOT / "_shared-memory" / "sinister-term-history" / "history.jsonl"
    if not hist.exists():
        return {"lines": []}
    try:
        lines = hist.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as e:
        return {"_error": f"read failed: {e}"}
    return {"lines": lines[-limit:], "total": len(lines)}


def _h_set_title(args: dict) -> dict:
    title = args.get("text") or ""
    if not title:
        return {"_error": "missing 'text' arg"}
    import platform
    if platform.system() == "Windows":
        os.system(f"title {title}")
    else:
        # ANSI OSC 0 set window title
        import sys
        sys.stdout.write(f"\033]0;{title}\007")
        sys.stdout.flush()
    return {"title": title}


def _h_ls(_args: dict) -> dict:
    if not SESSIONS_DIR.exists():
        return {"sessions": []}
    out = []
    for f in sorted(SESSIONS_DIR.glob("sterm-*.json")):
        try:
            out.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            continue
    return {"sessions": out}


def _h_close(_args: dict) -> dict:
    _close_requested.set()
    return {"closing": True}


def _h_swarm_spawn(args: dict) -> dict:
    project = args.get("project")
    if not project:
        return {"_error": "missing 'project' arg"}
    from term import swarm
    rc = swarm.spawn(project)
    return {"rc": rc, "project": project}


def _h_swarm_broadcast(args: dict) -> dict:
    msg = args.get("text") or ""
    if not msg:
        return {"_error": "missing 'text' arg"}
    from term import swarm
    path = swarm.broadcast(msg)
    return {"path": str(path)}


HANDLERS: dict[str, Callable[[dict], dict]] = {
    "health":           _h_health,
    "state":            _h_state,
    "dispatch":         _h_dispatch,
    "send-text":        _h_send_text,
    "get-prompt":       _h_get_prompt,
    "get-toolbar":      _h_get_toolbar,
    "get-history":      _h_get_history,
    "set-title":        _h_set_title,
    "ls":               _h_ls,
    "close":            _h_close,
    "swarm-spawn":      _h_swarm_spawn,
    "swarm-broadcast":  _h_swarm_broadcast,
}


# ── server loop ─────────────────────────────────────────────────────────────

def _handle_connection(conn: socket.socket, expected_token: str) -> None:
    try:
        conn.settimeout(5.0)
        buf = bytearray()
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            buf.extend(chunk)
            if b"\n" in chunk:
                break
        if not buf:
            return
        line = buf.split(b"\n", 1)[0].decode("utf-8", errors="replace").strip()
        try:
            req = json.loads(line)
        except json.JSONDecodeError as e:
            _write_response(conn, {"ok": False, "error": f"bad json: {e}"})
            return

        token = req.get("token") or ""
        if token != expected_token:
            _write_response(conn, {"ok": False, "error": "unauthorized: missing or invalid token"})
            return

        cmd = req.get("cmd") or ""
        handler = HANDLERS.get(cmd)
        if not handler:
            _write_response(conn, {"ok": False, "error": f"unknown command: {cmd!r}. known: {sorted(HANDLERS)}"})
            return

        try:
            result = handler(req.get("args") or {})
        except Exception as e:
            _write_response(conn, {"ok": False, "error": f"handler crashed: {type(e).__name__}: {e}"})
            return

        if isinstance(result, dict) and result.get("_error"):
            _write_response(conn, {"ok": False, "error": result["_error"]})
        else:
            _write_response(conn, {"ok": True, "result": result})
    except Exception:
        # Don't kill the server thread on a single bad connection
        try:
            _write_response(conn, {"ok": False, "error": "connection handler crashed"})
        except Exception:
            pass
    finally:
        try:
            conn.close()
        except OSError:
            pass


def _write_response(conn: socket.socket, payload: dict) -> None:
    try:
        body = json.dumps(payload, default=str).encode("utf-8") + b"\n"
        conn.sendall(body)
    except (BrokenPipeError, ConnectionResetError, OSError):
        pass


def serve(port: int = DEFAULT_PORT) -> None:
    """Blocking server loop. Run in a daemon thread from app.run()."""
    token = _ensure_token()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind((HOST, port))
    except OSError as e:
        # Port already in use — likely another sterm; skip silently
        try:
            sock.close()
        except OSError:
            pass
        return
    sock.listen(8)
    sock.settimeout(0.5)  # allow periodic close-check
    session_path = _record_session(os.getpid(), port)
    try:
        while not _close_requested.is_set():
            try:
                conn, _addr = sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            t = threading.Thread(
                target=_handle_connection,
                args=(conn, token),
                daemon=True,
            )
            t.start()
    finally:
        try:
            sock.close()
        except OSError:
            pass
        _clear_session(os.getpid())


def serve_in_background(port: int = DEFAULT_PORT) -> threading.Thread:
    """Start the IPC server in a daemon thread. Returns the thread handle."""
    t = threading.Thread(target=serve, args=(port,), daemon=True, name="sterm-ipc")
    t.start()
    return t


def read_token() -> str:
    """Read the bearer token from disk (called by IPC clients)."""
    return TOKEN_PATH.read_text(encoding="utf-8").strip()
