# Sinister Term :: tests/test_progress_of_builtin.py
# Author: RKOJ-ELENO :: 2026-05-26
# License: AGPL-3.0-or-later
#
# iter-76: /progress-of (alias /po) — read a peer agent's PROGRESS log.

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest


_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


@pytest.fixture
def fake_progress(tmp_path):
    base = tmp_path / "PROGRESS"
    base.mkdir()

    # Three agent logs + the two excluded files (_TEMPLATE.md, README.md)
    # + a .log non-md file to make sure the glob only picks .md files.
    (base / "Sinister OS.md").write_text(
        "# Agent: Sinister OS\n\n---\n\n"
        "## 2026-05-26 10:30 — shipped: VM preview overhaul\n"
        "Frame-cap throttled to 60 fps.\n\n"
        "## 2026-05-26 09:00 — shipped: dashboard skeleton inheritance\n"
        "Plugged the panel into the sinister theme tokens.\n\n"
        "## 2026-05-25 22:00 — shipped: novnc/x11vnc/port fix\n"
        "Bound to 127.0.0.1.\n\n"
        "## 2026-05-25 18:00 — shipped: jcode .desktop pattern\n"
        "## 2026-05-25 14:00 — shipped: phase 1A boot\n"
        "## 2026-05-25 10:00 — shipped: kernel APK boot path\n",
        encoding="utf-8",
    )
    (base / "Sinister Memory.md").write_text(
        "# Agent: Sinister Memory\n\n"
        "## 2026-05-26 08:30 — shipped: iter-22 contradict-results\n"
        "Brain entry shipped to sanctum-wide knowledge.\n",
        encoding="utf-8",
    )
    (base / "Eve EXE.md").write_text(
        "",
        encoding="utf-8",
    )
    (base / "_TEMPLATE.md").write_text("(should never appear)", encoding="utf-8")
    (base / "README.md").write_text("(should never appear)", encoding="utf-8")
    (base / "account-24h-watch-smoke.test.log").write_text("not md", encoding="utf-8")

    from term import commands as cmd_mod
    with patch.object(cmd_mod, "PROGRESS_DIR", base):
        yield base


def test_progress_of_no_args_lists_all_with_mtime_and_size(fake_progress):
    from term.commands import cmd_progress_of
    res = cmd_progress_of([])
    assert res.handled is True
    assert "3 agents" in res.output
    assert "sinister-os" in res.output
    assert "sinister-memory" in res.output
    assert "eve-exe" in res.output
    # excludes
    assert "TEMPLATE" not in res.output.upper().replace("KIB", "")
    assert "README" not in res.output.upper().replace("KIB", "")
    # NOT including .log files
    assert "smoke.test" not in res.output
    # KiB column present
    assert "KiB" in res.output


def test_progress_of_listing_newest_first(fake_progress):
    """Files sorted by mtime descending."""
    from term.commands import cmd_progress_of
    sos = fake_progress / "Sinister OS.md"
    smem = fake_progress / "Sinister Memory.md"
    eve = fake_progress / "Eve EXE.md"
    now = time.time()
    os.utime(sos, (now - 60, now - 60))
    os.utime(smem, (now - 3600, now - 3600))
    os.utime(eve, (now - 86400, now - 86400))
    res = cmd_progress_of([])
    rows = [l for l in res.output.splitlines() if l.startswith("  ")]
    # sinister-os (60s) is first; eve-exe (1d) is last
    assert "sinister-os" in rows[0]
    assert "eve-exe" in rows[-1]


def test_progress_of_exact_slug_default_5(fake_progress):
    from term.commands import cmd_progress_of
    res = cmd_progress_of(["sinister-os"])
    assert "PROGRESS-of sinister-os" in res.output
    assert "5 of top 5" in res.output
    # Top 5 entries shown
    assert "VM preview overhaul" in res.output
    assert "dashboard skeleton inheritance" in res.output
    # The 6th oldest entry should NOT appear (default 5)
    assert "kernel APK boot path" not in res.output


def test_progress_of_explicit_limit(fake_progress):
    from term.commands import cmd_progress_of
    res = cmd_progress_of(["sinister-os", "2"])
    assert "2 of top 2" in res.output
    assert "VM preview overhaul" in res.output
    # Third entry should NOT appear
    assert "novnc" not in res.output


def test_progress_of_substring_unique(fake_progress):
    """Substring match resolves to single slug."""
    from term.commands import cmd_progress_of
    res = cmd_progress_of(["memory"])
    assert "PROGRESS-of sinister-memory" in res.output


def test_progress_of_substring_ambiguous(fake_progress):
    """Substring matching multiple slugs returns candidates list."""
    from term.commands import cmd_progress_of
    # 'sinister' matches sinister-os + sinister-memory
    res = cmd_progress_of(["sinister"])
    assert "ambiguous" in res.output
    assert "sinister-memory" in res.output and "sinister-os" in res.output


def test_progress_of_no_match(fake_progress):
    from term.commands import cmd_progress_of
    res = cmd_progress_of(["totally-nonexistent"])
    assert "no PROGRESS log matching" in res.output
    assert "available:" in res.output


def test_progress_of_invalid_limit(fake_progress):
    from term.commands import cmd_progress_of
    res = cmd_progress_of(["sinister-os", "not-a-number"])
    assert "must be an integer" in res.output


def test_progress_of_limit_clamped(fake_progress):
    """Out-of-range limits are clamped silently."""
    from term.commands import cmd_progress_of
    # 999 clamped to 50; sinister-os has 6 entries, so we still see all 6
    res = cmd_progress_of(["sinister-os", "999"])
    assert "6 of top 50" in res.output


def test_progress_of_missing_dir(tmp_path):
    """Missing PROGRESS dir returns clear msg."""
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "PROGRESS_DIR", tmp_path / "nope"):
        res = cmd_mod.cmd_progress_of([])
    assert "no PROGRESS files" in res.output


def test_progress_of_empty_log(fake_progress):
    """Reading an agent with an empty PROGRESS file returns a clear msg."""
    from term.commands import cmd_progress_of
    res = cmd_progress_of(["eve-exe"])
    assert "empty" in res.output


def test_progress_of_no_heading_entries(fake_progress, tmp_path):
    """A log file with text but no `## ` headings reports 'no entries yet'."""
    target = fake_progress / "no-headings.md"
    target.write_text("just freeform text, no headings here\n", encoding="utf-8")
    from term.commands import cmd_progress_of
    res = cmd_progress_of(["no-headings"])
    assert "no `## ` entries" in res.output


def test_progress_of_case_insensitive(fake_progress):
    from term.commands import cmd_progress_of
    res = cmd_progress_of(["SINISTER-OS"])
    assert "PROGRESS-of sinister-os" in res.output


def test_progress_of_strips_leading_slash(fake_progress):
    """`/progress-of /sinister-os` strips the leading slash from the arg."""
    from term.commands import cmd_progress_of
    res = cmd_progress_of(["/sinister-os"])
    assert "PROGRESS-of sinister-os" in res.output


def test_progress_of_dispatch_via_slash(fake_progress):
    from term.commands import dispatch
    res = dispatch("/progress-of")
    assert res.handled is True
    assert "3 agents" in res.output


def test_progress_of_alias_po_dispatch(fake_progress):
    from term.commands import dispatch
    res = dispatch("/po sinister-memory 1")
    assert res.handled is True
    assert "PROGRESS-of sinister-memory" in res.output
    assert "1 of top 1" in res.output


def test_progress_of_in_help():
    from term.commands import cmd_help
    res = cmd_help([])
    assert "/progress-of" in res.output


def test_progress_of_slug_kebab_conversion(fake_progress):
    """Display name 'Eve EXE.md' becomes slug 'eve-exe'."""
    from term.commands import cmd_progress_of
    # Exact slug-form match should resolve directly.
    res = cmd_progress_of(["eve-exe"])
    # eve is empty so we get the empty msg, but the slug resolved.
    assert "empty" in res.output


def test_progress_of_excludes_template_and_readme(fake_progress):
    """`_TEMPLATE.md` and `README.md` never list and never resolve as a slug."""
    from term.commands import cmd_progress_of
    res_template = cmd_progress_of(["_template"])
    assert "no PROGRESS log matching" in res_template.output
    res_readme = cmd_progress_of(["readme"])
    assert "no PROGRESS log matching" in res_readme.output
