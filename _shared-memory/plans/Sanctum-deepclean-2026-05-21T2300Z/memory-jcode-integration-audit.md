# Author: RKOJ-ELENO :: 2026-05-21

# Memory-system ⇄ jcode integration gap audit
# Created at 2026-05-21T23:03Z

**Goal:** ensure every jcode-style agent spawned from RKOJ.exe correctly wires into the Sanctum `_shared-memory/` substrate (heartbeats / inbox / brain / resume / PROGRESS / cross-agent).

**Status:** READ-ONLY audit. Fix tasks queued in forward-plan.md lane R7.

## 1. Current spawn flow (post-read of `agents_tab.py`)

`AgentsView.spawn_agent(project_key, agent_name?, mode)` calls:

1. Read projects.json → pick display name.
2. Build `AgentSession(pane_id=uuid12, project_key, project_display, agent_name, mode, created_at)`.
3. Construct an `AgentCard` widget containing a QPlainTextEdit terminal + QLineEdit input + QProcess.
4. On first `_on_send()`:
   - Call `build_opening_prompt(project_key, agent_name, mode, accent)` from `persona.py` → returns a verbatim EVE persona block.
   - Append operator's text to that block.
   - QProcess starts `claude --dangerously-skip-permissions -p <prompt>` (ONE-SHOT).
5. stdout/stderr streamed back to terminal.
6. /save command writes a per-pane JSON to `_shared-memory/rkoj-qt/resume-points/<pane_id>.json`.

This is a **one-shot prompt** loop, not a persistent jcode-like session. Each turn re-prompts with appended history. No agent identity exists on disk; no heartbeat is written; the spawned `claude -p` process is short-lived per turn.

## 2. Memory-system entry points the agent SHOULD touch

| Surface | Path | Contract |
|---|---|---|
| Heartbeat | `_shared-memory/heartbeats/<slug>.json` | v1 schema, write every 30-60s while alive |
| Inbox | `_shared-memory/inbox/<slug>/*.json` | poll every 60s, archive on read |
| PROGRESS | `_shared-memory/PROGRESS/<display-name>.md` | append-only most-recent-first |
| Resume-point | `_shared-memory/resume-points/<display-name>/<ts>.json` | v1 schema; write before exit |
| Brain (read) | `_shared-memory/knowledge/_INDEX.md` + targeted entries | read at cold-start |
| Cross-agent (write) | `_shared-memory/cross-agent/<UTC>-<from>-to-<to>-<topic>.md` | drop only for human-readable handoffs |
| MASTER-PLAN | `_shared-memory/MASTER-PLAN.md` | read lane-relevant rows |
| OPERATOR-ACTION-QUEUE | `_shared-memory/OPERATOR-ACTION-QUEUE.md` | read open items, never edit |
| DIRECTIVES + WORK-TOWARD | `_shared-memory/DIRECTIVES.md` + `WORK-TOWARD.md` | read at cold-start |

## 3. Gap matrix

| # | Surface | Should-do | Currently does | Gap | Fix complexity |
|---|---|---|---|---|---|
| 1 | Heartbeat write | Spawn writes initial heartbeat + child re-writes every 30-60s | Nothing written | **No heartbeat** | XS |
| 2 | Per-agent identity | Slug + display + agent_identity:"EVE" persisted | In-memory only on parent | **Not on disk** | XS |
| 3 | PROGRESS append | Child appends milestones to display-name PROGRESS.md | Not written | **No PROGRESS** | S |
| 4 | Resume-point | Standard schema `resume-points/<display>/<ts>.json` | Non-standard path `_shared-memory/rkoj-qt/resume-points/<pane_id>.json` | **Wrong path + schema** | M |
| 5 | Inbox poll | Child polls inbox every 60s, surfaces [ASK]/[DELEGATE] | Not implemented | **No poll** | M |
| 6 | Brain read | Child reads relevant brain entries at cold-start | Persona block is static string | **No brain awareness** | S |
| 7 | Cross-agent write | Child can drop `cross-agent/` messages to siblings | Not implemented | **No sibling messaging** | S |
| 8 | Streaming + tool_use display | jcode-style thinking_delta + batch tool_use rendered inline | `claude -p` is one-shot text only | **Fundamental UX gap** | L (needs Anthropic SDK direct path) |
| 9 | Skill registry | Auto-load `~/.jcode/skills/*.md` style skills | Not implemented | **No skill awareness** | M |
| 10 | BM25 recall | Cross-session recall over prior turns | Not implemented | **No recall** | M |

## 4. Recommended bootstrap (Phase 1 — XS/S only this session)

Parent (`agents_tab.py::spawn_agent`) does BEFORE QProcess.start():

```python
import os, json, time
from pathlib import Path

# Resolve display + slug
slug = f"{project_key}-{pane_id[:6]}"
display = f"EVE on {project_display}"
heartbeat_path = SHARED_MEMORY / "heartbeats" / f"{slug}.json"
inbox_dir       = SHARED_MEMORY / "inbox" / slug
progress_path   = SHARED_MEMORY / "PROGRESS" / f"{display}.md"
resume_dir      = SHARED_MEMORY / "resume-points" / display

heartbeat_path.parent.mkdir(parents=True, exist_ok=True)
inbox_dir.mkdir(parents=True, exist_ok=True)
progress_path.parent.mkdir(parents=True, exist_ok=True)
resume_dir.mkdir(parents=True, exist_ok=True)

# Initial heartbeat
heartbeat_path.write_text(json.dumps({
    "schema_version": "sinister.heartbeat.v1",
    "agent_identity": "EVE",
    "agent": display,
    "agent_display": display,
    "slug": slug,
    "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "branch": f"agent/{project_key}/<topic>",
    "mode": mode,
    "session_status": "spawned-by-rkoj",
    "via": "rkoj-qt",
    "pane_id": pane_id,
}, indent=2))

# Pre-seed PROGRESS
if not progress_path.exists():
    progress_path.write_text(
        f"# Agent: {display}\n\nAppend-only progress log. Most recent at top.\n\n---\n\n"
    )

# Set env-vars on the child claude -p so it knows its identity
env = os.environ.copy()
env["SINISTER_AGENT_DISPLAY"] = display
env["SINISTER_AGENT_SLUG"] = slug
env["SINISTER_PANE_ID"] = pane_id
env["SINISTER_PROJECT_KEY"] = project_key
env["SINISTER_HEARTBEAT_PATH"] = str(heartbeat_path)
env["SINISTER_PROGRESS_PATH"] = str(progress_path)
env["SINISTER_RESUME_DIR"] = str(resume_dir)
proc.setProcessEnvironment(_qenv_from_dict(env))
```

QTimer in parent re-writes heartbeat every 30s (refresh ts_utc + last_seen_age) while card is alive. On card-close, heartbeat is updated with `session_status:"ended"` then deleted on next sweep.

## 5. Phase-2 wishlist (after this session)

- Async inbox poller in the AgentCard (`QTimer @ 60s` → `inbox_dir.glob("*.json")` → render alerts in card header).
- Cross-agent message-write button in card UI.
- Skill registry browser (extensions/skills/).
- Switch from `claude -p` one-shot to Anthropic-SDK direct path (per `jcode-agentic-loop-patterns-port-to-python`) — gives streaming thinking_delta + batch tool_use + persistent context. Gated by `ANTHROPIC_API_KEY` env var (operator-action-queue item).
- BM25 recall via `forge-memory-bridge` (already shipped per brain entry; just wire it).

## 6. Smoke tests (post-Phase-1)

| # | Test | Pass criteria |
|---|---|---|
| 1 | Spawn one agent | `_shared-memory/heartbeats/sanctum-<pane6>.json` appears within 1s |
| 2 | Heartbeat refresh | ts_utc updates every 30s while card alive |
| 3 | Close card | heartbeat file marks "ended" then deletes |
| 4 | PROGRESS append | `_shared-memory/PROGRESS/EVE on sanctum.md` exists with seed header |
| 5 | Env propagation | Spawned child sees `SINISTER_AGENT_SLUG` in env (verify via test prompt) |

## 7. Composes-with

- `agent-identity-eve` (persona)
- `jcode-agentic-loop-patterns-port-to-python` (Phase-2 architecture)
- `jcode-feature-matrix` (parity map)
- `forge-memory-bridge` BM25 (Phase-2 recall)
- `forever-expanding-modular-architecture-doctrine` (substrate)
- `sinister-rkoj-extensibility-doctrine` (plugin contract)

---

End of audit.
