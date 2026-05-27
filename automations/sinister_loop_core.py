#!/usr/bin/env python3
"""sinister_loop_core.py — unified looper primitive (jcode-parity + Github-Input synthesis).

Author: RKOJ-ELENO :: 2026-05-26

Operator hard-canonical 2026-05-26 (verbatim):
  "C:\\Users\\Zonia\\Desktop\\Github Input review this and how jcode does looping
   and make the best fastest and most efficient looper we can"

What it is
----------
A single-file Python primitive consolidating the looping mechanics scattered
across 6+ files in `automations/` (loop-relentless-watchdog.ps1, loop_checkpoint.py,
loop_open_agents.py, quality-monotonic-loop.ps1, overseer_loop_quality_agent.py,
eve_compliance_train_loop.py). Designed to be IMPORTED by callers — existing
loopers stay in place and migrate incrementally per `no-bat-no-ps1` doctrine.

Composed primitives (each ~30-60 LOC, no external deps beyond stdlib):

1. AdaptiveScheduler   — jcode scheduler.rs:188-247 parity. Computes next-tick
                          interval from (window_remaining / cycles_available),
                          clamped [min,max]. on_rate_limit() doubles backoff
                          (cap 64x); on_success() resets to 1x.

2. BackoffHelper       — openhuman useDaemonLifecycle.ts:60 pattern. Jittered
                          exponential backoff with attempt counter.

3. UsageLog            — jcode scheduler.rs:18-136 parity. Rolling 24h JSONL
                          window of (iter, tokens_in, tokens_out, duration_s).
                          Used by AdaptiveScheduler to reserve operator budget.

4. HeartbeatProbe      — Unifies the 3 different heartbeat readers in our
                          looper stack. Single source of truth for
                          "is agent <slug> alive?" (default fresh window 30min
                          per fleet-wide doctrine).

5. OperatorActive      — Reads `_shared-memory/heartbeats/sinister-operator.json`
                          (falls back to True if file missing — fail-open).
                          Callers de-prioritize expensive ticks when stale.

6. LoopGuard           — Context manager. Max-iters + max-seconds + jcode-style
                          forced-end after K iters without progress
                          (runner.rs:917-959 parity).

7. SwarmFanout         — Light wrapper over existing automations/sinister_swarm.py
                          for callers that want the unified looper to spawn slices.

CLI
---
  python sinister_loop_core.py smoke         — self-test all primitives
  python sinister_loop_core.py probe <slug>  — print live agent status
  python sinister_loop_core.py operator      — print operator active state
  python sinister_loop_core.py demo          — run a 5-tick adaptive loop

SOURCE CITATIONS (from sub-agent audit 2026-05-26)
--------------------------------------------------
- jcode `scheduler.rs:188-247`        — AdaptiveScheduler.calculate_interval
- jcode `scheduler.rs:260-267`        — on_rate_limit_hit / on_successful_cycle
- jcode `scheduler.rs:24,133-136`     — 24h rolling window (PRUNE_AGE_HOURS=24)
- jcode `runner.rs:584-585`           — active_user_sessions pause check
- jcode `runner.rs:917-959`           — forced-end after 2 missed end_cycle
- jcode `turn_loops.rs:693-714`       — empty-tool-calls stop condition
- openhuman `useDaemonLifecycle.ts:60-62` — BASE * 2^(attempt-1) capped
- dexter `agent.ts:24-25`             — MAX_OVERFLOW_RETRIES=2, MAX_ITERATIONS=10
- Decepticon `health.go:46-77`        — deadline-based polling
- ACE `layer.py:337-349`              — run_in_loop vs run_via_events toggle
"""

from __future__ import annotations

import json
import math
import os
import random
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Optional


SANCTUM_ROOT = Path(os.environ.get("SINISTER_SANCTUM_ROOT", r"D:\Sinister Sanctum"))
SHARED = SANCTUM_ROOT / "_shared-memory"
HEARTBEAT_DIR = SHARED / "heartbeats"
USAGE_LOG_PATH = SHARED / "looper-usage-log.jsonl"
LOOPER_TELEMETRY = SHARED / "looper-unified.jsonl"


def _now() -> float:
    return time.time()


def _utc_iso(ts: Optional[float] = None) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts if ts is not None else _now()))


def _emit_telemetry(kind: str, **fields) -> None:
    """Append a structured event to looper-unified.jsonl (best-effort)."""
    try:
        LOOPER_TELEMETRY.parent.mkdir(parents=True, exist_ok=True)
        row = {"ts_utc": _utc_iso(), "kind": kind, **fields}
        with LOOPER_TELEMETRY.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# 1. AdaptiveScheduler  (jcode scheduler.rs:188-274 parity)
# ---------------------------------------------------------------------------

@dataclass
class AdaptiveScheduler:
    """Compute next-tick interval from remaining budget vs cycles available.

    Mirrors jcode `scheduler.rs:188-247` (calculate_interval) + 260-267
    (on_rate_limit_hit / on_successful_cycle).

    Field defaults reflect Sanctum cadence: 5-min floor (cache-warm), 60-min cap.
    """
    min_interval_s: float = 300.0
    max_interval_s: float = 3600.0
    base_interval_s: float = 900.0  # 15 min default; matches loop_open_agents schtask
    user_reserve_fraction: float = 0.8
    _backoff_multiplier: float = 1.0
    _backoff_cap: float = 64.0

    def calculate_interval(
        self,
        window_remaining_s: Optional[float] = None,
        cycles_available: Optional[int] = None,
    ) -> float:
        """Return next sleep duration in seconds.

        If window+cycles supplied, distribute remaining budget evenly.
        Else use base_interval. Apply rate-limit backoff multiplier last.
        Clamped to [min_interval_s, max_interval_s].
        """
        if window_remaining_s is not None and cycles_available and cycles_available > 0:
            raw = window_remaining_s / cycles_available
        else:
            raw = self.base_interval_s
        scaled = raw * self._backoff_multiplier
        return max(self.min_interval_s, min(self.max_interval_s, scaled))

    def on_rate_limit_hit(self) -> None:
        """Double the backoff multiplier (capped at 64x). jcode scheduler.rs:260."""
        self._backoff_multiplier = min(self._backoff_cap, self._backoff_multiplier * 2.0)
        _emit_telemetry("rate-limit-backoff", multiplier=self._backoff_multiplier)

    def on_successful_cycle(self) -> None:
        """Reset backoff multiplier to 1x. jcode scheduler.rs:267."""
        if self._backoff_multiplier != 1.0:
            _emit_telemetry("backoff-reset", from_multiplier=self._backoff_multiplier)
        self._backoff_multiplier = 1.0

    @property
    def backoff_multiplier(self) -> float:
        return self._backoff_multiplier


# ---------------------------------------------------------------------------
# 2. BackoffHelper  (openhuman useDaemonLifecycle.ts:60-62 pattern)
# ---------------------------------------------------------------------------

@dataclass
class BackoffHelper:
    """Jittered exponential backoff. attempt is 1-indexed."""
    base_s: float = 30.0
    max_s: float = 3600.0
    jitter_fraction: float = 0.2  # +/- 20%

    def delay_for_attempt(self, attempt: int) -> float:
        if attempt <= 0:
            return 0.0
        raw = self.base_s * (2 ** (attempt - 1))
        capped = min(self.max_s, raw)
        if self.jitter_fraction > 0:
            jitter = capped * self.jitter_fraction
            capped += random.uniform(-jitter, jitter)
        return max(0.0, capped)

    def should_retry(self, last_attempt_ts: float, attempt: int, now: Optional[float] = None) -> bool:
        if attempt <= 0:
            return True
        elapsed = (now if now is not None else _now()) - last_attempt_ts
        return elapsed >= self.delay_for_attempt(attempt)


# ---------------------------------------------------------------------------
# 3. UsageLog  (jcode scheduler.rs:18-136 — 24h rolling JSONL window)
# ---------------------------------------------------------------------------

@dataclass
class UsageLog:
    """Append-only JSONL of per-cycle resource use; prunes records older than 24h.

    Used by AdaptiveScheduler.calculate_interval to estimate cycles_available
    given a wall-clock budget.
    """
    path: Path = field(default_factory=lambda: USAGE_LOG_PATH)
    prune_age_hours: int = 24

    def record(self, lane: str, cycle: int, tokens_in: int = 0, tokens_out: int = 0,
               duration_s: float = 0.0, status: str = "ok") -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        row = {
            "ts_utc": _utc_iso(),
            "ts_epoch": _now(),
            "lane": lane,
            "cycle": cycle,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "duration_s": round(duration_s, 3),
            "status": status,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")

    def recent(self, since_hours: float = 24.0) -> list[dict]:
        if not self.path.exists():
            return []
        cutoff = _now() - since_hours * 3600.0
        out: list[dict] = []
        try:
            for line in self.path.read_text(encoding="utf-8", errors="ignore").splitlines():
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except Exception:
                    continue
                if row.get("ts_epoch", 0) >= cutoff:
                    out.append(row)
        except Exception:
            return []
        return out

    def prune(self) -> int:
        """Rewrite log keeping only rows newer than prune_age_hours. Returns kept count."""
        rows = self.recent(since_hours=self.prune_age_hours)
        if not rows:
            return 0
        tmp = self.path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        tmp.replace(self.path)
        return len(rows)

    def avg_cycle_duration_s(self, since_hours: float = 24.0) -> float:
        rows = self.recent(since_hours=since_hours)
        if not rows:
            return 0.0
        durations = [r.get("duration_s", 0.0) for r in rows if r.get("status") == "ok"]
        if not durations:
            return 0.0
        return sum(durations) / len(durations)


# ---------------------------------------------------------------------------
# 4. HeartbeatProbe  (unifies 3 readers in current stack)
# ---------------------------------------------------------------------------

@dataclass
class HeartbeatProbe:
    """Single source of truth for 'is agent <slug> alive?'.

    Default fresh window: 30 minutes. Stale beyond that = considered offline.
    Replaces the 8-min vs 30-min vs 60-min divergence across our current files.
    """
    heartbeat_dir: Path = field(default_factory=lambda: HEARTBEAT_DIR)
    fresh_seconds: int = 30 * 60

    def heartbeat_path(self, slug: str) -> Path:
        return self.heartbeat_dir / f"{slug}.json"

    def age_seconds(self, slug: str) -> Optional[float]:
        """Returns seconds since last heartbeat file mtime; None if missing."""
        p = self.heartbeat_path(slug)
        if not p.exists():
            return None
        try:
            return _now() - p.stat().st_mtime
        except Exception:
            return None

    def is_alive(self, slug: str) -> bool:
        age = self.age_seconds(slug)
        return age is not None and age <= self.fresh_seconds

    def list_live(self) -> list[tuple[str, float]]:
        """Returns [(slug, age_seconds)] for every fresh heartbeat."""
        if not self.heartbeat_dir.exists():
            return []
        out: list[tuple[str, float]] = []
        for p in self.heartbeat_dir.glob("*.json"):
            try:
                age = _now() - p.stat().st_mtime
            except Exception:
                continue
            if age <= self.fresh_seconds:
                out.append((p.stem, age))
        out.sort(key=lambda x: x[1])
        return out


# ---------------------------------------------------------------------------
# 5. OperatorActive  (read sinister-operator heartbeat; fail-open)
# ---------------------------------------------------------------------------

@dataclass
class OperatorActive:
    """Is the human operator currently in a session?

    Fail-open: if marker file is missing, assume active (don't accidentally
    pause loops on first-run before instrumentation is wired up).
    """
    marker_slug: str = "sinister-operator"
    idle_floor_seconds: int = 60 * 60
    _probe: HeartbeatProbe = field(default_factory=HeartbeatProbe)

    def is_active(self) -> bool:
        age = self._probe.age_seconds(self.marker_slug)
        if age is None:
            return True  # fail-open
        return age <= self.idle_floor_seconds

    def is_idle(self) -> bool:
        return not self.is_active()


# ---------------------------------------------------------------------------
# 6. LoopGuard  (jcode runner.rs:917-959 — forced-end after K missed end_cycle)
# ---------------------------------------------------------------------------

class LoopBreak(Exception):
    """Raised by LoopGuard when stop-condition fires."""


@dataclass
class LoopGuard:
    """Bounded loop iterator with forced-end on stall.

    Usage:
        guard = LoopGuard(max_iters=10, max_seconds=600, max_progressless_iters=2)
        with guard as g:
            for i in g:
                ... work ...
                if progressed: g.mark_progress()
    """
    max_iters: int = 10
    max_seconds: float = 600.0
    max_progressless_iters: int = 2
    on_break_emit: bool = True
    _iter: int = 0
    _started: float = 0.0
    _progressless_streak: int = 0
    _break_reason: str = ""

    def __enter__(self) -> "LoopGuard":
        self._started = _now()
        self._iter = 0
        self._progressless_streak = 0
        self._break_reason = ""
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if self.on_break_emit:
            _emit_telemetry(
                "loop-guard-exit",
                iters=self._iter,
                duration_s=round(_now() - self._started, 3),
                break_reason=self._break_reason or ("exception" if exc else "exhausted"),
            )
        return exc_type is LoopBreak  # swallow LoopBreak only

    def __iter__(self) -> Iterator[int]:
        return self

    def __next__(self) -> int:
        if self._iter >= self.max_iters:
            self._break_reason = "max_iters"
            raise StopIteration
        if _now() - self._started >= self.max_seconds:
            self._break_reason = "max_seconds"
            raise StopIteration
        if self._progressless_streak >= self.max_progressless_iters:
            self._break_reason = "progressless"
            raise StopIteration
        self._iter += 1
        return self._iter

    def mark_progress(self) -> None:
        self._progressless_streak = 0

    def mark_no_progress(self) -> None:
        self._progressless_streak += 1

    def force_break(self, reason: str) -> None:
        self._break_reason = reason or "manual"
        raise LoopBreak(reason)


# ---------------------------------------------------------------------------
# 7. SwarmFanout  (light wrapper over automations/sinister_swarm.py)
# ---------------------------------------------------------------------------

def swarm_fanout(slices: list[dict], slug_prefix: str = "loop", timeout_s: int = 600) -> list[dict]:
    """Spawn N parallel slices via sinister_swarm.py and aggregate results.

    Importable wrapper so callers don't have to reach for subprocess directly.
    Each slice dict: {id, prompt, owned_paths, lane}.
    """
    import subprocess
    import tempfile
    swarm_py = Path(__file__).resolve().parent / "sinister_swarm.py"
    if not swarm_py.exists():
        _emit_telemetry("swarm-fanout-missing", py=str(swarm_py))
        return [{"error": "sinister_swarm.py not found", "slug_prefix": slug_prefix}]
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", encoding="utf-8", delete=False
    ) as tf:
        json.dump(slices, tf)
        slices_path = tf.name
    try:
        cmd = [
            sys.executable, str(swarm_py), "fanout",
            "--slug-prefix", slug_prefix,
            "--slices-file", slices_path,
            "--timeout-s", str(timeout_s),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s + 30)
        if proc.returncode != 0:
            _emit_telemetry("swarm-fanout-failed", rc=proc.returncode, stderr=proc.stderr[:500])
            return [{"error": proc.stderr or proc.stdout, "rc": proc.returncode}]
        try:
            return json.loads(proc.stdout)
        except Exception:
            return [{"raw": proc.stdout}]
    finally:
        try:
            os.unlink(slices_path)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cmd_smoke() -> int:
    """Self-test every primitive. Exit 0 if all pass."""
    failures: list[str] = []

    # AdaptiveScheduler
    sched = AdaptiveScheduler(min_interval_s=10, max_interval_s=100, base_interval_s=30)
    assert sched.calculate_interval() == 30, "default interval mismatch"
    sched.on_rate_limit_hit()
    iv = sched.calculate_interval()
    if iv != 60:
        failures.append(f"backoff 2x expected 60, got {iv}")
    sched.on_successful_cycle()
    if sched.calculate_interval() != 30:
        failures.append("reset after success failed")
    iv2 = sched.calculate_interval(window_remaining_s=300, cycles_available=10)
    if iv2 != 30:
        failures.append(f"window/cycles expected 30, got {iv2}")

    # Clamp test
    sched_clamp = AdaptiveScheduler(min_interval_s=5, max_interval_s=10, base_interval_s=20)
    if sched_clamp.calculate_interval() != 10:
        failures.append("max-clamp failed")

    # BackoffHelper
    bh = BackoffHelper(base_s=10.0, max_s=1000.0, jitter_fraction=0.0)
    if bh.delay_for_attempt(1) != 10.0:
        failures.append("backoff attempt=1 expected 10")
    if bh.delay_for_attempt(3) != 40.0:
        failures.append("backoff attempt=3 expected 40")
    if bh.delay_for_attempt(20) > 1000.0:
        failures.append("backoff cap failed")

    # UsageLog (use a temp path)
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tmp_log = Path(td) / "u.jsonl"
        u = UsageLog(path=tmp_log)
        u.record("test-lane", 1, tokens_in=100, tokens_out=50, duration_s=1.5)
        u.record("test-lane", 2, tokens_in=200, tokens_out=80, duration_s=2.0)
        rows = u.recent(since_hours=1)
        if len(rows) != 2:
            failures.append(f"usage log recent expected 2, got {len(rows)}")
        avg = u.avg_cycle_duration_s()
        if abs(avg - 1.75) > 0.01:
            failures.append(f"avg duration expected 1.75, got {avg}")
        kept = u.prune()
        if kept != 2:
            failures.append(f"prune expected to keep 2, kept {kept}")

    # HeartbeatProbe (use temp dir)
    with tempfile.TemporaryDirectory() as td:
        hb_dir = Path(td)
        hb = HeartbeatProbe(heartbeat_dir=hb_dir, fresh_seconds=60)
        if hb.is_alive("ghost"):
            failures.append("ghost slug should not be alive")
        (hb_dir / "live.json").write_text('{"ok":1}', encoding="utf-8")
        if not hb.is_alive("live"):
            failures.append("just-written heartbeat should be alive")
        live = hb.list_live()
        if not any(slug == "live" for slug, _ in live):
            failures.append("list_live missed 'live'")

    # OperatorActive (fail-open when marker missing)
    with tempfile.TemporaryDirectory() as td:
        hb_dir = Path(td)
        oa = OperatorActive(_probe=HeartbeatProbe(heartbeat_dir=hb_dir))
        if not oa.is_active():
            failures.append("operator should fail-open to active")

    # LoopGuard
    seen: list[int] = []
    try:
        with LoopGuard(max_iters=5, max_seconds=10, max_progressless_iters=2) as g:
            for i in g:
                seen.append(i)
                g.mark_no_progress()
    except Exception as e:  # noqa: BLE001
        failures.append(f"LoopGuard raised unexpectedly: {e}")
    if seen != [1, 2]:
        failures.append(f"LoopGuard progressless expected [1,2], got {seen}")

    # LoopGuard with progress markers should hit max_iters
    seen2: list[int] = []
    with LoopGuard(max_iters=3, max_seconds=10, max_progressless_iters=99) as g:
        for i in g:
            seen2.append(i)
            g.mark_progress()
    if seen2 != [1, 2, 3]:
        failures.append(f"LoopGuard max_iters expected [1,2,3], got {seen2}")

    # LoopGuard force_break
    seen3: list[int] = []
    with LoopGuard(max_iters=10, max_seconds=10) as g:
        for i in g:
            seen3.append(i)
            if i == 2:
                g.force_break("test")
    if seen3 != [1, 2]:
        failures.append(f"LoopGuard force_break expected [1,2], got {seen3}")

    if failures:
        print("SMOKE FAIL:")
        for f in failures:
            print("  -", f)
        return 1
    print("SMOKE OK: AdaptiveScheduler + BackoffHelper + UsageLog + HeartbeatProbe + "
          "OperatorActive + LoopGuard all green.")
    return 0


def _cmd_probe(slug: str) -> int:
    hb = HeartbeatProbe()
    age = hb.age_seconds(slug)
    if age is None:
        print(f"{slug}: NO HEARTBEAT FILE at {hb.heartbeat_path(slug)}")
        return 1
    alive = hb.is_alive(slug)
    print(f"{slug}: age={age:.1f}s alive={alive} (fresh window {hb.fresh_seconds}s)")
    return 0


def _cmd_operator() -> int:
    oa = OperatorActive()
    age = oa._probe.age_seconds(oa.marker_slug)
    if age is None:
        print(f"operator marker missing -> fail-open ACTIVE (would be at "
              f"{oa._probe.heartbeat_path(oa.marker_slug)})")
        return 0
    print(f"operator: age={age:.1f}s active={oa.is_active()} "
          f"(idle floor {oa.idle_floor_seconds}s)")
    return 0


def _cmd_demo() -> int:
    """Run a 5-tick adaptive loop printing timing info (no real work)."""
    sched = AdaptiveScheduler(min_interval_s=1, max_interval_s=10, base_interval_s=2)
    print("demo: 5 ticks of adaptive scheduler (no sleeps; printing computed intervals)")
    for i in range(1, 6):
        iv = sched.calculate_interval()
        print(f"  tick {i}: interval={iv}s  multiplier={sched.backoff_multiplier}")
        if i == 2:
            print("  -> simulating rate-limit hit")
            sched.on_rate_limit_hit()
        if i == 4:
            print("  -> simulating successful cycle")
            sched.on_successful_cycle()
    return 0


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__.split("\n\n", 1)[0])
        print("\ncommands: smoke | probe <slug> | operator | demo")
        return 2
    cmd = argv[1]
    if cmd == "smoke":
        return _cmd_smoke()
    if cmd == "probe":
        if len(argv) < 3:
            print("usage: probe <slug>")
            return 2
        return _cmd_probe(argv[2])
    if cmd == "operator":
        return _cmd_operator()
    if cmd == "demo":
        return _cmd_demo()
    print(f"unknown command: {cmd}")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
