"""hgly tokenizer — Unicode glyphs + ASCII fallbacks.

Author: RKOJ-ELENO :: 2026-05-25
Phase 2 bootstrap.

Emits Token(kind, lexeme, line, col). Whitespace + `# ...` line comments
are skipped. Both the U+13000-block hieroglyphs and their ASCII fallbacks
from docs/GLYPH-SYNTAX.md tokenize to the SAME canonical kind so the parser
treats them interchangeably.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, List, Optional

_GLYPH_TO_KIND = {
    "\U00013080": "LET", "\U000132AA": "CST", "\U0001318E": "FN",
    "\U0001339B": "RET", "\U000133CF": "LAM", "\U0001337F": "AS",
    "\U0001309D": "LBRACE", "\U0001309E": "RBRACE",
    "\U00013079": "IF", "\U0001309C": "EL", "\U000130C0": "MATCH",
    "\U000130E2": "LOOP", "\U0001335E": "BREAK", "\U000133A1": "CONT",
    "\U000133BC": "YIELD", "\U00013283": "FOR",
    "➕": "PLUS", "➖": "MINUS", "✖": "STAR", "➗": "SLASH",
    "☰": "PERCENT", "∧": "AND", "∨": "OR", "¬": "NOT",
}
_ASCII_KEYWORDS = {
    "let": "LET", "cst": "CST", "fn": "FN", "ret": "RET", "return": "RET",
    "lam": "LAM", "as": "AS", "if": "IF", "el": "EL", "else": "EL",
    "mch": "MATCH", "match": "MATCH", "lp": "LOOP", "loop": "LOOP",
    "brk": "BREAK", "break": "BREAK", "cnt": "CONT", "continue": "CONT",
    "yld": "YIELD", "yield": "YIELD", "for": "FOR", "true": "TRUE",
    "false": "FALSE", "nil": "NIL", "and": "AND", "or": "OR", "not": "NOT",
}
_MULTI_PUNCT = [("==", "EQ"), ("!=", "NEQ"), ("<=", "LE"), (">=", "GE"),
                (":=", "ASSIGN"), ("&&", "AND"), ("||", "OR")]
_SINGLE_PUNCT = {"{": "LBRACE", "}": "RBRACE", "(": "LPAREN", ")": "RPAREN",
                 "[": "LBRACK", "]": "RBRACK", ":": "COLON",
                 ",": "COMMA", ";": "SEMI", "+": "PLUS", "-": "MINUS",
                 "*": "STAR", "/": "SLASH", "%": "PERCENT", "<": "LT",
                 ">": "GT", "!": "NOT", "=": "EQ"}


@dataclass(frozen=True)
class Token:
    kind: str
    lexeme: str
    line: int
    col: int

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"Token({self.kind!r}, {self.lexeme!r}, L{self.line}:C{self.col})"


class LexError(Exception):
    def __init__(self, msg: str, line: int, col: int) -> None:
        super().__init__(f"{msg} at line {line} col {col}")
        self.line = line
        self.col = col


def _is_ident_start(c: str) -> bool:
    return c.isalpha() or c == "_"


def _is_ident_cont(c: str) -> bool:
    return c.isalnum() or c == "_"


def tokenize(src: str) -> List[Token]:
    out: List[Token] = []
    i = 0; line = 1; col = 1; n = len(src)
    while i < n:
        c = src[i]
        if c == "\n":
            i += 1; line += 1; col = 1; continue
        if c in " \t\r":
            i += 1; col += 1; continue
        if c == "#":
            while i < n and src[i] != "\n": i += 1
            continue
        if c == '"':
            start_col = col; j = i + 1; buf: List[str] = []
            while j < n and src[j] != '"':
                if src[j] == "\\" and j + 1 < n:
                    nxt = src[j + 1]
                    buf.append({"n": "\n", "t": "\t", "r": "\r", "\\": "\\",
                                '"': '"'}.get(nxt, nxt))
                    j += 2; continue
                if src[j] == "\n":
                    raise LexError("unterminated string", line, start_col)
                buf.append(src[j]); j += 1
            if j >= n: raise LexError("unterminated string", line, start_col)
            out.append(Token("STRING", "".join(buf), line, start_col))
            col += (j - i) + 1; i = j + 1; continue
        if c.isdigit():
            start_col = col; j = i
            while j < n and (src[j].isdigit() or src[j] == "." or src[j] == "_"):
                j += 1
            out.append(Token("NUMBER", src[i:j].replace("_", ""), line, start_col))
            col += (j - i); i = j; continue
        if c in _GLYPH_TO_KIND:
            out.append(Token(_GLYPH_TO_KIND[c], c, line, col))
            i += 1; col += 1; continue
        matched = False
        for sym, kind in _MULTI_PUNCT:
            if src.startswith(sym, i):
                out.append(Token(kind, sym, line, col))
                i += len(sym); col += len(sym); matched = True; break
        if matched: continue
        if c in _SINGLE_PUNCT:
            kind = _SINGLE_PUNCT[c]
            out.append(Token(kind, c, line, col)); i += 1; col += 1; continue
        if _is_ident_start(c):
            start_col = col; j = i
            while j < n and _is_ident_cont(src[j]): j += 1
            lex = src[i:j]
            out.append(Token(_ASCII_KEYWORDS.get(lex, "IDENT"), lex, line, start_col))
            col += (j - i); i = j; continue
        # RKOJ-ELENO :: 2026-05-25 (iter-8 lexer relaxation) :: unknown chars in
        # the Egyptian Hieroglyph block (U+13000-U+1342F) get treated as IDENT
        # so corpus programs using glyphs outside the canonical 16-token map
        # still tokenize. Phase 4+ tightens this when codegen needs strict
        # glyph-to-op mapping; for now interpreter lenient mode resolves them
        # to zero-stubs gracefully.
        cp = ord(c)
        if 0x13000 <= cp <= 0x1342F:
            # Egyptian Hieroglyph block; collect a run of glyph chars as one IDENT.
            start_col = col; j = i
            while j < n and 0x13000 <= ord(src[j]) <= 0x1342F:
                j += 1
            out.append(Token("IDENT", src[i:j], line, start_col))
            col += (j - i); i = j; continue
        raise LexError(f"unexpected character {c!r}", line, col)
    out.append(Token("EOF", "", line, col))
    return out


def iter_tokens(src: str) -> Iterator[Token]:
    yield from tokenize(src)
