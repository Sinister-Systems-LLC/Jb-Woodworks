# Sibling-Active-Launch Coordination Pattern

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Empirical origin:** 2026-05-21T10:25Z-11:30Z fleet expansion — operator launched 3 sibling agents (Forge, Term, RKOJ) into the same Sanctum tree within 90 minutes while sanctum was mid-session. Two earlier 09:19Z R4 collisions on `start-sinister-session.ps1` proved the pre-doctrine path is fragile.

## When this fires

You are running and the operator says ONE of:
- *"I'm launching another agent right now"*
- *"X agent is opening now, don't interfere"*
- *"start a Y agent in parallel"*
- *"we have A, B, C, D agents all running"*

OR you observe symptoms:
- A new `_shared-memory/inbox/<slug>/` directory appears mid-session
- A new heartbeat file mtime changes outside your slug
- A file you wanted to edit returns "File has been modified since read"
- The same project's PROGRESS.md grows entries you didn't author

## The doctrine (5 steps, in order)

### Step 1 — Drop a [HELLO] in their inbox FIRST

Before doing any work on shared files, write:
```
_shared-memory/inbox/<their-slug>/<UTC>-hello-from-<your-slug>.json
```

Schema:
```json
{
  "tag": "[HELLO]",
  "from": "<your-slug>",
  "to": "<their-slug>",
  "ts_utc": "<ISO>",
  "your_lane": "<description of THEIR full ownership>",
  "my_lane_this_session": "<description of YOUR work surface>",
  "what_im_shipping_for_you_to_consume": [...],
  "what_id_like_from_you": "[HELLO-ACK] in _shared-memory/inbox/<your-slug>/",
  "coordination_channel": "disk-first + Ruflo MCP backup"
}
```

Why first: you're declaring boundaries proactively. If they collide, they have a paper trail saying "you agreed I owned X".

### Step 2 — Work on COMPLEMENTARY surfaces, not their source tree

For each sibling, identify ONE lane discipline rule:

| Sibling display | Their owned source | Your no-touch list |
|---|---|---|
| Sinister Forge | `projects/sinister-forge/source/` | + `automations/resume-point-write.ps1` (Forge bridge hot-paths it) + `automations/start-sinister-session.ps1` (cold-start) |
| Sinister Term | `projects/sinister-term/source/term/` | + (when Track B opens) `projects/sinister-term/source/term-rs/` |
| RKOJ | `automations/window-manager/` | + window-manager EXE build artifacts |
| Sinister Panel | `projects/sinister-panel/` | + Hetzner deploy scripts in panel-deploy/ |
| Kernel APK | `projects/sinister-kernel-apk/` | + keybox per-signing flows |
| (other sibling) | `projects/<their-slug>/source/` (default) | + any per-project automation under `automations/<their-slug>-*` |

Your safe surfaces (Sanctum / coordination agent):
- `tools/*` (NEW tool dirs; existing tools = check authorship before edit)
- `automations/*` EXCEPT the no-touch list above
- `_shared-memory/knowledge/*`
- `_shared-memory/inbox/<other-slug>/` (DROP only; never read+modify their pending tags)
- `_shared-memory/cross-agent/` (always safe; this is the thread store)
- `_shared-memory/PROGRESS/<your-display>.md` (your own log)
- `_shared-memory/resume-points/<your-project>/` (your own checkpoints)

### Step 3 — Cross-agent thread for the human-readable handoff

Write one markdown at:
```
_shared-memory/cross-agent/<UTC>-<from-slug>-to-<to-slug-list>-<topic>.md
```

This is what the operator reads at end-of-turn to understand the coordination. Cover:
- Operator triggers (verbatim quotes with timestamps)
- Table of agent → owned source tree → no-touch list
- What each agent is shipping this session
- What's deliberately NOT touched
- Reply protocol

### Step 4 — Use Ruflo MCP hive-mind as backup channel

If your session has Ruflo MCP loaded (most do):

```python
mcp__ruflo__hive-mind_init(topology="mesh", consensus="raft", queenId="<your-slug>")
mcp__ruflo__memory_store(
    key=f"sinister-fleet/coordination/{utc}",
    namespace="sinister-coordination",
    tags=["coordination", "hello", "<your-slug>", "<their-slug>"],
    value={...full hello payload...}
)
```

Why: even if their session is cold-start AND doesn't read disk inbox in time, they'll see the broadcast via `mcp__ruflo__memory_search`.

### Step 5 — Heartbeat-check before edits to shared files

Right before any Edit/Write on a file under a no-touch boundary OR on a "shared" file (automations/session-templates/, agent-host-routing.md, etc):

```bash
# Re-read the file to detect siblings' mid-edits
test -f <path> && md5sum <path>
```

If the hash differs from what you last read, re-read the file fresh.

If you DO collide ("File has been modified since read"), DO NOT retry blindly:
- Re-read fresh
- See if the sibling already shipped what you were about to ship → release the row
- If you still need to ship → make your edit narrower (smaller diff window) so collision risk drops

## Anti-patterns (what NOT to do)

- ❌ Editing `automations/start-sinister-session.ps1` without operator's explicit authorization while 2+ siblings are mid-cold-start
- ❌ Reading `_shared-memory/inbox/<other-slug>/<UTC>-*.json` files marked for them (your slug isn't them)
- ❌ Writing to `_shared-memory/PROGRESS/<other-display>.md` (their log; they own it)
- ❌ Resetting a branch / force-pushing while a sibling has uncommitted work on it (canonical-11)
- ❌ Adding rows to `projects.json` / `agent-prefs.json` without bumping `version` (siblings cache by version)
- ❌ Asking the operator "should I add agent X to my registry?" when the registry is glob-discovered

## Composes with

- `_shared-memory/knowledge/forever-expanding-modular-architecture-doctrine.md` (this session) — the meta-doctrine; this is the runtime expression
- `automations/session-contracts.md` CONTRACT 5 (CROSS-AGENT COMMUNICATION) — base contract
- `_shared-memory/knowledge/multi-agent-branch-contention-isolation-pattern.md` (prior session 2026-05-20) — the FAILURE case this pattern prevents
- `_shared-memory/knowledge/sanctum-coaudit-pattern.md` (per prior PROGRESS; was reverted from disk by sibling churn — pending re-recreation)
- `automations/agent-host-routing.md` — multi-provider routing rules; one expression of "everyone is plugged into everyone"

## When to revisit

- A new sibling type emerges (e.g. operator-friend agents like Sinister Freeze's `freeze` lane — different from internal-fleet agents because their AUP-RESPECT scope is narrower)
- The number of simultaneous siblings exceeds 6 (we've validated 5+1 today; >6 may need a coordinator agent dedicated to this doctrine)
- A collision pattern not yet enumerated above appears (document it and add to the no-touch table)
