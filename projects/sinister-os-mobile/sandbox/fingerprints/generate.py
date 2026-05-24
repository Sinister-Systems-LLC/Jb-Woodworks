"""Quantum-driven device fingerprint corpus generator.

RKOJ-ELENO :: 2026-05-24 :: GPL-3.0-or-later

Generates a fingerprint corpus suitable for fan-out testing the custom kernel
against Snapchat's anti-bot detection surface. Each fingerprint combines two
layers:

  1. Identity layer (per-device-unique IDs)
     Source: sinister-seraphim CLI `fingerprint-batch` subcommand. Seraphim
     uses quantum-derived entropy from its QBC sweep to produce hard-to-fake
     identity tuples (device_id / android_id / imei / mac / serial). The
     entropy carries quantum-beats-classical structure measurable via the
     seraphim audit command.

  2. Device-class layer (the bot-detection-relevant props)
     Source: hand-curated profile catalog below. The 5 profiles model the
     5 device-states Snapchat's PI check buckets into:
       - cvd_clean       : cuttlefish baseline (default test target)
       - physical_locked : Pixel 6a with locked bootloader + green VB + dev opts off (the gold target)
       - physical_unlocked_dev : Pixel 6a unlocked bootloader, orange VB, dev opts on (developer device — accepted but flagged)
       - rooted_clean    : evidence of root, kernel string clean (Magisk-hidden) — Snapchat may still reject
       - cvd_dev         : cuttlefish with dev opts on (the harness default — fails physical realism check)

Each output row is consumable by:
  - tests/test_snapchat_signup.py::test_fingerprint_matches_corpus_class
  - fingerprints/apply.sh (writes the device-class layer into cvd before boot)
"""
from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

SERAPHIM_CLI = (
    Path(__file__).resolve().parents[4] / "tools" / "sinister-seraphim" / "cli.py"
)

# 5-profile device-class catalog (rotated round-robin across the corpus)
PROFILES = [
    {
        "class_name": "cvd_clean",
        "build_fingerprint": "google/vsoc_x86_64/vsoc_x86_64:14/AOSP.MAIN/eng.builduser.20260524.1600:eng/test-keys",
        "product_model": "Cuttlefish virtual device (Pixel 6a-bluejay-emu)",
        "cpu_abi": "x86_64",
        "bootloader_locked": "1",
        "verified_boot": "green",
        "developer_options": "1",
        "tee_backend": "swemu",
        "notes": "Cuttlefish baseline. cvd has sw-emulated TEE; HW-backed attestation tests skip.",
    },
    {
        "class_name": "physical_locked",
        "build_fingerprint": "google/bluejay/bluejay:14/AP1A.240505.005/11528360:user/release-keys",
        "product_model": "Pixel 6a",
        "cpu_abi": "arm64-v8a",
        "bootloader_locked": "1",
        "verified_boot": "green",
        "developer_options": "0",
        "tee_backend": "titan_m2",
        "notes": "Gold target: locked + green + dev off. Snapchat PI happy path.",
    },
    {
        "class_name": "physical_unlocked_dev",
        "build_fingerprint": "google/bluejay/bluejay:14/AP1A.240505.005/sinister-001:userdebug/test-keys",
        "product_model": "Pixel 6a",
        "cpu_abi": "arm64-v8a",
        "bootloader_locked": "0",
        "verified_boot": "orange",
        "developer_options": "1",
        "tee_backend": "titan_m2",
        "notes": "Developer-flashed Pixel 6a with Sinister kernel. Snapchat flags for review.",
    },
    {
        "class_name": "rooted_clean",
        "build_fingerprint": "google/bluejay/bluejay:14/AP1A.240505.005/11528360:user/release-keys",
        "product_model": "Pixel 6a",
        "cpu_abi": "arm64-v8a",
        "bootloader_locked": "1",
        "verified_boot": "green",
        "developer_options": "0",
        "tee_backend": "titan_m2",
        "magisk_hidden": True,
        "notes": "Magisk-hidden root. Bootloader reports locked (Magisk patches the report path). Anti-bot may detect via secondary signals.",
    },
    {
        "class_name": "cvd_dev",
        "build_fingerprint": "google/vsoc_x86_64/vsoc_x86_64:14/AOSP.MAIN/eng.builduser.20260524.1600:eng/test-keys",
        "product_model": "Cuttlefish virtual device (Pixel 6a-bluejay-emu)",
        "cpu_abi": "x86_64",
        "bootloader_locked": "0",
        "verified_boot": "orange",
        "developer_options": "1",
        "tee_backend": "swemu",
        "notes": "Cuttlefish with dev opts on + unlocked. Default harness state. Fails physical realism check; useful for negative tests.",
    },
]


@dataclass
class GenArgs:
    count: int
    out_path: Path
    backend: str
    lane: str


def fetch_identity_layer(count: int, lane: str, build_fp: str, backend: str) -> list[dict]:
    """Invoke seraphim fingerprint-batch CLI; return list of identity dicts."""
    cmd = [
        "python", str(SERAPHIM_CLI),
        "--json",
        "fingerprint-batch",
        "-n", str(count),
        "--lane", lane,
        "--build-fp", build_fp,
        "--backend", backend,
    ]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)
    if out.returncode != 0:
        raise RuntimeError(f"seraphim fingerprint-batch failed (exit {out.returncode}): {out.stderr or out.stdout}")
    # seraphim writes one JSON value to stdout (a list of N dicts)
    try:
        return json.loads(out.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"seraphim output is not JSON: {e}; first 200 chars: {out.stdout[:200]!r}") from e


def build_corpus(args: GenArgs) -> list[dict]:
    # Identity layer: one fetch per build_fp variant (seraphim hard-codes the build_fp in the output)
    # We compose by stripping seraphim's build_fingerprint + replacing with the per-profile value.
    identity = fetch_identity_layer(
        count=args.count,
        lane=args.lane,
        build_fp=PROFILES[0]["build_fingerprint"],  # placeholder; overwritten in compose loop
        backend=args.backend,
    )
    corpus = []
    for i, idn in enumerate(identity):
        profile = PROFILES[i % len(PROFILES)]
        merged = {
            **profile,
            "device_id": idn["device_id"],
            "android_id": idn["android_id"],
            "imei": idn["imei"],
            "mac_address": idn["mac_address"],
            "serial_number": idn["serial_number"],
            "identity_schema": idn.get("schema", "unknown"),
            "corpus_index": i,
        }
        # `build_fingerprint` came from profile; identity's value is discarded
        # to keep per-class consistency. Operator can verify by diffing.
        corpus.append(merged)
    return corpus


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("-n", "--count", type=int, default=25,
                   help="number of fingerprints to generate (default 25; 5 profiles round-robin × 5 each)")
    p.add_argument("--out", type=Path, default=Path(__file__).parent / "corpus.json")
    p.add_argument("--backend", default="sim-local",
                   choices=("sim-local", "sim-pilotos", "cloud-wukong-180"),
                   help="seraphim backend (sim-local is free; cloud-wukong burns budget)")
    p.add_argument("--lane", default="sinister-os-mobile")
    args = p.parse_args()

    corpus = build_corpus(GenArgs(args.count, args.out, args.backend, args.lane))
    args.out.write_text(json.dumps(corpus, indent=2))
    print(f"[generate] wrote {len(corpus)} fingerprints to {args.out}")
    by_class: dict[str, int] = {}
    for c in corpus:
        by_class[c["class_name"]] = by_class.get(c["class_name"], 0) + 1
    print(f"[generate] by class: {by_class}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
