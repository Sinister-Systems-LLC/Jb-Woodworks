<!-- decay:
  category: architecture
  confidence: 1.0
  reinforcements: 0
  half_life_days: 365
-->
# Overseer Monitors Doctrine — THREE sub-agents (operator hard-canonical 2026-05-25)

**Author:** RKOJ-ELENO :: 2026-05-25

## Operator verbatim (across iter-28)

> *"have the overseer make a agent for this part to analyse the claude rate limits and auto improve them"* (Image #7)
>
> *"tie the over screen rate limit watcher into the same thing for token watcher. so the overseer project will have two sub agents. one for token monitor and incrasing of system also features where we can like make sure all tokens are used and nothing is wasterd"*
>
> *"i need loop system too that keeps contradicting and expand until quality demishes and rehooks a save point. have a overseer agent to aid with this and specialize in it and a project called sinister looper"*

## Architecture: Sinister Overseer has THREE sub-agents

```
sinister-overseer
├── #1  Rate-limit monitor       (automations/overseer_rate_limit_agent.py)
│       schtask: SinisterOverseerRateLimitAgent (1-min headless)
│       SLA: 20s detect+autofix; auto-respawns dead agents on fresh accounts
│       Source signals: eve-incidents/anthropic-throttle/rate-limit-causes/claude-wrapper.log
│
├── #2  Token monitor             (automations/overseer_token_agent.py)
│       schtask: SinisterOverseerTokenAgent (1-min headless)
│       Goal: zero token waste. Rules:
│         - END-OF-WINDOW: <25 min left + >8% avail → fire 2 spare tasks
│         - IDLE-FILL:     >50% avail + 0 live agents → fire 1 chill task
│       Queue: _shared-memory/background-tasks.jsonl (priority-sorted FIFO)
│
└── #3  Loop quality monitor      (automations/overseer_loop_quality_agent.py)
        schtask: SinisterOverseerLoopQuality (1-min headless)
        Project: projects/sinister-looper/ (Sinister Looper — operator-asked)
        Contract:
          - Snapshot every iter (git tag looper-savepoint-<slug>-<iter>)
          - Quality score per project (100 - 10*incidents_last_10min)
          - Contradict every 5 iters (post inbox message asking 3 contradictions)
          - Rehook: if score drops >15 in 3-iter window → recommend git reset
            --hard to highest-scoring savepoint in window
        Default-on for every EVE-spawned session.
```

## Why three, not one

Different decision functions, different signals, different cadences. Three small focused enforcers compose with the existing Sanctum fleet better than one fat super-daemon.

## Sub-agent #1 — Rate-limit monitor (shipped iter-28)

Watches:
- `_shared-memory/eve-incidents.jsonl`
- `_shared-memory/anthropic-throttle-events.jsonl`
- `_shared-memory/rate-limit-causes.jsonl`
- `_shared-memory/claude-wrapper.log` (10 regex patterns: 429/529/overloaded/throttle/etc)

Actions on hit:
1. Mark account rate-limited 30min
2. Rotate cursor to next available account
3. Flag for Sinister Terminal banner
4. Update learning profile `prompt-profiles/rate-limit-tuning.json`
5. **Auto-recover**: stale-heartbeat project → re-spawn on fresh account

## Sub-agent #2 — Token monitor (shipped iter-28)

Decision function:

| Condition | Mode | Action |
|-----------|------|--------|
| `remaining_min < 25` AND `available_pct > 8` | **spare-capacity-window** | Fire 2 background tasks |
| `available_pct > 50` AND `live_agents == 0` | **idle-fill** | Fire 1 chill task |
| otherwise | **normal** | No fire |

Default queue seeds: `sanctum_custodian audit` / `overseer_rate_limit_agent --once` / `prompt_profiler --scan` / `project_manager categorize`.

Add custom: `python automations/overseer_token_agent.py --queue-add <cmd> --priority 5 --description "..."`

## Sub-agent #3 — Loop quality monitor (shipped iter-28)

Per project (live heartbeat <10min):

1. **Snapshot** — every iter, `git tag -f looper-savepoint-<slug>-<iter>`. Cheap, immortal until manual prune. Operator always has rollback points.
2. **Quality score** — `100 - (10 * incidents_in_last_10min)`. Future: pytest exit, forever-improve tally, git diff churn.
3. **Contradict** — every 5 iters, post `inbox/<slug>/.../from-looper-contradict.json` asking the agent to:
   - List 3 assumed-true things that may not be
   - Find one design decision worth reconsidering
   - Find one quality risk introduced
   - Address BEFORE expanding further (quality > velocity)
4. **Rehook** — if score drops >15 in 3-iter window, recommend `git reset --hard looper-savepoint-<slug>-<best-iter-in-window>`. Operator (or future automation) executes via `overseer_loop_quality_agent.py --rehook <slug> <tag>`.

## Operator's key insight (waste-avoidance heuristic, sub-agent #2)

> *"like it can have background tasks that are not as important or just chilling and lets say we have 10 percent left on a plan and 20 minutes left. the agent will make sure to use all tokens to have all power and control that we need"*

The token monitor is NOT a throttler — it's a maximizer. Primary load = operator's foreground sessions; background tasks fire ONLY when capacity would otherwise be wasted.

## Operator's key insight (quality-degradation loop, sub-agent #3)

> *"i need loop system too that keeps contradicting and expand until quality demishes and rehooks a save point"*

The loop-quality monitor lets agents PUSH UNTIL they break, then SNAPS BACK to the best-known-good state. Save points are immortal git tags; rehook is `git reset --hard`. The contradict pass forces the agent out of momentum-bias every 5 iters.

## Composes with

- `_shared-memory/knowledge/loop-relentless-pursuit-doctrine-2026-05-25.md` (relentless = use every cycle)
- `_shared-memory/knowledge/safe-quality-loops-doctrine-2026-05-24.md` (12 guardrails)
- `_shared-memory/knowledge/sanctum-master-full-control-doctrine-2026-05-25.md` (no per-fire confirmation)
- `_shared-memory/knowledge/hard-priority-ceiling-failsafe-2026-05-25.md` (background tasks inherit NORMAL ceiling)
- `_shared-memory/knowledge/sanctum-scope-discipline-2026-05-24.md` (background tasks stay in-lane)

## Anti-patterns

1. Fire background tasks WHEN operator is mid-conversation — gate via live_agents > 0 short-circuit
2. Fire heavy tasks at end-of-window — could mask real over-quota event. Defaults are <10s lightweight cleanups
3. Bundle the three decisions in one daemon — coupling. Always three.
4. Auto-respawn agents in infinite loop — cap 3 attempts/10min (future hardening)
5. Snapshot every iter forever without prune — operator can `--prune-savepoints --older-than 7d` (future CLI)
