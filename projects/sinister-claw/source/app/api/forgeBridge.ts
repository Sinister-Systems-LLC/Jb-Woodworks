// RKOJ Mobile :: api/forgeBridge.ts
// Author: RKOJ-ELENO :: 2026-05-21
// License: AGPL-3.0-or-later
//
// Aggregated re-export -- single import point for screens that need to
// reach the Forge bridge on the operator's PC (:5078 over Tailscale).
//
// Endpoints covered:
//   GET    /api/sanctum/heartbeats           (sanctum.getHeartbeats)
//   GET    /api/sanctum/projects             (sanctum.getProjects)
//   GET    /api/sanctum/commits              (sanctum.getRecentCommits)
//   GET    /api/sanctum/inbox                (sanctum.getInbox)
//   GET    /api/forge/agents                 (forge.listAgents)
//   POST   /api/forge/spawn                  (forge.spawnAgent)
//   DELETE /api/forge/agents/:id             (forge.terminateAgent)
//   SSE    /api/forge/agents/:id/stream      (forge.openAgentStream)
//   GET    /api/devices                      (devices.listDevices)
//   GET    /api/devices/:serial              (devices.getDeviceDetail)
//   POST   /api/devices/:serial/shell        (devices.adbShell)
//   POST   /api/devices/:serial/scrcpy       (devices.openScrcpy)
//   POST   /api/devices/:serial/rka/arm      (devices.rkaArm)
//   POST   /api/devices/:serial/rka/kill     (devices.rkaKill)
//   SSE    /api/devices/:serial/logcat       (devices.openLogcatStream)
//   GET    /api/workstation/vault/status     (workstation.vaultStatus)
//   GET    /api/workstation/brain/probe      (workstation.brainProbe)
//   GET    /api/workstation/watchdog/status  (workstation.watchdogStatus)
//   POST   /api/workstation/backups/run      (workstation.backupsRun)
//   GET    /api/workstation/mcp/probe        (workstation.mcpProbe)

export * from "./sanctum";
export * from "./forge";
export * from "./devices";
export * from "./workstation";
