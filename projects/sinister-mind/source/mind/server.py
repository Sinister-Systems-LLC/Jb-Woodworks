# Sinister Mind :: server.py (v2 - SSE live reload + tag-chip support)
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later

from __future__ import annotations

import json
import queue
import re
import threading
import time
from collections import defaultdict, deque
from pathlib import Path

from flask import Flask, Response, jsonify, request, send_from_directory


SANCTUM_ROOT = Path("D:/Sinister Sanctum")
BRAIN_INDEX = SANCTUM_ROOT / "_shared-memory" / "knowledge" / "_INDEX.md"
BRAIN_DIR = SANCTUM_ROOT / "_shared-memory" / "knowledge"
PROJECTS_JSON = SANCTUM_ROOT / "automations" / "session-templates" / "projects.json"
PLANS_DIR = SANCTUM_ROOT / "_shared-memory" / "plans"
PROGRESS_DIR = SANCTUM_ROOT / "_shared-memory" / "PROGRESS"
CROSS_AGENT_DIR = SANCTUM_ROOT / "_shared-memory" / "cross-agent"
RESUME_POINTS_DIR = SANCTUM_ROOT / "_shared-memory" / "resume-points"
HEARTBEATS_DIR = SANCTUM_ROOT / "_shared-memory" / "heartbeats"
MERMAID_RENDERS_DIR = SANCTUM_ROOT / "_shared-memory" / "forge-memory" / "mermaid-renders"

STATIC_DIR = Path(__file__).parent / "static"

# Mirrors the producer at projects/rkoj/source/sinister_rkoj_qt/api_server.py
# so RKOJ.exe :5077 and Mind :5079 expose the same diagram inventory off the
# same on-disk cache.
DIAGRAM_EXT_PRIORITY = (".png", ".svg", ".html", ".mmd")
# Flask appends charset=utf-8 to text/* mimetypes automatically, so we keep
# these bare. Don't add `; charset=utf-8` here or we get duplicate-charset
# headers in the response.
DIAGRAM_CONTENT_TYPES = {
    ".png":  "image/png",
    ".svg":  "image/svg+xml",
    ".html": "text/html",
    ".mmd":  "text/plain",
}

NODE_COLORS = {
    "brain":       "#A06EFF",
    "project":     "#6EE8FF",
    "plan":        "#6EFFA0",
    "progress":    "#FFD66E",
    "cross_agent": "#FF6EE8",
    "resume_pt":   "#FF6E6E",
}

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="/static")

# SSE subscriber queues
_sse_subscribers: list[queue.Queue] = []
_sse_lock = threading.Lock()


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def load_projects() -> list[dict]:
    if not PROJECTS_JSON.exists():
        return []
    try:
        return json.loads(_read_text(PROJECTS_JSON)).get("projects", [])
    except Exception:
        return []


def load_brain_entries() -> list[dict]:
    entries: list[dict] = []
    if not BRAIN_INDEX.exists():
        return entries
    text = _read_text(BRAIN_INDEX)
    for line in text.splitlines():
        if not line.startswith("| ") or line.startswith("| Slug |") or line.startswith("|---"):
            continue
        parts = [p.strip() for p in line.strip("| ").split("|")]
        if len(parts) < 4:
            continue
        slug = parts[0].strip("` ")
        if not slug or slug.startswith("---"):
            continue
        title = parts[1] if len(parts) > 1 else slug
        status = parts[2] if len(parts) > 2 else ""
        tags = [t.strip() for t in (parts[3] or "").split(",") if t.strip()]
        entries.append({
            "id": f"brain:{slug}",
            "label": slug,
            "type": "brain",
            "title": (title[:80] + "...") if len(title) > 80 else title,
            "status": status,
            "tags": tags,
            "color": NODE_COLORS["brain"],
        })
    return entries


def load_plan_artifacts() -> list[dict]:
    out: list[dict] = []
    if not PLANS_DIR.exists():
        return out
    for plan_dir in PLANS_DIR.iterdir():
        if not plan_dir.is_dir() or plan_dir.name.startswith("_"):
            continue
        out.append({
            "id": f"plan:{plan_dir.name}",
            "label": plan_dir.name,
            "type": "plan",
            "tags": [],
            "color": NODE_COLORS["plan"],
        })
    return out


def load_progress_headings() -> list[dict]:
    out: list[dict] = []
    if not PROGRESS_DIR.exists():
        return out
    for f in PROGRESS_DIR.glob("*.md"):
        if f.name.startswith("_"):
            continue
        agent = f.stem
        text = _read_text(f)
        m = re.search(r"^## (\d{4}-\d{2}-\d{2} [^\n]+)", text, flags=re.MULTILINE)
        title = m.group(1) if m else f.stem
        out.append({
            "id": f"progress:{agent}",
            "label": agent,
            "type": "progress",
            "title": title[:80],
            "tags": [],
            "color": NODE_COLORS["progress"],
        })
    return out


def load_cross_agent() -> list[dict]:
    out: list[dict] = []
    if not CROSS_AGENT_DIR.exists():
        return out
    for f in CROSS_AGENT_DIR.glob("*.md"):
        if f.parent.name == "_archive":
            continue
        out.append({
            "id": f"xa:{f.stem}",
            "label": f.stem[:40],
            "type": "cross_agent",
            "tags": [],
            "color": NODE_COLORS["cross_agent"],
        })
    return out[:200]


def load_resume_points() -> list[dict]:
    out: list[dict] = []
    if not RESUME_POINTS_DIR.exists():
        return out
    for proj_dir in RESUME_POINTS_DIR.iterdir():
        if not proj_dir.is_dir():
            continue
        files = sorted(proj_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not files:
            continue
        out.append({
            "id": f"resume:{proj_dir.name}",
            "label": proj_dir.name,
            "type": "resume_pt",
            "tags": [proj_dir.name],
            "color": NODE_COLORS["resume_pt"],
        })
    return out


def build_graph() -> dict:
    projects = load_projects()
    brain = load_brain_entries()
    plans = load_plan_artifacts()
    progress = load_progress_headings()
    xa = load_cross_agent()
    rp = load_resume_points()

    project_nodes = []
    project_keys = set()
    for p in projects:
        key = p.get("key", "")
        project_keys.add(key)
        project_nodes.append({
            "id": f"project:{key}",
            "label": p.get("display", key),
            "type": "project",
            "tag": p.get("tag", ""),
            "github": p.get("github", ""),
            "tags": [key],
            "color": NODE_COLORS["project"],
        })

    nodes = project_nodes + brain + plans + progress + xa + rp
    edges: list[dict] = []

    for b in brain:
        for pk in project_keys:
            if any(pk in t or t.startswith(pk) for t in b.get("tags", [])):
                edges.append({"source": b["id"], "target": f"project:{pk}", "weight": 1, "type": "brain-project"})

    for pl in plans:
        for pk in project_keys:
            if pl["label"].lower().startswith(pk.lower()) or pk.lower() in pl["label"].lower():
                edges.append({"source": pl["id"], "target": f"project:{pk}", "weight": 1, "type": "plan-project"})

    for r in rp:
        if r["label"] in project_keys:
            edges.append({"source": r["id"], "target": f"project:{r['label']}", "weight": 2, "type": "resume-project"})

    return {"nodes": nodes, "edges": edges, "counts": {
        "projects": len(project_nodes),
        "brain": len(brain),
        "plans": len(plans),
        "progress": len(progress),
        "cross_agent": len(xa),
        "resume_pts": len(rp),
        "total_nodes": len(nodes),
        "total_edges": len(edges),
    }}


# ---------------- Memory-graph diagram cache ----------------

def _diagram_groups() -> list[dict]:
    """Walk the mermaid-renders dir; group siblings by stem; newest-first.

    Same shape as RKOJ.exe ``/api/diagrams`` so any consumer can target
    either :5077 or :5079.
    """
    if not MERMAID_RENDERS_DIR.exists():
        return []
    groups: dict[str, list[Path]] = {}
    try:
        for fp in MERMAID_RENDERS_DIR.iterdir():
            if not fp.is_file():
                continue
            if fp.suffix.lower() not in DIAGRAM_EXT_PRIORITY:
                continue
            groups.setdefault(fp.stem, []).append(fp)
    except OSError:
        return []
    now = time.time()
    out: list[dict] = []
    for stem, files in groups.items():
        primary = next(
            (f for ext in DIAGRAM_EXT_PRIORITY
             for f in files if f.suffix.lower() == ext),
            files[0],
        )
        mtime = max(f.stat().st_mtime for f in files)
        out.append({
            "stem": stem,
            "ext": primary.suffix.lstrip("."),
            "mtime": mtime,
            "age_s": int(now - mtime),
            "primary_path": str(primary),
            "siblings": sorted(f.suffix.lstrip(".") for f in files),
        })
    out.sort(key=lambda d: d["mtime"], reverse=True)
    return out


def _resolve_diagram_primary(stem: str) -> Path | None:
    """Path-traversal-guarded resolve of the primary render for ``stem``."""
    if not stem or "/" in stem or "\\" in stem or stem in (".", ".."):
        return None
    for ext in DIAGRAM_EXT_PRIORITY:
        cand = MERMAID_RENDERS_DIR / f"{stem}{ext}"
        if cand.is_file():
            try:
                primary = cand.resolve(strict=True)
                base = MERMAID_RENDERS_DIR.resolve(strict=True)
                primary.relative_to(base)
                return primary
            except (OSError, ValueError):
                return None
    return None


# ---------------- SSE machinery ----------------

def _broadcast_change():
    """Push a 'graph-change' event to every subscriber."""
    with _sse_lock:
        dead = []
        for q in _sse_subscribers:
            try:
                q.put_nowait("change")
            except queue.Full:
                dead.append(q)
        for q in dead:
            try:
                _sse_subscribers.remove(q)
            except ValueError:
                pass


def _watch_loop():
    """Background thread: poll _shared-memory/ mtimes; broadcast when changes."""
    watched = [BRAIN_INDEX, PROJECTS_JSON, PLANS_DIR, PROGRESS_DIR, CROSS_AGENT_DIR, RESUME_POINTS_DIR]
    last_max = 0.0
    while True:
        try:
            mtimes = []
            for p in watched:
                if p.is_file():
                    mtimes.append(p.stat().st_mtime)
                elif p.is_dir():
                    for f in p.rglob("*"):
                        if f.is_file():
                            mtimes.append(f.stat().st_mtime)
            if mtimes:
                cur_max = max(mtimes)
                if last_max and cur_max > last_max + 0.5:
                    _broadcast_change()
                last_max = cur_max
        except Exception:
            pass
        time.sleep(2)


# Start watcher thread on first import
_watch_thread = threading.Thread(target=_watch_loop, daemon=True)
_watch_thread.start()


# ---------------- Endpoints ----------------

@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.route("/api/graph")
def api_graph():
    return jsonify(build_graph())


@app.route("/api/projects")
def api_projects():
    return jsonify(load_projects())


@app.route("/api/search")
def api_search():
    q = (request.args.get("q") or "").lower().strip()
    if not q:
        return jsonify({"matches": []})
    graph = build_graph()
    matches = [
        n for n in graph["nodes"]
        if q in n["id"].lower()
        or q in n.get("label", "").lower()
        or q in n.get("title", "").lower()
        or any(q in t.lower() for t in n.get("tags", []))
    ]
    return jsonify({"matches": matches[:50], "total": len(matches)})


@app.route("/api/path")
def api_path():
    a = request.args.get("a")
    b = request.args.get("b")
    if not a or not b:
        return jsonify({"error": "need ?a=<id>&b=<id>"}), 400
    graph = build_graph()
    adj: dict[str, list[str]] = defaultdict(list)
    for e in graph["edges"]:
        adj[e["source"]].append(e["target"])
        adj[e["target"]].append(e["source"])
    if a not in adj and b not in adj:
        return jsonify({"path": [], "found": False})
    qbfs = deque([[a]])
    seen = {a}
    while qbfs:
        path = qbfs.popleft()
        if path[-1] == b:
            return jsonify({"path": path, "found": True, "length": len(path) - 1})
        for n in adj.get(path[-1], []):
            if n not in seen:
                seen.add(n)
                qbfs.append(path + [n])
    return jsonify({"path": [], "found": False})


@app.route("/api/stream")
def api_stream():
    """SSE endpoint - emits 'graph-change' events when _shared-memory/ changes."""
    def event_stream():
        sub_q: queue.Queue = queue.Queue(maxsize=10)
        with _sse_lock:
            _sse_subscribers.append(sub_q)
        try:
            yield "event: hello\ndata: connected\n\n"
            while True:
                try:
                    _ = sub_q.get(timeout=30)
                    yield "event: graph-change\ndata: 1\n\n"
                except queue.Empty:
                    yield ": keepalive\n\n"
        finally:
            with _sse_lock:
                try:
                    _sse_subscribers.remove(sub_q)
                except ValueError:
                    pass

    return Response(event_stream(), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })


@app.route("/diagrams")
def diagrams_page():
    return send_from_directory(STATIC_DIR, "diagrams.html")


@app.route("/api/diagrams")
def api_diagrams():
    groups = _diagram_groups()
    return jsonify({
        "diagrams": groups,
        "count": len(groups),
        "renders_dir": str(MERMAID_RENDERS_DIR),
        "renders_dir_exists": MERMAID_RENDERS_DIR.exists(),
    })


@app.route("/api/diagrams/<stem>")
def api_diagram_bytes(stem: str):
    primary = _resolve_diagram_primary(stem)
    if primary is None:
        return jsonify({"error": "not found", "stem": stem}), 404
    ext = primary.suffix.lower()
    mime = DIAGRAM_CONTENT_TYPES.get(ext, "application/octet-stream")
    try:
        return Response(primary.read_bytes(), mimetype=mime, headers={
            "Cache-Control": "no-cache",
        })
    except OSError:
        return jsonify({"error": "read failed", "stem": stem}), 500


@app.route("/api/health")
def api_health():
    return jsonify({"ok": True, "name": "Sinister Mind", "version": "0.3.0"})
