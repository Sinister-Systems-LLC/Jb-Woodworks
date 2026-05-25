"""hgly interpreter tests.

Author: RKOJ-ELENO :: 2026-05-25
Phase 2 bootstrap. Six unit cases + one corpus smoke. Stdlib only.
Exit 0 iff every unit assertion passes (corpus reports counts but never fails
the suite — corpus failures expected on unimplemented syscalls).
"""
from __future__ import annotations
import glob
import io
import os
import sys
import traceback

# Force stdout to handle glyph output (corpus + interp output may contain U+13000 chars)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(os.path.dirname(_HERE), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from hgly import parse, Interpreter, HglyPanic  # noqa: E402

_PASS: list[str] = []
_FAIL: list[tuple[str, str]] = []


def _run(src: str, args=None) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    it = Interpreter(stdout=out, stderr=err)
    rc = it.run(parse(src), args)
    return rc, out.getvalue(), err.getvalue()


def _expect(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        _PASS.append(name); print(f"PASS {name}")
    else:
        _FAIL.append((name, detail)); print(f"FAIL {name} :: {detail}")


def test_let_and_print() -> None:
    rc, out, _ = _run('let x := 5; print(x)')
    _expect("let_and_print", rc == 0 and out == "5",
            f"rc={rc} out={out!r}")


def test_fizzbuzz_output() -> None:
    src = """
for i 1 16 {
  if (== % i 15 0) { println("FizzBuzz") }
  el if (== % i 3 0) { println("Fizz") }
  el if (== % i 5 0) { println("Buzz") }
  el { println(i) }
}
"""
    rc, out, _ = _run(src)
    expected = ("1\n2\nFizz\n4\nBuzz\nFizz\n7\n8\nFizz\nBuzz\n"
                "11\nFizz\n13\n14\nFizzBuzz\n")
    _expect("fizzbuzz_output", rc == 0 and out == expected,
            f"rc={rc} out={out!r}")


def test_recursive_factorial() -> None:
    src = """
fn fact(n) {
  if (< n 2) { ret 1 }
  ret n * fact(- n 1)
}
println(fact(6))
"""
    rc, out, _ = _run(src)
    _expect("recursive_factorial", rc == 0 and out == "720\n",
            f"rc={rc} out={out!r}")


def test_closure_capture() -> None:
    src = """
fn mkadder(x) {
  ret lam(y) { ret + x y }
}
let add5 := mkadder(5)
println(add5(37))
"""
    rc, out, _ = _run(src)
    _expect("closure_capture", rc == 0 and out == "42\n",
            f"rc={rc} out={out!r}")


def test_panic_returns_134() -> None:
    rc, _, err = _run('panic("boom")')
    _expect("panic_returns_134", rc == 134 and "boom" in err,
            f"rc={rc} err={err!r}")


def test_assert_false_returns_134() -> None:
    rc, _, err = _run('assert(false, "nope")')
    _expect("assert_false_returns_134", rc == 134 and "nope" in err,
            f"rc={rc} err={err!r}")


def test_corpus_smoke() -> int:
    """Walk bootstrap corpus; report pass/fail counts. NEVER fails the suite."""
    corpus_dir = os.path.normpath(os.path.join(
        _HERE, "..", "..", "..", "_shared-memory", "hgly-corpus",
        "bootstrap-2026-05-25"))
    files = sorted(glob.glob(os.path.join(corpus_dir, "*.shp")))
    if not files:
        print(f"corpus_smoke: no files at {corpus_dir}")
        return 0
    ok = 0; fail = 0
    for fp in files:
        name = os.path.basename(fp)
        try:
            with open(fp, "r", encoding="utf-8") as fh:
                src = fh.read()
            prog = parse(src)
            out = io.StringIO(); err = io.StringIO()
            rc = Interpreter(stdout=out, stderr=err).run(prog)
            if rc == 0:
                ok += 1; print(f"  corpus OK   {name}")
            else:
                fail += 1
                msg = ascii(err.getvalue())
                print(f"  corpus FAIL {name} rc={rc} err={msg}")
        except Exception as e:
            fail += 1; print(f"  corpus FAIL {name} :: {ascii(repr(e))}")
    total = ok + fail
    print(f"corpus_smoke: {ok}/{total} succeeded (criterion: >=12/20)")
    _expect("corpus_smoke_criterion", ok >= 12,
            f"only {ok}/{total} programs ran clean")
    return ok


def main() -> int:
    tests = [test_let_and_print, test_fizzbuzz_output, test_recursive_factorial,
             test_closure_capture, test_panic_returns_134,
             test_assert_false_returns_134]
    for t in tests:
        try:
            t()
        except Exception as e:
            _FAIL.append((t.__name__, f"exception: {e!r}"))
            traceback.print_exc()
    test_corpus_smoke()
    print(f"\n== {len(_PASS)} passed, {len(_FAIL)} failed ==")
    for n, d in _FAIL:
        print(f"  FAIL {n}: {d}")
    return 0 if not _FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
