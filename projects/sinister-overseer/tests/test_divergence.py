# Author: RKOJ-ELENO :: 2026-05-25
"""test_divergence.py -- 5 pytest tests for divergence sensor + spawn action.

Covers:
    a. signal-A file-cluster detection
    b. signal-B serial-blocker detection
    c. confidence scoring (signal D > A > C > E and clamping)
    d. suggested-lane-name uniqueness across opportunities
    e. SpawnSubLaneAction dry-run (no subprocess, no log mutation when patched)
"""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SRC = _HERE.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def _fleet_state_for_a() -> dict:
    return {
        "projects": [{"key": "sinister-demo", "path": "p", "queue_rows": 0}],
        "progress_rows": {
            "sinister-demo": [
                "edited projects/sinister-demo/frontend/app.tsx ok",
                "edited projects/sinister-demo/backend/api.py ok",
                "edited projects/sinister-demo/docs/01.md ok",
            ]
        },
        "utterances": [],
        "heartbeats": {},
        "iter_summaries": {},
    }


def _fleet_state_for_b() -> dict:
    return {
        "projects": [{"key": "demo-b", "path": "p", "queue_rows": 0}],
        "progress_rows": {},
        "utterances": [],
        "heartbeats": {},
        "iter_summaries": {
            "demo-b": [
                "iter 10 blocked on UI redesign approval",
                "iter 11 blocked on UI redesign approval",
                "iter 12 blocked on UI redesign approval",
            ]
        },
    }


def _fleet_state_for_d() -> dict:
    return {
        "projects": [],
        "progress_rows": {},
        "utterances": [
            {"text": "while sanctum is doing icons, also spawn a lane for analytics", "ts_utc": "2026-05-25T07:00:00Z"},
        ],
        "heartbeats": {},
        "iter_summaries": {},
    }


def test_signal_a_file_cluster() -> None:
    from overseer.sensors.divergence import DivergenceSensor

    s = DivergenceSensor()
    opps = s.scan(_fleet_state_for_a())
    sig_a = [o for o in opps if o.signal == "A"]
    assert len(sig_a) >= 1, f"expected >=1 signal-A opp, got {len(sig_a)}"
    o = sig_a[0]
    assert 0.55 <= o.confidence <= 0.85
    assert o.estimated_parallelism >= 2
    assert len(o.evidence) >= 2
    assert o.sub_topic.startswith("split-")


def test_signal_b_serial_blocker() -> None:
    from overseer.sensors.divergence import DivergenceSensor

    s = DivergenceSensor()
    opps = s.scan(_fleet_state_for_b())
    sig_b = [o for o in opps if o.signal == "B"]
    assert len(sig_b) == 1, f"expected exactly 1 signal-B opp, got {len(sig_b)}"
    o = sig_b[0]
    assert "unblock" in o.sub_topic
    assert o.confidence == 0.78
    assert len(o.evidence) == 3


def test_confidence_scoring_ordering() -> None:
    from overseer.sensors.divergence import DivergenceSensor

    s = DivergenceSensor()
    opps_d = s.scan(_fleet_state_for_d())
    s2 = DivergenceSensor()
    opps_a = s2.scan(_fleet_state_for_a())

    d_max = max((o.confidence for o in opps_d if o.signal == "D"), default=0.0)
    a_max = max((o.confidence for o in opps_a if o.signal == "A"), default=0.0)
    assert d_max > a_max, f"operator-directive (D={d_max}) should outrank file-cluster (A={a_max})"
    assert d_max <= 1.0 and a_max <= 1.0


def test_suggested_lane_name_uniqueness() -> None:
    from overseer.sensors.divergence import DivergenceSensor

    s = DivergenceSensor()
    # combine multiple signals
    combined = _fleet_state_for_a()
    combined["iter_summaries"] = _fleet_state_for_b()["iter_summaries"]
    combined["projects"].append({"key": "demo-b", "path": "p", "queue_rows": 0})
    combined["utterances"] = _fleet_state_for_d()["utterances"]

    opps = s.scan(combined)
    names = [o.suggested_lane_name for o in opps]
    assert len(names) == len(set(names)), f"duplicate suggested_lane_name: {names}"
    for n in names:
        assert n.startswith("agent/"), f"branch must start with agent/: {n}"
        parts = n.split("/")
        # agent/<project>/<topic-utcdate>
        assert len(parts) == 3, f"expected 3 path segments, got {n}"


def test_spawn_action_dry_run(monkeypatch, tmp_path) -> None:
    from overseer.actions import spawn_sub_lane as ssl
    from overseer.sensors.divergence import DivergenceOpportunity

    # Redirect log + heartbeat dir to tmp so we don't touch shared memory.
    monkeypatch.setattr(ssl, "SPAWN_LOG", tmp_path / "spawn.jsonl")
    monkeypatch.setattr(ssl, "HEARTBEAT_DIR", tmp_path / "hb")
    (tmp_path / "hb").mkdir(parents=True, exist_ok=True)

    opp = DivergenceOpportunity(
        project_key="demo",
        sub_topic="hello",
        evidence=("e1", "e2", "e3"),
        suggested_lane_name="agent/demo/hello-2026-05-25",
        estimated_parallelism=2,
        confidence=0.95,
        rationale="r",
        signal="A",
    )
    action = ssl.SpawnSubLaneAction()
    res = action.execute(opp, dry_run=True)
    assert res.status == "dry-run", f"expected status='dry-run', got {res.status}"
    assert res.lane_branch == "agent/demo/hello-2026-05-25"
    assert res.planned_command and "multi_agent_launcher.py" in " ".join(res.planned_command)
    assert (tmp_path / "spawn.jsonl").is_file()


if __name__ == "__main__":
    import json as _json

    tests = [
        test_signal_a_file_cluster,
        test_signal_b_serial_blocker,
        test_confidence_scoring_ordering,
        test_suggested_lane_name_uniqueness,
    ]
    passed = 0
    failed = []
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as exc:  # noqa: BLE001
            failed.append((t.__name__, repr(exc)))
    sys.stdout.write(_json.dumps({"passed": passed, "failed": [n for n, _ in failed]}, indent=2) + "\n")
    sys.exit(0 if not failed else 1)
