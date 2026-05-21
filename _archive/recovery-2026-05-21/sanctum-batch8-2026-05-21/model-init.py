# Sinister Sanctum :: sinister-model :: public API
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later

from .api import (
    list_models,
    current,
    providers,
    propose_switch,
    set_sanctum_root,
    get_sanctum_root,
    SCHEMA_VERSION,
)

__all__ = [
    "list_models",
    "current",
    "providers",
    "propose_switch",
    "set_sanctum_root",
    "get_sanctum_root",
    "SCHEMA_VERSION",
]

__version__ = "0.1.0"
