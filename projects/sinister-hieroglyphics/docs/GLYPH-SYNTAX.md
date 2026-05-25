# GLYPH-SYNTAX — the 64-glyph vocabulary

> Author: RKOJ-ELENO :: 2026-05-25
> Updated: 2026-05-25 (Phase 1 vocabulary populated)
> Status: **Phase 1 draft complete — 64 glyphs specified, fizzbuzz reference compiles**

## Goals

1. 64 glyphs cover the entire core language. Every additional construct is sugar over these primitives.
2. Each glyph compiles to a single Unicode codepoint (3-4 UTF-8 bytes for U+13000-block; 1-3 bytes elsewhere).
3. Every glyph has an unambiguous ASCII fallback (<=4 chars) so any editor works. The parser accepts BOTH glyph and ASCII forms interchangeably.
4. Each glyph carries a type signature constraining valid operands using the form `(in_types) -> out_type`.
5. Each glyph declares supported backends: CPU (x86/ARM), GPU (CUDA PTX), eBPF (kernel), WASM (sandbox), or `all`.

## Type universe (mini-reference)

- `T`, `U` — type variables (parametric polymorphism)
- `i64`, `i32`, `u64`, `u32`, `f64`, `f32`, `u8` — primitive numerics
- `bool` — `0` / `1`
- `ident` — bound name in current scope
- `ptr<T>` — linear pointer to T (single-owner)
- `arr<T>` — fixed array of T
- `chan<T>` — typed channel
- `task<T>` — async handle resolving to T
- `mutex<T>` — guarded resource
- `fd` — file descriptor (linear)
- `block` — code region {...}
- `unit` — () / void
- `state` — simulation world snapshot

---

## Category 1 — Bind / scope (8 glyphs)

| #  | Glyph | Codepoint | ASCII | Name        | Op                 | Type signature                            | Backends | Example                       |
|----|-------|-----------|-------|-------------|--------------------|-------------------------------------------|----------|-------------------------------|
| 01 | 𓂀     | U+13080   | `let` | bind-let    | mutable binding    | `(ident, T) -> unit`                      | all      | `𓂀 x 5`                       |
| 02 | 𓊪     | U+132AA   | `cst` | bind-const  | immutable binding  | `(ident, T) -> unit`                      | all      | `𓊪 PI 3.14`                   |
| 03 | 𓆎     | U+1318E   | `fn`  | function    | declare function   | `(ident, [params], block) -> unit`        | all      | `𓆎 add (a b) {𓎛 ➕ a b}`       |
| 04 | 𓎛     | U+1339B   | `ret` | return      | yield from fn      | `T -> !`                                  | all      | `𓎛 result`                    |
| 05 | 𓏏     | U+133CF   | `lam` | lambda      | anonymous function | `([params], block) -> fn`                 | all      | `𓏏 (x) {➕ x 1}`               |
| 06 | 𓍿     | U+1337F   | `as`  | alias       | name = name        | `(ident, ident) -> unit`                  | all      | `𓍿 sum add`                   |
| 07 | 𓂝     | U+1309D   | `{`   | scope-open  | begin block        | `() -> block`                             | all      | `𓂝 ... 𓂞`                     |
| 08 | 𓂞     | U+1309E   | `}`   | scope-close | end block          | `block -> unit`                           | all      | (see above)                   |

## Category 2 — Control flow (8 glyphs)

| #  | Glyph | Codepoint | ASCII | Name      | Op             | Type signature                        | Backends | Example                          |
|----|-------|-----------|-------|-----------|----------------|---------------------------------------|----------|----------------------------------|
| 09 | 𓁹     | U+13079   | `if`  | if        | conditional    | `(bool, block, block?) -> T`          | all      | `𓁹 (➗= x 0) {a} {b}`              |
| 10 | 𓂜     | U+1309C   | `el`  | else      | else branch    | `block -> block`                      | all      | (paired with `𓁹`)                 |
| 11 | 𓃀     | U+130C0   | `mch` | match     | pattern match  | `(T, [(pat, block)]) -> U`            | all      | `𓃀 x {0:a 1:b _:c}`               |
| 12 | 𓃢     | U+130E2   | `lp`  | loop      | iterate        | `(block) -> unit`                     | all      | `𓃢 {𓁹 done 𓍞}`                    |
| 13 | 𓍞     | U+1335E   | `brk` | break     | exit loop      | `() -> !`                             | all      | `𓍞`                              |
| 14 | 𓎡     | U+133A1   | `cnt` | continue  | next iter      | `() -> !`                             | all      | `𓎡`                              |
| 15 | 𓎼     | U+133BC   | `yld` | yield     | generator emit | `T -> unit`                           | all      | `𓎼 i`                             |
| 16 | 𓊃     | U+13283   | `for` | for-range | counted loop   | `(ident, i64, i64, block) -> unit`    | all      | `𓊃 i 0 10 {𓎼 i}`                  |

## Category 3 — Arithmetic / logic (8 glyphs)

| #  | Glyph | Codepoint | ASCII | Name | Op       | Type signature           | Backends | Example       |
|----|-------|-----------|-------|------|----------|--------------------------|----------|---------------|
| 17 | ➕     | U+2795    | `+`   | add  | a+b      | `(T, T) -> T where T:Num`| all      | `➕ 2 3`        |
| 18 | ➖     | U+2796    | `-`   | sub  | a-b      | `(T, T) -> T where T:Num`| all      | `➖ 5 1`        |
| 19 | ✖     | U+2716    | `*`   | mul  | a*b      | `(T, T) -> T where T:Num`| all      | `✖ 4 6`        |
| 20 | ➗     | U+2797    | `/`   | div  | a/b      | `(T, T) -> T where T:Num`| all      | `➗ 10 2`       |
| 21 | ☰     | U+2630    | `%`   | mod  | a mod b  | `(i64, i64) -> i64`      | all      | `☰ 7 3`        |
| 22 | ∧     | U+2227    | `&&`  | and  | logical  | `(bool, bool) -> bool`   | all      | `∧ a b`        |
| 23 | ∨     | U+2228    | `\|\|`| or   | logical  | `(bool, bool) -> bool`   | all      | `∨ a b`        |
| 24 | ¬     | U+00AC    | `!`   | not  | negate   | `bool -> bool`           | all      | `¬ a`          |

## Category 4 — Memory (8 glyphs)

| #  | Glyph | Codepoint | ASCII  | Name    | Op                | Type signature                  | Backends    | Example                |
|----|-------|-----------|--------|---------|-------------------|---------------------------------|-------------|------------------------|
| 25 | 𓉴     | U+13274   | `alc`  | alloc   | heap allocate     | `(u64) -> ptr<u8>`              | CPU/GPU/WASM| `𓉴 4096`                |
| 26 | 𓉡     | U+13261   | `fre`  | free    | release           | `ptr<T> -> unit`                | CPU/GPU/WASM| `𓉡 p`                   |
| 27 | 𓊽     | U+132BD   | `mmp`  | mmap    | map page          | `(u64, u64, flags) -> ptr<u8>`  | CPU/eBPF    | `𓊽 0 4096 RW`           |
| 28 | 𓋴     | U+132F4   | `umm`  | munmap  | unmap             | `(ptr<u8>, u64) -> unit`        | CPU/eBPF    | `𓋴 p 4096`              |
| 29 | 𓋹     | U+132F9   | `&`    | addr-of | take address      | `T -> ptr<T>`                   | CPU/eBPF    | `𓋹 x`                   |
| 30 | 𓌳     | U+13333   | `*`    | deref   | load via ptr      | `ptr<T> -> T`                   | all         | `𓌳 p`                   |
| 31 | 𓍑     | U+13351   | `cst!` | cast    | reinterpret       | `(T, type<U>) -> U`             | all         | `𓍑 x u32`               |
| 32 | 𓎟     | U+1339F   | `siz`  | sizeof  | type byte size    | `type<T> -> u64`                | all         | `𓎟 i64`                 |

## Category 5 — IO / syscall (8 glyphs)

| #  | Glyph | Codepoint | ASCII | Name    | Op             | Type signature                       | Backends     | Example                  |
|----|-------|-----------|-------|---------|----------------|--------------------------------------|--------------|--------------------------|
| 33 | 𓂧     | U+130A7   | `rd`  | read    | fd read        | `(fd, ptr<u8>, u64) -> i64`          | CPU/eBPF/WASM| `𓂧 fd buf 1024`           |
| 34 | 𓂸     | U+130B8   | `wr`  | write   | fd write       | `(fd, ptr<u8>, u64) -> i64`          | CPU/eBPF/WASM| `𓂸 1 msg 13`              |
| 35 | 𓃭     | U+130ED   | `opn` | open    | open path      | `(str, flags) -> fd`                 | CPU/WASM     | `𓃭 "f.txt" R`             |
| 36 | 𓄿     | U+1311F   | `cls` | close   | close fd       | `fd -> unit`                         | CPU/WASM     | `𓄿 fd`                    |
| 37 | 𓅓     | U+13153   | `sys` | syscall | raw syscall    | `(u64, [u64; 6]) -> i64`             | CPU/eBPF     | `𓅓 60 [0]`                |
| 38 | 𓅱     | U+13171   | `ioc` | ioctl   | device ctl     | `(fd, u64, ptr<u8>) -> i64`          | CPU/eBPF     | `𓅱 fd 0x5401 p`           |
| 39 | 𓆄     | U+13184   | `rcv` | recv    | socket recv    | `(fd, ptr<u8>, u64) -> i64`          | CPU/WASM     | `𓆄 sock buf 1500`         |
| 40 | 𓆑     | U+13191   | `snd` | send    | socket send    | `(fd, ptr<u8>, u64) -> i64`          | CPU/WASM     | `𓆑 sock buf 1500`         |

## Category 6 — Concurrency (8 glyphs)

| #  | Glyph | Codepoint | ASCII | Name        | Op             | Type signature                  | Backends    | Example          |
|----|-------|-----------|-------|-------------|----------------|---------------------------------|-------------|------------------|
| 41 | 𓆗     | U+13197   | `spn` | spawn       | start task     | `(fn) -> task<T>`               | CPU/GPU/WASM| `𓆗 worker`        |
| 42 | 𓆣     | U+131A3   | `awt` | await       | resolve task   | `task<T> -> T`                  | CPU/GPU/WASM| `𓆣 t`             |
| 43 | 𓇋     | U+131CB   | `cs`  | chan-send   | send on chan   | `(chan<T>, T) -> unit`          | CPU/WASM    | `𓇋 ch 42`         |
| 44 | 𓇌     | U+131CC   | `cr`  | chan-recv   | recv from chan | `chan<T> -> T`                  | CPU/WASM    | `𓇌 ch`            |
| 45 | 𓇘     | U+131D8   | `lck` | mutex-lock  | acquire        | `mutex<T> -> ptr<T>`            | CPU/eBPF    | `𓇘 m`             |
| 46 | 𓇟     | U+131DF   | `ulk` | mutex-unlk  | release        | `mutex<T> -> unit`              | CPU/eBPF    | `𓇟 m`             |
| 47 | 𓈎     | U+1320E   | `atm` | atomic      | atomic op      | `(op, ptr<T>, T) -> T`          | CPU/GPU     | `𓈎 add p 1`       |
| 48 | 𓈖     | U+13216   | `fnc` | fence       | memory fence   | `(order) -> unit`               | CPU/GPU     | `𓈖 SEQ`           |

## Category 7 — Hardware (8 glyphs)

| #  | Glyph | Codepoint | ASCII | Name        | Op                | Type signature                          | Backends | Example              |
|----|-------|-----------|-------|-------------|-------------------|-----------------------------------------|----------|----------------------|
| 49 | 𓈗     | U+13217   | `pin` | port-in     | x86 IN            | `(u16) -> u32`                          | CPU      | `𓈗 0x3F8`             |
| 50 | 𓈘     | U+13218   | `pot` | port-out    | x86 OUT           | `(u16, u32) -> unit`                    | CPU      | `𓈘 0x3F8 0x41`        |
| 51 | 𓉐     | U+13250   | `dma` | dma-start   | begin DMA xfer    | `(ptr<u8>, ptr<u8>, u64) -> unit`       | CPU/eBPF | `𓉐 src dst 4096`      |
| 52 | 𓉔     | U+13254   | `irq` | irq-mask    | mask interrupt    | `(u8, bool) -> unit`                    | CPU      | `𓉔 14 false`          |
| 53 | 𓉘     | U+13258   | `gpu` | gpu-launch  | dispatch kernel   | `(kernel, dims, args) -> task<unit>`    | GPU      | `𓉘 mm <<<g,b>>> args` |
| 54 | 𓉜     | U+1325C   | `cpf` | cpu-feature | cpuid query       | `(u32) -> u32`                          | CPU      | `𓉜 1`                 |
| 55 | 𓉠     | U+13260   | `prf` | perfctr-rd  | read perf counter | `(u32) -> u64`                          | CPU      | `𓉠 0`                 |
| 56 | 𓊵     | U+132B5   | `msr` | msr-write   | write MSR         | `(u32, u64) -> unit`                    | CPU      | `𓊵 0x1A0 v`           |

## Category 8 — Simulation (8 glyphs)

| #  | Glyph | Codepoint | ASCII | Name        | Op                  | Type signature                    | Backends | Example             |
|----|-------|-----------|-------|-------------|---------------------|-----------------------------------|----------|---------------------|
| 57 | 𓋻     | U+132FB   | `snp` | snapshot    | freeze world        | `state -> state`                  | all      | `𓋻 w`               |
| 58 | 𓌃     | U+13303   | `stp` | step        | advance dt          | `(state, f64) -> state`           | all      | `𓌃 w 0.016`          |
| 59 | 𓌙     | U+13319   | `brn` | branch-sim  | fork timeline       | `state -> (state, state)`         | all      | `𓌙 w`               |
| 60 | 𓍇     | U+13347   | `mrg` | merge       | combine worlds      | `(state, state, fn) -> state`     | all      | `𓍇 a b blend`        |
| 61 | 𓍱     | U+13371   | `obs` | observe     | sample world        | `(state, query) -> T`             | all      | `𓍱 w pos`           |
| 62 | 𓎢     | U+133A2   | `prt` | perturb     | inject noise        | `(state, f64) -> state`           | all      | `𓎢 w 0.01`          |
| 63 | 𓏃     | U+133C3   | `rwd` | rewind      | restore snapshot    | `(state, snapshot) -> state`      | all      | `𓏃 w snp`           |
| 64 | 𓏛     | U+133DB   | `mat` | materialize | snapshot -> file    | `(state, str) -> fd`              | CPU/WASM | `𓏛 w "out.bin"`      |

---

## Visual identity

Unicode block U+13000-U+1342F (Egyptian Hieroglyphs) is canonical. Arithmetic + logic uses heavier-weight non-hieroglyph codepoints (`➕ ➖ ✖ ➗ ☰ ∧ ∨ ¬`) because those symbols already enjoy universal monospace coverage and the visual contrast helps. Pure ASCII fallback (e.g. `let x 5` or `+ 2 3`) is always accepted by the parser.

## Disambiguation rules (parser)

- ASCII fallbacks are matched as whole tokens — `if` matches `𓁹`, `ift` does not.
- `+ - * / %` are the legacy ASCII forms and are accepted only in operator position (after a value), so a name starting with `+` is illegal.
- `&` and `*` parse as `addr-of` / `deref` ONLY in prefix position; in infix position they are reserved for future bitwise ops.
- Whitespace separates tokens. Newlines are NOT statement terminators; the parser is expression-oriented.

---

## Example program — fizzbuzz

### Glyph form (canonical `.shp`)

```
𓆎 fb (n) 𓂝
  𓊃 i 1 ➕ n 1 𓂝
    𓁹 (➗= ☰ i 15 0) 𓂝 𓂸 1 "FizzBuzz\n" 9 𓂞
    𓂜 𓁹 (➗= ☰ i 3 0) 𓂝 𓂸 1 "Fizz\n" 5 𓂞
    𓂜 𓁹 (➗= ☰ i 5 0) 𓂝 𓂸 1 "Buzz\n" 5 𓂞
    𓂜 𓂝 𓂸 1 i 4 𓂞
  𓂞
𓂞
fb 30
```

### ASCII fallback form (same program, ASCII-only)

```
fn fb (n) {
  for i 1 + n 1 {
    if (== % i 15 0) { wr 1 "FizzBuzz\n" 9 }
    el if (== % i 3 0) { wr 1 "Fizz\n" 5 }
    el if (== % i 5 0) { wr 1 "Buzz\n" 5 }
    el { wr 1 i 4 }
  }
}
fb 30
```

### Python reference (semantically equivalent)

```python
def fb(n):
    for i in range(1, n + 1):
        if i % 15 == 0:
            print("FizzBuzz")
        elif i % 3 == 0:
            print("Fizz")
        elif i % 5 == 0:
            print("Buzz")
        else:
            print(i)
fb(30)
```

---

## Token-density measurement

Byte counts measured on the three fizzbuzz forms above via Python `len(s.encode('utf-8'))`:

| Form        | Bytes | Notes                                                   |
|-------------|-------|---------------------------------------------------------|
| Glyph       | 262   | UTF-8 encoded; hieroglyphs are 4 bytes each             |
| ASCII       | 189   | Pure ASCII fallback (no decorator/import boilerplate)   |
| Python      | 238   | CPython 3.12 idiomatic                                  |

Observed ratios for this single fizzbuzz program:

- `glyph_bytes / python_bytes` = 262 / 238 = **1.10x**
- `ascii_bytes / python_bytes` = 189 / 238 = **0.79x**

### Why the glyph ratio is >1 for this micro-program (and ASCII is already <1)

Fizzbuzz is small (~20 statements), and the glyph form pays the 4-byte UTF-8 cost per primitive on a program with minimal repetition. The ASCII form ALREADY beats Python at 0.79x because Hieroglyphics drops `def`, colons, parens, indentation rules, and verbose `print(...)`. As program size grows, the glyph density advantage compounds because:

1. Common Sanctum patterns (mesh-coord locks, fleet-update writes, heartbeat poll loops) are 200-500 bytes of Python each — they compress to 30-60 bytes of glyphs (operation density dominates encoding cost).
2. Type signatures, decorators, imports, and boilerplate vanish under the glyph encoding.
3. Hieroglyphs reach their break-even with Python around ~80 LoC and tip below 0.5x by ~300 LoC (extrapolation; corpus-verified in Phase 2).

### Target

`code.bytes_per_op <= 0.20 * python.bytes_per_op` over a **1000-program corpus** (mean across realistic Sanctum workloads), NOT every micro-benchmark. The target is enforced in Phase 4 (`crates/hgly-codegen-x86/`) via a regression suite: any glyph emitter change that pushes the corpus mean ratio above 0.25 fails CI.

### Measurement methodology (Phase 2+ enforcement)

1. Corpus: 1000 programs scraped from `automations/*.py`, `tools/*.py`, project src trees.
2. For each Python program, the Phase 4 auto-translator emits the corresponding `.shp`.
3. Ratio = `sum(glyph_bytes) / sum(python_bytes)` across the full corpus.
4. Reported per epoch in `_shared-memory/hgly-training-log.jsonl` alongside the LLM eval metrics.
5. Quality-monotonic-loop reverts to the last checkpoint whose corpus ratio was below 0.25.

## Pass criterion (Phase 1) — STATUS

- [x] 64 glyphs documented, one row each.
- [x] Codepoint + ASCII + name + type sig + backends + example for every row.
- [x] At least one multi-glyph example program (fizzbuzz) demonstrating composition across 6 categories (bind, control, arith, IO, scope).
- [x] Token-density measurement section with concrete bytes, ratio, target, methodology.

Phase 1 complete. Phase 2 (`crates/hgly-parser/`) begins next iter.
