#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-26
# License: AGPL-3.0-or-later
"""
render_fleet_topology.py — turn live Sinister fleet state into a Mermaid diagram.

Reads:
  _shared-memory/heartbeats/*.json   (one file = one agent's heartbeat)
  _shared-memory/fleet-updates.jsonl (cross-lane signal stream)

Writes (stdout, --out file, or --svg via mermaid-rs if available):
  flowchart LR DSL — agents as nodes, fleet-updates as edges.

Wave 1.A of the Sinister parallel-execution plan (iter-83). Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


# --- repo-root resolution (script lives at <root>/automations/) -------------

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
HEARTBEATS_DIR = REPO_ROOT / "_shared-memory" / "heartbeats"
FLEET_UPDATES_PATH = REPO_ROOT / "_shared-memory" / "fleet-updates.jsonl"

EDGE_LABEL_MAX = 28
DEFAULT_STALE_MINUTES = 30
DEFAULT_INCLUDE_UPDATES = 100
MAX_INCLUDE_UPDATES = 500


# --- utils ------------------------------------------------------------------


def _slug_to_id(slug: str) -> str:
    """Mermaid node ids must be valid identifiers — replace hyphens + scrub."""
    return re.sub(r"[^A-Za-z0-9_]", "_", slug)


def _truncate(text: str, limit: int = EDGE_LABEL_MAX) -> str:
    text = " ".join(str(text).split())  # collapse whitespace/newlines
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)] + "..."


def _escape_label(text: str) -> str:
    """Escape a label for use inside a Mermaid `"..."` string."""
    return str(text).replace("\\", "\\\\").replace('"', "&quot;").replace("|", "&#124;")


def _parse_ts(ts: str | None) -> datetime | None:
    if not ts or not isinstance(ts, str):
        return None
    s = ts.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _humanize_age(dt: datetime | None, now: datetime) -> str:
    if dt is None:
        return "unknown"
    delta = now - dt
    secs = int(delta.total_seconds())
    if secs < 0:
        return "future"
    if secs < 60:
        return f"{secs}s ago"
    mins = secs // 60
    if mins < 60:
        return f"{mins}m ago"
    hrs = mins // 60
    if hrs < 24:
        return f"{hrs}h ago"
    return f"{hrs // 24}d ago"


# --- data loading -----------------------------------------------------------


def load_heartbeats(stale_minutes: int) -> dict[str, dict[str, Any]]:
    """Return {slug: hb_dict} for fresh heartbeats (mtime within stale window)."""
    if not HEARTBEATS_DIR.is_dir():
        return {}
    now = datetime.now(timezone.utc)
    cutoff_secs = stale_minutes * 60
    out: dict[str, dict[str, Any]] = {}
    for path in sorted(HEARTBEATS_DIR.glob("*.json")):
        try:
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        except OSError:
            continue
        if (now - mtime).total_seconds() > cutoff_secs:
            continue
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
            data = json.loads(raw)
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        slug = data.get("slug") or data.get("agent") or path.stem
        if not isinstance(slug, str) or not slug:
            slug = path.stem
        data["_mtime"] = mtime
        data["_slug"] = slug
        out[slug] = data
    return out


def load_fleet_updates(limit: int) -> list[dict[str, Any]]:
    """Return up to `limit` most-recent fleet-update rows (oldest-first order)."""
    if not FLEET_UPDATES_PATH.is_file():
        return []
    rows: list[dict[str, Any]] = []
    try:
        with FLEET_UPDATES_PATH.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(obj, dict):
                    rows.append(obj)
    except OSError:
        return []
    # Sort ascending by ts_utc, then keep the most-recent `limit`.
    rows.sort(key=lambda r: r.get("ts_utc") or "")
    if limit > 0 and len(rows) > limit:
        rows = rows[-limit:]
    return rows


# --- rendering --------------------------------------------------------------


def _agent_display(hb: dict[str, Any]) -> str:
    return (
        hb.get("display_name")
        or hb.get("display")
        or hb.get("agent")
        or hb.get("_slug", "")
    )


def _agent_mode(hb: dict[str, Any]) -> str:
    for key in ("mode", "loop_mode", "loop", "status"):
        v = hb.get(key)
        if isinstance(v, str) and v:
            return v
    return "idle"


def _build_nodes(
    heartbeats: dict[str, dict[str, Any]], stale_minutes: int, now: datetime
) -> tuple[list[str], list[str], list[str]]:
    """Return (node_lines, fresh_ids, stale_ids) sorted by slug."""
    node_lines: list[str] = []
    fresh: list[str] = []
    stale: list[str] = []
    cutoff_secs = stale_minutes * 60
    for slug in sorted(heartbeats):
        hb = heartbeats[slug]
        node_id = _slug_to_id(slug)
        display = _escape_label(_agent_display(hb) or slug)
        mode = _escape_label(_agent_mode(hb))
        # Prefer recorded ts_utc; fall back to file mtime.
        hb_ts = _parse_ts(hb.get("ts_utc")) or hb.get("_mtime")
        age = _humanize_age(hb_ts, now)
        label = f'{display}<br/>mode={mode}<br/>{age}'
        node_lines.append(f'    {node_id}["{label}"]')
        # Freshness uses ts_utc when present, else file mtime (already filtered).
        ref = hb_ts or hb.get("_mtime")
        if ref and (now - ref).total_seconds() <= cutoff_secs:
            fresh.append(node_id)
        else:
            stale.append(node_id)
    return node_lines, fresh, stale


def _targets_from_row(row: dict[str, Any]) -> list[str]:
    """Normalize target_slugs (dict|list|str|None) into a flat slug list."""
    t = row.get("target_slugs")
    if t is None:
        return []
    if isinstance(t, dict):
        return [str(k) for k in t.keys() if k]
    if isinstance(t, list):
        return [str(x) for x in t if x]
    if isinstance(t, str) and t:
        return [t]
    return []


def _edge_label(row: dict[str, Any]) -> str:
    kind = row.get("kind") or "update"
    msg = row.get("message") or ""
    # Take leading message phrase for context.
    head = str(msg).split("\n", 1)[0].split(".", 1)[0]
    base = f"{kind}: {head}" if head else str(kind)
    return _escape_label(_truncate(base))


def _build_edges(
    rows: list[dict[str, Any]], known_slugs: set[str]
) -> list[str]:
    """Build edge lines; skip rows with dangling endpoints. Ordered by ts_utc ASC."""
    edges: list[str] = []
    for row in rows:
        src = row.get("pushed_by")
        if not isinstance(src, str) or src not in known_slugs:
            continue
        targets = [t for t in _targets_from_row(row) if t in known_slugs]
        if not targets:
            continue
        label = _edge_label(row)
        src_id = _slug_to_id(src)
        for tgt in targets:
            tgt_id = _slug_to_id(tgt)
            edges.append(f'    {src_id} -->|{label}| {tgt_id}')
    return edges


def render_mermaid(stale_minutes: int, include_updates: int) -> str:
    now = datetime.now(timezone.utc)
    heartbeats = load_heartbeats(stale_minutes)
    rows = load_fleet_updates(include_updates)
    node_lines, fresh_ids, stale_ids = _build_nodes(heartbeats, stale_minutes, now)
    edge_lines = _build_edges(rows, set(heartbeats.keys()))

    out: list[str] = ["flowchart LR"]
    out.append("    %% Sinister fleet topology — auto-generated")
    out.append(f"    %% generated_at_utc={now.strftime('%Y-%m-%dT%H:%M:%SZ')}")
    out.append(
        f"    %% agents={len(heartbeats)} fresh={len(fresh_ids)} "
        f"stale={len(stale_ids)} edges={len(edge_lines)}"
    )
    if not node_lines:
        out.append("    empty[\"(no fresh heartbeats)\"]")
        return "\n".join(out) + "\n"
    out.append("    %% Nodes")
    out.extend(node_lines)
    out.append("    classDef fresh fill:#7be07b,stroke:#333")
    out.append("    classDef stale fill:#bbb,stroke:#666")
    if fresh_ids:
        out.append(f"    class {','.join(fresh_ids)} fresh")
    if stale_ids:
        out.append(f"    class {','.join(stale_ids)} stale")
    if edge_lines:
        out.append("    %% Edges")
        out.extend(edge_lines)
    return "\n".join(out) + "\n"


# --- SVG export -------------------------------------------------------------


def _mermaid_renderer() -> str | None:
    """Return a renderer executable on PATH, or None."""
    for name in ("mermaid-rs", "mmdc"):
        path = shutil.which(name)
        if path:
            return path
    return None


def write_svg(mermaid: str, svg_path: Path) -> tuple[bool, Path]:
    """Try to render SVG via mermaid-rs/mmdc; on failure write .mmd fallback.

    Returns (svg_written, final_path).
    """
    renderer = _mermaid_renderer()
    if renderer is None:
        fallback = svg_path.with_suffix(".mmd")
        fallback.write_text(mermaid, encoding="utf-8")
        sys.stderr.write("mermaid-rs not installed; .mmd written instead\n")
        return False, fallback
    # Write temp .mmd next to target, invoke renderer, then delete temp.
    tmp = svg_path.with_suffix(".mmd.tmp")
    tmp.write_text(mermaid, encoding="utf-8")
    try:
        # mermaid-rs convention: <bin> -i input.mmd -o output.svg
        # mmdc convention is identical.
        proc = subprocess.run(
            [renderer, "-i", str(tmp), "-o", str(svg_path)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if proc.returncode != 0:
            sys.stderr.write(
                f"renderer {renderer} failed (rc={proc.returncode}): {proc.stderr.strip()}\n"
            )
            fallback = svg_path.with_suffix(".mmd")
            fallback.write_text(mermaid, encoding="utf-8")
            return False, fallback
    except (OSError, subprocess.TimeoutExpired) as exc:
        sys.stderr.write(f"renderer invocation error: {exc}\n")
        fallback = svg_path.with_suffix(".mmd")
        fallback.write_text(mermaid, encoding="utf-8")
        return False, fallback
    finally:
        try:
            tmp.unlink()
        except OSError:
            pass
    return True, svg_path


# --- CLI --------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="render_fleet_topology.py",
        description=(
            "Render live Sinister fleet heartbeats + fleet-updates as a Mermaid "
            "flowchart. Defaults: stdout, 30-minute freshness window, last 100 "
            "fleet-update edges."
        ),
    )
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Write Mermaid DSL to this file path instead of stdout.",
    )
    p.add_argument(
        "--svg",
        type=Path,
        default=None,
        help=(
            "Render SVG to this path via mermaid-rs/mmdc on PATH; falls back to "
            "writing a .mmd at the same path if the renderer is unavailable."
        ),
    )
    p.add_argument(
        "--stale-minutes",
        type=int,
        default=DEFAULT_STALE_MINUTES,
        help=(
            "Only include agents whose heartbeat mtime is within N minutes "
            "(default 30)."
        ),
    )
    p.add_argument(
        "--include-updates",
        type=int,
        default=DEFAULT_INCLUDE_UPDATES,
        help=(
            "Number of fleet-updates rows to draw as edges "
            f"(default {DEFAULT_INCLUDE_UPDATES}, max {MAX_INCLUDE_UPDATES})."
        ),
    )
    return p


def main(argv: Iterable[str] | None = None) -> int:
    args = _build_parser().parse_args(list(argv) if argv is not None else None)

    stale = max(1, int(args.stale_minutes))
    include = max(0, min(MAX_INCLUDE_UPDATES, int(args.include_updates)))

    mermaid = render_mermaid(stale, include)

    if args.svg is not None:
        write_svg(mermaid, args.svg)
        return 0

    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(mermaid, encoding="utf-8")
        return 0

    sys.stdout.write(mermaid)
    return 0


if __name__ == "__main__":
    sys.exit(main())
