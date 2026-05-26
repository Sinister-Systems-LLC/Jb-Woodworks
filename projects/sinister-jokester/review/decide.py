"""Orchestrator: intake -> cross-ref -> verdict -> decision .md -> DB row.

Author: RKOJ-ELENO :: 2026-05-26

The `decide()` function is the canonical entrypoint used by jokester_cli.py.
It supports two modes:
  - 'auto'   : verdict heuristic from fleet_overlap_score + status (default).
  - 'manual' : caller supplies an explicit verdict + rationale_bullets.

Auto heuristic (intentionally conservative — operator wants deep review,
so 'auto' should mostly emit WATCH and let a human or follow-up agent
upgrade to ADOPT after deeper inspection):

  - status='pending' due to clone/download failure -> REJECT (failure_mode='intake-failed')
  - source_type='ig_audio' with status='pending' (deps missing) -> WATCH
  - overlap_score >= 0.85 -> WATCH (likely duplicate; needs human to decide ADOPT-as-replacement vs REJECT-as-dup)
  - overlap_score >= 0.25 -> WATCH (adjacent; needs human to scope integration)
  - overlap_score <  0.25 -> WATCH (novel; needs human to confirm relevance)

Every auto verdict ships with `rationale_bullets` that explain the score,
so the operator / next agent can flip ADOPT or REJECT in seconds.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = REPO_ROOT / "review" / "templates"
DECISIONS_DIR = REPO_ROOT / "vault" / "decisions"
DEFAULT_DB_PATH = REPO_ROOT / "vault" / "db" / "intake.sqlite"

sys.path.insert(0, str(REPO_ROOT))
from intake import github as gh_intake  # noqa: E402
from intake import ig as ig_intake  # noqa: E402
from intake import local as local_intake  # noqa: E402
from review.cross_reference import cross_reference  # noqa: E402
from review.notify_peers import notify_all as notify_peer_lanes  # noqa: E402
from review.notify_peers import route as route_peer_lanes  # noqa: E402


# -----------------------------------------------------------------------------
# DB helpers
# -----------------------------------------------------------------------------

def _conn(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(db_path)


def _upsert_intake_row(conn: sqlite3.Connection, candidate: dict[str, Any]) -> None:
    cols = [
        "id","source_url","source_type","intake_ts","status",
        "tags","title","short_summary","raw_metadata_json",
    ]
    vals = [candidate.get(c) for c in cols]
    placeholders = ",".join(["?"] * len(cols))
    set_clause = ",".join(f"{c}=excluded.{c}" for c in cols if c != "id")
    conn.execute(
        f"INSERT INTO intake_items ({','.join(cols)}) VALUES ({placeholders}) "
        f"ON CONFLICT(id) DO UPDATE SET {set_clause}",
        vals,
    )


def _log_event(conn: sqlite3.Connection, item_id: str, event: str, detail: str = "") -> None:
    conn.execute(
        "INSERT INTO intake_log (item_id, ts_utc, event, detail) VALUES (?,?,?,?)",
        (item_id, datetime.now(timezone.utc).isoformat(timespec="seconds"), event, detail),
    )


def _update_verdict(
    conn: sqlite3.Connection,
    item_id: str,
    verdict: str,
    decision_md_path: str,
    fleet_overlap_score: float,
    fleet_overlap_assets: list[dict[str, Any]],
    reviewed_by: str,
) -> None:
    conn.execute(
        """
        UPDATE intake_items SET
            status='decided',
            verdict=?,
            decision_md_path=?,
            fleet_overlap_score=?,
            fleet_overlap_assets=?,
            reviewed_by=?,
            decided_ts=?
        WHERE id=?
        """,
        (
            verdict,
            decision_md_path,
            float(fleet_overlap_score),
            json.dumps(fleet_overlap_assets, default=str),
            reviewed_by,
            datetime.now(timezone.utc).isoformat(timespec="seconds"),
            item_id,
        ),
    )


# -----------------------------------------------------------------------------
# Intake dispatch
# -----------------------------------------------------------------------------

def _intake(url: str, force: bool = False) -> dict[str, Any]:
    u = url.strip().lower()
    if "github.com/" in u:
        return gh_intake.intake(url, force=force)
    if "instagram.com/" in u:
        return ig_intake.intake(url, force=force)
    # Local path? (drive-letter, POSIX absolute, or existing dir)
    if local_intake.looks_like_local_path(url):
        return local_intake.intake(url, force=force)
    raise ValueError(f"no intake adapter for url: {url!r}")


def _compute_url_id(url: str) -> str | None:
    """Compute the deterministic id for a URL without doing any IO."""
    u = url.strip()
    try:
        if "github.com/" in u.lower():
            owner, repo = gh_intake.parse_github_url(u)
            return gh_intake.compute_id(owner, repo)
        if "instagram.com/" in u.lower():
            shortcode = ig_intake.parse_ig_url(u)
            return ig_intake.compute_id(shortcode)
        if local_intake.looks_like_local_path(u):
            from pathlib import Path as _P
            p = _P(u.strip().strip('"').strip("'")).expanduser().resolve()
            return local_intake.compute_id(p)
    except ValueError:
        return None
    return None


def _load_existing_row(conn: sqlite3.Connection, item_id: str) -> dict[str, Any] | None:
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM intake_items WHERE id = ? AND status='decided'",
        (item_id,),
    ).fetchone()
    if not row:
        return None
    return dict(row)


# -----------------------------------------------------------------------------
# Verdict heuristic
# -----------------------------------------------------------------------------

def _auto_verdict(candidate: dict[str, Any], xref: dict[str, Any]) -> tuple[str, list[str], str]:
    """Return (verdict, rationale_bullets, failure_mode).

    Heuristic (operator hard-canonical 2026-05-26: deep review + clear ADOPT when fit is obvious):

      - intake failed (genuine error)              -> REJECT
      - intake stub (deps missing)                 -> WATCH
      - peer-lane match exists + low fleet-overlap -> ADOPT (clear lane home, no dup risk)
      - peer-lane match + medium overlap           -> WATCH (lane home but possibly redundant)
      - very high overlap                          -> WATCH (likely dup, human decides)
      - no peer match + medium overlap             -> WATCH (adjacent)
      - no peer match + low overlap                -> WATCH (novel)

    The verdict respects operator intent: most things become WATCH (conservative) UNLESS
    there's a clean peer-lane fit with a low fleet-overlap, in which case ADOPT auto-fires
    and the right peer lane gets notified.
    """
    if candidate.get("status") == "pending" and not candidate.get("_intake_ok", True):
        reason = candidate.get("_reason") or "intake-failed"
        if reason == "deps-missing":
            return (
                "WATCH",
                [
                    "Intake stub: required deps missing (yt-dlp / whisper).",
                    "URL recorded so we don't lose it.",
                    "Re-decide automatically once deps are installed and re-intake runs.",
                ],
                "",
            )
        if reason == "path-not-found":
            return (
                "REJECT",
                [
                    f"Local path does not exist: {candidate.get('source_url')}",
                    "Re-evaluate only if the operator drops the artifact at the resolved path.",
                ],
                "intake-failed: path-not-found",
            )
        return (
            "REJECT",
            [
                f"Intake failed: {reason}.",
                f"Short summary: {candidate.get('short_summary')}",
                "Re-evaluate manually only if the source URL changes or becomes reachable.",
            ],
            f"intake-failed: {reason}",
        )

    score = float(xref.get("overlap_score", 0.0))
    n_assets = len(xref.get("overlapping_assets") or [])
    peer_slugs = route_peer_lanes(candidate, "PROVISIONAL")
    peer_hits = len(peer_slugs)
    peer_list = ", ".join(peer_slugs) if peer_slugs else "(none)"

    # ADOPT: clear lane home + not a flagrant dup.
    # Threshold 0.65 — peer-lane match is strong evidence the candidate belongs SOMEWHERE in
    # the fleet; high but not flagrant overlap (e.g. shared infrastructure terms) shouldn't
    # block the peer lane from claiming it. Real dup-risk (>=0.80) still routes to WATCH.
    if peer_hits >= 1 and score < 0.65:
        return (
            "ADOPT",
            [
                f"Clear peer-lane fit ({peer_hits}): {peer_list}.",
                f"Low weighted fleet-overlap (score={score:.2f}, {n_assets} matching files) — no duplication risk against existing implementations.",
                "Routed to the matched peer lane(s) for integration ownership. See peer inbox notes.",
            ],
            "",
        )

    # WATCH: lane home but potentially redundant.
    if peer_hits >= 1 and score < 0.80:
        return (
            "WATCH",
            [
                f"Peer-lane fit ({peer_hits}): {peer_list}.",
                f"Medium fleet-overlap (score={score:.2f}, {n_assets} matching) — possible redundancy.",
                "Promote to ADOPT once the peer lane confirms the candidate adds NEW capability vs incumbents.",
            ],
            "",
        )

    if score >= 0.80:
        return (
            "WATCH",
            [
                f"High weighted fleet-overlap (score={score:.2f}, {n_assets} matching assets).",
                "Likely duplicate or near-duplicate of existing fleet implementation.",
                "Promote to ADOPT only if it strictly improves an incumbent; else REJECT-as-dup.",
            ],
            "",
        )

    if peer_hits == 0 and score < 0.20:
        return (
            "WATCH",
            [
                f"Novel relative to fleet (score={score:.2f}, {n_assets} matching).",
                "No peer-lane keyword match — needs human to confirm relevance to fleet roadmap.",
                "If yes -> ADOPT with a fresh integration sketch. If no -> REJECT-as-irrelevant.",
            ],
            "",
        )

    return (
        "WATCH",
        [
            f"Adjacent to fleet (score={score:.2f}, {n_assets} matching, peer-hits={peer_hits}).",
            "Needs human/agent to scope integration path (which lane owns the merge).",
            "Default to WATCH until integration sketch exists.",
        ],
        "",
    )


# -----------------------------------------------------------------------------
# .md writer
# -----------------------------------------------------------------------------

def _format_overlap_block(xref: dict[str, Any]) -> str:
    assets = xref.get("overlapping_assets") or []
    if not assets:
        return "_(no fleet overlap detected — novel territory.)_"
    lines = []
    for a in assets[:10]:
        top_tokens = ", ".join(f"{k}({v})" for k, v in sorted(a["hits"].items(), key=lambda kv: -kv[1])[:5])
        lines.append(f"- `{a['path']}` — total hits: {a['hit_total']} — tokens: {top_tokens}")
    return "\n".join(lines)


def _write_decision_md(
    verdict: str,
    candidate: dict[str, Any],
    xref: dict[str, Any],
    rationale_bullets: list[str],
    extra: dict[str, str] | None = None,
    reviewed_by: str = "sinister-jokester",
) -> Path:
    template_path = TEMPLATES / f"{verdict.lower()}.md.tmpl"
    tmpl = template_path.read_text(encoding="utf-8")
    rationale_md = "\n".join(f"- {b}" for b in rationale_bullets) if rationale_bullets else "- _(no rationale)_"
    overlap_md = _format_overlap_block(xref)
    decided_ts = datetime.now(timezone.utc).isoformat(timespec="seconds")

    defaults = {
        "title": candidate.get("title") or candidate.get("source_url"),
        "source_url": candidate.get("source_url", ""),
        "source_type": candidate.get("source_type", ""),
        "intake_ts": candidate.get("intake_ts", ""),
        "decided_ts": decided_ts,
        "reviewed_by": reviewed_by,
        "fleet_overlap_score": f"{xref.get('overlap_score', 0.0):.3f}",
        "rationale_bullets": rationale_md,
        "short_summary": candidate.get("short_summary") or "_(no summary)_",
        "fleet_overlap_block": overlap_md,
        "tags": candidate.get("tags") or "_(none)_",
        "raw_metadata_json": candidate.get("raw_metadata_json") or "{}",
        # ADOPT-only fields
        "owning_lane": "TBD",
        "integration_sketch": "TBD — see proposed integration path.",
        "dependencies": "TBD",
        "effort_estimate": "TBD",
        # WATCH-only fields
        "trigger_1": "Re-evaluate when fleet capability gap surfaces.",
        "trigger_2": "Re-evaluate when project hits a 1.0 release.",
        "trigger_3": "Re-evaluate quarterly during forever-improve sweeps.",
        # REJECT-only fields
        "failure_mode": "See rationale bullets.",
    }
    if extra:
        defaults.update(extra)

    body = tmpl.format(**defaults)
    out_dir = DECISIONS_DIR / verdict.lower()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{candidate['id']}.md"
    out_path.write_text(body, encoding="utf-8")
    return out_path


# -----------------------------------------------------------------------------
# Public entrypoint
# -----------------------------------------------------------------------------

def _soft_review(
    url: str,
    existing: dict[str, Any],
    db_path: Path,
    reviewed_by: str,
) -> dict[str, Any]:
    """Lighter re-pass for an already-decided URL.

    No re-clone. Re-runs cross-reference (fleet may have grown), re-routes peers
    (new lanes may exist), appends a 'Soft re-review' addendum to the decision .md
    if anything changed materially, and writes peer notes only to lanes not previously notified.
    """
    candidate_for_xref: dict[str, Any] = {
        "id": existing["id"],
        "title": existing.get("title"),
        "short_summary": existing.get("short_summary"),
        "tags": existing.get("tags"),
        "source_url": existing.get("source_url"),
        "raw_metadata_json": existing.get("raw_metadata_json") or "{}",
        "source_type": existing.get("source_type"),
        "readme_excerpt": "",  # README excerpt isn't in DB; xref still finds enough signal
    }
    xref = cross_reference(candidate_for_xref)
    new_score = float(xref.get("overlap_score", 0.0))
    prev_score = float(existing.get("fleet_overlap_score") or 0.0)
    score_delta = new_score - prev_score

    prev_assets_json = existing.get("fleet_overlap_assets") or "[]"
    try:
        prev_assets = json.loads(prev_assets_json)
    except json.JSONDecodeError:
        prev_assets = []
    prev_asset_paths = {a.get("path") for a in prev_assets if isinstance(a, dict)}
    new_asset_paths = {a.get("path") for a in (xref.get("overlapping_assets") or [])}
    added_assets = sorted(new_asset_paths - prev_asset_paths)
    removed_assets = sorted(prev_asset_paths - new_asset_paths)

    # Peer routing diff: only notify peers that we haven't already notified for this id.
    all_routed = []  # will be populated below
    try:
        with _conn(db_path) as conn:
            log_rows = conn.execute(
                "SELECT detail FROM intake_log WHERE item_id=? AND event='notified'",
                (existing["id"],),
            ).fetchall()
        already_notified: set[str] = set()
        for (detail,) in log_rows:
            if detail and detail.startswith("peers="):
                already_notified.update(detail[len("peers="):].split(","))
    except sqlite3.Error:
        already_notified = set()

    from review.notify_peers import route as route_peers, write_inbox_note  # local import to avoid cycles at module load
    new_peer_slugs = route_peers(candidate_for_xref, existing.get("verdict") or "WATCH")
    new_only = [s for s in new_peer_slugs if s not in already_notified]
    newly_notified: list[dict[str, str]] = []
    for slug in new_only:
        path = write_inbox_note(
            slug,
            candidate_for_xref,
            existing.get("verdict") or "WATCH",
            existing.get("decision_md_path") or "",
            new_score,
        )
        newly_notified.append({"slug": slug, "inbox_path": str(path)})

    # Decide whether anything is worth appending to the .md.
    material_change = (
        abs(score_delta) >= 0.10
        or added_assets
        or removed_assets
        or newly_notified
    )

    md_path_rel = existing.get("decision_md_path")
    md_path_abs = REPO_ROOT / md_path_rel if md_path_rel else None
    if material_change and md_path_abs and md_path_abs.exists():
        addendum_lines = [
            "",
            "---",
            "",
            f"## Soft re-review :: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
            "",
            f"- **Re-reviewed by:** {reviewed_by}",
            f"- **Overlap score:** {prev_score:.3f} → {new_score:.3f} (Δ {score_delta:+.3f})",
            f"- **New overlapping assets ({len(added_assets)}):** "
            + (", ".join(f"`{p}`" for p in added_assets[:6]) + ("…" if len(added_assets) > 6 else "") if added_assets else "_(none)_"),
            f"- **Dropped overlapping assets ({len(removed_assets)}):** "
            + (", ".join(f"`{p}`" for p in removed_assets[:6]) + ("…" if len(removed_assets) > 6 else "") if removed_assets else "_(none)_"),
            f"- **Newly notified peer lanes:** "
            + (", ".join(n["slug"] for n in newly_notified) if newly_notified else "_(none)_"),
            "",
            "Verdict left unchanged. Promote/demote manually with `python jokester_cli.py intake <url> --verdict ADOPT|REJECT --rationale '...'`.",
            "",
        ]
        with md_path_abs.open("a", encoding="utf-8") as f:
            f.write("\n".join(addendum_lines))

    with _conn(db_path) as conn:
        # Update the score + assets snapshot but keep verdict + decision_md_path.
        conn.execute(
            "UPDATE intake_items SET fleet_overlap_score=?, fleet_overlap_assets=? WHERE id=?",
            (new_score, json.dumps(xref.get("overlapping_assets") or [], default=str), existing["id"]),
        )
        _log_event(
            conn,
            existing["id"],
            "soft-reviewed",
            f"prev_score={prev_score:.3f} new_score={new_score:.3f} added={len(added_assets)} removed={len(removed_assets)} new_peers={len(newly_notified)}",
        )
        if newly_notified:
            slugs = ",".join(n["slug"] for n in newly_notified)
            _log_event(conn, existing["id"], "notified", f"peers={slugs}")
        conn.commit()

    return {
        "id": existing["id"],
        "verdict": existing.get("verdict"),
        "decision_md_path": md_path_rel,
        "overlap_score": new_score,
        "prev_overlap_score": prev_score,
        "score_delta": round(score_delta, 3),
        "n_overlapping_assets": len(xref.get("overlapping_assets") or []),
        "intake_ok": True,
        "soft_reviewed": True,
        "material_change": material_change,
        "added_assets": added_assets,
        "removed_assets": removed_assets,
        "peers_notified": [n["slug"] for n in newly_notified],
    }


def decide(
    url: str,
    db_path: Path = DEFAULT_DB_PATH,
    force: bool = False,
    reviewed_by: str = "sinister-jokester",
    manual_verdict: str | None = None,
    manual_rationale: list[str] | None = None,
) -> dict[str, Any]:
    # Soft re-review short-circuit (operator hard-canonical 2026-05-26).
    # If this URL was already decided and the caller didn't pass --force or a manual
    # verdict override, do a light pass instead of re-cloning.
    if not force and not manual_verdict:
        precomputed_id = _compute_url_id(url)
        if precomputed_id:
            with _conn(db_path) as conn:
                existing = _load_existing_row(conn, precomputed_id)
            if existing:
                return _soft_review(url, existing, db_path, reviewed_by)

    candidate = _intake(url, force=force)

    with _conn(db_path) as conn:
        _upsert_intake_row(conn, candidate)
        _log_event(conn, candidate["id"], "intaken", f"status={candidate.get('status')}")
        conn.commit()

    xref = cross_reference(candidate)

    if manual_verdict:
        verdict = manual_verdict.upper()
        bullets = manual_rationale or [f"Manual verdict supplied by {reviewed_by}."]
        failure_mode = ""
    else:
        verdict, bullets, failure_mode = _auto_verdict(candidate, xref)

    extra = {}
    if verdict == "REJECT" and failure_mode:
        extra["failure_mode"] = failure_mode

    md_path = _write_decision_md(verdict, candidate, xref, bullets, extra=extra, reviewed_by=reviewed_by)
    rel_md = md_path.relative_to(REPO_ROOT).as_posix()

    with _conn(db_path) as conn:
        _update_verdict(
            conn,
            candidate["id"],
            verdict,
            rel_md,
            xref.get("overlap_score", 0.0),
            xref.get("overlapping_assets") or [],
            reviewed_by,
        )
        _log_event(conn, candidate["id"], "decided", f"verdict={verdict} md={rel_md}")
        conn.commit()

    # Peer-lane notification: drop an inbox note in every fleet lane whose
    # capability area this candidate touches. Operator hard-canonical 2026-05-26.
    notified = notify_peer_lanes(candidate, verdict, rel_md, xref.get("overlap_score", 0.0))
    if notified:
        with _conn(db_path) as conn:
            slugs = ",".join(n["slug"] for n in notified)
            _log_event(conn, candidate["id"], "notified", f"peers={slugs}")
            conn.commit()

    return {
        "id": candidate["id"],
        "verdict": verdict,
        "decision_md_path": rel_md,
        "overlap_score": xref.get("overlap_score", 0.0),
        "n_overlapping_assets": len(xref.get("overlapping_assets") or []),
        "intake_ok": candidate.get("_intake_ok", True),
        "peers_notified": [n["slug"] for n in notified],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--reviewer", default="sinister-jokester")
    ap.add_argument("--verdict", choices=["ADOPT", "WATCH", "REJECT"], default=None,
                    help="Override auto-verdict.")
    ap.add_argument("--rationale", default=None, help="Pipe-separated rationale bullets (used with --verdict).")
    args = ap.parse_args(argv)
    bullets = args.rationale.split("|") if args.rationale else None
    out = decide(
        args.url,
        db_path=args.db,
        force=args.force,
        reviewed_by=args.reviewer,
        manual_verdict=args.verdict,
        manual_rationale=bullets,
    )
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
