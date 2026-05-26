# Author: RKOJ-ELENO :: 2026-05-25
"""Sinister Memory :: wait-for-heartbeat.

Poll for a target slug's heartbeat file appearance + freshness within a
timeout window. Composes with `automations/start-sinister-session.ps1` so
agents calling spawn can validate the spawn actually initialized (not just
opened a window).

Iter-27 contradict-driven: my iter-5 claim "spawned sinister-mcp PID 46968"
was misleading -- the window opened but the agent never wrote a heartbeat.
14 hours later still NONE. Any delegate that depends on the spawned agent
being ready needs to wait + verify.

Public API:
  wait_for_heartbeat(slug, root, timeout_s=30, poll_interval_s=2,
                     freshness_window_s=120) -> dict
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path


def _read_expected_interval(hb_path: Path) -> "float | None":
    """Iter-40: read `expected_interval_s` from heartbeat JSON content if present.
    Lets per-lane heartbeats declare their own cadence -- e.g. a 10-min-cadence
    lane that would always look stale at the default 120s freshness window can
    set `expected_interval_s: 900` (15 min) in its heartbeat JSON and waiters
    using --from-heartbeat will respect that.
    """
    import json
    try:
        with hb_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        v = data.get("expected_interval_s")
        if isinstance(v, (int, float)) and v > 0:
            return float(v)
    except (OSError, json.JSONDecodeError, ValueError):
        pass
    return None


def wait_for_heartbeat(
    slug: str,
    root: Path,
    timeout_s: float = 30.0,
    poll_interval_s: float = 2.0,
    freshness_window_s: float = 120.0,
    from_heartbeat: bool = False,
    grace_multiplier: float = 3.0,
) -> dict:
    """Poll for heartbeat file. Returns {ok, status, elapsed_s, hb_path, hb_mtime_iso}.

    `ok` is True iff the heartbeat file exists AND its mtime is within
    `freshness_window_s` seconds (default 2 minutes) by the end of the poll.

    If `from_heartbeat=True` AND the file exists AND contains a numeric
    `expected_interval_s` field, the freshness window is TAKEN FROM that field
    multiplied by `grace_multiplier` (default 3.0 = allow up to 3 missed
    heartbeats before declaring stale; configurable per call as of iter-42).
    iter-40 shipped from_heartbeat; iter-42 makes the grace multiplier
    explicit + configurable (was hardcoded 3.0).

    `status` is one of:
      "fresh"          : file exists + mtime fresh -> ok=True
      "stale"          : file exists but mtime too old -> ok=False
      "missing-timeout": file never appeared within timeout -> ok=False
      "invalid-slug"   : slug doesn't pass safety check -> ok=False
    """
    # Slug safety: matches `_validate_slug` from auto_save.py conventions
    if not slug or not all(c.isalnum() or c in "-_" for c in slug):
        return {
            "ok": False, "status": "invalid-slug", "slug": slug,
            "elapsed_s": 0.0, "freshness_used_s": round(freshness_window_s, 1),
        }

    # Iter-43 contradict-fix for iter-42: reject negative grace_multiplier
    # before any work. Iter-42 accepted negative values + produced negative
    # freshness_used_s (e.g. -10000.0 with gm=-100) which was nonsense.
    if grace_multiplier < 0:
        return {
            "ok": False, "status": "invalid-grace-multiplier", "slug": slug,
            "elapsed_s": 0.0, "freshness_used_s": round(freshness_window_s, 1),
            "grace_multiplier": grace_multiplier,
        }

    hb_path = Path(root) / "_shared-memory" / "heartbeats" / f"{slug}.json"
    started = time.time()
    deadline = started + timeout_s
    effective_freshness = freshness_window_s

    while time.time() < deadline:
        if hb_path.exists():
            # Iter-40: read per-slug expected_interval_s if --from-heartbeat
            if from_heartbeat:
                interval = _read_expected_interval(hb_path)
                if interval is not None:
                    effective_freshness = interval * grace_multiplier
            try:
                mtime = hb_path.stat().st_mtime
            except OSError:
                mtime = 0.0
            age = time.time() - mtime
            if age <= effective_freshness:
                return {
                    "ok": True,
                    "status": "fresh",
                    "slug": slug,
                    "elapsed_s": round(time.time() - started, 2),
                    "hb_path": str(hb_path),
                    "hb_mtime_iso": datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "age_s": round(age, 1),
                    "freshness_used_s": round(effective_freshness, 1),
                }
            # File exists but stale: don't loop forever -- one more poll then bail
            # (caller may want to know about a STALE heartbeat, distinct from missing)
        time.sleep(poll_interval_s)

    # Final check at deadline
    if hb_path.exists():
        if from_heartbeat:
            interval = _read_expected_interval(hb_path)
            if interval is not None:
                effective_freshness = interval * grace_multiplier
        try:
            mtime = hb_path.stat().st_mtime
        except OSError:
            mtime = 0.0
        age = time.time() - mtime
        return {
            "ok": age <= effective_freshness,
            "status": "fresh" if age <= effective_freshness else "stale",
            "slug": slug,
            "elapsed_s": round(time.time() - started, 2),
            "hb_path": str(hb_path),
            "hb_mtime_iso": datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "age_s": round(age, 1),
            "freshness_used_s": round(effective_freshness, 1),
        }

    return {
        "ok": False,
        "status": "missing-timeout",
        "slug": slug,
        "elapsed_s": round(time.time() - started, 2),
        "hb_path": str(hb_path),
        "timeout_s": timeout_s,
        "freshness_used_s": round(effective_freshness, 1),
    }
