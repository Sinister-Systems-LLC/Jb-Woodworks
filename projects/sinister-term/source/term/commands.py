# Sinister Term :: commands.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Builtin slash-commands. Each returns (handled: bool, output: str).
# If handled=False, the line falls through to the underlying shell.

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


SANCTUM_ROOT = Path(os.environ.get("SANCTUM_ROOT") or "D:/Sinister Sanctum")
PROJECTS_JSON = SANCTUM_ROOT / "automations" / "session-templates" / "projects.json"
BOTS_INDEX = SANCTUM_ROOT / "bots" / "_INDEX.md"
SKILLS_INDEX = SANCTUM_ROOT / "skills" / "_INDEX.md"
HEARTBEATS_DIR = SANCTUM_ROOT / "_shared-memory" / "heartbeats"


@dataclass
class CommandResult:
    handled: bool
    output: str = ""
    exit_term: bool = False


def load_projects() -> list[dict]:
    if not PROJECTS_JSON.exists():
        return []
    try:
        return json.loads(PROJECTS_JSON.read_text(encoding="utf-8")).get("projects", [])
    except Exception:
        return []


def project_keys() -> list[str]:
    return [p["key"] for p in load_projects() if "key" in p]


def cmd_help(_args: list[str]) -> CommandResult:
    return CommandResult(True, """
Sinister Term commands:
  /forge                    Launch Sinister Forge TUI in this terminal
  /mind                     Open Sinister Mind in default browser (http://localhost:5079)
  /launch <project>         Spawn a Sinister session via Start-Sinister-Session.bat
  /projects                 List the 12 Sinister projects
  /heartbeats               Show live agent heartbeats
  /commits                  Show last 10 git commits from Sanctum
  /bot <name>               Run a Sinister bot from bots/ (lists if no name)
  /skill <name>             Run a Sinister skill (lists if no name)
  /cd <project>             cd into a project's root
  /clear                    Clear the screen
  /help                     This message
  /exit                     Exit Sinister Term

Anything else runs in the underlying shell.
""".strip())


def cmd_exit(_args: list[str]) -> CommandResult:
    return CommandResult(True, "Goodbye.", exit_term=True)


def cmd_clear(_args: list[str]) -> CommandResult:
    os.system("cls" if platform.system() == "Windows" else "clear")
    return CommandResult(True)


def cmd_projects(_args: list[str]) -> CommandResult:
    projects = load_projects()
    if not projects:
        return CommandResult(True, "(no projects.json found)")
    out = ["Sinister projects:"]
    for p in projects:
        out.append(f"  · {p['key']:<22} {p.get('display','')}")
    return CommandResult(True, "\n".join(out))


def cmd_heartbeats(_args: list[str]) -> CommandResult:
    if not HEARTBEATS_DIR.exists():
        return CommandResult(True, "(no heartbeats dir)")
    import time
    rows = []
    now = time.time()
    for hb in sorted(HEARTBEATS_DIR.glob("*.json")):
        try:
            data = json.loads(hb.read_text(encoding="utf-8"))
            agent = data.get("agent", hb.stem)
        except Exception:
            agent = hb.stem
        age_min = int((now - hb.stat().st_mtime) // 60)
        marker = "●" if age_min < 30 else "○"
        rows.append(f"  {marker} {agent:<30} {age_min}m ago")
    if not rows:
        return CommandResult(True, "(no heartbeats found)")
    return CommandResult(True, "Live agents:\n" + "\n".join(rows))


def cmd_commits(_args: list[str]) -> CommandResult:
    try:
        out = subprocess.check_output(
            ["git", "log", "-10", "--oneline"],
            cwd=str(SANCTUM_ROOT), text=True, stderr=subprocess.DEVNULL, timeout=10,
        )
    except Exception as e:
        return CommandResult(True, f"git log failed: {e}")
    return CommandResult(True, "Recent commits:\n" + out.rstrip())


def cmd_forge(_args: list[str]) -> CommandResult:
    """Boot the Forge TUI inline."""
    forge_src = SANCTUM_ROOT / "projects" / "sinister-forge" / "source"
    if not forge_src.exists():
        return CommandResult(True, f"(no Forge at {forge_src})")
    # Run synchronously in the foreground - replaces current process IO until exit
    try:
        subprocess.run([sys.executable, "-m", "forge"], cwd=str(forge_src), check=False)
        return CommandResult(True, "(Forge exited)")
    except Exception as e:
        return CommandResult(True, f"forge launch failed: {e}")


def cmd_mind(_args: list[str]) -> CommandResult:
    """Open Sinister Mind in default browser. If not running, start it first."""
    mind_src = SANCTUM_ROOT / "projects" / "sinister-mind" / "source"
    import webbrowser
    url = "http://localhost:5079/"
    # Best-effort start (background); ignore failure if already running
    try:
        if mind_src.exists():
            subprocess.Popen(
                [sys.executable, "-m", "mind"],
                cwd=str(mind_src),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
            )
    except Exception:
        pass
    webbrowser.open(url)
    return CommandResult(True, f"opened {url}")


def cmd_launch(args: list[str]) -> CommandResult:
    """Hand off to Start-Sinister-Session.ps1 for the given project key."""
    if not args:
        return CommandResult(True, "usage: /launch <project-key>\n" + cmd_projects([]).output)
    key = args[0]
    if key not in project_keys():
        return CommandResult(True, f"unknown project '{key}'. Try /projects.")
    ps1 = SANCTUM_ROOT / "automations" / "start-sinister-session.ps1"
    if not ps1.exists():
        return CommandResult(True, f"(no launcher at {ps1})")
    try:
        subprocess.Popen(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-File", str(ps1), "-Project", key],
            cwd=str(SANCTUM_ROOT),
        )
    except Exception as e:
        return CommandResult(True, f"launch failed: {e}")
    return CommandResult(True, f"launching {key}...")


def cmd_cd(args: list[str]) -> CommandResult:
    if not args:
        return CommandResult(True, "usage: /cd <project-key>")
    key = args[0]
    for p in load_projects():
        if p["key"] == key:
            root = p.get("root")
            if root and Path(root).exists():
                os.chdir(root)
                return CommandResult(True, f"cd {root}")
    return CommandResult(True, f"unknown project '{key}' or root missing")


def cmd_bot(args: list[str]) -> CommandResult:
    if not args:
        # list bots
        if not BOTS_INDEX.exists():
            return CommandResult(True, "(no bots/_INDEX.md)")
        body = BOTS_INDEX.read_text(encoding="utf-8", errors="replace")
        return CommandResult(True, body[:3000])
    # Bots are markdown agents; "running" a bot is symbolic - print its spec
    name = args[0]
    bots_dir = SANCTUM_ROOT / "bots"
    if not bots_dir.exists():
        return CommandResult(True, "(no bots/ dir)")
    candidates = list(bots_dir.glob(f"**/{name}*.md")) + list(bots_dir.glob(f"**/*{name}*.md"))
    if not candidates:
        return CommandResult(True, f"no bot matching '{name}'")
    return CommandResult(True, f"bot spec:\n{candidates[0].read_text(encoding='utf-8', errors='replace')[:3000]}")


def cmd_skill(args: list[str]) -> CommandResult:
    if not args:
        if not SKILLS_INDEX.exists():
            return CommandResult(True, "(no skills/_INDEX.md)")
        body = SKILLS_INDEX.read_text(encoding="utf-8", errors="replace")
        return CommandResult(True, body[:3000])
    name = args[0]
    skills_dir = SANCTUM_ROOT / "skills"
    if not skills_dir.exists():
        return CommandResult(True, "(no skills/ dir)")
    candidates = list(skills_dir.glob(f"**/{name}*.md")) + list(skills_dir.glob(f"**/*{name}*.md"))
    if not candidates:
        return CommandResult(True, f"no skill matching '{name}'")
    return CommandResult(True, f"skill:\n{candidates[0].read_text(encoding='utf-8', errors='replace')[:3000]}")


COMMANDS: dict[str, Callable[[list[str]], CommandResult]] = {
    "help": cmd_help,
    "?": cmd_help,
    "exit": cmd_exit,
    "quit": cmd_exit,
    "clear": cmd_clear,
    "cls": cmd_clear,
    "projects": cmd_projects,
    "heartbeats": cmd_heartbeats,
    "hb": cmd_heartbeats,
    "commits": cmd_commits,
    "log": cmd_commits,
    "forge": cmd_forge,
    "mind": cmd_mind,
    "launch": cmd_launch,
    "cd": cmd_cd,
    "bot": cmd_bot,
    "skill": cmd_skill,
}


def dispatch(line: str) -> CommandResult:
    """If line starts with `/`, route to a builtin; otherwise CommandResult(handled=False)."""
    stripped = line.strip()
    if not stripped.startswith("/"):
        return CommandResult(False)
    parts = stripped[1:].split()
    if not parts:
        return CommandResult(True)
    name, *args = parts
    handler = COMMANDS.get(name.lower())
    if not handler:
        return CommandResult(True, f"unknown command: /{name}. Try /help.")
    return handler(args)
