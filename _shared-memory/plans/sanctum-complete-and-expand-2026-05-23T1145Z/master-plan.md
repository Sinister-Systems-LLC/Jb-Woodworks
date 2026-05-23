<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# Sanctum :: Complete + Expand Everything :: Master Plan

**Created:** 2026-05-23 11:45Z
**Branch at creation:** `agent/sinister-sanctum/grant-autonomy-followup-2026-05-23` (cut off HEAD `8c57e8c`)
**Triggering directive (operator 2026-05-23):** *"switch to a sanctum branch and ship item 2. create a plan to complete and expand everything in the sanctum"*
**Author:** EVE on Sanctum
**Supersedes:** `_shared-memory/plans/sanctum-complete-2026-05-23T0455Z/forward-plan.md` (next-turn section) — items 1, 2, 3 in that plan are now shipped + verified; this plan reframes the remainder + adds the expansion lanes.

---

## TL;DR (one screen)

- **Where we are:** 8/8 canonical protections PASS; 9/9 grant-autonomy steps PASS via smoke-test; 14 projects visible in launcher, all roots resolve; 22 MCPs registered; 22 launcher directives A-O shipped; brain has 50+ doctrines indexed.
- **Open completion work (R0-R2, no operator gate):** 10 rows in Section B, grouped by lane.
- **Open expansion work (R0-R2):** 14 rows in Section C, grouped by surface.
- **Operator-gated:** 7 rows in Section D (Claude Code restart is #1 by impact).
- **Sequence:** Phase 0 (verify) → Phase 1 (mirror sync + queue refresh, this turn) → Phase 2 (lane-by-lane completion next 1-3 turns) → Phase 3 (expansion) → Phase 4 (operator-gated unlock).
- **Success criteria:** `canonical-protections-check.ps1` keeps PASS=8 FAIL=0; every project lane has fresh PROGRESS within 24h; every brain doctrine slug is indexed in `_INDEX.md`; OPERATOR-ACTION-QUEUE rolls only forward-looking items, never blocking ones.

---

## Section A — State of the fleet (cold to hot)

### A.1 Canonical protections (P1-P8)

Verified PASS this turn via `automations/canonical-protections-check.ps1`:

| # | Protection | State |
|---|---|---|
| P1 | `~/.claude/settings.json` bypassPermissions + dangerously-skip allowlist | PASS |
| P2 | understand-anything plugin enabled (user + Sanctum project) | PASS |
| P3 | CLAUDE.md cold-start step 0 = understand-anything pre-call | PASS |
| P4 | CLAUDE.md references `01_MEMORY\master\OPERATOR-DIRECTIVES.md` hub | PASS |
| P5 | CLAUDE.md references `09_REFERENCE\SANDBOX-GOTCHAS.md` | PASS |
| P6 | Brain entries (do-not-revert + sanctioned-bypasses) present + indexed | PASS |
| P7 | 00-RULES.md Rule 11 mandates understand-anything pre-call | PASS |
| P8 | projects.json: every project root exists on disk | PASS |

### A.2 Grant Claude Autonomy (9-step) script

`automations/grant-claude-autonomy.ps1` v2 (shipped in `73c628b`) verified via `-ReadOnly` smoke-test this turn:

| Step | Subject | Smoke Result |
|---|---|---|
| 1 | Project trust (hasTrustDialogAccepted=true) | 0 updated (all already trusted) |
| 2 | Env vars (SINISTER_SANCTUM_ROOT + SINISTER_USER) | 0 changed (already set) |
| 3 | Secrets surface (READ-only) | 2/6 set (GEMINI + OPENAI; the 4 operator-set keys are blank as expected) |
| 4 | MCP verify | 1/3 (sinister-bus present; ruflo + vault load via different registries — see B.5) |
| 5 | Scheduled tasks | 5/5 installed (auto-push + custodian + daily backup + RKOJ + Vault) |
| 6 | Permission allowlist | 213 allow + 12 deny entries (no additions needed) |
| 7 | canonical-protections-check verification | PASS (8/8) |
| 8 | SessionStart hook installer | already-installed |
| 9 | understand-anything plugin | already enabled (user + project) |

### A.3 Launcher (`start-sinister-session.ps1`)

22 jcode-style directives A through O shipped; PS-AST-parse-validated. 8 ASCII-art pieces in `automations/session-art/`. Free-text resume-point search (BM25-ish). Customize-Project (rename + accent). Clear-Context. S = Autonomy Setup picker option. Post-claude shell switches to `sterm` with bash fallback. `picker.visible_keys[]` covers 14 lanes in operator-canonical order. v6.1 baseline preserved at `automations/start-sinister-session-v6-baseline.ps1.bak`.

### A.4 Sinister Start.bat

v5 (Desktop canonical) — silent-close bug fixed; echoes every step; pause on non-zero exit; first-run autonomy bootstrap via marker file `~/.sanctum-autonomy-granted`; `--setup-autonomy` explicit re-run flag; EVE.exe probe + PS1 fallback. **Sanctum mirror synced this turn** (`tools/session-launcher/Sinister Start.bat` was at v4 — now matches v5).

### A.5 Brain (knowledge graph)

50+ doctrines indexed in `_shared-memory/knowledge/_INDEX.md`. 2026-05-23 brain entries:

- `mcp-server-failure-fix-2026-05-23` (doctrine, failure-fix, shipped)
- `jcode-swarm-token-parity-audit-2026-05-23` (audit, validated; 5 concrete recommendations)
- `spawned-window-capabilities-2026-05-23` (doctrine, standing-rule, binding)
- `eve-exe-launcher-jcode-speed-parity-2026-05-23` (doctrine, in-flight)
- `spawned-phrase-refusal-fix-2026-05-23` (doctrine, standing-rule, binding)
- `browser-bridge-integration-shape-2026-05-23` (doctrine, audit, proposed)
- `branch-checkout-silently-undoes-doctrine-2026-05-23` (doctrine, observed, binding)
- `sanctum-mirror-orphan-corruption-pattern-2026-05-23` (workaround)
- `agent-autonomy-push-and-completion-2026-05-23` (doctrine, standing-rule, binding)
- `handterm-vs-sinister-term-clarification-2026-05-23` (doctrine, binding)
- `launcher-v6.1-jcode-style-directives-2026-05-23` (doctrine, shipped)
- `forge-memory-usage-2026-05-23` (doctrine, validated)
- `wake-on-demand-bot-dispatcher-2026-05-23` (doctrine, proposed)
- `project-root-disk-integrity-2026-05-23` (doctrine, empirical, binding)
- `do-not-revert-operator-canonical-protections-2026-05-23` (doctrine, standing-rule, binding)
- `pip-editable-hides-mcp-cwd-emptiness-2026-05-23` (doctrine, audit-pattern, validated)
- `spawn-validation-end-to-end-2026-05-23` (doctrine, validated)
- `mcp-junction-fix-pattern-2026-05-23` (doctrine, shipped)
- `launcher-v6-concise-rewrite-2026-05-23` (doctrine, shipped)

### A.6 Per-lane status (parallel agents currently active)

| Lane | Last commit subject | Owner | State |
|---|---|---|---|
| sinister-generator | `8c57e8c ship(sinister-seraphim): quantum-compute application-layer rename` | sinister-generator agent | active (uncommitted work-tree) |
| rkoj | `ab16d16 ship(rkoj): v1.6.89 — no stray scrcpy windows + projects.json BOM fix` | rkoj agent | shipped; EXE rebuild pending operator |
| jb-woodworks | (uncommitted edits across hero/portfolio/services) | jb-woodworks agent | active |
| sinister-panel | (recent PROGRESS update) | sinister-panel agent | active |
| sinister-kernel-apk | (recent PROGRESS update) | kernel-apk agent | active |
| showmasters | (recent PROGRESS update) | showmasters agent | active |
| sanctum (this) | `8c57e8c` (inherited) → new branch | sanctum lane | this turn |

---

## Section B — Complete (close open items, R0-R2, in-lane)

Ordered by impact × reversibility-safety.

### B.1 (R1, 5 min) — Mark forward-plan items 2 + 3 shipped in OPERATOR-ACTION-QUEUE [THIS TURN]

The prior forward-plan (`sanctum-complete-2026-05-23T0455Z`) listed items 1, 2, 3 as "next turn — master-actionable". All three are shipped:

- Item 1 (commit anti-revert + freeze-restore work): commit `73c628b`
- Item 2 (Grant-Claude-Autonomy 9-step expansion): commit `73c628b` (smoke-tested PASS this turn)
- Item 3 (Sinister Start.bat first-run detection): Desktop bat v3 evening (lines 47-59 + 99-116); Sanctum mirror synced this turn

Queue update + close the rows. Brain entry tag bump (move `do-not-revert` from `doctrine, standing-rule, binding` → keep tag, add `verified-9-step-script-passes` to tag list).

### B.2 (R1, 10 min) — Resume-point chain cleanup

`_shared-memory/resume-points/Sinister Sanctum/` currently has 21 files. `resume-point-write.ps1` already prunes to last 20 on each write (saw "pruned 1 old" this turn). Verify the prune logic respects creation-time vs filename-UTC, and rotate `_shared-memory/resume-points/Sanctum/` legacy dir (none exists in this repo — placeholder for future migration).

### B.3 (R0, 20 min) — Audit + close stale OPERATOR-ACTION-QUEUE rows

The queue currently has ~30 rows spanning back to 2026-05-19. Sweep:

- Rows referencing operator-set env vars that are now set → close.
- Rows referencing scheduled-task installs where `schtasks /Query` returns OK → close.
- Rows referencing pre-shipped fixes (e.g. v1.6.85 RKOJ) → archive.
- Rows referencing operator clicks that have happened → close.

Format: each closed row gets `~~strikethrough~~ + ✅ + ts_close`.

### B.4 (R0, 15 min) — Cross-lane PROGRESS-log audit

PROGRESS-file adoption scan via `jcode-swarm-token-parity-audit-2026-05-23` showed:

- Sanctum (master): 22 bot mentions + 32 swarm mentions ← healthy
- Sinister Panel: 1 bot mention ← low
- Sinister Kernel APK: 5 bot mentions ← low
- RKOJ: 0 bot mentions ← critical (highest LOC)
- RKOJ-workstation: 0 bot mentions ← critical

Action: drop one `[INFO]` inbox message per low-adoption lane pointing at the bot-fleet quick-reference (when shipped in B.6) so the lanes' next turn picks it up.

### B.5 (R0, 15 min) — Clarify ruflo + vault MCP registration status

Grant-autonomy step 4 reports ruflo + vault NOT registered in `~/.claude/.mcp.json`, but both surfaces are functional this session (Ruflo deferred tools, vault MCP tools both visible). The shipped audit `jcode-swarm-token-parity-audit-2026-05-23` already flagged this. Concrete resolution paths:

1. **Vault MCP add** (one-liner per `tools/sinister-vault/INSTALL-MCP.md`): `claude mcp add vault -s user -- python -m sinister_vault.mcp_server`. Operator-gated (touches `~/.claude/.mcp.json`).
2. **Ruflo MCP add** (per `_shared-memory/knowledge/ruflo-mcp-integration*`): `claude mcp add ruflo -s user -- npx ruflo@latest mcp start`. Operator-gated.

Either both are added (cleaner — script step 4 then reports 3/3) or the script is updated to recognize the deferred-tool path (less clean — special-cases a doctrine reality). Recommended path: keep the script honest (it correctly reports `~/.claude/.mcp.json` contents) + add operator-gated row to action queue.

### B.6 (R1, 30 min) — Ship `bot-fleet-quick-reference.md`

The single highest-leverage open recommendation from the swarm-token-parity audit. Spec:

- Location: `_shared-memory/knowledge/bot-fleet-quick-reference.md`
- Format: 13 bots × 5 columns (slug, one-liner, common call, common-cost token estimate, when-to-use)
- Add CLAUDE.md cold-start step 7.5 pointer (or fold into step 6 brain index)
- Inject one-sentence bot-fleet hint into launcher Build-Phrase (composes with `launcher-v6.1-jcode-style-directives-2026-05-23`)

Estimated impact: 30-60% input-token reduction per Sanctum-master session for routine tasks (file search → librarian; classify → triage; URL fetch → researcher; digest → scribe; cross-project hunt → curator).

### B.7 (R2, 15 min) — Flip `jcode-feature-matrix.md` row 16 to shipped

Row 16 (Swarm-mode) currently `✅ disk + 🚧 MCP`. The audit confirmed sinister-swarm v0.1.0 pip-editable is shipped + 187 pytest-green. Flip to `✅ shipped (disk + CLI + Python API)`. R2 because matrix is operator-visible.

### B.8 (R1, 20 min) — Inbox cleanup

Per-lane inboxes accumulating. Sweep:

- `_shared-memory/inbox/sanctum/`: 1 unread [INFO] from kernel-apk (already responded-to in-spirit by current state — close)
- `_shared-memory/inbox/sanctum/peer/`: 4 messages 2026-05-21+05-23 (verify all closed)
- Per-project lane inboxes: rely on lane agents to sweep their own

Sanctum master responsibility: sweep `inbox/sanctum/` only.

### B.9 (R1, 15 min) — Context-cleaner spec draft

Operator 2026-05-23 evening verbatim: *"have a clearer that keeps the context clean but has all we need to work on projects"*. Existing `automations/context-pruner.ps1` (per CONTRACT 7) needs more aggressive surfacing-aware logic. Draft spec:

- Per-project retention policy (resume-points / progress / heartbeats)
- Automatic compaction triggers (every N turns / on resume / on switch)
- pre_warm_reads hygiene (cap to 5 most-relevant)
- Dirty-tree carry-forward rules (which files cross lanes via session-templates/projects.json)
- UX: launcher Clear-Context K option already wires to this — spec just defines the algorithm.

Output: `_shared-memory/plans/context-cleaner-spec-2026-05-23T<UTC>/spec.md`. Implementation in a follow-up turn.

### B.10 (R0, 10 min) — Knowledge graph index hygiene

Run `automations/sweep-knowledge-index.ps1` (or equivalent) to verify every `_shared-memory/knowledge/*.md` is indexed in `_INDEX.md`. The swarm audit doctrine entry mentioned `wake-on-demand-bot-dispatcher` was on-disk but un-indexed before being fixed; verify no new on-disk-orphans exist.

---

## Section C — Expand (forward-looking growth, R0-R2)

### C.1 (R2, 60 min) — `sinister-doctor` CLI

Single command running all four canonical layers (P1-P8 + grant-autonomy 9-step + inbox sweep + knowledge index hygiene) + writes a HTML health report. Composable from existing pieces. Spec lives in `forward-plan-2026-05-23T0455Z.md` section G.

### C.2 (R1, 90 min) — Per-project canonical-protections

Each project lane (Forge, Term, Panel, APK, etc.) gets a smaller P-set verifying their own canonical setup (CLAUDE.md presence + `.claude/settings.json` plugin enablement + ASF). One hook config per project. Composable from `canonical-protections-check.ps1`.

### C.3 (R2, 45 min) — L3 PreToolUse Edit guard

Block Edit/Write attempts that delete canonical lines from CLAUDE.md or settings.json. Optional opt-in via env var `SINISTER_CANONICAL_PROTECTIONS_PREWRITE_GUARD=1`. Anti-pattern docs already cover this (do-not-revert doctrine layer L3, currently "deferred to operator opt-in").

### C.4 (R1, 30 min) — Auto-restore via reference snapshot

Materialize `_shared-memory/canonical-protections-reference/<file>.canonical` from current good state + add splice-back logic to `canonical-protections-check.ps1`. Currently the auto-restore mode logs intent only. Enable with `SINISTER_CANONICAL_PROTECTIONS_AUTORESTORE=1`.

### C.5 (R1, 60 min) — Wake-on-demand bot dispatcher implementation

Doctrine shipped (`wake-on-demand-bot-dispatcher-2026-05-23.md`); implementation deferred to sinister-bus lane. Operator 2026-05-23 directive: *"have everything auto start or idle, sleep until a agent needs it then the agent can call and use anything it needs to"*. ~50 LOC patch to `sinister-bus/server.py` + per-bot `start_kit` script + `bus.health(target)` peek tool. Saves ~1.5 GB always-resident RAM across 13 bots.

### C.6 (R0, 30 min) — Cross-lane impact analysis

When a Sanctum agent commits a change touching shared files (`projects.json`, `CLAUDE.md`, settings), automatically diff vs canonical reference + post to `cross-agent/` so siblings see the change before they sync.

### C.7 (R1, 45 min) — Browser bridge Layer A probe → Layer B API

Per `browser-bridge-integration-shape-2026-05-23` (doctrine, audit, proposed). Layer A probe (`tools/sinister-browser/probe.py`) was added 2026-05-23 evening per recent commit `a4b71cf`. Next step is Layer B (`tools/sinister-browser/api.py`) pythonic wrapper class around the WebSocket action set. Operator-gated for XPI install / HKCU NativeMessagingHosts registry / FAB_AUTOLOGIN env.

### C.8 (R1, 90 min) — Memory-graph-render Stage-3 mermaid-rs-renderer integration

Per `jcode-memory-graph-visualization-pattern` brain entry. Stage-3 fastest path documented; needs verification in `tools/memory-graph-render/`. Operator-gated for Rust toolchain (mermaid-rs binary build).

### C.9 (R2, 120 min) — EVE.exe full build + dist

`automations/eve-launcher/` exists per `eve-exe-launcher-jcode-speed-parity-2026-05-23`. Needs PyInstaller --onefile build (~15-20 MB, <300 ms boot target). Sinister Start.bat already probes three paths (Desktop / build-output / LOCALAPPDATA); operator double-clicks `build-eve-exe.bat` once.

### C.10 (R0, 30 min) — Per-project bot-adoption playbook

Cross-lane completion-pattern for B.4. Document the exact "first 60 seconds" template each per-project agent should add to their cold-start: heartbeat + inbox-poll + one local-bot call (librarian or triage). Drop into `_shared-memory/knowledge/per-project-bot-adoption-playbook-2026-05-23.md`. Source of B.4's [INFO] inbox messages.

### C.11 (R1, 45 min) — Resume-point free-text search index

Launcher v6.1 already has BM25-ish free-text search across resume-points. Expand the search index to also include PROGRESS log entries + recent commit messages + brain entry tags. Single command: `automations/index-resume-search.ps1`. Result feeds the existing `Pick-ResumeRow` Score-Row scorer.

### C.12 (R2, 60 min) — Context-cleaner implementation (after B.9 spec)

After B.9 ships the spec, implement in `automations/context-pruner.ps1` v2. Composable from existing pieces.

### C.13 (R0, 30 min) — Telemetry rollup

`_shared-memory/telemetry/` (if exists) → daily/weekly rollup with token usage per lane, bot adoption rates, PROGRESS log freshness, brain-doctrine growth, P1-P8 protection-check FAIL/PASS history. Cron via `SinisterCustodian` scheduled task.

### C.14 (R1, 45 min) — Operator status dashboard (HTML)

Single static HTML at `_shared-memory/status/index.html` rolling up: P1-P8 status, lane heartbeat ages, OPERATOR-ACTION-QUEUE open-count, inbox unreads, brain doctrine count, recent ships. Refresh via SinisterCustodian. Operator double-clicks to open in browser.

---

## Section D — Operator-gated (each row has the exact one-liner)

| # | Subject | One-liner | Why gated |
|---|---|---|---|
| O1 | Restart Claude Code | Click `claude` in active window OR re-spawn via `Sinister Start.bat` | Highest-impact gate — activates the 12 junction-resolved MCPs + 14 dev plugins + SessionStart hook for every spawned EVE going forward |
| O2 | `ANTHROPIC_API_KEY` env var | `[Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY','sk-ant-...','User')` | Unblocks scribe daily-digest + curator code-scout + Sinister Chatbot LLM path |
| O3 | Add `vault` MCP via `claude mcp add vault -s user -- python -m sinister_vault.mcp_server` | One CLI line | `~/.claude/.mcp.json` is operator-owned per canonical-11 |
| O4 | Add `ruflo` MCP via `claude mcp add ruflo -s user -- npx ruflo@latest mcp start` | One CLI line | Same as O3 |
| O5 | Enable Docker Desktop auto-start | Docker Desktop → Settings → "Start Docker Desktop when you sign in" | Unlocks Tier-2 LLM bots via Ollama containers + sanctum-git Gitea |
| O6 | Pull Ollama models for Tier-2 bots | `docker exec -it ollama ollama pull qwen2.5:1.5b qwen2.5-coder:7b nomic-embed-text` | ~6 GB download; needs Docker running (O5) |
| O7 | Build EVE.exe | Double-click `D:\Sinister Sanctum\automations\eve-launcher\build-eve-exe.bat` | Boot-speed parity; bat already falls back to PS1 if EVE.exe missing — operator-optional |

---

## Section E — Sequencing + dependencies

```
Phase 0 — VERIFY (this turn, done)
  ├── Smoke-test grant-autonomy.ps1 -ReadOnly         [PASS]
  ├── canonical-protections-check.ps1                  [PASS 8/8]
  ├── Sanctum mirror Sinister Start.bat sync           [DONE]
  └── Branch cut: agent/sinister-sanctum/grant-autonomy-followup-2026-05-23

Phase 1 — IMMEDIATE COMPLETION (this turn, in-flight)
  ├── B.1 Mark items 2+3 shipped in OPERATOR-ACTION-QUEUE
  ├── B.10 Knowledge graph index hygiene (quick check)
  └── Commit + push sanctum branch + write resume-point

Phase 2 — LANE COMPLETION (next 1-3 turns, master-actionable)
  ├── B.6 Ship bot-fleet-quick-reference.md            (highest impact)
  ├── B.7 Flip jcode-feature-matrix row 16 to shipped
  ├── B.4 Cross-lane PROGRESS-log audit + [INFO] drops
  ├── B.3 OPERATOR-ACTION-QUEUE stale-row sweep
  ├── B.9 Context-cleaner spec
  └── B.5 Clarify ruflo + vault MCP status (queue + script options)

Phase 3 — EXPANSION (3-5 turns, master-actionable + some operator-gated)
  ├── C.1 sinister-doctor CLI
  ├── C.2 Per-project canonical-protections
  ├── C.10 Per-project bot-adoption playbook
  ├── C.13 Telemetry rollup
  ├── C.14 Operator status dashboard
  ├── C.5 Wake-on-demand bot dispatcher (cross-lane, sinister-bus)
  └── C.6 Cross-lane impact analysis

Phase 4 — OPERATOR-GATED UNLOCK (operator-paced)
  ├── O1 Restart Claude Code             (single highest impact)
  ├── O3 + O4 Add vault + ruflo MCPs    (compose with O1)
  └── O2 ANTHROPIC_API_KEY              (unblocks scribe/curator/chatbot)
```

Dependencies: B.6 unblocks C.10; B.9 unblocks C.12; B.5 informs O3 + O4; C.1 composes B.1-B.10 into one command; C.14 composes C.13.

---

## Section F — Reversibility ledger (R0-R4 per canonical-11)

| R | Class | Items |
|---|---|---|
| R0 | Pure read / dry-run | B.3, B.4, B.5 (audit), B.10, C.6, C.10, C.13 |
| R1 | Reversible file ops | B.1, B.2, B.6, B.8, B.9, C.2, C.4, C.7, C.8, C.11, C.14 |
| R2 | Commit-required | B.7, C.1, C.3, C.9, C.12 |
| R3 | Destructive but recoverable | (none in this plan) |
| R4 | Operator-gated wall | O1-O7 |

No R3 or R4 items in master-actionable scope. Plan is safe to execute autonomously without operator intervention.

---

## Section G — Success metrics (audit checkpoints)

After Phase 1 (this turn):
- [x] sanctum branch cut + smoke-test PASS captured
- [ ] OPERATOR-ACTION-QUEUE rows for items 2+3 marked shipped
- [ ] master plan committed + pushed

After Phase 2 (next 1-3 turns):
- [ ] `bot-fleet-quick-reference.md` exists in brain + indexed
- [ ] Per-project lanes have one [INFO] inbox message with bot-fleet pointer
- [ ] OPERATOR-ACTION-QUEUE open-row count down by ≥ 30%
- [ ] jcode-feature-matrix row 16 ✅ shipped

After Phase 3 (3-5 turns):
- [ ] `sinister-doctor` CLI exists + runs in < 10s + PASSes
- [ ] Per-project canonical-protections hook installed on ≥ 5 lanes
- [ ] `_shared-memory/status/index.html` opens + renders status pills
- [ ] Wake-on-demand dispatcher in sinister-bus saves measurable RAM

After Phase 4 (operator-gated):
- [ ] Restart Claude Code → 12 junction-MCPs resolve, 14 plugins enabled, hooks fire
- [ ] vault + ruflo MCPs visible in next session's deferred-tool list
- [ ] Scribe daily digest emits ≥ 1 entry per day after ANTHROPIC_API_KEY set

---

## Section H — Anti-patterns to avoid

1. **Don't re-ship what's already shipped.** Verify with smoke-test before "expanding" a script. Items 2 + 3 of the prior forward-plan were stale — saved 30-90 min by checking first.
2. **Don't break sibling agents' working tree.** Cut branch from current HEAD, stage ONLY sanctum-lane files, don't `git add -A`.
3. **Don't edit `~/.claude/.mcp.json` to "fix" the script.** Operator owns that file; one bad edit kills every active session. Use `claude mcp add` CLI (which the operator authorizes per-add).
4. **Don't compress the cold-start.** Anti-revert doctrine names 6 protections (now 8) that must stay. Every "streamline" should run `canonical-protections-check.ps1` post-edit.
5. **Don't auto-inject memory into spawn context.** forge-memory-bridge is pull-not-push by design. Adding a SessionStart auto-loader violates `forge-memory-usage-2026-05-23`.
6. **Don't expand without measuring.** Every C-row should have a success metric in Section G before shipping.

---

## TL;DR (close-out)

- **Operator's directive interpreted as:** complete the open completion-class items + open + sequence expansion-class items + define operator-gated unlocks + write down what done looks like.
- **What this turn ships:** Sanctum mirror sync of Sinister Start.bat + grant-autonomy smoke verification + this plan + OPERATOR-ACTION-QUEUE update + commit + push.
- **What's next (no-operator-gate):** B.6 (bot-fleet quick-ref) is the single highest-leverage next move — ~30-60% token reduction across the fleet.
- **What's gated:** O1 (restart Claude Code) remains the single biggest operator-side unlock.
- **What's safe:** every master-actionable row is R0-R2; no R3/R4 in plan; canonical protections protected by P1-P8 + SessionStart hook + anti-revert doctrine.
