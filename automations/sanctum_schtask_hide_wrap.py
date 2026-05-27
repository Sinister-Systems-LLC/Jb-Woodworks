#!/usr/bin/env python3
"""sanctum_schtask_hide_wrap.py -- F2 wave 3 fix.

Author: RKOJ-ELENO :: 2026-05-27

Wraps the 6 non-hidden Sinister/RKOJ scheduled tasks in `wscript.exe
headless-runner.vbs` so no console window pops on tick. Uses schtasks /Change
(not /Create) so triggers/cadences/principals are preserved.

Per fleet-master-complete-everything-2026-05-27 plan Wave 3 F2 acceptance:
  `schtasks /Query /FO LIST /V | findstr /i "Sinister RKOJ"
     | findstr /v "wscript pythonw scrcpy hidden"` returns empty

Composes:
  - headless-runners doctrine 2026-05-25
  - automate-everything-no-operator-admin 2026-05-25 (no UAC prompt; per-task
    edits via schtasks.exe inherit principal of caller)
  - no-bat-no-ps1-do-it-for-me 2026-05-25 (Python over ps1)

Smoke (any iter):
  python automations/sanctum_schtask_hide_wrap.py --dry-run
  python automations/sanctum_schtask_hide_wrap.py --apply
  python automations/sanctum_schtask_hide_wrap.py --verify
"""
from __future__ import annotations
import argparse
import re
import subprocess
import sys
from pathlib import Path

VBS_PATH = r"D:\Sinister Sanctum\automations\headless-runner.vbs"

# Tasks that show up as non-hidden / non-wscript / non-pythonw / non-scrcpy in
# `schtasks /Query /FO LIST /V` filtered by `findstr /i "Sinister RKOJ"`.
# Identified by the F2 acceptance grep run on 2026-05-27T04:54Z.
# Each entry: (task_name, original_exec) -- original_exec captured so we can
# print a diff in --dry-run and roll back if needed.
TARGETS = [
    (r"\RKOJ",
     r'cmd.exe /c "D:\Sinister Sanctum\automations\window-manager\console-daemon.bat"'),
    (r"\Sinister Fleet State Snapshot",
     r'"C:\Users\Zonia\AppData\Local\Programs\Python\Python312\python.exe" "D:\Sinister Sanctum\automations\fleet_state.py" snapshot'),
    (r"\SinisterOverseerContradictionWeeklyDigest",
     r'cmd /c set "PYTHONPATH=D:\Sinister Sanctum\projects\sinister-overseer\src" && "C:\Users\Zonia\AppData\Local\Programs\Python\Python312\python.exe" -m overseer contradiction-pass --weekly-digest'),
    (r"\SinisterOverseerStaleHeartbeatScan",
     r'cmd /c set "PYTHONPATH=D:\Sinister Sanctum\projects\sinister-overseer\src" && "C:\Users\Zonia\AppData\Local\Programs\Python\Python312\python.exe" -m overseer scan-stale-heartbeats --emit'),
    (r"\SinisterVault",
     r'cmd.exe /c "D:\Sinister Sanctum\tools\sinister-vault\vault-daemon.bat"'),
    (r"\Sinister\Sinister-daily-digest",
     r'C:\Users\Zonia\jupyter-workstation\Scripts\python.exe "C:\Users\Zonia\Desktop\Tools\cron\daily_digest.py"'),
]


def wrap_via_vbs(original_exec: str) -> tuple[str, str]:
    """Return (new_tr_value, new_arg_value) for `schtasks /Change /TR ... /RU ...`.

    schtasks /Change with /TR replaces the WHOLE 'Task To Run' field (which is
    the merged exe + args). We invoke wscript with the VBS and pass the original
    command as a single quoted arg (the VBS re-merges args back into cmd /c).
    """
    # wscript.exe path is canonical on Win10+
    wscript = r"C:\Windows\System32\wscript.exe"
    # Quote the inner command -- escape inner double quotes for cmd.exe
    inner = original_exec.replace('"', r'\"')
    new_tr = f'"{wscript}" //B //Nologo "{VBS_PATH}" "{inner}"'
    return new_tr, inner


def maybe_pythonw_shortcut(original_exec: str) -> str | None:
    """For commands that just call python.exe with a script, swap to pythonw.exe.
    pythonw runs the script with NO console window allocation -- satisfies F2
    acceptance ("pythonw" is in the allow-list) without VBS wrapping.
    Returns the rewritten command, or None if the substitution isn't safe.
    """
    if "python.exe" not in original_exec:
        return None
    # Don't touch commands with environment setup (cmd /c set ...) -- those
    # need a shell to expand %VAR%. Only safe substitution is a direct python
    # call OR `cmd /c "...python.exe... script.py"` without set/echo/pipes.
    if re.search(r"(?i)\bset\b|\becho\b|\bpipe\b|\|", original_exec):
        return None
    return original_exec.replace("python.exe", "pythonw.exe").replace(
        "Python.exe", "pythonw.exe"
    )


def _split_exec_args(tr: str) -> tuple[str, str]:
    """Split a 'Task To Run' string into (execute, arguments) for PowerShell."""
    tr = tr.strip()
    if tr.startswith('"'):
        end = tr.find('"', 1)
        if end > 0:
            return tr[1:end], tr[end + 1:].strip()
    parts = tr.split(None, 1)
    return parts[0], (parts[1] if len(parts) > 1 else "")


def schtasks_change(task_name: str, new_tr: str, dry: bool) -> int:
    """Try schtasks.exe first; fall back to schtasks /XML round-trip on
    Access-Denied (works for /RU=user tasks without re-prompting password).
    """
    cmd = ["schtasks.exe", "/Change", "/TN", task_name, "/TR", new_tr]
    if dry:
        print(f"  [dry-run] would run: schtasks /Change /TN '{task_name}' /TR <wrapped>")
        return 0
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode == 0:
        print(f"  [OK]   {task_name} (via schtasks /Change)")
        return 0
    # Fallback: XML round-trip. Export -> mutate <Command> + <Arguments> ->
    # delete -> recreate with /XML (preserves /RU + interactive principal).
    try:
        exp = subprocess.run(
            ["schtasks.exe", "/Query", "/TN", task_name, "/XML"],
            capture_output=True, text=True,
        )
        if exp.returncode != 0:
            raise RuntimeError(f"/Query /XML failed rc={exp.returncode}: {exp.stderr.strip()[:120]}")
        xml = exp.stdout
        # schtasks /Query /XML emits UTF-16 BOM sometimes; normalize.
        if xml.startswith("﻿"):
            xml = xml.lstrip("﻿")
        exe, arg = _split_exec_args(new_tr)
        # Replace <Command> + <Arguments>. There may be multiple Exec actions;
        # rewrite the FIRST one only (matches our acceptance grep target).
        cmd_re = re.compile(r"(<Command>)[^<]*(</Command>)")
        arg_re = re.compile(r"(<Arguments>)[^<]*(</Arguments>)")
        # Use lambda replacements so backslashes in paths are literal (no
        # re.sub backref interpretation).
        esc_exe = _xml_esc(exe)
        esc_arg = _xml_esc(arg)
        xml2, n_cmd = cmd_re.subn(
            lambda m: f"{m.group(1)}{esc_exe}{m.group(2)}", xml, count=1,
        )
        if n_cmd == 0:
            raise RuntimeError("No <Command> tag found in exported XML")
        if "<Arguments>" in xml2:
            xml3, _ = arg_re.subn(
                lambda m: f"{m.group(1)}{esc_arg}{m.group(2)}", xml2, count=1,
            )
        else:
            xml3 = re.sub(
                r"(</Command>)",
                lambda m: f"{m.group(1)}\n      <Arguments>{esc_arg}</Arguments>",
                xml2, count=1,
            )
        # Write to temp + re-import. /F forces overwrite without prompt.
        import tempfile, os
        tmp = tempfile.NamedTemporaryFile(suffix=".xml", delete=False, mode="w",
                                          encoding="utf-16", newline="\r\n")
        tmp.write(xml3)
        tmp.close()
        try:
            cr = subprocess.run(
                ["schtasks.exe", "/Create", "/TN", task_name, "/XML", tmp.name, "/F"],
                capture_output=True, text=True,
            )
            if cr.returncode == 0:
                print(f"  [OK]   {task_name} (via /XML round-trip)")
                return 0
            print(f"  [FAIL] {task_name}: /XML round-trip rc={cr.returncode}")
            if cr.stderr.strip():
                print(f"         stderr: {cr.stderr.strip()[:200]}")
            return cr.returncode
        finally:
            try:
                os.unlink(tmp.name)
            except OSError:
                pass
    except Exception as e:
        print(f"  [FAIL] {task_name}: schtasks rc={proc.returncode}; XML fallback err: {e}")
        if proc.stderr.strip():
            print(f"         schtasks stderr: {proc.stderr.strip()[:160]}")
        return proc.returncode


def _xml_esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;").replace("'", "&apos;"))


def verify() -> int:
    """Run the F2 acceptance grep. Return 0 if zero un-wrapped tasks remain."""
    proc = subprocess.run(
        ["schtasks.exe", "/Query", "/FO", "LIST", "/V"],
        capture_output=True, text=True, errors="replace",
    )
    blocks = re.split(r"\r?\n\r?\n", proc.stdout)
    bad = []
    for block in blocks:
        if not re.search(r"(?i)Sinister|RKOJ", block):
            continue
        tr_match = re.search(r"^Task To Run:\s+(.+)$", block, re.MULTILINE)
        tn_match = re.search(r"^TaskName:\s+(.+)$", block, re.MULTILINE)
        if not tr_match or not tn_match:
            continue
        tr = tr_match.group(1).strip()
        tn = tn_match.group(1).strip()
        if re.search(r"(?i)wscript|pythonw|scrcpy|hidden|//B|//Nologo", tr):
            continue
        bad.append((tn, tr))
    print(f"\n--- Verify (F2 acceptance grep) ---")
    print(f"Un-hidden Sinister/RKOJ tasks remaining: {len(bad)}")
    for tn, tr in bad:
        print(f"  - {tn}  ::  {tr[:80]}")
    return 0 if not bad else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    g.add_argument("--verify", action="store_true")
    args = ap.parse_args()

    if not Path(VBS_PATH).exists():
        print(f"[FAIL] headless-runner.vbs not found at: {VBS_PATH}")
        return 2

    if args.verify:
        return verify()

    dry = args.dry_run
    print(f"--- {'DRY-RUN' if dry else 'APPLY'} :: wrapping {len(TARGETS)} schtasks ---\n")
    fails = 0
    wrappers_dir = Path(r"D:\Sinister Sanctum\automations\schtask-wrappers")
    if not dry:
        wrappers_dir.mkdir(exist_ok=True)
    for name, original in TARGETS:
        print(f"\n[{name}]")
        print(f"  original: {original[:100]}{'...' if len(original) > 100 else ''}")

        # Path A: pythonw.exe substitution (cleanest, no VBS hop).
        pw = maybe_pythonw_shortcut(original)
        if pw is not None:
            print(f"  via pythonw: {pw[:100]}{'...' if len(pw) > 100 else ''}")
            rc = schtasks_change(name, pw, dry)
            if rc != 0:
                fails += 1
            continue

        # Path B: wscript+VBS wrap. Falls back to a per-task wrapper .bat if
        # the wrapped TR exceeds the 261-char schtasks /TR limit.
        new_tr, inner = wrap_via_vbs(original)
        if len(new_tr) <= 261:
            print(f"  wrapped:  {new_tr[:100]}{'...' if len(new_tr) > 100 else ''}")
            rc = schtasks_change(name, new_tr, dry)
        else:
            # Stage a per-task wrapper .bat (one-shot legacy bridge -- ok per
            # no-bat-no-ps1 doctrine's "existing legacy bridge" carve-out).
            safe_name = re.sub(r"[^A-Za-z0-9_-]", "_", name.strip("\\"))
            wrapper = wrappers_dir / f"{safe_name}.bat"
            if not dry:
                wrapper.write_text(
                    "@echo off\r\nREM Auto-generated by sanctum_schtask_hide_wrap.py (F2)\r\n"
                    f"REM Wraps long original-exec for: {name}\r\n"
                    f"{original}\r\n",
                    encoding="ascii",
                )
            short_tr = f'"{r"C:\Windows\System32\wscript.exe"}" //B //Nologo "{VBS_PATH}" "{wrapper}"'
            print(f"  wrapped (via wrapper bat, len={len(short_tr)}):")
            print(f"    bat: {wrapper}")
            print(f"    tr:  {short_tr[:100]}{'...' if len(short_tr) > 100 else ''}")
            rc = schtasks_change(name, short_tr, dry)
        if rc != 0:
            fails += 1
    print(f"\n--- Summary: {len(TARGETS) - fails} OK, {fails} FAIL ---")
    if not dry:
        return verify()
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
