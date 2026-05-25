"""hgly AST node dataclasses.

Author: RKOJ-ELENO :: 2026-05-25
Phase 2 bootstrap. Each node carries line/col of its lead token + to_dict().
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple


@dataclass
class Node:
    line: int = 0
    col: int = 0

    def to_dict(self) -> dict:
        d: dict[str, Any] = {"kind": type(self).__name__,
                             "line": self.line, "col": self.col}
        for k, v in self.__dict__.items():
            if k in ("line", "col"): continue
            d[k] = _serialize(v)
        return d


def _serialize(v: Any) -> Any:
    if isinstance(v, Node): return v.to_dict()
    if isinstance(v, (list, tuple)): return [_serialize(x) for x in v]
    if isinstance(v, dict): return {k: _serialize(x) for k, x in v.items()}
    return v


@dataclass
class Literal(Node):
    value: Any = None
    ltype: str = "nil"  # "int" / "float" / "str" / "bool" / "nil"


@dataclass
class Ident(Node):
    name: str = ""


@dataclass
class BinOp(Node):
    op: str = ""
    lhs: Optional[Node] = None
    rhs: Optional[Node] = None


@dataclass
class UnaryOp(Node):
    op: str = ""
    operand: Optional[Node] = None


@dataclass
class Call(Node):
    callee: Optional[Node] = None
    args: List[Node] = field(default_factory=list)


@dataclass
class Block(Node):
    stmts: List[Node] = field(default_factory=list)


@dataclass
class Bind(Node):
    name: str = ""
    value: Optional[Node] = None
    constant: bool = False


@dataclass
class FnDecl(Node):
    name: str = ""
    params: List[str] = field(default_factory=list)
    body: Optional[Block] = None


@dataclass
class Lambda(Node):
    params: List[str] = field(default_factory=list)
    body: Optional[Block] = None


@dataclass
class If(Node):
    cond: Optional[Node] = None
    then_branch: Optional[Block] = None
    else_branch: Optional[Node] = None  # Block or If (else-if)


@dataclass
class Match(Node):
    scrutinee: Optional[Node] = None
    arms: List[Tuple[Node, Block]] = field(default_factory=list)


@dataclass
class Loop(Node):
    body: Optional[Block] = None


@dataclass
class Break(Node):
    pass


@dataclass
class Return(Node):
    value: Optional[Node] = None


@dataclass
class Program(Node):
    stmts: List[Node] = field(default_factory=list)
