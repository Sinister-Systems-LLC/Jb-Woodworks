# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
"""Scheduler :: cron-like project automation for RKOJ.

Schedule entries live in `<sanctum_root>/_shared-memory/schedule.json` as a
JSON array. Each entry has `{id, name, cron, kind, action, enabled,
created_at, last_run, next_run}`. Supported action kinds:

  * `http`         — fire a generic HTTP request via httpx
  * `script`       — invoke a whitelisted .bat under sinister-bus scripts
  * `spawn-agent`  — launch a project session via start-sinister-session.ps1
  * `inbox`        — placeholder (server-side dispatch via inbox_mod will be wired later)
  * `resume-cycle` — placeholder (use /api/cycle-points/{slug}/resume directly)

`SchedulerLoop` is the async daemon: server.py constructs one at startup,
calls `start()`, and the loop ticks every 30 s, firing due entries through
an asyncio.Semaphore so at most N concurrent actions run.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    from croniter import croniter  # type: ignore
    HAVE_CRONITER = True
except Exception:
    croniter = None  # type: ignore
    HAVE_CRONITER = False

log = logging.getLogger("rkoj.scheduler")


def schedule_path(sanctum_root) -> Path:
    return Path(sanctum_root) / "_shared-memory" / "schedule.json"


def load_schedule(sanctum_root) -> list[dict]:
    sp = schedule_path(sanctum_root)
    if not sp.exists():
        return []
    try:
        data = json.loads(sp.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_schedule(sanctum_root, entries: list[dict]) -> None:
    sp = schedule_path(sanctum_root)
    sp.parent.mkdir(parents=True, exist_ok=True)
    sp.write_text(json.dumps(entries, indent=2, sort_keys=True), encoding="utf-8")


def compute_next(cron_expr: str, after: datetime | None = None) -> str | None:
    """Return ISO-8601 of next firing time, or None if croniter is unavailable / cron invalid."""
    if not HAVE_CRONITER or not cron_expr:
        return None
    after = after or datetime.now(timezone.utc)
    try:
        return croniter(cron_expr, after).get_next(datetime).isoformat()
    except Exception:
        return None


async def fire_action(entry: dict, httpx_client=None) -> dict:
    """Dispatch one schedule entry by kind. Returns {ok, ms, error?, ...}."""
    t0 = time.monotonic()
    kind = entry.get("kind")
    act = entry.get("action") or {}
    try:
        if kind == "http":
            import httpx
            method = act.get("method", "GET")
            url = act.get("url")
            if not url:
                return {"ok": False, "error": "http kind missing 'url'",
                        "ms": int((time.monotonic() - t0) * 1000)}
            async with httpx.AsyncClient(timeout=10.0) as c:
                r = await c.request(method, url, json=act.get("body"))
                ok = r.status_code < 400
                return {
                    "ok": ok,
                    "status": r.status_code,
                    "ms": int((time.monotonic() - t0) * 1000),
                }

        elif kind == "script":
            script = act.get("script", "")
            whitelist = {
                "check-hetzner-state",
                "verify-backups",
                "memory-garden",
                "aggregate-gotchas",
                "prepare-for-migration-dryrun",
            }
            if script not in whitelist:
                return {"ok": False, "error": f"script not whitelisted: {script}",
                        "ms": int((time.monotonic() - t0) * 1000)}
            hub = r"D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\scripts"
            sp = Path(hub) / f"{script}.bat"
            if not sp.exists():
                return {"ok": False, "error": f"script file missing: {sp}",
                        "ms": int((time.monotonic() - t0) * 1000)}
            proc = await asyncio.create_subprocess_exec(
                str(sp), *(act.get("args") or []),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                await asyncio.wait_for(proc.communicate(), timeout=300)
            except asyncio.TimeoutError:
                try:
                    proc.kill()
                except Exception:
                    pass
                return {"ok": False, "error": "script timeout (300s)",
                        "ms": int((time.monotonic() - t0) * 1000)}
            return {
                "ok": proc.returncode == 0,
                "rc": proc.returncode,
                "ms": int((time.monotonic() - t0) * 1000),
            }

        elif kind == "spawn-agent":
            ps1 = r"D:\Sinister Sanctum\automations\start-sinister-session.ps1"
            if not act.get("project"):
                return {"ok": False, "error": "spawn-agent missing 'project'",
                        "ms": int((time.monotonic() - t0) * 1000)}
            args = [
                "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-File", ps1,
                "-Project", act["project"],
                "-Mode", act.get("mode", "dev"),
            ]
            if act.get("fast"):
                args.append("-Fast")
            if act.get("custom_prompt"):
                args += ["-CustomPrompt", act["custom_prompt"]]
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            return {
                "ok": True,
                "pid": proc.pid,
                "ms": int((time.monotonic() - t0) * 1000),
            }

        elif kind == "inbox":
            return {
                "ok": False,
                "error": "inbox-kind not yet wired",
                "ms": int((time.monotonic() - t0) * 1000),
            }

        elif kind == "resume-cycle":
            return {
                "ok": False,
                "error": "resume-cycle wired via /api/cycle-points/{slug}/resume directly",
                "ms": int((time.monotonic() - t0) * 1000),
            }

        else:
            return {
                "ok": False,
                "error": f"unknown kind: {kind}",
                "ms": int((time.monotonic() - t0) * 1000),
            }

    except Exception as e:
        return {
            "ok": False,
            "error": f"{type(e).__name__}: {e}",
            "ms": int((time.monotonic() - t0) * 1000),
        }


class SchedulerLoop:
    """Async daemon: ticks every 30 s, fires due entries (semaphore-bounded)."""

    def __init__(self, sanctum_root, semaphore_size: int = 5):
        self.sanctum_root = sanctum_root
        self.sem = asyncio.Semaphore(semaphore_size)
        self.running = False
        self.task: asyncio.Task | None = None

    async def start(self) -> None:
        if self.running:
            return
        self.running = True
        self.task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except Exception:
                pass

    async def _loop(self) -> None:
        log.info("scheduler loop started")
        hb = Path(self.sanctum_root) / "_shared-memory" / "heartbeats" / "rkoj-scheduler.beat"
        hb.parent.mkdir(parents=True, exist_ok=True)
        try:
            while self.running:
                try:
                    hb.touch()
                except Exception:
                    pass
                entries = load_schedule(self.sanctum_root)
                now = datetime.now(timezone.utc)
                changed = False
                for e in entries:
                    if not e.get("enabled", True):
                        continue
                    next_run = e.get("next_run")
                    if not next_run:
                        e["next_run"] = compute_next(e.get("cron", "0 0 * * *"))
                        changed = True
                        continue
                    try:
                        nr = datetime.fromisoformat(next_run.replace("Z", "+00:00"))
                    except Exception:
                        e["next_run"] = compute_next(e.get("cron", "0 0 * * *"))
                        changed = True
                        continue
                    if now >= nr:
                        async with self.sem:
                            result = await fire_action(e)
                        e["last_run"] = {"at": now.isoformat(), **result}
                        e["next_run"] = compute_next(e.get("cron", "0 0 * * *"))
                        log.info("fired schedule %s: %s", e.get("id"), result)
                        changed = True
                if changed:
                    try:
                        save_schedule(self.sanctum_root, entries)
                    except Exception as e:
                        log.exception("scheduler: failed to persist schedule: %s", e)
                await asyncio.sleep(30)
        except asyncio.CancelledError:
            log.info("scheduler loop cancelled")
        except Exception as e:
            log.exception("scheduler loop crashed: %s", e)
