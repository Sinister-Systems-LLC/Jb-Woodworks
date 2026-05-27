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


# ---------------------------------------------------------------------------
# iter-78 — CLI / watch mode
# ---------------------------------------------------------------------------


def _stub_scan(monkeypatch, sessions):
    """Make scan_sessions return a fixed list (bypass filesystem)."""
    monkeypatch.setattr(rmux, "scan_sessions",
                        lambda *a, **kw: list(sessions))


def test_render_snapshot_returns_table(monkeypatch):
    import time
    s = _mk_sess(project_dir="myproj", last_active=time.time(),
                 model="claude-opus-4-7", input_tokens=1000, turn_count=2)
    _stub_scan(monkeypatch, [s])
    out = rmux.render_snapshot()
    assert "myproj" in out
    assert "claude-opus-4-7" in out


def test_render_snapshot_project_filter(monkeypatch):
    import time
    a = _mk_sess(project_dir="alpha-lane", last_active=time.time())
    b = _mk_sess(project_dir="bravo-lane", last_active=time.time())
    _stub_scan(monkeypatch, [a, b])
    out = rmux.render_snapshot(project="bravo")
    assert "bravo" in out
    assert "alpha" not in out


def test_render_json_emits_valid_json(monkeypatch):
    import time
    s = _mk_sess(session_id="abc", project_dir="p", model="claude-opus-4-7",
                 last_active=time.time(), input_tokens=1000,
                 output_tokens=500, turn_count=3)
    _stub_scan(monkeypatch, [s])
    out = rmux.render_json()
    payload = json.loads(out)
    assert payload["schema"] == "sinister.rmux.snapshot.v1"
    assert payload["session_count"] == 1
    assert payload["sessions"][0]["session_id"] == "abc"
    assert "ctx_pct" in payload["sessions"][0]
    assert "tool_counts" in payload["sessions"][0]


def test_render_json_aggregates_totals(monkeypatch):
    a = _mk_sess(input_tokens=1_000_000, output_tokens=0, model="claude-opus-4-7")
    b = _mk_sess(input_tokens=0, output_tokens=1_000_000, model="claude-opus-4-7")
    _stub_scan(monkeypatch, [a, b])
    out = rmux.render_json()
    payload = json.loads(out)
    # a contributes $5 (1M input * $5/M), b contributes $25 (1M output * $25/M)
    assert payload["total_cost_usd"] == pytest.approx(30.0, abs=0.01)
    assert payload["total_input_tokens"] == 1_000_000
    assert payload["total_output_tokens"] == 1_000_000


def test_render_detail_exact_match(monkeypatch):
    s = _mk_sess(session_id="xyz123abc", project_dir="p", model="claude-opus-4-7")
    _stub_scan(monkeypatch, [s])
    out = rmux.render_detail("xyz123abc")
    assert "Session  xyz123abc" in out


def test_render_detail_substring_unique(monkeypatch):
    s = _mk_sess(session_id="xyz123abc", project_dir="p", model="claude-opus-4-7")
    _stub_scan(monkeypatch, [s])
    out = rmux.render_detail("xyz12")
    assert "Session  xyz123abc" in out


def test_render_detail_ambiguous(monkeypatch):
    a = _mk_sess(session_id="abc111111", model="claude-opus-4-7")
    b = _mk_sess(session_id="abc222222", model="claude-opus-4-7")
    _stub_scan(monkeypatch, [a, b])
    out = rmux.render_detail("abc")
    assert "ambiguous" in out.lower()
    assert "abc11111" in out and "abc22222" in out


def test_render_detail_no_match(monkeypatch):
    _stub_scan(monkeypatch, [])
    out = rmux.render_detail("nothing")
    assert "no session matches" in out


def test_session_to_dict_includes_derived_fields():
    import time
    s = _mk_sess(session_id="t", model="claude-opus-4-7",
                 last_active=time.time(), input_tokens=1000)
    d = rmux._session_to_dict(s)
    for key in ("session_id", "model", "ctx_pct", "cost_usd", "is_live",
                "age_seconds", "top_tool", "tool_counts"):
        assert key in d


def test_watch_loop_runs_fixed_iterations(monkeypatch):
    """watch_loop returns after `iterations` renders without sleeping forever."""
    sleeps: list[float] = []
    writes: list[str] = []
    monkeypatch.setattr(rmux, "scan_sessions", lambda *a, **kw: [])
    n = rmux.watch_loop(interval=1.0, iterations=3, clear=False,
                        sleep_fn=lambda s: sleeps.append(s),
                        write_fn=lambda x: writes.append(x),
                        flush_fn=lambda: None)
    assert n == 3
    # sleep is skipped after the final render (loop returns first), so we
    # expect iterations-1 sleep calls
    assert len(sleeps) == 2
    body = "".join(writes)
    assert "(no sessions)" in body
    assert "rmux watch" in body


def test_watch_loop_clear_screen_when_enabled(monkeypatch):
    writes: list[str] = []
    monkeypatch.setattr(rmux, "scan_sessions", lambda *a, **kw: [])
    rmux.watch_loop(interval=0.5, iterations=1, clear=True,
                    sleep_fn=lambda s: None,
                    write_fn=lambda x: writes.append(x),
                    flush_fn=lambda: None)
    assert rmux._CLEAR in writes


def test_watch_loop_no_clear_when_disabled(monkeypatch):
    writes: list[str] = []
    monkeypatch.setattr(rmux, "scan_sessions", lambda *a, **kw: [])
    rmux.watch_loop(interval=0.5, iterations=1, clear=False,
                    sleep_fn=lambda s: None,
                    write_fn=lambda x: writes.append(x),
                    flush_fn=lambda: None)
    assert rmux._CLEAR not in writes


def test_watch_loop_handles_keyboard_interrupt(monkeypatch):
    def boom(_s):
        raise KeyboardInterrupt
    writes: list[str] = []
    monkeypatch.setattr(rmux, "scan_sessions", lambda *a, **kw: [])
    n = rmux.watch_loop(interval=0.5, iterations=10, clear=False,
                        sleep_fn=boom,
                        write_fn=lambda x: writes.append(x),
                        flush_fn=lambda: None)
    assert n == 1


def test_main_json_returns_zero(monkeypatch, capsys):
    monkeypatch.setattr(rmux, "scan_sessions", lambda *a, **kw: [])
    rc = rmux.main(["--json"])
    out = capsys.readouterr().out
    assert rc == 0
    payload = json.loads(out)
    assert payload["schema"] == "sinister.rmux.snapshot.v1"
    assert payload["session_count"] == 0


def test_main_default_snapshot_returns_zero(monkeypatch, capsys):
    monkeypatch.setattr(rmux, "scan_sessions", lambda *a, **kw: [])
    rc = rmux.main([])
    out = capsys.readouterr().out
    assert rc == 0
    assert "(no sessions)" in out


def test_main_detail_returns_zero(monkeypatch, capsys):
    monkeypatch.setattr(rmux, "scan_sessions", lambda *a, **kw: [])
    rc = rmux.main(["--detail", "anything"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "no session matches" in out


def test_main_unknown_sort_rejected(monkeypatch, capsys):
    with pytest.raises(SystemExit):
        rmux.main(["--sort", "totally-bogus"])


def test_main_watch_calls_loop_with_args(monkeypatch):
    captured = {}

    def fake_loop(**kw):
        captured.update(kw)
        return 1

    monkeypatch.setattr(rmux, "watch_loop", fake_loop)
    rc = rmux.main(["--watch", "0.25", "--sort", "cost", "--live", "--limit", "5"])
    assert rc == 0
    assert captured["interval"] == 0.25
    assert captured["sort"] == "cost"
    assert captured["live_only"] is True
    assert captured["limit"] == 5


def test_main_watch_no_arg_uses_default_interval(monkeypatch):
    captured = {}

    def fake_loop(**kw):
        captured.update(kw)
        return 1

    monkeypatch.setattr(rmux, "watch_loop", fake_loop)
    rmux.main(["--watch"])
    assert captured["interval"] == rmux._DEFAULT_WATCH_INTERVAL


def test_main_watch_clamps_too_small_interval(monkeypatch):
    captured = {}

    def fake_loop(**kw):
        captured.update(kw)
        return 1

    monkeypatch.setattr(rmux, "watch_loop", fake_loop)
    rmux.main(["--watch", "0.001"])
    assert captured["interval"] >= 0.25


def test_build_argparser_registers_all_flags():
    p = rmux.build_argparser()
    actions = {a.dest for a in p._actions}
    for k in ("watch", "json", "limit", "live", "sort", "project",
              "detail", "since_hours", "max_files", "show_path", "no_clear"):
        assert k in actions


# ---------------------------------------------------------------------------
# iter-80 — fleet-slug cross-reference
# ---------------------------------------------------------------------------


@pytest.fixture
def fleet_root(tmp_path: Path, monkeypatch):
    """SANCTUM_ROOT pointed at tmp_path with a heartbeats dir prepared."""
    monkeypatch.setenv("SANCTUM_ROOT", str(tmp_path))
    (tmp_path / "_shared-memory" / "heartbeats").mkdir(parents=True)
    return tmp_path


def _write_hb(root: Path, slug: str, **extra):
    p = root / "_shared-memory" / "heartbeats" / f"{slug}.json"
    data = {"agent": slug, "ts_utc": "2026-05-27T00:00:00Z", "alive": True}
    data.update(extra)
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def test_norm_cwd_normalizes_slashes():
    assert rmux._norm_cwd("D:\\Sinister Sanctum\\foo") == "d:/sinister sanctum/foo"


def test_norm_cwd_lowercases():
    assert rmux._norm_cwd("D:/Foo/Bar") == "d:/foo/bar"


def test_norm_cwd_strips_trailing_slash():
    assert rmux._norm_cwd("D:/foo/") == "d:/foo"


def test_norm_cwd_empty():
    assert rmux._norm_cwd("") == ""


def test_build_fleet_cwd_index_collects_entries(fleet_root):
    _write_hb(fleet_root, "sinister-term",
              cwd="D:/Sinister Sanctum/projects/sinister-term")
    idx = rmux._build_fleet_cwd_index()
    assert "d:/sinister sanctum/projects/sinister-term" in idx
    slug, age = idx["d:/sinister sanctum/projects/sinister-term"]
    assert slug == "sinister-term"
    assert age >= 0


def test_build_fleet_cwd_index_skips_no_cwd(fleet_root):
    _write_hb(fleet_root, "agent-without-cwd")
    idx = rmux._build_fleet_cwd_index()
    assert idx == {}


def test_build_fleet_cwd_index_missing_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("SANCTUM_ROOT", str(tmp_path / "nope"))
    assert rmux._build_fleet_cwd_index() == {}


def test_build_fleet_slug_age_index_lists_all(fleet_root):
    _write_hb(fleet_root, "sinister-term")
    _write_hb(fleet_root, "eve-exe")
    _write_hb(fleet_root, "kernel-apk")
    idx = rmux._build_fleet_slug_age_index()
    assert {"sinister-term", "eve-exe", "kernel-apk"} <= set(idx.keys())
    for v in idx.values():
        assert v >= 0


def test_build_fleet_slug_age_index_missing_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("SANCTUM_ROOT", str(tmp_path / "nope"))
    assert rmux._build_fleet_slug_age_index() == {}


def test_scan_sessions_attaches_fleet_slug_via_cwd(fleet_root):
    # write a session in tmp/projects-folder/file.jsonl + a matching heartbeat
    proj = fleet_root / "fakehome" / ".claude" / "projects" / "D--Sinister-Sanctum-projects-sinister-term"
    proj.mkdir(parents=True)
    jsonl = proj / "s1.jsonl"
    jsonl.write_text(
        json.dumps({
            "type": "assistant",
            "timestamp": "2026-05-27T00:00:00Z",
            "cwd": "D:/Sinister Sanctum/projects/sinister-term",
            "message": {
                "model": "claude-opus-4-7",
                "usage": {"input_tokens": 100, "output_tokens": 50,
                          "cache_creation_input_tokens": 0,
                          "cache_read_input_tokens": 0},
                "content": [{"type": "tool_use", "name": "Bash"}],
            },
        }),
        encoding="utf-8",
    )
    _write_hb(fleet_root, "sinister-term",
              cwd="D:/Sinister Sanctum/projects/sinister-term")
    sessions = rmux.scan_sessions(root=fleet_root / "fakehome" / ".claude" / "projects")
    assert len(sessions) == 1
    assert sessions[0].fleet_slug == "sinister-term"
    assert sessions[0].fleet_heartbeat_age_sec >= 0


def test_scan_sessions_attaches_fleet_slug_via_project_dir(fleet_root):
    # heartbeat exists for `eve-exe` (short slug); JSONL project_dir == eve-exe.
    proj = fleet_root / "fakehome" / ".claude" / "projects" / "D--Sinister-Sanctum-projects-eve-exe"
    proj.mkdir(parents=True)
    jsonl = proj / "s1.jsonl"
    jsonl.write_text(
        json.dumps({
            "type": "assistant", "timestamp": "2026-05-27T00:00:00Z",
            "cwd": "",  # heartbeat doesn't have cwd to match either
            "message": {"model": "claude-opus-4-7",
                        "usage": {"input_tokens": 1, "output_tokens": 1,
                                  "cache_creation_input_tokens": 0,
                                  "cache_read_input_tokens": 0},
                        "content": []},
        }),
        encoding="utf-8",
    )
    _write_hb(fleet_root, "eve-exe")
    sessions = rmux.scan_sessions(root=fleet_root / "fakehome" / ".claude" / "projects")
    assert sessions[0].fleet_slug == "eve-exe"


def test_scan_sessions_shorter_slug_fallback(fleet_root):
    # heartbeat = `kernel-apk`; JSONL project_dir = `sinister-kernel-apk`
    proj = fleet_root / "fakehome" / ".claude" / "projects" / "D--Sinister-Sanctum-projects-sinister-kernel-apk"
    proj.mkdir(parents=True)
    (proj / "s.jsonl").write_text(
        json.dumps({
            "type": "assistant", "timestamp": "2026-05-27T00:00:00Z", "cwd": "",
            "message": {"model": "claude-opus-4-7",
                        "usage": {"input_tokens": 1, "output_tokens": 1,
                                  "cache_creation_input_tokens": 0,
                                  "cache_read_input_tokens": 0},
                        "content": []},
        }), encoding="utf-8",
    )
    _write_hb(fleet_root, "kernel-apk")
    sessions = rmux.scan_sessions(root=fleet_root / "fakehome" / ".claude" / "projects")
    assert sessions[0].fleet_slug == "kernel-apk"


def test_scan_sessions_longer_slug_fallback(fleet_root):
    # heartbeat = `sinister-os`; JSONL project_dir = `os`
    proj = fleet_root / "fakehome" / ".claude" / "projects" / "D--Sinister-Sanctum-projects-os"
    proj.mkdir(parents=True)
    (proj / "s.jsonl").write_text(
        json.dumps({
            "type": "assistant", "timestamp": "2026-05-27T00:00:00Z", "cwd": "",
            "message": {"model": "claude-opus-4-7",
                        "usage": {"input_tokens": 1, "output_tokens": 1,
                                  "cache_creation_input_tokens": 0,
                                  "cache_read_input_tokens": 0},
                        "content": []},
        }), encoding="utf-8",
    )
    _write_hb(fleet_root, "sinister-os")
    sessions = rmux.scan_sessions(root=fleet_root / "fakehome" / ".claude" / "projects")
    assert sessions[0].fleet_slug == "sinister-os"


def test_scan_sessions_no_match_leaves_slug_empty(fleet_root):
    proj = fleet_root / "fakehome" / ".claude" / "projects" / "D--Sinister-Sanctum-projects-orphan"
    proj.mkdir(parents=True)
    (proj / "s.jsonl").write_text(
        json.dumps({
            "type": "assistant", "timestamp": "2026-05-27T00:00:00Z", "cwd": "",
            "message": {"model": "claude-opus-4-7",
                        "usage": {"input_tokens": 1, "output_tokens": 1,
                                  "cache_creation_input_tokens": 0,
                                  "cache_read_input_tokens": 0},
                        "content": []},
        }), encoding="utf-8",
    )
    # no matching heartbeat
    sessions = rmux.scan_sessions(root=fleet_root / "fakehome" / ".claude" / "projects")
    assert sessions[0].fleet_slug == ""
    assert sessions[0].fleet_heartbeat_age_sec == 0.0


def test_scan_sessions_attach_fleet_slugs_disabled(fleet_root):
    proj = fleet_root / "fakehome" / ".claude" / "projects" / "D--Sinister-Sanctum-projects-sinister-term"
    proj.mkdir(parents=True)
    (proj / "s.jsonl").write_text(
        json.dumps({
            "type": "assistant", "timestamp": "2026-05-27T00:00:00Z",
            "cwd": "D:/Sinister Sanctum/projects/sinister-term",
            "message": {"model": "claude-opus-4-7",
                        "usage": {"input_tokens": 1, "output_tokens": 1,
                                  "cache_creation_input_tokens": 0,
                                  "cache_read_input_tokens": 0},
                        "content": []},
        }), encoding="utf-8",
    )
    _write_hb(fleet_root, "sinister-term",
              cwd="D:/Sinister Sanctum/projects/sinister-term")
    sessions = rmux.scan_sessions(
        root=fleet_root / "fakehome" / ".claude" / "projects",
        attach_fleet_slugs=False,
    )
    assert sessions[0].fleet_slug == ""


def test_format_table_shows_fleet_column_when_any_set():
    import time
    s = _mk_sess(project_dir="foo", model="claude-opus-4-7",
                 last_active=time.time(), fleet_slug="sinister-foo")
    out = rmux.format_table([s])
    assert "fleet" in out
    assert "sinister-foo" in out


def test_format_table_omits_fleet_column_when_none():
    import time
    s = _mk_sess(project_dir="foo", model="claude-opus-4-7",
                 last_active=time.time(), fleet_slug="")
    out = rmux.format_table([s])
    # fleet column is auto-suppressed when no row carries a slug
    assert "fleet" not in out.split("\n")[0]


def test_format_session_detail_includes_fleet_row():
    s = _mk_sess(session_id="x", project_dir="foo", model="claude-opus-4-7",
                 fleet_slug="sinister-foo", fleet_heartbeat_age_sec=120.0)
    out = rmux.format_session_detail(s)
    assert "Fleet" in out
    assert "sinister-foo" in out
    assert "heartbeat age" in out


def test_format_session_detail_handles_missing_fleet():
    s = _mk_sess(session_id="x", project_dir="foo", model="claude-opus-4-7",
                 fleet_slug="")
    out = rmux.format_session_detail(s)
    assert "Fleet" in out
    assert "no matching heartbeat" in out


def test_session_to_dict_includes_fleet_fields():
    s = _mk_sess(session_id="x", model="claude-opus-4-7",
                 fleet_slug="sinister-foo", fleet_heartbeat_age_sec=42.0)
    d = rmux._session_to_dict(s)
    assert d["fleet_slug"] == "sinister-foo"
    assert d["fleet_heartbeat_age_sec"] == 42.0
