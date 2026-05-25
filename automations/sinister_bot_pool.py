#!/usr/bin/env python3
"""sinister_bot_pool.py -- shared bot pool daemon for all Sinister Sanctum sessions.

Author: RKOJ-ELENO :: 2026-05-25

Operator hard-canonical 2026-05-25 (verbatim):
    "have each bot work for all and as there is more demand per that bot at that
     time to allow for efficient use. use the fucking jcode log system. we have
     the bloody code"

What it does:
    Runs a shared HTTP daemon on port 17340 so every terminal session / agent
    queries the SAME set of Ollama bot workers instead of each spawning their
    own Ollama connection. Demand is tracked per bot and per caller_slug.
    If >3 requests are queued for a bot a scale-up event is logged (Ollama
    handles native concurrency, so the log is the action hook for future
    multi-GPU expansion).

    Every request + response is written to
    _shared-memory/bot-pool-session.jsonl in jcode JSONL format (same schema
    as Claude Code JSONL sessions: type / uuid / sessionId / timestamp /
    content).

Endpoints:
    POST /query   body: {bot, query, caller_slug}  -> {response, bot, model, duration_s}
    GET  /status  -> {bots, demand, queue_depths, uptime_s}
    GET  /health  -> {healthy, ollama_reachable, uptime_s}

Bot types:
    librarian  -- RAG / code search  (qwen2.5-coder:7b)
    triage     -- classify / route   (qwen2.5-coder:7b)
    researcher -- summarise / digest (qwen2.5-coder:7b)

CLI:
    --start           launch daemon (blocks; use schtask or nohup)
    --stop            send SIGTERM to PID file process
    --status          print JSON status from running daemon (or error)
    --install-schtask register SinisterBotPool logon schtask (user-level)

Doctrine:
    NO new .bat / NO new .ps1 (operator 2026-05-25T02:45Z).
    Operator clicks nothing (operator 2026-05-25 ~02:55Z).
    Author RKOJ-ELENO on every new file (operator 2026-05-21).
    jcode log format (operator 2026-05-25).
    We have the source: logging schema derived from
        C:\\Users\\Zonia\\Desktop\\jcode-0.12.4\\crates\\jcode-import-core\\src\\lib.rs
        (ClaudeCodeEntry struct, camelCase fields).

Composes with:
    automations/gpu_bot_fleet.py       -- Ollama reachability + model detection
    automations/bot_pool_client.py     -- thin client used by every agent
    _shared-memory/bot-pool-session.jsonl  -- jcode-format JSONL audit log
    _shared-memory/knowledge/shared-bot-pool-doctrine-2026-05-25.md
"""

from __future__ import annotations

import argparse
import json
import os
import queue
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Config / paths
# ---------------------------------------------------------------------------

SANCTUM_ROOT = Path(os.environ.get("SINISTER_SANCTUM_ROOT", r"D:\Sinister Sanctum"))
LOG_JSONL = SANCTUM_ROOT / "_shared-memory" / "bot-pool-session.jsonl"
PID_FILE = SANCTUM_ROOT / "_shared-memory" / "bot-pool.pid"

POOL_HOST = "127.0.0.1"
POOL_PORT = 17340
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/")
REQUEST_TIMEOUT_S = 90
SCALE_UP_THRESHOLD = 3  # queue depth that triggers a scale-up log event

# Bot -> preferred Ollama model (in priority order)
BOT_MODEL_PREFS: dict[str, list[str]] = {
    "librarian": [
        "qwen2.5-coder:7b",
        "qwen2.5:7b",
        "llama3.1:8b",
        "llama3:8b",
        "mistral:7b",
    ],
    "triage": [
        "qwen2.5-coder:7b",
        "qwen2.5:7b",
        "llama3.1:8b",
        "llama3:8b",
        "mistral:7b",
    ],
    "researcher": [
        "qwen2.5-coder:7b",
        "qwen2.5:7b",
        "llama3.1:8b",
        "llama3:8b",
        "mistral:7b",
    ],
}

BOT_SYSTEM_PROMPTS: dict[str, str] = {
    "librarian": (
        "You are the Sinister Sanctum Librarian bot. Your job is to search, "
        "retrieve, and answer questions about code, docs, and project knowledge. "
        "Be precise, cite file paths when possible, and keep responses concise."
    ),
    "triage": (
        "You are the Sinister Sanctum Triage bot. Your job is to classify "
        "incoming requests and route them to the correct lane or agent. "
        "Respond with a JSON object: {lane, priority, reason}."
    ),
    "researcher": (
        "You are the Sinister Sanctum Researcher bot. Your job is to summarise "
        "documents, distil key facts, and produce concise digests. "
        "Keep your output structured and scannable."
    ),
}

VALID_BOTS = set(BOT_MODEL_PREFS.keys())

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_start_time = time.time()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _http_get(url: str, timeout: int = 5) -> tuple[int, str]:
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace") if hasattr(exc, "read") else ""
        return exc.code, body
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return 0, str(exc)


def _http_post(url: str, body: dict[str, Any], timeout: int = REQUEST_TIMEOUT_S) -> tuple[int, str]:
    try:
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace") if hasattr(exc, "read") else ""
        return exc.code, body
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return 0, str(exc)


def detect_ollama_models() -> list[str]:
    """Return list of pulled Ollama model names (empty on failure)."""
    status, body = _http_get(f"{OLLAMA_URL}/api/tags", timeout=4)
    if status != 200:
        return []
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return []
    return [m.get("name", "") for m in payload.get("models", []) if m.get("name")]


def pick_model(bot: str, available: list[str]) -> str | None:
    prefs = BOT_MODEL_PREFS.get(bot, [])
    for pref in prefs:
        for name in available:
            if name == pref or name.startswith(pref):
                return name
    return available[0] if available else None


# ---------------------------------------------------------------------------
# jcode-format JSONL logger
# ---------------------------------------------------------------------------

class _JcodeLogger:
    """Write bot pool events to a JSONL file using jcode's ClaudeCodeEntry schema.

    jcode schema (from jcode-import-core/src/lib.rs ClaudeCodeEntry, camelCase):
        type        -- "user" | "assistant" | "tool_use" | "system_event"
        uuid        -- unique event ID
        parentUuid  -- for response entries, references the request uuid
        sessionId   -- daemon session ID (stable across daemon lifetime)
        timestamp   -- ISO-8601 UTC string
        isSidechain -- always false for bot pool entries
        content     -- arbitrary dict with event payload
    """

    _lock = threading.Lock()

    def __init__(self) -> None:
        self._session_id = f"bot-pool-{uuid.uuid4().hex[:12]}"
        LOG_JSONL.parent.mkdir(parents=True, exist_ok=True)

    @property
    def session_id(self) -> str:
        return self._session_id

    def _write(self, entry: dict[str, Any]) -> None:
        try:
            with self._lock:
                with LOG_JSONL.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass  # logging must never crash the daemon

    def log_request(
        self,
        *,
        bot: str,
        query: str,
        caller_slug: str,
        request_id: str,
    ) -> None:
        entry: dict[str, Any] = {
            "type": "user",
            "uuid": request_id,
            "parentUuid": None,
            "sessionId": self._session_id,
            "timestamp": utc_now_iso(),
            "isSidechain": False,
            "content": {
                "role": "user",
                "bot": bot,
                "caller_slug": caller_slug,
                "query": query[:2000],  # truncate for log hygiene
            },
        }
        self._write(entry)

    def log_response(
        self,
        *,
        bot: str,
        model: str | None,
        response: str,
        caller_slug: str,
        request_id: str,
        duration_s: float,
        error: str | None = None,
    ) -> None:
        entry: dict[str, Any] = {
            "type": "assistant",
            "uuid": uuid.uuid4().hex,
            "parentUuid": request_id,
            "sessionId": self._session_id,
            "timestamp": utc_now_iso(),
            "isSidechain": False,
            "content": {
                "role": "assistant",
                "bot": bot,
                "caller_slug": caller_slug,
                "model": model,
                "duration_s": round(duration_s, 3),
                "response": response[:4000],
                "error": error,
            },
        }
        self._write(entry)

    def log_system_event(self, event: str, **kwargs: Any) -> None:
        entry: dict[str, Any] = {
            "type": "tool_use",
            "uuid": uuid.uuid4().hex,
            "parentUuid": None,
            "sessionId": self._session_id,
            "timestamp": utc_now_iso(),
            "isSidechain": False,
            "content": {
                "event": event,
                **{k: v for k, v in kwargs.items()},
            },
        }
        self._write(entry)


# ---------------------------------------------------------------------------
# Demand tracker
# ---------------------------------------------------------------------------

class _DemandTracker:
    """Thread-safe counters: total requests + in-flight queue depth per bot/caller."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # {bot: {"total": int, "in_flight": int, "by_caller": {slug: int}}}
        self._data: dict[str, dict[str, Any]] = {
            bot: {"total": 0, "in_flight": 0, "by_caller": {}}
            for bot in VALID_BOTS
        }

    def enter(self, bot: str, caller_slug: str) -> int:
        """Record a new in-flight request. Returns current queue depth."""
        with self._lock:
            rec = self._data.setdefault(
                bot, {"total": 0, "in_flight": 0, "by_caller": {}}
            )
            rec["total"] += 1
            rec["in_flight"] += 1
            rec["by_caller"][caller_slug] = rec["by_caller"].get(caller_slug, 0) + 1
            return rec["in_flight"]

    def exit(self, bot: str) -> None:
        with self._lock:
            rec = self._data.get(bot)
            if rec and rec["in_flight"] > 0:
                rec["in_flight"] -= 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return json.loads(json.dumps(self._data))


# ---------------------------------------------------------------------------
# Ollama query engine
# ---------------------------------------------------------------------------

_demand = _DemandTracker()
_logger: _JcodeLogger | None = None
_available_models: list[str] = []
_models_lock = threading.Lock()
_models_refresh_ts: float = 0.0
MODELS_REFRESH_INTERVAL = 60  # seconds


def _refresh_models_if_stale() -> list[str]:
    global _available_models, _models_refresh_ts
    with _models_lock:
        if time.time() - _models_refresh_ts > MODELS_REFRESH_INTERVAL:
            _available_models = detect_ollama_models()
            _models_refresh_ts = time.time()
        return list(_available_models)


def _call_ollama(bot: str, query: str) -> tuple[str | None, str | None, float]:
    """Query Ollama. Returns (response_text, model_used, duration_s)."""
    available = _refresh_models_if_stale()
    model = pick_model(bot, available)
    if model is None:
        return None, None, 0.0

    system_prompt = BOT_SYSTEM_PROMPTS.get(bot, "")
    body: dict[str, Any] = {
        "model": model,
        "prompt": query,
        "system": system_prompt,
        "stream": False,
    }
    t0 = time.time()
    status, resp_body = _http_post(f"{OLLAMA_URL}/api/generate", body, timeout=REQUEST_TIMEOUT_S)
    duration_s = time.time() - t0

    if status != 200:
        return None, model, duration_s

    try:
        payload = json.loads(resp_body)
    except json.JSONDecodeError:
        return None, model, duration_s

    return payload.get("response", ""), model, duration_s


def handle_query(bot: str, query: str, caller_slug: str) -> dict[str, Any]:
    """Route a query through the bot pool. Thread-safe."""
    assert _logger is not None, "daemon not started"

    request_id = uuid.uuid4().hex
    _logger.log_request(bot=bot, query=query, caller_slug=caller_slug, request_id=request_id)

    depth = _demand.enter(bot, caller_slug)
    if depth > SCALE_UP_THRESHOLD:
        _logger.log_system_event(
            "scale_up",
            bot=bot,
            queue_depth=depth,
            note="Ollama handles native concurrency; log is hook for future multi-GPU expansion",
        )

    try:
        response_text, model, duration_s = _call_ollama(bot, query)
    except Exception as exc:
        _demand.exit(bot)
        err = str(exc)
        _logger.log_response(
            bot=bot,
            model=None,
            response="",
            caller_slug=caller_slug,
            request_id=request_id,
            duration_s=0.0,
            error=err,
        )
        return {"error": err, "bot": bot, "caller_slug": caller_slug}
    finally:
        _demand.exit(bot)

    if response_text is None:
        err = f"Ollama returned no response for bot={bot} model={model}"
        _logger.log_response(
            bot=bot,
            model=model,
            response="",
            caller_slug=caller_slug,
            request_id=request_id,
            duration_s=duration_s,
            error=err,
        )
        return {"error": err, "bot": bot, "caller_slug": caller_slug, "model": model}

    _logger.log_response(
        bot=bot,
        model=model,
        response=response_text,
        caller_slug=caller_slug,
        request_id=request_id,
        duration_s=duration_s,
    )
    return {
        "response": response_text,
        "bot": bot,
        "model": model,
        "duration_s": round(duration_s, 3),
        "caller_slug": caller_slug,
    }


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------

class _PoolHandler(BaseHTTPRequestHandler):
    """Minimal HTTP handler for the bot pool endpoints."""

    def log_message(self, fmt: str, *args: Any) -> None:  # silence access log
        pass

    def _send_json(self, code: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/health":
            _, body = _http_get(f"{OLLAMA_URL}/api/tags", timeout=4)
            reachable = True
            try:
                json.loads(body)
            except Exception:
                reachable = False
            # Re-check properly
            status, _ = _http_get(f"{OLLAMA_URL}/api/tags", timeout=4)
            reachable = status == 200
            self._send_json(200, {
                "healthy": reachable,
                "ollama_reachable": reachable,
                "uptime_s": round(time.time() - _start_time, 1),
                "port": POOL_PORT,
            })
        elif self.path == "/status":
            demand = _demand.snapshot()
            available = _refresh_models_if_stale()
            self._send_json(200, {
                "bots": list(VALID_BOTS),
                "demand": demand,
                "available_models": available,
                "uptime_s": round(time.time() - _start_time, 1),
                "port": POOL_PORT,
                "log_file": str(LOG_JSONL),
            })
        else:
            self._send_json(404, {"error": "not found", "path": self.path})

    def do_POST(self) -> None:
        if self.path != "/query":
            self._send_json(404, {"error": "not found", "path": self.path})
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)
            body = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            self._send_json(400, {"error": f"bad request body: {exc}"})
            return

        bot = body.get("bot", "")
        query = body.get("query", "")
        caller_slug = body.get("caller_slug", "unknown")

        if bot not in VALID_BOTS:
            self._send_json(400, {"error": f"unknown bot '{bot}'; valid: {sorted(VALID_BOTS)}"})
            return
        if not query:
            self._send_json(400, {"error": "query must not be empty"})
            return

        result = handle_query(bot, query, caller_slug)
        code = 200 if "error" not in result else 502
        self._send_json(code, result)


# ---------------------------------------------------------------------------
# Daemon lifecycle
# ---------------------------------------------------------------------------

def _write_pid() -> None:
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")


def _read_pid() -> int | None:
    try:
        return int(PID_FILE.read_text(encoding="utf-8").strip())
    except Exception:
        return None


def cmd_start() -> int:
    global _logger
    _logger = _JcodeLogger()
    _logger.log_system_event(
        "daemon_start",
        port=POOL_PORT,
        ollama_url=OLLAMA_URL,
        bots=list(VALID_BOTS),
        pid=os.getpid(),
    )

    _write_pid()
    _refresh_models_if_stale()

    server = HTTPServer((POOL_HOST, POOL_PORT), _PoolHandler)

    def _handle_signal(sig: int, _frame: Any) -> None:
        _logger.log_system_event("daemon_stop", signal=sig, pid=os.getpid())
        try:
            PID_FILE.unlink(missing_ok=True)
        except Exception:
            pass
        server.shutdown()

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    print(
        f"[sinister_bot_pool] daemon listening on http://{POOL_HOST}:{POOL_PORT} "
        f"| log={LOG_JSONL}",
        flush=True,
    )
    server.serve_forever()
    return 0


def cmd_stop() -> int:
    pid = _read_pid()
    if pid is None:
        print("sinister_bot_pool: no PID file found; daemon may not be running", file=sys.stderr)
        return 1
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/F"],
                check=True,
                capture_output=True,
            )
        else:
            os.kill(pid, signal.SIGTERM)
        print(f"sinister_bot_pool: sent stop signal to PID {pid}")
        PID_FILE.unlink(missing_ok=True)
        return 0
    except (ProcessLookupError, subprocess.CalledProcessError) as exc:
        print(f"sinister_bot_pool: could not stop PID {pid}: {exc}", file=sys.stderr)
        PID_FILE.unlink(missing_ok=True)
        return 1


def cmd_status() -> int:
    status_code, body = _http_get(f"http://{POOL_HOST}:{POOL_PORT}/status", timeout=4)
    if status_code == 0:
        print(f"sinister_bot_pool: daemon not reachable on port {POOL_PORT} ({body})")
        return 1
    try:
        print(json.dumps(json.loads(body), indent=2))
    except Exception:
        print(body)
    return 0


def cmd_install_schtask() -> int:
    """Register SinisterBotPool as a user-level logon schtask (no elevation)."""
    python_exe = sys.executable
    this_script = str(Path(__file__).resolve())

    # Build the schtasks command — user-level (no /RU SYSTEM, no elevation)
    task_name = "SinisterBotPool"
    action_args = f'"{python_exe}" "{this_script}" --start'

    # Delete existing task if present (ignore error)
    subprocess.run(
        ["schtasks", "/Delete", "/TN", task_name, "/F"],
        capture_output=True,
    )

    proc = subprocess.run(
        [
            "schtasks",
            "/Create",
            "/TN", task_name,
            "/TR", action_args,
            "/SC", "ONLOGON",
            "/DELAY", "0000:30",
            "/F",
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0:
        print(f"sinister_bot_pool: SinisterBotPool schtask registered (ONLOGON, user-level)")
        return 0
    else:
        # Fallback: PowerShell Register-ScheduledTask (user-level, no elevation)
        ps_cmd = (
            f"$action = New-ScheduledTaskAction -Execute '{python_exe}' "
            f"-Argument '\"{this_script}\" --start'; "
            "$trigger = New-ScheduledTaskTrigger -AtLogOn; "
            "$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable; "
            f"Register-ScheduledTask -TaskName '{task_name}' "
            "-Action $action -Trigger $trigger -Settings $settings -Force | Out-Null; "
            f"Write-Output 'SinisterBotPool registered'"
        )
        ps_proc = subprocess.run(
            ["powershell", "-NonInteractive", "-Command", ps_cmd],
            capture_output=True,
            text=True,
        )
        if ps_proc.returncode == 0:
            print(f"sinister_bot_pool: SinisterBotPool schtask registered via PowerShell")
            return 0
        else:
            print(
                f"sinister_bot_pool: schtask install failed\n"
                f"  schtasks stderr: {proc.stderr.strip()}\n"
                f"  powershell stderr: {ps_proc.stderr.strip()}",
                file=sys.stderr,
            )
            return 2


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Sinister Bot Pool daemon — shared Ollama bot workers for all sessions"
    )
    p.add_argument("--start", action="store_true", help="start the daemon (blocks)")
    p.add_argument("--stop", action="store_true", help="stop the running daemon")
    p.add_argument("--status", action="store_true", help="print status from running daemon")
    p.add_argument(
        "--install-schtask",
        action="store_true",
        help="register SinisterBotPool ONLOGON schtask (user-level, no elevation)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.install_schtask:
        return cmd_install_schtask()
    if args.stop:
        return cmd_stop()
    if args.status:
        return cmd_status()
    # default + --start
    return cmd_start()


if __name__ == "__main__":
    sys.exit(main())
