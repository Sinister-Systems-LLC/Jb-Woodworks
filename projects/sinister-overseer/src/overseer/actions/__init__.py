# Author: RKOJ-ELENO :: 2026-05-25
"""actions package -- side-effecting apply paths consumed by the Overseer.

Each action takes a typed proposal/opportunity dataclass + returns a typed
SpawnResult/ApplyResult. Actions NEVER run without an approval-gate check
in the orchestrator (low-risk = auto-approve via confidence floor; high-risk
= operator approval via touch-file).

Modules:
    spawn_sub_lane -- SpawnSubLaneAction: turn a DivergenceOpportunity into a
                      live spawned Claude session on its own agent/* branch.
"""

from overseer.actions.spawn_sub_lane import (  # noqa: F401
    SpawnSubLaneAction,
    SpawnResult,
)
