<!-- Author: RKOJ-ELENO :: 2026-05-25 -->
# 03 — Render Engine

## High-level

```
+-----------+    +------------+    +------------+    +--------+
| stdin /   | -> | EnergyTap  | -> | FrameMixer | -> | Output |
| pipe-tail |    | (bytes/s)  |    | (entity +  |    | (ANSI) |
+-----------+    +------------+    | palette +  |    +--------+
                                   |  rule)     |
                                   +------------+
```

- **EnergyTap** — reads bytes from a source (stdin / named pipe / file-tail) into a ring buffer; reports rolling bytes/sec averaged over the last 5s, clamped to a configurable max for visual gain.
- **FrameMixer** — pulls (entity, idle_palette, high_energy_palette, rule) from the registry; interpolates between palettes based on energy 0.0–1.0; applies the rule (rotation / shuffle / pulse) keyed off frame counter.
- **Output** — writes ANSI escape sequences to a target file descriptor (stdout by default; named-pipe sink in sidecar mode at P2).

## Frame budget

30 fps target → 33 ms / frame. Frame work:

- 0–5 ms — read EnergyTap, compute current rate.
- 5–15 ms — render frame string (concatenation of color-prefixed cells).
- 15–25 ms — write to output (single `sys.stdout.write` + `flush`).
- 25–33 ms — slack.

If a frame overruns, we drop the next frame and continue. Frame counter still increments so animations stay phase-correct.

## ANSI primitives

| Primitive | Sequence | Notes |
|---|---|---|
| Move cursor home | `\033[H` | top-left |
| Clear screen | `\033[2J` | full clear (use sparingly) |
| Erase line | `\033[2K` | one line |
| Hide cursor | `\033[?25l` | while rendering |
| Show cursor | `\033[?25h` | restore on exit |
| Truecolor FG | `\033[38;2;R;G;Bm` | preferred |
| 256-color FG | `\033[38;5;Nm` | fallback |
| Reset | `\033[0m` | always reset between cells |
| Alt screen | `\033[?1049h` / `\033[?1049l` | sidecar uses this so we don't pollute scrollback |

## Energy calculation

```python
# Ring buffer of (timestamp, bytes_read) pairs over last 5s.
# Energy = total bytes in window / 5.0
# Normalize: clamp(energy / ENERGY_MAX_BYTES_PER_SEC, 0.0, 1.0)
# ENERGY_MAX_BYTES_PER_SEC default = 2048 (Claude streaming text)
```

## Palette blending

For energy `e ∈ [0, 1]`:

- 0.0 ≤ e < 0.3 → idle palette, full saturation as-is.
- 0.3 ≤ e < 0.7 → blend idle with high-energy linearly, channel-wise.
- 0.7 ≤ e ≤ 1.0 → high-energy palette, with periodic "spike" frames using the danger color at frame % 8 == 0.

Blending uses HSV space (convert HEX → HSV → lerp → HEX) so the path between palettes doesn't pass through mud.

## Rule engine

Each entity has a `rule` string. Initial vocab:

| Rule | Effect |
|---|---|
| `shimmer` | every frame, rotate hue + (frame * 6°) mod 360 |
| `rotate-rows-down` | shift rendered glyph rows down by 1 per frame |
| `rotate-rows-up` | shift up by 1 per frame |
| `pulse-row-N` | row N alternates full / half / off / half per frame |
| `shuffle-cells-A-B` | randomly permute cells in lines [A, B] per frame |
| `collapse-every-N` | every Nth frame, replace glyph with the danger color column |

Rules can compose: `shimmer; rotate-rows-up; pulse-row-4`.

## Sidecar terminal (P2)

Two surfaces:

1. **Inline** (P0–P1) — render directly to the same terminal Claude runs in, with alt-screen so scrollback isn't polluted. Risk: collides with operator keystrokes. Mitigation: only animate when stdout is idle for >100 ms.
2. **Sidecar** (P2) — open a second Windows Terminal / iTerm pane and stream frames to it via a named pipe. Operator types into Claude pane; entity animates in the sidecar.

## Failure modes + handling

| Failure | Detection | Recovery |
|---|---|---|
| Terminal doesn't support truecolor | `$COLORTERM` not `truecolor` | fall back to 256-color column |
| Terminal too narrow (<25 cols) | `os.get_terminal_size()` | render minimal "Sanctum :: E:▮▮▮___" status line only |
| Frame overrun | wallclock check | drop next frame, log to `.last-frame-overrun.json` |
| EnergyTap empty | source closed | render at energy=0.0 (idle), display "[idle]" indicator |
| Palette lookup miss | unknown key | fall back to violet-core, log warning |
| Entity lookup miss | unknown project | fall back to sanctum entity |

## What we don't do at P0

- Per-glyph cell animation (every glyph is line-level only).
- Sound (the operator wanted artistic; we'll evaluate at P3).
- Mouse / interaction (display-only at P0).
- Custom user palettes (the catalog is canonical at P0–P2).
