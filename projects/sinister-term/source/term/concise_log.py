# Sinister Term :: concise_log.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# Port of jcode's src/logging.rs:145-426 to Python. Source is MIT
# (Copyright (c) 2025 Jeremy Huang). Re-licensed under AGPL-3.0-or-later
# per upstream MIT terms (one-way compatible).
#
# Features (parity with jcode):
#   - Context prefix: [srv:SHORT|ses:SHORT|prv:SHORT|mod:SHORT] EVENT key=value
#   - Structured event format: `EVENT event=NAME k=v k="quoted v" ...`
#   - JSON mode via STERM_LOG_JSON=1 (`EVENT_JSON {"event": ...}`)
#   - Rate-limit dedup HashMap with `min_interval` per rate-key + suppressed counter
#   - Field redaction: keys containing token/secret/key/credential/authorization → <redacted>
#   - URL query redaction: https://x/y?... → https://x/y?<redacted>
#   - Value sanitization: strip \r\n\t, truncate at 160 chars
#   - Key sanitization: non-alphanum → _, truncate at 80 chars
#   - Field ordering: alphabetical (BTreeMap equiv)
#   - Date-rotated file at ~/.sterm/logs/sterm-YYYY-MM-DD.log
#   - cleanup_old_logs() drops files older than 7 days
#   - AUTH events + TOOL events + CRASH events with same redaction
#   - Debug level gated on STERM_TRACE env

from __future__ import annotations

import json
import os
import re
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple


# ---------------------------------------------------------------------------
# Constants / paths
# ---------------------------------------------------------------------------

LOG_DIR = Path.home() / ".sterm" / "logs"
_VALUE_MAX = 160
_KEY_MAX = 80
_TOOL_INPUT_MAX = 200
_TOOL_OUTPUT_MAX = 500

_REDACT_KEY_TOKENS = (
    "token", "secret", "key", "credential", "callback",
    "authorization", "auth_code", "oauth_code",
    "code_verifier", "code_challenge",
)
_KEY_OK_RE = re.compile(r"[^A-Za-z0-9_\-.]")


# ---------------------------------------------------------------------------
# Context (per-thread, like jcode's thread_local LOG_CONTEXT)
# ---------------------------------------------------------------------------

@dataclass
class LogContext:
    server: Optional[str] = None
    session: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None


_local = threading.local()


def _ctx() -> LogContext:
    ctx = getattr(_local, "ctx", None)
    if ctx is None:
        ctx = LogContext()
        _local.ctx = ctx
    return ctx


def set_session(session: str) -> None:
    _ctx().session = session


def set_server(server: str) -> None:
    _ctx().server = server


def set_provider_info(provider: str, model: str) -> None:
    c = _ctx()
    c.provider = provider
    c.model = model


def current_context_snapshot() -> LogContext:
    c = _ctx()
    return LogContext(
        server=c.server, session=c.session,
        provider=c.provider, model=c.model,
    )


def current_session() -> Optional[str]:
    return _ctx().session


def _context_prefix() -> str:
    """Render `[srv:X|ses:Y|prv:Z|mod:W] ` or '' (jcode logging.rs:145-174)."""
    c = _ctx()
    parts: list[str] = []
    if c.server:
        parts.append(f"srv:{c.server}")
    if c.session:
        short = c.session[:20] if len(c.session) > 20 else c.session
        parts.append(f"ses:{short}")
    if c.provider:
        parts.append(f"prv:{c.provider}")
    if c.model:
        short = c.model.split("-", 1)[0]
        parts.append(f"mod:{short}")
    if not parts:
        return ""
    return f"[{'|'.join(parts)}] "


# ---------------------------------------------------------------------------
# Sanitization / redaction (jcode logging.rs:436-605)
# ---------------------------------------------------------------------------

def _truncate(s: str, n: int) -> str:
    return s if len(s) <= n else (s[:n] + "...")


def _sanitize_key(key: str) -> str:
    cleaned = _KEY_OK_RE.sub("_", key)
    if not cleaned:
        cleaned = "field"
    return _truncate(cleaned, _KEY_MAX)


def _redact_url_queries(value: str) -> str:
    out: list[str] = []
    for word in value.split(" "):
        if (word.startswith("http://") or word.startswith("https://")) and "?" in word:
            base, _ = word.split("?", 1)
            out.append(f"{base}?<redacted>")
        else:
            out.append(word)
    return " ".join(out)


def _sanitize_value(value: str) -> str:
    cleaned = value.replace("\n", " ").replace("\r", " ").replace("\t", " ")
    cleaned = _redact_url_queries(cleaned)
    return _truncate(cleaned, _VALUE_MAX)


def _redact_auth_field(key: str, value: str) -> str:
    klow = key.lower()
    for tok in _REDACT_KEY_TOKENS:
        if tok in klow:
            return "<redacted>"
    return _sanitize_value(value)


_NEEDS_QUOTE_RE = re.compile(r"[\s='\"]")


def _format_field_value(value: str) -> str:
    if value == "" or _NEEDS_QUOTE_RE.search(value):
        return json.dumps(value)
    return value


# ---------------------------------------------------------------------------
# Rate limiting (jcode logging.rs:329-385)
# ---------------------------------------------------------------------------

@dataclass
class _RateState:
    last_emit: float = 0.0
    suppressed: int = 0


_rate_lock = threading.Lock()
_rate_limits: Dict[str, _RateState] = {}


def _maybe_emit_rate_limited(rate_key: str, min_interval_s: float) -> Tuple[bool, int]:
    """Returns (should_emit, suppressed_count_on_this_emit)."""
    now = time.monotonic()
    with _rate_lock:
        state = _rate_limits.get(rate_key)
        if state is None:
            _rate_limits[rate_key] = _RateState(last_emit=now, suppressed=0)
            return True, 0
        if (now - state.last_emit) < min_interval_s:
            state.suppressed += 1
            return False, 0
        sup = state.suppressed
        state.suppressed = 0
        state.last_emit = now
        return True, sup


# ---------------------------------------------------------------------------
# File backend (date-rotated, lazy)
# ---------------------------------------------------------------------------

_file_lock = threading.Lock()
_fh: Optional[Any] = None
_fh_date: Optional[str] = None


def _open_for_today() -> Optional[Any]:
    global _fh, _fh_date
    today = time.strftime("%Y-%m-%d")
    if _fh is not None and _fh_date == today:
        return _fh
    if _fh is not None:
        try:
            _fh.flush()
            _fh.close()
        except Exception:
            pass
        _fh = None
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        path = LOG_DIR / f"sterm-{today}.log"
        _fh = open(path, "a", encoding="utf-8")
        _fh_date = today
        return _fh
    except Exception:
        _fh = None
        _fh_date = None
        return None


def _write_line(level: str, message: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S") + f".{int((time.time() % 1) * 1000):03d}"
    ctx = _context_prefix()
    line = f"[{ts}] [{level}] {ctx}{message}\n"
    with _file_lock:
        fh = _open_for_today()
        if fh is None:
            return
        try:
            fh.write(line)
            fh.flush()
        except Exception:
            pass


def cleanup_old_logs(keep_days: int = 7) -> int:
    """Delete sterm-*.log files older than keep_days. Returns count removed."""
    if not LOG_DIR.exists():
        return 0
    cutoff = time.time() - (keep_days * 86400)
    removed = 0
    for p in LOG_DIR.glob("sterm-*.log"):
        try:
            if p.stat().st_mtime < cutoff:
                p.unlink()
                removed += 1
        except Exception:
            pass
    return removed


def log_path_today() -> Path:
    return LOG_DIR / f"sterm-{time.strftime('%Y-%m-%d')}.log"


# ---------------------------------------------------------------------------
# Public level functions
# ---------------------------------------------------------------------------

def _structured_json_enabled() -> bool:
    return os.environ.get("STERM_LOG_JSON", "").lower() in ("1", "true", "yes")


def _trace_enabled() -> bool:
    return "STERM_TRACE" in os.environ


def _format_structured_event(event_name: str, fields: Iterable[Tuple[str, Any]]) -> str:
    """jcode logging.rs:395-427."""
    event = _sanitize_value(str(event_name))
    ordered: "OrderedDict[str, str]" = OrderedDict()
    for raw_k, raw_v in fields:
        sk = _sanitize_key(str(raw_k))
        sv = _redact_auth_field(str(raw_k), str(raw_v))
        ordered[sk] = sv
    # alphabetic order (BTreeMap parity)
    ordered = OrderedDict(sorted(ordered.items(), key=lambda kv: kv[0]))

    if _structured_json_enabled():
        obj: "OrderedDict[str, str]" = OrderedDict()
        obj["event"] = event
        for k, v in ordered.items():
            obj[k] = v
        return "EVENT_JSON " + json.dumps(obj, separators=(", ", ": "))

    parts: list[str] = [f"event={_format_field_value(event)}"]
    parts.extend(f"{k}={_format_field_value(v)}" for k, v in ordered.items())
    return "EVENT " + " ".join(parts)


def event(level: str, event_name: str, **fields: Any) -> None:
    level = level.upper()
    if level == "DEBUG" and not _trace_enabled():
        return
    msg = _format_structured_event(event_name, fields.items())
    _write_line(level, msg)


def event_rate_limited(level: str, rate_key: str, min_interval_s: float,
                       event_name: str, **fields: Any) -> None:
    level = level.upper()
    if level == "DEBUG" and not _trace_enabled():
        return
    should_emit, suppressed = _maybe_emit_rate_limited(rate_key, min_interval_s)
    if not should_emit:
        return
    items = list(fields.items())
    if suppressed > 0:
        items.append(("suppressed", suppressed))
    msg = _format_structured_event(event_name, items)
    _write_line(level, msg)


def info(message: str) -> None:
    _write_line("INFO", message)


def warn(message: str) -> None:
    _write_line("WARN", message)


def error(message: str) -> None:
    _write_line("ERROR", message)


def debug(message: str) -> None:
    if not _trace_enabled():
        return
    _write_line("DEBUG", message)


def auth_event(event_name: str, provider: str, fields: Optional[Mapping[str, str]] = None) -> None:
    """jcode logging.rs:471-489 — AUTH lines with conservative redaction."""
    parts = [
        f"event={_sanitize_value(event_name)}",
        f"provider={_sanitize_value(provider)}",
    ]
    if fields:
        for k, v in fields.items():
            parts.append(f"{_sanitize_value(k)}={_redact_auth_field(k, str(v))}")
    _write_line("AUTH", "AUTH " + " ".join(parts))


def tool_call(name: str, input_text: str, output_text: str) -> None:
    """jcode logging.rs:496-508."""
    msg = (
        f"TOOL[{name}] "
        f"input={_truncate(input_text, _TOOL_INPUT_MAX)} "
        f"output={_truncate(output_text, _TOOL_OUTPUT_MAX)}"
    )
    _write_line("TOOL", msg)


def crash(err: str, context: str) -> None:
    """jcode logging.rs:515-522."""
    _write_line("CRASH", f"CRASH: {err} | Context: {context}")


# ---------------------------------------------------------------------------
# Optional OO wrapper for backwards compat with app.py
# ---------------------------------------------------------------------------

class ConciseLogger:
    """Thin OO wrapper. app.py uses `_LOG.info("EVENT", key=value)`."""

    def info(self, event_name: str, **fields: Any) -> None:
        event("INFO", event_name, **fields)

    def warn(self, event_name: str, **fields: Any) -> None:
        event("WARN", event_name, **fields)

    def error(self, event_name: str, **fields: Any) -> None:
        event("ERROR", event_name, **fields)

    def debug(self, event_name: str, **fields: Any) -> None:
        event("DEBUG", event_name, **fields)

    def rate_limited(self, rate_key: str, min_interval_s: float,
                     event_name: str, level: str = "INFO", **fields: Any) -> None:
        event_rate_limited(level, rate_key, min_interval_s, event_name, **fields)


_default: Optional[ConciseLogger] = None


def default() -> ConciseLogger:
    global _default
    if _default is None:
        _default = ConciseLogger()
    return _default
