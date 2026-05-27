# [PROPOSAL] From Sinister Overseer -> Sinister Sanctum :: stale-heartbeat scan

**Author:** RKOJ-ELENO :: 2026-05-26T23:01:36Z
**From slug:** sinister-overseer
**To slug:** sanctum
**Priority:** high

## Summary

- total projects scanned: 36
- fresh (<= 24h): 9
- stale (> 24h):  0
- missing heartbeat:                       27

## Missing heartbeat (no file at all)

- `sinister-sleight` (tier=3) :: D:\Sinister Sanctum\_shared-memory\heartbeats\sinister-sleight.json
- `sinister-term-themes` (tier=3) :: D:\Sinister Sanctum\_shared-memory\heartbeats\sinister-term-themes.json
- `kernel-apk` (tier=2) :: D:\Sinister Sanctum\_shared-memory\heartbeats\kernel-apk.json
- `sinister-chatbot` (tier=2) :: D:\Sinister Sanctum\_shared-memory\heartbeats\sinister-chatbot.json
- `sinister-designer` (tier=2) :: D:\Sinister Sanctum\_shared-memory\heartbeats\sinister-designer.json
- `sinister-hieroglyphics` (tier=2) :: D:\Sinister Sanctum\_shared-memory\heartbeats\sinister-hieroglyphics.json
- `sinister-imessage-bridge` (tier=2) :: D:\Sinister Sanctum\_shared-memory\heartbeats\sinister-imessage-bridge.json
- `sinister-looper` (tier=2) :: D:\Sinister Sanctum\_shared-memory\heartbeats\sinister-looper.json
- `sinister-mcp` (tier=2) :: D:\Sinister Sanctum\_shared-memory\heartbeats\sinister-mcp.json
- `sinister-panel` (tier=2) :: D:\Sinister Sanctum\_shared-memory\heartbeats\sinister-panel.json
- `sinister-quantum` (tier=2) :: D:\Sinister Sanctum\_shared-memory\heartbeats\sinister-quantum.json
- `snap-emulator-api` (tier=2) :: D:\Sinister Sanctum\_shared-memory\heartbeats\snap-emulator-api.json
- `bumble-emulator-api` (tier=0) :: D:\Sinister Sanctum\_shared-memory\heartbeats\bumble-emulator-api.json
- `general` (tier=0) :: D:\Sinister Sanctum\_shared-memory\heartbeats\general.json
- `jb-woodworks` (tier=0) :: D:\Sinister Sanctum\_shared-memory\heartbeats\jb-woodworks.json
- `jkor` (tier=0) :: D:\Sinister Sanctum\_shared-memory\heartbeats\jkor.json
- `rkoj` (tier=0) :: D:\Sinister Sanctum\_shared-memory\heartbeats\rkoj.json
- `rkoj-workstation` (tier=0) :: D:\Sinister Sanctum\_shared-memory\heartbeats\rkoj-workstation.json
- `showmasters` (tier=0) :: D:\Sinister Sanctum\_shared-memory\heartbeats\showmasters.json
- `sinister-claw` (tier=0) :: D:\Sinister Sanctum\_shared-memory\heartbeats\sinister-claw.json
- `sinister-emulator` (tier=0) :: D:\Sinister Sanctum\_shared-memory\heartbeats\sinister-emulator.json
- `sinister-forge` (tier=0) :: D:\Sinister Sanctum\_shared-memory\heartbeats\sinister-forge.json
- `sinister-freeze` (tier=0) :: D:\Sinister Sanctum\_shared-memory\heartbeats\sinister-freeze.json
- `sinister-generator` (tier=0) :: D:\Sinister Sanctum\_shared-memory\heartbeats\sinister-generator.json
- `sinister-mind` (tier=0) :: D:\Sinister Sanctum\_shared-memory\heartbeats\sinister-mind.json
- `sinister-snap-api-quantum` (tier=0) :: D:\Sinister Sanctum\_shared-memory\heartbeats\sinister-snap-api-quantum.json
- `tiktok-emulator-api` (tier=0) :: D:\Sinister Sanctum\_shared-memory\heartbeats\tiktok-emulator-api.json

## Suggested action

Sanctum to decide whether to invoke `automations/start-sinister-session.ps1` for any of the above (per `auto-start-if-no-agent-doctrine-2026-05-25`). Overseer does NOT auto-spawn -- the spawn decision is sanctum-master scope.

End.
