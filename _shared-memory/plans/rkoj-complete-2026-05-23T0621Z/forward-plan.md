# RKOJ — complete-without-operator forward-plan (06:21Z slice)

> **Author:** RKOJ-ELENO :: 2026-05-23
> **Agent:** rkoj (EVE on RKOJ; umbrella for Forge + Term + Workstation + Mind + Claw per `projects.json` v6)
> **Branch:** `agent/rkoj/next-slate-2026-05-23` (cut fresh off doctrine HEAD `73c628b`)
> **HEAD at plan time:** `73c628b` (`doctrine+freeze+autonomy: anti-revert protection system + Sinister Freeze restore + agent autonomy override`)
> **Predecessor plan:** `_shared-memory/plans/rkoj-complete-2026-05-23T0455Z/forward-plan.md` (substantially shipped — see (a) below)
> **Mode:** /loop dynamic (self-paced) — operator broadcast `2026-05-23T1545Z` lifted self-imposed push gates

## Branch-cut note (pre-doctrine HEAD hazard caught + handled)

The prior `agent/rkoj/complete-without-operator-2026-05-23` branch was cut at `b9e89dc` — BEFORE the anti-revert doctrine commit `73c628b`. Checking it out silently rolled `CLAUDE.md` back to the 6-step cold-start (no understand-anything pre-call, no DO-NOT-REVERT block). Detected via the working-tree `CLAUDE.md` diff. Fix: cut a fresh branch off the doctrine HEAD instead of resurrecting the pre-doctrine one. Brain-entry candidate: `branch-checkout-silently-undoes-doctrine-2026-05-23.md` (in (c) below).

## (a) What's already shipped since the 04:55Z plan

| Commit | Surface | Effect |
|---|---|---|
| `4bc5b4d` | `forge/skills.py` watchdog + `forge/panes/mermaid_panel.py` (new) + matrix row 5 re-audit | jcode-parity matrix rows 5/15/18 → ✅ |
| `6d00c59` | `rkoj/source/sinister_rkoj_qt/api_server.py` (+95 LOC) | matrix row 12 advanced — `GET /api/diagrams` + `GET /api/diagrams/<stem>` |
| `73c628b` | CLAUDE.md, SESSION-START/00-RULES.md, automations/canonical-protections-check.ps1, .claude/settings.json SessionStart hook, projects/sinister-freeze/, brain doctrines | anti-revert protection system + Sinister Freeze restore + agent autonomy override |

**RKOJ.exe version:** v1.6.88 (no re-ship needed this slice).
**Matrix delta:** 6 of 11 ASK rows ✅; 4 still 🚧 (Mind web view, claude-hooks, Skill_Seekers, browser-bridge); 2 operator-gated (agentgrep, Rust mermaid renderer).

## (b) What's in-flight

Nothing on disk in `projects/rkoj/source/`. Working tree dirty only from cross-lane Sanctum sweep; per canonical-10 those edits stay on the Sanctum branch and are not master-rkoj's lane to commit.

## (c) What's still open + master-actionable (this slice)

| # | Row | Source | Effort | Reversibility |
|---|---|---|---|---|
| 1 | **Mind web view consumer for `/api/diagrams`** — adds `static/diagrams.html` + `mind.js` route + `server.py` proxy endpoints (`/api/diagrams` + `/api/diagrams/<stem>` on `:5079` proxying RKOJ Workstation `:5077`, with a fallback to direct-read of `_shared-memory/forge-memory/mermaid-renders/` when `:5077` is offline). Last 🚧 on jcode matrix row 12. | jcode-feature-matrix.md row 12 + operator "all jcode features" | 30-45 min | R1 |
| 2 | **Brain-entry capture** — `branch-checkout-silently-undoes-doctrine-2026-05-23.md` (the pre-doctrine-HEAD branch-cut hazard caught above) + `_INDEX.md` row. | this session | 10 min | R0 |
| 3 | **Browser-bridge wrapper exploration** — `firefox-agent-bridge-0.9.9/` IS on disk at `C:/Users/Zonia/Desktop/Github Research/`. Read-only audit + write a `_shared-memory/knowledge/browser-bridge-integration-shape-2026-05-23.md` documenting the native-host protocol + what a Sinister wrapper would copy vs reuse. NO source clone this slice (per matrix row 26 "NOT clone-and-run"). | jcode matrix row 26 + operator "all jcode features" | 20 min | R0 |
| 4 | **PROGRESS append + resume-point write** — append this slice's outcomes to `_shared-memory/PROGRESS/rkoj.md`; run `automations/resume-point-write.ps1 -ProjectKey rkoj -AgentName rkoj -Mode resume`. | CONTRACT 7 | 5 min | R0 |
| 5 | **Commit + push `agent/rkoj/next-slate-2026-05-23`** — per `2026-05-23T1545Z-from-sanctum-no-more-self-imposed-blocks.json` broadcast, per-agent branches push freely. | broadcast + doctrine agent-autonomy-push-and-completion-2026-05-23 | 5 min | R1 |

**Total master-actionable effort:** ~70-85 min. End-to-end loop-able without operator gates.

## (d) What's operator-gated (RKOJ-tangential only — not blocking this slice)

| Row | Severity | One-liner | RKOJ blast |
|---|---|---|---|
| Restart Claude Code | 🔴 | (close + reopen this Claude Code window) — activates 12 MCP servers + 14 plugins enabled at Sanctum project level | RKOJ.exe runs independently; not blocking. |
| Set `ANTHROPIC_API_KEY` env var | 🟠 | `[Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY','sk-ant-...','User')` then restart shell + RKOJ.exe | Unlocks RKOJ v0.7.0+ Anthropic SDK direct tool-use loop. Without it, RKOJ uses the existing `claude -p` one-shot path. |
| Install Rust toolchain (`rustup-init.exe`) | 🟠 | Download from `https://rustup.rs`, run installer + MSVC Build Tools | Unblocks `tools/sinister-mermaid-render/` (matrix row 28). |
| Install missing external pkgs | 🟡 | Drop `claude-hooks-2.4.0/` + `Skill_Seekers-3.6.0/` into `C:/Users/Zonia/Desktop/Github Research/` | Unblocks matrix rows 23 + 24. |
| `gh auth refresh -h github.com -s workflow` | 🟡 | 30 sec browser prompt | Unblocks auto-push of workflow file changes. |

Nothing on (d) blocks (c) — the rkoj lane can ship this slate without any operator click.

## (e) Reversibility class per row (per canonical-11)

- **R0** (no-impact / reversible at file level): brain-entry write, PROGRESS append, plan write, resume-point write, browser-bridge audit doc
- **R1** (local commit, `git revert` works): Mind diagrams page + server.py proxy endpoint, PROGRESS commit
- **R2** (rebuilds artifact / re-ship of RKOJ.exe v1.6.89): NOT planned this slice
- **R3** (cross-lane impact): none — touches only `projects/sinister-mind/source/` + `_shared-memory/`
- **R4** (operator-only / wall): all (d) rows above; not master-actionable

## (f) Recommended ordering + rough effort

1. **(c)#1** Ship Mind diagrams page + server.py endpoints — **~35 min** — R1
2. **(c)#2** Brain-entry for branch-checkout-undoes-doctrine — **~10 min** — R0
3. **(c)#3** Browser-bridge audit doc — **~20 min** — R0
4. **(c)#4** PROGRESS append + resume-point write — **~5 min** — R0
5. **(c)#5** Commit + push — **~5 min** — R1

Loop cycles row-by-row. No operator gates between steps. End of turn = resume-point + concise human-readable summary per CONTRACT 6.

## Cross-references

- `_shared-memory/PROGRESS/rkoj.md` — append-only lane log
- `_shared-memory/knowledge/jcode-feature-matrix.md` — capability map; row 12 flip surface
- `_shared-memory/knowledge/do-not-revert-operator-canonical-protections-2026-05-23.md` — six protections
- `_shared-memory/knowledge/agent-autonomy-push-and-completion-2026-05-23.md` — per-agent branch push policy
- `_shared-memory/inbox/rkoj/2026-05-23T1545Z-from-sanctum-no-more-self-imposed-blocks.json` — broadcast that lifted self-gates
- `automations/session-contracts.md` — 6 binding contracts
- `projects/rkoj/source/sinister_rkoj_qt/api_server.py` — `/api/diagrams` endpoint (the producer)
- `projects/sinister-mind/source/mind/server.py` — Mind Flask :5079 (the consumer surface)
- `projects/sinister-mind/source/mind/static/` — `index.html` + `mind.css` + `mind.js` (where the new diagrams page lands)
