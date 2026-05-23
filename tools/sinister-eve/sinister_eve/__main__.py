# Author: RKOJ-ELENO :: 2026-05-23
"""sinister-eve REPL — jcode-parity standalone CLI with EVE persona.

Usage:
    sinister-eve              # interactive REPL
    sinister-eve -p "hi"      # one-shot turn, prints reply, exits
    sinister-eve --resume <uuid>  # resume a saved session
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
__version__ = "0.1.0"

# ── ANSI color helpers ─────────────────────────────────────────────────
# Operator wants jcode-parity visual: purple branding + dim gray for
# system lines + gold for tool calls + cyan for thinking + reset on body.
_ENABLE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
if sys.platform == "win32" and _ENABLE_COLOR:
    # Enable ANSI on Windows 10+ by toggling VT processing.
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass


def _c(code: str, txt: str) -> str:
    if not _ENABLE_COLOR:
        return txt
    return f"\x1b[{code}m{txt}\x1b[0m"


PURPLE = lambda s: _c("38;2;191;90;242", s)         # noqa: E731 — terse helpers
PURPLE_BOLD = lambda s: _c("1;38;2;191;90;242", s)  # noqa: E731
DIM = lambda s: _c("2", s)                          # noqa: E731
GOLD_BOLD = lambda s: _c("1;38;2;240;160;32", s)    # noqa: E731 — tool headers
CYAN = lambda s: _c("36", s)                        # noqa: E731 — thinking
GRAY = lambda s: _c("38;2;140;140;145", s)          # noqa: E731 — tool results
RED = lambda s: _c("31", s)                         # noqa: E731 — errors
YELLOW = lambda s: _c("33", s)                      # noqa: E731 — warnings


# ── EVE persona prelude (matches RKOJ's persona.py shape) ──────────────
_EVE_PERSONA = (
    "You are EVE — Sinister Sanctum's orchestration agent. "
    "Self-reference as EVE (never 'Claude' or 'the AI'). "
    "Authorship for any new file you create: `Author: RKOJ-ELENO :: <today>`. "
    "Working repo: D:\\Sinister Sanctum. "
    "You have full file/shell/MCP tool access via the operator's claude CLI."
)

# v1.6.70 RKOJ parity — token budget warning + summarize hint at 100k
_TOKEN_WARN_THRESHOLD = 100_000

# Per-card slash command analogues — REPL subset of RKOJ's 60 commands.
_SLASH_HELP = """
Slash commands (REPL-side intercepts):
  /help          show this list
  /clear         clear terminal scrollback (best-effort via ANSI)
  /cancel        kill the in-flight turn (Ctrl+C also works)
  /cost          cumulative spend + tokens
  /session       print session uuid (for resume from another shell)
  /save          write session uuid + turns to ./eve-session-<uuid>.json
  /persona       print EVE identity (uuid, model, working dir)
  /summarize     ask EVE for a TL;DR of this conversation
  /history       last 10 turns (truncated)
  /quit          exit (also Ctrl+D)

Anything else is sent to EVE as a turn.
"""


def _find_claude() -> str:
    found = shutil.which("claude")
    if not found:
        sys.stderr.write(RED("error: claude CLI not on PATH.\n"))
        sys.stderr.write("  install: https://claude.ai/download (CLI bundle)\n")
        sys.exit(1)
    return found


class StreamRenderer:
    """Parses NDJSON stream-json events from `claude -p --output-format
    stream-json --include-partial-messages --verbose` and renders them
    to ANSI-colored stdout. Mirrors RKOJ's agents_tab._on_stdout."""

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
                    # Single-line preview while streaming
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
            # claude echoes the tool_result back as a user-role message
            msg = ev.get("message", {})
            content = msg.get("content", [])
            for blk in content:
                if blk.get("type") == "tool_result":
                    raw = blk.get("content", "")
                    if isinstance(raw, list):
                        # content is sometimes a list of {type:text,text:...}
                        raw = "".join(b.get("text", "") for b in raw if b.get("type") == "text")
                    raw_s = str(raw)
                    if raw_s:
                        preview = raw_s.replace("\n", " ")[:80]
                        print(GRAY(f"  ✓ {preview}"))
        elif t == "result":
            # Per-turn cost + token footer
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
                renderer: StreamRenderer) -> int:
    """Spawn one claude turn, stream stdout into renderer, return exit code."""
    args = [
        claude,
        "--dangerously-skip-permissions",
        "--output-format", "stream-json",
        "--include-partial-messages",
        "--verbose",
    ]
    if model:
        args += ["--model", model]
    if first_turn:
        args += [
            "--session-id", session_uuid,
            "--system-prompt", _EVE_PERSONA,
            "-p", text,
        ]
    else:
        args += ["--resume", session_uuid, "-p", text]
    # nul stdin so claude doesn't wait + warn
    devnull = subprocess.DEVNULL
    proc = subprocess.Popen(
        args,
        stdin=devnull,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        encoding="utf-8",
        errors="replace",
    )
    # Reader thread for stderr so it doesn't deadlock the pipe.
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


def _print_banner(session_uuid: str, model: str | None) -> None:
    print(PURPLE_BOLD("┌─────────────────────────────────────────┐"))
    print(PURPLE_BOLD("│        sinister-eve REPL · v") + PURPLE(__version__) + PURPLE_BOLD("        │"))
    print(PURPLE_BOLD("└─────────────────────────────────────────┘"))
    print(DIM(f"  session: {session_uuid}  ·  model: {model or 'default'}"))
    print(DIM("  /help for slash commands · /quit or Ctrl+D to exit"))
    print()


def _handle_slash(cmd: str, renderer: StreamRenderer,
                  session_uuid: str, turns: list[dict]) -> bool | str:
    """Return False to forward to EVE, True to stay in REPL, or a string
    sentinel for special actions ('quit', '<summarize-prompt>')."""
    head = cmd.split(None, 1)[0].lower()
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
        print(YELLOW("[/cancel] no in-flight turn (the REPL is idle right now)"))
        return True
    if head == "/cost":
        print(f"[/cost]  in: {renderer.total_in:,} · out: {renderer.total_out:,} "
              f"· total: ${renderer.total_cost:.4f}")
        return True
    if head == "/session":
        print(f"[/session] {session_uuid}")
        print(f"  resume from anywhere: claude -r {session_uuid} -p 'message'")
        return True
    if head == "/save":
        fp = Path.cwd() / f"eve-session-{session_uuid[:8]}.json"
        try:
            fp.write_text(json.dumps({
                "session_uuid": session_uuid,
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
        print(f"  identity:    EVE")
        print(f"  session:     {session_uuid}")
        print(f"  authorship:  RKOJ-ELENO")
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
    print(YELLOW(f"unknown slash command: {head}"))
    return True


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    p = argparse.ArgumentParser(
        prog="sinister-eve",
        description="jcode-style standalone EVE CLI REPL",
    )
    p.add_argument("-p", "--prompt", help="one-shot turn; prints reply + exits")
    p.add_argument("--resume", metavar="UUID", help="resume a saved session by uuid")
    p.add_argument("--model", help="model alias: claude / opus / haiku")
    p.add_argument("-V", "--version", action="store_true", help="print version + exit")
    args = p.parse_args(argv)

    if args.version:
        print(f"sinister-eve {__version__}  ({__author__ if False else 'RKOJ-ELENO'})")
        return 0

    claude = _find_claude()
    session_uuid = args.resume or uuid.uuid4().hex
    first_turn = not args.resume
    renderer = StreamRenderer()
    turns: list[dict] = []

    if args.prompt:
        # One-shot path
        turns.append({"user": args.prompt, "assistant": ""})
        rc = _spawn_turn(claude, session_uuid, first_turn, args.prompt,
                         args.model, renderer)
        turns[-1]["assistant"] = "".join(renderer.reply_text_buf)
        print()
        return rc

    # Interactive REPL
    _print_banner(session_uuid, args.model)
    while True:
        try:
            text = input(PURPLE(">> "))
        except (EOFError, KeyboardInterrupt):
            print()
            break
        text = text.strip()
        if not text:
            continue

        if text.startswith("/"):
            result = _handle_slash(text, renderer, session_uuid, turns)
            if result == "quit":
                break
            if result is True:
                continue
            # /summarize returns the canned prompt string — fall through.
            text = result  # type: ignore[assignment]

        turns.append({"user": text, "assistant": ""})
        renderer.reset_turn()
        _spawn_turn(claude, session_uuid, first_turn, text, args.model, renderer)
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
