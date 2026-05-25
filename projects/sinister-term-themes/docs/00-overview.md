<!-- Author: RKOJ-ELENO :: 2026-05-25 -->
# 00 — Overview

## What we're building (5-page bound)

Ancestral Remotion is a sidecar visualizer. The Claude session streams stdout into a Unix pipe / Windows named pipe / file-tail; the visualizer reads the stream, measures byte-rate, looks up the current project's entity + palette, and renders an animated ASCII art surface to a target terminal (the same one if we own the screen, or a sidecar pane).

It is **NOT** a replacement for logs. Key updates — questions, errors, "what to answer" — still pass through verbatim in a dedicated KEY-UPDATES band. The entity + palette are decoration WITH meaning: meaning carried by mood and movement, not by displacing text.

## Layered architecture

```
                                    ┌─────────────────────────────────────┐
                                    │  Ancestral Remotion render surface  │
                                    │   (ANSI escapes; 30fps; stdlib)     │
                                    └──────────────▲──────────────────────┘
                                                   │
                                                   │ frames
                                                   │
   ┌─────────────────┐    bytes/sec    ┌───────────┴──────────┐
   │ Claude stdout   │ ────────────────▶│  Engine (engine.py)  │
   │   (pipe/file)   │                  │  + entity registry   │
   └─────────────────┘                  │  + palette lookup    │
                                        └──────────────────────┘
                                                   │
                                                   │ active-project
                                                   │
                                        ┌──────────┴────────────┐
                                        │  Project context      │
                                        │  (env var / config)   │
                                        └───────────────────────┘
```

## Six principles

1. **Stdlib-only at P0–P2.** Portability beats fanciness. No pip install required.
2. **Energy = measurement.** Never a sim. We read the byte-rate.
3. **Entities are catalog rows, not code branches.** New entity = new file under `entities/`, NEVER a new branch of the renderer.
4. **Palettes are tables.** A new palette is a row in `palettes.py`, not a code change to the engine.
5. **Logs are sacred.** Key updates flow through.
6. **30fps is the target.** Slower than 30fps and the entity stops feeling alive.

## P0 deliverable (this iter)

- Package skeleton + 3 smoke tests passing.
- One working entity: Sanctum.
- One working palette: violet-core (Sanctum's).
- `python -m sinister_term_themes demo sanctum --frames N` runs cleanly with N small enough to fit in CI (5 or 30).

## What this overview does NOT cover

- Multi-project palette switching (see `02-color-palettes.md`).
- The sidecar terminal mechanism (see `03-render-engine.md`).
- Why we care (see `04-artistic-doctrine.md`).
- The Sinister OS endgame (see `06-sinister-os-integration.md`).
