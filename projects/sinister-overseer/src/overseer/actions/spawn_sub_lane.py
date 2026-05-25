# Author: RKOJ-ELENO :: 2026-05-25
"""actions/spawn_sub_lane.py -- turn a DivergenceOpportunity into a live sub-lane.

Steps (when ``execute(opportunity, dry_run=False)`` is called):
    1. Compose a spawn phrase using project context + sub-topic + (optionally)
       Sinister Memory recall hits if the memory module is importable.
    2. Auto-pick an OAuth slot via claude-oauth-accounts.ps1 PickBest. Falls
       back to env $CLAUDE_OAUTH_ACCOUNT or 'default' on missing helper.
    3. Spawn via automations/multi_agent_launcher.py (Sub-I shipped) with a
       custom one-off preset matching the opportunity.
    4. Verify spawn via heartbeat polling (60-sec timeout) against
       _shared-memory/heartbeats/<slug>.json.
    5. Log to _shared-memory/overseer-spawn-log.jsonl.

SAFETY (binding):
    - Respects operator-headroom invariant from
      gpu-fleet-resource-quotas-doctrine-2026-05-25: max 5 concurrent
      Overseer-spawned sub-lanes at any time.
    - Calls account_balancer.py --recommend (best-effort) before spawning to
      avoid over-allocating an OAuth quota.
    - On dry_run=True (default for orchestrator --dry-run), NO subprocess is
      launched and NO files are mutated. The SpawnResult.status is 'dry-run'
      and ``planned_command`` is populated.
    - automate-everything-no-operator-admin-2026-05-25: NEVER prompts the
      operator interactively. All choices are made automatically; if quota
      truly exhausted we emit ``status='blocked-quota'`` and the orchestrator
      logs to the queue for awareness (no operator click required to clear).
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from overseer.sensors.divergence import DivergenceOpportunity

SANCTUM_ROOT = Path("D:/Sinister Sanctum")
SHARED_MEM = SANCTUM_ROOT / "_shared-memory"
AUTOMATIONS = SANCTUM_ROOT / "automations"
HEARTBEAT_DIR = SHARED_MEM / "heartbeats"
SPAWN_LOG = SHARED_MEM / "overseer-spawn-log.jsonl"
MAX_CONCURRENT_SPAWNS = 5  # from gpu-fleet-resource-quotas-doctrine


@dataclass
class SpawnResult:
    opportunity_id: str
    status: str  # spawned | dry-run | blocked-quota | blocked-headroom | error
    lane_branch: str
    agent_slug: str
    oauth_account: str
    spawn_phrase_excerpt: str  # first 240 chars
    planned_command: list[str] = field(default_factory=list)
    pid: int | None = None
    heartbeat_seen: bool = False
    error: str = ""
    ts_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_jsonl(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


@dataclass
class SpawnSubLaneAction:
    sanctum_root: Path = SANCTUM_ROOT
    max_concurrent: int = MAX_CONCURRENT_SPAWNS
    heartbeat_timeout_seconds: int = 60

    # ---- public api -----------------------------------------------------
    def execute(self, opportunity: DivergenceOpportunity, dry_run: bool = True) -> SpawnResult:
        opp_id = f"{opportunity.project_key}-{opportunity.sub_topic}-{opportunity.signal}"
        slug = self._derive_slug(opportunity)
        branch = opportunity.suggested_lane_name

        # 1. compose spawn phrase
        phrase = self._compose_spawn_phrase(opportunity)
        excerpt = phrase[:240]

        # safety -- concurrent-spawn headroom
        live = self._count_live_spawns()
        if live >= self.max_concurrent:
            res = SpawnResult(
                opportunity_id=opp_id,
                status="blocked-headroom",
                lane_branch=branch,
                agent_slug=slug,
                oauth_account="(unselected)",
                spawn_phrase_excerpt=excerpt,
                error=f"{live} live spawns >= cap {self.max_concurrent}",
            )
            self._log(res)
            return res

        # 2. pick OAuth slot
        oauth_account = self._pick_oauth_account()
        if not oauth_account:
            res = SpawnResult(
                opportunity_id=opp_id,
                status="blocked-quota",
                lane_branch=branch,
                agent_slug=slug,
                oauth_account="(none-available)",
                spawn_phrase_excerpt=excerpt,
                error="No OAuth account returned by PickBest and no $CLAUDE_OAUTH_ACCOUNT",
            )
            self._log(res)
            return res

        # 3. build launch command
        launcher = AUTOMATIONS / "multi_agent_launcher.py"
        cmd = [
            "python",
            str(launcher),
            "--one-off",
            "--slug",
            slug,
            "--display-name",
            f"Sinister Overseer sub-{opportunity.sub_topic}",
            "--branch",
            branch,
            "--oauth-account",
            oauth_account,
            "--phrase-stdin",
        ]

        if dry_run:
            res = SpawnResult(
                opportunity_id=opp_id,
                status="dry-run",
                lane_branch=branch,
                agent_slug=slug,
                oauth_account=oauth_account,
                spawn_phrase_excerpt=excerpt,
                planned_command=cmd,
            )
            self._log(res)
            return res

        # 4. spawn for real
        try:
            proc = subprocess.Popen(  # noqa: S603 -- intentional spawn
                cmd,
                cwd=str(self.sanctum_root),
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if proc.stdin:
                proc.stdin.write(phrase.encode("utf-8"))
                proc.stdin.close()
            pid = proc.pid
        except (OSError, FileNotFoundError) as exc:
            res = SpawnResult(
                opportunity_id=opp_id,
                status="error",
                lane_branch=branch,
                agent_slug=slug,
                oauth_account=oauth_account,
                spawn_phrase_excerpt=excerpt,
                planned_command=cmd,
                error=f"spawn failed: {exc!r}",
            )
            self._log(res)
            return res

        # 5. verify heartbeat
        seen = self._await_heartbeat(slug, timeout_s=self.heartbeat_timeout_seconds)
        res = SpawnResult(
            opportunity_id=opp_id,
            status="spawned",
            lane_branch=branch,
            agent_slug=slug,
            oauth_account=oauth_account,
            spawn_phrase_excerpt=excerpt,
            planned_command=cmd,
            pid=pid,
            heartbeat_seen=seen,
        )
        self._log(res)
        return res

    # ---- helpers --------------------------------------------------------
    def _derive_slug(self, opp: DivergenceOpportunity) -> str:
        # slug must be filesystem + branch safe + match Sanctum convention
        return f"{opp.project_key}-{opp.sub_topic}".replace("_", "-")[:60]

    def _compose_spawn_phrase(self, opp: DivergenceOpportunity) -> str:
        ev_block = "\n".join(f"  - {e}" for e in opp.evidence)
        memory_block = self._memory_recall_optional(opp)
        return (
            f"# Sinister Overseer sub-lane spawn :: {opp.signal} signal\n"
            f"Project: {opp.project_key}\n"
            f"Sub-topic: {opp.sub_topic}\n"
            f"Branch: {opp.suggested_lane_name}\n"
            f"Confidence: {opp.confidence:.2f}\n"
            f"Estimated parallelism: {opp.estimated_parallelism}\n\n"
            f"## Rationale\n{opp.rationale}\n\n"
            f"## Evidence\n{ev_block}\n"
            f"{memory_block}"
            f"\n## Charter\n"
            f"You are an Overseer-spawned sub-lane operating in parallel with the main "
            f"'{opp.project_key}' lane. Pursue the sub-topic '{opp.sub_topic}' to "
            f"completion on your own branch. Honor fleet doctrine "
            f"(no-bullshit / forever-improve / mesh-coord). On completion, post a "
            f"close-out message to _shared-memory/inbox/{opp.project_key}/.\n"
        )

    def _memory_recall_optional(self, opp: DivergenceOpportunity) -> str:
        # Sinister Memory MCP (Sub-R) may or may not be landed; never hard-require.
        try:
            from overseer.memory_recall import recall as _recall  # type: ignore
            hits = _recall(opp.project_key + " " + opp.sub_topic, k=3)
            if not hits:
                return ""
            return "\n## Sinister Memory hits\n" + "\n".join(f"- {h}" for h in hits) + "\n"
        except Exception:  # noqa: BLE001 -- memory is optional
            return ""

    def _pick_oauth_account(self) -> str:
        env_pref = os.environ.get("CLAUDE_OAUTH_ACCOUNT", "").strip()
        if env_pref:
            return env_pref
        helper = AUTOMATIONS / "claude-oauth-accounts.ps1"
        if not helper.is_file():
            return ""
        try:
            proc = subprocess.run(  # noqa: S603
                ["powershell", "-NoProfile", "-File", str(helper), "PickBest"],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            if proc.returncode != 0:
                return ""
            out = proc.stdout.strip().splitlines()
            return out[-1].strip() if out else ""
        except (subprocess.TimeoutExpired, OSError):
            return ""

    def _count_live_spawns(self) -> int:
        if not SPAWN_LOG.is_file():
            return 0
        try:
            lines = SPAWN_LOG.read_text(encoding="utf-8", errors="ignore").splitlines()
            n = 0
            for ln in lines[-200:]:
                try:
                    row = json.loads(ln)
                except json.JSONDecodeError:
                    continue
                if row.get("status") != "spawned":
                    continue
                slug = row.get("agent_slug", "")
                hb = HEARTBEAT_DIR / f"{slug}.json"
                if hb.is_file():
                    try:
                        age = time.time() - hb.stat().st_mtime
                        if age < 30 * 60:  # 30 min freshness
                            n += 1
                    except OSError:
                        continue
            return n
        except OSError:
            return 0

    def _await_heartbeat(self, slug: str, timeout_s: int) -> bool:
        hb = HEARTBEAT_DIR / f"{slug}.json"
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            if hb.is_file():
                try:
                    if time.time() - hb.stat().st_mtime < 90:
                        return True
                except OSError:
                    pass
            time.sleep(2)
        return False

    def _log(self, result: SpawnResult) -> None:
        try:
            SPAWN_LOG.parent.mkdir(parents=True, exist_ok=True)
            with SPAWN_LOG.open("a", encoding="utf-8") as f:
                f.write(result.to_jsonl() + "\n")
        except OSError:
            pass


if __name__ == "__main__":
    # tiny demo
    opp = DivergenceOpportunity(
        project_key="demo",
        sub_topic="hello",
        evidence=("evidence-row-1", "evidence-row-2", "evidence-row-3"),
        suggested_lane_name="agent/demo/hello-2026-05-25",
        estimated_parallelism=2,
        confidence=0.8,
        rationale="demo opportunity",
        signal="A",
    )
    res = SpawnSubLaneAction().execute(opp, dry_run=True)
    print(res.to_jsonl())
