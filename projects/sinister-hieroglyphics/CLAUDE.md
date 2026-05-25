# CLAUDE.md — Sinister Hieroglyphics

**Author:** RKOJ-ELENO :: 2026-05-25

Per-lane CLAUDE.md for the `sinister-hieroglyphics` project. Inherits sanctum-wide doctrine from `D:\Sinister Sanctum\CLAUDE.md`. This lane designs and builds a purpose-built, token-dense, hardware-aware programming language for the Sanctum fleet's internal tools.

## Lane scope

- **Tag:** Token-dense hardware-aware programming language; direct hardware + Sinister OS binding; simulation-native; trained 24/7 on the operator's RTX 4090.
- **Tier:** T2 (lane authority over fleet-internal language design; consumed by tool-author lanes once Phase 4+ ships).
- **Sibling lanes:** `sinister-os` (kernel/userspace consumer), `sinister-memory` (corpus storage), `sinister-overseer` (training loop watcher), `sinister-looper` (quality-monotonic eval), every future tool-author lane.

## Charter (operator verbatim 2026-05-25 ~13:30Z)

> "we may need to make our own coding language for our tools so we can make eevrything as efficent as possible within the memory frame. i need you to create and add to a plan on how we can do this and how we can train it 24/7 with my 4090. i want the most efficet codfing language you can. i want this to be its own project in eve exe called Sinister Hieroglyphics. take note that we want to use our lanmguage to direct connect to the hardware, our OS and build hyper realistic simulations like th python simulator on the desktop"

## Master plan

Full 10-phase plan + 5-layer architecture + 24/7 4090 training budget + token-density target (<=20% of Python bytes/op) live at:

`D:\Sinister Sanctum\_shared-memory\plans\sinister-hieroglyphics-master-2026-05-25T1340Z\plan.md`

Phase 0 (this scaffold) shipped 2026-05-25. Phase 1 (64-glyph syntax draft) is next.

## Lane defaults

- **Display name:** `Sinister Hieroglyphics`
- **Branch prefix:** `agent/sinister-hieroglyphics/`
- **Tier:** 2
- **GitHub remote:** `Sinister-Sanctum` (internal monorepo per single-repo-push-policy-2026-05-25; NOT a carve-out repo).
- **Accent:** TBD (default Sanctum purple until visual identity locks in Phase 1).
- **Default modes:** `loop=relentless`, `swarm=on` (per loop-swarm-default-on-doctrine-2026-05-25).

## Public surface (Phase 0)

- `src/hgly/` — Python reference implementation skeleton. `python -m hgly.cli --version` should print the package version.
- `docs/GLYPH-SYNTAX.md` — the 64-glyph vocabulary spec (Phase 1 fills this in).
- `corpus/` — training corpus storage (gitkeep for now; Phase 9 fills it).
- `tests/test_smoke.py` — import + version smoke test.
- `pyproject.toml` — minimal package metadata.

The Rust crates (`hgly-parser`, `hgly-ir`, `hgly-codegen-*`, `hgly-rt`, `hgly-sim`) land in Phase 2+; structure preserved for future expansion.

## Lane-specific rules

1. **Token-density is the prime directive.** Every glyph addition is justified against `code.bytes_per_op <= 0.20 * python.bytes_per_op`. Phase 1 records the per-glyph compression budget.
2. **Hardware primitives are first-class.** No FFI wrapper layer between glyphs and `mmap` / IRQ / GPU command queue / kernel syscall.
3. **Backends are pluggable.** x86_64 (Cranelift) is reference; LLVM IR + CUDA PTX + eBPF + WASM are siblings, not afterthoughts.
4. **Linear types for hardware resources.** `gpu.queue`, `fd`, `mmap.region` cannot be aliased; type checker enforces.
5. **Quality-monotonic training.** Every fine-tune checkpoint scored on held-out test; checkpoint manager reverts to peak adapter on regression (composes with `automations/loop_checkpoint.py` + `quality-monotonic-loop.ps1`).
6. **No half-ass.** New surface (parser / codegen backend / runtime feature) ships with: spec row in `GLYPH-SYNTAX.md` + at least 1 example program + 1 acceptance test + PROGRESS row OR it is not claimed shipped.
7. **No operator clicks.** Training kicks off / pauses / resumes via `automations/hgly_trainer.py`; operator never `pip install`s manually.

## Authorship

Every new `.py`/`.md`/`.rs`/`.shp`/`.toml` in this lane carries `Author: RKOJ-ELENO :: <date>`.

## Doctrine references

- `_shared-memory/knowledge/no-bullshit-tested-before-claimed-doctrine-2026-05-23.md`
- `_shared-memory/knowledge/loop-relentless-pursuit-doctrine-2026-05-25.md`
- `_shared-memory/knowledge/loop-swarm-default-on-doctrine-2026-05-25.md`
- `_shared-memory/knowledge/single-repo-push-policy-2026-05-25.md`
- `_shared-memory/knowledge/sanctum-scope-discipline-2026-05-24.md`
- `_shared-memory/knowledge/full-relentless-swarm-fanout-mindset-doctrine-2026-05-25.md`
