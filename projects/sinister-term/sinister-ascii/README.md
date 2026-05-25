# Sinister ASCII

> **Author:** RKOJ-ELENO :: 2026-05-25
> **Parent project:** `sinister-term` (sub-project — lives under `projects/sinister-term/sinister-ascii/`)
> **Lane:** still `sinister-term` (no separate branch — ships on same commits)
> **Operator named (verbatim 2026-05-25T11:36:29Z):** *"call it sinister ascii"*
> **License:** AGPL-3.0-or-later

---

## What this is

Sinister ASCII is the artistic-ASCII rendering engine that runs inside Sinister Term **while Claude is working** — turning the formerly-boring "Claude is thinking..." dead-space into a living, color-expressive canvas. One entity per Sinister project. Each entity has its own personality, palette, and motion signature. Walking past one of our terminals should feel like looking at a living being, not a console.

## Operator vision (verbatim 2026-05-25)

> *"ok now the terminals have less logs but i want to be entertained like in our console using sinister termwhilke claude is running i want you to make it an artistic ascii materpiece of color and express with al sorts of reds, blues, greens indigos violets. even have like entities like characters and have everything be slighly different based on teh project like you showing me visual emotion while you work. i want it to look cool as shit and have the feeling of it being endless that leaves me breathles. launch all agents you need for this. make it a sub project."*

> *"really do this and grow it and put alot of time into it as like a sub project in your project"*

> *"call it sinister ascii"*

## Operator-binding tenets

1. **Sub-project of sinister-term, not a standalone repo.** Lives inside `projects/sinister-term/sinister-ascii/`. Ships on the same lane branch.
2. **Per-project entity.** Each Sinister project gets its own ASCII entity:
   - Distinct color palette (anchored on reds / blues / greens / indigos / violets — but each project picks ONE dominant + 2 accents from the 5)
   - Distinct silhouette / shape
   - Distinct motion signature (orbit / pulse / drift / spiral / breathe)
   - Subtle name / character tag visible in the corner
3. **Living being feel.** Render must convey emotion — not just animate. When the agent is working hard (lots of tokens flowing), the entity glows more, moves faster, color-shifts more vibrantly. Idle = breathing, slow color drift.
4. **Endless / breathless.** No "loop point" should be visible. Use long irrational period multipliers so the animation never visibly repeats.
5. **Speed + efficiency are key.** Per-frame budget = 16ms (60 FPS) max; per-keystroke budget = <2ms (operator must never feel UI lag from Sinister ASCII).
6. **In-band of Sinister Term.** Renders inside the existing prompt_toolkit / Rich console — does NOT spawn a separate window. Activated when sterm detects an active "agent working" signal (Claude session jsonl growing, or Sinister Bus broadcast).
7. **Toggle-able.** `SINISTER_ASCII=off` env var disables completely. `SINISTER_ASCII=minimal` = a tiny ambient indicator (single moving glyph). Default = full entity.

## Architecture (initial draft)

```
projects/sinister-term/sinister-ascii/
├── README.md                          ← this file
├── source/
│   └── sinister_ascii/
│       ├── __init__.py                ← public API
│       ├── engine.py                  ← frame loop + budget enforcement (16ms)
│       ├── palette.py                 ← reds/blues/greens/indigos/violets + HSV rotation
│       ├── entities/                  ← per-project entity definitions
│       │   ├── _base.py               ← Entity ABC (name, palette, motion_fn, intensity)
│       │   ├── sanctum.py             ← purple orbital — "EVE-prime"
│       │   ├── term.py                ← violet pulse — "Glyph-keeper"
│       │   ├── forge.py               ← red breathe — "Forge-spark"
│       │   ├── mind.py                ← indigo spiral — "Mind-weave"
│       │   ├── overseer.py            ← green drift — "Watcher"
│       │   └── ...                    ← one per project in projects.json
│       ├── motion.py                  ← orbit / pulse / drift / spiral / breathe primitives
│       ├── renderer.py                ← ANSI 24-bit truecolor frame writer
│       ├── intensity.py               ← reads activity signal (claude jsonl + sinister-bus)
│       └── render_loop.py             ← async loop driver + 60FPS budget
├── themes/
│   ├── palette-canonical.json         ← the 5 anchor palettes (red/blue/green/indigo/violet)
│   └── per-project.json               ← project_key -> entity_key mapping
├── docs/
│   ├── PALETTE.md                     ← color theory + the 5 anchor families
│   ├── ENTITIES.md                    ← per-project entity character bios
│   ├── PERFORMANCE.md                 ← <2ms keystroke / 16ms frame budget audit
│   └── INTENSITY.md                   ← how "agent working" intensity is sampled
└── tests/
    ├── test_palette.py
    ├── test_entities.py
    ├── test_engine_budget.py          ← regression guard: 16ms frame budget
    └── test_intensity.py
```

## Phases

| Phase | What | Status |
|---|---|---|
| **SA-PH0** | Scaffold + README + operator vision quote (this commit) | ✅ 2026-05-25 |
| **SA-PH1** | Palette module + 5 anchor families + HSV rotation primitive | queued |
| **SA-PH2** | Entity ABC + motion primitives (orbit / pulse / drift / spiral / breathe) | queued |
| **SA-PH3** | First 6 per-project entities (sanctum / term / forge / mind / overseer / chatbot) | queued |
| **SA-PH4** | Renderer (ANSI 24-bit truecolor) + 16ms frame loop | queued |
| **SA-PH5** | Intensity sampler — reads claude jsonl + sinister-bus broadcasts | queued |
| **SA-PH6** | Integration into sinister-term `app.py` — render between prompts when claude is running | queued |
| **SA-PH7** | Per-project entities for the remaining 23 projects | queued |
| **SA-PH8** | Performance audit + <2ms keystroke guard | queued |
| **SA-PH9** | Ship as default-on (SINISTER_ASCII=full); operator hard-canonical opt-out via env | queued |

## The 5 anchor color families

| Family | Hue range | Anchor projects | Personality |
|---|---|---|---|
| **Crimson Red** | 0°–25° + 335°–360° | sinister-forge, sinister-chatbot | aggressive, spark, ignite |
| **Indigo / Cobalt Blue** | 215°–255° | sinister-mind, sinister-kernel-apk | thoughtful, deep, focused |
| **Verdant Green** | 80°–155° | sinister-overseer, sinister-link | watchful, grow, balance |
| **Royal Indigo** | 255°–280° | sinister-vault, sinister-memory | deep magic, archive, lineage |
| **Sinister Violet** | 270°–315° | sinister-sanctum (master), sinister-term, sinister-panel | the canonical Sinister identity |

Each project's entity picks **one dominant family + two accent families**, never the full 5 at once — readability + identity demand restraint. Master Sanctum gets a unique entity that briefly cycles through all 5 (still bounded by the 16ms frame budget) to signal "I orchestrate the others."

## Composes with

- `_shared-memory/knowledge/sinister-sleight-color-palette-doctrine-2026-05-25.md` — the parent 8-color Sinister Sleight palette (Sinister ASCII inherits + extends with the 5-family anchor)
- `_shared-memory/knowledge/eve-ui-uniformity-doctrine-2026-05-24.md` — uniform UI tokens; Sinister ASCII renders in-band but respects the surrounding sterm chrome
- `_shared-memory/knowledge/sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24.md` — TUI not web, but the same expand-not-fork rule applies (one entity-base ABC, not 25 forks)
- `_shared-memory/knowledge/no-bullshit-tested-before-claimed-doctrine-2026-05-23.md` — every phase has a binary pass criterion

## Speed + efficiency posture

- **Per-frame:** 16ms ceiling (60 FPS). Renderer profiles each frame; if budget exceeded 3× in 1s, downgrade to "minimal" mode automatically.
- **Per-keystroke:** <2ms. Sinister ASCII renders on a dedicated thread; never blocks input.
- **CPU floor:** if CPU >70% (operator's machine working hard), Sinister ASCII auto-throttles to 10 FPS. Sinister OS hooks will let operator set the floor explicitly later.
- **GPU:** operator has a 4090. Phase SA-PH8+ may explore offloading HSV/RGB math to a CUDA shader; deferred until profiler says CPU is the bottleneck.

## License header for new files

```
# Sinister ASCII (sub-project of Sinister Term)
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
```
