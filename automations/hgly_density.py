#!/usr/bin/env python3
"""hgly_density.py — token-density measurement for Sinister Hieroglyphics.

Author: RKOJ-ELENO :: 2026-05-26

Scores .shp programs against the prime directive
(projects/sinister-hieroglyphics/CLAUDE.md rule 1 +
 _shared-memory/plans/sinister-hieroglyphics-master-2026-05-25T1340Z/plan.md
 token-density goal):

    shp_bytes_per_op <= 0.20 * python_bytes_per_op

Per program:
  - shp_bytes   = len(source.encode('utf-8'))
  - py_bytes    = sum(per_token_py_estimate(tok) for tok in lex(source))
  - ratio       = shp_bytes / max(1, py_bytes)
  - op_count    = len(non_punct_tokens) — proxy for semantic ops
  - PASS iff ratio <= 0.20

Subcommands
===========
  measure <path>     score a single .shp file (path or glob)
  corpus [--dir]     score the whole corpus under _shared-memory/hgly-corpus/
  report --json      JSON pretty-print of corpus measurement
  goal               re-print the goal + current pass rate; exit 0 always

Constraints (operator hard-canonical 2026-05-25):
  - Pure Python 3 stdlib + the in-tree hgly.lexer (no torch / no requests).
  - --dry-run on subcommands that touch disk.
  - Reads UTF-8 .shp; writes UTF-8 JSON.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import io
import json
import os
import pathlib
import sys
from typing import Any, Iterable, Optional

# Reconfigure stdout/stderr to UTF-8 so glyph codepoints print on Windows cp1252.
try:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
except Exception:
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

SANCTUM = pathlib.Path(os.environ.get("SINISTER_SANCTUM_ROOT", r"D:\Sinister Sanctum"))
HGLY_SRC = SANCTUM / "projects" / "sinister-hieroglyphics" / "src"
CORPUS_DIR = SANCTUM / "_shared-memory" / "hgly-corpus"

if str(HGLY_SRC) not in sys.path:
    sys.path.insert(0, str(HGLY_SRC))

try:
    from hgly.lexer import tokenize, Token, LexError  # type: ignore
    _HAS_LEXER = True
except Exception as _e:  # pragma: no cover - import-failure surface
    _HAS_LEXER = False
    _LEXER_ERR = repr(_e)


# Goal from CLAUDE.md lane rule 1 / plan token-density goal
DENSITY_GOAL = 0.20


# Token-kind -> Python source byte estimate. The estimate counts ONLY the
# python keyword/punctuation glue the kind expands to; identifier / literal
# bytes are added separately from the token's own lexeme length.
KIND_PY_BYTES: dict[str, int] = {
    # Bind / scope
    "LET":     4,    # "x = "
    "CST":     4,    # uppercase X = (same width)
    "FN":      12,   # "def name():\n"
    "RET":     7,    # "return "
    "LAM":     8,    # "lambda: "
    "AS":      9,    # "# alias\n"
    "LBRACE":  5,    # "    " indent + "\n" approx
    "RBRACE":  1,    # dedent (newline)

    # Control
    "IF":      3,    # "if "
    "EL":      6,    # "else: "
    "MATCH":   8,    # "match x:\n"
    "LOOP":    12,   # "while True:\n"
    "BREAK":   6,    # "break\n"
    "CONT":    9,    # "continue\n"
    "YIELD":   6,    # "yield "
    "FOR":     18,   # "for i in range():\n"

    # Arithmetic / logic (binary inline ops use " op ")
    "PLUS":    3,
    "MINUS":   3,
    "STAR":    3,
    "SLASH":   3,
    "PERCENT": 3,
    "AND":     5,    # " and "
    "OR":      4,    # " or "
    "NOT":     4,    # "not "
    "EQ":      4,    # " == "
    "NEQ":     4,    # " != "
    "LT":      3,
    "GT":      3,
    "LE":      4,
    "GE":      4,
    "ASSIGN":  3,    # " = "

    # Delimiters
    "LPAREN":  1,
    "RPAREN":  1,
    "LBRACK":  1,
    "RBRACK":  1,
    "COLON":   1,
    "COMMA":   1,
    "SEMI":    1,
    "AMP":     1,
    "PIPE":    1,
    "CAST":    8,    # "int(...)" or "cast(...)"

    # Literals
    "TRUE":    4,    # "True"
    "FALSE":   5,    # "False"
    "NIL":     4,    # "None"
}

# Non-keyword glyph / ASCII-fallback identifiers (categories 4-8) that tokenize
# as IDENT in the lexer but expand to substantial Python on translation. Map
# lexeme (normalized to lowercase ASCII fallback) -> python byte estimate.
# Bytes are a CONSERVATIVE estimate of the shortest Python that does the same op.
GLYPH_LEXEME_PY_BYTES: dict[str, int] = {
    # Category 4 — Memory
    "alc": 11,  # "bytearray(n)"
    "fre": 6,   # "del p\n"
    "mmp": 46,  # "mmap.mmap(0,0,prot=PROT_READ|PROT_WRITE)"
    "umm": 9,   # "p.close()"
    "ldb": 12,  # "int.from_bytes"
    "stb": 14,  # "n.to_bytes(...)"
    "mst": 8,   # "memset("
    "mcp": 9,   # "memcpy("
    # Category 5 — Concurrency
    "cas": 18,  # "atomic.compare_swap"
    "tsk": 18,  # "asyncio.create_task"
    "syn": 18,  # "threading.Lock()"
    "chn": 16,  # "queue.Queue()"
    "snd": 10,  # "ch.put(v)"
    "rcv": 12,  # "v = ch.get()"
    "spn": 16,  # "threading.Thread"
    "jn":  11,  # "thread.join"
    # Category 6 — Hardware
    "irq": 16,  # "signal.signal(...)"
    "io":  10,  # "os.read(fd)"
    "gpu": 20,  # "cuda.synchronize"
    "ker": 14,  # "syscall(SYS_...)"
    "dev": 14,  # "open('/dev/...')"
    "mmio": 24, # "mmap+ctypes"
    "fnc": 14,  # "threading.Event"
    "evt": 14,  # "evt.wait()"
    # Category 7 — IO
    "opn": 12,  # "open('p', 'r')"
    "cls": 11,  # "f.close()\n"
    "rd":  14,  # "data = f.read()"
    "wr":  14,  # "f.write(data)"
    "skl": 18,  # "socket.socket"
    "snk": 18,  # "sock.connect"
    "lsn": 14,  # "sock.listen"
    "acc": 12,  # "sock.accept"
    # Category 8 — Simulation
    "snp": 16,  # "world.snapshot()"
    "stp": 18,  # "world.step(dt)"
    "brn": 14,  # "branch(state)"
    "mrg": 12,  # "merge(a,b)"
    "prt": 14,  # "perturb(s, e)"
    "obs": 16,  # "observe(s, k)"
    "mat": 14,  # "materialize(s)"
    "rwd": 14,  # "rewind(state)"
}


def estimate_py_bytes(toks: Iterable[Token]) -> int:
    total = 0
    for t in toks:
        if t.kind in KIND_PY_BYTES:
            total += KIND_PY_BYTES[t.kind]
        elif t.kind == "IDENT":
            lex_lower = t.lexeme.lower()
            if lex_lower in GLYPH_LEXEME_PY_BYTES:
                total += GLYPH_LEXEME_PY_BYTES[lex_lower]
            else:
                # plain identifier — same name in Python
                total += max(1, len(t.lexeme.encode("utf-8")))
        elif t.kind == "NUMBER":
            total += max(1, len(t.lexeme.encode("utf-8")))
        elif t.kind == "STRING":
            # +2 for quotes (Python needs them too)
            total += max(2, len(t.lexeme.encode("utf-8")) + 2)
        else:
            total += max(1, len(t.lexeme.encode("utf-8")))
    return total


def count_ops(toks: Iterable[Token]) -> int:
    """Op count = non-punct, non-literal tokens. Proxy for semantic operations."""
    PUNCT = {"LPAREN", "RPAREN", "LBRACK", "RBRACK", "LBRACE", "RBRACE",
             "COLON", "COMMA", "SEMI"}
    return sum(1 for t in toks if t.kind not in PUNCT)


def measure_one(path: pathlib.Path) -> dict:
    if not _HAS_LEXER:
        return {"path": str(path), "error": f"lexer unavailable: {_LEXER_ERR}"}
    try:
        src = path.read_text(encoding="utf-8")
    except Exception as e:
        return {"path": str(path), "error": f"read failed: {e!r}"}
    shp_bytes = len(src.encode("utf-8"))
    try:
        toks = tokenize(src)
    except LexError as e:
        return {"path": str(path), "shp_bytes": shp_bytes,
                "error": f"lex failed: {e}"}
    py_bytes = estimate_py_bytes(toks)
    ops = count_ops(toks)
    ratio = (shp_bytes / py_bytes) if py_bytes > 0 else None
    return {
        "path": str(path),
        "shp_bytes": shp_bytes,
        "py_bytes_est": py_bytes,
        "tokens": len(toks),
        "ops": ops,
        "shp_bytes_per_op": round(shp_bytes / ops, 3) if ops else None,
        "py_bytes_per_op_est": round(py_bytes / ops, 3) if ops else None,
        "ratio": round(ratio, 4) if ratio is not None else None,
        "passes_goal": (ratio is not None and ratio <= DENSITY_GOAL),
    }


def measure_corpus(corpus_dir: pathlib.Path) -> dict:
    if not corpus_dir.exists():
        return {"error": f"corpus dir missing: {corpus_dir}"}
    rows: list[dict] = []
    for p in sorted(corpus_dir.rglob("*.shp")):
        rows.append(measure_one(p))
    measured = [r for r in rows if "error" not in r and r.get("ratio") is not None]
    n = len(measured)
    if n == 0:
        return {"corpus_dir": str(corpus_dir), "programs": 0,
                "errors": [r for r in rows if "error" in r]}
    total_shp = sum(r["shp_bytes"] for r in measured)
    total_py = sum(r["py_bytes_est"] for r in measured)
    total_ops = sum(r["ops"] for r in measured)
    ratios = sorted(r["ratio"] for r in measured)
    passing = sum(1 for r in measured if r["passes_goal"])
    return {
        "corpus_dir": str(corpus_dir),
        "programs": n,
        "errors": len([r for r in rows if "error" in r]),
        "shp_bytes_total": total_shp,
        "py_bytes_est_total": total_py,
        "ops_total": total_ops,
        "shp_bytes_per_op_avg": round(total_shp / total_ops, 3) if total_ops else None,
        "py_bytes_per_op_avg": round(total_py / total_ops, 3) if total_ops else None,
        "corpus_ratio": round(total_shp / total_py, 4) if total_py else None,
        "ratio_median": ratios[n // 2],
        "ratio_min": ratios[0],
        "ratio_max": ratios[-1],
        "programs_passing_goal": passing,
        "pass_rate": round(passing / n, 4),
        "goal_threshold": DENSITY_GOAL,
        "goal_met_corpus_wide": (total_shp / total_py) <= DENSITY_GOAL if total_py else False,
    }


def render_text(d: dict) -> str:
    if "error" in d:
        return f"ERROR: {d['error']}"
    lines = []
    lines.append(f"=== hgly density :: {d.get('corpus_dir', '?')} ===")
    lines.append(f"  programs        {d['programs']} (errors: {d['errors']})")
    lines.append(f"  shp bytes       {d['shp_bytes_total']:,}")
    lines.append(f"  py bytes (est)  {d['py_bytes_est_total']:,}")
    lines.append(f"  ops             {d['ops_total']:,}")
    lines.append(f"  shp/op avg      {d['shp_bytes_per_op_avg']} B")
    lines.append(f"  py/op avg       {d['py_bytes_per_op_avg']} B")
    lines.append(f"  corpus ratio    {d['corpus_ratio']}  (goal <= {d['goal_threshold']})")
    lines.append(f"  per-program     min={d['ratio_min']}  median={d['ratio_median']}  max={d['ratio_max']}")
    lines.append(f"  pass rate       {d['programs_passing_goal']}/{d['programs']} "
                 f"= {d['pass_rate'] * 100:.1f}%")
    verdict = "PASS" if d["goal_met_corpus_wide"] else "FAIL"
    lines.append(f"  verdict         {verdict} (corpus-wide ratio vs {d['goal_threshold']} goal)")
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(prog="hgly_density")
    sub = p.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("measure", help="score a single .shp file")
    m.add_argument("path")
    m.add_argument("--json", dest="json_out", action="store_true")

    c = sub.add_parser("corpus", help="score the corpus")
    c.add_argument("--dir", default=str(CORPUS_DIR))
    c.add_argument("--json", dest="json_out", action="store_true")

    sub.add_parser("goal", help="print density goal + current pass-rate snapshot")

    args = p.parse_args()

    if args.cmd == "measure":
        r = measure_one(pathlib.Path(args.path))
        if args.json_out:
            print(json.dumps(r, indent=2, ensure_ascii=False))
        else:
            for k, v in r.items():
                print(f"  {k:<22} {v}")
        return 0
    if args.cmd == "corpus":
        d = measure_corpus(pathlib.Path(args.dir))
        if args.json_out:
            print(json.dumps(d, indent=2, ensure_ascii=False))
        else:
            print(render_text(d))
        return 0
    if args.cmd == "goal":
        d = measure_corpus(CORPUS_DIR)
        print(f"density goal: shp_bytes / py_bytes_est <= {DENSITY_GOAL}")
        print(f"corpus ratio: {d.get('corpus_ratio')} ({d.get('programs', 0)} programs)")
        print(f"pass rate:    {d.get('pass_rate')}  (corpus-wide met={d.get('goal_met_corpus_wide')})")
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
