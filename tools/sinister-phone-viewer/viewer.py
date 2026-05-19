# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
"""
Sinister Sanctum :: sinister-phone-viewer (viewer.py)

Replacement for the broken Panda screen-mirror. Wraps `adb` + `scrcpy` with
strict per-phone containerization rules:

- Every adb call must carry `-s <serial>`. Bare `adb shell ...` is refused.
- scrcpy is launched with `--display-id 0` (mirror physical display only).
  Never `--new-display` / `--virtual-display` / `--display-overlay` --
  those create an Android VirtualDisplay visible to user apps via
  `DisplayManager.getDisplays()` and are detectable by Snapchat (which then
  blocks camera access). The physical display is invisible to apps.
- Per-phone state lives at `_shared-memory/notes/phones/<serial>.md`. The
  viewer reads it on demand and updates it after any explicit push.

Public surface (consumed by automations/window-manager/server.py):

    list_devices()                              -> list[dict]
    start_view(serial, *, audio, control, ...)  -> int (pid)
    stop_view(pid)                              -> bool
    get_phone_state(serial)                     -> dict
    push_frida_to(serial, local_path)           -> dict
    forbid_global_adb(cmd_list_or_str)          -> None | raises ValueError

    -- Thread 2 (phone-viewer full integration) async additions: --
    serial_run(serial, args, timeout=10)        -> awaitable dict (ok/rc/stdout/stderr/duration_ms)
    enrich_devices_parallel(devices)            -> awaitable list[dict] (battery/lane/...)
    parse_phone_md(serial)                      -> dict (lane/attestation/installed_modules/current_proxy)
    append_command_log(serial, agent, cmd, ...) -> Path (per-phone .md, most-recent at top)
    exec_adb(serial, raw_cmd, agent=..., ...)   -> awaitable dict (run result + serial + cmd)
    install_frida(serial, local_binary)         -> awaitable dict (push+chmod+spawn frida-server)
"""

from __future__ import annotations

import asyncio
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

# Subprocess pipe constant — used by asyncio.create_subprocess_exec.
PIPE = asyncio.subprocess.PIPE

# ---------------------------------------------------------------- paths ----

SANCTUM_ROOT = Path(r"D:\Sinister Sanctum")
PHONES_NOTES_DIR = SANCTUM_ROOT / "_shared-memory" / "notes" / "phones"

# Preferred scrcpy locations. We fall back to PATH if neither exists.
SCRCPY_CANDIDATES = [
    Path(r"C:\Users\Zonia\Desktop\Apps\scrcpy-win64-v3.3.4\scrcpy.exe"),
    Path(r"C:\Users\Zonia\Desktop\Apps\scrcpy\scrcpy.exe"),
]

# Forbidden scrcpy flags that would create a VirtualDisplay (detectable by
# user apps -- Snapchat blocks camera if one is present).
FORBIDDEN_SCRCPY_FLAGS = {
    "--new-display",
    "--virtual-display",
    "--display-overlay",
}

# Track live viewer processes by pid in-process. server.py keeps its own
# map keyed by serial; this is here as a defensive guard / debug aid.
_RUNNING: dict[int, subprocess.Popen] = {}


# ---------------------------------------------------------------- helpers ----

def _scrcpy_exe() -> str:
    """Locate scrcpy.exe. Prefer hard-coded operator paths; fall back to PATH."""
    for c in SCRCPY_CANDIDATES:
        if c.exists():
            return str(c)
    found = shutil.which("scrcpy")
    if found:
        return found
    raise FileNotFoundError(
        "scrcpy not found. Install scrcpy or update SCRCPY_CANDIDATES in viewer.py."
    )


def _adb_exe() -> str:
    found = shutil.which("adb")
    if not found:
        raise FileNotFoundError("adb not found on PATH (install Android platform-tools).")
    return found


def _safe_serial(serial: str) -> str:
    """Allow only typical ADB serial chars. Reject anything else to keep
    shell-injection out of the question (we use list-form subprocess anyway,
    but this is a belt-and-suspenders guard)."""
    if not serial or not isinstance(serial, str):
        raise ValueError("serial is required")
    if not re.match(r"^[A-Za-z0-9._:\-]+$", serial):
        raise ValueError(f"invalid serial format: {serial!r}")
    return serial


# ---------------------------------------------------------------- guard ----

def forbid_global_adb(cmd: list[str] | str) -> None:
    """Raise ValueError if `cmd` invokes `adb` without `-s <serial>`.

    Accepts a list (argv-style) or a string (shell-style). Intended to wrap
    any adb invocation in this tool or the server. Examples:

        forbid_global_adb(["adb", "shell", "ls"])
            -> raises (no -s)
        forbid_global_adb(["adb", "-s", "ABC123", "shell", "ls"])
            -> ok
        forbid_global_adb("adb shell ls")
            -> raises
        forbid_global_adb("adb -s ABC123 shell ls")
            -> ok
    """
    if isinstance(cmd, str):
        try:
            tokens = shlex.split(cmd, posix=False)
        except ValueError as e:
            raise ValueError(f"forbid_global_adb: unparseable command: {cmd!r} ({e})")
    elif isinstance(cmd, (list, tuple)):
        tokens = list(cmd)
    else:
        raise ValueError(f"forbid_global_adb: expected str or list, got {type(cmd).__name__}")

    if not tokens:
        return  # nothing to check

    head = Path(tokens[0]).name.lower()
    if head not in ("adb", "adb.exe"):
        return  # not an adb command, not our concern

    # Forbidden bare commands that act on all attached phones at once.
    BARE_FORBIDDEN = {"kill-server", "start-server"}
    if len(tokens) > 1 and tokens[1] in BARE_FORBIDDEN:
        raise ValueError(
            f"forbid_global_adb: '{tokens[0]} {tokens[1]}' is forbidden — "
            "it affects all attached phones. Use `adb -s <serial> reconnect` instead."
        )

    # Look for -s <serial> early in the argv.
    for i in range(1, len(tokens) - 1):
        if tokens[i] == "-s":
            if not tokens[i + 1]:
                raise ValueError("forbid_global_adb: -s present but serial is empty")
            return

    # Special-case: `adb devices` / `adb help` / `adb version` don't need -s.
    SAFE_SUBCMDS = {"devices", "help", "--help", "-h", "version", "--version"}
    if len(tokens) > 1 and tokens[1] in SAFE_SUBCMDS:
        return

    raise ValueError(
        f"forbid_global_adb: adb invocation missing -s <serial>: "
        f"{' '.join(tokens)} -- bare adb is forbidden when phones are attached."
    )


# ---------------------------------------------------------------- list ----

def list_devices() -> list[dict[str, Any]]:
    """Parse `adb devices -l` into a list of device dicts.

    Returns:
        [{serial, model, transport_id, state, product, device}, ...]
    """
    adb = _adb_exe()
    forbid_global_adb([adb, "devices", "-l"])
    try:
        proc = subprocess.run(
            [adb, "devices", "-l"],
            capture_output=True, text=True, timeout=10,
        )
    except subprocess.TimeoutExpired:
        return []
    out: list[dict[str, Any]] = []
    if proc.returncode != 0:
        return out
    lines = proc.stdout.splitlines()
    for line in lines[1:]:  # skip "List of devices attached"
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        serial = parts[0]
        state = parts[1]
        # Remaining tokens are k:v pairs like model:Pixel_5, transport_id:1
        kv: dict[str, str] = {}
        for tok in parts[2:]:
            if ":" in tok:
                k, _, v = tok.partition(":")
                kv[k] = v
        out.append({
            "serial": serial,
            "state": state,
            "online": state == "device",
            "model": kv.get("model", ""),
            "product": kv.get("product", ""),
            "device": kv.get("device", ""),
            "transport_id": kv.get("transport_id", ""),
        })
    return out


# ---------------------------------------------------------------- view ----

def start_view(
    serial: str,
    *,
    audio: bool = False,
    control: bool = True,
    max_size: int = 1280,
    bit_rate: str = "4M",
    record_path: str | None = None,
    extra_flags: Iterable[str] | None = None,
) -> int:
    """Spawn scrcpy mirroring the **physical** display of `serial`.

    Returns the spawned process pid. Caller should pass it to stop_view().

    Guarantees:
      - --serial <serial> is always set.
      - --display-id 0 is always set (NEVER --new-display / --virtual-display).
      - extra_flags is filtered against FORBIDDEN_SCRCPY_FLAGS.
    """
    serial = _safe_serial(serial)
    scrcpy = _scrcpy_exe()

    args: list[str] = [
        scrcpy,
        "--serial", serial,
        "--display-id", "0",  # physical display only — NEVER a virtual one
        "--max-size", str(int(max_size)),
        "--video-bit-rate", str(bit_rate),
    ]
    if not audio:
        args.append("--no-audio")
    if not control:
        args.append("--no-control")
    if record_path:
        args += ["--record", str(record_path)]

    if extra_flags:
        for flag in extra_flags:
            base = flag.split("=", 1)[0]
            if base in FORBIDDEN_SCRCPY_FLAGS:
                raise ValueError(
                    f"start_view: forbidden flag {flag!r} — would create a "
                    "VirtualDisplay (detectable by user apps). See README."
                )
            # Also reject --display-id with any non-zero value.
            if base == "--display-id" and not flag.endswith("=0") and flag != "0":
                # Allow only literal "0" via the explicit param.
                raise ValueError(
                    "start_view: --display-id may only be 0 (physical). "
                    "Use start_view's max_size/bit_rate params, not raw flags."
                )
            args.append(flag)

    # Detached on Windows so the scrcpy window outlives this request.
    creationflags = 0
    if sys.platform == "win32":
        creationflags = 0x00000008  # DETACHED_PROCESS

    proc = subprocess.Popen(
        args,
        creationflags=creationflags,
        close_fds=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    _RUNNING[proc.pid] = proc
    return proc.pid


def stop_view(pid: int) -> bool:
    """Terminate exactly the scrcpy process with `pid`. Does NOT kill all
    scrcpy processes — only this one. Returns True if a process was signaled."""
    pid = int(pid)
    proc = _RUNNING.pop(pid, None)
    if proc is not None:
        try:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
            return True
        except Exception:
            return False

    # Pid not in our tracking map; try OS-level terminate only if it exists.
    try:
        if sys.platform == "win32":
            # Use taskkill /PID <pid> /T /F — terminates only that pid tree.
            res = subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                capture_output=True, text=True, timeout=5,
            )
            return res.returncode == 0
        else:
            os.kill(pid, signal.SIGTERM)
            return True
    except Exception:
        return False


# ---------------------------------------------------------------- state ----

def _phone_note_path(serial: str) -> Path:
    serial = _safe_serial(serial)
    return PHONES_NOTES_DIR / f"{serial}.md"


def get_phone_state(serial: str) -> dict[str, Any]:
    """Read `_shared-memory/notes/phones/<serial>.md` (if present) and
    return a small parsed dict. Returns ok=False if the file is missing —
    not an error, just absence-of-data."""
    path = _phone_note_path(serial)
    if not path.exists():
        return {"ok": False, "serial": serial, "path": str(path), "exists": False}
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        return {"ok": False, "serial": serial, "path": str(path), "error": str(e)}

    # Pull a few common fields out of the markdown if present.
    def _find(field: str) -> str:
        m = re.search(rf"^\*\*{re.escape(field)}:\*\*\s*(.+)$", text, flags=re.MULTILINE)
        return m.group(1).strip() if m else ""

    return {
        "ok": True,
        "serial": serial,
        "path": str(path),
        "exists": True,
        "raw": text,
        "os": _find("OS"),
        "attestation": _find("Attestation"),
        "last_connected": _find("Last connected"),
        "owner_agent": _find("Owner agent"),
        "current_proxy": _find("Current proxy"),
    }


def _append_state_note(serial: str, line: str) -> Path:
    """Append a line under the phone's notes file, creating it if needed."""
    path = _phone_note_path(serial)
    PHONES_NOTES_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    if not path.exists():
        header = (
            f"> **Author:** sinister-phone-viewer (Claude master agent) :: {ts}\n\n"
            f"# Phone: {serial}\n\n"
            f"**OS:** (unknown)\n"
            f"**Attestation:** (unknown)\n"
            f"**Last connected:** {ts}\n"
            f"**Owner agent:** (unassigned)\n"
            f"**Current proxy:** none\n\n"
            f"## Activity log\n\n"
        )
        path.write_text(header, encoding="utf-8")
    with path.open("a", encoding="utf-8") as f:
        f.write(f"- {ts} — {line}\n")
    return path


# ---------------------------------------------------------------- push ----

def push_frida_to(serial: str, local_path: str) -> dict[str, Any]:
    """Explicit per-serial frida-server push. Refuses if serial is empty.

    Calls `adb -s <serial> push <local> /data/local/tmp/frida-server` and
    chmods it. Records the push in the phone's notes file.

    This is operator-driven; agents do not invoke this without explicit OK.
    """
    serial = _safe_serial(serial)
    src = Path(local_path)
    if not src.exists() or not src.is_file():
        return {"ok": False, "error": f"local frida binary not found: {local_path}"}

    adb = _adb_exe()
    push_cmd = [adb, "-s", serial, "push", str(src), "/data/local/tmp/frida-server"]
    chmod_cmd = [adb, "-s", serial, "shell", "chmod 755 /data/local/tmp/frida-server"]

    forbid_global_adb(push_cmd)
    forbid_global_adb(chmod_cmd)

    try:
        r1 = subprocess.run(push_cmd, capture_output=True, text=True, timeout=120)
        if r1.returncode != 0:
            return {"ok": False, "error": f"adb push failed: {r1.stderr.strip() or r1.stdout.strip()}"}
        r2 = subprocess.run(chmod_cmd, capture_output=True, text=True, timeout=30)
        if r2.returncode != 0:
            return {"ok": False, "error": f"chmod failed: {r2.stderr.strip() or r2.stdout.strip()}"}
    except subprocess.TimeoutExpired as e:
        return {"ok": False, "error": f"timeout running adb: {e}"}

    note_path = _append_state_note(
        serial,
        f"frida-server pushed from {src.name} → /data/local/tmp/frida-server (chmod 755). "
        "Operator must start it manually with `adb -s {serial} shell '/data/local/tmp/frida-server -D &'`."
    )

    return {
        "ok": True,
        "serial": serial,
        "remote_path": "/data/local/tmp/frida-server",
        "local_path": str(src),
        "note_path": str(note_path),
    }


# ---------------------------------------------------------------- utility ----

def adb_push_file(serial: str, local_path: str, dest_path: str) -> dict[str, Any]:
    """Generic per-serial push helper used by the /api/devices/<serial>/push
    HTTP endpoint. Refuses missing serial. Updates the phone's notes."""
    serial = _safe_serial(serial)
    src = Path(local_path)
    if not src.exists() or not src.is_file():
        return {"ok": False, "error": f"local file not found: {local_path}"}
    if not dest_path or not dest_path.startswith("/"):
        return {"ok": False, "error": f"dest_path must be an absolute device path, got: {dest_path!r}"}

    adb = _adb_exe()
    cmd = [adb, "-s", serial, "push", str(src), dest_path]
    forbid_global_adb(cmd)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired as e:
        return {"ok": False, "error": f"timeout: {e}"}
    if r.returncode != 0:
        return {"ok": False, "error": r.stderr.strip() or r.stdout.strip()}

    note_path = _append_state_note(serial, f"pushed {src.name} → {dest_path}")
    return {"ok": True, "serial": serial, "dest": dest_path, "note_path": str(note_path)}


# ============================================================ THREAD 2 ====
# Phone-Viewer full integration: async fan-out + per-pane exec + .md schema.
# All new functions below are consumed by server.py's upgraded /api/devices,
# /api/devices/{serial}, /api/devices/{serial}/exec, and /api/devices/{serial}
# /frida/install endpoints. server.py is OWNED by another agent — this file
# only exposes the building blocks; the HTTP wiring lives there.
# ============================================================================


# ----------------------------------------------------- md parsing helpers ----

_LANE_NORMALIZE = {
    "snap-emu": "snap-emu",
    "snap": "snap-emu",
    "snapemu": "snap-emu",
    "tiktok-emu": "tiktok-emu",
    "tiktok": "tiktok-emu",
    "tiktokemu": "tiktok-emu",
    "master": "master",
    "unowned": "unowned",
    "none": "unowned",
    "": "unowned",
}


def _normalize_lane(raw: str) -> str:
    """Map an arbitrary string to one of snap-emu/tiktok-emu/master/unowned."""
    key = (raw or "").strip().lower()
    # `**Lane:** snap-emu | tiktok-emu | master | unowned` template-leftover —
    # treat un-edited templates as unowned.
    if "|" in key:
        return "unowned"
    return _LANE_NORMALIZE.get(key, "unowned")


def parse_phone_md(serial: str) -> dict[str, Any]:
    """Read `_shared-memory/notes/phones/<SERIAL>.md` and pull out the lane /
    attestation / installed-modules / current-proxy / model fields. Returns
    `{}` if file is missing or unparseable — absence-of-data is not an error.

    Recognized labels (markdown bold `**Label:**`):
      - Lane       -> normalized to snap-emu/tiktok-emu/master/unowned
      - Attestation -> raw string (operator may write iso-utc or "never")
      - Installed modules -> list[str] (comma or newline separated)
      - Current proxy -> raw string
      - Model      -> raw string (used as fallback if `adb devices -l` lacked it)
    """
    try:
        serial = _safe_serial(serial)
    except ValueError:
        return {}

    path = PHONES_NOTES_DIR / f"{serial}.md"
    if not path.exists():
        return {}
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return {}

    def _label(field: str) -> str:
        m = re.search(
            rf"^\*\*{re.escape(field)}:\*\*\s*(.+)$",
            text,
            flags=re.MULTILINE,
        )
        return m.group(1).strip() if m else ""

    # Installed modules: either bullets under the **Installed modules:** label
    # or comma-separated on the same line. Grab both shapes.
    modules: list[str] = []
    inline = _label("Installed modules")
    if inline:
        for part in re.split(r"[,;]\s*", inline):
            p = part.strip().lstrip("-").strip()
            if p:
                modules.append(p)
    # Also pull bullets immediately following the label line.
    block_m = re.search(
        r"^\*\*Installed modules:\*\*\s*\n((?:\s*-\s*.+\n?)+)",
        text,
        flags=re.MULTILINE,
    )
    if block_m:
        for line in block_m.group(1).splitlines():
            line = line.strip()
            if line.startswith("-"):
                v = line.lstrip("-").strip()
                if v and v not in modules:
                    modules.append(v)

    return {
        "lane": _normalize_lane(_label("Lane")),
        "attestation": _label("Attestation") or "never",
        "installed_modules": modules,
        "current_proxy": _label("Current proxy") or "none",
        "model": _label("Model"),
        "owner_agent": _label("Owner agent"),
        "last_connected": _label("Last connected"),
        "os": _label("OS"),
    }


def _parse_battery_pct(dumpsys_output: str) -> int | None:
    """Pull the `level: N` line out of `adb shell dumpsys battery` output."""
    if not dumpsys_output:
        return None
    m = re.search(r"level:\s*(\d+)", dumpsys_output)
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None


# ----------------------------------------------------- default md template ----

def _default_phone_md(serial: str) -> str:
    """Minimal valid per-phone .md so first-touch never fails."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    return (
        f"> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19\n\n"
        f"# Phone {serial}\n\n"
        f"**Model:** (unknown)\n"
        f"**OS:** Android (unknown)\n"
        f"**Lane:** unowned\n"
        f"**Owner agent:** (unassigned)\n"
        f"**Attestation:** never\n"
        f"**Last connected:** {now}\n"
        f"**Installed modules:**\n"
        f"**Current proxy:** none\n\n"
        f"## Notes\n"
        f"Free-form per-operator notes.\n\n"
        f"## Activity log\n"
        f"- {now} - first auto-touched by viewer.py\n\n"
        f"## Recent commands (most-recent at top)\n"
    )


def append_command_log(
    serial: str,
    agent: str,
    cmd: str,
    stdout: str,
    rc: int,
) -> Path:
    """Append an entry to the per-phone .md `## Recent commands (most-recent
    at top)` section. Creates the file from `_default_phone_md` if missing.
    Output is truncated to 500 chars to keep the file readable.

    Returns the path to the .md file (existing or newly-created).
    """
    serial = _safe_serial(serial)
    path = _phone_note_path(serial)
    PHONES_NOTES_DIR.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        path.write_text(_default_phone_md(serial), encoding="utf-8")

    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        # If we can't read, rewrite from default and proceed.
        text = _default_phone_md(serial)
        path.write_text(text, encoding="utf-8")

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    safe_agent = (agent or "operator").strip() or "operator"
    truncated_stdout = (stdout or "").rstrip()
    if len(truncated_stdout) > 500:
        truncated_stdout = truncated_stdout[:500] + "\n...[truncated to 500 chars]"

    entry = (
        f"### {ts} by {safe_agent}\n"
        f"`{cmd}`\n"
        f"> rc={rc}\n"
        f"```\n{truncated_stdout}\n```\n\n"
    )

    section_header = "## Recent commands (most-recent at top)"
    if section_header in text:
        # Insert the new entry directly under the section header so most-recent
        # is always at top. Preserve everything else.
        new_text = text.replace(
            section_header,
            section_header + "\n\n" + entry.rstrip() + "\n",
            1,
        )
        # Above replacement leaves a leading blank line + entry; collapse any
        # accidental triple-blank-lines into doubles for tidiness.
        new_text = re.sub(r"\n{3,}", "\n\n", new_text)
    else:
        # Append the section if it never existed.
        if not text.endswith("\n"):
            text += "\n"
        new_text = text + "\n" + section_header + "\n\n" + entry

    path.write_text(new_text, encoding="utf-8")
    return path


def _upsert_installed_module(serial: str, mod: str) -> None:
    """Add `mod` to the per-phone .md `**Installed modules:**` section.

    Idempotent: if a bullet matching `mod` (case-insensitive prefix match on
    the module name before the first space/paren) already exists, do nothing.
    Creates the file from default if missing.
    """
    serial = _safe_serial(serial)
    if not mod:
        return
    path = _phone_note_path(serial)
    PHONES_NOTES_DIR.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(_default_phone_md(serial), encoding="utf-8")
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        text = _default_phone_md(serial)

    # Module identity for idempotency check: token before first space or "(".
    new_name = re.split(r"[\s(]", mod, 1)[0].lower()

    # Find the bullet block under `**Installed modules:**` (if any).
    label_m = re.search(r"^\*\*Installed modules:\*\*\s*\n", text, flags=re.MULTILINE)
    if not label_m:
        # Inline form with content on same line. Replace with a label + bullet.
        inline_m = re.search(
            r"^\*\*Installed modules:\*\*\s*(.*)$",
            text,
            flags=re.MULTILINE,
        )
        existing = inline_m.group(1).strip() if inline_m else ""
        bullets = []
        if existing:
            for part in re.split(r"[,;]\s*", existing):
                p = part.strip().lstrip("-").strip()
                if p:
                    bullets.append(p)
        # Idempotency.
        for b in bullets:
            if re.split(r"[\s(]", b, 1)[0].lower() == new_name:
                return
        bullets.append(mod)
        bullet_block = "\n".join(f"  - {b}" for b in bullets)
        replacement = "**Installed modules:**\n" + bullet_block
        if inline_m:
            text = text[: inline_m.start()] + replacement + text[inline_m.end():]
        else:
            text += "\n" + replacement + "\n"
        path.write_text(text, encoding="utf-8")
        return

    # Label exists on its own line; gather following bullets.
    start = label_m.end()
    tail = text[start:]
    bullet_re = re.compile(r"^(\s*-\s*.+)$", re.MULTILINE)
    bullets: list[str] = []
    consumed = 0
    for line in tail.splitlines(keepends=True):
        if line.strip() == "" or not bullet_re.match(line):
            break
        consumed += len(line)
        bullets.append(line.rstrip().lstrip().lstrip("-").strip())

    for b in bullets:
        if re.split(r"[\s(]", b, 1)[0].lower() == new_name:
            return  # already present

    bullets.append(mod)
    new_block = "\n".join(f"  - {b}" for b in bullets) + "\n"
    text = text[:start] + new_block + tail[consumed:]
    path.write_text(text, encoding="utf-8")


# ----------------------------------------------------- async speed primitive ----

async def serial_run(
    serial: str,
    args: list[str] | tuple[str, ...],
    timeout: int = 10,
) -> dict[str, Any]:
    """The speed primitive. Runs `adb -s <serial> <args...>` via
    `asyncio.create_subprocess_exec` (no PyPI dep). Routes the FULL command
    through `_safe_serial` + `forbid_global_adb` so the caller cannot bypass
    containerization.

    Returns: {ok, rc, stdout, stderr, duration_ms, serial, cmd}.
    On serial-validation failure: {ok: False, rc: -1, error, ...}.
    On timeout: {ok: False, rc: -1, stdout, stderr (with [TIMEOUT]), ...}.

    Notes:
      - args MUST NOT include leading `adb` or `-s <serial>` — this function
        adds both for you. If the caller wants to pre-split a user-typed
        string, use `exec_adb` (which strips those tokens first).
    """
    t0 = time.perf_counter()

    try:
        serial = _safe_serial(serial)
    except ValueError as e:
        return {
            "ok": False,
            "rc": -1,
            "stdout": "",
            "stderr": "",
            "duration_ms": int((time.perf_counter() - t0) * 1000),
            "error": str(e),
            "serial": serial,
            "cmd": "",
        }

    try:
        adb = _adb_exe()
    except FileNotFoundError as e:
        return {
            "ok": False,
            "rc": -1,
            "stdout": "",
            "stderr": "",
            "duration_ms": int((time.perf_counter() - t0) * 1000),
            "error": str(e),
            "serial": serial,
            "cmd": "",
        }

    cmd: list[str] = [adb, "-s", serial, *list(args)]
    try:
        forbid_global_adb(cmd)
    except ValueError as e:
        return {
            "ok": False,
            "rc": -1,
            "stdout": "",
            "stderr": "",
            "duration_ms": int((time.perf_counter() - t0) * 1000),
            "error": str(e),
            "serial": serial,
            "cmd": " ".join(cmd),
        }

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=PIPE,
            stderr=PIPE,
        )
    except (OSError, FileNotFoundError) as e:
        return {
            "ok": False,
            "rc": -1,
            "stdout": "",
            "stderr": "",
            "duration_ms": int((time.perf_counter() - t0) * 1000),
            "error": f"failed to spawn adb: {e}",
            "serial": serial,
            "cmd": " ".join(cmd),
        }

    try:
        out_b, err_b = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        try:
            proc.kill()
            await proc.wait()
        except Exception:
            pass
        return {
            "ok": False,
            "rc": -1,
            "stdout": "",
            "stderr": f"[TIMEOUT after {timeout}s] adb {' '.join(args)}",
            "duration_ms": int((time.perf_counter() - t0) * 1000),
            "error": "timeout",
            "serial": serial,
            "cmd": " ".join(cmd),
        }

    stdout = (out_b or b"").decode("utf-8", errors="replace")
    stderr = (err_b or b"").decode("utf-8", errors="replace")
    rc = proc.returncode if proc.returncode is not None else -1

    return {
        "ok": rc == 0,
        "rc": rc,
        "stdout": stdout,
        "stderr": stderr,
        "duration_ms": int((time.perf_counter() - t0) * 1000),
        "serial": serial,
        "cmd": " ".join(cmd),
    }


# ----------------------------------------------------- parallel enrichment ----

async def enrich_devices_parallel(
    devices: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """For each device with `state == "device"`, run
    `dumpsys battery` + `getprop ro.product.model` concurrently across all
    online phones via `asyncio.gather`. Folds in `parse_phone_md` (lane /
    attestation / installed_modules / current_proxy) before returning.

    At N phones this completes in ~one round-trip (~400 ms) instead of
    N*2*~250 ms sequential.

    Mutates copies of the input dicts (not the originals).
    """
    if not devices:
        return []

    enriched: list[dict[str, Any]] = [dict(d) for d in devices]
    online: list[tuple[int, str]] = [
        (i, d["serial"])
        for i, d in enumerate(enriched)
        if d.get("state") == "device" and d.get("serial")
    ]

    # Fan out: each online phone gets two concurrent tasks.
    batt_tasks = [
        serial_run(s, ["shell", "dumpsys", "battery"], timeout=4)
        for _, s in online
    ]
    model_tasks = [
        serial_run(s, ["shell", "getprop", "ro.product.model"], timeout=3)
        for _, s in online
    ]
    results = await asyncio.gather(
        *batt_tasks, *model_tasks, return_exceptions=True
    )
    n = len(online)
    batt_results = results[:n]
    model_results = results[n:]

    for (idx, serial), batt_res, model_res in zip(online, batt_results, model_results):
        d = enriched[idx]

        # Battery percentage.
        if isinstance(batt_res, dict) and batt_res.get("ok"):
            pct = _parse_battery_pct(batt_res.get("stdout", ""))
            if pct is not None:
                d["battery"] = pct
        else:
            d.setdefault("battery", None)

        # Model fallback (only if `adb devices -l` didn't already give us one).
        if not d.get("model"):
            if isinstance(model_res, dict) and model_res.get("ok"):
                m = (model_res.get("stdout") or "").strip()
                if m:
                    d["model"] = m

        # Per-phone .md metadata.
        meta = parse_phone_md(serial)
        d["lane"] = meta.get("lane", "unowned")
        d["last_attestation"] = meta.get("attestation", "never")
        d["installed_modules"] = meta.get("installed_modules", [])
        d["current_proxy"] = meta.get("current_proxy", "none")
        if not d.get("model") and meta.get("model"):
            d["model"] = meta["model"]

    # Offline / unauthorized phones still get a lane chip and defaults.
    for d in enriched:
        if d.get("state") != "device":
            d.setdefault("battery", None)
            meta = parse_phone_md(d.get("serial", "")) if d.get("serial") else {}
            d.setdefault("lane", meta.get("lane", "unowned"))
            d.setdefault("last_attestation", meta.get("attestation", "never"))
            d.setdefault("installed_modules", meta.get("installed_modules", []))
            d.setdefault("current_proxy", meta.get("current_proxy", "none"))

    return enriched


# ----------------------------------------------------- per-pane exec ----

async def exec_adb(
    serial: str,
    raw_cmd: str,
    agent: str = "operator",
    timeout: int = 15,
) -> dict[str, Any]:
    """Run a free-form ADB command typed in the per-phone UI pane.

    Splits `raw_cmd` via `shlex.split(posix=False)` (preserves Windows
    backslashes). Strips a leading `adb` / `adb.exe`. Refuses any inline
    `-s <OTHER>` — the UI scopes the serial for you via the pane.

    Calls `serial_run` (which calls `forbid_global_adb`). Appends a row to
    the per-phone .md `## Recent commands` section regardless of success.

    Returns: serial_run's result + {serial, cmd} for the UI to render.
    """
    serial_in = serial
    try:
        serial = _safe_serial(serial)
    except ValueError as e:
        return {"ok": False, "rc": -1, "error": str(e), "serial": serial_in, "cmd": raw_cmd}

    if not raw_cmd or not raw_cmd.strip():
        return {"ok": False, "rc": -1, "error": "empty command", "serial": serial, "cmd": raw_cmd}

    try:
        parts = shlex.split(raw_cmd, posix=False)
    except ValueError as e:
        return {
            "ok": False, "rc": -1, "error": f"unparseable command: {e}",
            "serial": serial, "cmd": raw_cmd,
        }

    # Strip a leading `adb` / `adb.exe` so the operator can type either form.
    if parts and Path(parts[0]).name.lower() in ("adb", "adb.exe"):
        parts = parts[1:]

    # Refuse inline `-s <X>` — the UI pane already scopes the serial.
    for i, tok in enumerate(parts):
        if tok == "-s":
            return {
                "ok": False,
                "rc": -1,
                "error": "do not pass -s in the command — the UI scopes it for you",
                "serial": serial,
                "cmd": raw_cmd,
            }

    if not parts:
        return {"ok": False, "rc": -1, "error": "empty command after stripping `adb`",
                "serial": serial, "cmd": raw_cmd}

    res = await serial_run(serial, parts, timeout=timeout)

    # Audit log regardless of success — this is the authoritative trail.
    try:
        append_command_log(
            serial,
            agent,
            f"adb -s {serial} {' '.join(parts)}",
            res.get("stdout", "") or res.get("error", ""),
            res.get("rc", -1),
        )
    except Exception:
        # Never let logging break the response.
        pass

    res["serial"] = serial
    res["cmd"] = f"adb -s {serial} {' '.join(parts)}"
    return res


# ----------------------------------------------------- install frida ----

async def install_frida(
    serial: str,
    local_binary: str,
) -> dict[str, Any]:
    """Push frida-server binary to a SPECIFIC phone, chmod, and spawn it
    backgrounded (nohup ... &). Per-phone container — does NOT affect any
    other attached phone. Updates the per-phone .md (installed_modules +
    command log).

    Returns:
      {ok: True, serial, remote: "/data/local/tmp/frida-server"}
      OR {ok: False, stage: "push"|"chmod"|"spawn", error: "..."}
    """
    try:
        serial = _safe_serial(serial)
    except ValueError as e:
        return {"ok": False, "stage": "validate", "error": str(e)}

    src = Path(local_binary)
    if not src.exists() or not src.is_file():
        return {
            "ok": False,
            "stage": "validate",
            "error": f"local frida binary not found: {local_binary}",
        }

    remote = "/data/local/tmp/frida-server"

    # 1. push
    push_res = await serial_run(serial, ["push", str(src), remote], timeout=120)
    if not push_res.get("ok"):
        return {
            "ok": False,
            "stage": "push",
            "error": push_res.get("stderr") or push_res.get("error") or "adb push failed",
            "rc": push_res.get("rc", -1),
        }

    # 2. chmod (must precede spawn or the & fork dies)
    chmod_res = await serial_run(
        serial,
        ["shell", "chmod", "755", remote],
        timeout=10,
    )
    if not chmod_res.get("ok"):
        return {
            "ok": False,
            "stage": "chmod",
            "error": chmod_res.get("stderr") or chmod_res.get("error") or "chmod failed",
            "rc": chmod_res.get("rc", -1),
        }

    # 3. spawn backgrounded — nohup so it survives the adb shell exiting.
    spawn_res = await serial_run(
        serial,
        ["shell", f"nohup {remote} -D >/dev/null 2>&1 &"],
        timeout=8,
    )
    # The spawn returns immediately due to `&`; rc may be 0 even if the server
    # later dies. We treat non-zero as a hard failure; zero as best-effort OK.
    if not spawn_res.get("ok"):
        return {
            "ok": False,
            "stage": "spawn",
            "error": spawn_res.get("stderr") or spawn_res.get("error") or "spawn failed",
            "rc": spawn_res.get("rc", -1),
        }

    # 4. update per-phone .md (idempotent module entry + command log).
    try:
        _upsert_installed_module(
            serial,
            f"frida-server ({src.name}, pushed {datetime.now().strftime('%Y-%m-%d')}, {remote})",
        )
        append_command_log(
            serial,
            "operator",
            f"adb -s {serial} push {src.name} {remote} && chmod 755 && nohup &",
            f"frida-server pushed and spawned (pid via nohup)",
            0,
        )
    except Exception:
        # Logging failure should never fail the install.
        pass

    return {
        "ok": True,
        "serial": serial,
        "remote": remote,
        "local": str(src),
    }


# ============================================================ /THREAD 2 ====


# ============================================================ embedded screen ====
# RKOJ embedded screen viewer — Sinister Sanctum master agent (Claude) :: 2026-05-19
# In-EXE screen capture so agents can SEE the phone inline in RKOJ without a
# scrcpy popup window. No anti-detect flags — operator's spoofing handles that
# upstream. Single-shot PNG; server.py wraps this into an MJPEG stream.
# ===============================================================================


async def capture_screen(serial: str, timeout: float = 5.0) -> bytes | None:
    """Capture a PNG screenshot of <serial> via `adb -s <serial> exec-out screencap -p`.
    Returns raw PNG bytes. Returns None on failure.
    No anti-detect flags — operator's spoofing handles that upstream."""
    try:
        serial = _safe_serial(serial)
    except ValueError:
        return None
    try:
        adb = _adb_exe()
    except FileNotFoundError:
        return None
    try:
        proc = await asyncio.create_subprocess_exec(
            adb, "-s", serial, "exec-out", "screencap", "-p",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            try:
                proc.kill()
                await proc.wait()
            except Exception:
                pass
            return None
        if proc.returncode != 0 or not out:
            return None
        # ADB on Windows can corrupt bytes via CRLF translation if not careful.
        # Strip CR if PNG starts with stray bytes.
        if out[:8] != b"\x89PNG\r\n\x1a\n":
            # Try CRLF -> LF replacement (rare; only old ADB versions)
            out = out.replace(b"\r\r\n", b"\r\n").replace(b"\r\n", b"\n")
        return out if out[:4] == b"\x89PNG" else None
    except Exception:
        return None


# ============================================================ /embedded screen ===


# ---------------------------------------------------------------- main ----

if __name__ == "__main__":
    # Tiny smoke-test CLI: `python viewer.py` lists devices.
    devices = list_devices()
    print(f"Detected {len(devices)} device(s):")
    for d in devices:
        print(f"  - {d['serial']:>20s}  {d['state']:>10s}  {d.get('model','')}")
