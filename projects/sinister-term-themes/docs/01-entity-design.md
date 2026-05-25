<!-- Author: RKOJ-ELENO :: 2026-05-25 -->
# 01 — Entity Design

The entity catalog. Each project gets a named character. The glyph is multi-line ASCII; the palette is named (lookup in `02-color-palettes.md`); the animation rule says what shifts frame to frame; the personality one-liner is what we'd say if asked "who's this?".

## The five P0 entities

### 1. Sanctum — "The Seed"

Personality: the violet hub from which every other entity grew. Patient. Concentric. Vast.

Idle palette: `violet-core` (deep violet + indigo + soft white)
High-energy palette: `violet-core-burning` (magenta + electric purple + bone white)

Glyph (10 lines):
```
        .   .       *  .  .       .
     .       *           .     *
   .    .::::SINISTER::::.     .
 *     ::                ::         *
 .   ::    ◉  E V E  ◉    ::    .
   ::      \  / | \  /      ::
    ::      \/  |  \/      ::      *
 .    ::    /\  |  /\    ::      .
      ::  /    \|/    \  ::
    *  ::::::::SANCTUM:::::::  *
```

Animation rule: every frame, rotate the dot density (`. * :`) one position right; on high energy, also rotate hue +30° per frame so the glyph shimmers.

### 2. Sinister Panel — "The Hand"

Personality: control, command, the hand that grips. Sharp. Red. Inescapable.

Idle palette: `red-control` (deep crimson + ember + pale gold)
High-energy palette: `red-burning` (arterial red + white-hot + flicker yellow)

Glyph (8 lines):
```
   ╔═══════════════════╗
   ║  ▓▓▓ PANEL ▓▓▓    ║
   ╠═══╦═══╦═══╦═══════╣
   ║ ■ ║ ■ ║ ■ ║ ●●●●  ║
   ║ ■ ║ ■ ║ ■ ║ ●●●●  ║
   ╠═══╩═══╩═══╩═══════╣
   ║   < S I N I S T R ║
   ╚═══════════════════╝
```

Animation rule: the `●●●●` row pulses (full → half → off → half → full). High energy: the entire grid bleeds red into white.

### 3. Sinister OS — "The Deep"

Personality: oceanic. Slow. Vast in volume but quiet on the surface. The OS is the floor of the world.

Idle palette: `blue-deep` (midnight blue + cobalt + pale cyan)
High-energy palette: `blue-storm` (electric cyan + white-foam + lightning indigo)

Glyph (10 lines):
```
  ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
 ≋ ≋ ≋ ≋ ≋ ≋ ≋ ≋ ≋ ≋ ≋ ≋ ≋ ≋ ≋ ≋
   ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒
    ░░▓▓▓██████   SOS  ██████▓▓▓░░
   ░░▓▓██▓▓░░  ◐  ░░▓▓██▓▓░░
   ▓▓██▓▓░░░░░░░░░░░░░░░░░██▓▓
   ██▓▓░░░░░░░  CORE  ░░░░░██
   ▓▓░░░░░░░░░░░░░░░░░░░░░░▓▓
    ░░░░░░░░░░░░░░░░░░░░░░░░
       ░ ░ ░ ░ ░ ░ ░ ░ ░ ░
```

Animation rule: rows shift up by one each frame (giving the impression of looking down through water). High energy: pressure waves — vertical compression columns sweep left to right.

### 4. Sinister Snap-API-Quantum — "The Interference"

Personality: an interference pattern viewed from inside. Probabilistic. Many states at once. Indigo.

Idle palette: `indigo-fringe` (deep indigo + violet + cool silver)
High-energy palette: `indigo-collapse` (electric violet + plasma white + impossible magenta)

Glyph (9 lines):
```
   . . . . . . . . . . . . . . .
   |   |   |   |   |   |   |
   |  ░|░  |  ▒|▒  |  ▓|▓  |
   |  ░|░  |  ▒|▒  |  ▓|▓  |
   ╫━━━╫━━━╫━━━[QBC]━━━╫━━━╫
   |  ░|░  |  ▒|▒  |  ▓|▓  |
   |  ░|░  |  ▒|▒  |  ▓|▓  |
   |   |   |   |   |   |   |
   ' ' ' ' ' ' ' ' ' ' ' ' ' ' '
```

Animation rule: the `░ ▒ ▓` density shuffles randomly each frame (sampled). High energy: collapse — for one frame every 8, the entire grid resolves to a single column of `▓` (measurement event), then returns.

### 5. Sinister Sleight — "The Hand of Cards"

Personality: fast. Precise. Green = growth + money. A shuffler who knows what each card will be before it's drawn.

Idle palette: `green-growth` (forest green + emerald + pale gold)
High-energy palette: `green-electric` (neon green + jade + white-hot teal)

Glyph (8 lines):
```
   ╭───╮ ╭───╮ ╭───╮ ╭───╮ ╭───╮
   │ ♠ │ │ ♥ │ │ ♦ │ │ ♣ │ │ $ │
   │   │ │   │ │   │ │   │ │   │
   ╰───╯ ╰───╯ ╰───╯ ╰───╯ ╰───╯
       SLEIGHT  ::  +0.00%
   ╭───┬───┬───┬───┬───┬───╮
   │ ▁ │ ▃ │ ▅ │ ▇ │ ▅ │ ▃ │
   ╰───┴───┴───┴───┴───┴───╯
```

Animation rule: the suits cycle (♠ → ♥ → ♦ → ♣ → $ → ♠) one position right per frame. The PnL number drifts ±0.05% per frame (cosmetic — actual PnL not surfaced here). High energy: the bottom equalizer bars dance at byte-rate.

## How to add a new entity

1. Pick a project key (from `automations/session-templates/projects.json`).
2. Pick a palette name (existing or new in `02-color-palettes.md`).
3. Draw an 8–12 line ASCII glyph.
4. Write a one-line personality.
5. Write a one-line animation rule.
6. Drop a file at `src/sinister_term_themes/entities/<key>.py` with the canonical structure (see `entities/sanctum.py`).
7. Smoke test: `python -m sinister_term_themes demo <key> --frames 5` exits 0.

## What NOT to do

- Don't make an entity that depends on emoji rendering — boxes and half-blocks render reliably; emoji don't.
- Don't make an entity narrower than 25 cols or wider than 60 — fits standard terminal windows.
- Don't add per-entity special-case render code — if the engine can't render it from the glyph + palette + rule, the entity is wrong, not the engine.
