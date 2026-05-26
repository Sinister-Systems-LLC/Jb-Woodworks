#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Author: RKOJ-ELENO :: 2026-05-26
"""
token_telemetry.py -- per-turn token-usage rolling ledger.

Models jcode telemetry lifecycle (TELEMETRY.md:176-185 +
src/telemetry/lifecycle.rs:54-59): every Claude API turn emits one row to an
append-only JSONL ledger so operators can see cache hit rates over time.

Sinister parallel-execution plan iter-96 (jcode-gap audit Rank #8).

CLI:
    record   -- append one row (per-turn usage tally)
    tail     -- print last N rows
    stats    -- aggregate JSON (totals + hit rate + breakdown)
    hits     -- one-line cache_hit_rate percentage
    --help

Storage:
    _shared-memory/token-ledger.jsonl (append-only; one JSON object per line)

Stdlib only.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable

# -----------------------------------------------------------------------------
# Paths & constants
# -----------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
SANCTUM_ROOT = SCRIPT_DIR.parent
LEDGER_PATH = SANCTUM_ROOT / "_shared-memory" / "token-ledger.jsonl"

# Opus pricing as of 2026-05 -- BEST-EFFORT defaults; rates may shift.
# Source assumption: Anthropic public price list (per-token USD).
#   input:           $3.00 / MTok  -> 0.000003
#   output:          $15.00 / MTok -> 0.000015
#   cache_creation:  $3.75 / MTok  -> 0.00000375
#   cache_read:      $0.30 / MTok  -> 0.0000003
PRICE_INPUT_USD_PER_TOK = 0.000003
PRICE_OUTPUT_USD_PER_TOK = 0.000015
PRICE_CACHE_CREATE_USD_PER_TOK = 0.00000375
PRICE_CACHE_READ_USD_PER_TOK = 0.0000003

DEFAULT_MODEL = "claude-opus-4-7"


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def _utc_now_iso() -> str:
    """RFC3339-ish UTC timestamp, second precision, with Z suffix."""
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_iso(ts: str) -> _dt.datetime | None:
    """Parse RFC3339-ish UTC timestamp; tolerate Z and offset forms."""
    if not isinstance(ts, str):
        return None
    s = ts.strip()
    if not s:
        return None
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        return _dt.datetime.fromisoformat(s)
    except ValueError:
        return None


def _compute_cost_usd(
    inp: int, out: int, cache_read: int, cache_create: int
) -> float:
    """Best-effort cost estimate using Opus rates documented above."""
    return round(
        inp * PRICE_INPUT_USD_PER_TOK
        + out * PRICE_OUTPUT_USD_PER_TOK
        + cache_create * PRICE_CACHE_CREATE_USD_PER_TOK
        + cache_read * PRICE_CACHE_READ_USD_PER_TOK,
        6,
    )


def _ensure_parent(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


def _iter_rows(
    ledger: Path = LEDGER_PATH,
    *,
    session: str | None = None,
    last_hours: float | None = None,
) -> Iterable[dict[str, Any]]:
    """Yield ledger rows; tolerant of missing file + corrupt lines.

    Filters:
        session     -- exact match against `session_slug`
        last_hours  -- only rows with `ts_utc >= now - last_hours`
    """
    if not ledger.exists():
        return
    cutoff: _dt.datetime | None = None
    if last_hours is not None:
        cutoff = _dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(
            hours=last_hours
        )
    try:
        with ledger.open("r", encoding="utf-8") as fh:
            for lineno, raw in enumerate(fh, start=1):
                line = raw.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    print(
                        f"token_telemetry: skipping corrupt row "
                        f"{ledger.name}:{lineno} ({exc})",
                        file=sys.stderr,
                    )
                    continue
                if not isinstance(row, dict):
                    print(
                        f"token_telemetry: skipping non-object row "
                        f"{ledger.name}:{lineno}",
                        file=sys.stderr,
                    )
                    continue
                if session and row.get("session_slug") != session:
                    continue
                if cutoff is not None:
                    row_ts = _parse_iso(row.get("ts_utc", ""))
                    if row_ts is None or row_ts < cutoff:
                        continue
                yield row
    except OSError as exc:
        print(
            f"token_telemetry: cannot read ledger {ledger}: {exc}",
            file=sys.stderr,
        )


# -----------------------------------------------------------------------------
# Subcommand: record
# -----------------------------------------------------------------------------


def cmd_record(args: argparse.Namespace) -> int:
    tools = (
        [t.strip() for t in args.tools.split(",") if t.strip()]
        if args.tools
        else []
    )
    cache_read = args.cache_read or 0
    cache_create = args.cache_creation or 0
    cost = _compute_cost_usd(args.input, args.output, cache_read, cache_create)
    row: dict[str, Any] = {
        "ts_utc": _utc_now_iso(),
        "session_slug": args.session,
        "session_id": args.session_id or "",
        "turn_n": args.turn,
        "input_tokens": args.input,
        "output_tokens": args.output,
        "cache_read_input_tokens": cache_read,
        "cache_creation_input_tokens": cache_create,
        "model": args.model or DEFAULT_MODEL,
        "duration_ms": args.duration_ms or 0,
        "cost_estimate_usd": cost,
        "tools_called": tools,
        "notes": args.notes or "",
    }
    _ensure_parent(LEDGER_PATH)
    # Atomic append: open in "a", single write call, with-block flush+close.
    # OS guarantees same-file appends are atomic up to PIPE_BUF on POSIX; on
    # Windows the write of one short JSON line is effectively atomic too.
    try:
        with LEDGER_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError as exc:
        print(f"token_telemetry: append failed: {exc}", file=sys.stderr)
        return 1
    print(
        f"recorded session={row['session_slug']} turn={row['turn_n']} "
        f"in={row['input_tokens']} out={row['output_tokens']} "
        f"cache_read={row['cache_read_input_tokens']} "
        f"cache_create={row['cache_creation_input_tokens']} "
        f"cost=${row['cost_estimate_usd']:.6f}"
    )
    return 0


# -----------------------------------------------------------------------------
# Subcommand: tail
# -----------------------------------------------------------------------------


def _fmt_row(row: dict[str, Any]) -> str:
    return (
        f"{row.get('ts_utc','')} | "
        f"{row.get('session_slug','')} | "
        f"turn={row.get('turn_n','')} | "
        f"in={row.get('input_tokens',0)} "
        f"out={row.get('output_tokens',0)} "
        f"cr={row.get('cache_read_input_tokens',0)} "
        f"cc={row.get('cache_creation_input_tokens',0)} | "
        f"{row.get('model','')} | "
        f"dur={row.get('duration_ms',0)}ms | "
        f"${row.get('cost_estimate_usd',0):.6f}"
    )


def cmd_tail(args: argparse.Namespace) -> int:
    n = args.n if args.n is not None else 10
    session = args.session
    if args.mine and not session:
        # --mine without an explicit --session is a no-op filter unless an env
        # var indicates the current session. SINISTER_AGENT_SLUG is the
        # canonical hint set by start-sinister-session.ps1.
        env_slug = os.environ.get("SINISTER_AGENT_SLUG") or os.environ.get(
            "AGENT_SLUG"
        )
        if env_slug:
            session = env_slug
    rows = list(_iter_rows(session=session))
    if not rows:
        return 0
    for row in rows[-n:]:
        print(_fmt_row(row))
    return 0


# -----------------------------------------------------------------------------
# Subcommand: stats
# -----------------------------------------------------------------------------


def _aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total_turns = len(rows)
    total_in = 0
    total_out = 0
    total_cr = 0
    total_cc = 0
    total_cost = 0.0
    total_dur = 0
    model_breakdown: dict[str, int] = {}
    for r in rows:
        total_in += int(r.get("input_tokens") or 0)
        total_out += int(r.get("output_tokens") or 0)
        total_cr += int(r.get("cache_read_input_tokens") or 0)
        total_cc += int(r.get("cache_creation_input_tokens") or 0)
        total_cost += float(r.get("cost_estimate_usd") or 0.0)
        total_dur += int(r.get("duration_ms") or 0)
        m = str(r.get("model") or "unknown")
        model_breakdown[m] = model_breakdown.get(m, 0) + 1
    # cache_hit_rate per acceptance criterion 4:
    #   cache_read / (cache_read + cache_create + input)
    denom = total_cr + total_cc + total_in
    hit_rate = (total_cr / denom) if denom > 0 else 0.0
    avg_dur = (total_dur / total_turns) if total_turns > 0 else 0.0
    return {
        "total_turns": total_turns,
        "total_input": total_in,
        "total_output": total_out,
        "total_cache_read": total_cr,
        "total_cache_creation": total_cc,
        "cache_hit_rate": round(hit_rate, 6),
        "total_cost_usd": round(total_cost, 6),
        "avg_duration_ms": round(avg_dur, 2),
        "model_breakdown": model_breakdown,
    }


def cmd_stats(args: argparse.Namespace) -> int:
    rows = list(
        _iter_rows(session=args.session, last_hours=args.last_hours)
    )
    agg = _aggregate(rows)
    print(json.dumps(agg, indent=2, ensure_ascii=False))
    return 0


# -----------------------------------------------------------------------------
# Subcommand: hits
# -----------------------------------------------------------------------------


def cmd_hits(args: argparse.Namespace) -> int:
    rows = list(
        _iter_rows(session=args.session, last_hours=args.last_hours)
    )
    agg = _aggregate(rows)
    pct = agg["cache_hit_rate"] * 100.0
    print(f"cache_hit_rate={pct:.1f}%")
    return 0


# -----------------------------------------------------------------------------
# Argument parser
# -----------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="token_telemetry",
        description=(
            "Per-turn token-usage rolling ledger. Append one JSONL row per "
            "Claude API turn; aggregate cache hit rate + cost over time."
        ),
    )
    sub = p.add_subparsers(dest="cmd", required=True, metavar="SUBCOMMAND")

    # record ------------------------------------------------------------------
    pr = sub.add_parser(
        "record", help="append one usage row to the ledger"
    )
    pr.add_argument("--session", required=True, help="session slug (lane)")
    pr.add_argument(
        "--turn", type=int, required=True, help="1-based turn number"
    )
    pr.add_argument(
        "--input", type=int, required=True, help="non-cache input tokens"
    )
    pr.add_argument(
        "--output", type=int, required=True, help="output tokens"
    )
    pr.add_argument(
        "--cache-read",
        type=int,
        default=0,
        help="cache_read_input_tokens (default 0)",
    )
    pr.add_argument(
        "--cache-creation",
        type=int,
        default=0,
        help="cache_creation_input_tokens (default 0)",
    )
    pr.add_argument("--session-id", default="", help="opaque session id")
    pr.add_argument(
        "--model", default=DEFAULT_MODEL, help=f"model id (default {DEFAULT_MODEL})"
    )
    pr.add_argument(
        "--duration-ms",
        type=int,
        default=0,
        help="turn wall-clock duration in ms",
    )
    pr.add_argument(
        "--tools", default="", help='comma-separated tools, e.g. "Bash,Read"'
    )
    pr.add_argument("--notes", default="", help="free-form note (<=200 chars)")
    pr.set_defaults(func=cmd_record)

    # tail --------------------------------------------------------------------
    pt = sub.add_parser("tail", help="print the last N ledger rows")
    pt.add_argument(
        "n",
        type=int,
        nargs="?",
        default=10,
        help="number of rows to show (default 10)",
    )
    pt.add_argument("--session", default=None, help="filter by session slug")
    pt.add_argument(
        "--mine",
        action="store_true",
        help="filter by current session slug (env SINISTER_AGENT_SLUG)",
    )
    pt.set_defaults(func=cmd_tail)

    # stats -------------------------------------------------------------------
    ps = sub.add_parser("stats", help="aggregate metrics as JSON")
    ps.add_argument("--session", default=None, help="filter by session slug")
    ps.add_argument(
        "--last-hours",
        type=float,
        default=None,
        help="only include rows within the last N hours",
    )
    ps.set_defaults(func=cmd_stats)

    # hits --------------------------------------------------------------------
    ph = sub.add_parser(
        "hits", help="print cache_hit_rate as a percentage"
    )
    ph.add_argument("--session", default=None, help="filter by session slug")
    ph.add_argument(
        "--last-hours",
        type=float,
        default=None,
        help="only include rows within the last N hours",
    )
    ph.set_defaults(func=cmd_hits)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
