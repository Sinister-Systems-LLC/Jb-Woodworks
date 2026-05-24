"""Kernel boot smoke tests — same 5 checks as boot-check.sh, in pytest form.

RKOJ-ELENO :: 2026-05-24

Runs in MOCK_CVD mode by default; the canned adb responses simulate a clean
boot. Set MOCK_CVD=0 + start cvd via boot-cuttlefish.sh to run against a real
kernel.
"""
from __future__ import annotations


def test_adb_reachable(adb) -> None:
    assert adb.reachable(), "adb returned nonzero on `true` — device did not boot"


def test_uname_looks_like_linux(adb) -> None:
    out = adb.shell("uname -a").stdout
    assert out, "empty uname output"
    assert "Linux" in out, f"uname doesn't look like Linux: {out!r}"


def test_system_mounted_readonly(adb) -> None:
    out = adb.shell("mount").stdout
    lines = [l for l in out.splitlines() if " /system " in l]
    assert lines, f"no /system mount line in: {out!r}"
    assert "ro," in lines[0], f"/system is not mounted ro: {lines[0]!r}"


def test_keystore2_present(adb) -> None:
    out = adb.shell("pgrep -f keystore2").stdout.strip()
    assert out and out.isdigit(), f"keystore2 daemon missing (Snapchat hard-requires this) — got: {out!r}"


def test_gatekeeper_hal_present(adb) -> None:
    out = adb.shell("pgrep -f android.hardware.gatekeeper").stdout.strip()
    assert out and out.isdigit(), f"gatekeeper HAL missing — got: {out!r}"


def test_no_kernel_panic_in_dmesg(adb) -> None:
    out = adb.shell("dmesg | tail -100").stdout
    assert "Kernel panic" not in out, f"kernel panic in dmesg tail: {out!r}"
    assert "Oops" not in out, f"oops in dmesg tail: {out!r}"


def test_sinister_eve_service_started(adb) -> None:
    """If the Sinister patch series is active, /init starts the EVE service early."""
    out = adb.shell("dmesg | tail -100").stdout
    # Without sinister patches this assertion is N/A — mark expected-pass since canned mock has it
    if "sinister-eve" not in out:
        # patches not applied yet (P0/P1 build vanilla GKI) — that's expected
        return
    assert "service started" in out or "ready" in out, f"EVE service signal not in dmesg: {out!r}"
