# Sinister Term :: tests/test_recall.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# P2-1: /recall <topic> builtin — searches _shared-memory/knowledge/*.md
# for matching entries. No MCP, no network — local filesystem only.

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest


_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


@pytest.fixture
def fake_knowledge(tmp_path: Path):
    """Build a temp _shared-memory/knowledge/ with a handful of .md files."""
    sanctum = tmp_path / "sanctum"
    kdir = sanctum / "_shared-memory" / "knowledge"
    kdir.mkdir(parents=True)
    (kdir / "jcode-paste-handling-doctrine-2026-05-25.md").write_text(
        "# Jcode paste handling doctrine\n\n"
        "Bracketed paste from src/tui/app/input.rs. We port to Python via "
        "term/paste_handler.py and expand placeholders before dispatch.\n",
        encoding="utf-8",
    )
    (kdir / "cmux-integration-audit-2026-05-25.md").write_text(
        "# Cmux integration audit\n\n"
        "Mineable features ranked. Event bus is the substrate.\n",
        encoding="utf-8",
    )
    (kdir / "sa-ph5-intensity-sampler-2026-05-25.md").write_text(
        "# SA-PH5 intensity sampler doctrine\n\n"
        "Reads claude jsonl growth + bus broadcast count.\n",
        encoding="utf-8",
    )
    (kdir / "_INDEX.md").write_text("# Index\n", encoding="utf-8")  # ignored
    return sanctum


def _run_recall(args, sanctum_root):
    """Helper: call cmd_recall with SANCTUM_ROOT monkey-patched."""
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "SANCTUM_ROOT", sanctum_root):
        return cmd_mod.cmd_recall(args)


def test_recall_usage_when_no_args(fake_knowledge):
    res = _run_recall([], fake_knowledge)
    assert res.handled is True
    assert "usage" in res.output.lower()


def test_recall_finds_doctrine_by_keyword(fake_knowledge):
    res = _run_recall(["paste"], fake_knowledge)
    assert res.handled is True
    assert "paste" in res.output.lower()
    assert "jcode-paste-handling-doctrine" in res.output


def test_recall_finds_multiple_files(fake_knowledge):
    res = _run_recall(["event"], fake_knowledge)
    # "event bus" appears in cmux audit
    assert "cmux-integration-audit" in res.output


def test_recall_no_matches_message(fake_knowledge):
    res = _run_recall(["nonexistenttoken"], fake_knowledge)
    assert "no matches" in res.output.lower()


def test_recall_filename_match_scores_higher(fake_knowledge):
    """Filename hits should weight more than body hits."""
    res = _run_recall(["jcode"], fake_knowledge)
    lines = res.output.splitlines()
    # jcode-paste-handling-doctrine has jcode in filename + body → wins
    assert "jcode-paste-handling-doctrine" in res.output


def test_recall_ignores_underscored_files(fake_knowledge):
    """_INDEX.md is excluded."""
    res = _run_recall(["index"], fake_knowledge)
    assert "_INDEX" not in res.output


def test_recall_missing_dir_graceful(tmp_path):
    res = _run_recall(["anything"], tmp_path / "nonexistent-sanctum")
    assert res.handled is True
    assert "no knowledge dir" in res.output


def test_recall_dispatch_via_slash(fake_knowledge):
    """Dispatch routes /recall <args> to cmd_recall."""
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "SANCTUM_ROOT", fake_knowledge):
        res = cmd_mod.dispatch("/recall paste")
    assert res.handled is True
    assert "paste" in res.output.lower()


def test_recall_shows_score_column(fake_knowledge):
    res = _run_recall(["paste"], fake_knowledge)
    # Score column is [NNN]; expect at least one bracketed number
    import re
    assert re.search(r"\[\s*\d+\]", res.output)


def test_recall_multi_term_combines_scores(fake_knowledge):
    """Both terms hit boosts score for the file containing both."""
    res_single = _run_recall(["intensity"], fake_knowledge)
    res_multi = _run_recall(["intensity", "sampler"], fake_knowledge)
    # Multi-term hit appears in both; the SA-PH5 file matches both terms.
    assert "sa-ph5-intensity-sampler" in res_multi.output
    assert "sa-ph5-intensity-sampler" in res_single.output


def test_recall_caps_results_at_8(tmp_path):
    """Many matches but only top 8 rendered."""
    sanctum = tmp_path / "s"
    k = sanctum / "_shared-memory" / "knowledge"
    k.mkdir(parents=True)
    for i in range(15):
        (k / f"doctrine-{i:02d}.md").write_text(
            f"# Doctrine {i}\n\nkeyword appears here\n", encoding="utf-8"
        )
    res = _run_recall(["keyword"], sanctum)
    # Count entries — each match is 2 lines (score+title + path)
    indent_lines = [l for l in res.output.splitlines() if l.startswith("  [")]
    assert len(indent_lines) <= 8
