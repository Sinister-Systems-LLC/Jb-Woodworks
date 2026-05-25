"""hgly codegen tests — Phase 4 stack-machine bytecode emitter + VM.

Author: RKOJ-ELENO :: 2026-05-25
"""
from __future__ import annotations

import io
import sys
import os

# allow `from hgly import ...`
_THIS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(_THIS, "..", "src")))

from hgly import parse  # noqa: E402
from hgly import ir as I  # noqa: E402
from hgly.codegen import compile_module, VM, compile_and_run, dump  # noqa: E402


def _capture_stdout(fn):
    buf = io.StringIO()
    saved = sys.stdout
    sys.stdout = buf
    try:
        rv = fn()
    finally:
        sys.stdout = saved
    return rv, buf.getvalue()


def t_const_arith():
    src = "let x := 5\nprint(x + 3)"
    _, out = _capture_stdout(lambda: compile_and_run(src))
    assert "8" in out, f"expected 8 in output, got {out!r}"


def t_string_concat():
    src = 'print("hello" + " " + "world")'
    _, out = _capture_stdout(lambda: compile_and_run(src))
    assert "hello world" in out, f"got {out!r}"


def t_arith_ops():
    src = "print(10 - 3)\nprint(2 * 6)\nprint(20 / 5)\nprint(7 % 3)"
    _, out = _capture_stdout(lambda: compile_and_run(src))
    lines = [l.strip() for l in out.split("\n") if l.strip()]
    assert lines == ["7", "12", "4", "1"], f"got {lines!r}"


def t_disassembly():
    mod = I.lower_ast(parse("let x := 1\nprint(x)"))
    cm = compile_module(mod)
    asm = dump(cm)
    assert "PUSH_CONST" in asm
    assert "CALL" in asm
    assert "STORE" in asm


def t_vm_matches_interpreter():
    """Compile-and-run output must match the tree-walking interpreter for the
    same source. Acts as the score signal for the monotonic-loop demo."""
    from hgly import Interpreter
    samples = [
        "print(2+3)",
        "let x := 4\nprint(x * x)",
        "print(10 - 7 - 1)",
    ]
    for src in samples:
        _, out_cg = _capture_stdout(lambda: compile_and_run(src))
        _, out_in = _capture_stdout(lambda: Interpreter().run(parse(src)))
        assert out_cg.strip() == out_in.strip(), (
            f"codegen vs interp mismatch for {src!r}: "
            f"cg={out_cg!r} in={out_in!r}"
        )


def t_lenient_unknown_call():
    """Unknown calls should return 0 (lenient), not crash. Matches interp."""
    src = "let r := nonexistent_fn(1, 2)\nprint(r)"
    _, out = _capture_stdout(lambda: compile_and_run(src))
    assert "0" in out, f"expected 0 from unknown call, got {out!r}"


def t_panic_returns_134():
    src = 'panic("boom")'
    rv = compile_and_run(src)
    assert rv == 134, f"expected 134 panic exit, got {rv!r}"


def t_vm_sim_dispatch():
    """VM must dispatch sim ops to real World (iter-16). Compile a tiny
    snapshot+step program; verify World advanced t > 0."""
    from hgly.sim import reset_world, get_world
    reset_world(init={"x": 1.0}, seed=99)
    src = "let s0 := snapshot(0)\nlet s1 := step(s0, 0.5)"
    compile_and_run(src)
    w = get_world()
    assert w.t > 0.0, f"expected world.t advanced after step, got t={w.t}"
    assert len(w.snapshots) >= 2, f"expected >=2 snapshots, got {len(w.snapshots)}"


def t_vm_interp_sim_parity():
    """Interpreter and VM must observe the SAME world state evolution given
    identical sim programs + seed. Operator-aligned monotonic-loop signal."""
    from hgly.sim import reset_world, get_world
    from hgly import Interpreter, parse
    src = ("let s0 := snapshot(0)\n"
           "let s1 := step(s0, 0.25)\n"
           "let s2 := perturb(s1, 0.02)\n"
           "let o := observe(s2, \"x\")")
    # Run via interp
    reset_world(init={"x": 5.0}, seed=7777)
    Interpreter().run(parse(src))
    w1 = get_world()
    t_interp = w1.t; n_interp = len(w1.snapshots)
    # Run via VM (fresh world, same seed)
    reset_world(init={"x": 5.0}, seed=7777)
    compile_and_run(src)
    w2 = get_world()
    t_vm = w2.t; n_vm = len(w2.snapshots)
    assert abs(t_interp - t_vm) < 1e-9, (
        f"world.t diverged: interp={t_interp} vm={t_vm}"
    )
    assert n_interp == n_vm, (
        f"snapshot count diverged: interp={n_interp} vm={n_vm}"
    )


def main():
    tests = [
        ("const_arith", t_const_arith),
        ("string_concat", t_string_concat),
        ("arith_ops", t_arith_ops),
        ("disassembly", t_disassembly),
        ("vm_matches_interpreter", t_vm_matches_interpreter),
        ("lenient_unknown_call", t_lenient_unknown_call),
        ("panic_returns_134", t_panic_returns_134),
        ("vm_sim_dispatch", t_vm_sim_dispatch),
        ("vm_interp_sim_parity", t_vm_interp_sim_parity),
    ]
    passed = 0
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS  {name}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"  FAIL  {name}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n== {passed} passed, {failed} failed ==")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
