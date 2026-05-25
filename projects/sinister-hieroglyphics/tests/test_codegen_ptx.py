"""hgly Phase 5 CUDA PTX codegen-stub tests.

Author: RKOJ-ELENO :: 2026-05-25
"""
from __future__ import annotations

import os
import sys

_THIS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(_THIS, "..", "src")))

from hgly import parse  # noqa: E402
from hgly import ir as I  # noqa: E402
from hgly.codegen_ptx import (compile_module, emit, PTX_VERSION,  # noqa: E402
                              PTX_TARGET)


def _emit_for(src: str) -> str:
    return emit(src)


def t_emits_ptx_header():
    out = _emit_for("let x := 5\nprint(x)")
    assert f".version {PTX_VERSION}" in out
    assert f".target {PTX_TARGET}" in out
    assert ".address_size 64" in out


def t_emits_kernel_entry():
    out = _emit_for("let x := 5")
    assert ".visible .entry" in out
    assert "__main__" in out


def t_const_lowers_to_mov():
    out = _emit_for("let x := 42")
    assert "mov.s64" in out
    assert "42" in out


def t_binop_lowers():
    out = _emit_for("let r := 6 * 7")
    # No matter which IR the lower chose, a mul.lo or add op should appear.
    assert "mul.lo.s64" in out or "add.s64" in out


def t_round_trip_deterministic():
    src = "let a := 1\nlet b := 2\nlet c := a + b"
    a = _emit_for(src)
    b = _emit_for(src)
    assert a == b, "PTX emit must be deterministic for same source"


def t_only_gpu_filter():
    """compile_module(only_gpu=True) should skip non-GPU fns."""
    mod = I.lower_ast(parse("let x := 5"))
    # main is Effect.IO by default; only_gpu=True -> empty kernel list
    pm = compile_module(mod, only_gpu=True)
    assert len(pm.kernels) == 0


def t_unsupported_ops_are_commented():
    """Calls, Allocs, etc. emit `// ` comments so the PTX file stays parseable
    (PTX accepts `//` line comments)."""
    out = _emit_for("let x := nonexistent_call(1, 2)")
    assert "//" in out


def main():
    tests = [
        ("emits_ptx_header", t_emits_ptx_header),
        ("emits_kernel_entry", t_emits_kernel_entry),
        ("const_lowers_to_mov", t_const_lowers_to_mov),
        ("binop_lowers", t_binop_lowers),
        ("round_trip_deterministic", t_round_trip_deterministic),
        ("only_gpu_filter", t_only_gpu_filter),
        ("unsupported_ops_are_commented", t_unsupported_ops_are_commented),
    ]
    passed = failed = 0
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
