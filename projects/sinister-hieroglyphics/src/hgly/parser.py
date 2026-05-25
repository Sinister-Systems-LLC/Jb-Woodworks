"""hgly Pratt parser. Author: RKOJ-ELENO :: 2026-05-25. Phase 2 bootstrap.

Public API: parse(src) / parse_file(path) -> Program; ParseError(msg,l,c).
Grammar: program=stmt* ; stmt=bind|fn|ret|brk|loop|for|if|match|expr ;
expr=pratt(prefix-arith + infix-arith + cmp + calls).
"""
from __future__ import annotations
from typing import List, Optional
from .ast import (Bind, BinOp, Block, Break, Call, FnDecl, Ident, If, Lambda,
                  Literal, Loop, Match, Node, Program, Return, UnaryOp)
from .lexer import Token, tokenize


class ParseError(Exception):
    def __init__(self, msg: str, line: int, col: int) -> None:
        super().__init__(f"{msg} at line {line} col {col}")
        self.msg = msg; self.line = line; self.col = col


_INFIX_PREC = {"OR": 10, "AND": 20, "EQ": 30, "NEQ": 30, "LT": 30, "GT": 30,
               "LE": 30, "GE": 30, "PLUS": 40, "MINUS": 40, "STAR": 50,
               "SLASH": 50, "PERCENT": 50}
_PREFIX_ARITH = {"PLUS", "MINUS", "STAR", "SLASH", "PERCENT", "AND", "OR",
                 "EQ", "NEQ", "LT", "GT", "LE", "GE"}
_OP_SYM = {"PLUS": "+", "MINUS": "-", "STAR": "*", "SLASH": "/",
           "PERCENT": "%", "AND": "&&", "OR": "||", "NOT": "!", "EQ": "==",
           "NEQ": "!=", "LT": "<", "GT": ">", "LE": "<=", "GE": ">="}
_ATOM_KINDS = ("NUMBER", "STRING", "IDENT", "TRUE", "FALSE", "NIL")


def _mk_literal(t: Token) -> Literal:
    if t.kind == "NUMBER":
        v = float(t.lexeme) if "." in t.lexeme else int(t.lexeme)
        lt = "float" if "." in t.lexeme else "int"
        return Literal(line=t.line, col=t.col, value=v, ltype=lt)
    if t.kind == "STRING":
        return Literal(line=t.line, col=t.col, value=t.lexeme, ltype="str")
    if t.kind == "TRUE": return Literal(line=t.line, col=t.col, value=True, ltype="bool")
    if t.kind == "FALSE": return Literal(line=t.line, col=t.col, value=False, ltype="bool")
    return Literal(line=t.line, col=t.col, value=None, ltype="nil")


class _Parser:
    def __init__(self, tokens: List[Token]) -> None:
        self.tokens = tokens; self.pos = 0

    def peek(self, off: int = 0) -> Token:
        idx = self.pos + off
        return self.tokens[idx] if idx < len(self.tokens) else self.tokens[-1]

    def advance(self) -> Token:
        t = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1: self.pos += 1
        return t

    def check(self, kind: str) -> bool:
        return self.peek().kind == kind

    def match(self, *kinds: str) -> Optional[Token]:
        return self.advance() if self.peek().kind in kinds else None

    def expect(self, kind: str, msg: Optional[str] = None) -> Token:
        t = self.peek()
        if t.kind != kind:
            raise ParseError(msg or f"expected {kind}, got {t.kind} ({t.lexeme!r})",
                             t.line, t.col)
        return self.advance()

    def parse_program(self) -> Program:
        first = self.peek(); stmts: List[Node] = []
        while not self.check("EOF"):
            stmts.append(self.parse_stmt())
            while self.match("SEMI"): pass
        return Program(line=first.line, col=first.col, stmts=stmts)

    def parse_stmt(self) -> Node:
        t = self.peek(); k = t.kind
        if k in ("LET", "CST"): return self._bind()
        if k == "FN": return self._fn()
        if k == "RET": return self._return()
        if k in ("BREAK", "CONT"):
            self.advance(); return Break(line=t.line, col=t.col)
        if k == "LOOP": return self._loop()
        if k == "FOR": return self._for()
        if k == "IF": return self._if()
        if k == "MATCH": return self._match()
        if k == "LBRACE": return self._block()
        return self.parse_expr()

    def _bind(self) -> Bind:
        tok = self.advance(); constant = tok.kind == "CST"
        name = self.expect("IDENT", "expected identifier after let/cst")
        self.match("ASSIGN")
        return Bind(line=tok.line, col=tok.col, name=name.lexeme,
                    value=self.parse_expr(), constant=constant)

    def _fn(self) -> FnDecl:
        tok = self.advance()
        name = self.expect("IDENT", "expected function name after fn")
        self.expect("LPAREN", "expected '(' after function name")
        params: List[str] = []
        while not self.check("RPAREN"):
            params.append(self.expect("IDENT", "expected parameter name").lexeme)
            self.match("COMMA")
        self.expect("RPAREN")
        return FnDecl(line=tok.line, col=tok.col, name=name.lexeme,
                      params=params, body=self._block())

    def _return(self) -> Return:
        tok = self.advance()
        if self.peek().kind in ("RBRACE", "EOF", "SEMI"):
            return Return(line=tok.line, col=tok.col, value=None)
        return Return(line=tok.line, col=tok.col, value=self.parse_expr())

    def _loop(self) -> Loop:
        tok = self.advance()
        return Loop(line=tok.line, col=tok.col, body=self._block())

    def _for(self) -> Loop:
        """`for IDENT lo hi { body }` desugars to a Loop with a head Bind
        for the induction variable + a hidden `__hgly_for_hi_<v>` marker."""
        tok = self.advance()
        var = self.expect("IDENT", "expected loop variable after 'for'")
        lo = self._call_atom() if self.peek().kind in _ATOM_KINDS else self.parse_expr()
        hi = self.parse_expr()
        body = self._block()
        body.stmts.insert(0, Bind(line=var.line, col=var.col, name=var.lexeme,
                                  value=lo, constant=False))
        body.stmts.insert(1, Bind(line=var.line, col=var.col,
                                  name=f"__hgly_for_hi_{var.lexeme}",
                                  value=hi, constant=True))
        return Loop(line=tok.line, col=tok.col, body=body)

    def _if(self) -> If:
        tok = self.advance()
        had_paren = bool(self.match("LPAREN"))
        cond = self.parse_expr()
        if had_paren: self.expect("RPAREN")
        then_b = self._block()
        else_b: Optional[Node] = None
        if self.match("EL"):
            else_b = self._if() if self.check("IF") else self._block()
        return If(line=tok.line, col=tok.col, cond=cond,
                  then_branch=then_b, else_branch=else_b)

    def _match(self) -> Match:
        tok = self.advance(); scrut = self.parse_expr()
        self.expect("LBRACE"); arms: list = []
        while not self.check("RBRACE"):
            pat = self.parse_expr()
            self.match("COMMA")
            body = (self._block() if self.check("LBRACE")
                    else Block(line=pat.line, col=pat.col, stmts=[self.parse_expr()]))
            arms.append((pat, body))
        self.expect("RBRACE")
        return Match(line=tok.line, col=tok.col, scrutinee=scrut, arms=arms)

    def _block(self) -> Block:
        tok = self.expect("LBRACE", "expected '{'"); stmts: List[Node] = []
        while not self.check("RBRACE") and not self.check("EOF"):
            stmts.append(self.parse_stmt())
            while self.match("SEMI"): pass
        self.expect("RBRACE", "expected '}'")
        return Block(line=tok.line, col=tok.col, stmts=stmts)

    def parse_expr(self, min_prec: int = 0) -> Node:
        left = self._prefix()
        while True:
            t = self.peek(); prec = _INFIX_PREC.get(t.kind)
            if prec is None or prec < min_prec: break
            op = self.advance(); right = self.parse_expr(prec + 1)
            left = BinOp(line=op.line, col=op.col, op=_OP_SYM[op.kind],
                         lhs=left, rhs=right)
        return left

    def _prefix(self) -> Node:
        t = self.peek(); k = t.kind
        if k in ("NUMBER", "STRING", "TRUE", "FALSE", "NIL"):
            return _mk_literal(self.advance())
        if k == "LPAREN":
            self.advance(); e = self.parse_expr()
            self.expect("RPAREN", "expected ')'"); return e
        if k == "NOT":
            self.advance()
            return UnaryOp(line=t.line, col=t.col, op="!", operand=self._prefix())
        if k == "MINUS" and self.peek(1).kind == "NUMBER":
            self.advance(); num = self.advance()
            v = -float(num.lexeme) if "." in num.lexeme else -int(num.lexeme)
            ltype = "float" if "." in num.lexeme else "int"
            return Literal(line=t.line, col=t.col, value=v, ltype=ltype)
        if k in _PREFIX_ARITH:
            op = self.advance()
            return BinOp(line=op.line, col=op.col, op=_OP_SYM[op.kind],
                         lhs=self._prefix_operand(), rhs=self._prefix_operand())
        if k == "IDENT":
            self.advance()
            node: Node = Ident(line=t.line, col=t.col, name=t.lexeme)
            if self.check("LPAREN"):
                self.advance(); args: List[Node] = []
                while not self.check("RPAREN"):
                    args.append(self.parse_expr()); self.match("COMMA")
                self.expect("RPAREN")
                return Call(line=t.line, col=t.col, callee=node, args=args)
            args2: List[Node] = []
            while self.peek().kind in _ATOM_KINDS and self.peek().line == t.line:
                args2.append(self._call_atom())
            if args2:
                return Call(line=t.line, col=t.col, callee=node, args=args2)
            return node
        if k == "LAM": return self._lambda()
        raise ParseError(f"unexpected token {k} ({t.lexeme!r})", t.line, t.col)

    def _prefix_operand(self) -> Node:
        """Operand for prefix-form arith op: atom / paren / nested prefix.
        Bare IDENT yields Ident (NOT a call) so `+ foo 1` works."""
        t = self.peek(); k = t.kind
        if k in ("NUMBER", "STRING", "TRUE", "FALSE", "NIL", "LPAREN", "NOT"):
            return self._prefix()
        if k == "MINUS" and self.peek(1).kind == "NUMBER":
            return self._prefix()
        if k in _PREFIX_ARITH:
            return self._prefix()
        if k == "IDENT":
            self.advance()
            return Ident(line=t.line, col=t.col, name=t.lexeme)
        raise ParseError(f"expected operand, got {k} ({t.lexeme!r})", t.line, t.col)

    def _call_atom(self) -> Node:
        t = self.advance()
        if t.kind == "IDENT":
            return Ident(line=t.line, col=t.col, name=t.lexeme)
        return _mk_literal(t)

    def _lambda(self) -> Lambda:
        tok = self.advance(); self.expect("LPAREN"); params: List[str] = []
        while not self.check("RPAREN"):
            params.append(self.expect("IDENT").lexeme); self.match("COMMA")
        self.expect("RPAREN")
        return Lambda(line=tok.line, col=tok.col, params=params, body=self._block())


def parse(src: str) -> Program:
    return _Parser(tokenize(src)).parse_program()


def parse_file(path: str) -> Program:
    with open(path, "r", encoding="utf-8") as f:
        return parse(f.read())
