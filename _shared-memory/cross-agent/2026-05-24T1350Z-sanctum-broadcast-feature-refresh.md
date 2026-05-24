# [BROADCAST] feature-refresh 2026-05-24

From: Sinister Sanctum (EVE master orchestration)
To: all live lanes (18 visible_keys)
ts_utc: 2026-05-24T13:50Z
Author: RKOJ-ELENO :: 2026-05-24
ack_required: false (informational refresh -- pick up on next inbox_poll, no reply needed)

## Why this broadcast

Operator hard-canonical 2026-05-24: "i want the agents memory and systems on all agents to update with new features, changes, etc, tools. without having to close and reopen them. do this now and push a message to all live agents about everything we have done and all the new tools they have".

Single-shot refresh -- read once per lane and integrate into your active session. No restart required.

## The 15 new capabilities (shipped 2026-05-23 -> 2026-05-24)

### 1. EVE.exe v0.4.4 -- primary launcher
- Onedir build: `D:/Sinister Sanctum/automations/eve-launcher/dist/EVE/EVE.exe`
- New picker keys: 1-N projects, A all-lanes, G grant-autonomy, K kill-all, S status, R resume-last, T quantum-tools, H health, Q queue, U utterances, L loop-mode toggle, X exit
- New icon: `automations/eve-launcher/assets/eve-icon.ico`
- Source: `automations/eve-launcher/eve.py` + `tools/eve-picker/*`

### 2. Multi-account rotation v2 (4 slots)
Slots: operator, leo, slot3, slot4. Auto-rotation on 429.
CLI: `automations/claude-accounts.ps1 -Action {List,Add,Enable,Disable,Remove,Test,Spawned,Released,RateLimited}`

### 3. Quantum tools (T key)
10 tools: qbc-recall, triad-prescreen, drift-check, catalog-list, quantum-summary, brain_recall (QDB-R S1), daas_mcp (S4), saecd_diagnostic (S6), kkd_conjecture_closer (S7 Pearson +0.9825), qadp_promoter (S8).
Source: `tools/eve-picker/quantum_tools.py`

### 4. Health picker (H key)
Server-throttle vs plan-quota distinction. Auto-recommends SINISTER_FLEET_BURST_LIMIT=2 when throttle rate > 1/hr.
Source: `tools/eve-picker/health_tools.py`

### 5. Operator-utterance tracking
Log: `automations/log-operator-utterance.ps1`. Ack: `automations/ack-operator-utterance.ps1`. Doctrine: `_shared-memory/knowledge/operator-utterance-tracking-doctrine-2026-05-24.md`. Picker U shows last 5 unresolved. Cold-start step 8 reads last 10 new/acknowledged from `_shared-memory/operator-utterances.jsonl`.

### 6. GitHub-first sourcing doctrine
Helper: `automations/github-prior-art.ps1 -Topic <feature> -License <license> -MinStars <N>`. Doctrine: `_shared-memory/knowledge/github-first-sourcing-doctrine-2026-05-24.md`. Cold-start step 9.

### 7. Server-throttle vs plan-quota separation
"Server is temporarily limiting requests" = server-side throttle, NOT account rate-limit. Doctrine: `_shared-memory/knowledge/anthropic-server-throttle-vs-plan-quota-2026-05-24.md`. Env var: SINISTER_FLEET_BURST_LIMIT.

### 8. Loop mode default-ON fleet-wide
`automations/session-templates/agent-prefs.json` v3: defaults.loop_mode=true + skip_modes_prompt=true. Override: --no-loop. Picker L toggles.

### 9. Loop quality-gate
`automations/loop-quality-gate.ps1` checks 10 signals (brain>150, PROGRESS>300KB, resume-points>20/lane, queue>25, plans>12, eve.py>1500 lines, etc.). DEGRADED -> stop and consolidate.

### 10. No-bullshit doctrine (8 rules)
Doctrine: `_shared-memory/knowledge/no-bullshit-tested-before-claimed-doctrine-2026-05-23.md`. Rules: precise verbs / test before claiming / surface only verified work / continuous self-audit / forever-upgrade / laser focus / concise summaries / quality-degradation limits.

### 11. Authorship = RKOJ-ELENO
Every new .py/.ps1/.bat/.md/.rs/.ts/.js/.sh needs `Author: RKOJ-ELENO :: <date>` header.

### 12. Agent identity = EVE
Self-reference: EVE. Commit trailer: `Co-Authored-By: EVE (Sinister Sanctum orchestration agent) <noreply@anthropic.com>`. Doctrine: `_shared-memory/knowledge/agent-identity-eve.md`.

### 13. Agent autonomy (push your own branches)
Push your own `agent/<slug>/*` branches directly. Direct main via `sanctum-auto-push` daemon. Doctrine: `_shared-memory/knowledge/agent-autonomy-push-and-completion-2026-05-23.md`.

### 14. Sinister Generator fleet-wide
Image-gen via `tools/nano-banana/nano_banana/api.py`. Conservative balance: cache-first, one variant first, cap 6/task (~$0.039/img), re-use brand-locks, skip when text suffices, log spend in PROGRESS.

### 15. understand-anything mandatory step 0
Every cold-start: understand-anything:understand-explain on lane root BEFORE substantive work. Locked into `automations/canonical-protections-check.ps1`.

## How to integrate without restart
1. No code reload needed. Next Read picks up.
2. Heartbeat picks this up on next sinister-bus.inbox_poll (Rule 9).
3. Re-read CLAUDE.md cold-start steps 0/8/9.
4. Self-apply no-bullshit doctrine to end-of-turn formatting.

## Deep-read paths
- `_shared-memory/knowledge/no-bullshit-tested-before-claimed-doctrine-2026-05-23.md`
- `_shared-memory/knowledge/operator-utterance-tracking-doctrine-2026-05-24.md`
- `_shared-memory/knowledge/github-first-sourcing-doctrine-2026-05-24.md`
- `_shared-memory/knowledge/anthropic-server-throttle-vs-plan-quota-2026-05-24.md`
- `_shared-memory/knowledge/agent-autonomy-push-and-completion-2026-05-23.md`
- `_shared-memory/knowledge/agent-identity-eve.md`
- `_shared-memory/knowledge/do-not-revert-operator-canonical-protections-2026-05-23.md`
- `_shared-memory/knowledge/sanctioned-bypasses-doctrine-2026-05-21.md`
- `CLAUDE.md` (cold-start steps 0-9)

## No action required
Informational. Continue current work.

-- Sinister Sanctum / EVE
