<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Author: RKOJ-ELENO :: 2026-05-21

# RKOJ Phase-1 memory⇄jcode bootstrap pattern

**Status:** doctrine, implemented
**Composes with:** `agent-identity-eve`, `jcode-agentic-loop-patterns-port-to-python`, `jcode-feature-matrix`, `forever-expanding-modular-architecture-doctrine`, `rkoj-ui-exact-spec-2026-05-21`.

---

## TL;DR

Every agent spawned by RKOJ.exe must be DISCOVERABLE to siblings within seconds — heartbeat on disk, PROGRESS seeded, identity in env. Phase-1 is XS-complexity, all-disk, no network. Operator directive (2026-05-21): *"make sure the memory system we use works perfect with the jcode system."*

## Three-part bootstrap

Implemented at `projects/rkoj/source/sinister_rkoj_qt/agents_tab.py`:

### 1. `_bootstrap_agent_memory(sess)` — disk presence

Pre-creates four canonical dirs + writes initial heartbeat at spawn time:

```python
sess.slug         = f"{sess.project_key}-{sess.pane_id[:6]}"   # e.g. "sanctum-9a1f2b"
sess.display_name = f"EVE on {sess.project_display}"           # e.g. "EVE on Sinister Sanctum"
sess.heartbeat_path = SHARED_MEMORY/"heartbeats"/f"{sess.slug}.json"
sess.progress_path  = SHARED_MEMORY/"PROGRESS"/f"{sess.display_name}.md"
sess.resume_dir     = SHARED_MEMORY/"resume-points"/sess.display_name
sess.inbox_dir      = SHARED_MEMORY/"inbox"/sess.slug
```

Heartbeat payload (schema_version `sinister.heartbeat.v1`):

```json
{
  "schema_version": "sinister.heartbeat.v1",
  "agent_identity": "EVE",
  "agent": "EVE on Sinister Sanctum",
  "agent_display": "EVE on Sinister Sanctum",
  "slug": "sanctum-9a1f2b",
  "ts_utc": "2026-05-21T22:59:33Z",
  "branch": "agent/sanctum/<topic>",
  "mode": "claude",
  "session_status": "spawned-by-rkoj",
  "via": "rkoj-qt",
  "pane_id": "9a1f2bc4e7d3",
  "project_key": "sanctum"
}
```

PROGRESS seed (only when file is new) writes the standard `# Agent: <display>` header + a single spawn entry.

### 2. `_refresh_heartbeat(sess, status)` — 30s QTimer keepalive

`AgentCard.__init__` constructs a `QTimer @ 30_000ms` that re-writes the heartbeat with a fresh `ts_utc` + current `session_status` (idle / busy / awaiting-input / online / offline). Per-card timer; stops on `_on_close()` / `shutdown()` with `session_status: "ended"`.

### 3. `_make_child_env(sess)` — QProcessEnvironment identity propagation

The QProcess spawned in `_on_send()` gets these env vars so the child `claude` process knows its identity:

```
SINISTER_AGENT_DISPLAY     = "EVE on Sinister Sanctum"
SINISTER_AGENT_SLUG        = "sanctum-9a1f2b"
SINISTER_PANE_ID           = "9a1f2bc4e7d3"
SINISTER_PROJECT_KEY       = "sanctum"
SINISTER_HEARTBEAT_PATH    = "_shared-memory/heartbeats/sanctum-9a1f2b.json"
SINISTER_PROGRESS_PATH     = "_shared-memory/PROGRESS/EVE on Sinister Sanctum.md"
SINISTER_RESUME_DIR        = "_shared-memory/resume-points/EVE on Sinister Sanctum"
SINISTER_INBOX_DIR         = "_shared-memory/inbox/sanctum-9a1f2b"
SINISTER_AGENT_IDENTITY    = "EVE"
SINISTER_AUTHORSHIP        = "RKOJ-ELENO"
```

Future: spawned agents read these at cold-start to know where to write their own heartbeats / PROGRESS / resume-points without needing to recompute paths.

## Phase-2 wishlist (deferred)

Per `_shared-memory/plans/Sanctum-deepclean-2026-05-21T2300Z/memory-jcode-integration-audit.md` § 5:

- Async inbox poller in AgentCard (QTimer @ 60s scanning `<inbox_dir>/*.json`).
- Cross-agent message-write button in card UI.
- Skill registry browser (extensions/skills/).
- Switch from `claude -p` one-shot to Anthropic-SDK direct path (gated by `ANTHROPIC_API_KEY` env var) — unlocks streaming thinking_delta + batch tool_use + persistent context per `jcode-agentic-loop-patterns-port-to-python`.
- BM25 recall via `forge-memory-bridge` (already shipped; just wire into RKOJ card cold-start).

## Anti-patterns

| Anti-pattern | Why bad |
|---|---|
| Block agent spawn on disk hiccups | UX disaster. Memory bootstrap is best-effort; wrap in `try: ... except: pass`. |
| Skip pre-creating dirs before write | Child writes fail silently if parent doesn't exist. Always `mkdir(parents=True, exist_ok=True)`. |
| Non-standard schema (e.g. `_shared-memory/rkoj-qt/resume-points/`) | Breaks sibling discovery + reuse. Schema is `_shared-memory/resume-points/<display>/<ts>.json`. |
| Skip the heartbeat refresh timer | Heartbeat goes stale within 2 minutes; presence pill flips to RED. Refresh every 30s minimum. |
| Skip env propagation | Child can't write its own heartbeat without re-computing paths. |
| Heartbeat path uses slug; PROGRESS uses display-name | Confusing duality but per existing convention: heartbeats by slug (machine), PROGRESS by display (human). Document this fork. |

## Smoke tests (post-implementation)

| # | Test | Pass criteria |
|---|---|---|
| 1 | Spawn 1 agent | `_shared-memory/heartbeats/<slug>.json` appears within 1s |
| 2 | Wait 30s + 5s | `ts_utc` in heartbeat updates |
| 3 | Close card | heartbeat `session_status` flips to `ended` |
| 4 | PROGRESS append | `_shared-memory/PROGRESS/EVE on <project>.md` exists with seed |
| 5 | Env propagation | (deferred — needs spawned-child test) |

## Composes-with

- `agent-identity-eve` — every spawned agent self-references as EVE.
- `jcode-agentic-loop-patterns-port-to-python` — Phase-2 architecture (Anthropic SDK direct).
- `forever-expanding-modular-architecture-doctrine` — disk-first surface + slug-namespaced.
- `multi-agent-branch-contention-isolation-pattern` — per-agent branches stay isolated when each agent knows its slug.
- `rkoj-ui-exact-spec-2026-05-21` § 7 — persona injection (parent does opening prompt; env vars give child its identity).
