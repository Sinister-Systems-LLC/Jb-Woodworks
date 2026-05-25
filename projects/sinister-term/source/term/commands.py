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
