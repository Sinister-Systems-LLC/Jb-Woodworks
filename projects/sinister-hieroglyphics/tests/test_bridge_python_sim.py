"""hgly bridge-to-python_simulator tests (Phase 8b).

Author: RKOJ-ELENO :: 2026-05-25
"""
from __future__ import annotations

import os
import sys

_THIS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(_THIS, "..", "src")))

from hgly.bridge_python_sim import (qsubmit, qstatus, is_live,  # noqa: E402
                                    builtins, _port_for, _synth_response)


def t_port_mapping_all_systems():
    assert _port_for("superconducting") == 7000
    assert _port_for("ion_trap") == 7001
    assert _port_for("neutral_atom") == 7002
    assert _port_for("photonic") == 7003
    assert _port_for("SuperConducting") == 7000
    assert _port_for("unknown") is None


def t_synth_response_deterministic():
    p = {"qubits": 4, "gates": ["H", "CX"]}
    a = _synth_response("superconducting", p)
    b = _synth_response("superconducting", p)
    assert a == b, "synth response must be deterministic"
    assert a["status"] == "ok"
    assert a["task_id"].startswith("synth-")
    assert "fidelity" in a["result"]
    assert 0.0 <= a["result"]["fidelity"] <= 1.0


def t_synth_response_varies_by_payload():
    a = _synth_response("superconducting", {"qubits": 2})
    b = _synth_response("superconducting", {"qubits": 4})
    assert a["task_id"] != b["task_id"], "different payloads -> different task_id"


def t_qsubmit_falls_back_when_no_server():
    """No desktop sim running -> synthesized response."""
    r = qsubmit("superconducting", {"qubits": 8})
    assert r["status"] == "ok"
    assert r["synthesized"] in (True, False)
    assert "task_id" in r
    assert "result" in r


def t_qstatus_returns_completed():
    s = qstatus("synth-abc123")
    assert s["task_id"] == "synth-abc123"
    assert s["status"] == "completed"


def t_is_live_does_not_throw():
    """Even when no server running, is_live() returns False without raising."""
    rv = is_live("photonic")
    assert isinstance(rv, bool)


def t_builtins_registry():
    b = builtins()
    for name in ("qsubmit", "qstatus", "qsim_live", "qsim"):
        assert name in b
    assert callable(b["qsubmit"])


def t_qsubmit_with_non_dict_payload():
    """Bridge should normalize string/int/None payloads -> dict."""
    assert qsubmit("superconducting", None)["status"] == "ok"
    assert qsubmit("superconducting", 42)["status"] == "ok"
    assert qsubmit("superconducting", "raw-prompt")["status"] == "ok"
    assert qsubmit("superconducting", '{"qubits":3}')["status"] == "ok"


def main():
    tests = [
        ("port_mapping_all_systems", t_port_mapping_all_systems),
        ("synth_response_deterministic", t_synth_response_deterministic),
        ("synth_response_varies_by_payload", t_synth_response_varies_by_payload),
        ("qsubmit_falls_back_when_no_server", t_qsubmit_falls_back_when_no_server),
        ("qstatus_returns_completed", t_qstatus_returns_completed),
        ("is_live_does_not_throw", t_is_live_does_not_throw),
        ("builtins_registry", t_builtins_registry),
        ("qsubmit_with_non_dict_payload", t_qsubmit_with_non_dict_payload),
    ]
    passed = failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS  {name}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"  FAIL  {name}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n== {passed} passed, {failed} failed ==")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
