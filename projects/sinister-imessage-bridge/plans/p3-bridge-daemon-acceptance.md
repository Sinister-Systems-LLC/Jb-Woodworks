# P3 — Bridge daemon acceptance plan

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Phase:** P3 (always-on daemon — polls inbound via FSEvents, posts to sinister-bus, surfaces to dashboard UI)
> **Unlock condition:** P2 (`plans/p2-send-acceptance.md`) is `acceptance-tested` PASS
> **Estimated bench time:** 2–4 h once P2 closes

P3 is the first phase that produces a long-running service. Everything before P3 was per-invocation scripts; P3 is a daemon the operator can leave running.

---

## 0. Architecture (binding)

```
                              ┌──────────────────────────────┐
                              │  bridge_daemon (Python)       │
                              │  • supervises tail.py         │
                              │  • supervises send_queue      │
                              │  • exposes HTTP API :8731     │
                              │  • posts to sinister-bus      │
                              └──────────────────────────────┘
                                ▲                          ▲
                                │ (mac farm SSH tunnel)    │ (local HTTP)
                                │                          │
   ┌────────────────────┐       │      ┌─────────────────────────┐
   │ recv_worker/tail.py│───────┘      │  dashboard UI (I4)       │
   │ FSEvents on        │              │  on Next.js dashboard-   │
   │ chat.db-wal        │              │  skeleton, purple accent │
   └────────────────────┘              └─────────────────────────┘
                                                  │
                                                  ▼
                                       ┌────────────────────────┐
                                       │  sinister-bus daemon   │
                                       │  org.sinister.Bus.*    │
                                       └────────────────────────┘
```

Three processes total:
1. `bridge_daemon` — main supervisor, owns the HTTP API + send queue. Runs on operator's Windows OR on a Linux/Mac box that has Tailscale to the farm. Talks to farm via SSH.
2. `recv_worker/tail.py` — sub-process spawned by bridge_daemon over SSH to the farm. Watches `chat.db-wal` via `fswatch` (mac) and emits one line per new message to stdout. Bridge_daemon parses each line and dispatches.
3. `send_worker/send.py` — invoked per outbound message. Already shipped at P2.

---

## 1. recv_worker/tail.py — live tail

```python
# source/recv_worker/tail.py :: RKOJ-ELENO :: 2026-05-24
# Runs ON THE FARM, spawned over SSH by bridge_daemon.
# Watches chat.db-wal; on each change polls the last 10 messages and emits
# JSON lines for any with ROWID > last-seen.
import sqlite3, json, time, sys, subprocess, pathlib

DB = pathlib.Path.home() / "Library" / "Messages" / "chat.db"
WAL = DB.with_suffix(".db-wal")
POLL_INTERVAL = 0.5  # secs between fsevent batches

def last_rowid(conn) -> int:
    row = conn.execute("SELECT COALESCE(MAX(ROWID), 0) FROM message").fetchone()
    return row[0]

def emit_new(conn, since: int) -> int:
    rows = conn.execute("""
        SELECT m.ROWID, m.date, m.is_from_me, m.service, h.id, m.text
        FROM message m LEFT JOIN handle h ON m.handle_id = h.ROWID
        WHERE m.ROWID > ? ORDER BY m.ROWID ASC LIMIT 50
    """, (since,)).fetchall()
    for row in rows:
        rowid, date, is_from_me, service, handle, text = row
        # Apple-epoch ns → unix s
        sent_unix = (date / 1_000_000_000) + 978_307_200
        sys.stdout.write(json.dumps({
            "rowid": rowid, "sent_unix": sent_unix, "is_from_me": is_from_me,
            "service": service, "handle": handle, "body": text
        }) + "\n")
        sys.stdout.flush()
        since = rowid
    return since

def main():
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=5)
    cur_last = last_rowid(conn)
    # fswatch -e events; we re-poll DB on each.
    proc = subprocess.Popen(["fswatch", "-1", str(WAL)], stdout=subprocess.PIPE, text=True)
    while True:
        proc.stdout.readline()  # blocks until WAL changes
        cur_last = emit_new(conn, cur_last)
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
```

**Why this shape:**
- `mode=ro` opens read-only — chat.db is owned by Messages.app; we MUST NOT take any write lock.
- `fswatch -1` blocks on WAL changes (much cheaper than polling every 500ms unconditionally).
- Emits JSON-per-line to stdout → bridge_daemon parses each line.
- Body INCLUDED in output (no longer just metadata — this is the bridge). bridge_daemon decides whether to persist + redact per contact-policy.

---

## 2. bridge_daemon — supervisor + HTTP API

```python
# source/bridge_daemon/bridge.py :: RKOJ-ELENO :: 2026-05-24
import asyncio, subprocess, json, logging
from aiohttp import web

API_PORT = 8731

async def tail_subprocess(state):
    ssh = ["ssh", state.farm_host, "python3", "/path/to/tail.py"]
    proc = await asyncio.create_subprocess_exec(*ssh, stdout=asyncio.subprocess.PIPE)
    async for line in proc.stdout:
        try:
            msg = json.loads(line)
            await dispatch_inbound(msg, state)
        except json.JSONDecodeError:
            logging.warning("malformed tail line: %r", line)

async def dispatch_inbound(msg, state):
    if msg["is_from_me"] == 1:
        return  # do not bus-post our own sends
    state.recent.appendleft(msg)
    if len(state.recent) > 500:
        state.recent.pop()
    # bus emit (replace with org.sinister.Bus on sinister-os):
    await state.bus_emit("iMessageReceived", msg)

async def http_threads(request):
    state = request.app["state"]
    threads = {}
    for m in state.recent:
        threads.setdefault(m["handle"], []).append(m)
    return web.json_response({"threads": threads})

async def http_send(request):
    state = request.app["state"]
    body = await request.json()
    if not body.get("operator_ok"):
        return web.json_response({"status": "blocked", "reason": "operator_ok=False"}, status=403)
    # delegate to send_worker.send.send(...)
    ...
```

**API surface (P3 minimum):**
- `GET /threads` — recent threads, grouped by handle
- `GET /threads/{handle}/messages?limit=50` — message stream for one thread
- `POST /send` — send a message; body `{ service, recipient, body, operator_ok }`
- `GET /status` — daemon health (farm SSH up? recv tail alive? send_queue depth?)
- `GET /events` — Server-Sent-Events stream of new inbound messages (the dashboard subscribes here)

---

## 3. sinister-bus integration

On Sinister OS, the bus is `org.sinister.Bus` DBus. Until OS-side lands, P3 emits `inbox/<lane>/<ts>-from-imessage-bridge-<event>.json` messages via the standard sanctum cross-agent surface. Other lanes opt in by polling their inbox or subscribing to the bus.

```python
async def bus_emit(event: str, payload: dict):
    # Sinister OS path:
    # await dbus_call("org.sinister.Bus", "/imessage", "Emit", event, payload)
    # Sanctum fallback:
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H%MZ")
    out = SANCTUM / "_shared-memory" / "cross-agent" / f"{ts}-from-imessage-{event}.json"
    out.write_text(json.dumps({"event": event, "ts_utc": ts, **payload}))
```

**Subscribers expected at P3 unlock (lanes already in fleet):**
- `sanctum` — surface "inbound iMessage from <handle>" in operator queue (high-priority for unknown handles)
- `forge` — Forge memory recall (suggest reply per persona, NO auto-send)
- `vault` — append to nightly backup of `chat.db`
- `mind` — graph node/edge update for the contact

---

## 4. Acceptance criteria — what makes P3 a PASS

P3 is `acceptance-tested` (per no-bullshit doctrine §1) when **all** of the following land in one PROGRESS row with command + exit code + per-step ts:

- [ ] `source/recv_worker/tail.py` committed; runs on farm via `ssh <farm> python3 tail.py` and emits at least one JSON line when operator sends a test message from the 2nd device (turnaround <3s)
- [ ] `source/bridge_daemon/bridge.py` committed; runs on Windows + supervises the SSH tail + serves HTTP :8731
- [ ] `curl http://localhost:8731/status` → 200 + JSON `{"farm_ssh": "up", "tail_alive": true, "send_queue_depth": 0}`
- [ ] `curl http://localhost:8731/threads` → 200 + JSON with at least one thread populated from chat.db
- [ ] `curl -N http://localhost:8731/events` → SSE stream emits a new event within 3s of operator sending a fresh message from 2nd device
- [ ] One `cross-agent/<ts>-from-imessage-iMessageReceived.json` file lands on inbound (verifies bus emit path)
- [ ] Pytest at `source/tests/test_dispatch.py` → all 6 mock-dispatch tests pass on Windows (no farm required)
- [ ] Brain entry `_shared-memory/knowledge/imessage-bridge-p3-daemon-2026-MM-DD.md` summarizing observed latency + FSEvents quirks

---

## 5. Safety + reversibility wall

| Risk | Mitigation |
|---|---|
| Daemon crash leaves orphan SSH proc on farm | bridge_daemon registers SIGTERM handler that kills the ssh subprocess; systemd-style PIDfile |
| chat.db-wal under heavy write contention with Messages.app | `mode=ro` + `timeout=5` + ignore-on-OperationalError; missed events caught on next poll |
| Bus subscribers fire arbitrary code on inbound | bus payload contains body — subscribers MUST treat body as untrusted text; never `eval`, never `subprocess.run(body, shell=True)` |
| HTTP API exposed beyond localhost | bind to `127.0.0.1` only; require `Authorization: Bearer <token>` from vault for `/send` |
| SSE stream consumer accumulating in memory | server-side cap at 500 messages in `state.recent`; dashboard re-fetches if it falls behind |

---

## 6. After P3 PASS — what's next

- Open `agent/sinister-imessage-bridge/p4-cross-lane-<date>` branch
- Per-lane wiring (operator-gated, one lane per session): vault backup, mind graph update, forge reply-suggestions, showmasters client-thread routing
- Land first auto-respond rule (operator-curated, single contact, single trigger pattern) — this is the FIRST time the bridge sends without per-message operator OK
