"""Sandbox test harness — pytest fixtures.

RKOJ-ELENO :: 2026-05-24

Two execution modes:
  * MOCK_CVD=1  — adb wrapper returns canned responses; runs anywhere (Windows OK).
                 Validates HARNESS LOGIC (the kernel is not actually exercised).
  * Real cvd   — adb wrapper hits a running cuttlefish on 0.0.0.0:6520.
                 Validates the KERNEL.

Mode is auto-detected: MOCK_CVD env var presence => mock mode; otherwise tries
real adb. Each test that requires a real device declares `@pytest.mark.real_cvd`;
those skip cleanly in mock mode with a clear reason.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

MOCK_MODE = os.environ.get("MOCK_CVD", "0") == "1" or shutil.which("adb") is None


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "real_cvd: requires a running cuttlefish (skipped under MOCK_CVD=1 or when adb is missing)",
    )
    config.addinivalue_line(
        "markers",
        "requires_hw_attestation: requires hardware-backed TEE attestation "
        "(skipped on cvd; only meaningful on physical Pixel 6a — P5 gate)",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    for item in items:
        if item.get_closest_marker("real_cvd") and MOCK_MODE:
            item.add_marker(pytest.mark.skip(reason="MOCK_CVD=1 or adb missing — real_cvd test skipped"))
        if item.get_closest_marker("requires_hw_attestation"):
            # CVD TEE is software-emulated; HW-backed attestation only works on physical Titan M2.
            item.add_marker(pytest.mark.skip(reason="cvd has sw-emulated TEE; requires_hw_attestation only runs on physical Pixel 6a (P5)"))


# ---------- ADB wrapper -------------------------------------------------------

@dataclass
class AdbResult:
    stdout: str
    stderr: str
    exit: int


class Adb:
    """Thin adb wrapper. Hits real adb in normal mode; serves canned responses in MOCK_CVD mode."""

    def __init__(self, target: str = "0.0.0.0:6520", *, mock: bool | None = None) -> None:
        self.target = target
        self.mock = MOCK_MODE if mock is None else mock
        self._mock_responses: dict[str, str] = self._default_mock_responses()

    def _default_mock_responses(self) -> dict[str, str]:
        return {
            "true": "",
            "uname -a": "Linux localhost 6.1.0-sinister-vsoc #1 SMP Sat May 24 16:00:00 UTC 2026 x86_64 Toybox",
            "mount": (
                "rootfs on / type rootfs (ro,seclabel)\n"
                "/dev/block/dm-0 on /system type ext4 (ro,seclabel,relatime)\n"
                "/dev/block/dm-1 on /vendor type ext4 (ro,seclabel,relatime)\n"
            ),
            "pgrep -f keystore2": "421",
            "pgrep -f android.hardware.gatekeeper": "423",
            "dmesg | tail -100": "[ 12.501] sinister-eve: service started\n[ 13.142] EVE control socket ready\n",
            "getprop ro.product.model": "Cuttlefish virtual device (Pixel 6a-bluejay-emu)",
            "getprop ro.product.cpu.abi": "x86_64",
            "getprop ro.build.fingerprint": "google/vsoc_x86_64/vsoc_x86_64:14/AOSP.MAIN/eng.builduser.20260524.1600:eng/test-keys",
            "getprop ro.boot.flash.locked": "1",
            "getprop ro.boot.verifiedbootstate": "green",
            "settings get global development_settings_enabled": "1",
            "pm list packages -f com.snapchat.android": "package:/data/app/~~mock~~/com.snapchat.android-1/base.apk=com.snapchat.android",
            "cmd account list": "account-1: type=com.snapchat.android.account name=test-2026-05-24@mocksnap",
        }

    def shell(self, cmd: str) -> AdbResult:
        if self.mock:
            text = self._mock_responses.get(cmd, "")
            return AdbResult(stdout=text, stderr="", exit=0)
        out = subprocess.run(
            ["adb", "-s", self.target, "shell", cmd],
            capture_output=True, text=True, timeout=30,
        )
        return AdbResult(stdout=out.stdout, stderr=out.stderr, exit=out.returncode)

    def getprop(self, prop: str) -> str:
        return self.shell(f"getprop {prop}").stdout.strip()

    def reachable(self) -> bool:
        return self.shell("true").exit == 0

    # Test helpers ------------------------------------------------------------
    def install_canned_response(self, cmd: str, stdout: str) -> None:
        """Test-only: override a mock response."""
        if not self.mock:
            raise RuntimeError("install_canned_response only works in mock mode")
        self._mock_responses[cmd] = stdout


# ---------- Fixtures ----------------------------------------------------------

@pytest.fixture
def adb() -> Adb:
    return Adb()


@pytest.fixture
def device_fingerprint(adb: Adb) -> dict[str, Any]:
    """Pull the device props Snapchat's bot-detection cares about."""
    return {
        "model":              adb.getprop("ro.product.model"),
        "cpu_abi":            adb.getprop("ro.product.cpu.abi"),
        "build_fingerprint":  adb.getprop("ro.build.fingerprint"),
        "verified_boot":      adb.getprop("ro.boot.verifiedbootstate"),
        "bootloader_locked":  adb.getprop("ro.boot.flash.locked"),
        "developer_options":  adb.shell("settings get global development_settings_enabled").stdout.strip(),
    }


# ---------- Project paths ----------------------------------------------------

@pytest.fixture
def sandbox_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def fingerprints_corpus(sandbox_root: Path) -> list[dict]:
    """Load the device-fingerprint corpus (generated by fingerprints/generate.py)."""
    f = sandbox_root / "fingerprints" / "corpus.json"
    if not f.exists():
        pytest.skip(f"fingerprints corpus not generated yet ({f}); run fingerprints/generate.py")
    return json.loads(f.read_text())
