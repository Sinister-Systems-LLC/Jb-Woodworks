#!/usr/bin/env python3
"""bot_pool_client.py -- thin client for the Sinister Bot Pool daemon.

Author: RKOJ-ELENO :: 2026-05-25

Usage (library):
    from automations.bot_pool_client import query

    answer = query("librarian", "what does gpu_bot_fleet.py do?", caller_slug="sanctum-helper-A")
    print(answer)

If the daemon is not reachable the client falls back to a direct Ollama call
so callers never need to check daemon health themselves.

Composes with:
    automations/sinister_bot_pool.py  -- the daemon this client talks to
    automations/gpu_bot_fleet.py      -- Ollama model detection used in fallback
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

POOL_HOST = "127.0.0.1"
POOL_PORT = 17340
POOL_BASE = f"http://{POOL_HOST}:{POOL_PORT}"

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/")
REQUEST_TIMEOUT_S = 90

# Mirror of daemon prefs so fallback can pick a sensible model
_FALLBACK_MODEL_PREFS = [
    "qwen2.5-coder:7b",
    "qwen2.5:7b",
    "llama3.1:8b",
    "llama3:8b",
    "mistral:7b",
    "phi3:medium",
]

_FALLBACK_SYSTEM_PROMPTS: dict[str, str] = {
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


# ---------------------------------------------------------------------------
# Internal HTTP helpers
# ---------------------------------------------------------------------------

def _http_get(url: str, timeout: int = 4) -> tuple[int, str]:
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


# ---------------------------------------------------------------------------
# Daemon probe + pool query
# ---------------------------------------------------------------------------

def _daemon_reachable(timeout: int = 2) -> bool:
    code, _ = _http_get(f"{POOL_BASE}/health", timeout=timeout)
    return code == 200


def _query_pool(bot: str, prompt: str, caller_slug: str) -> str | None:
    """POST to daemon /query. Returns response string or None on failure."""
    payload = {"bot": bot, "query": prompt, "caller_slug": caller_slug}
    code, body = _http_post(f"{POOL_BASE}/query", payload, timeout=REQUEST_TIMEOUT_S)
    if code != 200:
        return None
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return None
    return data.get("response")


# ---------------------------------------------------------------------------
# Fallback: direct Ollama call
# ---------------------------------------------------------------------------

def _detect_ollama_models() -> list[str]:
    code, body = _http_get(f"{OLLAMA_URL}/api/tags", timeout=4)
    if code != 200:
        return []
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return []
    return [m.get("name", "") for m in payload.get("models", []) if m.get("name")]


def _pick_fallback_model(available: list[str]) -> str | None:
    for pref in _FALLBACK_MODEL_PREFS:
        for name in available:
            if name == pref or name.startswith(pref):
                return name
    return available[0] if available else None


def _query_ollama_direct(bot: str, prompt: str) -> str:
    """Direct Ollama call used when daemon is unreachable."""
    available = _detect_ollama_models()
    model = _pick_fallback_model(available)
    if model is None:
        return f"[bot_pool_client fallback] Ollama unreachable and no models available for bot={bot}"

    system_prompt = _FALLBACK_SYSTEM_PROMPTS.get(bot, "")
    body: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False,
    }
    code, resp_body = _http_post(f"{OLLAMA_URL}/api/generate", body, timeout=REQUEST_TIMEOUT_S)
    if code != 200:
        return f"[bot_pool_client fallback] Ollama HTTP {code} for bot={bot} model={model}"
    try:
        data = json.loads(resp_body)
    except json.JSONDecodeError:
        return f"[bot_pool_client fallback] non-JSON response from Ollama for bot={bot}"
    return data.get("response", "")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def query(
    bot: str,
    prompt: str,
    caller_slug: str = "unknown",
    *,
    fallback: bool = True,
) -> str:
    """Query a bot through the shared pool daemon.

    Args:
        bot:         One of "librarian", "triage", "researcher".
        prompt:      The query text.
        caller_slug: Identifier for the calling agent/session (for demand tracking).
        fallback:    If True (default), fall back to direct Ollama on daemon failure.

    Returns:
        Response string. Never raises; returns an error string on total failure.
    """
    if _daemon_reachable():
        result = _query_pool(bot, prompt, caller_slug)
        if result is not None:
            return result
        # daemon up but returned error — fall through to fallback
        if not fallback:
            return f"[bot_pool_client] daemon returned error for bot={bot}"

    if fallback:
        return _query_ollama_direct(bot, prompt)
    return f"[bot_pool_client] daemon not reachable for bot={bot} (fallback disabled)"


def health() -> dict[str, Any]:
    """Return health dict from daemon, or a degraded dict if unreachable."""
    code, body = _http_get(f"{POOL_BASE}/health", timeout=3)
    if code == 200:
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            pass
    return {"healthy": False, "daemon_reachable": False, "port": POOL_PORT}


def status() -> dict[str, Any]:
    """Return status dict from daemon, or a degraded dict if unreachable."""
    code, body = _http_get(f"{POOL_BASE}/status", timeout=3)
    if code == 200:
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            pass
    return {"daemon_reachable": False, "port": POOL_PORT}


# ---------------------------------------------------------------------------
# CLI (for quick ad-hoc use: python bot_pool_client.py librarian "what is X?")
# ---------------------------------------------------------------------------

def _cli_main() -> int:
    import argparse

    p = argparse.ArgumentParser(description="bot_pool_client CLI")
    p.add_argument("bot", help="bot type: librarian | triage | researcher")
    p.add_argument("query", nargs="?", help="query text (or pipe stdin)")
    p.add_argument("--caller", default="cli", help="caller_slug")
    p.add_argument("--no-fallback", action="store_true", help="disable direct Ollama fallback")
    p.add_argument("--health", action="store_true", help="print daemon health JSON")
    p.add_argument("--status", action="store_true", help="print daemon status JSON")
    args = p.parse_args()

    if args.health:
        print(json.dumps(health(), indent=2))
        return 0
    if args.status:
        print(json.dumps(status(), indent=2))
        return 0

    prompt = args.query or sys.stdin.read().strip()
    if not prompt:
        print("bot_pool_client: provide query as argument or on stdin", file=sys.stderr)
        return 2

    result = query(args.bot, prompt, caller_slug=args.caller, fallback=not args.no_fallback)
    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(_cli_main())
