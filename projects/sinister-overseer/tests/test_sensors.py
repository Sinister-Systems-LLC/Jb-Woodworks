"""test_sensors.py -- smoke for sensors + contradiction stub.

Author: RKOJ-ELENO :: 2026-05-24

Runs in zero-dep mode (no pytest required) via ``python tests/test_sensors.py``
AND under pytest. Verifies:
    1. All three sensor classes import + instantiate.
    2. The SensorBus accepts sensors + subscribers + poll_all() returns a list.
    3. The contradiction module's public API is callable + returns the
       documented stub shapes (score=0 / verdict=apply on empty input).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


# Allow running as a script (no install required).
_HERE = Path(__file__).resolve().parent
_SRC = _HERE.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def test_sensors_instantiate() -> None:
    from overseer.sensors.analyzer import (
        ForeverImproveSensor,
        SensorBus,
        TokenAnalyzerSensor,
        UsageMeterSensor,
    )

    bus = SensorBus()
    bus.add_sensor(TokenAnalyzerSensor())
    bus.add_sensor(UsageMeterSensor(pct_threshold=0.85))
    bus.add_sensor(ForeverImproveSensor(open_threshold=3))

    collected: list = []
    bus.subscribe(collected.append)

    assert len(bus.sensors) == 3
    assert len(bus.handlers) == 1

    events = bus.poll_all()
    assert isinstance(events, list)


def test_sensors_package_reexports() -> None:
    # The package __init__ should re-export each public name.
    import overseer.sensors as pkg

    for name in (
        "SensorBus",
        "TokenAnalyzerSensor",
        "UsageMeterSensor",
        "ForeverImproveSensor",
        "WasteEvent",
        "RecommendationEvent",
        "UsageHighEvent",
        "RotInLogEvent",
    ):
        assert hasattr(pkg, name), f"sensors package missing re-export: {name}"


def test_contradiction_stubs() -> None:
    from overseer.contradiction import (
        FixProposal,
        Lane,
        run_full_contradiction_check,
        score_counter_argument,
        should_rollback,
    )

    fix = FixProposal(
        fix_id="fix-test-0001",
        lane="sinister-chatbot",
        kind="config-tweak",
        risk="low",
        diff_summary="Smoke fix for tests",
    )

    score = score_counter_argument(fix)
    assert score == 0  # P0 stub always returns 0

    assert should_rollback(7) is True
    assert should_rollback(5) is False
    assert should_rollback(6) is False  # threshold default 6, only > triggers

    verdict = run_full_contradiction_check(fix, all_lanes=[Lane(slug="sinister-chatbot")])
    assert verdict["fix_id"] == "fix-test-0001"
    assert verdict["counter_arg_score"] == 0
    assert verdict["verdict"] == "apply"  # zero score + no conflicts


def _main() -> int:
    tests = [
        test_sensors_instantiate,
        test_sensors_package_reexports,
        test_contradiction_stubs,
    ]
    passed = 0
    failed: list[tuple[str, str]] = []
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as exc:  # noqa: BLE001 -- want a full report
            failed.append((t.__name__, repr(exc)))

    report = {
        "total": len(tests),
        "passed": passed,
        "failed": len(failed),
        "failures": [{"name": n, "err": e} for n, e in failed],
    }
    sys.stdout.write(json.dumps(report, indent=2) + "\n")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(_main())
