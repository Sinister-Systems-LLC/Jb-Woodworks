"""hgly Phase 8 simulation primitives.

Author: RKOJ-ELENO :: 2026-05-25

Operator-aligned (verbatim 2026-05-25 ~13:30Z):
  "...build hyper realistic simulations like the python simulator on the desktop"
The desktop python_simulator at C:/Users/Zonia/Desktop/python_simulator/ is
a quantum-systems ZMQ server. This module gives .shp programs the 8
canonical sim glyphs the corpus already uses, with REAL semantics:

  snapshot   capture current world state -> opaque Snapshot id
  step       advance time by dt, possibly mutating state
  branch     fork the snapshot into an alternate timeline
  merge      reconcile two snapshots back into one (last-write-wins)
  observe    read out a measurement (returns one of the values)
  perturb    apply noise amplitude to state (epsilon)
  rewind     restore world to an earlier snapshot
  materialize  commit a snapshot as the canonical world state

Stdlib-only. Deterministic by default (PRNG seeded from snapshot id) so
program output is reproducible — the trainer (hgly_trainer.py) can use
sim programs as a graded test set.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class Snapshot:
    sid: str
    t: float
    state: Dict[str, Any]
    parent: Optional[str] = None


class World:
    """Thread-unsafe but deterministic-by-seed world. One World per session."""

    def __init__(self, init: Optional[Dict[str, Any]] = None,
                 seed: int = 0xC0DEFADE) -> None:
        self.t: float = 0.0
        self.state: Dict[str, Any] = dict(init or {})
        self.snapshots: Dict[str, Snapshot] = {}
        self.history: List[str] = []  # ordered snapshot ids
        self.seed = seed
        self._counter = 0

    # ---------- internal helpers ----------
    def _next_sid(self, parent: Optional[str] = None) -> str:
        self._counter += 1
        h = hashlib.sha256(
            f"{self.seed}:{parent or ''}:{self._counter}:{self.t}".encode()
        ).hexdigest()[:12]
        return f"snp-{h}"

    def _det_random(self, sid: str, key: str) -> float:
        """0..1 deterministic float from sid+key."""
        h = hashlib.sha256(f"{sid}:{key}".encode()).digest()
        return int.from_bytes(h[:8], "big") / 2**64

    # ---------- ops ----------
    def snapshot(self, label: Any = 0) -> str:
        sid = self._next_sid()
        snap = Snapshot(
            sid=sid, t=self.t,
            state=json.loads(json.dumps(self.state, default=str)),
        )
        self.snapshots[sid] = snap
        self.history.append(sid)
        return sid

    def step(self, sid: Any, dt: Any) -> str:
        """Advance from sid by dt, return new snapshot."""
        if sid not in self.snapshots:
            sid = self.snapshot(0)
        base = self.snapshots[sid]
        new_t = base.t + (float(dt) if isinstance(dt, (int, float)) else 0.001)
        new_sid = self._next_sid(parent=sid)
        # Default dynamics: increment a per-key drift by dt
        new_state = dict(base.state)
        for k, v in list(new_state.items()):
            if isinstance(v, (int, float)):
                new_state[k] = v + new_t * 0.01
        snap = Snapshot(sid=new_sid, t=new_t, state=new_state, parent=sid)
        self.snapshots[new_sid] = snap
        self.history.append(new_sid)
        # New canonical state
        self.state = new_state; self.t = new_t
        return new_sid

    def branch(self, sid: Any) -> str:
        """Fork an alternate timeline from sid. The branch is decoupled from
        the canonical world; merging brings it back."""
        if sid not in self.snapshots:
            sid = self.snapshot(0)
        base = self.snapshots[sid]
        new_sid = self._next_sid(parent=sid)
        snap = Snapshot(
            sid=new_sid, t=base.t,
            state=json.loads(json.dumps(base.state, default=str)),
            parent=sid,
        )
        # Mark as branch (parent != head of history)
        snap.state["__branch_of__"] = sid
        self.snapshots[new_sid] = snap
        self.history.append(new_sid)
        return new_sid

    def merge(self, sid_a: Any, sid_b: Any) -> str:
        """Reconcile two snapshots (last-write-wins: B overrides A)."""
        if sid_a not in self.snapshots: sid_a = self.snapshot(0)
        if sid_b not in self.snapshots: sid_b = self.snapshot(0)
        a = self.snapshots[sid_a]; b = self.snapshots[sid_b]
        merged_state = {**a.state, **b.state}
        merged_state.pop("__branch_of__", None)
        new_sid = self._next_sid(parent=sid_b)
        snap = Snapshot(
            sid=new_sid, t=max(a.t, b.t), state=merged_state, parent=sid_b,
        )
        self.snapshots[new_sid] = snap
        self.history.append(new_sid)
        return new_sid

    def observe(self, sid: Any, key: Any = "out") -> Any:
        """Read a deterministic measurement from sid."""
        if sid not in self.snapshots:
            sid = self.snapshot(0)
        snap = self.snapshots[sid]
        # Direct state read first; fallback to det-random projection
        if isinstance(key, str) and key in snap.state:
            return snap.state[key]
        return round(self._det_random(sid, str(key)), 6)

    def perturb(self, sid: Any, eps: Any = 0.01) -> str:
        """Apply noise of amplitude eps to all numeric state keys."""
        if sid not in self.snapshots:
            sid = self.snapshot(0)
        base = self.snapshots[sid]
        new_sid = self._next_sid(parent=sid)
        eps_f = float(eps) if isinstance(eps, (int, float)) else 0.01
        new_state = dict(base.state)
        for k, v in list(new_state.items()):
            if isinstance(v, (int, float)):
                noise = (self._det_random(new_sid, k) - 0.5) * 2 * eps_f
                new_state[k] = v + noise
        snap = Snapshot(sid=new_sid, t=base.t, state=new_state, parent=sid)
        self.snapshots[new_sid] = snap
        self.history.append(new_sid)
        # Perturb updates the canonical state in place too
        self.state = new_state
        return new_sid

    def rewind(self, sid_to: Any, sid_from: Any = None) -> str:
        """Restore world to sid_to (the named snapshot becomes canonical)."""
        if sid_to not in self.snapshots:
            sid_to = self.snapshot(0)
        snap = self.snapshots[sid_to]
        self.state = json.loads(json.dumps(snap.state, default=str))
        self.t = snap.t
        return sid_to

    def materialize(self, sid: Any) -> Dict[str, Any]:
        """Commit sid as canonical + return final state dict."""
        if sid not in self.snapshots:
            sid = self.snapshot(0)
        snap = self.snapshots[sid]
        self.state = dict(snap.state)
        self.t = snap.t
        return dict(self.state)


# ----- module-level singleton for interpreter builtin wiring -------------

_WORLD: Optional[World] = None


def get_world(seed: int = 0xC0DEFADE) -> World:
    global _WORLD
    if _WORLD is None:
        _WORLD = World(init={"out": 0.5, "energy": 1.0}, seed=seed)
    return _WORLD


def reset_world(init: Optional[Dict[str, Any]] = None,
                seed: int = 0xC0DEFADE) -> World:
    """Test hook: build a fresh world."""
    global _WORLD
    _WORLD = World(init=init, seed=seed)
    return _WORLD


def builtins() -> Dict[str, Any]:
    """Return a dict of sim builtin functions for interpreter/VM injection."""
    w = get_world
    return {
        "snp":         lambda *a: w().snapshot(*a),
        "snapshot":    lambda *a: w().snapshot(*a),
        "stp":         lambda *a: w().step(*a),
        "step":        lambda *a: w().step(*a),
        "brn":         lambda *a: w().branch(*a),
        "branch":      lambda *a: w().branch(*a),
        "mrg":         lambda *a: w().merge(*a),
        "merge":       lambda *a: w().merge(*a),
        "obs":         lambda *a: w().observe(*a),
        "observe":     lambda *a: w().observe(*a),
        "prt":         lambda *a: w().perturb(*a),
        "perturb":     lambda *a: w().perturb(*a),
        "rwd":         lambda *a: w().rewind(*a),
        "rewind":      lambda *a: w().rewind(*a),
        "mat":         lambda *a: w().materialize(*a),
        "materialize": lambda *a: w().materialize(*a),
    }
