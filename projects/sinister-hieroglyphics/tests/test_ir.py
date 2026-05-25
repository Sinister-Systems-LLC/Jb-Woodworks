"""hgly IR + TypeChecker tests.

Author: RKOJ-ELENO :: 2026-05-25
Phase 3 bootstrap. 8 unit tests covering lower_ast + type checker.
"""
from __future__ import annotations
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(HERE, "..", "src"))
if SRC not in sys.path: sys.path.insert(0, SRC)

from hgly import parse  # noqa: E402
from hgly.ir import (lower_ast, TypeChecker, Module, Function, Block, Effect,
                     TInt, TStr, TUnit, TLinear, TBool, TFloat,
                     Const, BinOp, Call, Return)  # noqa: E402


# ---- helpers -------------------------------------------------------------

def _ops(mod: Module):
    yield from mod.main.blocks[0].ops
    for f in mod.functions:
        for b in f.blocks:
            for o in b.ops: yield o


def _has(mod: Module, cls, **match) -> bool:
    for op in _ops(mod):
        if isinstance(op, cls):
            ok = True
            for k, v in match.items():
                if k == "value" and isinstance(op, Const):
                    if op.args[0] != v: ok = False; break
                elif k == "op" and isinstance(op, BinOp):
                    if op.args[0] != v: ok = False; break
                elif k == "callee" and isinstance(op, Call):
                    if op.args[0] != v: ok = False; break
            if ok: return True
    return False


# ---- test 1: lower small AST --------------------------------------------

def test_lower_small():
    prog = parse("let x := 5\nprint(x+3)")
    mod = lower_ast(prog)
    assert _has(mod, Const, value=5), "missing Const(5)"
    assert _has(mod, Const, value=3), "missing Const(3)"
    assert _has(mod, BinOp, op="+"), "missing BinOp(+)"
    assert _has(mod, Call, callee="print"), "missing Call(print)"


# ---- test 2: print_ir produces >=3 lines --------------------------------

def test_print_ir_lines():
    from hgly.ir import print_ir
    prog = parse("let x := 5\nprint(x+3)")
    out = print_ir(lower_ast(prog))
    assert out.count("\n") + 1 >= 3, f"print_ir too short: {out!r}"


# ---- test 3-5: valid programs (zero errors except known unbound idents) -

def _check(src: str):
    return TypeChecker(lower_ast(parse(src))).check()


def test_valid_arith():
    errs = _check("let a := 1\nlet b := 2\nlet c := a + b")
    assert not any(e.kind == "type-mismatch" for e in errs), errs


def test_valid_print():
    errs = _check('print("hello")')
    assert not any(e.kind == "effect-violation" for e in errs), errs


def test_valid_float():
    errs = _check("let x := 1.5\nlet y := x * 2.0")
    assert not any(e.kind == "type-mismatch" for e in errs), errs


# ---- test 6: invalid programs ------------------------------------------

def test_invalid_use_before_bind():
    # build IR manually with use-before-bind
    fn = Function(name="__main__", effect=Effect.IO)
    blk = Block("entry")
    blk.ops.append(BinOp(dest_var="%2", args=["+", "%X", "%Y"], loc=(3, 1)))
    blk.ops.append(Return(loc=(4, 1)))
    fn.blocks.append(blk)
    mod = Module(main=fn)
    errs = TypeChecker(mod).check()
    use = [e for e in errs if e.kind == "use-before-bind"]
    assert use, f"expected use-before-bind, got {errs}"
    assert use[0].line == 3, use


def test_invalid_int_plus_str():
    # int + str via crafted IR (parser would coerce)
    fn = Function(name="__main__", effect=Effect.IO)
    fn.locals = {"%0": TInt(), "%1": TStr()}
    blk = Block("entry")
    blk.ops.append(Const(dest_var="%0", args=[5], loc=(1, 1), ty=TInt()))
    blk.ops.append(Const(dest_var="%1", args=["hi"], loc=(2, 1), ty=TStr()))
    blk.ops.append(BinOp(dest_var="%2", args=["+", "%0", "%1"], loc=(3, 1)))
    blk.ops.append(Return(loc=(4, 1)))
    fn.blocks.append(blk)
    mod = Module(main=fn)
    errs = TypeChecker(mod).check()
    tm = [e for e in errs if e.kind == "type-mismatch"]
    assert tm, f"expected type-mismatch, got {errs}"
    assert tm[0].line == 3


def test_invalid_linear_reuse():
    fn = Function(name="__main__", effect=Effect.KERNEL)
    fn.locals = {"%h": TLinear(TInt()), "%a": TInt(), "%b": TInt()}
    blk = Block("entry")
    blk.ops.append(Const(dest_var="%h", args=[0], loc=(1, 1), ty=TLinear(TInt())))
    blk.ops.append(Const(dest_var="%a", args=[1], loc=(2, 1), ty=TInt()))
    blk.ops.append(Const(dest_var="%b", args=[2], loc=(3, 1), ty=TInt()))
    blk.ops.append(Call(dest_var="%r1", args=["use_handle", "%h"], loc=(4, 1)))
    blk.ops.append(Call(dest_var="%r2", args=["use_handle", "%h"], loc=(5, 1)))
    blk.ops.append(Return(loc=(6, 1)))
    fn.blocks.append(blk)
    mod = Module(main=fn)
    errs = TypeChecker(mod).check()
    lr = [e for e in errs if e.kind == "linear-reuse"]
    assert lr, f"expected linear-reuse, got {errs}"
    assert lr[0].line == 5, lr


def test_invalid_pure_calls_io():
    # build IR: pure fn calls print (IO)
    pure_fn = Function(name="pure_fn", effect=Effect.PURE, ret=TUnit())
    blk = Block("entry")
    blk.ops.append(Const(dest_var="%0", args=["x"], loc=(2, 1), ty=TStr()))
    blk.ops.append(Call(dest_var="%1", args=["print", "%0"],
                        effect=Effect.IO, loc=(3, 1)))
    blk.ops.append(Return(loc=(4, 1)))
    pure_fn.blocks.append(blk)
    pure_fn.locals = {"%0": TStr()}
    main = Function(name="__main__", effect=Effect.IO)
    main.blocks.append(Block("entry", [Return(loc=(0, 0))]))
    mod = Module(functions=[pure_fn], main=main)
    errs = TypeChecker(mod).check()
    ev = [e for e in errs if e.kind == "effect-violation"]
    assert ev, f"expected effect-violation, got {errs}"
    assert ev[0].line == 3


def test_invalid_return_type_mismatch():
    fn = Function(name="adder", effect=Effect.PURE, ret=TInt())
    fn.locals = {"%0": TStr()}
    blk = Block("entry")
    blk.ops.append(Const(dest_var="%0", args=["nope"], loc=(2, 1), ty=TStr()))
    blk.ops.append(Return(args=["%0"], loc=(3, 1), ty=TStr()))
    fn.blocks.append(blk)
    main = Function(name="__main__", effect=Effect.IO)
    main.blocks.append(Block("entry", [Return(loc=(0, 0))]))
    mod = Module(functions=[fn], main=main)
    errs = TypeChecker(mod).check()
    rm = [e for e in errs if e.kind == "return-type-mismatch"]
    assert rm, f"expected return-type-mismatch, got {errs}"
    assert rm[0].line == 3


# ---- runner --------------------------------------------------------------

TESTS = [
    test_lower_small, test_print_ir_lines, test_valid_arith,
    test_valid_print, test_valid_float, test_invalid_use_before_bind,
    test_invalid_int_plus_str, test_invalid_linear_reuse,
    test_invalid_pure_calls_io, test_invalid_return_type_mismatch,
]


def main() -> int:
    passed = 0; failed = 0
    for t in TESTS:
        try:
            t(); passed += 1
            print(f"PASS {t.__name__}")
        except Exception:
            failed += 1
            print(f"FAIL {t.__name__}")
            traceback.print_exc()
    print(f"\n{passed}/{len(TESTS)} passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
