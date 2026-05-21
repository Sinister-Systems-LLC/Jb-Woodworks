# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Sinister Forge :: spawn/anthropic_direct.py  (v0.7.0)
#
# Direct Anthropic SDK path for the RKOJ shell. Operator (2026-05-21, verbatim):
# "i want it to do its multitep tool stuff and use its tools like jcode does
# search before doing soemthing show tool calls show ist hinking in the shell
# not just oneshot answer".
#
# Wraps `anthropic.Anthropic.messages.create` with a streaming tool-use loop.
# The model alternates between:
#   - text/thinking blocks (printed live as they stream)
#   - tool_use blocks (rendered as visible "EVE → tool" lines + executed locally)
# Loop runs until the model returns `stop_reason == "end_turn"`.
#
# v0.7.0 jcode-parity upgrades on top of v0.6.0 baseline:
#   1. Parallel tool execution — read-only tools (read_file, glob_search,
#      grep_search, session_search) execute concurrently via a 4-worker
#      ThreadPoolExecutor. Write/exec tools (bash, write_file) run serially
#      after the parallel batch. Results are re-ordered to match the original
#      tool_use sequence (Anthropic API requires this ordering).
#   2. Prompt caching — system prompt is sent as a structured cache-control
#      block (`{"type": "ephemeral"}`) so subsequent turns hit the 5-min cache.
#   3. Thinking-block render — buffered until end-of-block then printed as a
#      dimmed-italic rich Panel titled `💭 Thought for {N:.1f}s`. Falls back
#      to plain ANSI dim italic when `rich` is not installed.
#   4. Token-budget guard — sums cumulative input+output tokens after each
#      response.usage; warns + breaks if total exceeds 150_000.
#   5. Session journaling — every assistant block + tool result + user prompt
#      is appended as a JSONL line under
#      `_shared-memory/forge-memory/anthropic-direct-sessions/<ts>-<uuid>.jsonl`.
#      Foundation for our own session_search across past conversations.
#
# Activation: caller (RKOJ-entry.py) checks `ANTHROPIC_API_KEY` in env and
# prefers this path over `claude -p` subprocess when available.
#
# Tools exposed (mirrors the jcode shell shape):
#   - bash            (safe-ish: rm -rf / format / shutdown blocked)
#   - read_file       (read-only — parallel-eligible)
#   - write_file
#   - glob_search     (read-only — parallel-eligible)
#   - grep_search     (read-only — parallel-eligible)
#   - session_search  (read-only — parallel-eligible)
#
# Pre-turn forge_memory_bridge.recall() and post-turn write() preserved
# (matches claude -p path so memory is consistent across both modes).

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Theme constants mirror RKOJ-entry.py so output is visually consistent when
# this module is invoked from the EXE.
RESET = "\033[0m"
BOLD = "\033[1m"


def _fg(r: int, g: int, b: int) -> str:
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
ORANGE = _fg(240, 140, 60)


# ---- Model + system prompt ------------------------------------------------

# CLAUDE.md canonical model ID — the file-level Author doctrine pinned this to
# the Opus 4.7 line. Use the model alias the SDK recognises.
MODEL_ID = "claude-opus-4-7"
MAX_TOKENS = 8192
MAX_TURNS = 12

# v0.7.0 — Token-budget guard. Default 200K context window; warn + stop at 150K
# to leave headroom for the assistant's reply. Override with env var if needed.
TOKEN_BUDGET = int(os.environ.get("ANTHROPIC_DIRECT_TOKEN_BUDGET", "150000"))

# v0.7.0 — Parallel-eligible tools (read-only, side-effect-free).
READ_ONLY_TOOLS: frozenset[str] = frozenset({
    "read_file", "glob_search", "grep_search", "session_search",
})
PARALLEL_WORKERS = 4

SYSTEM_PROMPT = (
    "You are EVE, the orchestration agent for the Sinister Sanctum fleet. "
    "Author signature for everything written: RKOJ-ELENO. "
    "Working directory: D:/Sinister Sanctum. "
    "You have tools: bash, read_file, write_file, glob_search, grep_search, "
    "session_search. "
    "When the operator asks you to do something non-trivial, BATCH tool calls "
    "in parallel (multiple tool_use blocks in one assistant turn) — for "
    "example, when searching for context, call session_search + glob_search + "
    "grep_search together. Always show your reasoning before tool calls. "
    "Prefer session_search over raw bash grep when looking through "
    "_shared-memory/. Keep replies concise — let the tool calls do the talking."
)


# ---- Tool schemas (Anthropic tool-use format) -----------------------------

TOOLS: list[dict[str, Any]] = [
    {
        "name": "bash",
        "description": (
            "Run a shell command (bash on *nix, cmd-via-bash on Win). Returns "
            "stdout+stderr. Destructive commands (rm -rf, format, shutdown, "
            "del /s) are BLOCKED. Use for safe ops like git status, ls, cat, "
            "echo, pip show, etc."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command."},
                "timeout_sec": {
                    "type": "integer",
                    "description": "Max seconds to wait (default 30).",
                },
            },
            "required": ["command"],
        },
    },
    {
        "name": "read_file",
        "description": "Read a file from disk. Use absolute paths.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "max_bytes": {
                    "type": "integer",
                    "description": "Cap read size (default 64KB).",
                },
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": (
            "Write content to a file (overwrites). Author line is your "
            "responsibility — include `# Author: RKOJ-ELENO :: 2026-05-21` "
            "near the top of any new code file."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "glob_search",
        "description": (
            "Glob-match filenames under a directory. Returns paths (max 200)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern e.g. '**/*.py'",
                },
                "root": {
                    "type": "string",
                    "description": "Search root (default Sanctum root).",
                },
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "grep_search",
        "description": (
            "Regex-search file contents. Returns matching lines with file:line "
            "prefix (max 200)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Python regex."},
                "root": {
                    "type": "string",
                    "description": "Search root (default Sanctum root).",
                },
                "glob": {
                    "type": "string",
                    "description": "Optional file glob filter e.g. '*.py'.",
                },
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "session_search",
        "description": (
            "Search the Sanctum shared-memory store (brain entries, inbox, "
            "PROGRESS logs, resume-points, knowledge index) for a substring or "
            "regex. Faster + more relevant than grep_search for fleet context."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "description": "Max hits (default 20)."},
            },
            "required": ["query"],
        },
    },
]


# ---- Safe-bash gate -------------------------------------------------------

_BAD_BASH_PATTERNS = [
    r"\brm\s+-rf\b",
    r"\brm\s+-fr\b",
    r"\bformat\s+[a-zA-Z]:",
    r"\bshutdown\b",
    r"\bdel\s+/s\b",
    r":\(\)\s*\{\s*:\|:&\s*\};\s*:",  # fork bomb
    r"\bmkfs\.",
    r"\bdd\s+if=.*of=/dev/",
    r">\s*/dev/sd[a-z]",
]


def _bash_is_safe(cmd: str) -> tuple[bool, str]:
    for pat in _BAD_BASH_PATTERNS:
        if re.search(pat, cmd, flags=re.IGNORECASE):
            return False, f"blocked by safety gate: matched `{pat}`"
    return True, ""


# ---- Tool implementations -------------------------------------------------

def _tool_bash(args: dict, root: Path) -> str:
    cmd = args.get("command", "")
    timeout = int(args.get("timeout_sec", 30))
    ok, reason = _bash_is_safe(cmd)
    if not ok:
        return f"[bash refused] {reason}"
    try:
        r = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(root),
        )
        out = (r.stdout or "") + (("\n[stderr]\n" + r.stderr) if r.stderr else "")
        return f"[exit {r.returncode}]\n{out[:8000]}"
    except subprocess.TimeoutExpired:
        return f"[bash timeout after {timeout}s]"
    except Exception as e:
        return f"[bash error: {e}]"


def _tool_read_file(args: dict, root: Path) -> str:
    p = Path(args.get("path", ""))
    if not p.is_absolute():
        p = root / p
    max_bytes = int(args.get("max_bytes", 65536))
    try:
        data = p.read_bytes()[:max_bytes]
        return data.decode("utf-8", errors="replace")
    except FileNotFoundError:
        return f"[read_file: not found: {p}]"
    except Exception as e:
        return f"[read_file error: {e}]"


def _tool_write_file(args: dict, root: Path) -> str:
    p = Path(args.get("path", ""))
    if not p.is_absolute():
        p = root / p
    content = args.get("content", "")
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"[wrote {len(content)} chars to {p}]"
    except Exception as e:
        return f"[write_file error: {e}]"


def _tool_glob_search(args: dict, root: Path) -> str:
    pattern = args.get("pattern", "")
    base = Path(args.get("root") or root)
    if not base.is_absolute():
        base = root / base
    try:
        hits = list(base.glob(pattern))[:200]
        if not hits:
            return f"[glob_search: no matches for `{pattern}` under {base}]"
        return "\n".join(str(p) for p in hits)
    except Exception as e:
        return f"[glob_search error: {e}]"


def _tool_grep_search(args: dict, root: Path) -> str:
    pattern = args.get("pattern", "")
    base = Path(args.get("root") or root)
    if not base.is_absolute():
        base = root / base
    glob = args.get("glob", "**/*")
    try:
        rx = re.compile(pattern)
    except re.error as e:
        return f"[grep_search: invalid regex: {e}]"
    out: list[str] = []
    try:
        for fp in base.glob(glob):
            if not fp.is_file():
                continue
            try:
                for i, ln in enumerate(
                    fp.read_text(encoding="utf-8", errors="replace").splitlines(),
                    1,
                ):
                    if rx.search(ln):
                        out.append(f"{fp}:{i}: {ln[:200]}")
                        if len(out) >= 200:
                            return "\n".join(out) + "\n[truncated at 200]"
            except (OSError, UnicodeDecodeError):
                continue
    except Exception as e:
        return f"[grep_search error: {e}]"
    return "\n".join(out) or f"[grep_search: no matches for `{pattern}`]"


def _tool_session_search(args: dict, root: Path) -> str:
    query = args.get("query", "")
    limit = int(args.get("limit", 20))
    sm = root / "_shared-memory"
    if not sm.exists():
        return "[session_search: no _shared-memory dir]"
    try:
        rx = re.compile(query, re.IGNORECASE)
    except re.error:
        rx = re.compile(re.escape(query), re.IGNORECASE)
    targets = ["knowledge", "PROGRESS", "inbox", "resume-points", "cross-agent", "plans"]
    out: list[str] = []
    for tgt in targets:
        d = sm / tgt
        if not d.exists():
            continue
        for fp in d.rglob("*"):
            if not fp.is_file():
                continue
            if fp.suffix not in {".md", ".json", ".txt", ""}:
                continue
            try:
                text = fp.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if rx.search(text):
                snippet = ""
                for ln in text.splitlines():
                    if rx.search(ln):
                        snippet = ln.strip()[:160]
                        break
                rel = fp.relative_to(root) if fp.is_relative_to(root) else fp
                out.append(f"{rel}: {snippet}")
                if len(out) >= limit:
                    return "\n".join(out) + f"\n[truncated at {limit}]"
    return "\n".join(out) or f"[session_search: no hits for `{query}`]"


TOOL_DISPATCH = {
    "bash": _tool_bash,
    "read_file": _tool_read_file,
    "write_file": _tool_write_file,
    "glob_search": _tool_glob_search,
    "grep_search": _tool_grep_search,
    "session_search": _tool_session_search,
}


# ---- Rendering ------------------------------------------------------------

def _short(s: str, n: int = 200) -> str:
    s = s.replace("\n", " ").replace("\r", " ")
    return s if len(s) <= n else s[: n - 1] + "…"


def _print_thinking_live(text: str) -> None:
    """v0.6.0 fallback — stream thinking_delta raw in dim purple.

    v0.7.0 prefers `_render_thinking_block` (buffered) but we keep this for the
    case where rich is missing AND the operator wants live feedback. The
    streaming loop in run_turn buffers by default; this helper is unused on the
    happy path but retained for diagnostic mode (env ANTHROPIC_DIRECT_LIVE_THINK).
    """
    sys.stdout.write(f"{PURPLE_DIM}{text}{RESET}")
    sys.stdout.flush()


def _render_thinking_block(text: str, elapsed_sec: float) -> None:
    """v0.7.0 — render a completed thinking block as a dimmed italic panel.

    Uses rich.panel.Panel when available; falls back to ANSI dim-italic
    bracketed block when rich is not installed.
    """
    title = f"💭 Thought for {elapsed_sec:.1f}s"
    text = text.strip()
    if not text:
        return
    try:
        from rich.console import Console
        from rich.panel import Panel

        Console().print(Panel(text, title=title, style="dim italic", border_style="dim"))
        return
    except Exception:
        pass
    # ANSI fallback — dim italic. \033[3m = italic.
    print(f"\n{PURPLE_DIM}╭── {title} ──{RESET}")
    for ln in text.splitlines():
        print(f"{PURPLE_DIM}│ \033[3m{ln}{RESET}")
    print(f"{PURPLE_DIM}╰──{RESET}")


# ---- v0.7.0 session journaling -------------------------------------------

def _journal_open(root: Path) -> Path | None:
    """Open a fresh JSONL session journal under _shared-memory/forge-memory/.

    Returns the path, or None if the directory cannot be created.
    """
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    short_uuid = uuid.uuid4().hex[:8]
    out_dir = root / "_shared-memory" / "forge-memory" / "anthropic-direct-sessions"
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        return None
    return out_dir / f"{ts}-{short_uuid}.jsonl"


def _journal_write(path: Path | None, role: str, type_: str, content: Any) -> None:
    """Append a single JSONL record. Silent on any failure — journaling is
    best-effort and must never break the agent loop.
    """
    if path is None:
        return
    try:
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "role": role,
            "type": type_,
            "content": content,
        }
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    except Exception:
        pass


def _print_text(text: str) -> None:
    sys.stdout.write(f"{WHITE}{text}{RESET}")
    sys.stdout.flush()


def _print_tool_call(name: str, args: dict) -> None:
    # Compact one-line preview of the args.
    preview = ""
    if name == "bash":
        preview = _short(args.get("command", ""), 100)
    elif name in ("read_file", "write_file"):
        preview = args.get("path", "")
    elif name == "glob_search":
        preview = args.get("pattern", "")
    elif name == "grep_search":
        preview = (
            f"{args.get('pattern', '')}"
            + (f"  in {args['glob']}" if args.get("glob") else "")
        )
    elif name == "session_search":
        preview = args.get("query", "")
    else:
        preview = _short(json.dumps(args, ensure_ascii=False), 100)
    print(f"\n  {GOLD}● tool {RESET}{WHITE}{name}{RESET} {GRAY}{preview}{RESET}")


def _print_tool_result(name: str, result: str) -> None:
    lines = result.splitlines()
    head = lines[:6]
    tail_count = max(0, len(lines) - len(head))
    for ln in head:
        print(f"    {GRAY}│ {ln[:200]}{RESET}")
    if tail_count:
        print(f"    {GRAY}│ … ({tail_count} more lines){RESET}")


# ---- Entry: run the tool-use loop -----------------------------------------

def _build_sdk_client():
    """Lazy-import + construct the SDK client. Returns (client, error_or_None)."""
    try:
        import anthropic  # noqa: F401
    except ImportError as e:
        return None, f"anthropic SDK not installed: {e}"
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None, "ANTHROPIC_API_KEY not set"
    try:
        from anthropic import Anthropic

        return Anthropic(), None
    except Exception as e:
        return None, f"Anthropic() ctor failed: {e}"


def _execute_tool(name: str, args: dict, tu_id: str, root: Path) -> tuple[str, dict[str, Any]]:
    """Execute a single tool and produce its tool_result block.

    Returns (tu_id, result_block). Pure function — safe to call from a worker
    thread for read-only tools.
    """
    fn = TOOL_DISPATCH.get(name)
    if fn is None:
        result = f"[unknown tool: {name}]"
    else:
        try:
            result = fn(args, root)
        except Exception as e:
            result = f"[tool {name} crashed: {e}]"
    return tu_id, {
        "type": "tool_result",
        "tool_use_id": tu_id,
        "content": result[:16000],
    }


def _run_tool_batch(
    tool_uses: list[dict[str, Any]],
    root: Path,
    journal: Path | None,
) -> list[dict[str, Any]]:
    """v0.7.0 — Execute a batch of tool_use blocks. Read-only tools run in
    parallel (4 workers); write/exec tools run serially after. Results are
    re-ordered to match the original tool_use sequence — the Anthropic API
    requires tool_result order to match tool_use order in the prior turn.
    """
    # Phase 1: print every tool call up-front so the operator sees the batch.
    for tu in tool_uses:
        _print_tool_call(tu.get("name", ""), tu.get("input", {}) or {})
        _journal_write(journal, "assistant", "tool_use", {
            "id": tu.get("id", ""),
            "name": tu.get("name", ""),
            "input": tu.get("input", {}) or {},
        })

    # Phase 2: split into parallel-eligible (read-only) vs serial.
    parallel_idx: list[int] = []
    serial_idx: list[int] = []
    for i, tu in enumerate(tool_uses):
        if tu.get("name", "") in READ_ONLY_TOOLS:
            parallel_idx.append(i)
        else:
            serial_idx.append(i)

    # Index → result_block. Filled by both phases, drained in original order.
    results_by_idx: dict[int, dict[str, Any]] = {}

    # Phase 2a: parallel read-only batch.
    if parallel_idx:
        with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as ex:
            future_to_idx = {
                ex.submit(
                    _execute_tool,
                    tool_uses[i].get("name", ""),
                    tool_uses[i].get("input", {}) or {},
                    tool_uses[i].get("id", ""),
                    root,
                ): i
                for i in parallel_idx
            }
            for fut in future_to_idx:
                i = future_to_idx[fut]
                try:
                    _, block = fut.result()
                except Exception as e:
                    block = {
                        "type": "tool_result",
                        "tool_use_id": tool_uses[i].get("id", ""),
                        "content": f"[parallel tool error: {e}]",
                    }
                results_by_idx[i] = block

    # Phase 2b: serial write/exec tools (bash, write_file).
    for i in serial_idx:
        tu = tool_uses[i]
        _, block = _execute_tool(
            tu.get("name", ""),
            tu.get("input", {}) or {},
            tu.get("id", ""),
            root,
        )
        results_by_idx[i] = block

    # Phase 3: print previews + journal in original order, build ordered list.
    ordered: list[dict[str, Any]] = []
    for i, tu in enumerate(tool_uses):
        block = results_by_idx[i]
        _print_tool_result(tu.get("name", ""), block.get("content", ""))
        _journal_write(journal, "tool", "tool_result", {
            "tool_use_id": block.get("tool_use_id", ""),
            "name": tu.get("name", ""),
            "content": block.get("content", ""),
        })
        ordered.append(block)
    return ordered


def run_turn(prompt: str, root: Path) -> int:
    """Run one operator turn through the Anthropic SDK with visible tool use.

    Returns shell-style exit code (0 = ok, non-zero = error).
    """
    client, err = _build_sdk_client()
    if err:
        print(f"  {RED}[anthropic_direct] {err}{RESET}")
        return 2

    # v0.7.0 — open a JSONL journal for this run.
    journal = _journal_open(root)
    _journal_write(journal, "user", "text", prompt)

    # ---- (1) PRE-TURN memory recall ------------------------------------
    memory_prefix = ""
    try:
        import forge_memory_bridge as _mem  # type: ignore

        hits = _mem.recall(prompt, limit=4) or []
        if hits:
            lines = ["[memory: recent relevant context]"]
            for h in hits if isinstance(hits, list) else [hits]:
                lines.append(f"- {str(h)[:200]}")
            memory_prefix = "\n".join(lines) + "\n\n"
            print(f"  {GRAY}↺ memory recall: {len(hits)} hits{RESET}")
    except Exception:
        pass

    user_text = (memory_prefix + prompt) if memory_prefix else prompt

    # ---- (2) tool-use loop ---------------------------------------------
    messages: list[dict[str, Any]] = [
        {"role": "user", "content": user_text},
    ]

    # v0.7.0 — system prompt as a structured cache-control block. Subsequent
    # turns reuse the same prefix → cache hit, ~10x cheaper input tokens.
    system_blocks = [
        {
            "type": "text",
            "text": SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},
        }
    ]

    print(f"  {GRAY}(anthropic SDK · model {MODEL_ID} · tools on · cache on · Ctrl+C to interrupt){RESET}")

    # v0.7.0 — cumulative token usage across all turns of this run.
    total_input_tokens = 0
    total_output_tokens = 0

    try:
        for turn_idx in range(MAX_TURNS):
            # v0.7.0 — token-budget guard. Sum so far; if over budget, warn and stop.
            total_so_far = total_input_tokens + total_output_tokens
            if total_so_far > TOKEN_BUDGET:
                print(
                    f"\n  {ORANGE}[budget guard] {total_so_far} tokens used "
                    f"(> {TOKEN_BUDGET}); stopping to preserve context.{RESET}"
                )
                _journal_write(journal, "assistant", "text",
                               f"[budget guard tripped at {total_so_far} tokens]")
                break

            # Stream the assistant turn so thinking/text is visible live.
            assistant_blocks: list[dict[str, Any]] = []
            stop_reason: str | None = None

            # v0.7.0 — buffer the current thinking block until end-of-block.
            thinking_buf: list[str] = []
            thinking_started_at: float | None = None

            try:
                with client.messages.stream(
                    model=MODEL_ID,
                    max_tokens=MAX_TOKENS,
                    system=system_blocks,
                    tools=TOOLS,
                    messages=messages,
                ) as stream:
                    for event in stream:
                        et = getattr(event, "type", "")
                        if et == "content_block_start":
                            cb = getattr(event, "content_block", None)
                            if getattr(cb, "type", "") == "thinking":
                                thinking_buf = []
                                thinking_started_at = time.monotonic()
                        elif et == "content_block_delta":
                            delta = getattr(event, "delta", None)
                            dtype = getattr(delta, "type", "")
                            if dtype == "text_delta":
                                _print_text(getattr(delta, "text", ""))
                            elif dtype == "thinking_delta":
                                thinking_buf.append(getattr(delta, "thinking", ""))
                        elif et == "content_block_stop":
                            # End of any content block — if it was thinking, render it now.
                            if thinking_started_at is not None and thinking_buf:
                                elapsed = time.monotonic() - thinking_started_at
                                full = "".join(thinking_buf)
                                _render_thinking_block(full, elapsed)
                                _journal_write(journal, "assistant", "thinking", {
                                    "text": full, "elapsed_sec": elapsed,
                                })
                                thinking_buf = []
                                thinking_started_at = None
                        elif et == "message_stop":
                            pass
                    final = stream.get_final_message()
                    stop_reason = final.stop_reason
                    for block in final.content:
                        bd = block.model_dump() if hasattr(block, "model_dump") else dict(block)
                        assistant_blocks.append(bd)
                    # v0.7.0 — track cumulative token usage for budget guard.
                    usage = getattr(final, "usage", None)
                    if usage is not None:
                        total_input_tokens += int(getattr(usage, "input_tokens", 0) or 0)
                        total_output_tokens += int(getattr(usage, "output_tokens", 0) or 0)
                        # Cached tokens count as input too (already added above
                        # via input_tokens for newer SDKs; older versions split).
                        cached = int(getattr(usage, "cache_read_input_tokens", 0) or 0)
                        if cached:
                            print(f"  {GRAY}↺ cache hit: {cached} tokens reused{RESET}")
            except KeyboardInterrupt:
                print(f"\n  {ORANGE}(interrupted by operator){RESET}")
                return 130
            except Exception as e:
                print(f"\n  {RED}[stream error] {e}{RESET}")
                return 3

            # Newline after streamed text.
            print()
            messages.append({"role": "assistant", "content": assistant_blocks})

            # Journal any text blocks for later session_search.
            for b in assistant_blocks:
                if b.get("type") == "text":
                    _journal_write(journal, "assistant", "text", b.get("text", ""))

            # If no tool calls — we're done.
            tool_uses = [b for b in assistant_blocks if b.get("type") == "tool_use"]
            if stop_reason != "tool_use" or not tool_uses:
                break

            # ---- (3) execute the batch (parallel + serial split) ---------
            tool_results = _run_tool_batch(tool_uses, root, journal)
            messages.append({"role": "user", "content": tool_results})
        else:
            print(f"\n  {ORANGE}(hit MAX_TURNS={MAX_TURNS} — stopping){RESET}")

    finally:
        # ---- (4) POST-TURN memory write ---------------------------------
        try:
            import forge_memory_bridge as _mem  # type: ignore

            _mem.write("rkoj-shell", prompt)
        except Exception:
            pass
        # v0.7.0 — surface the journal path so operator can grep it later.
        if journal is not None:
            try:
                rel = journal.relative_to(root)
                print(f"  {GRAY}↻ journal: {rel}{RESET}")
            except Exception:
                pass

    return 0


__all__ = ["run_turn", "MODEL_ID"]
