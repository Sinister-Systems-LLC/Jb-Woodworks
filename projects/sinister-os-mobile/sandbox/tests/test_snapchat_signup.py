"""Snapchat account creation flow tests.

RKOJ-ELENO :: 2026-05-24

The harness exercises Snapchat's onboarding surface so kernel changes can be
verified against it. It does NOT bypass Snapchat's anti-bot detection — that's
a separate research surface owned by the sinister-snap-api-quantum lane. What
this harness validates is:

  * Custom-kernel build doesn't break Snapchat's runtime requirements (keystore,
    attestation, file paths, system props the app reads)
  * Device fingerprint pulled from the booted cvd matches a fingerprint in our
    quantum-generated corpus (so signups would route through the expected device class)
  * The handoff path between cvd + the snap-api lane exists (we emit a clean
    JSON record per device-boot that the snap lane can consume)

To run for real, the operator wires:
  1. Snapchat APK in $SINISTER_CVD_HOME/apks/snapchat.apk
  2. A test SMS-receivable phone number
  3. The actual signup logic (lives in sinister-snap-api-quantum, not here)
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_device_fingerprint_has_expected_keys(device_fingerprint) -> None:
    """The fingerprint dict has every key downstream consumers expect."""
    expected = {
        "model", "cpu_abi", "build_fingerprint",
        "verified_boot", "bootloader_locked", "developer_options",
    }
    assert set(device_fingerprint) >= expected, \
        f"fingerprint missing keys: {expected - set(device_fingerprint)}"


def test_device_fingerprint_serialisable(device_fingerprint, tmp_path: Path) -> None:
    """The fingerprint must round-trip JSON — sinister-snap-api-quantum consumes it as JSON."""
    out = tmp_path / "fingerprint.json"
    out.write_text(json.dumps(device_fingerprint, indent=2, sort_keys=True))
    loaded = json.loads(out.read_text())
    assert loaded == device_fingerprint


def test_fingerprint_matches_corpus_class(device_fingerprint, fingerprints_corpus) -> None:
    """The fingerprint pulled from cvd belongs to a known class in our corpus.

    'Match' is: same cpu_abi + same locked state + same verified-boot state.
    Build fingerprint string varies per build; model varies (cvd vs physical).
    """
    cls = _classify(device_fingerprint)
    corpus_classes = {_classify(c) for c in fingerprints_corpus}
    assert cls in corpus_classes, (
        f"device class {cls} not in corpus classes {corpus_classes} "
        f"— add to fingerprints/corpus.json or regenerate via fingerprints/generate.py"
    )


def _classify(fp: dict) -> tuple[str, str, str]:
    return (fp["cpu_abi"], fp["bootloader_locked"], fp["verified_boot"])


def test_developer_options_disabled_on_physical_target(device_fingerprint) -> None:
    """Snapchat's PI check flags developer-options-enabled devices.

    The physical Pixel 6a flash target should ship with developer options OFF
    by default. Cuttlefish has them ON (we need them for adb), so this test is
    informational on cvd + binding on physical (P5).
    """
    is_cvd = "Cuttlefish" in device_fingerprint["model"] or "vsoc" in device_fingerprint["build_fingerprint"]
    dev_on = device_fingerprint["developer_options"] == "1"
    if is_cvd:
        # Informational — cvd always has dev options on
        return
    assert not dev_on, "developer options enabled on physical Pixel 6a — Snapchat will flag this for review"


def test_kernel_does_not_advertise_root(adb) -> None:
    """A common bot-detection signal: kernel string contains 'rooted', 'magisk', 'su' patterns.

    Even on a development cvd build the kernel string should be clean.
    """
    out = adb.shell("uname -a").stdout.lower()
    banned = ["magisk", "supersu", "kingroot", "kinguser", "lineage-su"]
    for b in banned:
        assert b not in out, f"kernel uname advertises {b}: {out!r}"


def test_keystore_can_persist_account_credentials_path_exists(adb) -> None:
    """Snapchat persists oauth-token-equivalents in the system keystore. The
    keystore data path must be present + writable post-boot. (Read-only check
    against the path; we don't write here.)
    """
    out = adb.shell("ls -la /data/misc/keystore").stdout
    # On mock, this returns empty; in real cvd, it returns the directory listing
    if not out:
        pytest.skip("keystore path not visible (mock mode or pre-boot)")
    assert "drwx" in out, f"keystore path is not a directory: {out!r}"


@pytest.mark.real_cvd
def test_snapchat_apk_signature_matches_play_store(adb) -> None:
    """If Snapchat APK is installed, its signature should match the canonical
    Google Play Store signature. Sideloaded modified APKs fail this — they're
    a brittle detection vector for Snapchat's anti-bot."""
    out = adb.shell("pm list packages -f com.snapchat.android").stdout
    if "com.snapchat.android" not in out:
        pytest.skip("Snapchat not installed")
    sig = adb.shell("dumpsys package com.snapchat.android | grep 'signing certificate'").stdout
    # Canonical Snapchat signing-cert SHA-256 lives in the sinister-snap-api-quantum brain
    # (and varies by version). Operator drops the expected sha into env var SNAPCHAT_EXPECTED_SHA256.
    import os
    expected = os.environ.get("SNAPCHAT_EXPECTED_SHA256")
    if not expected:
        pytest.skip("SNAPCHAT_EXPECTED_SHA256 env not set; operator provides per APK version")
    assert expected.lower() in sig.lower(), f"Snapchat signing cert mismatch — sig={sig!r}"
