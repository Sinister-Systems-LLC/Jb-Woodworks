# Sinister OS — dashboard-skeleton inheritance binding

> **Author:** RKOJ-ELENO :: 2026-05-25
> **Lane:** sinister-os
> **Binds:** every web UI surface this lane ships from this commit forward
> **Operator-canonical (verbatim 2026-05-25T~10:15Z):** *"you best have used my deshbaord skeleton and activity expand on that so taht we will make the best dsahboards and ui's"*
> **Composes-with:** `sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24` (the doctrine) · `dashboard-skeleton/THEME-DOCTRINE.md` (11 Commandments) · MASTER-AUDIT-EXPANSION-2026-05-25 Block J (HTTP shims that consume this binding)

## 1. What inherits + what doesn't

| Surface | Substrate | Inherits skeleton? |
|---|---|---|
| **VM preview (Phase 1A)** — i3 + xterm + banner.txt | OS shell layer (not web UI) | NO — this is the desktop ITSELF, not a dashboard rendered on it |
| **Sinister Panel** (`https://localhost:8443/`) | Bun + React, already on Hetzner | YES (already inherits) — accessed via existing `compose.panel-shell.yml`, no re-implementation needed |
| **Block J HTTP shims** (4 review pages: eve-status / gpu-arbiter / game-mode / chat-bridge) | NEW Next.js apps | **YES — MUST inherit** (this doc binds it) |
| **Block H "Windows-feel" KDE Plasma theme** | KDE Plasma (Qt-native, not web) | N/A — different substrate; uses Plasma Activities + Lightly theme |
| **EVE Desktop GTK4 app** (Phase 2, post-P3) | GTK4 (native Linux) | N/A — token-mirror the skeleton's accent + spacing scale in CSS, but GTK4 is not Next.js |
| **wofi chat sheet** | gtk4-layer-shell (native) | N/A — token-mirror only |
| **waybar pill** | waybar custom module (JSON output) | N/A — token-mirror only |

**Token-mirror** means: the GTK4 / Wayland-native surfaces consume the same `--accent`, `--surface-0..3`, motion durations, and iOS-easing curve as the skeleton — but they don't import the skeleton's React components.

## 2. Block J shims: the concrete inheritance plan

Block J ships 4 small Next.js apps as HTTP review surfaces for the docker preview + future bare-metal OS:

| Route | Purpose | Skeleton primitives used |
|---|---|---|
| `/eve-status` | EVE daemon state machine + intent log + uptime | `<PageShell>`, `<TabHeader>`, `<StatCard>` × 4 (state / epoch / uptime / actions), `<Card>` for recent action list, `<Icon name="eve">` |
| `/gpu-arbiter` | GPU arbiter mode + per-agent slice freezer state + nvidia-smi metrics | `<PageShell>`, `<TabHeader>`, `<KpiCard>` × 3 (util / power / VRAM), `<Chart>` for util-over-time, `<StatCard>` for agent rows |
| `/game-mode` | game-mode state machine + 15-step ARMING checklist + per-game overrides | `<PageShell>`, `<TabHeader>`, custom `<StateMachineDiagram>` (NEW primitive — see § 4), `<Card>` per step, `<Button>` for arm/disarm (always `rounded-full` per Commandment 2) |
| `/chat-bridge` | EVE-LLM bridge stats + persona picker + last 5 chats | `<PageShell>`, `<TabHeader>`, `<KpiCard>` for daily-token-count + cache-hit-rate, `<StatCard>` per persona, recent-chats `<Card>` list |

### 2.1 Sinister OS variant of the skeleton

Per the skeleton's doctrine "Per-surface `--accent` is the only allowed divergence":

- **Sinister OS accent:** **`--accent: #c084fc`** (Sinister purple — overrides skeleton's iOS-blue `#0A84FF`)
- **Sinister OS accent-hover:** `--accent-hover: #d8b4fe`
- **Sinister OS accent-pressed:** `--accent-pressed: #a855f7`
- **Sinister OS accent-soft:** `color-mix(in oklab, var(--accent) 15%, transparent)`
- **Sinister OS accent-ring:** `color-mix(in oklab, var(--accent) 60%, transparent)`

Everything else from THEME-DOCTRINE.md is preserved unchanged: `.lg-card`, `.lg-card-hero`, `.lg-rail`, `.lg-popover`, `.lg-pill[-active]`, `.lg-button`, `.lg-input`; surface neutrals; motion durations (`--motion-fast 150ms`, `--motion-med 300ms`, `--motion-slow 600ms`); iOS easing `cubic-bezier(0.22, 1, 0.36, 1)`; `rounded-full` on Button; custom SVG sprite; no emojis in chrome; no AI-slop copy.

### 2.2 Where the inherited app lives in the repo

```
projects/sinister-os/
└── source/
    └── docker-stack/
        └── dashboards/                            # NEW — Phase 2 Day 4-5 (Block J)
            ├── README.md                          # inheritance notes + how to add a route
            ├── package.json                       # extends dashboard-skeleton package.json
            ├── tailwind.config.ts                 # extends skeleton's tailwind.config.ts
            ├── postcss.config.mjs                 # copied verbatim from skeleton
            ├── next.config.mjs                    # copied verbatim from skeleton
            ├── app/
            │   ├── layout.tsx                     # imports skeleton's <Shell>
            │   ├── globals.css                    # imports skeleton's tokens + Sinister purple override
            │   ├── eve-status/page.tsx
            │   ├── gpu-arbiter/page.tsx
            │   ├── game-mode/page.tsx
            │   └── chat-bridge/page.tsx
            ├── components/
            │   ├── (re-exports from dashboard-skeleton/components)
            │   └── StateMachineDiagram.tsx        # NEW — see § 4
            └── lib/
                ├── eve-client.ts                  # talks to eve-daemon-stub via http://eve-daemon-stub:7331
                └── theme.ts                       # extends skeleton/lib/theme.ts with --accent override
```

### 2.3 Build chain (Block J extension)

`compose.dashboards.yml` (NEW, Phase 2 Day 4) adds a `dashboards` service:

```yaml
dashboards:
  build:
    context: ./dashboards
    dockerfile: ../Containerfile.dashboards   # multi-stage Next.js prod build
  ports:
    - "8081:3000"
  depends_on:
    - eve-daemon-stub
    - mock-panel
  environment:
    - NEXT_PUBLIC_EVE_URL=http://eve-daemon-stub:7331
    - NEXT_PUBLIC_PANEL_URL=http://mock-panel:8090
```

Operator opens `http://localhost:8081/eve-status` (or the 3 other routes) — sees a Sinister-purple Liquid Glass dashboard.

## 3. Per-Commandment compliance plan (the 11)

| # | Commandment | How Block J shims comply |
|---|---|---|
| 1 | One palette | Sinister purple ramp (50-950) replacing iOS-blue ramp; semantic survivors `--danger`/`--warning` unchanged |
| 2 | One primitive per role | Use skeleton's `<Button>`, `<Card>`, `<Input>`, `<Chart>`, `<Icon>`, `<TabHeader>`, `<StatCard>`, `<KpiCard>` — never raw `<button>` / `<div className="rounded-xl ...">` |
| 3 | No stock icons | Use skeleton's `components/icons/sprite.svg` (~120 glyphs); add new Sinister-OS glyphs (eve-pill, gpu-chip, game-controller, chat-bubble, lock-shield) to sprite — EXPAND skeleton |
| 4 | No emojis in UI | All text passes through `<Icon>` or plain text only |
| 5 | No AI-slop copy | Manual review of every string; ESLint `banned-phrases` rule active |
| 6 | Motion is a system | Use skeleton's 3 durations + 1 curve; no custom keyframes |
| 7 | Liquid Glass material | Use `.lg-*` classes verbatim; never roll own backdrop-filter |
| 8 | Numbers animate | `<StatCard>` + `<KpiCard>` use `<NumberTicker>` automatically |
| 9 | Pages have signature | Each of 4 routes has one custom detail: `/eve-status` = breathing daemon-pulse ring; `/gpu-arbiter` = animated power-draw gauge; `/game-mode` = state-machine arrow flow; `/chat-bridge` = persona-color shimmer on active persona card |
| 10 | Every primitive ships empty/loading/error | Use skeleton's `<EmptyState>` + `<Loading>` + `<Error>` slots; no raw spinners |
| 11 | Production parity TODO | Each route's source carries `## Production parity TODO` block listing the prod surfaces it should mirror later |

## 4. EXPAND — new primitive needed: `<StateMachineDiagram>`

The skeleton has Chart / Map / KPI / Table primitives but no state-machine diagram. The EVE daemon (5-state machine) and game-mode subsystem (7-state machine) both need to render typed states with transitions.

**Per the canonical doctrine: when a primitive is missing, ADD to skeleton FIRST, commit there, update PATTERNS.md, then consume.**

Plan for skeleton expansion:

1. Open PR to dashboard-skeleton repo: add `components/primitives/StateMachineDiagram.tsx`
2. Spec:
   - Props: `states: {id, label, accent?}[]`, `transitions: {from, to, label?}[]`, `current: stateId`, `onTransition?: (to) => void`
   - Material: `.lg-card` outer + per-state `.lg-pill` (active: `.lg-pill-active`)
   - Motion: state transitions use `--motion-med` + iOS easing
   - Empty / Loading / Error slots
3. Update `dashboard-skeleton/PATTERNS.md` with usage recipe
4. Update `dashboard-skeleton/docs/component-library.md` row
5. THEN import + use in sinister-os Block J shims

This is the EXPAND-not-fork pattern operator binds.

## 5. Pass criterion

Block J is doctrine-compliant when:

- `npm run doctrine-audit --strict` exits 0 on the dashboards/ app
- Every primitive used is from skeleton's catalog (no inline className blobs)
- Per-route signature exists (catalogued)
- Empty/Loading/Error slots present everywhere
- `--accent` overridden to Sinister purple via single CSS file
- No emojis, no AI-slop, no stock icons
- `<StateMachineDiagram>` shipped to skeleton repo first (PR merged), then consumed

## 6. Cross-references

- `_shared-memory/knowledge/sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24` (the binding doctrine)
- `projects/sinister-dashboard-skeleton/dashboard-skeleton/THEME-DOCTRINE.md` (11 Commandments + iOS-blue ramp + Liquid Glass surfaces)
- `projects/sinister-dashboard-skeleton/dashboard-skeleton/00-START-HERE.md` (~3 min agent onboarding)
- `projects/sinister-dashboard-skeleton/dashboard-skeleton/PATTERNS.md` (copy-paste recipes for every UI shape)
- `projects/sinister-os/plans/MASTER-AUDIT-EXPANSION-2026-05-25/plan.md` § 3.10 Block J (Docker stand-up shims that consume this)
- `projects/sinister-os/plans/EXECUTION-PLAN-2026-05-25/plan.md` § 3 Day 4-5 (Block J build window)
- Operator-canonical utterance `_shared-memory/operator-utterances.jsonl` ts=2026-05-25T~10:15Z
