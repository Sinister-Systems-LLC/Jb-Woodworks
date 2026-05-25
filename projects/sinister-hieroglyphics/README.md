# Sinister Hieroglyphics

> Author: RKOJ-ELENO :: 2026-05-25
> Status: **Phase 0 (scaffold) shipped 2026-05-25; Phase 1 (glyph syntax draft) next.**

A purpose-built, token-dense, hardware-aware programming language for the Sinister Sanctum fleet's internal tools.

## What

A new language designed from the ground up to minimize representational bytes per operation while exposing direct bindings to:

- CPU (x86_64 + ARM64 native via Cranelift / LLVM IR)
- GPU (CUDA PTX for RTX 4090 + SPIR-V for cross-vendor)
- Kernel (eBPF hooks into Sinister OS)
- Userspace (WASM for sandboxed surfaces)

Source files are `.shp` and use Unicode block U+13000 (Egyptian Hieroglyphs) for glyph identity, with full ASCII fallback so any editor works.

## Why

Sanctum's fleet agents pay context cost in tokens for every line of Python they read or write. A language where every common operation is a single 1-4 byte glyph (instead of a 20-200 byte Python call) compresses:

- Less context cost per program -> more program per token
- Smaller disk + memory footprint
- Hardware primitives without FFI overhead
- Simulation primitives (snapshot / step / branch / merge) as built-ins, replacing the desktop Python simulator with a same-language workflow

Concrete token-density target: `code.bytes_per_op <= 0.20 * python.bytes_per_op`.

## How it's trained

A base LLM (Qwen2.5-Coder 7B baseline) is fine-tuned 24/7 on the operator's RTX 4090 against a corpus the fleet builds in parallel. QLoRA on the 4090's 24 GB VRAM. Quality-monotonic loop reverts to peak adapter on regression.

GPU budget: 60% LoRA train / 15% rollout / 10% eval / 10% operator-reserved / 5% thermal slack.

## Status

| Phase | Status | What |
| --- | --- | --- |
| 0 | shipped 2026-05-25 | project scaffold + EVE.exe registration |
| 1 | next | 64-glyph syntax draft (`docs/GLYPH-SYNTAX.md`) |
| 2 | queued | Rust Pratt parser |
| 3 | queued | typed IR + type checker |
| 4 | queued | x86_64 codegen via Cranelift |
| 5 | queued | CUDA PTX backend for 4090 |
| 6 | queued | eBPF backend + Sinister OS kernel hooks |
| 7 | queued | tiny no-std runtime (<200 KB) |
| 8 | queued | simulation primitives |
| 9 | queued | LLM fine-tune corpus (continuous) |
| 10 | queued | EVE.exe integration + fleet agent rollout |

## Layout

```
projects/sinister-hieroglyphics/
  CLAUDE.md           # per-lane agent doctrine
  README.md           # this file
  PROGRESS.md         # append-only progress log
  pyproject.toml      # Python package metadata (reference impl)
  src/hgly/           # Python reference: parser shim + CLI
  docs/GLYPH-SYNTAX.md  # 64-glyph spec (Phase 1)
  corpus/             # training corpus (Phase 9 fills)
  tests/              # smoke + acceptance tests
```

## Plan

Full 10-phase plan + architecture + 4090 training schedule:

`D:\Sinister Sanctum\_shared-memory\plans\sinister-hieroglyphics-master-2026-05-25T1340Z\plan.md`

## Try it

```
python -m hgly.cli --version
# => 0.0.1
```
