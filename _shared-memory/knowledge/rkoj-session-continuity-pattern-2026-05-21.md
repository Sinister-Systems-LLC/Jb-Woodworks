# Author: RKOJ-ELENO :: 2026-05-21

# RKOJ session-continuity pattern (claude --session-id → --resume)

**Status:** doctrine, implemented v1.6.3
**Composes with:** `rkoj-phase1-memory-bootstrap-2026-05-21`, `agent-identity-eve`, `jcode-agentic-loop-patterns-port-to-python`, `forever-expanding-modular-architecture-doctrine`.

---

## TL;DR

Every RKOJ-spawned agent card gets a **full UUID4 session_uuid** at bootstrap. First turn uses `claude --dangerously-skip-permissions --session-id <uuid> --system-prompt <persona> -p <message>`. Subsequent turns use `claude --dangerously-skip-permissions --resume <uuid> -p <message>` — claude tracks conversation server-side, so no history-replay per turn.

## Why this matters

v1.6.2 prior pattern: send accumulated history per turn (capped to last 6 turns). Each turn = `claude -p "User: msg1\nEVE: reply1\nUser: msg2..."`. Latency ~10s per turn baseline + bloat as history grew. Token spend grew with conversation length.

v1.6.3 new pattern: claude maintains session state internally. Each turn = `claude --resume <uuid> -p "your latest message"`. Latency ~5s per follow-up turn (empirical). Token spend constant per turn.

## Empirical verification (shell test, 2026-05-21)

```bash
SID=$(python -c "import uuid; print(uuid.uuid4())")
# Turn 1 — create session
claude --dangerously-skip-permissions --session-id "$SID" -p "My favorite color is teal. Remember it."
# Reply: "Noted — favorite color is teal."

# Turn 2 — resume + ask
claude --dangerously-skip-permissions --resume "$SID" -p "What did I tell you?"
# Reply: "Your favorite color is teal."

# Turn 3 — resume again
claude --dangerously-skip-permissions --resume "$SID" -p "Repeat it once more."
# Reply: "Teal."
```

True per-pane memory works. Wall-clock per turn: 11.8s / 4.5s / 5.5s — first-turn overhead amortizes.

## Anti-patterns

| # | Anti-pattern | Why bad |
|---|---|---|
| 1 | Re-using `--session-id <uuid>` on second turn | claude errors `Session ID <uuid> is already in use`. Use `--resume <uuid>` for follow-ups. |
| 2 | Using `claude -c` / `--continue` for per-pane sessions | `--continue` resumes the most recent for the CWD — N panes in same CWD all share one session. Use `--session-id`/`--resume` for per-pane isolation. |
| 3 | Embedding persona in every turn instead of `--system-prompt` | The system prompt persists across the session automatically. Repeating it bloats each turn + risks the model thinking it's a fresh user message. |
| 4 | Short pane_id (< full UUID) as session_uuid | claude requires a valid UUID format (8-4-4-4-12 with hyphens). 12-hex-char pane_ids won't work. Generate `str(uuid.uuid4())` separately. |
| 5 | Storing session_uuid only in-memory | Lose-on-crash. Persist to resume-point JSON so operator can pick up from any terminal via `claude -r <uuid>`. |

## Implementation skeleton (RKOJ agents_tab.py)

```python
# AgentSession dataclass:
session_uuid: str = ""

# Bootstrap:
def _bootstrap_agent_memory(sess: AgentSession) -> None:
    if not sess.session_uuid:
        sess.session_uuid = str(uuid.uuid4())
    # ... heartbeat / PROGRESS / inbox / resume dirs ...

# Per-turn args build:
args = ["--dangerously-skip-permissions"]
if self.session.mode == "claude-haiku":
    args += ["--model", "haiku"]
elif self.session.mode == "claude-opus":
    args += ["--model", "opus"]

if self._first_turn:
    args += ["--session-id", self.session.session_uuid,
             "--system-prompt", persona_text,
             "-p", user_text]
else:
    args += ["--resume", self.session.session_uuid,
             "-p", user_text]
```

## Composes with

- `rkoj-phase1-memory-bootstrap-2026-05-21` — Phase-1 disk presence (heartbeat / PROGRESS / inbox / resume). session_uuid is generated here.
- `agent-identity-eve` — persona injected via --system-prompt (set once, persists across session).
- `jcode-agentic-loop-patterns-port-to-python` — long-term jcode-fidelity path is Anthropic SDK direct (Phase-2). This session-continuity pattern is the bridge until that's wired.
- `forever-expanding-modular-architecture-doctrine` — substrate.

## Phase-2 path (when ANTHROPIC_API_KEY ships)

Replace `claude -p` subprocess with direct Anthropic SDK in `forge.spawn.anthropic_direct.py` pattern. Streaming thinking_delta + batch tool_use + persistent context inside RKOJ.exe (no subprocess shell-out). Per-pane Anthropic message history kept in-memory (Python dict) instead of claude-CLI session file.
