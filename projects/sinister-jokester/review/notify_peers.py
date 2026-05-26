"""Post-decision peer-lane notification.

Author: RKOJ-ELENO :: 2026-05-26

When Sinister Jokester verdicts a candidate, peer lanes that own the
relevant capability area need to see the verdict + decision .md so they
can act (adopt-into-their-lane, reject-as-dup, watch). This module:

  1. Maps candidate tags/title/url tokens -> owning peer-lane slugs.
  2. Writes a small inbox note to `_shared-memory/inbox/<slug>/`.
  3. Returns the list of slugs notified so the caller can log.

Composes with operator directive 2026-05-26: *"if you find something we
need for memory for example you need to make sure the memory agent gets
its hands on and sees what you are trying to tell them."*

Slop guard: this module is keyword routing + a 12-line .md. No UI, no
new lanes invented; only routes to lanes that exist in `projects.json`.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SANCTUM_ROOT = Path(r"D:\Sinister Sanctum")
INBOX_ROOT = SANCTUM_ROOT / "_shared-memory" / "inbox"

# slug -> list of keyword regexes. Order matters: first-match wins per slug.
# Only lanes that actually exist in projects.json or are real fleet identities.
# Keep this LEAN; bloat = noise. Operator hard-canonical 2026-05-26:
#   - vault stuff -> sinister-vault
#   - debuggers / RE tools -> sinister-emulator-bundle / sinister-snap-api / sinister-tiktok-api
PEER_LANE_ROUTES: dict[str, list[str]] = {
    "sinister-vault": [
        r"\bvault\b", r"\bblockchain\b", r"\bgitchain\b", r"\bdecentral",
        r"\bp2p\b", r"\bpeer[- ]?to[- ]?peer\b", r"\bzkp\b", r"\bzero[- ]?knowledge\b",
        r"\bfhe\b", r"\bhomomorphic\b", r"\bcryptograph", r"\bsigned[- ]?commit",
        r"\bipfs\b", r"\bipld\b", r"\bmerkle\b", r"\bcontent[- ]?address",
        r"\bobject[- ]?store\b", r"\bbackup\b", r"\bsnapshot",
    ],
    "sinister-memory": [
        r"\bmemory\b", r"\brecall\b", r"\bembedding\b", r"\bvector[- ]?(db|search|store)\b",
        r"\bsemantic[- ]?search\b", r"\bknowledge[- ]?graph\b", r"\brag\b",
    ],
    "sinister-overseer": [
        r"\borchestrat", r"\bagent[- ]?coordination\b", r"\bswarm\b",
        r"\bworkflow[- ]?engine\b", r"\bsupervisor[- ]?tree\b",
    ],
    "sinister-term": [
        r"\btui\b", r"\bterminal\b", r"\bansi\b", r"\bcurses\b", r"\bblessed\b",
        r"\bbubbletea\b", r"\btermui\b", r"\brich[- ]?(cli|tui)\b",
    ],
    "sinister-panel": [
        r"\bdashboard\b", r"\badmin[- ]?panel\b", r"\bgrafana\b", r"\bweb[- ]?ui\b",
    ],
    "sinister-snap-api": [
        r"\bsnapchat\b", r"\bsnap[- ]?api\b", r"\bbitmoji\b", r"\bsnap[- ]?kit\b",
    ],
    "sinister-snap-api-quantum": [
        r"\bsnap[- ]?api[- ]?quantum\b", r"\bsnapchat[- ]?reverse",
    ],
    "sinister-tiktok-api": [
        r"\btiktok\b", r"\bdouyin\b", r"\bbytedance\b",
    ],
    "sinister-emulator-bundle": [
        r"\bemulator\b", r"\bandroid[- ]?emulator\b", r"\bgenymotion\b",
        r"\bwaydroid\b", r"\bbluestacks\b", r"\bavd\b",
        # RE / debugger tooling (operator: "debuggers or RE tools they need to go to sinister emui...")
        r"\bfrida\b", r"\bghidra\b", r"\bida[- ]?pro\b", r"\bradare2?\b",
        r"\bx64dbg\b", r"\bollydbg\b", r"\bdecompil", r"\bdisassembl",
        r"\bsmali\b", r"\bdex2jar\b", r"\bapktool\b", r"\bjadx\b",
        r"\bunidbg\b", r"\bunicorn[- ]?engine\b", r"\bqemu\b", r"\bbinaryninja\b",
        r"\bbinary[- ]?analysis\b", r"\breverse[- ]?engineer",
    ],
    "kernel-apk": [
        r"\bapk\b", r"\bkernel[- ]?patch\b", r"\bdex\b", r"\bmagisk\b",
        r"\bxposed\b", r"\bzygisk\b", r"\bandroid[- ]?root",
    ],
    "sinister-quantum": [
        r"\bqiskit\b", r"\bqubit\b", r"\bquantum[- ]?(comput|circuit|sim)",
    ],
    "eve-compliance": [
        r"\bcompliance\b", r"\bccbill\b", r"\bphotodna\b", r"\bcsam\b",
        r"\bncmec\b", r"\btrust[- ]?and[- ]?safety\b",
    ],
    "sinister-os": [
        r"\bdaemon\b", r"\bschtask\b", r"\bsystemd\b", r"\bwindows[- ]?service\b",
        r"\bcron\b", r"\binit[- ]?system\b",
    ],
    "sinister-forge": [
        r"\bcode[- ]?gen\b", r"\btemplate[- ]?engine\b", r"\bscaffold\b",
    ],
    "sinister-claw": [
        r"\bscrap", r"\bcrawl", r"\bspider\b", r"\bplaywright\b", r"\bpuppeteer\b",
    ],
    "letstext": [
        r"\bsms\b", r"\btwilio\b", r"\bbulk[- ]?text\b", r"\bmessaging[- ]?gateway\b",
    ],
}


def route(candidate: dict[str, Any], verdict: str) -> list[str]:
    """Return list of peer-lane slugs that should be notified for this candidate."""
    haystack = " ".join(
        str(candidate.get(k, "") or "")
        for k in ("title", "short_summary", "tags", "source_url", "readme_excerpt", "raw_metadata_json")
    ).lower()

    hits: list[str] = []
    for slug, patterns in PEER_LANE_ROUTES.items():
        for pat in patterns:
            if re.search(pat, haystack):
                hits.append(slug)
                break
    # WATCH for novel items still routes (adjacent lane gets a heads up); REJECT routes only on
    # explicit dup-against-incumbent so peers know we already triaged it.
    return hits


def write_inbox_note(
    slug: str,
    candidate: dict[str, Any],
    verdict: str,
    decision_md_path: str,
    overlap_score: float,
    sanctum_root: Path = SANCTUM_ROOT,
) -> Path:
    inbox_dir = sanctum_root / "_shared-memory" / "inbox" / slug
    inbox_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%MZ")
    safe_id = re.sub(r"[^a-z0-9]+", "-", candidate["id"].lower()).strip("-")
    fname = f"{ts}-from-sinister-jokester-{verdict.lower()}-{safe_id}.md"
    out_path = inbox_dir / fname

    title = candidate.get("title") or candidate.get("source_url")
    summary = candidate.get("short_summary") or "(no summary)"
    rel_decision = decision_md_path
    body = (
        f"# [DELEGATE-AWARE] Jokester verdict for {slug}\n\n"
        f"> From: sinister-jokester  ::  ts: {ts}  ::  verdict: **{verdict}**\n\n"
        f"## What\n\n"
        f"- **Candidate:** {title}\n"
        f"- **Source:** {candidate.get('source_url','')}\n"
        f"- **Type:** {candidate.get('source_type','')}\n"
        f"- **Overlap score:** {overlap_score:.2f}\n"
        f"- **Summary:** {summary}\n\n"
        f"## Why you (`{slug}`) are getting this\n\n"
        f"Your lane owns the capability area the candidate touches (per Jokester's peer-route table).\n"
        f"Read the full decision .md and decide if you want to ADOPT-into-your-lane, REJECT-as-dup,\n"
        f"or leave on WATCH.\n\n"
        f"## Read the verdict\n\n"
        f"- Decision .md: `projects/sinister-jokester/{rel_decision}`\n"
        f"- Raw artifacts: `projects/sinister-jokester/vault/intake/{candidate['id']}/`\n"
        f"- DB row: query via `python projects/sinister-jokester/db/recall.py search {candidate['id']}`\n\n"
        f"## Ack\n\n"
        f"No formal ack needed; just delete this file once you've acted (or moved it to `_acked/`).\n"
    )
    out_path.write_text(body, encoding="utf-8")
    return out_path


def notify_all(
    candidate: dict[str, Any],
    verdict: str,
    decision_md_path: str,
    overlap_score: float,
    sanctum_root: Path = SANCTUM_ROOT,
) -> list[dict[str, str]]:
    """Convenience: route + write inbox notes for every matched peer lane."""
    slugs = route(candidate, verdict)
    out: list[dict[str, str]] = []
    for slug in slugs:
        path = write_inbox_note(slug, candidate, verdict, decision_md_path, overlap_score, sanctum_root)
        out.append({"slug": slug, "inbox_path": str(path)})
    return out


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate-json", type=Path, required=True)
    ap.add_argument("--verdict", required=True)
    ap.add_argument("--decision-md", required=True)
    ap.add_argument("--overlap-score", type=float, default=0.0)
    args = ap.parse_args()
    cand = json.loads(args.candidate_json.read_text(encoding="utf-8"))
    out = notify_all(cand, args.verdict, args.decision_md, args.overlap_score)
    print(json.dumps(out, indent=2))
