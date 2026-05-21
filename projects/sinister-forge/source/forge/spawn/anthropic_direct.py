# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Sinister Forge :: spawn/anthropic_direct.py
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
# Activation: caller (RKOJ-entry.py) checks `ANTHROPIC_API_KEY` in env and
# prefers this path over `claude -p` subprocess when available.
#
# Tools exposed (mirrors the jcode shell shape):
#   - bash            (safe-ish: rm -rf / format / shutdown blocked)
#   - read_file
#   - write_file
#   - glob_search     (pattern + path)
#   - grep_search     (pattern + path, regex)
#   - session_search  (search _shared-memory/ for substring)
#
# Pre-turn forge_memory_bridge.recall() and post-turn write() preserved
# (matches claude -p path so memory is consistent across both modes).

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
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


def _print_thinking(text: str) -> None:
    sys.stdout.write(f"{PURPLE_DIM}{text}{RESET}")
    sys.stdout.flush()


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


def run_turn(prompt: str, root: Path) -> int:
    """Run one operator turn through the Anthropic SDK with visible tool use.

    Returns shell-style exit code (0 = ok, non-zero = error).
    """
    client, err = _build_sdk_client()
    if err:
        print(f"  {RED}[anthropic_direct] {err}{RESET}")
        return 2

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

    print(f"  {GRAY}(anthropic SDK · model {MODEL_ID} · tools on · Ctrl+C to interrupt){RESET}")

    try:
        for turn_idx in range(MAX_TURNS):
            # Stream the assistant turn so thinking/text is visible live.
            assistant_blocks: list[dict[str, Any]] = []
            stop_reason: str | None = None

            try:
                with client.messages.stream(
                    model=MODEL_ID,
                    max_tokens=MAX_TOKENS,
                    system=SYSTEM_PROMPT,
                    tools=TOOLS,
                    messages=messages,
                ) as stream:
                    for event in stream:
                        et = getattr(event, "type", "")
                        if et == "content_block_delta":
                            delta = getattr(event, "delta", None)
                            dtype = getattr(delta, "type", "")
                            if dtype == "text_delta":
                                _print_text(getattr(delta, "text", ""))
                            elif dtype == "thinking_delta":
                                _print_thinking(getattr(delta, "thinking", ""))
                        elif et == "message_stop":
                            pass
                    final = stream.get_final_message()
                    stop_reason = final.stop_reason
                    for block in final.content:
                        bd = block.model_dump() if hasattr(block, "model_dump") else dict(block)
                        assistant_blocks.append(bd)
            except KeyboardInterrupt:
                print(f"\n  {ORANGE}(interrupted by operator){RESET}")
                return 130
            except Exception as e:
                print(f"\n  {RED}[stream error] {e}{RESET}")
                return 3

            # Newline after streamed text.
            print()
            messages.append({"role": "assistant", "content": assistant_blocks})

            # If no tool calls — we're done.
            tool_uses = [b for b in assistant_blocks if b.get("type") == "tool_use"]
            if stop_reason != "tool_use" or not tool_uses:
                break

            # ---- (3) execute each tool_use, gather tool_result blocks ----
            tool_results: list[dict[str, Any]] = []
            for tu in tool_uses:
                name = tu.get("name", "")
                tu_id = tu.get("id", "")
                args = tu.get("input", {}) or {}
                _print_tool_call(name, args)
                fn = TOOL_DISPATCH.get(name)
                if fn is None:
                    result = f"[unknown tool: {name}]"
                else:
                    try:
                        result = fn(args, root)
                    except Exception as e:
                        result = f"[tool {name} crashed: {e}]"
                _print_tool_result(name, result)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tu_id,
                        "content": result[:16000],
                    }
                )

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

    return 0


__all__ = ["run_turn", "MODEL_ID"]
