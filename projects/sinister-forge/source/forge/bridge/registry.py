# Sinister Forge :: bridge/registry.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# In-process agent registry for the REST/SSE bridge. Wraps subprocess.Popen
# (NOT asyncio.subprocess - bridge runs in Flask thread world, not Textual's
# event loop). Each agent has a stdout pump thread that fans lines out to
# (1) a ring buffer for HTTP fetches and (2) SSE subscriber queues.

from __future__ import annotations

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


RING_SIZE = 2000  # last N lines kept per agent for late subscribers


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
        return rec

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
