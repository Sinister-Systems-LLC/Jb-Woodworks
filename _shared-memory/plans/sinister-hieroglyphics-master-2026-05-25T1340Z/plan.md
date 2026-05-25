# Sinister Hieroglyphics — master plan

> Author: RKOJ-ELENO :: 2026-05-25T13:40Z
> Lane: `sinister-hieroglyphics` (new) · spawned from eve-exe master directive
> Operator (verbatim 2026-05-25 ~13:30Z): *"we may need to make our own coding language for our tools so we can make eevrything as efficent as possible within the memory frame. i need you to create and add to a plan on how we can do this and how we can train it 24/7 with my 4090. i want the most efficet codfing language you can. i want this to be its own project in eve exe called Sinister Hieroglyphics. take note that we want to use our lanmguage to direct connect to the hardware, our OS and build hyper realistic simulations like th python simulator on the desktop"*

## Vision

A purpose-built, token-dense, hardware-aware programming language that:
1. **Minimizes representational bytes** — every common Sanctum operation compresses to a single glyph (1-4 byte UTF-8 codepoint) instead of a 20-200 byte function call. Result: lower context cost when agents write/read code; lower disk + memory; more program per token.
2. **Compiles direct to native** — emits x86_64 + ARM64 machine code (or LLVM IR for retargets) with optional eBPF / SPIR-V / CUDA PTX backends so the same source targets CPU, GPU, kernel, and OS-userspace.
3. **First-class hardware primitives** — types and ops for: memory pages, IRQs, device IO, GPU command queues, kernel syscalls. No FFI wrapper layer — direct binding.
4. **Pluggable into Sinister OS** — every OS service (vault, mesh, link, panel) authors in Hieroglyphics; the OS kernel itself eventually targets Hieroglyphics.
5. **Simulation-native** — built-in primitives for state-snapshot, time-step, parallel-trajectory, materialization. Replaces the desktop python simulator with a same-language workflow.
6. **Trainable** — a base LLM (Qwen2.5-Coder 7B or similar) is fine-tuned 24/7 on the operator's 4090 against a Hieroglyphics corpus the fleet builds in parallel. The fine-tuned model writes Hieroglyphics natively without translation overhead.

## Token-density goal

Concrete target: `code.bytes_per_op <= 0.20 * python.bytes_per_op` averaged over a 1000-program corpus. Means EVE-class programs (~200 KB of Python) compress to ~40 KB of Hieroglyphics source.

## Architecture (5 layers)

```
┌─────────────────────────────────────────────────────────┐
│  L5  Sinister Hieroglyphics fine-tuned LLM (4090 home)  │  ← agents write here
├─────────────────────────────────────────────────────────┤
│  L4  Source: glyph corpus (.shp files, UTF-8 dense)     │
├─────────────────────────────────────────────────────────┤
│  L3  Parser → AST → typed IR (Pratt parser, Rust)       │
├─────────────────────────────────────────────────────────┤
│  L2  Codegen backends:                                  │
│        a. x86_64 native (Cranelift)                     │
│        b. LLVM IR (for ARM64, RISCV, retargets)         │
│        c. CUDA PTX (for 4090 GPU kernels)               │
│        d. eBPF (for Sinister OS kernel hooks)           │
│        e. WASM (for browser / sandboxed surfaces)       │
├─────────────────────────────────────────────────────────┤
│  L1  Runtime: tiny (no-std, <200 KB) — owns scheduler,  │
│      hardware IO syscalls, GC-free arenas               │
└─────────────────────────────────────────────────────────┘
```

## Phase plan (10 phases)

### Phase 0 — project scaffold (this iter)
- Create `projects/sinister-hieroglyphics/` with CLAUDE.md + README.md + src/ + corpus/ + docs/.
- Register in `projects.json` so EVE.exe picker shows the lane.
- Heartbeat skeleton.
- **Pass criterion:** lane visible in EVE.exe; `git status` clean after commit.

### Phase 1 — glyph syntax draft (1-2 iters)
- Author `docs/GLYPH-SYNTAX.md` defining the initial 64-glyph vocabulary. Each glyph maps to: name, semantic op, type signature, ASCII fallback, target backends. Starting set covers: bind, call, branch, loop, alloc, free, syscall, mmap, send, recv, on-event, raise, parallel, await.
- Use Unicode block U+13000 (Egyptian Hieroglyphs) for visual identity — pun lands AND most monospace fonts ship subsets. ASCII fallback (e.g. `bind` = `𓂀` or `:=`) so every editor still works.
- **Pass criterion:** 64 glyphs documented, each with ASCII fallback + type sig + at least 1 example.

### Phase 2 — Pratt parser in Rust (1 iter)
- `crates/hgly-parser/` — tokenizer + Pratt parser → AST. Use `nom` or hand-written for tightness. Target: parse 10k lines/sec on CPU baseline.
- **Pass criterion:** parser round-trips a 500-line `.shp` test corpus byte-for-byte (parse → print → diff = 0).

### Phase 3 — typed IR + type checker (2 iters)
- `crates/hgly-ir/` — typed SSA IR with effect annotations (pure / io / kernel / gpu).
- Type system: row-polymorphic structural typing + linear types for hardware resources (a `gpu.queue` cannot be aliased).
- **Pass criterion:** hgly-ir passes 95% of a 200-program type test suite.

### Phase 4 — x86_64 codegen via Cranelift (2 iters)
- `crates/hgly-codegen-x86/` — IR → Cranelift IR → native machine code.
- Output: standalone `.exe` or `.o` for static linking.
- **Pass criterion:** 50 sample programs (fizzbuzz, hashmap, file IO, threading, syscall) compile + run + produce identical output to Python references.

### Phase 5 — CUDA PTX backend for 4090 (2 iters)
- `crates/hgly-codegen-cuda/` — IR ops marked `effect=gpu` lower to CUDA PTX kernels.
- Hello-world: parallel matrix mul on RTX 4090 from a `.shp` source file.
- **Pass criterion:** matmul 4096x4096 fp16 hits >70 TFLOPS on RTX 4090 (vs ~83 peak theoretical = ~85%).

### Phase 6 — eBPF backend + kernel hooks (1-2 iters)
- `crates/hgly-codegen-ebpf/` — IR ops with `effect=kernel` lower to eBPF bytecode loadable into Sinister OS or Linux kernel.
- Use case: a Hieroglyphics-authored Sinister Vault sync hook running inside kernel netfilter.

### Phase 7 — runtime + scheduler (1-2 iters)
- `crates/hgly-rt/` — tiny no-std runtime, arena allocator, M:N scheduler, IO queue (io_uring on Linux, IOCP on Windows).
- Cap: 200 KB stripped on Linux x86_64.

### Phase 8 — simulation primitives (2 iters)
- `crates/hgly-sim/` — built-in `snapshot`, `step`, `branch`, `merge` ops for hyperrealistic simulation.
- Reference example: port the desktop python simulator (`C:\Users\Zonia\Desktop\python_simulator_*`) to Hieroglyphics; benchmark token-density + perf delta.

### Phase 9 — LLM fine-tune corpus (continuous; gated by Phase 1-3)
- Base model: Qwen2.5-Coder 7B (Apache 2.0; fits in 4090's 24 GB VRAM with QLoRA).
- Corpus sources:
  - Auto-translate the entire Sanctum Python codebase (`automations/*.py`, `tools/*.py`, project src) to Hieroglyphics via a Phase 4-built translator.
  - Author 5000+ short example programs (the fleet writes them as training data in spare loop cycles).
  - Negative corpus: malformed glyphs → expected parser errors.
- Training cadence: 24/7 LoRA fine-tune on 4090, checkpoint every hour, evaluate against held-out test set each epoch. The quality-monotonic-loop + checkpoint manager (already shipped) drives this loop.
- **Pass criterion:** fine-tuned model writes valid Hieroglyphics at >85% syntactic correctness on the held-out test (vs ~5% baseline for unmodified Qwen2.5).

### Phase 10 — EVE.exe integration + agent rollout
- New EVE.exe page: `H) Hieroglyphics` showing live training metrics, corpus size, model version, recent compiles.
- Every fleet agent gets an opt-in `WRITES_HIEROGLYPHICS=on` flag; when set, the agent emits `.shp` files for new tool authoring instead of `.py`.
- **Pass criterion:** at least 3 fleet tools written end-to-end in Hieroglyphics (e.g. `forever-improve`, `mesh-coordinator`, `agent-poke`).

## 24/7 4090 training plan

```
RTX 4090 utilization budget (operator-reserved floor: 10% for the operator's own usage):
┌─────────────────────────────┬────────┐
│ LoRA fine-tune (Qwen-Coder) │  60%   │  ← Hieroglyphics codegen + parse training
│ Corpus generation rollouts  │  15%   │  ← Sample programs from current checkpoint
│ Evaluation suite            │  10%   │  ← Held-out test runs every 60min
│ Reserved (operator)         │  10%   │  ← Operator's own workloads
│ Cooling / thermal slack     │   5%   │  ← Throttle if GPU > 78C
└─────────────────────────────┴────────┘
```

- Scheduler: `automations/hgly_trainer.py` (new) — Python wrapper around `unsloth` + `peft`. Resumes from latest LoRA adapter on launch. Writes per-epoch metrics to `_shared-memory/hgly-training-log.jsonl`.
- Quality monotonic: each checkpoint scored on the held-out test; checkpoint manager (already shipped: `automations/loop_checkpoint.py`) reverts to peak adapter if eval regresses.

## Composition with already-shipped pieces

- `automations/loop_checkpoint.py` (shipped this session) — drives the quality-monotonic training loop with revert-to-peak.
- `automations/quality-monotonic-loop.ps1` (patched this session) — runs the eval cycle and triggers revert on regression.
- `automations/sinister_swarm.py` (to ship via parallel lane after rate-limit reset) — orchestrates parallel corpus generation across N rollout agents.

## Stop / abort conditions

- 3 consecutive eval regressions even after checkpoint revert → freeze training, surface to operator.
- VRAM OOM 3x in a row → drop LoRA rank by 8 and retry.
- Operator types `/loop stop hgly` or sets `HGLY_TRAINING=off` → graceful shutdown after current epoch.

## Open questions (operator decisions, surfaced once)

1. Visual identity: do we ship as `𓂀.shp` files (Unicode Egyptian Hieroglyphs U+13000) or ASCII-only `bind x := 5` style? Recommend BOTH (parser accepts both, glyph form is canonical).
2. License: MIT to match Sanctum monorepo? (recommend yes)
3. Train base model on local 4090 OR rent H100 for first big run then switch to 4090 for incremental? (recommend: bootstrap on 4090 to keep it 100% on-machine per operator's "use my 4090" mandate; H100 only if eval stalls below 50% syntactic correctness after 50 epochs)
