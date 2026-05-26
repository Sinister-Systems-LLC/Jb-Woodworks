# Author: RKOJ-ELENO :: 2026-05-26
"""Sinister Memory :: PROGRESS -> per-agent adoption sweep.

Closes the largest health-score gap (`adoption` sub-score, weighted 25/100).
Pre-sweep state on 2026-05-26: 1/35 lanes had v2-frontmatter saves (~2.9/100).
The sweep walks every lane named in `automations/session-templates/projects.json`,
locates its `_shared-memory/PROGRESS/<display>.md` file, extracts the newest
heading-delimited section, and writes it to
`_shared-memory/sinister-memory/per-agent/<key>/progress-<heading_id>.md` with
schema-v2 frontmatter (`format_version: 2`, category=fact, trust=medium).

Idempotency: writes only when the target file does not exist OR its current
body differs from the new body. Existing manual `iter-<NNNN>.md` rows are
never touched (different filename namespace).

Designed to run inside `consolidate.py` step 9 (ambient pass every 6h) so
the adoption sub-score keeps climbing without per-lane manual intervention.

Public API:
  sweep_progress_to_per_agent(root, *, dry_run=False, projects=None,
                              max_per_lane=1) -> dict
  extract_latest_progress(path) -> tuple[str, str, str] | None
  save_progress_row(slug, heading_id, title, body, root) -> tuple[Path, str]
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# Slug regex matches auto_save._validate_slug (kept inline so this module
# stays self-contained for ambient-pass safety).
_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{1,64}$")

# Heading detector: matches `## <body>` at start of line. Captures body.
_H2_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)

# Iter detector: matches "iter-NN", "iter NN", "iters NN-MM" (takes the
# largest number when range). Case-insensitive.
_ITER_RE = re.compile(r"iters?[\s\-_]?(\d+)(?:[\s\-_]+(\d+))?", re.IGNORECASE)

# ISO-ish date prefix often seen in PROGRESS headings: 2026-05-26 ...
_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")

# Heading-id sanitizer: keep [a-z0-9-], collapse runs, trim.
_HID_SANITIZE = re.compile(r"[^a-z0-9]+")


def _validate_slug_safe(slug: str) -> Optional[str]:
    s = slug.strip().lower()
    return s if _SLUG_RE.match(s) else None


def _heading_id(title: str) -> str:
    """Build a stable filesystem-safe id from a PROGRESS heading.

    Priority:
      1. If heading contains `iter-NN` or `iters NN-MM`, encode as
         `<date>-iter-<max_num>` when a date is also present, else `iter-<max_num>`.
      2. Else if a YYYY-MM-DD is present, encode as `<date>-<short-hash>`.
      3. Else fall back to a pure short-hash id.

    The short-hash (SHA256[:10]) provides idempotency for headings that
    repeat across sweeps. Truncating to 10 hex digits = ~2^40 collision
    domain which is comfortable for a single-lane history.
    """
    date_m = _DATE_RE.search(title)
    iter_m = _ITER_RE.search(title)
    short_hash = hashlib.sha256(title.strip().encode("utf-8", errors="replace")).hexdigest()[:10]
    if iter_m:
        nums = [int(g) for g in iter_m.groups() if g]
        iter_n = max(nums) if nums else 0
        if date_m:
            return f"{date_m.group(1)}-iter-{iter_n:04d}-{short_hash[:6]}"
        return f"iter-{iter_n:04d}-{short_hash[:6]}"
    if date_m:
        # Sanitize a snippet of the title for human readability.
        snippet = _HID_SANITIZE.sub("-", title.lower())[:40].strip("-")
        return f"{date_m.group(1)}-{snippet}-{short_hash[:6]}" if snippet else f"{date_m.group(1)}-{short_hash}"
    return short_hash


def extract_latest_progress(path: Path) -> Optional[tuple[str, str, str]]:
    """Extract (heading_id, title, body) for the newest ## section in a PROGRESS file.

    PROGRESS convention: newest entry at top. We take the FIRST `## ...` heading
    and slurp body lines until the next `## ` or end of file. The body is
    truncated to 6000 chars to keep per-agent rows lean.

    Returns None when the file has no `## ` headings.
    """
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    # Find the first heading.
    m = _H2_RE.search(text)
    if not m:
        return None
    title = m.group(1).strip()
    body_start = m.end()
    # Find the next heading after this one (start position).
    nxt = _H2_RE.search(text, body_start)
    body = text[body_start:nxt.start()] if nxt else text[body_start:]
    body = body.strip()
    if len(body) > 6000:
        body = body[:6000].rstrip() + "\n\n... [truncated by adoption_sweep]"
    hid = _heading_id(title)
    return hid, title, body


def _frontmatter(slug: str, heading_id: str, title: str, length: int) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return (
        "---\n"
        "format_version: 2\n"
        "author: RKOJ-ELENO\n"
        f"slug: {slug}\n"
        f"heading_id: {heading_id}\n"
        f"saved_at: {now}\n"
        f"length: {length}\n"
        "category: fact\n"
        "confidence: 0.500\n"
        "trust: medium\n"
        "source: adoption-sweep\n"
        "---\n"
    )


def save_progress_row(
    slug: str,
    heading_id: str,
    title: str,
    body: str,
    root: Path,
) -> tuple[Path, str]:
    """Write the per-agent progress row file. Returns (path, status).

    status:
      "written"   -- file created
      "updated"   -- existing file body differed; rewritten
      "unchanged" -- existing file body matches; not rewritten
    """
    slug_l = _validate_slug_safe(slug)
    if slug_l is None:
        raise ValueError(f"invalid slug: {slug!r}")
    out_dir = Path(root) / "_shared-memory" / "sinister-memory" / "per-agent" / slug_l
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"progress-{heading_id}.md"

    title_clean = title.strip().replace("\n", " ")
    body_clean = (body or "(empty)").strip()
    new_body = (
        _frontmatter(slug_l, heading_id, title_clean, len(body_clean))
        + f"\n# {slug_l} :: {title_clean}\n\n{body_clean}\n"
    )

    if out_path.exists():
        try:
            existing = out_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            existing = ""
        # Compare BODY portion only (frontmatter saved_at always differs).
        existing_body_idx = existing.find("\n---\n")
        existing_body = existing[existing_body_idx + 5:] if existing_body_idx != -1 else existing
        new_body_idx = new_body.find("\n---\n")
        new_body_payload = new_body[new_body_idx + 5:] if new_body_idx != -1 else new_body
        if existing_body == new_body_payload:
            return out_path, "unchanged"
        out_path.write_text(new_body, encoding="utf-8")
        return out_path, "updated"

    out_path.write_text(new_body, encoding="utf-8")
    return out_path, "written"


def _load_projects(projects_json: Path) -> list[dict]:
    try:
        with projects_json.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return []
    return data.get("projects", []) or []


def sweep_progress_to_per_agent(
    root: Path,
    *,
    dry_run: bool = False,
    projects: Optional[list[dict]] = None,
    max_per_lane: int = 1,
    progress_dir: Optional[Path] = None,
    projects_json: Optional[Path] = None,
) -> dict:
    """Walk every lane in projects.json; save the newest PROGRESS entry.

    Args:
      root           : Sanctum root.
      dry_run        : if True, scans but writes nothing; returns planned actions.
      projects       : override projects list (bypasses projects.json lookup; tests).
      max_per_lane   : how many headings to save per lane per sweep. Default 1
                       (newest only). Higher values walk deeper for backfill but
                       cost more I/O per ambient pass.
      progress_dir   : override PROGRESS directory (tests).
      projects_json  : override projects.json path (tests).

    Returns aggregated stats dict.
    """
    root = Path(root)
    if progress_dir is None:
        progress_dir = root / "_shared-memory" / "PROGRESS"
    if projects is None:
        if projects_json is None:
            projects_json = root / "automations" / "session-templates" / "projects.json"
        projects = _load_projects(projects_json)

    stats = {
        "dry_run": dry_run,
        "processed": 0,
        "written": 0,
        "updated": 0,
        "unchanged": 0,
        "skipped_no_progress": 0,
        "skipped_invalid_slug": 0,
        "skipped_no_headings": 0,
        "errors": [],
        "lanes": [],
    }

    for proj in projects:
        slug = proj.get("key", "")
        display = proj.get("display", slug)
        slug_l = _validate_slug_safe(slug)
        if slug_l is None:
            stats["skipped_invalid_slug"] += 1
            stats["errors"].append({"slug": slug, "reason": "invalid_slug"})
            continue

        progress_path = progress_dir / f"{display}.md"
        if not progress_path.is_file():
            stats["skipped_no_progress"] += 1
            stats["lanes"].append({"slug": slug_l, "status": "no_progress_file"})
            continue

        stats["processed"] += 1
        # Walk top N headings (newest first per PROGRESS append-top convention).
        try:
            text = progress_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            stats["errors"].append({"slug": slug_l, "reason": f"read_error: {exc}"})
            continue
        headings = list(_H2_RE.finditer(text))
        if not headings:
            stats["skipped_no_headings"] += 1
            stats["lanes"].append({"slug": slug_l, "status": "no_headings"})
            continue

        lane_actions: list[dict] = []
        for i, h in enumerate(headings[:max_per_lane]):
            title = h.group(1).strip()
            body_start = h.end()
            body_end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
            body = text[body_start:body_end].strip()
            if len(body) > 6000:
                body = body[:6000].rstrip() + "\n\n... [truncated by adoption_sweep]"
            hid = _heading_id(title)
            if dry_run:
                lane_actions.append({"slug": slug_l, "heading_id": hid, "title": title[:60], "status": "planned"})
                continue
            try:
                _path, status = save_progress_row(slug_l, hid, title, body, root)
                stats[status] = stats.get(status, 0) + 1
                lane_actions.append({"slug": slug_l, "heading_id": hid, "title": title[:60], "status": status})
            except (ValueError, OSError) as exc:
                stats["errors"].append({"slug": slug_l, "reason": f"save_error: {exc}"})

        stats["lanes"].append({"slug": slug_l, "actions": lane_actions})

    return stats
