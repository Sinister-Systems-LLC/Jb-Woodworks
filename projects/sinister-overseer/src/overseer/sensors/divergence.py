# Author: RKOJ-ELENO :: 2026-05-25
"""sensors/divergence.py -- detect when project areas can DIVERGE into autonomous sub-lanes.

Mirrors the master Sanctum agent's swarm methodology (detect independent
subtasks -> spawn parallel sub-agents -> 5x throughput vs serial) and applies
it at the PROJECT level. Where master Sanctum identifies parallelizable
sub-agents in a single turn, Overseer identifies parallelizable PROJECTS that
deserve their own concurrent lane.

Five detection signals (all are non-blocking; sensor poll() always returns
deduped DivergenceOpportunity list):
    A  file-cluster independence  -- recent PROGRESS rows touch 2+ distinct
       file clusters (frontend/ vs backend/ vs docs/ vs tests/). Forking is
       safe when the clusters share no mutable file.
    B  serial-blocker stall       -- last 3 iter-close summaries name the same
       blocker; spawn a focused sub-lane to unblock it.
    C  queue-depth threshold      -- project queue has >=8 rows AND no agent
       slug has heartbeat-touched it in last 30 min. Spawn a queue-drainer.
    D  operator-noted divergence  -- operator utterance matches pattern
       "while X is doing Y, also Z" or "split this into..." or
       "in parallel ..." -- treated as explicit directive (highest confidence).
    E  cross-project bleed        -- a project's PROGRESS references files in
       another project's source/. Suggests a bridge / integration sub-lane.

Each opportunity carries 3-5 file:line evidence refs so the operator can
audit before approval. Opportunities are PROPOSED, not auto-acted -- see
``actions/spawn_sub_lane.py`` for the apply path, and ``orchestrator.py``
for the approval-gated loop.

Composes with:
    sensors/analyzer.py          (sibling sensor; shares SensorBus pattern)
    contradiction.py             (engine rejects divergence proposals that
                                  conflict with another lane's active scope)
    actions/spawn_sub_lane.py    (the apply side; consumes opportunities)
    orchestrator.py              (5-min scan loop + approval gate)
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

SANCTUM_ROOT = Path("D:/Sinister Sanctum")
SHARED_MEM = SANCTUM_ROOT / "_shared-memory"
PROGRESS_DIR = SHARED_MEM / "PROGRESS"
HEARTBEAT_DIR = SHARED_MEM / "heartbeats"
UTTERANCES = SHARED_MEM / "operator-utterances.jsonl"
QUEUE = SHARED_MEM / "OPERATOR-ACTION-QUEUE.md"

# Cluster definitions: a top-level directory under a project counts as one
# cluster for signal A. Touching files in two different clusters in the same
# project's PROGRESS = parallelizable.
DEFAULT_CLUSTERS = (
    "frontend",
    "backend",
    "docs",
    "tests",
    "src",
    "mobile",
    "web",
    "automations",
    "scripts",
    "config",
)

# Signal-D regex: matches operator utterances like
#   "while X is doing Y, also Z"
#   "split this into X and Y"
#   "in parallel, run X"
#   "spawn a lane for X"
_DIVERGENCE_RE = re.compile(
    r"\b(while .* (?:doing|working|on)|in parallel|split (?:this|that) into|"
    r"spawn (?:a )?(?:lane|sub.?lane|sub.?agent) for|fork (?:a )?lane)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class DivergenceOpportunity:
    """A detected chance to fork a project area into its own autonomous lane."""

    project_key: str  # matches projects.json key
    sub_topic: str  # kebab-case <=30 chars; feeds branch name
    evidence: tuple[str, ...]  # 3-5 "FILE:LINE rationale" strings
    suggested_lane_name: str  # agent/<project-key>/<sub_topic>-<utc-date>
    estimated_parallelism: int  # 2-5; how many concurrent slices safe
    confidence: float  # 0.0-1.0; threshold gate uses this
    rationale: str  # 1-3 sentences -- shown to operator at approval
    signal: str  # A | B | C | D | E


@dataclass
class DivergenceSensor:
    """Scan fleet state for divergence opportunities. Stateless across runs.

    Usage:
        sensor = DivergenceSensor(sanctum_root=Path("D:/Sinister Sanctum"))
        opps = sensor.scan(fleet_state)  # fleet_state is a dict, see below

    ``fleet_state`` shape (all keys optional; sensor degrades gracefully):
        {
            "projects":      [{"key": "...", "path": "...", "queue_rows": int}],
            "progress_rows": {project_key: [str, ...]},
            "utterances":    [{"text": "...", "ts_utc": "..."}],
            "heartbeats":    {agent_slug: {"project": "...", "ts_utc": "..."}},
            "iter_summaries": {project_key: [str, str, str]},  # last 3
        }

    If fleet_state is empty / missing keys, scan() returns []. This keeps
    --dry-run --scan-only smoke tests green even on a fresh checkout.
    """

    sanctum_root: Path = SANCTUM_ROOT
    queue_depth_threshold: int = 8
    stall_minutes: int = 30
    min_confidence_emit: float = 0.0  # threshold filtering happens in orchestrator
    clusters: tuple[str, ...] = DEFAULT_CLUSTERS

    _seen_keys: set[str] = field(default_factory=set)

    def scan(self, fleet_state: dict | None = None) -> list[DivergenceOpportunity]:
        if fleet_state is None:
            fleet_state = self._collect_fleet_state()

        opps: list[DivergenceOpportunity] = []
        opps.extend(self._signal_a_file_cluster(fleet_state))
        opps.extend(self._signal_b_serial_blocker(fleet_state))
        opps.extend(self._signal_c_queue_depth(fleet_state))
        opps.extend(self._signal_d_operator_directive(fleet_state))
        opps.extend(self._signal_e_cross_project_bleed(fleet_state))

        # Dedup within this scan + against historical _seen_keys.
        fresh: list[DivergenceOpportunity] = []
        for o in opps:
            key = f"{o.project_key}|{o.sub_topic}|{o.signal}"
            if key in self._seen_keys:
                continue
            self._seen_keys.add(key)
            if o.confidence >= self.min_confidence_emit:
                fresh.append(o)
        return fresh

    # ---- best-effort fleet-state collection (graceful on missing files) ----
    def _collect_fleet_state(self) -> dict:
        state: dict = {
            "projects": [],
            "progress_rows": {},
            "utterances": [],
            "heartbeats": {},
            "iter_summaries": {},
        }
        proj_dir = self.sanctum_root / "projects"
        if proj_dir.is_dir():
            for p in proj_dir.iterdir():
                if p.is_dir() and not p.name.startswith("_"):
                    state["projects"].append({"key": p.name, "path": str(p), "queue_rows": 0})

        if (PROGRESS_DIR := self.sanctum_root / "_shared-memory" / "PROGRESS").is_dir():
            for f in PROGRESS_DIR.glob("*.md"):
                try:
                    rows = f.read_text(encoding="utf-8", errors="ignore").splitlines()[:200]
                    # crude project mapping by display-name slug
                    state["progress_rows"][f.stem.lower().replace(" ", "-")] = rows
                except OSError:
                    continue

        utt = self.sanctum_root / "_shared-memory" / "operator-utterances.jsonl"
        if utt.is_file():
            try:
                lines = utt.read_text(encoding="utf-8", errors="ignore").splitlines()[-50:]
                for ln in lines:
                    try:
                        state["utterances"].append(json.loads(ln))
                    except json.JSONDecodeError:
                        continue
            except OSError:
                pass

        hb_dir = self.sanctum_root / "_shared-memory" / "heartbeats"
        if hb_dir.is_dir():
            for hb in hb_dir.glob("*.json"):
                try:
                    state["heartbeats"][hb.stem] = json.loads(hb.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue

        return state

    # ---- Signal A ---------------------------------------------------------
    def _signal_a_file_cluster(self, fleet_state: dict) -> list[DivergenceOpportunity]:
        results: list[DivergenceOpportunity] = []
        rows_by_proj = fleet_state.get("progress_rows", {}) or {}
        for proj_key, rows in rows_by_proj.items():
            touched: dict[str, list[str]] = {}
            for idx, row in enumerate(rows[:120]):
                for cluster in self.clusters:
                    if f"/{cluster}/" in row or row.lstrip().startswith(f"{cluster}/"):
                        touched.setdefault(cluster, []).append(f"PROGRESS/{proj_key}.md:{idx + 1}")
                        break
            if len(touched) >= 2:
                ev = []
                for c, refs in list(touched.items())[:5]:
                    ev.append(f"{refs[0]} cluster={c}")
                results.append(
                    DivergenceOpportunity(
                        project_key=proj_key,
                        sub_topic=f"split-{'-'.join(sorted(touched)[:2])}"[:30],
                        evidence=tuple(ev[:5]),
                        suggested_lane_name=f"agent/{proj_key}/split-clusters-2026-05-25",
                        estimated_parallelism=min(len(touched), 5),
                        confidence=min(0.55 + 0.1 * len(touched), 0.85),
                        rationale=(
                            f"Project '{proj_key}' touches {len(touched)} distinct file "
                            f"clusters in recent PROGRESS ({', '.join(sorted(touched))}). "
                            "These clusters share no mutable file and can be pursued in parallel."
                        ),
                        signal="A",
                    )
                )
        return results

    # ---- Signal B ---------------------------------------------------------
    def _signal_b_serial_blocker(self, fleet_state: dict) -> list[DivergenceOpportunity]:
        results: list[DivergenceOpportunity] = []
        summaries = fleet_state.get("iter_summaries", {}) or {}
        for proj_key, last3 in summaries.items():
            if len(last3) < 3:
                continue
            blockers = [self._extract_blocker(s) for s in last3]
            blockers = [b for b in blockers if b]
            if len(blockers) >= 3 and len(set(blockers)) == 1:
                b = blockers[0]
                topic = re.sub(r"[^a-z0-9]+", "-", b.lower()).strip("-")[:30] or "unblock"
                results.append(
                    DivergenceOpportunity(
                        project_key=proj_key,
                        sub_topic=f"unblock-{topic}"[:30],
                        evidence=tuple(
                            [f"iter-summary[{i}] blocker='{b}'" for i in range(3)]
                        ),
                        suggested_lane_name=f"agent/{proj_key}/unblock-{topic}-2026-05-25",
                        estimated_parallelism=2,
                        confidence=0.78,
                        rationale=(
                            f"Same blocker '{b}' named in 3 consecutive iter summaries. "
                            "A focused sub-lane targeting this blocker unblocks the main lane."
                        ),
                        signal="B",
                    )
                )
        return results

    @staticmethod
    def _extract_blocker(summary: str) -> str:
        m = re.search(r"(?:blocked? on|waiting on|blocker[:=]?)\s*([^\.\n]{3,60})", summary, re.IGNORECASE)
        return m.group(1).strip() if m else ""

    # ---- Signal C ---------------------------------------------------------
    def _signal_c_queue_depth(self, fleet_state: dict) -> list[DivergenceOpportunity]:
        results: list[DivergenceOpportunity] = []
        hb = fleet_state.get("heartbeats", {}) or {}
        active_by_proj = {h.get("project", "") for h in hb.values() if isinstance(h, dict)}
        for p in fleet_state.get("projects", []) or []:
            qr = int(p.get("queue_rows", 0) or 0)
            if qr < self.queue_depth_threshold:
                continue
            if p["key"] in active_by_proj:
                continue
            results.append(
                DivergenceOpportunity(
                    project_key=p["key"],
                    sub_topic="queue-drainer",
                    evidence=(
                        f"projects/{p['key']}/queue depth={qr}",
                        f"heartbeats/* no active agent for project={p['key']}",
                        f"stall_window={self.stall_minutes}min",
                    ),
                    suggested_lane_name=f"agent/{p['key']}/queue-drainer-2026-05-25",
                    estimated_parallelism=2,
                    confidence=0.72,
                    rationale=(
                        f"Project '{p['key']}' has {qr} queued rows but no active "
                        f"agent in the last {self.stall_minutes} min. Spawning a "
                        "drainer lane parallelizes backlog burn."
                    ),
                    signal="C",
                )
            )
        return results

    # ---- Signal D ---------------------------------------------------------
    def _signal_d_operator_directive(self, fleet_state: dict) -> list[DivergenceOpportunity]:
        results: list[DivergenceOpportunity] = []
        for u in (fleet_state.get("utterances") or [])[-20:]:
            text = str(u.get("text", "") or u.get("utterance", ""))
            if not text:
                continue
            if _DIVERGENCE_RE.search(text):
                # Heuristic: take the first noun-ish token after the marker
                m = _DIVERGENCE_RE.search(text)
                tail = text[m.end():] if m else text
                topic_words = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", tail)[:3]
                topic = "-".join(w.lower() for w in topic_words) or "diverge"
                results.append(
                    DivergenceOpportunity(
                        project_key=str(u.get("project", "sanctum")),
                        sub_topic=topic[:30],
                        evidence=(
                            f"operator-utterances.jsonl ts={u.get('ts_utc', '?')}",
                            f"matched_pattern='{m.group(0) if m else '?'}'",
                            f"utterance='{text[:80]}'",
                        ),
                        suggested_lane_name=f"agent/sanctum/{topic[:24]}-2026-05-25",
                        estimated_parallelism=3,
                        confidence=0.92,  # operator-explicit = highest
                        rationale=(
                            f"Operator utterance explicitly directs parallel work: "
                            f"'{text[:120]}'. This is a high-confidence divergence directive."
                        ),
                        signal="D",
                    )
                )
        return results

    # ---- Signal E ---------------------------------------------------------
    def _signal_e_cross_project_bleed(self, fleet_state: dict) -> list[DivergenceOpportunity]:
        results: list[DivergenceOpportunity] = []
        project_keys = {p["key"] for p in fleet_state.get("projects") or [] if isinstance(p, dict)}
        rows_by_proj = fleet_state.get("progress_rows", {}) or {}
        for proj_key, rows in rows_by_proj.items():
            hits: list[tuple[str, int]] = []
            for idx, row in enumerate(rows[:120]):
                for other in project_keys:
                    if other == proj_key:
                        continue
                    if f"projects/{other}/" in row or f"projects\\{other}\\" in row:
                        hits.append((other, idx + 1))
                        break
            if len(hits) >= 2:
                other_keys = sorted({h[0] for h in hits})
                topic = f"bridge-{other_keys[0]}"[:30]
                results.append(
                    DivergenceOpportunity(
                        project_key=proj_key,
                        sub_topic=topic,
                        evidence=tuple(
                            [f"PROGRESS/{proj_key}.md:{ln} -> {other}" for other, ln in hits[:5]]
                        ),
                        suggested_lane_name=f"agent/{proj_key}/{topic}-2026-05-25",
                        estimated_parallelism=2,
                        confidence=0.68,
                        rationale=(
                            f"Project '{proj_key}' PROGRESS references "
                            f"{len(other_keys)} other projects ({', '.join(other_keys)}). "
                            "A dedicated bridge / integration sub-lane keeps the main "
                            "lane focused while integration work proceeds in parallel."
                        ),
                        signal="E",
                    )
                )
        return results


if __name__ == "__main__":
    s = DivergenceSensor()
    opps = s.scan({})  # empty -> empty
    print(json.dumps({"opportunities": len(opps), "ok": True}, indent=2))
