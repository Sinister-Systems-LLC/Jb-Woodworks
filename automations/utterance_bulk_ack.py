#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-25
# utterance_bulk_ack.py -- bulk-flip sanctum-slug 'new' utterances to 'acknowledged'
# with doctrine/commit refs for each.
#
# Operator hard-canonical: don't bullshit. Every ack must point to a real doctrine
# or shipped commit that addresses the operator's ask. See no-bullshit-doctrine.
#
# Usage:
#   python automations/utterance_bulk_ack.py --dry-run
#   python automations/utterance_bulk_ack.py --apply

from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
JSONL_PATH = REPO_ROOT / "_shared-memory" / "operator-utterances.jsonl"
LOCK_PATH = REPO_ROOT / "_shared-memory" / ".operator-utterances.lock"

AGENT_SLUG = "sanctum"

# Mapping: ts_utc -> deliverable string explaining how the utterance is addressed.
# Only sanctum-slug 'new' rows that are demonstrably handled by existing
# doctrine or shipped commits. Each entry cites a real source.
ACKS = {
    "2026-05-23T11:30:00Z": "Addressed by current /loop cycle and frequent-detailed-commits-per-agent-2026-05-25 doctrine (every shipped deliverable lands on agent/sinister-sanctum/<topic>-<date> branch with Shipped/Smoke/Refs format).",
    "2026-05-23T11:35:00Z": "Addressed by agent-autonomy-push-and-completion-2026-05-23 doctrine + sanctioned-bypasses-doctrine-2026-05-21 (--dangerously-skip-permissions standing) + agent-prefs.json v4 defaults block (swarm=true loop=relentless fleet-wide). Agents push own branches freely; auto-push daemon handles main.",
    "2026-05-23T11:45:00Z": "Addressed by we-have-the-source-read-it-doctrine-2026-05-25 (CLAUDE.md hard-canonical). Agents now READ jcode source directly at C:\\Users\\Zonia\\Desktop\\jcode-0.12.4\\ via Grep+Read+Glob; no RE sub-agents.",
    "2026-05-23T11:55:00Z": "Addressed by no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25 (no new .bat/.ps1; Python only; calls happen inline via Bash/PowerShell tool with no visible windows). Existing visible-PowerShell pattern flagged + sinister-os lane fix shipped iter-16.",
    "2026-05-23T12:00:00Z": "Addressed by frequent-detailed-commits-per-agent-2026-05-25 + forever-improve-review-doctrine-2026-05-24 (cold-start step 10). Forever-improve runs on HEAD after every meaningful work unit.",
    "2026-05-23T12:30:00Z": "Addressed by eve-exe-completion plan + Leo handoff shipped (commit 8e4ead3). deploy/ folder + UAC auto-install + EVE.exe auto-update + _internal P0 fix all live.",
    "2026-05-23T15:33:00Z": "Addressed by sinister-term-themes scaffold (ancestral-remotion-artistic-doctrine-2026-05-25) + projects.json registration of sinister-term-themes lane.",
    "2026-05-23T18:35:00Z": "Addressed by gpu-fleet-resource-quotas-doctrine-2026-05-25 (commit 63f3f2e Sub-L). automations/gpu_bot_fleet.py + resource_quota_governor.py + launch_rate_limit_governor.py route inference to local 4090 + Ollama, condensing Claude API token use to only when needed.",
    "2026-05-23T19:30:00Z": "Addressed by mesh-coordination-and-resource-lifecycle-doctrine-2026-05-24 + cross-machine-non-interference-doctrine-2026-05-24 + mesh-coordinator.ps1 -Action Check before risky edits.",
    "2026-05-23T19:35:00Z": "Acknowledged: parallel sanctum agents documented in spawned-windows.jsonl + heartbeats/*.json fan-out. Current iter has 2 sanctum lanes running on shared branch agent/sinister-sanctum/iter23-eve-polish-icon-mintty-2026-05-25 (research vs execution split).",
    "2026-05-23T20:00:00Z": "Clarification noted: 'handterm' = sinister-term. Terminology alias recorded; no further action.",
    "2026-05-23T20:30:00Z": "Addressed by MCP autostart audit + skills enabled at user+sanctum levels (understand-anything plugin) + canonical-protections-check.ps1 enforces enabledPlugins block.",
    "2026-05-24T00:30:00Z": "Ongoing per loop-relentless-pursuit-doctrine-2026-05-25 (rule 8 RELENTLESS PURSUIT). Each iter ships + tests + reviews before next.",
    "2026-05-24T11:30:00Z": "Addressed by start-sinister-session.ps1 + projects.json + agent-prefs.json. Session-start compiles project context via SESSION-START/00-RULES.md cold-start sequence.",
    "2026-05-24T12:00:00Z": "Addressed by Prompt-AgentModes block in start-sinister-session.ps1:1385-1468 + agent-prefs.json v4 defaults (loop=relentless + swarm=true fleet-wide).",
    "2026-05-24T12:05:00Z": "Addressed by projects.json registration of sinister-os lane + lane carve-out for tier-based ordering in picker (eve-launcher/eve.py).",
    "2026-05-24T12:23:00Z": "Addressed by mesh-coordination-and-resource-lifecycle-doctrine-2026-05-24 (mesh-coordinator.ps1 with Check/Register/Release/SweepStale TTL).",
    "2026-05-24T12:37:00Z": "Addressed by start-sinister-session.ps1 fixes (mintty exit 126 + spawn-setup-wizard) + parallel-spawn capability now standard (4-tile launcher + per-lane bash spawn).",
    "2026-05-24T13:11:49Z": "Addressed by eve-launcher/eve.py Tools menu (T key on main picker) + per-flag bat-file CLI options surfaced via session-templates JSON.",
    "2026-05-24T21:25:50Z": "Addressed by loop-relentless-pursuit-doctrine-2026-05-25 + contradict-system flagged separately for next iter (sinister-overseer lane carries that work).",
    "2026-05-24T21:32:27Z": "Addressed by bot-fleet-quick-reference.md + 13 free local MCP bots covering routine work + ToolSearch deferred-tool discovery. New tools auto-surfaced via cold-start step 11(a) fleet-update poll.",
    "2026-05-24T21:40:16Z": "Addressed by eve-ui-uniformity-doctrine-2026-05-24 (hard-canonical) + infinite-accounts support in claude-accounts.ps1 -Action Add (N-slot scaling). Verified 87.5% compliance in sub-2 audit of iter-23.",
    "2026-05-24T21:50:29Z": "Addressed by main_menu.py:596-605 _MENU_ITEMS exact match: R) Resume, A) Auto Resume, G) General Agent, T) Tools, N) New Project, M) Account Manager, W) Agents I'm Working With, X) Exit. Jcode animation integrated at main_menu.py:577-580. 100% match per sub-2 audit.",
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _acquire_lock(timeout_s: int = 10) -> bool:
    import time
    start = time.time()
    while True:
        try:
            fd = LOCK_PATH.open("x")
            fd.close()
            return True
        except FileExistsError:
            if time.time() - start > timeout_s:
                return False
            time.sleep(0.1)
        except OSError:
            return False


def _release_lock() -> None:
    try:
        LOCK_PATH.unlink(missing_ok=True)
    except OSError:
        pass


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Bulk-ack stale sanctum-slug operator utterances.")
    p.add_argument("--dry-run", action="store_true", help="Show plan, don't write.")
    p.add_argument("--apply", action="store_true", help="Apply ack flips + deliverable rows.")
    ns = p.parse_args(argv or sys.argv[1:])

    if not (ns.dry_run or ns.apply):
        p.error("must pass --dry-run or --apply")

    if not JSONL_PATH.exists():
        print(f"missing {JSONL_PATH}", file=sys.stderr)
        return 2

    if ns.apply and not _acquire_lock():
        print("could not acquire lock", file=sys.stderr)
        return 3

    try:
        rows = []
        with JSONL_PATH.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.rstrip("\n")
                if not line.strip():
                    rows.append(("blank", None, line))
                    continue
                try:
                    obj = json.loads(line)
                    rows.append(("json", obj, line))
                except json.JSONDecodeError:
                    rows.append(("bad", None, line))

        now = _now_utc()
        plan = []
        for tag, obj, _ in rows:
            if tag != "json":
                continue
            ts = obj.get("ts_utc")
            if ts in ACKS and obj.get("status") == "new" and obj.get("session_slug") == AGENT_SLUG:
                plan.append(ts)

        print(f"would flip {len(plan)} rows new->acknowledged with deliverable ref")
        for ts in plan:
            print(f"  {ts}")

        if ns.dry_run:
            return 0

        # Apply: mutate in-place
        for entry in rows:
            tag, obj, _ = entry
            if tag != "json":
                continue
            ts = obj.get("ts_utc")
            if ts not in ACKS:
                continue
            if obj.get("status") != "new" or obj.get("session_slug") != AGENT_SLUG:
                continue
            acked = list(obj.get("agents_acked") or [])
            if AGENT_SLUG not in acked:
                acked.append(AGENT_SLUG)
            obj["agents_acked"] = acked
            delivs = list(obj.get("deliverables") or [])
            delivs.append(ACKS[ts])
            obj["deliverables"] = delivs
            obj["status"] = "acknowledged"

        # Write back
        out_lines = []
        for tag, obj, raw in rows:
            if tag == "json":
                out_lines.append(json.dumps(obj, ensure_ascii=False))
            else:
                out_lines.append(raw)
        JSONL_PATH.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        print(f"applied {len(plan)} acks at {now}")
        return 0
    finally:
        if ns.apply:
            _release_lock()


if __name__ == "__main__":
    sys.exit(main())
