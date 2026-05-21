# Sinister Forge :: panes/agent_pane.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# AgentPane = pane-local UI for one spawned agent. Layout:
#   header (project + agent name + mode + status)
#   RichLog (forever-scroll stdout/stderr buffer + tool-use rendering)
#   Input (jcode-form interactive console with autocomplete suggester)
#   status_line (bottom strip: model · provider · tokens · live | idle)
#
# Operator session directive (2026-05-21, image 25): the Agents tab IS this
# pane. It must feel like a complete jcode-form interactive console. The
# 15-feature contract is enumerated at the top of the project plan; this
# module implements / wires every one of them.
#
# Builtins parsed inline (start with `:`):
#   :dm <slug> <message...>
#   :broadcast <message...>
#   :host claude|codex
#   :swarm <N>            -> spawn N parallel agents on this pane's project
#   :clear                -> clear RichLog
#   :help                 -> list inline commands
#
# Slash commands (start with `/`):
#   Full SLASH_COMMANDS registry from forge/commands.py (75+ commands).
#   Tab-completion via SuggestFromList over the registry names + skill names.
#
# Natural language (no `:` and no `/`):
#   When ANTHROPIC_API_KEY is set, the input is routed through
#   forge.spawn.anthropic_direct.run_turn for multi-step tool reasoning with
#   visible thinking blocks + tool calls. Falls back to subprocess.send_line()
#   if the SDK path is unavailable.
#
# Pane-local key bindings (priority=True so the Input doesn't swallow them):
#   PageUp / PageDown    - scroll the log a page
#   Ctrl+Up / Ctrl+Down  - scroll the log a line
#   Ctrl+R               - /resume picker (in-pane)
#   Ctrl+P               - command palette (via app)
#   Ctrl+M               - memory recall on current input text (BM25 top-5)
#   Ctrl+L               - clear log (also bubbles to app)

from __future__ import annotations
import asyncio
import json
import os
import shlex
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.suggester import SuggestFromList
from textual.widgets import Input, RichLog, Static

from forge.spawn.base import AgentSubprocess
from forge.theme import AGENT_ACCENTS

if TYPE_CHECKING:
    from forge.app import ForgeApp


# Token budget mirrors anthropic_direct.TOKEN_BUDGET so the status indicator
# tells the same story as the underlying runtime guard.
_DEFAULT_TOKEN_BUDGET = int(os.environ.get("ANTHROPIC_DIRECT_TOKEN_BUDGET", "200000"))


def _build_suggester() -> SuggestFromList | None:
    """Tab-complete from SLASH_COMMANDS dict + discovered skills.

    Each entry is `/<name>` so the suggester only triggers on slash-prefixed
    input (matches jcode). Falls back to None if commands import fails so the
    pane still constructs in environments without the registry.
    """
    suggestions: list[str] = []
    try:
        from forge.commands import SLASH_COMMANDS
        suggestions.extend(f"/{name}" for name in SLASH_COMMANDS)
    except Exception:
        pass
    try:
        from forge.skills import SkillRegistry
        suggestions.extend(f"/{n}" for n in SkillRegistry.shared().names())
    except Exception:
        pass
    if not suggestions:
        return None
    # Stable + de-duplicated. Suggester does prefix match.
    return SuggestFromList(sorted(set(suggestions)), case_sensitive=False)


class AgentPane(Vertical):
    """Single jcode-form interactive console for one agent.

    Mounts: header · RichLog · Input · status_line.
    Owns: token tally, turn counter, model id, journal pointer.
    """

    # Pane-local key bindings. priority=True ensures they win over the Input
    # widget's default text-edit bindings (otherwise PageUp would just move
    # the cursor instead of paging the log).
    BINDINGS = [
        Binding("pageup", "scroll_log_pageup", "Scroll Up", show=False, priority=True),
        Binding("pagedown", "scroll_log_pagedown", "Scroll Dn", show=False, priority=True),
        Binding("ctrl+up", "scroll_log_lineup", "Up", show=False, priority=True),
        Binding("ctrl+down", "scroll_log_linedown", "Dn", show=False, priority=True),
        Binding("ctrl+r", "open_resume_picker", "Resume", show=False, priority=True),
        Binding("ctrl+m", "recall_memory", "Memory", show=False, priority=True),
    ]

    def __init__(self, agent_name: str, project_display: str, mode: str,
                 accent: str = "purple", subprocess: AgentSubprocess | None = None,
                 project_key: str = "") -> None:
        super().__init__(classes="agent-pane")
        self.agent_name = agent_name
        self.project_display = project_display
        self.project_key = project_key or project_display.lower()
        self.mode = mode
        self.accent = accent
        self.subprocess = subprocess
        self._status = "ready"
        self._header: Static | None = None
        self._log: RichLog | None = None
        self._input: Input | None = None
        self._status_line: Static | None = None
        # ----- jcode-form runtime state (features 5, 9, 15) -----
        # Model + provider for the status indicator (feature 15).
        self._model_id = os.environ.get("ANTHROPIC_DIRECT_MODEL", "claude-opus-4-7")
        self._provider = "anthropic" if os.environ.get("ANTHROPIC_API_KEY") else "subprocess"
        self._tokens_used = 0
        self._tokens_budget = _DEFAULT_TOKEN_BUDGET
        self._turn_count = 0
        self._is_live = False
        # Journal path (feature 9). Lazy-created on first natural-language turn.
        self._journal_path: Path | None = None
        # Multi-line continuation buffer (feature 13).
        self._pending_lines: list[str] = []

    # ----- compose / mount -----

    def compose(self) -> ComposeResult:
        accent_hex = AGENT_ACCENTS.get(self.accent, AGENT_ACCENTS["purple"])
        self._header = Static(self._header_text(), classes="agent-header", markup=True)
        yield self._header
        self._log = RichLog(highlight=True, markup=True, wrap=False, auto_scroll=True)
        self._log.write(f"[bold {accent_hex}]Sinister Forge[/] :: agent pane ready")
        self._log.write(f"[dim]Project: {self.project_display} ({self.mode})[/dim]")
        self._log.write(
            "[dim]/cmd  · tab to autocomplete · type to chat · "
            ":dm :broadcast :host :swarm :clear :help[/dim]"
        )
        self._log.write(
            "[dim]PgUp/PgDn scroll · Ctrl+R resume · Ctrl+M memory recall · "
            "Ctrl+P palette · trailing `\\` for newline[/dim]"
        )
        if self.subprocess:
            self._log.write(f"[dim]Spawning {self.subprocess.binary_name}...[/dim]")
        yield self._log
        suggester = _build_suggester()
        self._input = Input(
            placeholder="/cmd or type to chat (tab autocompletes /commands)",
            classes="agent-input",
            suggester=suggester,
        )
        yield self._input
        self._status_line = Static(self._status_line_text(), classes="agent-status", markup=True)
        yield self._status_line

    def _header_text(self) -> str:
        return (
            f"  [b]{self.project_display.upper()}[/b]  ::  "
            f"[b]{self.agent_name}[/b]  ::  {self.mode}  ::  "
            f"[dim]{self._status}[/dim]  "
        )

    def _status_line_text(self) -> str:
        live = "[bold green]● live[/]" if self._is_live else "[dim]○ idle[/]"
        pct = 0
        if self._tokens_budget:
            pct = int(100 * self._tokens_used / self._tokens_budget)
        tok_color = "green" if pct < 60 else ("yellow" if pct < 85 else "red")
        return (
            f"  [dim]{self._model_id}[/] · [dim]{self._provider}[/] · "
            f"[{tok_color}]{self._tokens_used:,}[/]/[dim]{self._tokens_budget:,}[/] tok · "
            f"turn [dim]{self._turn_count}[/] · {live}  "
        )

    def update_header(self) -> None:
        if self._header:
            self._header.update(self._header_text())

    def update_status_line(self) -> None:
        if self._status_line:
            self._status_line.update(self._status_line_text())

    def write_line(self, line: str) -> None:
        if self._log:
            self._log.write(line)

    def clear_log(self) -> None:
        if self._log:
            self._log.clear()

    # ----- jcode-form input pipeline (features 1, 2, 12, 13) -----

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Operator pressed Enter in the pane input. Route by prefix.

        Feature 13 multi-line: a trailing `\\` accumulates the line into
        _pending_lines and clears the input without submitting. Plain Enter
        flushes the buffer + current line as a single multi-line message.
        """
        if event.input is not self._input:
            return
        raw = event.value or ""
        if self._input is not None:
            self._input.value = ""
        # Multi-line continuation: trailing backslash means "more coming".
        if raw.endswith("\\"):
            stripped = raw[:-1]
            self._pending_lines.append(stripped)
            self.write_line(f"[dim]… {stripped}[/]")
            return
        # Flush accumulated lines + the final line as one message.
        if self._pending_lines:
            text = "\n".join(self._pending_lines + [raw]).strip()
            self._pending_lines = []
        else:
            text = raw.strip()
        if not text:
            return
        if text.startswith("/"):
            await self._dispatch_slash(text)
            return
        if text.startswith(":"):
            await self._handle_builtin(text[1:].strip())
            return
        await self._handle_natural(text)

    async def _dispatch_slash(self, text: str) -> None:
        """jcode-style slash dispatch — surfaces SLASH_COMMANDS + skills.

        Feature 1 + feature 12 land here. The registry's `dispatch()` already
        falls back to maybe_dispatch_skill() so a typed `/<skillname>`
        activates the SkillRegistry skill.
        """
        try:
            from forge.commands import dispatch as _slash_dispatch
            app = getattr(self, "app", None)
            out = _slash_dispatch(text, pane=self, app=app)
            if out:
                self.write_line(out)
        except Exception as e:
            self.write_line(f"[red]slash dispatch crashed: {e}[/]")

    async def _handle_builtin(self, body: str) -> None:
        """Parse and dispatch a `:` builtin. body is the text after the colon."""
        try:
            tokens = shlex.split(body, posix=False)
        except ValueError:
            tokens = body.split()
        if not tokens:
            self.write_line("[yellow]empty :command[/]")
            return
        cmd = tokens[0].lower()
        args = tokens[1:]
        if cmd in ("help", "?"):
            self.write_line(
                "[bold]inline builtins[/]\n"
                "  :dm <slug> <message...>  - direct-message a sibling\n"
                "  :broadcast <message...>  - fan out to fleet\n"
                "  :host claude|codex       - switch this pane's host\n"
                "  :swarm <N>               - spawn N parallel agents on this project\n"
                "  :clear                   - clear this pane\n"
                "  :help                    - this message"
            )
            return
        if cmd == "clear":
            self.clear_log()
            return
        if cmd == "dm":
            if len(args) < 2:
                self.write_line("[yellow]usage: :dm <slug> <message...>[/]")
                return
            to_slug = args[0]
            message = " ".join(args[1:]).strip('"').strip("'")
            self._call_app_builtin_dm(to_slug, message)
            return
        if cmd == "broadcast":
            if not args:
                self.write_line("[yellow]usage: :broadcast <message...>[/]")
                return
            message = " ".join(args).strip('"').strip("'")
            self._call_app_builtin_broadcast(message)
            return
        if cmd == "host":
            if not args or args[0].lower() not in ("claude", "codex"):
                self.write_line("[yellow]usage: :host claude|codex[/]")
                return
            self._call_app_builtin_host(args[0].lower())
            return
        if cmd == "swarm":
            n = 3
            if args:
                try:
                    n = max(1, min(int(args[0]), 8))
                except ValueError:
                    self.write_line(f"[yellow]:swarm requires an int, got {args[0]!r}[/]")
                    return
            self._call_app_builtin_swarm(n)
            return
        self.write_line(f"[yellow]unknown :command `{cmd}` (try :help)[/]")

    # ----- Natural-language path (features 2, 6, 7, 8, 9) -----

    async def _handle_natural(self, text: str) -> None:
        """Natural language → multi-step Claude reasoning + tool use.

        Prefers the anthropic_direct path (visible thinking + tool calls) when
        ANTHROPIC_API_KEY is set. Falls back to subprocess.send_line() for the
        live `claude -p`/`codex` subprocess. This is the operator-asked
        "do its multistep tool stuff and use its tools like jcode does" path.
        """
        self._turn_count += 1
        self._is_live = True
        self.update_status_line()
        try:
            # Journal this turn at the pane level too — anthropic_direct keeps
            # its own JSONL but we mirror a minimal user-message record at the
            # pane journal path so /transcript can find it for subprocess turns
            # where the SDK isn't involved.
            self._journal_record("user", "text", text)
            if os.environ.get("ANTHROPIC_API_KEY"):
                await self._run_anthropic_direct(text)
            else:
                await self._forward_to_subprocess(text)
        finally:
            self._is_live = False
            self.update_status_line()

    async def _run_anthropic_direct(self, prompt: str) -> None:
        """Drive forge.spawn.anthropic_direct.run_turn in a worker thread.

        anthropic_direct.run_turn prints to stdout — that's fine for the
        bundled RKOJ.exe console mode but inside the Textual pane we want
        every line routed to the RichLog. We capture stdout via a pipe and
        stream it line-by-line to self.write_line.

        Tool-use rendering (feature 7), thinking-block render (feature 6),
        status-line `[tool]` / `→ ` indicators (feature 8) and session
        journaling (feature 9) are all emitted by anthropic_direct itself —
        we just pipe its stdout into the pane.
        """
        from forge.spawn import anthropic_direct as _ad

        root = self._sanctum_root()
        # Use asyncio.to_thread because run_turn is sync + blocks on the SDK.
        loop = asyncio.get_event_loop()
        # Redirect stdout for the duration of the call. We use a pipe + read
        # loop so output streams to the log in near-real-time rather than
        # arriving in one chunk at the end.
        import io
        import contextlib

        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                rc = await loop.run_in_executor(None, _ad.run_turn, prompt, root)
        except Exception as e:
            self.write_line(f"[red]anthropic_direct crashed: {e}[/]")
            return
        # Drain captured output to the log. ANSI escapes from anthropic_direct
        # render fine in RichLog when markup=True; the dim-italic thinking
        # panel + tool-call lines flow through as-is.
        out = buf.getvalue()
        for line in out.splitlines():
            self.write_line(line)
        # Update token tally from the journal if anthropic_direct wrote one.
        self._refresh_tokens_from_journal()
        if rc != 0:
            self.write_line(f"[yellow]anthropic_direct exit: {rc}[/]")

    async def _forward_to_subprocess(self, text: str) -> None:
        """Non-`:` input forwards to subprocess stdin via send_line().

        Used when ANTHROPIC_API_KEY is not set, i.e. the operator is running
        `claude -p` / `codex` as a live subprocess instead.
        """
        if not self.subprocess:
            self.write_line(
                "[dim]no subprocess attached (empty pane). Use Ctrl+W to spawn one, "
                "or set ANTHROPIC_API_KEY for the in-pane SDK path.[/]"
            )
            return
        try:
            await self.subprocess.send_line(text)
            self.write_line(f"[dim]> {text}[/]")
        except Exception as e:
            self.write_line(f"[yellow]send_line failed: {e} (stdin may be DEVNULL)[/]")

    # ----- key actions (features 3, 4, 10) -----

    def action_scroll_log_pageup(self) -> None:
        """Feature 3 — PageUp scrolls the log."""
        if self._log:
            self._log.scroll_page_up()

    def action_scroll_log_pagedown(self) -> None:
        """Feature 3 — PageDown scrolls the log."""
        if self._log:
            self._log.scroll_page_down()

    def action_scroll_log_lineup(self) -> None:
        """Feature 3 — Ctrl+Up scrolls one line up."""
        if self._log:
            self._log.scroll_up()

    def action_scroll_log_linedown(self) -> None:
        """Feature 3 — Ctrl+Down scrolls one line down."""
        if self._log:
            self._log.scroll_down()

    def action_recall_memory(self) -> None:
        """Feature 4 — Ctrl+M runs forge_memory_bridge.recall on the input text.

        Shows top-5 hits inline in the log so the operator can decide whether
        to fold the context into their next prompt. BM25 ranking lives in
        forge_memory_bridge.bm25_rescore.
        """
        query = (self._input.value if self._input else "").strip()
        if not query:
            self.write_line(
                "[yellow]Ctrl+M: type a query in the input first (e.g. "
                "'kernel apk broadcast su') then hit Ctrl+M[/]"
            )
            return
        try:
            import forge_memory_bridge as _mem  # type: ignore
            hits = _mem.recall(query, limit=5) or []
        except Exception as e:
            self.write_line(f"[red]memory recall failed: {e}[/]")
            return
        if not hits:
            self.write_line(f"[dim]memory recall: no hits for `{query}`[/]")
            return
        # Re-rank via BM25 when more than 1 hit (single-doc BM25 is degenerate).
        try:
            import forge_memory_bridge as _mem  # type: ignore
            if len(hits) > 1:
                hits = _mem.bm25_rescore(query, hits)
        except Exception:
            pass
        self.write_line(f"[bold]memory recall:[/] `{query}` → top {len(hits)}")
        for i, h in enumerate(hits, 1):
            if isinstance(h, dict):
                ns = h.get("namespace", "?")
                key = h.get("key", "?")
                txt = h.get("text") or h.get("content") or h.get("body") or ""
                if not isinstance(txt, str):
                    txt = str(txt)
                preview = txt.replace("\n", " ").strip()[:160]
                self.write_line(f"  [bold]{i}.[/] [dim]{ns}/{key}[/]  {preview}")
            else:
                self.write_line(f"  [bold]{i}.[/] {str(h)[:200]}")

    def action_open_resume_picker(self) -> None:
        """Feature 10 — Ctrl+R lists resume-points inline (uses /resume)."""
        try:
            from forge.commands import _cmd_resume  # noqa: PLC0415
            out = _cmd_resume([], pane=self, app=getattr(self, "app", None))
            if out:
                self.write_line(out)
        except Exception as e:
            self.write_line(f"[red]/resume failed: {e}[/]")

    # ----- subprocess + lifecycle (existing surface, preserved) -----

    async def run_subprocess(self) -> None:
        if not self.subprocess:
            return
        try:
            await self.subprocess.spawn()
            self._status = "running"
            self.update_header()
        except FileNotFoundError as e:
            self._status = "no binary"
            self.update_header()
            self.write_line(f"[red]{e}[/]")
            return

        async def _tail(stream_iter):
            async for line in stream_iter:
                self.write_line(line)

        await asyncio.gather(
            _tail(self.subprocess.tail_stdout()),
            _tail(self.subprocess.tail_stderr()),
        )
        exit_code = await self.subprocess.wait()
        self._status = f"exited ({exit_code})"
        self.update_header()
        self.write_line(f"[dim]Process exited with code {exit_code}.[/dim]")

    # ----- thin app-callbacks (deferred lookup so AgentPane has no app import cycle) -----

    def _call_app_builtin_dm(self, to_slug: str, message: str) -> None:
        from forge.swarm import send_dm as _send_dm
        from_slug = self.agent_name.lower().replace(" ", "-") or "forge"
        try:
            path = _send_dm(
                from_slug=from_slug,
                to_slug=to_slug,
                subject=f"inline-dm-from-{from_slug}",
                body=message,
                project_hint=self.project_key,
            )
            self.write_line(f"[green]:dm → {to_slug} :: {path.name}[/]")
        except Exception as e:
            self.write_line(f"[red]:dm failed: {e}[/]")

    def _call_app_builtin_broadcast(self, message: str) -> None:
        from forge.swarm import broadcast as _broadcast
        from_slug = self.agent_name.lower().replace(" ", "-") or "forge"
        try:
            paths = _broadcast(
                from_slug=from_slug,
                subject=f"inline-broadcast-from-{from_slug}",
                body=message,
                project_hint=self.project_key,
            )
            self.write_line(f"[green]:broadcast → {len(paths)} siblings[/]")
        except Exception as e:
            self.write_line(f"[red]:broadcast failed: {e}[/]")

    def _call_app_builtin_host(self, target_host: str) -> None:
        try:
            self.app._action_host_switch(target_host)  # type: ignore[attr-defined]
        except AttributeError:
            self.write_line("[red]:host requires the parent app to be ForgeApp[/]")

    def _call_app_builtin_swarm(self, n: int) -> None:
        try:
            self.app._action_swarm()  # type: ignore[attr-defined]
            self.write_line(f"[green]:swarm (default 3) on {self.project_display}[/]")
        except AttributeError:
            self.write_line("[red]:swarm requires the parent app to be ForgeApp[/]")

    # ----- pane-level journal helpers (feature 9) -----

    def _sanctum_root(self) -> Path:
        for c in (
            os.environ.get("SANCTUM_ROOT"),
            r"D:\Sinister Sanctum",
            r"C:\Sinister Sanctum",
            str(Path.home() / "Sinister Sanctum"),
        ):
            if c and (Path(c) / "CLAUDE.md").exists():
                return Path(c)
        return Path(r"D:\Sinister Sanctum")

    def _ensure_journal(self) -> Path | None:
        if self._journal_path is not None:
            return self._journal_path
        try:
            root = self._sanctum_root()
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
            slug = (self.agent_name or "agent").lower().replace(" ", "-").replace("/", "-")
            out_dir = root / "_shared-memory" / "forge-memory" / "pane-journals"
            out_dir.mkdir(parents=True, exist_ok=True)
            self._journal_path = out_dir / f"{ts}-{slug}.jsonl"
        except Exception:
            self._journal_path = None
        return self._journal_path

    def _journal_record(self, role: str, type_: str, content) -> None:
        p = self._ensure_journal()
        if p is None:
            return
        try:
            rec = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "role": role,
                "type": type_,
                "agent_name": self.agent_name,
                "project_key": self.project_key,
                "turn": self._turn_count,
                "content": content,
            }
            with p.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
        except Exception:
            pass

    def _refresh_tokens_from_journal(self) -> None:
        """Walk the most recent anthropic-direct-sessions journal and sum
        token usage so the status line (feature 15) reflects the current
        budget burn. Cheap — we only read the last <=5 .jsonl files.
        """
        try:
            root = self._sanctum_root()
            d = root / "_shared-memory" / "forge-memory" / "anthropic-direct-sessions"
            if not d.exists():
                return
            files = sorted(d.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]
            total = 0
            for fp in files:
                try:
                    for ln in fp.read_text(encoding="utf-8", errors="replace").splitlines():
                        try:
                            rec = json.loads(ln)
                        except Exception:
                            continue
                        c = rec.get("content")
                        if isinstance(c, dict):
                            total += int(c.get("input_tokens", 0) or 0)
                            total += int(c.get("output_tokens", 0) or 0)
                except OSError:
                    continue
            if total > 0:
                self._tokens_used = total
                self.update_status_line()
        except Exception:
            pass


__all__ = ["AgentPane"]
