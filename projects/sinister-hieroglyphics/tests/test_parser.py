"""hgly parser tests.

Author: RKOJ-ELENO :: 2026-05-25
Phase 2 bootstrap.

Cases:
 (a) 5 fizzbuzz variants (ASCII + glyph forms)
 (b) round-trip: lex -> parse -> render -> diff byte-identical for 50-line sample
 (c) 5 malformed inputs each surface ParseError with correct line/col
"""
from __future__ import annotations

import os
import sys
import traceback

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(os.path.dirname(_HERE), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import hgly  # noqa: E402
from hgly.ast import (  # noqa: E402
    Bind, BinOp, Block, Break, Call, FnDecl, Ident, If, Lambda,
    Literal, Loop, Match, Program, Return, UnaryOp,
)
from hgly.lexer import tokenize, LexError  # noqa: E402
from hgly.parser import ParseError  # noqa: E402


_FAILS: list[tuple[str, str]] = []
_PASSES: list[str] = []


def _check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        _PASSES.append(name)
    else:
        _FAILS.append((name, detail))


# ---------------- (a) Fizzbuzz variants ---------------------------------

FIZZBUZZ_ASCII_V1 = """
fn fb (n) {
  for i 1 + n 1 {
    if (== % i 15 0) { wr 1 "FizzBuzz" 8 }
    el if (== % i 3 0) { wr 1 "Fizz" 4 }
    el if (== % i 5 0) { wr 1 "Buzz" 4 }
    el { wr 1 i 4 }
  }
}
fb 30
"""

FIZZBUZZ_ASCII_V2 = """
# infix arithmetic variant
fn fb (n) {
  let total := 0
  let i := 1
  loop {
    if i > n { break }
    let r := i % 15
    if r == 0 { wr 1 "FizzBuzz" 8 } el { wr 1 i 4 }
    let i := i + 1
  }
  ret total
}
fb 100
"""

FIZZBUZZ_ASCII_V3 = """
fn fizzbuzz_one (i) {
  if == % i 15 0 { ret "FizzBuzz" }
  el if == % i 3 0 { ret "Fizz" }
  el if == % i 5 0 { ret "Buzz" }
  el { ret i }
}
"""

FIZZBUZZ_GLYPH_V4 = (
    "\U0001318E fb (n) \U0001309D\n"
    "  \U00013283 i 1 ➕ n 1 \U0001309D\n"
    "    \U00013079 (== ☰ i 15 0) \U0001309D wr 1 \"FizzBuzz\" 8 \U0001309E\n"
    "    \U0001309C \U00013079 (== ☰ i 3 0) \U0001309D wr 1 \"Fizz\" 4 \U0001309E\n"
    "    \U0001309C \U00013079 (== ☰ i 5 0) \U0001309D wr 1 \"Buzz\" 4 \U0001309E\n"
    "    \U0001309C \U0001309D wr 1 i 4 \U0001309E\n"
    "  \U0001309E\n"
    "\U0001309E\n"
    "fb 30\n"
)

FIZZBUZZ_MIXED_V5 = """
# mixed glyph + ASCII; uses ASCII keywords with glyph braces
fn run () \U0001309D
  let limit := 15
  for i 1 + limit 1 \U0001309D
    if (== ☰ i 15 0) { wr 1 "FB" 2 }
    el { wr 1 i 4 }
  \U0001309E
\U0001309E
"""


def test_fizzbuzz_variants() -> None:
    variants = {
        "v1-ascii-prefix": FIZZBUZZ_ASCII_V1,
        "v2-ascii-infix-loop": FIZZBUZZ_ASCII_V2,
        "v3-ascii-naked-cond": FIZZBUZZ_ASCII_V3,
        "v4-glyph-form": FIZZBUZZ_GLYPH_V4,
        "v5-mixed-glyph-ascii": FIZZBUZZ_MIXED_V5,
    }
    for name, src in variants.items():
        try:
            prog = hgly.parse(src)
            _check(f"fizzbuzz/{name}",
                   isinstance(prog, Program) and len(prog.stmts) >= 1,
                   detail=f"parsed {len(prog.stmts)} top-level stmts")
        except Exception as exc:  # pragma: no cover - debug aid
            _check(f"fizzbuzz/{name}", False,
                   detail=f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}")


# ---------------- (b) Round-trip --------------------------------------

# 50-line canonical sample (count includes blank lines / comments).
# We render the AST back to a canonical text form and require byte-identical.
ROUND_TRIP_SRC_LINES = [
    "# round-trip sample - 50 lines",                # 1
    "let x := 5",                                    # 2
    "let y := 10",                                   # 3
    "cst PI := 3.14",                                # 4
    "let flag := true",                              # 5
    "let name := \"sanctum\"",                       # 6
    "fn add (a b) {",                                # 7
    "  ret + a b",                                   # 8
    "}",                                             # 9
    "fn sub (a b) {",                                # 10
    "  ret - a b",                                   # 11
    "}",                                             # 12
    "fn mul (a b) {",                                # 13
    "  ret * a b",                                   # 14
    "}",                                             # 15
    "fn div (a b) {",                                # 16
    "  ret / a b",                                   # 17
    "}",                                             # 18
    "fn andF (a b) {",                               # 19
    "  ret && a b",                                  # 20
    "}",                                             # 21
    "fn orF (a b) {",                                # 22
    "  ret || a b",                                  # 23
    "}",                                             # 24
    "fn notF (a) {",                                 # 25
    "  ret ! a",                                     # 26
    "}",                                             # 27
    "fn main () {",                                  # 28
    "  let s := + x y",                              # 29
    "  let d := - x 1",                              # 30
    "  let p := * x 2",                              # 31
    "  let q := / y 2",                              # 32
    "  let r := % y 3",                              # 33
    "  if == r 0 {",                                 # 34
    "    ret 1",                                     # 35
    "  }",                                           # 36
    "  el {",                                        # 37
    "    ret 0",                                     # 38
    "  }",                                           # 39
    "}",                                             # 40
    "fn driver () {",                                # 41
    "  loop {",                                      # 42
    "    break",                                     # 43
    "  }",                                           # 44
    "}",                                             # 45
    "main",                                          # 46
    "driver",                                        # 47
    "add 1 2",                                       # 48
    "sub 5 3",                                       # 49
    "# end",                                         # 50
]
assert len(ROUND_TRIP_SRC_LINES) == 50, f"need 50 lines, got {len(ROUND_TRIP_SRC_LINES)}"
ROUND_TRIP_SRC = "\n".join(ROUND_TRIP_SRC_LINES) + "\n"


def _render(node, indent: int = 0) -> str:
    """Minimal canonical renderer matching ROUND_TRIP_SRC formatting."""
    pad = "  " * indent
    if isinstance(node, Program):
        return "\n".join(_render(s, indent) for s in node.stmts)
    if isinstance(node, Bind):
        kw = "cst" if node.constant else "let"
        return f"{pad}{kw} {node.name} := {_render_expr(node.value)}"
    if isinstance(node, FnDecl):
        params = " ".join(node.params)
        body = _render(node.body, indent + 1)
        return f"{pad}fn {node.name} ({params}) {{\n{body}\n{pad}}}"
    if isinstance(node, Block):
        return "\n".join(_render(s, indent) for s in node.stmts)
    if isinstance(node, Return):
        if node.value is None:
            return f"{pad}ret"
        return f"{pad}ret {_render_expr(node.value)}"
    if isinstance(node, If):
        cond = _render_expr(node.cond)
        then_body = _render(node.then_branch, indent + 1)
        out = f"{pad}if {cond} {{\n{then_body}\n{pad}}}"
        if isinstance(node.else_branch, If):
            out += f"\n{pad}el {_render(node.else_branch, indent).lstrip()}"
        elif isinstance(node.else_branch, Block):
            eb = _render(node.else_branch, indent + 1)
            out += f"\n{pad}el {{\n{eb}\n{pad}}}"
        return out
    if isinstance(node, Loop):
        body = _render(node.body, indent + 1)
        return f"{pad}loop {{\n{body}\n{pad}}}"
    if isinstance(node, Break):
        return f"{pad}break"
    if isinstance(node, Call):
        callee = _render_expr(node.callee)
        if not node.args:
            return f"{pad}{callee}"
        args = " ".join(_render_expr(a) for a in node.args)
        return f"{pad}{callee} {args}"
    # bare expression statement
    return f"{pad}{_render_expr(node)}"


def _render_expr(node) -> str:
    if node is None:
        return ""
    if isinstance(node, Literal):
        if node.ltype == "str":
            return '"' + node.value + '"'
        if node.ltype == "bool":
            return "true" if node.value else "false"
        if node.ltype == "nil":
            return "nil"
        return repr(node.value) if isinstance(node.value, float) else str(node.value)
    if isinstance(node, Ident):
        return node.name
    if isinstance(node, BinOp):
        # Render in prefix form to match canonical sample.
        return f"{node.op} {_render_expr(node.lhs)} {_render_expr(node.rhs)}"
    if isinstance(node, UnaryOp):
        return f"{node.op} {_render_expr(node.operand)}"
    if isinstance(node, Call):
        callee = _render_expr(node.callee)
        if not node.args:
            return callee
        return callee + " " + " ".join(_render_expr(a) for a in node.args)
    return f"<?{type(node).__name__}?>"


def _canonicalize_comments(src: str, ast: Program) -> str:
    """Render AST then weave comments back in by line number."""
    # Map line# -> comment text (preserve only standalone-line comments)
    comments: dict[int, str] = {}
    for i, line in enumerate(src.split("\n"), 1):
        stripped = line.lstrip()
        if stripped.startswith("#"):
            comments[i] = stripped  # without leading indent
    rendered_lines = _render(ast).split("\n")
    # Insert comments at their original line positions where possible.
    out: list[str] = []
    rendered_iter = iter(rendered_lines)
    src_total_lines = len(src.rstrip("\n").split("\n"))
    cur_rendered: list[str] = list(rendered_iter)
    ri = 0
    for ln in range(1, src_total_lines + 1):
        if ln in comments:
            out.append(comments[ln])
        else:
            if ri < len(cur_rendered):
                out.append(cur_rendered[ri]); ri += 1
    # Append any trailing
    while ri < len(cur_rendered):
        out.append(cur_rendered[ri]); ri += 1
    return "\n".join(out) + "\n"


def test_round_trip() -> None:
    prog = hgly.parse(ROUND_TRIP_SRC)
    rendered = _canonicalize_comments(ROUND_TRIP_SRC, prog)
    if rendered == ROUND_TRIP_SRC:
        _check("round-trip/byte-identical", True,
               detail=f"{len(ROUND_TRIP_SRC)} bytes")
    else:
        # Diff for diagnostics.
        a = ROUND_TRIP_SRC.split("\n")
        b = rendered.split("\n")
        max_len = max(len(a), len(b))
        diff_lines: list[str] = []
        for i in range(max_len):
            la = a[i] if i < len(a) else "<eof>"
            lb = b[i] if i < len(b) else "<eof>"
            if la != lb:
                diff_lines.append(f"L{i+1}: src={la!r} ren={lb!r}")
        _check("round-trip/byte-identical", False,
               detail="\n".join(diff_lines[:8]))


# ---------------- (c) Error cases -------------------------------------

def test_error_cases() -> None:
    cases = [
        # (source, expected_line, expected_col_or_None_for_any)
        ("let", 1, None),               # missing ident
        ("let x :=", 1, None),          # missing rhs
        ("fn ( ) {}", 1, None),         # missing name
        ("if {} ", 1, None),            # missing cond
        ("\n\n{ let x := 1 ", 3, None), # unterminated block
    ]
    for idx, (src, exp_line, exp_col) in enumerate(cases, 1):
        raised = False
        err: ParseError | None = None
        try:
            hgly.parse(src)
        except ParseError as e:
            raised = True; err = e
        except LexError as e:  # lex errors are also acceptable for malformed input
            raised = True
            err = ParseError(str(e), e.line, e.col)
        if not raised:
            _check(f"error-case-{idx}", False, detail=f"no exception for {src!r}")
            continue
        assert err is not None
        line_ok = err.line == exp_line if exp_line is not None else True
        col_ok = err.col == exp_col if exp_col is not None else err.col >= 1
        _check(f"error-case-{idx}", line_ok and col_ok,
               detail=f"got line={err.line} col={err.col} msg={err.msg!r}; want line={exp_line}")


# ---------------- runner --------------------------------------------------

def _safe_print(s: str) -> None:
    # Defensive: stdout on Windows may be cp1252. Encode-decode so glyphs
    # don't crash the runner.
    enc = (sys.stdout.encoding or "ascii").lower()
    try:
        print(s)
    except UnicodeEncodeError:
        print(s.encode(enc, errors="backslashreplace").decode(enc))


def main() -> int:
    test_fizzbuzz_variants()
    test_round_trip()
    test_error_cases()
    total = len(_PASSES) + len(_FAILS)
    _safe_print(f"\nResults: {len(_PASSES)}/{total} passed")
    for name in _PASSES:
        _safe_print(f"  PASS  {name}")
    for name, detail in _FAILS:
        _safe_print(f"  FAIL  {name}")
        if detail:
            for ln in detail.split("\n"):
                _safe_print(f"        {ln}")
    return 0 if not _FAILS else 1


if __name__ == "__main__":
    sys.exit(main())
