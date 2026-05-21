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
}


def state(key: str, default: Any = None) -> Any:
    return _state.get(key, default)


def set_state(key: str, value: Any) -> None:
    _state[key] = value


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
    if args:
        target = args[0].lstrip("/").lower()
        e = SLASH_COMMANDS.get(target)
        if not e:
            return f"[yellow]unknown command /{target}[/]"
        return f"[bold]/{target}[/]  {e.get('summary', '')}\n  {e.get('detail', '(no detail)')}"
    lines = ["[bold]EVE :: Forge slash commands (jcode parity)[/]\n"]
    by_cat: dict[str, list[str]] = {}
    for name, meta in sorted(SLASH_COMMANDS.items()):
        cat = meta.get("category", "misc")
        by_cat.setdefault(cat, []).append(name)
    cat_order = ["core", "session", "memory", "swarm", "auth", "system", "agent", "ui", "loop", "skills", "misc"]
    for cat in cat_order:
        if cat not in by_cat:
            continue
        lines.append(f"[purple]{cat.upper()}[/]")
        for n in by_cat[cat]:
            s = SLASH_COMMANDS[n].get("summary", "")
            lines.append(f"  /{n:<14} {s}")
    lines.append("\n[dim]also: :dm :broadcast :host :swarm :clear (legacy `:` prefix)[/]")
    return "\n".join(lines)


def _cmd_quit(args, pane, app) -> str:
    if app is not None:
        app.exit()
    return None


def _cmd_clear(args, pane, app) -> str:
    if pane is not None and hasattr(pane, "clear_log"):
        pane.clear_log()
    return None


def _cmd_version(args, pane, app) -> str:
    try:
        from forge import __version__ as forge_v
    except Exception:
        forge_v = "?"
    sanctum_versions = []
    for pkg in ("sinister_cli", "sinister_login", "sinister_usage",
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
    # Snapshot of session: project + agent count + last 5 inbox + last 5 brain.
    sr = _sanctum_root()
    lines = ["[bold]Context snapshot[/]"]
    lines.append(f"  branch: {_git_branch(sr)}  head: {_git_head(sr)}")
    proj = os.environ.get("SINISTER_PROJECT", "?")
    inbox = sr / "_shared-memory" / "inbox" / proj
    if inbox.exists():
        items = sorted(inbox.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]
        lines.append(f"  inbox/{proj}/: {len(items)} recent")
        for it in items:
            lines.append(f"    · {it.name}")
    return "\n".join(lines)


def _cmd_git(args, pane, app) -> str:
    sr = _sanctum_root()
    try:
        r = subprocess.run(["git", "-C", str(sr), "status", "-sb"],
                           capture_output=True, text=True, timeout=3)
        return f"[bold]git[/]\n{r.stdout}"
    except Exception as e:
        return f"[red]git failed: {e}[/]"


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
    if not cfg.exists():
        return f"[yellow]no config at {cfg}[/]"
    return f"[bold]config[/]\n  path: {cfg}\n  size: {cfg.stat().st_size} bytes\n  /config edit to open"


def _cmd_changelog(args, pane, app) -> str:
    sr = _sanctum_root()
    log = sr / "_shared-memory" / "PROGRESS" / "Sinister Sanctum.md"
    if not log.exists():
        return "[yellow]no PROGRESS log found[/]"
    try:
        lines = log.read_text(encoding="utf-8").splitlines()
        out = []
        count = 0
        for ln in lines:
            if ln.startswith("## "):
                count += 1
                if count > 5:
                    break
                out.append(ln)
        return "[bold]Recent changes[/]\n" + "\n".join(out)
    except Exception as e:
        return f"[red]changelog: {e}[/]"


# ----- session commands ---------------------------------------------------

def _cmd_resume(args, pane, app) -> str:
    """jcode /resume — browse + load past resume-points."""
    sr = _sanctum_root()
    proj = os.environ.get("SINISTER_PROJECT_DISPLAY") or os.environ.get("SINISTER_PROJECT", "Sanctum")
    rp_dir = sr / "_shared-memory" / "resume-points"
    candidates = []
    for slot in (proj, "Sanctum", "Sinister Sanctum"):
        d = rp_dir / slot
        if d.exists():
            candidates += list(d.glob("*.json"))
    if not candidates:
        return f"[yellow]no resume-points found for {proj}[/]"
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    if args and args[0].isdigit():
        idx = int(args[0])
        if not (1 <= idx <= len(candidates)):
            return f"[yellow]/resume: index out of range (1-{len(candidates)})[/]"
        return _format_resume_point(candidates[idx - 1])
    if args and args[0] == "latest":
        return _format_resume_point(candidates[0])
    # list mode
    lines = [f"[bold]Resume-points for {proj}[/]  [dim](/resume <N> to load detail, /resume latest)[/]"]
    for i, p in enumerate(candidates[:15], start=1):
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
    """jcode /save [label] — bookmark current session as a resume-point."""
    sr = _sanctum_root()
    script = sr / "automations" / "resume-point-write.ps1"
    if not script.exists():
        return f"[yellow]script missing: {script}[/]"
    proj = os.environ.get("SINISTER_PROJECT_DISPLAY") or "Sanctum"
    label = " ".join(args) if args else ""
    cmd = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
           "-File", str(script), "-SanctumRoot", str(sr),
           "-ProjectKey", proj, "-AgentName", "EVE", "-Mode", "resume"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        msg = r.stdout.strip() or r.stderr.strip()
        return f"[bold]saved[/]  label={label or '(none)'}\n  {msg}"
    except Exception as e:
        return f"[red]/save failed: {e}[/]"


def _cmd_rename(args, pane, app) -> str:
    if not args:
        return "[yellow]usage: /rename <name> | --clear[/]"
    if args[0] == "--clear":
        os.environ.pop("SINISTER_SESSION_NAME", None)
        return "  session name cleared"
    name = " ".join(args)
    os.environ["SINISTER_SESSION_NAME"] = name
    return f"  session named: {name}"


def _cmd_compact(args, pane, app) -> str:
    sr = _sanctum_root()
    script = sr / "automations" / "memory-consolidate.ps1"
    if not script.exists():
        return f"[yellow]no consolidate script at {script}[/]"
    try:
        subprocess.Popen(["powershell.exe", "-NoProfile", "-WindowStyle", "Hidden",
                          "-ExecutionPolicy", "Bypass", "-File", str(script)])
        return "  consolidate kicked off in background"
    except Exception as e:
        return f"[red]/compact failed: {e}[/]"


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
    sr = _sanctum_root()
    wt = sr / "_shared-memory" / "WORK-TOWARD.md"
    if not wt.exists():
        return "[yellow]no WORK-TOWARD.md[/]"
    snippet = "\n".join(wt.read_text(encoding="utf-8").splitlines()[:30])
    return f"[bold]Goals (WORK-TOWARD.md, top 30)[/]\n{snippet}"


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

def _cmd_auth(args, pane, app) -> str:
    try:
        from sinister_login import status_all  # type: ignore
        rows = status_all()
    except Exception as e:
        return f"[red]sinister-login unavailable: {e}[/]"
    lines = ["[bold]auth status[/]"]
    for r in rows:
        mark = "[green]●[/]" if r.get("configured") else "[dim]○[/]"
        lines.append(f"  {mark} {r['slug']:<22} {r['auth']:<8} {r.get('key_env_found', '(local)')}")
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


def _cmd_model(args, pane, app) -> str:
    """jcode /model — list/switch model. We list per-provider via sinister-login."""
    if not args:
        try:
            from sinister_login import status_all  # type: ignore
            configured = [r for r in status_all() if r.get("configured")]
        except Exception:
            configured = []
        if not configured:
            return "[yellow]no provider configured. /login <provider>[/]"
        return ("[bold]models per provider[/]\n"
                + "\n".join(f"  · {r['slug']:<22} {r['display']}" for r in configured)
                + "\n  /model <slug> to switch (sets default provider)")
    target = args[0].lower()
    set_state("default_provider", target)
    return f"  default provider → {target}"


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
    return _cmd_auth(args, pane, app)


def _cmd_effort(args, pane, app) -> str:
    if not args:
        return f"  effort = {state('effort')}"
    val = args[0].lower()
    if val not in {"none", "low", "medium", "high", "xhigh"}:
        return "[yellow]/effort: none|low|medium|high|xhigh[/]"
    set_state("effort", val); return f"  effort → {val}"


def _cmd_fast(args, pane, app) -> str:
    if not args:
        return f"  fast = {state('fast_mode')}"
    val = args[0].lower()
    if val not in {"on", "off", "status", "default"}:
        return "[yellow]/fast: on|off|status|default[/]"
    if val != "status":
        set_state("fast_mode", val)
    return f"  fast → {state('fast_mode')}"


# ----- system commands ----------------------------------------------------

def _cmd_reload(args, pane, app) -> str:
    return "[yellow]/reload: requires EXE restart — close + reopen RKOJ.exe[/]"


def _cmd_restart(args, pane, app) -> str:
    if app is not None:
        app.exit()
    return "[dim]exiting; relaunch RKOJ.exe to restart[/]"


def _cmd_rebuild(args, pane, app) -> str:
    sr = _sanctum_root()
    spec = sr / "automations" / "build" / "forge-exe"
    return (f"[bold]/rebuild[/]  run from outside the running EXE:\n"
            f"  cd {spec}\n"
            f"  pyinstaller --clean --noconfirm RKOJ.spec\n"
            f"  cp dist/RKOJ.exe \"C:/Users/Zonia/Desktop/RKOJ.exe\"")


def _cmd_mcp(args, pane, app) -> str:
    """List + lazy-load MCP servers. Sinister fleet MCPs:
    ruflo (28-tool agentdb), vault (operator's 1TB store), claude-Gmail/Calendar/Drive."""
    sr = _sanctum_root()
    mcp_cfg = Path.home() / ".claude" / ".mcp.json"
    lines = ["[bold]MCP servers[/]"]
    if mcp_cfg.exists():
        try:
            cfg = json.loads(mcp_cfg.read_text(encoding="utf-8"))
            servers = cfg.get("mcpServers", {})
            for name in sorted(servers):
                lines.append(f"  · {name}")
        except Exception as e:
            lines.append(f"  [red]parse error: {e}[/]")
    else:
        lines.append(f"  [dim]no ~/.claude/.mcp.json — MCP servers are loaded by Claude Code at session start[/]")
    lines.append("\n[dim]MCPs auto-load lazily when /memory, /swarm, vault commands fire.[/]")
    return "\n".join(lines)


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


def _cmd_debug_visual(args, pane, app) -> str:
    return "[yellow]/debug-visual: Textual reactive inspector. Run `textual console` in another window first.[/]"


# ----- session-loop commands (delegated to siblings) ---------------------

def _stub(name: str, summary: str, detail: str = "") -> Callable:
    def _h(args, pane, app):
        return f"[yellow]/{name}[/]: {summary}\n  [dim]{detail or 'roadmap item — wire up in next session'}[/]"
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
    """If `name` is a discovered skill, invoke it (return printout) else None."""
    for root in (Path.home() / ".claude" / "skills",
                 Path.home() / ".claude" / "plugins",
                 _sanctum_root() / ".claude" / "skills",
                 _sanctum_root() / "skills"):
        cand = root / name
        if cand.is_dir():
            md = cand / "SKILL.md"
            if md.exists():
                try:
                    txt = md.read_text(encoding="utf-8")[:1500]
                    return f"[bold]Skill[/] /{name}\n{txt}\n[dim]…[/]"
                except OSError:
                    pass
            return f"[bold]Skill[/] /{name}  [dim]{cand}[/]\n  [yellow](no SKILL.md — opening dir){RESET if False else ''}"
    return None


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
    "resume":     _entry(_cmd_resume,    "browse + read past resume-points",          "session"),
    "save":       _entry(_cmd_save,      "write a resume-point now",                  "session"),
    "rename":     _entry(_cmd_rename,    "name / unname session",                     "session"),
    "transcript": _entry(_cmd_transcript,"path to session transcript",                "session"),
    "todos":      _entry(_cmd_todos,     "operator-action-queue (todos)",             "session"),

    # MEMORY
    "memory":     _entry(_cmd_memory,    "on|off | search <q> | write <ns> <text> | recall <q> | list", "memory"),
    "goals":      _entry(_cmd_goals,     "show WORK-TOWARD.md goals",                 "memory"),
    "catchup":    _entry(_stub("catchup", "side-panel briefs for finished sessions",
                                "reads _shared-memory/cross-agent/ filtered by project"), "session"),
    "back":       _entry(_stub("back", "return to previous Catch Up session", ""), "session"),

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

    # MODEL ROUTING
    "model":      _entry(_cmd_model,     "list models / switch default provider",      "agent"),
    "effort":     _entry(_cmd_effort,    "none|low|medium|high|xhigh",                "agent"),
    "fast":       _entry(_cmd_fast,      "on|off|status|default",                     "agent"),
    "transport":  _entry(_stub("transport", "set transport mode auto|https|websocket",
                                "Sinister fleet uses Claude Code CLI; transport is fixed."), "agent"),
    "alignment":  _entry(_stub("alignment", "text alignment: status|centered|left", ""), "ui"),

    # SYSTEM
    "reload":     _entry(_cmd_reload,    "reload — restart RKOJ.exe",                 "system"),
    "restart":    _entry(_cmd_restart,   "restart with current binary",               "system"),
    "rebuild":    _entry(_cmd_rebuild,   "full rebuild — instructions",               "system"),
    "client-reload": _entry(_stub("client-reload", "remote-only", ""), "system"),
    "server-reload": _entry(_stub("server-reload", "remote-only", ""), "system"),
    "debug-visual":  _entry(_cmd_debug_visual, "enable Textual reactive inspector",   "system"),
    "mcp":        _entry(_cmd_mcp,       "list MCP servers / auto-load on call",      "system"),
    "tools":      _entry(_cmd_tools,     "list builtin tools + sinister-cli + MCP",   "system"),
    "skills":     _entry(_cmd_skills,    "list discovered skills",                    "skills"),
    "dictate":    _entry(_stub("dictate", "external speech-to-text",
                                "configure STT command in agent-prefs.json"), "system"),

    # LOOPS (improve / refactor / overnight)
    "improve":    _entry(_stub("improve", "autonomous code-quality loop",
                                "wire up via Sanctum auto-mode + per-project EXACT-INSTRUCTIONS"), "loop"),
    "refactor":   _entry(_stub("refactor", "safe refactor + review loop", ""), "loop"),
    "overnight":  _entry(_stub("overnight", "schedule long-running improvements (cron)", ""), "loop"),
    "fix":        _entry(_stub("fix", "attempt recovery from errors",
                                "/fix re-runs the last failed turn with cleared context"), "loop"),
    "poke":       _entry(_stub("poke", "nudge model to resume incomplete todos", ""), "loop"),
    "recover":    _entry(_stub("recover", "recover from missing tool outputs", ""), "loop"),
    "rewind":     _entry(_stub("rewind", "show numbered history, /rewind N to step back", ""), "session"),
    "splitview":  _entry(_stub("splitview", "mirror current chat in side panel", ""), "ui"),
    "split":      _entry(_stub("split", "clone session into new window", ""), "ui"),
    "transfer":   _entry(_stub("transfer", "fresh session with compacted context + todos", ""), "ui"),
    "workspace":  _entry(_stub("workspace", "Niri-style workspace splits",
                                "Forge already has scrollable columns by default (PH18)"), "ui"),
    "subscription": _entry(_stub("subscription", "Sinister LLC subscription scaffold", ""), "auth"),
    "unsave":     _entry(_stub("unsave", "remove bookmark", ""), "session"),
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
