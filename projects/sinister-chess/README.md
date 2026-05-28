# Sinister Chess

> Be the operator's perfect chess mirror. Play them at every level. Coach the fastest path forward.

**Author:** RKOJ-ELENO :: 2026-05-27
**Status:** P0 scaffold (engine wiring + panel integration next)

## The promise

You play. Sinister Chess plays you at exactly the level that maximizes your growth per game — not too easy (boredom), not crushing (frustration). After each game it tells you the 3 things you'd most benefit from drilling. Your ELO climbs faster because every game is calibrated to your edge.

Same service for Leo. Separate vaults. Separate mirrors. Same engine.

## Pillars

1. **Stockfish-backed strength** — real engine, capped per-target-ELO
2. **Per-player mirror model** — learns how YOU think so it can play AS you
3. **Liquid-Glass UI in Sinister Panel** — board + history + coach output + study queue
4. **Memory across sessions** — every game logged, every blunder tracked, every drill remembered
5. **Coach output that's actionable** — "drill these 3 endgame patterns this week" not "you should study endgames"

## Quick start (post-iter-1)

```
cd projects/sinister-chess/source
pip install -e .
sinister-chess play --player operator --level 1400
```

Or via the panel: open Sinister Panel → Sinister Chess tab → click Start.

## Scope

- Bullet / blitz / rapid / classical time controls
- Live opponent (engine) + vs-mirror mode
- Post-game coach with concrete drills
- ELO trajectory chart
- Multi-player isolation (operator + Leo + future)

## Out of scope (don't ask)

- Real-time online opponent matching (use chess.com / lichess for that)
- Tournament organization
- Cheat detection (we're not the platform)

## Lane scope reminder

Per `sanctum-scope-discipline-2026-05-24`: this lane owns the engine + per-player model + coach + UI. It does NOT own:
- Memory storage primitives (sinister-memory)
- Vault storage (sinister-vault)
- Panel route shell (sinister-panel)

We CONSUME those, we don't reimplement.
