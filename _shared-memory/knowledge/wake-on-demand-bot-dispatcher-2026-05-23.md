<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# Wake-on-demand bot dispatcher pattern

**Status:** proposed 2026-05-23 — operator directive *"have everything auto start or idle, sleep until a agent needs it then the agent can call and use anything it needs to"*.
**Anchor:** `Sanctum-agent-stack-readiness-2026-05-23T0820Z/forward-plan.md` C1.

## The problem

The 13 specialist bot MCPs (sentinel, translator, librarian, watcher, auditor, triage, scribe, curator, custodian, stealth-browser, researcher, vault, sinister-bus) currently sit in one of two states:

- **Always-on** — Custodian-style scheduled-task daemons that consume RAM continuously even when no agent calls them. RAM cost: ~50-150 MB per bot × 13 bots = ~1.5 GB always-resident. Most of this is import overhead + idle Python interpreter, not active work.
- **Always-off** — Bots that don't have a scheduled-task entry sit at zero until an MCP client (Claude Code, RKOJ) spawns them via stdio. Cold-start each call: ~500ms Python interpreter + module imports + MCP handshake. This is the typical case for sentinel/translator/etc. that aren't long-running.

Operator wants a middle ground: bot wakes when an agent asks for it, stays warm for a burst window, sleeps when idle. Saves RAM + still gives sub-second response to sequential calls.

## The pattern

`sinister-bus` (the dispatcher) gains a lazy-spawn + idle-kill loop:

```python
# sinister-bus/server.py (sketch)

ALIVE_UNTIL: dict[str, float] = {}  # bot-name → epoch when it idle-kills
SUBPROCS:    dict[str, subprocess.Popen] = {}
IDLE_TTL = 300.0  # 5 minutes of inactivity before idle-kill
HOT_BOTS = {"custodian", "sinister-bus"}  # never sleep

def _ensure_alive(bot: str) -> subprocess.Popen:
    """Lazy-spawn bot if not alive; reset alive-until."""
    now = time.time()
    proc = SUBPROCS.get(bot)
    if proc is None or proc.poll() is not None:
        cfg = _read_bot_config(bot)  # cwd, python.exe path, server.py
        proc = subprocess.Popen(
            [cfg["python"], cfg["server"]],
            cwd=cfg["cwd"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=cfg["env"],
        )
        # Block until bot prints "ready" on stderr (MCP handshake fingerprint)
        _wait_ready(proc, timeout_s=5.0)
        SUBPROCS[bot] = proc
    ALIVE_UNTIL[bot] = now + IDLE_TTL
    return proc

def _idle_sweep():
    """Run every 60s. Kill any subproc past its alive-until."""
    now = time.time()
    for bot, until in list(ALIVE_UNTIL.items()):
        if bot in HOT_BOTS:
            continue
        if until < now:
            proc = SUBPROCS.get(bot)
            if proc and proc.poll() is None:
                try: proc.terminate()
                except Exception: pass
            SUBPROCS.pop(bot, None)
            ALIVE_UNTIL.pop(bot, None)

@mcp.tool()
def bus_dispatch(target: str, args: dict, context_id: str | None = None) -> dict:
    proc = _ensure_alive(target)
    # forward via MCP protocol over stdin/stdout
    ...
```

The bus itself stays hot (one always-on Python process). Bots cold-start on first dispatch, stay warm 5 minutes, then sleep.

## Reusable patterns codified

1. **Hot-set / cold-set split** — explicit `HOT_BOTS` set for always-on; everything else is wake-on-demand. Operator decides which bots are hot at config-time.
2. **Idle-TTL is per-bot configurable** — sentinel might need 5 min (operator watching alarms), librarian 30 sec (one-shot recall). Override via `bot-config.json` per bot.
3. **Cold-start synchronous, idle-kill async** — dispatch path blocks until bot ready (sub-second). Idle-kill runs on a 60s timer thread; never blocks a dispatch.
4. **Health check decoupled from wake** — `bus_health(target)` reads ALIVE_UNTIL + SUBPROCS without touching them. Peek doesn't wake.
5. **Restart-on-crash** — if subprocess.poll() returns non-None, next dispatch re-spawns. Bots crash silent → bus auto-heals.
6. **Single stdio multiplexer** — bus owns each bot's stdin/stdout; agents talk to bus, bus translates. Avoids 13 MCP servers fighting for stdio.

## Anti-patterns

1. **Don't keep all 13 bots always-on** — wastes ~1.5 GB RAM continuously. The operator's machine has finite memory.
2. **Don't restart Python interpreter per call** — kills the warm-cache + import-cost benefits. The whole point of the dispatcher is amortizing import cost across a burst.
3. **Don't share subprocess.Popen objects across threads without a lock** — Python's subprocess is fine for spawn/poll/terminate from multiple threads, but stdin writes need serialization. Add a `threading.Lock` per bot.
4. **Don't make bots reach back into bus to wake siblings** — recursive wake-cascades risk deadlock. Bots are leaves; bus is the root.
5. **Don't let HOT_BOTS grow unchecked** — every entry there is permanent RAM. Default ZERO hot bots except sinister-bus itself + custodian (24/7 cleanup). Anything else needs operator justification.
6. **Don't wake on `health()` calls** — peek must be cheap; if you wake on health you can't poll a fleet without bringing them all up.

## Empirical anchors (when implemented)

To validate after implementation:

- Cold-start time for `librarian.recall("foo")` from cold: should be <1 s (Python import + faiss load is the long path)
- Warm-call to same after 5 sec: <50 ms (just MCP roundtrip)
- Idle-kill at T+300s: subprocess gone, ALIVE_UNTIL clean
- RAM resident: 1 hot bot × ~100 MB = ~100 MB baseline, vs current ~1.5 GB if everything pre-loaded

## Implementation gate

Sibling-lane edit required: `D:\Sinister Sanctum\_sinister-skills\12_LLM_ORCHESTRATION\agents\sinister-bus\server.py`. That's NOT in `D:\Sinister Sanctum\projects\` — it's part of the `_sinister-skills` mirror that the sinister-bus agent owns. Drop a [DELEGATE] in `inbox/sinister-bus/` rather than direct-edit per canonical-10.

The ~50-line patch is small enough that a single agent turn can ship + test. Implementation prereqs:
- Each bot has a stable `server.py` entry point (confirmed for all 13)
- Each bot's `requirements.txt` deps are installed (confirmed: mcp, faiss-cpu, anthropic, numpy)
- MCP stdio handshake is identifiable in stderr (the FastMCP server prints a startup line — that's the "ready" signal)

## Composes with

- `sanctioned-bypasses-doctrine-2026-05-21.md` (2026-05-23 block) — bots spawn freely; this pattern just makes spawn lazy.
- `launcher-v6-concise-rewrite-2026-05-23.md` — launcher spawns child Claude eagerly; bot dispatcher is the inner-loop optimization.
- `forever-expanding-modular-architecture-doctrine.md` — each new bot plugs into the bus; lazy-spawn means adding a 14th bot doesn't add RAM cost unless it gets called.
- `jcode-feature-matrix.md` row 11 (background memory consolidation) — same idea applied to memory-consolidate.ps1 instead of bots.

## When this pattern doesn't apply

- **Streaming bots** (stealth-browser running a long page interaction) — these should pin themselves alive while in active session. Bus marks them busy + extends TTL on every progress event.
- **Bot-to-bot calls** — if librarian calls scribe, the wake-cascade is OK but adds latency. Pre-warm dependent bots when a known cascade starts.
- **Operator-pinned bots** — if operator says "keep curator hot all day for the daily-digest run", add to HOT_BOTS in config. Default no.
