"""hgly sim tests — Phase 8 simulation primitives.

Author: RKOJ-ELENO :: 2026-05-25
"""
from __future__ import annotations

import os
import sys

_THIS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(_THIS, "..", "src")))

from hgly.sim import World, get_world, reset_world, builtins  # noqa: E402


def t_snapshot_id_unique():
    w = World()
    a = w.snapshot()
    b = w.snapshot()
    assert a != b, "snapshot ids must be unique"
    assert a.startswith("snp-") and b.startswith("snp-")


def t_step_advances_time():
    w = World(init={"x": 0.0})
    s0 = w.snapshot()
    s1 = w.step(s0, 0.5)
    assert w.snapshots[s1].t > w.snapshots[s0].t
    assert w.snapshots[s1].state["x"] != w.snapshots[s0].state["x"]


def t_branch_decoupled():
    w = World(init={"y": 1.0})
    s0 = w.snapshot()
    b = w.branch(s0)
    # Mutating branch state should NOT change s0
    w.snapshots[b].state["y"] = 99.0
    assert w.snapshots[s0].state["y"] == 1.0


def t_merge_last_write_wins():
    w = World(init={"a": 1, "b": 2})
    s0 = w.snapshot()
    s1 = w.branch(s0)
    w.snapshots[s1].state["a"] = 99
    m = w.merge(s0, s1)
    assert w.snapshots[m].state["a"] == 99  # b overrides a
    assert w.snapshots[m].state["b"] == 2


def t_observe_deterministic():
    w = World(init={"out": 0.42}, seed=1)
    s = w.snapshot()
    assert w.observe(s, "out") == 0.42
    # Unknown key -> deterministic float in [0,1)
    v1 = w.observe(s, "qbit-0")
    v2 = w.observe(s, "qbit-0")
    assert v1 == v2, "observe of same key must be deterministic"
    assert 0.0 <= v1 <= 1.0


def t_perturb_bounded():
    w = World(init={"e": 10.0}, seed=2)
    s0 = w.snapshot()
    s1 = w.perturb(s0, 0.1)
    delta = abs(w.snapshots[s1].state["e"] - 10.0)
    assert delta <= 0.1 + 1e-9, f"perturb out of bound: delta={delta}"


def t_rewind_restores():
    w = World(init={"k": 5})
    s0 = w.snapshot()
    w.step(s0, 0.1)
    w.step(w.history[-1], 0.1)
    w.rewind(s0)
    assert w.state["k"] == 5
    assert w.t == 0.0


def t_materialize_commits():
    w = World(init={"q": 7})
    s0 = w.snapshot()
    s1 = w.branch(s0)
    w.snapshots[s1].state["q"] = 11
    final = w.materialize(s1)
    assert final["q"] == 11
    assert w.state["q"] == 11


def t_builtins_registry_has_all_8():
    b = builtins()
    for name in ("snapshot", "step", "branch", "merge",
                 "observe", "perturb", "rewind", "materialize"):
        assert name in b, f"missing builtin: {name}"
        # ASCII fallback aliases too
    for asc in ("snp", "stp", "brn", "mrg", "obs", "prt", "rwd", "mat"):
        assert asc in b, f"missing ASCII alias: {asc}"


def t_full_pipeline_via_builtins():
    reset_world(init={"q": 1.0}, seed=42)
    b = builtins()
    s0 = b["snapshot"](0)
    s1 = b["step"](s0, 0.001)
    br = b["branch"](s1)
    b["perturb"](br, 0.01)
    o = b["observe"](br, "q")
    m = b["merge"](s1, br)
    b["rewind"](m, s0)
    final = b["materialize"](m)
    assert isinstance(o, (int, float))
    assert "q" in final


def main():
    tests = [
        ("snapshot_id_unique", t_snapshot_id_unique),
        ("step_advances_time", t_step_advances_time),
        ("branch_decoupled", t_branch_decoupled),
        ("merge_last_write_wins", t_merge_last_write_wins),
        ("observe_deterministic", t_observe_deterministic),
        ("perturb_bounded", t_perturb_bounded),
        ("rewind_restores", t_rewind_restores),
        ("materialize_commits", t_materialize_commits),
        ("builtins_registry_has_all_8", t_builtins_registry_has_all_8),
        ("full_pipeline_via_builtins", t_full_pipeline_via_builtins),
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
