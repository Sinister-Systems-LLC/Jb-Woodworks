<!-- Author: RKOJ-ELENO :: 2026-05-25 -->
# Ancestral Remotion :: Sinister Term Themes

> Project root: `D:\Sinister Sanctum\projects\sinister-term-themes\`
> Slug: `sinister-term-themes` | Display: `Ancestral Remotion` | Accent: deep indigo `#6366f1`
> Tier: T3 (creative / UX) | Persona: EVE
> Status: P0 SCAFFOLDED + first sanctum entity demo runs

## Operator brief (verbatim 2026-05-25 ~03:30Z)

> "ok now the terminals have less logs but i want to be entertained like in our console using sinsiter term whilke claude is running i want you to make it an atristic ascii materpiece of color and express with al sorts of reds, blues, greens indigos violets. even have like entities like characters and have everything be slighly different based on teh project like you showing me visual emotion while you work. i want it to look cool as shit and have the feeling of it being endless that leaves me breathles. launch all agents you need for this. make it a sub project. its desc is sinister term themes. and this will be called ancestral remotion. and when its really running alot of energy through it, you can look at it and have the feeling as if you were looking at a living being. i want our uis to have that life i want you to update in md files that we what to display that much of artics vlaue and meaning to what we do and we are starting with teh logs. now i still want to see key updates. know what im suppose to answer. i can see all the things i need to see. like what if we went so far with the sinister os that no consoles are show and its just a complete UI built into the operating system on the servers with a complete command center for me to run all my companies from that is waht i want. i want a complete command center and a hive mind live eve to conquer my computer so i can use them to do whatever i want to do with them like fucking tony stark take note if this"

## Mission (one line)

A living, breathing ASCII entity that visualizes Claude work in real time — per-project palettes (reds / blues / greens / indigos / violets), energy-responsive (idle vs. high-throughput), endless variation, and the foundation for a complete Tony-Stark-tier Sinister OS command center.

## What this project is

Ancestral Remotion replaces the terminal's normal Claude-output spam with an animated ASCII surface that:

- **Renders an entity** — multi-line ASCII glyph mapped to the current project (Sanctum / Panel / OS / Snap / Sleight / etc.) with its own personality.
- **Reflects energy** — bytes-per-second of Claude stdout in the last 5 seconds drives palette intensity + glyph animation amplitude. High energy = the entity looks alive; idle = the entity breathes.
- **Per-project palettes** — Reds for control surfaces (Sinister Panel), Blues for OS depth (Sinister OS), Indigos for quantum/snap (Snap API Quantum), Greens for growth/money (Sinister Sleight), Violets for fleet core (Sanctum).
- **Surfaces key updates** — operator still sees what they need to answer, what to look at. Logs aren't gone, they're transformed.
- **Composes** — feeds the longer-term Sinister OS vision (no consoles shown; entire OS is a command center for running the operator's companies).

## What this project is NOT (yet)

- NOT a working terminal sidecar (P0 = render engine + entity catalog + 1 demo; sidecar lands at P1).
- NOT replacing the existing `projects/sinister-term/` — `sinister-term` is the terminal substrate; `sinister-term-themes` is the artistic visualization layer on top.
- NOT a GPU shader (everything stays in ANSI escapes + stdlib for portability).

## Quick demo (P0 ships this)

```bash
cd "D:/Sinister Sanctum/projects/sinister-term-themes"
python -m sinister_term_themes demo sanctum --frames 5
```

Should print the Sanctum entity glyph cycling through ~5 frames of HSV-shifted purple shimmer + a pulsing energy bar, then exit 0.

## Files in this project

| Path | Status | Purpose |
|---|---|---|
| `README.md` (this) | scaffolded | Project overview + operator brief verbatim |
| `CLAUDE.md` | scaffolded | Per-agent cold-start protocol |
| `MISSION.md` | scaffolded | The longer-term living-OS vision |
| `docs/00-overview.md` | scaffolded | What we're building in 5 pages max |
| `docs/01-entity-design.md` | scaffolded | Per-project entity catalog (5 initial) |
| `docs/02-color-palettes.md` | scaffolded | Per-project palette tables (HEX + ANSI 256) |
| `docs/03-render-engine.md` | scaffolded | Render-loop architecture |
| `docs/04-artistic-doctrine.md` | scaffolded | Why visual emotion matters (with operator quote) |
| `docs/05-roadmap.md` | scaffolded | P0 → P4 plan |
| `docs/06-sinister-os-integration.md` | scaffolded | How this becomes the Sinister OS command center |
| `pyproject.toml` | scaffolded | Stdlib-only Python 3.11 package |
| `src/sinister_term_themes/` | scaffolded | Package skeleton + entities/sanctum + cli |
| `tests/test_smoke.py` | scaffolded | 3 smoke tests |
| `.gitignore` | scaffolded | Python defaults |
| `.env.example` | scaffolded | Energy-source URI + frame-rate cap |

## Composes with

- `projects/sinister-term/` — the terminal substrate this paints onto
- `projects/sinister-dashboard-skeleton/` — UI base (we inherit token discipline; ASCII is not CSS but the discipline of NEVER-FORK + EXPAND-ONLY still binds)
- `projects/sinister-os/` — the larger command-center vision; Ancestral Remotion is the visual language

## Lane metadata

- Branch: `agent/sinister-term-themes/<short-topic>-<utc-date>`
- Heartbeat: `_shared-memory/heartbeats/sinister-term-themes.json`
- PROGRESS: `_shared-memory/PROGRESS/Ancestral Remotion.md`
- Resume-points: `_shared-memory/resume-points/Ancestral Remotion/<UTC>.json`
- Inbox: `_shared-memory/inbox/sinister-term-themes/`
