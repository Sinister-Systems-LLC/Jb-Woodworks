"""
sinister_link_vault_transport.py - Vault-backed transport for Sinister LINK.

Author: RKOJ-ELENO :: 2026-05-25

Purpose
-------
Sinister LINK currently uses git-only transport (sanctum-auto-push every 30
min). This helper adds a vault-backed transport via Syncthing on the vault's
sync/ subtree -- sub-minute propagation between operator + Leo without a
GitHub round-trip.

The existing automations/sinister-link.ps1 shells out to this helper when
-Transport vault is selected. Wire is additive; git transport stays default
and untouched.

Wire
----
  python sinister_link_vault_transport.py --push  <invite-id> --payload <file>
  python sinister_link_vault_transport.py --pull  <invite-id> [--out <file>]
  python sinister_link_vault_transport.py --list  [--peer <name>]
  python sinister_link_vault_transport.py --health

Mechanics
---------
Vault daemon at http://127.0.0.1:5078 handles audit + quota + liveness.
Payload exchange uses the filesystem under
    D:\\sinister-vault\\sync\\sinister-link\\<invite-id>\\<role>.json
which Syncthing replicates LAN<2s / WAN ~5s to every paired peer.

After every push, audit-append to the vault daemon so both sides see
'who pushed what when' in the shared audit stream.

Exit codes: 0 ok / 1 not-found / 2 missing-arg / 3 io-fail / 4 daemon-down
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib import request as urlrequest
from urllib.error import URLError

VERSION = "1.0.0"
VAULT_ROOT = Path(r"D:\sinister-vault")
LINK_DIR = VAULT_ROOT / "sync" / "sinister-link"
DAEMON_URL = os.environ.get("SINISTER_VAULT_HOST", "http://127.0.0.1:5078")


def utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def actor_name() -> str:
    return (os.environ.get("SINISTER_ACCOUNT")
            or os.environ.get("USERNAME")
            or "unknown")


def daemon_get(path: str, timeout: float = 5.0) -> Optional[dict]:
    try:
        with urlrequest.urlopen(f"{DAEMON_URL}{path}", timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except (URLError, ValueError, OSError):
        return None


def daemon_post(path: str, body: dict, timeout: float = 5.0) -> Optional[dict]:
    data = json.dumps(body).encode("utf-8")
    req = urlrequest.Request(f"{DAEMON_URL}{path}", data=data,
                             headers={"Content-Type": "application/json"},
                             method="POST")
    try:
        with urlrequest.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except (URLError, ValueError, OSError):
        return None


def audit(kind: str, message: str, meta: Optional[dict] = None) -> None:
    """Best-effort audit append; never raises."""
    body = {"kind": kind, "actor": actor_name(),
            "path": "/sync/sinister-link/",
            "message": message, "meta": meta or {}}
    daemon_post("/api/vault/audit", body)


def daemon_alive() -> bool:
    return daemon_get("/api/vault/health") is not None


def push(invite_id: str, payload_file: str) -> int:
    if not invite_id:
        sys.stderr.write("missing --push <invite-id>\n")
        return 2
    pfile = Path(payload_file)
    if not pfile.exists():
        sys.stderr.write(f"payload not found: {payload_file}\n")
        return 1
    if not daemon_alive():
        sys.stderr.write(f"vault daemon at {DAEMON_URL} not reachable\n")
        return 4
    target_dir = LINK_DIR / invite_id
    target_dir.mkdir(parents=True, exist_ok=True)
    role = actor_name()
    target_file = target_dir / f"{role}.json"
    raw = pfile.read_bytes()
    target_file.write_bytes(raw)
    meta_file = target_dir / f"{role}.meta.json"
    meta_file.write_text(json.dumps({
        "ts": utc_iso(),
        "from": role,
        "invite_id": invite_id,
        "bytes": len(raw),
        "src_path": str(pfile.resolve()),
    }, indent=2), encoding="utf-8")
    audit("push", f"sinister-link push role={role} invite={invite_id} bytes={len(raw)}",
          {"invite_id": invite_id, "role": role, "bytes": len(raw)})
    print(json.dumps({"ok": True, "wrote": str(target_file),
                      "bytes": len(raw), "invite_id": invite_id}))
    return 0


def pull(invite_id: str, out_file: Optional[str]) -> int:
    if not invite_id:
        sys.stderr.write("missing --pull <invite-id>\n")
        return 2
    target_dir = LINK_DIR / invite_id
    if not target_dir.exists():
        sys.stderr.write(f"no link bucket: {invite_id}\n")
        return 1
    # Pull peer file = anything in this dir not authored by us.
    me = actor_name()
    candidates = sorted(
        [p for p in target_dir.glob("*.json")
         if not p.name.endswith(".meta.json") and p.stem != me],
        key=lambda p: p.stat().st_mtime, reverse=True,
    )
    if not candidates:
        sys.stderr.write("no peer payload yet (waiting on Syncthing)\n")
        return 1
    chosen = candidates[0]
    data = chosen.read_bytes()
    if out_file:
        Path(out_file).write_bytes(data)
        print(json.dumps({"ok": True, "from": chosen.stem,
                          "wrote": out_file, "bytes": len(data)}))
    else:
        sys.stdout.buffer.write(data)
    audit("pull", f"sinister-link pull role={me} from={chosen.stem} invite={invite_id} bytes={len(data)}",
          {"invite_id": invite_id, "from": chosen.stem, "bytes": len(data)})
    return 0


def list_buckets(peer_filter: Optional[str]) -> int:
    LINK_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for bucket in sorted(LINK_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if not bucket.is_dir():
            continue
        files = sorted(bucket.glob("*.json"))
        peers = sorted({f.stem.replace(".meta", "") for f in files})
        if peer_filter and peer_filter not in peers:
            continue
        latest = max((f.stat().st_mtime for f in files), default=0.0)
        rows.append({
            "invite_id": bucket.name,
            "peers": peers,
            "file_count": len(files),
            "latest_mtime": datetime.fromtimestamp(latest, tz=timezone.utc).isoformat(timespec="seconds") if latest else None,
        })
    print(json.dumps({"ok": True, "buckets": rows, "count": len(rows)}, indent=2))
    return 0


def health() -> int:
    h = daemon_get("/api/vault/health")
    LINK_DIR.mkdir(parents=True, exist_ok=True)
    bucket_count = sum(1 for p in LINK_DIR.iterdir() if p.is_dir())
    out = {
        "ok": h is not None,
        "daemon_url": DAEMON_URL,
        "daemon": h,
        "link_root": str(LINK_DIR),
        "bucket_count": bucket_count,
        "actor": actor_name(),
    }
    print(json.dumps(out, indent=2))
    return 0 if h else 4


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Sinister LINK vault transport")
    ap.add_argument("--push", metavar="INVITE", help="push payload to invite bucket")
    ap.add_argument("--pull", metavar="INVITE", help="pull peer payload from invite bucket")
    ap.add_argument("--list", action="store_true", help="list buckets")
    ap.add_argument("--health", action="store_true", help="report transport health")
    ap.add_argument("--payload", help="payload file (for --push)")
    ap.add_argument("--out", help="output file (for --pull)")
    ap.add_argument("--peer", help="filter --list by peer name")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    if args.health:
        return health()
    if args.list:
        return list_buckets(args.peer)
    if args.push:
        if not args.payload:
            sys.stderr.write("--push requires --payload <file>\n")
            return 2
        return push(args.push, args.payload)
    if args.pull:
        return pull(args.pull, args.out)
    sys.stderr.write("no action; use --push / --pull / --list / --health\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
