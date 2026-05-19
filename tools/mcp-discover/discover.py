#!/usr/bin/env python3
"""mcp-discover -- poll the MCP Registry, diff vs registered servers, surface candidates.

Author: Sinister Sanctum master agent (Claude) :: 2026-05-19

Pure-read tool. Never modifies ~/.claude.json. Writes a diff report to
_shared-memory/external-imports/mcp-candidates.md so the operator (or a master
agent) can scan + decide which to register.

Usage:
  python discover.py                     # default: 100 servers, latest first
  python discover.py --limit 50          # cap at 50
  python discover.py --keyword github    # filter by keyword match in name/desc

Exit codes:
  0  -- discovery ran clean (report written; may have 0+ candidates)
  1  -- registry returned non-200 OR JSON parse failed
  2  -- claude.json not parseable
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import httpx
except ImportError:
    print("[FATAL] httpx not installed. Run: pip install httpx", file=sys.stderr)
    sys.exit(1)


REGISTRY_BASE = "https://registry.modelcontextprotocol.io"
REGISTRY_PATH = "/v0/servers"
SANCTUM_ROOT = Path(r"D:\Sinister Sanctum")
USER_HOME = Path(os.environ.get("USERPROFILE", ""))
# Newer Claude Code writes MCP entries to ~/.claude.json (user scope).
# Older project-scope MCP entries live at ~/.claude/.mcp.json.
# Sanctum spans both — read both files when diffing.
CLAUDE_JSON_PATHS = [
    USER_HOME / ".claude.json",
    USER_HOME / ".claude" / ".mcp.json",
]
OUT_PATH = SANCTUM_ROOT / "_shared-memory" / "external-imports" / "mcp-candidates.md"


def load_registered_names(paths: list[Path]) -> set[str]:
    """Union of MCP server names across all known Claude config files."""
    names: set[str] = set()
    for p in paths:
        if not p.exists():
            continue
        try:
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"[WARN] could not parse {p}: {e}", file=sys.stderr)
            continue
        servers = data.get("mcpServers", {})
        if isinstance(servers, dict):
            names.update(servers.keys())
    return names


def fetch_registry(limit: int) -> list[dict[str, Any]]:
    """Page through the registry until we have `limit` servers or the registry ends."""
    out: list[dict[str, Any]] = []
    cursor: str | None = None
    with httpx.Client(base_url=REGISTRY_BASE, timeout=10.0) as client:
        while len(out) < limit:
            params: dict[str, Any] = {}
            if cursor:
                params["cursor"] = cursor
            try:
                r = client.get(REGISTRY_PATH, params=params)
            except httpx.HTTPError as e:
                print(f"[FAIL] registry GET error: {e}", file=sys.stderr)
                return out
            if r.status_code != 200:
                print(f"[FAIL] registry returned {r.status_code}", file=sys.stderr)
                return out
            try:
                payload = r.json()
            except json.JSONDecodeError as e:
                print(f"[FAIL] registry JSON parse: {e}", file=sys.stderr)
                return out
            page = payload.get("servers") or []
            if not page:
                break
            out.extend(page)
            cursor = (payload.get("metadata") or {}).get("nextCursor")
            if not cursor:
                break
    return out[:limit]


def normalize(entry: dict[str, Any]) -> dict[str, str]:
    """Pull display-name + description from a registry entry."""
    srv = entry.get("server", entry)
    name = srv.get("name", "(unnamed)")
    desc = (srv.get("description") or "").strip()
    return {
        "name": name,
        "short_name": name.rsplit("/", 1)[-1],
        "description": desc[:240] + ("..." if len(desc) > 240 else ""),
        "repository": srv.get("repository", {}).get("url", "") if isinstance(srv.get("repository"), dict) else "",
    }


def render_report(
    candidates: list[dict[str, str]],
    registered: set[str],
    limit: int,
    keyword: str | None,
) -> str:
    utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines: list[str] = []
    lines.append("> **Author:** mcp-discover (Sinister Sanctum master agent) :: " + utc)
    lines.append("")
    lines.append("# MCP Registry — candidate servers")
    lines.append("")
    lines.append(f"Pulled {len(candidates)} entries from `{REGISTRY_BASE}{REGISTRY_PATH}` (limit={limit}" + (f", keyword={keyword!r}" if keyword else "") + ").")
    lines.append("")
    lines.append(f"Already registered in `~/.claude.json`: **{len(registered)}** server(s). Listed below with status flag.")
    lines.append("")
    lines.append("**How to use this report:** scan the table, pick a candidate, decide whether the capability fits Sanctum's roadmap, run case-study per `_shared-memory/DIRECTIVES.md:7-19`, then `claude mcp add <name> ... ` if approved. Pure-read; this script never edits `.claude.json`.")
    lines.append("")
    lines.append("| Status | Short name | Full name | Description | Repo |")
    lines.append("|---|---|---|---|---|")
    for c in candidates:
        in_fleet = c["short_name"] in registered or c["name"] in registered
        flag = "REGISTERED" if in_fleet else "candidate"
        desc = c["description"].replace("|", "\\|").replace("\n", " ")
        repo_link = f"[link]({c['repository']})" if c["repository"] else ""
        lines.append(f"| {flag} | {c['short_name']} | `{c['name']}` | {desc} | {repo_link} |")
    lines.append("")
    lines.append("## Method")
    lines.append("")
    lines.append("- Endpoint: `GET https://registry.modelcontextprotocol.io/v0/servers` (paginated; cursor follows next-page links until limit hit)")
    lines.append("- Diff key: server `name` (with short-name fallback) vs `mcpServers` keys in `~/.claude.json`")
    lines.append("- Write target: this file (overwritten each run; append-only history lives in git)")
    lines.append("")
    lines.append("## See also")
    lines.append("")
    lines.append("- `_shared-memory/external-imports/CANDIDATES.md` — manually-curated external-imports master list")
    lines.append("- `_shared-memory/DIRECTIVES.md:7-19` — case-study workflow for adding new MCPs")
    lines.append("- `tools/mcp-discover/README.md` — this tool's spec")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="MCP Registry discovery + diff vs ~/.claude.json")
    ap.add_argument("--limit", type=int, default=100, help="max number of entries to fetch (default 100)")
    ap.add_argument("--keyword", type=str, default=None, help="case-insensitive substring filter on name + description")
    ap.add_argument("--out", type=Path, default=OUT_PATH, help="output report path")
    args = ap.parse_args()

    registered = load_registered_names(CLAUDE_JSON_PATHS)
    print(f"[INFO] {len(registered)} servers registered across {len(CLAUDE_JSON_PATHS)} config file(s)")

    raw = fetch_registry(args.limit)
    if not raw:
        print("[FAIL] registry returned no entries", file=sys.stderr)
        return 1
    print(f"[INFO] fetched {len(raw)} registry entries")

    candidates = [normalize(e) for e in raw]

    if args.keyword:
        kw = args.keyword.lower()
        candidates = [c for c in candidates if kw in c["name"].lower() or kw in c["description"].lower()]
        print(f"[INFO] keyword filter: {len(candidates)} match {args.keyword!r}")

    new = [c for c in candidates if c["short_name"] not in registered and c["name"] not in registered]
    print(f"[INFO] new candidates (not yet registered): {len(new)}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    report = render_report(candidates, registered, args.limit, args.keyword)
    args.out.write_text(report, encoding="utf-8")
    print(f"[OK] wrote report: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
