"""hgly tree-walking interpreter — reference semantics for Sinister Hieroglyphics.

Author: RKOJ-ELENO :: 2026-05-25
Phase 2 bootstrap. Lock semantics here BEFORE Phase 3-7 codegen targets ship.
Stdlib only. API: Interpreter(stdout,stderr).run(prog,args)->int / .eval(node)
/ .env. HglyPanic from panic()/assert() => exit 134. i64 wrap on int ops.
Lenient mode: unbound idents -> zero-stub; non-callable call -> 0; arith
coerces non-numerics to 0 (lets corpus run despite unimplemented intrinsics).
"""
from __future__ import annotations
import sys
from typing import Any, Callable, Dict, List, Optional

from .ast import (Bind, BinOp, Block, Break, Call, FnDecl, Ident, If, Lambda,
                  Literal, Loop, Match, Node, Program, Return, UnaryOp)

_I64_MAX = (1 << 63) - 1
_I64_MASK = (1 << 64) - 1


def _wrap_i64(v: Any) -> Any:
    if not isinstance(v, int) or isinstance(v, bool): return v
    w = v & _I64_MASK
    return w - (1 << 64) if w > _I64_MAX else w


class HglyPanic(Exception):
    """Raised by panic()/failed assert(); run() returns 134."""
    def __init__(self, msg: str) -> None:
        super().__init__(msg); self.msg = msg

class _BreakSignal(Exception): pass

class _ReturnSignal(Exception):
    def __init__(self, value: Any) -> None: self.value = value

class Environment:
    """Chained-scope environment supporting let/cst/fn bindings."""
    def __init__(self, parent: Optional["Environment"] = None) -> None:
        self.parent = parent
        self.vars: Dict[str, Any] = {}
        self.consts: set = set()

    def define(self, name: str, value: Any, constant: bool = False) -> None:
        self.vars[name] = value
        if constant: self.consts.add(name)

    def get(self, name: str) -> Any:
        e: Optional[Environment] = self
        while e is not None:
            if name in e.vars: return e.vars[name]
            e = e.parent
        raise NameError(f"unbound identifier: {name}")

    def assign(self, name: str, value: Any) -> None:
        e: Optional[Environment] = self
        while e is not None:
            if name in e.vars:
                if name in e.consts:
                    raise HglyPanic(f"cannot reassign constant '{name}'")
                e.vars[name] = value; return
            e = e.parent
        self.vars[name] = value

class Closure:
    """First-class function. Captures env at definition time."""
    def __init__(self, params: List[str], body: Block, env: Environment,
                 name: str = "<lambda>") -> None:
        self.params = params; self.body = body; self.env = env; self.name = name

    def __repr__(self) -> str:
        return f"<fn {self.name}({','.join(self.params)})>"

def _stringify(v: Any) -> str:
    if v is None: return "nil"
    if isinstance(v, bool): return "true" if v else "false"
    if isinstance(v, float):
        return f"{v:.1f}" if v.is_integer() else repr(v)
    return str(v)

def _truthy(v: Any) -> bool:
    if v is None or v is False: return False
    if isinstance(v, (int, float)) and v == 0: return False
    if isinstance(v, str) and v == "": return False
    return True

def _coerce_num(v: Any) -> Any:
    """Non-numeric → 0 (lenient mode for corpus parse-ambiguities)."""
    if isinstance(v, bool): return 1 if v else 0
    if isinstance(v, (int, float)): return v
    if v is None or isinstance(v, Closure) or callable(v): return 0
    return v

class Interpreter:
    """Tree-walking interpreter for hgly Programs."""
    def __init__(self, stdout=None, stderr=None) -> None:
        self.stdout = stdout if stdout is not None else sys.stdout
        self.stderr = stderr if stderr is not None else sys.stderr
        self.env = Environment()
        self._install_builtins()

    def _install_builtins(self) -> None:
        def _print(*a: Any) -> Any:
            self.stdout.write(" ".join(_stringify(x) for x in a))
            try: self.stdout.flush()
            except Exception: pass

        def _println(*a: Any) -> Any:
            self.stdout.write(" ".join(_stringify(x) for x in a) + "\n")
            try: self.stdout.flush()
            except Exception: pass

        def _len(x: Any) -> int:
            try: return len(x)
            except TypeError: raise HglyPanic(f"len() not supported on {type(x).__name__}")

        def _panic(msg: Any = "") -> Any: raise HglyPanic(_stringify(msg))

        def _assert(cond: Any, msg: Any = "assertion failed") -> Any:
            if not _truthy(cond): raise HglyPanic(_stringify(msg))

        def _stub(*_a: Any, **_k: Any) -> int: return 0  # corpus intrinsic stub

        for nm in ("wr", "rd", "opn", "cls", "alc", "fre", "sys", "mutex", "lck",
                   "ulk", "chan", "fnc", "cas", "gpu", "awt", "yld"):
            self.env.define(nm, _stub)
        for nm, fn in (("print", _print), ("println", _println), ("len", _len),
                       ("range", lambda *a: list(range(*[int(x) for x in a]))),
                       ("int", int), ("str", _stringify),
                       ("panic", _panic), ("assert", _assert)):
            self.env.define(nm, fn, constant=True)
        # RKOJ-ELENO :: 2026-05-25 (iter-15) :: wire Phase-8 sim primitives so
        # corpus simulation-pipeline.shp programs run with REAL semantics
        # instead of zero-stubs. World is module-singleton via get_world().
        # Operator-aligned with desktop python_simulator quantum-systems sim.
        try:
            from .sim import builtins as _sim_builtins
            for nm, fn in _sim_builtins().items():
                # Don't clobber prior bindings (e.g. _stub) -- override deliberately
                # so the 8 sim ops + 8 ASCII aliases get REAL implementations.
                self.env.define(nm, fn, constant=False)
        except Exception:
            pass  # sim is optional; corpus still parses + interpreter runs without
        # RKOJ-ELENO :: 2026-05-25 (iter-17) :: Phase 8b bridge to the desktop
        # python_simulator (ZMQ quantum server). Same pattern as sim wiring.
        try:
            from .bridge_python_sim import builtins as _qsim_builtins
            for nm, fn in _qsim_builtins().items():
                self.env.define(nm, fn, constant=False)
        except Exception:
            pass

    def run(self, prog: Program, args: Optional[List[str]] = None) -> int:
        self.env.define("argv", list(args or []))
        try:
            for stmt in prog.stmts: self.eval(stmt)
            return 0
        except HglyPanic as e:
            try: self.stderr.write(f"panic: {e.msg}\n")
            except Exception: pass
            return 134
        except _ReturnSignal: return 0

    def eval(self, node: Optional[Node]) -> Any:
        if node is None: return None
        m = _DISPATCH.get(type(node))
        if m is None: raise HglyPanic(f"unhandled AST node: {type(node).__name__}")
        return m(self, node)

    def _eval_block(self, blk: Block, env: Optional[Environment] = None) -> Any:
        prev = self.env
        self.env = Environment(prev) if env is None else env
        try:
            last: Any = None
            for s in blk.stmts: last = self.eval(s)
            return last
        finally: self.env = prev

    def _call(self, callee: Any, args: List[Any]) -> Any:
        if isinstance(callee, Closure):
            ce = Environment(callee.env)
            for i, p in enumerate(callee.params):
                ce.define(p, args[i] if i < len(args) else None)
            try: return self._eval_block(callee.body, ce)
            except _ReturnSignal as r: return r.value
        if callable(callee): return callee(*args)
        return 0  # lenient: non-callable call → 0


# ---------- per-node visitors ----------
def _ev_literal(it: Interpreter, n: Literal) -> Any: return n.value


def _ev_ident(it: Interpreter, n: Ident) -> Any:
    """Unbound idents → zero-stub (lenient: lets corpus call intrinsics)."""
    try: return it.env.get(n.name)
    except NameError:
        return lambda *_a, **_k: 0


def _ev_binop(it: Interpreter, n: BinOp) -> Any:
    op = n.op
    if op == "&&":
        l = it.eval(n.lhs); return l if not _truthy(l) else it.eval(n.rhs)
    if op == "||":
        l = it.eval(n.lhs); return l if _truthy(l) else it.eval(n.rhs)
    a = it.eval(n.lhs); b = it.eval(n.rhs)
    if op == "+":
        if isinstance(a, str) or isinstance(b, str):
            return _stringify(a) + _stringify(b)
        a, b = _coerce_num(a), _coerce_num(b); r = a + b
    elif op in ("-", "*", "/", "%"):
        a, b = _coerce_num(a), _coerce_num(b)
        if op == "-": r = a - b
        elif op == "*": r = a * b
        elif op == "/":
            if b == 0: raise HglyPanic("division by zero")
            r = a // b if isinstance(a, int) and isinstance(b, int) else a / b
        else:
            if b == 0: raise HglyPanic("modulo by zero")
            r = a % b
    elif op == "==": return a == b
    elif op == "!=": return a != b
    elif op == "<":  return a < b
    elif op == ">":  return a > b
    elif op == "<=": return a <= b
    elif op == ">=": return a >= b
    else: raise HglyPanic(f"unknown binop {op}")
    return _wrap_i64(r) if isinstance(r, int) and not isinstance(r, bool) else r


def _ev_unop(it: Interpreter, n: UnaryOp) -> Any:
    v = it.eval(n.operand)
    if n.op == "!": return not _truthy(v)
    if n.op == "-": return _wrap_i64(-v) if isinstance(v, int) else -v
    raise HglyPanic(f"unknown unop {n.op}")


def _ev_call(it: Interpreter, n: Call) -> Any:
    return it._call(it.eval(n.callee), [it.eval(a) for a in n.args])


def _ev_block_node(it: Interpreter, n: Block) -> Any: return it._eval_block(n)


def _ev_bind(it: Interpreter, n: Bind) -> Any:
    v = it.eval(n.value); it.env.define(n.name, v, constant=n.constant); return v


def _ev_fndecl(it: Interpreter, n: FnDecl) -> Any:
    c = Closure(n.params, n.body, it.env, n.name)
    it.env.define(n.name, c); return c


def _ev_lambda(it: Interpreter, n: Lambda) -> Any:
    return Closure(n.params, n.body, it.env, "<lambda>")


def _ev_if(it: Interpreter, n: If) -> Any:
    if _truthy(it.eval(n.cond)): return it._eval_block(n.then_branch)
    if n.else_branch is None: return None
    if isinstance(n.else_branch, Block): return it._eval_block(n.else_branch)
    return it.eval(n.else_branch)


def _ev_match(it: Interpreter, n: Match) -> Any:
    scrut = it.eval(n.scrutinee)
    for pat, body in n.arms:
        if isinstance(pat, Ident) and pat.name == "_":
            return it._eval_block(body)
        try: pv = it.eval(pat)
        except HglyPanic: continue
        if pv == scrut: return it._eval_block(body)
    return None


def _ev_loop(it: Interpreter, n: Loop) -> Any:
    # for-desugar detection: first 2 stmts = induction Bind + __hgly_for_hi_ marker
    if (n.body and len(n.body.stmts) >= 2
            and isinstance(n.body.stmts[0], Bind)
            and isinstance(n.body.stmts[1], Bind)
            and n.body.stmts[1].name.startswith("__hgly_for_hi_")):
        var = n.body.stmts[0].name; hi_name = n.body.stmts[1].name
        lo = it.eval(n.body.stmts[0].value); hi = it.eval(n.body.stmts[1].value)
        env = Environment(it.env); env.define(var, lo); env.define(hi_name, hi, True)
        prev = it.env; it.env = env
        try:
            i = lo
            while i < hi:
                env.assign(var, i)
                try:
                    for s in n.body.stmts[2:]: it.eval(s)
                except _BreakSignal: return None
                i += 1
            return None
        finally: it.env = prev
    while True:
        try: it._eval_block(n.body)
        except _BreakSignal: return None


def _ev_break(it: Interpreter, n: Break) -> Any: raise _BreakSignal()


def _ev_return(it: Interpreter, n: Return) -> Any:
    raise _ReturnSignal(it.eval(n.value) if n.value is not None else None)


def _ev_program(it: Interpreter, n: Program) -> Any:
    last = None
    for s in n.stmts: last = it.eval(s)
    return last


_DISPATCH: Dict[type, Callable] = {
    Literal: _ev_literal, Ident: _ev_ident, BinOp: _ev_binop, UnaryOp: _ev_unop,
    Call: _ev_call, Block: _ev_block_node, Bind: _ev_bind, FnDecl: _ev_fndecl,
    Lambda: _ev_lambda, If: _ev_if, Match: _ev_match, Loop: _ev_loop,
    Break: _ev_break, Return: _ev_return, Program: _ev_program,
}
