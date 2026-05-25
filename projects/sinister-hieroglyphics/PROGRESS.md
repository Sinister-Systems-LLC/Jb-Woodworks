# PROGRESS — Sinister Hieroglyphics

> Author: RKOJ-ELENO :: 2026-05-25
> Append-only. Most-recent on top.

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
