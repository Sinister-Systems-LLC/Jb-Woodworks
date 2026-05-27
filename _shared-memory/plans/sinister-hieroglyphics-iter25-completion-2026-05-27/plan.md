# Plan — Sinister Hieroglyphics iter-25 -> completion

> Author: RKOJ-ELENO :: 2026-05-27 (kernel-apk lane spawn worked on the
> hieroglyphics lane per the active branch + cwd CLAUDE.md)
> Triggered by operator directive (verbatim 2026-05-26T20:??Z): *"retry
> the cherry-pick now and create a plan to complete everything i said
> to do"*

## Verified ground-truth at plan-write time

| commit | branch | what shipped |
|---|---|---|
| eb06c90 | agent/sinister-hieroglyphics/iter24-token-density-measure-2026-05-26 | iter-24 token-density measurement tool + 7 acceptance tests |
| 64c1a65 | agent/sinister-hieroglyphics/iter24-token-density-measure-2026-05-26 | iter-25 `track` subcommand + JSONL trajectory + 9 acceptance tests (re-cherry-pick from polluted 65f1cda) |

Both pushed to origin. Hieroglyphics lane now has a continuously
observable token-density ratio = **0.9389** (corpus-wide, 255
programs). Goal = 0.20. Distance to goal = 0.74 ratio units.

## Why corpus expansion is the long pole

The bootstrap corpus (255 programs · mean 76 B · median 68 B) is
fundamentally too small to amortize the 3-4-byte UTF-8 cost of glyph
codepoints. Per-glyph compression vs Python only pays off when the
program has enough Python boilerplate (imports, `def`, `__main__`
guards) to compress against. Empirically (test_density.py
`t_passing_shrinks_with_glyph_overhead`):

- ASCII fallback ratio on 20-byte program: 1.16
- Glyph form on same program: 1.38

The path to 0.20 is NOT smaller glyphs; it's bigger Python boilerplate
to amortize against. That means: multi-hundred-line corpus programs
across the memory + concurrency + simulation categories.

## Phase order (this plan)

| # | Phase | Acceptance | Effort | Ratio impact |
|---|---|---|---|---|
| **iter-26** | Wire `hgly_density track` into `loop_checkpoint.py` post-iter hook | Trajectory JSONL grows by 1 row per `loop_checkpoint` close; sample read+chart matches | S | none direct; enables monotonic guard |
| **iter-27** | Add `_tpl_big_*` templates (5 templates × 50-150 LOC each) covering memory + concurrency + simulation + matrix + io | New corpus dir `_shared-memory/hgly-corpus/big-2026-05-27/` ≥ 50 programs; each parses clean (`test_parser` extension) | M | direct; expect ratio drop to ~0.5-0.7 |
| **iter-28** | Re-`track`; commit second JSONL row; chart ratio trajectory iter-25 -> iter-27 | Two JSONL rows; delta documented in PROGRESS row | S | observation only |
| **iter-29** | Add `--by-category` flag to `hgly_density.py corpus` so the chart can show which category compresses best | New JSON shape: `{categories: {memory: {ratio: ..., count: ...}, ...}}`; test asserts schema | S | none; observability boost |
| **iter-30** | Phase 9 (master plan) corpus seeder + fanout — port `_tpl_big_*` into `hgly_corpus_seed.py` so multiple sub-agents can each ship 100-LOC programs in parallel | Single `sinister_swarm.py fanout` call produces 5+ slice results that all parse | L | direct; ratio target < 0.4 |
| **iter-31** | Phase 9.6: trainer-input projection — the LoRA trainer at `automations/hgly_trainer.py` reads from the corpus + the trajectory JSONL as its eval signal | Trainer dry-run emits `eval_loss` + `density_ratio` per epoch | M | sets up monotonic loop |
| **iter-32** | Phase 9.7: monotonic-revert hook — if `density_ratio` regresses by > 0.05 across two iters, `loop_checkpoint.py` reverts to prior peak adapter | Test injects synthetic regression and asserts revert | M | safety net for trainer loop |
| **iter-33+** | Phase 10 master-plan items resume (PTX codegen polish, sim-bridge resilience) — orthogonal to ratio chase | per master plan | L | none |

## iter-26 — wire-up details

**File:** `automations/loop_checkpoint.py`
**Hook point:** end-of-iter checkpoint write (the existing
`commits=0 AND progress=0 skip` site per `iter-31 looper skips ckpt`)
**Insertion:** after the heartbeat-write step, conditional on
`slug == "sinister-hieroglyphics"` (so the hook only fires on this
lane and doesn't pollute other lanes' checkpoint passes).

Pseudo:
```python
if slug in {"sinister-hieroglyphics", "Sinister Hieroglyphics"}:
    try:
        from subprocess import run
        run([sys.executable,
             str(SANCTUM / "automations" / "hgly_density.py"),
             "track", "--note", f"loop-checkpoint iter-{iter_num}"],
            check=False, timeout=30)
    except Exception:
        pass  # checkpoint never blocks on side-effects
```

**Acceptance test (new):** `tests/test_loop_checkpoint_hgly.py` —
exercises the hook in dry-run mode (`SINISTER_HGLY_TRACK_DRY_RUN=1`)
and asserts the JSONL would have grown by exactly 1 row.

## iter-27 — `_tpl_big_*` templates

Five new templates in `automations/hgly_corpus_seed.py` (~50-150 LOC
each). Each must parse cleanly via `hgly.parser.parse(src)`. Names + scope:

1. `_tpl_big_memory_pool` — alloc 4kB pool, partition into 4 1kB
   slabs via `mmap`, walk each slab with `addr-of` + `deref`, free
   atomically via `munmap`. Glyphs: 12-15 from cat-4.
2. `_tpl_big_concurrent_counter` — N threads via `spawn`, atomic
   CAS on shared counter, mutex-protected slow path, fence + await.
   Glyphs: 10-12 from cat-5.
3. `_tpl_big_sim_pipeline` — full Phase 8 sim: `snapshot` -> `step`
   loop × 50 -> `branch-sim` × 4 -> `merge` -> `materialize`.
   Glyphs: 8 from cat-8 used multiple times.
4. `_tpl_big_matrix_multiply` — N×N matmul via lists + `for` + `bind`.
   Pure cat-1/2/3, no cat-4+ glyphs. Establishes that ratio works
   without exotic hardware glyphs too.
5. `_tpl_big_io_pump` — open socket, `recv` loop until EOF, write
   each chunk to a file, close both. Glyphs from cat-7.

Each template's `python_ref` field is the AUTHENTIC equivalent Python
(not stub), because that's what the ratio is measuring against.

## Doctrine to write after iter-26 ships

`_shared-memory/knowledge/cross-agent-git-race-lock-doctrine-2026-05-27.md`
documenting: the rmux + eve-exe + hieroglyphics branch-surf race that
caused commit `65f1cda` to land on wrong branch with pollution, and
the recovery via `--no-commit` cherry-pick + selective unstage.
Composes with `one-terminal-per-project-no-overlap-doctrine-2026-05-25`
+ `stale-git-lock-auto-cleanup-doctrine-2026-05-26`. Includes the
clean-stale-git-locks.py + `git ls-files <path>` discovery pattern.

## Test invariants (must remain green every iter)

- `python projects/sinister-hieroglyphics/tests/test_smoke.py` — OK <ver>
- `python projects/sinister-hieroglyphics/tests/test_parser.py` — 11/11
- `python projects/sinister-hieroglyphics/tests/test_ir.py` — 10/10
- `python projects/sinister-hieroglyphics/tests/test_density.py` — N/N (grows each iter)
- `python automations/hgly_density.py corpus` — exit 0 + valid ratio
- `python automations/hgly_density.py track --dry-run` — exit 0 + schema

## Commit discipline

Every iter:
1. Mesh-check `automations/hgly_*.py` + `projects/sinister-hieroglyphics/**/*.py` paths.
2. Stage ONLY hgly + density + corpus paths (NEVER `git add -A`).
3. Test before commit (NOT after).
4. Detailed commit format (Shipped/Smoke/Refs) per `frequent-detailed-commits-per-agent-2026-05-25`.
5. Push via `git push origin HEAD:agent/sinister-hieroglyphics/iter24-token-density-measure-2026-05-26`
   (NOT `sanctum-auto-push.ps1` — that script branch-surfs and causes the race).

## Loop-stop condition (binding for this work-unit)

This plan is complete when:
- Phases 26-30 are all shipped + verified
- Corpus-wide ratio is < 0.40 (50% reduction from 0.9389 baseline) OR
  the honest "ratio is asymptotic above 0.5 for this language design"
  conclusion is documented with measurements
- Trajectory JSONL has ≥ 5 rows showing monotonic improvement (with
  any regression auto-reverted)
- iter-31 trainer-input projection is live

## Risk register

| Risk | Mitigation |
|---|---|
| Cross-agent branch race steals the working tree mid-commit | Always `git ls-files <path>` before `git add`; commit with explicit file list; `git push HEAD:<branch>` never `git push <branch>` |
| `loop_checkpoint.py` hook adds 50ms per kernel close | Hook is `check=False, timeout=30`, fire-and-forget |
| Big templates fail to parse (parser edge cases) | iter-27 acceptance gate: parser pass before measurement |
| Ratio gets stuck because the design fundamentally over-encodes | Document honestly; the language is still valuable for trainer corpus; consider category-8 (sim) glyph compression as a separate Phase 11+ |
