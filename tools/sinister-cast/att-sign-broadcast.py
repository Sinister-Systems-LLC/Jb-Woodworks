# Author: RKOJ-ELENO :: 2026-05-25
"""Phase B-0 helper: fire SinisterDebugReceiver att_sign capture broadcasts via adb.

Bridges the manual-capture path while Phase B (native ART hook on
AttestationHeadersCallback) is in flight. Diagnose lane can use this to
pre-warm the AttSignRingBuffer for any account, unblocking
AttSignHarvester.fillBodyGaps -> PanelPusher att_sign fill end-to-end
WITHOUT waiting for the native hook to land.

Pairs with on-device classes:
  - com.sinister.detector.control.SinisterDebugReceiver (intent handler)
  - com.sinister.detector.harvest.AttSignHook.captureFromJson (parser)
  - com.sinister.detector.harvest.AttSignRingBuffer (storage)
  - com.sinister.detector.harvest.AttSignHarvester.fillBodyGaps (consumer)

Useful for:
  - Diagnose lane: pre-warm ring for an account that we have a captured
    Atlas request for from mitmproxy/Wireshark/Frida-on-different-phone.
  - Panel admin tooling: replay an att_sign captured from one device
    onto another device's Sinister Detector ring (if accounts move between
    phones).

Exit codes: 0 ok, 1 usage, 2 adb missing, 3 broadcast failed.
"""
from __future__ import annotations

import argparse
import base64
import json
import shutil
import subprocess
import sys
from pathlib import Path


INTENT_ACTION = "com.sinister.detector.debug.ATT_SIGN_CAPTURE"


def _emit(d: dict) -> None:
    sys.stdout.write(json.dumps(d, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase B-0 manual att_sign capture broadcast (kernel-apk lane)")
    ap.add_argument("--device-serial", required=True)
    ap.add_argument("--account", required=True, help="Snap username, [a-z0-9._-]+")
    ap.add_argument("--url", required=True, help="Snap API path, e.g. /snapchat.friending.server.FriendAction/AddFriends")
    ap.add_argument("--method", default="POST")
    ap.add_argument("--body-file", required=True, type=Path, help="Raw request body bytes (will be base64-encoded)")
    ap.add_argument("--att-sign-file", required=True, type=Path, help="Raw att_sign blob bytes (will be base64-encoded)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not args.body_file.is_file():
        _emit({"ok": False, "error": f"--body-file not found: {args.body_file}"})
        return 1
    if not args.att_sign_file.is_file():
        _emit({"ok": False, "error": f"--att-sign-file not found: {args.att_sign_file}"})
        return 1

    body_b64 = base64.b64encode(args.body_file.read_bytes()).decode("ascii")
    att_sign_b64 = base64.b64encode(args.att_sign_file.read_bytes()).decode("ascii")

    payload = json.dumps({
        "account": args.account,
        "url": args.url,
        "method": args.method,
        "body_b64": body_b64,
        "att_sign": att_sign_b64,
    }, separators=(",", ":"))

    cmd = [
        "adb", "-s", args.device_serial, "shell", "am", "broadcast",
        "-a", INTENT_ACTION, "--es", "json", payload,
    ]

    if args.dry_run:
        _emit({"ok": True, "dry_run": True, "device_serial": args.device_serial, "account": args.account, "url": args.url, "body_bytes": len(body_b64), "att_sign_bytes": len(att_sign_b64), "command": " ".join(cmd[:10]) + " <payload truncated>"})
        return 0

    if not shutil.which("adb"):
        _emit({"ok": False, "error": "adb not on PATH"})
        return 2

    r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    if r.returncode != 0 or "Broadcast completed" not in r.stdout:
        _emit({"ok": False, "phase": "att_sign_broadcast", "error": "broadcast failed", "stdout": r.stdout[-300:], "stderr": r.stderr[-300:]})
        return 3

    _emit({"ok": True, "phase": "att_sign_broadcast", "account": args.account, "url": args.url, "result_code": 0, "verify_hint": f"adb -s {args.device_serial} shell 'su -c cat /data/adb/sinister/attsign/{args.account}/ring.jsonl | tail -1' to confirm ring populated"})
    return 0


if __name__ == "__main__":
    sys.exit(main())
