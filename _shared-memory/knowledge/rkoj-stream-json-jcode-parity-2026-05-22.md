# Author: RKOJ-ELENO :: 2026-05-22

# RKOJ stream-json jcode-parity arc (v1.6.11 → v1.6.18)

**Status:** doctrine, implemented + shipped
**Composes with:** `rkoj-session-continuity-pattern-2026-05-21`, `rkoj-phase1-memory-bootstrap-2026-05-21`, `agent-identity-eve`, `jcode-agentic-loop-patterns-port-to-python`, `forever-expanding-modular-architecture-doctrine`.

---

## TL;DR

Switching from `claude -p` plain-text output to `claude -p --output-format stream-json --include-partial-messages --verbose` unlocks jcode-style live feedback inside RKOJ.exe without needing the Anthropic SDK direct path (which requires `ANTHROPIC_API_KEY`). Operator (verbatim 2026-05-22): *"i want it to work like jcode and have everything i asked for"*. v1.6.11 wired the parser; v1.6.12-18 added telemetry + ergonomic surfaces on top.

## What stream-json gives you

`claude -p` with these flags emits NDJSON to stdout — one JSON event per line. Key event types:

| `type` | When | Fields RKOJ uses |
|---|---|---|
| `system` (subtype `init` / `status` / `hook_*`) | Session boot, status changes | (suppressed — too noisy) |
| `stream_event` + `content_block_delta` + `text_delta` | Token-by-token text generation | `delta.text` → terminal append |
| `stream_event` + `content_block_delta` + `thinking_delta` | Extended-thinking mode (opus, gated) | `delta.thinking` → spinner preview |
| `stream_event` + `content_block_start` + `tool_use` | Tool call begins | `name`, `input` → `● Tool(args)` marker + spinner active-tool |
| `user` + content `tool_result` | Tool finishes | `content` → `✓ <result-preview>` |
| `assistant` | Complete assembled message | (skipped — deltas already streamed it) |
| `rate_limit_event` | 5-hour rate-limit info | (not yet rendered) |
| `result` | Turn end summary | `usage.input_tokens` / `output_tokens` / `cache_read_input_tokens` / `total_cost_usd` / `duration_ms` → footer + cost pill |

## Why this beats plain `-p`

| | plain `-p` | `-p --output-format=stream-json` |
|---|---|---|
| Latency-to-first-byte | one chunk at end | first token in ~1.5–2s |
| Thinking visibility | none | `💭 <preview>` in spinner |
| Tool transparency | hidden | `● Tool(args)` + `✓ result` lines |
| Token / cost accounting | none | per-turn footer with full breakdown |
| Operator perception | "is it hung?" | "I see it working live" |

## NDJSON parsing pitfalls (and the fix)

`QProcess.readyReadStandardOutput` fires per OS buffer flush, NOT per line. A single chunk may contain partial lines (e.g., `{"type":"stream_event"...` with no trailing `\n` if the event spans the buffer boundary).

**Solution** — line-buffer in `_stream_buf`:

```python
self._stream_buf += new_chunk
while "\n" in self._stream_buf:
    line, self._stream_buf = self._stream_buf.split("\n", 1)
    line = line.strip()
    if not line:
        continue
    if line.startswith("{") and line.endswith("}"):
        try:
            event = json.loads(line)
            self._handle_stream_event(event)
        except json.JSONDecodeError:
            self._render_plain_chunk(line + "\n")
    else:
        self._render_plain_chunk(line + "\n")
```

Trailing partial line stays in `_stream_buf` for the next chunk. Reset `_stream_buf = ""` at the start of each new turn.

## Required CLI flags

```
claude --dangerously-skip-permissions
       --output-format stream-json
       --include-partial-messages   ← critical: enables text_delta events
       --verbose                    ← without this stream-json is quieter
       --session-id <uuid>          ← OR --resume <uuid> (per session continuity)
       --system-prompt <persona>    ← only on first turn (--session-id path)
       -p <text>                    ← operator's message
```

Omit `--include-partial-messages` and you get assembled `assistant` events but no token-by-token deltas — no streaming feel.

## Telemetry chain shipped on top (v1.6.12 → v1.6.18)

- **v1.6.12** — Cumulative cost pill in card header + `/cost` slash + Ctrl+L = clear.
- **v1.6.13** — Auto-focus input on spawn + terminal min-height 240px.
- **v1.6.14** — Sticky-scroll terminal (don't yank operator down when reading scrollback).
- **v1.6.15** — Recent saved sessions inline in empty state (one-click resume).
- **v1.6.16** — Post-stream markdown formatting (code fences + inline code + bold) via QTextCharFormat over `_reply_start_pos..end` range.
- **v1.6.17** — Slash-command autocomplete popup (typing `/` shows filtered list; Up/Down/Enter/Esc navigate).
- **v1.6.18** — Live tool-name in spinner (`⠹ ● Bash…` instead of generic thinking) + rotating placeholder hints + `/devices` + `/export` slash commands.

## Anti-patterns

| # | Anti-pattern | Why bad |
|---|---|---|
| 1 | `_on_stdout` parses each chunk independently | Misses events spanning buffer boundaries. Always line-buffer. |
| 2 | Rendering the `assistant` event AS WELL as deltas | Doubles the text. Choose: deltas (streaming) OR assistant (final). |
| 3 | Forgetting `--include-partial-messages` | No `text_delta` events; back to all-at-end. |
| 4 | Calling `--system-prompt` on every turn | Only valid with `--session-id` (new session). Resume turns inherit the system prompt. |
| 5 | Cost-pill update inside `_on_stdout` per chunk | Costs only land on `result` event. Accumulate there, not per token. |
| 6 | Markdown formatting mid-stream | Closing ` ``` ` / `*` markers may not have arrived. Defer formatting to `_on_finished`. |

## Tested + verified

Inline harness in v1.6.11 commit (`/tmp/test_stream_parser.py`):
- 19 NDJSON events parsed from a real `claude -p` call (6 input tok / 176 output / $0.07 / 4.4s)
- Streamed text accumulated correctly via `text_delta` events
- `result` event produced the expected token+cost summary
- No thinking_delta / tool_use in that sample (simple "say hi" prompt); spawn a tools-using prompt to exercise those paths

## Phase-2 (when `ANTHROPIC_API_KEY` ships)

Replace `claude -p` subprocess with direct Anthropic SDK in `forge.spawn.anthropic_direct.py` pattern. Streaming `thinking_delta` + parallel `tool_use` + prompt-caching all in-process (no subprocess shell-out). Per-pane message history kept in-memory; session_uuid still serves as a stable identifier for resume-point cross-references. The stream-json parser stays as the fallback path when no API key is set.

## Composes with

- `rkoj-session-continuity-pattern-2026-05-21` — `--session-id` / `--resume` per pane (session_uuid is generated in bootstrap)
- `rkoj-phase1-memory-bootstrap-2026-05-21` — heartbeat / PROGRESS / inbox / resume bootstrap (env vars propagated to child)
- `agent-identity-eve` — persona injected via `--system-prompt` on first turn
- `jcode-agentic-loop-patterns-port-to-python` — long-term jcode-fidelity goal (Anthropic SDK direct, Phase-2)
- `forever-expanding-modular-architecture-doctrine` — substrate
