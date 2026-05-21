# Sinister Sanctum :: sinister-swarm :: package
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later

__version__ = "0.1.0"

from .api import (
    dm,
    broadcast,
    spawn_agent,
    list_active,
    watch_file,
    mark_done,
    wait_for,
    detect_my_slug,
    set_sanctum_root,
    get_sanctum_root,
    mcp_broadcast,
    mcp_hive_status,
    WatchHandle,
    SCHEMA_VERSION,
)

__all__ = [
    "dm",
    "broadcast",
    "spawn_agent",
    "list_active",
    "watch_file",
    "mark_done",
    "wait_for",
    "detect_my_slug",
    "set_sanctum_root",
    "get_sanctum_root",
    "mcp_broadcast",
    "mcp_hive_status",
    "WatchHandle",
    "SCHEMA_VERSION",
    "__version__",
]
