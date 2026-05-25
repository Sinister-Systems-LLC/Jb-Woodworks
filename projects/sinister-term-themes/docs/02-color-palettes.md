<!-- Author: RKOJ-ELENO :: 2026-05-25 -->
# 02 — Color Palettes

Per-project palette tables. Each row = (name, role, HEX, ANSI 256, ANSI 24-bit). Truecolor preferred; 256-color fallback when terminal doesn't advertise truecolor.

## Naming convention

`<color-family>-<mood>` — `violet-core`, `red-control`, `red-burning`, `blue-deep`, `blue-storm`, `indigo-fringe`, `indigo-collapse`, `green-growth`, `green-electric`.

Each project has TWO palettes: idle (lower-energy, more saturation pulled down) + high-energy (full saturation + a "danger color" added).

## Sanctum — violet family

### `violet-core` (idle)

| Role | HEX | ANSI 256 | Notes |
|---|---|---|---|
| primary | #6366f1 | 99 | deep indigo (Sanctum accent) |
| secondary | #a855f7 | 135 | electric violet |
| tertiary | #c084fc | 177 | brand purple (composes with `--accent` token) |
| highlight | #f5f3ff | 255 | bone white |
| dim | #312e81 | 54 | midnight indigo |

### `violet-core-burning` (high energy)

| Role | HEX | ANSI 256 | Notes |
|---|---|---|---|
| primary | #a855f7 | 135 | electric violet |
| secondary | #ec4899 | 199 | hot magenta |
| tertiary | #f0abfc | 219 | plasma pink |
| highlight | #ffffff | 231 | full white |
| danger | #fbbf24 | 220 | gold warning |

## Sinister Panel — red family

### `red-control` (idle)

| Role | HEX | ANSI 256 | Notes |
|---|---|---|---|
| primary | #b91c1c | 124 | deep crimson |
| secondary | #ef4444 | 196 | ember red |
| tertiary | #f97316 | 208 | orange embers |
| highlight | #fef3c7 | 230 | pale gold |
| dim | #450a0a | 52 | dried-blood maroon |

### `red-burning` (high energy)

| Role | HEX | ANSI 256 | Notes |
|---|---|---|---|
| primary | #dc2626 | 160 | arterial red |
| secondary | #fbbf24 | 220 | flame gold |
| tertiary | #fde047 | 226 | white-hot yellow |
| highlight | #ffffff | 231 | white |
| danger | #fb923c | 215 | flicker orange |

## Sinister OS — blue family

### `blue-deep` (idle)

| Role | HEX | ANSI 256 | Notes |
|---|---|---|---|
| primary | #1e3a8a | 18 | midnight blue |
| secondary | #2563eb | 27 | cobalt |
| tertiary | #38bdf8 | 75 | pale cyan |
| highlight | #e0f2fe | 195 | foam white |
| dim | #0c1e3a | 17 | abyss |

### `blue-storm` (high energy)

| Role | HEX | ANSI 256 | Notes |
|---|---|---|---|
| primary | #06b6d4 | 38 | electric cyan |
| secondary | #818cf8 | 105 | lightning indigo |
| tertiary | #f0f9ff | 230 | white-foam |
| highlight | #ffffff | 231 | white |
| danger | #fef08a | 228 | static yellow |

## Sinister Snap-API-Quantum — indigo family

### `indigo-fringe` (idle)

| Role | HEX | ANSI 256 | Notes |
|---|---|---|---|
| primary | #4338ca | 56 | deep indigo |
| secondary | #7c3aed | 92 | violet |
| tertiary | #cbd5e1 | 252 | cool silver |
| highlight | #ddd6fe | 189 | quantum mist |
| dim | #1e1b4b | 17 | event horizon |

### `indigo-collapse` (high energy)

| Role | HEX | ANSI 256 | Notes |
|---|---|---|---|
| primary | #8b5cf6 | 99 | electric violet |
| secondary | #f0abfc | 219 | plasma white |
| tertiary | #d946ef | 200 | impossible magenta |
| highlight | #ffffff | 231 | measurement-event white |
| danger | #fbbf24 | 220 | wavefunction-collapse gold |

## Sinister Sleight — green family

### `green-growth` (idle)

| Role | HEX | ANSI 256 | Notes |
|---|---|---|---|
| primary | #16a34a | 34 | forest green |
| secondary | #22c55e | 41 | emerald |
| tertiary | #84cc16 | 112 | lime |
| highlight | #fef3c7 | 230 | pale gold (the money) |
| dim | #14532d | 22 | shadow forest |

### `green-electric` (high energy)

| Role | HEX | ANSI 256 | Notes |
|---|---|---|---|
| primary | #4ade80 | 121 | neon green |
| secondary | #2dd4bf | 80 | jade teal |
| tertiary | #67e8f9 | 117 | white-hot teal |
| highlight | #ffffff | 231 | white |
| danger | #f59e0b | 214 | gold-rush amber |

## Fallback chain

1. **Truecolor** — `\033[38;2;R;G;Bm` (use HEX directly).
2. **256-color** — `\033[38;5;Nm` (use ANSI 256 column).
3. **16-color** — only if neither advertised. Map each family to its nearest 16-color member (red→31/91, green→32/92, blue→34/94, etc.). At this fidelity the experience degrades; document but don't dwell.

## Adding a new palette

1. Pick a family (red/green/blue/indigo/violet/cyan/yellow/etc.).
2. Pick a mood (`-core`, `-deep`, `-fringe`, `-storm`, `-burning`, `-collapse`, ...).
3. Add the row to `palettes.py` and to this doc in the same commit.
4. Each palette MUST have 5 roles: primary / secondary / tertiary / highlight / dim-or-danger.
5. Run smoke: `python -m sinister_term_themes demo <entity-using-this-palette> --frames 5` exits 0.
