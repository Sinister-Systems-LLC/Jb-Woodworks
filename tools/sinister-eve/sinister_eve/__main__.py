# Author: RKOJ-ELENO :: 2026-05-23
"""sinister-eve REPL — jcode-parity standalone CLI with EVE persona.

v0.2.0
- Proper UUID format (was sending dashless hex → claude rejected as invalid)
- jcode-style centered banner with EVE skull ASCII + version block
- Numbered N> prompts like jcode (1>, 2>, ...)
- Default model = claude-opus-4-7 (Opus 4.7)
- /create <project>  spawn a new session bound to a Sanctum project
                     (loads project resume_dir + persona context)
- /resume            interactive picker from _shared-memory/resume-points/
- /memory <query>    BM25 recall via tools/forge-memory-bridge (if installed)
- /sandbox           list active permission-skip flags (operator-binding)
- /projects          list all known Sanctum projects
- /model <alias>     switch model for next turn
- /skills            list skills with frontmatter (jcode parity)

Usage:
    sinister-eve                    interactive REPL (claude-opus-4-7 default)
    sinister-eve -p "hi"            one-shot turn, prints reply, exits
    sinister-eve --resume <uuid>    resume a saved session
    sinister-eve --create panel     start in project context
    sinister-eve --model haiku      override default Opus 4.7
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import IO

# v0.1.0 — inlined (was `from . import __version__`) so PyInstaller's
# top-level-script entry works without a parent package.
__version__ = "0.2.0"

# v0.2.0 — default to Opus 4.7 per operator directive. Can override with
# --model or /model in the REPL. Aliases: opus / haiku / sonnet / haiku-fast.
_DEFAULT_MODEL = "claude-opus-4-7"

# v0.2.0 — Sanctum repo root. Used for projects.json, resume-points,
# skills, brain-entry roots. Override with SINISTER_SANCTUM env var.
_SANCTUM_ROOT = Path(os.environ.get("SINISTER_SANCTUM", r"D:\Sinister Sanctum"))


# ── ANSI color helpers ─────────────────────────────────────────────────
# v0.2.0 — force UTF-8 on stdout so Unicode (▸ ● ░ █ 💭) renders in
# Windows cmd.exe / PowerShell which default to cp1252.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
_ENABLE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
if sys.platform == "win32" and _ENABLE_COLOR:
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        # Also flip console output codepage to UTF-8 (65001) so the
        # terminal itself accepts the bytes we send.
        kernel32.SetConsoleOutputCP(65001)
    except Exception:
        pass


def _c(code: str, txt: str) -> str:
    if not _ENABLE_COLOR:
        return txt
    return f"\x1b[{code}m{txt}\x1b[0m"


PURPLE = lambda s: _c("38;2;191;90;242", s)         # noqa: E731
PURPLE_BOLD = lambda s: _c("1;38;2;191;90;242", s)  # noqa: E731
PURPLE_DIM = lambda s: _c("38;2;120;60;160", s)     # noqa: E731 — banner art
DIM = lambda s: _c("2", s)                          # noqa: E731
GOLD_BOLD = lambda s: _c("1;38;2;240;160;32", s)    # noqa: E731 — tool headers
CYAN = lambda s: _c("36", s)                        # noqa: E731 — thinking
GRAY = lambda s: _c("38;2;140;140;145", s)          # noqa: E731 — tool results
RED = lambda s: _c("31", s)                         # noqa: E731 — errors
YELLOW = lambda s: _c("33", s)                      # noqa: E731 — warnings
GREEN = lambda s: _c("32", s)                       # noqa: E731 — providers


# ── EVE persona prelude ────────────────────────────────────────────────
_EVE_PERSONA = (
    "You are EVE — Sinister Sanctum's orchestration agent. "
    "Self-reference as EVE (never 'Claude' or 'the AI'). "
    "Authorship for any new file you create: `Author: RKOJ-ELENO :: <today>`. "
    "Working repo: D:\\Sinister Sanctum. "
    "You have full file/shell/MCP tool access via the operator's claude CLI."
)

_TOKEN_WARN_THRESHOLD = 100_000

# Sanctioned operator bypasses (from sanctioned-bypasses-doctrine brain entry)
_SANDBOX_FLAGS = [
    "--dangerously-skip-permissions  (claude CLI: tool auto-approve)",
    "MCP full access                  (~/.claude/.mcp.json all servers loaded)",
    "schtask hidden                   (RKOJ/Vault auto-start, no UAC popup)",
    "taskkill /F                      (relaunch.bat kills running EXEs)",
    "auto-push main                   (commits → upstream without confirm)",
    "CREATE_NO_WINDOW                 (PowerShell subprocess hides console)",
    "mklink /J                        (junction targets across drives)",
    "D:/sinister-vault/              (1 TB collaborative auth store)",
]

# v0.2.0 — EVE skull mascot (parity with RKOJ's mascot.svg, ASCII).
_EVE_MASCOT = r"""
                    ╔══════╗
                    ║ ◣◣◣◣ ║
                    ║ ▓  ▓ ║
                    ║▒▒▒▒▒▒║
                    ║  ▽▽  ║
                    ╚══════╝
                       ║║
                       ║║
                   ╔═══╩╩═══╗
                   ║  EVE   ║
                   ╚════════╝
"""


_SLASH_HELP = """
Slash commands (sinister-eve REPL):
  /help                show this list
  /create <project>    start fresh session bound to a Sanctum project
  /resume              interactive picker of saved sessions
  /projects            list all Sanctum projects (projects.json)
  /model <alias>       switch model (opus / haiku / sonnet / claude-opus-4-7)
  /memory <query>      BM25 recall via forge-memory-bridge (if installed)
  /sandbox             show active permission-skip flags
  /skills              list installed skills (parses YAML frontmatter)
  /skill <name>        load a skill file as the next turn
  /clear               clear terminal scrollback
  /cancel              kill the in-flight turn (Ctrl+C also works)
  /cost                cumulative spend + tokens
  /budget              token-budget gauge vs 100k warn threshold
  /session             print session uuid (for resume from another shell)
  /save                write session uuid + turns to ./eve-session-<uuid>.json
  /persona             print EVE identity (uuid, model, project, working dir)
  /summarize           ask EVE for a TL;DR of this conversation
  /history             last 10 turns (truncated)
  /quit                exit (also Ctrl+D)

Anything else is sent to EVE as a turn.
"""


def _term_width() -> int:
    try:
        return max(60, min(140, shutil.get_terminal_size((100, 25)).columns))
    except Exception:
        return 100


def _center(line: str, width: int) -> str:
    """Center an ANSI-colored line by stripping color codes for length calc."""
    import re
    visible = re.sub(r"\x1b\[[0-9;]*m", "", line)
    pad = max(0, (width - len(visible)) // 2)
    return " " * pad + line


def _find_claude() -> str:
    found = shutil.which("claude")
    if not found:
        sys.stderr.write(RED("error: claude CLI not on PATH.\n"))
        sys.stderr.write("  install: https://claude.ai/download (CLI bundle)\n")
        sys.exit(1)
    return found


def _load_projects() -> list[dict]:
    """Read automations/session-templates/projects.json. Returns empty list
    if missing (operator may run sinister-eve from outside the Sanctum repo)."""
    fp = _SANCTUM_ROOT / "automations" / "session-templates" / "projects.json"
    if not fp.exists():
        return []
    try:
        data = json.loads(fp.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "projects" in data:
            return data["projects"]
    except Exception:
        pass
    return []


def _scan_resume_points() -> list[dict]:
    """Walk _shared-memory/resume-points/*/*.json and return latest entry
    per unique session_uuid (newest saved_at wins)."""
    root = _SANCTUM_ROOT / "_shared-memory" / "resume-points"
    if not root.exists():
        return []
    latest: dict[str, dict] = {}
    for proj_dir in root.iterdir():
        if not proj_dir.is_dir():
            continue
        for fp in proj_dir.glob("*.json"):
            try:
                d = json.loads(fp.read_text(encoding="utf-8"))
            except Exception:
                continue
            suid = d.get("session_uuid") or ""
            if not suid:
                continue
            ts = d.get("saved_at", "")
            if suid not in latest or ts > latest[suid].get("saved_at", ""):
                d["_filepath"] = str(fp)
                d["_project_dir"] = proj_dir.name
                latest[suid] = d
    return sorted(latest.values(), key=lambda x: x.get("saved_at", ""), reverse=True)


# ── Stream renderer (NDJSON from claude --output-format stream-json) ───
class StreamRenderer:
    def __init__(self) -> None:
        self._buf = ""
        self.total_cost = 0.0
        self.total_in = 0
        self.total_out = 0
        self.reply_text_buf: list[str] = []
        self.tools_run: list[str] = []
        self._reply_started = False
        self._token_warning_shown = False

    def feed(self, chunk: str) -> None:
        self._buf += chunk
        while "\n" in self._buf:
            line, _, self._buf = self._buf.partition("\n")
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except Exception:
                continue
            self._handle(ev)

    def _handle(self, ev: dict) -> None:
        t = ev.get("type")
        if t == "content_block_delta":
            delta = ev.get("delta", {})
            dt = delta.get("type")
            if dt == "text_delta":
                if not self._reply_started:
                    print(PURPLE_BOLD("\n● EVE  "), end="", flush=True)
                    self._reply_started = True
                text = delta.get("text", "")
                self.reply_text_buf.append(text)
                sys.stdout.write(text)
                sys.stdout.flush()
            elif dt == "thinking_delta":
                think = delta.get("thinking", "")
                if think:
                    head = think.replace("\n", " ")[:80]
                    sys.stdout.write("\r" + CYAN(f"💭 {head}") + "\x1b[K")
                    sys.stdout.flush()
        elif t == "content_block_start":
            block = ev.get("content_block", {})
            if block.get("type") == "tool_use":
                name = block.get("name", "?")
                self.tools_run.append(name)
                print(GOLD_BOLD(f"\n● {name}"), end="", flush=True)
                inp = block.get("input", {})
                if inp:
                    preview = json.dumps(inp)[:80].replace("\n", " ")
                    print(GRAY(f"  {preview}"), flush=True)
                else:
                    print(flush=True)
        elif t == "user":
            msg = ev.get("message", {})
            content = msg.get("content", [])
            for blk in content:
                if blk.get("type") == "tool_result":
                    raw = blk.get("content", "")
                    if isinstance(raw, list):
                        raw = "".join(b.get("text", "") for b in raw if b.get("type") == "text")
                    raw_s = str(raw)
                    if raw_s:
                        preview = raw_s.replace("\n", " ")[:80]
                        print(GRAY(f"  ✓ {preview}"))
        elif t == "result":
            usage = ev.get("usage", {})
            in_tok = usage.get("input_tokens", 0) or 0
            out_tok = usage.get("output_tokens", 0) or 0
            cache_read = usage.get("cache_read_input_tokens", 0) or 0
            cost = ev.get("total_cost_usd", 0) or 0
            dur = (ev.get("duration_ms", 0) or 0) / 1000
            self.total_cost += float(cost)
            self.total_in += int(in_tok)
            self.total_out += int(out_tok)
            tools_note = (
                f" · tools: {', '.join(self.tools_run)}"
                if self.tools_run else ""
            )
            print(DIM(
                f"\n  ▸ {in_tok:,} in + {out_tok:,} out tokens "
                f"(cache_read={cache_read:,}) · ${cost:.4f} · {dur:.1f}s{tools_note}"
            ))
            combined = self.total_in + self.total_out
            if not self._token_warning_shown and combined >= _TOKEN_WARN_THRESHOLD:
                self._token_warning_shown = True
                print(YELLOW(
                    f"  ⚠ token budget: {combined:,} cumulative tokens "
                    f"(≥{_TOKEN_WARN_THRESHOLD:,}). Consider /summarize."
                ))

    def reset_turn(self) -> None:
        self._buf = ""
        self.reply_text_buf = []
        self.tools_run = []
        self._reply_started = False


def _spawn_turn(claude: str, session_uuid: str, first_turn: bool,
                text: str, model: str | None,
                renderer: StreamRenderer,
                persona_extra: str = "") -> int:
    """Spawn one claude turn, stream stdout into renderer, return exit code."""
    args = [
        claude,
        "--dangerously-skip-permissions",  # sanctioned bypass
        "--output-format", "stream-json",
        "--include-partial-messages",
        "--verbose",
    ]
    if model:
        args += ["--model", model]
    if first_turn:
        full_persona = _EVE_PERSONA
        if persona_extra:
            full_persona = full_persona + "\n\n" + persona_extra
        args += [
            "--session-id", session_uuid,
            "--system-prompt", full_persona,
            "-p", text,
        ]
    else:
        args += ["--resume", session_uuid, "-p", text]
    proc = subprocess.Popen(
        args,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        encoding="utf-8",
        errors="replace",
    )
    stderr_buf: list[str] = []
    def _drain_stderr(fh: IO[str]) -> None:
        for line in fh:
            stderr_buf.append(line.rstrip("\n"))
    t = threading.Thread(target=_drain_stderr, args=(proc.stderr,), daemon=True)
    t.start()
    try:
        assert proc.stdout is not None
        for line in proc.stdout:
            renderer.feed(line)
    except KeyboardInterrupt:
        print(RED("\n[/cancel] killed by Ctrl+C"))
        proc.kill()
        proc.wait(timeout=2)
        return 130
    proc.wait()
    t.join(timeout=1)
    benign = ("Warning: no stdin data received", "stream-json events emitted")
    for line in stderr_buf:
        if line.strip() and not any(b in line for b in benign):
            print(RED(f"  [stderr] {line}"))
    return proc.returncode or 0


# ── jcode-style centered startup banner ────────────────────────────────
def _print_banner(session_uuid: str, model: str, project: dict | None) -> None:
    """v0.2.0 — jcode-parity centered banner with EVE skull + info block.
    Matches the jcode/pagoda Owl layout the operator screenshotted."""
    w = _term_width()
    # ASCII mascot
    for line in _EVE_MASCOT.split("\n"):
        if line.strip():
            print(_center(PURPLE(line), w))
    print()
    # Title
    title = f"sinister-eve · v{__version__}"
    print(_center(PURPLE_BOLD(title), w))
    print(_center(DIM("EVE on Sinister Sanctum (jcode-parity REPL)"), w))
    print()
    # Info block (jcode "client/server/model" pattern)
    lines = []
    lines.append(("server:", PURPLE_BOLD("Sinister Sanctum")))
    lines.append(("client:", PURPLE_BOLD("EVE")))
    lines.append(("model:",  PURPLE(model)))
    lines.append(("session:", DIM(session_uuid)))
    if project:
        lines.append(("project:", GREEN(project.get("display") or project.get("key") or "?")))
        rd = project.get("resume_dir") or ""
        if rd:
            lines.append(("resume_dir:", DIM(rd)))
    cwd = Path.cwd()
    lines.append(("working dir:", DIM(str(cwd))))
    # Providers row (jcode shows "anthropic(oauth) ● openrouter ● openai(key)")
    providers = [
        GREEN("● anthropic"),
        DIM("○ openrouter"),
        DIM("○ openai"),
    ]
    lines.append(("providers:", " ".join(providers)))
    # MCP servers — read ~/.claude/.mcp.json if present
    mcp_path = Path.home() / ".claude" / ".mcp.json"
    if mcp_path.exists():
        try:
            mcp = json.loads(mcp_path.read_text(encoding="utf-8"))
            srv = list((mcp.get("mcpServers") or {}).keys())
            mcp_str = f"{len(srv)} loaded ({', '.join(srv[:3])}{'...' if len(srv) > 3 else ''})"
        except Exception:
            mcp_str = "config present"
    else:
        mcp_str = "(none)"
    lines.append(("mcp:", PURPLE(mcp_str)))
    # Right-align labels (jcode uses colon-aligned columns)
    label_w = max(len(lbl) for lbl, _ in lines)
    for lbl, val in lines:
        composed = f"{lbl.rjust(label_w)} {val}"
        print(_center(composed, w))
    print()
    print(_center(DIM("/help for slash commands · /quit or Ctrl+D to exit"), w))
    print()


def _print_projects(projects: list[dict]) -> None:
    if not projects:
        print(YELLOW("[/projects] no projects.json found at "
                     f"{_SANCTUM_ROOT / 'automations' / 'session-templates' / 'projects.json'}"))
        return
    print(PURPLE_BOLD(f"[/projects] {len(projects)} Sanctum project(s):"))
    for p in projects:
        key = p.get("key") or "?"
        display = p.get("display") or key
        print(f"  {GREEN(key.ljust(20))}  {display}")


def _pick_resume() -> str | None:
    """Interactive picker. Returns session_uuid to resume, or None to abort."""
    entries = _scan_resume_points()
    if not entries:
        print(YELLOW("[/resume] no saved sessions at "
                     f"{_SANCTUM_ROOT / '_shared-memory' / 'resume-points'}"))
        return None
    print(PURPLE_BOLD(f"[/resume] {len(entries)} saved session(s) "
                     f"(newest first, max 20 shown):"))
    show = entries[:20]
    for i, d in enumerate(show, 1):
        ts = (d.get("saved_at") or "")[:19]
        proj = d.get("_project_dir") or d.get("project_display") or "?"
        agent = d.get("agent_name") or "?"
        suid = (d.get("session_uuid") or "")[:8]
        turns = len([t for t in (d.get("turns") or []) if t.get("user")])
        cost = d.get("total_cost_usd", 0) or 0
        print(f"  {GREEN(f'{i:2d}.')} {ts}  {proj:20s}  {agent:20s}  "
              f"{turns:2d}t  ${cost:.4f}  {DIM(suid)}")
    print()
    try:
        sel = input(PURPLE("pick #: ")).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return None
    if not sel or not sel.isdigit():
        print(YELLOW("[/resume] cancelled"))
        return None
    idx = int(sel) - 1
    if idx < 0 or idx >= len(show):
        print(RED(f"[/resume] out of range 1..{len(show)}"))
        return None
    return show[idx].get("session_uuid") or None


def _memory_query(query: str) -> None:
    """v0.2.0 — best-effort BM25 recall via forge-memory-bridge."""
    # Try to invoke forge-memory-bridge if installed.
    candidates = [
        ["python", "-m", "forge_memory_bridge", "search", query],
        ["python", "-m", "forge_memory_bridge", query],
        ["forge-memory-bridge", "search", query],
    ]
    for cmd in candidates:
        if not shutil.which(cmd[0]) and cmd[0] != "python":
            continue
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            if r.returncode == 0 and r.stdout.strip():
                print(PURPLE_BOLD(f"[/memory] {query!r}"))
                print(r.stdout.rstrip())
                return
        except Exception:
            continue
    # Fallback: grep brain entries for the query.
    brain = _SANCTUM_ROOT / "_shared-memory" / "knowledge"
    if not brain.exists():
        print(YELLOW("[/memory] forge-memory-bridge not installed; "
                     "no brain dir to fall back to"))
        return
    matches: list[tuple[Path, str]] = []
    q_lower = query.lower()
    for fp in brain.glob("*.md"):
        try:
            txt = fp.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if q_lower in txt.lower():
            # Find the first line containing the query as preview
            for ln in txt.split("\n"):
                if q_lower in ln.lower():
                    matches.append((fp, ln.strip()[:80]))
                    break
        if len(matches) >= 10:
            break
    if not matches:
        print(YELLOW(f"[/memory] no matches for {query!r} in brain ({brain})"))
        return
    print(PURPLE_BOLD(f"[/memory] {len(matches)} brain hit(s) for {query!r}:"))
    for fp, preview in matches:
        print(f"  {GREEN(fp.name)}: {preview}")


def _handle_slash(cmd: str, renderer: StreamRenderer,
                  session_uuid: str, turns: list[dict],
                  state: dict) -> bool | str:
    """Return True to stay in REPL, 'quit' to exit, or a string to forward
    as the next turn text (for /summarize, /skill, etc).
    `state` is a mutable dict carrying {model, project, turn_no} so slashes
    can mutate them in-place."""
    parts = cmd.split(None, 1)
    head = parts[0].lower()
    rest = parts[1].strip() if len(parts) > 1 else ""

    if head in ("/quit", "/exit"):
        return "quit"
    if head == "/help":
        print(_SLASH_HELP)
        return True
    if head == "/clear":
        if _ENABLE_COLOR:
            print("\x1b[2J\x1b[H", end="")
        return True
    if head == "/cancel":
        print(YELLOW("[/cancel] no in-flight turn (REPL idle)"))
        return True
    if head == "/cost":
        print(f"[/cost]  in: {renderer.total_in:,}  out: {renderer.total_out:,}  "
              f"total: ${renderer.total_cost:.4f}")
        return True
    if head == "/budget":
        combined = renderer.total_in + renderer.total_out
        pct = (combined / _TOKEN_WARN_THRESHOLD) * 100 if _TOKEN_WARN_THRESHOLD else 0
        bar_w = 30
        filled = min(bar_w, int(bar_w * combined / _TOKEN_WARN_THRESHOLD))
        bar = "█" * filled + "░" * (bar_w - filled)
        print(f"[/budget]  {bar}  {combined:,} / {_TOKEN_WARN_THRESHOLD:,} ({pct:.0f}%)")
        return True
    if head == "/session":
        print(f"[/session] {session_uuid}")
        print(f"  resume: sinister-eve --resume {session_uuid}")
        print(f"  or via claude: claude -r {session_uuid} -p 'message'")
        return True
    if head == "/save":
        fp = Path.cwd() / f"eve-session-{session_uuid[:8]}.json"
        try:
            fp.write_text(json.dumps({
                "session_uuid": session_uuid,
                "model": state.get("model"),
                "project": state.get("project"),
                "turns": turns,
                "total_cost_usd": renderer.total_cost,
                "total_in_tokens": renderer.total_in,
                "total_out_tokens": renderer.total_out,
                "saved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }, indent=2), encoding="utf-8")
            print(f"[/save] wrote {fp}")
        except Exception as exc:
            print(RED(f"[/save] failed: {exc}"))
        return True
    if head == "/persona":
        print(f"[/persona]")
        print(f"  identity   : EVE")
        print(f"  session    : {session_uuid}")
        print(f"  model      : {state.get('model')}")
        print(f"  project    : {(state.get('project') or {}).get('display', '(none)')}")
        print(f"  authorship : RKOJ-ELENO")
        print(f"  working dir: {Path.cwd()}")
        return True
    if head == "/summarize":
        return (
            "Give me a TL;DR of our conversation so far. Format:\n"
            "1) goal: what are we trying to do? (1 sentence)\n"
            "2) working: what's confirmed working? (2-3 bullets)\n"
            "3) blocked: what's stuck or unclear? (2-3 bullets)\n"
            "4) next: what should we try next? (1-3 bullets)\n"
            "Be concrete — reference specific files / errors / decisions."
        )
    if head == "/history":
        if not turns:
            print("[/history] no turns yet")
            return True
        print(f"[/history] {len(turns)} turn(s):")
        for i, t in enumerate(turns[-10:], start=max(1, len(turns) - 9)):
            u = (t.get("user") or "").strip().replace("\n", " ")[:60]
            a = (t.get("assistant") or "").strip().replace("\n", " ")[:60]
            print(f"  {i:2d}. >> {u}")
            print(f"      << {a}")
        return True
    if head == "/projects":
        _print_projects(_load_projects())
        return True
    if head == "/create":
        if not rest:
            print("[/create] usage: /create <project-key>  (try /projects to list)")
            return True
        projects = _load_projects()
        match = next((p for p in projects if p.get("key", "").lower() == rest.lower()
                      or (p.get("display") or "").lower() == rest.lower()), None)
        if not match:
            print(RED(f"[/create] no project '{rest}'. Try /projects."))
            return True
        state["project"] = match
        # Reset session — operator wants a NEW session bound to this project.
        state["new_session_uuid"] = str(uuid.uuid4())
        state["new_first_turn"] = True
        state["new_persona_extra"] = (
            f"You are working on project '{match.get('display', rest)}'. "
            f"Project resume_dir: {match.get('resume_dir', '?')}. "
            f"Project key for branches: {match.get('key', rest)}. "
        )
        print(GREEN(f"[/create] bound to project '{match.get('display')}' "
                    f"(new session {state['new_session_uuid'][:8]}…)"))
        return True
    if head == "/resume":
        new_uuid = _pick_resume()
        if new_uuid:
            state["new_session_uuid"] = new_uuid
            state["new_first_turn"] = False  # session exists server-side
            print(GREEN(f"[/resume] resuming {new_uuid[:8]}… on next turn"))
        return True
    if head == "/model":
        if not rest:
            print(f"[/model] current: {state.get('model')}. Aliases: opus, haiku, "
                  f"sonnet, claude-opus-4-7, claude-haiku-4-5-20251001")
            return True
        state["model"] = rest
        print(GREEN(f"[/model] switched to '{rest}' (applies to next turn)"))
        return True
    if head == "/memory":
        if not rest:
            print("[/memory] usage: /memory <query>")
            return True
        _memory_query(rest)
        return True
    if head == "/sandbox":
        print(PURPLE_BOLD("[/sandbox] sanctioned permission-skips active:"))
        for line in _SANDBOX_FLAGS:
            print(f"  {GREEN('●')} {line}")
        return True
    if head == "/skills":
        roots = [
            _SANCTUM_ROOT / "skills",
            Path.home() / ".sinister" / "skills",
            Path.home() / ".claude" / "skills",
        ]
        found = []
        for r in roots:
            if not r.exists():
                continue
            for p in list(r.glob("*.md")) + list(r.glob("*/SKILL.md")):
                found.append(p)
        if not found:
            print(YELLOW(f"[/skills] no .md skills in {', '.join(str(r) for r in roots)}"))
            return True
        print(PURPLE_BOLD(f"[/skills] {len(found)} skill(s):"))
        for fp in found[:30]:
            short = fp.stem if fp.name != "SKILL.md" else fp.parent.name
            # Quick frontmatter peek for description
            desc = ""
            try:
                head_text = fp.read_text(encoding="utf-8", errors="ignore")[:2000]
                if head_text.startswith("---"):
                    for ln in head_text.split("\n")[1:30]:
                        if ln.strip() == "---":
                            break
                        if ln.lower().startswith("description:"):
                            desc = ln.split(":", 1)[1].strip().strip('"\'')[:60]
                            break
            except Exception:
                pass
            tail = f" — {desc}" if desc else ""
            print(f"  /skill {GREEN(short)}{tail}")
        return True
    if head == "/skill":
        if not rest:
            print("[/skill] usage: /skill <name>  (try /skills to list)")
            return True
        roots = [
            _SANCTUM_ROOT / "skills",
            Path.home() / ".sinister" / "skills",
            Path.home() / ".claude" / "skills",
        ]
        for r in roots:
            for cand in (r / f"{rest}.md", r / rest / "SKILL.md"):
                if cand.exists():
                    try:
                        text = cand.read_text(encoding="utf-8")
                    except Exception as exc:
                        print(RED(f"[/skill] read failed: {exc}"))
                        return True
                    # Strip frontmatter
                    if text.startswith("---"):
                        lines = text.split("\n")
                        for i in range(1, min(40, len(lines))):
                            if lines[i].strip() == "---":
                                text = "\n".join(lines[i+1:]).lstrip()
                                break
                    print(GREEN(f"[/skill] loaded {cand.name} ({len(text):,} chars)"))
                    return text  # forward as next turn
        print(RED(f"[/skill] no skill '{rest}'. Try /skills."))
        return True

    print(YELLOW(f"unknown slash command: {head}"))
    return True


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    p = argparse.ArgumentParser(
        prog="sinister-eve",
        description="jcode-parity standalone EVE CLI REPL",
    )
    p.add_argument("-p", "--prompt", help="one-shot turn; prints reply + exits")
    p.add_argument("--resume", metavar="UUID", help="resume a saved session by uuid")
    p.add_argument("--create", metavar="PROJECT", help="start in a Sanctum project context")
    p.add_argument("--model", default=_DEFAULT_MODEL,
                   help=f"model alias (default: {_DEFAULT_MODEL})")
    p.add_argument("-V", "--version", action="store_true", help="print version + exit")
    args = p.parse_args(argv)

    if args.version:
        print(f"sinister-eve {__version__}  (RKOJ-ELENO · default model {_DEFAULT_MODEL})")
        return 0

    claude = _find_claude()
    # v0.2.0 BUG FIX — claude requires proper UUID format with dashes;
    # `.hex` produced a 32-char dashless string which it rejected as
    # "Invalid session ID. Must be a valid UUID."
    session_uuid = args.resume or str(uuid.uuid4())
    first_turn = not args.resume
    renderer = StreamRenderer()
    turns: list[dict] = []

    # v0.2.0 — REPL state mutable by slash commands.
    project: dict | None = None
    if args.create:
        projects = _load_projects()
        match = next((p for p in projects if p.get("key", "").lower() == args.create.lower()
                      or (p.get("display") or "").lower() == args.create.lower()), None)
        if match:
            project = match
        else:
            print(YELLOW(f"[--create] no project '{args.create}'; ignoring"))

    state: dict = {
        "model": args.model,
        "project": project,
        "turn_no": 0,
    }
    persona_extra = ""
    if project:
        persona_extra = (
            f"You are working on project '{project.get('display')}'. "
            f"Project resume_dir: {project.get('resume_dir', '?')}. "
            f"Project key for branches: {project.get('key', '?')}. "
        )

    if args.prompt:
        # One-shot path
        turns.append({"user": args.prompt, "assistant": ""})
        rc = _spawn_turn(claude, session_uuid, first_turn, args.prompt,
                         args.model, renderer, persona_extra)
        turns[-1]["assistant"] = "".join(renderer.reply_text_buf)
        print()
        return rc

    # Interactive REPL
    _print_banner(session_uuid, args.model, project)
    turn_no = 0
    while True:
        # Honor any state changes from /create or /resume slashes.
        if "new_session_uuid" in state:
            session_uuid = state.pop("new_session_uuid")
            first_turn = state.pop("new_first_turn", True)
            persona_extra = state.pop("new_persona_extra", persona_extra)
            renderer = StreamRenderer()  # fresh cost / token totals
            turns = []
            turn_no = 0
            _print_banner(session_uuid, state.get("model"), state.get("project"))

        try:
            prompt_label = f"{turn_no + 1}> "
            text = input(PURPLE(prompt_label))
        except (EOFError, KeyboardInterrupt):
            print()
            break
        text = text.strip()
        if not text:
            continue

        if text.startswith("/"):
            result = _handle_slash(text, renderer, session_uuid, turns, state)
            if result == "quit":
                break
            if result is True:
                continue
            # /summarize or /skill returned text to forward as next turn.
            text = result  # type: ignore[assignment]

        turn_no += 1
        turns.append({"user": text, "assistant": ""})
        renderer.reset_turn()
        _spawn_turn(claude, session_uuid, first_turn, text,
                    state.get("model"), renderer, persona_extra)
        turns[-1]["assistant"] = "".join(renderer.reply_text_buf)
        first_turn = False
        print()

    print(DIM(
        f"\nsession ended  ·  {len(turns)} turn(s)  ·  "
        f"${renderer.total_cost:.4f} spent  ·  uuid {session_uuid}"
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
