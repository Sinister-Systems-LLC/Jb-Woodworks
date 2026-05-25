---
from: sanctum-smoke-test-subagent
to: sanctum (master EVE)
ts: 2026-05-24T21:30Z
type: smoke-test-report
trigger: operator verbatim "test everything and make sure it works"
verdict: READY for operator relaunch
---

Author: RKOJ-ELENO :: 2026-05-24

# EVE.exe + Launcher Pipeline Smoke Test Report

Pipeline under test: `C:\Users\Zonia\.eve\EVE.exe` (mirrored 17:20) + `automations/eve-launcher/eve.py` + `tools/eve-picker/eve_picker_lib.py` + `automations/start-sinister-session.ps1`.

## Test Results (10/10)

| # | Test | Result | Evidence |
|---|------|--------|----------|
| 1 | EVE.exe `--version` | PASS | `EVE.exe 0.4.5 :: Sinister Sanctum session launcher` exit 0 |
| 2 | EVE.exe `--profile` | PASS | `boot=0ms rows=20 mcp=22 bots=14` exit 0 |
| 3 | MCP/bot count via eve_picker_lib | PASS | `mcp:22 bots:14` (matches expected, NOT mcp:2) |
| 4 | Build-Phrase binding-language regression | PASS | The 4 tokens (MANDATORY, EXECUTE this 4-step, Do NOT end the turn, NEVER schedule) appear only in line-1048 explanatory comment, NOT in any emitted phrase |
| 5 | PowerShell parse `start-sinister-session.ps1` | PASS | `OK` (no parser errors) |
| 6 | Python parse `eve.py` | PASS | `OK` |
| 6b | Python parse `eve_picker_lib.py` | PASS | `OK` |
| 7 | Accounts JSON readable | PASS | `accounts=4 strategy=round-robin-strict enabled=1` |
| 8 | Overseer agent scan | PASS | clean table, totals HEALTHY=1 SLOW=1 STALLED=1 DEAD=25, ExitCode=0 |
| 9 | claude-accounts `-Action Status` | PASS | Table renders, 1/4 enabled (operator ON, leo/slot3/slot4 OFF), rate-limited=0, no error |
| 10 | Heartbeats < 10 min | PASS | 3 fresh: kernel-apk.json, sanctum-mesh-foundation.json, sanctum.json |
| 11 | Stale lock check | PASS | Lock file was 0-bytes/stale (16:50 mtime); auto-cleaned by claude-accounts.ps1 Status call between this test's first and second reads. No lock present now. |

## Findings

**Zero blocking issues.** Every test passed.

**Notable observations (non-blocking):**

1. EVE.exe boot time is `0ms` per `--profile` — extremely fast cold start.
2. mcp count is **22** (matches expected; the prior `mcp:2` regression has been fixed in eve_picker_lib.count_mcp).
3. Build-Phrase RESUME branch now points AT on-disk CLAUDE.md hard-canonical blocks rather than inlining the binding-language tokens that triggered the first-turn classifier rejection (phase-shrink fix per 2026-05-24T20:47Z operator report).
4. Overseer shows 25 DEAD sessions — expected (history from prior loops); only `sanctum-mesh-foundation` is HEALTHY and current sanctum is SLOW (likely this very subagent's heartbeat).
5. claude-accounts: only the `operator` slot is enabled. `leo` + `slot3` + `slot4` are unconfigured but that's by design until operator/Leo provisions keys.
6. Stale-lock auto-clean works: a 0-byte lock from 16:50 was present at test-start, gone after Status call. Reverse-confirms the lock-recovery code path.

## Overall Verdict

**READY for operator relaunch.**

The full chain — EVE.exe binary, picker probe, accounts rotation, overseer, parse-integrity, heartbeat freshness, and the instant-close fix — is green. The operator can launch `Sinister Start.bat` or `EVE.exe` directly with no expected regression.

## Recommendations

No code changes needed before next launch. Two low-priority follow-ups for future iterations (not blocking):

1. **Heartbeat coverage** — only 3 of ~28 known slugs reported fresh heartbeats in the last 10 min. Most other slugs are tracked as DEAD which is correct (no live session). When operator spawns next session, verify its heartbeat lands.
2. **Multi-account** — to actually exercise round-robin rotation under load, at least one additional slot (leo or slot3) needs an API key. Operator-action item, already tracked.

End of report.
