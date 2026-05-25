<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Per-agent intelligence-level control (Sanctum Console → live Claude session)

**Status:** fixed
**Tags:** claude-code, model, intelligence, console, agent, inbox, [config], two-track
**Related:** `gitea-self-host.md`, `per-agent-branch-convention.md`

## Problem

Operator wants to change a running agent's model (Opus 4.7 / Opus 4.6 + fast / Sonnet 4.6 / Haiku 4.5) with one click from the Sanctum Console, and have the agent "continue working" at the new level — no kill, no respawn, no operator typing `/model`.

## Why this is hard

Claude Code controls model selection per-session. There is **no IPC** that lets an outside process (e.g. the Console at :5077) reach into a live `claude` REPL and force a `/model` swap. The session's stdin is owned by the user, not by us.

## Fix — the two-track pattern

We can't reach in. We CAN ask the agent to reach in itself, AND we CAN make sure its next respawn boots at the new level. Both tracks are wired:

### Track 1 — persistent (respawn-safe)
- Console writes `{model, fast, changed_at, changed_by}` to `D:\Sinister Sanctum\_shared-memory\agent-prefs.json` keyed by agent display name.
- `start-sinister-session.ps1` reads that file at spawn time and injects `--model <name>` into the `claude` invocation. The new window boots at the requested level. (Verified: `claude --help` confirms `--model <model>` accepts both full names like `claude-sonnet-4-6` and aliases `opus`/`sonnet`/`haiku`.)

### Track 2 — live (mid-task swap)
- The same Console POST also drops an inbox message into `_shared-memory/_inbox/<agent>/messages.jsonl` with tag `[config, model]` and body `[CONFIG] model=<X> fast=<Y> — call /model <X> now, ack, continue.`
- A standing rule in `_shared-memory/DIRECTIVES.md` (prepended 2026-05-19) tells every agent: on `inbox_poll` (Rule 9 mandates per-turn poll) — if you see `[CONFIG] model=<X>`, ack via `inbox_reply`, then invoke `/model <X>` slash command yourself, then continue your prior task at the new level.

Worst case the swap lands on the agent's next turn boundary, NOT mid-thinking. Best case the operator clicks → next turn → swap. No restart visible to the operator.

## API surface

| Endpoint | Body | Purpose |
|---|---|---|
| `GET /api/agents/prefs` | – | All known prefs as one dict. |
| `GET /api/agents/{name}/intelligence` | – | Current level for one agent (`{ok, agent, model, fast}`). |
| `POST /api/agents/{name}/intelligence` | `{model, fast?}` | Persist + queue `[CONFIG]` inbox msg. Returns `{ok, agent, model, fast, applied: "persisted; inbox notified"}`. |

Server-side code: `automations\window-manager\server.py` Block 1 (Thread 4) at lines ~391-462. Helpers `_load_agent_prefs` / `_save_agent_prefs` write JSON sorted-indented for diff-friendliness.

## Discoveries

### 2026-05-19 04:55 by Sinister Sanctum
Plan called for `_inbox_mod.send(to=, frm=, body=, tags=)` but the real exported signature in `_shared.inbox` is `inbox_send(to_agent=, message=, from_agent=, tags=)` (verified at `D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\_shared\inbox.py:115`). Agent A used the real signature; other agents adding inbox sends should follow suit.

### 2026-05-19 05:10 by Sinister Sanctum
For the launcher hook to find the prefs entry, used `$prefs.PSObject.Properties[$AgentName].Value` (not `$prefs.$AgentName`) because agent names contain spaces ("Sinister Snap API") and PS doesn't dot-access cleanly there. Idiom that works:

```powershell
$prop = $prefs.PSObject.Properties[$AgentName]
if ($prop -and $prop.Value -and $prop.Value.model) { ... }
```

Wraps in try/catch so a corrupt JSON file never stops a spawn.
