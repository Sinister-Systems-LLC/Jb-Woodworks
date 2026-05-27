# Sinister Term :: tests/test_rmux.py
# Author: RKOJ-ELENO :: 2026-05-26
# License: AGPL-3.0-or-later
#
# Unit tests for term.rmux (htop-style fleet monitor — port of agtop).

from __future__ import annotations

import json
from pathlib import Path

import pytest

from term import rmux
from term.commands import cmd_rmux, dispatch


# ---------------------------------------------------------------------------
# Pricing / model normalization
# ---------------------------------------------------------------------------


def test_normalize_model_strips_1m_suffix():
    assert rmux._normalize_model("claude-opus-4-7[1m]") == "claude-opus-4-7"


def test_normalize_model_handles_none():
    assert rmux._normalize_model(None) == "unknown"
    assert rmux._normalize_model("") == "unknown"


def test_price_for_known_model():
    p = rmux._price_for("claude-opus-4-7")
    assert p["input"] == 5.0 and p["output"] == 25.0


def test_price_for_unknown_model_falls_back_by_family():
    p = rmux._price_for("claude-opus-future-X")
    assert p["input"] == 5.0  # opus family fallback


def test_price_for_completely_unknown_model_uses_opus_default():
    p = rmux._price_for("totally-made-up-model")
    assert p["input"] == rmux.DEFAULT_PRICING["input"]


def test_ctx_max_1m_tag_promotes_window():
    assert rmux._ctx_max_for("claude-opus-4-7", "claude-opus-4-7[1m]") == 1_000_000


def test_ctx_max_default_is_200k():
    assert rmux._ctx_max_for("claude-opus-4-7", "claude-opus-4-7") == 200_000


# ---------------------------------------------------------------------------
# JSONL parsing — synthetic session
# ---------------------------------------------------------------------------


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")


def _assistant_row(model="claude-opus-4-7", in_tok=1000, out_tok=500,
                   cw_tok=2000, cr_tok=8000, tool_name="Bash",
                   ts="2026-05-26T20:00:00Z", cw_5m=0, cw_1h=0):
    usage = {
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        "cache_creation_input_tokens": cw_tok,
        "cache_read_input_tokens": cr_tok,
    }
    if cw_5m or cw_1h:
        usage["cache_creation"] = {
            "ephemeral_5m_input_tokens": cw_5m,
            "ephemeral_1h_input_tokens": cw_1h,
        }
    return {
        "type": "assistant",
        "timestamp": ts,
        "cwd": "D:/foo/proj",
        "gitBranch": "agent/sinister-term/test",
        "version": "2.1.119",
        "sessionId": "sess-abc",
        "message": {
            "model": model,
            "usage": usage,
            "content": [
                {"type": "thinking", "thinking": "..."},
                {"type": "tool_use", "name": tool_name, "input": {}},
            ],
        },
    }


def test_parse_minimal_session(tmp_path: Path):
    proj_dir = tmp_path / "D--Sinister-Sanctum-projects-sinister-term"
    proj_dir.mkdir(parents=True)
    jsonl = proj_dir / "abc.jsonl"
    _write_jsonl(jsonl, [
        {"type": "permission-mode", "permissionMode": "auto", "sessionId": "abc"},
        _assistant_row(),
    ])
    sess = rmux.parse_jsonl_session(jsonl)
    assert sess.session_id == "abc"
    assert sess.project_dir == "sinister-term"
    assert sess.model == "claude-opus-4-7"
    assert sess.turn_count == 1
    assert sess.input_tokens == 1000
    assert sess.output_tokens == 500
    assert sess.cache_creation_tokens == 2000
    assert sess.cache_read_tokens == 8000
    assert sess.last_ctx_tokens == 1000 + 2000 + 8000  # output NOT included


def test_parse_skips_blank_and_corrupt_lines(tmp_path: Path):
    jsonl = tmp_path / "x.jsonl"
    jsonl.write_text(
        "\n"
        "not-json{{}\n"
        + json.dumps(_assistant_row()) + "\n"
        "more-garbage\n"
        + json.dumps(_assistant_row(in_tok=2000)) + "\n",
        encoding="utf-8",
    )
    sess = rmux.parse_jsonl_session(jsonl)
    assert sess.turn_count == 2
    assert sess.input_tokens == 3000


def test_parse_tool_counts_aggregate(tmp_path: Path):
    jsonl = tmp_path / "x.jsonl"
    _write_jsonl(jsonl, [
        _assistant_row(tool_name="Bash"),
        _assistant_row(tool_name="Bash"),
        _assistant_row(tool_name="Read"),
        _assistant_row(tool_name="Grep"),
    ])
    sess = rmux.parse_jsonl_session(jsonl)
    assert sess.tool_counts == {"Bash": 2, "Read": 1, "Grep": 1}
    assert sess.top_tool == "Bash"


def test_parse_handles_5m_1h_cache_split(tmp_path: Path):
    jsonl = tmp_path / "x.jsonl"
    _write_jsonl(jsonl, [_assistant_row(cw_5m=10000, cw_1h=4000, cw_tok=14000)])
    sess = rmux.parse_jsonl_session(jsonl)
    assert sess.cache_write_5m_tokens == 10000
    assert sess.cache_write_1h_tokens == 4000


def test_parse_missing_file_sets_error(tmp_path: Path):
    sess = rmux.parse_jsonl_session(tmp_path / "does-not-exist.jsonl")
    assert sess.parse_error
    assert sess.turn_count == 0


def test_parse_ignores_non_assistant_rows(tmp_path: Path):
    jsonl = tmp_path / "x.jsonl"
    _write_jsonl(jsonl, [
        {"type": "user", "timestamp": "2026-05-26T20:00:00Z"},
        {"type": "system", "subtype": "compact_boundary",
         "timestamp": "2026-05-26T20:01:00Z"},
        {"type": "permission-mode", "permissionMode": "auto"},
        _assistant_row(),
    ])
    sess = rmux.parse_jsonl_session(jsonl)
    assert sess.turn_count == 1


# ---------------------------------------------------------------------------
# Cost / CTX formulas
# ---------------------------------------------------------------------------


def test_cost_matches_agtop_formula(tmp_path: Path):
    jsonl = tmp_path / "x.jsonl"
    _write_jsonl(jsonl, [
        _assistant_row(in_tok=1_000_000, out_tok=0, cw_tok=0, cr_tok=0,
                       cw_5m=0, cw_1h=0),
    ])
    sess = rmux.parse_jsonl_session(jsonl)
    # 1M input tokens @ opus = $5.00
    assert sess.cost_usd == pytest.approx(5.0, rel=1e-6)


def test_cost_aggregates_all_token_types(tmp_path: Path):
    jsonl = tmp_path / "x.jsonl"
    _write_jsonl(jsonl, [
        _assistant_row(in_tok=1_000_000, out_tok=1_000_000,
                       cw_tok=0, cr_tok=1_000_000,
                       cw_5m=1_000_000, cw_1h=1_000_000),
    ])
    sess = rmux.parse_jsonl_session(jsonl)
    # opus rates: in=5, out=25, cw5m=6.25, cw1h=10, cr=0.5
    expected = 5.0 + 25.0 + 6.25 + 10.0 + 0.5
    assert sess.cost_usd == pytest.approx(expected, rel=1e-6)


def test_ctx_pct_basis_excludes_output(tmp_path: Path):
    jsonl = tmp_path / "x.jsonl"
    _write_jsonl(jsonl, [
        _assistant_row(in_tok=20_000, out_tok=100_000,
                       cw_tok=30_000, cr_tok=50_000),
    ])
    sess = rmux.parse_jsonl_session(jsonl)
    # last_ctx = 20k + 30k + 50k = 100k; ctx_pct = 100k/200k = 50%
    assert sess.last_ctx_tokens == 100_000
    assert sess.ctx_pct == pytest.approx(50.0, rel=1e-6)


def test_ctx_pct_promotes_to_1m_when_huge_usage(tmp_path: Path):
    jsonl = tmp_path / "x.jsonl"
    _write_jsonl(jsonl, [
        _assistant_row(in_tok=300_000, out_tok=0, cw_tok=0, cr_tok=0),
    ])
    sess = rmux.parse_jsonl_session(jsonl)
    # 300k > 200k → auto-promote to 1m window → 30% not 100%
    assert sess.last_ctx_tokens == 300_000
    assert sess.ctx_pct == pytest.approx(30.0, rel=1e-6)


# ---------------------------------------------------------------------------
# Discovery + scanning
# ---------------------------------------------------------------------------


def test_discover_returns_empty_when_root_missing(tmp_path: Path):
    assert rmux.discover_sessions(tmp_path / "nope") == []


def test_discover_sorts_newest_first(tmp_path: Path):
    import os, time
    p1 = tmp_path / "proj-a"
    p2 = tmp_path / "proj-b"
    p1.mkdir(); p2.mkdir()
    f1 = p1 / "old.jsonl"; f1.write_text("")
    f2 = p2 / "new.jsonl"; f2.write_text("")
    os.utime(f1, (time.time() - 10000, time.time() - 10000))
    os.utime(f2, (time.time(), time.time()))
    found = rmux.discover_sessions(tmp_path)
    assert [p.name for p in found] == ["new.jsonl", "old.jsonl"]


def test_discover_honors_since_seconds(tmp_path: Path):
    import os, time
    p1 = tmp_path / "proj-a"; p1.mkdir()
    old = p1 / "old.jsonl"; old.write_text("")
    new = p1 / "new.jsonl"; new.write_text("")
    os.utime(old, (time.time() - 10000, time.time() - 10000))
    found = rmux.discover_sessions(tmp_path, since_seconds=3600)
    assert [p.name for p in found] == ["new.jsonl"]


def test_scan_sessions_parses_each_file(tmp_path: Path):
    proj = tmp_path / "D--foo-projects-mine"
    proj.mkdir(parents=True)
    _write_jsonl(proj / "s1.jsonl", [_assistant_row(in_tok=100)])
    _write_jsonl(proj / "s2.jsonl", [_assistant_row(in_tok=200)])
    sessions = rmux.scan_sessions(tmp_path)
    assert len(sessions) == 2
    assert sum(s.input_tokens for s in sessions) == 300


# ---------------------------------------------------------------------------
# Sorting
# ---------------------------------------------------------------------------


def _mk_sess(**kw):
    s = rmux.RmuxSession(path=Path("/tmp/x"))
    for k, v in kw.items():
        setattr(s, k, v)
    return s


def test_sort_by_cost_descending():
    a = _mk_sess(input_tokens=10_000_000, model="claude-opus-4-7")
    b = _mk_sess(input_tokens=1_000_000, model="claude-opus-4-7")
    ordered = rmux.sort_sessions([b, a], "cost")
    assert ordered[0] is a


def test_sort_by_age_newest_first():
    import time
    now = time.time()
    a = _mk_sess(last_active=now - 100)
    b = _mk_sess(last_active=now)
    ordered = rmux.sort_sessions([a, b], "age")
    assert ordered[0] is b


def test_sort_unknown_key_falls_back_to_age():
    import time
    now = time.time()
    a = _mk_sess(last_active=now - 100)
    b = _mk_sess(last_active=now)
    ordered = rmux.sort_sessions([a, b], "totally-bogus")
    assert ordered[0] is b


# ---------------------------------------------------------------------------
# Formatter
# ---------------------------------------------------------------------------


def test_format_table_empty():
    assert rmux.format_table([]) == "(no sessions)"


def test_format_table_renders_columns():
    import time
    s = _mk_sess(
        session_id="abc123",
        project_dir="sinister-term",
        model="claude-opus-4-7",
        last_active=time.time(),
        input_tokens=1000, output_tokens=500,
        cache_creation_tokens=2000, cache_read_tokens=8000,
        last_ctx_tokens=11000, turn_count=3,
        tool_counts={"Bash": 5},
    )
    out = rmux.format_table([s])
    assert "sinister-term" in out
    assert "claude-opus-4-7" in out
    assert "Bash" in out
    assert "sessions: 1" in out
    assert "live: 1" in out


def test_format_table_live_filter():
    import time
    fresh = _mk_sess(project_dir="fresh", last_active=time.time())
    stale = _mk_sess(project_dir="stale", last_active=time.time() - 99999)
    out = rmux.format_table([fresh, stale], live_only=True)
    assert "fresh" in out
    assert "stale" not in out


def test_format_table_limit_clamped():
    import time
    sessions = [_mk_sess(project_dir=f"p{i}", last_active=time.time() - i)
                for i in range(50)]
    out = rmux.format_table(sessions, limit=5)
    assert "p0" in out and "p4" in out
    assert "p10" not in out


def test_format_session_detail_includes_all_sections():
    s = _mk_sess(
        session_id="xyz",
        project_dir="myproj",
        cwd="D:/x",
        git_branch="agent/test",
        cc_version="2.1.119",
        model="claude-opus-4-7",
        raw_model="claude-opus-4-7",
        input_tokens=1000, output_tokens=500,
        cache_creation_tokens=2000, cache_read_tokens=8000,
        last_ctx_tokens=11000,
        turn_count=4,
        tool_counts={"Bash": 5, "Read": 3},
    )
    out = rmux.format_session_detail(s)
    assert "Session  xyz" in out
    assert "Branch   agent/test" in out
    assert "Bash" in out and "Read" in out
    assert "CTX%" in out
    assert "Cost" in out


# ---------------------------------------------------------------------------
# /rmux dispatch / cmd_rmux
# ---------------------------------------------------------------------------


def test_cmd_rmux_help_arg():
    r = cmd_rmux(["help"])
    assert r.handled
    assert "Sinister rmux" in r.output


def test_cmd_rmux_unknown_arg_rejected():
    r = cmd_rmux(["totally-bogus-flag"])
    assert r.handled
    assert "unknown" in r.output.lower()


def test_cmd_rmux_bad_sort_key_rejected():
    r = cmd_rmux(["sort=totally-bogus"])
    assert r.handled
    assert "sort" in r.output.lower()


def test_dispatch_routes_slash_rmux():
    r = dispatch("/rmux help")
    assert r.handled
    assert "Sinister rmux" in r.output


def test_dispatch_routes_slash_agtop_alias():
    r = dispatch("/agtop help")
    assert r.handled
    assert "Sinister rmux" in r.output


def test_help_lists_rmux():
    from term.commands import cmd_help
    r = cmd_help([])
    assert "/rmux" in r.output


# Truncation helper

def test_truncate_short_string_unchanged():
    assert rmux._truncate("abc", 10) == "abc"


def test_truncate_long_string_ends_with_ellipsis():
    out = rmux._truncate("abcdefghij", 5)
    assert out.endswith("…")
    assert len(out) == 5


# Project shorthand

def test_short_project_extracts_after_projects_segment():
    assert rmux._short_project("D--Sinister-Sanctum-projects-sinister-term") == "sinister-term"


def test_short_project_strips_source_suffix():
    assert (
        rmux._short_project("D--Sinister-Sanctum-projects-letstext-source")
        == "letstext"
    )


def test_short_project_fallback_when_no_marker():
    assert rmux._short_project("flat-name") == "name"


# Formatters

def test_fmt_age_buckets():
    assert rmux._fmt_age(0) == "0s"
    assert rmux._fmt_age(45) == "45s"
    assert rmux._fmt_age(125) == "2m05s"
    assert rmux._fmt_age(3661).startswith("1h")
    assert rmux._fmt_age(90000).startswith("1d")


def test_fmt_int_buckets():
    assert rmux._fmt_int(0) == "0"
    assert rmux._fmt_int(999) == "999"
    assert rmux._fmt_int(1500) == "1.5k"
    assert rmux._fmt_int(2_500_000) == "2.50M"


def test_fmt_cost_thresholds():
    assert rmux._fmt_cost(0.0001) == "$0.0001"
    assert rmux._fmt_cost(0.50) == "$0.500"
    assert rmux._fmt_cost(15.0) == "$15.00"
