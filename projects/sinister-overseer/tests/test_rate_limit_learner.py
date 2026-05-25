# Author: RKOJ-ELENO :: 2026-05-25
"""D3 slice-1 tests for rate-limit sensor + learner.

Covers:
  1. RateLimitSensor reads JSONL events + dedups across polls.
  2. RateLimitSensor handles missing/malformed input gracefully.
  3. RateLimitLearner computes per-slot rolling counts (1h / 24h).
  4. Mean inter-arrival is computed in seconds.
  5. Recommendation: burning slot rotates to highest-availability peer.
  6. Burning slot with NO viable peer escalates as `quota_exhaustion_escalate`.
  7. Burn window (5 min) -- recently 429'd peer is skipped as a rotation target.
  8. Persist ledger writes valid JSON with expected shape.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Allow running pytest without installing the package
SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pytest

from overseer.rate_limit_learner import RateLimitLearner, RotationRecommendation, SlotStats
from overseer.sensors.rate_limit import RateLimit429Event, RateLimitSensor


# ---------------------------------------------------------------------------
# sensor tests
# ---------------------------------------------------------------------------

def _write_throttle(tmp_path: Path, rows: list[dict]) -> Path:
    p = tmp_path / "throttle.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return p


def test_sensor_reads_events(tmp_path):
    log = _write_throttle(tmp_path, [
        {"ts_utc": "2026-05-25T08:00:00Z", "account": "operator", "project": "p1", "excerpt": "rate limit hit"},
        {"ts_utc": "2026-05-25T08:01:00Z", "account": "operator-b", "project": "p2", "excerpt": "rate limit hit"},
    ])
    sensor = RateLimitSensor(throttle_log=log)
    events = sensor.poll()
    assert len(events) == 2
    accts = sorted(e.account for e in events)
    assert accts == ["operator", "operator-b"]


def test_sensor_dedups_across_polls(tmp_path):
    log = _write_throttle(tmp_path, [
        {"ts_utc": "2026-05-25T08:00:00Z", "account": "operator", "project": "p1", "excerpt": "x"},
    ])
    sensor = RateLimitSensor(throttle_log=log)
    assert len(sensor.poll()) == 1
    # second poll on same file -> dedup -> 0 fresh
    assert sensor.poll() == []


def test_sensor_missing_file_returns_empty(tmp_path):
    sensor = RateLimitSensor(throttle_log=tmp_path / "does-not-exist.jsonl")
    assert sensor.poll() == []


def test_sensor_skips_malformed_lines(tmp_path):
    log = tmp_path / "throttle.jsonl"
    log.write_text(
        '{"ts_utc":"2026-05-25T08:00:00Z","account":"operator","project":"p1","excerpt":"x"}\n'
        'not-json-at-all\n'
        '   \n'
        '{"ts_utc":"2026-05-25T08:02:00Z","account":"operator","project":"p1","excerpt":"y"}\n',
        encoding="utf-8",
    )
    sensor = RateLimitSensor(throttle_log=log)
    events = sensor.poll()
    assert len(events) == 2


# ---------------------------------------------------------------------------
# learner tests
# ---------------------------------------------------------------------------

def _fmt(ts: datetime) -> str:
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def test_learner_counts_1h_vs_24h(tmp_path):
    now = datetime.now(timezone.utc)
    events = [
        # 1h-old
        RateLimit429Event(ts_utc=_fmt(now - timedelta(minutes=30)), account="op", project="p1", excerpt="x"),
        RateLimit429Event(ts_utc=_fmt(now - timedelta(minutes=10)), account="op", project="p1", excerpt="x"),
        # 24h-old (NOT in 1h window)
        RateLimit429Event(ts_utc=_fmt(now - timedelta(hours=6)), account="op", project="p2", excerpt="x"),
        # >24h -- dropped
        RateLimit429Event(ts_utc=_fmt(now - timedelta(hours=30)), account="op", project="p3", excerpt="x"),
    ]
    learner = RateLimitLearner(
        ledger_path=tmp_path / "ledger.json",
        oauth_health_path=tmp_path / "missing.json",
    )
    learner.ingest(events)
    stats = learner.compute_slot_stats(now=now)
    assert "op" in stats
    assert stats["op"].count_1h == 2
    assert stats["op"].count_24h == 3
    assert "p3" not in stats["op"].projects_429d_24h


def test_learner_mean_inter_arrival_seconds(tmp_path):
    now = datetime.now(timezone.utc)
    events = [
        RateLimit429Event(ts_utc=_fmt(now - timedelta(minutes=30)), account="op", project="p1", excerpt="x"),
        RateLimit429Event(ts_utc=_fmt(now - timedelta(minutes=20)), account="op", project="p1", excerpt="x"),
        RateLimit429Event(ts_utc=_fmt(now - timedelta(minutes=10)), account="op", project="p1", excerpt="x"),
    ]
    learner = RateLimitLearner(ledger_path=tmp_path / "ledger.json")
    learner.ingest(events)
    stats = learner.compute_slot_stats(now=now)
    # 10-minute spacing -> mean ~600s
    assert 595.0 <= stats["op"].mean_inter_arrival_s <= 605.0


def test_learner_recommends_rotation_to_best_peer(tmp_path):
    now = datetime.now(timezone.utc)
    events = [
        RateLimit429Event(ts_utc=_fmt(now - timedelta(minutes=15)), account="op", project="p1", excerpt="x"),
        RateLimit429Event(ts_utc=_fmt(now - timedelta(minutes=10)), account="op", project="p1", excerpt="x"),
        RateLimit429Event(ts_utc=_fmt(now - timedelta(minutes=5)), account="op", project="p1", excerpt="x"),
    ]
    health = {
        "slots": [
            {"name": "op", "enabled": True, "rate_limited": False, "availability_score": 0.1},
            {"name": "op-b", "enabled": True, "rate_limited": False, "availability_score": 0.85},
            {"name": "op-c", "enabled": True, "rate_limited": False, "availability_score": 0.50},
            {"name": "leo", "enabled": False, "rate_limited": False, "availability_score": 0.99},
        ],
    }
    learner = RateLimitLearner(ledger_path=tmp_path / "ledger.json")
    learner.ingest(events)
    stats = learner.compute_slot_stats(now=now)
    recs = learner.recommendations(stats, oauth_health=health, now=now)
    assert len(recs) == 1
    assert recs[0].from_slot == "op"
    # Highest-scoring viable peer (excluding self + disabled leo) is op-b
    assert recs[0].to_slot == "op-b"
    assert recs[0].risk == "medium"
    assert recs[0].fix_template == "rotate_oauth_slot"


def test_learner_escalates_when_no_viable_peer(tmp_path):
    now = datetime.now(timezone.utc)
    events = [
        RateLimit429Event(ts_utc=_fmt(now - timedelta(minutes=15)), account="op", project="p1", excerpt="x"),
        RateLimit429Event(ts_utc=_fmt(now - timedelta(minutes=10)), account="op", project="p1", excerpt="x"),
        RateLimit429Event(ts_utc=_fmt(now - timedelta(minutes=5)), account="op", project="p1", excerpt="x"),
    ]
    health = {
        "slots": [
            {"name": "op", "enabled": True, "rate_limited": False, "availability_score": 0.1},
            {"name": "op-b", "enabled": True, "rate_limited": True, "availability_score": 0.85},  # already RL
            {"name": "leo", "enabled": False, "rate_limited": False, "availability_score": 0.99},  # disabled
        ],
    }
    learner = RateLimitLearner(ledger_path=tmp_path / "ledger.json")
    learner.ingest(events)
    stats = learner.compute_slot_stats(now=now)
    recs = learner.recommendations(stats, oauth_health=health, now=now)
    assert len(recs) == 1
    assert recs[0].fix_template == "quota_exhaustion_escalate"
    assert recs[0].risk == "high"


def test_learner_burn_window_excludes_recent_429_peer(tmp_path):
    now = datetime.now(timezone.utc)
    # op is burning; op-b was 429'd 2 min ago -> in burn window -> SKIP
    events = [
        RateLimit429Event(ts_utc=_fmt(now - timedelta(minutes=15)), account="op", project="p1", excerpt="x"),
        RateLimit429Event(ts_utc=_fmt(now - timedelta(minutes=10)), account="op", project="p1", excerpt="x"),
        RateLimit429Event(ts_utc=_fmt(now - timedelta(minutes=5)), account="op", project="p1", excerpt="x"),
        RateLimit429Event(ts_utc=_fmt(now - timedelta(minutes=2)), account="op-b", project="p1", excerpt="x"),
    ]
    health = {
        "slots": [
            {"name": "op", "enabled": True, "rate_limited": False, "availability_score": 0.1},
            {"name": "op-b", "enabled": True, "rate_limited": False, "availability_score": 0.85},
            {"name": "op-c", "enabled": True, "rate_limited": False, "availability_score": 0.50},
        ],
    }
    learner = RateLimitLearner(ledger_path=tmp_path / "ledger.json")
    learner.ingest(events)
    stats = learner.compute_slot_stats(now=now)
    recs = learner.recommendations(stats, oauth_health=health, now=now)
    # op rotates to op-c (op-b in burn window)
    op_recs = [r for r in recs if r.from_slot == "op"]
    assert len(op_recs) == 1
    assert op_recs[0].to_slot == "op-c"


def test_learner_persist_writes_valid_ledger(tmp_path):
    now = datetime.now(timezone.utc)
    events = [
        RateLimit429Event(ts_utc=_fmt(now - timedelta(minutes=5)), account="op", project="p1", excerpt="x"),
    ]
    health = {"slots": [{"name": "op-b", "enabled": True, "rate_limited": False, "availability_score": 0.85}]}
    ledger = tmp_path / "ledger.json"
    learner = RateLimitLearner(ledger_path=ledger)
    learner.ingest(events)
    stats = learner.compute_slot_stats(now=now)
    recs = learner.recommendations(stats, oauth_health=health, now=now)
    out = learner.persist(stats, recs)
    assert out == ledger
    doc = json.loads(ledger.read_text(encoding="utf-8"))
    assert doc["schema_version"] == "sinister.overseer.rate-limit-learner.v1"
    assert "op" in doc["slots"]
    assert doc["slots"]["op"]["count_24h"] == 1


def test_learner_no_burning_slot_no_recs(tmp_path):
    now = datetime.now(timezone.utc)
    # one event, far enough that not burning
    events = [
        RateLimit429Event(ts_utc=_fmt(now - timedelta(minutes=45)), account="op", project="p1", excerpt="x"),
    ]
    health = {"slots": [{"name": "op-b", "enabled": True, "rate_limited": False, "availability_score": 0.85}]}
    learner = RateLimitLearner(ledger_path=tmp_path / "ledger.json")
    learner.ingest(events)
    stats = learner.compute_slot_stats(now=now)
    recs = learner.recommendations(stats, oauth_health=health, now=now)
    assert recs == []
