"""Single-file http.server sorter — runs at http://localhost:<port>/, persistent."""
# Author: RKOJ-ELENO :: 2026-05-23

from __future__ import annotations

import json
import mimetypes
import pathlib
import shutil
import sys
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import List, Optional, Tuple

GREAT_SUBDIR = "💎 Great"
GOOD_SUBDIR = "✅ Good"
SIZE_OFF_SUBDIR = "📐 Size Off"
WRONG_GUY_SUBDIR = "👤 Wrong Guy"
WRONG_STYLE_SUBDIR = "🎨 Wrong Style"
SKIP_CONCEPT_SUBDIR = "♻️ Skip Concept"
BAD_SUBDIR = "❌ Bad"
REFS_SUBDIR = "📥 Refs"
SKIP_SUBDIRS = {
    GREAT_SUBDIR, GOOD_SUBDIR, SIZE_OFF_SUBDIR, WRONG_GUY_SUBDIR,
    WRONG_STYLE_SUBDIR, SKIP_CONCEPT_SUBDIR, BAD_SUBDIR, REFS_SUBDIR,
    "✅ Yes", "❌ No",
}
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp")

HERE = pathlib.Path(__file__).resolve().parent
INDEX_HTML_PATH = HERE / "index.html"


class _State:
    def __init__(self, folder: pathlib.Path):
        self.folder = folder
        self.lock = threading.Lock()
        self.history: List[Tuple[str, pathlib.Path, pathlib.Path]] = []  # verdict, src, dest

    def queue(self) -> List[pathlib.Path]:
        out = []
        for p in sorted(self.folder.iterdir()):
            if p.is_dir():
                continue
            if p.suffix.lower() not in IMAGE_EXTS:
                continue
            if p.parent.name in SKIP_SUBDIRS:
                continue
            out.append(p)
        return out

    def stats(self) -> dict:
        def count(d: pathlib.Path) -> int:
            if not d.is_dir():
                return 0
            return sum(1 for p in d.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS)
        return {
            "queue": len(self.queue()),
            "great": count(self.folder / GREAT_SUBDIR),
            "good": count(self.folder / GOOD_SUBDIR),
            "size_off": count(self.folder / SIZE_OFF_SUBDIR),
            "wrong_guy": count(self.folder / WRONG_GUY_SUBDIR),
            "wrong_style": count(self.folder / WRONG_STYLE_SUBDIR),
            "skip_concept": count(self.folder / SKIP_CONCEPT_SUBDIR),
            "bad": count(self.folder / BAD_SUBDIR),
            "refs": count(self.folder / REFS_SUBDIR),
            "folder": str(self.folder),
        }

    def sort(self, filename: str, verdict: str) -> dict:
        with self.lock:
            src = self.folder / filename
            if not src.is_file():
                return {"status": "error", "error": f"file not in queue: {filename}"}
            verdict_to_dir = {
                "great": GREAT_SUBDIR,
                "good": GOOD_SUBDIR,
                "size_off": SIZE_OFF_SUBDIR,
                "wrong_guy": WRONG_GUY_SUBDIR,
                "wrong_style": WRONG_STYLE_SUBDIR,
                "skip_concept": SKIP_CONCEPT_SUBDIR,
                "bad": BAD_SUBDIR,
                "promote_ref": REFS_SUBDIR,
            }
            if verdict == "skip":
                self.history.append(("skip", src, src))
                return {"status": "ok", "verdict": "skip"}
            if verdict not in verdict_to_dir:
                return {"status": "error", "error": f"unknown verdict: {verdict}"}
            dest_dir = self.folder / verdict_to_dir[verdict]
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = _next_available(dest_dir / src.name)
            shutil.move(str(src), str(dest))
            # Move sidecar
            meta_src = src.with_suffix(src.suffix + ".meta.json")
            if meta_src.is_file():
                meta_dest = dest.with_suffix(dest.suffix + ".meta.json")
                try:
                    shutil.move(str(meta_src), str(meta_dest))
                except OSError:
                    pass
            # Write tier-specific note
            utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            ext_for_verdict = {
                "great": ".great.txt",
                "good": ".endorse.txt",
                "size_off": ".sizeoff.txt",
                "wrong_guy": ".wrongguy.txt",
                "wrong_style": ".wrongstyle.txt",
                "skip_concept": ".skipconcept.txt",
                "bad": ".reject.txt",
                "promote_ref": ".promoted-ref.txt",
            }
            note_path = dest.with_suffix(dest.suffix + ext_for_verdict[verdict])
            tier_label = {
                "great": "GREAT (would use as-is)",
                "good": "GOOD (on theme, needs work)",
                "size_off": "SIZE OFF (good idea, wrong size/aspect/framing — reshape candidate)",
                "wrong_guy": "WRONG GUY (good concept, character drift — needs stronger char refs)",
                "wrong_style": "WRONG STYLE (good composition, wrong vibe/lighting/palette)",
                "skip_concept": "SKIP CONCEPT (drop this prompt direction in future iter)",
                "bad": "BAD (rejected)",
                "promote_ref": "PROMOTED TO REFS (operator endorses as canonical for future gens)",
            }[verdict]
            try:
                note_path.write_text(f"operator {tier_label} via web sorter at {utc}\n", encoding="utf-8")
            except OSError:
                pass
            self.history.append((verdict, src, dest))
            return {"status": "ok", "verdict": verdict, "src": str(src), "dest": str(dest)}

    def undo(self) -> dict:
        with self.lock:
            while self.history:
                verdict, src, dest = self.history.pop()
                if verdict == "skip":
                    return {"status": "ok", "undone": "skip"}
                try:
                    shutil.move(str(dest), str(src))
                except OSError as e:
                    return {"status": "error", "error": str(e)}
                meta_dest = dest.with_suffix(dest.suffix + ".meta.json")
                if meta_dest.is_file():
                    meta_src = src.with_suffix(src.suffix + ".meta.json")
                    try:
                        shutil.move(str(meta_dest), str(meta_src))
                    except OSError:
                        pass
                for ext in (
                    ".great.txt", ".endorse.txt", ".reject.txt",
                    ".sizeoff.txt", ".wrongguy.txt", ".wrongstyle.txt",
                    ".skipconcept.txt", ".promoted-ref.txt",
                ):
                    note = dest.with_suffix(dest.suffix + ext)
                    if note.is_file():
                        try:
                            note.unlink()
                        except OSError:
                            pass
                return {"status": "ok", "undone": verdict, "restored": str(src)}
            return {"status": "ok", "undone": "none"}

    def meta_for(self, filename: str) -> dict:
        path = self.folder / filename
        if not path.is_file():
            return {"error": "not found"}
        out: dict = {"filename": filename, "size_bytes": path.stat().st_size}
        meta_path = path.with_suffix(path.suffix + ".meta.json")
        if meta_path.is_file():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                prompt = meta.get("prompt", "") or ""
                out["prompt_excerpt"] = prompt[:600]
                out["model"] = meta.get("model", "")
                out["created_utc"] = meta.get("created_utc", "")
                out["ref_image_count"] = meta.get("ref_image_count", 0)
            except (OSError, json.JSONDecodeError):
                pass
        try:
            from PIL import Image
            with Image.open(path) as im:
                out["width"], out["height"] = im.size
        except Exception:
            pass
        return out


def _next_available(path: pathlib.Path) -> pathlib.Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    for i in range(1, 1000):
        candidate = parent / f"{stem}.dup{i}{suffix}"
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"too many duplicates of {path}")


def _make_handler(state: _State):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            # Quiet by default; uncomment for debugging
            pass

        def _json(self, code: int, body: dict):
            payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(payload)

        def _file(self, path: pathlib.Path, content_type: Optional[str] = None):
            if not path.is_file():
                self._json(404, {"error": "not found"})
                return
            ctype = content_type or mimetypes.guess_type(str(path))[0] or "application/octet-stream"
            data = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path
            if path == "/" or path == "/index.html":
                self._file(INDEX_HTML_PATH, "text/html; charset=utf-8")
                return
            if path == "/api/queue":
                queue = [p.name for p in state.queue()]
                self._json(200, {"queue": queue, "stats": state.stats()})
                return
            if path.startswith("/api/image/"):
                fname = urllib.parse.unquote(path[len("/api/image/"):])
                self._file(state.folder / fname)
                return
            if path.startswith("/api/meta/"):
                fname = urllib.parse.unquote(path[len("/api/meta/"):])
                self._json(200, state.meta_for(fname))
                return
            self._json(404, {"error": "unknown route", "path": path})

        def do_POST(self):
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length > 0 else b"{}"
            try:
                body = json.loads(raw.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                self._json(400, {"error": "invalid JSON"})
                return
            if path == "/api/sort":
                filename = body.get("filename") or ""
                verdict = body.get("verdict") or ""
                self._json(200, state.sort(filename, verdict))
                return
            if path == "/api/undo":
                self._json(200, state.undo())
                return
            self._json(404, {"error": "unknown route", "path": path})

    return Handler


def run_server(folder: pathlib.Path, port: int = 7099) -> int:
    state = _State(folder)
    httpd = ThreadingHTTPServer(("127.0.0.1", port), _make_handler(state))
    msg = (
        f"\n  [*] JOKR sorter (web) running at http://localhost:{port}/\n"
        f"      watching: {folder}\n"
        f"      Ctrl+C to stop\n"
    )
    try:
        sys.stdout.write(msg)
        sys.stdout.flush()
    except UnicodeEncodeError:
        sys.stdout.buffer.write(msg.encode("utf-8", errors="replace"))
        sys.stdout.flush()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0
