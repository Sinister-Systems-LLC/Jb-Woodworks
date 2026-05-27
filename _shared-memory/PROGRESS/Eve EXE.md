# Eve EXE — PROGRESS

> Author: RKOJ-ELENO :: 2026-05-25
> Lane: `eve-exe` :: Display: **Eve EXE**
> Tier: 2 :: Default modes: swarm=on, loop=relentless

Append-only; most-recent at top.

---

## 2026-05-26T23:50Z — iter-8 HIVE partition audit (genesis-architect + petals) SHIPPED

Branch: `agent/eve-exe/hive-genesis-petals-audit-2026-05-26`. Operator directive via inbox 22:47Z from sanctum: eve-exe lane owns audit of `genesis-architect-main` + `petals-main` (no overlap with sanctum/memory/term/os lanes).

- **Swarm fan-out:** 2 parallel `Explore` sub-agents (one per repo, very-thorough). All claims cited FILE:LINE.
- **genesis-architect-main verdict:** research-first lifecycle scaffolding skill (not a TUI). 5 portable patterns: G1 phase-state checkpoint+resume, G2 env-probe→cached-JSON, G3 hard-gate A/B/C/D menu, G4 vault-first knowledge lookup, G5 evidence-pack+mitigation-enforcer.
- **petals-main verdict:** distributed-inference engine with `configargparse` multi-mode CLI (no TUI; external monitor lives at health.petals.dev). 5 portable patterns: P1 multi-mode CLI+YAML-fallback, P2 throughput calibration+ETA UX, P3 ServerState 3-state enum+daemon announcer, P4 humanfriendly multiaddr/IP shortcuts, P5 humanfriendly units+quant presets.
- **Top-5 ranked for next-iter port:** P3 fleet-state.json (unifies heartbeats + Sinister Panel `/fleet`), G3 A/B/C/D menus (eve.py picker), P1 multi-mode CLI+YAML (collapses `.bat`), G2 env-probe (replaces brittle PS env-detect), P2 throughput calibration (spawn ETA UX). 5 deferred until concretely needed (G4/G5/P4/P5/G1).
- **Anti-overlap call-outs:** flagged but did NOT claim — sanctum (jcode/hivemind/orchestration), os (petals-infra DHT/libp2p), memory (model arch / vault internals route to memory for verdict), term (CALM/tessera).
- **Shipped artifacts:** brain entry `_shared-memory/knowledge/hive-eve-exe-genesis-petals-audit-2026-05-26.md` + `_INDEX.md` row + inbox msg moved to `_acked/` + heartbeat updated to iter-8.
- **Status:** `triage-shipped, no-code-this-iter, 10-port-candidates-ranked` (per `no-bullshit-tested-before-claimed` rule 8 — no port claimed shipped without smoke-test).

Composes with: `we-have-the-source-read-it-doctrine-2026-05-25` (read source, no RE), `full-relentless-swarm-fanout-mindset-doctrine-2026-05-25` (2 parallel Explore agents), `sanctum-scope-discipline-doctrine-2026-05-24` (anti-overlap flagged, not claimed).

---

## 2026-05-26T20:45Z — iter-7 R9 train-loop dedup SHIPPED (smoke-tested)

Branch: `agent/eve-compliance/train-loop-dedup-2026-05-26`. Single-file change to `automations/eve_compliance_train_loop.py`:

- Added `_stable_signature()` — ignores volatile keys (ts_utc / cycle / duration_sec / raw_lines / stderr_tail / coalesce-bookkeeping).
- Added `_read_last_jsonl_row()` + `_coalesce_into()` helpers.
- Rewrote `write_metrics()` — if the new row's stable signature matches the file's last row, in-place coalesce (bump `repeat_count`, update `last_ts_utc` / `last_cycle` / `last_duration_sec` / `last_raw_lines`); else append.
- Added `compact_existing_metrics()` + `--compact-existing` CLI flag — retroactive dedup with `.pre-dedup-bak` sibling backup.

Ran on the live file: **128 rows → 3 rows (-125)**. Backup `eve-training-loop.jsonl.pre-dedup-bak` (38 KB, 128 lines) preserved. The 3 surviving rows are: (a) baseline coalesced 126x (precision 0.83, training_jsonl=38, first 2026-05-25T13:06Z, last 2026-05-26T20:09Z), (b) single training-row bump (39 lines), (c) precision drop to 0.71 — exactly the signal that was buried in noise.

Smoke: 3-assertion in-process test PASS (stable_signature, write_metrics coalesce, compact_existing 6→2).

Daemon: schtask `SinisterEveComplianceTrainLoop` is `Ready` (not running). Next scheduled fire picks up new code automatically — no restart needed.

Stopping point — operator signaled "many things queued, let me know when you stop".

---

## 2026-05-25T15:13Z — iter-6 fan-out (3 parallel sub-agents)

Dispatched after iter-5 (`aa65335` clamp claude-usage-meter) unblocked the spawn signal.

- **A** (`a23fad992edb80378`): Hieroglyphics Phase 2 Python Pratt parser bootstrap — lexer + ast + parser + tests under `projects/sinister-hieroglyphics/src/hgly/`.
- **B** (`abb5e22cf79854705`): Auto-spawn `sinister-designer` + `sinister-hieroglyphics` agents now that 999% signal is fixed; verify heartbeats refresh; OPERATOR-ACTION-QUEUE row on fail.
- **C** (`ab58d145fa588026b`): `automations/hgly_corpus_seed.py` + bootstrap 20-program corpus at `_shared-memory/hgly-corpus/bootstrap-2026-05-25/` for the 4090 trainer.

Self-paced loop continues; next wakeup at ~15:38Z.

---

## 2026-05-25T13:15Z–15:10Z — iter-1 through iter-5 (7 commits pushed)

| Commit | What |
|---|---|
| `f5e3caa` | iter-1: Q quick-launch + claude-icon (`make-claude-icon.py`) + sub-page centering + start-sinister-session mintty icon bug fix |
| `a00a9c7` | iter-2: shimmering sub-page header/footer separators (Image #66 more animations) |
| `d38c13d` | iter-3: headless subprocess monkey-patch (no more powershell popup windows) |
| `5ac7bf8` | iter-4: first-run wizard regression fix (eve.py:619 soft-warns no longer fire wizard) + `loop_checkpoint.py` (verified revert-to-peak) + `quality-monotonic-loop.ps1` checkpoint params + Sinister Hieroglyphics 10-phase plan |
| `fcb78a4` | jcode swarm port: `automations/sinister_swarm.py` (`try_join_all` analogue) |
| `e22f14c` | Hieroglyphics Phase 0 scaffold + projects.json v14 |
| `649eb91` | Hieroglyphics Phase 1: 64-glyph syntax + fizzbuzz density measurement |
| `1ce74df` | `automations/hgly_trainer.py` (786 LOC, 6 subcommands) — 4090 LoRA trainer scaffold |
| `6db3a14` | sinister-designer BRAND-BRIEF.md (10 UI surfaces, top-3 queue) |
| `aa65335` | iter-5: clamp `claude-usage-meter` pct at 100 (was 999) — unblocks slot-health + spawn |

Verified this session: Spawn Sanctum Agent.bat 100% working (6/6 checks pass), first-run wizard fires only on hard-blocks, loop checkpoint manager round-trips a planted regression, EVE.exe v0.4.5 banner renders without wizard popup.
