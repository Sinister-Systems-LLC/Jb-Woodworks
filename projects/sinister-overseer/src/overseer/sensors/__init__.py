"""sensors package -- live event sources for the Sinister Overseer WatchBus.

Author: RKOJ-ELENO :: 2026-05-24

Each sensor wraps an existing Sanctum automation script (token-analytics.ps1 /
claude-usage-meter.ps1 / forever-improve.ps1 / heartbeat-sweep.ps1) and emits
typed events onto the SensorBus. The Overseer detector consumes the bus.

Modules:
    analyzer  -- TokenAnalyzerSensor + UsageMeterSensor + ForeverImproveSensor
                 + SensorBus
"""

from overseer.sensors.analyzer import (  # noqa: F401
    SensorBus,
    TokenAnalyzerSensor,
    UsageMeterSensor,
    ForeverImproveSensor,
    WasteEvent,
    RecommendationEvent,
    UsageHighEvent,
    RotInLogEvent,
)
