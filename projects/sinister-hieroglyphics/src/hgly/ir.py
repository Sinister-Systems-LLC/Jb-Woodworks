"""hgly typed SSA IR.

Author: RKOJ-ELENO :: 2026-05-25
Phase 3 bootstrap. Row-polymorphic structural types + linear-type tracking
for hardware resources + effect annotations (PURE/IO/KERNEL/GPU).
Codegen backends (Phase 4-6) consume Module produced by lower_ast().
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from . import ast as A


# ----- types --------------------------------------------------------------

class Effect(Enum):
    PURE = "pure"; IO = "io"; KERNEL = "kernel"; GPU = "gpu"


@dataclass(frozen=True)
class Type: pass
@dataclass(frozen=True)
class TInt(Type):
    bits: int = 64
    def __repr__(self) -> str: return f"i{self.bits}"
@dataclass(frozen=True)
class TFloat(Type):
    bits: int = 64
    def __repr__(self) -> str: return f"f{self.bits}"
@dataclass(frozen=True)
class TBool(Type):
    def __repr__(self) -> str: return "bool"
@dataclass(frozen=True)
class TStr(Type):
    def __repr__(self) -> str: return "str"
@dataclass(frozen=True)
class TUnit(Type):
    def __repr__(self) -> str: return "()"
@dataclass(frozen=True)
class TList(Type):
    elem: Type = field(default_factory=TUnit)
    def __repr__(self) -> str: return f"[{self.elem!r}]"
@dataclass(frozen=True)
class TTuple(Type):
    elems: Tuple[Type, ...] = ()
    def __repr__(self) -> str: return "(" + ",".join(repr(e) for e in self.elems) + ")"
@dataclass(frozen=True)
class TStruct(Type):
    fields: Tuple[Tuple[str, Type], ...] = ()  # row-polymorphic: structural
    def __repr__(self) -> str: return "{" + ",".join(f"{n}:{t!r}" for n, t in self.fields) + "}"
@dataclass(frozen=True)
class TFn(Type):
    params: Tuple[Type, ...] = ()
    ret: Type = field(default_factory=TUnit)
    effect: Effect = Effect.PURE
    def __repr__(self) -> str:
        return f"fn({','.join(repr(p) for p in self.params)})->{self.ret!r}@{self.effect.value}"
@dataclass(frozen=True)
class TPtr(Type):
    elem: Type = field(default_factory=TUnit)
    def __repr__(self) -> str: return f"*{self.elem!r}"
@dataclass(frozen=True)
class TLinear(Type):
    inner: Type = field(default_factory=TUnit)
    def __repr__(self) -> str: return f"!{self.inner!r}"


def _is_numeric(t: Type) -> bool: return isinstance(t, (TInt, TFloat))


# ----- IR ops -------------------------------------------------------------

@dataclass
class IROp:
    dest_var: Optional[str] = None
    args: List[Any] = field(default_factory=list)
    effect: Effect = Effect.PURE
    loc: Tuple[int, int] = (0, 0)
    ty: Optional[Type] = None

@dataclass
class Const(IROp): kind: str = "const"
@dataclass
class Bind(IROp): kind: str = "bind"
@dataclass
class Call(IROp): kind: str = "call"  # args=[callee_name, *arg_vars]
@dataclass
class BranchIf(IROp): kind: str = "br_if"
@dataclass
class Jump(IROp): kind: str = "jmp"
@dataclass
class Return(IROp): kind: str = "ret"
@dataclass
class Phi(IROp): kind: str = "phi"
@dataclass
class Alloc(IROp): kind: str = "alloc"
@dataclass
class Load(IROp): kind: str = "load"
@dataclass
class Store(IROp): kind: str = "store"
@dataclass
class BinOp(IROp): kind: str = "binop"  # args=[op, lhs, rhs]
@dataclass
class UnaryOp(IROp): kind: str = "unop"  # args=[op, operand]


@dataclass
class Block:
    label: str = "entry"
    ops: List[IROp] = field(default_factory=list)

@dataclass
class Function:
    name: str = ""
    params: List[Tuple[str, Type]] = field(default_factory=list)
    ret: Type = field(default_factory=TUnit)
    effect: Effect = Effect.PURE
    locals: Dict[str, Type] = field(default_factory=dict)
    blocks: List[Block] = field(default_factory=list)

@dataclass
class Module:
    functions: List[Function] = field(default_factory=list)
    main: Function = field(default_factory=Function)


# ----- AST -> IR lowering -------------------------------------------------

class _Lower:
    def __init__(self) -> None:
        self.counter = 0
        self.module = Module()
        self.main = Function(name="__main__", effect=Effect.IO)
        self.main.blocks.append(Block("entry"))
        self.module.main = self.main
        self.cur_fn = self.main
        self.env: Dict[str, str] = {}

    def fresh(self) -> str:
        v = f"%{self.counter}"; self.counter += 1; return v

    def emit(self, op: IROp) -> None: self.cur_fn.blocks[-1].ops.append(op)

    def lower_program(self, prog: A.Program) -> Module:
        for s in prog.stmts: self.lower_stmt(s)
        last = self.cur_fn.blocks[-1]
        if not last.ops or not isinstance(last.ops[-1], Return):
            self.emit(Return(loc=(0, 0)))
        return self.module

    def lower_stmt(self, n: A.Node) -> Optional[str]:
        if isinstance(n, A.Bind):
            v = self.lower_expr(n.value) if n.value else self.fresh()
            ty = self.cur_fn.locals.get(v, TUnit())
            self.env[n.name] = v
            self.cur_fn.locals[n.name] = ty
            self.cur_fn.locals.setdefault(v, ty)
            return v
        if isinstance(n, A.FnDecl):
            fn = Function(name=n.name, effect=Effect.PURE,
                          params=[(p, TInt()) for p in n.params])
            fn.blocks.append(Block("entry"))
            saved_fn, saved_env = self.cur_fn, dict(self.env)
            self.cur_fn = fn; self.env = {p: f"%p{i}" for i, p in enumerate(n.params)}
            for p, v in self.env.items():
                fn.locals[v] = TInt(); fn.locals[p] = TInt()
            if n.body:
                for s in n.body.stmts: self.lower_stmt(s)
            if not fn.blocks[-1].ops or not isinstance(fn.blocks[-1].ops[-1], Return):
                fn.blocks[-1].ops.append(Return(loc=(n.line, n.col)))
            self.module.functions.append(fn)
            self.cur_fn, self.env = saved_fn, saved_env
            return None
        if isinstance(n, A.Return):
            val = self.lower_expr(n.value) if n.value else None
            ret_ty = self.cur_fn.locals.get(val, TUnit()) if val else TUnit()
            self.cur_fn.ret = ret_ty
            self.emit(Return(args=[val] if val else [], loc=(n.line, n.col), ty=ret_ty))
            return None
        return self.lower_expr(n)

    def lower_expr(self, n: A.Node) -> str:
        if isinstance(n, A.Literal):
            v = self.fresh()
            ty: Type = ({"int": TInt(), "float": TFloat(), "bool": TBool(),
                         "str": TStr()}).get(n.ltype, TUnit())
            self.cur_fn.locals[v] = ty
            self.emit(Const(dest_var=v, args=[n.value], loc=(n.line, n.col), ty=ty))
            return v
        if isinstance(n, A.Ident):
            if n.name in self.env: return self.env[n.name]
            v = self.fresh(); self.cur_fn.locals[v] = TUnit()
            self.emit(Load(dest_var=v, args=[n.name], loc=(n.line, n.col), ty=TUnit()))
            return v
        if isinstance(n, A.BinOp):
            lhs = self.lower_expr(n.lhs); rhs = self.lower_expr(n.rhs)
            v = self.fresh()
            lt = self.cur_fn.locals.get(lhs, TUnit())
            rt = self.cur_fn.locals.get(rhs, TUnit())
            res = lt if isinstance(lt, (TInt, TFloat)) else rt
            if n.op in ("==", "!=", "<", ">", "<=", ">=", "&&", "||"): res = TBool()
            self.cur_fn.locals[v] = res
            self.emit(BinOp(dest_var=v, args=[n.op, lhs, rhs], loc=(n.line, n.col), ty=res))
            return v
        if isinstance(n, A.UnaryOp):
            o = self.lower_expr(n.operand); v = self.fresh()
            self.cur_fn.locals[v] = self.cur_fn.locals.get(o, TUnit())
            self.emit(UnaryOp(dest_var=v, args=[n.op, o], loc=(n.line, n.col),
                              ty=self.cur_fn.locals[v]))
            return v
        if isinstance(n, A.Call):
            callee = n.callee.name if isinstance(n.callee, A.Ident) else "<lambda>"
            arg_vars = [self.lower_expr(a) for a in n.args]
            v = self.fresh()
            eff = Effect.IO if callee in ("print", "println", "read", "write") else Effect.PURE
            self.cur_fn.locals[v] = TUnit()
            self.emit(Call(dest_var=v, args=[callee, *arg_vars],
                           effect=eff, loc=(n.line, n.col), ty=TUnit()))
            return v
        v = self.fresh(); self.cur_fn.locals[v] = TUnit()
        self.emit(Const(dest_var=v, args=[None],
                        loc=(getattr(n, "line", 0), getattr(n, "col", 0)), ty=TUnit()))
        return v


def lower_ast(prog: A.Program) -> Module: return _Lower().lower_program(prog)


# ----- type checker -------------------------------------------------------

@dataclass
class TypeError_:
    kind: str; msg: str; line: int = 0; col: int = 0
    def __repr__(self) -> str: return f"<TypeError {self.kind} {self.msg} L{self.line}C{self.col}>"


TypeError = TypeError_  # operator-facing alias

_IO_BUILTINS = {"print", "println", "read", "write", "input", "fopen", "fwrite"}
_KERNEL_BUILTINS = {"syscall", "ioctl", "mmap"}
_GPU_BUILTINS = {"gpu_launch", "gpu_copy"}
_ARITH_OPS = {"+", "-", "*", "/", "%"}
_CMP_OPS = {"==", "!=", "<", ">", "<=", ">="}


class TypeChecker:
    def __init__(self, module: Module) -> None:
        self.module = module; self.errors: List[TypeError_] = []

    def check(self) -> List[TypeError_]:
        fns = list(self.module.functions) + [self.module.main]
        self.sigs: Dict[str, Tuple[List[Type], Type, Effect]] = {
            f.name: ([t for _, t in f.params], f.ret, f.effect) for f in fns}
        for f in fns: self._check_fn(f)
        return self.errors

    def _err(self, kind: str, msg: str, loc: Tuple[int, int]) -> None:
        self.errors.append(TypeError_(kind, msg, loc[0], loc[1]))

    def _call_effect(self, callee: str, op_eff: Effect) -> Effect:
        if callee in _IO_BUILTINS: return Effect.IO
        if callee in _KERNEL_BUILTINS: return Effect.KERNEL
        if callee in _GPU_BUILTINS: return Effect.GPU
        if callee in self.sigs: return self.sigs[callee][2]
        return op_eff

    def _check_fn(self, fn: Function) -> None:
        defined: set = {p for p, _ in fn.params} | {f"%p{i}" for i in range(len(fn.params))}
        linear_used: Dict[str, int] = {}
        for blk in fn.blocks:
            for op in blk.ops:
                if isinstance(op, BinOp):
                    o, lhs, rhs = op.args
                    for u in (lhs, rhs):
                        if u not in defined and u not in fn.locals:
                            self._err("use-before-bind", f"var {u} used before bind", op.loc)
                    lt = fn.locals.get(lhs, TUnit()); rt = fn.locals.get(rhs, TUnit())
                    if o in _ARITH_OPS:
                        if not (_is_numeric(lt) and _is_numeric(rt)):
                            self._err("type-mismatch",
                                      f"binop {o} needs numerics, got {lt!r} {rt!r}", op.loc)
                        elif type(lt) is not type(rt):
                            self._err("type-mismatch",
                                      f"binop {o} mismatch: {lt!r} vs {rt!r}", op.loc)
                    elif o in _CMP_OPS:
                        if type(lt) is not type(rt) and not (_is_numeric(lt) and _is_numeric(rt)):
                            self._err("type-mismatch",
                                      f"cmp {o} mismatch: {lt!r} vs {rt!r}", op.loc)
                if isinstance(op, Call):
                    call_eff = self._call_effect(op.args[0], op.effect)
                    if fn.effect == Effect.PURE and call_eff != Effect.PURE:
                        self._err("effect-violation",
                                  f"pure fn {fn.name!r} cannot call {call_eff.value} "
                                  f"{op.args[0]!r}", op.loc)
                    for a in op.args[1:]:
                        if a not in defined and a not in fn.locals:
                            self._err("use-before-bind", f"arg {a} used before bind", op.loc)
                if isinstance(op, Return) and op.args:
                    rv = op.args[0]
                    if rv not in defined and rv not in fn.locals:
                        self._err("use-before-bind", f"ret {rv} used before bind", op.loc)
                    rt = fn.locals.get(rv, TUnit())
                    if not isinstance(fn.ret, TUnit) and type(rt) is not type(fn.ret):
                        self._err("return-type-mismatch",
                                  f"return {rt!r} but fn declares {fn.ret!r}", op.loc)
                # linear-type tracking
                use_vars: List[str] = []
                if isinstance(op, BinOp): use_vars = [op.args[1], op.args[2]]
                elif isinstance(op, UnaryOp): use_vars = [op.args[1]]
                elif isinstance(op, Call): use_vars = list(op.args[1:])
                elif isinstance(op, Return): use_vars = list(op.args)
                elif isinstance(op, Store): use_vars = list(op.args)
                for u in use_vars:
                    if isinstance(fn.locals.get(u), TLinear):
                        linear_used[u] = linear_used.get(u, 0) + 1
                        if linear_used[u] > 1:
                            self._err("linear-reuse",
                                      f"linear var {u} used {linear_used[u]} times", op.loc)
                if op.dest_var: defined.add(op.dest_var)
        for v, t in fn.locals.items():
            if isinstance(t, TLinear) and linear_used.get(v, 0) == 0 and v.startswith("%"):
                self._err("linear-leak", f"linear var {v} never consumed", (0, 0))


# ----- pretty printer -----------------------------------------------------

def print_ir(module: Module) -> str:
    lines: List[str] = []
    for fn in list(module.functions) + [module.main]:
        params = ", ".join(f"{n}:{t!r}" for n, t in fn.params)
        lines.append(f"fn {fn.name}({params}) -> {fn.ret!r} @{fn.effect.value} {{")
        for blk in fn.blocks:
            lines.append(f"  {blk.label}:")
            for op in blk.ops:
                d = f"{op.dest_var} = " if op.dest_var else ""
                a = " ".join(str(x) for x in op.args)
                ty = f" : {op.ty!r}" if op.ty is not None else ""
                lines.append(f"    {d}{op.kind} {a}{ty}  ; @{op.effect.value} L{op.loc[0]}")
        lines.append("}")
    return "\n".join(lines)
