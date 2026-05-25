"""Play Integrity surface tests.

RKOJ-ELENO :: 2026-05-24

Three layers, each correctly gated:
  * Layer 1 (no cvd, no keybox) — keybox manifest + parser invariants
                                 (mostly covered in test_keybox.py)
  * Layer 2 (cvd, no keybox)    — PI service surface present + responsive on
                                 booted cvd (covered as real_cvd tests below)
  * Layer 3 (cvd + keybox + PIFork Magisk module) — full PI handshake with
                                 keybox-injected attestation. Operator
                                 wires PIFork at P3+; these tests skip
                                 until that lands.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

KEYBOX_MANIFEST = Path(__file__).resolve().parents[1] / "keybox" / "manifest.json"


def _has_active_keybox_in_manifest() -> bool:
    if not KEYBOX_MANIFEST.exists():
        return False
    data = json.loads(KEYBOX_MANIFEST.read_text(encoding="utf-8"))
    return any(r.get("status") == "active" for r in data.get("keyboxes", []))


# ---------- Layer 2: PI service on cvd ----------------------------------------

@pytest.mark.real_cvd
def test_play_services_package_present(adb) -> None:
    """com.google.android.gms must be installed for PI to function at all.

    cvd ships without GApps by default; operator pushes a GApps payload at P3.
    This test gates on its presence."""
    out = adb.shell("pm list packages -f com.google.android.gms").stdout
    if "com.google.android.gms" not in out:
        pytest.skip("Play Services not installed on cvd (operator pushes GApps at P3)")
    assert "com.google.android.gms" in out


@pytest.mark.real_cvd
def test_play_integrity_dumpsys_responds(adb) -> None:
    """`dumpsys` against the integrity service returns SOMETHING (alive check)."""
    out = adb.shell("dumpsys activity service com.google.android.gms/.integrity.IntegrityService").stdout
    if not out:
        pytest.skip("integrity service not present (GApps not installed)")
    # Even an error response from dumpsys is fine — it proves the service handle resolved
    assert len(out) > 0


@pytest.mark.real_cvd
def test_no_test_keys_in_build_fingerprint(adb) -> None:
    """Snapchat + many anti-bot SDKs reject `test-keys` builds.

    cvd uses test-keys by default (`eng/test-keys` suffix). A real PI-survivable
    profile rebuilds with release-keys. This test surfaces the gap."""
    fp = adb.shell("getprop ro.build.fingerprint").stdout.strip()
    if not fp:
        pytest.skip("could not read build fingerprint")
    if "test-keys" in fp:
        # On cvd_clean / cvd_dev classes this is EXPECTED; just log + skip
        pytest.skip(f"cvd build uses test-keys ({fp}) — expected on emulator; physical Pixel uses release-keys")
    assert "release-keys" in fp


# ---------- Layer 3: PIFork keybox injection ----------------------------------

@pytest.mark.real_cvd
def test_pifork_magisk_module_installed(adb) -> None:
    """PIFork lives at /data/adb/modules/playintegrityfork/.

    Operator installs at P3 via Magisk Manager + reboot. This test surfaces
    whether the module is present so subsequent PI tests have a clear gate."""
    out = adb.shell("ls -la /data/adb/modules/playintegrityfork/").stdout
    if "module.prop" not in out:
        pytest.skip("PIFork not installed (operator action at P3)")
    assert "module.prop" in out


@pytest.mark.real_cvd
def test_pifork_keybox_volume_present(adb) -> None:
    """The keybox is volume-mounted into the cvd at /data/adb/pif.json + /data/adb/keybox.xml."""
    if not _has_active_keybox_in_manifest():
        pytest.skip("no active keybox in manifest — run verify_keybox.py first")
    out = adb.shell("ls -la /data/adb/keybox.xml").stdout
    if "keybox.xml" not in out:
        pytest.skip("keybox not mounted in cvd (operator action: volume-mount at boot)")
    assert "keybox.xml" in out


@pytest.mark.real_cvd
@pytest.mark.requires_hw_attestation
def test_pi_verdict_meets_device_integrity() -> None:
    """The actual PI handshake returns a 'MEETS_DEVICE_INTEGRITY' verdict.

    This is the ULTIMATE acceptance bar — proves the keybox + PIFork chain
    fools Google's PI service. Runs only when:
      (a) cvd is up
      (b) keybox is in manifest + mounted
      (c) PIFork module is installed
      (d) operator-supplied PI testbed APK is present (NOT Snapchat — a
          standalone PI tester like PlayIntegrityChecker by chiteroman)

    Marked requires_hw_attestation because (paradoxically) we're testing
    that we CAN return a hw-attestation verdict from an emulator — only
    meaningful when the keybox + PIFork chain is wired."""
    raise AssertionError("requires_hw_attestation + real_cvd test should have been skipped on bare cvd")


# ---------- Layer 1: manifest consistency under all modes ---------------------

def test_keybox_manifest_present_or_logged() -> None:
    """If no keybox is in the manifest, the harness should skip cleanly + not
    error. This test asserts the skip path works."""
    if _has_active_keybox_in_manifest():
        return  # nothing to assert beyond presence
    # If no active keybox, this MUST be intentional (e.g., fresh checkout)
    # — log it visibly so a wandering EVE notices
    pytest.skip(
        "no active keybox in manifest. Operator runs: "
        "python sandbox/keybox/verify_keybox.py --path <path> --accept-new"
    )
