"""
server.py - Sinister Vault HTTP API
Author: RKOJ-ELENO :: 2026-05-24

Mirrors the surface of the existing tools/sinister-vault/ daemon at :5078 but
runs containerized. Endpoints:

    GET  /api/vault/health           -> liveness + quota state
    GET  /api/vault/list?path=...    -> file listing
    GET  /api/vault/read?path=...    -> file contents (text)
    POST /api/vault/write            -> {path, content} -> writes + audits
    POST /api/vault/audit            -> {event, payload} -> appends to today's JSONL
    GET  /api/vault/snapshot         -> filename of latest snapshot

Quota = soft cap 1024 GB; warn at 950; HTTP 507 above hard cap.
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import JSONResponse, PlainTextResponse
import uvicorn

VAULT_ROOT = Path(os.environ.get("VAULT_ROOT", "/vault"))
VAULT_PORT = int(os.environ.get("VAULT_PORT", "5078"))
SOFT_CAP_GB = 1024
WARN_GB = 950

VAULT_ROOT.mkdir(parents=True, exist_ok=True)
(VAULT_ROOT / "audit").mkdir(parents=True, exist_ok=True)
(VAULT_ROOT / "snapshots").mkdir(parents=True, exist_ok=True)

app = FastAPI(title="sinister-vault-api", version="0.1.0")


def _now_utc():
    return datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_size_gb() -> float:
    total = 0
    for root, _, files in os.walk(VAULT_ROOT):
        for f in files:
            try:
                total += (Path(root) / f).stat().st_size
            except OSError:
                pass
    return total / (1024 ** 3)


def _audit(event: str, payload: dict) -> None:
    day = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    line = json.dumps({"ts_utc": _now_utc(), "event": event, "payload": payload})
    (VAULT_ROOT / "audit" / f"{day}.jsonl").open("a", encoding="utf-8").write(line + "\n")


def _resolve(path_str: str) -> Path:
    p = (VAULT_ROOT / path_str.lstrip("/")).resolve()
    if VAULT_ROOT.resolve() not in p.parents and p != VAULT_ROOT.resolve():
        raise HTTPException(403, "path escapes vault root")
    return p


@app.get("/api/vault/health")
def health():
    size = _vault_size_gb()
    status = "ok"
    if size >= SOFT_CAP_GB:
        status = "full"
    elif size >= WARN_GB:
        status = "warn"
    return {
        "status": status,
        "service": "sinister-vault-api",
        "version": "0.1.0",
        "vault_root": str(VAULT_ROOT),
        "size_gb": round(size, 3),
        "soft_cap_gb": SOFT_CAP_GB,
        "warn_at_gb": WARN_GB,
        "ts_utc": _now_utc(),
    }


@app.get("/api/vault/list")
def list_path(path: str = ""):
    p = _resolve(path)
    if not p.exists():
        raise HTTPException(404, "not found")
    if p.is_file():
        return {"type": "file", "path": str(p.relative_to(VAULT_ROOT)), "size": p.stat().st_size}
    entries = []
    for child in sorted(p.iterdir()):
        entries.append({
            "name": child.name,
            "type": "dir" if child.is_dir() else "file",
            "size": child.stat().st_size if child.is_file() else None,
        })
    return {"type": "dir", "path": str(p.relative_to(VAULT_ROOT)), "entries": entries}


@app.get("/api/vault/read", response_class=PlainTextResponse)
def read_file(path: str):
    p = _resolve(path)
    if not p.is_file():
        raise HTTPException(404, "not a file")
    return p.read_text(encoding="utf-8", errors="replace")


@app.post("/api/vault/write")
def write_file(body: dict = Body(...)):
    if _vault_size_gb() >= SOFT_CAP_GB:
        raise HTTPException(507, "vault full")
    path = body.get("path")
    content = body.get("content", "")
    if not path:
        raise HTTPException(400, "path required")
    p = _resolve(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    _audit("write", {"path": str(p.relative_to(VAULT_ROOT)), "bytes": len(content)})
    return {"ok": True, "path": str(p.relative_to(VAULT_ROOT)), "ts_utc": _now_utc()}


@app.post("/api/vault/audit")
def post_audit(body: dict = Body(...)):
    event = body.get("event", "info")
    payload = body.get("payload", {})
    _audit(event, payload)
    return {"ok": True, "ts_utc": _now_utc()}


@app.get("/api/vault/snapshot")
def latest_snapshot():
    snaps = sorted((VAULT_ROOT / "snapshots").glob("*"))
    if not snaps:
        return {"latest": None}
    return {"latest": str(snaps[-1].relative_to(VAULT_ROOT))}


if __name__ == "__main__":
    print(f"[sinister-vault-api] listening on :{VAULT_PORT}, vault_root={VAULT_ROOT}")
    uvicorn.run(app, host="0.0.0.0", port=VAULT_PORT, log_level="info")
