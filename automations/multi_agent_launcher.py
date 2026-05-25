#!/usr/bin/env python3
"""multi_agent_launcher.py -- one-key multi-agent spawn (Tony Stark command center).

Author: RKOJ-ELENO :: 2026-05-25
Operator hard-canonical 2026-05-25 ~06:30Z:
    "think of how i can control, open, manage multiple claude agents at once
     in the most efficent manner you can come up with based on everything we
     have been building and our customs."

Reinforcement (Image 1, 2026-05-25 ~06:30Z):
    "make sure you place in good round robin jerry rigging so that we can use
     the 4 different accounts flking under the radar to gain more power."

Composes with:
    automations/swarm-presets.json                -- named bundles consumed here
    automations/start-sinister-session.ps1        -- existing per-agent launcher
    automations/claude-oauth-accounts.ps1         -- PickBest / RotateToNext
    automations/account_balancer.py               -- usage feedback loop
    automations/multi_agent_status.py             -- live dashboard
    _shared-memory/multi-launch-log.jsonl         -- spawn audit log

Doctrine binding: NO new .bat / NO new .ps1 (operator 2026-05-25T02:45Z). This
script IS allowed to CALL the existing start-sinister-session.ps1 because that
PS1 already exists and is the canonical launcher; the ban is on CREATING new
PS1 / BAT files.

CLI:
    --list-presets                 print every preset + spawn count + first project
    --swarm <name>                 launch the named preset
    --build-preset <name> --projects p1,p2 --modes loop,swarm
                                   write a new preset entry into swarm-presets.json
    --dry-run                      print planned spawn commands without spawning
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SANCTUM_ROOT = Path(os.environ.get("SINISTER_SANCTUM_ROOT", r"D:\Sinister Sanctum"))
PRESETS_FILE = SANCTUM_ROOT / "automations" / "swarm-presets.json"
LAUNCHER_PS1 = SANCTUM_ROOT / "automations" / "start-sinister-session.ps1"
ACCOUNTS_PS1 = SANCTUM_ROOT / "automations" / "claude-oauth-accounts.ps1"
ACCOUNTS_JSON = SANCTUM_ROOT / "_shared-memory" / "claude-accounts.json"
LAUNCH_LOG = SANCTUM_ROOT / "_shared-memory" / "multi-launch-log.jsonl"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def load_presets() -> dict:
    if not PRESETS_FILE.exists():
        raise FileNotFoundError(f"swarm-presets.json missing at {PRESETS_FILE}")
    return json.loads(PRESETS_FILE.read_text(encoding="utf-8-sig", errors="replace"))


def save_presets(doc: dict) -> None:
    PRESETS_FILE.write_text(
        json.dumps(doc, indent=4, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def load_accounts() -> dict:
    if not ACCOUNTS_JSON.exists():
        return {"accounts": []}
    return json.loads(ACCOUNTS_JSON.read_text(encoding="utf-8-sig", errors="replace"))


def pick_round_robin(used_this_run: list[str]) -> str:
    """Return next enabled non-rate-limited account, skipping any already-used in this run."""
    cfg = load_accounts()
    accts = cfg.get("accounts", [])
    now = datetime.now(timezone.utc)
    candidates: list[str] = []
    for a in accts:
        if not a.get("enabled", False):
            continue
        rl = a.get("rate_limited_until_utc")
        if rl:
            try:
                rl_dt = datetime.fromisoformat(rl.replace("Z", "+00:00"))
                if rl_dt > now:
                    continue
            except Exception:
                pass
        candidates.append(a["name"])
    # Prefer not-yet-used-this-run; if all used, recycle from start.
    unused = [c for c in candidates if c not in used_this_run]
    if unused:
        return unused[0]
    if candidates:
        return candidates[0]
    # Hard fallback: default slot
    return cfg.get("default", "operator")


def append_log(entry: dict) -> None:
    LAUNCH_LOG.parent.mkdir(parents=True, exist_ok=True)
    with LAUNCH_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def list_presets() -> int:
    doc = load_presets()
    presets = doc.get("presets", {})
    if not presets:
        print("(no presets defined)")
        return 0
    print(f"swarm-presets.json :: {len(presets)} preset(s)")
    print("-" * 68)
    for name, p in presets.items():
        spawns = p.get("spawns", [])
        first = spawns[0]["project"] if spawns else "(empty)"
        stagger = p.get("stagger_seconds", 0)
        doc_line = p.get("_doc", "")
        print(f"  {name:<18}  {len(spawns)} spawn(s)  stagger={stagger}s  first={first}")
        if doc_line:
            print(f"    {doc_line[:90]}")
    print()
    print("Run a preset:  python automations/multi_agent_launcher.py --swarm <name>")
    return 0


def spawn_one(spawn: dict, account: str, dry_run: bool) -> tuple[bool, str]:
    """Invoke start-sinister-session.ps1 once for a single spawn descriptor."""
    project = spawn["project"]
    modes = spawn.get("modes", {})
    topic = spawn.get("topic_suffix", "swarm")
    branch = f"agent/{project}/{topic}-{utc_compact()}"

    env = os.environ.copy()
    env["SINISTER_ACCOUNT"] = account
    env["SINISTER_DEFAULT_LOOP"] = "1" if modes.get("loop", True) else "0"
    env["SINISTER_DEFAULT_SWARM"] = "1" if modes.get("swarm", True) else "0"
    if modes.get("loop_relentless", True):
        env["SINISTER_LOOP_RELENTLESS"] = "1"
    env["SINISTER_BRANCH_OVERRIDE"] = branch
    env["SINISTER_PROJECT_KEY"] = project
    env["SINISTER_MULTI_LAUNCH"] = "1"

    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(LAUNCHER_PS1),
        "-ProjectKey",
        project,
        "-Account",
        account,
        "-NonInteractive",
    ]
    if dry_run:
        return True, f"DRY-RUN  {project}@{account}  branch={branch}"
    if not LAUNCHER_PS1.exists():
        return False, f"launcher missing at {LAUNCHER_PS1}"
    try:
        # Use Popen + DETACHED so terminals open independently; we don't wait.
        creationflags = 0
        if os.name == "nt":
            creationflags = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        subprocess.Popen(cmd, env=env, cwd=str(SANCTUM_ROOT), creationflags=creationflags)
        return True, f"spawned {project}@{account}  branch={branch}"
    except Exception as e:
        return False, f"spawn fail: {e!r}"


def run_swarm(name: str, dry_run: bool) -> int:
    doc = load_presets()
    presets = doc.get("presets", {})
    if name not in presets:
        print(f"ERROR: preset '{name}' not found. Available: {', '.join(presets.keys()) or '(none)'}")
        return 2
    preset = presets[name]
    spawns = preset.get("spawns", [])
    stagger = int(preset.get("stagger_seconds", 2))
    if not spawns:
        print(f"ERROR: preset '{name}' has no spawns")
        return 2

    used: list[str] = []
    print(f"swarm-launch :: {name}  ({len(spawns)} spawn(s), stagger={stagger}s)")
    print("-" * 68)
    successes = 0
    for i, spawn in enumerate(spawns, start=1):
        hint = spawn.get("account_hint", "auto")
        acct = hint if hint != "auto" else pick_round_robin(used)
        used.append(acct)
        ok, detail = spawn_one(spawn, acct, dry_run)
        flag = "OK" if ok else "FAIL"
        print(f"  [{i}/{len(spawns)}] {flag}  {detail}")
        append_log({
            "ts_utc": utc_now_iso(),
            "preset": name,
            "spawn_index": i,
            "project": spawn["project"],
            "account": acct,
            "modes": spawn.get("modes", {}),
            "topic_suffix": spawn.get("topic_suffix", ""),
            "dry_run": bool(dry_run),
            "ok": ok,
            "detail": detail,
        })
        if ok:
            successes += 1
        if i < len(spawns) and stagger > 0 and not dry_run:
            time.sleep(stagger)
    print("-" * 68)
    print(f"done :: {successes}/{len(spawns)} spawned. log: {LAUNCH_LOG}")
    return 0 if successes == len(spawns) else 1


def build_preset(name: str, projects_csv: str, modes_csv: str) -> int:
    """Interactive-light preset builder: writes a new preset into swarm-presets.json."""
    doc = load_presets()
    presets = doc.setdefault("presets", {})
    if name in presets:
        print(f"WARN: overwriting existing preset '{name}'")
    projects = [p.strip() for p in projects_csv.split(",") if p.strip()]
    if not projects:
        print("ERROR: --projects required (comma list)")
        return 2
    mode_set = set(m.strip().lower() for m in modes_csv.split(",") if m.strip())
    modes = {
        "loop": "loop" in mode_set or "relentless" in mode_set,
        "swarm": "swarm" in mode_set,
        "loop_relentless": "relentless" in mode_set or "loop" in mode_set,
    }
    if not any(modes.values()):
        modes = {"loop": True, "swarm": True, "loop_relentless": True}
    spawns = []
    for p in projects:
        spawns.append({
            "project": p,
            "account_hint": "auto",
            "modes": modes,
            "model": "opus",
            "topic_suffix": f"custom-{name}",
        })
    presets[name] = {
        "_doc": f"Custom preset built {utc_now_iso()} via --build-preset.",
        "stagger_seconds": 2,
        "spawns": spawns,
    }
    save_presets(doc)
    print(f"OK preset '{name}' written with {len(spawns)} spawn(s). Run: --swarm {name}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--list-presets", action="store_true")
    ap.add_argument("--swarm", type=str, default=None, help="named preset to launch")
    ap.add_argument("--build-preset", type=str, default=None, help="new preset name")
    ap.add_argument("--projects", type=str, default="", help="comma-list (with --build-preset)")
    ap.add_argument("--modes", type=str, default="loop,swarm,relentless",
                    help="comma-list of mode flags (with --build-preset)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.list_presets:
        return list_presets()
    if args.build_preset:
        return build_preset(args.build_preset, args.projects, args.modes)
    if args.swarm:
        return run_swarm(args.swarm, args.dry_run)
    ap.print_help()
    print("\n(no action) -- pass --list-presets, --swarm <name>, or --build-preset <name>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
