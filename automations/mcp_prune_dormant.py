#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-26
"""
mcp_prune_dormant.py -- safely prune known-dormant MCP servers from ~/.claude/.mcp.json.

ROOT CAUSE (per _shared-memory/knowledge/fleet-freeze-and-zombie-windows-diagnosis-2026-05-25.md
+ jokester-freeze SUB-D diagnostic 2026-05-26):

  ~/.claude/.mcp.json registers 22 MCP servers. Each `claude` boot waits for every
  one to handshake. Four are dormant/broken (no longer install or hang on startup):
  playwright, context7, sequential-thinking, memory. Their handshake blocking is
  the dominant cause of the 1-10min "Simmering" pause operators see post-spawn.

SAFETY (matches CLAUDE.md "master agent NEVER touches ~/.claude/.mcp.json blindly"):

  - --dry-run is DEFAULT. Operator must pass --apply to mutate.
  - Backup written to ~/.claude/.mcp.json.backup-<utc-stamp> BEFORE any mutation.
  - JSON parse-check post-mutation; if it fails we restore the backup automatically.
  - --restore <stamp> re-applies a backup if a bad prune happened.
  - --list prints current MCP server keys for verification.

Doctrine refs:
  - fleet-freeze-and-zombie-windows-diagnosis-2026-05-25.md (dormant list source)
  - perf-freeze-root-cause-2026-05-24.md (prior doctrine, partial fix)
  - automate-everything-no-operator-admin-2026-05-25.md (no operator clicks)
  - no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25.md (Python over .ps1)

Usage:
  python automations/mcp_prune_dormant.py --list          # show current MCP servers
  python automations/mcp_prune_dormant.py --dry-run       # show what would be removed
  python automations/mcp_prune_dormant.py --apply         # actually prune (with backup)
  python automations/mcp_prune_dormant.py --restore <ts>  # restore from backup
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

# Canonical dormant list — per SUB-D 2026-05-26 + prior doctrine.
# Each entry is a top-level key under .mcp.json["mcpServers"]. Add to this list
# ONLY with new evidence (heartbeat-correlation or operator confirmation).
DORMANT_KEYS = [
    "playwright",
    "context7",
    "sequential-thinking",
    "memory",
]

MCP_PATH = Path(os.environ.get("CLAUDE_MCP_PATH", Path.home() / ".claude" / ".mcp.json"))


def _utc_stamp() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def _load_mcp() -> dict:
    if not MCP_PATH.exists():
        raise FileNotFoundError(f"MCP config not found at {MCP_PATH}")
    raw = MCP_PATH.read_text(encoding="utf-8-sig")
    return json.loads(raw)


def _save_mcp(cfg: dict) -> None:
    MCP_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def _backup() -> Path:
    stamp = _utc_stamp()
    dst = MCP_PATH.with_suffix(f".json.backup-{stamp}")
    shutil.copy2(MCP_PATH, dst)
    return dst


def cmd_list(_args: argparse.Namespace) -> int:
    cfg = _load_mcp()
    servers = cfg.get("mcpServers", {})
    print(f"MCP config: {MCP_PATH}")
    print(f"  total servers: {len(servers)}")
    for k in sorted(servers.keys()):
        flag = " [DORMANT-CANDIDATE]" if k in DORMANT_KEYS else ""
        print(f"   - {k}{flag}")
    return 0


def cmd_dry_run(_args: argparse.Namespace) -> int:
    cfg = _load_mcp()
    servers = cfg.get("mcpServers", {})
    would_remove = [k for k in DORMANT_KEYS if k in servers]
    not_present = [k for k in DORMANT_KEYS if k not in servers]
    print(f"MCP config: {MCP_PATH}")
    print(f"  current count : {len(servers)}")
    print(f"  would remove  : {len(would_remove)} ({', '.join(would_remove) or '(none)'})")
    print(f"  not present   : {len(not_present)} ({', '.join(not_present) or '(none)'})")
    print(f"  after prune   : {len(servers) - len(would_remove)}")
    print("  --apply to make the change (backup written first).")
    return 0


def cmd_apply(_args: argparse.Namespace) -> int:
    cfg = _load_mcp()
    servers = cfg.get("mcpServers", {})
    removed = []
    for k in DORMANT_KEYS:
        if k in servers:
            removed.append(k)
    if not removed:
        print(f"[mcp-prune] nothing to remove (none of {DORMANT_KEYS} present)")
        return 0

    backup_path = _backup()
    print(f"[mcp-prune] backup -> {backup_path}")

    for k in removed:
        del servers[k]
    cfg["mcpServers"] = servers

    try:
        _save_mcp(cfg)
        # parse-check
        reloaded = json.loads(MCP_PATH.read_text(encoding="utf-8-sig"))
        if len(reloaded.get("mcpServers", {})) != len(servers):
            raise RuntimeError("post-save server-count mismatch")
    except Exception as exc:
        print(f"[mcp-prune] FAIL post-save validation: {exc}", file=sys.stderr)
        print(f"[mcp-prune] auto-restoring from backup {backup_path}", file=sys.stderr)
        shutil.copy2(backup_path, MCP_PATH)
        return 4

    print(f"[mcp-prune] OK removed {len(removed)}: {', '.join(removed)}")
    print(f"[mcp-prune] new count: {len(servers)}")
    print(f"[mcp-prune] restore: python {sys.argv[0]} --restore {backup_path.suffix.lstrip('.').replace('backup-','')}")
    return 0


def cmd_restore(args: argparse.Namespace) -> int:
    stamp = args.stamp
    candidate = MCP_PATH.with_suffix(f".json.backup-{stamp}")
    if not candidate.exists():
        # try alternative naming
        candidate = MCP_PATH.parent / f".mcp.json.backup-{stamp}"
        if not candidate.exists():
            print(f"[mcp-prune] FAIL backup not found: {candidate}", file=sys.stderr)
            return 2
    shutil.copy2(candidate, MCP_PATH)
    print(f"[mcp-prune] restored from {candidate}")
    return 0


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Safely prune dormant MCP servers")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--list", action="store_true", help="list current MCP servers")
    g.add_argument("--dry-run", action="store_true", help="show what would be pruned")
    g.add_argument("--apply", action="store_true", help="prune (with backup)")
    g.add_argument("--restore", dest="stamp", metavar="STAMP", help="restore from backup-<stamp>")
    args = p.parse_args(argv)

    try:
        if args.list:
            return cmd_list(args)
        if args.dry_run:
            return cmd_dry_run(args)
        if args.apply:
            return cmd_apply(args)
        if args.stamp:
            return cmd_restore(args)
    except Exception as exc:
        print(f"[mcp-prune] FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
