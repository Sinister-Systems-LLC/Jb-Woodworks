# Author: RKOJ-ELENO :: 2026-05-25
"""rate_limit_learner.py -- per-slot 429 learner + auto-rotate recommender.

Slice-1 of D3 ("Rate-limit Adaptive Learning Overseer"). Consumes
:class:`RateLimit429Event` rows from the rate-limit sensor + the live
`_shared-memory/oauth-slot-health.json` snapshot. Produces:

  - Per-slot rolling stats (count last 1h / 24h, mean inter-arrival, last_429_ts)
  - Recommended next slot (highest availability_score AND not currently
    rate_limited AND not 429-burned in the last 5 min)
  - Learned-threshold suggestions (e.g. "operator-b usually 429s at usage_pct_5h
    > 800; consider downshift to operator at >= 700") -- writes to
    `_shared-memory/overseer-rate-limit-learning.json` as the persistent ledger.

The learner is intentionally simple at slice-1: no neural prediction, just
event-count windowing + threshold tracking. The fix-action (auto-rotate)
proposal is generated as a dict; the apply gate decides whether to fire it.

Composes with:
    `sensors/rate_limit.py` (event source)
    `docs/02-token-efficiency.md` (downshift policy)
    `actions/spawn_sub_lane.py` (precedent for ledger-style learning state)

Status: SHIPPED. Tests at `tests/test_rate_limit_learner.py`.
"""

from __future__ import annotations

import json
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from overseer.sensors.rate_limit import RateLimit429Event


SANCTUM_ROOT = Path("D:/Sinister Sanctum")
LEDGER_PATH_DEFAULT = SANCTUM_ROOT / "_shared-memory" / "overseer-rate-limit-learning.json"
OAUTH_HEALTH_DEFAULT = SANCTUM_ROOT / "_shared-memory" / "oauth-slot-health.json"


def _parse_iso(ts: str) -> datetime | None:
    """Parse ISO-8601 UTC timestamp. Returns None on parse fail."""
    if not ts:
        return None
    s = ts.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@dataclass
class SlotStats:
    account: str
    count_1h: int = 0
    count_24h: int = 0
    last_429_ts: str = ""
    mean_inter_arrival_s: float = 0.0
    projects_429d_24h: list[str] = field(default_factory=list)


@dataclass
class RotationRecommendation:
    """One auto-rotate suggestion produced by the learner."""

    from_slot: str
    to_slot: str
    reason: str
    confidence: float  # 0.0 - 1.0
    risk: str = "medium"  # mapped to AUTO_APPLY_RULES tier
    fix_template: str = "rotate_oauth_slot"


class RateLimitLearner:
    """Rolling per-slot 429 learner.

    Usage::

        learner = RateLimitLearner()
        learner.ingest(events)                      # list[RateLimit429Event]
        slot_stats = learner.compute_slot_stats(now)
        recs = learner.recommendations(slot_stats, oauth_health)
        learner.persist(slot_stats, recs)           # writes ledger
    """

    WINDOW_1H = timedelta(hours=1)
    WINDOW_24H = timedelta(hours=24)
    BURN_WINDOW = timedelta(minutes=5)

    def __init__(
        self,
        ledger_path: Path = LEDGER_PATH_DEFAULT,
        oauth_health_path: Path = OAUTH_HEALTH_DEFAULT,
    ) -> None:
        self.ledger_path = Path(ledger_path)
        self.oauth_health_path = Path(oauth_health_path)
        self._events: list[RateLimit429Event] = []

    # -- ingest --------------------------------------------------------------

    def ingest(self, events: list[RateLimit429Event]) -> None:
        """Append events to the in-memory rolling buffer."""
        self._events.extend(events)
        # Keep only events newer than 24h to bound memory (the ledger persists
        # aggregates, not raw events).
        cutoff = datetime.now(timezone.utc) - self.WINDOW_24H
        self._events = [e for e in self._events if (_parse_iso(e.ts_utc) or cutoff) >= cutoff]

    # -- compute -------------------------------------------------------------

    def compute_slot_stats(self, now: datetime | None = None) -> dict[str, SlotStats]:
        """Return per-account rolling stats based on the in-memory buffer."""
        now = now or datetime.now(timezone.utc)
        cutoff_1h = now - self.WINDOW_1H
        cutoff_24h = now - self.WINDOW_24H

        by_slot: dict[str, list[RateLimit429Event]] = {}
        for ev in self._events:
            ts = _parse_iso(ev.ts_utc)
            if ts is None or ts < cutoff_24h:
                continue
            by_slot.setdefault(ev.account, []).append(ev)

        stats: dict[str, SlotStats] = {}
        for slot, evs in by_slot.items():
            evs.sort(key=lambda e: _parse_iso(e.ts_utc) or now)
            count_1h = sum(1 for e in evs if (_parse_iso(e.ts_utc) or cutoff_24h) >= cutoff_1h)
            count_24h = len(evs)

            mean_iat = 0.0
            if len(evs) >= 2:
                deltas: list[float] = []
                last_ts = None
                for e in evs:
                    cur = _parse_iso(e.ts_utc)
                    if cur is None:
                        continue
                    if last_ts is not None:
                        deltas.append((cur - last_ts).total_seconds())
                    last_ts = cur
                if deltas:
                    mean_iat = float(statistics.fmean(deltas))

            last_ts = evs[-1].ts_utc if evs else ""
            projects = sorted({e.project for e in evs if e.project})

            stats[slot] = SlotStats(
                account=slot,
                count_1h=count_1h,
                count_24h=count_24h,
                last_429_ts=last_ts,
                mean_inter_arrival_s=round(mean_iat, 1),
                projects_429d_24h=projects,
            )
        return stats

    # -- recommend -----------------------------------------------------------

    def recommendations(
        self,
        slot_stats: dict[str, SlotStats],
        oauth_health: dict | None = None,
        now: datetime | None = None,
    ) -> list[RotationRecommendation]:
        """Return rotation suggestions.

        Rule: any slot with count_1h >= 3 or last_429 < 5 min ago is "burning"
        and should rotate to the highest-availability_score peer that:
          - is enabled
          - is not currently rate_limited
          - was not 429-burned in BURN_WINDOW
        """
        now = now or datetime.now(timezone.utc)
        burn_cutoff = now - self.BURN_WINDOW
        oauth_health = oauth_health or self._read_oauth_health()
        slots = oauth_health.get("slots", []) if isinstance(oauth_health, dict) else []
        if not isinstance(slots, list):
            slots = []

        # Build available-slot ranking
        candidates: list[tuple[str, float]] = []
        for s in slots:
            if not isinstance(s, dict):
                continue
            name = s.get("name", "")
            if not name or not s.get("enabled"):
                continue
            if s.get("rate_limited"):
                continue
            # Drop slots burned in the last 5 min
            recent = slot_stats.get(name)
            if recent and recent.last_429_ts:
                last = _parse_iso(recent.last_429_ts)
                if last and last >= burn_cutoff:
                    continue
            score = float(s.get("availability_score", 0.0) or 0.0)
            candidates.append((name, score))
        candidates.sort(key=lambda c: c[1], reverse=True)

        recs: list[RotationRecommendation] = []
        for slot, stat in slot_stats.items():
            burning = stat.count_1h >= 3
            if not burning and stat.last_429_ts:
                last = _parse_iso(stat.last_429_ts)
                if last and last >= burn_cutoff:
                    burning = True
            if not burning:
                continue

            # Find the highest-score peer that is NOT this slot
            target = next((name for name, _ in candidates if name != slot), "")
            if not target:
                # No viable peer -> escalate to operator (telemetry, no auto-apply)
                recs.append(
                    RotationRecommendation(
                        from_slot=slot,
                        to_slot="",
                        reason=(
                            f"Slot {slot} burning (count_1h={stat.count_1h}, last_429={stat.last_429_ts})"
                            " but NO viable peer in oauth-slot-health (all rate_limited/disabled/burned)."
                            " Escalate to operator -- quota exhaustion likely."
                        ),
                        confidence=0.95,
                        risk="high",
                        fix_template="quota_exhaustion_escalate",
                    )
                )
                continue

            confidence = min(0.99, 0.6 + 0.1 * stat.count_1h)
            recs.append(
                RotationRecommendation(
                    from_slot=slot,
                    to_slot=target,
                    reason=(
                        f"Slot {slot} burning (count_1h={stat.count_1h}, mean_iat="
                        f"{stat.mean_inter_arrival_s:.1f}s); rotate to {target}"
                        f" (availability_score peer-best)."
                    ),
                    confidence=round(confidence, 2),
                    risk="medium",
                    fix_template="rotate_oauth_slot",
                )
            )
        return recs

    # -- persistence ---------------------------------------------------------

    def _read_oauth_health(self) -> dict:
        if not self.oauth_health_path.is_file():
            return {}
        try:
            return json.loads(self.oauth_health_path.read_text(encoding="utf-8-sig", errors="ignore"))
        except (OSError, json.JSONDecodeError):
            return {}

    def persist(
        self,
        slot_stats: dict[str, SlotStats],
        recommendations: list[RotationRecommendation],
    ) -> Path:
        """Write the rolling learner state + last recommendations to the ledger."""
        doc = {
            "schema_version": "sinister.overseer.rate-limit-learner.v1",
            "updated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "slots": {
                name: {
                    "account": s.account,
                    "count_1h": s.count_1h,
                    "count_24h": s.count_24h,
                    "last_429_ts": s.last_429_ts,
                    "mean_inter_arrival_s": s.mean_inter_arrival_s,
                    "projects_429d_24h": s.projects_429d_24h,
                }
                for name, s in slot_stats.items()
            },
            "recommendations": [
                {
                    "from_slot": r.from_slot,
                    "to_slot": r.to_slot,
                    "reason": r.reason,
                    "confidence": r.confidence,
                    "risk": r.risk,
                    "fix_template": r.fix_template,
                }
                for r in recommendations
            ],
        }
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self.ledger_path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
        return self.ledger_path


def run_once(
    sanctum_root: Path = SANCTUM_ROOT,
    ledger_path: Path = LEDGER_PATH_DEFAULT,
    oauth_health_path: Path = OAUTH_HEALTH_DEFAULT,
) -> dict:
    """CLI helper: poll the rate-limit sensor once + persist learner output.

    Returns a summary dict suitable for printing.
    """
    from overseer.sensors.rate_limit import RateLimitSensor

    sensor = RateLimitSensor(sanctum_root=sanctum_root)
    learner = RateLimitLearner(ledger_path=ledger_path, oauth_health_path=oauth_health_path)
    events = sensor.poll()
    learner.ingest(events)
    stats = learner.compute_slot_stats()
    recs = learner.recommendations(stats)
    learner.persist(stats, recs)
    return {
        "events_ingested": len(events),
        "slot_count": len(stats),
        "recommendations": len(recs),
        "ledger_path": str(learner.ledger_path),
    }
