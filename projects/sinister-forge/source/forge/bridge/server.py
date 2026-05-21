# Sinister Forge :: bridge/server.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Flask REST/SSE bridge on port :5078. Serves Sinister Claw (mobile) and any
# other Sanctum surface that wants to drive Forge agents over Tailscale.
#
# Endpoints
# ---------
# Sanctum-scope (read-only fleet overview):
#   GET  /api/sanctum/heartbeats     -> { agents: [{ agent, ts_utc, alive, ago_min }] }
#   GET  /api/sanctum/projects       -> projects.json contents
#   GET  /api/sanctum/commits?limit  -> last N commits from D:\Sinister Sanctum
#
# Forge-scope (live agent control):
#   GET    /api/forge/agents               -> [ AgentRecord ]
#   POST   /api/forge/spawn                -> AgentRecord
#   DELETE /api/forge/agents/<id>          -> { ok: true }
#   GET    /api/forge/agents/<id>/stream   -> SSE stream of stdout lines
#   POST   /api/forge/agents/<id>/input    -> { ok: true } (sends a line to stdin)
#
# Auth
# ----
# Token is auto-generated at first boot and stored at
# `_shared-memory/forge-bridge-token.txt` (gitignored). Operator copies it
# into Sinister Claw's Settings tab. All endpoints accept either:
#   Authorization: Bearer <token>     header
#   ?token=<token>                    query string  (needed for EventSource)

from __future__ import annotations

import json
import os
import queue
import secrets
import subprocess
import time
from pathlib import Path

from flask import Flask, Response, jsonify, request, stream_with_context

from forge.bridge.registry import REGISTRY


# --- Constants -------------------------------------------------------------

SANCTUM_ROOT = Path(os.environ.get("SANCTUM_ROOT") or "D:/Sinister Sanctum")
HEARTBEATS_DIR = SANCTUM_ROOT / "_shared-memory" / "heartbeats"
PROJECTS_JSON = SANCTUM_ROOT / "automations" / "session-templates" / "projects.json"
TOKEN_FILE = SANCTUM_ROOT / "_shared-memory" / "forge-bridge-token.txt"


# --- Token ----------------------------------------------------------------


def _load_or_create_token() -> str:
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    if TOKEN_FILE.exists():
        existing = TOKEN_FILE.read_text(encoding="utf-8").strip()
        if existing:
            return existing
    token = secrets.token_urlsafe(32)
    TOKEN_FILE.write_text(token, encoding="utf-8")
    return token


AUTH_TOKEN = _load_or_create_token()


def _check_auth() -> bool:
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        if secrets.compare_digest(header.removeprefix("Bearer ").strip(), AUTH_TOKEN):
            return True
    qs = request.args.get("token") or ""
    if qs and secrets.compare_digest(qs, AUTH_TOKEN):
        return True
    return False


# --- App ------------------------------------------------------------------


app = Flask(__name__)


@app.before_request
def _gate():
    # Health endpoint stays open so operator can poll the bridge unauthenticated
    if request.path == "/api/health":
        return None
    if not _check_auth():
        return jsonify({"error": "unauthorized"}), 401
    return None


# --- Sanctum endpoints ----------------------------------------------------


@app.route("/api/health")
def health():
    return jsonify({
        "ok": True,
        "name": "Sinister Forge bridge",
        "version": "0.1.0",
        "agents_active": sum(1 for r in REGISTRY.list() if r.status == "running"),
    })


@app.route("/api/sanctum/heartbeats")
def sanctum_heartbeats():
    agents = []
    if HEARTBEATS_DIR.exists():
        now = time.time()
        for hb in HEARTBEATS_DIR.glob("*.json"):
            try:
                data = json.loads(hb.read_text(encoding="utf-8"))
                ts = data.get("ts_utc") or data.get("timestamp") or ""
                mtime = hb.stat().st_mtime
                ago_min = int((now - mtime) // 60)
                agents.append({
                    "agent": data.get("agent") or hb.stem,
                    "ts_utc": ts,
                    "alive": ago_min < 30,
                    "ago_min": ago_min,
                })
            except Exception:
                continue
    agents.sort(key=lambda a: a["ago_min"])
    return jsonify({"agents": agents})


@app.route("/api/sanctum/projects")
def sanctum_projects():
    if not PROJECTS_JSON.exists():
        return jsonify([])
    try:
        data = json.loads(PROJECTS_JSON.read_text(encoding="utf-8"))
    except Exception:
        return jsonify([])
    return jsonify(data.get("projects", []))


@app.route("/api/sanctum/commits")
def sanctum_commits():
    try:
        limit = max(1, min(int(request.args.get("limit", "20")), 200))
    except ValueError:
        limit = 20
    try:
        out = subprocess.check_output(
            ["git", "log", f"-{limit}", "--pretty=format:%H|%D|%s|%cI"],
            cwd=str(SANCTUM_ROOT),
            text=True,
            encoding="utf-8",
            errors="replace",
            stderr=subprocess.DEVNULL,
            timeout=10,
        )
    except Exception as e:
        return jsonify({"error": f"git log failed: {e}"}), 500
    commits = []
    for line in out.splitlines():
        parts = line.split("|", 3)
        if len(parts) < 4:
            continue
        h, refs, msg, ts = parts
        branch = ""
        for tok in refs.split(","):
            tok = tok.strip()
            if tok.startswith("HEAD -> "):
                branch = tok.removeprefix("HEAD -> ")
                break
            if tok and not tok.startswith("origin/"):
                branch = branch or tok
        commits.append({"hash": h, "branch": branch, "message": msg, "ts_utc": ts})
    return jsonify(commits)


# --- Forge endpoints ------------------------------------------------------


@app.route("/api/forge/agents")
def forge_list():
    return jsonify([r.to_public_dict() for r in REGISTRY.list()])


@app.route("/api/forge/spawn", methods=["POST"])
def forge_spawn():
    body = request.get_json(silent=True) or {}
    project_key = (body.get("project") or "").strip()
    if not project_key:
        return jsonify({"error": "missing 'project'"}), 400

    project = _resolve_project(project_key)
    if not project:
        return jsonify({"error": f"unknown project '{project_key}'"}), 404

    agent_name = (body.get("agent_name") or "Sinister Forge Agent").strip()
    accent = (body.get("accent") or "purple").strip()
    host = (body.get("host") or "claude").strip()
    if host not in ("claude", "codex"):
        return jsonify({"error": "host must be 'claude' or 'codex'"}), 400
    token_mode = (body.get("token_mode") or "compact").strip()
    speed = (body.get("speed") or "turbo").strip()
    objective = (body.get("objective") or "dev").strip()
    focus = (body.get("focus") or "").strip()

    phrase = _compose_phrase(
        project_key=project_key,
        agent_name=agent_name,
        objective=objective,
        token_mode=token_mode,
        speed=speed,
        focus=focus,
    )

    try:
        rec = REGISTRY.spawn(
            project_key=project_key,
            project_display=project.get("display", project_key),
            project_root=Path(project.get("root") or str(SANCTUM_ROOT)),
            agent_name=agent_name,
            accent=accent,
            host=host,
            mode=objective,
            token_mode=token_mode,
            speed=speed,
            phrase=phrase,
        )
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 500

    return jsonify(rec.to_public_dict())


@app.route("/api/forge/agents/<agent_id>", methods=["DELETE"])
def forge_terminate(agent_id: str):
    ok = REGISTRY.terminate(agent_id)
    if not ok:
        return jsonify({"error": "unknown or unstartable agent"}), 404
    return jsonify({"ok": True})


@app.route("/api/forge/agents/<agent_id>/input", methods=["POST"])
def forge_input(agent_id: str):
    rec = REGISTRY.get(agent_id)
    if not rec or not rec.proc or not rec.proc.stdin:
        return jsonify({"error": "no agent or stdin closed"}), 404
    body = request.get_json(silent=True) or {}
    line = body.get("line") or ""
    try:
        rec.proc.stdin.write(line + "\n")
        rec.proc.stdin.flush()
    except Exception as e:
        return jsonify({"error": f"write failed: {e}"}), 500
    return jsonify({"ok": True})


@app.route("/api/forge/agents/<agent_id>/stream")
def forge_stream(agent_id: str):
    sub = REGISTRY.subscribe(agent_id)
    if not sub:
        return jsonify({"error": "unknown agent"}), 404
    rec, q = sub

    @stream_with_context
    def event_stream():
        try:
            yield f"event: hello\ndata: {rec.id}\n\n"
            while True:
                try:
                    line = q.get(timeout=25)
                except queue.Empty:
                    yield ": keepalive\n\n"
                    continue
                if line == "__EOF__":
                    yield "event: end\ndata: exit\n\n"
                    break
                # Plain `data:` is read by the default `message` event in EventSource.
                # We tag as `line` to match openAgentStream() in api/forge.ts.
                yield "event: line\n"
                for chunk in line.splitlines() or [""]:
                    yield f"data: {chunk}\n"
                yield "\n"
        finally:
            REGISTRY.unsubscribe(rec, q)

    return Response(event_stream(), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })


# --- Helpers --------------------------------------------------------------


def _resolve_project(key: str) -> dict | None:
    if not PROJECTS_JSON.exists():
        return None
    try:
        data = json.loads(PROJECTS_JSON.read_text(encoding="utf-8"))
    except Exception:
        return None
    for p in data.get("projects", []):
        if p.get("key") == key:
            return p
    return None


def _compose_phrase(
    *,
    project_key: str,
    agent_name: str,
    objective: str,
    token_mode: str,
    speed: str,
    focus: str,
) -> str:
    """Build the opening phrase the Claude/Codex CLI gets as its first message."""
    contracts = "Read automations/session-contracts.md (6 binding contracts)."
    focus_block = f"\n\nFocus: {focus}" if focus else ""
    return (
        f"You are {agent_name}, the Sinister {project_key} lane agent via Forge bridge. "
        f"Mode={objective}, TokenMode={token_mode}, Speed={speed}. {contracts}"
        f"{focus_block}\n\nStart the loop."
    )


# --- Entrypoint -----------------------------------------------------------


def run(host: str = "0.0.0.0", port: int = 5078) -> None:
    """Start the bridge. Bind on 0.0.0.0 so Tailscale can reach it."""
    print(f"[forge-bridge] starting on http://{host}:{port}", flush=True)
    print(f"[forge-bridge] auth token (copy into Claw Settings): {AUTH_TOKEN}", flush=True)
    print(f"[forge-bridge] token file: {TOKEN_FILE}", flush=True)
    app.run(host=host, port=port, threaded=True, debug=False, use_reloader=False)


if __name__ == "__main__":
    run()
