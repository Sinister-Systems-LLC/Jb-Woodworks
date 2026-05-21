"""sinister-watchdog :: core loop.

Author: RKOJ-ELENO :: 2026-05-21
License: AGPL-3.0-or-later

Watches three surfaces and respawns broken pieces of the Sanctum fleet:

  1. Local agent heartbeats under `_shared-memory/heartbeats/<slug>.json|.beat`
     - Stale > 5 min → look up launch command in `registry.json` → spawn detached.

  2. MCP servers from `~/.claude/.mcp.json`
     - Read-only on that file (operator-owned).
     - For each: probe by spawning `command args...` with stdio piped, sending an
       MCP `initialize` request, waiting for a response, then disconnecting.
     - If unresponsive: respawn the same command detached (it stays alive for the
       next Claude Code session to attach to via stdio).
     - NOTE: stdio MCP servers are spawned by Claude Code itself per session.
       The watchdog's job here is to verify the *command resolves and starts*.
       If a probe fails, we log + flag — we never write to `.mcp.json`.

  3. Optional docker services from `registry.json` with `kind: "docker"`.
     - `docker ps --filter name=<name>` → start if not running.

Everything is logged to `_shared-memory/watchdog.log`.

Pure Python stdlib. No third-party deps required.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SanctumPaths:
    """Canonical filesystem layout the watchdog reads / writes."""

    sanctum_root: Path
    heartbeats: Path
    watchdog_log: Path
    pid_file: Path
    state_file: Path
    registry_file: Path
    mcp_config: Path

    @classmethod
    def detect(cls, override_root: Path | None = None) -> "SanctumPaths":
        root = override_root or _detect_sanctum_root()
        sm = root / "_shared-memory"
        sm.mkdir(parents=True, exist_ok=True)
        return cls(
            sanctum_root=root,
            heartbeats=sm / "heartbeats",
            watchdog_log=sm / "watchdog.log",
            pid_file=root / "tools" / "sinister-watchdog" / "watchdog.pid",
            state_file=root / "tools" / "sinister-watchdog" / "state.json",
            registry_file=root / "tools" / "sinister-watchdog" / "registry.json",
            mcp_config=Path.home() / ".claude" / ".mcp.json",
        )


def _detect_sanctum_root() -> Path:
    # Env override
    env = os.environ.get("SINISTER_SANCTUM_ROOT")
    if env and Path(env).exists():
        return Path(env)
    # Default
    default = Path(r"D:\Sinister Sanctum")
    if default.exists():
        return default
    # Walk up from this file
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "_shared-memory").is_dir() and (parent / "tools").is_dir():
            return parent
    return default  # last resort


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


_LOG_LOCK = threading.Lock()


def _log(paths: SanctumPaths, level: str, msg: str) -> None:
    line = f"[{_now_iso()}] [{level}] {msg}\n"
    with _LOG_LOCK:
        try:
            # Rotate at 5 MB
            if paths.watchdog_log.exists() and paths.watchdog_log.stat().st_size > 5 * 1024 * 1024:
                rotated = paths.watchdog_log.with_suffix(".log.1")
                if rotated.exists():
                    rotated.unlink()
                paths.watchdog_log.rename(rotated)
            paths.watchdog_log.parent.mkdir(parents=True, exist_ok=True)
            with paths.watchdog_log.open("a", encoding="utf-8") as f:
                f.write(line)
        except OSError:
            sys.stderr.write(line)


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Registry (what to spawn for each agent / service)
# ---------------------------------------------------------------------------


def load_registry(paths: SanctumPaths) -> dict[str, Any]:
    """Read the per-slug launch registry. Returns {} on missing/bad file."""
    if not paths.registry_file.exists():
        return {"agents": {}, "services": {}}
    try:
        return json.loads(paths.registry_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _log(paths, "WARN", f"registry.json unreadable: {exc}")
        return {"agents": {}, "services": {}}


# ---------------------------------------------------------------------------
# Heartbeat scan
# ---------------------------------------------------------------------------


def scan_heartbeats(paths: SanctumPaths, stale_minutes: int = 5) -> list[dict[str, Any]]:
    """Return one row per heartbeat file under `_shared-memory/heartbeats/`.

    Row shape: {slug, path, mtime, age_minutes, stale, content}.
    """
    rows: list[dict[str, Any]] = []
    if not paths.heartbeats.exists():
        return rows
    now = time.time()
    for p in sorted(paths.heartbeats.iterdir()):
        if not p.is_file():
            continue
        if p.suffix not in (".json", ".beat"):
            continue
        if p.name.endswith(".tmp") or ".tmp." in p.name:
            continue
        try:
            mtime = p.stat().st_mtime
        except OSError:
            continue
        age_min = (now - mtime) / 60.0
        slug = p.stem
        content: dict[str, Any] = {}
        if p.suffix == ".json":
            try:
                content = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                content = {}
        rows.append(
            {
                "slug": slug,
                "path": str(p),
                "mtime": mtime,
                "age_minutes": round(age_min, 1),
                "stale": age_min > stale_minutes,
                "content": content,
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Spawn helper
# ---------------------------------------------------------------------------


def _spawn_detached(command: list[str], cwd: str | None, env: dict[str, str] | None) -> int | None:
    """Spawn a fully-detached child. Returns pid (or None on failure)."""
    if not command:
        return None
    full_env = os.environ.copy()
    if env:
        full_env.update({str(k): str(v) for k, v in env.items()})
    creationflags = 0
    start_new_session = False
    if os.name == "nt":
        # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW
        creationflags = 0x00000008 | 0x00000200 | 0x08000000
    else:
        start_new_session = True
    try:
        proc = subprocess.Popen(
            command,
            cwd=cwd,
            env=full_env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            creationflags=creationflags,
            start_new_session=start_new_session,
        )
        return proc.pid
    except (OSError, ValueError):
        return None


def revive_agent(paths: SanctumPaths, slug: str, registry: dict[str, Any]) -> dict[str, Any]:
    """Look up the agent's launch entry and spawn it detached.

    Honors `auto_revive: false` — if set, we log + skip (operator opt-out).
    """
    agents = (registry.get("agents") or {})
    entry = agents.get(slug)
    if not entry:
        _log(paths, "WARN", f"no registry entry for stale agent '{slug}' — skipping")
        return {"slug": slug, "ok": False, "reason": "no-registry-entry"}
    if entry.get("auto_revive") is False:
        _log(paths, "INFO", f"stale agent '{slug}' has auto_revive=false — skipping per operator")
        return {"slug": slug, "ok": False, "reason": "auto-revive-disabled"}
    kind = entry.get("kind", "process")
    if kind == "docker":
        return docker_ensure(paths, slug, entry)
    cmd = entry.get("command") or []
    if isinstance(cmd, str):
        cmd = [cmd]
    args = entry.get("args") or []
    full = [*cmd, *args]
    cwd = entry.get("cwd")
    env = entry.get("env") or {}
    pid = _spawn_detached(full, cwd, env)
    if pid is None:
        _log(paths, "ERROR", f"revive_agent({slug}) spawn failed: {full!r}")
        return {"slug": slug, "ok": False, "reason": "spawn-failed", "command": full}
    _log(paths, "INFO", f"revived agent '{slug}' pid={pid} cmd={full!r}")
    return {"slug": slug, "ok": True, "pid": pid, "command": full}


# ---------------------------------------------------------------------------
# MCP probe
# ---------------------------------------------------------------------------


_INIT_REQUEST = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "sinister-watchdog", "version": "0.1.0"},
    },
}


def probe_mcp_servers(paths: SanctumPaths, timeout: float = 8.0) -> list[dict[str, Any]]:
    """Read `.mcp.json` (READ-ONLY) and probe each server.

    Probe = spawn the command, send `initialize` over stdin, wait for a response
    line on stdout. Success = response line received within timeout.
    """
    if not paths.mcp_config.exists():
        _log(paths, "WARN", f".mcp.json missing at {paths.mcp_config}")
        return []
    try:
        # Be lenient with operator-edited JSON: strip UTF-8 BOM if present.
        raw = paths.mcp_config.read_text(encoding="utf-8-sig")
        cfg = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        _log(paths, "WARN", f".mcp.json unreadable: {exc}")
        return []
    servers = cfg.get("mcpServers") or {}
    out: list[dict[str, Any]] = []
    for name, spec in servers.items():
        if not isinstance(spec, dict):
            continue
        result = _probe_one_mcp(paths, name, spec, timeout=timeout)
        out.append(result)
    return out


def _probe_one_mcp(
    paths: SanctumPaths, name: str, spec: dict[str, Any], timeout: float
) -> dict[str, Any]:
    cmd = spec.get("command")
    if not cmd:
        return {"name": name, "ok": False, "reason": "no-command"}
    args = spec.get("args") or []
    cwd = spec.get("cwd")
    env = spec.get("env") or {}

    # Resolve the executable on PATH if it's a bare name (handles Windows .exe).
    if not Path(cmd).is_absolute() and not Path(cmd).exists():
        resolved = shutil.which(cmd)
        if resolved:
            cmd_to_run = resolved
        else:
            cmd_to_run = cmd  # let Popen surface the error
    else:
        cmd_to_run = cmd

    full = [cmd_to_run, *args]
    full_env = os.environ.copy()
    full_env.update({str(k): str(v) for k, v in env.items()})

    creationflags = 0
    if os.name == "nt":
        creationflags = 0x08000000  # CREATE_NO_WINDOW

    try:
        proc = subprocess.Popen(
            full,
            cwd=cwd,
            env=full_env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
            text=False,
        )
    except (OSError, ValueError) as exc:
        return {"name": name, "ok": False, "reason": f"spawn-error:{exc}", "command": full}

    # Send the initialize request and watch for any stdout response.
    response_ok = False
    response_snippet = ""
    try:
        if proc.stdin:
            proc.stdin.write(json.dumps(_INIT_REQUEST).encode("utf-8") + b"\n")
            proc.stdin.flush()
        deadline = time.monotonic() + timeout
        # Pull one line with a deadline. We use a thread because Windows pipes
        # block. If anything comes back at all, we consider the server alive.
        result_box: list[bytes] = []

        def _reader() -> None:
            try:
                if proc.stdout:
                    line = proc.stdout.readline()
                    if line:
                        result_box.append(line)
            except OSError:
                pass

        t = threading.Thread(target=_reader, daemon=True)
        t.start()
        while time.monotonic() < deadline:
            if result_box:
                break
            if proc.poll() is not None:
                break
            time.sleep(0.1)
        if result_box:
            response_ok = True
            try:
                response_snippet = result_box[0][:200].decode("utf-8", errors="replace")
            except Exception:
                response_snippet = "(binary)"
    finally:
        try:
            if proc.poll() is None:
                if os.name == "nt":
                    proc.terminate()
                else:
                    proc.send_signal(signal.SIGTERM)
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()
        except OSError:
            pass

    return {
        "name": name,
        "ok": response_ok,
        "command": full,
        "cwd": cwd,
        "response_preview": response_snippet,
        "reason": None if response_ok else "no-response-within-timeout",
    }


def revive_mcp(paths: SanctumPaths, name: str, spec: dict[str, Any]) -> dict[str, Any]:
    """Spawn the MCP command detached. This is a best-effort 'warm it up' —
    Claude Code still owns the per-session stdio attach.
    """
    cmd = spec.get("command")
    if not cmd:
        return {"name": name, "ok": False, "reason": "no-command"}
    args = spec.get("args") or []
    cwd = spec.get("cwd")
    env = spec.get("env") or {}
    pid = _spawn_detached([cmd, *args], cwd, env)
    if pid is None:
        _log(paths, "ERROR", f"revive_mcp({name}) spawn failed")
        return {"name": name, "ok": False, "reason": "spawn-failed"}
    _log(paths, "INFO", f"revived mcp '{name}' pid={pid}")
    return {"name": name, "ok": True, "pid": pid}


# ---------------------------------------------------------------------------
# Docker service helpers
# ---------------------------------------------------------------------------


def docker_ensure(paths: SanctumPaths, slug: str, entry: dict[str, Any]) -> dict[str, Any]:
    """Make sure a docker container is running. Starts the named container if not."""
    container = entry.get("container") or slug
    image = entry.get("image")
    docker = shutil.which("docker")
    if not docker:
        _log(paths, "WARN", f"docker_ensure({slug}) — docker not on PATH; skipping")
        return {"slug": slug, "ok": False, "reason": "docker-not-installed"}
    # ps to check
    try:
        out = subprocess.run(
            [docker, "ps", "--filter", f"name=^{container}$", "--format", "{{.Names}}"],
            capture_output=True, text=True, timeout=10,
        )
        names = [n.strip() for n in (out.stdout or "").splitlines() if n.strip()]
    except (OSError, subprocess.TimeoutExpired) as exc:
        _log(paths, "WARN", f"docker ps failed for {slug}: {exc}")
        return {"slug": slug, "ok": False, "reason": "docker-ps-failed"}

    if container in names:
        return {"slug": slug, "ok": True, "container": container, "state": "already-running"}

    # Try docker start; if container doesn't exist and image is given, run it.
    try:
        rc = subprocess.run([docker, "start", container], capture_output=True, text=True, timeout=15)
        if rc.returncode == 0:
            _log(paths, "INFO", f"docker started '{container}' for slug={slug}")
            return {"slug": slug, "ok": True, "container": container, "state": "started"}
    except (OSError, subprocess.TimeoutExpired) as exc:
        _log(paths, "WARN", f"docker start failed for {slug}: {exc}")

    if image:
        run_args = [docker, "run", "-d", "--name", container, *(entry.get("docker_args") or []), image]
        try:
            rc = subprocess.run(run_args, capture_output=True, text=True, timeout=30)
            if rc.returncode == 0:
                _log(paths, "INFO", f"docker ran new '{container}' image={image} for slug={slug}")
                return {"slug": slug, "ok": True, "container": container, "state": "created"}
        except (OSError, subprocess.TimeoutExpired) as exc:
            _log(paths, "WARN", f"docker run failed for {slug}: {exc}")

    return {"slug": slug, "ok": False, "reason": "could-not-start", "container": container}


# ---------------------------------------------------------------------------
# Snapshot — one-pass status used by CLI + Forge surface
# ---------------------------------------------------------------------------


def snapshot_status(paths: SanctumPaths | None = None) -> dict[str, Any]:
    """One read-only pass — no respawns. Used by `status` CLI + Forge."""
    p = paths or SanctumPaths.detect()
    registry = load_registry(p)
    hb = scan_heartbeats(p)
    mcp_servers = []
    if p.mcp_config.exists():
        try:
            raw = p.mcp_config.read_text(encoding="utf-8-sig")
            cfg = json.loads(raw)
            mcp_servers = list((cfg.get("mcpServers") or {}).keys())
        except (OSError, json.JSONDecodeError):
            mcp_servers = []
    return {
        "ts_utc": _now_iso(),
        "sanctum_root": str(p.sanctum_root),
        "heartbeats": hb,
        "stale_count": sum(1 for r in hb if r["stale"]),
        "agent_total": len(hb),
        "registered_agents": list((registry.get("agents") or {}).keys()),
        "mcp_servers_configured": mcp_servers,
        "mcp_config_path": str(p.mcp_config),
        "log_path": str(p.watchdog_log),
        "pid_file": str(p.pid_file),
        "running": p.pid_file.exists(),
    }


# ---------------------------------------------------------------------------
# Watchdog loop
# ---------------------------------------------------------------------------


@dataclass
class Watchdog:
    paths: SanctumPaths = field(default_factory=SanctumPaths.detect)
    poll_interval: float = 60.0
    stale_minutes: float = 5.0
    probe_mcp_interval_cycles: int = 5     # probe MCP every N heartbeat cycles
    enable_mcp_probe: bool = True
    enable_docker: bool = True
    _stop: bool = False

    def stop(self, *_a: Any) -> None:
        self._stop = True
        _log(self.paths, "INFO", "stop requested")

    def run(self) -> None:
        _log(self.paths, "INFO", f"watchdog start interval={self.poll_interval}s stale={self.stale_minutes}m")
        self._write_pid()
        try:
            signal.signal(signal.SIGTERM, self.stop)
        except (ValueError, AttributeError):
            pass
        try:
            if os.name != "nt":
                signal.signal(signal.SIGINT, self.stop)
        except (ValueError, AttributeError):
            pass

        cycle = 0
        while not self._stop:
            try:
                self._tick(cycle)
            except Exception as exc:  # noqa: BLE001 — log + keep going
                _log(self.paths, "ERROR", f"tick failed: {exc}")
            cycle += 1
            for _ in range(int(self.poll_interval * 10)):
                if self._stop:
                    break
                time.sleep(0.1)

        _log(self.paths, "INFO", "watchdog stopped")
        self._clear_pid()

    def _tick(self, cycle: int) -> None:
        registry = load_registry(self.paths)

        # 1. Heartbeats — with per-slug stale-minutes override
        overrides = (registry.get("stale_minutes_override") or {})
        hb_rows = scan_heartbeats(self.paths, stale_minutes=self.stale_minutes)
        # Re-flag stale using overrides where present.
        for r in hb_rows:
            thresh = overrides.get(r["slug"], self.stale_minutes)
            r["stale"] = r["age_minutes"] > thresh
        stale = [r for r in hb_rows if r["stale"]]
        if stale:
            _log(self.paths, "WARN", f"stale agents: {[r['slug'] for r in stale]}")
            for row in stale:
                revive_agent(self.paths, row["slug"], registry)

        # 2. Docker services (from registry, not from .mcp.json)
        services = (registry.get("services") or {})
        if self.enable_docker:
            for slug, entry in services.items():
                if not isinstance(entry, dict):
                    continue
                if entry.get("kind") != "docker":
                    continue
                if entry.get("enabled") is False:
                    continue
                docker_ensure(self.paths, slug, entry)

        # 3. MCP probes (less often — every N cycles)
        if self.enable_mcp_probe and cycle % self.probe_mcp_interval_cycles == 0:
            results = probe_mcp_servers(self.paths)
            broken = [r for r in results if not r["ok"]]
            if broken:
                _log(self.paths, "WARN", f"unresponsive mcp: {[r['name'] for r in broken]}")
                if not self.paths.mcp_config.exists():
                    return
                try:
                    raw = self.paths.mcp_config.read_text(encoding="utf-8-sig")
                    cfg = json.loads(raw)
                except (OSError, json.JSONDecodeError):
                    return
                servers = cfg.get("mcpServers") or {}
                for r in broken:
                    spec = servers.get(r["name"])
                    if spec:
                        revive_mcp(self.paths, r["name"], spec)

        # 4. Write a state snapshot for the CLI / Forge surface
        try:
            self.paths.state_file.parent.mkdir(parents=True, exist_ok=True)
            snap = {
                "cycle": cycle,
                "ts_utc": _now_iso(),
                "heartbeats": hb_rows,
                "stale": [r["slug"] for r in stale],
            }
            self.paths.state_file.write_text(json.dumps(snap, indent=2), encoding="utf-8")
        except OSError:
            pass

    def _write_pid(self) -> None:
        try:
            self.paths.pid_file.parent.mkdir(parents=True, exist_ok=True)
            self.paths.pid_file.write_text(str(os.getpid()), encoding="utf-8")
        except OSError:
            pass

    def _clear_pid(self) -> None:
        try:
            if self.paths.pid_file.exists():
                self.paths.pid_file.unlink()
        except OSError:
            pass
