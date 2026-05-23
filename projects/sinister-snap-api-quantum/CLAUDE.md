<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# CLAUDE.md — Sinister Snap API Quantum

> Project root: `D:\Sinister Sanctum\projects\sinister-snap-api-quantum\`
> Sanctum harness root: `D:\Sinister Sanctum\`
> Agent slug: `sinister-snap-api-quantum`
> Display name: `Sinister Snap API Quantum`
> Persona: EVE
> Accent: purple

## What this project is

Dedicated test environment exercising **Sinister Seraphim** against **Snap API EMU + Sinister EMU bundle simultaneously**. See `README.md` for the full description.

The lane's job: provide a reproducible, audit-only, zero-cloud-cost harness so any agent (or the operator directly) can validate Seraphim's Lane 1 (audit) + Lane 2 (emulator fingerprints) end-to-end without touching the real Snap/TikTok/Bumble fire pipelines or burning the 120s cloud budget.

## Cold-start (every spawn)

1. **Read `D:\Sinister Sanctum\CLAUDE.md`** — fleet-wide doctrine.
2. **Read `D:\Sinister Sanctum\SESSION-START\`** in order.
3. **Read this `README.md`** + `run-test.py` head to understand the test shape.
4. **Read brain entry `seraphim-for-emu-re-2026-05-23.md`** — the doctrine pinning Seraphim's EMU/RE focus + the 120s cloud budget table.
5. **Read related brain entries**: `snap-emu-pb2-schema-shadow-2026-05-21.md`, `snap-account-24h-survival-doctrine-2026-05-21.md`, `snap-tt-rka-chain-attestation-insufficient-2026-05-19.md`.
6. **Heartbeat each turn**: write `D:\Sinister Sanctum\_shared-memory\heartbeats\sinister-snap-api-quantum.json`.
7. **Append PROGRESS**: `D:\Sinister Sanctum\_shared-memory\PROGRESS\Sinister Snap API Quantum.md`.
8. **Resume-points**: `D:\Sinister Sanctum\_shared-memory\resume-points\Sinister Snap API Quantum\<UTC>.json`.

## Per-agent branch

`agent/sinister-snap-api-quantum/<short-topic>` cut off latest doctrine HEAD. Push freely.

## Hard rules for THIS lane

1. **NEVER fire real HTTP** against snap.com / api.tiktok / bumble servers. The test harness is dry-run by design.
2. **NEVER spend cloud-Wukong-180 seconds**. All Seraphim calls default `backend='sim-local'`. If you ever need cloud-grade entropy, ask the operator FIRST with a [REQUEST cloud-Wukong-N seconds for X] inbox message.
3. **NEVER modify** `projects/sinister-snap-emu/source/` or `projects/sinister-emulator-bundle/source/`. Read-only import via sys.path.
4. **NEVER vendor** the python_simulator tarball into git (`_vendor/` is gitignored).
5. **NEVER edit** `~/.claude/.mcp.json` or `_vault-personal/licenses/pilotos.txt`.

## What lives here

| Path | Purpose |
|---|---|
| `README.md` | Project description + how to run the test |
| `CLAUDE.md` (this) | Agent cold-start protocol |
| `run-test.py` | Single-command dual-lane test driver |
| `tests/` | Sub-test modules (per-lane harness fixtures) |
| `outputs/` | Test-run artifacts (gitignored — regenerated per run) |
| `.gitignore` | Excludes outputs/ + __pycache__/ |

## Composes with

- `tools/sinister-seraphim/` (the application layer under test)
- `tools/sinister-seraphim/snap_re.py` (lane-specific adapter)
- `projects/sinister-snap-emu/source/` (Snap API EMU lane, read-only)
- `projects/sinister-emulator-bundle/source/` (Sinister EMU bundle, read-only)
- `_shared-memory/knowledge/seraphim-for-emu-re-2026-05-23.md` (operator-canonical doctrine)
- `_shared-memory/dashboards/seraphim.html` (visible test results)
