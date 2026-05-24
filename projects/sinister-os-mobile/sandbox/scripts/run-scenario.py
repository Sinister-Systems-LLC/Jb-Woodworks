"""Scenario runner — composes a full account-creation test scenario.

RKOJ-ELENO :: 2026-05-24 :: GPL-3.0-or-later

One scenario = one tuple of:
  * device_class    (cvd_clean | physical_locked | physical_unlocked_dev |
                     rooted_clean | cvd_dev) — from fingerprints/corpus.json
  * identity        (device_id + android_id + imei + mac + serial) — quantum-derived
  * keybox          (sha256 reference to a manifest row) — for PI attestation
  * behavioral      (fast_typer | slow_typer | anxious_consent_reader |
                     casual_swiper) — from behavioral/profiles/
  * target_action   (snap_signup | snap_login | snap_addfriend | snap_send)

Output: one JSON ledger row appended to sandbox/.scenario-ledger.jsonl with
the full scenario spec + (when executed against a real cvd) the observed
results — per-step latencies, PI verdict, account creation success, etc.

Modes:
  --dry-run       Just emit the scenario JSON; do not invoke cvd
  --mock-cvd      Run the scenario flow against the MOCK_CVD adb shim
  --real-cvd      Run against a booted cvd at 0.0.0.0:6520 (operator action)

Fan-out:
  --fanout N      Generate + record N scenario rows in one invocation
                  (random device-class + behavioral combinations)
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import random
import subprocess
import sys
import time
from pathlib import Path

SANDBOX_ROOT = Path(__file__).resolve().parents[1]
FINGERPRINTS = SANDBOX_ROOT / "fingerprints" / "corpus.json"
KEYBOX_MANIFEST = SANDBOX_ROOT / "keybox" / "manifest.json"
BEHAVIORAL_DIR = SANDBOX_ROOT / "behavioral" / "profiles"
LEDGER = SANDBOX_ROOT / ".scenario-ledger.jsonl"

TARGET_ACTIONS = ("snap_signup", "snap_login", "snap_addfriend", "snap_send")


def utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_corpus() -> list[dict]:
    if not FINGERPRINTS.exists():
        sys.exit("FAIL: fingerprints/corpus.json missing — run fingerprints/generate.py first")
    return json.loads(FINGERPRINTS.read_text())


def load_keyboxes() -> list[dict]:
    if not KEYBOX_MANIFEST.exists():
        return []
    data = json.loads(KEYBOX_MANIFEST.read_text(encoding="utf-8"))
    return [k for k in data.get("keyboxes", []) if k.get("status") == "active"]


def load_behavioral_profiles() -> list[dict]:
    if not BEHAVIORAL_DIR.exists():
        sys.exit(f"FAIL: {BEHAVIORAL_DIR} missing — run behavioral/generate.py first")
    profiles = []
    for f in sorted(BEHAVIORAL_DIR.glob("*.json")):
        profiles.append(json.loads(f.read_text()))
    if not profiles:
        sys.exit("FAIL: no behavioral profiles — run behavioral/generate.py first")
    return profiles


def compose_scenario(
    *,
    device_class: str | None = None,
    behavioral_class: str | None = None,
    target_action: str = "snap_signup",
    rng: random.Random,
) -> dict:
    """Build one scenario tuple. Picks random class/behavioral if not specified."""
    corpus = load_corpus()
    keyboxes = load_keyboxes()
    behavioral_profiles = load_behavioral_profiles()

    if device_class is None:
        device_class = rng.choice(list({c["class_name"] for c in corpus}))
    candidates = [c for c in corpus if c["class_name"] == device_class]
    if not candidates:
        raise ValueError(f"no fingerprint with class_name={device_class!r} in corpus")
    fp = rng.choice(candidates)

    if behavioral_class is None:
        behavioral_class = rng.choice([p["profile_class"] for p in behavioral_profiles])
    bp = next((p for p in behavioral_profiles if p["profile_class"] == behavioral_class), None)
    if not bp:
        raise ValueError(f"no behavioral profile with profile_class={behavioral_class!r}")

    keybox_ref = None
    if keyboxes:
        kb = rng.choice(keyboxes)
        keybox_ref = {
            "sha256": kb["sha256"],
            "device_id": kb.get("device_id"),
            "primary_key_algorithm": kb.get("primary_key_algorithm"),
        }

    return {
        "scenario_id": f"scen-{int(time.time() * 1000)}-{rng.randint(0, 0xFFFF):04x}",
        "composed_at_utc": utc_now(),
        "target_action": target_action,
        "device": {
            "class_name": fp["class_name"],
            "build_fingerprint": fp.get("build_fingerprint"),
            "product_model": fp.get("product_model"),
            "cpu_abi": fp.get("cpu_abi"),
            "bootloader_locked": fp.get("bootloader_locked"),
            "verified_boot": fp.get("verified_boot"),
            "developer_options": fp.get("developer_options"),
            "tee_backend": fp.get("tee_backend"),
            "identity": {
                "device_id": fp.get("device_id"),
                "android_id": fp.get("android_id"),
                "imei": fp.get("imei"),
                "mac_address": fp.get("mac_address"),
                "serial_number": fp.get("serial_number"),
            },
        },
        "keybox": keybox_ref,
        "behavioral": {
            "profile_class": bp["profile_class"],
            "channels_summary": {
                "gyro_rms_xyz": [
                    bp["channels"]["gyro"]["stats"]["rms_x"],
                    bp["channels"]["gyro"]["stats"]["rms_y"],
                    bp["channels"]["gyro"]["stats"]["rms_z"],
                ],
                "typing_median_ms": bp["channels"]["typing"]["stats"]["median_ms"],
                "dwell_total_sec": bp["channels"]["dwell"]["stats"]["total_sec"],
                "swipe_count": bp["channels"]["swipes"]["n_swipes"],
            },
        },
        "expected_pi_verdict": _expected_pi_verdict(fp),
    }


def _expected_pi_verdict(fp: dict) -> str:
    """Predict Snapchat PI verdict from the device class + keybox combo.

    See sandbox/fingerprints/generate.py PROFILES catalog for the per-class
    expected verdicts.
    """
    cls = fp["class_name"]
    if cls == "physical_locked":
        return "MEETS_DEVICE_INTEGRITY"
    if cls == "cvd_clean":
        return "REJECT_sw_emu_tee_no_keybox_inject"
    if cls == "physical_unlocked_dev":
        return "ACCEPT_WITH_FLAG_review_queue"
    if cls == "rooted_clean":
        return "VARIABLE_magisk_hidden_may_pass_surface"
    if cls == "cvd_dev":
        return "REJECT_dev_opts_on_emu"
    return "UNKNOWN_class"


def execute_scenario(scenario: dict, *, mode: str) -> dict:
    """Execute the scenario against the configured execution mode.

    Returns a dict of observed results. mode in {dry, mock, real}.
    """
    started_utc = utc_now()
    result: dict = {
        "execution_mode": mode,
        "started_at_utc": started_utc,
        "steps": [],
    }
    if mode == "dry":
        result["steps"].append({"step": "dry-run", "status": "noop", "duration_ms": 0})
        result["completed_at_utc"] = utc_now()
        result["overall_status"] = "dry_run_ok"
        return result

    # mock + real share the same step list; conftest's adb shim handles routing
    sys.path.insert(0, str(SANDBOX_ROOT / "tests"))
    from conftest import Adb  # noqa: E402

    adb = Adb(mock=(mode == "mock"))

    # Step 1: device reachability + props match scenario
    t0 = time.monotonic()
    reachable = adb.reachable()
    result["steps"].append({
        "step": "adb_reachable", "status": "ok" if reachable else "fail",
        "duration_ms": int((time.monotonic() - t0) * 1000),
    })
    if not reachable:
        result["overall_status"] = "device_unreachable"
        result["completed_at_utc"] = utc_now()
        return result

    # Step 2: read actual device props + diff vs scenario
    t0 = time.monotonic()
    actual_fp = adb.getprop("ro.build.fingerprint")
    actual_locked = adb.getprop("ro.boot.flash.locked")
    actual_vb = adb.getprop("ro.boot.verifiedbootstate")
    expected_locked = scenario["device"]["bootloader_locked"]
    expected_vb = scenario["device"]["verified_boot"]
    diffs = []
    if actual_locked != expected_locked:
        diffs.append(f"bootloader_locked: actual={actual_locked!r} expected={expected_locked!r}")
    if actual_vb != expected_vb:
        diffs.append(f"verified_boot: actual={actual_vb!r} expected={expected_vb!r}")
    result["steps"].append({
        "step": "props_diff", "status": "match" if not diffs else "diff",
        "diffs": diffs,
        "actual_build_fingerprint": actual_fp,
        "duration_ms": int((time.monotonic() - t0) * 1000),
    })

    # Step 3: PI surface presence (mock returns canned PI service handle)
    t0 = time.monotonic()
    pi_proc = adb.shell("pgrep -f keystore2").stdout.strip()
    result["steps"].append({
        "step": "pi_surface_present", "status": "ok" if pi_proc.isdigit() else "fail",
        "duration_ms": int((time.monotonic() - t0) * 1000),
    })

    # Step 4: Snapchat package check (mock has it; real-cvd requires operator-pushed APK)
    t0 = time.monotonic()
    pkg = adb.shell("pm list packages -f com.snapchat.android").stdout
    result["steps"].append({
        "step": "snapchat_pkg_installed",
        "status": "ok" if "com.snapchat.android" in pkg else "skip",
        "duration_ms": int((time.monotonic() - t0) * 1000),
    })

    # Step 5: account-list pre-check (don't actually create accounts in this runner;
    # account creation lives in sinister-snap-api-quantum)
    t0 = time.monotonic()
    accts = adb.shell("cmd account list").stdout
    result["steps"].append({
        "step": "account_list_baseline",
        "status": "ok",
        "snapchat_accounts": accts.count("snapchat"),
        "duration_ms": int((time.monotonic() - t0) * 1000),
    })

    result["completed_at_utc"] = utc_now()
    result["overall_status"] = "executed"
    return result


def append_to_ledger(scenario: dict, result: dict) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    row = {**scenario, "observed": result}
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--device-class", default=None,
                    help="Pin a device class (default: random from corpus)")
    ap.add_argument("--behavioral", default=None,
                    help="Pin a behavioral profile (default: random)")
    ap.add_argument("--target-action", default="snap_signup", choices=TARGET_ACTIONS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--fanout", type=int, default=1)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--mock-cvd", action="store_true")
    mode.add_argument("--real-cvd", action="store_true")
    ap.add_argument("--print", action="store_true", help="Print each scenario row to stdout")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    execution_mode = "mock" if args.mock_cvd or os.environ.get("MOCK_CVD") == "1" else (
        "real" if args.real_cvd else "dry"
    )

    print(f"[scenario] mode={execution_mode} fanout={args.fanout}", file=sys.stderr)
    for i in range(args.fanout):
        scenario = compose_scenario(
            device_class=args.device_class,
            behavioral_class=args.behavioral,
            target_action=args.target_action,
            rng=rng,
        )
        result = execute_scenario(scenario, mode=execution_mode)
        append_to_ledger(scenario, result)
        if args.print:
            print(json.dumps({"scenario": scenario, "observed": result}, indent=2))
        else:
            print(
                f"[scenario] {i+1}/{args.fanout} {scenario['scenario_id']} "
                f"class={scenario['device']['class_name']} "
                f"behav={scenario['behavioral']['profile_class']} "
                f"expected_pi={scenario['expected_pi_verdict']} "
                f"status={result['overall_status']}",
                file=sys.stderr,
            )
    print(f"[scenario] {args.fanout} rows appended to {LEDGER}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
