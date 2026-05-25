"""hgly Phase 4 codegen stub.

Author: RKOJ-ELENO :: 2026-05-25

Lowers typed-SSA IR (hgly.ir.Module) to a stack-machine bytecode plus a
tiny tree-shaken VM that executes it. This is the bootstrap path before
real native codegen (Cranelift x86_64 / LLVM / PTX) lands in Phase 4b-6.

Goals (per master plan):
- Demonstrate a full source -> AST -> IR -> bytecode -> output pipeline.
- Match the tree-walking interpreter's observable output on simple programs.
- Tiny + stdlib-only so the trainer (hgly_trainer.py) can use it as an
  eval reference without dragging in heavy deps.

Bytecode instruction set (12 ops):
- PUSH_CONST <val>           push literal
- LOAD <name>                push value of named local
- STORE <name>               pop, bind local
- BINOP <op>                 pop rhs, lhs; push lhs <op> rhs
- UNOP <op>                  pop operand; push <op> operand
- CALL <name> <argc>         pop argc args; invoke builtin/fn; push result
- JMP <offset>               unconditional jump (relative)
- JMP_IF_FALSE <offset>      pop; jump if falsy
- POP                        discard top
- RET                        return top of stack
- HALT                       stop VM
- NOP                        no-op padding (debugger anchor)
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from . import ir as I


# ----- bytecode types -----------------------------------------------------

@dataclass
class Instr:
    op: str
    args: tuple = ()
    loc: tuple = (0, 0)

    def __repr__(self) -> str:
        return f"{self.op}({', '.join(map(repr, self.args))})"


@dataclass
class CompiledFn:
    name: str = "__main__"
    params: List[str] = field(default_factory=list)
    code: List[Instr] = field(default_factory=list)


@dataclass
class CompiledModule:
    main: CompiledFn = field(default_factory=CompiledFn)
    fns: Dict[str, CompiledFn] = field(default_factory=dict)


# ----- IR -> bytecode -----------------------------------------------------

def _emit_const(code: List[Instr], v: Any, loc: tuple) -> None:
    code.append(Instr("PUSH_CONST", (v,), loc))


def _compile_fn(fn: I.Function) -> CompiledFn:
    out = CompiledFn(name=fn.name, params=[p[0] for p in fn.params])
    code = out.code
    for block in fn.blocks:
        for op in block.ops:
            if isinstance(op, I.Const):
                _emit_const(code, op.args[0], op.loc)
                if op.dest_var:
                    code.append(Instr("STORE", (op.dest_var,), op.loc))
            elif isinstance(op, I.Load):
                code.append(Instr("LOAD", (op.args[0],), op.loc))
                if op.dest_var:
                    code.append(Instr("STORE", (op.dest_var,), op.loc))
            elif isinstance(op, I.BinOp):
                _, lhs, rhs = op.args
                code.append(Instr("LOAD", (lhs,), op.loc))
                code.append(Instr("LOAD", (rhs,), op.loc))
                code.append(Instr("BINOP", (op.args[0],), op.loc))
                if op.dest_var:
                    code.append(Instr("STORE", (op.dest_var,), op.loc))
            elif isinstance(op, I.UnaryOp):
                _, operand = op.args
                code.append(Instr("LOAD", (operand,), op.loc))
                code.append(Instr("UNOP", (op.args[0],), op.loc))
                if op.dest_var:
                    code.append(Instr("STORE", (op.dest_var,), op.loc))
            elif isinstance(op, I.Call):
                callee = op.args[0]
                argv = op.args[1:]
                for a in argv:
                    code.append(Instr("LOAD", (a,), op.loc))
                code.append(Instr("CALL", (callee, len(argv)), op.loc))
                if op.dest_var:
                    code.append(Instr("STORE", (op.dest_var,), op.loc))
            elif isinstance(op, I.Return):
                if op.args:
                    code.append(Instr("LOAD", (op.args[0],), op.loc))
                else:
                    _emit_const(code, None, op.loc)
                code.append(Instr("RET", (), op.loc))
    if not code or code[-1].op != "RET":
        _emit_const(code, None, (0, 0))
        code.append(Instr("RET", (), (0, 0)))
    return out


def compile_module(mod: I.Module) -> CompiledModule:
    out = CompiledModule(main=_compile_fn(mod.main))
    for fn in mod.functions:
        out.fns[fn.name] = _compile_fn(fn)
    return out


# ----- VM -----------------------------------------------------------------

def _builtin_print(*args: Any) -> None:
    print(*[str(a) if a is not None else "nil" for a in args])


def _builtin_println(*args: Any) -> None:
    print(*[str(a) if a is not None else "nil" for a in args])


def _builtin_len(x: Any) -> int:
    try:
        return len(x)
    except Exception:
        return 0


def _builtin_int(x: Any) -> int:
    try:
        return int(x)
    except Exception:
        return 0


def _builtin_str(x: Any) -> str:
    return "nil" if x is None else str(x)


def _builtin_panic(msg: Any = "panic") -> None:
    raise RuntimeError(f"hgly panic: {msg}")


_BUILTINS: Dict[str, Callable[..., Any]] = {
    "print": _builtin_print,
    "println": _builtin_println,
    "len": _builtin_len,
    "int": _builtin_int,
    "str": _builtin_str,
    "panic": _builtin_panic,
}


def _binop(op: str, a: Any, b: Any) -> Any:
    try:
        if op == "+":
            if isinstance(a, str) or isinstance(b, str):
                return str(a) + str(b)
            return (a or 0) + (b or 0)
        if op == "-": return (a or 0) - (b or 0)
        if op == "*": return (a or 0) * (b or 0)
        if op == "/":
            if not b: return 0
            if isinstance(a, int) and isinstance(b, int): return a // b
            return a / b
        if op == "%":
            return (a or 0) % (b or 1) if b else 0
        if op in ("&&", "and"): return bool(a) and bool(b)
        if op in ("||", "or"): return bool(a) or bool(b)
        if op == "==": return a == b
        if op == "!=": return a != b
        if op == "<": return (a or 0) < (b or 0)
        if op == ">": return (a or 0) > (b or 0)
        if op == "<=": return (a or 0) <= (b or 0)
        if op == ">=": return (a or 0) >= (b or 0)
    except Exception:
        return 0
    return 0


def _unop(op: str, a: Any) -> Any:
    if op == "-":
        try: return -(a or 0)
        except Exception: return 0
    if op == "!":
        return not bool(a)
    return a


class VM:
    """Tiny stack VM. exec_module() returns the main return value (or 0)."""

    def __init__(self) -> None:
        self.stack: List[Any] = []
        self.locals: Dict[str, Any] = {}
        self.module: Optional[CompiledModule] = None

    def exec_module(self, mod: CompiledModule) -> Any:
        self.module = mod
        try:
            return self._exec_fn(mod.main, [])
        except RuntimeError:
            return 134  # panic exit code (matches interpreter)

    def _exec_fn(self, fn: CompiledFn, args: List[Any]) -> Any:
        saved_locals = self.locals
        self.locals = {p: a for p, a in zip(fn.params, args)}
        try:
            pc = 0
            while pc < len(fn.code):
                ins = fn.code[pc]
                op = ins.op
                if op == "PUSH_CONST":
                    self.stack.append(ins.args[0])
                elif op == "LOAD":
                    self.stack.append(self.locals.get(ins.args[0], 0))
                elif op == "STORE":
                    self.locals[ins.args[0]] = self.stack.pop() if self.stack else 0
                elif op == "BINOP":
                    b = self.stack.pop() if self.stack else 0
                    a = self.stack.pop() if self.stack else 0
                    self.stack.append(_binop(ins.args[0], a, b))
                elif op == "UNOP":
                    a = self.stack.pop() if self.stack else 0
                    self.stack.append(_unop(ins.args[0], a))
                elif op == "CALL":
                    callee, argc = ins.args
                    call_args = []
                    for _ in range(argc):
                        call_args.append(self.stack.pop() if self.stack else 0)
                    call_args.reverse()
                    if callee in _BUILTINS:
                        try:
                            r = _BUILTINS[callee](*call_args)
                        except RuntimeError:
                            raise
                        self.stack.append(r)
                    elif self.module and callee in self.module.fns:
                        r = self._exec_fn(self.module.fns[callee], call_args)
                        self.stack.append(r)
                    else:
                        self.stack.append(0)  # lenient: unknown call -> 0
                elif op == "POP":
                    if self.stack: self.stack.pop()
                elif op == "JMP":
                    pc += ins.args[0]; continue
                elif op == "JMP_IF_FALSE":
                    v = self.stack.pop() if self.stack else False
                    if not v: pc += ins.args[0]; continue
                elif op == "RET":
                    return self.stack.pop() if self.stack else None
                elif op == "HALT":
                    return None
                pc += 1
            return self.stack.pop() if self.stack else None
        finally:
            self.locals = saved_locals


def compile_and_run(src: str) -> Any:
    """Convenience: source -> ast -> ir -> bytecode -> run. Returns main rv."""
    from . import parse
    prog = parse(src)
    mod = I.lower_ast(prog)
    cm = compile_module(mod)
    return VM().exec_module(cm)


def dump(cm: CompiledModule) -> str:
    """Human-readable disassembly."""
    out = []
    out.append(f"; module: main ({len(cm.main.code)} instr) + {len(cm.fns)} fns")
    out.append(f"fn {cm.main.name}:")
    for i, ins in enumerate(cm.main.code):
        out.append(f"  {i:3d}  {ins.op}{' ' + ' '.join(map(repr, ins.args)) if ins.args else ''}")
    for name, f in cm.fns.items():
        out.append(f"fn {name}({', '.join(f.params)}):")
        for i, ins in enumerate(f.code):
            out.append(f"  {i:3d}  {ins.op}{' ' + ' '.join(map(repr, ins.args)) if ins.args else ''}")
    return "\n".join(out)
