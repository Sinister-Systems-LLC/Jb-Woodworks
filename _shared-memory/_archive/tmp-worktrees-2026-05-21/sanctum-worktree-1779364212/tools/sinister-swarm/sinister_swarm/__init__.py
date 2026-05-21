# Sinister Sanctum :: sinister-swarm :: public API
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later

from .api import (
    dm,
    broadcast,
    spawn_agent,
    list_active,
    watch_file,
    mark_done,
    wait_for,
    mcp_broadcast,
    mcp_hive_status,
    set_sanctum_root,
    get_sanctum_root,
    detect_my_slug,
    SCHEMA_VERSION,
    DEFAULT_SANCTUM_ROOT,
)

__all__ = [
    "dm",
    "broadcast",
    "spawn_agent",
    "list_active",
    "watch_file",
    "mark_done",
    "wait_for",
    "mcp_broadcast",
    "mcp_hive_status",
    "set_sanctum_root",
    "get_sanctum_root",
    "detect_my_slug",
    "SCHEMA_VERSION",
    "DEFAULT_SANCTUM_ROOT",
]

__version__ = "0.1.0"
