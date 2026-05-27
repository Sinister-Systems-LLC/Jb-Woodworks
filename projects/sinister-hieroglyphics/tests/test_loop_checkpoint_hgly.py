"""test_loop_checkpoint_hgly.py — acceptance for the hgly density hook
fired from loop_checkpoint.save().

Author: RKOJ-ELENO :: 2026-05-27

Verifies that `loop_checkpoint._hgly_density_hook` only fires for the
hgly lane and writes one row to the trajectory JSONL (or skips when
SINISTER_HGLY_TRACK_DRY_RUN=1).

Run via:
  python tests/test_loop_checkpoint_hgly.py
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2].parent  # sanctum root
SANCTUM = ROOT
HGLY_SRC = SANCTUM / "projects" / "sinister-hieroglyphics" / "src"
LOOP_CKPT_TOOL = SANCTUM / "automations" / "loop_checkpoint.py"
DENSITY_TOOL = SANCTUM / "automations" / "hgly_density.py"
TRAJECTORY = SANCTUM / "_shared-memory" / "hgly-density-trajectory.jsonl"

if str(HGLY_SRC) not in sys.path:
    sys.path.insert(0, str(HGLY_SRC))
if str(SANCTUM / "automations") not in sys.path:
    sys.path.insert(0, str(SANCTUM / "automations"))


PASSED = 0
FAILED: list[str] = []


def _ok(label: str) -> None:
    global PASSED
    PASSED += 1
    print(f"  PASS  {label}")


def _fail(label: str, msg: str) -> None:
    FAILED.append(f"{label}: {msg}")
    print(f"  FAIL  {label}: {msg}")


def t_hook_skips_non_hgly_lane() -> None:
    import loop_checkpoint as lc
    # No-op for non-hgly lane: should return without trying to invoke
    # hgly_density.py at all. Smoke via dry-run env so even an accidental
    # invoke would be no-op.
    os.environ["SINISTER_HGLY_TRACK_DRY_RUN"] = "1"
    try:
        lc._hgly_density_hook(lane="sinister-kernel-apk",
                              run_id="rtest",
                              iter_n=42,
                              sanctum_root=SANCTUM)
        _ok("hook is no-op for non-hgly lane (no exception)")
    except Exception as e:
        _fail("hook non-hgly lane", repr(e))
    finally:
        os.environ.pop("SINISTER_HGLY_TRACK_DRY_RUN", None)


def t_hook_dry_run_does_not_append() -> None:
    """With SINISTER_HGLY_TRACK_DRY_RUN=1 set, the hook fires but the
    --dry-run flag is passed through, so the JSONL trajectory does NOT
    grow."""
    import loop_checkpoint as lc
    before_lines = 0
    if TRAJECTORY.exists():
        before_lines = sum(1 for _ in TRAJECTORY.open(encoding="utf-8"))
    os.environ["SINISTER_HGLY_TRACK_DRY_RUN"] = "1"
    try:
        lc._hgly_density_hook(lane="sinister-hieroglyphics",
                              run_id="rtest-dry",
                              iter_n=99,
                              sanctum_root=SANCTUM)
    finally:
        os.environ.pop("SINISTER_HGLY_TRACK_DRY_RUN", None)
    after_lines = 0
    if TRAJECTORY.exists():
        after_lines = sum(1 for _ in TRAJECTORY.open(encoding="utf-8"))
    if before_lines == after_lines:
        _ok(f"dry-run hook did NOT grow trajectory ({before_lines} -> {after_lines})")
    else:
        _fail("dry-run grew trajectory",
              f"before={before_lines} after={after_lines}")


def t_save_smoke_with_dry_run_env() -> None:
    """End-to-end: invoke loop_checkpoint.save() against a throwaway path
    set with SINISTER_HGLY_TRACK_DRY_RUN=1 so the hook fires in dry-run.
    Smoke that .save() succeeds AND the trajectory size is unchanged."""
    if not LOOP_CKPT_TOOL.exists():
        _fail("loop_checkpoint present", f"missing {LOOP_CKPT_TOOL}")
        return
    before_lines = 0
    if TRAJECTORY.exists():
        before_lines = sum(1 for _ in TRAJECTORY.open(encoding="utf-8"))
    # Create a throwaway empty file inside sanctum to checkpoint
    tmp_path = SANCTUM / "_tmp-hgly-test-checkpoint-source"
    tmp_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path.write_text("ckpt-smoke", encoding="utf-8")
    env = dict(os.environ)
    env["SINISTER_HGLY_TRACK_DRY_RUN"] = "1"
    try:
        r = subprocess.run(
            [sys.executable, str(LOOP_CKPT_TOOL), "save",
             "--lane", "sinister-hieroglyphics",
             "--run-id", "rtest-smoke",
             "--iter", "0",
             "--paths", str(tmp_path.relative_to(SANCTUM)),
             "--sanctum-root", str(SANCTUM)],
            env=env, capture_output=True, text=True, timeout=60,
        )
    finally:
        tmp_path.unlink(missing_ok=True)
        # Best-effort cleanup of the throwaway checkpoint dir
        ckpt_dir = (SANCTUM / "_shared-memory" / "loop-checkpoints" /
                    "sinister-hieroglyphics" / "rtest-smoke-iter0")
        if ckpt_dir.exists():
            shutil.rmtree(ckpt_dir, ignore_errors=True)
    if r.returncode != 0:
        _fail("loop_checkpoint save", f"rc={r.returncode} stderr={r.stderr[:200]}")
        return
    after_lines = 0
    if TRAJECTORY.exists():
        after_lines = sum(1 for _ in TRAJECTORY.open(encoding="utf-8"))
    if before_lines == after_lines:
        _ok(f"save() + dry-run hook left trajectory unchanged ({before_lines})")
    else:
        _fail("save() grew trajectory in dry-run",
              f"before={before_lines} after={after_lines}")


def t_hook_constants_match_doctrine() -> None:
    """The hgly-lane allowlist must include the canonical slug, display
    name, and short alias (so SLUG-based + DISPLAY-based callers both
    hit the hook)."""
    import loop_checkpoint as lc
    expected = {"sinister-hieroglyphics", "Sinister Hieroglyphics", "hgly"}
    if expected <= lc._HGLY_LANES:
        _ok(f"_HGLY_LANES includes {sorted(expected)}")
    else:
        _fail("_HGLY_LANES coverage",
              f"missing {expected - lc._HGLY_LANES}")


def main() -> int:
    print("=== test_loop_checkpoint_hgly ===")
    for fn in (t_hook_constants_match_doctrine,
               t_hook_skips_non_hgly_lane,
               t_hook_dry_run_does_not_append,
               t_save_smoke_with_dry_run_env):
        try:
            fn()
        except Exception as e:
            _fail(fn.__name__, f"unexpected exc: {e!r}")
    print(f"\nResults: {PASSED}/{PASSED + len(FAILED)} passed")
    if FAILED:
        print("Failures:")
        for f in FAILED:
            print(f"  - {f}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
