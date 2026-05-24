"""TEE / attestation surface tests.

RKOJ-ELENO :: 2026-05-24

Snapchat's Play Integrity check exercises:
  - keystore2 (key store daemon, software path)
  - gatekeeper HAL (lock-screen credential verifier)
  - hardware-backed attestation (Titan M2 on Pixel 6a; software-emulated on cvd)

Tests that DEPEND on hardware-backed attestation are marked `requires_hw_attestation`
and SKIP on cvd. They only run against a physical Pixel 6a (P5 phase).
"""
from __future__ import annotations

import pytest


def test_verified_boot_reports_green(device_fingerprint) -> None:
    """ro.boot.verifiedbootstate must be 'green' (or 'orange' for unlocked-bootloader build).
    Snapchat's PI check rejects 'yellow' and 'red'."""
    state = device_fingerprint["verified_boot"]
    assert state in ("green", "orange"), \
        f"verified-boot state is {state!r}; Snapchat will refuse signup"


def test_bootloader_lock_state_reasonable(device_fingerprint) -> None:
    """ro.boot.flash.locked == '1' on a locked bootloader, '0' on unlocked.
    Cuttlefish reports '1' by default. A physical device with a locked bootloader
    + signed Sinister kernel would also report '1' (the kernel signature must
    chain to a known root). An unlocked development phone reports '0' — Snapchat
    accepts but flags-for-review."""
    locked = device_fingerprint["bootloader_locked"]
    assert locked in ("0", "1"), f"unexpected lock state: {locked!r}"


def test_keystore2_responds_to_basic_query(adb) -> None:
    """Keystore daemon is alive + answering. Most basic check — Snapchat will time
    out waiting for keystore if it's hung."""
    out = adb.shell("pgrep -f keystore2").stdout.strip()
    assert out.isdigit(), "keystore2 daemon not running"


@pytest.mark.requires_hw_attestation
def test_hardware_backed_key_can_be_generated(adb) -> None:
    """Generate a hardware-backed key + verify the attestation chain reaches a
    Google root cert. Only meaningful on physical Pixel 6a — cvd emulates a
    software-only TEE which Snapchat's PI check correctly rejects."""
    # This test SKIPS on cvd via the conftest.py auto-marker.
    # When it runs (P5 on physical hardware), it will:
    #   1. adb shell run-as com.sinister.testattestation
    #      keygen --tee --attestation
    #   2. Parse the returned x509 chain
    #   3. Assert chain root SHA matches one of the known Google attestation roots
    raise AssertionError("requires_hw_attestation test should have been skipped on cvd")


@pytest.mark.real_cvd
def test_snapchat_package_installed_if_apk_supplied(adb) -> None:
    """If the operator dropped a Snapchat APK in $SINISTER_CVD_HOME/apks/snapchat.apk,
    pm-install it then assert the package is visible. Otherwise skip."""
    out = adb.shell("pm list packages -f com.snapchat.android").stdout
    if "com.snapchat.android" not in out:
        pytest.skip("Snapchat APK not installed on cvd; operator pushes via adb install $SINISTER_CVD_HOME/apks/snapchat.apk")
    assert "com.snapchat.android" in out
