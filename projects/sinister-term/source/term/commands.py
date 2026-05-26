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

# RKOJ-ELENO :: 2026-05-23 :: alias builtin
from term.aliases import load_aliases, save_aliases

# iter-52: publish builtin-dispatch events to the cmux event_bus so future
# Feed panel + crash replay can consume them. Best-effort import — older
# installs without event_bus still boot.
try:
    from term.event_bus import publish as _bus_publish
    _HAVE_BUS = True
except Exception:
    _HAVE_BUS = False
    def _bus_publish(name, category, payload=None):  # noqa: E501
        return None


SANCTUM_ROOT = Path(os.environ.get("SANCTUM_ROOT") or "D:/Sinister Sanctum")
PROJECTS_JSON = SANCTUM_ROOT / "automations" / "session-templates" / "projects.json"
BOTS_INDEX = SANCTUM_ROOT / "bots" / "_INDEX.md"
SKILLS_INDEX = SANCTUM_ROOT / "skills" / "_INDEX.md"
HEARTBEATS_DIR = SANCTUM_ROOT / "_shared-memory" / "heartbeats"
INBOX_DIR = SANCTUM_ROOT / "_shared-memory" / "inbox"
SELF_SLUG = "sinister-term"
SELF_DISPLAY = "Sinister Term"
CROSS_AGENT_DIR = SANCTUM_ROOT / "_shared-memory" / "cross-agent"
PROGRESS_FILE = SANCTUM_ROOT / "_shared-memory" / "PROGRESS" / "Sinister Term.md"


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
  /inbox [n]                List our inbox or read message n
  /cross-agent [n]          List recent cross-agent messages or read one (alias /ca)
  /ask <agent> <message>    Drop an [ASK] in another agent's inbox
  /progress [add <msg>]     Show top 5 PROGRESS entries (or add a new one)
  /recall <term> [term2...]  Search the brain at _shared-memory/knowledge/*.md
  /swarm <sub> [args]       Fan-out: list / spawn / dm / broadcast (try /swarm)
  /events [N] [--cat C] [--name N] [--disk]  Tail cmux event_bus (ring or jsonl)
  /ascii [on|off|status|project K|list]  Control SA-PH6 living-entity overlay
  /health                   Single-screen sterm dashboard (version/branch/agents/inbox/bridge/bus)
  /uptime                   Session duration + event count + ascii frames + cache size
  /branch                   Current branch + upstream + ahead/behind + dirty count + HEAD
  /touch [status...]        Pulse sterm heartbeat NOW (+ optional status note)
  /locks                    List active mesh-coordinator locks (owner / path / ttl / age)
  /utterances [N] [--new --mine --search X]   Tail operator-utterances.jsonl (alias /utt)
  /watch <relpath> [N]      Tail any jsonl under _shared-memory/ (sandboxed)
  /agents [N --fresh --stale --slug X]   Richer heartbeats (mode + branch + note)
  /find <glob> [--sanctum --type d|f] [N]   Recursive name search (skips .git/venv/etc)
  /doctrine [--sanctum --search X]   List operator hard-canonicals from CLAUDE.md
  /crashlog [N --mine --module X]   Read eve-crash-log.jsonl (alias /crashes)
  /grep <pattern> [path] [--glob X] [-i] [N]   Content search (skips .git/venv/binaries)
  /fu [N --priority --kind --mine --unacked]   Tail fleet-updates.jsonl (alias /fleet-updates)
  /incidents [N --severity --kind --agent]   Tail eve-incidents.jsonl (degraded states)
  /me                       Show our own heartbeat in detail (drilldown of /agents)
  /diff [--staged --unstaged --name-only] [path]   git diff --stat summary
  /version                  Composite version dashboard (sterm/ascii/python/deps/git/modules)
  /alias [name=val|remove n] List aliases, define one, or remove one
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


def _probe_port(host: str, port: int, timeout: float = 1.0) -> bool:
    """RKOJ-ELENO :: 2026-05-23 :: 1s TCP probe — True iff something's listening."""
    import socket
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def cmd_mind(_args: list[str]) -> CommandResult:
    """Open Sinister Mind in browser — but only if the mind server answers a
    1-second probe first. RKOJ-ELENO :: 2026-05-23 :: avoids the silent
    chrome-with-broken-page UX when the server isn't running."""
    import webbrowser
    host = os.environ.get("SINISTER_MIND_HOST", "localhost")
    try:
        port = int(os.environ.get("SINISTER_MIND_PORT", "5079"))
    except ValueError:
        port = 5079
    url = f"http://{host}:{port}/"
    if not _probe_port(host, port, timeout=1.0):
        return CommandResult(
            True,
            f"mind server not reachable at {host}:{port} — start with "
            f"`sinister-mind serve` or set SINISTER_MIND_HOST=... / "
            f"SINISTER_MIND_PORT=...",
        )
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


def _utc_ts_filename() -> str:
    import time as _t
    return _t.strftime("%Y-%m-%dT%H%MZ", _t.gmtime())


def _utc_ts_iso() -> str:
    import time as _t
    return _t.strftime("%Y-%m-%dT%H:%M:%SZ", _t.gmtime())


def cmd_inbox(args: list[str]) -> CommandResult:
    """List our inbox messages, or show one with /inbox <n>."""
    my_inbox = INBOX_DIR / SELF_SLUG
    if not my_inbox.exists():
        return CommandResult(True, "(no inbox dir)")
    files = sorted(my_inbox.glob("*.json"))
    if not files:
        return CommandResult(True, "Inbox is empty.")

    if args and args[0].isdigit():
        idx = int(args[0])
        if 1 <= idx <= len(files):
            return CommandResult(True, files[idx - 1].read_text(encoding="utf-8", errors="replace"))
        return CommandResult(True, f"out of range (1..{len(files)})")

    rows = [f"Inbox ({len(files)} message(s)):"]
    for i, f in enumerate(files, 1):
        try:
            data = json.loads(f.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            rows.append(f"  {i}. {f.name}  (unparseable)")
            continue
        tag = data.get("tag", "")
        frm = data.get("from_display") or data.get("from", "?")
        subj = data.get("subject", "(no subject)")
        ts = data.get("ts_utc", "")
        rows.append(f"  {i}. {tag:<12} {frm:<20} {ts}  {subj[:60]}")
    rows.append("\n(use /inbox <n> to read one)")
    return CommandResult(True, "\n".join(rows))


def cmd_cross_agent(args: list[str]) -> CommandResult:
    """List or read cross-agent messages."""
    if not CROSS_AGENT_DIR.exists():
        return CommandResult(True, "(no cross-agent dir)")
    files = sorted(CROSS_AGENT_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    if args and args[0].isdigit():
        idx = int(args[0])
        if 1 <= idx <= len(files):
            return CommandResult(True, files[idx - 1].read_text(encoding="utf-8", errors="replace")[:4000])
        return CommandResult(True, f"out of range (1..{len(files)})")
    if not files:
        return CommandResult(True, "(no cross-agent messages)")
    rows = ["Recent cross-agent messages (newest first):"]
    for i, f in enumerate(files[:20], 1):
        rows.append(f"  {i}. {f.name}")
    rows.append("\n(use /cross-agent <n> to read one)")
    return CommandResult(True, "\n".join(rows))


def cmd_ask(args: list[str]) -> CommandResult:
    """Write an [ASK] message into another agent's inbox.

    Usage: /ask <agent-slug> <message...>
    """
    if len(args) < 2:
        return CommandResult(True, "usage: /ask <agent-slug> <message...>\nknown slugs: " + ", ".join(_known_agent_slugs()))
    target = args[0]
    msg = " ".join(args[1:])
    target_dir = INBOX_DIR / target
    if not target_dir.exists():
        return CommandResult(True, f"unknown agent inbox: {target_dir}")
    ts_iso = _utc_ts_iso()
    ts_file = _utc_ts_filename()
    body = {
        "_author": "RKOJ-ELENO :: 2026-05-21",
        "tag": "[ASK]",
        "from": SELF_SLUG,
        "from_display": SELF_DISPLAY,
        "to": target,
        "ts_utc": ts_iso,
        "subject": msg[:80],
        "message": msg,
    }
    path = target_dir / f"{ts_file}-ask-from-{SELF_SLUG}.json"
    path.write_text(json.dumps(body, indent=2), encoding="utf-8")
    return CommandResult(True, f"[ASK] -> {path.relative_to(SANCTUM_ROOT)}")


def _known_agent_slugs() -> list[str]:
    if not INBOX_DIR.exists():
        return []
    return sorted(d.name for d in INBOX_DIR.iterdir() if d.is_dir())


def cmd_progress(args: list[str]) -> CommandResult:
    """Show top 5 PROGRESS entries, or prepend a new one with /progress add <msg>."""
    if args and args[0] == "add":
        if len(args) < 2:
            return CommandResult(True, "usage: /progress add <message>")
        new_msg = " ".join(args[1:])
        import time as _t
        header = "## " + _t.strftime("%Y-%m-%d %H:%M", _t.gmtime()) + " — note: " + new_msg[:80]
        body = new_msg if len(new_msg) > 80 else ""
        entry = header + ("\n" + body if body else "") + "\n\n"

        existing = ""
        if PROGRESS_FILE.exists():
            existing = PROGRESS_FILE.read_text(encoding="utf-8")
            # Prepend after the leading header block (insert above the first `## ` line)
            lines = existing.split("\n")
            insert_at = 0
            for i, ln in enumerate(lines):
                if ln.startswith("## ") and "YYYY-MM-DD" not in ln:
                    insert_at = i
                    break
            else:
                insert_at = len(lines)
            new_text = "\n".join(lines[:insert_at]) + "\n" + entry + "\n".join(lines[insert_at:])
        else:
            new_text = "# Agent: Sinister Term\n\n---\n\n" + entry
        PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
        PROGRESS_FILE.write_text(new_text, encoding="utf-8")
        return CommandResult(True, f"progress entry added.")

    if not PROGRESS_FILE.exists():
        return CommandResult(True, "(no PROGRESS file yet — try /progress add <message>)")
    text = PROGRESS_FILE.read_text(encoding="utf-8")
    # Take the first 5 `## ` blocks
    blocks: list[str] = []
    current: list[str] = []
    for line in text.split("\n"):
        if line.startswith("## "):
            if current:
                blocks.append("\n".join(current).rstrip())
                if len(blocks) >= 5:
                    break
            current = [line]
        elif current:
            current.append(line)
    if current and len(blocks) < 5:
        blocks.append("\n".join(current).rstrip())
    return CommandResult(True, "Recent progress:\n\n" + "\n\n".join(blocks[:5]))


# RKOJ-ELENO :: 2026-05-23 :: alias builtin — list / define / remove
def cmd_alias(args: list[str]) -> CommandResult:
    """List aliases, define one (name=value), or remove one (remove <name>).

    Examples:
      /alias                 -> list
      /alias ll=ls -la       -> define
      /alias remove ll       -> delete
    """
    aliases = load_aliases()
    if not args:
        if not aliases:
            return CommandResult(True, "(no aliases — try /alias ll=ls -la)")
        rows = ["Aliases:"]
        for name in sorted(aliases):
            rows.append(f"  {name:<16} = {aliases[name]}")
        return CommandResult(True, "\n".join(rows))
    if args[0] == "remove":
        if len(args) < 2:
            return CommandResult(True, "usage: /alias remove <name>")
        name = args[1]
        if name not in aliases:
            return CommandResult(True, f"no such alias '{name}'")
        del aliases[name]
        save_aliases(aliases)
        return CommandResult(True, f"removed alias '{name}'")
    # define: rejoin args, then split on first '='
    raw = " ".join(args)
    if "=" not in raw:
        return CommandResult(True, "usage: /alias <name>=<expansion>  or  /alias remove <name>")
    name, _, value = raw.partition("=")
    name = name.strip()
    value = value.strip()
    if not name or not value:
        return CommandResult(True, "usage: /alias <name>=<expansion>")
    aliases[name] = value
    save_aliases(aliases)
    return CommandResult(True, f"alias {name} = {value}")


def cmd_recall(args: list[str]) -> CommandResult:
    """P2-1 (iter-50): search the brain at _shared-memory/knowledge/*.md
    for entries matching the given query terms. Returns the top-N matches
    with title + path + score. ALL local file-system work — no MCP, no
    network. Operator can then `cat` the path or open in their editor.

    Usage: /recall <term> [<term2> ...]
    Examples:
      /recall jcode logging
      /recall paste handler
      /recall sa-ph5 intensity
    """
    if not args:
        return CommandResult(True,
            "usage: /recall <term> [<term2> ...]\n"
            "Searches _shared-memory/knowledge/*.md for matching entries.")
    knowledge_dir = SANCTUM_ROOT / "_shared-memory" / "knowledge"
    if not knowledge_dir.exists():
        return CommandResult(True, f"(no knowledge dir at {knowledge_dir})")
    terms = [t.lower() for t in args if t]
    matches: list[tuple[int, Path, str]] = []  # (score, path, title)
    try:
        for md in knowledge_dir.glob("*.md"):
            if md.name.startswith("_"):
                continue
            try:
                # Read first 4 KiB — enough for title + lede + most context
                with md.open("r", encoding="utf-8", errors="replace") as fh:
                    head = fh.read(4096)
            except OSError:
                continue
            head_low = head.lower()
            name_low = md.name.lower()
            score = 0
            for t in terms:
                score += head_low.count(t) * 1
                score += name_low.count(t) * 5  # filename hits weighted higher
            if score > 0:
                # Pull title from first `# ` line, else use stem
                title = md.stem
                for ln in head.splitlines():
                    if ln.startswith("# "):
                        title = ln[2:].strip()
                        break
                matches.append((score, md, title))
    except OSError as e:
        return CommandResult(True, f"recall failed: {e}")
    if not matches:
        try:
            _bus_publish("recall", "agent",
                         payload={"terms": list(args)[:8], "match_count": 0})
        except Exception:
            pass
        return CommandResult(True, f"(no matches for {' '.join(args)})")
    matches.sort(key=lambda x: (-x[0], x[1].name))
    top_n = matches[:8]
    lines = [f"Recall: {len(matches)} match{'es' if len(matches) != 1 else ''}"
             f" (showing top {len(top_n)}) for: {' '.join(args)}"]
    for score, path, title in top_n:
        try:
            rel = path.relative_to(SANCTUM_ROOT)
        except ValueError:
            rel = path
        lines.append(f"  [{score:>3}] {title}")
        lines.append(f"        {rel.as_posix()}")
    try:
        _bus_publish("recall", "agent",
                     payload={"terms": list(args)[:8], "match_count": len(matches),
                              "top_titles": [t for _, _, t in top_n[:3]]})
    except Exception:
        pass
    return CommandResult(True, "\n".join(lines))


_HEARTBEAT_PATH = SANCTUM_ROOT / "_shared-memory" / "heartbeats" / f"{SELF_SLUG}.json"
_MESH_LOCKS_DIR = SANCTUM_ROOT / "_shared-memory" / "mesh-locks"
_UTTERANCES_PATH = SANCTUM_ROOT / "_shared-memory" / "operator-utterances.jsonl"


_CRASH_LOG_PATH = SANCTUM_ROOT / "_shared-memory" / "eve-crash-log.jsonl"


_FLEET_UPDATES_PATH = SANCTUM_ROOT / "_shared-memory" / "fleet-updates.jsonl"
_INCIDENTS_PATH = SANCTUM_ROOT / "_shared-memory" / "eve-incidents.jsonl"


def cmd_version(_args: list[str]) -> CommandResult:
    """iter-71: composite version dashboard.

    Shows: sinister-term version, sinister-ascii version (if importable),
    Python version, prompt_toolkit version, rich version, pytest version,
    git HEAD short-sha, term module count. Pure introspection; every probe
    is try/except'd so missing-package paths don't break the panel.
    """
    import sys as _sys
    lines = ["Version dashboard:"]

    # sinister-term
    try:
        from term import __version__ as _v
        lines.append(f"  sinister-term:  {_v}")
    except Exception as e:
        lines.append(f"  sinister-term:  ? ({e})")

    # sinister-ascii
    try:
        from term.ascii_bridge import _ensure_ascii_on_path
        if _ensure_ascii_on_path():
            from sinister_ascii import __version__ as _va  # type: ignore
            lines.append(f"  sinister-ascii: {_va}")
        else:
            lines.append("  sinister-ascii: (not importable)")
    except Exception as e:
        lines.append(f"  sinister-ascii: ? ({e})")

    # Python + key deps
    lines.append(
        f"  python:         {_sys.version_info.major}.{_sys.version_info.minor}.{_sys.version_info.micro}"
    )
    for pkg in ("prompt_toolkit", "rich", "pytest"):
        try:
            mod = __import__(pkg)
            ver = getattr(mod, "__version__", "?")
            lines.append(f"  {pkg:<14}: {ver}")
        except Exception:
            lines.append(f"  {pkg:<14}: (not installed)")

    # git HEAD short-sha
    sha = _git_one(["rev-parse", "--short", "HEAD"])
    if sha:
        lines.append(f"  git HEAD:       {sha}")
    else:
        lines.append("  git HEAD:       (not in a git repo)")

    # term module count (cheap glob — term/source/term/*.py)
    try:
        # __file__ = projects/sinister-term/source/term/commands.py
        term_dir = Path(__file__).resolve().parent
        modules = [p.name for p in term_dir.glob("*.py")
                   if not p.name.startswith("__")]
        lines.append(
            f"  term modules:   {len(modules)} files in {term_dir.name}/"
        )
    except Exception as e:
        lines.append(f"  term modules:   ? ({e})")

    # builtin command count (introspection of COMMANDS dict)
    try:
        # COMMANDS is defined later in this same module; access via globals
        cmds = globals().get("COMMANDS")
        if isinstance(cmds, dict):
            lines.append(f"  builtins:       {len(cmds)} commands registered")
    except Exception:
        pass

    return CommandResult(True, "\n".join(lines))


def cmd_diff(args: list[str]) -> CommandResult:
    """iter-70: git diff --stat for the current working tree.

    Shows unstaged + staged changes as compact `path | +M -N` rows so the
    operator can survey what's about to land before /branch + a commit.
    No diff body — keep the line count sane. Composes with /branch (which
    shows ahead/behind + dirty count).

    Usage:
      /diff                          unstaged + staged summary
      /diff --staged                 only staged
      /diff --unstaged               only unstaged
      /diff <path>                   restrict diff to a path
      /diff --name-only              just the changed file names
    """
    only_staged = False
    only_unstaged = False
    name_only = False
    path_arg: str | None = None
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--staged":
            only_staged = True
            i += 1
            continue
        if a == "--unstaged":
            only_unstaged = True
            i += 1
            continue
        if a == "--name-only":
            name_only = True
            i += 1
            continue
        if a.startswith("-"):
            return CommandResult(True,
                f"unknown flag: {a}. Try /diff with no args for usage.")
        if path_arg is None:
            path_arg = a
        else:
            return CommandResult(True,
                f"unexpected arg: {a} (already have path {path_arg!r})")
        i += 1

    # Verify we're in a git repo
    branch = _git_one(["rev-parse", "--abbrev-ref", "HEAD"])
    if branch is None:
        return CommandResult(True, "(not in a git repo)")

    def _run_diff(staged: bool) -> str | None:
        flags = ["diff", "--stat"] if not name_only else ["diff", "--name-only"]
        if staged:
            flags.append("--staged")
        if path_arg:
            flags.append("--")
            flags.append(path_arg)
        return _git_one(flags, timeout_s=4.0)

    show_unstaged = not only_staged
    show_staged = not only_unstaged
    sections: list[tuple[str, str]] = []
    if show_unstaged:
        u = _run_diff(staged=False)
        if u:
            sections.append(("unstaged", u))
    if show_staged:
        s = _run_diff(staged=True)
        if s:
            sections.append(("staged", s))

    if not sections:
        return CommandResult(True, "(no changes)")

    out: list[str] = []
    out.append(f"Diff (branch={branch}):")
    for label, body in sections:
        out.append(f"  [{label}]")
        # Indent each line + cap line count so massive diffs don't flood
        body_lines = [l for l in body.splitlines() if l.strip()]
        MAX_LINES = 40
        truncated = ""
        if len(body_lines) > MAX_LINES:
            truncated = f"  ... ({len(body_lines) - MAX_LINES} more)"
            body_lines = body_lines[:MAX_LINES]
        for ln in body_lines:
            # Truncate very long single lines too
            if len(ln) > 110:
                ln = ln[:107] + "..."
            out.append(f"    {ln}")
        if truncated:
            out.append(truncated)
    return CommandResult(True, "\n".join(out))


def cmd_me(_args: list[str]) -> CommandResult:
    """iter-69: show sinister-term's own heartbeat in detail.

    Operator-introspection: what fields does the spawner + loop + /touch
    write into MY heartbeat? Drilldown view that the multi-agent `/agents`
    summary can't show without bloating the row layout.
    """
    if not _HEARTBEAT_PATH.exists():
        try:
            rel = _HEARTBEAT_PATH.relative_to(SANCTUM_ROOT).as_posix()
        except ValueError:
            rel = str(_HEARTBEAT_PATH)
        return CommandResult(True,
            f"(no heartbeat for sinister-term yet at {rel}\n"
            f" — try /touch to write one)")
    try:
        text = _HEARTBEAT_PATH.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return CommandResult(True, f"/me failed: {e}")

    try:
        data = json.loads(text)
        if not isinstance(data, dict):
            data = {"raw": str(data)[:200]}
    except Exception as e:
        return CommandResult(True,
            f"/me: heartbeat JSON corrupt ({e})\n"
            f"raw: {text[:400]}")

    import time as _t
    try:
        mtime = _HEARTBEAT_PATH.stat().st_mtime
        age_s = max(0.0, _t.time() - mtime)
        age = _format_duration(age_s)
    except OSError:
        age = "?"

    try:
        rel = _HEARTBEAT_PATH.relative_to(SANCTUM_ROOT).as_posix()
    except ValueError:
        rel = str(_HEARTBEAT_PATH)

    lines = [f"My heartbeat ({rel}, age {age}):"]
    # Preferred-order field rendering — known fields first, then anything else
    PREFERRED_KEYS = [
        "agent", "ts_utc", "alive", "mode", "branch_intent",
        "status_note", "last_shipped", "cwd", "via",
    ]
    seen: set[str] = set()
    for k in PREFERRED_KEYS:
        if k not in data:
            continue
        seen.add(k)
        v = data[k]
        # Truncate long string values
        if isinstance(v, str) and len(v) > 200:
            v = v[:197] + "..."
        lines.append(f"  {k:<16}: {v}")
    # Any remaining keys (forward-compat with new fields)
    for k, v in data.items():
        if k in seen:
            continue
        if isinstance(v, str) and len(v) > 200:
            v = v[:197] + "..."
        lines.append(f"  {k:<16}: {v}")

    return CommandResult(True, "\n".join(lines))


def cmd_incidents(args: list[str]) -> CommandResult:
    """iter-68: read fleet-wide eve-incidents.jsonl.

    Incidents are higher-level than crashes — operator-visible degraded
    states (oauth slot empty, watchdog tripped, sister-agent stuck, etc).
    Logged by various sanctum automations.

    Usage:
      /incidents                       last 10
      /incidents N                     last N (1..500)
      /incidents --severity high       filter by severity
      /incidents --kind X              filter by kind/type substring
      /incidents --agent <slug>        filter by agent/source slug
    """
    limit = 10
    sev: str | None = None
    kind_filter: str | None = None
    agent_filter: str | None = None
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--severity" and i + 1 < len(args):
            sev = args[i + 1].lower()
            i += 2
            continue
        if a == "--kind" and i + 1 < len(args):
            kind_filter = args[i + 1].lower()
            i += 2
            continue
        if a == "--agent" and i + 1 < len(args):
            agent_filter = args[i + 1].lower()
            i += 2
            continue
        try:
            limit = max(1, min(500, int(a)))
        except ValueError:
            return CommandResult(True,
                f"unknown arg: {a}. Try /incidents with no args for usage.")
        i += 1

    if not _INCIDENTS_PATH.exists():
        try:
            rel = _INCIDENTS_PATH.relative_to(SANCTUM_ROOT).as_posix()
        except ValueError:
            rel = str(_INCIDENTS_PATH)
        return CommandResult(True, f"(no incidents log at {rel})")

    rows: list[dict] = []
    try:
        with _INCIDENTS_PATH.open("r", encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    obj = json.loads(ln)
                    if isinstance(obj, dict):
                        rows.append(obj)
                except Exception:
                    continue
    except OSError as e:
        return CommandResult(True, f"/incidents failed: {e}")

    if sev:
        rows = [r for r in rows
                if (r.get("severity") or r.get("level") or "").lower() == sev]
    if kind_filter:
        rows = [r for r in rows
                if kind_filter in (r.get("kind") or r.get("type") or "").lower()]
    if agent_filter:
        rows = [r for r in rows
                if agent_filter in (r.get("agent") or r.get("source") or "").lower()]

    if not rows:
        flt = []
        if sev: flt.append(f"--severity {sev}")
        if kind_filter: flt.append(f"--kind {kind_filter}")
        if agent_filter: flt.append(f"--agent {agent_filter}")
        return CommandResult(True,
            f"(no incidents{' (' + ' '.join(flt) + ')' if flt else ''})")

    shown = rows[-limit:]
    try:
        rel = _INCIDENTS_PATH.relative_to(SANCTUM_ROOT).as_posix()
    except ValueError:
        rel = str(_INCIDENTS_PATH)
    out = [f"Incidents: {len(shown)} of {len(rows)} in {rel}"]
    for r in shown:
        ts = (r.get("ts_utc") or "?")[:19] + "Z"
        sev_v = (r.get("severity") or r.get("level") or "?").lower()
        if sev_v == "high" or sev_v == "critical":
            badge = "[HI]"
        elif sev_v == "low":
            badge = "[lo]"
        else:
            badge = "[no]"
        kind = (r.get("kind") or r.get("type") or "?")[:16]
        agent = (r.get("agent") or r.get("source") or "?")[:14]
        msg = (r.get("message") or r.get("detail") or r.get("description") or "")[:60]
        out.append(f"  {ts}  {badge}  {kind:<16}  {agent:<14}  {msg}")
    return CommandResult(True, "\n".join(out))


def cmd_fleet_updates(args: list[str]) -> CommandResult:
    """iter-67: read fleet-updates.jsonl (alias /fu).

    Cross-lane broadcast log: every agent posts here via
    `automations/fleet-update.ps1 -Action Push`. Surface row shape:
      {id, ts_utc, priority, kind, message, target_slugs, pushed_by, acks}

    Usage:
      /fu                          last 10
      /fu N                        last N (1..500)
      /fu --priority high          only high-pri rows
      /fu --kind doctrine_update   filter by kind
      /fu --mine                   only target_slugs naming sinister-term, OR
                                   pushed_by=sinister-term
      /fu --unacked                only rows NOT acked by sinister-term yet
    """
    limit = 10
    pri: str | None = None
    kind_filter: str | None = None
    only_mine = False
    only_unacked = False
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--priority" and i + 1 < len(args):
            pri = args[i + 1].lower()
            i += 2
            continue
        if a == "--kind" and i + 1 < len(args):
            kind_filter = args[i + 1].lower()
            i += 2
            continue
        if a == "--mine":
            only_mine = True
            i += 1
            continue
        if a == "--unacked":
            only_unacked = True
            i += 1
            continue
        try:
            limit = max(1, min(500, int(a)))
        except ValueError:
            return CommandResult(True,
                f"unknown arg: {a}. Try /fu with no args for usage.")
        i += 1

    if not _FLEET_UPDATES_PATH.exists():
        try:
            rel = _FLEET_UPDATES_PATH.relative_to(SANCTUM_ROOT).as_posix()
        except ValueError:
            rel = str(_FLEET_UPDATES_PATH)
        return CommandResult(True, f"(no fleet-updates at {rel})")

    rows: list[dict] = []
    try:
        with _FLEET_UPDATES_PATH.open("r", encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    obj = json.loads(ln)
                    if isinstance(obj, dict):
                        rows.append(obj)
                except Exception:
                    continue
    except OSError as e:
        return CommandResult(True, f"/fu failed: {e}")

    if pri:
        rows = [r for r in rows if (r.get("priority") or "").lower() == pri]
    if kind_filter:
        rows = [r for r in rows
                if kind_filter in (r.get("kind") or "").lower()]
    if only_mine:
        def _is_mine(r: dict) -> bool:
            if (r.get("pushed_by") or "").lower() == SELF_SLUG:
                return True
            tgt = r.get("target_slugs") or {}
            # target_slugs can be dict, list, or string in observed data
            if isinstance(tgt, dict):
                return SELF_SLUG in {k.lower() for k in tgt.keys()}
            if isinstance(tgt, list):
                return SELF_SLUG in {str(s).lower() for s in tgt}
            if isinstance(tgt, str):
                return SELF_SLUG.lower() in tgt.lower()
            return False
        rows = [r for r in rows if _is_mine(r)]
    if only_unacked:
        rows = [r for r in rows
                if SELF_SLUG not in (r.get("acks") or [])]

    if not rows:
        flt = []
        if pri: flt.append(f"--priority {pri}")
        if kind_filter: flt.append(f"--kind {kind_filter}")
        if only_mine: flt.append("--mine")
        if only_unacked: flt.append("--unacked")
        return CommandResult(True,
            f"(no fleet-updates{' (' + ' '.join(flt) + ')' if flt else ''})")

    shown = rows[-limit:]
    try:
        rel = _FLEET_UPDATES_PATH.relative_to(SANCTUM_ROOT).as_posix()
    except ValueError:
        rel = str(_FLEET_UPDATES_PATH)
    out = [f"Fleet-updates: {len(shown)} of {len(rows)} in {rel}"]
    for r in shown:
        ts = (r.get("ts_utc") or "?")[:19] + "Z"
        pri_label = (r.get("priority") or "?")[:5]
        # Priority badge color hint: high → [HI], normal → [no], low → [lo]
        if pri_label == "high":
            badge = "[HI]"
        elif pri_label == "low":
            badge = "[lo]"
        else:
            badge = "[no]"
        kind = (r.get("kind") or "?")[:16]
        pusher = (r.get("pushed_by") or "?")[:14]
        msg = (r.get("message") or "")[:70]
        n_acks = len(r.get("acks") or [])
        ack_str = f"({n_acks} ack)" if n_acks else ""
        out.append(f"  {ts}  {badge}  {kind:<16}  {pusher:<14}  {msg} {ack_str}")
    return CommandResult(True, "\n".join(out))


def cmd_grep(args: list[str]) -> CommandResult:
    """iter-66: content search across files under cwd or a sub-path.

    Pure-Python re.search; honors the same SKIP_DIRS as /find. Cap: scans
    up to 2000 files, returns up to 50 matches (configurable via N arg).
    Binary files (anything with NUL in first 4 KiB) silently skipped.

    Usage:
      /grep <pattern>                          search under cwd
      /grep <pattern> <relpath>                search under cwd/<relpath>
      /grep <pattern> --glob *.py              only files matching glob
      /grep <pattern> --ignore-case            case-insensitive (-i alias)
      /grep <pattern> -i                       case-insensitive
      /grep <pattern> N                        cap matches at N (1..500)
    """
    if not args:
        return CommandResult(True,
            "usage: /grep <pattern> [<relpath>] [--glob *.py] [-i] [N]\n"
            "  e.g. /grep 'def cmd_' --glob *.py\n"
            "       /grep TODO _shared-memory")
    pattern_str = args[0]
    sub_path: str | None = None
    glob_pat: str | None = None
    ignore_case = False
    limit = 50
    SCAN_CAP = 2000

    i = 1
    while i < len(args):
        a = args[i]
        if a == "--glob" and i + 1 < len(args):
            glob_pat = args[i + 1]
            i += 2
            continue
        if a in ("-i", "--ignore-case"):
            ignore_case = True
            i += 1
            continue
        if a.startswith("-"):
            return CommandResult(True,
                f"unknown flag: {a}. Try /grep with no args for usage.")
        # Numeric → limit; otherwise → relpath
        try:
            limit = max(1, min(500, int(a)))
        except ValueError:
            if sub_path is None:
                sub_path = a
            else:
                return CommandResult(True,
                    f"unexpected arg: {a} (already have sub-path {sub_path!r})")
        i += 1

    import re as _re
    try:
        flags = _re.IGNORECASE if ignore_case else 0
        rx = _re.compile(pattern_str, flags)
    except _re.error as e:
        return CommandResult(True, f"bad regex: {e}")

    root = Path.cwd() if sub_path is None else (Path.cwd() / sub_path)
    if not root.exists():
        return CommandResult(True, f"path does not exist: {root}")

    SKIP_DIRS = {".git", "node_modules", "__pycache__", ".pytest_cache",
                 "venv", ".venv", "dist", "build", ".idea", ".vscode"}

    # Use either glob iterator or rglob("*")
    if glob_pat:
        iterator = root.rglob(glob_pat)
    elif root.is_file():
        iterator = iter([root])
    else:
        iterator = root.rglob("*")

    matches: list[tuple[str, int, str]] = []  # (rel-path, line-no, text)
    scanned = 0
    files_scanned = 0
    overflow = False
    try:
        for p in iterator:
            scanned += 1
            if scanned > SCAN_CAP:
                overflow = True
                break
            if any(part in SKIP_DIRS for part in p.parts):
                continue
            try:
                if not p.is_file():
                    continue
            except OSError:
                continue
            files_scanned += 1
            try:
                with p.open("rb") as fh:
                    head = fh.read(4096)
                    if b"\x00" in head:
                        continue  # binary
                    rest = fh.read()
                full_bytes = head + rest
                text = full_bytes.decode("utf-8", errors="replace")
            except OSError:
                continue
            for lineno, ln in enumerate(text.splitlines(), start=1):
                if rx.search(ln):
                    try:
                        rel = p.relative_to(root).as_posix()
                    except ValueError:
                        rel = str(p)
                    matches.append((rel, lineno, ln.rstrip()))
                    if len(matches) >= limit + 1:
                        break
            if len(matches) >= limit + 1:
                overflow = True
                break
    except (OSError, ValueError) as e:
        return CommandResult(True, f"/grep failed: {e}")

    if not matches:
        scope = f"{root}"
        if glob_pat:
            scope += f" (glob={glob_pat})"
        return CommandResult(True, f"(no matches for /{pattern_str}/ in {scope})")

    shown = matches[:limit]
    truncated = " (capped)" if overflow else ""
    suffix = f" — {files_scanned} files scanned"
    lines = [f"Grep: {len(shown)} hit{'s' if len(shown) != 1 else ''}"
             f" for /{pattern_str}/ in {root}{suffix}{truncated}"]
    for rel, lineno, text in shown:
        # Truncate long lines
        body = text if len(text) <= 100 else text[:97] + "..."
        lines.append(f"  {rel}:{lineno}: {body}")
    return CommandResult(True, "\n".join(lines))


def cmd_crashlog(args: list[str]) -> CommandResult:
    """iter-65: read the fleet crash log so the operator can triage from sterm.

    `_shared-memory/eve-crash-log.jsonl` is the fleet-wide crash sink that
    iter-45 term/crash_recovery.py + many sanctum scripts write to. Each
    row: {ts_utc, module, error, [context], [agent]}.

    Usage:
      /crashlog                       last 10 crashes
      /crashlog N                     last N (1..500)
      /crashlog --mine                only sinister-term-emitted entries
      /crashlog --module foo          filter by module substring
      /crashes ...                    alias
    """
    limit = 10
    only_mine = False
    module_filter: str | None = None
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--mine":
            only_mine = True
            i += 1
            continue
        if a == "--module" and i + 1 < len(args):
            module_filter = args[i + 1].lower()
            i += 2
            continue
        try:
            limit = max(1, min(500, int(a)))
        except ValueError:
            return CommandResult(True,
                f"unknown arg: {a}. Try /crashlog with no args for usage.")
        i += 1

    if not _CRASH_LOG_PATH.exists():
        try:
            rel = _CRASH_LOG_PATH.relative_to(SANCTUM_ROOT).as_posix()
        except ValueError:
            rel = str(_CRASH_LOG_PATH)
        return CommandResult(True, f"(no crash log at {rel})")

    rows: list[dict] = []
    try:
        with _CRASH_LOG_PATH.open("r", encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    obj = json.loads(ln)
                    if isinstance(obj, dict):
                        rows.append(obj)
                except Exception:
                    continue
    except OSError as e:
        return CommandResult(True, f"/crashlog failed: {e}")

    if only_mine:
        # term/* modules + sinister-term agent
        def _is_mine(r: dict) -> bool:
            mod = (r.get("module") or "").lower()
            agent = (r.get("agent") or "").lower()
            return mod.startswith("term.") or agent == SELF_SLUG
        rows = [r for r in rows if _is_mine(r)]
    if module_filter:
        rows = [r for r in rows
                if module_filter in (r.get("module") or "").lower()]

    if not rows:
        flt = []
        if only_mine: flt.append("--mine")
        if module_filter: flt.append(f"--module {module_filter}")
        return CommandResult(True,
            f"(no crashes{' (' + ' '.join(flt) + ')' if flt else ''})")

    shown = rows[-limit:]
    try:
        rel = _CRASH_LOG_PATH.relative_to(SANCTUM_ROOT).as_posix()
    except ValueError:
        rel = str(_CRASH_LOG_PATH)
    out = [f"Crashes: {len(shown)} of {len(rows)} in {rel}"]
    for r in shown:
        ts = (r.get("ts_utc") or "?")[:19] + "Z"
        mod = (r.get("module") or "?")[:28]
        err = (r.get("error") or r.get("err") or "?")
        if len(err) > 70:
            err = err[:67] + "..."
        out.append(f"  {ts}  {mod:<28}  {err}")
    return CommandResult(True, "\n".join(out))


def cmd_doctrine(args: list[str]) -> CommandResult:
    """iter-64: list the operator hard-canonical directives from CLAUDE.md.

    The Sanctum CLAUDE.md uses `## Operator hard-canonical YYYY-MM-DD — <TITLE>`
    section headings for binding fleet doctrine. This builtin scans the
    top-level Sanctum CLAUDE.md (and the project-level one if present) and
    prints each heading + the FIRST quoted operator-verbatim line found
    under it so the operator can see the canonicals at a glance.

    Usage:
      /doctrine                       all hard-canonicals from both CLAUDE.md files
      /doctrine --sanctum             only the top-level CLAUDE.md
      /doctrine --search <substring>  filter by case-insensitive substring on heading
    """
    sanctum_md = SANCTUM_ROOT / "CLAUDE.md"
    # Project-level CLAUDE.md sits two dirs up from term/source (term/source -> sinister-term/)
    project_md = SANCTUM_ROOT / "projects" / "sinister-term" / "CLAUDE.md"

    only_sanctum = False
    search_term: str | None = None
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--sanctum":
            only_sanctum = True
            i += 1
            continue
        if a == "--search" and i + 1 < len(args):
            search_term = args[i + 1].lower()
            i += 2
            continue
        return CommandResult(True,
            f"unknown arg: {a}. Try /doctrine with no args for usage.")

    sources = [sanctum_md]
    if not only_sanctum:
        sources.append(project_md)

    import re as _re
    heading_re = _re.compile(r"^##\s+Operator hard-canonical\s+(\d{4}-\d{2}-\d{2})\s+[—-]+\s+(.+)$", _re.IGNORECASE)
    verbatim_re = _re.compile(r"\*?\"([^\"]{4,})\"\*?")

    rows: list[tuple[str, str, str, str]] = []  # (source-label, date, title, first-quote)
    for md_path in sources:
        if not md_path.exists():
            continue
        label = "sanctum" if md_path == sanctum_md else "lane"
        try:
            text = md_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        # Walk line-by-line; when we hit a heading, scan the next ~20 lines
        # for a verbatim quote.
        lines = text.splitlines()
        for idx, ln in enumerate(lines):
            m = heading_re.match(ln.strip())
            if not m:
                continue
            date, title = m.group(1), m.group(2).strip()
            if search_term and search_term not in title.lower():
                continue
            quote = ""
            for follow in lines[idx + 1: idx + 25]:
                qm = verbatim_re.search(follow)
                if qm:
                    quote = qm.group(1).strip()
                    break
            rows.append((label, date, title, quote))

    if not rows:
        flt = ""
        if only_sanctum:
            flt += " --sanctum"
        if search_term:
            flt += f" --search {search_term}"
        return CommandResult(True,
            f"(no hard-canonicals{flt})")

    # Sort newest-first by date, sanctum BEFORE lane within same date.
    # Sort in two passes to avoid reverse=True flipping the label tiebreaker.
    rows.sort(key=lambda r: 0 if r[0] == "sanctum" else 1)  # sanctum first
    rows.sort(key=lambda r: r[1], reverse=True)              # date newest first (stable)

    out = [f"Hard-canonicals: {len(rows)} doctrine{'s' if len(rows) != 1 else ''}"]
    for label, date, title, quote in rows:
        title_short = title if len(title) <= 70 else title[:67] + "..."
        out.append(f"  {date} [{label:<7}] {title_short}")
        if quote:
            q = quote if len(quote) <= 100 else quote[:97] + "..."
            out.append(f"            \"{q}\"")
    return CommandResult(True, "\n".join(out))


def cmd_find(args: list[str]) -> CommandResult:
    """iter-63: find files by name pattern under the current project or Sanctum.

    Recursive glob search. Cheap and pure-Python (no subprocess), bounded by
    a 5000-file scan cap so we never lock up sterm on a huge tree.

    Usage:
      /find <glob>              search under current cwd (e.g. /find *.py)
      /find <glob> --here       (alias) restrict to cwd subtree
      /find <glob> --sanctum    search across the whole Sanctum repo
      /find <glob> --type d     directories only
      /find <glob> --type f     files only (default)
      /find <glob> N            cap results at N (default 30, max 200)
    """
    if not args:
        return CommandResult(True,
            "usage: /find <glob> [--sanctum --type d|f] [N]\n"
            "  e.g. /find *.py\n"
            "       /find heartbeats --type d --sanctum")
    pattern = args[0]
    use_sanctum = False
    want_type = "f"
    limit = 30
    SCAN_CAP = 5000
    i = 1
    while i < len(args):
        a = args[i]
        if a == "--sanctum":
            use_sanctum = True
            i += 1
            continue
        if a == "--here":
            use_sanctum = False
            i += 1
            continue
        if a == "--type" and i + 1 < len(args):
            t = args[i + 1].lower()
            if t not in ("f", "file", "d", "dir", "directory"):
                return CommandResult(True,
                    f"--type must be f or d, got: {t}")
            want_type = "d" if t.startswith("d") else "f"
            i += 2
            continue
        try:
            limit = max(1, min(200, int(a)))
        except ValueError:
            return CommandResult(True,
                f"unknown arg: {a}. Try /find with no args for usage.")
        i += 1

    root = SANCTUM_ROOT if use_sanctum else Path.cwd()
    if not root.exists():
        return CommandResult(True, f"root does not exist: {root}")

    # `rglob` doesn't apply gitignore — manually skip common heavy dirs
    SKIP_DIRS = {".git", "node_modules", "__pycache__", ".pytest_cache",
                 "venv", ".venv", "dist", "build", ".idea", ".vscode"}
    hits: list[Path] = []
    scanned = 0
    try:
        for p in root.rglob(pattern):
            scanned += 1
            if scanned > SCAN_CAP:
                break
            # Skip if any parent dir is in SKIP_DIRS
            if any(part in SKIP_DIRS for part in p.parts):
                continue
            try:
                is_dir = p.is_dir()
            except OSError:
                continue
            if want_type == "f" and is_dir:
                continue
            if want_type == "d" and not is_dir:
                continue
            hits.append(p)
            if len(hits) >= limit + 1:  # +1 so we can detect overflow
                break
    except (OSError, ValueError) as e:
        return CommandResult(True, f"/find failed: {e}")

    if not hits:
        scope = "sanctum" if use_sanctum else "cwd"
        return CommandResult(True,
            f"(no matches for '{pattern}' under {scope})")

    overflow = len(hits) > limit
    shown = hits[:limit]
    scope = f"sanctum ({SANCTUM_ROOT})" if use_sanctum else f"cwd ({root})"
    suffix = f" (capped — {scanned}+ files scanned)" if overflow or scanned > SCAN_CAP else ""
    lines = [f"Find: {len(shown)} match{'es' if len(shown) != 1 else ''}"
             f" for '{pattern}' [{want_type}] in {scope}{suffix}"]
    for p in shown:
        try:
            rel = p.relative_to(root)
            rel_str = rel.as_posix()
        except ValueError:
            rel_str = str(p)
        if len(rel_str) > 100:
            rel_str = "..." + rel_str[-97:]
        lines.append(f"  {rel_str}")
    return CommandResult(True, "\n".join(lines))


def cmd_agents(args: list[str]) -> CommandResult:
    """iter-62: richer /heartbeats — show fleet agents with mode + branch_intent
    + status_note (from /touch).

    Default sort = newest first. Args:
      /agents                 all agents
      /agents --fresh         only fresh (<30 min) heartbeats
      /agents --stale         only stale heartbeats
      /agents --slug X        only agents matching slug substring
      /agents N               limit to top N rows after filter
    """
    if not HEARTBEATS_DIR.exists():
        return CommandResult(True, "(no heartbeats dir)")
    import time as _t
    only_fresh = False
    only_stale = False
    slug_filter: str | None = None
    limit = 50
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--fresh":
            only_fresh = True
            i += 1
            continue
        if a == "--stale":
            only_stale = True
            i += 1
            continue
        if a == "--slug" and i + 1 < len(args):
            slug_filter = args[i + 1].lower()
            i += 2
            continue
        try:
            limit = max(1, min(500, int(a)))
        except ValueError:
            return CommandResult(True,
                f"unknown arg: {a}. Try /agents with no args for usage.")
        i += 1

    now = _t.time()
    rows: list[tuple[float, str, dict]] = []
    try:
        for hb in HEARTBEATS_DIR.glob("*.json"):
            try:
                mtime = hb.stat().st_mtime
            except OSError:
                continue
            data: dict = {}
            try:
                data = json.loads(hb.read_text(encoding="utf-8", errors="replace"))
                if not isinstance(data, dict):
                    data = {}
            except Exception:
                pass
            agent = data.get("agent") or hb.stem
            age_min = max(0, int((now - mtime) // 60))
            fresh = age_min < 30
            if only_fresh and not fresh:
                continue
            if only_stale and fresh:
                continue
            if slug_filter and slug_filter not in agent.lower():
                continue
            rows.append((mtime, agent, data))
    except OSError as e:
        return CommandResult(True, f"/agents failed: {e}")

    if not rows:
        flt = []
        if only_fresh: flt.append("--fresh")
        if only_stale: flt.append("--stale")
        if slug_filter: flt.append(f"--slug {slug_filter}")
        return CommandResult(True,
            f"(no agents{' (' + ' '.join(flt) + ')' if flt else ''})")

    rows.sort(key=lambda r: -r[0])  # newest first
    shown = rows[:limit]
    fresh_n = sum(1 for r in rows if (now - r[0]) / 60 < 30)
    stale_n = len(rows) - fresh_n
    out = [f"Agents: {len(shown)} of {len(rows)} "
           f"(fresh<30m={fresh_n}, stale={stale_n})"]
    for mtime, agent, data in shown:
        age_min = max(0, int((now - mtime) // 60))
        marker = "●" if age_min < 30 else "○"
        mode = (data.get("mode") or "")[:18]
        full_branch = data.get("branch_intent") or ""
        note = data.get("status_note") or ""
        # Show branch slug only (after last /) for compactness — rsplit FIRST
        # then truncate so we get the topic, not the agent/lane/ prefix.
        branch_short = (full_branch.rsplit("/", 1)[-1] if full_branch else "")[:32]
        line = (f"  {marker} {agent:<28} {age_min:>4}m  "
                f"{mode:<18}  {branch_short:<32}")
        if note:
            line += f"  · {note[:40]}"
        out.append(line)
    return CommandResult(True, "\n".join(out))


def cmd_watch(args: list[str]) -> CommandResult:
    """iter-61: tail any jsonl/text log under _shared-memory.

    Generic companion to the lane-specific tail builtins (/utterances,
    /events). The path arg is resolved relative to SANCTUM_ROOT and
    sandboxed to `_shared-memory/` so this builtin can't accidentally
    dump the operator's home dir or any path outside the fleet's shared
    memory.

    Usage:
      /watch <relative-path-from-shared-memory> [N]
    Examples:
      /watch fleet-updates.jsonl                 last 10 rows of fleet-updates
      /watch fleet-updates.jsonl 30              last 30 rows
      /watch sinister-link-poll-log.jsonl 5
      /watch overseer-distribute-log.jsonl
    """
    if not args:
        return CommandResult(True,
            "usage: /watch <relative-path-from-_shared-memory> [N]\n"
            "  e.g. /watch fleet-updates.jsonl 20\n"
            "Paths are sandboxed under _shared-memory/.")
    rel = args[0]
    limit = 10
    if len(args) > 1:
        try:
            limit = max(1, min(500, int(args[1])))
        except ValueError:
            return CommandResult(True,
                f"second arg must be an integer line count, got: {args[1]}")

    shared = SANCTUM_ROOT / "_shared-memory"
    target = (shared / rel).resolve()
    try:
        target.relative_to(shared.resolve())
    except ValueError:
        return CommandResult(True,
            f"refused: path escapes _shared-memory/ sandbox: {rel}")
    if not target.exists():
        return CommandResult(True, f"(no file at _shared-memory/{rel})")
    if target.is_dir():
        return CommandResult(True,
            f"(path is a directory: _shared-memory/{rel} — give a file)")

    # Read last ~256 KiB tail for efficiency on big logs
    try:
        size = target.stat().st_size
        with target.open("rb") as fh:
            if size > 256 * 1024:
                fh.seek(size - 256 * 1024)
                _ = fh.readline()  # discard partial line
            tail_bytes = fh.read()
    except OSError as e:
        return CommandResult(True, f"/watch failed: {e}")
    try:
        text = tail_bytes.decode("utf-8", errors="replace")
    except Exception as e:
        return CommandResult(True, f"/watch decode failed: {e}")

    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return CommandResult(True, f"(empty: _shared-memory/{rel})")
    shown = lines[-limit:]
    out = [f"Watch: {len(shown)} of {len(lines)} lines in _shared-memory/{rel}"]
    for ln in shown:
        # If it parses as JSON object, render compactly; otherwise raw
        try:
            obj = json.loads(ln)
            if isinstance(obj, dict):
                ts = obj.get("ts_utc") or obj.get("timestamp") or ""
                # Pick a short key to lead with
                lead = (obj.get("kind") or obj.get("event") or obj.get("name")
                        or obj.get("subject") or obj.get("title") or "")
                preview = ln if len(ln) <= 120 else ln[:117] + "..."
                if ts or lead:
                    out.append(f"  {ts[:19]}  {lead[:20]:<20}  {preview[:90]}")
                else:
                    out.append(f"  {preview[:120]}")
            else:
                out.append(f"  {ln[:120]}")
        except Exception:
            out.append(f"  {ln[:120]}")
    return CommandResult(True, "\n".join(out))


def cmd_utterances(args: list[str]) -> CommandResult:
    """iter-60: tail recent operator utterances from operator-utterances.jsonl.

    Operator hard-canonical 2026-05-24: *"make sure that everything i ever
    say is tracked"* — every operator message is appended as one jsonl row
    by `automations/log-operator-utterance.ps1`. This builtin lets us read
    the tail from inside sterm without leaving the shell.

    Usage:
      /utterances             last 10 rows
      /utt 20                 last 20 rows (alias)
      /utterances --new       only status=new (unacked)
      /utterances --mine      only session_slug=sinister-term
      /utterances --search X  only rows where preview/message contains X
    """
    if not _UTTERANCES_PATH.exists():
        try:
            rel = _UTTERANCES_PATH.relative_to(SANCTUM_ROOT).as_posix()
        except ValueError:
            rel = str(_UTTERANCES_PATH)
        return CommandResult(True, f"(no operator-utterances.jsonl at {rel})")
    limit = 10
    only_new = False
    only_mine = False
    search_term: str | None = None
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--new":
            only_new = True
            i += 1
            continue
        if a == "--mine":
            only_mine = True
            i += 1
            continue
        if a == "--search" and i + 1 < len(args):
            search_term = args[i + 1].lower()
            i += 2
            continue
        try:
            limit = max(1, min(500, int(a)))
        except ValueError:
            return CommandResult(True,
                f"unknown arg: {a}. Try /utterances with no args for usage.")
        i += 1

    rows: list[dict] = []
    try:
        with _UTTERANCES_PATH.open("r", encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    rows.append(json.loads(ln))
                except Exception:
                    continue
    except OSError as e:
        return CommandResult(True, f"/utterances failed: {e}")

    if only_new:
        rows = [r for r in rows if r.get("status") == "new"]
    if only_mine:
        rows = [r for r in rows if r.get("session_slug") == SELF_SLUG]
    if search_term:
        def _matches(r: dict) -> bool:
            for k in ("preview", "message_full"):
                v = r.get(k)
                if isinstance(v, str) and search_term in v.lower():
                    return True
            return False
        rows = [r for r in rows if _matches(r)]

    if not rows:
        flt = []
        if only_new:
            flt.append("--new")
        if only_mine:
            flt.append("--mine")
        if search_term:
            flt.append(f"--search {search_term}")
        return CommandResult(True,
            f"(no utterances{' (' + ' '.join(flt) + ')' if flt else ''})")

    rows = rows[-limit:]
    try:
        rel = _UTTERANCES_PATH.relative_to(SANCTUM_ROOT).as_posix()
    except ValueError:
        rel = str(_UTTERANCES_PATH)
    lines = [f"Utterances: {len(rows)} of {rel}"]
    for r in rows:
        ts = r.get("ts_utc", "?")[:19] + "Z"
        slug = (r.get("session_slug") or "?")[:18]
        status = r.get("status") or "?"
        # Status badge: NEW=red-ish, acked=dim, resolved=ok
        if status == "new":
            badge = "[NEW]"
        elif status == "resolved":
            badge = "[res]"
        else:
            badge = "[ack]"
        prev = (r.get("preview") or r.get("message_full") or "")[:80]
        lines.append(f"  {ts}  {badge}  {slug:<18}  {prev}")
    return CommandResult(True, "\n".join(lines))


def cmd_locks(_args: list[str]) -> CommandResult:
    """iter-59: list active mesh-coordinator locks.

    Composes with `mesh-coordination-and-resource-lifecycle-2026-05-24`
    doctrine: before any risky edit, /locks shows who holds what so we
    don't trample a sister-agent's in-flight work.

    Lock files live in `_shared-memory/mesh-locks/*.json`. Each lock JSON
    is expected to contain {owner, path, ttl_seconds, acquired_at_utc}
    but tolerant if any are missing. Files modified more than ttl_seconds
    ago are flagged as `(stale)` so operator can decide whether to reclaim.
    """
    if not _MESH_LOCKS_DIR.exists():
        try:
            rel = _MESH_LOCKS_DIR.relative_to(SANCTUM_ROOT).as_posix()
        except ValueError:
            rel = str(_MESH_LOCKS_DIR)
        return CommandResult(True, f"(no mesh-locks dir at {rel})")
    import time as _t
    rows: list[tuple[float, str, dict]] = []  # (mtime, fname, parsed_or_empty)
    try:
        for lf in _MESH_LOCKS_DIR.glob("*.json"):
            try:
                mtime = lf.stat().st_mtime
            except OSError:
                continue
            data: dict = {}
            try:
                data = json.loads(lf.read_text(encoding="utf-8", errors="replace"))
                if not isinstance(data, dict):
                    data = {}
            except Exception:
                pass
            rows.append((mtime, lf.name, data))
    except OSError as e:
        return CommandResult(True, f"/locks failed: {e}")
    if not rows:
        return CommandResult(True, "(no active mesh-coordinator locks)")
    rows.sort(key=lambda r: -r[0])  # newest first

    now = _t.time()
    lines = [f"Mesh locks: {len(rows)} active"]
    for mtime, fname, data in rows:
        age_s = max(0.0, now - mtime)
        age = _format_duration(age_s)
        owner = data.get("owner") or data.get("agent") or "?"
        path = data.get("path") or data.get("focus") or data.get("target") or "?"
        ttl = data.get("ttl_seconds")
        stale = ""
        if isinstance(ttl, (int, float)) and ttl > 0 and age_s > ttl:
            stale = "  (stale)"
        ttl_str = f"ttl={int(ttl)}s" if isinstance(ttl, (int, float)) else "ttl=?"
        # Truncate path to keep one-liner tidy
        path_s = str(path)
        if len(path_s) > 50:
            path_s = path_s[:47] + "..."
        lines.append(
            f"  {owner:<24}  {path_s:<50}  {ttl_str}  age={age}{stale}"
        )
    return CommandResult(True, "\n".join(lines))


def cmd_touch(args: list[str]) -> CommandResult:
    """iter-58: manually pulse the sinister-term heartbeat NOW.

    Useful when the operator wants to confirm liveness without typing JSON,
    or attach a status note ("paused waiting for review") that surfaces to
    other agents via /swarm list / mesh-coordinator polls.

    Usage:
      /touch                          refresh heartbeat with default status
      /touch <free-form status...>    attach a status note to the heartbeat
    """
    import time as _t
    note = " ".join(args).strip() if args else None
    payload = {
        "agent": SELF_SLUG,
        "ts_utc": _t.strftime("%Y-%m-%dT%H:%M:%SZ", _t.gmtime()),
        "alive": True,
        "via": "sterm /touch",
        "cwd": str(Path.cwd()),
    }
    if note:
        # Cap free-form note so a runaway paste doesn't bloat the heartbeat.
        payload["status_note"] = note[:280]

    # Read existing heartbeat (if any) so we don't blow away unrelated keys
    # like mode / branch_intent / last_shipped that the spawner / loop wrote.
    try:
        if _HEARTBEAT_PATH.exists():
            existing = json.loads(
                _HEARTBEAT_PATH.read_text(encoding="utf-8", errors="replace")
            )
            if isinstance(existing, dict):
                # Update existing in place so historical fields survive
                existing.update(payload)
                payload = existing
    except Exception:
        # Corrupted JSON — overwrite with the fresh payload
        pass

    try:
        _HEARTBEAT_PATH.parent.mkdir(parents=True, exist_ok=True)
        _HEARTBEAT_PATH.write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )
    except OSError as e:
        return CommandResult(True, f"/touch failed: {e}")

    lines = [
        f"heartbeat pulsed: {_HEARTBEAT_PATH.name}",
        f"  ts_utc:    {payload['ts_utc']}",
        f"  cwd:       {payload['cwd']}",
    ]
    if note:
        lines.append(f"  status:    {payload['status_note']}")
    return CommandResult(True, "\n".join(lines))


def _git_one(args: list[str], *, cwd: Path | None = None,
             timeout_s: float = 2.0) -> str | None:
    """Run a `git` invocation and return stripped stdout (or None on error)."""
    try:
        out = subprocess.check_output(
            ["git", *args],
            cwd=str(cwd or Path.cwd()),
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=timeout_s,
        )
        return out.strip()
    except Exception:
        return None


def cmd_branch(_args: list[str]) -> CommandResult:
    """iter-57: current branch + ahead/behind origin + dirty file count.

    Cheap one-shot `git` poll — useful inside sterm before a /swarm
    broadcast / commit so the operator can see they're on the expected
    lane slug. All shells exec'd via subprocess with 2s timeout.
    """
    branch = _git_one(["rev-parse", "--abbrev-ref", "HEAD"])
    if branch is None:
        return CommandResult(True, "branch: (not in a git repo)")

    lines = [f"Branch: {branch}"]

    # upstream tracking
    upstream = _git_one(["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])
    if upstream:
        lines.append(f"  upstream:       {upstream}")
        # ahead/behind via rev-list --left-right --count
        counts = _git_one(["rev-list", "--left-right", "--count", "HEAD...@{u}"])
        if counts and "\t" in counts:
            ahead, behind = counts.split("\t", 1)
            lines.append(f"  ahead/behind:   +{ahead} / -{behind}")
        else:
            lines.append("  ahead/behind:   (rev-list failed)")
    else:
        lines.append("  upstream:       (no upstream tracking)")

    # dirty count
    status = _git_one(["status", "--porcelain"])
    if status is None:
        lines.append("  working tree:   (status failed)")
    elif not status:
        lines.append("  working tree:   clean")
    else:
        rows = [l for l in status.splitlines() if l.strip()]
        # Classify by first letter (staged) / second letter (unstaged)
        staged = sum(1 for r in rows if r[0] != " " and r[0] != "?")
        unstaged = sum(1 for r in rows if len(r) > 1 and r[1] != " " and r[0] != "?")
        untracked = sum(1 for r in rows if r.startswith("??"))
        lines.append(
            f"  working tree:   {len(rows)} change{'s' if len(rows) != 1 else ''}"
            f"  (staged={staged}, unstaged={unstaged}, untracked={untracked})"
        )

    # HEAD commit one-liner
    head = _git_one(["log", "-1", "--oneline"])
    if head:
        # Truncate to keep line tidy
        if len(head) > 80:
            head = head[:77] + "..."
        lines.append(f"  HEAD:           {head}")

    return CommandResult(True, "\n".join(lines))


def _format_duration(seconds: float) -> str:
    """Render a duration as a compact human-readable string.

    Examples:
      45.0   -> '45.0s'
      90.0   -> '1m 30s'
      3661.0 -> '1h 01m 01s'
      90061.0 -> '1d 01h 01m'
    """
    seconds = max(0.0, float(seconds))
    if seconds < 60:
        return f"{seconds:.1f}s"
    if seconds < 3600:
        m, s = divmod(int(seconds), 60)
        return f"{m}m {s:02d}s"
    if seconds < 86400:
        h, rem = divmod(int(seconds), 3600)
        m, s = divmod(rem, 60)
        return f"{h}h {m:02d}m {s:02d}s"
    d, rem = divmod(int(seconds), 86400)
    h, m = divmod(rem, 3600)
    return f"{d}d {h:02d}h {m // 60:02d}m"


# Module-level boot timestamp — captured on first import = effective sterm start.
import time as _time_mod
_STERM_BOOT_T = _time_mod.monotonic()
_STERM_BOOT_WALL = _time_mod.time()


def cmd_uptime(_args: list[str]) -> CommandResult:
    """iter-56: sterm session duration + activity counters.

    Composes with /health but focuses on the "how long has this shell been
    alive and how much has it done" question. Cheap: just monotonic delta
    + bus seq + bridge frame count.
    """
    import time as _t
    monotonic_now = _t.monotonic()
    wall_now = _t.time()
    secs = monotonic_now - _STERM_BOOT_T
    lines = [
        f"Sinister Term uptime:",
        f"  session:        {_format_duration(secs)}",
        f"  booted at:      {_t.strftime('%Y-%m-%dT%H:%M:%SZ', _t.gmtime(_STERM_BOOT_WALL))}",
        f"  now:            {_t.strftime('%Y-%m-%dT%H:%M:%SZ', _t.gmtime(wall_now))}",
    ]

    # Activity counters — what HAS happened since boot
    try:
        from term.event_bus import default_bus
        bus = default_bus()
        lines.append(
            f"  events seen:    {bus.current_seq}  (ring {bus.ring_size}/4096)"
        )
    except Exception:
        lines.append("  events seen:    (event_bus unavailable)")

    try:
        from term import ascii_bridge as _br
        s = _br.default_bridge().status()
        if s.running:
            running_for = (wall_now - s.started_at) if s.started_at else 0
            lines.append(
                f"  ascii frames:   {s.frames_rendered}  "
                f"(bridge ON for {_format_duration(running_for)})"
            )
        else:
            lines.append(
                f"  ascii frames:   {s.frames_rendered}  (bridge off)"
            )
    except Exception:
        lines.append("  ascii frames:   (ascii_bridge unavailable)")

    try:
        from term import cache as _cache
        lines.append(f"  cache entries:  {_cache.size()}")
    except Exception:
        pass

    return CommandResult(True, "\n".join(lines))


def cmd_health(_args: list[str]) -> CommandResult:
    """iter-55: single-screen sterm health dashboard.

    Composite read of: sterm version, live agent count + fresh marker,
    inbox count, ascii bridge status, event_bus seq + boot id, git branch.
    Pure local reads; all wrapped in try/except so a single broken source
    doesn't take down the whole panel.
    """
    lines = ["Sinister Term health:"]

    # version
    try:
        from term import __version__ as _v
        lines.append(f"  version:        sinister-term {_v}")
    except Exception as e:
        lines.append(f"  version:        ? ({e})")

    # branch
    try:
        from term.status import git_branch
        b = git_branch()
        lines.append(f"  git branch:     {b or '(not in a repo)'}")
    except Exception as e:
        lines.append(f"  git branch:     ? ({e})")

    # heartbeats — count + freshest sibling
    try:
        if HEARTBEATS_DIR.exists():
            hbs = list(HEARTBEATS_DIR.glob("*.json"))
            import time as _t
            fresh = 0
            stale = 0
            now = _t.time()
            for hb in hbs:
                try:
                    age_min = (now - hb.stat().st_mtime) / 60
                except OSError:
                    continue
                if age_min < 30:
                    fresh += 1
                else:
                    stale += 1
            lines.append(f"  fleet agents:   {len(hbs)} total  ({fresh} fresh <30m, {stale} stale)")
        else:
            lines.append("  fleet agents:   (no heartbeats dir)")
    except Exception as e:
        lines.append(f"  fleet agents:   ? ({e})")

    # inbox
    try:
        inbox = INBOX_DIR / SELF_SLUG
        n = sum(1 for _ in inbox.glob("*.json")) if inbox.exists() else 0
        lines.append(f"  inbox:          {n} unread")
    except Exception as e:
        lines.append(f"  inbox:          ? ({e})")

    # ascii bridge
    try:
        from term import ascii_bridge as _br
        s = _br.default_bridge().status()
        state = "ON" if s.running else "off"
        lines.append(
            f"  ascii bridge:   {state}  "
            f"project={s.project_key}  frames={s.frames_rendered}"
        )
    except Exception as e:
        lines.append(f"  ascii bridge:   ? ({e})")

    # event_bus
    try:
        from term.event_bus import default_bus
        bus = default_bus()
        lines.append(
            f"  event_bus:      seq={bus.current_seq}  ring={bus.ring_size}/4096  "
            f"boot={bus.boot_id[:8]}"
        )
    except Exception as e:
        lines.append(f"  event_bus:      ? ({e})")

    # progress log existence
    try:
        if PROGRESS_FILE.exists():
            import os as _os
            size_kb = _os.path.getsize(PROGRESS_FILE) / 1024
            lines.append(f"  PROGRESS log:   {PROGRESS_FILE.name}  ({size_kb:.1f} KiB)")
        else:
            lines.append(f"  PROGRESS log:   (none — {PROGRESS_FILE.name} missing)")
    except Exception as e:
        lines.append(f"  PROGRESS log:   ? ({e})")

    return CommandResult(True, "\n".join(lines))


def cmd_ascii(args: list[str]) -> CommandResult:
    """iter-54: operator-facing control of the SA-PH6 ascii_bridge.

    Lets the operator toggle the living-entity overlay without restarting
    sterm or fiddling with SINISTER_ASCII env. Swap the entity per project
    without leaving the shell.

    Usage:
      /ascii                          show current status
      /ascii on                       start the bridge (if importable)
      /ascii off                      stop the bridge
      /ascii status                   detailed status
      /ascii project <project-key>    swap the per-project entity
      /ascii list                     list all known entities
    """
    try:
        from term import ascii_bridge as _br
    except Exception as e:
        return CommandResult(True, f"ascii_bridge unavailable: {e}")

    if not args:
        s = _br.default_bridge().status()
        state = "ON" if s.running else "off"
        return CommandResult(True,
            f"ascii: {state}  project={s.project_key}  frames={s.frames_rendered}  "
            f"intensity={s.last_intensity:.2f}  (try /ascii on|off|status|project|list)")

    sub = args[0].lower()
    rest = args[1:]
    bridge = _br.default_bridge()

    if sub == "on":
        ok = bridge.start()
        s = bridge.status()
        if ok:
            return CommandResult(True,
                f"ascii: ON  project={s.project_key}  refresh={s.refresh_seconds}s")
        return CommandResult(True,
            f"ascii: failed to start ({s.error or 'unknown error'})")

    if sub == "off":
        bridge.stop()
        return CommandResult(True, "ascii: off")

    if sub == "status":
        s = bridge.status()
        lines = [
            f"ascii bridge status:",
            f"  running:        {s.running}",
            f"  project_key:    {s.project_key}",
            f"  refresh_secs:   {s.refresh_seconds}",
            f"  frames_rendered:{s.frames_rendered}",
            f"  last_intensity: {s.last_intensity:.3f}",
            f"  started_at:     {s.started_at}",
            f"  error:          {s.error or '(none)'}",
        ]
        return CommandResult(True, "\n".join(lines))

    if sub == "project":
        if not rest:
            return CommandResult(True, "usage: /ascii project <project-key>")
        ok = bridge.set_project(rest[0])
        s = bridge.status()
        if ok:
            return CommandResult(True,
                f"ascii: project={s.project_key}  running={s.running}")
        return CommandResult(True, f"ascii: failed to swap project ({s.error or 'unknown'})")

    if sub == "list":
        # Make sure sinister_ascii is on path then list the entity registry
        if not _br._ensure_ascii_on_path():
            return CommandResult(True, "ascii: sinister_ascii not importable")
        try:
            from sinister_ascii.entities import ENTITIES
            lines = [f"ascii: {len(ENTITIES)} per-project entities:"]
            for k in sorted(ENTITIES.keys()):
                e = ENTITIES[k]
                lines.append(f"  {k:<22} -> {e.name:<22} motion={e.motion_kind}")
            return CommandResult(True, "\n".join(lines))
        except Exception as e:
            return CommandResult(True, f"ascii list failed: {e}")

    return CommandResult(True,
        f"unknown ascii subcommand: {sub}. Try /ascii with no args for usage.")


def cmd_events(args: list[str]) -> CommandResult:
    """iter-53: read recent cmux-bus events.

    Lets the operator inspect what the bus has captured this session
    without leaving sterm. The bus retains the last 4096 events
    in-memory (cmux spec) and rotates jsonl at 512 KiB on disk.

    Usage:
      /events                 last 20 events
      /events 50              last N events
      /events --cat lifecycle filter by category (lifecycle / agent / terminal / ui / network)
      /events --name dispatch filter by name (exact match)
      /events --disk          tail the rotated jsonl on disk instead of ram
    """
    try:
        from term.event_bus import default_bus
    except Exception as e:
        return CommandResult(True, f"event_bus unavailable: {e}")

    limit = 20
    cat_filter: str | None = None
    name_filter: str | None = None
    from_disk = False
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--cat" and i + 1 < len(args):
            cat_filter = args[i + 1]
            i += 2
            continue
        if a == "--name" and i + 1 < len(args):
            name_filter = args[i + 1]
            i += 2
            continue
        if a == "--disk":
            from_disk = True
            i += 1
            continue
        try:
            limit = max(1, min(500, int(a)))
        except ValueError:
            return CommandResult(True,
                f"unknown arg: {a}. Try /events with no args for usage.")
        i += 1

    bus = default_bus()
    if from_disk:
        events_iter = bus.replay_from_disk(after_seq=0)
    else:
        # Subscribe with after_seq=0 = give everything in ring
        events_iter = bus.subscribe(
            after_seq=0,
            names=[name_filter] if name_filter else None,
            categories=[cat_filter] if cat_filter else None,
        )
    rows: list = []
    for ev in events_iter:
        if from_disk:
            if cat_filter and ev.category != cat_filter:
                continue
            if name_filter and ev.name != name_filter:
                continue
        rows.append(ev)
    if not rows:
        scope = "disk" if from_disk else "ring"
        flt = ""
        if cat_filter:
            flt += f" cat={cat_filter}"
        if name_filter:
            flt += f" name={name_filter}"
        return CommandResult(True, f"(no events in {scope}{flt})")

    rows = rows[-limit:]
    src = "disk" if from_disk else "ring"
    lines = [f"Events ({len(rows)} of bus.{src}, boot={bus.boot_id[:8]}):"]
    for ev in rows:
        # ts_ns → HH:MM:SS local-ish (use UTC for portability)
        import time as _t
        secs = ev.ts_ns / 1_000_000_000
        hms = _t.strftime("%H:%M:%S", _t.gmtime(secs))
        # Compact payload summary: first 4 keys
        pl = ev.payload or {}
        if isinstance(pl, dict):
            kvs = ", ".join(f"{k}={_short(v)}" for k, v in list(pl.items())[:4])
            if len(pl) > 4:
                kvs += f", +{len(pl) - 4}"
        else:
            kvs = str(pl)[:60]
        lines.append(
            f"  #{ev.seq:>5} {hms}Z [{ev.category:<9}] {ev.name:<22} {kvs}"
        )
    return CommandResult(True, "\n".join(lines))


def _short(v):
    """Render a payload value compactly for /events output."""
    s = str(v)
    if len(s) > 40:
        return s[:37] + "..."
    return s


def cmd_swarm(args: list[str]) -> CommandResult:
    """P2-3 (iter-51): wrap term.swarm.{spawn,list_agents,dm,broadcast} as
    a single /-prefix builtin so the operator can fan-out / coordinate from
    inside sterm without dropping to the CLI.

    Usage:
      /swarm                              show subcommand usage
      /swarm list                         list live agents from heartbeats/
      /swarm spawn <project-key>          spawn a new agent via launcher
      /swarm dm <agent-slug> <message>    drop [ASK] in target's inbox
      /swarm broadcast <message>          write to _shared-memory/cross-agent/
    """
    from term import swarm as _swarm_mod  # local import keeps boot lean
    if not args:
        return CommandResult(True,
            "usage: /swarm <subcommand>\n"
            "  /swarm list                          live agents from heartbeats\n"
            "  /swarm spawn <project-key>           spawn an agent via launcher\n"
            "  /swarm dm <agent-slug> <message>     drop [ASK] in inbox\n"
            "  /swarm broadcast <message>           write to cross-agent/")
    sub = args[0].lower()
    rest = args[1:]
    if sub == "list":
        rows = _swarm_mod.list_agents()
        try:
            _bus_publish("swarm_list", "agent", payload={"agent_count": len(rows)})
        except Exception:
            pass
        if not rows:
            return CommandResult(True, "(no live agents)")
        lines = [f"Swarm: {len(rows)} agent{'s' if len(rows) != 1 else ''}"]
        for r in rows:
            lines.append(
                f"  {r.get('marker', '·')} {r.get('agent', '?'):<32}"
                f"  {r.get('age_min', '?')}m ago  cwd={r.get('cwd', '?')}"
            )
        return CommandResult(True, "\n".join(lines))
    if sub == "spawn":
        if not rest:
            return CommandResult(True, "usage: /swarm spawn <project-key>")
        rc = _swarm_mod.spawn(rest[0])
        try:
            _bus_publish("swarm_spawn", "agent",
                         payload={"project_key": rest[0], "exit_code": int(rc)})
        except Exception:
            pass
        return CommandResult(True,
            f"spawn → exit {rc}" if rc != 0 else f"spawned: {rest[0]}")
    if sub == "dm":
        if len(rest) < 2:
            return CommandResult(True, "usage: /swarm dm <agent-slug> <message...>")
        target = rest[0]
        msg = " ".join(rest[1:])
        path = _swarm_mod.dm(target, msg)
        try:
            _bus_publish("swarm_dm", "agent",
                         payload={"target": target, "msg_len": len(msg),
                                  "delivered": path is not None})
        except Exception:
            pass
        if path is None:
            return CommandResult(True, f"unknown agent inbox: {target}")
        return CommandResult(True, f"[DM] → {path}")
    if sub == "broadcast":
        if not rest:
            return CommandResult(True, "usage: /swarm broadcast <message...>")
        msg = " ".join(rest)
        path = _swarm_mod.broadcast(msg)
        try:
            _bus_publish("swarm_broadcast", "agent",
                         payload={"msg_len": len(msg), "path": str(path)})
        except Exception:
            pass
        return CommandResult(True, f"[BROADCAST] → {path}")
    return CommandResult(True,
        f"unknown swarm subcommand: {sub}. Try /swarm with no args for help.")


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
    "inbox": cmd_inbox,
    "cross-agent": cmd_cross_agent,
    "ca": cmd_cross_agent,
    "ask": cmd_ask,
    "progress": cmd_progress,
    "alias": cmd_alias,
    "recall": cmd_recall,  # P2-1 iter-50
    "swarm": cmd_swarm,    # P2-3 iter-51
    "events": cmd_events,  # iter-53 — read the cmux event_bus
    "ascii": cmd_ascii,    # iter-54 — control SA-PH6 ascii_bridge
    "health": cmd_health,  # iter-55 — single-screen sterm dashboard
    "uptime": cmd_uptime,  # iter-56 — sterm session duration + activity counters
    "branch": cmd_branch,  # iter-57 — branch + ahead/behind + dirty count
    "touch": cmd_touch,    # iter-58 — manually pulse sinister-term heartbeat
    "locks": cmd_locks,        # iter-59 — mesh-coordinator lock state
    "utterances": cmd_utterances,  # iter-60 — recent operator utterances
    "utt": cmd_utterances,         # short alias
    "watch": cmd_watch,            # iter-61 — tail any jsonl under _shared-memory
    "agents": cmd_agents,          # iter-62 — richer heartbeats with mode/branch/note
    "find": cmd_find,              # iter-63 — recursive name search under SANCTUM_ROOT
    "doctrine": cmd_doctrine,      # iter-64 — list operator hard-canonicals from CLAUDE.md
    "crashlog": cmd_crashlog,      # iter-65 — read eve-crash-log.jsonl
    "crashes": cmd_crashlog,       # alias
    "grep": cmd_grep,              # iter-66 — content search across files
    "fleet-updates": cmd_fleet_updates,  # iter-67 — read fleet-updates.jsonl
    "fu": cmd_fleet_updates,             # short alias
    "incidents": cmd_incidents,          # iter-68 — read eve-incidents.jsonl
    "me": cmd_me,                        # iter-69 — show our own heartbeat in detail
    "diff": cmd_diff,                    # iter-70 — git diff --stat for unstaged + staged
    "version": cmd_version,              # iter-71 — composite version dashboard
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
