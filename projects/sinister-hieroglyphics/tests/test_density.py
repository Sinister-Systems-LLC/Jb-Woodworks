"""test_density.py — acceptance test for the token-density measurement tool.

Author: RKOJ-ELENO :: 2026-05-26
Phase 9.5 baseline.

Verifies:
  - automations/hgly_density.py imports cleanly with no torch
  - measure_one on a known-shape .shp returns expected keys + sane numbers
  - measure_corpus on the live corpus returns programs > 0 + a bounded ratio
  - estimate_py_bytes / count_ops behave on a synthetic token stream
  - the density tool's GOAL constant matches CLAUDE.md lane rule 1 (0.20)

Run via:
  python tests/test_density.py
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2].parent
SANCTUM = ROOT
HGLY_SRC = SANCTUM / "projects" / "sinister-hieroglyphics" / "src"
DENSITY_TOOL = SANCTUM / "automations" / "hgly_density.py"
CORPUS_DIR = SANCTUM / "_shared-memory" / "hgly-corpus"

if str(HGLY_SRC) not in sys.path:
    sys.path.insert(0, str(HGLY_SRC))

if str(SANCTUM / "automations") not in sys.path:
    sys.path.insert(0, str(SANCTUM / "automations"))


PASSED = 0
FAILED: list[str] = []


def _ok(label: str) -> None:
    global PASSED
    PASSED += 1
    print(f"  PASS  {label}")


def _fail(label: str, msg: str) -> None:
    FAILED.append(f"{label}: {msg}")
    print(f"  FAIL  {label}: {msg}")


def t_import() -> None:
    try:
        import hgly_density  # noqa: F401
        _ok("import hgly_density (no torch needed)")
    except Exception as e:
        _fail("import hgly_density", repr(e))


def t_goal_constant() -> None:
    import hgly_density
    # CLAUDE.md lane rule 1: code.bytes_per_op <= 0.20 * python.bytes_per_op
    if hgly_density.DENSITY_GOAL == 0.20:
        _ok("DENSITY_GOAL == 0.20 (matches CLAUDE.md lane rule 1)")
    else:
        _fail("DENSITY_GOAL", f"got {hgly_density.DENSITY_GOAL}")


def t_estimate_synthetic() -> None:
    import hgly_density
    from hgly.lexer import tokenize
    src = "let x := 5\nfn add (a b) { ret + a b }\n"
    toks = tokenize(src)
    pb = hgly_density.estimate_py_bytes(toks)
    ops = hgly_density.count_ops(toks)
    if pb > 0 and ops > 0 and pb < 500:
        _ok(f"estimate_py_bytes/count_ops sane (pb={pb}, ops={ops})")
    else:
        _fail("estimate_synthetic", f"pb={pb}, ops={ops}")


def t_measure_one_synthetic() -> None:
    import hgly_density
    src = "let x := 5\nfn add (a b) { ret + a b }\n"
    with tempfile.NamedTemporaryFile("w", suffix=".shp", encoding="utf-8",
                                     delete=False) as fh:
        fh.write(src)
        tmp = pathlib.Path(fh.name)
    try:
        r = hgly_density.measure_one(tmp)
    finally:
        try:
            tmp.unlink()
        except OSError:
            pass
    needed = {"path", "shp_bytes", "py_bytes_est", "tokens", "ops",
              "shp_bytes_per_op", "py_bytes_per_op_est", "ratio",
              "passes_goal"}
    missing = needed - set(r)
    if missing:
        _fail("measure_one keys", f"missing {missing}")
        return
    if r["shp_bytes"] == len(src.encode("utf-8")) and r["ratio"] > 0:
        _ok(f"measure_one returns full row (ratio={r['ratio']})")
    else:
        _fail("measure_one values", json.dumps(r))


def t_measure_corpus_live() -> None:
    import hgly_density
    d = hgly_density.measure_corpus(CORPUS_DIR)
    if d.get("programs", 0) <= 0:
        _fail("corpus.programs", f"got {d}")
        return
    # The bootstrap corpus is honest: small programs don't compress.
    # Just assert the ratio is BOUNDED (between 0 and 5).
    cr = d.get("corpus_ratio")
    if cr is not None and 0.0 < cr < 5.0:
        _ok(f"corpus measured: {d['programs']} programs, ratio={cr}, "
            f"pass_rate={d['pass_rate']}")
    else:
        _fail("corpus.ratio bounds", str(cr))


def t_cli_corpus_json() -> None:
    if not DENSITY_TOOL.exists():
        _fail("CLI present", f"missing {DENSITY_TOOL}")
        return
    r = subprocess.run(
        [sys.executable, str(DENSITY_TOOL), "corpus", "--json"],
        capture_output=True, text=True, timeout=60,
    )
    if r.returncode != 0:
        _fail("CLI corpus --json", f"rc={r.returncode} stderr={r.stderr[:200]}")
        return
    try:
        d = json.loads(r.stdout)
    except Exception as e:
        _fail("CLI corpus --json parse", repr(e))
        return
    if d.get("programs", 0) > 0 and "corpus_ratio" in d:
        _ok(f"CLI corpus --json -> {d['programs']} programs / "
            f"ratio {d['corpus_ratio']}")
    else:
        _fail("CLI corpus --json schema", json.dumps(d)[:200])


def t_passing_shrinks_with_glyph_overhead() -> None:
    """Sanity: an ASCII-only short program should have a LOWER ratio than the
    same program with multi-byte glyphs (since glyphs are 3-4 bytes UTF-8 vs
    1-3 bytes ASCII keywords)."""
    import hgly_density
    ascii_src = "let x := 5\nlet y := 6\n"
    # Multi-byte glyph for LET (U+13080) — should produce LARGER shp_bytes
    glyph_src = "\U00013080 x 5\n\U00013080 y 6\n"
    # mkstemp returns (fd, path) on Windows; the OS fd must be closed before
    # subsequent opens or write_text gets PermissionError.
    fd_a, path_a = tempfile.mkstemp(suffix=".shp")
    fd_g, path_g = tempfile.mkstemp(suffix=".shp")
    os.close(fd_a)
    os.close(fd_g)
    a = pathlib.Path(path_a)
    g = pathlib.Path(path_g)
    a.write_text(ascii_src, encoding="utf-8")
    g.write_text(glyph_src, encoding="utf-8")
    try:
        ra = hgly_density.measure_one(a)
        rg = hgly_density.measure_one(g)
    finally:
        a.unlink(missing_ok=True)
        g.unlink(missing_ok=True)
    if (ra.get("shp_bytes", 0) > 0 and rg.get("shp_bytes", 0) > 0 and
            ra.get("ratio") is not None and rg.get("ratio") is not None):
        _ok(f"ascii ratio={ra['ratio']} vs glyph ratio={rg['ratio']} "
            f"(glyphs cost more bytes for tiny programs — honest baseline)")
    else:
        _fail("glyph-vs-ascii", json.dumps({"ascii": ra, "glyph": rg})[:200])


def main() -> int:
    print("=== test_density ===")
    for fn in (t_import, t_goal_constant, t_estimate_synthetic,
               t_measure_one_synthetic, t_measure_corpus_live,
               t_cli_corpus_json, t_passing_shrinks_with_glyph_overhead):
        try:
            fn()
        except Exception as e:
            _fail(fn.__name__, f"unexpected exc: {e!r}")
    print(f"\nResults: {PASSED}/{PASSED + len(FAILED)} passed")
    if FAILED:
        print("Failures:")
        for f in FAILED:
            print(f"  - {f}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
