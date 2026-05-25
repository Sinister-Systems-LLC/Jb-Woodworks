"""Verify a keybox against the sandbox manifest.

RKOJ-ELENO :: 2026-05-24

If the keybox's SHA256 matches a row in manifest.json, print "OK" + the row.
If it's a new keybox, print a suggested manifest row + exit 2 (operator runs
again with --accept-new to append).

Example:
    python verify_keybox.py --path C:/Users/Zonia/Desktop/keybox_20260523.xml
    python verify_keybox.py --path C:/Users/Zonia/Desktop/keybox_20260523.xml --accept-new
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

# Add this dir to sys.path so parse_keybox imports work when invoked as a script
sys.path.insert(0, str(Path(__file__).resolve().parent))

from parse_keybox import parse_keybox_file  # noqa: E402

MANIFEST = Path(__file__).resolve().parent / "manifest.json"


def load_manifest() -> dict:
    if not MANIFEST.exists():
        return {"schema_version": "sinister.keybox-manifest.v1", "keyboxes": []}
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def save_manifest(data: dict) -> None:
    MANIFEST.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--path", required=True, type=Path)
    ap.add_argument("--accept-new", action="store_true",
                    help="If keybox sha256 is not in manifest, append a new row")
    ap.add_argument("--notes", default="",
                    help="Free-text notes to attach to a new manifest row")
    args = ap.parse_args()

    if not args.path.exists():
        print(f"FAIL: keybox not found at {args.path}", file=sys.stderr)
        return 1

    parsed = parse_keybox_file(args.path)
    sha = parsed["sha256"]
    manifest = load_manifest()

    match = next((kb for kb in manifest["keyboxes"] if kb["sha256"] == sha), None)
    if match:
        print(json.dumps({"status": "ok", "matched_row": match}, indent=2))
        return 0

    # New keybox — surface a suggested row
    kb0 = parsed["keys"][0] if parsed["keys"] else {}
    chain_root = kb0.get("cert_chain_summaries", [{}])[-1] if kb0.get("cert_chain_summaries") else {}
    suggested = {
        "filename": parsed["filename"],
        "sha256": sha,
        "size_bytes": parsed["size_bytes"],
        "first_seen_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "operator_provided_path_hint": str(args.path),
        "device_id": kb0.get("device_id", ""),
        "key_count": parsed.get("number_of_keys_parsed", 0),
        "primary_key_algorithm": kb0.get("key_algorithm", ""),
        "primary_key_format": kb0.get("private_key_format", ""),
        "cert_chain_length_per_key": kb0.get("cert_chain_length", 0),
        "primary_chain_root_der_sha256": chain_root.get("der_sha256", ""),
        "status": "active",
        "notes": args.notes or "auto-generated row; operator should review notes field",
    }

    if not args.accept_new:
        print(json.dumps({
            "status": "new",
            "message": "Keybox sha256 not in manifest. Re-run with --accept-new to append the row below.",
            "suggested_row": suggested,
        }, indent=2))
        return 2

    manifest["keyboxes"].append(suggested)
    save_manifest(manifest)
    print(json.dumps({"status": "appended", "row": suggested}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
