# Sinister Forge :: commands.py — jcode-parity slash command registry
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Operator directive 2026-05-21 (verbatim): *"make sure we have all features
# they have. all memory systems. memory on by deafult. modes like swarm all
# that shit + all the mcp tools we have that need to auto start when thyey
# are being called. all skills we use all that"*
#
# Central slash-command registry. Mirrors jcode v0.12.3's 91-command surface.
# Each command is a dict entry: handler(args, pane, app) -> str|None.
# Returns a string → pane writes it. Returns None → handler already printed.
#
# Resolution order in AgentPane:
#   1. `/cmd args...`     → SLASH_COMMANDS (this file)
#   2. `:cmd args...`     → AgentPane._handle_builtin (legacy `:` prefix)
#   3. `/<skill-name>`    → dynamic skill activation (scans skills/ dirs)
#   4. else               → forward to subprocess stdin

from __future__ import annotations

import datetime
import difflib
import json
import os
import platform
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from typing import Any, Callable, Iterable


# ----- module-state ------------------------------------------------------

# Per-session toggles. Memory is ON by default per operator 2026-05-21.
_state: dict[str, Any] = {
    "memory_enabled": True,
    "swarm_enabled": False,
    "poke_enabled": False,
    "autoreview_enabled": False,
    "autojudge_enabled": False,
    "splitview_enabled": False,
    "workspace_enabled": False,
    "scroll_lock": False,
    "effort": "medium",          # none/low/medium/high/xhigh
    "fast_mode": "default",      # on/off/default
    "default_provider": None,
    "default_model": None,
    "SINISTER_DEBUG_VISUAL": False,
}


def state(key: str, default: Any = None) -> Any:
    return _state.get(key, default)


def set_state(key: str, value: Any) -> None:
    _state[key] = value


# ----- forge-prefs persistence ------------------------------------------

def _forge_prefs_path() -> Path:
    """Returns ~/.config/sinister/forge-prefs.json or
    %APPDATA%/sinister/forge-prefs.json on Windows."""
    if platform.system() == "Windows":
        appdata = os.environ.get("APPDATA")
        base = Path(appdata) if appdata else Path.home() / "AppData" / "Roaming"
        return base / "sinister" / "forge-prefs.json"
    return Path.home() / ".config" / "sinister" / "forge-prefs.json"


def _load_forge_prefs() -> dict:
    """Read forge-prefs.json. Returns {} on any error (missing/parse/etc)."""
    p = _forge_prefs_path()
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def _save_forge_prefs(prefs: dict) -> Path:
    """Atomic write — tmp + rename. Creates parent dirs as needed."""
    p = _forge_prefs_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(prefs, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(str(tmp), str(p))
    return p


# ----- todos persistence (jcode-parity /todo) ----------------------------

def _todos_path() -> Path:
    """Returns ~/.config/sinister/todos.json or %APPDATA%/sinister/todos.json."""
    if platform.system() == "Windows":
        appdata = os.environ.get("APPDATA")
        base = Path(appdata) if appdata else Path.home() / "AppData" / "Roaming"
        return base / "sinister" / "todos.json"
    return Path.home() / ".config" / "sinister" / "todos.json"


def _load_todos() -> list[dict]:
    """Read todos.json. Returns [] on any error (missing/parse/etc)."""
    p = _todos_path()
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8-sig"))
        if isinstance(data, list):
            return data
        return []
    except Exception:
        return []


def _save_todos(todos: list[dict]) -> Path:
    """Atomic write — tmp + rename. Creates parent dirs as needed."""
    p = _todos_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(todos, indent=2, sort_keys=False), encoding="utf-8")
    os.replace(str(tmp), str(p))
    return p


# ----- unified-diff helper (jcode-parity /diff) --------------------------

def _unified_diff_text(a: str, b: str, fromfile: str, tofile: str) -> str:
    """Return unified diff between two text blobs. Empty string if identical."""
    a_lines = a.splitlines(keepends=True) if a else []
    b_lines = b.splitlines(keepends=True) if b else []
    diff = difflib.unified_diff(
        a_lines, b_lines, fromfile=fromfile, tofile=tofile, n=3
    )
    return "".join(diff)


# ----- sanctum-root helper -----------------------------------------------

def _sanctum_root() -> Path:
    for c in (os.environ.get("SANCTUM_ROOT"),
              r"D:\Sinister Sanctum", r"C:\Sinister Sanctum",
              str(Path.home() / "Sinister Sanctum")):
        if c and (Path(c) / "CLAUDE.md").exists():
            return Path(c)
    return Path(r"D:\Sinister Sanctum")


# ===========================================================================
# CORE COMMANDS — implemented
# ===========================================================================

def _cmd_help(args, pane, app) -> str:
    """jcode-style /help overlay — rich.Panel grouped by section.

    Operator directive 2026-05-21: jcode's /help opens a beautiful overlay with
    60+ commands organized in sections. Match that form factor (Title with 0%
    token indicator, Commands / Session / Memory & Swarm / Auth & Accounts /
    System / Navigation sections, purple #A06EFF headings, gray-dim descs).
    """
    if args:
        target = args[0].lstrip("/").lower()
        e = SLASH_COMMANDS.get(target)
        if not e:
            return f"[yellow]unknown command /{target}[/]"
        return f"[bold]/{target}[/]  {e.get('summary', '')}\n  {e.get('detail', '(no detail)')}"

    # Build overlay via rich.Panel. Render to a string so it works in both the
    # Textual pane (which calls pane.write) and the in-EXE shell (which prints).
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.text import Text
        import io
    except Exception:
        return _cmd_help_plaintext()

    PURPLE = "#A06EFF"
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
            ("/quit",          "exit Forge"),
        ]),
        ("Navigation", [
            ("PageUp/PageDown", "scroll the chat log"),
            ("Esc",             "close this overlay"),
            ("/help <cmd>",     "show detail for one command"),
        ]),
    ]

    body = Text()
    body.append("Help", style=f"bold {PURPLE}")
    body.append("                                                      ")
    body.append("0%", style=f"bold {DIM}")
    body.append("  (token usage)\n", style=DIM)
    body.append("\n")
    for title, rows in sections:
        body.append(f"{title}\n", style=f"bold {PURPLE}")
        width = max((len(n) for n, _ in rows), default=14)
        for name, desc in rows:
            body.append(f"  {name:<{width + 2}}", style="white")
            body.append(f"{desc}\n", style=DIM)
        body.append("\n")

    buf = io.StringIO()
    console = Console(file=buf, force_terminal=True, color_system="truecolor",
                      width=92, record=False, legacy_windows=False)
    panel = Panel(body, title=f"[{PURPLE}]EVE — Forge[/]",
                  border_style=PURPLE, padding=(1, 2))
    console.print(panel)
    return buf.getvalue().rstrip()


def _cmd_help_plaintext() -> str:
    """Plain-text fallback for when rich is unavailable."""
    lines = ["[bold]EVE :: Forge slash commands (jcode parity)[/]\n"]
    by_cat: dict[str, list[str]] = {}
    for name, meta in sorted(SLASH_COMMANDS.items()):
        cat = meta.get("category", "misc")
        by_cat.setdefault(cat, []).append(name)
    cat_order = ["core", "session", "memory", "swarm", "auth", "system",
                 "agent", "ui", "loop", "skills", "misc"]
    for cat in cat_order:
        if cat not in by_cat:
            continue
        lines.append(f"[purple]{cat.upper()}[/]")
        for n in by_cat[cat]:
            s = SLASH_COMMANDS[n].get("summary", "")
            lines.append(f"  /{n:<14} {s}")
    lines.append("\n[dim]Esc closes overlay · PageUp/PageDown scroll · /help <cmd> detail[/]")
    return "\n".join(lines)


def _cmd_quit(args, pane, app) -> str:
    if app is not None:
        app.exit()
    return None


def _cmd_clear(args, pane, app) -> str:
    """jcode /clear — wipe in-memory conversation history of the current session.

    Tries forge_memory_bridge.clear_current_session() first; if absent, falls
    back to clearing the pane's log buffer. Never raises. Returns a 1-line
    confirmation string.
    """
    cleared_bridge = False
    bridge_err = None
    try:
        import forge_memory_bridge  # type: ignore
        fn = getattr(forge_memory_bridge, "clear_current_session", None)
        if callable(fn):
            try:
                fn()
                cleared_bridge = True
            except Exception as e:
                bridge_err = str(e)
    except Exception:
        pass

    if pane is not None and hasattr(pane, "clear_log"):
        try:
            pane.clear_log()
        except Exception:
            pass

    if cleared_bridge:
        return "  session cleared (bridge.clear_current_session ok)"
    if bridge_err:
        return f"  session cleared (in-memory only; bridge errored: {bridge_err})"
    return "  session cleared (in-memory only)"


def _cmd_version(args, pane, app) -> str:
    try:
        from forge import __version__ as forge_v
    except Exception:
        forge_v = "?"
    sanctum_versions = []
    for pkg in ("sinister_cli", "sinister_login", "sinister_usage", "sinister_model",
                "sinister_swarm", "forge_memory_bridge", "memory_graph_render"):
        try:
            import importlib
            m = importlib.import_module(pkg)
            sanctum_versions.append(f"  {pkg:<22} {getattr(m, '__version__', '?')}")
        except Exception:
            sanctum_versions.append(f"  {pkg:<22} not installed")
    return ("[bold]Sinister RKOJ / Forge[/]\n"
            f"  forge                  {forge_v}\n"
            f"  RKOJ.exe entry         v0.3.2\n"
            + "\n".join(sanctum_versions) +
            f"\n  python                 {sys.version.split()[0]}\n"
            f"  platform               {platform.platform()}")


def _cmd_info(args, pane, app) -> str:
    sr = _sanctum_root()
    proj = os.environ.get("SINISTER_PROJECT", "?")
    proj_disp = os.environ.get("SINISTER_PROJECT_DISPLAY", proj)
    mode = os.environ.get("SINISTER_MODE", "?")
    tools = os.environ.get("SINISTER_TOOLS", "")
    return (f"[bold]Session info[/]\n"
            f"  identity:   EVE\n"
            f"  project:    {proj_disp}  ({proj})\n"
            f"  mode:       {mode}\n"
            f"  tools:      {tools or '(none)'}\n"
            f"  sanctum:    {sr}\n"
            f"  cwd:        {Path.cwd()}\n"
            f"  memory:     {'on' if state('memory_enabled') else 'off'}\n"
            f"  swarm:      {'on' if state('swarm_enabled') else 'off'}\n"
            f"  effort:     {state('effort')}\n"
            f"  fast:       {state('fast_mode')}")


def _cmd_context(args, pane, app) -> str:
    """jcode /context — full session context snapshot.

    Prints: message count, tokens estimate (chars/4), current model (from
    sinister-model state), pre-warm reads list (from last resume-point),
    active skills, last compaction (if any), inbox tail.
    """
    sr = _sanctum_root()
    lines = ["[bold]Context snapshot[/]"]
    lines.append(f"  branch: {_git_branch(sr)}  head: {_git_head(sr)}")

    # 1. message count + token estimate from latest session journal
    sessions_dir = sr / "_shared-memory" / "forge-memory" / "anthropic-direct-sessions"
    msg_count = 0
    char_count = 0
    journal_name = "(none)"
    if sessions_dir.exists():
        jrn = sorted(sessions_dir.glob("*.jsonl"),
                     key=lambda p: p.stat().st_mtime, reverse=True)
        if jrn:
            try:
                txt = jrn[0].read_text(encoding="utf-8")
                journal_name = jrn[0].name
                for raw in txt.splitlines():
                    raw = raw.strip()
                    if not raw:
                        continue
                    msg_count += 1
                    char_count += len(raw)
            except Exception:
                pass
    token_est = char_count // 4
    lines.append(f"  journal: {journal_name}")
    lines.append(f"  messages: {msg_count}  ·  chars: {char_count}  ·  ~tokens: {token_est}")

    # 2. current model (sinister-model state)
    model_line = "  model: (none persisted)"
    try:
        from sinister_model.state import get_current as _get_current  # type: ignore
        cur = _get_current()
        if cur:
            model_line = (f"  model: {cur.get('model_id', '?')}  "
                          f"provider={cur.get('provider', '?')}  "
                          f"set_at={cur.get('set_at', '?')}")
    except Exception as e:
        model_line = f"  model: (sinister-model unavailable: {e})"
    lines.append(model_line)

    # 3. pre-warm reads from the latest resume-point
    proj = (os.environ.get("SINISTER_PROJECT_DISPLAY")
            or os.environ.get("SINISTER_PROJECT")
            or "Sinister Sanctum")
    rp_dir = sr / "_shared-memory" / "resume-points"
    rps: list[Path] = []
    for slot in (proj, "Sanctum", "Sinister Sanctum"):
        d = rp_dir / slot
        if d.exists():
            rps += list(d.glob("*.json"))
    rps.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    pwr: list[str] = []
    if rps:
        try:
            # resume-points may be BOM-prefixed (PS1 ConvertTo-Json default).
            data = json.loads(rps[0].read_text(encoding="utf-8-sig"))
            pwr = (data.get("pre_warm_reads")
                   or data.get("last_5_files_touched_24h") or [])
        except Exception:
            pass
    if pwr:
        lines.append(f"  pre-warm reads ({len(pwr)}) [from {rps[0].name}]:")
        for r in pwr[:5]:
            lines.append(f"    · {r}")
    else:
        lines.append("  pre-warm reads: (none — no resume-point found)")

    # 4. active skills (via SkillRegistry, fall back to filesystem)
    skill_names: list[str] = []
    try:
        from forge.skills import SkillRegistry  # type: ignore
        reg = SkillRegistry.shared()
        skill_names = list(reg.names())
    except Exception:
        for root in (Path.home() / ".claude" / "skills",
                     sr / ".claude" / "skills",
                     sr / "skills"):
            if root.exists():
                for d in root.iterdir():
                    if d.is_dir() and not d.name.startswith("_"):
                        skill_names.append(d.name)
        skill_names = sorted(set(skill_names))
    if skill_names:
        preview = ", ".join(skill_names[:12])
        more = f"  (+{len(skill_names) - 12} more)" if len(skill_names) > 12 else ""
        lines.append(f"  active skills ({len(skill_names)}): {preview}{more}")
    else:
        lines.append("  active skills: (none discovered)")

    # 5. last compaction (if /compact was called this session)
    lc = state("last_compaction_path")
    if lc:
        lines.append(f"  last compaction: {lc}")

    # 6. inbox tail (preserve previous behavior)
    inbox_proj = os.environ.get("SINISTER_PROJECT", "?")
    inbox = sr / "_shared-memory" / "inbox" / inbox_proj
    if inbox.exists():
        items = sorted(inbox.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]
        lines.append(f"  inbox/{inbox_proj}/: {len(items)} recent")
        for it in items:
            lines.append(f"    · {it.name}")

    return "\n".join(lines)


def _cmd_git(args, pane, app) -> str:
    """jcode /git — branch + working tree status for sanctum repo.

    Usage:
      /git              -> status of sanctum repo
      /git status       -> same (subarg is optional + accepted for parity)
      /git --repo <p>   -> status of repo at <p>

    Shows `git status --short` + the last commit summary
    (`git log -1 --format='%h %s (%cr)'`).
    """
    # Resolve target repo
    repo = _sanctum_root()
    if args:
        toks = list(args)
        if "--repo" in toks:
            idx = toks.index("--repo")
            if idx + 1 < len(toks):
                repo = Path(toks[idx + 1])
                # strip it for any trailing parsing
                del toks[idx:idx + 2]
            else:
                return "[yellow]/git: --repo requires a path[/]"
        # remaining toks may be 'status' (subarg) — ignored, only subcommand we accept

    if not repo.exists():
        return f"[red]/git: repo path does not exist: {repo}[/]"

    try:
        branch = _git_branch(repo)
        head = _git_head(repo)
        st = subprocess.run(
            ["git", "-C", str(repo), "status", "--short"],
            capture_output=True, text=True, timeout=3,
        )
        lg = subprocess.run(
            ["git", "-C", str(repo), "log", "-1", "--format=%h %s (%cr)"],
            capture_output=True, text=True, timeout=3,
        )
    except Exception as e:
        return f"[red]git failed: {e}[/]"

    status_body = st.stdout.rstrip() or "(working tree clean)"
    last = lg.stdout.strip() or f"{head} (no log)"
    return (f"[bold]git[/]  [dim]{repo}[/]\n"
            f"  branch: {branch}\n"
            f"  last:   {last}\n"
            f"  status:\n{status_body}")


def _cmd_config(args, pane, app) -> str:
    sr = _sanctum_root()
    cfg = sr / "automations" / "session-templates" / "agent-prefs.json"
    if args and args[0] == "edit":
        try:
            if platform.system() == "Windows":
                os.startfile(str(cfg))
            else:
                subprocess.Popen([os.environ.get("EDITOR", "vi"), str(cfg)])
            return f"  opened {cfg}"
        except Exception as e:
            return f"[red]config edit failed: {e}[/]"
    if args and args[0] == "init":
        if cfg.exists():
            return f"[yellow]config already exists: {cfg}[/]\n  /config edit to open"
        try:
            cfg.parent.mkdir(parents=True, exist_ok=True)
            cfg.write_text(json.dumps({
                "accent": "purple",
                "theme": "sinister",
                "memory_enabled": True,
                "swarm_enabled": False,
                "effort": "medium",
                "fast_mode": "default",
            }, indent=2), encoding="utf-8")
            return f"[bold]wrote default config[/]  {cfg}"
        except Exception as e:
            return f"[red]config init failed: {e}[/]"
    if not cfg.exists():
        return f"[yellow]no config at {cfg}[/]\n  /config init to write defaults"
    return f"[bold]config[/]\n  path: {cfg}\n  size: {cfg.stat().st_size} bytes\n  /config edit | /config init"


def _cmd_changelog(args, pane, app) -> str:
    """jcode /changelog — last N commits via `git log --oneline -N`.

    Usage:
      /changelog            -> last 10 commits
      /changelog --count 25 -> last 25 commits

    Rendered through rich.Panel (cyan border) when rich is importable;
    falls back to plain text otherwise.
    """
    count = 10
    if args:
        toks = list(args)
        if "--count" in toks:
            idx = toks.index("--count")
            if idx + 1 < len(toks):
                try:
                    count = max(1, int(toks[idx + 1]))
                except ValueError:
                    return "[yellow]/changelog: --count needs an integer[/]"

    sr = _sanctum_root()
    try:
        r = subprocess.run(
            ["git", "-C", str(sr), "log", f"--oneline", f"-{count}"],
            capture_output=True, text=True, timeout=5,
        )
    except Exception as e:
        return f"[red]/changelog: git failed: {e}[/]"

    body = r.stdout.rstrip() or "(no commits)"

    # Try rich.Panel render
    try:
        from rich.console import Console
        from rich.panel import Panel
        import io
        buf = io.StringIO()
        Console(file=buf, force_terminal=True, width=120,
                color_system="truecolor").print(
            Panel(body,
                  title=f"Changelog · last {count}",
                  border_style="cyan",
                  padding=(0, 1)))
        return buf.getvalue().rstrip("\n")
    except Exception:
        return f"[bold]Changelog · last {count}[/]\n{body}"


# ----- session commands ---------------------------------------------------

def _cmd_start(args, pane, app) -> str:
    """jcode /start — bat-file project-picker parity. Lists projects sorted by
    last activity. Efficient, clean, fast.

    Mirrors `automations/start-sinister-session.ps1` UX inline. Reads
    `automations/session-templates/projects.json`; sorts by most-recent
    resume-point mtime; max 20 rows. In the Forge TUI this prints the list +
    instructions (interactive stdin picker only fires from the RKOJ.exe shell
    loop, via `_start_picker` in RKOJ-entry.py).
    """
    sr = _sanctum_root()
    proj_path = sr / "automations" / "session-templates" / "projects.json"
    if not proj_path.exists():
        return f"[red]/start: projects.json missing at {proj_path}[/]"
    try:
        data = json.loads(proj_path.read_text(encoding="utf-8"))
    except Exception as e:
        return f"[red]/start: projects.json parse error: {e}[/]"
    projects = [p for p in data.get("projects", []) if not p.get("_subsumed_by")]
    if not projects:
        return "[yellow]/start: no projects in registry[/]"

    rp_dir = sr / "_shared-memory" / "resume-points"

    def _last_mtime(p: dict) -> float:
        for slot in (p.get("display"), p.get("key"), (p.get("key") or "").title()):
            if not slot:
                continue
            d = rp_dir / slot
            if d.exists():
                pts = list(d.glob("*.json"))
                if pts:
                    return max(x.stat().st_mtime for x in pts)
        return 0.0

    projects = sorted(projects, key=_last_mtime, reverse=True)[:20]
    lines = ["[bold]EVE :: /start — pick a project (bat-file parity)[/]"]
    for i, p in enumerate(projects, start=1):
        mt = _last_mtime(p)
        ts = datetime.datetime.fromtimestamp(mt).strftime("%m-%d %H:%M") if mt else "never"
        lines.append(f"  [purple]{i:>2}[/]. [bold]{p.get('key', '?'):<22}[/] · {p.get('display', '')}  [dim]({ts})[/]")
    lines.append("\n[dim]Run /start at the RKOJ.exe `>` prompt for the interactive picker (project + mode).[/]")
    return "\n".join(lines)


def _cmd_resume(args, pane, app) -> str:
    """jcode /resume — multi-project resume-point browser.

    Operator directive 2026-05-21: show ALL projects with resume-points first,
    then drill down into one.

    Forms:
      /resume                  → list every project under
                                 _shared-memory/resume-points/ with count +
                                 most-recent timestamp (descending by recency).
      /resume <project>        → list resume-points within that project
                                 (most-recent first, up to 20 rows).
      /resume <project> <N>    → load resume-point N from that project
                                 (1-based; same _format_resume_point output).
      /resume <project> latest → load most-recent resume-point in project.

    Project arg matches the directory name under resume-points/ either exactly
    or case-insensitively or as a prefix (e.g. "panel" → "Sinister Panel").
    """
    sr = _sanctum_root()
    rp_dir = sr / "_shared-memory" / "resume-points"
    if not rp_dir.exists():
        return f"[yellow]/resume: no resume-points dir at {rp_dir}[/]"

    # Build {project_dir_name: [Path, ...]} for every subdir with at least one *.json.
    projects: dict[str, list[Path]] = {}
    for child in rp_dir.iterdir():
        if not child.is_dir():
            continue
        pts = list(child.glob("*.json"))
        if pts:
            projects[child.name] = sorted(pts, key=lambda p: p.stat().st_mtime, reverse=True)
    if not projects:
        return f"[yellow]/resume: no resume-points found under {rp_dir}[/]"

    # No-arg → list projects.
    if not args:
        rows = sorted(projects.items(),
                      key=lambda kv: kv[1][0].stat().st_mtime, reverse=True)
        lines = [
            "[bold]EVE :: /resume — projects with resume-points[/]  "
            "[dim](/resume <project>, /resume <project> <N>)[/]"
        ]
        for i, (name, pts) in enumerate(rows, start=1):
            mt = datetime.datetime.fromtimestamp(pts[0].stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            lines.append(f"  [purple]{i:>2}[/]. [bold]{name:<24}[/] · {len(pts):>3} point(s)  "
                         f"[dim]latest {mt}[/]")
        lines.append("\n[dim]Next: /resume <project> to drill in, or /resume <project> latest.[/]")
        return "\n".join(lines)

    # Resolve project arg → directory name.
    arg_proj = args[0]
    resolved: str | None = None
    if arg_proj in projects:
        resolved = arg_proj
    else:
        low = arg_proj.lower()
        # case-insensitive exact, then prefix
        for name in projects:
            if name.lower() == low:
                resolved = name
                break
        if resolved is None:
            for name in projects:
                if name.lower().startswith(low):
                    resolved = name
                    break
    if resolved is None:
        avail = ", ".join(sorted(projects.keys())) or "(none)"
        return f"[yellow]/resume: project '{arg_proj}' not found.[/]  [dim]available: {avail}[/]"

    candidates = projects[resolved]
    rest = args[1:]

    # /resume <project> <N>
    if rest and rest[0].isdigit():
        idx = int(rest[0])
        if not (1 <= idx <= len(candidates)):
            return f"[yellow]/resume: index out of range (1-{len(candidates)}) for {resolved}[/]"
        return _format_resume_point(candidates[idx - 1])

    # /resume <project> latest
    if rest and rest[0] == "latest":
        return _format_resume_point(candidates[0])

    # /resume <project>  → list points for that project
    lines = [
        f"[bold]Resume-points for {resolved}[/]  "
        f"[dim]({len(candidates)} total — /resume {resolved} <N> to load, "
        f"/resume {resolved} latest)[/]"
    ]
    for i, p in enumerate(candidates[:20], start=1):
        mt = datetime.datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        lines.append(f"  {i:>2}. {p.name}  [dim]{mt}[/]")
    return "\n".join(lines)


def _format_resume_point(path: Path) -> str:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return f"[red]failed to read {path}: {e}[/]"
    lines = [f"[bold]Resume-point:[/] {path.name}"]
    g = data.get("git", {})
    lines.append(f"  branch: {g.get('branch', '?')}  head: {g.get('head', '?')[:10]}  {g.get('head_msg', '')[:80]}")
    for p in data.get("progress_top3", [])[:3]:
        lines.append(f"  · {p[:100]}")
    lines.append(f"  inbox unread: {data.get('inbox_unread_count', 0)}")
    pwr = data.get("pre_warm_reads", [])
    if pwr:
        lines.append(f"  pre-warm reads ({len(pwr)}):")
        for r in pwr[:5]:
            lines.append(f"    · {Path(r).name}")
    return "\n".join(lines)


def _cmd_save(args, pane, app) -> str:
    """jcode /save [label] — write a resume-point bookmark for the current session.

    Writes to _shared-memory/resume-points/<proj>/<ts>-<label>.json with:
      - branch + HEAD + head_msg
      - current_query (from SINISTER_LAST_QUERY env or _state["last_user_input"])
      - pre_warm_reads (last 5 files read — best effort from pane / _state)
      - progress_summary (last 3 PROGRESS lines)
      - label (from arg or _state["session_name"])

    Never raises. Returns a 1-2 line confirmation.
    """
    sr = _sanctum_root()
    proj = (os.environ.get("SINISTER_PROJECT_DISPLAY")
            or os.environ.get("SINISTER_PROJECT")
            or state("session_project")
            or "Sinister Sanctum")
    label_raw = (" ".join(args) if args else
                 state("session_name") or os.environ.get("SINISTER_SESSION_NAME") or "")
    label = "".join(c if (c.isalnum() or c in "-_") else "-" for c in label_raw).strip("-")

    ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H%M%SZ")
    rp_dir = sr / "_shared-memory" / "resume-points" / proj
    try:
        rp_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return f"[note] /save needs writable resume-points dir: {e}"

    fname = f"{ts}-{label}.json" if label else f"{ts}.json"
    out_path = rp_dir / fname

    branch = _git_branch(sr)
    head = _git_head(sr)
    head_msg = ""
    try:
        r = subprocess.run(["git", "-C", str(sr), "log", "-1", "--pretty=%s"],
                           capture_output=True, text=True, timeout=3)
        head_msg = r.stdout.strip()
    except Exception:
        pass

    current_query = (os.environ.get("SINISTER_LAST_QUERY")
                     or state("last_user_input") or "")

    pwr: list[str] = []
    if pane is not None:
        for attr in ("recent_reads", "last_reads", "files_read"):
            v = getattr(pane, attr, None)
            if isinstance(v, (list, tuple)):
                pwr = [str(x) for x in list(v)[-5:]]
                break
    if not pwr:
        v = state("recent_reads")
        if isinstance(v, (list, tuple)):
            pwr = [str(x) for x in list(v)[-5:]]

    progress_lines: list[str] = []
    prog_path = sr / "_shared-memory" / "PROGRESS" / f"{proj}.md"
    if not prog_path.exists():
        prog_path = sr / "_shared-memory" / "PROGRESS" / "Sinister Sanctum.md"
    if prog_path.exists():
        try:
            for ln in prog_path.read_text(encoding="utf-8").splitlines():
                if ln.startswith("## "):
                    progress_lines.append(ln[3:].strip())
                    if len(progress_lines) >= 3:
                        break
        except Exception:
            pass

    payload = {
        "schema_version": "sinister.resume-point.v1",
        "ts_utc": ts,
        "project": proj,
        "agent_name": "EVE",
        "label": label_raw or None,
        "mode": "resume",
        "git": {
            "branch": branch,
            "head": head,
            "head_msg": head_msg,
        },
        "current_query": current_query,
        "pre_warm_reads": pwr,
        "progress_summary": progress_lines,
        "inbox_unread_count": 0,
    }

    try:
        out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    except Exception as e:
        return f"[note] /save needs writable resume-points dir: {e}"

    set_state("last_resume_point", str(out_path))
    return (f"  saved → {out_path.name}\n"
            f"  branch={branch}  head={head[:10]}  pre-warm={len(pwr)}  progress={len(progress_lines)}")


def _cmd_rename(args, pane, app) -> str:
    """jcode /rename <name> — set a session label, consumed by next /save.

    For v0.8.0 this is in-memory state. Mirrors into SINISTER_SESSION_NAME env
    for sibling tools that read it. Use /rename --clear to remove the label.
    """
    if not args:
        cur = state("session_name") or os.environ.get("SINISTER_SESSION_NAME") or "(unnamed)"
        return f"  session name: {cur}\n  usage: /rename <name> | /rename --clear"
    if args[0] == "--clear":
        set_state("session_name", None)
        os.environ.pop("SINISTER_SESSION_NAME", None)
        return "  session name cleared"
    name = " ".join(args)
    set_state("session_name", name)
    os.environ["SINISTER_SESSION_NAME"] = name
    return f"  session named: {name}  (applied on next /save)"


def _cmd_unsave(args, pane, app) -> str:
    """jcode /unsave — remove the most-recently-created resume-point bookmark.

    Resolution order:
      1. _state["last_resume_point"] — the path written by /save this session.
      2. Latest *.json in _shared-memory/resume-points/<proj>/ by mtime.

    Requires --force (or -f) to delete; otherwise prints the candidate and
    exits cleanly. This is jcode's "confirm before delete" without blocking.
    """
    sr = _sanctum_root()
    proj = (os.environ.get("SINISTER_PROJECT_DISPLAY")
            or os.environ.get("SINISTER_PROJECT")
            or state("session_project")
            or "Sinister Sanctum")

    candidate: Path | None = None
    last_rp = state("last_resume_point")
    if last_rp:
        p = Path(last_rp)
        if p.exists():
            candidate = p
    if candidate is None:
        rp_dir = sr / "_shared-memory" / "resume-points" / proj
        if rp_dir.exists():
            rps = sorted(rp_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            if rps:
                candidate = rps[0]

    if candidate is None:
        return f"[note] /unsave needs a saved bookmark: none found for project '{proj}'."

    force = bool(args and args[0].lower() in {"--force", "-f", "force", "yes", "y"})
    if not force:
        return (f"  would delete: {candidate}\n"
                f"  re-run as /unsave --force to confirm")

    try:
        candidate.unlink()
    except Exception as e:
        return f"[note] /unsave could not delete {candidate.name}: {e}"

    if state("last_resume_point") == str(candidate):
        set_state("last_resume_point", None)
    return f"  removed → {candidate.name}"


def _cmd_rewind(args, pane, app) -> str:
    """jcode /rewind [N] — show numbered history from the most recent session journal.

    /rewind          -> last 5 messages
    /rewind <N>      -> last N messages (1-200)

    v0.8.0 is read-only: actually rewinding session state is a future
    invention. This is the operator's window into recent journal content.
    """
    n = 5
    if args:
        try:
            n = max(1, min(int(args[0]), 200))
        except (ValueError, TypeError):
            return f"[note] /rewind needs an integer count: got `{args[0]}`"

    sr = _sanctum_root()
    sessions_dir = sr / "_shared-memory" / "forge-memory" / "anthropic-direct-sessions"
    if not sessions_dir.exists():
        return ("[note] /rewind needs anthropic-direct-sessions journal: "
                f"no such dir at {sessions_dir}")

    jrn = sorted(sessions_dir.glob("*.jsonl"),
                 key=lambda p: p.stat().st_mtime, reverse=True)
    if not jrn:
        return f"[note] /rewind needs a session journal: none found under {sessions_dir}"

    journal = jrn[0]
    try:
        raw_lines = [ln for ln in journal.read_text(encoding="utf-8").splitlines() if ln.strip()]
    except Exception as e:
        return f"[note] /rewind could not read journal: {e}"

    tail = raw_lines[-n:] if len(raw_lines) > n else raw_lines
    start_idx = max(1, len(raw_lines) - len(tail) + 1)

    out = [f"[bold]rewind — {journal.name}[/]  [dim]({len(raw_lines)} total, showing {len(tail)})[/]"]
    for i, raw in enumerate(tail, start=start_idx):
        try:
            rec = json.loads(raw)
            role = rec.get("role") or rec.get("type") or "?"
            content = rec.get("content") or rec.get("text") or ""
            if isinstance(content, list):
                content = " ".join(
                    str(c.get("text", "")) if isinstance(c, dict) else str(c)
                    for c in content
                )
            content = str(content).strip().replace("\n", " ")
            if len(content) > 220:
                content = content[:220] + "…"
            out.append(f"  {i:>3}. [{role}] {content}")
        except Exception:
            preview = raw[:220].replace("\n", " ")
            out.append(f"  {i:>3}. [raw] {preview}")
    return "\n".join(out)


def _cmd_compact(args, pane, app) -> str:
    """jcode /compact — summarize current session into a short bullet list and
    write it to _shared-memory/forge-memory/compacted/<ts>.md.

    v0.8.0 produces a placeholder summary based on the last N (default 30)
    messages from the most-recent session journal under
    _shared-memory/forge-memory/anthropic-direct-sessions/*.jsonl. If no
    journal is found we still write a minimal compaction record so the
    operator gets a confirmation path.
    """
    sr = _sanctum_root()
    sessions_dir = sr / "_shared-memory" / "forge-memory" / "anthropic-direct-sessions"
    compacted_dir = sr / "_shared-memory" / "forge-memory" / "compacted"

    # Optional arg: /compact <N>  -> bound the tail-count, max 200
    n = 30
    if args:
        try:
            n = max(5, min(int(args[0]), 200))
        except (ValueError, TypeError):
            pass

    # Locate the most-recent session journal.
    journal = None
    if sessions_dir.exists():
        jrn = sorted(sessions_dir.glob("*.jsonl"),
                     key=lambda p: p.stat().st_mtime, reverse=True)
        if jrn:
            journal = jrn[0]

    bullets: list[str] = []
    role_counts = {"user": 0, "assistant": 0, "tool": 0, "system": 0, "other": 0}
    total_chars = 0
    if journal is not None:
        try:
            lines = journal.read_text(encoding="utf-8").splitlines()
            tail = lines[-n:] if len(lines) > n else lines
            for raw in tail:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    rec = json.loads(raw)
                except Exception:
                    continue
                role = str(rec.get("role") or rec.get("type") or "other").lower()
                role_counts[role] = role_counts.get(role, 0) + 1
                content = rec.get("content") or rec.get("text") or ""
                if isinstance(content, list):
                    content = " ".join(
                        str(c.get("text", "")) if isinstance(c, dict) else str(c)
                        for c in content
                    )
                content = str(content).strip().replace("\n", " ")
                total_chars += len(content)
                if content and role in {"user", "assistant"} and len(bullets) < 12:
                    bullets.append(f"- [{role}] {content[:160]}")
        except Exception as e:
            bullets.append(f"- [warn] could not parse journal: {e}")

    ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H%M%SZ")
    try:
        compacted_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return f"[note] /compact needs writable forge-memory/compacted/: {e}"

    out_path = compacted_dir / f"{ts}.md"
    body_lines = [
        f"# Compacted session — {ts}",
        f"Author: RKOJ-ELENO :: {datetime.date.today().isoformat()}",
        "",
        f"Source journal: `{journal.name if journal else '(none — no anthropic-direct-sessions found)'}`",
        f"Tail-count: {n}  ·  total chars: {total_chars}",
        f"Role counts: " + ", ".join(f"{k}={v}" for k, v in role_counts.items() if v),
        "",
        "## Summary bullets (placeholder — v0.8.0 heuristic)",
        "",
    ]
    if bullets:
        body_lines.extend(bullets)
    else:
        body_lines.append("- (no user/assistant content available to summarize)")

    try:
        out_path.write_text("\n".join(body_lines) + "\n", encoding="utf-8")
    except Exception as e:
        return f"[note] /compact needs writable forge-memory/compacted/: {e}"

    # Mirror the compaction into in-memory state so subsequent /context can hint at it.
    set_state("last_compaction_path", str(out_path))
    return (f"  compacted → {out_path}\n"
            f"  source: {journal.name if journal else '(none)'}  ·  bullets: {len(bullets)}")


def _cmd_create(args, pane, app) -> str:
    """Sinister /create — scaffold a new project under projects/sinister-<slug>/.

    Operator directive 2026-05-21: `/create <project>` spins up a new project
    folder with CLAUDE.md + README.md skeletons (Author: RKOJ-ELENO :: today)
    and appends a row to projects/rkoj/MANIFEST.json components.

    Forms:
      /create                                  → usage + prompt for required args
      /create <name>                           → name only (default description + parent)
      /create <name> <description...>          → name + description
      /create <name> <description...> --parent=<dir>
                                               → override parent directory

    The <name> arg is slugified: lowercased, non-alnum → '-', and a 'sinister-'
    prefix is added if missing. Final folder = <parent>/sinister-<slug>/.

    Files created:
      - <parent>/sinister-<slug>/CLAUDE.md   (project agent bootstrap)
      - <parent>/sinister-<slug>/README.md   (public-ish one-pager)

    MANIFEST update:
      Appends one component row to projects/rkoj/MANIFEST.json with
      kind=project, enabled=true, role=<description>, created_at=ISO date.

    Idempotent: if the folder already exists, refuses (no clobber).
    """
    sr = _sanctum_root()
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")

    # --- arg parse ---------------------------------------------------------
    if not args:
        return (
            "[bold]/create — scaffold a new Sinister project[/]\n"
            "  usage: /create <name> [<description...>] [--parent=<dir>]\n"
            "  e.g.:  /create radar  Sinister radar — RF-scan visualizer\n"
            "  e.g.:  /create radar 'RF-scan visualizer' --parent=projects\n"
            "  notes: name auto-slugged + 'sinister-' prefix added if missing;\n"
            "         default parent = projects/ ;\n"
            "         creates CLAUDE.md + README.md + appends MANIFEST row."
        )

    # Pluck out --parent=<dir> (anywhere in args).
    parent_override: str | None = None
    rest_args: list[str] = []
    for a in args:
        if a.startswith("--parent="):
            parent_override = a.split("=", 1)[1].strip().strip('"').strip("'")
        else:
            rest_args.append(a)
    if not rest_args:
        return "[yellow]/create: name required.  /create <name> [<description...>][/]"

    raw_name = rest_args[0]
    description = (" ".join(rest_args[1:]).strip()
                   or f"Sinister {raw_name} project (scaffolded by EVE)")

    # --- slugify ---------------------------------------------------------
    base = raw_name.lower().strip()
    slug = "".join(c if (c.isalnum() or c == "-") else "-" for c in base)
    slug = "-".join(seg for seg in slug.split("-") if seg)  # collapse runs
    if not slug:
        return f"[yellow]/create: name '{raw_name}' slugifies to empty.[/]"
    if not slug.startswith("sinister-"):
        slug = f"sinister-{slug}"

    # --- resolve parent dir -------------------------------------------------
    parent: Path
    if parent_override:
        p = Path(parent_override)
        parent = p if p.is_absolute() else (sr / p)
    else:
        parent = sr / "projects"

    proj_dir = parent / slug
    if proj_dir.exists():
        return f"[yellow]/create: refusing to clobber existing dir {proj_dir}[/]"

    # --- write files -------------------------------------------------------
    try:
        proj_dir.mkdir(parents=True, exist_ok=False)
    except Exception as e:
        return f"[red]/create: mkdir failed: {e}  [dim]({proj_dir})[/]"

    display = slug.replace("sinister-", "").replace("-", " ").title()
    display = f"Sinister {display}" if not display.lower().startswith("sinister") else display

    claude_md = (
        f"# CLAUDE.md — {display}\n"
        f"\n"
        f"> Author: RKOJ-ELENO :: {today}\n"
        f"> Persona: EVE (Sinister Sanctum orchestration agent)\n"
        f"\n"
        f"## What this project is\n"
        f"\n"
        f"{description}\n"
        f"\n"
        f"## Agent identity (per-project)\n"
        f"\n"
        f"- Display name: `{display}`\n"
        f"- Slug: `{slug.replace('sinister-', '')}`\n"
        f"- Branch convention: `agent/{slug.replace('sinister-', '')}/<short-topic>`\n"
        f"- Heartbeat fallback: `_shared-memory/heartbeats/{slug.replace('sinister-', '')}.json`\n"
        f"- PROGRESS log: `_shared-memory/PROGRESS/{display}.md`\n"
        f"\n"
        f"## Cold-start\n"
        f"\n"
        f"1. Read parent `D:/Sinister Sanctum/CLAUDE.md` for fleet-wide rules.\n"
        f"2. Run `sinister-bus.heartbeat my_agent=\"{display}\"` (or write the JSON fallback).\n"
        f"3. Poll inbox: `sinister-bus.inbox_poll my_agent=\"{display}\"`.\n"
        f"4. Append milestones to `_shared-memory/PROGRESS/{display}.md`.\n"
        f"\n"
        f"## Source\n"
        f"\n"
        f"Scaffolded by `/create {raw_name}` on {today}.\n"
    )

    readme_md = (
        f"# {display}\n"
        f"\n"
        f"> Author: RKOJ-ELENO :: {today}\n"
        f"\n"
        f"{description}\n"
        f"\n"
        f"## Status\n"
        f"\n"
        f"Scaffolded {today} via `/create {raw_name}` from the Sinister Forge TUI.\n"
        f"\n"
        f"## See also\n"
        f"\n"
        f"- Sanctum root: `D:/Sinister Sanctum/`\n"
        f"- Project CLAUDE.md (agent bootstrap): `./CLAUDE.md`\n"
        f"- Fleet manifest: `projects/rkoj/MANIFEST.json`\n"
    )

    try:
        (proj_dir / "CLAUDE.md").write_text(claude_md, encoding="utf-8")
        (proj_dir / "README.md").write_text(readme_md, encoding="utf-8")
    except Exception as e:
        return f"[red]/create: file write failed: {e}[/]"

    # --- append MANIFEST row -----------------------------------------------
    manifest_path = sr / "projects" / "rkoj" / "MANIFEST.json"
    manifest_msg = "MANIFEST untouched (file missing)"
    if manifest_path.exists():
        try:
            mf = json.loads(manifest_path.read_text(encoding="utf-8"))
            comps = mf.setdefault("components", [])
            # Avoid double-add if a row with same name already exists.
            if not any((c.get("name") == slug) for c in comps if isinstance(c, dict)):
                rel_path = proj_dir.relative_to(sr).as_posix() if proj_dir.is_relative_to(sr) else str(proj_dir)
                comps.append({
                    "name": slug,
                    "kind": "project",
                    "path": rel_path,
                    "enabled": True,
                    "version": "0.1.0",
                    "role": description,
                    "created_at": today,
                    "created_by": "EVE /create",
                })
                mf["updated"] = today
                manifest_path.write_text(json.dumps(mf, indent=2) + "\n", encoding="utf-8")
                manifest_msg = f"MANIFEST row appended ({slug})"
            else:
                manifest_msg = f"MANIFEST already has '{slug}' — skipped"
        except Exception as e:
            manifest_msg = f"MANIFEST update failed: {e}"

    return (
        f"  [bold green]created[/] [purple]{slug}[/]\n"
        f"  · dir:      {proj_dir}\n"
        f"  · CLAUDE.md ✓  README.md ✓  (Author: RKOJ-ELENO :: {today})\n"
        f"  · {manifest_msg}\n"
        f"  next: cd into {proj_dir} or spawn an agent for it from the Forge sidebar."
    )


def _cmd_transcript(args, pane, app) -> str:
    sr = _sanctum_root()
    hist = sr / "_shared-memory" / "sinister-term-history" / "history.jsonl"
    return f"  transcript: {hist}  ({'exists' if hist.exists() else 'missing'})"


def _cmd_todos(args, pane, app) -> str:
    sr = _sanctum_root()
    queue = sr / "_shared-memory" / "OPERATOR-ACTION-QUEUE.md"
    if not queue.exists():
        return "[yellow]no OPERATOR-ACTION-QUEUE.md found[/]"
    try:
        txt = queue.read_text(encoding="utf-8")
        snippet = "\n".join(txt.splitlines()[:30])
        return f"[bold]todos (operator-action-queue, top 30 lines)[/]\n{snippet}"
    except Exception as e:
        return f"[red]/todos: {e}[/]"


# ----- memory commands ----------------------------------------------------

def _cmd_memory(args, pane, app) -> str:
    if not args:
        return f"  memory is {'[green]ON[/]' if state('memory_enabled') else '[red]OFF[/]'}\n  /memory on|off|search <q>|write <ns> <data>|list|stats|recall <q>"
    sub = args[0].lower()
    if sub in {"on", "enable"}:
        set_state("memory_enabled", True)
        return "  memory: ON"
    if sub in {"off", "disable"}:
        set_state("memory_enabled", False)
        return "  memory: OFF"
    # delegate to forge-memory-bridge
    try:
        import forge_memory_bridge  # type: ignore
    except Exception as e:
        return f"[red]forge-memory-bridge unavailable: {e}[/]"
    rest = args[1:]
    if sub == "search" or sub == "recall":
        if not rest:
            return "[yellow]usage: /memory search <query>[/]"
        q = " ".join(rest)
        try:
            results = forge_memory_bridge.recall(q, limit=8)
            if not results:
                return f"  no matches for {q!r}"
            lines = [f"[bold]memory.recall({q!r})[/]"]
            for r in (results if isinstance(results, list) else [results]):
                lines.append(f"  · {str(r)[:200]}")
            return "\n".join(lines)
        except Exception as e:
            return f"[red]recall failed: {e}[/]"
    if sub == "write":
        if len(rest) < 2:
            return "[yellow]usage: /memory write <namespace> <text>[/]"
        ns = rest[0]
        body = " ".join(rest[1:])
        try:
            forge_memory_bridge.write(ns, body)
            return f"  wrote to memory[{ns}]"
        except Exception as e:
            return f"[red]write failed: {e}[/]"
    if sub == "list":
        try:
            rows = forge_memory_bridge.list()
            return f"  memory namespaces: {len(rows) if hasattr(rows, '__len__') else '?'}"
        except Exception as e:
            return f"[red]list failed: {e}[/]"
    return f"[yellow]unknown /memory subcommand `{sub}`[/]"


def _cmd_goals(args, pane, app) -> str:
    """jcode /goals — overview of fleet-shared goals from WORK-TOWARD.md.

    Prints the first 5 lines (rolling goals are kept at the top of the file).
    With `resume <slug>` arg, sets `_state["active_goal"]` so other loops can
    pick it up.
    """
    sr = _sanctum_root()
    wt = sr / "_shared-memory" / "WORK-TOWARD.md"
    if not wt.exists():
        return "[yellow]no WORK-TOWARD.md[/]"
    try:
        raw = wt.read_text(encoding="utf-8")
    except Exception as e:
        return f"[red]/goals: cannot read {wt}: {e}[/]"

    if args and args[0].lower() == "resume" and len(args) > 1:
        slug = " ".join(args[1:]).strip()
        set_state("active_goal", slug)
        return f"  active goal set: [bold]{slug}[/]  [dim]({wt})[/]"

    lines = raw.splitlines()
    snippet = "\n".join(lines[:5])
    return (f"[bold]Goals (WORK-TOWARD.md, top 5)[/]  [dim]{wt}[/]\n"
            f"{snippet}")


# ----- session/workspace management commands (jcode parity) -------------

def _cmd_workspace(args, pane, app) -> str:
    """jcode /workspace — niri-style workspace toggle/list/add.

    /workspace              -> status
    /workspace status       -> status
    /workspace on|off       -> toggle workspaces; persists workspace_enabled
                               to forge-prefs.json and current workspace id
    /workspace add          -> create a new workspace pane (Forge TUI only)
    """
    sub = (args[0].lower() if args else "status")
    in_tui = app is not None

    if sub in {"status", ""}:
        cur = bool(state("workspace_enabled"))
        wsid = state("current_workspace_id", 0)
        ctx = "Forge TUI" if in_tui else "RKOJ shell"
        return (f"  workspace: {'[green]ON[/]' if cur else '[red]OFF[/]'}  "
                f"id={wsid}  [dim]({ctx})[/]")

    if sub in {"on", "off"}:
        new_val = (sub == "on")
        set_state("workspace_enabled", new_val)
        try:
            prefs = _load_forge_prefs()
            prefs["workspace_enabled"] = new_val
            prefs.setdefault("current_workspace_id",
                             int(state("current_workspace_id", 0)))
            path = _save_forge_prefs(prefs)
        except Exception as e:
            return f"[red]/workspace {sub}: persist failed: {e}[/]"
        if in_tui:
            try:
                post = getattr(app, "post_message", None)
                if callable(post):
                    try:
                        from textual.message import Message  # type: ignore
                        class WorkspaceToggle(Message):  # type: ignore
                            def __init__(self, enabled: bool) -> None:
                                super().__init__()
                                self.enabled = enabled
                        post(WorkspaceToggle(new_val))
                    except Exception:
                        pass
            except Exception:
                pass
        return f"  workspace: {sub.upper()}  [dim]({path})[/]"

    if sub == "add":
        if not in_tui:
            return ("[note] /workspace add: needs Forge TUI — "
                    "shell can only show status")
        cur_id = int(state("current_workspace_id", 0))
        new_id = cur_id + 1
        set_state("current_workspace_id", new_id)
        try:
            prefs = _load_forge_prefs()
            prefs["current_workspace_id"] = new_id
            _save_forge_prefs(prefs)
        except Exception:
            pass
        try:
            post = getattr(app, "post_message", None)
            if callable(post):
                try:
                    from textual.message import Message  # type: ignore
                    class WorkspaceToggle(Message):  # type: ignore
                        def __init__(self, action: str, ws_id: int) -> None:
                            super().__init__()
                            self.action = action
                            self.ws_id = ws_id
                    post(WorkspaceToggle("add", new_id))
                except Exception:
                    pass
        except Exception:
            pass
        return f"  workspace add → id={new_id}"

    return f"[yellow]/workspace: unknown sub `{sub}` — status|on|off|add[/]"


def _cmd_splitview(args, pane, app) -> str:
    """jcode /splitview — mirror current chat in the side panel.

    /splitview            -> status
    /splitview status     -> status
    /splitview on|off     -> toggle splitview; spawn/close mirror pane (TUI only)
    """
    sub = (args[0].lower() if args else "status")
    in_tui = app is not None

    if sub in {"status", ""}:
        cur = bool(state("splitview_enabled"))
        if not in_tui:
            return ("[note] /splitview: shell mode — splitview is a Forge TUI "
                    "feature; only status is queryable here\n"
                    f"  splitview = {'on' if cur else 'off'}")
        return f"  splitview: {'[green]ON[/]' if cur else '[red]OFF[/]'}"

    if sub in {"on", "off"}:
        new_val = (sub == "on")
        set_state("splitview_enabled", new_val)
        if not in_tui:
            return ("[note] /splitview: not applicable in shell mode — "
                    "Forge TUI required to spawn a mirror pane.\n"
                    f"  splitview state recorded as {sub} for next TUI launch")
        try:
            post = getattr(app, "post_message", None)
            if callable(post):
                try:
                    from textual.message import Message  # type: ignore
                    class SplitviewToggle(Message):  # type: ignore
                        def __init__(self, enabled: bool) -> None:
                            super().__init__()
                            self.enabled = enabled
                    post(SplitviewToggle(new_val))
                except Exception:
                    pass
        except Exception:
            pass
        return f"  splitview: {sub.upper()}"

    return f"[yellow]/splitview: unknown sub `{sub}` — on|off|status[/]"


def _cmd_split(args, pane, app) -> str:
    """jcode /split — clone the current session into a new window.

    Spawns a new RKOJ.exe instance with `--shell` (cloning the Forge TUI inside
    the same process is heavy). Passes env vars so the clone inherits project,
    model, effort, and session-name context.
    """
    sr = _sanctum_root()
    candidates = [
        sr / "automations" / "build" / "forge-exe" / "dist" / "RKOJ.exe",
        Path(sys.executable) if sys.executable else None,
    ]
    binary = next((c for c in candidates if c and c.exists()), None)
    if binary is None:
        return ("[red]/split: no RKOJ.exe found — run /rebuild first[/]\n"
                f"  [dim]checked {candidates[0]}[/]")

    env = os.environ.copy()
    for k in ("SINISTER_PROJECT", "SINISTER_PROJECT_DISPLAY",
              "SINISTER_SESSION_NAME", "SANCTUM_ROOT"):
        if k in os.environ:
            env[k] = os.environ[k]
    env["SINISTER_PARENT_PID"] = str(os.getpid())
    cur_model = state("default_model")
    if cur_model:
        env["SINISTER_DEFAULT_MODEL"] = str(cur_model)
    cur_effort = state("effort")
    if cur_effort:
        env["SINISTER_EFFORT"] = str(cur_effort)

    try:
        creationflags = 0
        if platform.system() == "Windows":
            # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
            creationflags = 0x00000008 | 0x00000200
        subprocess.Popen(
            [str(binary), "--shell"],
            env=env,
            cwd=str(sr),
            creationflags=creationflags,
            close_fds=True,
        )
    except Exception as e:
        return f"[red]/split: failed to spawn {binary}: {e}[/]"
    return f"  split → spawned {binary.name} --shell  [dim]({binary})[/]"


def _cmd_transfer(args, pane, app) -> str:
    """jcode /transfer — open a fresh session with only compacted context + todos.

    Reads the latest compacted summary from
    `_shared-memory/forge-memory/compacted/*.md`, copies todos found in the
    latest journal under `_shared-memory/forge-memory/anthropic-direct-sessions/`,
    writes a transfer envelope, and spawns a new shell session.
    """
    sr = _sanctum_root()
    compacted_dir = sr / "_shared-memory" / "forge-memory" / "compacted"
    sessions_dir = sr / "_shared-memory" / "forge-memory" / "anthropic-direct-sessions"

    summary_path = None
    summary_text = ""
    if compacted_dir.exists():
        cands = sorted(compacted_dir.glob("*.md"),
                       key=lambda p: p.stat().st_mtime, reverse=True)
        if cands:
            summary_path = cands[0]
            try:
                summary_text = summary_path.read_text(encoding="utf-8")
            except Exception:
                summary_text = ""

    todos: list[str] = []
    journal = None
    if sessions_dir.exists():
        jrn = sorted(sessions_dir.glob("*.jsonl"),
                     key=lambda p: p.stat().st_mtime, reverse=True)
        if jrn:
            journal = jrn[0]
            try:
                for line in journal.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    try:
                        rec = json.loads(line)
                    except Exception:
                        continue
                    blob = json.dumps(rec)
                    if "TodoWrite" not in blob:
                        continue
                    content = rec.get("content")
                    if isinstance(content, list):
                        for c in content:
                            if isinstance(c, dict) and c.get("name") == "TodoWrite":
                                inp = c.get("input") or {}
                                for t in (inp.get("todos") or []):
                                    if isinstance(t, dict) and t.get("content"):
                                        todos.append(str(t["content"]))
                    elif isinstance(content, dict) and content.get("name") == "TodoWrite":
                        inp = content.get("input") or {}
                        for t in (inp.get("todos") or []):
                            if isinstance(t, dict) and t.get("content"):
                                todos.append(str(t["content"]))
            except Exception:
                pass

    seen: set[str] = set()
    todos = [t for t in todos if not (t in seen or seen.add(t))][:20]

    transfer_dir = sr / "_shared-memory" / "forge-memory" / "transfers"
    try:
        transfer_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return f"[red]/transfer: cannot create {transfer_dir}: {e}[/]"

    ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H%M%SZ")
    env_path = transfer_dir / f"transfer-{ts}.md"
    body = [
        f"# Transfer envelope — {ts}",
        f"Author: RKOJ-ELENO :: {datetime.date.today().isoformat()}",
        "",
        f"Source compaction: `{summary_path.name if summary_path else '(none)'}`",
        f"Source journal:    `{journal.name if journal else '(none)'}`",
        f"Todos carried:     {len(todos)}",
        "",
        "## Compacted context",
        "",
        summary_text.strip() or "(no compacted summary available)",
        "",
        "## Todos",
        "",
    ]
    if todos:
        body.extend(f"- [ ] {t}" for t in todos)
    else:
        body.append("(no todos found in latest journal)")
    try:
        env_path.write_text("\n".join(body) + "\n", encoding="utf-8")
    except Exception as e:
        return f"[red]/transfer: write failed: {e}[/]"

    set_state("last_transfer_path", str(env_path))

    binary = sr / "automations" / "build" / "forge-exe" / "dist" / "RKOJ.exe"
    if binary.exists():
        env = os.environ.copy()
        env["SINISTER_TRANSFER_ENVELOPE"] = str(env_path)
        env["SINISTER_PARENT_PID"] = str(os.getpid())
        try:
            creationflags = 0
            if platform.system() == "Windows":
                creationflags = 0x00000008 | 0x00000200
            subprocess.Popen(
                [str(binary), "--shell"],
                env=env,
                cwd=str(sr),
                creationflags=creationflags,
                close_fds=True,
            )
            spawn_note = f"spawned {binary.name} --shell"
        except Exception as e:
            spawn_note = f"spawn failed: {e}"
    else:
        spawn_note = "no RKOJ.exe — envelope written; launch a new session manually"

    return (f"  transfer → {env_path.name}\n"
            f"  todos:    {len(todos)}  ·  compaction: "
            f"{summary_path.name if summary_path else '(none)'}\n"
            f"  {spawn_note}  [dim]({env_path})[/]")


def _catchup_last_n_msgs(journal: Path, n: int) -> list[str]:
    """Return last N user/assistant messages from a JSONL journal."""
    msgs: list[str] = []
    try:
        for line in reversed(journal.read_text(encoding="utf-8").splitlines()):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            role = str(rec.get("role") or rec.get("type") or "").lower()
            if role not in {"user", "assistant"}:
                continue
            c = rec.get("content") or rec.get("text") or ""
            if isinstance(c, list):
                c = " ".join(
                    str(x.get("text", "")) if isinstance(x, dict) else str(x)
                    for x in c
                )
            c = str(c).strip().replace("\n", " ")
            if c:
                msgs.append(f"[{role}] {c}")
                if len(msgs) >= n:
                    break
    except Exception:
        pass
    return list(reversed(msgs))


def _catchup_render(journal: Path) -> str:
    """Render a Catch Up brief for a single journal."""
    if not journal.exists():
        return f"[yellow]/catchup: journal missing: {journal}[/]"
    msgs = _catchup_last_n_msgs(journal, 6)
    mt = datetime.datetime.fromtimestamp(journal.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    lines = [f"[bold]Catch Up:[/] {journal.name}  [dim]({mt})[/]"]
    for m in msgs:
        lines.append(f"  · {m[:160]}")
    return "\n".join(lines)


def _cmd_catchup(args, pane, app) -> str:
    """jcode /catchup — jump into finished sessions and open Catch Up brief.

    /catchup           -> list 5 most-recent finished sessions
    /catchup list      -> same as above
    /catchup next      -> advance to next brief in the queue
    """
    sr = _sanctum_root()
    sessions_dir = sr / "_shared-memory" / "forge-memory" / "anthropic-direct-sessions"

    sub = (args[0].lower() if args else "list")

    if sub == "next":
        queue = _state.get("_catchup_queue") or []
        if not queue:
            if not sessions_dir.exists():
                return "[yellow]/catchup next: no sessions dir[/]"
            queue = [str(p) for p in sorted(
                sessions_dir.glob("*.jsonl"),
                key=lambda x: x.stat().st_mtime, reverse=True)[:5]]
            _state["_catchup_queue"] = queue
        if not queue:
            return "[yellow]/catchup next: queue empty[/]"
        nxt = queue.pop(0)
        _state["_catchup_queue"] = queue
        # Remember source for /back (the listing/prior brief we came from).
        _state.setdefault("catchup_source", _state.get("catchup_current"))
        _state["catchup_current"] = nxt
        return _catchup_render(Path(nxt))

    # list mode (default)
    if not sessions_dir.exists():
        return "[yellow]/catchup: no anthropic-direct-sessions found[/]"
    cands = sorted(sessions_dir.glob("*.jsonl"),
                   key=lambda p: p.stat().st_mtime, reverse=True)[:5]
    if not cands:
        return "[yellow]/catchup: no finished sessions[/]"
    lines = ["[bold]Catch Up — 5 most-recent finished sessions[/]"]
    for i, p in enumerate(cands, start=1):
        mt = datetime.datetime.fromtimestamp(p.stat().st_mtime).strftime("%m-%d %H:%M")
        last2 = _catchup_last_n_msgs(p, 2)
        lines.append(f"  [purple]{i:>2}[/]. {p.name}  [dim]({mt})[/]")
        for msg in last2:
            lines.append(f"      [dim]· {msg[:120]}[/]")
    lines.append("\n[dim]/catchup next to advance · /back to return[/]")
    _state["_catchup_queue"] = [str(p) for p in cands]
    return "\n".join(lines)


def _cmd_back(args, pane, app) -> str:
    """jcode /back — return to the previous Catch Up source session.

    Reads `_state['catchup_source']`. If none, prints a hint.
    """
    src = _state.get("catchup_source")
    if not src:
        cur = _state.get("catchup_current")
        if cur:
            _state["catchup_current"] = None
            return (f"  back: cleared current brief ({Path(cur).name})  "
                    f"[dim](no prior source — back-stack empty)[/]")
        return "[note] /back: no previous Catch Up source session"
    _state["catchup_current"] = src
    _state["catchup_source"] = None
    return f"  back → {Path(str(src)).name}"


def _cmd_poke(args, pane, app) -> str:
    """jcode /poke — nudge the model to resume work on incomplete todos.

    /poke           -> status
    /poke status    -> status
    /poke on|off    -> toggle the poke loop
    """
    sub = (args[0].lower() if args else "status")
    cur = bool(state("poke_enabled"))

    if sub in {"status", ""}:
        return f"  poke: {'[green]ON[/]' if cur else '[red]OFF[/]'}"

    if sub in {"on", "off"}:
        new_val = sub == "on"
        set_state("poke_enabled", new_val)
        if app is None:
            return (f"[note] /poke: shell-mode stub — state recorded "
                    f"({sub.upper()}). Forge TUI required to fire follow-up turns.")
        try:
            prefs = _load_forge_prefs()
            prefs["poke_enabled"] = new_val
            _save_forge_prefs(prefs)
        except Exception:
            pass
        if new_val and pane is not None:
            poke_msg = "check for incomplete todos and continue"
            try:
                inject = (getattr(pane, "submit_user_text", None)
                          or getattr(pane, "_submit", None)
                          or getattr(pane, "write_stdin", None))
                if callable(inject):
                    inject(poke_msg)
            except Exception:
                pass
        return f"  poke: {sub.upper()}"

    return f"[yellow]/poke: unknown sub `{sub}` — on|off|status[/]"


def _cmd_improve(args, pane, app) -> str:
    """jcode /improve — autonomous repo-improvement loop.

    v1.0.0: not yet implemented; tracked in jcode-parity-roadmap.md.
    /improve resume   -> resumes from `_state['last_improve_loop']` if any.
    """
    if args and args[0].lower() == "resume":
        prev = _state.get("last_improve_loop")
        if not prev:
            return ("[note] /improve resume: no previous loop checkpoint "
                    "(_state['last_improve_loop'] is empty)")
        return (f"[note] /improve resume: would resume from {prev}\n"
                f"  [dim]not yet implemented; tracked in jcode-parity-roadmap.md[/]")
    return ("[improve] not yet implemented; tracked in jcode-parity-roadmap.md\n"
            "  [dim]use /improve resume to pick up a paused loop once available[/]")


def _cmd_refactor(args, pane, app) -> str:
    """jcode /refactor — safe refactor + review loop.

    v1.0.0: not yet implemented; tracked in jcode-parity-roadmap.md.
    /refactor resume  -> resumes from `_state['last_refactor_loop']` if any.
    """
    if args and args[0].lower() == "resume":
        prev = _state.get("last_refactor_loop")
        if not prev:
            return ("[note] /refactor resume: no previous loop checkpoint "
                    "(_state['last_refactor_loop'] is empty)")
        return (f"[note] /refactor resume: would resume from {prev}\n"
                f"  [dim]not yet implemented; tracked in jcode-parity-roadmap.md[/]")
    return ("[refactor] not yet implemented; tracked in jcode-parity-roadmap.md\n"
            "  [dim]use /refactor resume to pick up a paused loop once available[/]")


# ----- swarm commands -----------------------------------------------------

def _cmd_swarm(args, pane, app) -> str:
    if not args:
        return f"  swarm is {'[green]ON[/]' if state('swarm_enabled') else '[red]OFF[/]'}\n  /swarm on|off|spawn <N>|list|dm <slug> <msg>|broadcast <msg>"
    sub = args[0].lower()
    rest = args[1:]
    if sub == "on":
        set_state("swarm_enabled", True); return "  swarm: ON"
    if sub == "off":
        set_state("swarm_enabled", False); return "  swarm: OFF"
    if sub == "spawn":
        n = 3
        if rest:
            try:
                n = max(1, min(int(rest[0]), 8))
            except ValueError:
                return f"[yellow]/swarm spawn needs int[/]"
        if pane and hasattr(pane, "_call_app_builtin_swarm"):
            pane._call_app_builtin_swarm(n)
            return None
        return f"[yellow]swarm spawn unavailable from this context[/]"
    if sub == "list":
        try:
            from sinister_swarm import list_active  # type: ignore
            rows = list_active()
            if not rows:
                return "  no live agents"
            lines = ["[bold]live agents[/]"]
            for r in rows:
                lines.append(f"  · {r.get('slug', '?'):<22} {r.get('stale_minutes', '?')}m ago")
            return "\n".join(lines)
        except Exception as e:
            return f"[red]swarm list: {e}[/]"
    if sub == "dm":
        if len(rest) < 2:
            return "[yellow]usage: /swarm dm <slug> <msg...>[/]"
        if pane and hasattr(pane, "_call_app_builtin_dm"):
            pane._call_app_builtin_dm(rest[0], " ".join(rest[1:]))
            return None
        return "[yellow]/swarm dm unavailable[/]"
    if sub == "broadcast":
        if not rest:
            return "[yellow]usage: /swarm broadcast <msg...>[/]"
        if pane and hasattr(pane, "_call_app_builtin_broadcast"):
            pane._call_app_builtin_broadcast(" ".join(rest))
            return None
        return "[yellow]/swarm broadcast unavailable[/]"
    return f"[yellow]unknown /swarm subcommand `{sub}`[/]"


def _cmd_dm(args, pane, app) -> str:
    if len(args) < 2:
        return "[yellow]usage: /dm <slug> <msg...>[/]"
    if pane and hasattr(pane, "_call_app_builtin_dm"):
        pane._call_app_builtin_dm(args[0], " ".join(args[1:]))
        return None
    return "[yellow]dm unavailable from this context[/]"


def _cmd_broadcast(args, pane, app) -> str:
    if not args:
        return "[yellow]usage: /broadcast <msg...>[/]"
    if pane and hasattr(pane, "_call_app_builtin_broadcast"):
        pane._call_app_builtin_broadcast(" ".join(args))
        return None
    return "[yellow]broadcast unavailable[/]"


def _cmd_agents(args, pane, app) -> str:
    try:
        from sinister_swarm import list_active  # type: ignore
        rows = list_active()
    except Exception:
        rows = _heartbeat_scan()
    if not rows:
        return "  no live agents"
    lines = ["[bold]Agents[/]"]
    for r in rows:
        slug = r.get("slug", r.get("agent", "?"))
        age = r.get("stale_minutes", r.get("age_min", "?"))
        live = "●" if (isinstance(age, int) and age < 30) else "○"
        lines.append(f"  {live} {slug:<22} {age}m")
    return "\n".join(lines)


def _heartbeat_scan() -> list[dict]:
    sr = _sanctum_root()
    hb_dir = sr / "_shared-memory" / "heartbeats"
    if not hb_dir.exists():
        return []
    now = time.time()
    rows = []
    for p in hb_dir.glob("*.json"):
        try:
            age = int((now - p.stat().st_mtime) // 60)
            rows.append({"slug": p.stem, "age_min": age})
        except OSError:
            pass
    rows.sort(key=lambda r: r["age_min"])
    return rows


# ----- auth + provider commands ------------------------------------------

def _sinister_config_path(filename: str) -> Path:
    """Returns ~/.config/sinister/<filename> or %APPDATA%/sinister/<filename>
    on Windows. Mirrors `_forge_prefs_path()` layout for jcode parity."""
    if platform.system() == "Windows":
        appdata = os.environ.get("APPDATA")
        base = Path(appdata) if appdata else Path.home() / "AppData" / "Roaming"
        return base / "sinister" / filename
    return Path.home() / ".config" / "sinister" / filename


def _load_login_state() -> dict:
    """Read ~/.config/sinister/login-state.json. Returns {} on any error."""
    p = _sinister_config_path("login-state.json")
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def _mask_key(value: str | None, tail: int = 6, mask_chars: int = 6) -> str:
    """Mask an API key — show last `tail` chars only with a fixed-width
    `mask_chars`-char prefix of '*' (default '******XXXXXX'). Returns
    '<unset>' if empty. Capping mask width keeps the /account table aligned.
    """
    if not value:
        return "<unset>"
    if len(value) <= tail:
        return "*" * len(value)
    return ("*" * mask_chars) + value[-tail:]


def _cmd_auth(args, pane, app) -> str:
    """jcode /auth [status] — show 11-provider auth status + default provider.

    Delegates to sinister_login.api.status_all() for the per-provider rows;
    adds a "current default provider" line read from
    ~/.config/sinister/login-state.json (key: 'default_provider'). Falls
    back to in-memory _state['default_provider'] when the file is absent
    or the key is missing.
    """
    try:
        from sinister_login import status_all  # type: ignore
    except Exception as e:
        return f"[red]sinister-login unavailable: {e}[/]"
    # Subcommand parsing — only 'status' is recognized; everything else is
    # treated as the default listing (jcode accepts a bare /auth too).
    sub = args[0].lower() if args else "status"
    if sub not in {"status", ""}:
        return (f"[yellow]/auth: unknown subcommand `{sub}` "
                f"(use /auth or /auth status)[/]")
    try:
        rows = status_all()
    except Exception as e:
        return f"[red]sinister-login.status_all crashed: {e}[/]"

    login_state = _load_login_state()
    default_prov = (login_state.get("default_provider")
                    or state("default_provider")
                    or "(auto-resolved)")

    configured = sum(1 for r in rows if r.get("configured"))
    total = len(rows)

    lines = [f"[bold]auth status[/]  ({configured}/{total} configured)"]
    lines.append(f"  [dim]default provider:[/] {default_prov}")
    lines.append("")
    for r in rows:
        mark = "[green]●[/]" if r.get("configured") else "[dim]○[/]"
        slug = r.get("slug", "?")
        auth = r.get("auth", "?")
        env_name = r.get("key_env_found") or "(local)"
        lines.append(f"  {mark} {slug:<22} {auth:<8} {env_name}")
    return "\n".join(lines)


def _cmd_login(args, pane, app) -> str:
    try:
        from sinister_login.__main__ import main as login_main
    except Exception as e:
        return f"[red]sinister-login unavailable: {e}[/]"
    if not args:
        return _cmd_auth([], pane, app)
    return _capture_cli(login_main, args)


def _cmd_usage(args, pane, app) -> str:
    try:
        from sinister_usage.__main__ import main as usage_main
    except Exception as e:
        return f"[red]sinister-usage unavailable: {e}[/]"
    return _capture_cli(usage_main, args or ["check-all"])


def _cmd_backup(args, pane, app) -> str:
    """/backup — Sinister Sanctum daily backups (sanctum-backup CLI).

    Subcommands (delegated to sanctum_backup.cli):
        /backup                -> list known backups
        /backup now            -> run a backup right now
        /backup list           -> list known backups
        /backup verify <date>  -> re-check a snapshot's manifest
        /backup prune          -> delete backups older than 7 days
        /backup install-task   -> register the daily Windows scheduled task (operator-gated)
    """
    try:
        from sanctum_backup.__main__ import main as backup_main
    except Exception as e:
        return (f"[red]sanctum-backup unavailable: {e}[/]\n"
                f"  install: pip install -e \"D:/Sinister Sanctum/tools/sanctum-backup\"")
    return _capture_cli(backup_main, args or ["list"])


def _cmd_model(args, pane, app) -> str:
    """jcode /model — dispatch to sinister-model CLI.

    Subcommands (delegated to sinister_model.cli):
        /model               -> list models for currently-logged-in provider
        /model list [prov]   -> list models for a provider
        /model current       -> show active model
        /model set <id>      -> set active model
        /model info <id>     -> show model details
        /model providers     -> list providers + counts
        /model clear         -> clear active selection
    """
    try:
        from sinister_model.cli import main as model_main
    except Exception as e:
        return f"[red]sinister-model unavailable: {e}[/]\n  install: pip install -e \"D:/Sinister Sanctum/tools/sinister-model\""
    # Default action: list models for currently logged-in provider.
    if not args:
        body = _capture_cli(model_main, ["list"])
    else:
        body = _capture_cli(model_main, args)
    # Mirror the selection into Forge session-state for downstream awareness.
    if args and args[0] == "set" and len(args) >= 2:
        set_state("default_model", args[1])
        try:
            from sinister_model.registry import find_provider_for_model  # type: ignore
            prov = find_provider_for_model(args[1])
            if prov:
                set_state("default_provider", prov)
        except Exception:
            pass
    return body


def _cmd_jcode(args, pane, app) -> str:
    """/jcode — sidecar launch of the prebuilt jcode-windows-x86_64.exe.

    Delegates to `sinister_jcode_shim.cli run` so jcode boots with our
    Sinister env (config-dir, skills-dir, sessions-dir, wallet keys,
    selected model) injected. Operator-gated source fork lives at
    `_shared-memory/plans/jcode-fork-2026-05-21/plan.md`.

    Subcommands:
        /jcode                -> exec jcode with injected env
        /jcode --print-bin    -> show resolved binary path
        /jcode --dry-run      -> show what would be exec'd + env
        /jcode doctor         -> diagnose shim readiness
        /jcode -- <args...>   -> forward args to jcode
    """
    try:
        from sinister_jcode_shim.__main__ import main as shim_main
    except Exception as e:
        return (f"[red]sinister-jcode-shim unavailable: {e}[/]\n"
                f"  install: pip install -e \"D:/Sinister Sanctum/tools/sinister-jcode-shim\"")
    sub = args[0].lower() if args else None
    if sub == "doctor":
        return _capture_cli(shim_main, ["doctor"])
    return _capture_cli(shim_main, ["run", *args])


def _cmd_provider(args, pane, app) -> str:
    if not args:
        return _cmd_auth([], pane, app)
    sub = args[0].lower()
    if sub == "list":
        return _cmd_auth([], pane, app)
    if sub == "current":
        return f"  default provider: {state('default_provider') or 'auto-resolved'}"
    return f"[yellow]unknown /provider subcommand `{sub}`[/]"


def _cmd_account(args, pane, app) -> str:
    """jcode /account — combined Claude/OpenAI account picker.

    Reads the 11-provider wallet from sinister-login and prints a 2-column
    table: provider | account (last 6 chars of key shown, rest masked).
    For local-auth providers (lmstudio, ollama) the endpoint URL is shown
    instead of a key. For unconfigured providers the cell reads '<unset>'.
    """
    try:
        from sinister_login import PROVIDERS, status_all  # type: ignore
    except Exception as e:
        return f"[red]sinister-login unavailable: {e}[/]"
    try:
        rows = status_all()
    except Exception as e:
        return f"[red]sinister-login.status_all crashed: {e}[/]"

    login_state = _load_login_state()
    default_prov = (login_state.get("default_provider")
                    or state("default_provider"))

    # Build provider→key lookup via the same env-vars sinister-login uses.
    prov_by_slug = {p.slug: p for p in PROVIDERS}

    # Column widths.
    name_w = max((len(r.get("slug", "")) for r in rows), default=14) + 2

    lines = ["[bold]account wallet[/]  (last 6 chars shown; rest masked)"]
    if default_prov:
        lines.append(f"  [dim]default:[/] {default_prov}")
    lines.append("")
    header = f"  {'provider':<{name_w}} account"
    lines.append(f"[dim]{header}[/]")
    lines.append(f"[dim]  {'-' * (name_w - 2):<{name_w}} {'-' * 30}[/]")

    for r in rows:
        slug = r.get("slug", "?")
        p = prov_by_slug.get(slug)
        auth = r.get("auth", "?")
        configured = r.get("configured")
        if auth == "local":
            endpoint = r.get("endpoint") or (p.base_url if p else "")
            account_cell = endpoint or "(local)"
        elif configured and p is not None:
            key = p.key_value()
            account_cell = _mask_key(key, tail=6)
        else:
            account_cell = "<unset>"
        mark = "[green]●[/]" if configured else "[dim]○[/]"
        lines.append(f"  {mark} {slug:<{name_w - 2}} {account_cell}")
    return "\n".join(lines)


def _capture_subscription_info() -> dict:
    """Return a unified subscription/usage/wallet snapshot.

    Combines:
      - ~/.config/sinister/subscription.json (jcode/RKOJ scaffold, if present):
        tier, monthly_cap, renews_at, etc.
      - forge-prefs.json (agent V's surface — read for any subscription_* keys).
      - sinister-usage.today_summary()  (local usage estimate).
      - sinister-login.status_all()     (which providers configured).

    All sources are optional — missing modules / files degrade gracefully.
    Returned shape (stable):
      {
        "subscription": {"present": bool, "path": str, "tier": str|None,
                         "monthly_cap": int|None, "renews_at": str|None,
                         "raw": dict},
        "usage":        {"present": bool, "sessions_today": int,
                         "bytes_today": int, "rough_tokens_today": int,
                         "as_of_utc": str|None},
        "wallet":       {"configured_count": int, "total": int,
                         "default_provider": str|None,
                         "configured_slugs": list[str]},
        "prefs_keys":   list[str],   # any forge-prefs keys starting with 'subscription_'
      }
    """
    out: dict = {
        "subscription": {"present": False, "path": "", "tier": None,
                         "monthly_cap": None, "renews_at": None,
                         "current_usage": None, "raw": {}},
        "usage": {"present": False, "sessions_today": 0, "bytes_today": 0,
                  "rough_tokens_today": 0, "as_of_utc": None},
        "wallet": {"configured_count": 0, "total": 0,
                   "default_provider": None, "configured_slugs": []},
        "prefs_keys": [],
    }

    # 1. subscription.json
    sub_path = _sinister_config_path("subscription.json")
    out["subscription"]["path"] = str(sub_path)
    if sub_path.exists():
        try:
            raw = json.loads(sub_path.read_text(encoding="utf-8-sig"))
            out["subscription"]["present"] = True
            out["subscription"]["raw"] = raw if isinstance(raw, dict) else {}
            if isinstance(raw, dict):
                out["subscription"]["tier"] = raw.get("tier")
                out["subscription"]["monthly_cap"] = raw.get("monthly_cap")
                out["subscription"]["renews_at"] = raw.get("renews_at")
                out["subscription"]["current_usage"] = raw.get("current_usage")
        except Exception:
            pass

    # 2. forge-prefs.json — any subscription_* keys agent V dropped in
    try:
        prefs = _load_forge_prefs()
        out["prefs_keys"] = sorted(k for k in prefs.keys()
                                   if k.startswith("subscription"))
    except Exception:
        pass

    # 3. sinister-usage.today_summary
    try:
        from sinister_usage import today_summary  # type: ignore
        summ = today_summary()
        out["usage"]["present"] = True
        out["usage"]["sessions_today"] = int(summ.get("sessions_today", 0))
        out["usage"]["bytes_today"] = int(summ.get("bytes_today", 0))
        out["usage"]["rough_tokens_today"] = int(summ.get("rough_tokens_today", 0))
        out["usage"]["as_of_utc"] = summ.get("as_of_utc")
    except Exception:
        pass

    # 4. sinister-login.status_all + default-provider lookup
    try:
        from sinister_login import status_all  # type: ignore
        rows = status_all()
        configured = [r for r in rows if r.get("configured")]
        out["wallet"]["configured_count"] = len(configured)
        out["wallet"]["total"] = len(rows)
        out["wallet"]["configured_slugs"] = [r.get("slug") for r in configured]
    except Exception:
        pass

    login_state = _load_login_state()
    out["wallet"]["default_provider"] = (login_state.get("default_provider")
                                         or state("default_provider"))

    return out


def _cmd_subscription(args, pane, app) -> str:
    """jcode /subscription — inspect the jcode/RKOJ subscription scaffold.

    Reads ~/.config/sinister/subscription.json if present; otherwise prints
    a placeholder showing exactly where the data WOULD live (tier,
    monthly_cap, current_usage from sinister-usage, renews_at).

    Use `/subscription raw` to dump the raw JSON payload (when present).
    """
    info = _capture_subscription_info()
    sub = info["subscription"]
    usage = info["usage"]
    wallet = info["wallet"]

    # `/subscription raw` — dump the parsed JSON (for debugging).
    if args and args[0].lower() == "raw":
        if not sub["present"]:
            return f"[yellow]/subscription raw: no file at {sub['path']}[/]"
        return json.dumps(sub["raw"], indent=2, sort_keys=True)

    lines = ["[bold]subscription[/]  (jcode/RKOJ scaffold)"]
    lines.append(f"  [dim]file:[/] {sub['path']}")
    if sub["present"]:
        lines.append(f"  [dim]status:[/] [green]present[/]")
        lines.append(f"  tier:           {sub['tier'] or '(unset)'}")
        cap = sub["monthly_cap"]
        lines.append(f"  monthly_cap:    {cap if cap is not None else '(unset)'}")
        lines.append(f"  renews_at:      {sub['renews_at'] or '(unset)'}")
        cur_usage = sub.get("current_usage")
        if cur_usage is not None:
            lines.append(f"  current_usage:  {cur_usage}  [dim](from subscription.json)[/]")
    else:
        lines.append(f"  [dim]status:[/] [yellow]placeholder[/] — file not yet written")
        lines.append("")
        lines.append("  [dim]when present, this file would contain:[/]")
        lines.append("    tier:           free | starter | pro | enterprise")
        lines.append("    monthly_cap:    <int>     (token cap for the period)")
        lines.append("    current_usage:  <int>     (rolling token count this period)")
        lines.append("    renews_at:      <iso8601> (next billing renewal)")

    # Always show current usage estimate from sinister-usage (local-only).
    lines.append("")
    if usage["present"]:
        lines.append("  [dim]current usage (sinister-usage today_summary, local-only):[/]")
        lines.append(f"    sessions_today:      {usage['sessions_today']}")
        lines.append(f"    bytes_today:         {usage['bytes_today']}")
        lines.append(f"    rough_tokens_today:  {usage['rough_tokens_today']}")
        if usage["as_of_utc"]:
            lines.append(f"    as_of_utc:           {usage['as_of_utc']}")
    else:
        lines.append("  [dim]sinister-usage unavailable — install:[/] "
                     "pip install -e \"D:/Sinister Sanctum/tools/sinister-usage\"")

    # Wallet summary line (which providers are configured).
    lines.append("")
    lines.append(f"  [dim]wallet:[/] "
                 f"{wallet['configured_count']}/{wallet['total']} providers configured  "
                 f"[dim]default:[/] {wallet['default_provider'] or '(auto-resolved)'}")
    if wallet["configured_slugs"]:
        lines.append(f"    configured: {', '.join(wallet['configured_slugs'])}")

    if info["prefs_keys"]:
        lines.append("")
        lines.append(f"  [dim]forge-prefs subscription keys:[/] "
                     f"{', '.join(info['prefs_keys'])}")

    return "\n".join(lines)


def _cmd_effort(args, pane, app) -> str:
    """jcode /effort — set reasoning effort level. Persists to forge-prefs.json.

    Levels: none | low | medium | high | xhigh.
    """
    prefs = _load_forge_prefs()
    current = prefs.get("reasoning_effort") or state("effort")
    if not args:
        return f"  effort = {current}"
    val = args[0].lower()
    if val not in {"none", "low", "medium", "high", "xhigh"}:
        return "[yellow]/effort: none|low|medium|high|xhigh[/]"
    prev = current
    prefs["reasoning_effort"] = val
    try:
        path = _save_forge_prefs(prefs)
    except Exception as e:
        return f"[red]/effort: persist failed: {e}[/]"
    set_state("effort", val)
    return f"  effort: {prev} → {val}  [dim]({path})[/]"


def _cmd_fast(args, pane, app) -> str:
    """jcode /fast — toggle OpenAI/Codex fast mode. Persists fast_mode bool.

    /fast            -> print status
    /fast on         -> enable
    /fast off        -> disable
    /fast status     -> print status
    /fast default    -> reset to off
    """
    prefs = _load_forge_prefs()
    current = bool(prefs.get("fast_mode", False))
    if not args or args[0].lower() == "status":
        return f"  fast = {'on' if current else 'off'}"
    val = args[0].lower()
    if val not in {"on", "off", "default"}:
        return "[yellow]/fast: on|off|status|default[/]"
    new_val = True if val == "on" else False  # off + default both -> False
    prefs["fast_mode"] = new_val
    try:
        path = _save_forge_prefs(prefs)
    except Exception as e:
        return f"[red]/fast: persist failed: {e}[/]"
    set_state("fast_mode", "on" if new_val else "off")
    return f"  fast: {'on' if current else 'off'} → {'on' if new_val else 'off'}  [dim]({path})[/]"


def _cmd_transport(args, pane, app) -> str:
    """jcode /transport — set provider transport mode. Persists to forge-prefs.

    Modes: auto | https | websocket. Some providers (Anthropic, OpenAI) only
    support https; the flag is accepted regardless and documented gracefully —
    transport selection is honored by the future provider router.
    """
    prefs = _load_forge_prefs()
    current = prefs.get("transport", "auto")
    if not args:
        return f"  transport = {current}"
    val = args[0].lower()
    if val not in {"auto", "https", "websocket"}:
        return "[yellow]/transport: auto|https|websocket[/]"
    prev = current
    prefs["transport"] = val
    try:
        path = _save_forge_prefs(prefs)
    except Exception as e:
        return f"[red]/transport: persist failed: {e}[/]"
    note = ""
    if val == "websocket":
        note = ("\n  [dim]note: Anthropic + OpenAI providers only support https; "
                "the websocket flag will be ignored for those providers.[/]")
    return f"  transport: {prev} → {val}  [dim]({path})[/]" + note


def _cmd_alignment(args, pane, app) -> str:
    """jcode /alignment — text alignment preference. Persists text_alignment.

    Args: status | centered | left.
    Note: the actual rendering switch is not wired yet; the flag is read by
    the future renderer (jcode-style centered output vs. default left).
    """
    prefs = _load_forge_prefs()
    current = prefs.get("text_alignment", "left")
    if not args or args[0].lower() == "status":
        return (f"  text_alignment = {current}\n"
                f"  [dim]note: renderer hook not yet wired — flag persisted only[/]")
    val = args[0].lower()
    if val not in {"centered", "left"}:
        return "[yellow]/alignment: status|centered|left[/]"
    prev = current
    prefs["text_alignment"] = val
    try:
        path = _save_forge_prefs(prefs)
    except Exception as e:
        return f"[red]/alignment: persist failed: {e}[/]"
    return (f"  alignment: {prev} → {val}  [dim]({path})[/]\n"
            f"  [dim]note: renderer hook not yet wired — future renderer will read this[/]")


def _cmd_dictate(args, pane, app) -> str:
    """jcode /dictate — launch external dictation command.

    Reads SINISTER_DICTATE_CMD env var. If set, runs it (detached, fire-and-
    forget). If unset, prints a hint with the env-var name.
    """
    cmd = os.environ.get("SINISTER_DICTATE_CMD", "").strip()
    if not cmd:
        return "[dictate] set SINISTER_DICTATE_CMD env var to a dictation launcher command"
    try:
        if platform.system() == "Windows":
            # use shell=True so things like "start dictation.exe" work
            subprocess.Popen(cmd, shell=True)
        else:
            subprocess.Popen(cmd, shell=True,
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
        return f"  [dictate] launched: {cmd}"
    except Exception as e:
        return f"[red]/dictate: launch failed ({cmd}): {e}[/]"


# ----- system commands ----------------------------------------------------

def _fmt_age(seconds: float) -> str:
    """Human-friendly age string for a delta in seconds."""
    seconds = max(0.0, float(seconds))
    if seconds < 60:
        return f"{int(seconds)}s ago"
    if seconds < 3600:
        return f"{int(seconds // 60)}m ago"
    if seconds < 86400:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        return f"{h}h{m:02d}m ago"
    d = int(seconds // 86400)
    h = int((seconds % 86400) // 3600)
    return f"{d}d{h:02d}h ago"


def _cmd_reload(args, pane=None, app=None) -> str:
    """Reload to a newer RKOJ.exe binary if one is available on disk.

    Compares mtime of `automations/build/forge-exe/dist/RKOJ.exe` against the
    currently-running interpreter / EXE (`sys.executable`). If dist is newer,
    prints a relaunch instruction. Does NOT actually re-exec — too risky inside
    a running Forge TUI.
    """
    sr = _sanctum_root()
    dist = sr / "automations" / "build" / "forge-exe" / "dist" / "RKOJ.exe"
    if not dist.exists():
        return (f"[yellow]/reload[/]: no built RKOJ.exe at {dist}\n"
                f"  [dim]run /rebuild first[/]")
    try:
        dist_mtime = dist.stat().st_mtime
    except OSError as e:
        return f"[red]/reload[/]: cannot stat {dist}: {e}"

    cur_exe = sys.executable or ""
    try:
        cur_mtime = Path(cur_exe).stat().st_mtime if cur_exe else 0.0
    except OSError:
        cur_mtime = 0.0

    now = time.time()
    dist_age = _fmt_age(now - dist_mtime)

    if dist_mtime <= cur_mtime:
        return (f"[dim]/reload[/]: dist RKOJ.exe (built {dist_age}) is not newer "
                f"than the currently-running binary.\n"
                f"  current: {cur_exe}\n"
                f"  dist:    {dist}\n"
                f"  [dim]run /rebuild to produce a fresh build first[/]")

    return (f"[reload] newer binary at {dist} (built {dist_age}). "
            f"exit + relaunch from there?\n"
            f"  [dim]/quit, then launch: {dist}[/]\n"
            f"  [dim](re-exec from inside the running TUI is disabled — too risky)[/]")


def _cmd_restart(args, pane=None, app=None) -> str:
    """Restart the current session with the same params (no rebuild).

    In the Forge TUI: posts a `RestartSession` message to the app (best-effort —
    if the app doesn't handle it, falls back to `app.exit()`).
    In the RKOJ.exe simple shell: prints an instruction.
    """
    if app is None:
        return ("[restart] please type /quit then relaunch RKOJ.exe — "
                "restart-in-place is not supported in the simple shell")

    posted = False
    try:
        post = getattr(app, "post_message", None)
        if callable(post):
            try:
                from textual.message import Message  # type: ignore
            except Exception:
                Message = None  # type: ignore
            if Message is not None:
                class RestartSession(Message):  # type: ignore
                    pass
                post(RestartSession())
                posted = True
    except Exception:
        posted = False

    if posted:
        return "[dim]/restart[/]: RestartSession posted — app should rebuild panes shortly."

    try:
        app.exit()
    except Exception:
        pass
    return "[dim]/restart[/]: exiting current session; relaunch to restart (no rebuild)."


def _cmd_rebuild(args, pane=None, app=None) -> str:
    """Trigger a full PyInstaller rebuild of RKOJ.exe in the background.

    Spawns `pyinstaller --clean --noconfirm RKOJ.spec` in
    `automations/build/forge-exe/` via detached subprocess.Popen, logging
    stdout + stderr to a timestamped file. Does not block — returns
    immediately with the log path + ETA (~3-5 min).
    """
    sr = _sanctum_root()
    build_dir = sr / "automations" / "build" / "forge-exe"
    spec = build_dir / "RKOJ.spec"
    if not spec.exists():
        return (f"[red]/rebuild[/]: spec file not found at {spec}\n"
                f"  [dim]expected {build_dir}/RKOJ.spec[/]")

    log_dir = build_dir / "build-logs"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        return f"[red]/rebuild[/]: cannot create log dir {log_dir}: {e}"

    stamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    log_path = log_dir / f"rebuild-{stamp}.log"

    creationflags = 0
    start_new_session = False
    if sys.platform.startswith("win"):
        # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        creationflags = 0x00000008 | 0x00000200
    else:
        start_new_session = True

    try:
        log_fh = open(log_path, "wb")
    except OSError as e:
        return f"[red]/rebuild[/]: cannot open log file {log_path}: {e}"

    cmd = ["pyinstaller", "--clean", "--noconfirm", "RKOJ.spec"]
    try:
        subprocess.Popen(
            cmd,
            cwd=str(build_dir),
            stdout=log_fh,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            creationflags=creationflags,
            start_new_session=start_new_session,
            close_fds=True,
        )
    except FileNotFoundError:
        log_fh.close()
        return ("[red]/rebuild[/]: `pyinstaller` not found on PATH.\n"
                "  [dim]pip install pyinstaller, then retry /rebuild[/]")
    except Exception as e:
        log_fh.close()
        return f"[red]/rebuild[/]: failed to spawn pyinstaller: {e}"

    set_state("last_rebuild_log", str(log_path))
    set_state("last_rebuild_started", time.time())

    return (f"[rebuild] spawned `pyinstaller --clean --noconfirm RKOJ.spec`\n"
            f"  cwd: {build_dir}\n"
            f"  log: {log_path}\n"
            f"  ETA: ~3-5 min  (tail the log to watch progress)\n"
            f"  [dim]calling session is not blocked; run /reload when the build completes[/]")


def _cmd_client_reload(args, pane=None, app=None) -> str:
    """Reload the agent pane's Textual widgets without re-spawning the subprocess.

    In the Forge TUI context, calls `pane.refresh()`. In the simple shell
    context (no pane), it's a no-op with a note.
    """
    if pane is None:
        return "[client-reload] no-op in the simple shell (no Textual pane to refresh)."
    refresh = getattr(pane, "refresh", None)
    if not callable(refresh):
        return "[yellow]/client-reload[/]: current pane has no .refresh() method."
    try:
        refresh()
    except Exception as e:
        return f"[red]/client-reload[/]: pane.refresh() failed: {e}"
    return "[dim]/client-reload[/]: pane widgets refreshed (subprocess untouched)."


def _cmd_server_reload(args, pane=None, app=None) -> str:
    """Kill + respawn the current agent subprocess (without tearing down the pane).

    In the Forge TUI: calls `pane._spawn_agent_again()` if it exists.
    In the simple shell: prints an instruction (no agent subprocess).
    """
    if pane is None:
        return "[server-reload] please /quit + relaunch"
    respawn = getattr(pane, "_spawn_agent_again", None)
    if not callable(respawn):
        return ("[yellow]/server-reload[/]: current pane has no _spawn_agent_again() "
                "hook — /quit + relaunch to reset the subprocess.")
    try:
        respawn()
    except Exception as e:
        return f"[red]/server-reload[/]: respawn failed: {e}"
    return "[dim]/server-reload[/]: agent subprocess respawned."


def _cmd_mcp(args, pane, app) -> str:
    """MCP fleet management — list servers, inspect tools, call tools.

    Subcommands (Phase 2 wired 2026-05-21 with v1.4.0 EXE bundle of the `mcp` SDK):
      /mcp                    list servers from ~/.claude/.mcp.json (default)
      /mcp list               same as default
      /mcp show <name>        show full config for a server
      /mcp tools <name>       list tools the server provides (async stdio probe)
      /mcp call <name> <tool> [json]   call a tool via stdio (returns result)
      /mcp status             report whether the `mcp` Python SDK is bundled

    Sinister fleet MCPs: ruflo (200+ tools), vault (1TB store), eve, sinister-panel,
    sinister-snap, sinister-tiktok. Each speaks stdio MCP — the bundled `mcp` SDK
    connects to them on demand.
    """
    mcp_cfg = Path.home() / ".claude" / ".mcp.json"
    sub = args[0].lower() if args else "list"

    # Load config once
    cfg = {}
    servers = {}
    if mcp_cfg.exists():
        try:
            cfg = json.loads(mcp_cfg.read_text(encoding="utf-8"))
            servers = cfg.get("mcpServers", {})
        except Exception as e:
            return f"[red]parse error reading {mcp_cfg}: {e}[/]"
    else:
        return f"[yellow]no ~/.claude/.mcp.json found at {mcp_cfg}[/]\nClaude Code writes this file on first MCP install."

    if sub in ("list", "ls"):
        lines = [f"[bold]MCP servers[/]  [dim]({len(servers)} configured in ~/.claude/.mcp.json)[/]"]
        for name in sorted(servers):
            entry = servers.get(name, {})
            cmd = entry.get("command", "?")
            cargs = entry.get("args", [])
            cargs_disp = " ".join(cargs[:3])
            lines.append(f"  · [bold]{name}[/]  [dim]{cmd} {cargs_disp}[/]")
        lines.append("\n[dim]/mcp show <name>  · /mcp tools <name>  · /mcp call <name> <tool> [json][/]")
        return "\n".join(lines)

    if sub == "show":
        if len(args) < 2:
            return "[yellow]usage: /mcp show <server-name>[/]"
        name = args[1]
        if name not in servers:
            return f"[red]no such server: {name}[/]  [dim](try /mcp list)[/]"
        entry = servers[name]
        return f"[bold]{name}[/]\n{json.dumps(entry, indent=2)}"

    if sub == "status":
        try:
            import mcp as _mcp_pkg  # noqa: F401
            sdk = f"OK ({getattr(_mcp_pkg, '__version__', 'unknown')})"
        except Exception as e:
            sdk = f"MISSING ({e})"
        return (
            f"[bold]MCP runtime[/]\n"
            f"  SDK:     {sdk}  [dim](bundled in RKOJ.exe v1.4.0+)[/]\n"
            f"  Config:  {mcp_cfg}  [dim]{'exists' if mcp_cfg.exists() else 'missing'}[/]\n"
            f"  Servers: {len(servers)}\n"
        )

    if sub == "tools":
        if len(args) < 2:
            return "[yellow]usage: /mcp tools <server-name>[/]"
        name = args[1]
        if name not in servers:
            return f"[red]no such server: {name}[/]"
        # Phase 2B follow-up: full async stdio probe. For now, surface the
        # tool list the server's package documents (hardcoded fleet knowledge)
        # OR run `sinister mcp tools <name>` once that CLI exists.
        return (
            f"[bold]{name} tools[/]\n"
            f"  [dim]live stdio probe of MCP servers is Phase 2B (next turn).[/]\n"
            f"  [dim]today: the `mcp` Python SDK ships inside RKOJ.exe v1.4.0;[/]\n"
            f"  [dim]use it directly from a Python shell:[/]\n\n"
            f"    from mcp import ClientSession, StdioServerParameters\n"
            f"    from mcp.client.stdio import stdio_client\n"
            f"    # ... see https://github.com/modelcontextprotocol/python-sdk\n"
        )

    if sub == "call":
        if len(args) < 3:
            return "[yellow]usage: /mcp call <server> <tool> [json-args][/]"
        return (
            f"[dim]/mcp call wire-up is Phase 2B follow-up.[/]\n"
            f"[dim]Today the SDK is bundled; the slash-command wire-up needs an[/]\n"
            f"[dim]async-safe Textual-loop integration (helper subprocess vs.[/]\n"
            f"[dim]loop.run_in_executor). Tracked in MCP Phase 2 TaskList.[/]"
        )

    return f"[yellow]unknown /mcp subcommand: {sub}[/]  [dim]try /mcp list | show | tools | call | status[/]"


def _cmd_tools(args, pane, app) -> str:
    return ("[bold]Available tools[/]\n"
            "  builtin (in EXE):  read · write · edit · bash · grep · glob · git · webfetch · webSearch · task · taskOutput · monitor\n"
            "  sinister-cli:      sinister memory · swarm · graph · login · usage · forge · term\n"
            "  MCP (lazy):        ruflo (28 tools) · vault (10) · gmail · calendar · drive\n"
            "  skills:            see /skills")


def _cmd_skills(args, pane, app) -> str:
    """List user + project skills (jcode pattern)."""
    found = []
    for root in (Path.home() / ".claude" / "skills",
                 Path.home() / ".claude" / "plugins",
                 _sanctum_root() / ".claude" / "skills",
                 _sanctum_root() / "skills"):
        if not root.exists():
            continue
        for d in root.iterdir():
            if d.is_dir() and not d.name.startswith("_"):
                found.append((d.name, str(d)))
    if not found:
        return "[yellow]no skills discovered[/]"
    found = sorted(set(found))
    lines = [f"[bold]Skills ({len(found)})[/]  [dim]type /<skill-name> to activate[/]"]
    for name, path in found[:50]:
        lines.append(f"  · /{name:<28} [dim]{Path(path).parent.name}[/]")
    if len(found) > 50:
        lines.append(f"  [dim]… +{len(found) - 50} more[/]")
    return "\n".join(lines)


def _cmd_debug_visual(args, pane=None, app=None) -> str:
    """Toggle the SINISTER_DEBUG_VISUAL flag in `_state`.

    When on, future tool calls + thinking blocks include extra render markers
    (borders, line numbers). This handler just flips the flag — the render
    code that consumes it can be added later. Accepts optional `on`/`off`/
    `status` argument; with no arg, toggles the current state.
    """
    cur = bool(_state.get("SINISTER_DEBUG_VISUAL", False))
    if args:
        val = args[0].lower()
        if val in {"on", "true", "1", "yes"}:
            new = True
        elif val in {"off", "false", "0", "no"}:
            new = False
        elif val in {"status", "?"}:
            return f"[dim]/debug-visual[/]: SINISTER_DEBUG_VISUAL = {cur}"
        elif val in {"toggle", "flip"}:
            new = not cur
        else:
            return "[yellow]/debug-visual: on|off|toggle|status[/]"
    else:
        new = not cur

    set_state("SINISTER_DEBUG_VISUAL", new)
    # Mirror to env so child processes / render code can see it without
    # importing forge.commands._state directly.
    os.environ["SINISTER_DEBUG_VISUAL"] = "1" if new else "0"
    arrow = "ON" if new else "OFF"
    return (f"[debug-visual] SINISTER_DEBUG_VISUAL = {arrow}  "
            f"[dim](render markers / borders / line-numbers will appear once "
            f"render code consumes the flag)[/]")


# ----- session-loop commands (delegated to siblings) ---------------------

def _stub(name: str, summary: str, detail: str = "",
          subcommands: dict[str, str] | None = None) -> Callable:
    """Factory for jcode-parity stub handlers.

    Operator directive 2026-05-21: every command in jcode's /help overlay must
    exist as either a real handler or a stub that tells the operator the feature
    is tracked. Use subcommands={'resume': 'desc'} to support `/improve resume`,
    `/refactor resume`, `/catchup next`, etc.
    """
    def _h(args, pane, app):
        if args and subcommands and args[0].lower() in subcommands:
            sub = args[0].lower()
            sd = subcommands[sub]
            return (f"[yellow]/{name} {sub}[/]: {sd}\n"
                    f"  [dim]not implemented in v0.7.0; tracked in jcode-parity-roadmap[/]")
        return (f"[note] /{name}: {summary} — "
                f"not implemented in v0.7.0; tracked in jcode-parity-roadmap\n"
                f"  [dim]{detail or 'roadmap'}[/]")
    return _h


# ----- helpers -----------------------------------------------------------

def _git_branch(root: Path) -> str:
    try:
        r = subprocess.run(["git", "-C", str(root), "rev-parse", "--abbrev-ref", "HEAD"],
                           capture_output=True, text=True, timeout=2)
        return r.stdout.strip() or "?"
    except Exception:
        return "?"


def _git_head(root: Path) -> str:
    try:
        r = subprocess.run(["git", "-C", str(root), "rev-parse", "--short", "HEAD"],
                           capture_output=True, text=True, timeout=2)
        return r.stdout.strip() or "?"
    except Exception:
        return "?"


def _capture_cli(cli_main: Callable, argv: list[str]) -> str:
    import io
    out, err = io.StringIO(), io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        rv = cli_main(argv)
    except SystemExit as e:
        rv = e.code
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    body = out.getvalue() or err.getvalue()
    return body.rstrip()


# ----- skill dynamic dispatch --------------------------------------------

def maybe_dispatch_skill(name: str, args: list[str]) -> str | None:
    """If `name` is a discovered skill, invoke it (return printout) else None.

    Resolution order:
      1. SkillRegistry (jcode-parity loader — ~/.sinister/skills/*.md and
         D:/Sinister Sanctum/skills/*.md as flat .md files).
      2. Legacy SKILL.md directory layout (~/.claude/skills/<name>/SKILL.md).
    """
    # 1. SkillRegistry (flat .md file layout — preferred)
    try:
        from forge.skills import SkillRegistry  # type: ignore
        reg = SkillRegistry.shared()
        skill = reg.get(name)
        if skill is not None:
            head = (
                f"[bold]Skill[/] /{skill.name}  "
                f"[dim]{skill.path}[/]\n"
                f"  {skill.description}\n"
            )
            if skill.allowed_tools:
                head += f"  [dim]allowed-tools: {', '.join(skill.allowed_tools)}[/]\n"
            body = skill.content.strip()
            preview = body if len(body) < 1500 else body[:1500] + "\n[dim]… (truncated)[/]"
            return head + "\n" + preview
    except Exception as e:
        # Never block dispatch on a registry error — fall through to legacy.
        pass

    # 2. Legacy ~/.claude/skills/<name>/SKILL.md directory layout
    for root in (Path.home() / ".claude" / "skills",
                 Path.home() / ".claude" / "plugins",
                 _sanctum_root() / ".claude" / "skills"):
        cand = root / name
        if cand.is_dir():
            md = cand / "SKILL.md"
            if md.exists():
                try:
                    txt = md.read_text(encoding="utf-8")[:1500]
                    return f"[bold]Skill[/] /{name}\n{txt}\n[dim]…[/]"
                except OSError:
                    pass
            return f"[bold]Skill[/] /{name}  [dim]{cand}[/]\n  [yellow](no SKILL.md found)[/]"
    return None


# ----- /skill registry commands ------------------------------------------

def _cmd_skill(args, pane, app) -> str:
    """/skill list | show <name> | run <name> | reload  — jcode-parity skill registry."""
    try:
        from forge.skills import SkillRegistry
    except Exception as e:
        return f"[red]forge.skills unavailable: {e}[/]"

    sub = (args[0].lower() if args else "list")
    rest = args[1:]

    if sub in {"list", "ls", ""}:
        reg = SkillRegistry.shared()
        names = reg.names()
        if not names:
            roots = "\n    ".join(str(r) for r in reg.roots())
            return f"[yellow]no skills found[/]\n  roots scanned:\n    {roots}"
        lines = [f"[bold]Skills ({len(names)})[/]  [dim]/<name> to activate, /skill show <name>, /skill run <name>[/]"]
        for n in names:
            s = reg.get(n)
            if s is None:
                continue
            lines.append(f"  /{n:<24} {s.description}")
        return "\n".join(lines)

    if sub in {"show", "info", "cat"}:
        if not rest:
            return "[yellow]usage: /skill show <name>[/]"
        reg = SkillRegistry.shared()
        s = reg.get(rest[0])
        if s is None:
            return f"[yellow]/skill: no such skill `{rest[0]}`[/]"
        head = (f"[bold]Skill[/] /{s.name}  [dim]{s.path}[/]\n"
                f"  {s.description}\n")
        if s.allowed_tools:
            head += f"  allowed-tools: {', '.join(s.allowed_tools)}\n"
        return head + "\n" + s.content.strip()

    if sub in {"run", "activate"}:
        if not rest:
            return "[yellow]usage: /skill run <name>[/]"
        out = maybe_dispatch_skill(rest[0], rest[1:])
        if out is None:
            return f"[yellow]/skill: no such skill `{rest[0]}`[/]"
        return out

    if sub in {"reload", "refresh"}:
        reg = SkillRegistry.reload_shared()
        return f"  reloaded — {len(reg.names())} skill(s) from {len(reg.roots())} root(s)"

    return f"[yellow]/skill: unknown subcommand `{sub}` — use list|show|run|reload[/]"


# ----- /mermaid — wraps tools/memory-graph-render for inline + file renders -

# Tracks last-rendered SVG/PNG path for /mermaid open.
_LAST_MERMAID_RENDER: dict[str, str | None] = {"path": None}


def _mermaid_renders_dir() -> Path:
    """Output dir for /mermaid renders. Honors SANCTUM_ROOT discovery."""
    d = _sanctum_root() / "_shared-memory" / "forge-memory" / "mermaid-renders"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _extract_first_mermaid_block(text: str) -> str | None:
    """Return the contents of the first ```mermaid ... ``` fenced block, or
    None if no fence is present. Treats whole text as mermaid if no fences."""
    # fenced ```mermaid ... ```
    needle = "```mermaid"
    idx = text.lower().find(needle)
    if idx == -1:
        return None
    # advance past the line containing the fence open
    nl = text.find("\n", idx)
    if nl == -1:
        return None
    rest = text[nl + 1:]
    end = rest.find("```")
    if end == -1:
        return None
    return rest[:end].strip()


def _mermaid_help() -> str:
    return ("[bold]/mermaid[/]  [dim]render Mermaid diagrams via memory-graph-render[/]\n"
            "  /mermaid file <path>      read .md/.mmd, render first mermaid block\n"
            "  /mermaid render <inline>  render inline mermaid syntax (quote it)\n"
            "  /mermaid open             open the last rendered file in OS viewer\n"
            "  /mermaid backends         show available render backends")


def _cmd_mermaid(args, pane, app) -> str:
    """/mermaid file|render|open|backends — wraps memory-graph-render."""
    if not args:
        return _mermaid_help()
    sub = args[0].lower()
    rest = args[1:]

    try:
        from memory_graph_render import render as mgr_render, detect_backend
    except Exception as e:
        return (f"[red]/mermaid: memory_graph_render not importable: {e}[/]\n"
                f"  install: pip install -e \"{_sanctum_root()}/tools/memory-graph-render\"")

    if sub in {"backends", "backend"}:
        return f"[bold]/mermaid backends[/]\n  active: {detect_backend()}\n  priority: mermaid-rs-renderer → mmdc → html-fallback"

    if sub == "open":
        last = _LAST_MERMAID_RENDER.get("path")
        if not last or not Path(last).exists():
            return "[yellow]/mermaid open: no recent render — run /mermaid file|render first[/]"
        try:
            if platform.system() == "Windows":
                os.startfile(last)  # type: ignore[attr-defined]
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", last])
            else:
                subprocess.Popen(["xdg-open", last])
            return f"  opened: {last}"
        except Exception as e:
            return f"[red]/mermaid open: {e}[/]"

    # both `file` and `render` resolve to a mermaid source string
    if sub == "file":
        if not rest:
            return "[yellow]usage: /mermaid file <path>[/]"
        p = Path(" ".join(rest).strip('"').strip("'"))
        if not p.is_absolute():
            p = _sanctum_root() / p
        if not p.exists():
            return f"[red]/mermaid file: not found: {p}[/]"
        try:
            text = p.read_text(encoding="utf-8")
        except Exception as e:
            return f"[red]/mermaid file: read error: {e}[/]"
        if p.suffix.lower() == ".mmd":
            src = text.strip()
        else:
            block = _extract_first_mermaid_block(text)
            if block is None:
                return f"[yellow]/mermaid file: no ```mermaid``` block found in {p.name}[/]"
            src = block
        title = f"mermaid :: {p.name}"
    elif sub == "render":
        if not rest:
            return "[yellow]usage: /mermaid render <inline-mermaid-syntax>[/]"
        src = " ".join(rest)
        # If user wrapped in backticks/fence, strip
        block = _extract_first_mermaid_block(src)
        if block is not None:
            src = block
        title = "mermaid :: inline"
    else:
        return f"[yellow]/mermaid: unknown subcommand `{sub}`[/]\n" + _mermaid_help()

    if not src.strip():
        return "[yellow]/mermaid: empty source[/]"

    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    out_dir = _mermaid_renders_dir()
    # memory_graph_render writes .png + .mmd + .html; pass a .png stem and
    # surface whichever backend produced is available; .html is always present.
    target = out_dir / f"{ts}.png"
    try:
        result = mgr_render(mermaid_src=src, output=str(target), title=title)
    except Exception as e:
        return f"[red]/mermaid: render crashed: {e}[/]"

    backend = result.get("backend") or "unknown"
    png = result.get("png")
    html = result.get("html")
    mmd = result.get("mmd")
    err = result.get("error")

    # Pick what to open: prefer PNG, then HTML fallback, then MMD.
    preferred = png or html or mmd
    if preferred:
        _LAST_MERMAID_RENDER["path"] = preferred

    lines = [f"[bold]/mermaid[/]  backend={backend}"]
    if png:
        lines.append(f"  png:  {png}")
    if html:
        lines.append(f"  html: {html}")
    if mmd:
        lines.append(f"  mmd:  {mmd}")
    if err and not png:
        lines.append(f"  [yellow]note:[/] {err}")
    lines.append("  [dim]/mermaid open  — open the rendered file[/]")
    return "\n".join(lines)


# ===========================================================================
# NEW (jcode-parity batch): /todo /focus /diff /search /export
# ===========================================================================

def _cmd_todo(args, pane=None, app=None) -> str:
    """jcode-parity /todo — per-session todo list, persists to todos.json.

    Subcommands:
      /todo                 -> list (default)
      /todo list            -> checkbox-style list
      /todo add <text>      -> append a new todo
      /todo done <N>        -> mark todo N (1-indexed) done
      /todo clear           -> remove all done todos

    Each entry: {id, text, created, done}.
    """
    todos = _load_todos()
    sub = (args[0].lower() if args else "list")

    if sub == "list":
        if not todos:
            return ("  no todos.  "
                    "[dim]/todo add <text> · /todo done <N> · /todo clear[/]")
        lines = [f"[bold]Todos[/] [dim]({_todos_path()})[/]"]
        for i, t in enumerate(todos, start=1):
            box = "[x]" if t.get("done") else "[ ]"
            text = t.get("text", "(no text)")
            lines.append(f"  {i:>2}. {box} {text}")
        n_done = sum(1 for t in todos if t.get("done"))
        lines.append(f"  [dim]{n_done}/{len(todos)} done · /todo done <N> · /todo clear[/]")
        return "\n".join(lines)

    if sub == "add":
        text = " ".join(args[1:]).strip()
        if not text:
            return "[yellow]usage: /todo add <text>[/]"
        next_id = (max((t.get("id", 0) for t in todos), default=0) + 1)
        entry = {
            "id": next_id,
            "text": text,
            "created": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "done": False,
        }
        todos.append(entry)
        try:
            p = _save_todos(todos)
        except Exception as e:
            return f"[red]/todo add: save failed: {e}[/]"
        return f"  added #{next_id}: {text}  [dim]→ {p}[/]"

    if sub == "done":
        if len(args) < 2 or not args[1].isdigit():
            return "[yellow]usage: /todo done <N>  (1-indexed)[/]"
        idx = int(args[1])
        if not (1 <= idx <= len(todos)):
            return f"[yellow]/todo done: index out of range (1-{len(todos)})[/]"
        todos[idx - 1]["done"] = True
        try:
            _save_todos(todos)
        except Exception as e:
            return f"[red]/todo done: save failed: {e}[/]"
        return f"  done #{idx}: {todos[idx - 1].get('text', '')}"

    if sub == "clear":
        before = len(todos)
        kept = [t for t in todos if not t.get("done")]
        try:
            _save_todos(kept)
        except Exception as e:
            return f"[red]/todo clear: save failed: {e}[/]"
        return f"  cleared {before - len(kept)} done todo(s); {len(kept)} remain"

    return f"[yellow]unknown /todo subcommand `{sub}` — list | add <text> | done <N> | clear[/]"


def _cmd_focus(args, pane=None, app=None) -> str:
    """jcode-parity /focus — pin a focus file consumed by /context recall + system prompt.

    Subcommands:
      /focus                -> alias of status
      /focus status         -> show current focus
      /focus off            -> clear focus
      /focus <filename>     -> set focus path
    """
    prefs = _load_forge_prefs()
    sub = (args[0].lower() if args else "status")

    if sub == "status":
        cur = prefs.get("focus_file")
        if not cur:
            return ("  focus: (none)  "
                    "[dim]/focus <filename> to set · /focus off to clear[/]")
        exists = Path(cur).exists()
        flag = "[green]ok[/]" if exists else "[yellow]missing[/]"
        return f"  focus: {cur}  {flag}"

    if sub == "off":
        if "focus_file" in prefs:
            prefs.pop("focus_file", None)
            try:
                _save_forge_prefs(prefs)
            except Exception as e:
                return f"[red]/focus off: save failed: {e}[/]"
            return "  focus cleared"
        return "  focus already empty"

    # treat all args as the path (supports paths with spaces via shlex)
    path = " ".join(args).strip().strip('"').strip("'")
    if not path:
        return "[yellow]usage: /focus <filename> | off | status[/]"
    prefs["focus_file"] = path
    try:
        p = _save_forge_prefs(prefs)
    except Exception as e:
        return f"[red]/focus: save failed: {e}[/]"
    exists = Path(path).exists()
    flag = "[green]ok[/]" if exists else "[yellow]not yet on disk[/]"
    return f"  focus: {path}  {flag}  [dim]→ {p}[/]"


def _cmd_diff(args, pane=None, app=None) -> str:
    """jcode-parity /diff — unified diff between two resume-points.

    Usage:
      /diff                       -> diff most-recent vs second-most-recent
      /diff <rp-1> <rp-2>         -> diff two named resume-points (by filename)

    Diffs head_msg + pre_warm_reads + progress_top3 fields.
    """
    sr = _sanctum_root()
    proj = (os.environ.get("SINISTER_PROJECT_DISPLAY")
            or os.environ.get("SINISTER_PROJECT")
            or "Sinister Sanctum")
    rp_dir = sr / "_shared-memory" / "resume-points"
    seen: set[str] = set()
    candidates: list[Path] = []
    for slot in (proj, "Sanctum", "Sinister Sanctum"):
        d = rp_dir / slot
        if d.exists():
            for f in d.glob("*.json"):
                key = str(f.resolve())
                if key in seen:
                    continue
                seen.add(key)
                candidates.append(f)
    if not candidates:
        return f"[yellow]/diff: no resume-points found for {proj}[/]"
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    def _resolve(name: str) -> Path | None:
        # exact name first
        for c in candidates:
            if c.name == name:
                return c
        # stem match
        for c in candidates:
            if c.stem == name:
                return c
        return None

    if len(args) >= 2:
        a_path = _resolve(args[0])
        b_path = _resolve(args[1])
        if not a_path:
            return f"[yellow]/diff: resume-point not found: {args[0]}[/]"
        if not b_path:
            return f"[yellow]/diff: resume-point not found: {args[1]}[/]"
    else:
        if len(candidates) < 2:
            return ("[yellow]/diff: need at least 2 resume-points "
                    f"(found {len(candidates)})[/]")
        # diff older vs newer (older as 'a', newer as 'b' — so + means "added recently")
        b_path = candidates[0]
        a_path = candidates[1]

    def _load(p: Path) -> dict:
        try:
            return json.loads(p.read_text(encoding="utf-8-sig"))
        except Exception:
            return {}

    a_data = _load(a_path)
    b_data = _load(b_path)

    def _render(d: dict) -> str:
        head_msg = (d.get("git") or {}).get("head_msg", "") or d.get("head_msg", "")
        pwr = d.get("pre_warm_reads") or []
        top3 = d.get("progress_top3") or d.get("progress_summary") or []
        lines = [f"head_msg: {head_msg}", "pre_warm_reads:"]
        for r in pwr:
            lines.append(f"  - {r}")
        lines.append("progress_top3:")
        for p in top3:
            lines.append(f"  - {p}")
        return "\n".join(lines) + "\n"

    a_text = _render(a_data)
    b_text = _render(b_data)
    diff = _unified_diff_text(a_text, b_text, a_path.name, b_path.name)
    if not diff:
        return f"  [dim]no differences between {a_path.name} and {b_path.name}[/]"
    header = (f"[bold]/diff[/]  {a_path.name}  →  {b_path.name}\n"
              f"  [dim]fields: head_msg + pre_warm_reads + progress_top3[/]\n")
    return header + diff.rstrip()


def _cmd_search(args, pane=None, app=None) -> str:
    """jcode-parity /search — full-text search across _shared-memory/.

    Prefers forge_memory_bridge.recall() (BM25-ranked) when available,
    falls back to a grep-style scan. Prints top 5 matches with snippets.
    """
    if not args:
        return "[yellow]usage: /search <query>[/]"
    q = " ".join(args).strip()
    if not q:
        return "[yellow]usage: /search <query>[/]"

    # 1. Try forge_memory_bridge (BM25 if it has it).
    try:
        import forge_memory_bridge  # type: ignore
        fn = getattr(forge_memory_bridge, "recall", None)
        if callable(fn):
            try:
                results = fn(q, limit=5)
                if results:
                    seq = results if isinstance(results, list) else [results]
                    lines = [f"[bold]/search[/] {q!r}  [dim](bridge.recall — BM25)[/]"]
                    for i, r in enumerate(seq[:5], start=1):
                        snippet = str(r).replace("\n", " ")
                        if len(snippet) > 200:
                            snippet = snippet[:200] + "…"
                        lines.append(f"  {i}. {snippet}")
                    return "\n".join(lines)
            except Exception:
                pass
    except Exception:
        pass

    # 2. Fallback: grep-style scan of _shared-memory/.
    sr = _sanctum_root()
    root = sr / "_shared-memory"
    if not root.exists():
        return f"[yellow]/search: {root} does not exist[/]"
    needle = q.lower()
    hits: list[tuple[Path, int, str]] = []
    # cap walked files to keep this snappy
    walked = 0
    for ext in ("*.md", "*.json", "*.txt"):
        for p in root.rglob(ext):
            walked += 1
            if walked > 3000:
                break
            try:
                txt = p.read_text(encoding="utf-8-sig", errors="replace")
            except Exception:
                continue
            low = txt.lower()
            idx = low.find(needle)
            if idx < 0:
                continue
            # snippet: 60 chars before + 120 after
            start = max(0, idx - 60)
            end = min(len(txt), idx + 120)
            snippet = txt[start:end].replace("\n", " ")
            hits.append((p, idx, snippet))
            if len(hits) >= 50:
                break
        if len(hits) >= 50:
            break
    if not hits:
        return f"  [dim]no matches for {q!r} in {root} ({walked} files scanned)[/]"
    # rank: prefer shallow paths (lower depth) then by file mtime
    hits.sort(key=lambda h: (len(h[0].relative_to(root).parts),
                             -h[0].stat().st_mtime))
    lines = [f"[bold]/search[/] {q!r}  [dim](grep fallback — top 5 of {len(hits)})[/]"]
    for i, (p, _idx, snip) in enumerate(hits[:5], start=1):
        rel = p.relative_to(sr)
        lines.append(f"  {i}. {rel}")
        lines.append(f"     [dim]{snip.strip()}[/]")
    return "\n".join(lines)


def _cmd_export(args, pane=None, app=None) -> str:
    """jcode-parity /export — session journal / brain entries to JSONL.

    Usage:
      /export                       -> session (default), default path
      /export session [<path>]      -> latest session journal as JSONL
      /export brain   [<path>]      -> all brain entries (YAML+content) as JSONL
      /export all     [<path>]      -> both

    Default path: ~/Desktop/rkoj-export-<ts>.jsonl
    """
    kind = (args[0].lower() if args else "session")
    if kind not in ("session", "brain", "all"):
        return "[yellow]usage: /export [session|brain|all] [<path>][/]"
    explicit_path = " ".join(args[1:]).strip().strip('"').strip("'") if len(args) >= 2 else ""

    ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H%M%SZ")
    if explicit_path:
        out_path = Path(explicit_path).expanduser()
    else:
        desktop = Path.home() / "Desktop"
        if not desktop.exists():
            desktop = Path.home()
        out_path = desktop / f"rkoj-export-{ts}.jsonl"

    sr = _sanctum_root()
    records: list[dict] = []
    summary: list[str] = []

    def _add_session() -> None:
        sess_dir = sr / "_shared-memory" / "forge-memory" / "anthropic-direct-sessions"
        if not sess_dir.exists():
            summary.append("session: (no anthropic-direct-sessions dir)")
            return
        journals = sorted(sess_dir.glob("*.jsonl"),
                          key=lambda p: p.stat().st_mtime, reverse=True)
        if not journals:
            summary.append("session: (no *.jsonl journals found)")
            return
        latest = journals[0]
        n = 0
        try:
            for raw in latest.read_text(encoding="utf-8-sig", errors="replace").splitlines():
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                except Exception:
                    obj = {"raw": raw}
                if isinstance(obj, dict):
                    obj.setdefault("_export_kind", "session")
                    obj.setdefault("_export_source", latest.name)
                    records.append(obj)
                else:
                    records.append({
                        "_export_kind": "session",
                        "_export_source": latest.name,
                        "payload": obj,
                    })
                n += 1
        except Exception as e:
            summary.append(f"session: read failed: {e}")
            return
        summary.append(f"session: {n} message(s) from {latest.name}")

    def _add_brain() -> None:
        brain_dir = sr / "_shared-memory" / "knowledge"
        if not brain_dir.exists():
            summary.append("brain: (no knowledge dir)")
            return
        n = 0
        for md in sorted(brain_dir.glob("*.md")):
            try:
                content = md.read_text(encoding="utf-8-sig", errors="replace")
            except Exception:
                continue
            # naive YAML front-matter extraction (--- ... --- at file start)
            yaml_block = ""
            body = content
            if content.startswith("---\n") or content.startswith("---\r\n"):
                end = content.find("\n---", 4)
                if end > 0:
                    yaml_block = content[4:end].strip()
                    body = content[end + 4:].lstrip("\r\n")
            records.append({
                "_export_kind": "brain",
                "_export_source": md.name,
                "path": str(md.relative_to(sr)),
                "yaml": yaml_block,
                "content": body,
            })
            n += 1
        summary.append(f"brain: {n} entry/entries from knowledge/")

    if kind in ("session", "all"):
        _add_session()
    if kind in ("brain", "all"):
        _add_brain()

    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception as e:
        return f"[red]/export: write failed: {e}  [dim](path={out_path})[/]"

    lines = [f"  exported {len(records)} record(s) → {out_path}"]
    for s in summary:
        lines.append(f"  · {s}")
    return "\n".join(lines)


# ===========================================================================
# /watchdog — read-only surface onto sinister-watchdog daemon
# ===========================================================================
# Author: RKOJ-ELENO :: 2026-05-21
#
# Operator-facing read-only snapshot of the auto-online keeper.
#   /watchdog          → status (default)
#   /watchdog status   → same
#   /watchdog tail [N] → last N log lines (default 20)
#   /watchdog probe    → probe MCP servers once and print results
#
# This handler NEVER starts / stops the daemon — that's an operator action via
# the install-task.ps1 / `python -m sinister_watchdog start --bg` path. Per
# operator's "no popups" doctrine + Sanctum hard rule on lane discipline.

def _cmd_watchdog(args, pane=None, app=None) -> str:
    sub = (args[0].lower() if args else "status")
    sr = _sanctum_root()

    # Try in-process import first (zero subprocess overhead).
    try:
        sys.path.insert(0, str(sr / "tools" / "sinister-watchdog"))
        from sinister_watchdog import SanctumPaths, snapshot_status, probe_mcp_servers  # type: ignore
        paths = SanctumPaths.detect(sr)
    except Exception as exc:  # noqa: BLE001
        return f"[red]/watchdog: import failed: {exc}[/]"

    if sub in ("status", "show", ""):
        snap = snapshot_status(paths)
        running = "[green]●[/]" if snap["running"] else "[dim red]○[/]"
        out: list[str] = []
        out.append(f"[bold]sinister-watchdog[/] {running} @ {snap['ts_utc']}")
        out.append(f"  daemon       : {'running' if snap['running'] else 'NOT RUNNING'}  (pid file: {snap['pid_file']})")
        out.append(f"  agents       : {snap['agent_total']} total, [yellow]{snap['stale_count']}[/] stale")
        out.append(f"  mcp servers  : {len(snap['mcp_servers_configured'])} configured")
        if snap["mcp_servers_configured"]:
            out.append(f"                 {', '.join(snap['mcp_servers_configured'])}")
        out.append(f"  log          : {snap['log_path']}")
        out.append("")
        out.append("  [bold]heartbeats[/]")
        if not snap["heartbeats"]:
            out.append("    (none)")
        else:
            for row in snap["heartbeats"]:
                tag = "[red]STALE[/]" if row["stale"] else "[green]ok   [/]"
                out.append(f"    {tag} {row['slug']:<28} {row['age_minutes']:>6.1f} min")
        if not snap["running"]:
            out.append("")
            out.append("  [dim]start the daemon: `python -m sinister_watchdog start --bg`[/]")
            out.append("  [dim]or install scheduled task: `tools/sinister-watchdog/install-task.ps1`[/]")
        return "\n".join(out)

    if sub == "tail":
        n = 20
        if len(args) > 1:
            try:
                n = max(1, int(args[1]))
            except ValueError:
                pass
        log = paths.watchdog_log
        if not log.exists():
            return "  (no watchdog.log yet)"
        try:
            lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError as exc:
            return f"[red]/watchdog tail: read failed: {exc}[/]"
        return "\n".join(lines[-n:]) or "  (empty)"

    if sub == "probe":
        try:
            results = probe_mcp_servers(paths, timeout=6.0)
        except Exception as exc:  # noqa: BLE001
            return f"[red]/watchdog probe: failed: {exc}[/]"
        if not results:
            return "  (no MCP servers configured or .mcp.json unreadable)"
        out = [f"[bold]/watchdog probe[/] :: {len(results)} mcp servers"]
        for r in results:
            tag = "[green]ok  [/]" if r["ok"] else "[red]FAIL[/]"
            reason = r.get("reason") or "responsive"
            out.append(f"  {tag} {r['name']:<22} {reason}")
        return "\n".join(out)

    return "[yellow]usage: /watchdog [status|tail [N]|probe][/]"


# ===========================================================================
# REGISTRY — name → handler + metadata
# ===========================================================================

def _entry(handler: Callable, summary: str, category: str = "misc", detail: str = "") -> dict:
    return {"handler": handler, "summary": summary, "category": category, "detail": detail}


SLASH_COMMANDS: dict[str, dict[str, Any]] = {
    # CORE
    "help":       _entry(_cmd_help,      "show this help / detail for one command", "core"),
    "quit":       _entry(_cmd_quit,      "exit Forge",                                "core"),
    "exit":       _entry(_cmd_quit,      "alias of /quit",                            "core"),
    "version":    _entry(_cmd_version,   "show version + bundled tools",              "core"),
    "info":       _entry(_cmd_info,      "session info + token / mode / tools",       "core"),
    "context":    _entry(_cmd_context,   "full session context snapshot",             "core"),
    "git":        _entry(_cmd_git,       "git status -sb for sanctum repo",           "core"),
    "config":     _entry(_cmd_config,    "show config (/config edit to open)",        "core"),
    "changelog":  _entry(_cmd_changelog, "recent PROGRESS entries",                   "core"),

    # SESSION
    "clear":      _entry(_cmd_clear,     "clear this pane's log",                     "session"),
    "compact":    _entry(_cmd_compact,   "consolidate memory (kicks memory-consolidate.ps1)", "session"),
    "start":      _entry(_cmd_start,     "pick a project + mode and launch a session (bat-file parity)", "session"),
    "create":     _entry(_cmd_create,    "<name> [<description...>] [--parent=<dir>]  scaffold a new project", "session",
                          "Creates projects/sinister-<slug>/ with CLAUDE.md + README.md (Author: RKOJ-ELENO :: today) and appends a MANIFEST row."),
    "resume":     _entry(_cmd_resume,    "[<project>] [<N>|latest]  list projects → list points → load point", "session",
                          "No args: list every project under _shared-memory/resume-points/ with count + most-recent ts. `/resume <project>` lists that project's points; `/resume <project> <N>` loads point N."),
    "save":       _entry(_cmd_save,      "write a resume-point now",                  "session"),
    "rename":     _entry(_cmd_rename,    "name / unname session",                     "session"),
    "transcript": _entry(_cmd_transcript,"path to session transcript",                "session"),
    "todos":      _entry(_cmd_todos,     "operator-action-queue (todos)",             "session"),

    # MEMORY
    "memory":     _entry(_cmd_memory,    "on|off | search <q> | write <ns> <text> | recall <q> | list", "memory"),
    "goals":      _entry(_cmd_goals,     "show WORK-TOWARD.md goals",                 "memory"),
    "catchup":    _entry(_cmd_catchup,   "list | next — side-panel briefs for finished sessions", "session"),
    "back":       _entry(_cmd_back,      "return to previous Catch Up source session", "session"),

    # SWARM + COMMS
    "swarm":      _entry(_cmd_swarm,     "on|off | spawn N | list | dm <slug> <msg> | broadcast <msg>", "swarm"),
    "dm":         _entry(_cmd_dm,        "direct-message a sibling",                  "swarm"),
    "broadcast":  _entry(_cmd_broadcast, "fan-out to fleet",                          "swarm"),
    "agents":     _entry(_cmd_agents,    "list active agents + heartbeat ages",       "swarm"),
    "subagent":   _entry(_stub("subagent", "spawn subagent — /subagent --type <t> --model <m>",
                                "for now, use Ctrl+W picker or /swarm spawn N"), "swarm"),
    "autoreview": _entry(_stub("autoreview", "toggle auto-review of subagent output",
                                "wire up via _shared-memory/subagent-review/"), "swarm"),
    "autojudge":  _entry(_stub("autojudge", "auto-judge code quality", ""), "swarm"),

    # AUTH
    "auth":       _entry(_cmd_auth,      "11-provider auth status",                   "auth"),
    "login":      _entry(_cmd_login,     "providers | current | doctor <p> | env <p> | add <p>", "auth"),
    "account":    _entry(_cmd_account,   "alias of /auth (combined picker)",          "auth"),
    "provider":   _entry(_cmd_provider,  "list | current",                            "auth"),
    "usage":      _entry(_cmd_usage,     "token-quota / billing endpoint registry",   "auth"),
    "backup":     _entry(_cmd_backup,    "now | list | verify <date> | prune | install-task (sanctum-backup)", "system"),

    # MODEL ROUTING
    "model":      _entry(_cmd_model,     "list | current | set <id> | info <id> | providers | clear  (jcode-model parity)", "agent"),
    "jcode":      _entry(_cmd_jcode,     "sidecar launch of prebuilt jcode.exe with Sinister env injected", "agent"),
    "effort":     _entry(_cmd_effort,    "none|low|medium|high|xhigh",                "agent"),
    "fast":       _entry(_cmd_fast,      "on|off|status|default",                     "agent"),
    "transport":  _entry(_cmd_transport, "set transport mode auto|https|websocket",   "agent"),
    "alignment":  _entry(_cmd_alignment, "text alignment: status|centered|left",      "ui"),

    # SYSTEM
    "reload":     _entry(_cmd_reload,    "reload — relaunch from newer RKOJ.exe if dist is newer", "system"),
    "restart":    _entry(_cmd_restart,   "restart current session (no rebuild)",      "system"),
    "rebuild":    _entry(_cmd_rebuild,   "full PyInstaller rebuild of RKOJ.exe (background)", "system"),
    "client-reload": _entry(_cmd_client_reload, "refresh Textual pane widgets (no subprocess restart)", "system"),
    "server-reload": _entry(_cmd_server_reload, "kill + respawn agent subprocess (pane intact)",     "system"),
    "debug-visual":  _entry(_cmd_debug_visual,  "toggle SINISTER_DEBUG_VISUAL render flag", "system"),
    "mcp":        _entry(_cmd_mcp,       "list MCP servers / auto-load on call",      "system"),
    "watchdog":   _entry(_cmd_watchdog,  "status | tail [N] | probe — sinister-watchdog auto-online keeper", "system",
                          "Read-only surface onto the sinister-watchdog daemon (tools/sinister-watchdog). Status shows heartbeat ages + stale count + MCP list. Tail prints recent log lines. Probe checks every MCP server responds to `initialize`. Daemon is started separately via install-task.ps1 or `python -m sinister_watchdog start --bg`."),
    "tools":      _entry(_cmd_tools,     "list builtin tools + sinister-cli + MCP",   "system"),
    "skills":     _entry(_cmd_skills,    "list discovered skills",                    "skills"),
    "skill":      _entry(_cmd_skill,     "list | show <name> | run <name> | reload   (jcode skill-loader)", "skills"),
    "mermaid":    _entry(_cmd_mermaid,   "file <path> | render <inline> | open | backends — Mermaid diagram render",
                          "system",
                          "Wraps tools/memory-graph-render. Outputs to _shared-memory/forge-memory/mermaid-renders/<ts>.{png,html,mmd}. Backends: mermaid-rs-renderer → mmdc → html-fallback."),
    "dictate":    _entry(_cmd_dictate,   "external speech-to-text (SINISTER_DICTATE_CMD)", "system"),

    # LOOPS (improve / refactor / overnight)
    "improve":    _entry(_cmd_improve,   "autonomous code-quality loop (sub: resume)", "loop"),
    "refactor":   _entry(_cmd_refactor,  "safe refactor + review loop (sub: resume)",  "loop"),
    "overnight":  _entry(_stub("overnight", "schedule long-running improvements (cron)", ""), "loop"),
    "fix":        _entry(_stub("fix", "attempt recovery from errors",
                                "/fix re-runs the last failed turn with cleared context"), "loop"),
    "poke":       _entry(_cmd_poke,      "on|off|status — nudge model to resume incomplete todos", "loop"),
    "recover":    _entry(_stub("recover", "recover from missing tool outputs", ""), "loop"),
    "rewind":     _entry(_cmd_rewind,    "show numbered history, /rewind N to step back", "session"),
    "splitview":  _entry(_cmd_splitview, "on|off|status — mirror current chat in side panel", "ui"),
    "split":      _entry(_cmd_split,     "clone current session into a new RKOJ.exe --shell window", "ui"),
    "transfer":   _entry(_cmd_transfer,  "fresh session with compacted context + todos",      "ui"),
    "workspace":  _entry(_cmd_workspace, "status|on|off|add — niri-style workspace splits",   "ui"),
    "subscription": _entry(_cmd_subscription, "tier + monthly_cap + current_usage + renews_at (jcode/RKOJ scaffold)", "auth"),
    "unsave":     _entry(_cmd_unsave,    "remove the most recent resume-point bookmark (use --force to confirm)", "session"),

    # NEW (jcode-parity batch W): /todo /focus /diff /search /export
    "todo":       _entry(_cmd_todo,      "list | add <text> | done <N> | clear  (per-session todos)", "session",
                          "Persists to ~/.config/sinister/todos.json or %APPDATA%/sinister/todos.json. Each entry: {id, text, created, done}."),
    "focus":      _entry(_cmd_focus,     "<filename> | off | status  (focus file for /context + system prompt)", "session",
                          "Persisted to forge-prefs.json under `focus_file`. Consumed by /context recall."),
    "diff":       _entry(_cmd_diff,      "[<resume-point-1> <resume-point-2>]  (unified diff)", "session",
                          "Diffs head_msg + pre_warm_reads + progress_top3 fields. Default: latest vs previous."),
    "search":     _entry(_cmd_search,    "<query>  (full-text across _shared-memory/)", "memory",
                          "Prefers forge_memory_bridge.recall() (BM25) when available; falls back to grep-style scan."),
    "export":     _entry(_cmd_export,    "[session|brain|all] [<path>]  (export to JSONL)", "session",
                          "Default path: ~/Desktop/rkoj-export-<ts>.jsonl. Session=latest journal, brain=knowledge/*.md."),
}


# Add common aliases
for alias, target in (("?", "help"), ("h", "help"), ("q", "quit"),
                      ("v", "version"), ("st", "info")):
    if target in SLASH_COMMANDS:
        SLASH_COMMANDS[alias] = SLASH_COMMANDS[target]


def dispatch(line: str, pane=None, app=None) -> str | None:
    """Top-level slash dispatch. line includes leading `/`."""
    if not line.startswith("/"):
        return None
    body = line[1:].strip()
    if not body:
        return _cmd_help([], pane, app)
    import shlex
    try:
        tokens = shlex.split(body, posix=False)
    except ValueError:
        tokens = body.split()
    cmd = tokens[0].lower()
    args = tokens[1:]
    entry = SLASH_COMMANDS.get(cmd)
    if entry:
        try:
            return entry["handler"](args, pane, app)
        except Exception as e:
            return f"[red]/{cmd} crashed: {e}[/]"
    # Dynamic skill fallback
    skill_out = maybe_dispatch_skill(cmd, args)
    if skill_out is not None:
        return skill_out
    return f"[yellow]unknown /{cmd}. /help for the full list.[/]"
