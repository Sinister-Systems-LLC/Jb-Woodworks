"""Behavioral fingerprint generator — hyper-realistic human-vs-bot signals.

RKOJ-ELENO :: 2026-05-24 :: GPL-3.0-or-later

Generates 4 behavioral channels that Snapchat (and most modern anti-bot SDKs)
sample during account creation + first-session activity:

  1. gyro_micro_tremor  — humans have 4-10Hz hand tremor (essential tremor +
                          physiological vibration). Bots running on cvd
                          report zero gyro motion → instant flag.
                          Source distribution: sum of 2 sinusoids (4Hz + 8Hz)
                          + 1/f pink noise + QRNG-seeded amplitude per sample.

  2. typing_intervals   — inter-keystroke intervals are log-normally distributed
                          (median ~120-280ms for English-on-mobile). Bots
                          either use uniform or constant intervals → flag.
                          Distribution: log-normal(μ=5.2, σ=0.45) clipped to
                          [40, 1200]ms, with rare "pause" outliers (10-30s)
                          for word-boundary thinking.

  3. dwell_time         — time spent on each onboarding screen. Distribution:
                          gamma(k=2.5, θ=4.0) seconds, with bimodality —
                          first-time-users spend more time on consent screens.

  4. swipe_gestures     — touchscreen swipe velocity + curvature. Real humans
                          produce arc-shaped swipes (start fast, decelerate,
                          slight curve from index-finger pivot). Bots produce
                          straight-line + constant-velocity swipes → flag.
                          Generated as Bézier-control-point sequences with
                          QRNG-perturbed curvature.

All 4 channels are SEEDED via sinister-seraphim CLI `qrng` for non-classical
entropy. Each profile generates ONE complete activity log (~30 seconds of
in-app behavior) consumable by the scenario runner.

Output schema: sandbox/behavioral/profiles/<class_name>.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import subprocess
from pathlib import Path
from typing import Any

SERAPHIM_CLI = (
    Path(__file__).resolve().parents[4] / "tools" / "sinister-seraphim" / "cli.py"
)


# ---------- QRNG entropy source ----------------------------------------------

QRNG_CHUNK_MAX = 1024  # seraphim qrng tolerates up to ~4096; 1024 is a safe ceiling


def qrng_bytes(n: int, purpose: str) -> bytes:
    """Fetch n bytes of QRNG entropy from seraphim. Chunks requests to stay
    inside seraphim's per-call limit. Falls back to hashlib only if seraphim
    is unreachable (with a visible stderr warning)."""
    out = bytearray()
    chunk_idx = 0
    while len(out) < n:
        want = min(QRNG_CHUNK_MAX, n - len(out))
        chunk = _qrng_one_call(want, f"{purpose}#chunk{chunk_idx}")
        if chunk is None:
            return _hashlib_fallback(n, purpose)
        out.extend(chunk)
        chunk_idx += 1
    return bytes(out[:n])


def _qrng_one_call(n: int, purpose: str) -> bytes | None:
    """One seraphim qrng invocation. Returns bytes on success, None on failure."""
    cmd = [
        "python", str(SERAPHIM_CLI), "--json", "qrng",
        "-n", str(n), "--purpose", purpose,
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=10, check=False)
        if out.returncode != 0:
            return None
        data = json.loads(out.stdout)
        if "bytes_hex" in data:
            return bytes.fromhex(data["bytes_hex"])
        if "hex" in data:
            return bytes.fromhex(data["hex"])
        if "bytes" in data and isinstance(data["bytes"], list):
            return bytes(data["bytes"])
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError, ValueError):
        pass
    return None


def _hashlib_fallback(n: int, purpose: str) -> bytes:
    import sys
    print(f"[behavioral] WARN: seraphim QRNG unreachable; falling back to hashlib for '{purpose}'", file=sys.stderr)
    seed = hashlib.sha256(purpose.encode()).digest()
    out = bytearray()
    while len(out) < n:
        seed = hashlib.sha256(seed).digest()
        out.extend(seed)
    return bytes(out[:n])


def qrng_floats(n: int, purpose: str) -> list[float]:
    """Return n floats in [0, 1) from QRNG-derived bytes."""
    raw = qrng_bytes(n * 4, purpose)
    return [struct.unpack(">I", raw[i*4:(i+1)*4])[0] / 0xFFFFFFFF for i in range(n)]


def qrng_normal(n: int, purpose: str, mu: float = 0.0, sigma: float = 1.0) -> list[float]:
    """Box-Muller transform on QRNG uniforms → N(mu, sigma)."""
    u = qrng_floats(n + (n % 2), purpose)  # need even count for box-muller pairs
    out = []
    for i in range(0, len(u) - 1, 2):
        u1, u2 = u[i], u[i + 1]
        if u1 < 1e-10:  # avoid log(0)
            u1 = 1e-10
        mag = math.sqrt(-2.0 * math.log(u1))
        z1 = mag * math.cos(2.0 * math.pi * u2)
        z2 = mag * math.sin(2.0 * math.pi * u2)
        out.append(mu + sigma * z1)
        out.append(mu + sigma * z2)
    return out[:n]


# ---------- Channel 1: gyro micro-tremor --------------------------------------

def gen_gyro_tremor(duration_sec: float, sample_rate_hz: int, purpose: str) -> dict:
    """3-axis gyro samples (rad/s). Realistic human hand-holding-phone signature.

    Spectrum: 4Hz (physiological) + 8Hz (essential tremor mode) + 1/f pink noise.
    Amplitudes from real-human Pixel 6a samples: ~0.005 rad/s peak per axis.
    """
    n = int(duration_sec * sample_rate_hz)
    # 3 independent noise series (x, y, z); each gets its own QRNG draw
    samples = []
    rand_x = qrng_normal(n, f"{purpose}/gyro/x", sigma=0.0015)
    rand_y = qrng_normal(n, f"{purpose}/gyro/y", sigma=0.0015)
    rand_z = qrng_normal(n, f"{purpose}/gyro/z", sigma=0.0015)
    # 1/f cumulative shaping (Brownian-bridge approximation of pink noise)
    pink_x, pink_y, pink_z = 0.0, 0.0, 0.0
    decay = 0.95
    for i in range(n):
        t = i / sample_rate_hz
        # Periodic components
        per_x = 0.0015 * math.sin(2 * math.pi * 4.2 * t) + 0.0010 * math.sin(2 * math.pi * 7.8 * t + 1.1)
        per_y = 0.0012 * math.sin(2 * math.pi * 4.6 * t + 0.4) + 0.0008 * math.sin(2 * math.pi * 8.4 * t)
        per_z = 0.0008 * math.sin(2 * math.pi * 5.1 * t) + 0.0005 * math.sin(2 * math.pi * 9.2 * t + 0.7)
        # Pink noise
        pink_x = decay * pink_x + (1 - decay) * rand_x[i] * 8
        pink_y = decay * pink_y + (1 - decay) * rand_y[i] * 8
        pink_z = decay * pink_z + (1 - decay) * rand_z[i] * 8
        samples.append([
            round(per_x + pink_x + rand_x[i] * 0.3, 6),
            round(per_y + pink_y + rand_y[i] * 0.3, 6),
            round(per_z + pink_z + rand_z[i] * 0.3, 6),
        ])
    return {
        "channel": "gyro_micro_tremor",
        "unit": "rad/s",
        "sample_rate_hz": sample_rate_hz,
        "duration_sec": duration_sec,
        "n_samples": n,
        "samples_xyz": samples,
        "stats": {
            "rms_x": round(math.sqrt(sum(s[0]**2 for s in samples) / n), 6),
            "rms_y": round(math.sqrt(sum(s[1]**2 for s in samples) / n), 6),
            "rms_z": round(math.sqrt(sum(s[2]**2 for s in samples) / n), 6),
        },
    }


# ---------- Channel 2: typing intervals ---------------------------------------

def gen_typing_intervals(n_keystrokes: int, purpose: str) -> dict:
    """Inter-keystroke intervals in ms. Log-normal(μ=5.2, σ=0.45) → median ~180ms.

    Add rare "thinking pauses" (10-30s) every ~30 keystrokes for word-boundary
    cognition delay.
    """
    base = qrng_normal(n_keystrokes, f"{purpose}/typing/log", mu=5.2, sigma=0.45)
    intervals_ms = []
    pause_decisions = qrng_floats(n_keystrokes, f"{purpose}/typing/pauses")
    for i, x in enumerate(base):
        ms = math.exp(x)
        ms = max(40.0, min(1200.0, ms))  # clip to plausible range
        # 3% chance of a thinking pause
        if pause_decisions[i] < 0.03:
            ms = ms * 50 + 5000  # 5-30s outlier
        intervals_ms.append(round(ms, 1))
    return {
        "channel": "typing_intervals",
        "unit": "ms",
        "n_keystrokes": n_keystrokes,
        "intervals_ms": intervals_ms,
        "stats": {
            "median_ms": round(sorted(intervals_ms)[n_keystrokes // 2], 1),
            "mean_ms": round(sum(intervals_ms) / n_keystrokes, 1),
            "min_ms": min(intervals_ms),
            "max_ms": max(intervals_ms),
            "n_pauses_over_5s": sum(1 for ms in intervals_ms if ms > 5000),
        },
    }


# ---------- Channel 3: dwell time ---------------------------------------------

def gen_dwell_times(n_screens: int, purpose: str) -> dict:
    """Per-screen dwell time in seconds. Gamma(k=2.5, θ=4.0) → mean ~10s."""
    u = qrng_floats(n_screens * 2, f"{purpose}/dwell")
    dwells = []
    for i in range(n_screens):
        # Sum of 2 exponentials = Erlang/Gamma(2, θ); we approximate gamma(2.5)
        e1 = -4.0 * math.log(max(u[i*2], 1e-10))
        e2 = -4.0 * math.log(max(u[i*2 + 1], 1e-10))
        dwell_sec = (e1 + e2) / 2
        # First-time-user consent boost: first 2 screens get 1.5x dwell
        if i < 2:
            dwell_sec *= 1.5
        dwells.append(round(dwell_sec, 2))
    return {
        "channel": "dwell_time",
        "unit": "seconds",
        "n_screens": n_screens,
        "dwell_sec_per_screen": dwells,
        "stats": {
            "total_sec": round(sum(dwells), 2),
            "mean_sec": round(sum(dwells) / n_screens, 2),
            "min_sec": min(dwells),
            "max_sec": max(dwells),
        },
    }


# ---------- Channel 4: swipe gestures -----------------------------------------

def gen_swipe_gestures(n_swipes: int, screen_w: int, screen_h: int, purpose: str) -> dict:
    """Each swipe = start (x,y), end (x,y), Bézier control points, ms duration.

    Real human swipes:
      - Start fast, decelerate (cubic ease-out)
      - Slight curve from index-finger pivot (control points offset 5-15% off the
        straight-line midpoint)
      - Duration: 150-450ms for short swipes, 450-900ms for full-screen swipes
    """
    rand = qrng_floats(n_swipes * 10, f"{purpose}/swipes")
    swipes = []
    for i in range(n_swipes):
        base = i * 10
        x0 = int(rand[base] * screen_w)
        y0 = int(rand[base + 1] * screen_h)
        x1 = int(rand[base + 2] * screen_w)
        y1 = int(rand[base + 3] * screen_h)
        dx = x1 - x0
        dy = y1 - y0
        dist = math.sqrt(dx*dx + dy*dy)
        # Duration scales with distance + ease-out
        duration_ms = max(150, min(900, int(150 + dist * 0.6 + rand[base + 4] * 150)))
        # Bezier control: midpoint + perpendicular curve
        mid_x = (x0 + x1) / 2
        mid_y = (y0 + y1) / 2
        # perpendicular vector (normalized)
        if dist > 0:
            perp_x = -dy / dist
            perp_y = dx / dist
        else:
            perp_x = perp_y = 0
        curve = (rand[base + 5] - 0.5) * 0.15 * dist  # ±7.5% of dist
        c_x = int(mid_x + perp_x * curve)
        c_y = int(mid_y + perp_y * curve)
        swipes.append({
            "start": [x0, y0],
            "end": [x1, y1],
            "bezier_control": [c_x, c_y],
            "duration_ms": duration_ms,
            "distance_px": round(dist, 1),
        })
    return {
        "channel": "swipe_gestures",
        "n_swipes": n_swipes,
        "screen_resolution": [screen_w, screen_h],
        "swipes": swipes,
        "stats": {
            "mean_duration_ms": round(sum(s["duration_ms"] for s in swipes) / n_swipes, 1),
            "mean_distance_px": round(sum(s["distance_px"] for s in swipes) / n_swipes, 1),
            "all_have_curve": all(s["bezier_control"] != [(s["start"][0]+s["end"][0])//2, (s["start"][1]+s["end"][1])//2] for s in swipes),
        },
    }


# ---------- Profile assembly --------------------------------------------------

def build_profile(class_name: str, duration_sec: float = 30.0) -> dict:
    """Bundle all 4 channels into one behavioral profile."""
    purpose = f"sinister-os-mobile/sandbox/behavioral/{class_name}/2026-05-24"
    return {
        "profile_class": class_name,
        "purpose_label": purpose,
        "generated_at_utc": "2026-05-24T17:Xz",  # iteration timestamp
        "duration_sec": duration_sec,
        "channels": {
            "gyro": gen_gyro_tremor(duration_sec=duration_sec, sample_rate_hz=50, purpose=purpose),
            "typing": gen_typing_intervals(n_keystrokes=24, purpose=purpose),
            "dwell": gen_dwell_times(n_screens=6, purpose=purpose),
            "swipes": gen_swipe_gestures(n_swipes=8, screen_w=1080, screen_h=2400, purpose=purpose),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", default="profiles", type=Path)
    ap.add_argument("--classes", nargs="+", default=["fast_typer", "slow_typer", "anxious_consent_reader", "casual_swiper"])
    ap.add_argument("--duration-sec", default=30.0, type=float)
    args = ap.parse_args()

    out_dir = Path(__file__).resolve().parent / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    for cls in args.classes:
        profile = build_profile(cls, duration_sec=args.duration_sec)
        out_path = out_dir / f"{cls}.json"
        out_path.write_text(json.dumps(profile, indent=2))
        ch = profile["channels"]
        print(
            f"[behavioral] {cls}: "
            f"gyro {ch['gyro']['n_samples']} samples, "
            f"typing median {ch['typing']['stats']['median_ms']}ms, "
            f"dwell total {ch['dwell']['stats']['total_sec']}s, "
            f"{ch['swipes']['n_swipes']} swipes "
            f"-> {out_path.name}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
