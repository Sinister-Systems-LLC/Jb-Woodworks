# Sinister Sanctum :: forge-memory-bridge :: public API
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later

from .api import (
    write,
    recall,
    bm25_rescore,
    ls,
    list,  # alias preserved for v0.1.0 callers; see api.py
    graph,
    consolidate,
    delete,
    set_root,
    get_root,
    DEFAULT_ROOT,
    SCHEMA_VERSION,
)

__all__ = [
    "write",
    "recall",
    "bm25_rescore",
    "ls",
    "list",
    "graph",
    "consolidate",
    "delete",
    "set_root",
    "get_root",
    "DEFAULT_ROOT",
    "SCHEMA_VERSION",
]

__version__ = "0.1.2"
