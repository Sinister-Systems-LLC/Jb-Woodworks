# Sinister Term :: tests/test_rmux_verbs.py
# Author: RKOJ-ELENO :: 2026-05-26
# License: AGPL-3.0-or-later
#
# Unit tests for term.rmux_verbs — the verb-based management surface of
# rmux (spawn/stop/kill/focus/attach/logs/projects/help/ls/watch/json/detail).

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from term import rmux_verbs as rv
from term import rmux as rm


# ---------------------------------------------------------------------------
# Fixture: redirect SANCTUM_ROOT into a tmp_path for hermetic tests
# ---------------------------------------------------------------------------


@pytest.fixture
def sanctum(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("SANCTUM_ROOT", str(tmp_path))
    # set up the directory skeleton
    (tmp_path / "_shared-memory" / "heartbeats").mkdir(parents=True)
    (tmp_path / "_shared-memory" / "inbox").mkdir(parents=True)
    (tmp_path / "_shared-memory" / "PROGRESS").mkdir(parents=True)
    (tmp_path / "automations" / "session-templates").mkdir(parents=True)
    # minimal projects.json
    (tmp_path / "automations" / "session-templates" / "projects.json").write_text(
        json.dumps({
            "version": 99,
            "projects": [
                {"key": "sanctum", "display_name": "Sinister Sanctum",
                 "tier": 1, "accent": "purple"},
                {"key": "sinister-term", "display_name": "Sinister Term",
                 "tier": 2, "accent": "purple"},
                {"key": "sinister-os", "display_name": "Sinister OS",
                 "tier": 2, "accent": "blue"},
            ],
        }),
        encoding="utf-8",
    )
    return tmp_path


# ---------------------------------------------------------------------------
# Projects registry helpers
# ---------------------------------------------------------------------------


def test_load_projects_returns_list(sanctum):
    projects = rv.load_projects()
    assert len(projects) == 3
    keys = {p["key"] for p in projects}
    assert keys == {"sanctum", "sinister-term", "sinister-os"}


def test_load_projects_returns_empty_when_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("SANCTUM_ROOT", str(tmp_path))
    assert rv.load_projects() == []


def test_load_projects_tolerates_corrupt_json(sanctum):
    (sanctum / "automations" / "session-templates" / "projects.json").write_text(
        "this is not json{{",
        encoding="utf-8",
    )
    assert rv.load_projects() == []


def test_lookup_project_exact_key(sanctum):
    p, cands = rv.lookup_project("sinister-term")
    assert p is not None and p["key"] == "sinister-term"
    assert cands == []


def test_lookup_project_substring_unique(sanctum):
    p, cands = rv.lookup_project("term")
    assert p is not None and p["key"] == "sinister-term"


def test_lookup_project_substring_ambiguous(sanctum):
    p, cands = rv.lookup_project("sinister")
    assert p is None
    assert len(cands) >= 2


def test_lookup_project_no_match(sanctum):
    p, cands = rv.lookup_project("nothing-here")
    assert p is None
    assert cands == []


def test_lookup_project_matches_display_name(sanctum):
    p, cands = rv.lookup_project("Sanctum")
    assert p is not None and p["key"] == "sanctum"


# ---------------------------------------------------------------------------
# Heartbeat helpers
# ---------------------------------------------------------------------------


def _write_hb(sanctum: Path, slug: str, **fields):
    hb = sanctum / "_shared-memory" / "heartbeats" / f"{slug}.json"
    data = {"agent": slug, "ts_utc": "2026-05-26T23:50:00Z",
            "alive": True, **fields}
    hb.write_text(json.dumps(data), encoding="utf-8")
    return hb


def test_load_heartbeat_returns_dict(sanctum):
    _write_hb(sanctum, "sinister-term", mode="resume")
    hb = rv.load_heartbeat("sinister-term")
    assert hb is not None
    assert hb["mode"] == "resume"


def test_load_heartbeat_missing(sanctum):
    assert rv.load_heartbeat("nonexistent") is None


def test_load_heartbeat_corrupt(sanctum):
    p = sanctum / "_shared-memory" / "heartbeats" / "bad.json"
    p.write_text("not-json{", encoding="utf-8")
    assert rv.load_heartbeat("bad") is None


def test_list_live_slugs_filters_by_age(sanctum):
    _write_hb(sanctum, "fresh-a")
    _write_hb(sanctum, "fresh-b")
    stale = _write_hb(sanctum, "stale-c")
    # set stale's mtime to 2 hours ago
    long_ago = time.time() - 7200
    os.utime(stale, (long_ago, long_ago))
    live = rv.list_live_slugs(max_age_minutes=30)
    slugs = {s for s, _ in live}
    assert "fresh-a" in slugs and "fresh-b" in slugs
    assert "stale-c" not in slugs


def test_resolve_slug_exact(sanctum):
    _write_hb(sanctum, "sinister-term")
    s, cands = rv.resolve_slug("sinister-term")
    assert s == "sinister-term"


def test_resolve_slug_substring_unique(sanctum):
    _write_hb(sanctum, "sinister-term")
    _write_hb(sanctum, "sinister-os")
    s, cands = rv.resolve_slug("term")
    assert s == "sinister-term"


def test_resolve_slug_substring_ambiguous(sanctum):
    _write_hb(sanctum, "sinister-term")
    _write_hb(sanctum, "sinister-os")
    s, cands = rv.resolve_slug("sinister")
    assert s is None
    assert len(cands) >= 2


def test_resolve_slug_no_match(sanctum):
    _write_hb(sanctum, "sinister-term")
    s, cands = rv.resolve_slug("doesnt-exist")
    assert s is None and cands == []


# ---------------------------------------------------------------------------
# verb_projects
# ---------------------------------------------------------------------------


def test_verb_projects_lists_each(sanctum):
    r = rv.verb_projects([])
    assert r.ok
    assert "sanctum" in r.text
    assert "sinister-term" in r.text
    assert "sinister-os" in r.text
    assert "3 project(s)" in r.text


def test_verb_projects_no_registry(monkeypatch, tmp_path):
    monkeypatch.setenv("SANCTUM_ROOT", str(tmp_path))
    r = rv.verb_projects([])
    assert not r.ok


# ---------------------------------------------------------------------------
# verb_ls / verb_watch / verb_json / verb_detail (monitor wrappers)
# ---------------------------------------------------------------------------


def test_verb_ls_returns_table(monkeypatch):
    monkeypatch.setattr(rm, "scan_sessions", lambda *a, **kw: [])
    r = rv.verb_ls([])
    assert r.ok
    assert "(no sessions)" in r.text


def test_verb_ls_with_bad_sort(monkeypatch):
    monkeypatch.setattr(rm, "scan_sessions", lambda *a, **kw: [])
    r = rv.verb_ls(["sort=totally-bogus"])
    assert not r.ok


def test_verb_json_emits_schema(monkeypatch):
    monkeypatch.setattr(rm, "scan_sessions", lambda *a, **kw: [])
    r = rv.verb_json([])
    assert r.ok
    payload = json.loads(r.text)
    assert payload["schema"] == "sinister.rmux.snapshot.v1"
    assert payload["session_count"] == 0


def test_verb_watch_routes_to_loop(monkeypatch):
    captured = {}

    def fake_loop(**kw):
        captured.update(kw)
        return 1

    monkeypatch.setattr(rm, "watch_loop", fake_loop)
    monkeypatch.setattr(rm, "scan_sessions", lambda *a, **kw: [])
    r = rv.verb_watch(["1.5", "live", "sort=cost"])
    assert r.ok
    assert captured["interval"] == 1.5
    assert captured["live_only"] is True
    assert captured["sort"] == "cost"


def test_verb_watch_default_interval(monkeypatch):
    captured = {}

    def fake_loop(**kw):
        captured.update(kw)
        return 0

    monkeypatch.setattr(rm, "watch_loop", fake_loop)
    rv.verb_watch([])
    assert captured["interval"] == rm._DEFAULT_WATCH_INTERVAL


def test_verb_detail_no_args(monkeypatch):
    monkeypatch.setattr(rm, "scan_sessions", lambda *a, **kw: [])
    r = rv.verb_detail([])
    assert not r.ok


def test_verb_detail_no_match(monkeypatch):
    monkeypatch.setattr(rm, "scan_sessions", lambda *a, **kw: [])
    r = rv.verb_detail(["xyz"])
    assert r.ok  # ok=True; text says no match
    assert "no session matches" in r.text


# ---------------------------------------------------------------------------
# verb_spawn
# ---------------------------------------------------------------------------


def test_verb_spawn_no_args(sanctum):
    r = rv.verb_spawn([])
    assert not r.ok
    assert "usage" in r.text.lower()


def test_verb_spawn_unknown_project(sanctum):
    r = rv.verb_spawn(["nonexistent-key"])
    assert not r.ok
    assert "no project matches" in r.text


def test_verb_spawn_ambiguous_project(sanctum):
    r = rv.verb_spawn(["sinister"])
    assert not r.ok
    assert "ambiguous" in r.text.lower()


def test_verb_spawn_no_script_present(sanctum, monkeypatch):
    # spawn script doesn't exist (we haven't created the automations one)
    monkeypatch.setattr(rv, "_resolve_powershell", lambda: "powershell.exe")
    r = rv.verb_spawn(["sinister-term"])
    assert not r.ok
    assert "spawn script not found" in r.text


def test_verb_spawn_no_powershell(sanctum, monkeypatch):
    # create stub script so we get to the powershell check
    (sanctum / "automations" / "start-sinister-session.ps1").write_text("", encoding="utf-8")
    monkeypatch.setattr(rv, "_resolve_powershell", lambda: None)
    r = rv.verb_spawn(["sinister-term"])
    assert not r.ok
    assert "powershell" in r.text.lower()


def test_verb_spawn_invokes_subprocess(sanctum, monkeypatch):
    (sanctum / "automations" / "start-sinister-session.ps1").write_text("", encoding="utf-8")
    monkeypatch.setattr(rv, "_resolve_powershell", lambda: "powershell.exe")
    captured = {}

    def fake_run(cmd, **kw):
        captured["cmd"] = cmd
        captured["cwd"] = kw.get("cwd")
        return SimpleNamespace(pid=12345)

    r = rv.verb_spawn(["sinister-term"], run_fn=fake_run)
    assert r.ok
    assert "sinister-term" in r.text
    assert "powershell.exe" in captured["cmd"][0]
    assert "-Project" in captured["cmd"]
    assert "sinister-term" in captured["cmd"]


def test_verb_spawn_passes_mode_arg(sanctum, monkeypatch):
    (sanctum / "automations" / "start-sinister-session.ps1").write_text("", encoding="utf-8")
    monkeypatch.setattr(rv, "_resolve_powershell", lambda: "powershell.exe")
    captured = {}

    def fake_run(cmd, **kw):
        captured["cmd"] = cmd
        return SimpleNamespace(pid=1)

    r = rv.verb_spawn(["sinister-term", "--mode", "loop"], run_fn=fake_run)
    assert r.ok
    assert "-Mode" in captured["cmd"]
    assert "loop" in captured["cmd"]


# ---------------------------------------------------------------------------
# verb_stop
# ---------------------------------------------------------------------------


def test_verb_stop_no_bat(sanctum):
    r = rv.verb_stop([])
    assert not r.ok
    assert "stop bat not found" in r.text


def test_verb_stop_success(sanctum):
    (sanctum / "Stop-EVE.bat").write_text("@echo off", encoding="utf-8")

    def fake_run(cmd, **kw):
        return SimpleNamespace(returncode=0, stdout="closed 3 sessions", stderr="")

    r = rv.verb_stop([], run_fn=fake_run)
    assert r.ok
    assert "stopped" in r.text.lower()


def test_verb_stop_nonzero_exit(sanctum):
    (sanctum / "Stop-EVE.bat").write_text("", encoding="utf-8")

    def fake_run(cmd, **kw):
        return SimpleNamespace(returncode=1, stdout="", stderr="boom")

    r = rv.verb_stop([], run_fn=fake_run)
    assert not r.ok
    assert "rc=1" in r.text
    assert "boom" in r.text


def test_verb_stop_quiet_flag(sanctum):
    (sanctum / "Stop-EVE.bat").write_text("", encoding="utf-8")

    def fake_run(cmd, **kw):
        return SimpleNamespace(returncode=0, stdout="noisy output", stderr="")

    r = rv.verb_stop(["--quiet"], run_fn=fake_run)
    assert r.ok
    assert "noisy output" not in r.text


# ---------------------------------------------------------------------------
# verb_kill — graceful inbox poke
# ---------------------------------------------------------------------------


def test_verb_kill_no_args():
    r = rv.verb_kill([])
    assert not r.ok


def test_verb_kill_unknown_slug(sanctum):
    r = rv.verb_kill(["nonexistent"])
    assert not r.ok
    assert "no agent matches" in r.text


def test_verb_kill_ambiguous_slug(sanctum):
    _write_hb(sanctum, "sinister-term")
    _write_hb(sanctum, "sinister-os")
    r = rv.verb_kill(["sinister"])
    assert not r.ok
    assert "ambiguous" in r.text.lower()


def test_verb_kill_writes_inbox_message(sanctum):
    _write_hb(sanctum, "sinister-term")
    r = rv.verb_kill(["sinister-term"])
    assert r.ok
    # locate the message file we just wrote
    inbox = sanctum / "_shared-memory" / "inbox" / "sinister-term"
    msgs = list(inbox.glob("*-from-sinister-term-rmux-kill.json"))
    assert len(msgs) == 1
    payload = json.loads(msgs[0].read_text(encoding="utf-8"))
    assert payload["to_slug"] == "sinister-term"
    assert payload["kind"] == "graceful-shutdown"
    assert payload["priority"] == "high"


def test_verb_kill_substring_unique(sanctum):
    _write_hb(sanctum, "sinister-term")
    r = rv.verb_kill(["term"])
    assert r.ok


# ---------------------------------------------------------------------------
# verb_focus / verb_attach
# ---------------------------------------------------------------------------


def test_verb_focus_no_args():
    r = rv.verb_focus([])
    assert not r.ok


def test_verb_focus_unknown_slug(sanctum):
    r = rv.verb_focus(["nonexistent"])
    assert not r.ok
    assert "no agent matches" in r.text


def test_verb_focus_success(sanctum, monkeypatch):
    _write_hb(sanctum, "sinister-term", agent_display="Sinister Term")
    monkeypatch.setattr(rv, "_resolve_powershell", lambda: "powershell.exe")

    def fake_run(cmd, **kw):
        # mimic AppActivate success
        return SimpleNamespace(stdout="OK\n", stderr="", returncode=0)

    r = rv.verb_focus(["sinister-term"], run_fn=fake_run)
    assert r.ok
    assert "focused" in r.text.lower()


def test_verb_focus_no_window_match(sanctum, monkeypatch):
    _write_hb(sanctum, "sinister-term")
    monkeypatch.setattr(rv, "_resolve_powershell", lambda: "powershell.exe")

    def fake_run(cmd, **kw):
        return SimpleNamespace(stdout="NOMATCH\n", stderr="", returncode=0)

    r = rv.verb_focus(["sinister-term"], run_fn=fake_run)
    assert not r.ok
    assert "no mintty window matched" in r.text


def test_verb_attach_alias_of_focus(sanctum, monkeypatch):
    _write_hb(sanctum, "sinister-term")
    monkeypatch.setattr(rv, "_resolve_powershell", lambda: "powershell.exe")

    def fake_run(cmd, **kw):
        return SimpleNamespace(stdout="OK\n", stderr="", returncode=0)

    r = rv.verb_attach(["sinister-term"], run_fn=fake_run)
    assert r.ok


# ---------------------------------------------------------------------------
# verb_logs
# ---------------------------------------------------------------------------


def test_verb_logs_no_args():
    r = rv.verb_logs([])
    assert not r.ok


def test_verb_logs_unknown_slug(sanctum):
    r = rv.verb_logs(["nonexistent"])
    assert not r.ok


def test_verb_logs_reads_display_name_file(sanctum):
    _write_hb(sanctum, "sinister-term")
    pf = sanctum / "_shared-memory" / "PROGRESS" / "Sinister Term.md"
    pf.write_text(
        "# Header\n\n"
        "## 2026-05-26 23:50 — shipped: iter-77\nbody1\n\n"
        "## 2026-05-26 21:00 — shipped: iter-76\nbody2\n",
        encoding="utf-8",
    )
    r = rv.verb_logs(["sinister-term", "2"])
    assert r.ok
    assert "iter-77" in r.text
    assert "iter-76" in r.text


def test_verb_logs_handles_no_headings(sanctum):
    _write_hb(sanctum, "sinister-term")
    pf = sanctum / "_shared-memory" / "PROGRESS" / "Sinister Term.md"
    pf.write_text("just some text, no markdown headings.", encoding="utf-8")
    r = rv.verb_logs(["sinister-term"])
    assert r.ok
    assert "no ## entries" in r.text


def test_verb_logs_missing_progress_file(sanctum):
    _write_hb(sanctum, "sinister-term")
    r = rv.verb_logs(["sinister-term"])
    assert not r.ok


def test_slug_to_display_basic():
    assert rv._slug_to_display("sinister-term") == "Sinister Term"


def test_slug_to_display_preserves_caps():
    # "OS" / "APK" should stay uppercase
    assert rv._slug_to_display("sinister-os") == "Sinister OS"
    assert rv._slug_to_display("kernel-apk") == "Kernel APK"


def test_slug_to_display_empty():
    assert rv._slug_to_display("") == ""


# ---------------------------------------------------------------------------
# verb_help + dispatcher
# ---------------------------------------------------------------------------


def test_verb_help_returns_usage():
    r = rv.verb_help([])
    assert r.ok
    assert "rmux spawn" in r.text
    assert "rmux watch" in r.text


def test_is_verb_recognizes_known_names():
    for name in ("ls", "watch", "json", "detail", "spawn", "stop", "kill",
                 "focus", "attach", "logs", "projects", "help", "start",
                 "list", "log", "?"):
        assert rv.is_verb(name)


def test_is_verb_rejects_unknown():
    assert not rv.is_verb("nonsense")
    assert not rv.is_verb("--help")
    assert not rv.is_verb("")


def test_dispatch_verb_unknown():
    r = rv.dispatch_verb("nonsense", [])
    assert not r.ok
    assert "unknown verb" in r.text


def test_dispatch_verb_help():
    r = rv.dispatch_verb("help", [])
    assert r.ok


# ---------------------------------------------------------------------------
# rmux.main() verb integration
# ---------------------------------------------------------------------------


def test_main_verb_help(monkeypatch, capsys):
    rc = rm.main(["help"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "rmux spawn" in out


def test_main_verb_ls(monkeypatch, capsys):
    monkeypatch.setattr(rm, "scan_sessions", lambda *a, **kw: [])
    rc = rm.main(["ls"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "(no sessions)" in out


def test_main_verb_projects(sanctum, capsys):
    rc = rm.main(["projects"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "sinister-term" in out


def test_main_unknown_verb_falls_through_to_argparse(monkeypatch, capsys):
    """`rmux some-unknown` is not a verb → argparse should reject."""
    with pytest.raises(SystemExit):
        rm.main(["nonexistent-verb-xyz"])


def test_main_flag_still_works_without_verb(monkeypatch, capsys):
    monkeypatch.setattr(rm, "scan_sessions", lambda *a, **kw: [])
    rc = rm.main(["--json"])
    out = capsys.readouterr().out
    assert rc == 0
    payload = json.loads(out)
    assert payload["schema"] == "sinister.rmux.snapshot.v1"
