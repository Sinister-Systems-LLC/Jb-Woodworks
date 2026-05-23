# Author: RKOJ-ELENO :: 2026-05-23
# License: AGPL-3.0-or-later

"""Unit tests for the Layer A probe.

stdlib only; no live firefox-agent-bridge required. The tests spin up
fake TCP servers in-process to exercise the three exit-code paths.
"""

from __future__ import annotations

import base64
import hashlib
import socket
import threading
import time
import unittest

from sinister_browser.probe import probe, _WS_GUID


def _free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class _FakeWSServer:
    """A minimal WebSocket-handshake-only server. Doesn't speak frames."""

    def __init__(self, port: int, *, send_correct_accept: bool = True):
        self.port = port
        self.send_correct_accept = send_correct_accept
        self._srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._srv.bind(("127.0.0.1", port))
        self._srv.listen(1)
        self._srv.settimeout(2.0)
        self._thread = threading.Thread(target=self._serve, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def _serve(self) -> None:
        try:
            conn, _ = self._srv.accept()
        except socket.timeout:
            return
        try:
            conn.settimeout(2.0)
            buf = b""
            while b"\r\n\r\n" not in buf and len(buf) < 4096:
                chunk = conn.recv(1024)
                if not chunk:
                    break
                buf += chunk
            # Parse the Sec-WebSocket-Key
            client_key = ""
            for line in buf.decode("iso-8859-1").splitlines():
                if line.lower().startswith("sec-websocket-key:"):
                    client_key = line.split(":", 1)[1].strip()
                    break
            accept_in = client_key + _WS_GUID
            accept_correct = base64.b64encode(
                hashlib.sha1(accept_in.encode("ascii")).digest()
            ).decode("ascii")
            accept_value = accept_correct if self.send_correct_accept else "WRONG=="
            resp = (
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Accept: {accept_value}\r\n"
                "Server: fake-bridge/0.0\r\n"
                "\r\n"
            )
            conn.sendall(resp.encode("ascii"))
        finally:
            try:
                conn.close()
            except OSError:
                pass
            try:
                self._srv.close()
            except OSError:
                pass


class _FakeHTTPServer:
    """Returns plain 200 OK to anything — simulates 'wrong service on the port'."""

    def __init__(self, port: int):
        self.port = port
        self._srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._srv.bind(("127.0.0.1", port))
        self._srv.listen(1)
        self._srv.settimeout(2.0)
        self._thread = threading.Thread(target=self._serve, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def _serve(self) -> None:
        try:
            conn, _ = self._srv.accept()
        except socket.timeout:
            return
        try:
            conn.settimeout(2.0)
            # consume the request
            conn.recv(4096)
            conn.sendall(
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Length: 0\r\n"
                b"Server: not-a-bridge/0.0\r\n"
                b"\r\n"
            )
        finally:
            try:
                conn.close()
            except OSError:
                pass
            try:
                self._srv.close()
            except OSError:
                pass


class TestProbe(unittest.TestCase):
    def test_exit_2_when_nothing_listening(self):
        # Find a free port and don't bind it — connect should refuse.
        port = _free_port()
        result = probe(port=port, timeout=1.0)
        self.assertEqual(result.exit_code, 2)
        self.assertFalse(result.tcp_ok)
        self.assertFalse(result.handshake_ok)

    def test_exit_0_when_valid_ws_handshake(self):
        port = _free_port()
        srv = _FakeWSServer(port, send_correct_accept=True)
        srv.start()
        time.sleep(0.05)
        result = probe(port=port, timeout=2.0)
        self.assertEqual(
            result.exit_code, 0,
            f"summary={result.summary!r} server={result.server_header!r} match={result.accept_header_match!r}",
        )
        self.assertTrue(result.tcp_ok)
        self.assertTrue(result.handshake_ok)
        self.assertEqual(result.accept_header_match, True)

    def test_exit_3_when_wrong_accept(self):
        port = _free_port()
        srv = _FakeWSServer(port, send_correct_accept=False)
        srv.start()
        time.sleep(0.05)
        result = probe(port=port, timeout=2.0)
        self.assertEqual(result.exit_code, 3)
        self.assertTrue(result.tcp_ok)
        self.assertFalse(result.handshake_ok)
        self.assertEqual(result.accept_header_match, False)

    def test_exit_3_when_plain_http(self):
        port = _free_port()
        srv = _FakeHTTPServer(port)
        srv.start()
        time.sleep(0.05)
        result = probe(port=port, timeout=2.0)
        self.assertEqual(result.exit_code, 3)
        self.assertTrue(result.tcp_ok)
        self.assertFalse(result.handshake_ok)


if __name__ == "__main__":
    unittest.main()
