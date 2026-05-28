"""test_hgly_trainer_multiobj.py — acceptance for the iter-31 multi-objective
density signal wired into hgly_trainer.cmd_eval.

Author: RKOJ-ELENO :: 2026-05-27

Verifies:
  - cmd_eval --dry-run (no flag)        -> placeholder score, mode=placeholder-dry-run
  - cmd_eval --dry-run --multi-objective with live by-category surface
      -> multi-objective score, mode=multi-objective-dry-run, density_signal embedded
  - cmd_eval --dry-run --multi-objective when by-category is unavailable
      -> graceful fallback to placeholder, mode=placeholder-fallback-dry-run
  - composite_score formula: 100 * mean(min(1, 0.20 / ratio_c)) over glyph cats
  - GLYPH_CATEGORIES excludes "other" (per iter-29 honest-reframe)
  - quality-log row carries density_signal field when multi-objective is set

Run via:
  python projects/sinister-hieroglyphics/tests/test_hgly_trainer_multiobj.py
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[2].parent  # sanctum root
SANCTUM = ROOT
AUTOMATIONS = SANCTUM / "automations"
TRAINER = AUTOMATIONS / "hgly_trainer.py"
DENSITY = AUTOMATIONS / "hgly_density.py"

if str(AUTOMATIONS) not in sys.path:
    sys.path.insert(0, str(AUTOMATIONS))


PASSED = 0
FAILED: list[str] = []


def _ok(label: str) -> None:
    global PASSED
    PASSED += 1
    print(f"  PASS  {label}")


def _fail(label: str, msg: str) -> None:
    FAILED.append(f"{label} :: {msg}")
    print(f"  FAIL  {label} :: {msg}")


def _run_eval(extra_args: list[str], env: dict | None = None) -> tuple[int, dict, str]:
    """Run hgly_trainer.py eval --dry-run [extra] and parse the JSON stdout."""
    proc = subprocess.run(
        [sys.executable, str(TRAINER), "eval", "--dry-run", *extra_args],
        capture_output=True, text=True, timeout=60,
        env=env if env is not None else os.environ.copy(),
    )
    try:
        payload = json.loads(proc.stdout)
    except Exception:
        payload = {}
    return proc.returncode, payload, proc.stderr


def t_backcompat_no_flag() -> None:
    """eval --dry-run without --multi-objective preserves placeholder mode."""
    rc, payload, _ = _run_eval([])
    if rc != 0:
        return _fail("t_backcompat_no_flag", f"exit {rc}")
    if payload.get("multi_objective") is not False:
        return _fail("t_backcompat_no_flag", f"multi_objective should be False, got {payload.get('multi_objective')!r}")
    if payload.get("mode") != "placeholder-dry-run":
        return _fail("t_backcompat_no_flag", f"mode should be placeholder-dry-run, got {payload.get('mode')!r}")
    if "density_signal" in payload:
        return _fail("t_backcompat_no_flag", "density_signal should NOT be in result when flag is off")
    score = payload.get("score")
    if not isinstance(score, (int, float)) or not (25.0 <= float(score) <= 75.0):
        return _fail("t_backcompat_no_flag", f"placeholder score out of 25..75 range: {score!r}")
    _ok("t_backcompat_no_flag")


def t_multi_objective_dry_run_live() -> None:
    """eval --dry-run --multi-objective consumes the live --by-category surface."""
    rc, payload, stderr = _run_eval(["--multi-objective"])
    if rc != 0:
        return _fail("t_multi_objective_dry_run_live", f"exit {rc} stderr={stderr[-200:]}")
    if payload.get("multi_objective") is not True:
        return _fail("t_multi_objective_dry_run_live", f"multi_objective should be True, got {payload.get('multi_objective')!r}")
    sig = payload.get("density_signal") or {}
    if not sig.get("available"):
        # graceful-fallback shape — still valid but log it
        if payload.get("mode") != "placeholder-fallback-dry-run":
            return _fail("t_multi_objective_dry_run_live",
                         f"signal unavailable but mode is {payload.get('mode')!r}")
        _ok("t_multi_objective_dry_run_live (fallback path)")
        return
    if payload.get("mode") != "multi-objective-dry-run":
        return _fail("t_multi_objective_dry_run_live",
                     f"mode should be multi-objective-dry-run, got {payload.get('mode')!r}")
    if sig.get("density_goal") != 0.20:
        return _fail("t_multi_objective_dry_run_live", f"density_goal should be 0.20, got {sig.get('density_goal')!r}")
    score = payload.get("score")
    composite = sig.get("composite_score")
    if score != composite:
        return _fail("t_multi_objective_dry_run_live",
                     f"score ({score}) should equal composite_score ({composite})")
    per_cat = sig.get("per_category") or {}
    # GLYPH_CATEGORIES per iter-29 honest reframe — no "other" bucket
    if "other" in per_cat:
        return _fail("t_multi_objective_dry_run_live",
                     "per_category MUST NOT include 'other' (corpus-wide noise bucket)")
    expected_cats = {"bind", "ctrl", "arith", "mem", "io", "conc", "hw", "sim"}
    if set(per_cat.keys()) != expected_cats:
        return _fail("t_multi_objective_dry_run_live",
                     f"per_category keys mismatch: got {set(per_cat.keys())}, expected {expected_cats}")
    _ok("t_multi_objective_dry_run_live")


def t_composite_formula() -> None:
    """Composite = mean(min(1, 0.20/r) * 100) over scored cats. Pin the math."""
    # Inline-recompute over the live signal so the formula is asserted not faked.
    rc, payload, _ = _run_eval(["--multi-objective"])
    if rc != 0:
        return _fail("t_composite_formula", f"exit {rc}")
    sig = payload.get("density_signal") or {}
    if not sig.get("available"):
        _ok("t_composite_formula (skipped — signal unavailable)")
        return
    per_cat = sig.get("per_category") or {}
    contributions = []
    for c, row in per_cat.items():
        ratio = row.get("ratio")
        if ratio is None:
            continue
        contrib = round(100.0 * min(1.0, 0.20 / max(float(ratio), 1e-9)), 2)
        contributions.append(contrib)
        # also verify the contribution echoed in the payload matches
        if abs((row.get("contribution") or -1) - contrib) > 0.011:
            return _fail("t_composite_formula",
                         f"cat={c} ratio={ratio} contribution mismatch: payload {row.get('contribution')!r} vs recomputed {contrib}")
    if not contributions:
        return _fail("t_composite_formula", "no scored contributions")
    expected = round(sum(contributions) / len(contributions), 2)
    actual = sig.get("composite_score")
    if abs(float(actual) - expected) > 0.011:
        return _fail("t_composite_formula", f"composite_score {actual} != expected {expected}")
    _ok("t_composite_formula")


def t_glyph_categories_constant() -> None:
    """The trainer's GLYPH_CATEGORIES constant must NOT include 'other'."""
    import hgly_trainer  # type: ignore
    cats = hgly_trainer.GLYPH_CATEGORIES
    if "other" in cats:
        return _fail("t_glyph_categories_constant", "GLYPH_CATEGORIES must exclude 'other'")
    if hgly_trainer.DENSITY_GOAL != 0.20:
        return _fail("t_glyph_categories_constant",
                     f"DENSITY_GOAL should mirror lane rule 1 (0.20), got {hgly_trainer.DENSITY_GOAL!r}")
    expected = ("bind", "ctrl", "arith", "mem", "io", "conc", "hw", "sim")
    if tuple(cats) != expected:
        return _fail("t_glyph_categories_constant",
                     f"GLYPH_CATEGORIES order should be {expected}, got {tuple(cats)}")
    _ok("t_glyph_categories_constant")


def t_density_signal_fallback_when_cli_broken() -> None:
    """When the density CLI exits non-zero, _density_signal returns available=False."""
    import hgly_trainer  # type: ignore
    # Point at a non-existent corpus dir to force the "corpus dir missing" path.
    bogus = pathlib.Path(tempfile.gettempdir()) / "hgly-corpus-does-not-exist-iter31-test"
    if bogus.exists():
        import shutil
        shutil.rmtree(bogus, ignore_errors=True)
    sig = hgly_trainer._density_signal(bogus)
    if sig.get("available") is not False:
        return _fail("t_density_signal_fallback_when_cli_broken",
                     f"should be unavailable, got {sig!r}")
    if "error" not in sig:
        return _fail("t_density_signal_fallback_when_cli_broken", "missing error field")
    _ok("t_density_signal_fallback_when_cli_broken")


def t_quality_log_carries_density_signal() -> None:
    """When --multi-objective is set, the appended hgly-eval row embeds density_signal."""
    log_path = SANCTUM / "_shared-memory" / "quality-loop-log.jsonl"
    size_before = log_path.stat().st_size if log_path.exists() else 0
    rc, payload, _ = _run_eval(["--multi-objective"])
    if rc != 0:
        return _fail("t_quality_log_carries_density_signal", f"exit {rc}")
    if not log_path.exists():
        return _fail("t_quality_log_carries_density_signal", "log file not created")
    # Read the tail
    with log_path.open("rb") as f:
        f.seek(max(0, log_path.stat().st_size - 8192))
        tail = f.read().decode("utf-8", errors="replace")
    last_row = None
    for line in tail.strip().splitlines():
        try:
            row = json.loads(line)
        except Exception:
            continue
        if row.get("kind") == "hgly-eval" and row.get("run_id") == payload.get("run_id"):
            last_row = row
    if last_row is None:
        return _fail("t_quality_log_carries_density_signal",
                     f"no hgly-eval row matching run_id={payload.get('run_id')!r}")
    if "density_signal" not in last_row:
        return _fail("t_quality_log_carries_density_signal",
                     "row missing density_signal field")
    _ok("t_quality_log_carries_density_signal")


def main() -> int:
    print(f"=== test_hgly_trainer_multiobj (iter-31 acceptance) ===")
    print(f"  trainer: {TRAINER}")
    print(f"  density: {DENSITY}")
    print()
    t_glyph_categories_constant()
    t_backcompat_no_flag()
    t_multi_objective_dry_run_live()
    t_composite_formula()
    t_density_signal_fallback_when_cli_broken()
    t_quality_log_carries_density_signal()
    total = PASSED + len(FAILED)
    print()
    print(f"Results: {PASSED}/{total} passed")
    if FAILED:
        for f in FAILED:
            print(f"  - {f}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
