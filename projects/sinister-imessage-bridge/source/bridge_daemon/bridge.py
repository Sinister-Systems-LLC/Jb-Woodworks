"""Bridge daemon HTTP API.

RKOJ-ELENO :: 2026-05-24 :: phase P3 (stubbed; runnable on Windows for dashboard
development — answers from a canned chat.db until the farm comes online).

Endpoints:
  GET  /status                                 → daemon health snapshot
  GET  /threads                                → all threads with last 50 msgs each
  GET  /threads/{chat_id}/messages?limit=50    → message stream for one thread
  POST /send                                   → send a message (requires operator_ok)
  GET  /events                                 → SSE stream of new inbound msgs (TODO real-tail)

The dashboard UI (Next.js, dashboard-skeleton inheritance) talks to this on
127.0.0.1:8731 during dev.
"""
from __future__ import annotations

import asyncio
import json
import os
import time
from pathlib import Path

from aiohttp import web

from recv_worker.poll import fetch_threads
from send_worker.send import send as send_msg

DEFAULT_CHATDB = Path(os.environ.get(
    "IMESSAGE_CHATDB",
    str(Path(__file__).resolve().parents[2] / "source" / "fixtures" / "canned-chat.db"),
))
DEFAULT_PORT = int(os.environ.get("IMESSAGE_BRIDGE_PORT", "8731"))
DEFAULT_HOST = "127.0.0.1"


def make_app(chatdb_path: Path = DEFAULT_CHATDB) -> web.Application:
    app = web.Application()
    app["chatdb_path"] = chatdb_path
    app["boot_unix"] = time.time()
    app.router.add_get("/status", http_status)
    app.router.add_get("/threads", http_threads)
    app.router.add_get("/threads/{chat_id}/messages", http_thread_messages)
    app.router.add_post("/send", http_send)
    app.router.add_get("/events", http_events_sse)
    return app


async def http_status(request: web.Request) -> web.Response:
    chatdb = request.app["chatdb_path"]
    return web.json_response({
        "ok": True,
        "phase": "P0-scaffold",
        "chatdb_path": str(chatdb),
        "chatdb_exists": chatdb.exists(),
        "uptime_sec": int(time.time() - request.app["boot_unix"]),
        "farm_ssh": "not_connected",
        "tail_alive": False,
        "send_queue_depth": 0,
    })


async def http_threads(request: web.Request) -> web.Response:
    chatdb = request.app["chatdb_path"]
    if not chatdb.exists():
        return web.json_response({"threads": [], "warning": "chatdb missing"}, status=200)
    threads = await asyncio.to_thread(fetch_threads, chatdb, 50)
    return web.json_response({"threads": threads})


async def http_thread_messages(request: web.Request) -> web.Response:
    chat_id = int(request.match_info["chat_id"])
    limit = int(request.query.get("limit", 50))
    chatdb = request.app["chatdb_path"]
    if not chatdb.exists():
        return web.json_response({"messages": [], "warning": "chatdb missing"})
    all_threads = await asyncio.to_thread(fetch_threads, chatdb, limit)
    for t in all_threads:
        if t["chat_id"] == chat_id:
            return web.json_response({"thread": t})
    return web.json_response({"error": f"chat_id {chat_id} not found"}, status=404)


async def http_send(request: web.Request) -> web.Response:
    body = await request.json()
    required = {"service", "recipient", "body"}
    missing = required - set(body)
    if missing:
        return web.json_response({"status": "blocked", "reason": f"missing fields: {sorted(missing)}"}, status=400)
    result = await asyncio.to_thread(
        send_msg,
        body["service"],
        body["recipient"],
        body["body"],
        operator_ok=bool(body.get("operator_ok", False)),
        dry_run=bool(body.get("dry_run", False)),
    )
    status = 200 if result.get("status") in ("ok", "dry_run") else 403
    return web.json_response(result, status=status)


async def http_events_sse(request: web.Request) -> web.StreamResponse:
    """SSE stream stub — emits one keep-alive every 15s until the real tail lands.

    When P3 tail is wired in, this drains an asyncio.Queue fed by the tail proc.
    """
    resp = web.StreamResponse(
        status=200,
        reason="OK",
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
    await resp.prepare(request)
    try:
        while True:
            payload = {"type": "keepalive", "ts_unix": time.time()}
            await resp.write(f"data: {json.dumps(payload)}\n\n".encode())
            await asyncio.sleep(15)
    except (asyncio.CancelledError, ConnectionResetError):
        pass
    return resp


def main() -> int:
    import argparse
    p = argparse.ArgumentParser(description="Sinister iMessage Bridge daemon.")
    p.add_argument("--chatdb", default=str(DEFAULT_CHATDB), help="Path to chat.db (canned or real)")
    p.add_argument("--host", default=DEFAULT_HOST)
    p.add_argument("--port", default=DEFAULT_PORT, type=int)
    args = p.parse_args()
    app = make_app(Path(args.chatdb))
    print(f"[bridge] listening on http://{args.host}:{args.port} (chatdb={args.chatdb})")
    web.run_app(app, host=args.host, port=args.port, print=None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
