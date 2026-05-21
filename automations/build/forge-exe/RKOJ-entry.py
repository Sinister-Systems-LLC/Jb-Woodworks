# Sinister Sanctum :: RKOJ.exe entry script (v0.5.0 — jcode-shell)
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Operator escalation 2026-05-21 (verbatim): *"i just want the complet jcode
# appraoch like this and i just tell it what to do and it goes or i can use
# /resume and see resume based on project"*.
#
# Drop the picker entirely. After the status panel: a single `>` prompt.
# Type ANYTHING:
#   - `/resume`           → browse resume-points grouped by project
#   - `/resume N`         → load resume-point N (prints summary)
#   - `/help`             → list all slash commands
#   - `/login providers`  → 11-provider auth wallet
#   - `/usage`            → token quota
#   - `/swarm spawn 3`    → spawn 3 EVE agents
#   - `/forge`            → launch the multi-pane Forge TUI
#   - `/quit`             → exit
#   - <natural language>  → spawn `claude --dangerously-skip-permissions <text>`
#                           in Sanctum root, stream output to this terminal.

from __future__ import annotations

import datetime
import itertools
import json
import os
import platform
import re
import subprocess
import sys
import threading
import time
import traceback
from pathlib import Path

__version__ = "1.3.0"


# ----- Sub-command dispatch (RKOJ.exe login providers etc) -----------------

def _route_subcommand(argv: list[str]) -> int | None:
    if not argv:
        return None
    head = argv[0]
    if head in {"login", "usage", "swarm", "memory", "graph", "version", "help",
                "providers", "current", "doctor"}:
        try:
            from sinister_cli.__main__ import main as cli_main
        except Exception as e:
            print(f"[RKOJ] sinister-cli backend missing: {e}", file=sys.stderr)
            return 2
        return int(cli_main(argv) or 0)
    return None


# ----- Runtime hardening ---------------------------------------------------

def _install_runtime_logger() -> None:
    log_path = (Path(sys.executable).parent if getattr(sys, "frozen", False)
                else Path(__file__).resolve().parent) / "RKOJ.crash.log"

    def _hook(exctype, value, tb):
        try:
            with log_path.open("a", encoding="utf-8") as fh:
                fh.write(f"\n=== {_utc_now().isoformat()} ===\n")
                traceback.print_exception(exctype, value, tb, file=fh)
        except OSError:
            pass
        if sys.__stderr__ is not None:
            try:
                sys.__stderr__.write(f"\n[RKOJ] crash log: {log_path}\n")
                traceback.print_exception(exctype, value, tb, file=sys.__stderr__)
            except (AttributeError, OSError):
                pass

    sys.excepthook = _hook


def _enable_vt() -> None:
    # Force UTF-8 on stdout/stderr so unicode block chars + Braille spinners
    # don't crash with UnicodeEncodeError on cp1252 (Windows default when
    # stdout is piped or redirected).
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is not None and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
    if platform.system() != "Windows":
        return
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        STD_OUTPUT_HANDLE = -11
        ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        h = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
        mode = ctypes.c_ulong()
        kernel32.GetConsoleMode(h, ctypes.byref(mode))
        kernel32.SetConsoleMode(h, mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING)
        # Also set the console output codepage to UTF-8 (chcp 65001) so the
        # cmd console renders the unicode block + Braille glyphs correctly.
        kernel32.SetConsoleOutputCP(65001)
        kernel32.SetConsoleCP(65001)
    except Exception:
        pass


def _utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


# ----- Theme ---------------------------------------------------------------

RESET = "\033[0m"
BOLD = "\033[1m"

def _fg(r, g, b) -> str:
    return f"\033[38;2;{r};{g};{b}m"

PURPLE = _fg(138, 43, 226)
PURPLE_BRIGHT = _fg(186, 85, 211)
PURPLE_DIM = _fg(75, 0, 130)
CYAN = _fg(0, 200, 220)
WHITE = _fg(220, 220, 230)
GRAY = _fg(120, 120, 130)
GOLD = _fg(218, 165, 32)
GREEN = _fg(85, 200, 110)
RED = _fg(220, 40, 60)
DOT_ON = GREEN + "●" + RESET
DOT_OFF = GRAY + "○" + RESET


# ----- Tiny mark + spinner -------------------------------------------------

SINISTER_MARK = r"""
  ███████╗██╗███╗   ██╗██╗███████╗████████╗███████╗██████╗
  ██║════╝██║██╔██╗ ██║██║██║════╝   ██║   ██║════╝██╔══██╗
  ███████╗██║██║ ╚████║██║███████║   ██║   ███████╗██║  ██║""".strip("\n")


def _print_mark() -> None:
    print(PURPLE_BRIGHT + SINISTER_MARK + RESET)


BRAILLE = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"


class _Spin:
    def __init__(self, label: str, fps: int = 12):
        self.label = label; self.delay = 1.0 / fps
        self._stop = threading.Event(); self._t = None

    def __enter__(self): self.start(); return self
    def __exit__(self, *a): self.stop()

    def start(self):
        def _spin():
            for ch in itertools.cycle(BRAILLE):
                if self._stop.is_set():
                    break
                try:
                    sys.stdout.write(f"\r  {PURPLE_BRIGHT}{ch}{RESET} {GRAY}{self.label}{RESET}")
                    sys.stdout.flush()
                except OSError:
                    break
                time.sleep(self.delay)
        self._t = threading.Thread(target=_spin, daemon=True); self._t.start()

    def stop(self):
        self._stop.set()
        if self._t:
            self._t.join(timeout=0.4)
        try:
            sys.stdout.write("\r\033[2K"); sys.stdout.flush()
        except OSError:
            pass


# ----- Sanctum-state discovery ---------------------------------------------

def _find_sanctum_root() -> Path:
    for c in (os.environ.get("SANCTUM_ROOT"),
              r"D:\Sinister Sanctum", r"C:\Sinister Sanctum",
              str(Path.home() / "Sinister Sanctum")):
        if c and (Path(c) / "CLAUDE.md").exists():
            return Path(c)
    here = Path(sys.executable if getattr(sys, "frozen", False) else __file__).resolve()
    for parent in here.parents:
        if (parent / "CLAUDE.md").exists():
            return parent
    return Path(r"D:\Sinister Sanctum")


def _git_status(root: Path) -> dict:
    out = {"branch": "?", "head": "?", "head_age_min": -1}
    try:
        r = subprocess.run(["git", "-C", str(root), "rev-parse", "--abbrev-ref", "HEAD"],
                           capture_output=True, text=True, timeout=2)
        if r.returncode == 0:
            out["branch"] = r.stdout.strip()
        r = subprocess.run(["git", "-C", str(root), "log", "-1", "--format=%h|%ct"],
                           capture_output=True, text=True, timeout=2)
        if r.returncode == 0 and "|" in r.stdout:
            sha, ts = r.stdout.strip().split("|", 1)
            out["head"] = sha
            try:
                out["head_age_min"] = max(0, int((time.time() - int(ts)) // 60))
            except ValueError:
                pass
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return out


def _provider_chips(limit: int = 6) -> str:
    try:
        from sinister_login import status_all  # type: ignore
        rows = status_all()
    except Exception:
        return ""
    on, off = [], []
    for r in rows:
        kind = r.get("auth", "?")
        tag = "env" if kind == "apikey" else ("local" if kind == "local" else kind)
        if r.get("configured"):
            on.append(f"{DOT_ON} {WHITE}{r['slug']}{RESET}{GRAY}({tag}){RESET}")
        else:
            off.append(f"{DOT_OFF} {GRAY}{r['slug']}{RESET}")
    extra = max(0, len(off) - max(0, limit - len(on)))
    chips = on + off[:limit - len(on)]
    return "  ".join(chips) + (f"  {GRAY}(+{extra}){RESET}" if extra else "")


def _heartbeat_status(root: Path) -> tuple[int, int, str]:
    hb_dir = root / "_shared-memory" / "heartbeats"
    if not hb_dir.exists():
        return 0, 0, ""
    fresh = total = 0
    items = []
    now = time.time()
    for p in hb_dir.glob("*.json"):
        if p.name.endswith(".tmp"):
            continue
        try:
            age = int((now - p.stat().st_mtime) // 60)
            total += 1
            if age < 30:
                fresh += 1
            items.append((p.stem, age))
        except OSError:
            continue
    items.sort(key=lambda r: r[1])
    detail = "  ".join(f"{GREEN if a < 30 else GRAY}{s}{RESET} {GRAY}{a}m{RESET}" for s, a in items[:3])
    return fresh, total, detail


def _inbox_count(root: Path) -> int:
    inbox = root / "_shared-memory" / "inbox"
    if not inbox.exists():
        return 0
    n = 0
    for sub in inbox.iterdir():
        if not sub.is_dir():
            continue
        for f in sub.glob("*.json"):
            if f.name == ".gitkeep":
                continue
            n += 1
    return n


def _brain_count(root: Path) -> int:
    idx = root / "_shared-memory" / "knowledge" / "_INDEX.md"
    if not idx.exists():
        return 0
    try:
        return sum(1 for ln in idx.read_text(encoding="utf-8").splitlines()
                   if ln.startswith("| ") and not ln.startswith("| Slug") and "|---|" not in ln)
    except OSError:
        return 0


def _load_projects(root: Path) -> list[dict]:
    out = []
    for path in (root / "automations" / "session-templates" / "projects.json",
                 root / "automations" / "session-templates" / "personal-projects.json"):
        try:
            if path.exists():
                out.extend(json.loads(path.read_text(encoding="utf-8")).get("projects", []))
        except Exception:
            pass
    return out


# ----- Dense status panel --------------------------------------------------

def _print_status_panel(root: Path) -> None:
    now = _utc_now()
    git = _git_status(root)
    age = git["head_age_min"]
    age_str = "now" if age == 0 else f"{age}m"
    fresh, total, hb_detail = _heartbeat_status(root)
    inbox = _inbox_count(root)
    brain = _brain_count(root)
    provider_line = _provider_chips()
    print(f"{PURPLE_BRIGHT}{BOLD}  RKOJ v{__version__}{RESET}{GRAY} · {now.strftime('%Y-%m-%d %H:%M')} UTC · "
          f"branch {WHITE}{git['branch']}{RESET}{GRAY} · HEAD {WHITE}{git['head']}{RESET}{GRAY} ({age_str}){RESET}")
    if provider_line:
        print(f"  {provider_line}")
    print(f"  {WHITE}agents: {fresh} live{RESET}{GRAY} / {total} total{RESET}  {hb_detail}  "
          f"{GRAY}· {RESET}{WHITE}inbox {inbox}{RESET}{GRAY} · {RESET}{WHITE}brain {brain}{RESET}")
    print(f"  {GRAY}(api-key:claude) opus-4.7 · /model · mcp: ruflo+vault · memory: forge-memory-bridge{RESET}")
    print()
    print(f"  {GRAY}EVE here. type {WHITE}/help{GRAY} for commands, {WHITE}/resume{GRAY} for past sessions, or describe what you want.{RESET}")


# ===========================================================================
# SLASH COMMAND DISPATCH (in-EXE; mirrors forge/commands.py for shell mode)
# ===========================================================================

def _cmd_help(args, root) -> str:
    """jcode-style /help overlay — rich.Panel grouped by section (in-EXE).

    Operator directive 2026-05-21: match jcode's overlay form factor with a
    title bearing a 0% token-usage indicator, and sections for Commands /
    Session / Memory & Swarm / Auth & Accounts / System / Navigation. Purple
    #A06EFF accent for headings; gray-dim descriptions.
    """
    if args:
        target = args[0].lstrip("/").lower()
        h = SLASH_COMMANDS.get(target)
        if not h:
            return f"  {RED}unknown command /{target}{RESET}"
        meta = SLASH_COMMAND_META.get(target, {})
        return (f"  {WHITE}/{target}{RESET}  {GRAY}{meta.get('summary', '')}{RESET}\n"
                f"  {GRAY}{meta.get('detail', '(no detail)')}{RESET}")

    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.text import Text
        import io
    except Exception:
        return _cmd_help_plaintext()

    P = "#A06EFF"
    DIM = "grey50"

    sections: list[tuple[str, list[tuple[str, str]]]] = [
        ("Commands", [
            ("/help",         "show this overlay"),
            ("/model",        "list | current | set <id> | info <id> | providers"),
            ("/agents",       "live agents + heartbeat ages"),
            ("/effort",       "none|low|medium|high|xhigh"),
            ("/fast",         "on|off|status|default"),
            ("/transport",    "set transport mode auto|https|websocket"),
            ("/alignment",    "text alignment: status|centered|left"),
            ("/config",       "show config (sub: init, edit)"),
            ("/dictate",      "external speech-to-text"),
            ("/git",          "git status -sb for sanctum repo"),
            ("/context",      "full session context snapshot"),
            ("/info",         "session info + mode / tools"),
            ("/usage",        "token-quota / billing endpoint registry"),
            ("/version",      "show version + bundled tools"),
            ("/changelog",    "recent PROGRESS entries"),
        ]),
        ("Session", [
            ("/clear",        "clear this pane's log"),
            ("/compact",      "consolidate memory (memory-consolidate.ps1)"),
            ("/rewind",       "show numbered history, /rewind N to step back"),
            ("/fix",          "attempt recovery from errors"),
            ("/poke",         "nudge model to resume incomplete todos"),
            ("/improve",      "autonomous code-quality loop (sub: resume)"),
            ("/refactor",     "safe refactor + review loop (sub: resume)"),
            ("/split",        "clone session into new window"),
            ("/splitview",    "mirror current chat in side panel"),
            ("/transfer",     "fresh session with compacted context + todos"),
            ("/workspace",    "Niri-style workspace splits"),
            ("/catchup",      "side-panel briefs (sub: next)"),
            ("/back",         "return to previous Catch Up session"),
            ("/resume",       "browse + read past resume-points"),
            ("/save",         "write a resume-point now"),
            ("/rename",       "name / unname session"),
            ("/unsave",       "remove bookmark"),
        ]),
        ("Memory & Swarm", [
            ("/memory",       "on|off | search | write | recall | list"),
            ("/goals",        "show WORK-TOWARD.md goals"),
            ("/swarm",        "on|off | spawn N | list | dm | broadcast"),
        ]),
        ("Auth & Accounts", [
            ("/auth",         "11-provider auth status"),
            ("/login",        "providers | current | doctor <p> | env <p>"),
            ("/account",      "alias of /auth (combined picker)"),
            ("/subscription", "Sinister LLC subscription scaffold"),
        ]),
        ("System", [
            ("/reload",        "reload — restart RKOJ.exe"),
            ("/restart",       "restart with current binary"),
            ("/rebuild",       "full rebuild — instructions"),
            ("/client-reload", "remote-only"),
            ("/server-reload", "remote-only"),
            ("/debug-visual",  "enable Textual reactive inspector"),
            ("/quit",          "exit"),
        ]),
        ("Navigation", [
            ("PageUp/PageDown", "scroll the chat log"),
            ("Esc",             "close this overlay"),
            ("/help <cmd>",     "show detail for one command"),
        ]),
    ]

    body = Text()
    body.append("Help", style=f"bold {P}")
    body.append("                                                      ")
    body.append("0%", style=f"bold {DIM}")
    body.append("  (token usage)\n", style=DIM)
    body.append("\n")
    for title, rows in sections:
        body.append(f"{title}\n", style=f"bold {P}")
        width = max((len(n) for n, _ in rows), default=14)
        for name, desc in rows:
            body.append(f"  {name:<{width + 2}}", style="white")
            body.append(f"{desc}\n", style=DIM)
        body.append("\n")

    buf = io.StringIO()
    console = Console(file=buf, force_terminal=True, color_system="truecolor",
                      width=92, record=False, legacy_windows=False)
    panel = Panel(body, title=f"[{P}]EVE — RKOJ (jcode parity)[/]",
                  border_style=P, padding=(1, 2))
    console.print(panel)
    return buf.getvalue().rstrip()


def _cmd_help_plaintext() -> str:
    """Plain-text fallback for when rich is unavailable in the frozen EXE."""
    return (
        f"{PURPLE_BRIGHT}{BOLD}commands{RESET}\n"
        f"  {WHITE}/start{RESET}                  pick a project + mode and launch a session\n"
        f"  {WHITE}/resume{RESET}                 list resume-points grouped by project\n"
        f"  {WHITE}/projects{RESET}               list all known projects\n"
        f"  {WHITE}/agents{RESET}                 live agents + heartbeat ages\n"
        f"  {WHITE}/inbox [slug]{RESET}           list inbox messages\n"
        f"  {WHITE}/brain [tag]{RESET}            list brain entries\n"
        f"  {WHITE}/login{RESET}                  11-provider auth wallet status\n"
        f"  {WHITE}/usage{RESET}                  token-quota / billing endpoint registry\n"
        f"  {WHITE}/swarm{RESET}                  multi-agent broadcast/DM/spawn\n"
        f"  {WHITE}/memory <q>{RESET}             memory recall (forge-memory-bridge)\n"
        f"  {WHITE}/forge{RESET}                  launch the multi-pane Forge TUI\n"
        f"  {WHITE}/info{RESET}                   session info\n"
        f"  {WHITE}/version{RESET}                version + tool list\n"
        f"  {WHITE}/quit{RESET}                   exit\n"
        f"  {GRAY}(anything else: spawns an EVE agent with that as the prompt){RESET}"
    )


def _cmd_quit(args, root) -> str:
    sys.exit(0)


def _cmd_version(args, root) -> str:
    return _capture(lambda: subprocess.run(
        [sys.executable if not getattr(sys, "frozen", False) else sys.executable, "-c",
         "from sinister_cli.__main__ import _print_version; _print_version()"]
        if not getattr(sys, "frozen", False) else None,
        capture_output=True, text=True))  # never used in frozen


def _cmd_info(args, root) -> str:
    return (
        f"  identity:   EVE\n"
        f"  RKOJ:       v{__version__}\n"
        f"  sanctum:    {root}\n"
        f"  cwd:        {Path.cwd()}\n"
        f"  python:     {sys.version.split()[0]}\n"
        f"  platform:   {platform.platform()}"
    )


def _cmd_projects(args, root) -> str:
    projects = _load_projects(root)
    visible = [p for p in projects if not p.get("_subsumed_by")]
    lines = [f"{PURPLE_BRIGHT}{BOLD}projects ({len(visible)}){RESET}"]
    for p in visible:
        tag = (p.get("tag", "") or "")[:60]
        lines.append(f"  {WHITE}{p.get('key', '?'):<22}{RESET} {GRAY}{tag}{RESET}")
    return "\n".join(lines)


def _cmd_resume(args, root) -> str:
    """jcode-parity: /resume = browse by project. /resume <project> = list points. /resume <project> <N> = show detail."""
    rp_dir = root / "_shared-memory" / "resume-points"
    if not rp_dir.exists():
        return f"  {GRAY}no resume-points dir{RESET}"

    # /resume — group by project
    if not args:
        slots = {}
        for proj_dir in rp_dir.iterdir():
            if not proj_dir.is_dir():
                continue
            pts = sorted(proj_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            if pts:
                slots[proj_dir.name] = pts
        if not slots:
            return f"  {GRAY}no resume-points found{RESET}"
        lines = [f"{PURPLE_BRIGHT}{BOLD}resume-points by project{RESET}  {GRAY}(/resume <project> to expand){RESET}"]
        for proj in sorted(slots, key=lambda k: -slots[k][0].stat().st_mtime):
            latest = slots[proj][0]
            mt = datetime.datetime.fromtimestamp(latest.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            lines.append(f"  {WHITE}{proj:<28}{RESET} {GRAY}{len(slots[proj])} pts · latest {mt}{RESET}")
        return "\n".join(lines)

    proj_name = args[0]
    # fuzzy match project name
    candidates = []
    for d in rp_dir.iterdir():
        if d.is_dir() and proj_name.lower() in d.name.lower():
            candidates.append(d)
    if not candidates:
        return f"  {RED}no project matching `{proj_name}`. /resume to see all.{RESET}"
    if len(candidates) > 1 and len(args) < 2:
        return ("  " + RED + f"ambiguous: {[d.name for d in candidates]}" + RESET)
    proj_dir = candidates[0]
    pts = sorted(proj_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not pts:
        return f"  {GRAY}no resume-points in {proj_dir.name}{RESET}"

    # /resume <project> <N>
    if len(args) >= 2 and args[1].isdigit():
        idx = int(args[1])
        if not (1 <= idx <= len(pts)):
            return f"  {RED}idx out of range (1-{len(pts)}){RESET}"
        return _format_resume_point(pts[idx - 1])

    # /resume <project>
    lines = [f"{PURPLE_BRIGHT}{BOLD}{proj_dir.name}{RESET}  {GRAY}(/resume {proj_name} <N> to load detail){RESET}"]
    for i, p in enumerate(pts[:15], start=1):
        mt = datetime.datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        lines.append(f"  {PURPLE_BRIGHT}{i:>2}{RESET}. {WHITE}{p.name:<48}{RESET} {GRAY}{mt}{RESET}")
    return "\n".join(lines)


def _format_resume_point(path: Path) -> str:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return f"  {RED}read failed: {e}{RESET}"
    g = data.get("git", {})
    lines = [f"{PURPLE_BRIGHT}{BOLD}{path.name}{RESET}"]
    lines.append(f"  branch:    {g.get('branch', '?')}")
    lines.append(f"  head:      {g.get('head', '?')[:10]} {g.get('head_msg', '')[:80]}")
    for p in data.get("progress_top3", [])[:3]:
        lines.append(f"  · {p[:120]}")
    lines.append(f"  inbox:     {data.get('inbox_unread_count', 0)} unread")
    pwr = data.get("pre_warm_reads", [])
    if pwr:
        lines.append(f"  pre-warm reads ({len(pwr)}):")
        for r in pwr[:6]:
            lines.append(f"    · {Path(r).name}")
    return "\n".join(lines)


def _cmd_agents(args, root) -> str:
    hb_dir = root / "_shared-memory" / "heartbeats"
    if not hb_dir.exists():
        return f"  {GRAY}no heartbeats dir{RESET}"
    now = time.time()
    rows = []
    for p in hb_dir.glob("*.json"):
        if p.name.endswith(".tmp"):
            continue
        try:
            age = int((now - p.stat().st_mtime) // 60)
            rows.append((p.stem, age))
        except OSError:
            continue
    rows.sort(key=lambda r: r[1])
    if not rows:
        return f"  {GRAY}no agents{RESET}"
    lines = [f"{PURPLE_BRIGHT}{BOLD}agents ({len(rows)}){RESET}"]
    for slug, age in rows:
        marker = DOT_ON if age < 30 else DOT_OFF
        lines.append(f"  {marker} {WHITE}{slug:<28}{RESET} {GRAY}{age}m{RESET}")
    return "\n".join(lines)


def _cmd_inbox(args, root) -> str:
    inbox = root / "_shared-memory" / "inbox"
    if not inbox.exists():
        return f"  {GRAY}no inbox dir{RESET}"
    if args:
        slot = inbox / args[0]
        if not slot.exists():
            return f"  {RED}no inbox slot `{args[0]}`{RESET}"
        msgs = sorted(slot.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        lines = [f"{PURPLE_BRIGHT}{BOLD}inbox/{args[0]} ({len(msgs)}){RESET}"]
        for m in msgs[:20]:
            mt = datetime.datetime.fromtimestamp(m.stat().st_mtime).strftime("%m-%d %H:%M")
            lines.append(f"  {GRAY}{mt}{RESET}  {WHITE}{m.name[:80]}{RESET}")
        return "\n".join(lines)
    lines = [f"{PURPLE_BRIGHT}{BOLD}inbox{RESET}"]
    for sub in sorted(inbox.iterdir()):
        if not sub.is_dir():
            continue
        n = len([f for f in sub.glob("*.json") if f.name != ".gitkeep"])
        lines.append(f"  {WHITE}{sub.name:<28}{RESET} {GRAY}{n} msgs{RESET}")
    return "\n".join(lines)


def _cmd_brain(args, root) -> str:
    idx = root / "_shared-memory" / "knowledge" / "_INDEX.md"
    if not idx.exists():
        return f"  {GRAY}no _INDEX.md{RESET}"
    try:
        lines = idx.read_text(encoding="utf-8").splitlines()
    except OSError as e:
        return f"  {RED}{e}{RESET}"
    rows = [ln for ln in lines if ln.startswith("| ") and "|---" not in ln and not ln.startswith("| Slug")]
    if args:
        tag = args[0].lower()
        rows = [r for r in rows if tag in r.lower()]
    out = [f"{PURPLE_BRIGHT}{BOLD}brain ({len(rows)} match){RESET}"]
    for r in rows[:20]:
        parts = r.split("|")
        if len(parts) >= 3:
            slug = parts[1].strip()
            title = parts[2].strip()[:80]
            out.append(f"  {WHITE}{slug:<32}{RESET} {GRAY}{title}{RESET}")
    return "\n".join(out)


def _capture(_fn) -> str:
    try:
        return _fn()
    except Exception as e:
        return f"  {RED}{e}{RESET}"


def _route_sinister_cli(argv: list[str]) -> str:
    import io
    out, err = io.StringIO(), io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        from sinister_cli.__main__ import main as cli_main
        cli_main(argv)
    except SystemExit:
        pass
    except Exception as e:
        return f"  {RED}{e}{RESET}"
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    return (out.getvalue() or err.getvalue()).rstrip()


def _cmd_login(args, root) -> str:
    return _route_sinister_cli(["login"] + (args or ["providers"]))


def _cmd_usage(args, root) -> str:
    return _route_sinister_cli(["usage"] + (args or ["check-all"]))


def _cmd_swarm(args, root) -> str:
    return _route_sinister_cli(["swarm"] + (args or ["list"]))


def _cmd_memory(args, root) -> str:
    if not args:
        return _route_sinister_cli(["memory"])
    return _route_sinister_cli(["memory"] + args)


def _cmd_forge(args, root) -> str:
    """Launch the multi-pane Forge TUI inline. Takes over the console."""
    try:
        from forge.app import ForgeApp
    except Exception as e:
        return f"  {RED}forge backend unavailable: {e}{RESET}"
    try:
        ForgeApp().run()
    except Exception as e:
        return f"  {RED}forge crashed: {e}{RESET}"
    return f"  {GRAY}forge exited.{RESET}"


# ----- /start picker (bat-file project-picker parity) ---------------------

def _start_picker(root: Path) -> bool:
    """Interactive `/start` flow. Mirrors automations/start-sinister-session.ps1
    UX inline at the RKOJ.exe `>` prompt. Returns True if a session was
    launched, False on cancel.

    Steps: list (sorted by recency, max 20) → pick (1-N | new | q) → mode
    (r/e/s, default r) → set env + spawn (resume/expand → claude; shell →
    same shell continues).
    """
    proj_path = root / "automations" / "session-templates" / "projects.json"
    if not proj_path.exists():
        print(f"  {RED}/start: projects.json missing at {proj_path}{RESET}")
        return False
    try:
        data = json.loads(proj_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  {RED}/start: parse error: {e}{RESET}")
        return False
    projects = [p for p in data.get("projects", []) if not p.get("_subsumed_by")]
    if not projects:
        print(f"  {GRAY}/start: no projects in registry{RESET}")
        return False

    rp_dir = root / "_shared-memory" / "resume-points"

    def _mt(p: dict) -> float:
        for slot in (p.get("display"), p.get("key"), (p.get("key") or "").title()):
            if not slot:
                continue
            d = rp_dir / slot
            if d.exists():
                pts = list(d.glob("*.json"))
                if pts:
                    return max(x.stat().st_mtime for x in pts)
        return 0.0

    projects = sorted(projects, key=_mt, reverse=True)[:20]
    print(f"{PURPLE_BRIGHT}{BOLD}  /start — pick a project to resume{RESET}")
    for i, p in enumerate(projects, start=1):
        m = _mt(p)
        ts = datetime.datetime.fromtimestamp(m).strftime("%m-%d %H:%M") if m else "never"
        print(f"  {PURPLE_BRIGHT}{i:>2}{RESET}. {WHITE}{p.get('key', '?'):<22}{RESET} "
              f"{GRAY}· {p.get('display', '')}{RESET}  {GRAY}({ts}){RESET}")
    print()
    try:
        pick = input(f"  {PURPLE_BRIGHT}pick (1-{len(projects)}) or 'new', q to cancel:{RESET} ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    if not pick or pick == "q":
        print(f"  {GRAY}/start canceled{RESET}")
        return False

    slug = display = branch_topic = None
    if pick == "new":
        try:
            slug = input(f"  {PURPLE_BRIGHT}new slug:{RESET} ").strip()
            display = input(f"  {PURPLE_BRIGHT}display name:{RESET} ").strip() or slug
            branch_topic = input(f"  {PURPLE_BRIGHT}branch topic (short):{RESET} ").strip() or "scratch"
        except (EOFError, KeyboardInterrupt):
            print()
            return False
        if not slug:
            print(f"  {RED}/start: slug required{RESET}")
            return False
    elif pick.isdigit():
        idx = int(pick)
        if not (1 <= idx <= len(projects)):
            print(f"  {RED}/start: out of range (1-{len(projects)}){RESET}")
            return False
        proj = projects[idx - 1]
        slug = proj.get("key", "?")
        display = proj.get("display", slug)
        branch_topic = f"resume-{datetime.datetime.now().strftime('%Y-%m-%d')}"
    else:
        print(f"  {RED}/start: bad pick `{pick}`{RESET}")
        return False

    try:
        m = input(f"  {PURPLE_BRIGHT}mode? [r]esume / [e]xpand / [s]hell (default r):{RESET} ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    mode = "resume" if not m or m.startswith("r") else (
           "expand" if m.startswith("e") else (
           "shell"  if m.startswith("s") else "resume"))
    branch = f"agent/{slug}/{branch_topic}"

    # Last resume-point timestamp for display.
    last_rp = "fresh"
    rp_slot = rp_dir / (display or slug)
    if rp_slot.exists():
        pts = sorted(rp_slot.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
        if pts:
            last_rp = datetime.datetime.fromtimestamp(pts[0].stat().st_mtime).strftime("%Y-%m-%d %H:%M")

    print()
    print(f"  {PURPLE_BRIGHT}EVE on {display}{RESET} {GRAY}· {mode} · branch {branch} · resume-point {last_rp}{RESET}")

    os.environ["SINISTER_PROJECT"] = slug
    os.environ["SINISTER_PROJECT_DISPLAY"] = display or slug
    os.environ["SINISTER_MODE"] = mode
    os.environ["SINISTER_BRANCH"] = branch

    if mode == "shell":
        print(f"  {GRAY}shell mode — env set; type at the `>` prompt to continue.{RESET}")
        return True
    prompt = f"pick up where we left off on {display}"
    _spawn_claude(prompt, root)
    return True


def _cmd_start(args, root) -> str:
    """Interactive picker — only meaningful in the `>` shell loop. Triggers
    `_start_picker(root)` directly via the main loop bypass (see _dispatch_slash)."""
    return f"  {GRAY}(/start picker runs inline in the shell loop — see prompt above){RESET}"


# ----- jcode-parity stub factory ------------------------------------------

def _cmd_stub(name: str, description: str,
              subcommands: dict[str, str] | None = None):
    """Stub factory for jcode-parity surface. Operator directive 2026-05-21:
    every command in jcode's /help overlay must exist as either a real handler
    or a stub. Returns a handler that prints the not-implemented note."""
    def _h(args, root):
        if args and subcommands and args[0].lower() in subcommands:
            sub = args[0].lower()
            return (f"  {GRAY}[note] /{name} {sub}: {subcommands[sub]} — "
                    f"not implemented in v{__version__}; tracked in jcode-parity-roadmap{RESET}")
        return (f"  {GRAY}[note] /{name}: {description} — "
                f"not implemented in v{__version__}; tracked in jcode-parity-roadmap{RESET}")
    return _h


# Metadata table (used by /help <cmd>): name -> {summary, detail, category}.
SLASH_COMMAND_META: dict[str, dict[str, str]] = {
    # Implemented
    "help":     {"summary": "show this overlay",                 "category": "Commands", "detail": "/help <cmd> for detail on one command"},
    "quit":     {"summary": "exit",                              "category": "System",   "detail": ""},
    "version":  {"summary": "show version + bundled tools",      "category": "Commands", "detail": ""},
    "info":     {"summary": "session info + mode / tools",       "category": "Commands", "detail": ""},
    "projects": {"summary": "list all known projects",           "category": "Commands", "detail": ""},
    "start":    {"summary": "pick a project + mode and launch",  "category": "Session",  "detail": "bat-file parity picker"},
    "resume":   {"summary": "browse + read past resume-points",  "category": "Session",  "detail": "/resume <project> <N>"},
    "agents":   {"summary": "live agents + heartbeat ages",      "category": "Commands", "detail": ""},
    "inbox":    {"summary": "list inbox messages",               "category": "Memory & Swarm", "detail": ""},
    "brain":    {"summary": "list brain entries",                "category": "Memory & Swarm", "detail": ""},
    "login":    {"summary": "11-provider auth wallet status",    "category": "Auth & Accounts", "detail": "/login providers for table"},
    "usage":    {"summary": "token-quota / billing endpoint",    "category": "Commands", "detail": ""},
    "swarm":    {"summary": "multi-agent broadcast/DM/spawn",    "category": "Memory & Swarm", "detail": ""},
    "memory":   {"summary": "memory recall (forge-memory-bridge)", "category": "Memory & Swarm", "detail": ""},
    "forge":    {"summary": "launch the multi-pane Forge TUI",   "category": "Commands", "detail": ""},
}


SLASH_COMMANDS = {
    # ---- implemented (existing handlers) ----
    "help":     _cmd_help,
    "?":        _cmd_help,
    "h":        _cmd_help,
    "quit":     _cmd_quit,
    "exit":     _cmd_quit,
    "q":        _cmd_quit,
    "version":  _cmd_version,
    "v":        _cmd_version,
    "info":     _cmd_info,
    "projects": _cmd_projects,
    "start":    _cmd_start,
    "resume":   _cmd_resume,
    "agents":   _cmd_agents,
    "inbox":    _cmd_inbox,
    "brain":    _cmd_brain,
    "login":    _cmd_login,
    "usage":    _cmd_usage,
    "swarm":    _cmd_swarm,
    "memory":   _cmd_memory,
    "forge":    _cmd_forge,

    # ---- jcode-parity stubs (Commands section) ----
    "model":      _cmd_stub("model",      "list | current | set <id> | info <id> | providers"),
    "effort":     _cmd_stub("effort",     "none|low|medium|high|xhigh"),
    "fast":       _cmd_stub("fast",       "on|off|status|default"),
    "transport":  _cmd_stub("transport",  "set transport mode auto|https|websocket"),
    "alignment":  _cmd_stub("alignment",  "text alignment: status|centered|left"),
    "config":     _cmd_stub("config",     "show config",
                            subcommands={"init": "write default agent-prefs.json",
                                          "edit": "open agent-prefs.json in $EDITOR"}),
    "dictate":    _cmd_stub("dictate",    "external speech-to-text"),
    "git":        _cmd_stub("git",        "git status -sb for sanctum repo"),
    "context":    _cmd_stub("context",    "full session context snapshot"),
    "changelog":  _cmd_stub("changelog",  "recent PROGRESS entries"),

    # ---- Session ----
    "clear":      _cmd_stub("clear",      "clear this pane's log"),
    "compact":    _cmd_stub("compact",    "consolidate memory (memory-consolidate.ps1)"),
    "rewind":     _cmd_stub("rewind",     "show numbered history, /rewind N"),
    "fix":        _cmd_stub("fix",        "attempt recovery from errors"),
    "poke":       _cmd_stub("poke",       "nudge model to resume incomplete todos"),
    "improve":    _cmd_stub("improve",    "autonomous code-quality loop",
                            subcommands={"resume": "resume a paused improve loop"}),
    "refactor":   _cmd_stub("refactor",   "safe refactor + review loop",
                            subcommands={"resume": "resume a paused refactor loop"}),
    "split":      _cmd_stub("split",      "clone session into new window"),
    "splitview":  _cmd_stub("splitview",  "mirror current chat in side panel"),
    "transfer":   _cmd_stub("transfer",   "fresh session with compacted context + todos"),
    "workspace":  _cmd_stub("workspace",  "Niri-style workspace splits"),
    "catchup":    _cmd_stub("catchup",    "side-panel briefs for finished sessions",
                            subcommands={"next": "advance to next Catch Up brief"}),
    "back":       _cmd_stub("back",       "return to previous Catch Up session"),
    "save":       _cmd_stub("save",       "write a resume-point now"),
    "rename":     _cmd_stub("rename",     "name / unname session"),
    "unsave":     _cmd_stub("unsave",     "remove bookmark"),

    # ---- Memory & Swarm ----
    "goals":      _cmd_stub("goals",      "show WORK-TOWARD.md goals"),

    # ---- Auth & Accounts ----
    "auth":       _cmd_stub("auth",       "11-provider auth status"),
    "account":    _cmd_stub("account",    "alias of /auth (combined picker)"),
    "subscription": _cmd_stub("subscription", "Sinister LLC subscription scaffold"),

    # ---- System ----
    "reload":         _cmd_stub("reload",         "restart RKOJ.exe"),
    "restart":        _cmd_stub("restart",        "restart with current binary"),
    "rebuild":        _cmd_stub("rebuild",        "full rebuild — instructions"),
    "client-reload":  _cmd_stub("client-reload",  "remote-only"),
    "server-reload":  _cmd_stub("server-reload",  "remote-only"),
    "debug-visual":   _cmd_stub("debug-visual",   "enable Textual reactive inspector"),
}

# Auto-populate META for stubs (default summary = "(stub)" so /help <cmd> works).
for _name, _h in list(SLASH_COMMANDS.items()):
    if _name in SLASH_COMMAND_META:
        continue
    SLASH_COMMAND_META[_name] = {"summary": "(jcode-parity stub)",
                                  "category": "stub",
                                  "detail": "not implemented in v" + __version__}


def _dispatch_slash(line: str, root: Path) -> str | None:
    if not line.startswith("/"):
        return None
    body = line[1:].strip()
    if not body:
        return _cmd_help([], root)
    import shlex
    try:
        tokens = shlex.split(body, posix=False)
    except ValueError:
        tokens = body.split()
    cmd = tokens[0].lower()
    args = tokens[1:]
    h = SLASH_COMMANDS.get(cmd)
    if h:
        return h(args, root)
    return f"  {RED}unknown /{cmd}. /help for commands.{RESET}"


# ===========================================================================
# Natural-language: spawn an EVE agent on Sanctum root with that text as prompt
# ===========================================================================

def _spawn_anthropic_direct(text: str, root: Path) -> int | None:
    """Try the Anthropic SDK direct path (multi-step visible tool reasoning).

    Returns the exit code on success, or None to signal "fallback to claude -p".
    Activation gate: `ANTHROPIC_API_KEY` env var present AND the spawn module
    importable. Pre-turn recall + post-turn write are handled inside the module
    (mirror the claude -p path) so memory stays consistent across modes.
    """
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        from forge.spawn.anthropic_direct import run_turn  # type: ignore
    except Exception as e:
        print(f"  {GRAY}(anthropic_direct unavailable: {e} — falling back to claude -p){RESET}")
        return None
    print(f"  {GRAY}→ EVE on Sanctum (SDK direct):{RESET} {WHITE}{text}{RESET}")
    try:
        return int(run_turn(text, root) or 0)
    except KeyboardInterrupt:
        print()
        return 130
    except Exception as e:
        print(f"  {RED}anthropic_direct crashed: {e}{RESET}")
        return None


def _spawn_claude(text: str, root: Path) -> int:
    """Spawn an EVE turn on Sanctum.

    Prefers the Anthropic SDK direct path (visible multi-step tool reasoning)
    when `ANTHROPIC_API_KEY` is set. Operator (2026-05-21): wants jcode-style
    visible tool calls, not the one-shot `claude -p` print. The SDK path falls
    through to `claude -p` if the key is missing or the SDK module crashes.

    jcode-style memory wiring on the `claude -p` fallback:
      1. PRE-TURN: forge-memory-bridge.recall(text, k=4) — surface relevant
         brain entries + past turns; inject as context prefix.
      2. SPAWN claude -p with the augmented prompt; stream stdout/stderr inline.
      3. POST-TURN: forge-memory-bridge.write("session", text) so the next
         turn can recall it. All jcode memory features inherited.
    """
    # ---- (0) Prefer SDK direct path when ANTHROPIC_API_KEY is set --------
    rc = _spawn_anthropic_direct(text, root)
    if rc is not None:
        return rc

    print(f"  {GRAY}→ EVE on Sanctum:{RESET} {WHITE}{text}{RESET}")
    # ---- (1) PRE-TURN memory recall ----
    memory_prefix = ""
    try:
        import forge_memory_bridge as _mem  # type: ignore
        hits = _mem.recall(text, limit=4) or []
        if hits:
            lines = ["[memory: recent relevant context]"]
            for h in (hits if isinstance(hits, list) else [hits]):
                lines.append(f"- {str(h)[:200]}")
            memory_prefix = "\n".join(lines) + "\n\n"
            print(f"  {GRAY}↺ memory recall: {len(hits)} hits{RESET}")
    except Exception:
        pass
    augmented = (memory_prefix + text) if memory_prefix else text

    print(f"  {GRAY}(claude -p stream — Ctrl+C to interrupt){RESET}")
    print()

    # ---- (2) SPAWN claude -p ----
    # Resolve claude binary explicitly — PyInstaller sterile-PATH means
    # `which claude` may miss the npm-global shim. Try `.exe` first then plain.
    candidates = [
        os.path.expanduser(r"~\.local\bin\claude.exe"),
        os.path.expanduser(r"~\.local\bin\claude"),
        "claude.exe", "claude",
    ]
    last_err: Exception | None = None
    rc = 1
    for cmd in candidates:
        if cmd.startswith(os.path.expanduser("~")) and not Path(cmd).exists():
            continue
        try:
            rc = subprocess.call(
                [cmd, "--dangerously-skip-permissions", "-p", augmented],
                cwd=str(root),
            )
            break
        except FileNotFoundError as e:
            last_err = e
            continue
        except KeyboardInterrupt:
            print()
            return 130
    else:
        print(f"  {RED}claude CLI not found ({last_err}){RESET}")
        print(f"  {GRAY}install: https://github.com/anthropics/claude-code{RESET}")
        return 1

    # ---- (3) POST-TURN memory write ----
    try:
        import forge_memory_bridge as _mem  # type: ignore
        _mem.write("rkoj-shell", text)
    except Exception:
        pass
    return rc


# ===========================================================================
# Main shell loop
# ===========================================================================

def _launch_forge_tui(sanctum_root: Path) -> int:
    """Operator 2026-05-21: launch RKOJ.exe → goes straight to the multi-pane
    Forge TUI (Sinister Panel sidebar + Agents/ADB tabs + niri-style scrollable
    panes). Same code path as `/forge` at the simple `>` prompt, but the
    default."""
    try:
        from forge.app import ForgeApp
    except Exception as exc:
        sys.stderr.write(f"\n[RKOJ] Forge TUI import failed: {exc}\n"
                         f"[RKOJ] falling back to the simple `>` shell.\n\n")
        return _shell_loop(sanctum_root)
    try:
        ForgeApp().run()
        return 0
    except (KeyboardInterrupt, SystemExit):
        return 0
    except Exception as exc:
        sys.stderr.write(f"\n[RKOJ] Forge TUI crashed: {exc}\n"
                         f"[RKOJ] falling back to the simple `>` shell.\n\n")
        return _shell_loop(sanctum_root)


def _shell_loop(sanctum_root: Path) -> int:
    while True:
        print()
        try:
            line = input(f"  {PURPLE_BRIGHT}>{RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not line:
            continue
        if line.startswith("/"):
            # /start needs interactive stdin (bat-file picker parity) — bypass
            # the stateless dispatcher and call the picker directly.
            stripped = line[1:].strip().lower()
            if stripped == "start" or stripped.startswith("start "):
                _start_picker(sanctum_root)
                continue
            out = _dispatch_slash(line, sanctum_root)
            if out:
                print(out)
            continue
        # natural language → spawn EVE on Sanctum
        rc = _spawn_claude(line, sanctum_root)
        print(f"  {GRAY}(exit {rc}){RESET}")


def main() -> int:
    _install_runtime_logger()
    rv = _route_subcommand(sys.argv[1:])
    if rv is not None:
        return rv

    _enable_vt()
    sanctum_root = _find_sanctum_root()

    # Operator 2026-05-21 (image 27): "still no ui when i launch exe with tabs
    # and aeverything i asked you to do". Default mode is the Forge TUI (sidebar
    # + Agents/ADB tabs + niri scroll). `--shell` keeps the jcode-style minimal
    # `>` prompt for operators who prefer it.
    argv = sys.argv[1:]
    if "--shell" in argv or os.environ.get("RKOJ_DEFAULT_MODE", "").lower() == "shell":
        print()
        try:
            _print_mark()
        except UnicodeEncodeError:
            print(PURPLE_BRIGHT + "  SINISTER" + RESET)
        with _Spin("warming sanctum"):
            time.sleep(0.25)
        _print_status_panel(sanctum_root)
        return _shell_loop(sanctum_root)

    return _launch_forge_tui(sanctum_root)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print()
        sys.exit(130)
