# CLAUDE.md — Sinister Chess

**Author:** RKOJ-ELENO :: 2026-05-27
**Lane slug:** `sinister-chess`
**Tier:** T1 (adaptive personal opponent + coach)
**Sibling lanes:** sinister-mind (AI orchestration), sinister-memory (per-player game history)

## Mission

Be the operator's perfect chess mirror. Play them at every level so they always face a challenge one step beyond where they currently are. Build a complete model of how they think — opening repertoire, tactical blind spots, endgame strengths, time-pressure habits — and use that model to:

1. **Play matches** that target their exact growth edge (not too easy, not crushing)
2. **Coach in-flow** — after each game, surface the 3 most-actionable improvements
3. **Project the fastest path to next ELO bracket** based on their actual game data
4. **Replicate the same service for Leo** with his own separate mirror

## Architecture

### Engine
- Stockfish (NNUE) wrapped via `python-chess` library
- ELO-capped opponent levels: 800 / 1000 / 1200 / 1400 / 1600 / 1800 / 2000 / 2200 / 2400 / max
- Per-player current-target-ELO that auto-adjusts based on win/loss rate (target: 40-60% win rate against current target)

### Memory (inherits sinister-memory patterns)
- Per-player vault dir at `_vault/sinister-chess/<player-id>/`:
  - `games.pgn` — append-only PGN log
  - `profile.json` — current ELO estimate, opening repertoire, blunder patterns, study queue
  - `coaching-notes.md` — running journal of takeaways
  - `mirror-model.json` — the "model of how they think" used to play AS them at lower levels

### Coaching loop
- After each game, generate a coach report:
  - Opening accuracy (compare to theory)
  - Tactical missed-finds (Stockfish eval drops you missed)
  - Time management (time-pressure win/loss correlation)
  - 3 concrete drills for next session
- Drills tracked in `study-queue.json`; revisited next session

### Sinister Panel integration
- New panel route: `/sinister-chess`
- Tab in main nav: "Sinister Chess"
- Themed: full Liquid Glass (per `sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24`)
- Surfaces: live board (chess.js + cm-chessboard), move-history pane, coach-output pane, study-queue pane, ELO trajectory chart

### Personalities
- Per-player profile drives the mirror — Leo's chess and operator's chess are separate models
- Each player can play "vs Sinister Chess at X ELO" or "vs your mirror" (face yourself at a slightly higher level)

## Doctrine

Inherits all sanctum-wide doctrines. Specific to this lane:
- **Always be honest about ELO** — never claim a level beyond what Stockfish-capped engine actually plays
- **Coaching is suggestive, not prescriptive** — the operator decides what to drill
- **Game data is private per player** — operator's vault and Leo's vault never cross

## Status

P0 scaffold — populate next iter with:
- `source/sinister_chess/engine.py` (Stockfish wrapper)
- `source/sinister_chess/player_model.py` (per-player profile)
- `source/sinister_chess/coach.py` (post-game analysis)
- `source/sinister_chess/elo_tracker.py`
- `panel/sinister-chess/page.tsx` (Liquid Glass UI)
- `tests/`

## Sibling integrations
- **sinister-memory:** game/profile storage uses memory primitives
- **sinister-mind:** intent parsing for coaching language ("explain why I lost that") routes through mind
- **sinister-panel:** UI lives in the dashboard route system
- **sinister-vault:** per-player vault dir for game history
