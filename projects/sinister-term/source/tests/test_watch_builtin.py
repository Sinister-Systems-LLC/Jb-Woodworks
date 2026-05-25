# Sinister Term :: tests/test_watch_builtin.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# iter-61: /watch <relpath> tails any jsonl/text log under _shared-memory.

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


@pytest.fixture
def fake_sanctum(tmp_path):
    """Build a tmp SANCTUM_ROOT with _shared-memory/ inside it."""
    sanctum = tmp_path / "sanctum"
    (sanctum / "_shared-memory").mkdir(parents=True)
    from term import commands as cmd_mod
    with patch.object(cmd_mod, "SANCTUM_ROOT", sanctum):
        yield sanctum


def test_watch_no_args_shows_usage(fake_sanctum):
    from term.commands import cmd_watch
    res = cmd_watch([])
    assert "usage:" in res.output.lower()
    assert "/watch" in res.output


def test_watch_jsonl_tails_default_10(fake_sanctum):
    target = fake_sanctum / "_shared-memory" / "log.jsonl"
    lines = [json.dumps({"ts_utc": f"2026-05-25T00:00:{i:02d}Z",
                         "kind": "test", "i": i}) for i in range(20)]
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    from term.commands import cmd_watch
    res = cmd_watch(["log.jsonl"])
    assert "10 of 20 lines" in res.output
    # Last row (i=19) appears, first (i=0) doesn't
    assert "00:00:19" in res.output
    assert "00:00:00" not in res.output


def test_watch_explicit_limit(fake_sanctum):
    target = fake_sanctum / "_shared-memory" / "log.jsonl"
    lines = [json.dumps({"ts_utc": f"row-{i}", "kind": "k"}) for i in range(50)]
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    from term.commands import cmd_watch
    res = cmd_watch(["log.jsonl", "5"])
    assert "5 of 50 lines" in res.output


def test_watch_missing_file(fake_sanctum):
    from term.commands import cmd_watch
    res = cmd_watch(["nonexistent.jsonl"])
    assert "no file at" in res.output


def test_watch_empty_file(fake_sanctum):
    (fake_sanctum / "_shared-memory" / "empty.jsonl").write_text("", encoding="utf-8")
    from term.commands import cmd_watch
    res = cmd_watch(["empty.jsonl"])
    assert "empty:" in res.output


def test_watch_directory_path_rejected(fake_sanctum):
    (fake_sanctum / "_shared-memory" / "subdir").mkdir()
    from term.commands import cmd_watch
    res = cmd_watch(["subdir"])
    assert "directory" in res.output


def test_watch_path_traversal_blocked(fake_sanctum):
    """`../../etc/passwd`-style paths must escape the sandbox."""
    from term.commands import cmd_watch
    res = cmd_watch(["../../../etc/passwd"])
    assert "refused" in res.output
    assert "sandbox" in res.output


def test_watch_absolute_path_escapes_sandbox(tmp_path, fake_sanctum):
    """An absolute path that's outside SANCTUM_ROOT is rejected.

    Note: passing an absolute path means the `/` join logic may interpret
    it as fully replacing the prefix; either way, the relative_to() check
    rejects it.
    """
    from term.commands import cmd_watch
    res = cmd_watch([str(tmp_path / "outside.jsonl")])
    assert "refused" in res.output


def test_watch_subdirectory_path(fake_sanctum):
    sub = fake_sanctum / "_shared-memory" / "inbox" / "sinister-term"
    sub.mkdir(parents=True)
    (sub / "msg.jsonl").write_text(
        json.dumps({"ts_utc": "2026-05-25T00:00:00Z", "kind": "ASK"}) + "\n",
        encoding="utf-8",
    )
    from term.commands import cmd_watch
    res = cmd_watch(["inbox/sinister-term/msg.jsonl"])
    assert "1 of 1 lines" in res.output
    assert "ASK" in res.output


def test_watch_non_json_lines_pass_through(fake_sanctum):
    """Raw text lines (not JSON) still render."""
    target = fake_sanctum / "_shared-memory" / "raw.log"
    target.write_text("hello\nworld\nthird line\n", encoding="utf-8")
    from term.commands import cmd_watch
    res = cmd_watch(["raw.log"])
    assert "hello" in res.output
    assert "world" in res.output
    assert "third line" in res.output


def test_watch_truncates_long_lines(fake_sanctum):
    target = fake_sanctum / "_shared-memory" / "long.jsonl"
    target.write_text(json.dumps({"x": "y" * 300}) + "\n", encoding="utf-8")
    from term.commands import cmd_watch
    res = cmd_watch(["long.jsonl"])
    # 300-char value not in full
    assert "y" * 300 not in res.output


def test_watch_json_extracts_kind_field(fake_sanctum):
    target = fake_sanctum / "_shared-memory" / "log.jsonl"
    target.write_text(json.dumps({
        "ts_utc": "2026-05-25T12:00:00Z",
        "kind": "fleet-update",
        "msg": "x",
    }) + "\n", encoding="utf-8")
    from term.commands import cmd_watch
    res = cmd_watch(["log.jsonl"])
    assert "fleet-update" in res.output


def test_watch_handles_invalid_limit_arg(fake_sanctum):
    (fake_sanctum / "_shared-memory" / "x.jsonl").write_text("a\n", encoding="utf-8")
    from term.commands import cmd_watch
    res = cmd_watch(["x.jsonl", "notanumber"])
    assert "must be an integer" in res.output


def test_watch_dispatch_via_slash(fake_sanctum):
    (fake_sanctum / "_shared-memory" / "x.jsonl").write_text("a\nb\n", encoding="utf-8")
    from term.commands import dispatch
    res = dispatch("/watch x.jsonl 1")
    assert res.handled is True
    assert "1 of 2 lines" in res.output


def test_watch_in_help():
    from term.commands import cmd_help
    res = cmd_help([])
    assert "/watch" in res.output


def test_watch_skips_blank_lines(fake_sanctum):
    target = fake_sanctum / "_shared-memory" / "spaced.log"
    target.write_text("alpha\n\nbeta\n\n\ngamma\n", encoding="utf-8")
    from term.commands import cmd_watch
    res = cmd_watch(["spaced.log"])
    # Only 3 non-blank lines
    assert "3 of 3 lines" in res.output


def test_watch_big_file_only_reads_tail(fake_sanctum):
    """File > 256 KiB: only the last ~256 KiB is read."""
    target = fake_sanctum / "_shared-memory" / "big.log"
    # ~500 KiB of repeated lines
    line = "x" * 100 + "\n"
    text = line * 5000  # ~500 KB
    target.write_text(text, encoding="utf-8")
    from term.commands import cmd_watch
    res = cmd_watch(["big.log", "5"])
    # Should succeed without OOM
    assert "5 of" in res.output
