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
import threading
import time
from pathlib import Path

from flask import Flask, Response, jsonify, request, stream_with_context

from forge.bridge.registry import REGISTRY


# --- Constants -------------------------------------------------------------

SANCTUM_ROOT = Path(os.environ.get("SANCTUM_ROOT") or "D:/Sinister Sanctum")
HEARTBEATS_DIR = SANCTUM_ROOT / "_shared-memory" / "heartbeats"
PROJECTS_JSON = SANCTUM_ROOT / "automations" / "session-templates" / "projects.json"
INBOX_DIR = SANCTUM_ROOT / "_shared-memory" / "inbox"
CROSS_AGENT_DIR = SANCTUM_ROOT / "_shared-memory" / "cross-agent"
PROGRESS_DIR = SANCTUM_ROOT / "_shared-memory" / "PROGRESS"
RESUME_DIR = SANCTUM_ROOT / "_shared-memory" / "resume-points"
PLANS_DIR = SANCTUM_ROOT / "_shared-memory" / "plans"
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


@app.route("/api/sanctum/inbox")
def sanctum_inbox():
    """Aggregate operator-relevant messages from inbox/ + cross-agent/.

    Each item is { id, source, from, to, subject, ts_utc, project_hint, body }.
    Sorted newest-first. Bound to limit (default 50, max 200).
    """
    try:
        limit = max(1, min(int(request.args.get("limit", "50")), 200))
    except ValueError:
        limit = 50
    items: list[dict] = []

    if INBOX_DIR.exists():
        for proj_dir in INBOX_DIR.iterdir():
            if not proj_dir.is_dir():
                continue
            for f in proj_dir.glob("*.json"):
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                except Exception:
                    continue
                items.append({
                    "id": f"inbox/{proj_dir.name}/{f.name}",
                    "source": "inbox",
                    "tag": data.get("tag", ""),
                    "from": data.get("from_display") or data.get("from", "?"),
                    "to": data.get("to_display") or data.get("to", proj_dir.name),
                    "subject": data.get("subject", f.stem),
                    "ts_utc": data.get("ts_utc") or _file_iso_mtime(f),
                    "project_hint": proj_dir.name,
                    "body_path": str(f.relative_to(SANCTUM_ROOT)).replace("\\", "/"),
                    "body": json.dumps(data, indent=2),
                })

    if CROSS_AGENT_DIR.exists():
        for f in CROSS_AGENT_DIR.glob("*.md"):
            if f.parent.name == "_archive":
                continue
            try:
                body = f.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            subject = _extract_first_heading(body) or f.stem
            project_hint = _guess_project_from_name(f.stem)
            items.append({
                "id": f"cross-agent/{f.name}",
                "source": "cross-agent",
                "tag": _extract_first_tag(body),
                "from": _guess_from_filename(f.stem, "from"),
                "to": _guess_from_filename(f.stem, "to"),
                "subject": subject[:140],
                "ts_utc": _file_iso_mtime(f),
                "project_hint": project_hint,
                "body_path": str(f.relative_to(SANCTUM_ROOT)).replace("\\", "/"),
                "body": body[:8000],
            })

    items.sort(key=lambda i: i.get("ts_utc") or "", reverse=True)
    return jsonify({
        "items": items[:limit],
        "total": len(items),
    })


@app.route("/api/sanctum/projects/<key>/detail")
def sanctum_project_detail(key: str):
    project = _resolve_project(key)
    if not project:
        return jsonify({"error": f"unknown project '{key}'"}), 404

    display = project.get("display", key)
    progress_file = _find_progress_file(key, display)
    progress_entries = _parse_progress_top(progress_file, n=5) if progress_file else []

    resume_dir = RESUME_DIR / display
    resume_pt = None
    if resume_dir.exists():
        files = sorted(resume_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if files:
            try:
                resume_pt = json.loads(files[0].read_text(encoding="utf-8-sig"))
            except Exception:
                pass

    plans: list[dict] = []
    if PLANS_DIR.exists():
        kl = key.lower()
        dl = display.lower().replace(" ", "-")
        for plan in PLANS_DIR.iterdir():
            if not plan.is_dir():
                continue
            name = plan.name.lower()
            if kl in name or dl in name:
                plans.append({"dir": plan.name, "mtime": _file_iso_mtime(plan)})
    plans.sort(key=lambda p: p["mtime"], reverse=True)

    return jsonify({
        "project": project,
        "progress_entries": progress_entries,
        "resume_point": resume_pt,
        "plans": plans[:10],
    })


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


def _file_iso_mtime(p: Path) -> str:
    try:
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(p.stat().st_mtime))
    except Exception:
        return ""


def _extract_first_heading(body: str) -> str:
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
        if line.startswith("## "):
            return line[3:].strip()
    return ""


def _extract_first_tag(body: str) -> str:
    """Find a bracketed tag like [ASK] / [ACK] / [BROADCAST] in the first 500 chars."""
    head = body[:500]
    import re
    m = re.search(r"\[([A-Z_-]{2,20})\]", head)
    return m.group(1) if m else ""


def _guess_project_from_name(stem: str) -> str:
    """Stems look like '2026-05-21T03Z-sanctum-to-rkoj-...' -> 'rkoj'."""
    parts = stem.split("-")
    if "to" in parts:
        i = parts.index("to")
        if i + 1 < len(parts):
            return parts[i + 1]
    return ""


def _guess_from_filename(stem: str, which: str) -> str:
    """Return 'from' or 'to' segment from '<ts>-<from>-to-<to>-<subj>'."""
    parts = stem.split("-")
    if "to" not in parts:
        return ""
    i = parts.index("to")
    if which == "from" and i >= 1:
        return parts[i - 1]
    if which == "to" and i + 1 < len(parts):
        return parts[i + 1]
    return ""


def _find_progress_file(key: str, display: str) -> Path | None:
    """PROGRESS files don't follow a strict naming rule. Try a few patterns."""
    if not PROGRESS_DIR.exists():
        return None
    candidates = [
        PROGRESS_DIR / f"{display}.md",
        PROGRESS_DIR / f"{key}.md",
        PROGRESS_DIR / f"Sinister {display}.md",
    ]
    # short-form aliases used historically
    aliases = {
        "snap-emulator-api": ["snap-emu.md", "Sinister Snap API.md"],
        "tiktok-emulator-api": ["tiktok-emu.md", "Sinister TikTok API.md"],
        "bumble-emulator-api": ["bumble-emu.md", "Sinister Bumble API.md"],
        "kernel-apk": ["Sinister Kernel APK.md"],
        "sanctum": ["Sinister Sanctum.md"],
        "sinister-panel": ["Sinister Panel.md"],
    }
    for alias in aliases.get(key, []):
        candidates.append(PROGRESS_DIR / alias)
    for c in candidates:
        if c.exists():
            return c
    return None


def _parse_progress_top(path: Path, n: int = 5) -> list[dict]:
    """Progress files are markdown with `## YYYY-MM-DD HH:MM - <title>` sections.
    Return top n entries newest-first.
    """
    try:
        body = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []
    import re
    out: list[dict] = []
    pattern = re.compile(r"^## (\d{4}-\d{2}-\d{2}[^\n]+)$", flags=re.MULTILINE)
    matches = list(pattern.finditer(body))
    for i, m in enumerate(matches[:n]):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        snippet = body[start:end].strip()
        out.append({
            "heading": m.group(1).strip(),
            "snippet": snippet[:1200],
        })
    return out


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


# --- Heartbeat writer ----------------------------------------------------


def _heartbeat_loop() -> None:
    """Write the bridge's own heartbeat so master/Sanctum can see it's alive."""
    hb_path = HEARTBEATS_DIR / "forge-bridge.json"
    HEARTBEATS_DIR.mkdir(parents=True, exist_ok=True)
    while True:
        try:
            payload = {
                "agent": "forge-bridge",
                "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "alive": True,
                "agents_active": sum(1 for r in REGISTRY.list() if r.status == "running"),
                "agents_total": len(REGISTRY.list()),
                "version": "0.1.0",
            }
            hb_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception:
            pass
        time.sleep(60)


def run(host: str = "0.0.0.0", port: int = 5078) -> None:
    """Start the bridge. Bind on 0.0.0.0 so Tailscale can reach it."""
    print(f"[forge-bridge] starting on http://{host}:{port}", flush=True)
    print(f"[forge-bridge] auth token (copy into Claw Settings): {AUTH_TOKEN}", flush=True)
    print(f"[forge-bridge] token file: {TOKEN_FILE}", flush=True)
    threading.Thread(target=_heartbeat_loop, daemon=True).start()
    app.run(host=host, port=port, threaded=True, debug=False, use_reloader=False)


if __name__ == "__main__":
    run()
