# Sinister Chess — panel integration

The UI for this lane is rendered by **sinister-panel** (the dashboard Next.js app), per the canonical-route doctrine: the lane owns the engine + rules + (future) coach; the dashboard owns the route shell.

## Live route

- **URL:** `/chess`
- **Nav entry:** "Sinister Chess" under the **Personal** section in the sidebar.
- **Visibility:** all roles (admin, sinister, viewer).

## Source location

Files live in the dashboard app router:

```
projects/sinister-panel/source/Andrew Panel/Sinister Panel/panel/dashboard/
├── app/chess/
│   ├── page.tsx         # Route shell + state + bot loop
│   ├── Chessboard.tsx   # Pure-SVG 8x8 board (Unicode pieces)
│   └── engine.ts        # Thin adapter over chess.js
├── components/sidebar.tsx       # Added "Personal" section + chess entry
└── components/icons/index.tsx   # Added NavChess glyph
```

## Engine

- **chess.js v1.4.0** — pure-JS rules engine. Validates moves, detects
  check/mate/stalemate/draw, generates legal-move lists, tracks history.
- **No AI** wired up. P0 ships human-vs-human + a uniformly-random-move
  bot toggle. Stockfish WASM is **deferred** until operator approves the
  ~1MB binary drop into `/public`.

## Modes shipped

- Human vs Human (default)
- vs Random Bot (bot plays black; toggle on the board canvas)

## Build / lint status at ship

- `chess.js@^1.4.0` added to `dashboard/package.json` and extracted to
  `node_modules/chess.js/` (v1.4.0).
- TS parser walks all 5 new/touched files clean (no syntax errors).
- Full `npm install` / `next build` / `next lint` could **not** be run to
  completion in the ship environment — the dashboard's `node_modules/` is
  in a half-installed state (many leftover `node` processes holding files
  open, Windows `ENOTEMPTY` rmdir races). Same lib-missing diagnostics
  appear on pre-existing untouched files, confirming the environment, not
  the new code, is the blocker.
- **Next step for the operator:** kill stray node processes, then run
  `cd panel/dashboard && rm -rf node_modules && npm install && npm run build`.

## Stretch goals deferred (need operator sign-off)

- Stockfish WASM at ELO-capped strengths (per lane CLAUDE.md pillar 1).
- Per-player mirror model (sinister-memory integration).
- Coach output pane.
- ELO trajectory chart.
- PGN export / vault persistence under `_vault/sinister-chess/<player-id>/`.
