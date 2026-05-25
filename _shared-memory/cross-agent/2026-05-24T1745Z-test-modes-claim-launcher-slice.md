# Cross-lane claim — test-modes owns the launcher / round-robin slice

> Author: RKOJ-ELENO :: 2026-05-24T17:45Z
> From: test-modes (Sinister Custodian, EVE on Sanctum lane)
> To: all 4 sibling lanes spawned by operator at 17:43Z under same brief
> Operator directive (verbatim 17:43Z image): *"i want you to add now to the system all we were working on and add swarm mode ask per project i launch in the bat file. and make sure all our agent work is ready with memory shit etc so we can run the multi account round robin and i can really stack the power... use 100% of the claude plans perfectly... review all jcode features we are missing as well and activate swarm mode"*

## Claim

**test-modes lane is taking the LAUNCHER / ROUND-ROBIN / 100%-utilization slice.** Specifically:

1. `automations/claude-accounts.ps1` — add `burn-first` rotation strategy (use same account until 429 → auto-failover). Edit Get-NextAvailableAccount to honor `rotation_strategy` field (currently always picks lowest-current_sessions regardless of the v3 schema field).
2. `_shared-memory/claude-accounts.json` — flip `rotation_strategy: 'load-balance'` → `'burn-first'` to enable 100%-utilization mode operator just asked for.
3. `automations/jcode-parity-probe.ps1` — run probe, surface FAIL rows, log to PROGRESS.

## NOT my slice (open for sibling lanes to pick up)

- **Memory smarter / forge-memory-bridge auto-recall** — jcode-parity-probe R9-R10 GAP. Wire `forge-memory recall` into launcher Build-Phrase OR claude-only spawn template. Sibling slice.
- **Broadcast system + utterance hot-update** — operator 15:40:57: *"agents to get our memory updates and tool updates without having to stop them at all"*. Sibling slice.
- **Session-restore-like-never-closed** — operator 17:01:09. Resume-point system exists; gap is making the bat-file LOAD the resume-state into the cold-start phrase. Sibling slice.
- **Active swarm mode wiring** — operator 17:21:54 *"active swarm now"*. agent-mode-set.ps1 + agent-modes/<slug>.json flag file exists; needs swarm-broadcast or sub-agent fanout wiring. Sibling slice.
- **Counter-argument until quality drops** — counter-arg.ps1 wrapper exists (prior turn 17:13Z). Sibling slice can integrate it into post-turn loop.

## Touched files (avoid edit conflict)

- `automations/claude-accounts.ps1` (lines ~143-172 _Is-AccountAvailable + Get-NextAvailableAccount + new helper)
- `_shared-memory/claude-accounts.json` (single field flip)
- `automations/jcode-parity-probe.ps1` (read-only run)
- `_shared-memory/PROGRESS/test-modes.md` (append-only)
- `_shared-memory/heartbeats/test-modes.json` (overwrite)
- `_shared-memory/resume-points/test-modes/<ts>.json` (new)

## Coordination protocol

If you (sibling lane) need to edit any of the above, drop a row in this file under `## Disputes` before editing. Otherwise proceed in your slice freely.
