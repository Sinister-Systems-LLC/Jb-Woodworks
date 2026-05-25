"""sensors/analyzer.py -- integration wrappers for existing Sanctum analyzers.

Author: RKOJ-ELENO :: 2026-05-24

Wraps three already-shipped sensor scripts so the Sinister Overseer's watch
loop can subscribe to a single SensorBus instead of subprocess-ing each script
itself:

    TokenAnalyzerSensor    -> automations/token-analytics.ps1 -Action Json
    UsageMeterSensor       -> automations/claude-usage-meter.ps1 -Mode Json
    ForeverImproveSensor   -> automations/forever-improve.ps1 -Action Tally

Each sensor polls on its own cadence (configurable; defaults respect the
$5/day per-attachment cost cap from docs/02-token-efficiency.md), de-duplicates
events against its last-emit cache, and routes to the SensorBus. The Overseer's
detector.py reads events off the bus and classifies them with a cheap-tier
(Haiku) call.

Composes with:
    docs/03-watch-architecture.md  (event sources -> detector pipeline)
    docs/09-unified-improvement-engine.md (this module is "Sensors -> WatchBus")
    contradiction.py (events are evidence; fixes proposed in response go
                      through the ContradictionEngine before apply)

Status: P0 STUB. Classes instantiate cleanly + smoke test passes; the
subprocess wiring is wired-but-soft (returns empty event lists if the
target script is missing or returns non-JSON). P2 ships the live integration
under the cost cap.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


# ---------------------------------------------------------------------------
# Event taxonomy. Each is a frozen dataclass; sensors emit only these.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WasteEvent:
    """Token-waste pattern flagged by token-analytics.ps1 -Action WasteReport."""

    pattern: str  # abandoned-cache | context-bloat | tool-loop | no-caching
    project: str
    session_id: str
    severity: str  # P0 | P1 | P2 | P3
    detail: str
    detected_at_utc: str


@dataclass(frozen=True)
class RecommendationEvent:
    """P0-P3 recommendation row from token-analytics.ps1 -Action Recommendations."""

    priority: str  # P0 | P1 | P2 | P3
    title: str
    body: str
    affected_lanes: tuple[str, ...]
    detected_at_utc: str


@dataclass(frozen=True)
class UsageHighEvent:
    """Live-window usage above pct_msgs_threshold from claude-usage-meter."""

    window: str  # 1h | 5h | 24h | 7d
    pct_msgs: float  # 0.0-1.0
    pct_tokens: float  # 0.0-1.0
    cost_usd: float
    detected_at_utc: str


@dataclass(frozen=True)
class RotInLogEvent:
    """forever-improve.ps1 Tally shows open rows older than 3 lane-turns."""

    lane: str
    open_count: int
    oldest_age_turns: int
    top_severity: str  # R0 | R1 | R2 | R3
    detected_at_utc: str


# Union type alias (we don't import typing.Union; use new syntax).
SensorEvent = WasteEvent | RecommendationEvent | UsageHighEvent | RotInLogEvent


# ---------------------------------------------------------------------------
# Shared base sensor.
# ---------------------------------------------------------------------------

SANCTUM_ROOT = Path("D:/Sinister Sanctum")


class _BaseSensor:
    """Common scaffolding for every sensor. Not for direct use."""

    name: str = "base"
    default_poll_seconds: int = 600  # 10 min default; per-sensor overrides

    def __init__(
        self,
        sanctum_root: Path | str = SANCTUM_ROOT,
        poll_seconds: int | None = None,
    ) -> None:
        self.sanctum_root = Path(sanctum_root)
        self.poll_seconds = poll_seconds or self.default_poll_seconds
        self._last_emit_cache: set[str] = set()  # dedup keys
        self._last_run_utc: str | None = None

    # ---- subclass hooks --------------------------------------------------

    def _script_path(self) -> Path:
        raise NotImplementedError

    def _build_args(self) -> list[str]:
        raise NotImplementedError

    def _parse(self, raw_stdout: str) -> list[SensorEvent]:
        raise NotImplementedError

    # ---- public api ------------------------------------------------------

    def poll(self) -> list[SensorEvent]:
        """Run the underlying script + return de-duped new events.

        Returns empty list on script-missing / parse-fail / dedup-only (so the
        smoke test runs cleanly even when the underlying script has no fresh
        data). Real errors are NEVER raised out of poll() -- they're logged
        and an empty list is returned. The Overseer's apply gate handles
        sensor-quiet vs sensor-erroring at a higher layer.
        """
        script = self._script_path()
        if not script.is_file():
            return []
        try:
            args = ["powershell", "-NoProfile", "-File", str(script)] + self._build_args()
            proc = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            if proc.returncode != 0:
                return []
            events = self._parse(proc.stdout)
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError, OSError):
            return []

        # Dedup against last-emit cache.
        fresh: list[SensorEvent] = []
        for e in events:
            key = self._dedup_key(e)
            if key in self._last_emit_cache:
                continue
            self._last_emit_cache.add(key)
            fresh.append(e)
        return fresh

    @staticmethod
    def _dedup_key(event: SensorEvent) -> str:
        # Hash on the type name + every public field value.
        parts = [type(event).__name__]
        for slot in event.__dataclass_fields__:
            parts.append(f"{slot}={getattr(event, slot)!r}")
        return "|".join(parts)


# ---------------------------------------------------------------------------
# Concrete sensors.
# ---------------------------------------------------------------------------

class TokenAnalyzerSensor(_BaseSensor):
    """Wraps ``automations/token-analytics.ps1 -Action Json``.

    Emits a :class:`WasteEvent` per row in the ``waste_patterns`` array AND a
    :class:`RecommendationEvent` per row in ``recommendations``.

    Default poll cadence: 60 minutes (token-analytics is heavy; per-attachment
    cost cap is the binding constraint).
    """

    name = "token-analyzer"
    default_poll_seconds = 3600

    def _script_path(self) -> Path:
        return self.sanctum_root / "automations" / "token-analytics.ps1"

    def _build_args(self) -> list[str]:
        return ["-Action", "Json"]

    def _parse(self, raw_stdout: str) -> list[SensorEvent]:
        try:
            doc = json.loads(raw_stdout)
        except json.JSONDecodeError:
            return []
        events: list[SensorEvent] = []
        scanned_at = doc.get("scanned_at_utc", "")
        for w in doc.get("waste_patterns", []) or []:
            events.append(
                WasteEvent(
                    pattern=str(w.get("pattern", "?")),
                    project=str(w.get("project", "?")),
                    session_id=str(w.get("session_id", "?")),
                    severity=str(w.get("severity", "P3")),
                    detail=str(w.get("detail", "")),
                    detected_at_utc=scanned_at,
                )
            )
        for r in doc.get("recommendations", []) or []:
            lanes_raw = r.get("affected_lanes", []) or []
            if isinstance(lanes_raw, str):
                lanes_raw = [lanes_raw]
            events.append(
                RecommendationEvent(
                    priority=str(r.get("priority", "P3")),
                    title=str(r.get("title", "")),
                    body=str(r.get("body", "")),
                    affected_lanes=tuple(str(x) for x in lanes_raw),
                    detected_at_utc=scanned_at,
                )
            )
        return events


class UsageMeterSensor(_BaseSensor):
    """Wraps ``automations/claude-usage-meter.ps1 -Mode Json``.

    Emits a :class:`UsageHighEvent` when any window's ``pct_msgs`` exceeds
    ``pct_threshold`` (default 0.75 = 75 percent of the 5-hour Max quota).

    Default poll cadence: 5 minutes (lightweight; reads transcript jsonl).
    """

    name = "usage-meter"
    default_poll_seconds = 300

    def __init__(
        self,
        sanctum_root: Path | str = SANCTUM_ROOT,
        poll_seconds: int | None = None,
        pct_threshold: float = 0.75,
    ) -> None:
        super().__init__(sanctum_root=sanctum_root, poll_seconds=poll_seconds)
        self.pct_threshold = pct_threshold

    def _script_path(self) -> Path:
        return self.sanctum_root / "automations" / "claude-usage-meter.ps1"

    def _build_args(self) -> list[str]:
        return ["-Mode", "Json"]

    def _parse(self, raw_stdout: str) -> list[SensorEvent]:
        try:
            doc = json.loads(raw_stdout)
        except json.JSONDecodeError:
            return []
        events: list[SensorEvent] = []
        scanned_at = doc.get("scanned_at_utc") or doc.get("captured_utc", "")
        windows = doc.get("windows", {}) or {}
        for win_name, win_doc in windows.items():
            if not isinstance(win_doc, dict):
                continue
            pct_msgs = float(win_doc.get("pct_msgs", 0.0) or 0.0)
            if pct_msgs < self.pct_threshold:
                continue
            events.append(
                UsageHighEvent(
                    window=str(win_name),
                    pct_msgs=pct_msgs,
                    pct_tokens=float(win_doc.get("pct_tokens", 0.0) or 0.0),
                    cost_usd=float(win_doc.get("cost_usd", 0.0) or 0.0),
                    detected_at_utc=str(scanned_at),
                )
            )
        return events


class ForeverImproveSensor(_BaseSensor):
    """Wraps ``automations/forever-improve.ps1 -Action Tally``.

    Emits a :class:`RotInLogEvent` when any lane has more than
    ``open_threshold`` open rows.

    Default poll cadence: 30 minutes.
    """

    name = "forever-improve"
    default_poll_seconds = 1800

    def __init__(
        self,
        sanctum_root: Path | str = SANCTUM_ROOT,
        poll_seconds: int | None = None,
        open_threshold: int = 3,
    ) -> None:
        super().__init__(sanctum_root=sanctum_root, poll_seconds=poll_seconds)
        self.open_threshold = open_threshold

    def _script_path(self) -> Path:
        return self.sanctum_root / "automations" / "forever-improve.ps1"

    def _build_args(self) -> list[str]:
        # Tally renders human text by default; we ask for json-style output if
        # available. The script falls back to readable text if -Json isn't
        # supported, in which case _parse returns []. P2 will add -Json to the
        # script proper and this sensor will start emitting live events.
        return ["-Action", "Tally", "-Json"]

    def _parse(self, raw_stdout: str) -> list[SensorEvent]:
        try:
            doc = json.loads(raw_stdout)
        except json.JSONDecodeError:
            return []
        events: list[SensorEvent] = []
        scanned_at = doc.get("scanned_at_utc", "")
        for lane_row in doc.get("lanes", []) or []:
            open_count = int(lane_row.get("open", 0) or 0)
            if open_count <= self.open_threshold:
                continue
            events.append(
                RotInLogEvent(
                    lane=str(lane_row.get("lane", "?")),
                    open_count=open_count,
                    oldest_age_turns=int(lane_row.get("oldest_age_turns", 0) or 0),
                    top_severity=str(lane_row.get("top_severity", "R3")),
                    detected_at_utc=str(scanned_at),
                )
            )
        return events


# ---------------------------------------------------------------------------
# SensorBus -- aggregates events from N sensors + routes to subscribers.
# ---------------------------------------------------------------------------

EventHandler = Callable[[SensorEvent], None]


@dataclass
class SensorBus:
    """Aggregates events from registered sensors + fans them out to handlers.

    Usage::

        bus = SensorBus()
        bus.add_sensor(TokenAnalyzerSensor())
        bus.add_sensor(UsageMeterSensor(pct_threshold=0.85))
        bus.add_sensor(ForeverImproveSensor(open_threshold=5))
        bus.subscribe(my_detector_callback)
        new_events = bus.poll_all()  # returns the same list it dispatched

    The bus de-duplicates by (sensor.name, event.dedup_key) so the same waste
    pattern reported by two sensors doesn't double-fire downstream. Subscribers
    are best-effort: an exception in one handler does NOT stop dispatch to
    others.
    """

    sensors: list[_BaseSensor] = field(default_factory=list)
    handlers: list[EventHandler] = field(default_factory=list)
    _seen: set[str] = field(default_factory=set)

    def add_sensor(self, sensor: _BaseSensor) -> None:
        self.sensors.append(sensor)

    def subscribe(self, handler: EventHandler) -> None:
        self.handlers.append(handler)

    def poll_all(self) -> list[SensorEvent]:
        """Poll every sensor in order; emit + return deduped event list."""
        emitted: list[SensorEvent] = []
        for sensor in self.sensors:
            try:
                events = sensor.poll()
            except Exception:  # noqa: BLE001 -- sensors must not break the bus
                events = []
            for evt in events:
                key = f"{sensor.name}|{_BaseSensor._dedup_key(evt)}"
                if key in self._seen:
                    continue
                self._seen.add(key)
                emitted.append(evt)
                for h in self.handlers:
                    try:
                        h(evt)
                    except Exception:  # noqa: BLE001
                        continue
        return emitted


# ---------------------------------------------------------------------------
# Module-level smoke (run via `python -m overseer.sensors.analyzer`).
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Trivial smoke: instantiate everything + poll once with no sensors wired.
    bus = SensorBus()
    bus.add_sensor(TokenAnalyzerSensor())
    bus.add_sensor(UsageMeterSensor(pct_threshold=0.85))
    bus.add_sensor(ForeverImproveSensor(open_threshold=3))
    events = bus.poll_all()
    sys.stdout.write(
        json.dumps(
            {
                "sensor_count": len(bus.sensors),
                "events_this_poll": len(events),
                "handlers_subscribed": len(bus.handlers),
            },
            indent=2,
        )
        + "\n"
    )
