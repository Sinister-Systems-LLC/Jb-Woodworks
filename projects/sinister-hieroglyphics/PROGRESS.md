# PROGRESS — Sinister Hieroglyphics

> Author: RKOJ-ELENO :: 2026-05-25
> Append-only. Most-recent on top.

## 2026-05-27T00:03Z — iter-25 Phase 9.5b density trajectory tracker

Shipped:

- `automations/hgly_density.py` — added `track` subcommand. Composes
  `measure_corpus` -> `trajectory_row` projection (ts_utc + git_sha + 9
  metric fields + freeform `note`) -> `append_trajectory` (JSONL row to
  `_shared-memory/hgly-density-trajectory.jsonl`). `--dry-run` returns
  the row without writing. `--json` flips human-readable text to JSON.
- `_shared-memory/hgly-density-trajectory.jsonl` — seeded with first row:
  ts=2026-05-27T00:02:50Z, sha=85bbbb7, ratio=0.9389. Append-only,
  one JSON object per line.
- `projects/sinister-hieroglyphics/tests/test_density.py` — +2 assertions:
  `t_track_dry_run_schema` (validates trajectory_row keys) and
  `t_track_cli_dry_run` (validates CLI invocation + JSON output schema).
  Total assertions: 7 -> 9.

**Why this and not the queued "Phase 9 corpus expansion" first:** the
ratio trajectory needs a *measurement spine* before the corpus-growth
loop can be evaluated quality-monotonically. Without the JSONL row each
expansion iter would be an opinion ("did ratio improve?"); with it,
loop_checkpoint can read the JSONL tail and detect regression
quantitatively. This is rule-1 from `quality-monotonic-loop.ps1` /
`no-bullshit-tested-before-claimed` — measure first, then expand.

Composes with:

- CLAUDE.md lane rule 1 — token-density is the prime directive; the
  trajectory makes the directive *continuously observable*.
- `loop_checkpoint.py` — next iter wires `hgly_density.py track` into the
  per-iter checkpoint so any ratio regression triggers revert.
- `_shared-memory/plans/sinister-hieroglyphics-master-2026-05-25T1340Z/plan.md`
  Phase 9 — corpus-grow loop now has a fitness function it can chart.

Verify (this turn, all green, same host):

- `python automations/hgly_density.py track --dry-run` -> schema dump, exit 0
- `python automations/hgly_density.py track --note "..."` -> appended JSONL row, exit 0
- `python projects/sinister-hieroglyphics/tests/test_density.py` -> 9/9 passed, exit 0
- `python projects/sinister-hieroglyphics/tests/test_parser.py` -> 11/11 (regression), exit 0
- `python projects/sinister-hieroglyphics/tests/test_ir.py` -> 10/10 (regression), exit 0
- `python projects/sinister-hieroglyphics/tests/test_smoke.py` -> OK 0.0.7, exit 0

Next iter (queued):

1. Wire `hgly_density.py track` into `automations/loop_checkpoint.py` post-iter
   hook so every kernel-loop completion appends a trajectory row tagged with
   the iter id (becomes the quality-monotonic input for the trainer).
2. Phase 9 corpus expansion proper — extend `hgly_corpus_seed.py` with
   `--big` templates (50+ line programs combining memory + concurrency +
   simulation glyphs) since current templates max out around 12 lines.
3. After (2), re-`track` and compare; expect ratio improvement as glyph
   bytes get amortized over larger op counts.

## 2026-05-26T23:25Z — iter-24 Phase 9.5 token-density measurement

Shipped (new files):

- `automations/hgly_density.py` (~280 LOC) — token-density measurement
  tool. Reuses `hgly.lexer.tokenize` so the byte-cost estimator stays in
  lockstep with the language. Subcommands: `measure <path>` (single
  .shp), `corpus [--dir]` (whole corpus), `goal` (one-line baseline).
  Per-program output: `shp_bytes`, `py_bytes_est`, `ops`,
  `shp_bytes_per_op`, `py_bytes_per_op_est`, `ratio`, `passes_goal`.
- `tests/test_density.py` (~155 LOC, 7 assertions) — covers import
  (no torch), DENSITY_GOAL constant matches CLAUDE.md lane rule 1
  (0.20), synthetic token-stream estimator sanity, `measure_one`
  schema, `measure_corpus` live read, CLI `corpus --json` smoke,
  ascii-vs-glyph byte ratio comparison.
- `automations/hgly_status.py` — added `density` subsection to JSON +
  text output (one new line under glyph-coverage row).
- `tests/test_smoke.py` — replaced hardcoded `0.0.2` version assertion
  with SemVer parse + major==0 guard (the literal was stale at 0.0.7,
  was blocking `python tests/test_smoke.py`).

Baseline measured this turn (live corpus, 255 programs):

| metric | value |
|---|---|
| programs | 255 |
| shp bytes total | 18,598 |
| py bytes est total | 19,808 |
| ops total | 4,499 |
| shp B/op avg | 4.134 |
| py B/op avg | 4.403 |
| corpus ratio | **0.9389** |
| pass rate (per-program) | 0/255 (0.0%) |
| goal threshold | 0.20 |
| verdict | **FAIL** (corpus-wide vs 0.20 goal) |

**Honest read:** the bootstrap corpus is 255 tiny 3-to-5-line programs
(mean 73 bytes/program). At that size the 3-4 byte UTF-8 cost of glyphs
actually *hurts* density vs ASCII fallbacks, because there is no
boilerplate Python (imports, function defs, `if __name__`) to
amortize against. The path to <=0.20 is Phase 9 corpus expansion to
multi-hundred-line programs where Python overhead dominates and glyph
compression catches up. This iter ships the *measurement*; the
optimization loop now has a real fitness function.

Verify (all green this turn, same host):

- `python automations/hgly_density.py corpus` -> 255 programs / ratio 0.9389, exit 0
- `python tests/test_density.py` -> `Results: 7/7 passed`, exit 0
- `python tests/test_smoke.py` -> `OK 0.0.7`, exit 0
- `python tests/test_parser.py` -> 11/11 passed (regression check, exit 0)
- `python tests/test_ir.py` -> 10/10 passed (regression check, exit 0)
- `python automations/hgly_status.py` -> shows new `density` row, exit 0

Compose with:

- CLAUDE.md lane rule 1 (token-density is the prime directive) — now
  measured continuously instead of asserted in spec only.
- `_shared-memory/plans/sinister-hieroglyphics-master-2026-05-25T1340Z/plan.md`
  Phase 9 corpus generation — the trainer now has an objective metric
  (ratio drift) for held-out evaluation.
- `automations/hgly_corpus_seed.py` fanout — every new corpus row
  contributes to the rolling ratio; regression triggers loop_checkpoint.

Next iter (queued): Phase 9 corpus expansion via swarm fan-out
(`hgly_corpus_seed.py fanout --slug-prefix hgly-corpus-grow`) targeting
50-line programs that exercise the memory + concurrency + simulation
categories, then re-measure and chart the ratio trajectory.

## CATCH-UP — iter-3 through iter-23 (back-fill 2026-05-26)

The local `PROGRESS.md` was last touched 2026-05-25T15:25Z at v0.0.2;
the actual lane shipped iter-3 through iter-23 in parallel turns whose
PROGRESS rows landed in `_shared-memory/PROGRESS/sinister-hieroglyphics-and-looper.md`
(combo lane). Catch-up below covers the lane-local files that didn't
get a row here. Commit hashes are in `git log --grep=hgly`.

| iter | shipped | tests | commit |
|---|---|---|---|
| 3 | Phase 3 typed SSA IR + TypeChecker | 10/10 | 48f33c3 |
| 4 | Tree-walking interpreter | 7/7 | 75330b2 |
| 5-9 | Parser leniency: corpus pass 12/20 -> 16/20 -> 20/20 | 11/11 | 7f6b0a5 / 648d923 |
| 12 | Absolute peak: 255/255 corpus parse + 64/64 glyph coverage | 11/11 | 1e35845 |
| 13 | Phase 4 stack-VM bytecode codegen stub | 9/9 | 94cb80d |
| 14 | Phase 8 simulation primitives — 8 sim ops | 10/10 | 1a8e023 |
| 15 | Sim primitives wired into interpreter (glyph .shp runs World) | 10/10 | e6b1ac2 |
| 16 | VM dispatches sim ops + interp/VM parity proven | 9/9 | 3fd3ead |
| 17 | Phase 8b ZMQ bridge to desktop python_simulator + synth fallback | 8/8 | 3e25955 |
| 18-19 | Phase 5 PTX text-emit codegen stub + e2e loop demo + revert verified | 7/7 | 7cf5f44 |
| 22 | Live .shp e2e demo (examples/quantum_sim_demo.shp) | (smoke) | a575988 |
| 23 | Bridge wire-protocol fix (MsgType capitalized + SN field) | 8/8 | 32e18be |

**Cumulative state at iter-23 close:** hgly v0.0.7 · 62 unit assertions
+ 255-program corpus + 64/64 glyph coverage + Phase 8b bridge verified
LIVE on :7000 + Phase 5 PTX stub + Phase 4 stack-VM with interp/VM
parity. Trainer scaffold + corpus-seeder + status reader shipped
under `automations/hgly_*.py`. No trainer state JSON yet (torch
unavailable on this host; trainer dry-run path works).

## 2026-05-25T15:25Z — Phase 2 bootstrap (Python parser shipped)

Deviation from master plan: Phase 2 specced `crates/hgly-parser/` in Rust.
Shipped a Python reference implementation first (faster to iterate on the
fluid 64-glyph grammar). Rust port becomes **Phase 2b** once the corpus
+ AST shape stabilize.

Shipped:

- `src/hgly/lexer.py` (126 LOC) — tokenizer for both U+13000 hieroglyphs
  and ASCII fallbacks; `# ...` line comments; string literals with
  `\n \t \r \\ \"` escapes; `Token(kind, lexeme, line, col)`;
  `LexError(msg, line, col)`.
- `src/hgly/ast.py` (117 LOC) — dataclass nodes: `Program`, `Bind`,
  `FnDecl`, `Call`, `If`, `Match`, `Loop`, `Break`, `Return`, `Lambda`,
  `BinOp`, `UnaryOp`, `Literal`, `Ident`, `Block`. All carry `line`/`col`
  and ship a `to_dict()` recursive serializer.
- `src/hgly/parser.py` (248 LOC) — hand-written Pratt parser; precedence
  table covers the Category-3 arith/logic glyphs (`+ - * / % && || == !=
  < > <= >=`) in both **prefix** form (`+ 2 3`) and **infix** form
  (`2 + 3`). Public API: `parse(src) -> Program`, `parse_file(path)`,
  `ParseError(msg, line, col)`. `for v lo hi { body }` desugars to a
  `Loop` with a head `Bind` + `__hgly_for_hi_<v>` marker for later passes.
- `tests/test_parser.py` (361 LOC) — assert-based, runs as `python
  tests/test_parser.py`. Covers 5 fizzbuzz variants (ASCII prefix /
  ASCII infix-loop / naked-cond / glyph-form / mixed glyph+ASCII),
  byte-identical lex->parse->render round-trip on a 50-line sample, and
  5 malformed inputs that surface `ParseError` with correct line/col.
- `src/hgly/__init__.py` — bumped to `0.0.2`; re-exports `parse`,
  `parse_file`, `ParseError`.
- `tests/test_smoke.py` — version assertion bumped to `0.0.2`.

Verify (all green):

- `python tests/test_parser.py` -> `Results: 11/11 passed`, exit 0.
- `python tests/test_smoke.py` -> `OK 0.0.2`, exit 0.
- One-liner: `python -c "import sys; sys.path.insert(0,'src'); import hgly;
  ast = hgly.parse('let x := 5\\nfn main() { print(x) }'); print(ast.to_dict())"`
  runs without exception, prints AST dict.
- Round-trip byte-identical: 557 bytes in == 557 bytes out across the
  50-line canonical sample.

Next: Phase 2b — port to Rust crate `crates/hgly-parser/` once Phase 3
(type checker / lowering) hardens the AST shape.

## 2026-05-25T13:45Z — LANE CREATED

Phase 0 scaffold shipped. Created:

- `CLAUDE.md` (per-lane agent doctrine; tier 2; branch prefix `agent/sinister-hieroglyphics/`)
- `README.md` (public-facing one-pager; 10-phase status table)
- `PROGRESS.md` (this file)
- `pyproject.toml` (name=sinister-hieroglyphics, version=0.0.1, authors=[RKOJ-ELENO], requires-python>=3.10)
- `src/hgly/__init__.py` (`__version__ = "0.0.1"`)
- `src/hgly/cli.py` (argparse stub with `--version` flag)
- `docs/GLYPH-SYNTAX.md` (skeleton TOC for the 64-glyph vocabulary; Phase 1 fills it)
- `corpus/.gitkeep` (placeholder)
- `tests/test_smoke.py` (import + version assertion)

Registered in `automations/session-templates/projects.json` (v14) + added to `picker.visible_keys` + new `Languages` category. Heartbeat skeleton seeded at `_shared-memory/heartbeats/sinister-hieroglyphics.json` with `status: "scaffolded"`.

Master plan path: `_shared-memory/plans/sinister-hieroglyphics-master-2026-05-25T1340Z/plan.md`.

Next: Phase 1 — author the 64-glyph syntax draft in `docs/GLYPH-SYNTAX.md` (Unicode U+13000 block, ASCII fallbacks, type signatures, target backends).
