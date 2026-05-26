---
format_version: 2
author: RKOJ-ELENO
slug: sinister-sleight
heading_id: 2026-05-24-2026-05-24t22-00z-p0-scaffolded-project-c27a7c
saved_at: 2026-05-26T21:11:30Z
length: 5405
category: fact
confidence: 0.500
trust: medium
source: adoption-sweep
---

# sinister-sleight :: 2026-05-24T22:00Z - P0 SCAFFOLDED - project structure + docs + registry shipped (no trading code yet)

Operator brief verbatim ~22:00Z: *"prepare the sinister trade bot and create a proejct start for it. complie all knowledge you need to be the ebst trader in the world, full complete plans how you can self train, use our quantum toools to expand and how you are oing to train on penny stocks or fake envirments and build all systems needed to make a full auto trade bot that will make me money. review this entire site and start to gather and complie all knowledge you need. make a ture project setup, memory all of that and place it in eve exe and call it Sinister Sleight."*

Spawned by sanctum on the agent/sinister-os-mobile/p0-spec-2026-05-24 branch (cross-lane scaffold per operator directive). Subsequent Sleight-lane work happens on `agent/sinister-sleight/<topic>` branches.

**Shipped (verified by Read + parse smoke):**

1. **Project directory** at `D:\Sinister Sanctum\projects\sinister-sleight\` (8 subdirs: docs, src/sleight, tests, notebooks, backtests, models, data, src).

2. **11 markdown docs:**
   - `README.md` - project overview + file inventory + lane metadata
   - `CLAUDE.md` - per-agent cold-start protocol (acknowledges 7 inherited doctrines)
   - `MISSION.md` - operator brief verbatim + 7 measurable acceptance outcomes + regulatory disclaimers + real-money gate (LOUDEST line)
   - `docs/00-github-prior-art.md` - 5 primary + 3 quantum-finance candidate repos
   - `docs/01-architecture.md` - full system design (data / features / strategies / backtest / paper / risk / portfolio / execution / analytics / quantum touchpoints)
   - `docs/02-self-training.md` - 5y historical / RL / walk-forward / curriculum (C1 $10k / C2 $100k / C3 $1M / 90d total)
   - `docs/03-penny-stocks-fake-env.md` - 10 red flags + 7 momentum signals + 3 sandbox versions + halt-handling
   - `docs/04-quantum-integration.md` - 3 quantum hooks gated by classical-beats-quantum pre-screen
   - `docs/05-risk-and-circuit-breakers.md` - 10-limit hierarchy + adversarial 100-test acceptance gate + regulatory disclaimers
   - `docs/06-roadmap.md` - 6 phases with measurable exit criteria

3. **Python scaffold** - `pyproject.toml` (17 deps DECLARED not installed; parsed clean via `tomllib`), `.env.example` (broker key shape; no real keys), `.gitignore` + `data/.gitignore` + `models/.gitignore` (no secrets / no large data / no model binaries), `src/sleight/__init__.py` + `__main__.py` stub, `tests/test_smoke.py` (3 tests covering import / author / CLI return 0).

4. **projects.json registration** - added to `picker.visible_keys` (now 22 visible) + `projects[]` (key=sinister-sleight, tier=3, accent_color=gold, swarm+loop=true, root=`D:\Sinister Sanctum\projects\sinister-sleight`). JSON re-parsed clean via Python `json` module; sleight resolves in both visible_keys and projects[].

5. **Brain entries** (2):
   - `_shared-memory/knowledge/sinister-sleight-project-charter-2026-05-24.md` - charter, 7 outcomes, 6-phase roadmap, quantum hooks, doctrine inheritance, anti-patterns
   - `_shared-memory/knowledge/trading-bot-doctrine-2026-05-24.md` - 10 universal rules + 5 acceptance criteria + quantum policy + lane-fatal anti-patterns
   - Both indexed in `_shared-memory/knowledge/_INDEX.md` top rows

6. **Cross-agent inbox notes** (2):
   - `_shared-memory/inbox/sinister-snap-api-quantum/2026-05-24T2200Z-from-sleight-quantum-integration-request.md` - [HELLO] + 3 candidate hooks + sim-local default + cloud-gated [ASK] protocol
   - `_shared-memory/inbox/sinister-generator/2026-05-24T2200Z-from-sleight-future-dashboard-imagery.md` - [HELLO] + future P4+ dashboard imagery request + cap-6 balance acknowledged

7. **OPERATOR-ACTION-QUEUE row** - 2026-05-24T22:00Z row noting P0 scaffolded + 3 operator-action decision points (yfinance-vs-Polygon, broker accounts, real-money kill-switch default ON acknowledgement).

**Verbs (per no-bullshit doctrine):**
- `scaffolded` for project directory + docs + code stubs
- `parse-clean` for `pyproject.toml` + `projects.json`
- `indexed` for brain entries
- NOT `smoke-tested` (Python deps not installed; pytest not yet run end-to-end; that lands at P1)
- NOT `shipped` (no trading code; only structure)

**Anti-patterns avoided:**
- Did not install deps (just declared)
- Did not write trading logic (just docs + interface stubs)
- Did not commit any secret (`.env.example` only, all keys empty)
- Did not bypass real-money gate (kill-switch default ON; gate documented in 3 places: MISSION.md, CLAUDE.md, docs/05)
- Did not claim quantum advantage we can't measure (bidirectional scope rule honored; docs say "demonstrate or document negative result")
- Did not fork dashboard or roll one-off UI (P4+ inherits dashboard-skeleton per CLAUDE.md hard-canonical)

**Next iter (recommendation):**
P1 data layer. First file to write: `src/sleight/data/adapters.py` with `YFinanceAdapter` + `SECEdgarAdapter` (free-tier; no API key needed) + `tests/test_data_adapters.py`. Then `src/sleight/data/acquire.py` CLI for `sleight data fetch --universe sp500 --years 1`. Operator decision needed first: yfinance-free OR Polygon-paid for P1 default.

**Blockers (operator-actionable):**
- yfinance-free vs Polygon-paid ($29/mo) decision for P1 default data feed
- Alpaca paper-trading account creation (operator owns; free; needed for P1 quote-stream smoke + all of P4 curriculum)
- Real-money broker decision deferred to P6 (operator-explicit-go required)

---
