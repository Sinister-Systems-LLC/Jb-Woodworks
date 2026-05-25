"""Sinister Hieroglyphics reference implementation.

Author: RKOJ-ELENO :: 2026-05-25
Phase 2 bootstrap (Python). Rust port lands in Phase 2b.
"""
from .parser import parse, parse_file, ParseError  # noqa: F401

__version__ = "0.0.2"

__all__ = ["parse", "parse_file", "ParseError", "__version__"]
