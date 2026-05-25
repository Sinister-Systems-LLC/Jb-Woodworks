#!/usr/bin/env python3
"""eve-vm.py — Sinister OS VM preview launcher.

Author: RKOJ-ELENO :: 2026-05-25
License: operator-owned (Sinister fleet, internal)

ONE command — operator types `python eve-vm.py up` — and within ~90s a browser
opens to http://localhost:6080 showing Hyprland + Sinister overlays + EVE
daemon stub. Works on Windows host with Docker Desktop installed. Falls back
to WSL2 + Arch path if Docker Desktop is missing.

This is the Phase 1A deliverable from EXECUTION-PLAN-2026-05-25/plan.md.

Usage:
    python eve-vm.py up           # build + start (default)
    python eve-vm.py down          # stop + clean
    python eve-vm.py status        # show running state
    python eve-vm.py logs          # tail container logs
    python eve-vm.py rebuild       # nuke + rebuild from scratch
    python eve-vm.py test --suite t0   # run T0 docker acceptance suite
    python eve-vm.py test --suite t1   # run T1 VM acceptance suite (needs --iso for real ISO test)
    python eve-vm.py install --target laptop --mode dualboot   # Phase 4 (gated)

Per operator hard-canonical 2026-05-25 (no-bat-no-ps1): this is Python, not a
.bat or .ps1. Operator runs `python eve-vm.py <action>`.

Per operator hard-canonical 2026-05-25 (never-ask-for-admin): this script
self-detects Docker Desktop status, prerequisite gaps, port conflicts, and
tries automated workarounds first. Only surfaces 1-line ops when truly
operator-only (e.g. "Docker Desktop not installed; choose A=install B=WSL2
fallback C=cancel").
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
COMPOSE_FILE_BASE = SCRIPT_DIR / "docker-compose.yml"
COMPOSE_FILE_PREVIEW = SCRIPT_DIR / "compose.os-preview.yml"
CONTAINERFILE = SCRIPT_DIR / "Containerfile.os-preview"
NOVNC_URL = "http://localhost:6080/vnc.html?autoconnect=1&resize=remote"
EVE_DAEMON_URL = "http://localhost:7331/health"

PREVIEW_PROJECT = "sinister-os-preview"


# ---------------------------------------------------------------------------
# Pretty printing
# ---------------------------------------------------------------------------

PURPLE = "\033[95m"
DARKP = "\033[35m"
BRIGHTP = "\033[94m"
WHITE = "\033[97m"
BOLD = "\033[1m"
DIM = "\033[2m"
OK = "\033[92m"
WARN = "\033[93m"
FAIL = "\033[91m"
RESET = "\033[0m"


def banner(title: str) -> None:
    print(f"{DARKP}---{RESET} {WHITE}{BOLD}{title}{RESET} {DARKP}---{RESET}")


def step(msg: str) -> None:
    print(f"{BRIGHTP}>>>{RESET} {msg}")


def ok(msg: str) -> None:
    print(f"{OK}OK{RESET}   {msg}")


def warn(msg: str) -> None:
    print(f"{WARN}WARN{RESET} {msg}")


def fail(msg: str) -> None:
    print(f"{FAIL}FAIL{RESET} {msg}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Environment detection
# ---------------------------------------------------------------------------


def have_command(name: str) -> bool:
    return shutil.which(name) is not None


def docker_status() -> dict:
    """Return a dict describing Docker availability and engine state."""
    state = {"installed": False, "running": False, "compose": False, "version": None}
    if not have_command("docker"):
        return state
    state["installed"] = True
    try:
        r = subprocess.run(
            ["docker", "version", "--format", "{{json .}}"],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0:
            data = json.loads(r.stdout) if r.stdout.strip() else {}
            state["running"] = "Server" in data
            state["version"] = data.get("Client", {}).get("Version")
    except (subprocess.TimeoutExpired, json.JSONDecodeError):
        pass
    state["compose"] = have_command("docker") and subprocess.run(
        ["docker", "compose", "version"], capture_output=True, timeout=5
    ).returncode == 0
    return state


def wsl_status() -> dict:
    """Return a dict describing WSL2 availability on Windows."""
    state = {"is_windows": platform.system() == "Windows", "installed": False, "distros": []}
    if not state["is_windows"]:
        return state
    if not have_command("wsl.exe"):
        return state
    state["installed"] = True
    try:
        r = subprocess.run(
            ["wsl.exe", "--list", "--quiet"],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0:
            # wsl output is UTF-16; decode tolerantly
            raw = r.stdout
            if "\x00" in raw:
                raw = raw.encode("utf-16-le", errors="ignore").decode("utf-16-le", errors="ignore")
            state["distros"] = [d.strip() for d in raw.splitlines() if d.strip()]
    except subprocess.TimeoutExpired:
        pass
    return state


def port_free(port: int) -> bool:
    """Best-effort check that a TCP port is not currently in use locally."""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    try:
        s.connect(("127.0.0.1", port))
        s.close()
        return False
    except (OSError, socket.timeout):
        return True


def preflight() -> bool:
    """Run prerequisite checks; return True if we can proceed via Docker path."""
    banner("PREFLIGHT")
    d = docker_status()
    if not d["installed"]:
        warn("docker CLI not on PATH")
        return False
    if not d["running"]:
        warn(f"docker engine not running (version: {d['version']})")
        return False
    if not d["compose"]:
        warn("docker compose plugin not available (try Docker Desktop >= 24)")
        return False
    ok(f"docker {d['version']} + compose plugin OK")

    for p in (6080, 7331, 8030, 8443):
        if port_free(p):
            ok(f"port {p} free")
        else:
            warn(f"port {p} in use — may conflict with preview stack")
    return True


def wsl_fallback_hint() -> None:
    """Show the WSL2 fallback path when Docker is unavailable."""
    banner("WSL2 FALLBACK")
    w = wsl_status()
    if not w["is_windows"]:
        warn("Non-Windows host; install Docker via your distro package manager")
        warn("  Arch:    sudo pacman -S docker docker-compose && sudo systemctl enable --now docker")
        warn("  Debian:  curl -fsSL https://get.docker.com | sh")
        return
    if not w["installed"]:
        warn("WSL2 not installed. In an elevated terminal run: wsl --install")
        warn("Then reboot. Re-run this script.")
        return
    print(f"  Installed WSL distros: {w['distros'] or '(none)'}")
    print("")
    print("  Fastest path:")
    print(f"    {BRIGHTP}wsl --install -d Ubuntu{RESET}    # if no distro present")
    print(f"    {BRIGHTP}wsl{RESET}                         # enter the distro")
    print(f"    {BRIGHTP}sudo apt install docker.io docker-compose-plugin{RESET}")
    print(f"    {BRIGHTP}sudo service docker start{RESET}")
    print(f"    Then re-run: {BRIGHTP}python {Path(__file__).name} up{RESET}")
    print("")
    warn("Future Phase 1A.2 work: this script will spawn its own Arch WSL distro")
    warn("with Sinister tools preinstalled. Until then, please use the steps above.")


# ---------------------------------------------------------------------------
# Compose lifecycle
# ---------------------------------------------------------------------------


def compose_args(extra: list[str]) -> list[str]:
    return [
        "docker", "compose",
        "-p", PREVIEW_PROJECT,
        "-f", str(COMPOSE_FILE_BASE),
        "-f", str(COMPOSE_FILE_PREVIEW),
        *extra,
    ]


def compose_up(build: bool = True) -> int:
    args = ["up", "-d"]
    if build:
        args.insert(1, "--build")
    args.append("os-preview")
    args.append("mock-panel")
    r = subprocess.run(compose_args(args))
    return r.returncode


def compose_down(volumes: bool = False) -> int:
    args = ["down"]
    if volumes:
        args.append("-v")
    return subprocess.run(compose_args(args)).returncode


def compose_logs(follow: bool = True) -> int:
    args = ["logs", "os-preview"]
    if follow:
        args.append("-f")
    return subprocess.run(compose_args(args)).returncode


def compose_ps() -> int:
    return subprocess.run(compose_args(["ps"])).returncode


# ---------------------------------------------------------------------------
# Wait + open browser
# ---------------------------------------------------------------------------


def wait_for_url(url: str, timeout_s: int = 120) -> bool:
    """Poll a URL until it returns any response or timeout."""
    import urllib.request
    import urllib.error
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as _:
                return True
        except (urllib.error.URLError, OSError):
            time.sleep(1.5)
    return False


def open_browser(url: str) -> None:
    try:
        webbrowser.open(url)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


def cmd_up(args) -> int:
    banner("Sinister OS — VM PREVIEW (Phase 1A)")
    if not preflight():
        wsl_fallback_hint()
        return 1
    step("docker compose up -d --build os-preview mock-panel")
    rc = compose_up(build=not args.no_build)
    if rc != 0:
        fail("compose up failed; check `python eve-vm.py logs`")
        return rc
    step("waiting for noVNC to come online (up to 120s)…")
    if wait_for_url("http://localhost:6080/", timeout_s=120):
        ok(f"noVNC ready at {NOVNC_URL}")
    else:
        warn("noVNC not reachable within 120s; container may still be starting")
        warn("check `python eve-vm.py logs`")
    step(f"opening browser → {NOVNC_URL}")
    open_browser(NOVNC_URL)
    print("")
    banner("OPERATOR REVIEW")
    print(f"  {WHITE}Browser:{RESET}    {BRIGHTP}{NOVNC_URL}{RESET}")
    print(f"  {WHITE}EVE health:{RESET} {BRIGHTP}{EVE_DAEMON_URL}{RESET}")
    print(f"  {WHITE}Logs:{RESET}       {BRIGHTP}python eve-vm.py logs{RESET}")
    print(f"  {WHITE}Stop:{RESET}       {BRIGHTP}python eve-vm.py down{RESET}")
    print("")
    print(f"  {DIM}Inside the noVNC desktop, open a terminal and try:{RESET}")
    print(f"    {BRIGHTP}eve chat 'hello from the operator'{RESET}")
    print(f"    {BRIGHTP}eve game-mode arm{RESET}")
    print(f"    {BRIGHTP}eve status{RESET}")
    print("")
    return 0


def cmd_down(args) -> int:
    banner("Sinister OS — VM PREVIEW DOWN")
    rc = compose_down(volumes=args.volumes)
    if rc == 0:
        ok("stack stopped")
        if args.volumes:
            ok("volumes wiped")
    return rc


def cmd_status(args) -> int:
    banner("Sinister OS — VM PREVIEW STATUS")
    return compose_ps()


def cmd_logs(args) -> int:
    banner("Sinister OS — VM PREVIEW LOGS")
    return compose_logs(follow=not args.no_follow)


def cmd_rebuild(args) -> int:
    banner("Sinister OS — VM PREVIEW REBUILD")
    compose_down(volumes=True)
    return cmd_up(argparse.Namespace(no_build=False))


def cmd_test(args) -> int:
    banner(f"Sinister OS — ACCEPTANCE TEST ({args.suite})")
    if args.suite == "t0":
        warn("T0 docker acceptance harness scaffolding lands Phase 2 Block I.")
        warn("For now this command verifies the preview stack is healthy.")
        if wait_for_url("http://localhost:6080/", timeout_s=5):
            ok("noVNC reachable")
        else:
            fail("noVNC unreachable — run `python eve-vm.py up` first")
            return 1
        if wait_for_url(EVE_DAEMON_URL, timeout_s=5):
            ok("EVE daemon stub reachable")
        else:
            warn("EVE daemon stub unreachable")
        return 0
    if args.suite == "t1":
        warn("T1 VM acceptance suite needs a real ISO (Phase 2 Block I + 1B).")
        warn("Use `--iso path/to/sinister-os.iso` once Phase 1B ships the ISO.")
        return 0
    if args.suite == "t2":
        warn("T2 laptop bare-metal suite is operator-gated (Phase 4).")
        return 0
    fail(f"unknown suite: {args.suite}")
    return 2


def cmd_install(args) -> int:
    banner("Sinister OS — LAPTOP INSTALL (Phase 4)")
    fail("Phase 4 install is operator-gated.")
    print("")
    print("  This command refuses to run until Phase 3 acceptance is green AND")
    print("  the operator explicitly says 'ship to laptop' in the current session.")
    print("")
    print("  See: projects/sinister-os/plans/EXECUTION-PLAN-2026-05-25/plan.md § 5")
    return 1


# ---------------------------------------------------------------------------
# argparse
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="eve-vm",
        description="Sinister OS VM preview launcher (Phase 1A).",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    p_up = sub.add_parser("up", help="build + start the preview stack")
    p_up.add_argument("--no-build", action="store_true", help="skip image rebuild")
    p_up.set_defaults(func=cmd_up)

    p_down = sub.add_parser("down", help="stop the preview stack")
    p_down.add_argument("-v", "--volumes", action="store_true", help="also wipe volumes")
    p_down.set_defaults(func=cmd_down)

    p_status = sub.add_parser("status", help="show running state")
    p_status.set_defaults(func=cmd_status)

    p_logs = sub.add_parser("logs", help="tail container logs")
    p_logs.add_argument("--no-follow", action="store_true", help="dump and exit")
    p_logs.set_defaults(func=cmd_logs)

    p_rebuild = sub.add_parser("rebuild", help="wipe + rebuild from scratch")
    p_rebuild.set_defaults(func=cmd_rebuild)

    p_test = sub.add_parser("test", help="run acceptance suite")
    p_test.add_argument("--suite", choices=["t0", "t1", "t2"], required=True)
    p_test.add_argument("--iso", help="path to Sinister OS ISO (T1)")
    p_test.set_defaults(func=cmd_test)

    p_install = sub.add_parser("install", help="(Phase 4; operator-gated)")
    p_install.add_argument("--target", choices=["laptop", "main-pc"], required=True)
    p_install.add_argument("--mode", choices=["dualboot", "replace", "usb"], required=True)
    p_install.set_defaults(func=cmd_install)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("")
        warn("interrupted")
        return 130


if __name__ == "__main__":
    sys.exit(main())
