"""
Sinister Sanctum :: Window-Manager backend (FastAPI, port 5077)

Localhost-only, operator-only, no auth. Wraps existing _shared inbox/runlog
modules so the static UI in ./web/ can list projects, see online sessions,
send inbox messages, view recent runlogs, and launch new Claude sessions
via start-sinister-session.ps1.

Lane discipline:
  - Reads projects.json (operator-extensible registry; same file launcher uses).
  - Reads online.flag mtimes from 01_MEMORY/_inbox/<agent>/.
  - Imports _shared.inbox + _shared.runlog directly (no HTTP roundtrip).
  - Calls panel's existing /api/dashboard/stats with short timeout for trophy data.
  - Spawns start-sinister-session.ps1 via subprocess for launches.
  - DOES NOT touch panel source. DOES NOT touch ~/.claude/.mcp.json.
  - DOES NOT write anywhere outside automations/window-manager/ except via the
    documented inbox.inbox_send (which writes to 01_MEMORY/_inbox/<agent>/).

Run:
  python -m uvicorn server:app --host 127.0.0.1 --port 5077
or via the Open-Sanctum-Console.bat on Desktop.
"""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Literal, Optional

# 2026-05-19 SS-D follow-up: httpx is lazy-imported inside each call-site to
# shave ~1.3s off cold EXE boot. Do NOT re-add `import httpx` at module scope.
import secrets
import socket
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# --- paths ---
HERE = Path(__file__).resolve().parent
WEB_DIR = HERE / "web"
SANCTUM_ROOT = Path(r"D:\Sinister Sanctum")
HUB_REGISTRY_PATH = SANCTUM_ROOT / "skills" / "_REGISTRY.yaml"  # Skills Hub source of truth (yaml; regenerates HUB.md via automations/sync-fleet.ps1)
HUB_ROOT = Path(os.environ.get("SINISTER_HUB_ROOT", r"D:\Sinister\Sinister Skills"))
PROJECTS_JSON = SANCTUM_ROOT / "automations" / "session-templates" / "projects.json"
LAUNCHER_PS1 = SANCTUM_ROOT / "automations" / "start-sinister-session.ps1"
PANEL_CONFIG_JSON = SANCTUM_ROOT / "tools" / "panel-config" / "panel-config.json"
INBOX_ROOT = HUB_ROOT / "01_MEMORY" / "_inbox"
SCRIPT_RUNS_DIR = HUB_ROOT / "12_LLM_ORCHESTRATION" / "runtime-state" / "script-runs"
VAULT_DIR = SANCTUM_ROOT / "_vault"
TOKEN_FILE = VAULT_DIR / "window-manager-token.txt"

# --- LAN auth ---
LAN_MODE = os.environ.get("SINISTER_LAN") == "1"


def _ensure_token() -> str:
    """Get-or-create the bearer token. Persisted to _vault/window-manager-token.txt."""
    VAULT_DIR.mkdir(parents=True, exist_ok=True)
    if TOKEN_FILE.exists():
        tok = TOKEN_FILE.read_text(encoding="utf-8").strip()
        if tok:
            return tok
    tok = secrets.token_urlsafe(24)
    TOKEN_FILE.write_text(tok + "\n", encoding="utf-8")
    return tok


LAN_TOKEN = _ensure_token() if LAN_MODE else ""

# --- import _shared.inbox + _shared.runlog (hub) + sanctum_shared.* (local) ---
# 2026-05-19 (HR-B fix): the local `_shared/` package was renamed to
# `sanctum_shared/` so PyInstaller's collect_submodules picks it up — the
# underscore-prefix data-tuple form silently dropped the bundle's local
# `_shared/` and broke cycle-points + scheduler inside the frozen EXE.
# Hub imports (`from _shared import inbox / runlog`) keep working because we
# insert the hub `agents/` directory at sys.path[0]: `_shared` now resolves
# unambiguously to the hub package.
SHARED_DIR = HUB_ROOT / "12_LLM_ORCHESTRATION" / "agents" / "_shared"
if str(SHARED_DIR.parent) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR.parent))

# Also keep the window-manager directory on sys.path so `from sanctum_shared
# import cycle_points / scheduler` resolves to ./sanctum_shared/.
# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

try:
    from _shared import inbox as _inbox_mod  # type: ignore
    from _shared import runlog as _runlog_mod  # type: ignore
    SHARED_OK = True
    SHARED_ERR = None
except Exception as e:
    _inbox_mod = None
    _runlog_mod = None
    SHARED_OK = False
    SHARED_ERR = str(e)

VERSION = "8aj.1"
PORT = int(os.environ.get("SINISTER_SERVER_PORT", "5077"))

# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19 -- v2 sidebar+split
# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19 — Skills/Tools/Inventions/Codex endpoints
# Forever-growing sidebar tool registry. Future tools push a new entry; the
# frontend hydrates the sidebar from /api/window-tools (and a copy is echoed in
# /api/health for one-roundtrip bootstrap).
WINDOW_TOOLS_REGISTRY = [
    {"id": "agents", "label": "Claude agents", "icon": "A",
     "route": "group:agents", "category": "agents"},
    {"id": "requests", "label": "Operator requests", "icon": "!",
     "route": "view:requests", "category": "agents"},
    {"id": "command-menu", "label": "Command menu", "icon": "C",
     "route": "view:command-menu", "category": "agents"},
    {"id": "launcher", "label": "Launcher", "icon": "L",
     "route": "view:launcher", "category": "agents"},
    {"id": "phones", "label": "Phone viewer", "icon": "P",
     "route": "view:phones", "category": "phones"},
]

app = FastAPI(title="Sinister Sanctum :: Window-Manager", version=VERSION)


# --- HWID-locked auth middleware (v2; replaces LAN-only middleware) ---
# All requests (loopback + LAN) require a session token issued by /api/auth/login.
# The session token is HWID-bound: the same key on a different machine is denied.
# Public endpoints (no token required): /login (HTML), /api/auth/login, /api/health,
# /static/* (assets — they need to render the login page).
try:
    from auth import login as _auth_login_fn, validate_token as _auth_validate_fn, logout as _auth_logout_fn, status as _auth_status_fn, derive_hwid as _auth_hwid_fn  # type: ignore
    AUTH_AVAILABLE = True
except Exception as e:
    AUTH_AVAILABLE = False
    AUTH_ERR = str(e)

# Memory-poisoning defense (defense-in-depth on the write endpoints)
try:
    from memory_sanitizer import scan as _mem_scan, audit_block as _mem_audit_block  # type: ignore
    SANITIZER_AVAILABLE = True
    BLOCKED_WRITES_FILE = SANCTUM_ROOT / "_shared-memory" / "blocked-writes.jsonl"
except Exception:
    SANITIZER_AVAILABLE = False


def _sanitize_or_block(target: str, agent: str, title: str, body: str):
    """Run the sanitizer against the proposed write. If blocked, return an
    HTTPException to raise. If clean/warn, return None (allow)."""
    if not SANITIZER_AVAILABLE:
        return None
    combined = f"{title}\n{body}"
    res = _mem_scan(combined)
    if res.get("blocked"):
        try:
            _mem_audit_block(target, agent, title, body, res, BLOCKED_WRITES_FILE)
        except Exception:
            pass
        return HTTPException(
            status_code=400,
            detail={
                "ok": False,
                "error": "memory-poisoning-blocked",
                "patterns": res.get("patterns", []),
                "rationale": res.get("rationale", ""),
            },
        )
    return None


# --- operator-requests queue (👍 / 👎 / 💬) -------------------------------
# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
# Agents append "I need the operator to X because Y" requests. Operator triages
# from the Console: thumbs-up = approved, thumbs-down = denied, reply = typed
# answer routed back to the originating agent's inbox.

OP_REQ_FILE = SANCTUM_ROOT / "_shared-memory" / "operator-requests.jsonl"
OP_REQ_FILE.parent.mkdir(parents=True, exist_ok=True)
if not OP_REQ_FILE.exists():
    OP_REQ_FILE.write_text("", encoding="utf-8")


def _read_op_requests() -> list[dict[str, Any]]:
    out = []
    try:
        for line in OP_REQ_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    except Exception:
        pass
    return out


def _write_op_requests(reqs: list[dict[str, Any]]) -> None:
    OP_REQ_FILE.write_text(
        "\n".join(json.dumps(r) for r in reqs) + ("\n" if reqs else ""),
        encoding="utf-8",
    )


PUBLIC_PATHS = {"/login", "/api/auth/login", "/api/auth/whoami", "/api/health"}


@app.middleware("http")
async def hwid_auth(request: Request, call_next):
    path = request.url.path
    if not AUTH_AVAILABLE:
        # Fall back to old LAN-only behavior if auth module didn't import
        return await call_next(request)
    if path in PUBLIC_PATHS:
        return await call_next(request)
    if path.startswith("/static/") or path == "/m" or path.startswith("/m/") or path == "/favicon.ico":
        return await call_next(request)
    auth_hdr = request.headers.get("authorization", "")
    token = ""
    if auth_hdr.startswith("Bearer "):
        token = auth_hdr[7:].strip()
    if not token:
        token = request.query_params.get("t", "") or request.cookies.get("sinister_token", "")
    if token:
        res = _auth_validate_fn(token)
        if res.get("ok"):
            return await call_next(request)
    # Not authenticated — if it's an HTML page request, REAL 302 redirect
    # (browsers ignore Location headers on 401). JSON 401 for fetch() callers.
    accepts_html = "text/html" in (request.headers.get("accept", ""))
    if accepts_html and not path.startswith("/api/"):
        return RedirectResponse(url="/login", status_code=302)
    return JSONResponse({"ok": False, "error": "unauthorized - log in at /login"}, status_code=401)


# ---------------------------------------------------------------- helpers ---

def _read_projects() -> list[dict[str, Any]]:
    if not PROJECTS_JSON.exists():
        return []
    try:
        data = json.loads(PROJECTS_JSON.read_text(encoding="utf-8-sig"))
    except Exception:
        data = json.loads(PROJECTS_JSON.read_text(encoding="utf-8"))
    return data.get("projects", [])


def _age_human(seconds: float | int | None) -> str:
    if seconds is None:
        return "never"
    s = int(seconds)
    if s < 60:
        return f"{s}s ago"
    if s < 3600:
        return f"{s // 60}m ago"
    if s < 86400:
        return f"{s // 3600}h ago"
    return f"{s // 86400}d ago"


def _read_inbox_tail(agent: str, limit: int = 5) -> list[dict[str, Any]]:
    """Non-consuming tail read of messages.jsonl for an agent."""
    safe = "".join(c for c in agent if c.isalnum() or c in "-_")
    mpath = INBOX_ROOT / safe / "messages.jsonl"
    if not mpath.exists():
        return []
    try:
        lines = mpath.read_text(encoding="utf-8").splitlines()
    except Exception:
        return []
    out = []
    for line in lines[-limit:]:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


# ---------------------------------------------------------------- routes ----

@app.get("/api/health")
def health():
    return {
        "ok": True,
        "version": VERSION,
        "port": PORT,
        "shared_ok": SHARED_OK,
        "shared_err": SHARED_ERR,
        "auth_available": AUTH_AVAILABLE,
        "ts": datetime.now(timezone.utc).isoformat(),
        "tools_registry": WINDOW_TOOLS_REGISTRY,
    }


# --- operator-requests queue endpoints --------------------------------------

class OpReqCreate(BaseModel):
    agent: str
    title: str          # one-line "what do you need?"
    why: str = ""       # context / why
    urgency: str = "normal"   # low | normal | high | block
    kind: str = "ask"   # ask | approve-action | review-decision | merge-request


@app.get("/api/operator-requests")
def op_requests_list(status: str = "pending"):
    """List operator-requests. status= pending | approved | denied | replied | all."""
    reqs = _read_op_requests()
    if status and status != "all":
        reqs = [r for r in reqs if r.get("status") == status]
    reqs.sort(key=lambda r: r.get("ts", ""), reverse=True)
    return {"ok": True, "count": len(reqs), "requests": reqs}


@app.post("/api/operator-requests")
def op_requests_create(payload: OpReqCreate):
    """Agent submits a new request for operator triage."""
    if not payload.agent.strip() or not payload.title.strip():
        raise HTTPException(status_code=400, detail="agent + title required")
    # Memory-poisoning defense (operator-requests bubble to the operator's UI;
    # poisoned ones would phish the operator's approval).
    blk = _sanitize_or_block("operator-requests", payload.agent, payload.title, payload.why or "")
    if blk:
        raise blk
    rid = f"r-{int(time.time() * 1000)}-{secrets.token_hex(3)}"
    now = datetime.now(timezone.utc).isoformat()
    req = {
        "id": rid,
        "ts": now,
        "agent": payload.agent,
        "title": payload.title.strip(),
        "why": payload.why,
        "urgency": payload.urgency,
        "kind": payload.kind,
        "status": "pending",
        "operator_reply": None,
        "decided_at": None,
    }
    reqs = _read_op_requests()
    reqs.append(req)
    _write_op_requests(reqs)
    return {"ok": True, "id": rid, "request": req}


class OpReqDecision(BaseModel):
    reply: str = ""   # optional operator note attached to the decision


def _decide_request(rid: str, status: str, reply: str) -> dict[str, Any]:
    reqs = _read_op_requests()
    found = None
    now = datetime.now(timezone.utc).isoformat()
    for r in reqs:
        if r.get("id") == rid:
            r["status"] = status
            r["decided_at"] = now
            if reply:
                r["operator_reply"] = reply
            found = r
            break
    if not found:
        return {"ok": False, "error": "request not found"}
    _write_op_requests(reqs)
    # Route operator's reply back into the originating agent's inbox
    if reply and SHARED_OK and _inbox_mod is not None:
        try:
            _inbox_mod.inbox_send(
                to_agent=found["agent"],
                message=f"[operator-{status}] {found['title']}\n\n{reply}",
                from_agent="operator",
                urgent=(status == "approved" and found.get("urgency") == "block"),
                tags=["operator-decision", status],
            )
        except Exception:
            pass
    return {"ok": True, "request": found}


@app.post("/api/operator-requests/{rid}/approve")
def op_requests_approve(rid: str, payload: OpReqDecision):
    res = _decide_request(rid, "approved", payload.reply)
    if not res.get("ok"):
        raise HTTPException(status_code=404, detail=res.get("error"))
    return res


@app.post("/api/operator-requests/{rid}/deny")
def op_requests_deny(rid: str, payload: OpReqDecision):
    res = _decide_request(rid, "denied", payload.reply)
    if not res.get("ok"):
        raise HTTPException(status_code=404, detail=res.get("error"))
    return res


@app.post("/api/operator-requests/{rid}/reply")
def op_requests_reply(rid: str, payload: OpReqDecision):
    res = _decide_request(rid, "replied", payload.reply)
    if not res.get("ok"):
        raise HTTPException(status_code=404, detail=res.get("error"))
    return res


# ===== Agent prefs / intelligence-level control ============================
# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
# Operator clicks the intelligence chip in the Console -> we persist the choice
# to agent-prefs.json (launcher reads at spawn) AND drop a [CONFIG] inbox
# message the live agent self-applies via /model on its next turn. No restart.

SHARED_MEMORY_ROOT = SANCTUM_ROOT / "_shared-memory"
AGENT_PREFS_PATH = SHARED_MEMORY_ROOT / "agent-prefs.json"


class IntelligenceBody(BaseModel):
    model: Literal[
        "claude-opus-4-7",
        "claude-opus-4-6",
        "claude-sonnet-4-6",
        "claude-haiku-4-5-20251001",
    ]
    fast: bool = False


def _load_agent_prefs() -> dict:
    if not AGENT_PREFS_PATH.exists():
        return {}
    try:
        return json.loads(AGENT_PREFS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_agent_prefs(prefs: dict) -> None:
    AGENT_PREFS_PATH.parent.mkdir(parents=True, exist_ok=True)
    AGENT_PREFS_PATH.write_text(json.dumps(prefs, indent=2, sort_keys=True), encoding="utf-8")


@app.get("/api/agents/prefs")
def list_agent_prefs():
    """All known agent prefs as one dict."""
    return {"ok": True, "prefs": _load_agent_prefs()}


@app.get("/api/agents/{name}/intelligence")
def get_intelligence(name: str):
    prefs = _load_agent_prefs()
    return {"ok": True, "agent": name, **prefs.get(name, {"model": None, "fast": False})}


@app.post("/api/agents/{name}/intelligence")
def set_intelligence(name: str, body: IntelligenceBody, request: Request):
    prefs = _load_agent_prefs()
    entry = prefs.get(name, {})
    entry.update({
        "model": body.model,
        "fast": body.fast,
        "changed_at": datetime.utcnow().isoformat() + "Z",
        "changed_by": request.headers.get("X-Agent", "operator"),
    })
    prefs[name] = entry
    _save_agent_prefs(prefs)
    inbox_sent = False
    if SHARED_OK and _inbox_mod is not None:
        try:
            _inbox_mod.inbox_send(
                to_agent=name,
                message=f"[CONFIG] model={body.model} fast={body.fast} — call /model {body.model} now, ack via inbox_reply, then continue your prior task.",
                from_agent="sanctum-console",
                tags=["config", "model"],
            )
            inbox_sent = True
        except Exception:
            inbox_sent = False
    return {"ok": True, "agent": name, "model": body.model, "fast": body.fast,
            "applied": "persisted; inbox notified" if inbox_sent else "persisted (inbox unavailable)"}


# --- spawned-windows control (per-agent suspend / close / nudge / save+exit) ---
# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
# Reads the JSONL the launcher appends to on every spawn. Per-pid actions:
#   close   -> Stop-Process the spawned mintty PID (only PIDs in this list)
#   suspend -> Pause the process (via PowerShell PInvoke; best-effort)
#   resume  -> Resume a suspended process
#   nudge   -> Send a polite inbox message asking Claude to wrap up + save progress
#   stop    -> Inbox: "operator says STOP what you're doing right now"
# Close-All: kills EVERY pid in this list. Never touches anything not in the list.

SPAWNED_WINDOWS_FILE = SANCTUM_ROOT / "_shared-memory" / "spawned-windows.jsonl"


def _read_spawned_windows() -> list[dict[str, Any]]:
    out = []
    if not SPAWNED_WINDOWS_FILE.exists():
        return out
    try:
        for line in SPAWNED_WINDOWS_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    except Exception:
        pass
    # Drop entries whose PID no longer exists (dead window)
    live = []
    for w in out:
        pid = w.get("pid")
        if not pid:
            continue
        try:
            # On Windows, os.kill(pid, 0) raises if pid is gone
            os.kill(int(pid), 0)
            live.append(w)
        except (OSError, ProcessLookupError):
            continue
        except Exception:
            # Permission error etc — still consider alive
            live.append(w)
    return live


@app.get("/api/spawned-windows")
def spawned_windows_list():
    return {"ok": True, "windows": _read_spawned_windows()}


def _pid_in_spawn_list(pid: int) -> dict[str, Any] | None:
    for w in _read_spawned_windows():
        if int(w.get("pid", -1)) == int(pid):
            return w
    return None


@app.post("/api/spawned-windows/{pid}/close")
def spawned_windows_close(pid: int):
    """Kill ONE spawned Claude window. Only PIDs in our spawn list are eligible —
    operator's other terminals are never touched."""
    w = _pid_in_spawn_list(pid)
    if not w:
        raise HTTPException(status_code=404, detail="pid not in spawn list — refusing")
    try:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True, timeout=5)
        else:
            os.kill(pid, 15)
        return {"ok": True, "killed": pid, "agent": w.get("agent")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"close failed: {e}")


@app.post("/api/spawned-windows/{pid}/suspend")
def spawned_windows_suspend(pid: int):
    w = _pid_in_spawn_list(pid)
    if not w:
        raise HTTPException(status_code=404, detail="pid not in spawn list")
    try:
        # PsSuspend.exe from sysinternals (if installed) or fallback to PowerShell PInvoke
        subprocess.run(["powershell.exe", "-NoProfile", "-Command",
                        f"$p=Get-Process -Id {pid} -ErrorAction Stop; "
                        f"foreach($t in $p.Threads){{[void][PInvoke]::SuspendThread($t.Id)}}"
                       ], capture_output=True, timeout=5)
        return {"ok": True, "suspended": pid}
    except Exception as e:
        return {"ok": False, "error": str(e)}


class WindowNudge(BaseModel):
    kind: str = "nudge"   # nudge | stop | save-exit | custom
    custom_body: str = ""  # when kind == 'custom', this is the literal message


@app.post("/api/spawned-windows/{pid}/nudge")
def spawned_windows_nudge(pid: int, payload: WindowNudge):
    """Send an inbox message to the agent in that window. The agent sees it on
    next inbox_poll and obeys politely. Does NOT kill the process."""
    w = _pid_in_spawn_list(pid)
    if not w:
        raise HTTPException(status_code=404, detail="pid not in spawn list")
    if not (SHARED_OK and _inbox_mod is not None):
        return {"ok": False, "error": "_shared.inbox unavailable"}
    msg_map = {
        "nudge":      "[operator-nudge] Pause what you're doing and check the operator-requests queue / inbox.",
        "stop":       "[operator-STOP] Operator says: stop what you're doing right now. Do not write any more files. Wait for further instruction.",
        "save-exit":  "[operator-save+exit] Time to wrap up this session. Save all progress to PROGRESS/<your-name>.md, commit any pending changes to your branch, and prepare to exit cleanly. Reply with a one-line summary of session state when done.",
    }
    if payload.kind == "custom" and payload.custom_body.strip():
        body = f"[operator-command] {payload.custom_body.strip()}"
    else:
        body = msg_map.get(payload.kind, msg_map["nudge"])
    try:
        _inbox_mod.inbox_send(
            to_agent=w["agent"],
            message=body,
            from_agent="operator",
            urgent=(payload.kind in ("stop", "save-exit")),
            tags=["operator", payload.kind],
        )
        return {"ok": True, "delivered_to": w["agent"], "kind": payload.kind}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/api/console/close-all")
def console_close_all():
    """Kill all spawned Claude windows (only PIDs in our spawn list) + clear the file.
    NEVER touches operator's other terminals or unrelated processes."""
    killed = []
    failed = []
    for w in _read_spawned_windows():
        pid = w.get("pid")
        if not pid:
            continue
        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True, timeout=5)
            else:
                os.kill(int(pid), 15)
            killed.append({"pid": pid, "agent": w.get("agent")})
        except Exception as e:
            failed.append({"pid": pid, "error": str(e)})
    # Clear the spawn list
    try:
        SPAWNED_WINDOWS_FILE.write_text("", encoding="utf-8")
    except Exception:
        pass
    return {"ok": True, "killed": killed, "failed": failed, "count": len(killed)}


# --- auth endpoints --------------------------------------------------------
class LoginBody(BaseModel):
    key: str


@app.post("/api/auth/login")
def auth_login(payload: LoginBody):
    if not AUTH_AVAILABLE:
        raise HTTPException(status_code=500, detail="auth module unavailable")
    res = _auth_login_fn(payload.key)
    if not res.get("ok"):
        raise HTTPException(status_code=401, detail=res.get("error", "login failed"))
    resp = JSONResponse({"ok": True, "label": res["label"], "token": res["token"]})
    # Also set as cookie for browser-side convenience
    resp.set_cookie(key="sinister_token", value=res["token"], httponly=False, samesite="lax", max_age=86400 * 7)
    return resp


@app.get("/api/auth/whoami")
def auth_whoami(request: Request):
    if not AUTH_AVAILABLE:
        return {"ok": False, "error": "auth module unavailable"}
    auth_hdr = request.headers.get("authorization", "")
    token = ""
    if auth_hdr.startswith("Bearer "):
        token = auth_hdr[7:].strip()
    if not token:
        token = request.cookies.get("sinister_token", "")
    if not token:
        return {"ok": False, "error": "no token"}
    res = _auth_validate_fn(token)
    if res.get("ok"):
        return {"ok": True, "label": res["label"], "hwid": _auth_hwid_fn()}
    return {"ok": False, "error": res.get("error", "invalid")}


@app.post("/api/auth/logout")
def auth_logout(request: Request):
    if not AUTH_AVAILABLE:
        raise HTTPException(status_code=500, detail="auth module unavailable")
    auth_hdr = request.headers.get("authorization", "")
    token = ""
    if auth_hdr.startswith("Bearer "):
        token = auth_hdr[7:].strip()
    if not token:
        token = request.cookies.get("sinister_token", "")
    if token:
        _auth_logout_fn(token)
    resp = JSONResponse({"ok": True})
    resp.delete_cookie("sinister_token")
    return resp


@app.get("/api/auth/status")
def auth_status():
    if not AUTH_AVAILABLE:
        return {"ok": False, "error": "auth module unavailable"}
    return _auth_status_fn()


@app.get("/login")
def login_page():
    lp = WEB_DIR / "login.html"
    if not lp.exists():
        raise HTTPException(status_code=500, detail=f"missing {lp}")
    return FileResponse(lp, media_type="text/html")


@app.get("/api/window-tools")
def window_tools():
    """Sidebar tool registry consumed by the v2 UI. Hard-coded for now; future
    tools just append to WINDOW_TOOLS_REGISTRY (or a registry file)."""
    return {"ok": True, "tools": WINDOW_TOOLS_REGISTRY}


# ---------------------------------------------------------------- FLEET / heartbeats / SSE ----
# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
# HR-B audit consolidation: three views of the fleet (spawned-windows, sessions
# strip, inbox agents list) were polling three endpoints on three timers and
# rendering the same data three different ways. Wave-2 collapses them into a
# single SSE feed at /api/fleet-stream that the frontend's FleetState module
# subscribes to once. /api/fleet/heartbeats is the daemon-liveness panel — it
# reads the *.beat files directly off disk (no auth coupling to the writers).

HEARTBEATS_DIR = SANCTUM_ROOT / "_shared-memory" / "heartbeats"
# Only the canonical daemon-liveness beats — build-stamps (rkoj-build.beat,
# sanctum-console-build.beat) are intentionally excluded; they're emitted once
# per PyInstaller run, not on a heartbeat cadence.
_DAEMON_LIVENESS_BEATS = ("sanctum-console", "sinister-vault", "rkoj")
_HEARTBEAT_STALE_S = 120  # alive if age_s < this


def _read_heartbeat(slug: str) -> dict[str, Any]:
    """Return one heartbeat's snapshot row. Missing file => alive=False, age=None."""
    path = HEARTBEATS_DIR / f"{slug}.beat"
    row: dict[str, Any] = {
        "slug": slug,
        "path": str(path),
        "exists": False,
        "mtime_iso": None,
        "age_s": None,
        "alive": False,
        "last_line": "",
    }
    if not path.exists():
        return row
    try:
        st = path.stat()
        mtime = st.st_mtime
        age = max(0, int(time.time() - mtime))
        text = ""
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            text = ""
        last_line = ""
        for ln in reversed(text.splitlines()):
            if ln.strip():
                last_line = ln.strip()
                break
        row.update({
            "exists": True,
            "mtime_iso": datetime.fromtimestamp(mtime, timezone.utc).isoformat(),
            "age_s": age,
            "alive": age < _HEARTBEAT_STALE_S,
            "last_line": last_line,
        })
    except Exception as e:
        row["error"] = str(e)
    return row


def _compute_heartbeats_snapshot() -> dict[str, Any]:
    """Scan _shared-memory/heartbeats/*.beat for the canonical daemon liveness set."""
    beats: dict[str, dict[str, Any]] = {}
    for slug in _DAEMON_LIVENESS_BEATS:
        beats[slug] = _read_heartbeat(slug)
    return {
        "ok": True,
        "now_iso": datetime.now(timezone.utc).isoformat(),
        "stale_threshold_s": _HEARTBEAT_STALE_S,
        "heartbeats": beats,
    }


@app.get("/api/fleet/heartbeats")
def fleet_heartbeats():
    """Daemon-liveness panel data. alive = age_s < 120 (no file => alive=False)."""
    return _compute_heartbeats_snapshot()


def _compute_fleet_snapshot() -> dict[str, Any]:
    """One unified payload for spawned-windows + sessions + heartbeats + inbox tails.
    Used by /api/fleet-stream so all 3 frontend views consume the same source.
    """
    sessions_snap = _compute_sessions_snapshot()
    sessions = sessions_snap.get("sessions") or []
    online_agents = [s["agent"] for s in sessions if s.get("online")]
    inbox_tails: dict[str, list[dict[str, Any]]] = {}
    for agent in online_agents:
        inbox_tails[agent] = _read_inbox_tail(agent, limit=5)
    return {
        "ok": True,
        "ts": datetime.now(timezone.utc).isoformat(),
        "windows": _read_spawned_windows(),
        "sessions": sessions,
        "sessions_source": sessions_snap.get("source"),
        "heartbeats": _compute_heartbeats_snapshot()["heartbeats"],
        "inbox_tails": inbox_tails,
    }


@app.get("/api/fleet-stream")
async def fleet_stream(request: Request):
    """SSE feed that fans out heartbeats + spawned-windows + sessions + inbox
    tails on a single 5-second tick. Auth via the existing middleware (the
    token is read from `?t=<token>` for EventSource which can't set headers).

    Emits `event: fleet-update` every 5s + immediately on connect. Sends
    keep-alive `: ping` comments every 15s so dead connections drop quickly
    and proxies don't buffer.
    """
    refresh_s = 5.0
    keepalive_s = 15.0

    async def event_stream():
        # Immediate snapshot so subscribers don't wait 5s for first paint.
        try:
            initial = _compute_fleet_snapshot()
            yield f"event: fleet-update\ndata: {json.dumps(initial, default=str)}\n\n"
        except Exception as e:
            err = {"ok": False, "error": f"snapshot failed: {type(e).__name__}: {e}"}
            yield f"event: fleet-update\ndata: {json.dumps(err)}\n\n"
        last_emit = time.monotonic()
        last_ping = last_emit
        try:
            while True:
                if await request.is_disconnected():
                    break
                # Sleep in short slices so we can mix refresh + keep-alive.
                await asyncio.sleep(1.0)
                now = time.monotonic()
                if now - last_emit >= refresh_s:
                    try:
                        snap = _compute_fleet_snapshot()
                        yield f"event: fleet-update\ndata: {json.dumps(snap, default=str)}\n\n"
                    except Exception as e:
                        err = {"ok": False, "error": f"{type(e).__name__}: {e}",
                               "ts": datetime.now(timezone.utc).isoformat()}
                        yield f"event: fleet-update\ndata: {json.dumps(err)}\n\n"
                    last_emit = now
                    last_ping = now
                elif now - last_ping >= keepalive_s:
                    yield ": ping\n\n"
                    last_ping = now
        except asyncio.CancelledError:
            return

    headers = {
        "Cache-Control": "no-cache, no-transform",
        "X-Accel-Buffering": "no",
        "Connection": "keep-alive",
    }
    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=headers)


# ---------------------------------------------------------------- DEVICES (phone viewer) ----
# Per operator's containerization directive (2026-05-19): each phone is its own
# container. Every adb call carries -s <serial>. scrcpy mirrors the physical
# display only (--display-id 0). Replaces broken Panda screen-mirror.

_PHONE_VIEWER_DIR = SANCTUM_ROOT / "tools" / "sinister-phone-viewer"
if _PHONE_VIEWER_DIR.exists() and str(_PHONE_VIEWER_DIR) not in sys.path:
    sys.path.insert(0, str(_PHONE_VIEWER_DIR))

try:
    import viewer as _viewer_mod  # type: ignore
    VIEWER_OK = True
    VIEWER_ERR = None
except Exception as e:
    _viewer_mod = None  # type: ignore
    VIEWER_OK = False
    VIEWER_ERR = str(e)

# In-memory map: serial -> Popen pid. Tracks the active viewer process per
# phone so /stop knows which pid to terminate (without touching other scrcpy
# instances).
_DEVICE_VIEWERS: dict[str, int] = {}


@app.get("/api/devices")
def devices_list():
    """List ADB-attached phones via `adb devices -l`. Returns
    {ok, devices: [{serial, model, state, online, transport_id, ...}],
     viewers: {serial: pid, ...}}."""
    if not VIEWER_OK or _viewer_mod is None:
        return JSONResponse(
            {"ok": False, "error": f"viewer module unavailable: {VIEWER_ERR}", "devices": []},
            status_code=200,
        )
    try:
        devs = _viewer_mod.list_devices()
        # Annotate with active viewer pid if any.
        for d in devs:
            d["viewer_pid"] = _DEVICE_VIEWERS.get(d.get("serial", ""), None)
        return {"ok": True, "devices": devs, "viewers": dict(_DEVICE_VIEWERS)}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e), "devices": []}, status_code=200)


class DeviceViewBody(BaseModel):
    max_size: int = 1280
    bit_rate: str = "4M"
    audio: bool = False
    control: bool = True


@app.post("/api/devices/{serial}/view")
def devices_view_start(serial: str, payload: DeviceViewBody | None = None):
    """Spawn scrcpy mirroring serial's PHYSICAL display (--display-id 0).
    NEVER --new-display / --virtual-display / --display-overlay."""
    if not VIEWER_OK or _viewer_mod is None:
        raise HTTPException(status_code=503, detail=f"viewer module unavailable: {VIEWER_ERR}")
    if not serial.strip():
        raise HTTPException(status_code=400, detail="serial required")

    # Stop any existing viewer for this serial first (idempotent).
    existing_pid = _DEVICE_VIEWERS.pop(serial, None)
    if existing_pid is not None:
        try:
            _viewer_mod.stop_view(existing_pid)
        except Exception:
            pass

    body = payload or DeviceViewBody()
    try:
        pid = _viewer_mod.start_view(
            serial,
            audio=body.audio,
            control=body.control,
            max_size=body.max_size,
            bit_rate=body.bit_rate,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"failed to start scrcpy: {e}")

    _DEVICE_VIEWERS[serial] = pid
    return {"ok": True, "serial": serial, "pid": pid}


@app.post("/api/devices/{serial}/stop")
def devices_view_stop(serial: str):
    """Terminate the scrcpy viewer process for this serial only.
    Does NOT touch other scrcpy instances on other phones."""
    if not VIEWER_OK or _viewer_mod is None:
        raise HTTPException(status_code=503, detail=f"viewer module unavailable: {VIEWER_ERR}")
    pid = _DEVICE_VIEWERS.pop(serial, None)
    if pid is None:
        return {"ok": True, "serial": serial, "note": "no viewer was running for this serial"}
    try:
        ok = _viewer_mod.stop_view(pid)
        return {"ok": True, "serial": serial, "pid": pid, "terminated": bool(ok)}
    except Exception as e:
        return JSONResponse(
            {"ok": False, "serial": serial, "pid": pid, "error": str(e)},
            status_code=500,
        )


@app.get("/api/devices/{serial}/state")
def devices_state(serial: str):
    """Return the per-phone state notes file (_shared-memory/notes/phones/<serial>.md)
    if present, otherwise ok=true with exists=false."""
    if not VIEWER_OK or _viewer_mod is None:
        raise HTTPException(status_code=503, detail=f"viewer module unavailable: {VIEWER_ERR}")
    try:
        return _viewer_mod.get_phone_state(serial)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


class DevicePushBody(BaseModel):
    file_path: str
    dest_path: str


# RKOJ embedded screen viewer — Sinister Sanctum master agent (Claude) :: 2026-05-19
@app.get("/api/devices/{serial}/screen")
async def device_screen(serial: str):
    """Single-shot PNG screenshot of device. ~200-500ms per frame.
    No anti-detect flags — operator's spoofing handles that upstream."""
    if not VIEWER_OK or _viewer_mod is None:
        raise HTTPException(status_code=503, detail=f"viewer module unavailable: {VIEWER_ERR}")
    try:
        png = await _viewer_mod.capture_screen(serial, timeout=5.0)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not png:
        raise HTTPException(status_code=404, detail=f"could not capture screen for {serial}")
    return Response(content=png, media_type="image/png")


# RKOJ embedded screen viewer — Sinister Sanctum master agent (Claude) :: 2026-05-19
@app.get("/api/devices/{serial}/screen.mjpeg")
async def device_screen_mjpeg(serial: str, fps: float = 2.0):
    """Multipart MJPEG stream of device screen. Default 2 fps; cap 10 fps."""
    if not VIEWER_OK or _viewer_mod is None:
        raise HTTPException(status_code=503, detail=f"viewer module unavailable: {VIEWER_ERR}")
    fps = max(0.2, min(fps, 10.0))
    interval = 1.0 / fps
    boundary = "--rkoj-screen"

    async def gen():
        try:
            while True:
                try:
                    png = await _viewer_mod.capture_screen(serial, timeout=interval + 1.0)
                except Exception:
                    png = None
                if not png:
                    await asyncio.sleep(interval)
                    continue
                yield (
                    f"\r\n{boundary}\r\n"
                    f"Content-Type: image/png\r\n"
                    f"Content-Length: {len(png)}\r\n\r\n"
                ).encode()
                yield png
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            return

    return StreamingResponse(
        gen(), media_type=f"multipart/x-mixed-replace; boundary={boundary[2:]}"
    )


@app.post("/api/devices/{serial}/push")
def devices_push(serial: str, payload: DevicePushBody):
    """Per-serial `adb -s <serial> push <file_path> <dest_path>`. Operator-only
    (HWID auth required by middleware). Updates the phone's state notes."""
    if not VIEWER_OK or _viewer_mod is None:
        raise HTTPException(status_code=503, detail=f"viewer module unavailable: {VIEWER_ERR}")
    if not payload.file_path.strip() or not payload.dest_path.strip():
        raise HTTPException(status_code=400, detail="file_path + dest_path required")
    try:
        res = _viewer_mod.adb_push_file(serial, payload.file_path, payload.dest_path)
        status = 200 if res.get("ok") else 400
        return JSONResponse(res, status_code=status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


# ============================================================
# Phones tab — Devices console routes
# Author: RKOJ-ELENO :: 2026-05-21
# Powers web/devices-tab.js — Sinister Panel-style fleet console:
#   /api/devices/details   -> identity (model, android, build, transport)
#   /api/phone-viewer/launch -> spawn tools/sinister-phone-viewer/viewer.py
#   /api/scrcpy/launch       -> spawn `scrcpy -s <serial>` direct
#   /api/adb/shell           -> one-shot adb -s <serial> shell <cmd>
#   /api/adb/logcat          -> SSE stream of last 50 logcat lines
# All subprocess.Popen launches use CREATE_NO_WINDOW on win32 so the
# console flash that scrcpy/python.exe would otherwise produce stays hidden.
# ============================================================

# Windows-specific: CREATE_NO_WINDOW = 0x08000000. On non-win32 this is 0
# (so the flag silently no-ops and Popen behaves normally on linux/mac).
_PHONE_CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0

# Path constants for the Phones tab.
_PHONE_VIEWER_PY = SANCTUM_ROOT / "tools" / "sinister-phone-viewer" / "viewer.py"
_PHONE_HEARTBEAT_DIR = SANCTUM_ROOT / "_shared-memory" / "heartbeats" / "phones"
_PHONE_RKA_LOG = Path(r"D:\Sinister\01_Projects\Sinister\Sinister-APK\.recovery-watchdog\recovery-watchdog.log")


def _phone_run_adb(serial: str, *args: str, timeout: float = 10.0) -> dict[str, Any]:
    """Run `adb -s <serial> <args>` with a short timeout. Returns
    {ok, stdout, stderr, returncode}. Never raises — surfaces error text instead.
    Author: RKOJ-ELENO :: 2026-05-21."""
    try:
        cp = subprocess.run(
            ["adb", "-s", serial, *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=_PHONE_CREATE_NO_WINDOW,
        )
        return {
            "ok": cp.returncode == 0,
            "stdout": cp.stdout,
            "stderr": cp.stderr,
            "returncode": cp.returncode,
        }
    except FileNotFoundError:
        return {"ok": False, "stdout": "", "stderr": "adb not on PATH", "returncode": -1}
    except subprocess.TimeoutExpired:
        return {"ok": False, "stdout": "", "stderr": f"adb timed out after {timeout}s", "returncode": -2}
    except Exception as e:
        return {"ok": False, "stdout": "", "stderr": str(e), "returncode": -3}


@app.get("/api/devices/details")
def devices_details(serial: str):
    """Return per-device identity (model, android version, build fingerprint, transport)
    via `adb -s <serial> shell getprop <key>`. Operator-facing right-pane in Phones tab.
    Also returns heartbeat freshness + RKA log tail if those files exist.
    Author: RKOJ-ELENO :: 2026-05-21."""
    if not serial.strip():
        raise HTTPException(status_code=400, detail="serial required")
    props = {
        "model":            "ro.product.model",
        "manufacturer":     "ro.product.manufacturer",
        "brand":            "ro.product.brand",
        "android_version":  "ro.build.version.release",
        "sdk":              "ro.build.version.sdk",
        "build":            "ro.build.fingerprint",
        "serialno":         "ro.serialno",
    }
    out: dict[str, Any] = {"ok": True, "serial": serial}
    for key, prop in props.items():
        r = _phone_run_adb(serial, "shell", f"getprop {prop}", timeout=5.0)
        out[key] = (r.get("stdout") or "").strip() if r.get("ok") else ""
    # Transport pill — try `adb devices -l` line for this serial.
    try:
        cp = subprocess.run(
            ["adb", "devices", "-l"],
            capture_output=True, text=True, timeout=5.0,
            creationflags=_PHONE_CREATE_NO_WINDOW,
        )
        transport = ""
        for ln in cp.stdout.splitlines():
            if ln.startswith(serial):
                # e.g. "ABCD device usb:1-2 product:cheetah model:Pixel_7_Pro transport_id:3"
                transport = ln.split(None, 1)[1] if " " in ln else ""
                break
        out["transport"] = transport
    except Exception:
        out["transport"] = ""

    # Heartbeat freshness (per-serial — falls back to serial-as-filename).
    hb_file = _PHONE_HEARTBEAT_DIR / f"{serial}.json"
    if hb_file.exists():
        try:
            hb = json.loads(hb_file.read_text(encoding="utf-8"))
            out["heartbeat"] = {
                "exists": True,
                "last_seen": hb.get("last_seen"),
                "display_name": hb.get("display_name"),
                "project": hb.get("project"),
                "mtime": hb_file.stat().st_mtime,
            }
        except Exception as e:
            out["heartbeat"] = {"exists": True, "error": str(e)}
    else:
        out["heartbeat"] = {"exists": False}

    # RKA daemon log tail (last 5 lines of recovery-watchdog.log if present).
    if _PHONE_RKA_LOG.exists():
        try:
            txt = _PHONE_RKA_LOG.read_text(encoding="utf-8", errors="replace")
            tail = txt.splitlines()[-5:]
            out["rka_log_tail"] = tail
            out["rka_log_path"] = str(_PHONE_RKA_LOG)
        except Exception as e:
            out["rka_log_tail"] = [f"(read error: {e})"]
    else:
        out["rka_log_tail"] = []
        out["rka_log_path"] = str(_PHONE_RKA_LOG) + " (not found)"

    return out


@app.post("/api/phone-viewer/launch")
def phone_viewer_launch(serial: str):
    """Spawn tools/sinister-phone-viewer/viewer.py <serial> as a detached subprocess
    so its scrcpy/Tk window outlives this request. Returns {ok, pid}.
    Author: RKOJ-ELENO :: 2026-05-21."""
    if not serial.strip():
        raise HTTPException(status_code=400, detail="serial required")
    if not _PHONE_VIEWER_PY.exists():
        raise HTTPException(status_code=503, detail=f"phone-viewer missing: {_PHONE_VIEWER_PY}")
    try:
        proc = subprocess.Popen(
            [sys.executable, str(_PHONE_VIEWER_PY), serial],
            cwd=str(_PHONE_VIEWER_PY.parent),
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=_PHONE_CREATE_NO_WINDOW,
            close_fds=True,
        )
        return {"ok": True, "serial": serial, "pid": proc.pid}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


@app.post("/api/scrcpy/launch")
def scrcpy_launch(serial: str):
    """Spawn `scrcpy -s <serial>` directly. If scrcpy not on PATH, return 503 with
    a hint to install (so the UI can show a 'install scrcpy' nudge).
    Author: RKOJ-ELENO :: 2026-05-21."""
    if not serial.strip():
        raise HTTPException(status_code=400, detail="serial required")
    import shutil
    if not shutil.which("scrcpy"):
        raise HTTPException(
            status_code=503,
            detail="scrcpy not on PATH — install via `winget install Genymobile.scrcpy` "
                   "or download from https://github.com/Genymobile/scrcpy/releases",
        )
    try:
        proc = subprocess.Popen(
            ["scrcpy", "-s", serial],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=_PHONE_CREATE_NO_WINDOW,
            close_fds=True,
        )
        return {"ok": True, "serial": serial, "pid": proc.pid}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


class _AdbShellBody(BaseModel):
    cmd: str


@app.post("/api/adb/shell")
def adb_shell(serial: str, cmd: str = "", payload: _AdbShellBody | None = None):
    """One-shot `adb -s <serial> shell <cmd>` with 10s timeout. The `cmd` can come
    via query-string (?cmd=...) or POST body (json {cmd}). Returns
    {ok, stdout, stderr, returncode}.
    Author: RKOJ-ELENO :: 2026-05-21."""
    effective = cmd or (payload.cmd if payload else "")
    if not serial.strip() or not effective.strip():
        raise HTTPException(status_code=400, detail="serial + cmd both required")
    r = _phone_run_adb(serial, "shell", effective, timeout=10.0)
    return r


@app.get("/api/adb/logcat")
async def adb_logcat(serial: str):
    """SSE stream of `adb -s <serial> logcat -d -t 50` — last 50 lines, refreshed
    every 3 seconds. The text/event-stream gives the devices-tab a clean reactive
    tail without WebSocket overhead.
    Author: RKOJ-ELENO :: 2026-05-21."""
    if not serial.strip():
        raise HTTPException(status_code=400, detail="serial required")

    async def gen():
        try:
            while True:
                try:
                    cp = await asyncio.to_thread(
                        subprocess.run,
                        ["adb", "-s", serial, "logcat", "-d", "-t", "50"],
                        capture_output=True, text=True, timeout=8.0,
                    )
                    payload = cp.stdout if cp.returncode == 0 else (cp.stderr or f"adb exit {cp.returncode}")
                except FileNotFoundError:
                    payload = "[adb not on PATH]"
                except subprocess.TimeoutExpired:
                    payload = "[adb logcat timed out]"
                except Exception as e:
                    payload = f"[error: {e}]"
                # SSE: data lines must be prefixed; we collapse newlines so one event
                # carries the full last-50-line tail (the UI just replaces innerText).
                safe = payload.replace("\r", "").replace("\n", "\\n")
                yield f"data: {safe}\n\n".encode("utf-8")
                await asyncio.sleep(3.0)
        except asyncio.CancelledError:
            return

    return StreamingResponse(gen(), media_type="text/event-stream")


@app.get("/api/projects")
def projects():
    return {"ok": True, "projects": _read_projects()}


def _read_inbox_freshness(agent: str) -> dict[str, Any]:
    """Return last_inbox_check (mtime of inbox dir / messages.jsonl) +
    last_turn_marker (mtime of turn-marker file if it exists, else messages.jsonl).
    Used by the heartbeat / re-ping UI so the operator can tell ALIVE vs STALE.
    Author: Sinister Sanctum master agent (Claude) :: 2026-05-19 (hot-reload sprint).
    """
    safe = "".join(c for c in agent if c.isalnum() or c in "-_")
    adir = INBOX_ROOT / safe
    out: dict[str, Any] = {"last_inbox_check": None, "last_turn_marker": None}
    if not adir.exists():
        return out
    try:
        # The agent's `inbox_poll` write touches messages.jsonl / cursor file.
        for fname, key in (("cursor.txt", "last_inbox_check"),
                           ("messages.jsonl", "last_turn_marker")):
            f = adir / fname
            if f.exists():
                out[key] = datetime.fromtimestamp(f.stat().st_mtime, timezone.utc).isoformat()
        # Fallback: any change to the agent's online.flag bumps last_turn_marker too.
        if out["last_turn_marker"] is None:
            flag = adir / "online.flag"
            if flag.exists():
                out["last_turn_marker"] = datetime.fromtimestamp(flag.stat().st_mtime, timezone.utc).isoformat()
    except Exception:
        pass
    return out


def _compute_sessions_snapshot() -> dict[str, Any]:
    """Internal helper — produces the same payload as `/api/sessions`.
    Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
    Factored out so both `/api/sessions` and the `/api/fleet-stream` SSE feed
    share a single source-of-truth without an HTTP roundtrip.
    """
    out: list[dict[str, Any]] = []
    if SHARED_OK and _inbox_mod is not None:
        try:
            rows = _inbox_mod.who_is_online()
            for r in rows:
                last_age = r.get("last_seen_age_seconds")
                r["last_seen_human"] = _age_human(last_age)
                r["inbox_tail"] = _read_inbox_tail(r["agent"], limit=3)
                r.update(_read_inbox_freshness(r["agent"]))
                out.append(r)
            return {"ok": True, "sessions": out, "source": "_shared.inbox"}
        except Exception as e:
            return {"ok": False, "error": str(e), "sessions": []}
    # Fallback: read directory directly
    if not INBOX_ROOT.exists():
        return {"ok": True, "sessions": [], "source": "fallback-empty"}
    now = time.time()
    for d in sorted(INBOX_ROOT.iterdir()):
        if not d.is_dir():
            continue
        flag = d / "online.flag"
        if flag.exists():
            try:
                age = now - flag.stat().st_mtime
                row = {
                    "agent": d.name,
                    "online": age < 5 * 60,
                    "last_seen_age_seconds": int(age),
                    "last_seen_human": _age_human(age),
                    "last_seen": datetime.fromtimestamp(flag.stat().st_mtime, timezone.utc).isoformat(),
                    "inbox_tail": _read_inbox_tail(d.name, limit=3),
                }
                row.update(_read_inbox_freshness(d.name))
                out.append(row)
            except Exception:
                continue
        else:
            row = {"agent": d.name, "online": False, "last_seen_age_seconds": None,
                   "last_seen_human": "never", "last_seen": None,
                   "inbox_tail": _read_inbox_tail(d.name, limit=3)}
            row.update(_read_inbox_freshness(d.name))
            out.append(row)
    return {"ok": True, "sessions": out, "source": "fallback-fs"}


@app.get("/api/sessions")
def sessions():
    """List every agent dir + online state (heartbeat < 5 min).

    Each row also carries `last_inbox_check` + `last_turn_marker` so the
    heartbeat / [UPDATE] ping UI can distinguish ALIVE (recent turn) from
    STALE (online.flag still warm but no actual turn activity).
    """
    snap = _compute_sessions_snapshot()
    if not snap.get("ok") and snap.get("error"):
        return JSONResponse(snap, status_code=200)
    return snap


@app.get("/api/inbox/{agent}")
def inbox_tail_endpoint(agent: str, limit: int = 10):
    return {"ok": True, "agent": agent, "messages": _read_inbox_tail(agent, limit=limit)}


class InboxSendBody(BaseModel):
    to: str
    body: str
    sender: str = "window-manager"
    urgent: bool = False
    tags: list[str] | None = None


@app.post("/api/inbox/send")
def inbox_send_endpoint(payload: InboxSendBody):
    if not payload.to.strip() or not payload.body.strip():
        raise HTTPException(status_code=400, detail="to + body required")
    if not (SHARED_OK and _inbox_mod is not None):
        return JSONResponse({"ok": False, "error": f"shared module unavailable: {SHARED_ERR}"}, status_code=503)
    try:
        res = _inbox_mod.inbox_send(
            to_agent=payload.to,
            message=payload.body,
            from_agent=payload.sender,
            urgent=payload.urgent,
            tags=payload.tags or ["window-manager"],
        )
        return {"ok": True, "result": res}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


# --- Cross-agent broadcast (Sinister Sanctum master agent (Claude) :: 2026-05-19) ---
# Standing rule (DIRECTIVES.md 2026-05-19 — CROSS-AGENT COORDINATION):
# agents that discover fleet-relevant info should fan it out to every online
# agent in one call instead of N round-trips through the operator.
class BroadcastBody(BaseModel):
    body: str
    tags: List[str] = []
    from_agent: str = "operator"
    exclude: List[str] = []  # agent names to skip


@app.post("/api/inbox/broadcast")
def inbox_broadcast(body: BroadcastBody):
    """Fan-out one message to every currently-online agent in one call.

    Iterates `_inbox_mod.who_is_online()` (same source as /api/sessions),
    calls `_inbox_mod.inbox_send(...)` per agent, returns delivered/skipped lists.
    Honors `exclude` (e.g. don't send back to the sender that just told you).
    """
    if not body.body.strip():
        raise HTTPException(status_code=400, detail="body required")
    if not SHARED_OK or _inbox_mod is None:
        return JSONResponse(
            {"ok": False, "error": f"inbox subsystem offline: {SHARED_ERR}"},
            status_code=503,
        )
    try:
        online = _inbox_mod.who_is_online()
    except Exception as e:
        return JSONResponse({"ok": False, "error": f"who_is_online failed: {e}"}, status_code=500)

    delivered: List[str] = []
    skipped: List[str] = []
    tags = body.tags or ["cross-agent", "broadcast"]
    for row in online:
        agent = row.get("agent") if isinstance(row, dict) else None
        if not agent:
            continue
        if agent in body.exclude:
            skipped.append(agent)
            continue
        # Only deliver to actually-online agents (heartbeat-fresh).
        if isinstance(row, dict) and row.get("online") is False:
            skipped.append(f"{agent}: offline")
            continue
        try:
            _inbox_mod.inbox_send(
                to_agent=agent,
                message=body.body,
                from_agent=body.from_agent,
                tags=tags,
            )
            delivered.append(agent)
        except Exception as e:
            skipped.append(f"{agent}: {e}")
    return {"ok": True, "delivered": delivered, "skipped": skipped, "count": len(delivered)}


@app.get("/api/recent-runlogs")
def recent_runlogs(limit: int = 20):
    if SHARED_OK and _runlog_mod is not None:
        try:
            rows = _runlog_mod.list_recent(limit=limit)
            return {"ok": True, "runlogs": rows, "source": "_shared.runlog"}
        except Exception as e:
            return JSONResponse({"ok": False, "error": str(e), "runlogs": []}, status_code=200)
    # Fallback
    if not SCRIPT_RUNS_DIR.exists():
        return {"ok": True, "runlogs": [], "source": "fallback-empty"}
    files = sorted(SCRIPT_RUNS_DIR.glob("*.json"),
                   key=lambda p: p.stat().st_mtime, reverse=True)[:limit]
    out = []
    for f in files:
        try:
            m = json.loads(f.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        out.append({
            "id": f.stem,
            "script": m.get("script"),
            "started": m.get("started"),
            "finished": m.get("finished"),
            "ok": m.get("ok"),
            "exit_code": m.get("exit_code"),
            "step_count": len(m.get("steps", [])),
        })
    return {"ok": True, "runlogs": out, "source": "fallback-fs"}


def _load_panel_config() -> dict:
    """Read tools/panel-config/panel-config.json. Hardcoded safety net if missing.

    Authoritative knob for primary / fallback URLs + per-source timeouts. Edited
    live by operator; we re-read on every request (no module-level cache).
    """
    default = {
        "primary": "http://127.0.0.1:5055",
        "fallback": "https://snap.sinijkr.com",
        "timeout_ms_primary": 1500,
        "timeout_ms_fallback": 4000,
    }
    try:
        if PANEL_CONFIG_JSON.exists():
            cfg = json.loads(PANEL_CONFIG_JSON.read_text(encoding="utf-8"))
            for k, v in default.items():
                cfg.setdefault(k, v)
            return cfg
    except Exception:
        pass
    return default


@app.get("/api/trophy")
def trophy():
    """Aggregate live counts from panel + RKA. Loopback-first per panel-config.json.

    Response includes `source: "local" | "prod" | "offline"` so the UI can tag the cell.
    """
    cfg = _load_panel_config()
    out = {
        "ok": True,
        "panel_online": False,
        "rka_online": False,
        "source": "offline",
        "accounts": None,
        "videos": None,
        "active": None,
        "pushes": None,
        "banned": None,
        "devices": None,
        "wired_actions": None,
        "errors": [],
    }
    # (base_url, label, timeout_ms)
    sources = []
    if cfg.get("primary"):
        sources.append((cfg["primary"].rstrip("/"), "local", cfg.get("timeout_ms_primary", 1500)))
    if cfg.get("fallback"):
        sources.append((cfg["fallback"].rstrip("/"), "prod", cfg.get("timeout_ms_fallback", 4000)))
    # Keep hardcoded chain as last-ditch fallback if config was empty
    if not sources:
        sources = [
            ("http://127.0.0.1:5055", "local", 1500),
            ("https://snap.sinijkr.com", "prod", 4000),
        ]
    bases = [s[0] for s in sources]

    def _pick(obj, paths, default=None):
        if obj is None:
            return default
        for p in paths:
            cur = obj
            for k in p.split("."):
                if cur is None:
                    break
                if isinstance(cur, dict):
                    cur = cur.get(k)
                else:
                    cur = getattr(cur, k, None)
            if cur not in (None, ""):
                return cur
        return default

    # 2026-05-19 SS-D follow-up: lazy httpx import keeps cold EXE boot ~1.3s faster.
    import httpx

    dash = None
    rka = None
    devs = None
    acts = None
    for base, label, tmo_ms in sources:
        try:
            with httpx.Client(timeout=max(0.5, tmo_ms / 1000.0)) as c:
                d = c.get(f"{base}/api/dashboard/stats")
                if d.status_code == 200:
                    dash = d.json()
                r = c.get(f"{base}/api/harvest/signer-status")
                if r.status_code == 200:
                    rka = r.json()
                dv = c.get(f"{base}/api/harvest/devices")
                if dv.status_code == 200:
                    devs = dv.json()
                ac = c.get(f"{base}/api/actions/status")
                if ac.status_code == 200:
                    acts = ac.json()
            if dash or rka:
                out["panel_online"] = True
                out["source"] = label
                break
        except Exception as e:
            out["errors"].append(f"{base}: {type(e).__name__}")
            continue

    out["accounts"] = _pick(dash, ["accounts.total", "accountCount", "totalAccounts", "accounts"])
    out["videos"] = _pick(dash, ["videos.total", "videoCount", "totalVideos", "videos"])
    out["active"] = _pick(dash, ["accounts.active", "activeAccounts"])
    out["pushes"] = _pick(dash, ["pushes.total", "pushCount", "accounts.pushed"])
    out["banned"] = _pick(dash, ["banned.total", "bannedCount", "accounts.banned"])
    out["rka_online"] = bool(rka)
    if devs:
        if isinstance(devs, list):
            out["devices"] = len(devs)
        elif isinstance(devs, dict):
            if "devices" in devs and isinstance(devs["devices"], list):
                out["devices"] = len(devs["devices"])
            elif "count" in devs:
                out["devices"] = devs["count"]
    out["wired_actions"] = _pick(acts, ["wired", "wiredCount", "total.wired"])
    return out


# --- operator-action queue ---------------------------------------------------
# Reads _shared-memory/OPERATOR-ACTION-QUEUE.md and returns checkbox totals
# grouped by priority bucket. Dashboard tile consumes this for one-glance status.
OPERATOR_ACTION_QUEUE = SANCTUM_ROOT / "_shared-memory" / "OPERATOR-ACTION-QUEUE.md"


@app.get("/api/operator-actions")
def operator_actions():
    """Parse OPERATOR-ACTION-QUEUE.md checkboxes; return counts + items per bucket.

    Defense-in-depth: bails out if the source file is unreasonably large
    (operator queues are bounded in practice; > 256 KB signals corruption).
    """
    if not OPERATOR_ACTION_QUEUE.exists():
        return {"ok": False, "error": f"missing: {OPERATOR_ACTION_QUEUE}"}
    try:
        size = OPERATOR_ACTION_QUEUE.stat().st_size
    except Exception as e:
        return {"ok": False, "error": f"stat failed: {e}"}
    if size > 256_000:
        return {"ok": False, "error": f"file too large ({size} bytes > 256000)"}
    try:
        text = OPERATOR_ACTION_QUEUE.read_text(encoding="utf-8")
    except Exception as e:
        return {"ok": False, "error": f"read failed: {e}"}

    bucket_map = {
        "\U0001F534": "critical",  # red circle
        "\U0001F7E0": "high",      # orange circle
        "\U0001F7E1": "medium",    # yellow circle
        "\U0001F7E2": "low",       # green circle
        "✅": "closed",        # white-check
    }
    bucket = None
    buckets: dict[str, dict] = {}
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("## "):
            head = line[3:].lstrip()
            matched = False
            for emoji, name in bucket_map.items():
                if head.startswith(emoji):
                    bucket = name
                    buckets.setdefault(bucket, {"done": 0, "total": 0, "items": []})
                    matched = True
                    break
            if not matched:
                bucket = None
            continue
        if bucket is None:
            continue
        s = line.lstrip()
        if not s.startswith("- ["):
            continue
        if len(s) < 5:
            continue
        mark = s[3]
        if mark not in (" ", "x", "X"):
            continue
        buckets[bucket]["total"] += 1
        if mark in ("x", "X"):
            buckets[bucket]["done"] += 1
        label = s[5:].strip()
        if label.startswith("] "):
            label = label[2:]
        buckets[bucket]["items"].append({"done": mark in ("x", "X"), "text": label})

    total = sum(b["total"] for b in buckets.values())
    done = sum(b["done"] for b in buckets.values())
    return {
        "ok": True,
        "source": str(OPERATOR_ACTION_QUEUE),
        "total": total,
        "done": done,
        "buckets": buckets,
    }


class LaunchBody(BaseModel):
    project: str
    mode: str = "dev"
    no_notepad: bool = True


class LauncherSpawnBody(BaseModel):
    project: str
    mode: str
    fast: bool = False
    custom_prompt: Optional[str] = None


@app.post("/api/launch")
def launch(payload: LaunchBody):
    """Spawn start-sinister-session.ps1 -Project X -Mode Y. Returns spawn pid."""
    if not LAUNCHER_PS1.exists():
        raise HTTPException(status_code=500, detail=f"launcher not found at {LAUNCHER_PS1}")
    # Validate project against registry
    proj_keys = [p.get("key") for p in _read_projects()]
    if payload.project not in proj_keys:
        raise HTTPException(status_code=400, detail=f"unknown project '{payload.project}' (known: {proj_keys})")
    valid_modes = {"overview", "dev", "audit", "deploy", "push", "debug", "explore"}
    if payload.mode not in valid_modes:
        raise HTTPException(status_code=400, detail=f"invalid mode '{payload.mode}' (must be one of {sorted(valid_modes)})")
    args = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", str(LAUNCHER_PS1),
        "-Project", payload.project,
        "-Mode", payload.mode,
    ]
    if payload.no_notepad:
        args.append("-NoNotepad")
    try:
        # Spawn detached so the new powershell + git-bash window outlives this request
        DETACHED = 0x00000008  # DETACHED_PROCESS on Windows
        proc = subprocess.Popen(
            args,
            creationflags=DETACHED if sys.platform == "win32" else 0,
            close_fds=True,
        )
        return {"ok": True, "pid": proc.pid, "project": payload.project, "mode": payload.mode}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


# --- launcher parity: spawn + options (Thread 5) ---------------------------
# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
# Lets the Console call the launcher with the same surface as
# Start-Sinister-Session.bat: -Project, -Mode, optional -Fast / -CustomPrompt.

@app.post("/api/launcher/spawn")
def launcher_spawn(body: LauncherSpawnBody):
    """Spawn a project/mode session via start-sinister-session.ps1.
    body = {project, mode, fast=False, custom_prompt=None}"""
    ps1 = SANCTUM_ROOT / "automations" / "start-sinister-session.ps1"
    if not ps1.exists():
        raise HTTPException(500, f"launcher missing: {ps1}")
    args = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps1),
            "-Project", body.project, "-Mode", body.mode]
    if body.fast:
        args.append("-Fast")
    if body.custom_prompt:
        args += ["-CustomPrompt", body.custom_prompt]
    proc = subprocess.Popen(args, cwd=str(ps1.parent),
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
    return {"ok": True, "pid": proc.pid, "project": body.project, "mode": body.mode}


@app.get("/api/launcher/options")
def launcher_options():
    proj_file = SANCTUM_ROOT / "automations" / "session-templates" / "projects.json"
    projects = []
    try:
        if proj_file.exists():
            projects = json.loads(proj_file.read_text(encoding="utf-8"))
    except Exception:
        pass
    modes = ["overview", "dev", "audit", "deploy", "push", "debug", "explore"]
    return {"ok": True, "projects": projects, "modes": modes}


# ===== RKOJ :: Cycle points + Scheduler =====================================
# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
# Cycle points = one-click project-state resume (JSON snapshots).
# Scheduler   = cron-like daemon that fires actions (http / script /
# spawn-agent / inbox / resume-cycle) on a 30s tick.

# Local-package imports. The window-manager dir is on sys.path so this
# resolves to ./sanctum_shared/cycle_points.py and
# ./sanctum_shared/scheduler.py. Renamed from `_shared` -> `sanctum_shared`
# on 2026-05-19 to dodge PyInstaller's underscore-prefix data-tuple drop
# (HR-B audit). The hub `_shared` package keeps serving inbox + runlog via
# the sys.path injection up top.
try:
    from sanctum_shared import cycle_points as cp_mod  # type: ignore
    from sanctum_shared import scheduler as sched_mod  # type: ignore
    RKOJ_BACKEND_OK = True
    RKOJ_BACKEND_ERR = None
except Exception as _rkoj_e:  # pragma: no cover
    cp_mod = None  # type: ignore
    sched_mod = None  # type: ignore
    RKOJ_BACKEND_OK = False
    RKOJ_BACKEND_ERR = str(_rkoj_e)


# ---- Scheduler daemon: boot at FastAPI startup ----------------------------
_scheduler_instance = None  # type: ignore


@app.on_event("startup")
async def _start_scheduler():  # pragma: no cover (event handler)
    """Spin up the SchedulerLoop on app start. Failure here MUST NOT crash the
    server — the rest of the API surface stays useful even if scheduler dies."""
    global _scheduler_instance
    if not RKOJ_BACKEND_OK or sched_mod is None:
        return
    try:
        _scheduler_instance = sched_mod.SchedulerLoop(SANCTUM_ROOT, semaphore_size=5)
        await _scheduler_instance.start()
    except Exception as e:
        import logging
        logging.exception("rkoj scheduler start failed: %s", e)


@app.on_event("shutdown")
async def _stop_scheduler():  # pragma: no cover (event handler)
    global _scheduler_instance
    if _scheduler_instance is not None:
        try:
            await _scheduler_instance.stop()
        except Exception:
            pass


# ---- Cycle points endpoints ----------------------------------------------

class CyclePointBody(BaseModel):
    name: str
    project: str
    note: str = ""
    agent: dict
    context: dict = {}
    slug: Optional[str] = None


@app.get("/api/cycle-points")
def cycle_points_list():
    if not RKOJ_BACKEND_OK or cp_mod is None:
        raise HTTPException(503, f"rkoj backend unavailable: {RKOJ_BACKEND_ERR}")
    return {"ok": True, "points": cp_mod.list_cycle_points(SANCTUM_ROOT)}


@app.get("/api/cycle-points/{slug}")
def cycle_points_get(slug: str):
    if not RKOJ_BACKEND_OK or cp_mod is None:
        raise HTTPException(503, f"rkoj backend unavailable: {RKOJ_BACKEND_ERR}")
    cp = cp_mod.load_cycle(SANCTUM_ROOT, slug)
    if not cp:
        raise HTTPException(404, "cycle point not found")
    return {"ok": True, "point": cp}


@app.post("/api/cycle-points")
def cycle_points_create(body: CyclePointBody, request: Request):
    if not RKOJ_BACKEND_OK or cp_mod is None:
        raise HTTPException(503, f"rkoj backend unavailable: {RKOJ_BACKEND_ERR}")
    payload = body.dict()
    payload.setdefault("created_by", request.headers.get("X-Agent", "operator"))
    return cp_mod.save_cycle(SANCTUM_ROOT, payload)


@app.delete("/api/cycle-points/{slug}")
def cycle_points_delete(slug: str):
    if not RKOJ_BACKEND_OK or cp_mod is None:
        raise HTTPException(503, f"rkoj backend unavailable: {RKOJ_BACKEND_ERR}")
    res = cp_mod.delete_cycle(SANCTUM_ROOT, slug)
    if not res.get("ok"):
        raise HTTPException(404, res.get("error", "not found"))
    return res


@app.post("/api/cycle-points/{slug}/resume")
def cycle_points_resume(slug: str):
    """Resume a cycle point: load the JSON, compose launcher params, fire the
    existing /api/launcher/spawn logic. Returns whatever launcher_spawn returns."""
    if not RKOJ_BACKEND_OK or cp_mod is None:
        raise HTTPException(503, f"rkoj backend unavailable: {RKOJ_BACKEND_ERR}")
    cp = cp_mod.load_cycle(SANCTUM_ROOT, slug)
    if not cp:
        raise HTTPException(404, "cycle point not found")
    payload = cp_mod.resume_payload(cp)
    body = LauncherSpawnBody(**payload)
    return launcher_spawn(body)


# ---- Scheduler endpoints --------------------------------------------------

class ScheduleEntryBody(BaseModel):
    name: str
    cron: str
    kind: Literal["script", "spawn-agent", "inbox", "resume-cycle", "http"]
    action: dict
    enabled: bool = True


@app.get("/api/schedule")
def schedule_list():
    if not RKOJ_BACKEND_OK or sched_mod is None:
        raise HTTPException(503, f"rkoj backend unavailable: {RKOJ_BACKEND_ERR}")
    return {"ok": True, "entries": sched_mod.load_schedule(SANCTUM_ROOT)}


@app.post("/api/schedule")
def schedule_add(body: ScheduleEntryBody):
    if not RKOJ_BACKEND_OK or sched_mod is None:
        raise HTTPException(503, f"rkoj backend unavailable: {RKOJ_BACKEND_ERR}")
    entries = sched_mod.load_schedule(SANCTUM_ROOT)
    eid = "sched-" + secrets.token_hex(4)
    entry = body.dict()
    entry["id"] = eid
    entry["created_at"] = datetime.now(timezone.utc).isoformat()
    entry["next_run"] = sched_mod.compute_next(entry["cron"])
    entry["history"] = []
    entries.append(entry)
    sched_mod.save_schedule(SANCTUM_ROOT, entries)
    return {"ok": True, "entry": entry}


@app.patch("/api/schedule/{eid}")
def schedule_patch(eid: str, body: dict):
    if not RKOJ_BACKEND_OK or sched_mod is None:
        raise HTTPException(503, f"rkoj backend unavailable: {RKOJ_BACKEND_ERR}")
    entries = sched_mod.load_schedule(SANCTUM_ROOT)
    for e in entries:
        if e.get("id") == eid:
            e.update(body)
            if "cron" in body:
                e["next_run"] = sched_mod.compute_next(e["cron"])
            sched_mod.save_schedule(SANCTUM_ROOT, entries)
            return {"ok": True, "entry": e}
    raise HTTPException(404, "schedule entry not found")


@app.delete("/api/schedule/{eid}")
def schedule_delete(eid: str):
    if not RKOJ_BACKEND_OK or sched_mod is None:
        raise HTTPException(503, f"rkoj backend unavailable: {RKOJ_BACKEND_ERR}")
    entries = sched_mod.load_schedule(SANCTUM_ROOT)
    before = len(entries)
    entries = [e for e in entries if e.get("id") != eid]
    if len(entries) == before:
        raise HTTPException(404, "schedule entry not found")
    sched_mod.save_schedule(SANCTUM_ROOT, entries)
    return {"ok": True}


@app.post("/api/schedule/{eid}/run-now")
async def schedule_run_now(eid: str):
    if not RKOJ_BACKEND_OK or sched_mod is None:
        raise HTTPException(503, f"rkoj backend unavailable: {RKOJ_BACKEND_ERR}")
    entries = sched_mod.load_schedule(SANCTUM_ROOT)
    for e in entries:
        if e.get("id") == eid:
            result = await sched_mod.fire_action(e)
            e["last_run"] = {"at": datetime.now(timezone.utc).isoformat(), **result}
            sched_mod.save_schedule(SANCTUM_ROOT, entries)
            return {"ok": True, **result}
    raise HTTPException(404, "schedule entry not found")


# ---------------------------------------------------------------- vault proxies ----
# Author: Sinister Sanctum SV-A agent (Claude) :: 2026-05-19
# Thin loopback proxies into the Sinister Vault daemon on port 5078. httpx
# is lazy-imported inside each proxy (2026-05-19 SS-D follow-up: cold boot
# perf), so the Vault drawer can fetch /api/vault/* on same origin (no CORS).
# If the daemon is offline, return a shaped "vault_offline" payload so the UI
# can render a graceful empty state instead of a 5xx.

VAULT_DAEMON_BASE = "http://127.0.0.1:5078"


@app.get("/api/vault/health")
async def vault_health_proxy():
    # 2026-05-19 SS-D follow-up: lazy httpx import keeps cold EXE boot ~1.3s faster.
    import httpx
    try:
        async with httpx.AsyncClient(timeout=2.0) as c:
            r = await c.get(f"{VAULT_DAEMON_BASE}/api/vault/health")
            return r.json()
    except Exception as e:
        return {"ok": False, "error": str(e), "vault_offline": True}


@app.get("/api/vault/quota")
async def vault_quota_proxy():
    # 2026-05-19 SS-D follow-up: lazy httpx import keeps cold EXE boot ~1.3s faster.
    import httpx
    try:
        async with httpx.AsyncClient(timeout=2.0) as c:
            r = await c.get(f"{VAULT_DAEMON_BASE}/api/vault/quota")
            return r.json()
    except Exception as e:
        return {"ok": False, "error": str(e), "vault_offline": True}


@app.get("/api/vault/audit")
async def vault_audit_proxy(limit: int = 50):
    # 2026-05-19 SS-D follow-up: lazy httpx import keeps cold EXE boot ~1.3s faster.
    import httpx
    try:
        async with httpx.AsyncClient(timeout=2.0) as c:
            r = await c.get(f"{VAULT_DAEMON_BASE}/api/vault/audit", params={"limit": limit})
            return r.json()
    except Exception:
        return {"ok": False, "events": [], "vault_offline": True}


# ---------------------------------------------------------------- shared-memory ----

SHARED_MEM_DIR = SANCTUM_ROOT / "_shared-memory"
PROGRESS_DIR = SHARED_MEM_DIR / "PROGRESS"
KNOWLEDGE_DIR = SHARED_MEM_DIR / "knowledge"


# --- knowledge base (the Sanctum brain) -------------------------------------

@app.get("/api/knowledge")
def knowledge_list(search: str = ""):
    """List every knowledge topic. Optional ?search=<keyword> filters by file-content match."""
    out = []
    if not KNOWLEDGE_DIR.exists():
        return {"ok": True, "topics": []}
    needle = search.lower().strip()
    for f in sorted(KNOWLEDGE_DIR.glob("*.md")):
        if f.name.startswith("_"):
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except Exception:
            continue
        if needle and needle not in text.lower():
            continue
        # Parse title + status from header
        title = f.stem.replace("-", " ")
        status = "unknown"
        tags = []
        for line in text.splitlines()[:40]:
            if line.startswith("# Topic:"):
                title = line.replace("# Topic:", "").strip()
            elif line.startswith("**Status:**"):
                status = line.replace("**Status:**", "").strip().split()[0].lower()
            elif line.startswith("**Tags:**"):
                tags = [t.strip() for t in line.replace("**Tags:**", "").split(",") if t.strip()]
        out.append({
            "slug": f.stem,
            "title": title,
            "status": status,
            "tags": tags,
            "size": f.stat().st_size,
            "mtime": f.stat().st_mtime,
        })
    out.sort(key=lambda t: t["mtime"], reverse=True)
    return {"ok": True, "count": len(out), "topics": out}


@app.get("/api/knowledge/{slug}")
def knowledge_read(slug: str):
    """Return the raw markdown for a topic."""
    safe = "".join(c for c in slug if c.isalnum() or c in "-_")
    if not safe:
        raise HTTPException(status_code=400, detail="invalid slug")
    f = KNOWLEDGE_DIR / f"{safe}.md"
    if not f.exists():
        raise HTTPException(status_code=404, detail=f"no such topic: {slug}")
    return {"ok": True, "slug": safe, "markdown": f.read_text(encoding="utf-8")}


class KnowledgeAppend(BaseModel):
    slug: str
    agent: str
    kind: str = "discovery"   # discovery | fix | workaround | superseded
    title: str
    body: str = ""
    new_status: str | None = None


@app.post("/api/knowledge/append")
def knowledge_append(payload: KnowledgeAppend):
    """Append a discovery to an existing topic, OR create a new topic from the template."""
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    safe = "".join(c if c.isalnum() or c == "-" else "-" for c in payload.slug.lower()).strip("-")
    if not safe:
        raise HTTPException(status_code=400, detail="invalid slug")
    if not payload.agent.strip() or not payload.title.strip():
        raise HTTPException(status_code=400, detail="agent + title required")
    # Memory-poisoning defense
    blk = _sanitize_or_block(f"knowledge:{safe}", payload.agent, payload.title, payload.body or "")
    if blk:
        raise blk
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    fpath = KNOWLEDGE_DIR / f"{safe}.md"
    body = payload.body.strip() or "(no body)"
    new_entry = f"### {ts} by {payload.agent}\n{body}\n\n"
    if fpath.exists():
        # Append to existing — insert at top of "Discoveries" section
        text = fpath.read_text(encoding="utf-8")
        pivot = text.find("## Discoveries")
        if pivot >= 0:
            head_end = text.find("\n", pivot)
            # skip the next newline + look for the next "### " or end-of-section
            insert_at = text.find("\n", head_end + 1) + 1
            new_text = text[:insert_at] + "\n" + new_entry + text[insert_at:]
        else:
            new_text = text.rstrip() + "\n\n## Discoveries\n\n" + new_entry
        # Optionally update Last updated + Status
        new_text = _update_topic_meta(new_text, ts, payload.agent, payload.new_status)
        fpath.write_text(new_text, encoding="utf-8")
        return {"ok": True, "action": "appended", "slug": safe, "path": str(fpath)}
    else:
        # Create new topic from template skeleton
        tmpl = (
            f"> **Author:** {payload.agent} :: {ts.split()[0]}\n\n"
            f"# Topic: {payload.title}\n\n"
            f"**Slug:** {safe}\n"
            f"**First discovered:** {ts} by {payload.agent}\n"
            f"**Last updated:** {ts} by {payload.agent}\n"
            f"**Status:** {payload.new_status or 'open'}\n"
            f"**Tags:** (add tags)\n\n"
            f"## Problem\n\n{body}\n\n"
            f"## Why it happens\n\n(root cause TBD)\n\n"
            f"## Fix or workaround\n\n(TBD)\n\n"
            f"## Discoveries (append-only log, most-recent at top)\n\n"
            f"### {ts} by {payload.agent}\n{body}\n"
        )
        fpath.write_text(tmpl, encoding="utf-8")
        # Append to _INDEX.md
        idx_path = KNOWLEDGE_DIR / "_INDEX.md"
        if idx_path.exists():
            idx = idx_path.read_text(encoding="utf-8")
            new_row = f"| {safe} | {payload.title} | {payload.new_status or 'open'} | | {ts.split()[0]} | {ts.split()[0]} |\n"
            # Insert below the table header
            lines = idx.splitlines(keepends=True)
            for i, ln in enumerate(lines):
                if ln.startswith("|---"):
                    lines.insert(i + 1, new_row)
                    break
            idx_path.write_text("".join(lines), encoding="utf-8")
        return {"ok": True, "action": "created", "slug": safe, "path": str(fpath)}


def _update_topic_meta(text: str, ts: str, agent: str, new_status: str | None) -> str:
    """Update Last updated + (optionally) Status lines in a topic file."""
    out_lines = []
    for line in text.splitlines():
        if line.startswith("**Last updated:**"):
            out_lines.append(f"**Last updated:** {ts} by {agent}")
        elif new_status and line.startswith("**Status:**"):
            out_lines.append(f"**Status:** {new_status}")
        else:
            out_lines.append(line)
    return "\n".join(out_lines) + ("\n" if text.endswith("\n") else "")


# --- codex companion (OpenAI peer-review skill) -----------------------------
# Lazy-imported on first request so the Console can boot without the openai
# package installed. See D:\Sinister Sanctum\tools\codex-companion\README.md.

CODEX_DIR = SANCTUM_ROOT / "tools" / "codex-companion"
CODEX_REVIEWS_DIR = SANCTUM_ROOT / "_shared-memory" / "codex-reviews"
_codex_mod = None
_codex_err: str | None = None


def _get_codex():
    """Lazy-import codex.py from tools/codex-companion/. Returns (module, err)."""
    global _codex_mod, _codex_err
    if _codex_mod is not None:
        return _codex_mod, None
    if _codex_err is not None:
        return None, _codex_err
    try:
        if str(CODEX_DIR) not in sys.path:
            sys.path.insert(0, str(CODEX_DIR))
        import codex as _cx  # type: ignore
        _codex_mod = _cx
        return _cx, None
    except Exception as e:
        _codex_err = f"codex module unavailable: {type(e).__name__}: {e}"
        return None, _codex_err


class CodexReviewBody(BaseModel):
    content: str
    context: str = ""
    language: str = "python"
    depth: str = "standard"   # quick | standard | deep


@app.post("/api/codex/review")
def codex_review(payload: CodexReviewBody):
    """Peer-review a code blob / diff via OpenAI Codex-grade models.
    Returns the structured verdict dict. See tools/codex-companion/README.md."""
    if not payload.content.strip():
        raise HTTPException(status_code=400, detail="content required")
    if payload.depth not in ("quick", "standard", "deep"):
        raise HTTPException(status_code=400, detail="depth must be quick|standard|deep")
    cx, err = _get_codex()
    if cx is None:
        return JSONResponse({"ok": False, "error": err}, status_code=200)
    try:
        result = cx.review(
            payload.content,
            context=payload.context,
            language=payload.language,
            depth=payload.depth,
        )
        return result
    except Exception as e:
        return JSONResponse({"ok": False, "error": f"{type(e).__name__}: {e}"},
                            status_code=200)


@app.get("/api/codex/reviews")
def codex_reviews_list(limit: int = 20):
    """List recent codex reviews (filename, verdict, summary, mtime)."""
    if not CODEX_REVIEWS_DIR.exists():
        return {"ok": True, "reviews": [], "source": "empty"}
    files = sorted(CODEX_REVIEWS_DIR.glob("*.json"),
                   key=lambda p: p.stat().st_mtime, reverse=True)[:max(1, limit)]
    out = []
    for f in files:
        item: dict[str, Any] = {
            "id": f.stem,
            "filename": f.name,
            "size": f.stat().st_size,
            "mtime": f.stat().st_mtime,
            "verdict": None,
            "summary": None,
            "model": None,
            "depth": None,
        }
        try:
            obj = json.loads(f.read_text(encoding="utf-8"))
            item["verdict"] = obj.get("verdict")
            item["model"] = obj.get("model")
            item["depth"] = obj.get("depth")
            s = (obj.get("summary") or "").strip()
            item["summary"] = (s[:280] + "...") if len(s) > 280 else s
            item["ok"] = obj.get("ok", True)
        except Exception as e:
            item["error"] = str(e)
        out.append(item)
    return {"ok": True, "count": len(out), "reviews": out}


@app.get("/api/codex/review/{review_id}")
def codex_review_read(review_id: str):
    """Return a single codex review JSON in full."""
    safe = "".join(c for c in review_id if c.isalnum() or c in "-_T")
    if not safe:
        raise HTTPException(status_code=400, detail="invalid review id")
    f = CODEX_REVIEWS_DIR / f"{safe}.json"
    if not f.exists():
        raise HTTPException(status_code=404, detail=f"no such review: {review_id}")
    try:
        return {"ok": True, "id": safe, "review": json.loads(f.read_text(encoding="utf-8"))}
    except Exception as e:
        return JSONResponse({"ok": False, "id": safe, "error": str(e)}, status_code=500)


def _parse_progress_md(text: str, agent: str) -> list[dict[str, Any]]:
    """Crude parser: split on lines starting with '## '. Each section becomes an entry."""
    entries = []
    cur = None
    for line in text.splitlines():
        if line.startswith("## "):
            if cur:
                entries.append(cur)
            header = line[3:].strip()
            # try "YYYY-MM-DD HH:MM - status: title"
            ts = ""
            status = "note"
            title = header
            try:
                first_dash = header.find(" - ")
                if first_dash > 0:
                    ts = header[:first_dash].strip()
                    rest = header[first_dash + 3:].strip()
                    colon = rest.find(":")
                    if colon > 0:
                        status = rest[:colon].strip().lower()
                        title = rest[colon + 1:].strip()
                    else:
                        title = rest
            except Exception:
                pass
            cur = {"agent": agent, "ts": ts, "status": status, "title": title, "body": ""}
        elif cur is not None:
            cur["body"] += line + "\n"
    if cur:
        entries.append(cur)
    return entries


@app.get("/api/progress")
def progress_feed(limit: int = 50):
    """Aggregate progress across all agents. Returns newest-first up to `limit`."""
    out = []
    if PROGRESS_DIR.exists():
        for f in PROGRESS_DIR.glob("*.md"):
            if f.name.startswith("_") or f.name.lower() == "readme.md":
                continue
            agent = f.stem
            try:
                text = f.read_text(encoding="utf-8")
            except Exception:
                continue
            out.extend(_parse_progress_md(text, agent))
    # Sort by timestamp string (works for YYYY-MM-DD HH:MM lex-order)
    out.sort(key=lambda e: e.get("ts", ""), reverse=True)
    # Trim each body to ~280 chars for the feed
    for e in out:
        b = e.get("body", "").strip()
        if len(b) > 280:
            e["body"] = b[:280] + "..."
        else:
            e["body"] = b
    return {"ok": True, "count": len(out[:limit]), "total": len(out), "entries": out[:limit]}


class ProgressAppend(BaseModel):
    agent: str
    status: str = "note"   # started | shipped | blocked | paused | note | failed
    title: str
    body: str = ""


@app.post("/api/progress/append")
def progress_append(payload: ProgressAppend):
    """Append a progress entry for an agent. Prepends to top of agent's md file."""
    if not payload.agent.strip() or not payload.title.strip():
        raise HTTPException(status_code=400, detail="agent + title required")
    PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
    # Sanitize agent name to a filesystem-safe filename (keep spaces; strip dangerous chars)
    safe = "".join(c for c in payload.agent if c.isalnum() or c in " -_").strip()
    if not safe:
        raise HTTPException(status_code=400, detail="agent name must contain alphanumerics")
    fpath = PROGRESS_DIR / f"{safe}.md"
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"## {ts} - {payload.status}: {payload.title}\n{payload.body.strip()}\n\n"
    if fpath.exists():
        existing = fpath.read_text(encoding="utf-8")
        # Find pivot after '---' separator if present
        pivot = existing.find("---\n")
        if pivot >= 0:
            head = existing[:pivot + 4]
            tail = existing[pivot + 4:]
            fpath.write_text(head + "\n" + entry + tail, encoding="utf-8")
        else:
            fpath.write_text(existing.rstrip() + "\n\n" + entry, encoding="utf-8")
    else:
        header = f"# Agent: {payload.agent}\n\nAppend-only progress log. Most recent at top.\n\n---\n\n{entry}"
        fpath.write_text(header, encoding="utf-8")
    return {"ok": True, "path": str(fpath), "agent": payload.agent, "ts": ts}


@app.get("/api/shared-memory")
def shared_memory_read():
    """Return current contents of DIRECTIVES.md + WORK-TOWARD.md + a list of notes."""
    out = {"ok": True, "directives": "", "work_toward": "", "notes": []}
    dpath = SHARED_MEM_DIR / "DIRECTIVES.md"
    wpath = SHARED_MEM_DIR / "WORK-TOWARD.md"
    npath = SHARED_MEM_DIR / "notes"
    if dpath.exists(): out["directives"] = dpath.read_text(encoding="utf-8")
    if wpath.exists(): out["work_toward"] = wpath.read_text(encoding="utf-8")
    if npath.exists():
        for f in sorted(npath.glob("*.md"), reverse=True)[:20]:
            out["notes"].append({"name": f.name, "size": f.stat().st_size, "mtime": f.stat().st_mtime})
    return out


class SharedMemAppend(BaseModel):
    target: str  # 'directives' | 'work_toward' | 'note'
    title: str
    body: str = ""


@app.post("/api/shared-memory/append")
def shared_memory_append(payload: SharedMemAppend):
    """Append a timestamped entry to DIRECTIVES.md / WORK-TOWARD.md / new note."""
    if not payload.title.strip():
        raise HTTPException(status_code=400, detail="title required")
    # Memory-poisoning defense
    blk = _sanitize_or_block(f"shared-memory:{payload.target}", "(unknown agent)", payload.title, payload.body or "")
    if blk:
        raise blk
    SHARED_MEM_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M")
    body = payload.body or ""

    if payload.target == "note":
        slug = "".join(c if c.isalnum() or c == "-" else "-" for c in payload.title.lower()).strip("-")[:40]
        date_prefix = datetime.now().strftime("%Y-%m-%d")
        notes_dir = SHARED_MEM_DIR / "notes"
        notes_dir.mkdir(parents=True, exist_ok=True)
        path = notes_dir / f"{date_prefix}-{slug}.md"
        content = f"# {payload.title}\n\n**Captured:** {ts}\n**Origin:** window-manager UI\n\n{body}\n"
        path.write_text(content, encoding="utf-8")
        return {"ok": True, "path": str(path)}

    fname = {"directives": "DIRECTIVES.md", "work_toward": "WORK-TOWARD.md"}.get(payload.target)
    if not fname:
        raise HTTPException(status_code=400, detail="target must be 'directives' | 'work_toward' | 'note'")
    path = SHARED_MEM_DIR / fname
    existing = path.read_text(encoding="utf-8") if path.exists() else f"# {fname}\n\n---\n"
    entry = f"\n## {ts} - {payload.title}\n\n{body}\n"
    # Insert after the first '---' separator (so newest is at top)
    pivot = existing.find("---\n")
    if pivot < 0:
        new = existing.rstrip() + "\n\n" + entry
    else:
        head = existing[:pivot + 4]
        tail = existing[pivot + 4:]
        new = head + entry + tail
    path.write_text(new, encoding="utf-8")
    return {"ok": True, "path": str(path)}


# ---------------------------------------------------------------- skills / tools / inventions ----
# Browsable markdown collections living under D:\Sinister Sanctum\{skills,tools,inventions}.
# All three use the same shape: a list endpoint returns [{slug, title, summary, mtime}],
# a read endpoint returns {ok, slug, title, markdown, mtime}.
# Slug sanitization: [a-zA-Z0-9-]+ only; anything else -> HTTP 400.

import re as _re

SKILLS_DIR = SANCTUM_ROOT / "skills"
TOOLS_DIR = SANCTUM_ROOT / "tools"
INVENTIONS_DIR = SANCTUM_ROOT / "inventions"

_SLUG_RX = _re.compile(r"^[a-zA-Z0-9-]+$")


def _check_slug(slug: str) -> str:
    if not slug or not _SLUG_RX.match(slug):
        raise HTTPException(status_code=400, detail="invalid slug (allowed: a-z A-Z 0-9 -)")
    return slug


def _md_extract_summary(text: str, max_len: int = 140) -> tuple[str, str]:
    """Pull a (title, summary) pair out of a markdown blob.
    title := first '# ...' heading (or filename stem if none).
    summary := first non-empty, non-heading, non-frontmatter line."""
    title = ""
    summary = ""
    in_frontmatter = False
    for i, raw in enumerate(text.splitlines()):
        line = raw.strip()
        if i == 0 and line == "---":
            in_frontmatter = True
            continue
        if in_frontmatter:
            if line == "---":
                in_frontmatter = False
            continue
        if not line:
            continue
        if line.startswith("#") and not title:
            title = line.lstrip("#").strip()
            continue
        if not summary and not line.startswith("#") and not line.startswith(">"):
            summary = line
            if title:
                break
    if len(summary) > max_len:
        summary = summary[:max_len].rstrip() + "..."
    return title, summary


def _list_md_dir(root: Path, *, skip_names: set[str] | None = None,
                 newest_first_by_filename: bool = False) -> list[dict[str, Any]]:
    """Generic .md collection lister. skip_names is a set of lowercase filenames to ignore."""
    skip_names = skip_names or set()
    out: list[dict[str, Any]] = []
    if not root.exists():
        return out
    for f in root.glob("*.md"):
        if not f.is_file():
            continue
        lname = f.name.lower()
        if lname in skip_names or lname.startswith("_"):
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except Exception:
            continue
        title, summary = _md_extract_summary(text)
        if not title:
            title = f.stem.replace("-", " ").replace("_", " ")
        out.append({
            "slug": f.stem,
            "title": title,
            "summary": summary,
            "mtime": f.stat().st_mtime,
            "size": f.stat().st_size,
        })
    if newest_first_by_filename:
        # Inventions are prefixed YYYY-MM-DD-; lex sort descending gives newest first.
        out.sort(key=lambda r: r["slug"], reverse=True)
    else:
        out.sort(key=lambda r: r["title"].lower())
    return out


def _list_tools_dir() -> list[dict[str, Any]]:
    """Tools live as subdirectories with a README.md inside (plus a top-level _INDEX.md
    used for human-readable navigation). Each subdir's README is the tool's primary doc."""
    out: list[dict[str, Any]] = []
    if not TOOLS_DIR.exists():
        return out
    for d in TOOLS_DIR.iterdir():
        if not d.is_dir():
            continue
        if d.name.startswith("_") or d.name.startswith("."):
            continue
        readme = d / "README.md"
        if not readme.exists():
            continue
        # Slug must be safe for the URL pattern.
        slug = d.name
        if not _SLUG_RX.match(slug):
            continue
        try:
            text = readme.read_text(encoding="utf-8")
        except Exception:
            continue
        title, summary = _md_extract_summary(text)
        if not title:
            title = slug.replace("-", " ").replace("_", " ")
        out.append({
            "slug": slug,
            "title": title,
            "summary": summary,
            "mtime": readme.stat().st_mtime,
            "size": readme.stat().st_size,
        })
    out.sort(key=lambda r: r["title"].lower())
    return out


@app.get("/api/skills")
def skills_list():
    """List all skills (D:\\Sinister Sanctum\\skills\\*.md, minus _INDEX/_template)."""
    items = _list_md_dir(SKILLS_DIR, skip_names={"readme.md", "_index.md", "_template.md"})
    return {"ok": True, "items": items, "count": len(items)}


@app.get("/api/skills/{slug}")
def skills_read(slug: str):
    safe = _check_slug(slug)
    f = SKILLS_DIR / f"{safe}.md"
    if not f.exists():
        raise HTTPException(status_code=404, detail=f"no such skill: {slug}")
    text = f.read_text(encoding="utf-8")
    title, _ = _md_extract_summary(text)
    return {
        "ok": True,
        "slug": safe,
        "title": title or safe,
        "markdown": text,
        "mtime": f.stat().st_mtime,
    }


@app.get("/api/tools")
def tools_list():
    """List all tools (each is a subdirectory under D:\\Sinister Sanctum\\tools\\ with README.md)."""
    items = _list_tools_dir()
    return {"ok": True, "items": items, "count": len(items)}


@app.get("/api/tools/{slug}")
def tools_read(slug: str):
    safe = _check_slug(slug)
    d = TOOLS_DIR / safe
    readme = d / "README.md"
    if not d.is_dir() or not readme.exists():
        raise HTTPException(status_code=404, detail=f"no such tool: {slug}")
    text = readme.read_text(encoding="utf-8")
    title, _ = _md_extract_summary(text)
    return {
        "ok": True,
        "slug": safe,
        "title": title or safe,
        "markdown": text,
        "mtime": readme.stat().st_mtime,
    }


@app.get("/api/inventions")
def inventions_list():
    """List all inventions, newest-first by YYYY-MM-DD- filename prefix.
    Skips README.md, _template.md, _INDEX.md."""
    items = _list_md_dir(
        INVENTIONS_DIR,
        skip_names={"readme.md", "_template.md", "_index.md"},
        newest_first_by_filename=True,
    )
    return {"ok": True, "items": items, "count": len(items)}


@app.get("/api/inventions/{slug}")
def inventions_read(slug: str):
    safe = _check_slug(slug)
    f = INVENTIONS_DIR / f"{safe}.md"
    if not f.exists():
        raise HTTPException(status_code=404, detail=f"no such invention: {slug}")
    text = f.read_text(encoding="utf-8")
    title, _ = _md_extract_summary(text)
    return {
        "ok": True,
        "slug": safe,
        "title": title or safe,
        "markdown": text,
        "mtime": f.stat().st_mtime,
    }


@app.get("/api/skills/hub")
def skills_hub():
    """Skills Hub registry: parsed _REGISTRY.yaml -> JSON.

    Single source of truth lives at skills/_REGISTRY.yaml. The companion
    skills/HUB.md (human-readable) is regenerated by
    automations/sync-fleet.ps1 -Apply. This endpoint is read-only and is the
    canonical machine-readable view of every Sanctum bot/tool/skill/external/
    invention with status, install_state, and security posture.
    """
    if not HUB_REGISTRY_PATH.exists():
        raise HTTPException(status_code=404, detail="_REGISTRY.yaml not found")
    try:
        import yaml as _yaml  # local import so server.py still boots if pyyaml is absent in the venv
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="pyyaml not installed in window-manager venv; run: pip install pyyaml",
        )
    try:
        data = _yaml.safe_load(HUB_REGISTRY_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"YAML parse failed: {e}")
    categories = ("bots", "tools", "skills", "externals", "inventions")
    counts = {cat: len(data.get(cat, []) or []) for cat in categories}
    counts["total"] = sum(counts.values())
    return {
        "ok": True,
        "version": data.get("version"),
        "generated": data.get("generated"),
        "generated_by": data.get("generated_by"),
        "counts": counts,
        "categories": {cat: data.get(cat, []) or [] for cat in categories},
        "mtime": HUB_REGISTRY_PATH.stat().st_mtime,
    }


# ---------------------------------------------------------------- LAN ------

def _lan_ip() -> str:
    """Best-effort LAN IP discovery."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"


@app.get("/api/connect-info")
def connect_info():
    """Returns the LAN URL + bearer token for phone clients. Loopback-only when
    LAN mode is off (so the operator on PC can still scan to phone)."""
    ip = _lan_ip()
    return {
        "ok": True,
        "lan_mode": LAN_MODE,
        "host": ip,
        "port": PORT,
        "loopback_url": f"http://127.0.0.1:{PORT}/",
        "lan_url": f"http://{ip}:{PORT}/" if LAN_MODE else None,
        "mobile_url": f"http://{ip}:{PORT}/m?t={LAN_TOKEN}" if LAN_MODE else None,
        "token": LAN_TOKEN if LAN_MODE else None,
    }


@app.get("/api/qr")
def qr_png():
    """QR PNG encoding the mobile URL + token (so the phone scans + lands
    with the token already in the URL → app.js stashes it in localStorage)."""
    if not LAN_MODE:
        raise HTTPException(status_code=400, detail="LAN mode is off; nothing to QR")
    import io
    import qrcode  # type: ignore
    ip = _lan_ip()
    url = f"http://{ip}:{PORT}/m?t={LAN_TOKEN}"
    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return Response(content=buf.getvalue(), media_type="image/png")


# ---------------------------------------------------------------- static ----

@app.get("/")
def root():
    idx = WEB_DIR / "index.html"
    if not idx.exists():
        raise HTTPException(status_code=500, detail=f"missing {idx}")
    return FileResponse(idx, media_type="text/html")


@app.get("/m")
def mobile_entry():
    """Mobile entry page: captures ?t=<token> from URL, stashes in localStorage,
    then redirects to /. The main app.js reads localStorage and adds the token
    to every fetch's Authorization header."""
    mob = WEB_DIR / "mobile.html"
    if not mob.exists():
        raise HTTPException(status_code=500, detail=f"missing {mob}")
    return FileResponse(mob, media_type="text/html")


@app.get("/m/{view}")
def mobile_deep_link(view: str):
    """Deep-link entry: /m/requests, /m/inbox, /m/dashboard, /m/progress, /m/knowledge.
    Same HTML shell; mobile.js routes client-side based on URL path."""
    allowed = {"requests", "inbox", "dashboard", "progress", "knowledge"}
    if view not in allowed:
        raise HTTPException(status_code=404, detail=f"unknown mobile view '{view}'")
    mob = WEB_DIR / "mobile.html"
    if not mob.exists():
        raise HTTPException(status_code=500, detail=f"missing {mob}")
    return FileResponse(mob, media_type="text/html")


# ---------------------------------------------------------------- hot-reload SSE ----
# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
# Why: operator wants to ship updates to the workbench WITHOUT restarting RKOJ
# (mid-flight agents would lose context, popouts would close, palette state would
# evaporate). A long-poll SSE channel tied to a watchdog observer lets the
# frontend hot-patch CSS by URL-bumping the <link> href (zero context loss), and
# softly nag the operator for JS / HTML / template changes (those need a full
# reload — operator decides when). Pairs with the agent-side `[UPDATE]` inbox
# pattern (DIRECTIVES.md 2026-05-19): one mechanism for the workbench surface,
# the other for spawned Claude sessions, same overall shape.
# Knowledge: rkoj-hot-reload-pattern.md
_sse_subscribers: "set[asyncio.Queue]" = set()
_sse_lock = threading.Lock()
_sse_observer = None  # watchdog Observer instance, lazily started
_sse_loop: "asyncio.AbstractEventLoop | None" = None

_HR_EXT_KIND = {
    ".css": "css", ".js": "js", ".html": "html", ".htm": "html",
    ".png": "img", ".ico": "img", ".jpg": "img", ".jpeg": "img",
    ".svg": "img", ".gif": "img", ".webp": "img",
}


def _hr_classify(path: Path) -> str | None:
    return _HR_EXT_KIND.get(path.suffix.lower())


def _hr_emit(kind: str, rel_path: str, mtime: float) -> None:
    """Broadcast a file-changed event to every connected SSE subscriber.
    Called from the watchdog thread; uses call_soon_threadsafe to cross into the
    asyncio loop where the subscriber queues live."""
    if _sse_loop is None:
        return
    payload = {"path": rel_path, "kind": kind, "mtime": mtime}
    with _sse_lock:
        targets = list(_sse_subscribers)
    for q in targets:
        try:
            _sse_loop.call_soon_threadsafe(q.put_nowait, payload)
        except Exception:
            pass


def _start_hot_reload_watcher() -> None:
    """Wire watchdog against ./web/. Idempotent. Silent on missing dep."""
    global _sse_observer
    if _sse_observer is not None or not WEB_DIR.exists():
        return
    try:
        from watchdog.observers import Observer  # type: ignore
        from watchdog.events import FileSystemEventHandler  # type: ignore
    except Exception:
        return  # watchdog not installed; SSE channel stays open but stays silent

    # Debounce: editors often emit two events per save (write + rename). Coalesce.
    _last_emit: dict[str, float] = {}
    # 2026-05-19 SS-D follow-up: reduced from 400ms — operator wants faster CSS roundtrip.
    DEBOUNCE_S = 0.15

    class _H(FileSystemEventHandler):
        def _maybe_emit(self, src_path: str) -> None:
            try:
                p = Path(src_path)
            except Exception:
                return
            kind = _hr_classify(p)
            if kind is None:
                return
            try:
                rel = str(p.relative_to(WEB_DIR)).replace("\\", "/")
            except Exception:
                rel = p.name
            now = time.time()
            last = _last_emit.get(rel, 0.0)
            if (now - last) < DEBOUNCE_S:
                return
            _last_emit[rel] = now
            try:
                mt = p.stat().st_mtime
            except Exception:
                mt = now
            _hr_emit(kind, rel, mt)

        def on_modified(self, event):
            if getattr(event, "is_directory", False):
                return
            self._maybe_emit(event.src_path)

        def on_created(self, event):
            if getattr(event, "is_directory", False):
                return
            self._maybe_emit(event.src_path)

        def on_moved(self, event):
            if getattr(event, "is_directory", False):
                return
            dst = getattr(event, "dest_path", None) or event.src_path
            self._maybe_emit(dst)

    try:
        obs = Observer()
        obs.schedule(_H(), str(WEB_DIR), recursive=True)
        obs.daemon = True
        obs.start()
        _sse_observer = obs
    except Exception:
        _sse_observer = None


@app.on_event("startup")
async def _hot_reload_startup() -> None:  # pragma: no cover
    global _sse_loop
    _sse_loop = asyncio.get_running_loop()
    _start_hot_reload_watcher()


@app.on_event("shutdown")
async def _hot_reload_shutdown() -> None:  # pragma: no cover
    global _sse_observer
    if _sse_observer is not None:
        try:
            _sse_observer.stop()
            _sse_observer.join(timeout=2.0)
        except Exception:
            pass
        _sse_observer = None


@app.get("/api/sse/changes")
async def sse_changes(request: Request):
    """Server-sent events stream for live file changes in ./web/.

    Frontend opens `new EventSource('/api/sse/changes')`. On `file-changed`
    events the client decides what to do:
      - CSS: bump the <link>'s href ?v=<mtime> -> browser refetches, no reload
      - JS / HTML: surface a toast, operator clicks to do a full reload
      - PNG/ICO/etc: bump <img src> on matching elements

    Heartbeat every 15s as a comment line (`:hb`) so dead connections drop
    promptly and intermediate proxies don't buffer indefinitely.
    """

    async def event_stream():
        q: asyncio.Queue = asyncio.Queue(maxsize=64)
        with _sse_lock:
            _sse_subscribers.add(q)
        try:
            # Hello frame so the client knows the channel is live + can compute
            # reconnect-recovery state (first message is always a hello).
            hello = {
                "kind": "hello",
                "ts": datetime.now(timezone.utc).isoformat(),
                "watcher": _sse_observer is not None,
                "version": VERSION,
            }
            yield f"event: hello\ndata: {json.dumps(hello)}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    payload = await asyncio.wait_for(q.get(), timeout=15.0)
                except asyncio.TimeoutError:
                    yield ":hb\n\n"
                    continue
                yield f"event: file-changed\ndata: {json.dumps(payload)}\n\n"
        finally:
            with _sse_lock:
                _sse_subscribers.discard(q)

    headers = {
        "Cache-Control": "no-cache, no-transform",
        "X-Accel-Buffering": "no",
        "Connection": "keep-alive",
    }
    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=headers)


# ---------------------------------------------------------------- heartbeat / [UPDATE] inbox broadcast ----
# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
# Companion to /api/inbox/broadcast — surfaces the standing `[UPDATE]` subkinds
# (DIRECTIVES.md 2026-05-19) as first-class endpoints so the operator's "Ping
# all" button + ribbon helpers don't have to assemble the body themselves.

_VALID_UPDATE_SUBKINDS = {
    "refresh-prefs",
    "branch-switch",
    "palette-rebuild",
    "knowledge-recheck",
    "noop",
}


class UpdatePingBody(BaseModel):
    subkind: str = "noop"            # one of _VALID_UPDATE_SUBKINDS
    args: dict[str, Any] = {}        # {new: "<branch>"} for branch-switch, {slug: "<name>"} for knowledge-recheck
    to: Optional[str] = None         # if set, single-agent ping; else broadcast
    from_agent: str = "operator"
    exclude: List[str] = []          # broadcast only


def _format_update_body(subkind: str, args: dict[str, Any]) -> str:
    if subkind == "branch-switch":
        new = (args or {}).get("new", "main")
        return f"[UPDATE] branch-switch new={new}"
    if subkind == "knowledge-recheck":
        slug = (args or {}).get("slug", "")
        return f"[UPDATE] knowledge-recheck slug={slug}"
    return f"[UPDATE] {subkind}"


# ============================================================ runtime heartbeat ====
# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
# HR-B audit (PROGRESS 11:17) flagged _shared-memory/heartbeats/ as containing
# BUILD stamps only — no daemon wrote a runtime heartbeat. install-rkoj-task.ps1
# documents rkoj-runtime.beat as the liveness signal; this loop is what produces
# it. Cadence + line format mirror tools/sinister-vault/daemon.py:_heartbeat_loop
# so fleet-monitor reads both with the same parser.
# Knowledge: runtime-liveness-heartbeats.md
RUNTIME_HEARTBEAT_DIR = SANCTUM_ROOT / "_shared-memory" / "heartbeats"
RUNTIME_HEARTBEAT_FILE = RUNTIME_HEARTBEAT_DIR / "rkoj-runtime.beat"
RUNTIME_HEARTBEAT_INTERVAL_S = 30
_runtime_started_at = time.time()


def _write_runtime_heartbeat() -> None:
    """Write one rkoj-runtime.beat line. Synchronous; cheap; called from the
    asyncio loop directly (write < 1ms; the loop won't notice)."""
    RUNTIME_HEARTBEAT_DIR.mkdir(parents=True, exist_ok=True)
    uptime = int(time.time() - _runtime_started_at)
    line = (f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} "
            f"pid={os.getpid()} port={PORT} uptime={uptime}")
    RUNTIME_HEARTBEAT_FILE.write_text(line + "\n", encoding="utf-8")


async def _runtime_heartbeat_loop() -> None:
    """Background ticker. Never raises out of the loop."""
    while True:
        try:
            _write_runtime_heartbeat()
        except Exception:
            pass
        await asyncio.sleep(RUNTIME_HEARTBEAT_INTERVAL_S)


@app.on_event("startup")
async def _runtime_heartbeat_startup() -> None:  # pragma: no cover
    # Tick once immediately so the file exists from t=0; install-rkoj-task.ps1
    # treats mtime > 120s as stale and we want green within seconds of boot.
    try:
        _write_runtime_heartbeat()
    except Exception:
        pass
    asyncio.create_task(_runtime_heartbeat_loop())


# ============================================================ fleet-state SSE ====
# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
# HR-B recommendation #4 (PROGRESS 11:17): replace 3 setIntervals in web/app.js
# (refreshSpawnedWindows @ 15s, refreshAgentsSessionsStrip + refreshActivityFeed
# bundled @ REFRESH_MS) with a single SSE consolidating spawned-windows +
# sessions + progress + operator-requests count. Frontend driver:
# web/fleet-state.js exposes window.FleetState.subscribe({onTick}).
# Pattern mirrored from the hot-reload SSE above (_sse_subscribers).
# Knowledge: rkoj-fleet-state-sse.md
_fleet_subscribers: "set[asyncio.Queue]" = set()
FLEET_TICK_INTERVAL_S = 5
_fleet_loop_started = False


def _compute_fleet_snapshot() -> dict[str, Any]:
    """Gather the consolidated fleet state. Best-effort: any helper that throws
    just contributes an empty list / 0 instead of killing the snapshot."""
    snap: dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    try:
        snap["spawned"] = _read_spawned_windows()
    except Exception as e:
        snap["spawned"] = []
        snap["spawned_err"] = str(e)
    try:
        sessions_snap = _compute_sessions_snapshot()
        if isinstance(sessions_snap, dict):
            snap["sessions"] = sessions_snap.get("sessions", []) if sessions_snap.get("ok", True) else []
        else:
            snap["sessions"] = []
    except Exception as e:
        snap["sessions"] = []
        snap["sessions_err"] = str(e)
    # Progress: top 10 newest entries (inline aggregation; mirrors /api/progress).
    try:
        items: list[dict[str, Any]] = []
        if PROGRESS_DIR.exists():
            for f in PROGRESS_DIR.glob("*.md"):
                if f.name.startswith("_") or f.name.lower() == "readme.md":
                    continue
                try:
                    text = f.read_text(encoding="utf-8")
                except Exception:
                    continue
                items.extend(_parse_progress_md(text, f.stem))
        items.sort(key=lambda e: e.get("ts", ""), reverse=True)
        for e in items[:10]:
            b = e.get("body", "").strip()
            if len(b) > 200:
                e["body"] = b[:200] + "..."
        snap["progress"] = items[:10]
    except Exception:
        snap["progress"] = []
    # Operator-requests pending count.
    try:
        reqs = _read_op_requests() or []
        snap["operator_requests_pending"] = sum(
            1 for r in reqs if (r.get("status") or "pending") == "pending"
        )
    except Exception:
        snap["operator_requests_pending"] = 0
    # Heartbeats — consumed by web/app.js daemon-liveness indicator (3 dots).
    # Stale threshold = 120s (matches install-rkoj-task.ps1 + vault daemon).
    snap["heartbeats"] = _compute_heartbeat_states()
    return snap


_HEARTBEAT_SLUGS = {
    "rkoj": "rkoj-runtime.beat",
    "sinister-vault": "sinister-vault.beat",
    "sanctum-console": "sanctum-console-runtime.beat",  # legacy slot; may not exist
}
_HEARTBEAT_STALE_S = 120


def _compute_heartbeat_states() -> dict[str, Any]:
    """For each canonical daemon slug, return alive/age_s/exists/last_line.
    Shape matches what _mountDaemonLivenessIndicator in app.js expects."""
    now = time.time()
    out: dict[str, Any] = {}
    for slug, fname in _HEARTBEAT_SLUGS.items():
        path = RUNTIME_HEARTBEAT_DIR / fname
        entry: dict[str, Any] = {"slug": slug, "file": fname, "exists": False,
                                  "alive": False, "age_s": None, "last_line": ""}
        try:
            if path.exists():
                entry["exists"] = True
                age = int(now - path.stat().st_mtime)
                entry["age_s"] = age
                entry["alive"] = age < _HEARTBEAT_STALE_S
                try:
                    entry["last_line"] = path.read_text(encoding="utf-8").strip().splitlines()[-1] if path.stat().st_size else ""
                except Exception:
                    entry["last_line"] = ""
        except Exception:
            pass
        out[slug] = entry
    return out


async def _fleet_state_loop() -> None:
    """Emit a `fleet-update` payload to every subscriber every FLEET_TICK_INTERVAL_S.
    Slow consumers (queue full) are dropped — we never block the publisher.
    Event name aligned with web/fleet-state.js client-side listener."""
    while True:
        try:
            payload = {"kind": "fleet-update", "data": _compute_fleet_snapshot()}
            for q in list(_fleet_subscribers):
                try:
                    q.put_nowait(payload)
                except asyncio.QueueFull:
                    _fleet_subscribers.discard(q)
                except Exception:
                    _fleet_subscribers.discard(q)
        except Exception:
            pass
        await asyncio.sleep(FLEET_TICK_INTERVAL_S)


@app.on_event("startup")
async def _fleet_state_startup() -> None:  # pragma: no cover
    global _fleet_loop_started
    if _fleet_loop_started:
        return
    _fleet_loop_started = True
    asyncio.create_task(_fleet_state_loop())


@app.get("/api/fleet-snapshot")
def fleet_snapshot():
    """One-shot REST view of what the SSE emits per tick. Useful for the EXE
    embedded WebView on cold start before EventSource is alive, or for any
    consumer that doesn't want a long-lived connection."""
    return {"ok": True, "data": _compute_fleet_snapshot()}


@app.get("/api/fleet-stream")
async def fleet_stream(request: Request):
    """Server-sent events channel. Emits one `hello` event (snapshot) on connect
    + a `tick` event every FLEET_TICK_INTERVAL_S seconds with the same shape.
    Disconnect-aware (drops on client close); slow-consumer-safe (drops the
    subscriber if the per-client queue overflows)."""
    queue: asyncio.Queue = asyncio.Queue(maxsize=8)
    _fleet_subscribers.add(queue)
    # Emit the current snapshot immediately so consumers render off-cache while
    # waiting for the first scheduled tick. Single canonical event name keeps
    # the client listener simple (web/fleet-state.js binds 'fleet-update').
    try:
        queue.put_nowait({"kind": "fleet-update", "data": _compute_fleet_snapshot()})
    except Exception:
        pass

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=20.0)
                except asyncio.TimeoutError:
                    # Keepalive comment line defeats idle-proxy buffering (Edge
                    # WebView2, some corporate proxies). SSE spec: lines starting
                    # with ':' are comments and ignored by the EventSource client.
                    yield ": keepalive\n\n"
                    continue
                kind = item.get("kind", "fleet-update")
                data = item.get("data", {})
                yield f"event: {kind}\ndata: {json.dumps(data, default=str)}\n\n"
        finally:
            _fleet_subscribers.discard(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.post("/api/inbox/update-ping")
def inbox_update_ping(body: UpdatePingBody):
    """Send an `[UPDATE] <subkind>` message to one agent or every online agent.

    Standing rule (DIRECTIVES.md 2026-05-19): on next turn boundary, the agent
    self-applies the update and acks. Does NOT restart the loop / lose context.
    The `noop` subkind is the heartbeat probe (operator's "are you alive" ping).
    """
    if body.subkind not in _VALID_UPDATE_SUBKINDS:
        raise HTTPException(status_code=400, detail=f"unknown subkind '{body.subkind}'")
    if not SHARED_OK or _inbox_mod is None:
        return JSONResponse(
            {"ok": False, "error": f"inbox subsystem offline: {SHARED_ERR}"},
            status_code=503,
        )
    msg_body = _format_update_body(body.subkind, body.args)
    tags = ["update", body.subkind, "window-manager"]

    # Single-recipient path
    if body.to:
        try:
            res = _inbox_mod.inbox_send(
                to_agent=body.to,
                message=msg_body,
                from_agent=body.from_agent,
                tags=tags,
            )
            return {"ok": True, "delivered": [body.to], "skipped": [], "body": msg_body, "result": res}
        except Exception as e:
            return JSONResponse({"ok": False, "error": str(e)}, status_code=500)

    # Broadcast path — fan-out to every currently-online agent
    try:
        online = _inbox_mod.who_is_online()
    except Exception as e:
        return JSONResponse({"ok": False, "error": f"who_is_online failed: {e}"}, status_code=500)

    delivered: list[str] = []
    skipped: list[dict[str, Any]] = []
    excludes = {x.strip() for x in (body.exclude or []) if x}
    for row in online:
        agent = row.get("agent")
        if not agent or agent in excludes:
            skipped.append({"agent": agent, "reason": "excluded"})
            continue
        if not row.get("online"):
            skipped.append({"agent": agent, "reason": "offline"})
            continue
        try:
            _inbox_mod.inbox_send(
                to_agent=agent,
                message=msg_body,
                from_agent=body.from_agent,
                tags=tags,
            )
            delivered.append(agent)
        except Exception as e:
            skipped.append({"agent": agent, "reason": f"send-failed: {e}"})
    return {"ok": True, "delivered": delivered, "skipped": skipped, "body": msg_body}


# ============================================================================
# jcode-form agent terminals — WebSocket-backed Claude CLI subprocess panes
# Author: RKOJ-ELENO :: 2026-05-21
# ----------------------------------------------------------------------------
# Each pane wraps a `claude --dangerously-skip-permissions -p <phrase>` child.
# Strategy chosen: Claude CLI's `-p` (print) mode is **one-shot** — it reads the
# prompt, prints the reply, and exits. So we don't pipe stdin for follow-up
# turns. Instead, each operator message respawns the subprocess with the
# accumulated context (previous turns concatenated) as the new `-p` argument.
# The pane's session state (turns list) lives in memory in PANES below.
# Rationale: the alternative — keeping `claude` interactive — would need a
# pty (Windows pywinpty), which adds a heavy dep we don't have yet. Once
# we wire the `forge.spawn` interactive PTY worker, we'll switch over.
# ============================================================================
import uuid as _uuid_mod

PANES: dict[str, dict[str, Any]] = {}
# pane_id -> {project_key, agent_name, mode, accent, opening_phrase,
#             turns: [{role:"operator"|"agent", text:str, ts:str}],
#             created_at:str, status:"idle"|"running"|"closed",
#             current_proc: asyncio.subprocess.Process | None}


class _SpawnPaneBody(BaseModel):
    project_key: str = "sanctum"
    agent_name: str = "EVE"
    mode: str = "overview"
    accent: str = "purple"
    opening_phrase: Optional[str] = None


def _pane_summary(pane_id: str, p: dict[str, Any]) -> dict[str, Any]:
    return {
        "pane_id": pane_id,
        "project_key": p.get("project_key"),
        "agent_name": p.get("agent_name"),
        "mode": p.get("mode"),
        "accent": p.get("accent"),
        "status": p.get("status", "idle"),
        "created_at": p.get("created_at"),
        "turn_count": len(p.get("turns", [])),
    }


@app.post("/api/agent/spawn")
def jcode_spawn(body: _SpawnPaneBody):
    """Reserve a pane_id and seed initial state. The WebSocket then drives the
    actual claude subprocess. We do NOT spawn here — that happens on
    websocket /ws/agent/{pane_id} connect, so we can stream output."""
    pane_id = _uuid_mod.uuid4().hex[:12]
    # Sanctum operator-canonical persona (per agent-identity-eve.md): the AI
    # ALWAYS calls itself EVE — never "Claude", never "the assistant". RKOJ-ELENO
    # is the author of every new file. Sanctum purple accent. All Sanctum-built
    # tools available via slash commands: /memory /swarm /vault /mcp /watchdog
    # /skills /mermaid /git /save /resume /create. Auto-uses sinister-watchdog
    # (auto-online), sinister-vault (1 TB collab store :5078), forge-memory-bridge
    # (BM25 recall), memory-graph-render (mermaid), sanctum-backup (7d retention),
    # sinister-cli (login/usage/swarm/model umbrella). Renders inside the Sinister
    # Panel pywebview UI with rounded glass cards + niri-scrollable agent grid.
    opening = body.opening_phrase or (
        f"You are EVE, the {body.agent_name} agent operating inside RKOJ.exe "
        f"(Sinister Sanctum workstation, frameless pywebview, Sanctum purple branding, "
        f"RKOJ-ELENO authorship). Project: {body.project_key}. Mode: {body.mode}.\n"
        f"\n"
        f"You ALWAYS identify as EVE — never 'Claude', never 'the assistant', never 'the AI'. "
        f"Author every new file with `Author: RKOJ-ELENO :: <date>`. Branch on "
        f"`agent/{body.project_key}/<topic>` cut from main. Append progress to "
        f"`_shared-memory/PROGRESS/<your-display-name>.md` (most-recent at top).\n"
        f"\n"
        f"You have the full Sinister fleet at hand: /memory /swarm /vault /mcp "
        f"/watchdog /skills /mermaid /git /save /resume /create /effort /fast — plus "
        f"the bundled sinister-* tools (sinister-cli, sinister-login, sinister-usage, "
        f"sinister-model, sinister-swarm, sinister-jcode-shim, sinister-diagnose, "
        f"forge-memory-bridge BM25 recall, memory-graph-render mermaid, sanctum-backup). "
        f"MCP servers (eve, sinister-panel, sinister-snap, sinister-tiktok, vault, ruflo) "
        f"are configured at ~/.claude/.mcp.json; the watchdog auto-restarts any that go down.\n"
        f"\n"
        f"Acknowledge as EVE, in one short purple-themed line, and report what you see."
    )
    PANES[pane_id] = {
        "project_key": body.project_key,
        "agent_name": body.agent_name,
        "mode": body.mode,
        "accent": body.accent,
        "opening_phrase": opening,
        "turns": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "idle",
        "current_proc": None,
    }
    return {"ok": True, "pane_id": pane_id, "pane": _pane_summary(pane_id, PANES[pane_id])}


@app.get("/api/agent/list")
def jcode_list():
    return {"ok": True, "panes": [_pane_summary(k, v) for k, v in PANES.items()]}


@app.post("/api/agent/{pane_id}/close")
async def jcode_close(pane_id: str):
    p = PANES.get(pane_id)
    if not p:
        raise HTTPException(status_code=404, detail="pane not found")
    proc = p.get("current_proc")
    if proc is not None and getattr(proc, "returncode", 0) is None:
        try:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=2.0)
            except asyncio.TimeoutError:
                proc.kill()
        except Exception:
            pass
    p["status"] = "closed"
    p["current_proc"] = None
    return {"ok": True, "pane_id": pane_id}


def _build_prompt_with_history(p: dict[str, Any], new_text: Optional[str]) -> str:
    """Concatenate prior turns + new operator line into a single -p prompt.
    Keeps it short (last ~12 turns) so the CLI arg stays under Windows' 32 KB
    process-arg limit."""
    chunks: list[str] = [p.get("opening_phrase", "")]
    history = p.get("turns", [])[-12:]
    for t in history:
        role = "Operator" if t.get("role") == "operator" else "EVE"
        chunks.append(f"\n[{role}] {t.get('text', '')}")
    if new_text:
        chunks.append(f"\n[Operator] {new_text}")
        chunks.append("\n[EVE]")
    return "\n".join(chunks).strip()


async def _run_claude_and_stream(ws: WebSocket, p: dict[str, Any], prompt: str) -> None:
    """Spawn `claude -p <prompt>`, stream stdout/stderr to the websocket."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "claude",
            "--dangerously-skip-permissions",
            "-p",
            prompt,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.DEVNULL,
        )
    except FileNotFoundError:
        await ws.send_json({
            "kind": "stderr",
            "data": "[ERROR] `claude` CLI not on PATH. Install Claude Code CLI or fix PATH.\r\n",
        })
        await ws.send_json({"kind": "status", "data": "idle"})
        return
    except Exception as e:
        await ws.send_json({"kind": "stderr", "data": f"[ERROR] spawn failed: {e}\r\n"})
        await ws.send_json({"kind": "status", "data": "idle"})
        return

    p["current_proc"] = proc
    p["status"] = "running"
    await ws.send_json({"kind": "status", "data": "running"})

    agent_buf: list[str] = []

    async def _pump(stream, kind: str) -> None:
        while True:
            chunk = await stream.read(1024)
            if not chunk:
                break
            try:
                text = chunk.decode("utf-8", errors="replace")
            except Exception:
                text = repr(chunk)
            # Normalize bare LF to CRLF so xterm.js wraps cleanly.
            text = text.replace("\r\n", "\n").replace("\n", "\r\n")
            if kind == "stdout":
                agent_buf.append(text)
            try:
                await ws.send_json({"kind": kind, "data": text})
            except Exception:
                return

    try:
        await asyncio.gather(_pump(proc.stdout, "stdout"), _pump(proc.stderr, "stderr"))
        await proc.wait()
    except Exception as e:
        try:
            await ws.send_json({"kind": "stderr", "data": f"[stream error] {e}\r\n"})
        except Exception:
            pass
    finally:
        # Record the agent reply (stdout, stripped of CR) into pane history.
        reply = "".join(agent_buf).replace("\r\n", "\n").strip()
        if reply:
            p.setdefault("turns", []).append({
                "role": "agent",
                "text": reply,
                "ts": datetime.now(timezone.utc).isoformat(),
            })
        p["current_proc"] = None
        p["status"] = "idle"
        try:
            await ws.send_json({"kind": "status", "data": "idle"})
            await ws.send_json({"kind": "turn-end", "data": ""})
        except Exception:
            pass


@app.websocket("/ws/agent/{pane_id}")
async def jcode_ws(ws: WebSocket, pane_id: str):
    """Per-pane WebSocket. Client frames:
        {"kind":"stdin","data":"..."}   — operator's next turn (respawns claude)
        {"kind":"kill"}                 — terminate running subprocess
    Server frames:
        {"kind":"stdout"|"stderr","data":"..."}
        {"kind":"status","data":"idle"|"running"|"closed"}
        {"kind":"turn-end","data":""}   — current claude invocation finished
    """
    await ws.accept()
    p = PANES.get(pane_id)
    if not p:
        await ws.send_json({"kind": "stderr", "data": "[ERROR] unknown pane_id\r\n"})
        await ws.close()
        return

    # Header banner inside xterm.
    banner = (
        f"\x1b[35m─── EVE on {p.get('agent_name')} :: {p.get('project_key')} "
        f"({p.get('mode')}) ───\x1b[0m\r\n"
    )
    await ws.send_json({"kind": "stdout", "data": banner})

    # Initial turn: send the opening phrase.
    initial_prompt = _build_prompt_with_history(p, None)
    # Spawn the first invocation in the background so we can also pump operator frames.
    initial_task = asyncio.create_task(_run_claude_and_stream(ws, p, initial_prompt))

    try:
        while True:
            try:
                msg = await ws.receive_json()
            except WebSocketDisconnect:
                break
            except Exception:
                continue
            kind = (msg or {}).get("kind") or ""
            if kind == "stdin":
                text = (msg.get("data") or "").strip()
                if not text:
                    continue
                # If a previous turn is still running, let the user know.
                if p.get("status") == "running":
                    await ws.send_json({
                        "kind": "stderr",
                        "data": "[busy] previous turn still running — wait or send /kill\r\n",
                    })
                    continue
                p.setdefault("turns", []).append({
                    "role": "operator",
                    "text": text,
                    "ts": datetime.now(timezone.utc).isoformat(),
                })
                prompt = _build_prompt_with_history(p, None)
                asyncio.create_task(_run_claude_and_stream(ws, p, prompt))
            elif kind == "kill":
                proc = p.get("current_proc")
                if proc is not None and getattr(proc, "returncode", 0) is None:
                    try:
                        proc.terminate()
                    except Exception:
                        pass
                    await ws.send_json({"kind": "stderr", "data": "[killed]\r\n"})
            else:
                # Unknown frame; ignore.
                pass
    finally:
        # Drain the initial task if still pending.
        if not initial_task.done():
            initial_task.cancel()
        try:
            await ws.close()
        except Exception:
            pass


# Mount /static for assets (theme.css, app.js, sinister-logo.png, etc.)
if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")
