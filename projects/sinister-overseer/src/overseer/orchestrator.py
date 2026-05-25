# Author: RKOJ-ELENO :: 2026-05-25
"""orchestrator.py -- Overseer main loop for divergence scan + approval gate + spawn.

Cycle:
    every 5 min:
        opps = divergence_sensor.scan(fleet_state)
        for opp in opps:
            if opp.confidence >= AUTO_APPROVE_FLOOR (default 0.90):
                action.execute(opp, dry_run=False)
            elif opp.confidence >= PROPOSE_FLOOR (default 0.70):
                propose_to_operator_queue(opp)
            else:
                ignore (logged at DEBUG)

The propose-to-operator-queue mechanism uses touch-file approval per
automate-everything-no-operator-admin-2026-05-25 (operator never clicks UAC;
operator just `touch _shared-memory/overseer-approvals/<opp-id>.json` to
approve, or `touch _shared-memory/overseer-approvals/<opp-id>.deny` to reject).

Outcome tracking (simple reinforcement loop):
    On lane completion (close-out message in _shared-memory/inbox/<lane>/ with
    kind='spawn-close-out'), record outcome in
    _shared-memory/overseer-divergence-outcomes.jsonl and gently adjust
    confidence thresholds:
        success rate >= 0.8 over last 10  -> AUTO_APPROVE_FLOOR -= 0.02 (more autonomous)
        success rate <= 0.5 over last 10  -> AUTO_APPROVE_FLOOR += 0.05 (more cautious)
        clamped to [0.80, 0.99]

Composes with:
    sensors/divergence.py    (the scan)
    sensors/analyzer.py      (existing sensors; orchestrator polls both buses)
    contradiction.py         (every spawn proposal also passes through
                              contradiction.run_full_contradiction_check)
    actions/spawn_sub_lane.py(the apply path)
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from overseer.actions.spawn_sub_lane import SpawnResult, SpawnSubLaneAction
from overseer.sensors.divergence import DivergenceOpportunity, DivergenceSensor

SANCTUM_ROOT = Path("D:/Sinister Sanctum")
SHARED_MEM = SANCTUM_ROOT / "_shared-memory"
APPROVALS_DIR = SHARED_MEM / "overseer-approvals"
OUTCOMES_LOG = SHARED_MEM / "overseer-divergence-outcomes.jsonl"
QUEUE = SHARED_MEM / "OPERATOR-ACTION-QUEUE.md"

DEFAULT_AUTO_APPROVE_FLOOR = 0.90
DEFAULT_PROPOSE_FLOOR = 0.70
DEFAULT_SCAN_INTERVAL_S = 300  # 5 min


@dataclass
class OrchestratorState:
    auto_approve_floor: float = DEFAULT_AUTO_APPROVE_FLOOR
    propose_floor: float = DEFAULT_PROPOSE_FLOOR
    scan_interval_s: int = DEFAULT_SCAN_INTERVAL_S
    iterations: int = 0
    proposed_total: int = 0
    spawned_total: int = 0
    last_scan_utc: str = ""
    history: list[dict] = field(default_factory=list)


@dataclass
class OverseerOrchestrator:
    sanctum_root: Path = SANCTUM_ROOT
    sensor: DivergenceSensor = field(default_factory=DivergenceSensor)
    action: SpawnSubLaneAction = field(default_factory=SpawnSubLaneAction)
    state: OrchestratorState = field(default_factory=OrchestratorState)

    # ---- public api ----------------------------------------------------
    def run_once(self, dry_run: bool = True) -> dict:
        """One scan pass. Returns a summary dict."""
        self.state.iterations += 1
        self.state.last_scan_utc = datetime.now(timezone.utc).isoformat()

        try:
            opps = self.sensor.scan(None)
        except Exception as exc:  # noqa: BLE001 -- never crash the loop
            return {
                "ok": False,
                "iter": self.state.iterations,
                "error": repr(exc),
                "opportunities": 0,
            }

        proposed: list[DivergenceOpportunity] = []
        auto_spawned: list[SpawnResult] = []
        ignored = 0

        for opp in opps:
            if opp.confidence >= self.state.auto_approve_floor:
                res = self.action.execute(opp, dry_run=dry_run)
                auto_spawned.append(res)
                if res.status == "spawned":
                    self.state.spawned_total += 1
            elif opp.confidence >= self.state.propose_floor:
                self._propose_to_operator_queue(opp)
                proposed.append(opp)
                self.state.proposed_total += 1
            else:
                ignored += 1

        # Process any approval touch-files for previously proposed opps.
        approved = self._process_approvals(dry_run=dry_run)
        auto_spawned.extend(approved)

        # Adjust thresholds via outcomes ledger (cheap; safe to call each iter).
        self._adjust_thresholds()

        summary = {
            "ok": True,
            "iter": self.state.iterations,
            "opportunities_scanned": len(opps),
            "proposed_to_operator": len(proposed),
            "auto_spawned": len(auto_spawned),
            "ignored_low_confidence": ignored,
            "auto_approve_floor": round(self.state.auto_approve_floor, 3),
            "propose_floor": round(self.state.propose_floor, 3),
            "scan_utc": self.state.last_scan_utc,
            "dry_run": dry_run,
        }
        self.state.history.append(summary)
        return summary

    def run_loop(self, dry_run: bool = True, max_iters: int | None = None) -> None:
        i = 0
        while True:
            self.run_once(dry_run=dry_run)
            i += 1
            if max_iters is not None and i >= max_iters:
                break
            time.sleep(self.state.scan_interval_s)

    # ---- helpers -------------------------------------------------------
    def _propose_to_operator_queue(self, opp: DivergenceOpportunity) -> None:
        opp_id = self._opp_id(opp)
        APPROVALS_DIR.mkdir(parents=True, exist_ok=True)
        marker = APPROVALS_DIR / f"{opp_id}.proposed.json"
        try:
            marker.write_text(
                json.dumps(
                    {
                        "opp_id": opp_id,
                        "project_key": opp.project_key,
                        "sub_topic": opp.sub_topic,
                        "branch": opp.suggested_lane_name,
                        "confidence": opp.confidence,
                        "rationale": opp.rationale,
                        "evidence": list(opp.evidence),
                        "signal": opp.signal,
                        "proposed_utc": datetime.now(timezone.utc).isoformat(),
                        "approve_path": str(APPROVALS_DIR / f"{opp_id}.json"),
                        "deny_path": str(APPROVALS_DIR / f"{opp_id}.deny"),
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
        except OSError:
            pass

    def _process_approvals(self, dry_run: bool) -> list[SpawnResult]:
        results: list[SpawnResult] = []
        if not APPROVALS_DIR.is_dir():
            return results
        for f in APPROVALS_DIR.glob("*.proposed.json"):
            opp_id = f.name[: -len(".proposed.json")]
            approve = APPROVALS_DIR / f"{opp_id}.json"
            deny = APPROVALS_DIR / f"{opp_id}.deny"
            if deny.is_file():
                try:
                    f.unlink()
                except OSError:
                    pass
                continue
            if not approve.is_file():
                continue
            try:
                doc = json.loads(f.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            opp = DivergenceOpportunity(
                project_key=doc["project_key"],
                sub_topic=doc["sub_topic"],
                evidence=tuple(doc.get("evidence", [])),
                suggested_lane_name=doc["branch"],
                estimated_parallelism=2,
                confidence=doc["confidence"],
                rationale=doc["rationale"],
                signal=doc.get("signal", "?"),
            )
            res = self.action.execute(opp, dry_run=dry_run)
            results.append(res)
            try:
                f.unlink()
            except OSError:
                pass
        return results

    @staticmethod
    def _opp_id(opp: DivergenceOpportunity) -> str:
        return f"{opp.project_key}-{opp.sub_topic}-{opp.signal}".replace("/", "-")

    def _adjust_thresholds(self) -> None:
        if not OUTCOMES_LOG.is_file():
            return
        try:
            lines = OUTCOMES_LOG.read_text(encoding="utf-8", errors="ignore").splitlines()[-10:]
        except OSError:
            return
        if len(lines) < 5:
            return
        succ = 0
        total = 0
        for ln in lines:
            try:
                row = json.loads(ln)
            except json.JSONDecodeError:
                continue
            total += 1
            if row.get("outcome") == "success":
                succ += 1
        if total == 0:
            return
        rate = succ / total
        if rate >= 0.8:
            self.state.auto_approve_floor = max(0.80, self.state.auto_approve_floor - 0.02)
        elif rate <= 0.5:
            self.state.auto_approve_floor = min(0.99, self.state.auto_approve_floor + 0.05)


# ---- CLI ------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="overseer-orchestrator",
        description="Sinister Overseer divergence orchestrator (scan + propose + spawn).",
    )
    p.add_argument("--dry-run", action="store_true", help="Do not spawn or mutate files.")
    p.add_argument("--scan-only", action="store_true", help="One scan pass then exit.")
    p.add_argument("--max-iters", type=int, default=None, help="Stop after N iterations.")
    p.add_argument("--scan-interval", type=int, default=DEFAULT_SCAN_INTERVAL_S)
    p.add_argument("--auto-approve-floor", type=float, default=DEFAULT_AUTO_APPROVE_FLOOR)
    p.add_argument("--propose-floor", type=float, default=DEFAULT_PROPOSE_FLOOR)
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    orch = OverseerOrchestrator()
    orch.state.auto_approve_floor = args.auto_approve_floor
    orch.state.propose_floor = args.propose_floor
    orch.state.scan_interval_s = args.scan_interval
    if args.scan_only:
        summary = orch.run_once(dry_run=args.dry_run)
        sys.stdout.write(json.dumps(summary, indent=2) + "\n")
        return 0
    try:
        orch.run_loop(dry_run=args.dry_run, max_iters=args.max_iters)
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
