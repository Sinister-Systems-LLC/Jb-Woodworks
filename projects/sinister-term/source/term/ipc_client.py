# Sinister Term :: ipc_client.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Thin JSON-over-TCP client for the sterm IPC server. Used by `sinister ctl`
# and by sibling agents (Forge, RKOJ, Panel, Sanctum) to drive a live sterm.

from __future__ import annotations

import json
import socket
from typing import Any

from term.ipc import HOST, DEFAULT_PORT, read_token


def call(cmd: str, args: dict | None = None, port: int = DEFAULT_PORT, timeout: float = 5.0) -> dict:
    """Send one request, get one response, close the connection."""
    token = read_token()
    payload = {
        "cmd": cmd,
        "token": token,
        "args": args or {},
    }
    body = json.dumps(payload, default=str).encode("utf-8") + b"\n"
    with socket.create_connection((HOST, port), timeout=timeout) as conn:
        conn.sendall(body)
        buf = bytearray()
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            buf.extend(chunk)
            if b"\n" in chunk:
                break
    line = buf.split(b"\n", 1)[0].decode("utf-8", errors="replace").strip()
    try:
        return json.loads(line)
    except json.JSONDecodeError as e:
        return {"ok": False, "error": f"bad response json: {e}", "raw": line}
