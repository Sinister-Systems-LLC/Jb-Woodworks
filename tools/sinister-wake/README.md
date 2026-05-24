<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# sinister-wake :: wake-on-demand bot dispatcher (C.5)

**Status:** standalone implementation ready; sinister-bus integration deferred to bus lane.
**Doctrine:** `_shared-memory/knowledge/wake-on-demand-bot-dispatcher-2026-05-23.md`
**Implements:** C.5 of `_shared-memory/plans/sanctum-complete-and-expand-2026-05-23T1145Z/master-plan.md`

## What it does

Wraps each bot's MCP server in a lazy-spawn + idle-kill loop. Bots cold-start on first call, stay warm for a configurable TTL (default 300s), get terminated when idle. HOT_BOTS (`custodian`, `sinister-bus`) never sleep.

Saves **~1.5 GB always-resident RAM** across 13 bots vs always-on; preserves sub-second response for sequential calls vs always-off cold-start.

## Quick usage

```python
from sinister_wake.wake_dispatcher import WakeDispatcher, start_sweep_thread

dispatcher = WakeDispatcher()  # loads bot-config.json from this dir
sweep = start_sweep_thread(dispatcher)  # 60s timer

# In sinister-bus's dispatch handler:
proc = dispatcher.ensure_alive("librarian")  # spawns if cold
# ... forward MCP call over proc.stdin / proc.stdout ...

# Peek without waking:
state = dispatcher.bus_health_target("sentinel")
# -> {name: "sentinel", state: "cold"|"warm"|"hot", ttl_remaining_sec: N, pid: int|None, in_hot_set: bool}

# Clean exit:
dispatcher.shutdown_all()
```

## Smoke test

```bash
python wake_dispatcher.py
```

Outputs config + peek-state for every configured bot (no wake). Example output:
```
WakeDispatcher loaded config from D:\...\tools\sinister-wake\bot-config.json
  hot_bots: ['custodian', 'sinister-bus']
  global_idle_ttl_sec: 300.0
  configured bots: ['auditor', 'curator', ...]

Per-bot health (peek without wake):
  auditor              state=cold   ttl=   0.0s pid=None hot=False
  custodian            state=cold   ttl=   0.0s pid=None hot=True
  ...
```

## Integration path (for sinister-bus lane)

Three steps to wire in (~30 LOC patch):

1. Add `from sinister_wake.wake_dispatcher import WakeDispatcher, start_sweep_thread` to `bots/agents/sinister-bus/server.py` (with sys.path.append for the tools dir).
2. Instantiate `_DISPATCHER = WakeDispatcher()` at module load; call `start_sweep_thread(_DISPATCHER)` once.
3. Expose 3 new MCP tools:
   - `@mcp.tool() bus_wake(target: str) -> dict` → calls `_DISPATCHER.ensure_alive(target)` + returns health.
   - `@mcp.tool() bus_sleep(target: str) -> dict` → drops `target` from `_DISPATCHER.alive_until` so next sweep kills it.
   - `@mcp.tool() bus_health_target(target: str) -> dict` → calls `_DISPATCHER.bus_health_target(target)`.
4. (Optional) Modify existing `dispatch(target, args)` to call `_ensure_alive(target)` BEFORE forwarding — converts the existing dispatch path to wake-on-demand transparently.

## Config (`bot-config.json`)

Per-bot `idle_ttl_sec` override. Operator-editable:

| Bot | Default TTL (s) | Rationale |
|---|---|---|
| librarian | 180 | RAG one-shots; short |
| scribe | 120 | Haiku is cheaper to cold-start than keep warm |
| curator | 120 | Same |
| auditor | 120 | Fast burst pattern |
| sentinel | 600 | Operator polls periodically |
| translator | 600 | |
| vault | 600 | |
| stealth-browser | 600 | Chrome launch is expensive (~5s); keep warm |
| custodian / sinister-bus | (hot) | Never sleep |

## Anti-patterns

1. **Don't auto-enable in production without bus-lane review.** This module is standalone-ready; the bus lane should review the integration commit before merging.
2. **Don't put non-MCP bots in `hot_bots`.** HOT means "always alive subprocess"; only MCP-spec'd bots belong here.
3. **Don't tune `idle_ttl_sec` < 60s.** The sweep timer is 60s; shorter TTLs get killed before they're useful.
4. **Don't call `ensure_alive` from inside the sweep thread.** It can deadlock if both fight for the lock. Sweep should only terminate; spawning is dispatch-path only.
5. **Don't skip the `_wait_ready` step.** MCP handshake is async; dispatching to a not-yet-ready bot loses the first message.

## Reference

- Doctrine: `_shared-memory/knowledge/wake-on-demand-bot-dispatcher-2026-05-23.md` (proposed → implementation now ready)
- Master plan: C.5 of `_shared-memory/plans/sanctum-complete-and-expand-2026-05-23T1145Z/master-plan.md`
- Operator directive: 2026-05-23: *"have everything auto start or idle, sleep until a agent needs it then the agent can call and use anything it needs to"*
- Author: RKOJ-ELENO :: 2026-05-24
