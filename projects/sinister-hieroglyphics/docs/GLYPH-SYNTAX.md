# GLYPH-SYNTAX — the 64-glyph vocabulary

> Author: RKOJ-ELENO :: 2026-05-25
> Status: **skeleton / Phase 1 work-in-progress**. Operator will iterate here.

## Goals

1. 64 glyphs covers the entire core language (every additional construct is sugar).
2. Each glyph compiles to a single Unicode codepoint (1-4 UTF-8 bytes).
3. Every glyph has an ASCII fallback so any editor works.
4. Each glyph carries a type signature constraining valid operands.
5. Each glyph declares which backends (x86 / LLVM / CUDA / eBPF / WASM) support it.

## Table of contents (Phase 1 fills the spec rows)

1. Bindings + scope (`bind`, `let`, `const`, `del`)
2. Control flow (`branch`, `loop`, `break`, `continue`, `return`)
3. Function + closure (`fn`, `call`, `tail-call`, `closure`)
4. Arithmetic + logic (`add`, `sub`, `mul`, `div`, `mod`, `and`, `or`, `not`, `xor`, `shl`, `shr`)
5. Comparison (`eq`, `ne`, `lt`, `le`, `gt`, `ge`)
6. Memory (`alloc`, `free`, `mmap`, `munmap`, `load`, `store`, `arena`)
7. Hardware IO (`syscall`, `irq`, `port-in`, `port-out`, `dma`)
8. GPU (`gpu.queue`, `gpu.dispatch`, `gpu.sync`, `gpu.copy`)
9. Concurrency (`spawn`, `await`, `parallel`, `channel.send`, `channel.recv`)
10. Events (`on-event`, `raise`, `catch`)
11. Simulation primitives (`snapshot`, `step`, `branch-sim`, `merge`, `materialize`)
12. Types + IR effects (`pure`, `io`, `kernel`, `gpu`, `linear`)

## Per-glyph spec row template (to fill in Phase 1)

| # | Glyph | Codepoint | ASCII fallback | Name | Type signature | Effect | Backends | Example |
|---|-------|-----------|----------------|------|----------------|--------|----------|---------|
| 01 | TBD | U+13xxx | `bind` | bind | `(name: ident, value: T) -> unit` | pure | all | `name := 5` |

(63 more rows to come in Phase 1.)

## Visual identity

Unicode block U+13000-U+1342F (Egyptian Hieroglyphs) is canonical. Most monospace fonts ship subsets; pairs with the project name. ASCII fallback is always accepted by the parser so older terminals stay usable.

## Pass criterion (Phase 1)

- 64 glyphs documented in the table above.
- Each row complete (codepoint + ASCII + name + type sig + effect + backends + example).
- At least 1 multi-glyph example program at the end of this file demonstrating composition.
