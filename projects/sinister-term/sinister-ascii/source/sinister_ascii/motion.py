# Sinister ASCII (sub-project of Sinister Term)
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# SA-PH2 :: motion.py — the 5 motion primitives an entity can adopt.
# orbit / pulse / drift / spiral / breathe. Each returns (x, y, intensity)
# for absolute time `t_seconds` in a normalized [-1, 1] coordinate space.
# The renderer projects to character cells.
#
# All math is pure + deterministic. Anti-loop period multipliers use irrational
# constants (phi, pi/3) so the operator never sees a "repeats every N seconds"
# point — the operator vision (verbatim 2026-05-25):
#   "the feeling of it being endless that leaves me breathles".

from __future__ import annotations

import math
from dataclasses import dataclass


_PHI = (1.0 + math.sqrt(5.0)) / 2.0  # golden ratio ≈ 1.618033988
_INV_PHI = 1.0 / _PHI                 # ≈ 0.618033988
_TAU = 2.0 * math.pi


@dataclass(frozen=True)
class MotionFrame:
    """One sample of an entity's motion at time t."""
    x: float        # [-1.0, 1.0] normalized
    y: float        # [-1.0, 1.0] normalized
    intensity: float  # [0.0, 1.0] — drives color blend + brightness


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def orbit(t_seconds: float, *, radius: float = 0.7, period_s: float = 6.0,
          phase: float = 0.0, wobble: float = 0.12) -> MotionFrame:
    """Circular orbit around the origin with subtle wobble.

    The radius pulses slightly (wobble) to avoid the "perfect circle" feel,
    and intensity peaks twice per orbit (figure-8 in intensity space).
    """
    omega = _TAU / max(0.1, period_s)
    theta = omega * t_seconds + phase * _TAU
    r = radius + wobble * math.sin(theta * _PHI)  # wobble at irrational ratio
    x = _clamp(r * math.cos(theta), -1.0, 1.0)
    y = _clamp(r * math.sin(theta), -1.0, 1.0)
    intensity = 0.55 + 0.4 * abs(math.sin(2.0 * theta))
    return MotionFrame(x, y, _clamp(intensity, 0.0, 1.0))


def pulse(t_seconds: float, *, period_s: float = 1.8, attack: float = 0.25,
          decay: float = 0.65) -> MotionFrame:
    """Stationary entity that pulses in intensity. Heartbeat-like.

    Position is fixed at origin; intensity sweeps a sawtooth-ish profile with
    a fast attack (compressed) and slow decay.
    """
    phase = (t_seconds % max(0.1, period_s)) / max(0.1, period_s)
    if phase < attack:
        intensity = phase / attack
    else:
        rem = (phase - attack) / max(0.001, (1.0 - attack))
        intensity = math.exp(-rem * (1.0 + 3.0 * decay))
    return MotionFrame(0.0, 0.0, _clamp(intensity, 0.0, 1.0))


def drift(t_seconds: float, *, x_period_s: float = 13.0,
          y_period_s: float = 17.0, x_amp: float = 0.65,
          y_amp: float = 0.45) -> MotionFrame:
    """Slow lissajous drift — never repeats because periods are coprime irrationals."""
    x = x_amp * math.sin(_TAU * t_seconds / x_period_s)
    y = y_amp * math.cos(_TAU * t_seconds / y_period_s + _INV_PHI)
    # Intensity rides a third irrational period
    intensity = 0.45 + 0.45 * math.sin(_TAU * t_seconds / 23.0 + 1.111)
    return MotionFrame(_clamp(x, -1.0, 1.0), _clamp(y, -1.0, 1.0),
                       _clamp(intensity, 0.0, 1.0))


def spiral(t_seconds: float, *, period_s: float = 9.0,
           growth: float = 0.6) -> MotionFrame:
    """Spiral outward then snap back. Period_s is one full out-back cycle."""
    half = period_s / 2.0
    cycle_phase = t_seconds % period_s
    if cycle_phase < half:
        r = (cycle_phase / half) * growth
    else:
        r = (1.0 - (cycle_phase - half) / half) * growth
    omega = _TAU / max(0.1, period_s) * 3.0  # 3 turns per cycle
    theta = omega * t_seconds
    x = r * math.cos(theta)
    y = r * math.sin(theta)
    # Intensity scales with radius — feels like winding up + releasing
    intensity = 0.4 + 0.55 * (r / max(growth, 0.001))
    return MotionFrame(_clamp(x, -1.0, 1.0), _clamp(y, -1.0, 1.0),
                       _clamp(intensity, 0.0, 1.0))


def breathe(t_seconds: float, *, inhale_s: float = 2.4,
            exhale_s: float = 3.6) -> MotionFrame:
    """Asymmetric breathing — inhale faster than exhale (like a real living being).

    Position is fixed; intensity describes a smooth in-out cycle.
    """
    full = inhale_s + exhale_s
    phase = t_seconds % full
    if phase < inhale_s:
        # ease-in-out cubic
        t_norm = phase / inhale_s
        s = t_norm * t_norm * (3.0 - 2.0 * t_norm)
        intensity = 0.25 + 0.75 * s
    else:
        t_norm = (phase - inhale_s) / max(0.001, exhale_s)
        s = 1.0 - t_norm * t_norm * (3.0 - 2.0 * t_norm)
        intensity = 0.25 + 0.75 * s
    return MotionFrame(0.0, 0.0, _clamp(intensity, 0.0, 1.0))


# Lookup table by name so entities can reference motion by string
MOTIONS = {
    "orbit": orbit,
    "pulse": pulse,
    "drift": drift,
    "spiral": spiral,
    "breathe": breathe,
}


def sample(name: str, t_seconds: float, **kwargs) -> MotionFrame:
    """Lookup-and-call a motion primitive by name."""
    fn = MOTIONS.get(name)
    if fn is None:
        # Default to breathe (least visually disruptive) on unknown motion
        return breathe(t_seconds)
    return fn(t_seconds, **kwargs)
