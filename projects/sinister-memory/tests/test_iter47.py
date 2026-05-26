# Author: RKOJ-ELENO :: 2026-05-26
"""Iter-47 :: adoption_sweep regression tests.

Closes the adoption-gap (2.9/100 -> >0/100 climb) by sweeping PROGRESS file
headings into `_shared-memory/sinister-memory/per-agent/<slug>/`. Tests cover:

  1. heading_id stable + collision-resistant
  2. extract_latest_progress on synthetic + edge-cases
  3. save_progress_row writes v2 frontmatter
  4. save_progress_row idempotent on unchanged body
  5. save_progress_row reports "updated" on body change
  6. sweep walks projects.json synthetic + matches by display name
  7. sweep idempotent: second run -> all unchanged
  8. sweep dry_run writes nothing
  9. health adoption climbs after sweep (end-to-end)
 10. CLI subcommand exits 0 + emits JSON
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from sinister_memory import adoption_sweep, health


# ---------------------------------------------------------------------------
# Fixture: synthetic Sanctum-root with projects.json + PROGRESS files
# ---------------------------------------------------------------------------
def _make_synthetic_root(tmp_path: Path, lanes: list[dict], progress_bodies: dict[str, str]) -> Path:
    """Build a temp dir matching the real Sanctum layout for sweep tests."""
    root = tmp_path / "sanctum"
    (root / "_shared-memory" / "PROGRESS").mkdir(parents=True)
    (root / "automations" / "session-templates").mkdir(parents=True)
    projects_json = root / "automations" / "session-templates" / "projects.json"
    projects_json.write_text(json.dumps({"projects": lanes}, indent=2), encoding="utf-8")
    for display, body in progress_bodies.items():
        (root / "_shared-memory" / "PROGRESS" / f"{display}.md").write_text(body, encoding="utf-8")
    return root


# ---------------------------------------------------------------------------
# 1. heading_id encoding
# ---------------------------------------------------------------------------
def test_heading_id_iter_pattern():
    hid = adoption_sweep._heading_id("2026-05-26 02:36 — shipped: iter-75 /inbox-of")
    assert hid.startswith("2026-05-26-iter-0075-"), hid
    # 6-char short hash suffix
    assert len(hid.rsplit("-", 1)[1]) == 6


def test_heading_id_iter_range_takes_max():
    hid = adoption_sweep._heading_id("2026-05-25 ~19:30Z — Iters 34-47: catchup row")
    # Max of 34, 47 -> 47
    assert "iter-0047" in hid, hid


def test_heading_id_no_iter_uses_date_plus_snippet():
    hid = adoption_sweep._heading_id("2026-05-26 — shipped: a brand new feature")
    assert hid.startswith("2026-05-26-"), hid


def test_heading_id_no_date_no_iter_pure_hash():
    hid = adoption_sweep._heading_id("just a plain heading with no date or iter")
    # Pure 10-char hex hash
    assert len(hid) == 10
    assert all(c in "0123456789abcdef" for c in hid)


def test_heading_id_stable_across_calls():
    title = "2026-05-26 — shipped: iter-99 stable test"
    assert adoption_sweep._heading_id(title) == adoption_sweep._heading_id(title)


def test_heading_id_different_titles_different_ids():
    a = adoption_sweep._heading_id("2026-05-26 — title A")
    b = adoption_sweep._heading_id("2026-05-26 — title B")
    assert a != b


# ---------------------------------------------------------------------------
# 2. extract_latest_progress
# ---------------------------------------------------------------------------
def test_extract_latest_progress_basic(tmp_path):
    p = tmp_path / "log.md"
    p.write_text(
        "# Lane\n\nIntro line.\n\n---\n\n"
        "## 2026-05-26 — shipped: iter-75 newest thing\n\nNewest body line.\n\n"
        "## 2026-05-25 — shipped: iter-74 older thing\n\nOlder body.\n",
        encoding="utf-8",
    )
    result = adoption_sweep.extract_latest_progress(p)
    assert result is not None
    hid, title, body = result
    assert "iter-75" in title
    assert "iter-0075" in hid
    assert "Newest body line." in body
    assert "Older body" not in body


def test_extract_latest_progress_no_headings(tmp_path):
    p = tmp_path / "empty.md"
    p.write_text("# Lane\n\nJust intro, no h2 headings.\n", encoding="utf-8")
    assert adoption_sweep.extract_latest_progress(p) is None


def test_extract_latest_progress_truncates_long_body(tmp_path):
    p = tmp_path / "long.md"
    p.write_text("## 2026-05-26 — big\n\n" + "x" * 10000, encoding="utf-8")
    result = adoption_sweep.extract_latest_progress(p)
    assert result is not None
    _, _, body = result
    assert "[truncated by adoption_sweep]" in body
    assert len(body) <= 6100


def test_extract_latest_progress_missing_file_returns_none(tmp_path):
    assert adoption_sweep.extract_latest_progress(tmp_path / "nope.md") is None


# ---------------------------------------------------------------------------
# 3-5. save_progress_row + idempotency
# ---------------------------------------------------------------------------
def test_save_progress_row_writes_v2_frontmatter(tmp_path):
    out, status = adoption_sweep.save_progress_row(
        slug="test-lane",
        heading_id="2026-05-26-iter-0001-abc123",
        title="shipped: iter-1 test thing",
        body="Body of the test entry.",
        root=tmp_path,
    )
    assert status == "written"
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert content.startswith("---\n")
    assert "format_version: 2" in content
    assert "slug: test-lane" in content
    assert "category: fact" in content
    assert "trust: medium" in content
    assert "source: adoption-sweep" in content
    assert "Body of the test entry." in content


def test_save_progress_row_idempotent_on_unchanged(tmp_path):
    args = dict(slug="t-l", heading_id="hid-1", title="T", body="B", root=tmp_path)
    out1, s1 = adoption_sweep.save_progress_row(**args)
    out2, s2 = adoption_sweep.save_progress_row(**args)
    assert s1 == "written"
    assert s2 == "unchanged"
    assert out1 == out2


def test_save_progress_row_updates_on_body_change(tmp_path):
    base = dict(slug="t-l", heading_id="hid-2", title="T", root=tmp_path)
    adoption_sweep.save_progress_row(body="original", **base)
    _, s = adoption_sweep.save_progress_row(body="modified", **base)
    assert s == "updated"


def test_save_progress_row_rejects_invalid_slug(tmp_path):
    # Slug regex disallows spaces + slashes + leading non-alphanumeric;
    # validator also lowercases, so case alone is not enough.
    with pytest.raises(ValueError):
        adoption_sweep.save_progress_row(
            slug="has spaces",
            heading_id="x",
            title="t",
            body="b",
            root=tmp_path,
        )


# ---------------------------------------------------------------------------
# 6-8. sweep_progress_to_per_agent
# ---------------------------------------------------------------------------
def _two_lane_root(tmp_path: Path) -> Path:
    lanes = [
        {"key": "lane-a", "display": "Lane A"},
        {"key": "lane-b", "display": "Lane B"},
    ]
    bodies = {
        "Lane A": "## 2026-05-26 — shipped: iter-10 A-thing\n\nA body.\n\n## 2026-05-25 — iter-9 older\n\nOlder.\n",
        "Lane B": "## 2026-05-26 — shipped: iter-5 B-thing\n\nB body.\n",
    }
    return _make_synthetic_root(tmp_path, lanes, bodies)


def test_sweep_writes_one_row_per_lane(tmp_path):
    root = _two_lane_root(tmp_path)
    stats = adoption_sweep.sweep_progress_to_per_agent(root)
    assert stats["processed"] == 2
    assert stats["written"] == 2
    assert stats["unchanged"] == 0
    pa = root / "_shared-memory" / "sinister-memory" / "per-agent"
    assert (pa / "lane-a").is_dir()
    assert (pa / "lane-b").is_dir()
    a_files = list((pa / "lane-a").glob("progress-*.md"))
    b_files = list((pa / "lane-b").glob("progress-*.md"))
    assert len(a_files) == 1
    assert len(b_files) == 1


def test_sweep_idempotent_second_run(tmp_path):
    root = _two_lane_root(tmp_path)
    adoption_sweep.sweep_progress_to_per_agent(root)
    stats2 = adoption_sweep.sweep_progress_to_per_agent(root)
    assert stats2["written"] == 0
    assert stats2["unchanged"] == 2


def test_sweep_dry_run_writes_nothing(tmp_path):
    root = _two_lane_root(tmp_path)
    stats = adoption_sweep.sweep_progress_to_per_agent(root, dry_run=True)
    assert stats["dry_run"] is True
    assert stats["processed"] == 2
    assert stats.get("written", 0) == 0
    pa = root / "_shared-memory" / "sinister-memory" / "per-agent"
    assert not (pa / "lane-a").exists() or not list((pa / "lane-a").glob("*.md"))


def test_sweep_skips_lane_with_no_progress_file(tmp_path):
    lanes = [{"key": "ghost-lane", "display": "Ghost"}]
    root = _make_synthetic_root(tmp_path, lanes, {})  # no PROGRESS file
    stats = adoption_sweep.sweep_progress_to_per_agent(root)
    assert stats["processed"] == 0
    assert stats["skipped_no_progress"] == 1


def test_sweep_skips_invalid_slug(tmp_path):
    lanes = [{"key": "BAD CAPS", "display": "Bad"}]
    root = _make_synthetic_root(tmp_path, lanes, {"Bad": "## h\nbody\n"})
    stats = adoption_sweep.sweep_progress_to_per_agent(root)
    assert stats["skipped_invalid_slug"] == 1


def test_sweep_max_per_lane_2_walks_two_headings(tmp_path):
    root = _two_lane_root(tmp_path)  # lane-a has 2 headings
    stats = adoption_sweep.sweep_progress_to_per_agent(root, max_per_lane=2)
    assert stats["written"] == 3  # 2 from lane-a + 1 from lane-b


# ---------------------------------------------------------------------------
# 9. health adoption climbs after sweep (end-to-end leverage check)
# ---------------------------------------------------------------------------
def test_health_adoption_climbs_after_sweep(tmp_path):
    root = _two_lane_root(tmp_path)
    # Need 3 lanes for adoption math; add one more without a progress file so
    # the sweep can't grab it (proves we measure actual coverage, not 100%).
    proj = root / "automations" / "session-templates" / "projects.json"
    data = json.loads(proj.read_text(encoding="utf-8"))
    data["projects"].append({"key": "lane-c", "display": "Lane C"})
    proj.write_text(json.dumps(data), encoding="utf-8")
    before_score, before_detail = health._sub_adoption(root)
    assert before_score == pytest.approx(0.0)
    assert before_detail["adopted_lanes"] == 0
    adoption_sweep.sweep_progress_to_per_agent(root)
    after_score, after_detail = health._sub_adoption(root)
    # 2 of 3 lanes now adopted -> 66.67%
    assert after_detail["adopted_lanes"] == 2
    assert after_detail["total_lanes"] == 3
    assert after_score > before_score


# ---------------------------------------------------------------------------
# 10. CLI subcommand smoke
# ---------------------------------------------------------------------------
def test_cli_sweep_adoption_dry_run_json(tmp_path):
    root = _two_lane_root(tmp_path)
    proc = subprocess.run(
        [
            sys.executable, "-m", "sinister_memory.cli",
            "--root", str(root),
            "sweep-adoption", "--dry-run", "--json",
        ],
        capture_output=True, text=True, timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["dry_run"] is True
    assert payload["processed"] == 2


def test_cli_sweep_adoption_apply(tmp_path):
    root = _two_lane_root(tmp_path)
    proc = subprocess.run(
        [
            sys.executable, "-m", "sinister_memory.cli",
            "--root", str(root),
            "sweep-adoption",
        ],
        capture_output=True, text=True, timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    assert "written=2" in proc.stdout
    pa = root / "_shared-memory" / "sinister-memory" / "per-agent"
    assert list((pa / "lane-a").glob("progress-*.md"))
    assert list((pa / "lane-b").glob("progress-*.md"))
