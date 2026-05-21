# Sinister Sanctum :: sinister-model :: package
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later

__version__ = "0.1.0"

from .registry import (
    PROVIDER_MODELS,
    SCHEMA_VERSION,
    Model,
    list_providers,
    list_models,
    get_model,
    find_provider_for_model,
)
from .state import (
    STATE_PATH,
    get_current,
    set_current,
    clear_current,
    state_path,
)

__all__ = [
    "PROVIDER_MODELS",
    "SCHEMA_VERSION",
    "Model",
    "list_providers",
    "list_models",
    "get_model",
    "find_provider_for_model",
    "STATE_PATH",
    "get_current",
    "set_current",
    "clear_current",
    "state_path",
    "__version__",
]
