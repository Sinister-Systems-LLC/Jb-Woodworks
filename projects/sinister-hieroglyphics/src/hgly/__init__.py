"""Sinister Hieroglyphics reference implementation.

Author: RKOJ-ELENO :: 2026-05-25
Phase 3 bootstrap (Python). Rust port lands in Phase 3b.
"""
from .parser import parse, parse_file, ParseError  # noqa: F401
try:
    from .interpreter import Interpreter, HglyPanic  # noqa: F401
    _HAS_INTERP = True
except Exception:
    _HAS_INTERP = False
from .ir import (Module, Function, Block, Effect, Type, TInt, TFloat, TBool,
                 TStr, TUnit, TList, TTuple, TStruct, TFn, TPtr, TLinear,
                 lower_ast, TypeChecker, TypeError, print_ir)  # noqa: F401

__version__ = "0.0.4"

__all__ = ["parse", "parse_file", "ParseError", "Module", "Function", "Block",
           "Effect", "Type", "TInt", "TFloat", "TBool", "TStr", "TUnit",
           "TList", "TTuple", "TStruct", "TFn", "TPtr", "TLinear", "lower_ast",
           "TypeChecker", "TypeError", "print_ir", "__version__"]
if _HAS_INTERP:
    __all__ += ["Interpreter", "HglyPanic"]
