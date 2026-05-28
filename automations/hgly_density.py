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
  track [--dry-run]  measure corpus + append row to density trajectory JSONL

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
TRAJECTORY_PATH = SANCTUM / "_shared-memory" / "hgly-density-trajectory.jsonl"

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


# ---------------------------------------------------------------------------
# iter-29 + iter-31 restoration (2026-05-27): per-category density surface.
#
# Categories mirror hgly_corpus_seed.GLYPHS (8 glyph buckets + "other" for
# plain identifiers / numbers / strings that are structurally incompressible).
# The motivating finding from iter-29 PROGRESS row: corpus-wide ratio is
# asymptotic ~0.90 because "other" dominates token counts, but the
# GLYPH-BEARING categories (sim, io, mem, ctrl, conc, hw, arith, bind) can
# and DO hit the <= 0.20 goal independently. The trainer (iter-31) consumes
# this breakdown as a multi-objective fitness signal.
# ---------------------------------------------------------------------------

# Token kind -> category. Bind/scope, control, arithmetic, delimiters all
# resolve via kind alone. The IDENT lexemes that map to specific glyph
# operations route through _LEXEME_CATEGORY below.
_KIND_CATEGORY: dict[str, str] = {
    # bind / scope
    "LET": "bind", "CST": "bind", "FN": "bind", "RET": "bind",
    "LAM": "bind", "AS": "bind", "LBRACE": "bind", "RBRACE": "bind",
    # control
    "IF": "ctrl", "EL": "ctrl", "MATCH": "ctrl", "LOOP": "ctrl",
    "BREAK": "ctrl", "CONT": "ctrl", "YIELD": "ctrl", "FOR": "ctrl",
    # arith / logic
    "PLUS": "arith", "MINUS": "arith", "STAR": "arith", "SLASH": "arith",
    "PERCENT": "arith", "AND": "arith", "OR": "arith", "NOT": "arith",
    "EQ": "arith", "NEQ": "arith", "LT": "arith", "GT": "arith",
    "LE": "arith", "GE": "arith", "ASSIGN": "arith",
    # literals / delimiters route to "other"; left out so default applies
}

# IDENT lexeme -> category. Mirrors hgly_corpus_seed.GLYPHS categories 4-8.
_LEXEME_CATEGORY: dict[str, str] = {
    # Category 4 — Memory
    "alc": "mem", "fre": "mem", "mmp": "mem", "umm": "mem",
    "ldb": "mem", "stb": "mem", "mst": "mem", "mcp": "mem",
    # Category 5 — Concurrency
    "cas": "conc", "tsk": "conc", "syn": "conc", "chn": "conc",
    "snd": "conc", "rcv": "conc", "spn": "conc", "jn": "conc",
    # Category 6 — Hardware
    "irq": "hw", "io": "hw", "gpu": "hw", "ker": "hw",
    "dev": "hw", "mmio": "hw", "fnc": "hw", "evt": "hw",
    # Category 7 — IO
    "opn": "io", "cls": "io", "rd": "io", "wr": "io",
    "skl": "io", "snk": "io", "lsn": "io", "acc": "io",
    # Category 8 — Simulation
    "snp": "sim", "stp": "sim", "brn": "sim", "mrg": "sim",
    "prt": "sim", "obs": "sim", "mat": "sim", "rwd": "sim",
}

CATEGORIES = ("bind", "ctrl", "arith", "mem", "io", "conc", "hw", "sim", "other")


def categorize(t: "Token") -> str:
    if t.kind in _KIND_CATEGORY:
        return _KIND_CATEGORY[t.kind]
    if t.kind == "IDENT" and t.lexeme.lower() in _LEXEME_CATEGORY:
        return _LEXEME_CATEGORY[t.lexeme.lower()]
    return "other"


def measure_by_category(toks: Iterable["Token"]) -> dict:
    """Per-category {shp_bytes, py_bytes_est, tokens, ratio} aggregator."""
    out = {c: {"shp_bytes": 0, "py_bytes_est": 0, "tokens": 0}
           for c in CATEGORIES}
    for t in toks:
        c = categorize(t)
        out[c]["tokens"] += 1
        out[c]["shp_bytes"] += max(1, len(t.lexeme.encode("utf-8")))
        if t.kind in KIND_PY_BYTES:
            out[c]["py_bytes_est"] += KIND_PY_BYTES[t.kind]
        elif t.kind == "IDENT":
            lex_lower = t.lexeme.lower()
            if lex_lower in GLYPH_LEXEME_PY_BYTES:
                out[c]["py_bytes_est"] += GLYPH_LEXEME_PY_BYTES[lex_lower]
            else:
                out[c]["py_bytes_est"] += max(1, len(t.lexeme.encode("utf-8")))
        elif t.kind == "NUMBER":
            out[c]["py_bytes_est"] += max(1, len(t.lexeme.encode("utf-8")))
        elif t.kind == "STRING":
            out[c]["py_bytes_est"] += max(2, len(t.lexeme.encode("utf-8")) + 2)
        else:
            out[c]["py_bytes_est"] += max(1, len(t.lexeme.encode("utf-8")))
    for c, d in out.items():
        py = d["py_bytes_est"]
        d["ratio"] = round(d["shp_bytes"] / py, 4) if py > 0 else None
    return out


def measure_corpus_by_category(corpus_dir: pathlib.Path) -> dict:
    """Aggregate per-category metrics across the entire corpus."""
    if not corpus_dir.exists():
        return {"error": f"corpus dir missing: {corpus_dir}"}
    if not _HAS_LEXER:
        return {"error": f"lexer unavailable: {_LEXER_ERR}"}
    totals = {c: {"shp_bytes": 0, "py_bytes_est": 0, "tokens": 0}
              for c in CATEGORIES}
    n_progs = 0
    n_errors = 0
    for p in sorted(corpus_dir.rglob("*.shp")):
        try:
            src = p.read_text(encoding="utf-8")
            toks = tokenize(src)
        except Exception:
            n_errors += 1
            continue
        n_progs += 1
        per = measure_by_category(toks)
        for c in CATEGORIES:
            totals[c]["shp_bytes"] += per[c]["shp_bytes"]
            totals[c]["py_bytes_est"] += per[c]["py_bytes_est"]
            totals[c]["tokens"] += per[c]["tokens"]
    for c, d in totals.items():
        py = d["py_bytes_est"]
        d["ratio"] = round(d["shp_bytes"] / py, 4) if py > 0 else None
    return {
        "corpus_dir": str(corpus_dir),
        "programs": n_progs,
        "errors": n_errors,
        "categories": totals,
    }


def _git_short_sha() -> Optional[str]:
    try:
        import subprocess
        out = subprocess.run(
            ["git", "-C", str(SANCTUM), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        if out.returncode == 0:
            sha = out.stdout.strip()
            return sha or None
    except Exception:
        return None
    return None


def trajectory_row(d: dict, note: Optional[str] = None) -> dict:
    """Project a corpus-measurement dict down to the trajectory schema."""
    return {
        "ts_utc": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_sha": _git_short_sha(),
        "programs": d.get("programs"),
        "shp_bytes_total": d.get("shp_bytes_total"),
        "py_bytes_est_total": d.get("py_bytes_est_total"),
        "ops_total": d.get("ops_total"),
        "corpus_ratio": d.get("corpus_ratio"),
        "ratio_median": d.get("ratio_median"),
        "pass_rate": d.get("pass_rate"),
        "goal_threshold": d.get("goal_threshold"),
        "goal_met_corpus_wide": d.get("goal_met_corpus_wide"),
        "note": note,
    }


def append_trajectory(row: dict, path: pathlib.Path = TRAJECTORY_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


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
    c.add_argument(
        "--by-category",
        action="store_true",
        help="iter-29: also emit per-category (sim/io/mem/...) ratio breakdown",
    )

    sub.add_parser("goal", help="print density goal + current pass-rate snapshot")

    t = sub.add_parser("track", help="measure corpus + append trajectory row")
    t.add_argument("--dir", default=str(CORPUS_DIR))
    t.add_argument("--out", default=str(TRAJECTORY_PATH))
    t.add_argument("--note", default=None, help="freeform note tagged on the row")
    t.add_argument("--dry-run", action="store_true", help="print row, no JSONL append")
    t.add_argument("--json", dest="json_out", action="store_true")

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
        if args.by_category:
            bc = measure_corpus_by_category(pathlib.Path(args.dir))
            if "error" not in bc:
                d["by_category"] = bc.get("categories", {})
        if args.json_out:
            print(json.dumps(d, indent=2, ensure_ascii=False))
        else:
            print(render_text(d))
            if args.by_category and "by_category" in d:
                print()
                print("  --- per-category ratio breakdown ---")
                print(f"  {'cat':<8} {'ratio':<8} {'shp B':<8} {'py B':<8} {'tokens':<8}")
                for cat in ("sim", "io", "mem", "ctrl", "conc", "hw", "arith", "bind", "other"):
                    row = d["by_category"].get(cat, {})
                    ratio = row.get("ratio")
                    ratio_s = f"{ratio:.4f}" if ratio is not None else "-"
                    print(f"  {cat:<8} {ratio_s:<8} {row.get('shp_bytes', 0):<8} "
                          f"{row.get('py_bytes_est', 0):<8} {row.get('tokens', 0):<8}")
        return 0
    if args.cmd == "goal":
        d = measure_corpus(CORPUS_DIR)
        print(f"density goal: shp_bytes / py_bytes_est <= {DENSITY_GOAL}")
        print(f"corpus ratio: {d.get('corpus_ratio')} ({d.get('programs', 0)} programs)")
        print(f"pass rate:    {d.get('pass_rate')}  (corpus-wide met={d.get('goal_met_corpus_wide')})")
        return 0
    if args.cmd == "track":
        d = measure_corpus(pathlib.Path(args.dir))
        row = trajectory_row(d, note=args.note)
        if not args.dry_run:
            append_trajectory(row, pathlib.Path(args.out))
        if args.json_out:
            print(json.dumps(row, indent=2, ensure_ascii=False))
        else:
            status = "dry-run" if args.dry_run else f"appended {args.out}"
            print(f"density trajectory ({status}):")
            for k in ("ts_utc", "git_sha", "programs", "corpus_ratio",
                      "ratio_median", "pass_rate", "goal_met_corpus_wide", "note"):
                print(f"  {k:<22} {row.get(k)}")
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
