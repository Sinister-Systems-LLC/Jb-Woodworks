# Sinister Memory — PROGRESS log

**Author:** RKOJ-ELENO :: 2026-05-25 (sinister-memory lane)

Newest entry at top. Append, do not rewrite.

---

## 2026-05-25 (this session) — P1 + P2 wired + real-data smoke (accepted at top; PROGRESS corrected)

**Shipped (verified):**

- **P1 — forever-improve.ps1 AutoSave**: added `-AutoSave -Summary <text>` params + wired `sinister-memory save` call in `Tally` dispatch. Agents can now persist iter-close memories via `forever-improve.ps1 -Action Tally -Lane <slug> -AutoSave -Summary <text>`. Smoke: Tally still prints table correctly (parse-clean).
- **P2 — start-sinister-session.ps1 inject-spawn-phrase**: added `Get-SinisterMemoryInject` function (parallel to `Get-MemoryRecallInject`); wired call in RESUME Build-Phrase after forge-memory inject. Every future spawn gets `SINISTER_MEMORY (last iter-close memories for <slug>):` in cold-start phrase.
- **encoding fix** — `recall.format_hits_markdown`: `—` (em-dash) → `--` (ASCII), removes Windows CP1252 mojibake in terminal output.
- **real-data smoke** — `sinister-memory --root "D:\Sinister Sanctum" index`: indexed=303 skipped=0 removed=0 (live `_shared-memory/`). `recall "loop relentless"` returns ranked brain entries. CLI exit 0.
- **pkg install** — `pip install -e .` confirmed; `sinister-memory` now on PATH.
- **pytest 5/5 PASS** — re-confirmed after encoding fix.

**Heartbeat:** `_shared-memory/heartbeats/sinister-memory.json` written.

---

## 2026-05-25 07:32 UTC — sinister-memory lane scaffolded (operator 07:29:17Z)

**Operator verbatim 2026-05-25T07:29:17Z:** *"make sure loop system works and add to eve exe a project start for Sinister Memroy and complie all thigsn he needs there"*

**Shipped (sanctum master, P0 scaffold so EVE.exe picker can spawn the lane):**

- `projects/sinister-memory/CLAUDE.md`: lane cold-start (scope, in/out, branch convention, composes-with)
- `projects/sinister-memory/src/sinister_memory/__init__.py`: package marker with primitives surface (store/recall/supersede/decay/cluster/verify — NotImplementedError until P1)
- `projects/sinister-memory/` already had `src/sinister_memory/`, `docs/`, `tests/` empty scaffold dirs from earlier work
- `automations/session-templates/projects.json`: new entry registering lane in EVE.exe picker
- `_shared-memory/PROGRESS/Sinister Memory.md`: this file

**Next iter (P1 — first primitive impl):**

- Implement `store()` + `recall()` backed by `_shared-memory/knowledge/_INDEX.md` (consume existing brain rows as first dataset).
- Wire to Ruflo MCP `agentdb_hierarchical-store` / `agentdb_hierarchical-recall` for vector backing.
- pytest fixtures covering 5 synthetic memories + 5 real brain rows + decay assertion.
