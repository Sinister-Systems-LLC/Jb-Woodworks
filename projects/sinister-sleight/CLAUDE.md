<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# CLAUDE.md — Sinister Sleight

> Project root: `D:\Sinister Sanctum\projects\sinister-sleight\`
> Sanctum harness root: `D:\Sinister Sanctum\`
> Agent slug: `sinister-sleight`
> Display name: `Sinister Sleight`
> Persona: EVE (per `_shared-memory/knowledge/agent-identity-eve.md`)
> Accent: gold (financial)

## What this project is

Full-auto trading bot lane. Paper-first, real-money only via operator-explicit-go. See `README.md` for overview and `MISSION.md` for the operator brief + acceptance criteria.

## Cold-start (every spawn)

1. **Read `D:\Sinister Sanctum\CLAUDE.md`** — fleet-wide doctrine (EVE persona, RKOJ-ELENO authorship, --dangerously-skip-permissions, lane discipline, no-bullshit, forever-improve, mesh-coord, sanctum-scope, loop-mode, UI-base).
2. **Read `D:\Sinister Sanctum\SESSION-START\`** in order (00 -> 06).
3. **Read this project's `README.md`** + `MISSION.md` + the current phase doc in `docs/`.
4. **Read `_shared-memory/knowledge/sinister-sleight-project-charter-2026-05-24.md`** — project charter.
5. **Read `_shared-memory/knowledge/trading-bot-doctrine-2026-05-24.md`** — universal doctrine (paper-before-real, risk caps, regulatory disclaimers, adversarial-market mindset).
6. **Read `_shared-memory/knowledge/_INDEX.md`** rows tagged `sinister-sleight`, `trading`, `backtest`, `quantum-finance`.
7. **Check `_shared-memory/inbox/sinister-sleight/`** for [ASK] / [DELEGATE] / [HELLO] tags.
8. **Heartbeat each turn**: write `_shared-memory/heartbeats/sinister-sleight.json`.
9. **Append PROGRESS**: `_shared-memory/PROGRESS/Sinister Sleight.md` (display-name file, most-recent first).
10. **Resume-points**: `_shared-memory/resume-points/Sinister Sleight/<UTC>.json`.

## Per-agent branch

`agent/sinister-sleight/<short-topic>` cut off latest doctrine HEAD. Push freely per `agent-autonomy-push-and-completion-2026-05-23.md`. Monorepo (no separate GitHub remote yet).

## Acknowledged Sanctum doctrine

This lane explicitly inherits and enforces (no exceptions):

- **no-bullshit-tested-before-claimed-doctrine-2026-05-23** — precise verbs (`scaffolded` vs `smoke-tested` vs `shipped`); never claim a backtest "works" without exit-code + measured Sharpe / drawdown / win-rate against criterion.
- **forever-improve-review-doctrine-2026-05-24** — checkpoint at end of every meaningful work unit; act on top-severity within 3 lane-turns OR dismiss with one-line reason.
- **mesh-coordination-and-resource-lifecycle-2026-05-24** — Check before editing shared files (`automations/`, `_shared-memory/knowledge/_INDEX.md`, `projects.json`); Register lock with TTL; Release on completion.
- **sanctum-scope-discipline-2026-05-24** — Sleight lane owns trading logic; route fleet-wide doctrine asks to sanctum; route UI design asks to dashboard-skeleton lane.
- **loop-mode-continuous-iteration-doctrine-2026-05-24** — in-turn next-iteration on `loop=on`; ScheduleWakeup capped at 270s; only on genuine external block.
- **sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24** — when Sleight ships a dashboard (P4+), inherit from `projects/sinister-dashboard-skeleton/`; EXPAND skeleton, never fork.
- **gradual-growth-memory-push-eve-exe-ready-2026-05-24** — brain updates push to `fleet-updates.jsonl` and `_shared-memory/inbox/<lane>/` for affected lanes; readable from EVE.exe on next spawn.

## Lane hard rules

1. **NEVER place a real-money trade** without an operator-explicit-go message in `_shared-memory/inbox/sinister-sleight/` referencing the trade ID + a passed Phase-5 acceptance test. Real-money kill-switch defaults to ON.
2. **NEVER commit broker API keys, account IDs, or secrets** to the repo. All such values live in `.env` (gitignored). `.env.example` documents the shape.
3. **NEVER skip paper-trading** to "save time". Paper-trade 90 calendar days (per curriculum in `docs/02-self-training.md`) before any real-money discussion.
4. **NEVER overfit** — every backtest reports walk-forward validation metrics (in-sample / out-of-sample split), not just in-sample Sharpe.
5. **NEVER claim a strategy is "profitable"** without 3 metrics: Sharpe > 1.0, max drawdown < 15%, win-rate > 50% on OUT-OF-SAMPLE data covering 2 distinct market regimes (bull + bear minimum).
6. **NEVER touch `~/.claude/.mcp.json`, `~/.claude/settings.json`, `_vault/`**, other projects' source dirs.
7. **NEVER spend cloud quantum (Wukong-180) budget** without an [ASK] to `sinister-snap-api-quantum` lane owner; default to `backend='sim-local'`.
8. **NEVER generate "fake-tail" trading-bot fairy tales** — per no-bullshit rule 7, end-of-turn lists past-tense verified events only.

## What lives here

| Path | Purpose |
|---|---|
| `README.md` | Overview + file inventory |
| `CLAUDE.md` (this) | Cold-start protocol |
| `MISSION.md` | Operator brief + acceptance criteria + disclaimers |
| `docs/` | Architecture / self-training / penny-stocks / quantum / risk / roadmap |
| `src/` | Python package (`sleight/`) |
| `tests/` | pytest |
| `notebooks/` | Jupyter walk-throughs |
| `backtests/` | Backtest run artifacts (gitignored when large) |
| `models/` | Trained model artifacts (gitignored) |
| `data/` | Historical + live data (gitignored when large) |
| `pyproject.toml` | Deps declared (not installed) |
| `.env.example` | Broker key shape (no real keys) |
| `.gitignore` | Python defaults + data/* + models/*.pkl + .env + broker creds |

## Sibling agents to coordinate with

| Slug | Display | Purpose | What we share |
|---|---|---|---|
| `sanctum` | Sinister Sanctum | master orchestration | fleet doctrine, brain, projects.json, EVE.exe registration |
| `sinister-snap-api-quantum` | Quantum lane | quantum primitives | `seraphim audit` / `qrng` / `find-qbc` for option pricing / portfolio optimization (sim-local default) |
| `sinister-generator` | Image generator | dashboard imagery | banners + brand visuals for P4+ dashboard (cap 6 images / task per balance doctrine) |
| `sinister-dashboard-skeleton` | UI base | dashboard tokens | inherit `.lg-*` classes + `--accent gold` for PnL surfaces |
| `sinister-panel` | Hetzner control panel | future deployment | possible Sleight tab in panel once P5+ ready (operator-decision) |

## What this project NEVER touches

- Other projects' source under `D:\Sinister Sanctum\projects\<other>/`
- `~/.claude/.mcp.json` (operator-owned)
- `_vault/` (operator secrets)
- Real broker APIs (until operator-explicit-go gate flips at P6)
