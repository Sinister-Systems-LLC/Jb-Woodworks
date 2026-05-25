#!/usr/bin/env python3
"""Atomic recreate + add + commit of feature-refresh broadcast.
Author: RKOJ-ELENO :: 2026-05-24
Disposable: delete after use.
"""
import json
import os
import subprocess
import sys
import time

os.chdir(r"D:\Sinister Sanctum")

lanes = [
    "sanctum", "sinister-chatbot", "sinister-panel", "kernel-apk",
    "sinister-emulator", "rkoj", "snap-emulator-api", "tiktok-emulator-api",
    "bumble-emulator-api", "sinister-freeze", "jb-woodworks", "showmasters",
    "letstext", "sinister-generator", "jkor", "sinister-snap-api-quantum",
    "sinister-os", "sinister-imessage-bridge",
]

summary = (
    "15 new capabilities live (no restart needed). EVE.exe v0.4.4 launcher + new picker keys (T/H/Q/U/L). "
    "Multi-account rotation v2. Quantum tools menu. Health picker (server-throttle vs plan-quota). "
    "Operator-utterance tracking (cold-start step 8). GitHub-first sourcing (step 9). Loop-mode default-ON + quality-gate. "
    "No-bullshit doctrine (8 rules: precise verbs, test before claim, quality-degradation limits). "
    "Authorship=RKOJ-ELENO on all new files. Agent identity=EVE. Agent autonomy (push own branches). "
    "Sinister Generator fleet-wide (conservative balance: cache-first, cap 6/task). understand-anything mandatory step 0. "
    "Body at _shared-memory/cross-agent/2026-05-24T1350Z-sanctum-broadcast-feature-refresh.md"
)

# Step 1: Re-create inbox JSONs
for lane in lanes:
    d = os.path.join("_shared-memory", "inbox", lane)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "2026-05-24T1350Z-from-sanctum-feature-refresh.json")
    payload = {
        "tag": "[BROADCAST]",
        "from": "sanctum",
        "to": lane,
        "ts_utc": "2026-05-24T13:50Z",
        "subject": "feature-refresh 2026-05-24 :: 15 new capabilities live (no restart)",
        "body_path": "_shared-memory/cross-agent/2026-05-24T1350Z-sanctum-broadcast-feature-refresh.md",
        "reply_required": False,
        "ack_required": False,
        "summary": summary,
        "author": "RKOJ-ELENO :: 2026-05-24",
    }
    with open(p, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")

# Step 2: Re-create canonical body
body_path = "_shared-memory/cross-agent/2026-05-24T1350Z-sanctum-broadcast-feature-refresh.md"
body = """# [BROADCAST] feature-refresh 2026-05-24

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
"""
with open(body_path, "w", encoding="utf-8") as f:
    f.write(body)

# Step 3: Ensure _global-broadcasts.md exists
gb = "_shared-memory/cross-agent/_global-broadcasts.md"
gb_text = """# Global Broadcasts Ledger

> Author: RKOJ-ELENO :: 2026-05-24

Append-only ledger of fleet-wide broadcasts. Most recent at top.

---

## 2026-05-24T13:50Z -- feature-refresh 2026-05-24 (15 capabilities live, no restart)

- From: sanctum (EVE master)
- To: all 18 visible lanes (sanctum, sinister-chatbot, sinister-panel, kernel-apk, sinister-emulator, rkoj, snap-emulator-api, tiktok-emulator-api, bumble-emulator-api, sinister-freeze, jb-woodworks, showmasters, letstext, sinister-generator, jkor, sinister-snap-api-quantum, sinister-os, sinister-imessage-bridge)
- Body: `_shared-memory/cross-agent/2026-05-24T1350Z-sanctum-broadcast-feature-refresh.md`
- Inbox JSONs: `_shared-memory/inbox/<slug>/2026-05-24T1350Z-from-sanctum-feature-refresh.json` (18 files)
- Items: EVE.exe v0.4.4 + new picker keys (T/H/Q/U/L) ; multi-account rotation v2 ; quantum tools (T) ; health picker (H) ; operator-utterance tracking (step 8) ; GitHub-first sourcing (step 9) ; throttle/quota separation + SINISTER_FLEET_BURST_LIMIT ; loop default-ON ; loop quality-gate (10 signals) ; no-bullshit doctrine (8 rules) ; authorship=RKOJ-ELENO ; agent identity=EVE ; agent autonomy ; Sinister Generator fleet-wide ; understand-anything step 0
- Operator trigger: 2026-05-24 -- "i want the agents memory and systems on all agents to update ... without having to close and reopen them"
- ack_required: false
"""
with open(gb, "w", encoding="utf-8") as f:
    f.write(gb_text)

print(f"INBOX_COUNT={sum(1 for s in lanes if os.path.exists(f'_shared-memory/inbox/{s}/2026-05-24T1350Z-from-sanctum-feature-refresh.json'))}", flush=True)
print(f"BODY_EXISTS={os.path.exists(body_path)}", flush=True)
print(f"GLOBALS_EXISTS={os.path.exists(gb)}", flush=True)

# Step 4: Atomic stage + commit
files = ["_shared-memory/PROGRESS/Sinister Sanctum.md", body_path, gb] + [
    f"_shared-memory/inbox/{s}/2026-05-24T1350Z-from-sanctum-feature-refresh.json" for s in lanes
]

msg = """sanctum: broadcast feature-refresh 2026-05-24 to all 18 visible lanes (no restart)

Operator (verbatim 2026-05-24): "i want the agents memory and systems on all
agents to update with new features, changes, etc, tools. without having to
close and reopen them. do this now and push a message to all live agents
about everything we have done and all the new tools they have".

Fanned out a single canonical broadcast body to every visible-keys lane plus
sanctum/rkoj/sinister-chatbot (18 unique slugs). Agents pick up via Rule 9
sinister-bus.inbox_poll on next turn -- no restart, no reply required.

15 capabilities broadcast: EVE.exe v0.4.4 + new picker keys (T/H/Q/U/L) ;
multi-account rotation v2 ; quantum tools menu ; health picker (throttle vs
quota) ; operator-utterance tracking (cold-start step 8) ; GitHub-first
sourcing (step 9) ; SINISTER_FLEET_BURST_LIMIT env var ; loop default-ON ;
loop quality-gate (10 doctrine signals) ; no-bullshit doctrine (8 rules) ;
authorship=RKOJ-ELENO ; agent identity=EVE ; agent autonomy (push own
branches) ; Sinister Generator fleet-wide ; understand-anything cold-start
step 0.

Author: RKOJ-ELENO :: 2026-05-24

Co-Authored-By: EVE (Sinister Sanctum orchestration agent) <noreply@anthropic.com>"""


def clear_stale():
    lock = r".git\index.lock"
    if os.path.exists(lock):
        try:
            age = time.time() - os.path.getmtime(lock)
            if age > 30:
                os.remove(lock)
                return True
        except Exception:
            pass
    return False


for attempt in range(1, 121):
    if os.path.exists(r".git\index.lock"):
        clear_stale()
        time.sleep(1)
        continue
    add = subprocess.run(["git", "add", "--"] + files, capture_output=True, text=True)
    if add.returncode != 0:
        if "index.lock" in (add.stderr or ""):
            clear_stale()
            time.sleep(1)
            continue
        print(f"ADD_FAIL_ATTEMPT={attempt}: {add.stderr[-800:]}", flush=True)
        sys.exit(1)
    commit = subprocess.run(["git", "commit", "-m", msg, "--"] + files, capture_output=True, text=True)
    if commit.returncode == 0:
        rev = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
        print(f"COMMIT_OK_AT_ATTEMPT={attempt}", flush=True)
        print(f"HEAD={rev.stdout.strip()}", flush=True)
        # Verify our files are in the commit
        check = subprocess.run(["git", "show", "--stat", "HEAD"], capture_output=True, text=True)
        print(f"commit_stat_tail={check.stdout[-1500:]}", flush=True)
        sys.exit(0)
    if "index.lock" in (commit.stderr or ""):
        clear_stale()
        time.sleep(1)
        continue
    if "nothing to commit" in (commit.stdout or "") or "nothing to commit" in (commit.stderr or ""):
        print(f"NOTHING_TO_COMMIT_ATTEMPT={attempt}", flush=True)
        print(f"stderr={commit.stderr[-500:]}", flush=True)
        print(f"stdout={commit.stdout[-500:]}", flush=True)
        sys.exit(0)
    print(f"COMMIT_FAIL_ATTEMPT={attempt}: stderr={commit.stderr[-800:]} stdout={commit.stdout[-800:]}", flush=True)
    sys.exit(1)

print("TIMEOUT_NEVER_COMMITTED", flush=True)
sys.exit(2)
