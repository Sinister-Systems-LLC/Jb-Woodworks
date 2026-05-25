#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-24
# SinisterCast WebSocket bridge — phone TCP H.264 NAL stream <-> browser MediaSource.
# PC-side process surface = this script + adbd only. No scrcpy-server, no Panda.

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import shutil
import struct
import subprocess
import sys
from typing import Optional

try:
    import websockets
    try:
        from websockets.asyncio.server import ServerConnection as WebSocketServerProtocol  # websockets >= 13
    except ImportError:
        from websockets.server import WebSocketServerProtocol  # websockets < 13 fallback
except ImportError:
    sys.stderr.write("missing dep: pip install websockets\n")
    sys.exit(2)

LOG = logging.getLogger("sinister-cast")
PHONE_VIDEO_PORT = 9001
PHONE_TOUCH_PORT = 9101
NAL_START = b"\x00\x00\x00\x01"


def _run_adb(serial: str, *args: str) -> subprocess.CompletedProcess:
    adb = shutil.which("adb") or "adb"
    cmd = [adb, "-s", serial, *args]
    LOG.info("adb: %s", " ".join(cmd))
    return subprocess.run(cmd, capture_output=True, text=True, timeout=15)


def setup_adb_tunnels(serial: str) -> None:
    rev = _run_adb(serial, "reverse", f"tcp:{PHONE_VIDEO_PORT}", f"tcp:{PHONE_VIDEO_PORT}")
    if rev.returncode != 0:
        LOG.warning("adb reverse failed (continuing — phone may not be attached yet): %s", rev.stderr.strip())
    fwd = _run_adb(serial, "forward", f"tcp:{PHONE_TOUCH_PORT}", f"tcp:{PHONE_VIDEO_PORT}")
    if fwd.returncode != 0:
        LOG.warning("adb forward failed (continuing): %s", fwd.stderr.strip())


async def _read_exact(reader: asyncio.StreamReader, n: int) -> bytes:
    buf = await reader.readexactly(n)
    return buf


async def _phone_tcp_reader(out_queue: "asyncio.Queue[bytes]") -> None:
    backoff = 0.5
    while True:
        try:
            reader, writer = await asyncio.open_connection("127.0.0.1", PHONE_VIDEO_PORT)
            LOG.info("connected to phone video tcp 127.0.0.1:%d", PHONE_VIDEO_PORT)
            backoff = 0.5
            while True:
                header = await _read_exact(reader, 4)
                (length,) = struct.unpack(">I", header)
                if length == 0 or length > 8 * 1024 * 1024:
                    raise ConnectionError(f"bogus nal length {length}")
                payload = await _read_exact(reader, length)
                # Browser MediaSource expects Annex-B framed NAL units (00 00 00 01 + payload).
                await out_queue.put(NAL_START + payload)
            writer.close()
        except (ConnectionError, asyncio.IncompleteReadError, OSError) as exc:
            LOG.warning("phone tcp dropped (%s) — reconnect in %.1fs", exc, backoff)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 8.0)


async def _stream_handler(ws: WebSocketServerProtocol, queue: "asyncio.Queue[bytes]") -> None:
    LOG.info("viewer connected: /stream")
    try:
        while True:
            chunk = await queue.get()
            await ws.send(chunk)
    except websockets.ConnectionClosed:
        LOG.info("viewer disconnected: /stream")


async def _touch_handler(ws: WebSocketServerProtocol) -> None:
    LOG.info("viewer connected: /touch")
    backoff = 0.5
    while True:
        try:
            reader, writer = await asyncio.open_connection("127.0.0.1", PHONE_TOUCH_PORT)
            LOG.info("connected to phone touch tcp 127.0.0.1:%d", PHONE_TOUCH_PORT)
            backoff = 0.5
            try:
                async for msg in ws:
                    try:
                        evt = json.loads(msg) if isinstance(msg, str) else None
                    except json.JSONDecodeError:
                        continue
                    if not evt or "x" not in evt or "y" not in evt or "action" not in evt:
                        continue
                    line = (json.dumps({
                        "x": int(evt["x"]),
                        "y": int(evt["y"]),
                        "action": str(evt["action"]),
                        "ts_ns": int(evt.get("ts_ns", 0)),
                    }) + "\n").encode("utf-8")
                    writer.write(line)
                    await writer.drain()
            except websockets.ConnectionClosed:
                LOG.info("viewer disconnected: /touch")
                writer.close()
                return
        except (ConnectionError, OSError) as exc:
            LOG.warning("phone touch tcp dropped (%s) — reconnect in %.1fs", exc, backoff)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 8.0)


def _make_router(video_queue: "asyncio.Queue[bytes]"):
    async def handler(ws: WebSocketServerProtocol, path: str) -> None:
        if path.startswith("/stream"):
            await _stream_handler(ws, video_queue)
        elif path.startswith("/touch"):
            await _touch_handler(ws)
        else:
            await ws.close(code=1008, reason="unknown path")
    return handler


async def _serve(args: argparse.Namespace) -> None:
    setup_adb_tunnels(args.phone_serial)
    video_queue: "asyncio.Queue[bytes]" = asyncio.Queue(maxsize=256)
    reader_task = asyncio.create_task(_phone_tcp_reader(video_queue))
    ws_server = await websockets.serve(_make_router(video_queue), "localhost", args.port, max_size=None)
    LOG.info("sinister-cast bridge listening on ws://localhost:%d (/stream + /touch)", args.port)
    try:
        await asyncio.Future()
    finally:
        reader_task.cancel()
        ws_server.close()
        await ws_server.wait_closed()


def main() -> int:
    parser = argparse.ArgumentParser(prog="bridge.py", description="SinisterCast PC-side WebSocket bridge.")
    parser.add_argument("--phone-serial", required=True, help="adb device serial (adb devices) — passed as -s to adb")
    parser.add_argument("--port", type=int, default=9002, help="local WebSocket port (default 9002)")
    parser.add_argument("--log", default="INFO", help="log level (DEBUG/INFO/WARNING/ERROR)")
    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log.upper(), logging.INFO),
                        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
                        stream=sys.stderr)
    try:
        asyncio.run(_serve(args))
    except KeyboardInterrupt:
        LOG.info("shutdown on ctrl-c")
    return 0


if __name__ == "__main__":
    sys.exit(main())
