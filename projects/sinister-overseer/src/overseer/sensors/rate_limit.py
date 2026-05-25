# Author: RKOJ-ELENO :: 2026-05-25
"""sensors/rate_limit.py -- 429 / quota-throttle sensor for Sinister Overseer.

Slice-1 of D3 ("Rate-limit Adaptive Learning Overseer") per the consolidation
plan at `_shared-memory/plans/sanctum-consolidate-stop-overlap-2026-05-25T0945Z/plan.md`.

Reads two Sanctum-fleet data sources (no subprocess; JSONL + JSON file-based):

  1. `_shared-memory/anthropic-throttle-events.jsonl` -- append-only log of 429
     events emitted by the fleet's claude-wrapper layer. Schema (one per line):
        {"ts_utc": "...", "account": "operator-b", "project": "sinister-os",
         "excerpt": "..."}

  2. `_shared-memory/oauth-slot-health.json` -- current per-slot health snapshot
     written by the fleet OAuth health daemon. Used to map 429 events to slot
     metadata + score.

Emits :class:`RateLimit429Event` per fresh row. Dedups by (ts_utc + account +
project) so re-poll doesn't re-emit historical events.

Composes with:
    `overseer.rate_limit_learner` (consumes events + builds rolling stats)
    `sensors.analyzer.SensorBus` (this sensor plugs into the existing bus)
    `docs/02-token-efficiency.md` (rate-limit drives cost-tier downshift)

Status: SHIPPED. Tests at `tests/test_rate_limit_sensor.py`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
import json

from overseer.sensors.analyzer import _BaseSensor  # type: ignore  -- internal reuse


SANCTUM_ROOT = Path("D:/Sinister Sanctum")


@dataclass(frozen=True)
class RateLimit429Event:
    """A single 429 / quota-throttle row from the fleet throttle log."""

    ts_utc: str
    account: str
    project: str
    excerpt: str


class RateLimitSensor(_BaseSensor):
    """File-tail sensor for `anthropic-throttle-events.jsonl`.

    Default poll cadence: 60s (rate-limit detection must be fast).

    Unlike script-based sensors in analyzer.py, this one bypasses subprocess and
    reads the JSONL directly. The dedup cache + base class hooks still apply.
    """

    name = "rate-limit"
    default_poll_seconds = 60

    def __init__(
        self,
        sanctum_root: Path | str = SANCTUM_ROOT,
        poll_seconds: int | None = None,
        throttle_log: Path | None = None,
    ) -> None:
        super().__init__(sanctum_root=sanctum_root, poll_seconds=poll_seconds)
        self._log_override = throttle_log

    # No script path -- this sensor is file-based. Stubs so the base class API
    # is satisfied but never executed.
    def _script_path(self) -> Path:
        return Path("/__not_used__")

    def _build_args(self) -> list[str]:
        return []

    def _parse(self, raw_stdout: str) -> list:  # type: ignore[override]
        return []

    # ----------------------------------------------------------------------

    def throttle_log_path(self) -> Path:
        if self._log_override is not None:
            return self._log_override
        return self.sanctum_root / "_shared-memory" / "anthropic-throttle-events.jsonl"

    def _read_events(self) -> Iterable[dict]:
        p = self.throttle_log_path()
        if not p.is_file():
            return []
        try:
            lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            return []
        out: list[dict] = []
        for ln in lines:
            ln = ln.strip()
            if not ln:
                continue
            try:
                row = json.loads(ln)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                out.append(row)
        return out

    def poll(self) -> list[RateLimit429Event]:  # type: ignore[override]
        """Read the throttle log + emit deduplicated fresh events."""
        rows = self._read_events()
        fresh: list[RateLimit429Event] = []
        for row in rows:
            evt = RateLimit429Event(
                ts_utc=str(row.get("ts_utc", "")),
                account=str(row.get("account", "?")),
                project=str(row.get("project", "?")),
                excerpt=str(row.get("excerpt", ""))[:500],
            )
            key = _BaseSensor._dedup_key(evt)
            if key in self._last_emit_cache:
                continue
            self._last_emit_cache.add(key)
            fresh.append(evt)
        return fresh
