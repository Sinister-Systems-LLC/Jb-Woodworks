# SMOKE TEST — sinister-eve-mcp-bridge.py prototype

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Tester lane:** sinister-os (EVE session)
> **Target:** `scaffold/sinister-eve-mcp-bridge.py` (431 lines, Python stdlib-only)
> **Host:** Windows 10, Python 3.12.10 (cold-start of the prototype before VM packaging)
> **Bind:** 127.0.0.1:7331 (loopback only, per prototype default)
> **Mode:** `--dev` (uses temp dirs + stubbed LLM, no `/var/lib/sinister/` required)

## Overall verdict

**CONDITIONAL GO** — 5/6 endpoints PASS as-shipped. 1 endpoint FAIL caused by a real input-validation bug. One-line patch identified; once applied, the prototype is ready to ship to the CachyOS VM as the EVE service for P3 validation. Without the patch it is still demoable; clients just have to pre-serialize values to strings.

## Environment

| Item | Value |
|---|---|
| Python version | 3.12.10 (script uses no `tomllib`; spec note about 3.11+ is a false alarm) |
| Bridge PID | 33080 |
| RSS at steady state | 25,763,840 bytes (~24.6 MB) |
| Startup time (process-spawn → `listening on...`) | < 0.5 s wall (registry-load → listen socket: 6 ms per timestamps) |
| Tools registered | 2 (`eve-cli`, `panel-control`) → 14 subcommands exposed via `/v1/tools/list` |
| LLM backend | stubbed (`stub: true`, no network call), as designed for `--dev` |
| Memory root (dev) | `C:\Users\Zonia\AppData\Local\Temp\sinister-eve-dev\memory` |

## Endpoint results

### 1. `GET /health` — PASS

```json
{"status": "ok", "uptime_secs": 0.3, "tool_count": 2,
 "memory_root": "C:\\Users\\Zonia\\AppData\\Local\\Temp\\sinister-eve-dev\\memory",
 "llm": {"anthropic_configured": false, "ollama_host": "http://127.0.0.1:11434", "model": "claude-opus-4-7"}}
```

Verdict: PASS. Returns uptime, tool count, memory root, LLM status. Shape matches `EVEDaemon.health()`.

### 2. `GET /v1/tools/list` — PASS

Returned 14 flat `tool.subcommand` rows across the 2 registered tools. Both example configs (`eve-cli.json`, `panel-control.json`) parsed cleanly. Example rows: `eve-cli.status`, `eve-cli.say`, `panel-control.tab.open`, `panel-control.theme.set`. Full list captured in `_smoke-test.log`.

Verdict: PASS.

### 3. `POST /v1/intent/dispatch` — PASS

Body: `{"intent":"check status of docker stack"}`

Response:
```json
{"matched": false, "llm": {"backend": "ollama", "model": "claude-opus-4-7",
 "stub": true, "note": "Prototype does not call the LLM. Rust daemon will. See DESIGN.md sec 2.4.",
 "echo": {"role": "user", "content": "check status of docker stack"}}}
```

No regex in the example configs matches "docker stack", so the bridge correctly fell through to the LLM stub. Utterance was appended to `operator-utterances.jsonl` per `do_POST` line 319-323.

Verdict: PASS. (Note: `llm.backend` reports `ollama` because there is no `ANTHROPIC_API_KEY` set in this shell; that is intended dev fallback in `LLMBackend.chat()` line 250.)

### 4. `POST /v1/memory/set` — FAIL (bug found) → PASS after workaround

Body as specified: `{"key":"test/smoke","value":{"hello":"world"}}` (value is an object)

Response:
```json
{"error": "write() argument must be str, not dict"}
```

Server-side traceback (from `_smoke-test.log`):
```
File "...sinister-eve-mcp-bridge.py", line 315, in do_POST
    self.daemon.memory.set(body["key"], body["value"])
File "...sinister-eve-mcp-bridge.py", line 87, in set
    tmp.write(value)
TypeError: write() argument must be str, not dict
```

**Bug:** `scaffold/sinister-eve-mcp-bridge.py:314-316` accepts the raw JSON body's `value` field and passes it directly into `MemoryStore.set()`, which calls `tmp.write(value)` on line 87. If a client sends a JSON object (the natural shape for structured memory like heartbeats), the write blows up with a 500. The handler should serialize non-string values before persisting, OR the `MemoryStore.set()` signature should accept `str | dict | list` and JSON-encode internally.

Repeating with a string value: `{"key":"test/smoke","value":"{\"hello\":\"world\"}"}` returned `{"ok": true, "key": "test/smoke"}` — confirming the daemon itself works, only the input coercion is missing.

**Proposed one-line patch** (apply before P3 VM bake):

`scaffold/sinister-eve-mcp-bridge.py` line 315 — change:
```python
self.daemon.memory.set(body["key"], body["value"])
```
to:
```python
v = body["value"]
self.daemon.memory.set(body["key"], v if isinstance(v, str) else json.dumps(v, ensure_ascii=False))
```

Verdict for the endpoint as-shipped: **FAIL** (500 on dict value). Workaround verified PASS. Patch is trivial; intentionally NOT applied this turn per "fix in-place if trivial" judgment call — this is structural enough that it merits an explicit commit on a new turn with the no-bullshit doctrine's "tested-before-claimed" gate, so the next session will land the fix + a regression curl-test.

### 5. `GET /v1/memory/get?key=test/smoke` — PASS

After the workaround write succeeded, the read returned:
```json
{"key": "test/smoke", "value": "{\"hello\":\"world\"}"}
```

Atomic-write-then-rename in `MemoryStore.set` (lines 84-92) works on Windows NTFS; `os.replace()` is the cross-platform-correct call.

Verdict: PASS.

### 6. `POST /v1/heartbeat` — PASS

Body: `{"slug":"smoke","ts":"2026-05-24T17:00:00Z"}`

Response: `{"ok": true, "slug": "smoke"}`

Side-effect verification: `GET /v1/memory/get?key=heartbeats/smoke.json` returned:
```json
{"key": "heartbeats/smoke.json",
 "value": "{\n  \"slug\": \"smoke\",\n  \"ts\": 1779642363.3364398,\n  \"payload\": {}\n}"}
```

The handler stomps the client-supplied `ts` ("2026-05-24T17:00:00Z") with `time.time()` (line 342). Not a bug per the current schema, but worth noting: if a per-project lane wants to backfill heartbeats, the API silently drops their timestamp. Document or honor; pick one before P3.

Verdict: PASS (works as coded, minor schema clarity gap).

## Bugs / observations summary

| # | Severity | File:line | Description |
|---|---|---|---|
| 1 | R1 (functional) | `scaffold/sinister-eve-mcp-bridge.py:314-316` | `/v1/memory/set` 500s on dict/list values; needs `json.dumps` coercion. Patch provided above. |
| 2 | R3 (cosmetic / docs) | `scaffold/sinister-eve-mcp-bridge.py:338-344` | `/v1/heartbeat` ignores client `ts` and uses `time.time()`. Either honor it or document the override. |
| 3 | R3 (spec drift) | `DESIGN.md` / task brief | Brief stated the script uses `tomllib` (Python 3.11+). Grep confirms zero `tomllib` imports; only `json` is used to load registry configs. The 3.11+ requirement is currently a non-constraint; the prototype runs on 3.10+ (probably 3.7+ given dataclasses + f-strings). Spec should be updated when the Rust port adds a real `/etc/sinister/eve.toml`. |

## Performance

- Cold-start to listening: < 500 ms (registry parse: 6 ms across 2 JSON files).
- RSS at idle: ~24.6 MB (Python 3.12 baseline; well within budget for an always-on systemd service).
- All 6 curl calls returned in under 50 ms (loopback, no LLM hit).

## GO / NO-GO for VM ship

**GO with patch.** The prototype's surface area (health, tools/list, intent/dispatch, memory/set+get, heartbeat) is real, the JSON drop-in tool registration loop works, and the memory atomic-write survives Windows. The single R1 bug is a 1-line fix; once landed, the next session can package this as `/usr/local/bin/sinister-eve-mcp-bridge` + a `sinister-eve.service` unit and ship it into the CachyOS VM for P3 acceptance.

Suggested next-turn rows:
1. Apply the `/v1/memory/set` JSON-coercion patch + re-run this smoke test, capture identical evidence in `SMOKE-TEST-2026-05-25.md`.
2. Decide heartbeat `ts` semantics; update either handler or DESIGN.md.
3. Add `--bind` smoke-test (already supported via CLI flag line 394-408 but not exercised here).
4. Add a `/v1/tools/call` smoke-test (handler exists at line 311-313; the example tools' `exec` paths won't exist on Windows so the `dry_run` branch on line 190-191 should be exercised).

---

## 2026-05-24 — R1 fixed inline (post-smoke)

Author: RKOJ-ELENO :: 2026-05-24

The `POST /v1/memory/set` 500 on non-string values is patched at `scaffold/sinister-eve-mcp-bridge.py:315` (HTTP handler coerces dict/list/non-str to `json.dumps(v, ensure_ascii=False)` before calling `MemoryStore.set`).

Re-smoke result (single endpoint, same dev mode):
- `POST /v1/memory/set {"key":"test/smoke-postfix","value":{"hello":"world","n":42}}` → `{"ok": true, "key": "test/smoke-postfix"}`
- `GET /v1/memory/get?key=test/smoke-postfix` → returns the JSON-stringified value, round-trip clean

Verdict updated: **FULL GO** for shipping the prototype as `sinister-eve.service` on the CachyOS VM.
