# Sinister Forge :: bridge/registry.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# In-process agent registry for the REST/SSE bridge. Wraps subprocess.Popen
# (NOT asyncio.subprocess - bridge runs in Flask thread world, not Textual's
# event loop). Each agent has a stdout pump thread that fans lines out to
# (1) a ring buffer for HTTP fetches and (2) SSE subscriber queues.

from __future__ import annotations

import json
import os
import queue
import shutil
import subprocess
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path


SANCTUM_ROOT = Path(os.environ.get("SANCTUM_ROOT") or "D:/Sinister Sanctum")


RING_SIZE = 2000  # last N lines kept per agent for late subscribers

# PH16 file-edit watcher: scan period + glob roots. Lazily started on first
# Registry.spawn() so test code paths that never spawn don't pay the cost.
_WATCH_ROOTS = (SANCTUM_ROOT / "projects",)
_WATCH_GLOB_SUFFIX = "source"  # only watch projects/<x>/source/* subtrees
_WATCH_DEBOUNCE_SEC = 0.6      # collapse rapid-fire writes (IDE saves)
_WATCH_IGNORE_SUFFIXES = (".pyc", ".pyo", ".swp", ".tmp", "~", ".egg-info")
_WATCH_IGNORE_DIRS = (".git", "__pycache__", "node_modules", ".venv", ".sanctum-staging")


@dataclass
class AgentRecord:
    id: str
    agent_name: str
    project_key: str
    project_display: str
    accent: str
    mode: str
    host: str  # "claude" | "codex"
    token_mode: str
    speed: str
    started_at: float
    project_root: Path
    proc: subprocess.Popen | None = None
    ring: deque[str] = field(default_factory=lambda: deque(maxlen=RING_SIZE))
    subscribers: list[queue.Queue] = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock)
    status: str = "ready"
    exit_code: int | None = None

    def to_public_dict(self) -> dict:
        return {
            "id": self.id,
            "agent_name": self.agent_name,
            "project_key": self.project_key,
            "project_display": self.project_display,
            "accent": self.accent,
            "mode": self.mode,
            "host": self.host,
            "status": self.status,
            "pid": self.proc.pid if self.proc else None,
            "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self.started_at)),
            "exit_code": self.exit_code,
        }


class Registry:
    def __init__(self) -> None:
        self._agents: dict[str, AgentRecord] = {}
        self._lock = threading.Lock()
        # PH16 file-edit notification pump (lazy-init on first spawn)
        self._file_watch_started = False
        self._file_watch_lock = threading.Lock()

    def list(self) -> list[AgentRecord]:
        with self._lock:
            return list(self._agents.values())

    def get(self, agent_id: str) -> AgentRecord | None:
        with self._lock:
            return self._agents.get(agent_id)

    def remove(self, agent_id: str) -> None:
        with self._lock:
            self._agents.pop(agent_id, None)

    def spawn(
        self,
        *,
        project_key: str,
        project_display: str,
        project_root: Path,
        agent_name: str,
        accent: str,
        host: str,
        mode: str,
        token_mode: str,
        speed: str,
        phrase: str,
        focus_intent: str = "",
    ) -> AgentRecord:
        binary = "claude" if host == "claude" else "codex"
        resolved = shutil.which(binary)
        if not resolved:
            raise FileNotFoundError(
                f"{binary} not on PATH. Install + retry, or pick a different Agent Host."
            )

        if host == "claude":
            argv = [resolved, "--dangerously-skip-permissions", phrase]
        else:
            argv = [resolved, "exec", phrase]

        env = dict(os.environ)
        env.update({
            "SINISTER_AGENT_NAME": agent_name,
            "SINISTER_ACCENT_COLOR": accent,
            "SINISTER_PROJECT_KEY": project_key,
            "SINISTER_MODE": mode,
            "SINISTER_TOKEN_MODE": token_mode,
            "SINISTER_SPEED": speed,
            "SINISTER_HOST": host,
            "SINISTER_VIA": "forge-bridge",
        })

        try:
            proc = subprocess.Popen(
                argv,
                cwd=str(project_root),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                bufsize=1,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except FileNotFoundError as e:
            raise FileNotFoundError(f"failed to spawn {binary}: {e}") from e

        rec = AgentRecord(
            id=uuid.uuid4().hex[:12],
            agent_name=agent_name,
            project_key=project_key,
            project_display=project_display,
            accent=accent,
            mode=mode,
            host=host,
            token_mode=token_mode,
            speed=speed,
            started_at=time.time(),
            project_root=project_root,
            proc=proc,
            status="running",
        )

        with self._lock:
            self._agents[rec.id] = rec

        threading.Thread(target=_pump_stdout, args=(rec,), daemon=True).start()
        _write_resume_point(rec, focus_intent=focus_intent)
        # PH16: ensure the file-edit notification pump is running so every
        # active agent receives [FILE-CHANGED] events from sibling editors.
        self._ensure_file_watch_started()
        return rec

    def _ensure_file_watch_started(self) -> None:
        """Lazy-start the watchdog observer on first spawn.

        Imports watchdog only when needed - tests that touch the registry
        for unit-level smoke (no real spawn) shouldn't pay the import cost
        or risk a missing-dep failure if watchdog isn't installed in dev.
        """
        with self._file_watch_lock:
            if self._file_watch_started:
                return
            try:
                _start_file_watcher(self)
                self._file_watch_started = True
            except Exception as e:
                # Non-fatal: file-edit notifications are sugar, not a contract.
                print(f"[forge-bridge] file-watch start failed: {e}", flush=True)

    def all_slugs(self) -> list[str]:
        """Distinct agent slugs/names currently in the registry (for FILE-CHANGED fanout)."""
        with self._lock:
            return list({rec.agent_name for rec in self._agents.values() if rec.agent_name})

    def slug_owning_path(self, path: str) -> str | None:
        """Heuristic: if `path` lives under one of the registry's project_roots,
        return the agent_name whose project that is. Used to suppress self-
        notifications when an agent edits its own project file.

        For multi-agent on the same project, both agents are notified - the
        editor identity isn't recoverable from filesystem events alone.
        """
        norm = str(Path(path).resolve()).lower()
        with self._lock:
            best: tuple[int, str] | None = None
            for rec in self._agents.values():
                proot = str(Path(rec.project_root).resolve()).lower()
                if norm.startswith(proot) and (best is None or len(proot) > best[0]):
                    best = (len(proot), rec.agent_name)
            return best[1] if best else None

    def terminate(self, agent_id: str) -> bool:
        rec = self.get(agent_id)
        if not rec or not rec.proc:
            return False
        try:
            rec.proc.terminate()
            try:
                rec.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                rec.proc.kill()
                rec.proc.wait(timeout=2)
        except Exception:
            try:
                rec.proc.kill()
            except Exception:
                pass
        rec.status = "exited"
        rec.exit_code = rec.proc.returncode if rec.proc else None
        return True

    def subscribe(self, agent_id: str) -> tuple[AgentRecord, queue.Queue] | None:
        rec = self.get(agent_id)
        if not rec:
            return None
        sub: queue.Queue = queue.Queue(maxsize=4000)
        with rec.lock:
            # Replay ring buffer to give the new subscriber recent context
            for line in list(rec.ring):
                try:
                    sub.put_nowait(line)
                except queue.Full:
                    break
            rec.subscribers.append(sub)
        return rec, sub

    def unsubscribe(self, rec: AgentRecord, sub: queue.Queue) -> None:
        with rec.lock:
            try:
                rec.subscribers.remove(sub)
            except ValueError:
                pass


def _write_resume_point(rec: AgentRecord, *, focus_intent: str) -> None:
    """Drop a sinister.resume-point.v1 JSON so the spawned agent boots warm."""
    try:
        head, head_msg, recent = _git_head_info()
    except Exception:
        head, head_msg, recent = ("", "", [])
    payload = {
        "schema_version": "sinister.resume-point.v1",
        "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "project": rec.project_display,
        "agent_name": rec.agent_name,
        "mode": rec.mode,
        "focus_intent": focus_intent,
        "via": "forge-bridge",
        "git": {
            "branch": _git_branch(),
            "head": head,
            "head_msg": head_msg,
            "recent_commits": recent,
        },
        "progress_top3": [],
        "latest_plan": {"dir": None, "artifact": None},
    }
    try:
        rp_dir = SANCTUM_ROOT / "_shared-memory" / "resume-points" / rec.project_display
        rp_dir.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y-%m-%dT%H%M%SZ", time.gmtime())
        (rp_dir / f"{stamp}.json").write_text(
            json.dumps(payload, indent=4), encoding="utf-8"
        )
    except Exception:
        pass


def _git_branch() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(SANCTUM_ROOT), text=True, stderr=subprocess.DEVNULL, timeout=5,
        ).strip()
    except Exception:
        return ""


def _git_head_info() -> tuple[str, str, list[str]]:
    try:
        out = subprocess.check_output(
            ["git", "log", "-10", "--pretty=format:%H|%s"],
            cwd=str(SANCTUM_ROOT), text=True, stderr=subprocess.DEVNULL, timeout=5,
        )
    except Exception:
        return ("", "", [])
    lines = [ln for ln in out.splitlines() if "|" in ln]
    if not lines:
        return ("", "", [])
    head_hash, head_msg = lines[0].split("|", 1)
    recent = [ln.replace("|", " ", 1)[:120] for ln in lines]
    return (head_hash, head_msg, recent)


def _pump_stdout(rec: AgentRecord) -> None:
    """Drain the child's stdout line-by-line into ring + every SSE subscriber."""
    if not rec.proc or not rec.proc.stdout:
        return
    try:
        for raw in rec.proc.stdout:
            line = raw.rstrip("\n").rstrip("\r")
            with rec.lock:
                rec.ring.append(line)
                dead: list[queue.Queue] = []
                for sub in rec.subscribers:
                    try:
                        sub.put_nowait(line)
                    except queue.Full:
                        dead.append(sub)
                for d in dead:
                    try:
                        rec.subscribers.remove(d)
                    except ValueError:
                        pass
    except Exception:
        pass
    finally:
        rec.status = "exited"
        rec.exit_code = rec.proc.returncode if rec.proc else None
        # Tell subscribers we're done
        with rec.lock:
            for sub in rec.subscribers:
                try:
                    sub.put_nowait("__EOF__")
                except queue.Full:
                    pass


REGISTRY = Registry()


# ---- PH16 file-edit watchdog observer ---------------------------------------


def _start_file_watcher(registry: "Registry") -> None:
    """Spin up the watchdog Observer that fanouts [FILE-CHANGED] inbox JSONs.

    Imports watchdog lazily inside this function. The observer is daemon-
    threaded so the bridge process exits clean on Ctrl+C.
    """
    from watchdog.events import FileSystemEventHandler  # noqa: WPS433
    from watchdog.observers import Observer  # noqa: WPS433

    from forge.swarm import notify_file_changed  # local import: swarm uses no Textual

    class _Handler(FileSystemEventHandler):
        def __init__(self) -> None:
            super().__init__()
            self._last_seen: dict[str, float] = {}

        def on_modified(self, event) -> None:  # noqa: WPS110
            try:
                if event.is_directory:
                    return
                self._dispatch(event.src_path)
            except Exception:
                pass

        def on_created(self, event) -> None:
            try:
                if event.is_directory:
                    return
                self._dispatch(event.src_path)
            except Exception:
                pass

        def _dispatch(self, src_path: str) -> None:
            p = Path(src_path)
            if any(d in p.parts for d in _WATCH_IGNORE_DIRS):
                return
            if any(p.name.endswith(suf) for suf in _WATCH_IGNORE_SUFFIXES):
                return
            now = time.time()
            last = self._last_seen.get(src_path, 0.0)
            if now - last < _WATCH_DEBOUNCE_SEC:
                return
            self._last_seen[src_path] = now
            editor = registry.slug_owning_path(src_path) or "external"
            subscribers = registry.all_slugs()
            if not subscribers:
                return
            notify_file_changed(
                editor_slug=editor,
                file_path=src_path,
                subscribers=subscribers,
            )

    observer = Observer()
    handler = _Handler()
    for root in _WATCH_ROOTS:
        if not root.exists():
            continue
        # Recursive watch, but watchdog can't filter directories before delivery
        # so the handler applies _WATCH_IGNORE_DIRS post-hoc.
        observer.schedule(handler, str(root), recursive=True)
    observer.daemon = True
    observer.start()
    print(f"[forge-bridge] file-watch started on {_WATCH_ROOTS}", flush=True)
