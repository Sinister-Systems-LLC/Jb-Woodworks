"""
Sinister RKOJ extension :: brain

Author: RKOJ-ELENO :: 2026-05-21

Indexes + greps `_shared-memory/knowledge/*.md` for fast top-N substring recall, and
shells out to `tools/memory-graph-render/memory_graph_render/api.py` for full mermaid
renders. Self-contained — no imports from sinister_rkoj_qt.*, PyQt6 imports are
TYPE_CHECKING-only so manifest.json parses on any stdlib Python >=3.10.

Hooks implemented:
  - hook_slash(args, pane, app)  : /brain search|grep|render|index
  - hook_workstation_action()    : opens the latest mermaid render (HTML)
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QWidget  # noqa: F401


KNOWLEDGE_REL = os.path.join("_shared-memory", "knowledge")
RENDERS_REL = os.path.join("_shared-memory", "forge-memory", "mermaid-renders")
GRAPH_API_REL = os.path.join("tools", "memory-graph-render", "memory_graph_render")
MAX_HITS_DEFAULT = 5
SNIPPET_RADIUS = 80


class BrainExtension:
    """Plugin entry-point. One instance per RKOJ session."""

    id = "sinister-brain"
    version = "0.1.0"

    def __init__(self) -> None:
        self._sanctum_root: str | None = None  # cached

    # -------------------------------------------------------------- /brain
    def hook_slash(self, args: list[str], pane: "QWidget | None", app: Any) -> str:
        """
        /brain <subcommand> [args]
          search <query>   — top-5 substring hits across _shared-memory/knowledge/*.md
          grep <regex>     — regex hits with file:line:snippet (top-20)
          render [file]    — invoke memory-graph-render; opens the resulting HTML
          index            — list the brain corpus (file count, total bytes)
        """
        sub = (args[0] if args else "").lower()
        rest = args[1:] if len(args) > 1 else []

        if sub == "" or sub == "help":
            return (
                "[brain] usage:\n"
                "  /brain search <query>\n"
                "  /brain grep <regex>\n"
                "  /brain render [file.md]\n"
                "  /brain index"
            )
        if sub == "search":
            if not rest:
                return "[brain] usage: /brain search <query>"
            return self._search(" ".join(rest), max_hits=MAX_HITS_DEFAULT)
        if sub == "grep":
            if not rest:
                return "[brain] usage: /brain grep <regex>"
            return self._grep(" ".join(rest), max_hits=20)
        if sub == "render":
            target = rest[0] if rest else None
            return self._render(target)
        if sub == "index":
            return self._index()
        return f"[brain] unknown subcommand: {sub} (try: search|grep|render|index)"

    # --------------------------------------------------- workstation card
    def hook_workstation_action(self) -> dict[str, Any]:
        """Open the most-recent mermaid render HTML in the default browser."""
        renders = self._latest_renders(limit=1)
        if not renders:
            # Fall back to invoking the render once, then opening it.
            msg = self._render(None)
            renders = self._latest_renders(limit=1)
            if not renders:
                return {"ok": False, "message": msg}
        html_path = renders[0]
        try:
            self._open_path(html_path)
            return {"ok": True, "message": f"Opened {os.path.basename(html_path)}"}
        except Exception as exc:
            return {"ok": False, "message": f"open failed: {exc}"}

    # ------------------------------------------------------------- search
    def _search(self, query: str, max_hits: int) -> str:
        kdir = self._knowledge_dir()
        if kdir is None:
            return "[brain] _shared-memory/knowledge/ not found"
        needle = query.lower()
        hits: list[tuple[str, int, str, int]] = []  # (path, line_no, snippet, score)
        for path in self._iter_markdown(kdir):
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as fp:
                    for line_no, line in enumerate(fp, start=1):
                        low = line.lower()
                        idx = low.find(needle)
                        if idx == -1:
                            continue
                        snippet = self._snippet(line, idx, len(query))
                        score = low.count(needle) * 10 + (1 if line.lstrip().startswith("#") else 0)
                        hits.append((path, line_no, snippet, score))
            except OSError:
                continue
        if not hits:
            return f"[brain] search '{query}' :: 0 hits"
        hits.sort(key=lambda h: (-h[3], h[0], h[1]))
        top = hits[:max_hits]
        lines = [f"[brain] search '{query}' :: top {len(top)} of {len(hits)}"]
        for path, line_no, snippet, _ in top:
            rel = self._rel_from_sanctum(path)
            lines.append(f"  {rel}:{line_no}\n    {snippet}")
        return "\n".join(lines)

    # --------------------------------------------------------------- grep
    def _grep(self, pattern: str, max_hits: int) -> str:
        kdir = self._knowledge_dir()
        if kdir is None:
            return "[brain] _shared-memory/knowledge/ not found"
        try:
            rx = re.compile(pattern, re.IGNORECASE)
        except re.error as exc:
            return f"[brain] bad regex: {exc}"
        hits: list[tuple[str, int, str]] = []
        for path in self._iter_markdown(kdir):
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as fp:
                    for line_no, line in enumerate(fp, start=1):
                        m = rx.search(line)
                        if m:
                            hits.append((path, line_no, self._snippet(line, m.start(), m.end() - m.start())))
                            if len(hits) >= max_hits * 4:
                                break
            except OSError:
                continue
        if not hits:
            return f"[brain] grep /{pattern}/ :: 0 hits"
        top = hits[:max_hits]
        lines = [f"[brain] grep /{pattern}/ :: top {len(top)} of {len(hits)}"]
        for path, line_no, snippet in top:
            rel = self._rel_from_sanctum(path)
            lines.append(f"  {rel}:{line_no}: {snippet}")
        return "\n".join(lines)

    # -------------------------------------------------------------- render
    def _render(self, target: str | None) -> str:
        api_dir = self._graph_api_dir()
        if api_dir is None:
            return "[brain] tools/memory-graph-render not installed"
        # Ensure import path
        if api_dir not in sys.path:
            sys.path.insert(0, os.path.dirname(api_dir))
        try:
            import importlib
            api = importlib.import_module("memory_graph_render.api")
        except Exception:
            # Fall back to invoking via CLI.
            return self._render_via_cli(target)

        try:
            if target and hasattr(api, "render_file"):
                out_path = api.render_file(target)
            elif hasattr(api, "render_index"):
                out_path = api.render_index()
            elif hasattr(api, "render"):
                out_path = api.render(target) if target else api.render()
            else:
                return self._render_via_cli(target)
            return f"[brain] rendered -> {out_path}"
        except Exception as exc:
            return f"[brain] render error: {exc}"

    def _render_via_cli(self, target: str | None) -> str:
        cmd = [sys.executable, "-m", "memory_graph_render"]
        if target:
            cmd += ["--file", target]
        try:
            cp = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)
            out = (cp.stdout or "") + (cp.stderr or "")
            return f"[brain] render (cli)\n{out.rstrip()}" if out.strip() else f"[brain] render exit={cp.returncode}"
        except Exception as exc:
            return f"[brain] render cli error: {exc}"

    # --------------------------------------------------------------- index
    def _index(self) -> str:
        kdir = self._knowledge_dir()
        if kdir is None:
            return "[brain] _shared-memory/knowledge/ not found"
        files = list(self._iter_markdown(kdir))
        total_bytes = 0
        newest = (0.0, "")
        for p in files:
            try:
                st = os.stat(p)
                total_bytes += st.st_size
                if st.st_mtime > newest[0]:
                    newest = (st.st_mtime, p)
            except OSError:
                continue
        newest_rel = self._rel_from_sanctum(newest[1]) if newest[1] else "-"
        newest_ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(newest[0])) if newest[0] else "-"
        return (
            f"[brain] index\n"
            f"  dir:    {self._rel_from_sanctum(kdir)}\n"
            f"  files:  {len(files)}\n"
            f"  bytes:  {total_bytes:,}\n"
            f"  newest: {newest_rel} ({newest_ts})"
        )

    # ------------------------------------------------------------- helpers
    def _sanctum_root_path(self) -> str | None:
        if self._sanctum_root:
            return self._sanctum_root
        here = os.path.abspath(os.path.dirname(__file__))
        # extensions/brain -> tools/sinister-rkoj-qt -> tools -> sanctum-root
        for _ in range(8):
            if os.path.isdir(os.path.join(here, "_shared-memory")):
                self._sanctum_root = here
                return here
            parent = os.path.dirname(here)
            if parent == here:
                break
            here = parent
        return None

    def _knowledge_dir(self) -> str | None:
        root = self._sanctum_root_path()
        if not root:
            return None
        kdir = os.path.join(root, KNOWLEDGE_REL)
        return kdir if os.path.isdir(kdir) else None

    def _graph_api_dir(self) -> str | None:
        root = self._sanctum_root_path()
        if not root:
            return None
        api_dir = os.path.join(root, GRAPH_API_REL)
        return api_dir if os.path.isdir(api_dir) else None

    def _renders_dir(self) -> str | None:
        root = self._sanctum_root_path()
        if not root:
            return None
        rdir = os.path.join(root, RENDERS_REL)
        return rdir if os.path.isdir(rdir) else None

    def _latest_renders(self, limit: int = 1) -> list[str]:
        rdir = self._renders_dir()
        if not rdir:
            return []
        entries: list[tuple[float, str]] = []
        for name in os.listdir(rdir):
            if not name.lower().endswith(".html"):
                continue
            full = os.path.join(rdir, name)
            try:
                entries.append((os.stat(full).st_mtime, full))
            except OSError:
                continue
        entries.sort(reverse=True)
        return [p for _, p in entries[:limit]]

    @staticmethod
    def _iter_markdown(root: str):
        for dirpath, _dirnames, filenames in os.walk(root):
            for name in filenames:
                if name.lower().endswith(".md"):
                    yield os.path.join(dirpath, name)

    @staticmethod
    def _snippet(line: str, idx: int, match_len: int) -> str:
        start = max(0, idx - SNIPPET_RADIUS)
        end = min(len(line), idx + match_len + SNIPPET_RADIUS)
        snip = line[start:end].strip()
        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(line) else ""
        return f"{prefix}{snip}{suffix}"

    def _rel_from_sanctum(self, path: str) -> str:
        root = self._sanctum_root_path()
        if not root or not path:
            return path
        try:
            return os.path.relpath(path, root).replace("\\", "/")
        except ValueError:
            return path

    @staticmethod
    def _open_path(path: str) -> None:
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])


# Doctrine-pattern bare-function fallback.
_singleton = BrainExtension()


def handle(args: list[str], pane: Any, app: Any) -> str:
    return _singleton.hook_slash(args, pane, app)
