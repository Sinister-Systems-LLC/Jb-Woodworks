<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# Lane Plan :: test-modes-verify

> Per-lane completion plan. Composes with operator-utterance-tracking + forever-improve + no-bullshit verbs.
> Each row: `- [ ] <ts_utc> :: <priority> :: <task>`  (status moves between sections; never delete)

## TODO
- [ ] 2026-05-24T16:59:12Z :: normal :: Investigate sinister-chatbot pollution (200/307/401/502 files at repo root); surface root-cause script to chatbot lane
- [ ] 2026-05-24T16:59:12Z :: high :: Resolve R29 by triggering rkoj-iter7 -> main merge (0 conflicts confirmed; 74 ahead / 18 behind)

## IN-PROGRESS

## DONE
- [x] 2026-05-24T17:13:31Z :: high :: Add P13 canonical-protection (lane resume-point coverage); flags lanes missing resume-points + offers seed-resume-points command  // evidence: canonical-protections-check now reports P13 OK with all 16 previously-gapped lanes covered
- [x] 2026-05-24T17:04:03Z :: high :: Build seed-resume-points.ps1 + apply across fleet (16 lanes seeded, 0 gaps remain)  // evidence: 16 lanes seeded; gaps-after=0; operator directive 2026-05-24T17:01:09Z fulfilled
- [x] 2026-05-24T16:59:13Z :: high :: Fix R9-R10 forge-memory-bridge gap via Build-Phrase edit  // evidence: commit 02aa0c7 (bundled by spawned lane); probe R9-R10 flipped FAIL -> PASS
- [x] 2026-05-24T16:59:13Z :: low :: Expand probe to detect runtime gaps not just file presence (e.g. R8 actually call Ruflo MCP, R14 measure keypress latency)  // evidence: commit fe6341b; 26/31 PASS / 1 REAL-FAIL / 4 EXPECTED-GAP

