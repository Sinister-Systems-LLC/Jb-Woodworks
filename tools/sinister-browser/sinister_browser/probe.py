# Author: RKOJ-ELENO :: 2026-05-23
# License: AGPL-3.0-or-later

"""Layer A — connectivity probe against firefox-agent-bridge upstream.

stdlib-only. Performs:

1. TCP connect to (host, port) — refused/timeout → bridge not installed
   or Firefox not running (exit code 2).
2. Minimal HTTP Upgrade handshake (RFC 6455 §4.2.2 client side) — server
   must respond with 101 Switching Protocols + correct Sec-WebSocket-Accept
   header. If yes → bridge alive (exit 0). If no → something else on the
   port, or the bridge is broken (exit 3).

We deliberately do NOT send a WebSocket frame here — that needs the full
client framing logic and lives in Layer B. The handshake response is
sufficient evidence that the listener speaks WebSocket.
"""

from __future__ import annotations

import base64
import hashlib
import secrets
import socket
from dataclasses import dataclass


# RFC 6455 §4.2.2 — fixed GUID concatenated with the client key,
# SHA-1 hashed, base64-encoded, returned by the server.
_WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


@dataclass(frozen=True)
class ProbeResult:
    """Outcome of a probe attempt.

    `exit_code` follows the documented contract:
      0 = bridge alive (handshake completed with correct Accept)
      2 = bridge not installed (TCP refused / timeout)
      3 = installed but unreachable (TCP ok, handshake wrong)
    """

    exit_code: int
    summary: str
    host: str
    port: int
    tcp_ok: bool
    handshake_ok: bool
    server_header: str | None = None
    accept_header_match: bool | None = None
    error: str | None = None


def _expected_accept(client_key_b64: str) -> str:
    raw = (client_key_b64 + _WS_GUID).encode("ascii")
    return base64.b64encode(hashlib.sha1(raw).digest()).decode("ascii")


def _try_handshake(
    sock: socket.socket,
    host: str,
    port: int,
    timeout: float,
) -> tuple[bool, str | None, bool | None]:
    """Send WebSocket Upgrade GET; return (101_ok, server_header, accept_match)."""
    client_key = base64.b64encode(secrets.token_bytes(16)).decode("ascii")
    request_lines = [
        "GET / HTTP/1.1",
        f"Host: {host}:{port}",
        "Upgrade: websocket",
        "Connection: Upgrade",
        f"Sec-WebSocket-Key: {client_key}",
        "Sec-WebSocket-Version: 13",
        "Origin: http://sinister-browser-probe",
        "",
        "",
    ]
    request = "\r\n".join(request_lines).encode("ascii")
    sock.settimeout(timeout)
    sock.sendall(request)

    # Read until headers are complete (\r\n\r\n) or timeout.
    buf = bytearray()
    while b"\r\n\r\n" not in buf and len(buf) < 4096:
        try:
            chunk = sock.recv(1024)
        except socket.timeout:
            return False, None, None
        if not chunk:
            break
        buf.extend(chunk)

    text = buf.decode("iso-8859-1", errors="replace")
    if "\r\n\r\n" not in text:
        return False, None, None
    head = text.split("\r\n\r\n", 1)[0]
    lines = head.split("\r\n")
    status = lines[0] if lines else ""
    headers = {}
    for ln in lines[1:]:
        if ":" in ln:
            k, _, v = ln.partition(":")
            headers[k.strip().lower()] = v.strip()

    server = headers.get("server")
    accept = headers.get("sec-websocket-accept", "")
    accept_match = accept == _expected_accept(client_key)
    upgrade_ok = "101" in status and accept_match
    return upgrade_ok, server, accept_match


def probe(
    host: str = "127.0.0.1",
    port: int = 8766,
    timeout: float = 3.0,
) -> ProbeResult:
    """Run a Layer A probe. Returns a ProbeResult; never raises."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        try:
            sock.connect((host, port))
        except (ConnectionRefusedError, socket.timeout, OSError) as e:
            return ProbeResult(
                exit_code=2,
                summary=f"bridge not installed or Firefox not running ({type(e).__name__})",
                host=host, port=port,
                tcp_ok=False, handshake_ok=False,
                error=str(e),
            )

        try:
            ok, server, accept_match = _try_handshake(sock, host, port, timeout)
        except (OSError, socket.timeout) as e:
            return ProbeResult(
                exit_code=3,
                summary=f"TCP connected but handshake failed ({type(e).__name__})",
                host=host, port=port,
                tcp_ok=True, handshake_ok=False,
                error=str(e),
            )

        if ok:
            return ProbeResult(
                exit_code=0,
                summary="bridge alive — WebSocket handshake completed",
                host=host, port=port,
                tcp_ok=True, handshake_ok=True,
                server_header=server, accept_header_match=True,
            )
        return ProbeResult(
            exit_code=3,
            summary="TCP open but handshake rejected (server present but not the bridge, or bridge broken)",
            host=host, port=port,
            tcp_ok=True, handshake_ok=False,
            server_header=server, accept_header_match=accept_match,
        )
    finally:
        try:
            sock.close()
        except OSError:
            pass
