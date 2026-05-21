# sinister-watchdog :: auto-online keeper for local agents + MCP servers
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later

from .core import (
    Watchdog,
    SanctumPaths,
    scan_heartbeats,
    probe_mcp_servers,
    revive_agent,
    revive_mcp,
    docker_ensure,
    load_registry,
    snapshot_status,
)

__all__ = [
    "Watchdog",
    "SanctumPaths",
    "scan_heartbeats",
    "probe_mcp_servers",
    "revive_agent",
    "revive_mcp",
    "docker_ensure",
    "load_registry",
    "snapshot_status",
]

__version__ = "0.1.0"
