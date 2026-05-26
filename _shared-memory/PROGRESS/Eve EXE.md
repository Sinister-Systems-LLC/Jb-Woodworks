# Eve EXE — PROGRESS

> Author: RKOJ-ELENO :: 2026-05-25
> Lane: `eve-exe` :: Display: **Eve EXE**
> Tier: 2 :: Default modes: swarm=on, loop=relentless

Append-only; most-recent at top.

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
