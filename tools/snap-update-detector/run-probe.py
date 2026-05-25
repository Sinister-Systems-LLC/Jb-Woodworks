# Author: RKOJ-ELENO :: 2026-05-24
#
# run-probe.py -- Snap auto-update Phase 2 orchestrator.
#
# What it does:
#   Drives the Phase 2 step of the Snap auto-update pipeline:
#     1. Verifies frida + adb are on PATH and the cvd device is reachable.
#     2. Installs the freshly-acquired Snap APK on the cvd emulator.
#     3. Launches Snap and waits for class loading.
#     4. Attaches Frida and runs frida-probe.js to enumerate loaded classes
#        and match the three known shape patterns (kiib_zck / m0l / hlm).
#     5. Parses the probe JSON (carved between PROBE_OUTPUT_START/END markers).
#     6. Picks the top candidate per pattern, downgrades overall confidence
#        when any pattern is ambiguous (>1 HIGH match) or missing (0 matches).
#     7. Writes hooks/v<snap-version>-hooks.json (atomic) with
#        validation_status="pending" for Phase 3 to validate.
#
# Composition:
#   - Phase 1 (acquire-snap-apk.py) produces the APK consumed via --apk-path.
#   - Phase 3 (smoke-test-hooks.py) reads the hooks file and flips
#     validation_status from "pending" to "validated" or "rejected".
#
# Usage:
#   python run-probe.py --apk-path acquired/snap-13.89.0.5.apk \
#                       --cvd-name cvd-1 --snap-version 13.89.0.5
#
# Dry-run (skips all device I/O; emits synthetic candidates for logic testing):
#   python run-probe.py --apk-path /nonexistent.apk --cvd-name cvd-1 \
#                       --snap-version 13.89.0.5 --dry-run

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
FRIDA_PROBE_JS = SCRIPT_DIR / "frida-probe.js"
DEFAULT_HOOKS_DIR = SCRIPT_DIR / "hooks"
PROBE_START_MARKER = "===PROBE_OUTPUT_START==="
PROBE_END_MARKER = "===PROBE_OUTPUT_END==="
SNAP_PKG = "com.snapchat.android"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def die(code: int, msg: str) -> None:
    sys.stderr.write("[run-probe] ERROR: " + msg + "\n")
    sys.exit(code)


def which_or_die(binary: str, exit_code: int) -> str:
    path = shutil.which(binary)
    if not path:
        die(exit_code, binary + " not found on PATH")
    return path  # type: ignore[return-value]


def preflight(cvd_name: str) -> None:
    which_or_die("frida", 2)
    which_or_die("adb", 2)
    try:
        r = subprocess.run(
            ["frida", "--version"], capture_output=True, text=True, timeout=10
        )
        if r.returncode != 0:
            die(2, "frida --version failed: " + (r.stderr or "").strip())
    except subprocess.TimeoutExpired:
        die(2, "frida --version timed out")
    try:
        r = subprocess.run(
            ["adb", "-s", cvd_name, "get-state"],
            capture_output=True, text=True, timeout=10,
        )
        state = (r.stdout or "").strip()
        if state != "device":
            die(2, "cvd device " + cvd_name + " not ready (state=" + state + ")")
    except subprocess.TimeoutExpired:
        die(2, "adb get-state timed out for " + cvd_name)


def install_apk(cvd_name: str, apk_path: Path) -> None:
    if not apk_path.is_file():
        die(3, "apk not found: " + str(apk_path))
    r = subprocess.run(
        ["adb", "-s", cvd_name, "install", "-r", str(apk_path)],
        capture_output=True, text=True, timeout=180,
    )
    if r.returncode != 0:
        die(3, "apk install failed: " + (r.stderr or r.stdout or "").strip())


def launch_snap(cvd_name: str) -> None:
    subprocess.run(
        ["adb", "-s", cvd_name, "shell", "monkey", "-p", SNAP_PKG,
         "-c", "android.intent.category.LAUNCHER", "1"],
        capture_output=True, text=True, timeout=30, check=True,
    )


def run_frida(probe_js: Path) -> str:
    r = subprocess.run(
        ["frida", "-U", "-n", SNAP_PKG, "-l", str(probe_js),
         "--quiet", "--runtime=v8", "--no-pause"],
        capture_output=True, text=True, timeout=60,
    )
    if r.returncode != 0 and not r.stdout:
        die(4, "frida failed: " + (r.stderr or "").strip())
    return r.stdout or ""


def parse_probe_output(blob: str) -> Dict[str, Any]:
    pattern = re.compile(
        re.escape(PROBE_START_MARKER) + r"\s*(.*?)\s*" + re.escape(PROBE_END_MARKER),
        re.DOTALL,
    )
    m = pattern.search(blob)
    if not m:
        die(4, "probe output markers not found in frida stdout")
    raw = m.group(1).strip()  # type: ignore[union-attr]
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        die(4, "probe JSON parse failed: " + str(exc))
        return {}  # unreachable


def pick_top(matches: List[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], int]:
    """Return (top_match, count_of_HIGH_matches). Top is highest-confidence."""
    if not matches:
        return None, 0
    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    ranked = sorted(matches, key=lambda m: order.get(m.get("confidence", "LOW"), 3))
    high_count = sum(1 for m in matches if m.get("confidence") == "HIGH")
    return ranked[0], high_count


def build_hooks(probe: Dict[str, Any], snap_version: str) -> Dict[str, Any]:
    cands = probe.get("candidates", {}) or {}
    missing: List[str] = []
    ambiguous: List[str] = []
    resolved: Dict[str, Any] = {}
    for key in ("kiib_zck", "m0l", "hlm"):
        top, high_count = pick_top(cands.get(key, []) or [])
        if top is None:
            missing.append(key)
            resolved[key] = None
        else:
            resolved[key] = top
            if high_count > 1:
                ambiguous.append(key)
    if missing:
        overall = "LOW"
    elif ambiguous:
        overall = "MEDIUM"
    else:
        confs = [resolved[k].get("confidence", "LOW") for k in resolved if resolved[k]]
        overall = "HIGH" if all(c == "HIGH" for c in confs) else "MEDIUM"
    return {
        "schema_version": "sinister.snap-hooks.v1",
        "snap_version": snap_version,
        "generated_at": now_iso(),
        "validation_status": "pending",
        "confidence": overall,
        "validation_details": {
            "missing": missing,
            "ambiguous": ambiguous,
            "all_classes_count": probe.get("all_classes_count", 0),
            "probe_completed_at": probe.get("probe_completed_at"),
        },
        "hooks": resolved,
    }


def atomic_write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".hooks-", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)
            f.write("\n")
        os.replace(tmp_name, str(path))
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def synthetic_probe(snap_version: str) -> Dict[str, Any]:
    return {
        "schema_version": "sinister.frida-probe.v1",
        "snap_version_guess": snap_version,
        "probe_completed_at": now_iso(),
        "all_classes_count": 12345,
        "candidates": {
            "kiib_zck": [
                {"pattern": "kiib_zck", "class": "kiib.zck",
                 "method_g": "g", "method_h": "h", "confidence": "HIGH"}
            ],
            "m0l": [
                {"pattern": "m0l", "class": "C33042m0l",
                 "payload_field": "c", "int_field_count": 2, "confidence": "HIGH"}
            ],
            "hlm": [
                {"pattern": "hlm", "class": "Hlm.d",
                 "has_finalize": False, "has_apply": True,
                 "apply_returns": "com.google.android.gms.common.api.Status",
                 "confidence": "HIGH"}
            ],
        },
    }


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Snap auto-update Phase 2 orchestrator")
    ap.add_argument("--apk-path", required=True, type=Path)
    ap.add_argument("--cvd-name", default="cvd-1")
    ap.add_argument("--snap-version", required=True)
    ap.add_argument("--output", default=None, type=Path)
    ap.add_argument("--dry-run", action="store_true")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    out_path: Path = args.output or (DEFAULT_HOOKS_DIR / ("v" + args.snap_version + "-hooks.json"))
    if args.dry_run:
        probe = synthetic_probe(args.snap_version)
        hooks = build_hooks(probe, args.snap_version)
        sys.stdout.write("[run-probe] DRY-RUN -- would write " + str(out_path) + "\n")
        sys.stdout.write(json.dumps(hooks, indent=2, sort_keys=True) + "\n")
        return 0
    preflight(args.cvd_name)
    install_apk(args.cvd_name, args.apk_path)
    launch_snap(args.cvd_name)
    time.sleep(8)
    if not FRIDA_PROBE_JS.is_file():
        die(5, "frida-probe.js not found at " + str(FRIDA_PROBE_JS))
    blob = run_frida(FRIDA_PROBE_JS)
    probe = parse_probe_output(blob)
    hooks = build_hooks(probe, args.snap_version)
    atomic_write_json(out_path, hooks)
    sys.stdout.write(str(out_path) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
