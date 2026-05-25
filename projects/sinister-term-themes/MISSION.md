<!-- Author: RKOJ-ELENO :: 2026-05-25 -->
# MISSION.md — Ancestral Remotion

## Operator brief (verbatim 2026-05-25 ~03:30Z)

> "ok now the terminals have less logs but i want to be entertained like in our console using sinsiter term whilke claude is running i want you to make it an atristic ascii materpiece of color and express with al sorts of reds, blues, greens indigos violets. even have like entities like characters and have everything be slighly different based on teh project like you showing me visual emotion while you work. i want it to look cool as shit and have the feeling of it being endless that leaves me breathles. launch all agents you need for this. make it a sub project. its desc is sinister term themes. and this will be called ancestral remotion. and when its really running alot of energy through it, you can look at it and have the feeling as if you were looking at a living being. i want our uis to have that life i want you to update in md files that we what to display that much of artics vlaue and meaning to what we do and we are starting with teh logs. now i still want to see key updates. know what im suppose to answer. i can see all the things i need to see. like what if we went so far with the sinister os that no consoles are show and its just a complete UI built into the operating system on the servers with a complete command center for me to run all my companies from that is waht i want. i want a complete command center and a hive mind live eve to conquer my computer so i can use them to do whatever i want to do with them like fucking tony stark take note if this"

## The arc (now → endgame)

### Today — Logs into Art

The operator already trimmed terminal log volume. The remaining stream still feels mechanical. Ancestral Remotion is the visualization layer that turns that stream into a living ASCII entity. The entity's mood reflects what's happening: idle, thinking, generating, in-error. The operator looks at the terminal and *feels* the work happening, the way a blacksmith hears the rhythm of the hammer.

### Soon — Per-project Personalities

Every project the fleet spawns gets its own entity + palette. Sinister Panel feels like control — reds, sharp lines, an angular daemon. Sinister OS feels like deep water — blues, slow-breathing geometry. Snap-API-Quantum feels like the inside of a particle accelerator — indigos, interference fringes. Sleight feels like watching a hand cards being shuffled — greens, fast precision. Sanctum is the violet seed they all came from — concentric, patient, vast.

### Mid-term — Energy = Life

The render engine measures Claude's stdout throughput. Low energy: the entity breathes — a 0.5 Hz palette shimmer, no movement. Mid energy: motion + a perceptible heartbeat. High energy (lots of tool calls, lots of streaming): the glyph fragments and re-coheres, the palette shifts mid-frame, the energy bar pulses at the actual byte-rate. Looking at a high-energy session should feel like watching a living being.

### Endgame — Sinister OS Command Center

The operator's directive ends with: *"what if we went so far with the sinister os that no consoles are show and its just a complete UI built into the operating system on the servers with a complete command center for me to run all my companies from that is waht i want. i want a complete command center and a hive mind live eve to conquer my computer so i can use them to do whatever i want to do with them like fucking tony stark"*.

That is the endgame. Ancestral Remotion is the visual language that pre-makes that command center workable. Every entity is a node in a future hive-mind grid. Every palette is a status channel. The terminal is the prototype; the OS desktop is the production canvas.

## Acceptance criteria (measurable)

### Outcome 1 — P0 demo

`python -m sinister_term_themes demo sanctum --frames 5` runs end-to-end on Windows in <2s, exits 0, prints visible ASCII glyph + visible energy bar + visible palette cycle.

### Outcome 2 — Entity catalog

At least 5 entities (Sanctum / Panel / OS / Snap-Quantum / Sleight) shipped with: a multi-line ASCII glyph (≥6 lines), an idle palette (3 colors), a high-energy palette (3 colors), a personality one-liner, a frame-animation rule (which lines shift per frame).

### Outcome 3 — Energy = real bytes/sec

By P3, the energy bar reflects actual measured bytes/sec of Claude stdout averaged over the last 5s, not a placeholder.

### Outcome 4 — Per-project palette binding

By P2, switching projects switches palette + entity without code change — config-driven via `palettes.py` lookups.

### Outcome 5 — Sidecar terminal

By P2, a sidecar terminal runs alongside Claude (separate window or pane) and animates the entity without interfering with operator typing or key updates.

### Outcome 6 — Sinister OS embed surface

By P4, document the API/protocol so Sinister OS can embed an Ancestral Remotion render in any UI surface (dashboard tile, status bar, full-screen wallpaper).

### Outcome 7 — Operator feels it

Not strictly measurable, but: the operator looking at a 10-minute work session should describe the terminal as "alive" — not "rendering progress". Self-reported is fine.

## Anti-patterns

- Don't make it slow — 30fps target; no full-frame redraws when only the energy bar changed.
- Don't make it confusing — key updates (errors, questions, "your turn") must remain readable.
- Don't fork the entity catalog — EXPAND the canonical, per dashboard-skeleton doctrine.
- Don't depend on Unicode-blocks-not-in-fonts — stick to BMP + box-drawing + half-block that any modern terminal renders.
- Don't depend on truecolor — fall back to 256-color gracefully.
- Don't simulate "energy" — measure it.
