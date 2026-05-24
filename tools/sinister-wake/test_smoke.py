"""sinister-wake :: smoke test (iter 9 e2e validation).

Author: RKOJ-ELENO :: 2026-05-24

Tests WakeDispatcher lifecycle without spawning real bots. Uses a tiny
subprocess stub that prints 'ready' to stderr then sleeps.

Run: python test_smoke.py
Exit: 0 if all tests PASS, 1 if any fail.
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

# Add this dir to path so we can import wake_dispatcher
sys.path.insert(0, str(Path(__file__).resolve().parent))
from wake_dispatcher import WakeDispatcher  # noqa: E402

FAIL = []
PASS = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        PASS.append(name)
        print(f"  [OK]   {name}" + (f" :: {detail}" if detail else ""))
    else:
        FAIL.append(name)
        print(f"  [FAIL] {name}" + (f" :: {detail}" if detail else ""))


def main() -> int:
    print("=== sinister-wake smoke tests ===\n")

    d = WakeDispatcher()
    check("config loaded", d.config_path.exists(), str(d.config_path))
    check("hot_bots populated", len(d.hot_bots) >= 2, ", ".join(sorted(d.hot_bots)))
    check("global_idle_ttl > 0", d.global_idle_ttl > 0, f"{d.global_idle_ttl}s")

    # Test 1: peek without wake on a known bot
    print("\n--- Test 1: peek without wake ---")
    h = d.bus_health_target("auditor")
    check("peek returns dict", isinstance(h, dict))
    check("peek state=cold", h.get("state") == "cold", h.get("state"))
    check("peek doesn't spawn", h.get("pid") is None)

    # Test 2: _wait_ready with mock subprocess
    print("\n--- Test 2: _wait_ready with mock 'ready' stub ---")
    proc = subprocess.Popen(
        [sys.executable, "-c", "import sys, time; sys.stderr.write('ready\\n'); sys.stderr.flush(); time.sleep(10)"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    ready = d._wait_ready(proc, timeout_s=3.0)
    check("wait_ready detects 'ready' on stderr", ready)
    check("proc alive after ready", proc.poll() is None)

    # Test 3: idle_sweep terminates expired bots
    print("\n--- Test 3: idle_sweep cleanup ---")
    d.subprocs["test-stub"] = proc
    d.alive_until["test-stub"] = time.time() - 1  # already expired
    actions = d.idle_sweep()
    check("idle_sweep returns dict", isinstance(actions, dict))
    check("expired bot was acted on", "test-stub" in actions, str(actions))
    check("test-stub removed from subprocs", "test-stub" not in d.subprocs)
    check("test-stub removed from alive_until", "test-stub" not in d.alive_until)

    # Test 4: hot_bots survive idle_sweep
    print("\n--- Test 4: hot_bots immortal ---")
    hot_proc = subprocess.Popen(
        [sys.executable, "-c", "import sys, time; sys.stderr.write('ready\\n'); sys.stderr.flush(); time.sleep(10)"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    d._wait_ready(hot_proc, timeout_s=3.0)
    d.subprocs["custodian"] = hot_proc  # in HOT_BOTS
    d.alive_until["custodian"] = time.time() - 1  # also "expired"
    actions = d.idle_sweep()
    check("hot bot was kept", actions.get("custodian") == "hot-keep", str(actions))
    check("hot bot still in subprocs", "custodian" in d.subprocs)

    # Cleanup
    print("\n--- Cleanup ---")
    sd = d.shutdown_all()
    check("shutdown_all returns dict", isinstance(sd, dict))

    # Wait for processes to actually terminate
    time.sleep(0.5)

    print(f"\n=== Result: PASS={len(PASS)} FAIL={len(FAIL)} ===")
    if FAIL:
        for f in FAIL:
            print(f"  FAILED: {f}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
