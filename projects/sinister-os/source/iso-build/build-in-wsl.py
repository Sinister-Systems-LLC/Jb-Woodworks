#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-25
"""
build-in-wsl.py — one-command Sinister OS ISO builder for Windows hosts.

Wraps build.sh + bake-panel.sh so the operator can produce a bootable
sinister-os-<date>.iso from PowerShell or Claude tool calls without
hand-running bash. Picks a substrate in this order:

  1. Docker Desktop (if the daemon is reachable from Windows) — preferred,
     fastest, no kernel module shenanigans inside WSL2.
  2. WSL2 with docker installed inside the distro — auto-detected via
     `wsl.exe -l -v` + `wsl.exe -- which docker`.
  3. WSL2 with `arch4edu/archlinux:latest` + mkarchiso bind-mounted — last
     resort; documented but slow.

Subcommands:

  python build-in-wsl.py prereqs   — check + report what's installed
  python build-in-wsl.py panel     — run bake-panel.sh (Panel bundle)
  python build-in-wsl.py build     — full build (panel -> mkarchiso -> ISO)
  python build-in-wsl.py clean     — rm -rf build/_work, build/_stage
  python build-in-wsl.py iso-info  — list ISOs in build/ with size + mtime

Composes with:
  - source/iso-build/build.sh (the existing bash-based driver)
  - source/iso-build/bake-panel.sh (Panel bundle prereq)
  - EXECUTION-PLAN-2026-05-25 § 2 Phase 1B Day 1 deliverable
  - no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25 (Python over .bat/.ps1)
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent.parent  # projects/sinister-os/
BUILD_OUT = (PROJECT_ROOT / "build").resolve()
PANEL_SERVER_JS = HERE / "airootfs" / "srv" / "sinister-panel" / "server.js"

# Colors — keep dependency-free; ANSI escape sequences with PowerShell-safe
# fallbacks. On non-tty (piped) the codes are stripped.
USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR", "") == ""


def c(code: str, s: str) -> str:
    if not USE_COLOR:
        return s
    return f"\x1b[{code}m{s}\x1b[0m"


def info(s: str) -> None:
    print(f"{c('36', '==>')} {s}", flush=True)


def warn(s: str) -> None:
    print(f"{c('33', '!! ')} {s}", flush=True)


def fail(s: str, rc: int = 1) -> None:
    print(f"{c('31', 'XX ')} {s}", flush=True)
    sys.exit(rc)


def ok(s: str) -> None:
    print(f"{c('32', 'OK ')} {s}", flush=True)


# ---------------------------------------------------------------------------
# Substrate detection
# ---------------------------------------------------------------------------


@dataclass
class Substrate:
    kind: str  # "docker-desktop" | "wsl-docker" | "wsl-archiso" | "none"
    distro: str | None = None  # for wsl-* kinds
    docker_cmd: list[str] | None = None  # e.g. ["docker"] or ["wsl.exe","-d","Ubuntu","--","docker"]

    @property
    def runs_via_wsl(self) -> bool:
        return self.kind.startswith("wsl-")


def _which(name: str) -> str | None:
    return shutil.which(name)


def _run(cmd: list[str], capture: bool = True, check: bool = False, timeout: int | None = 30) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        capture_output=capture,
        text=True,
        check=check,
        timeout=timeout,
    )


def _docker_daemon_alive(docker_cmd: list[str]) -> bool:
    try:
        proc = _run(docker_cmd + ["info", "--format", "{{.ServerVersion}}"], timeout=10)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False
    return proc.returncode == 0 and proc.stdout.strip() != ""


def _list_wsl_distros() -> list[str]:
    """Return list of running/usable WSL2 distros, or [] if WSL not installed."""
    wsl = _which("wsl.exe") or _which("wsl")
    if not wsl:
        return []
    try:
        proc = _run([wsl, "-l", "-q"], timeout=10)
    except Exception:
        return []
    if proc.returncode != 0:
        return []
    raw = proc.stdout.replace("\x00", "")
    return [ln.strip() for ln in raw.splitlines() if ln.strip()]


def _wsl_has_docker(distro: str) -> bool:
    wsl = _which("wsl.exe") or _which("wsl")
    if not wsl:
        return False
    try:
        proc = _run([wsl, "-d", distro, "--", "which", "docker"], timeout=15)
    except Exception:
        return False
    return proc.returncode == 0 and "/docker" in proc.stdout


def detect_substrate() -> Substrate:
    # 1) Docker Desktop on Windows host
    docker = _which("docker.exe") or _which("docker")
    if docker and _docker_daemon_alive([docker]):
        return Substrate(kind="docker-desktop", docker_cmd=[docker])

    # 2) WSL2 distro with docker inside
    for distro in _list_wsl_distros():
        if _wsl_has_docker(distro):
            wsl = _which("wsl.exe") or _which("wsl")
            cmd = [wsl, "-d", distro, "--", "docker"]
            if _docker_daemon_alive(cmd):
                return Substrate(kind="wsl-docker", distro=distro, docker_cmd=cmd)

    # 3) WSL2 fallback: any distro at all -> wsl-archiso path
    distros = _list_wsl_distros()
    if distros:
        return Substrate(kind="wsl-archiso", distro=distros[0])

    return Substrate(kind="none")


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------


def cmd_prereqs(args: argparse.Namespace) -> int:
    info("Detecting build substrate...")
    sub = detect_substrate()
    print(f"  substrate: {c('35', sub.kind)}")
    if sub.distro:
        print(f"  distro:    {sub.distro}")
    if sub.docker_cmd:
        print(f"  docker:    {' '.join(sub.docker_cmd)}")

    info("Checking on-disk inputs...")
    has_panel = PANEL_SERVER_JS.exists()
    print(f"  panel bundle: {c('32','OK') if has_panel else c('33','MISSING')}  ({PANEL_SERVER_JS})")
    print(f"  build.sh:     {c('32','OK') if (HERE/'build.sh').exists() else c('31','MISSING')}")
    print(f"  bake-panel.sh:{c('32','OK') if (HERE/'bake-panel.sh').exists() else c('31','MISSING')}")
    print(f"  profiledef.sh:{c('32','OK') if (HERE/'profiledef.sh').exists() else c('31','MISSING')}")
    print(f"  output dir:   {BUILD_OUT}")

    info("Operator hint:")
    if sub.kind == "docker-desktop":
        print("  ready -> run:  python build-in-wsl.py build")
    elif sub.kind == "wsl-docker":
        print(f"  WSL2+docker via distro '{sub.distro}' -> run: python build-in-wsl.py build")
    elif sub.kind == "wsl-archiso":
        print(f"  fallback WSL2 path via '{sub.distro}'. Slower; consider installing Docker Desktop.")
        print( "  proceed anyway:  python build-in-wsl.py build")
    else:
        warn("No Docker AND no WSL2 distro found. Install one of:")
        print("    - Docker Desktop:  winget install Docker.DockerDesktop")
        print("    - WSL2 + Arch:     wsl --install --distribution Arch")
        return 2
    return 0


def _exec_streaming(cmd: list[str], cwd: Path | None = None, env: dict | None = None) -> int:
    info("RUN " + " ".join(repr(p) if " " in p else p for p in cmd))
    t0 = time.time()
    proc = subprocess.Popen(cmd, cwd=str(cwd) if cwd else None, env=env)
    try:
        rc = proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        rc = 130
    dt = time.time() - t0
    info(f"exit={rc}  wall={dt:.1f}s")
    return rc


def _to_wsl_path(p: Path, distro: str) -> str:
    """Convert a Windows path (D:\\Sinister Sanctum\\...) -> /mnt/d/Sinister Sanctum/..."""
    win = str(p).replace("/", "\\")
    drive, rest = (win[0].lower(), win[2:].replace("\\", "/")) if len(win) > 2 and win[1] == ":" else (None, win)
    if drive is None:
        return win
    return f"/mnt/{drive}{rest}"


def _run_script_via(sub: Substrate, script: str, env: dict | None = None) -> int:
    """Run an inner script (build.sh / bake-panel.sh) via the chosen substrate."""
    if sub.kind == "docker-desktop":
        # bash from git-for-windows or WSL.  Prefer git-bash if present.
        bash = _which("bash.exe") or _which("bash")
        if not bash:
            fail("bash not found on PATH. Install git-for-windows or use WSL2.")
        return _exec_streaming([bash, script], cwd=HERE, env=env)
    if sub.runs_via_wsl:
        wsl = _which("wsl.exe") or _which("wsl")
        wsl_dir = _to_wsl_path(HERE, sub.distro or "")
        return _exec_streaming(
            [wsl, "-d", sub.distro, "--cd", wsl_dir, "--", "bash", script],
            env=env,
        )
    fail(f"Cannot run {script}: no substrate detected. Run `prereqs` first.")
    return 99


def cmd_panel(args: argparse.Namespace) -> int:
    sub = detect_substrate()
    if sub.kind == "none":
        fail("No build substrate. Run `prereqs` and install Docker Desktop or WSL2.")
    return _run_script_via(sub, "./bake-panel.sh")


def cmd_build(args: argparse.Namespace) -> int:
    sub = detect_substrate()
    if sub.kind == "none":
        fail("No build substrate. Run `prereqs` and install Docker Desktop or WSL2.")

    if not PANEL_SERVER_JS.exists():
        info("Panel bundle missing — running bake-panel first.")
        rc = _run_script_via(sub, "./bake-panel.sh")
        if rc != 0:
            fail(f"bake-panel.sh exited {rc}", rc)

    env = os.environ.copy()
    if args.packages:
        env["SINISTER_PACKAGES"] = args.packages

    rc = _run_script_via(sub, "./build.sh", env=env)
    if rc != 0:
        return rc

    info("ISO build complete. Looking in build/ for the output:")
    return cmd_iso_info(args)


def cmd_clean(args: argparse.Namespace) -> int:
    targets = [BUILD_OUT / "_work", BUILD_OUT / "_stage", BUILD_OUT / "_panel-staging"]
    for t in targets:
        if t.exists():
            info(f"rm -rf {t}")
            shutil.rmtree(t, ignore_errors=True)
        else:
            info(f"skip  {t}  (not present)")
    ok("clean done. Output ISOs in build/ left intact.")
    return 0


def cmd_iso_info(args: argparse.Namespace) -> int:
    if not BUILD_OUT.exists():
        warn(f"No build output directory yet at {BUILD_OUT}")
        return 0
    isos = sorted(BUILD_OUT.glob("*.iso"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not isos:
        warn(f"No ISOs found under {BUILD_OUT}")
        return 0
    info(f"ISOs in {BUILD_OUT}:")
    for iso in isos:
        st = iso.stat()
        size_mb = st.st_size / (1024 * 1024)
        mtime = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(st.st_mtime))
        print(f"  {mtime}  {size_mb:8.1f} MB  {iso.name}")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: Iterable[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="build-in-wsl.py",
        description="Sinister OS ISO builder wrapper (Windows host -> Docker/WSL2 -> mkarchiso).",
    )
    sub = p.add_subparsers(dest="cmd", required=False)

    sp_pre = sub.add_parser("prereqs", help="Check substrate + report what's installed.")
    sp_pre.set_defaults(func=cmd_prereqs)

    sp_panel = sub.add_parser("panel", help="Bake the Sinister Panel bundle into airootfs/.")
    sp_panel.set_defaults(func=cmd_panel)

    sp_build = sub.add_parser("build", help="Full build (panel -> mkarchiso -> ISO).")
    sp_build.add_argument(
        "--packages",
        choices=["slim", "fat", "auto"],
        default=None,
        help="Override SINISTER_PACKAGES (slim=lean ~85 pkgs, fat=109 pkgs, auto=prefer slim).",
    )
    sp_build.set_defaults(func=cmd_build)

    sp_clean = sub.add_parser("clean", help="Remove build/_work, build/_stage, build/_panel-staging.")
    sp_clean.set_defaults(func=cmd_clean)

    sp_info = sub.add_parser("iso-info", help="List ISOs in build/ with size + mtime.")
    sp_info.set_defaults(func=cmd_iso_info)

    args = p.parse_args(argv)
    if not args.cmd:
        return cmd_prereqs(argparse.Namespace())

    if platform.system() not in {"Windows", "Linux", "Darwin"}:
        warn(f"Untested host platform: {platform.system()}. Proceeding anyway.")

    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
