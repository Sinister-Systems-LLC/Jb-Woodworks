# Sinister Sanctum :: sinister-login :: package
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later

__version__ = "0.1.0"

from .providers import (
    PROVIDERS,
    Provider,
    list_providers,
    get_provider,
    provider_status,
    SCHEMA_VERSION,
)
from .api import (
    status_all,
    doctor,
    resolve_active,
    print_env_for,
    add_to_envfile,
)

__all__ = [
    "PROVIDERS",
    "Provider",
    "list_providers",
    "get_provider",
    "provider_status",
    "status_all",
    "doctor",
    "resolve_active",
    "print_env_for",
    "add_to_envfile",
    "SCHEMA_VERSION",
    "__version__",
]
