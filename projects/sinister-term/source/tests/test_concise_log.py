# Sinister Term :: tests/test_concise_log.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# Parity tests against jcode's logging.rs:600+ test cases plus rate-limit
# coverage that jcode lacks.

from __future__ import annotations

import time

import pytest

from term import concise_log as cl


# ----- Sanitization / redaction (jcode logging.rs:611-660 parity) ------

class TestRedact:
    def test_redact_api_key(self):
        assert cl._redact_auth_field("api_key", "sk-secret") == "<redacted>"

    def test_redact_callback_url(self):
        assert cl._redact_auth_field("callback_url", "https://x/y?code=z") == "<redacted>"

    def test_does_not_redact_exit_code(self):
        # jcode test: keeps non-secret 'code' fields. exit_code passes through.
        # Note: jcode keeps exit_code because the test calls fmt_event with
        # 'exit_code', '127' which is non-redactable. We mirror the test —
        # our impl redacts anything with 'code' in the key UNLESS it's
        # one of the explicit non-secret patterns? Re-read jcode...
        # Actually jcode redacts key=='code' substring matches. Our list
        # includes 'auth_code', 'oauth_code', 'code_verifier', 'code_challenge'.
        # Plain 'exit_code' should NOT be redacted because none of those
        # substrings appear.
        assert cl._redact_auth_field("exit_code", "127") == "127"

    def test_sanitize_url_query(self):
        v = cl._sanitize_value("failed\nhttps://login.example.com/cb?code=secret&state=abc")
        assert v == "failed https://login.example.com/cb?<redacted>"


class TestStructuredEvent:
    def test_orders_and_redacts(self):
        line = cl._format_structured_event(
            "server_request",
            [("z", "last"), ("api_key", "sk-secret"), ("a field", "hello world")],
        )
        # jcode parity:
        # EVENT event=server_request a_field="hello world" api_key=<redacted> z=last
        assert line == 'EVENT event=server_request a_field="hello world" api_key=<redacted> z=last'

    def test_redacts_url_queries(self):
        line = cl._format_structured_event(
            "callback",
            [("url", "https://example.test/cb?code=secret&state=abc")],
        )
        assert line == "EVENT event=callback url=https://example.test/cb?<redacted>"

    def test_keeps_non_secret_code_fields(self):
        line = cl._format_structured_event("tool_done", [("exit_code", "127")])
        assert line == "EVENT event=tool_done exit_code=127"

    def test_json_mode(self, monkeypatch):
        monkeypatch.setenv("STERM_LOG_JSON", "1")
        line = cl._format_structured_event("e", [("k", "v")])
        assert line.startswith("EVENT_JSON ")
        # parse the json portion
        import json
        payload = json.loads(line[len("EVENT_JSON "):])
        assert payload["event"] == "e"
        assert payload["k"] == "v"


# ----- Rate limiting -----------------------------------------------------

class TestRateLimit:
    def test_first_emit_passes(self):
        cl._rate_limits.clear()
        should, sup = cl._maybe_emit_rate_limited("k1", 5.0)
        assert should is True
        assert sup == 0

    def test_within_window_suppresses(self):
        cl._rate_limits.clear()
        cl._maybe_emit_rate_limited("k2", 5.0)
        should, _ = cl._maybe_emit_rate_limited("k2", 5.0)
        assert should is False

    def test_outside_window_emits_with_suppressed_count(self):
        cl._rate_limits.clear()
        cl._maybe_emit_rate_limited("k3", 0.01)
        cl._maybe_emit_rate_limited("k3", 0.01)
        cl._maybe_emit_rate_limited("k3", 0.01)  # 2 suppressed
        time.sleep(0.05)
        should, sup = cl._maybe_emit_rate_limited("k3", 0.01)
        assert should is True
        assert sup == 2


# ----- Context prefix ----------------------------------------------------

class TestContextPrefix:
    def test_empty_context(self):
        cl._ctx().server = None
        cl._ctx().session = None
        cl._ctx().provider = None
        cl._ctx().model = None
        assert cl._context_prefix() == ""

    def test_full_context_renders(self):
        cl.set_server("srv1")
        cl.set_session("sess-abcdef-shorty")
        cl.set_provider_info("anthropic", "claude-opus-4-7-1m")
        out = cl._context_prefix()
        assert out.startswith("[")
        assert "srv:srv1" in out
        assert "ses:sess-abcdef-shorty" in out
        assert "prv:anthropic" in out
        assert "mod:claude" in out

    def test_session_truncated_at_20(self):
        cl.set_server(None) if False else None
        cl._ctx().server = None
        cl._ctx().provider = None
        cl._ctx().model = None
        cl.set_session("x" * 50)
        out = cl._context_prefix()
        assert "ses:" + ("x" * 20) in out

    def test_model_short_form(self):
        cl._ctx().server = None
        cl._ctx().session = None
        cl.set_provider_info("anthropic", "claude-3-7-sonnet")
        out = cl._context_prefix()
        assert "mod:claude" in out
        assert "mod:claude-3" not in out  # short form is just before first '-'


# ----- File backend ------------------------------------------------------

class TestFileBackend:
    def test_info_writes_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(cl, "LOG_DIR", tmp_path)
        # close any existing handle so it re-opens under new LOG_DIR
        if cl._fh is not None:
            try:
                cl._fh.close()
            except Exception:
                pass
            cl._fh = None
            cl._fh_date = None
        cl.info("HELLO")
        files = list(tmp_path.glob("sterm-*.log"))
        assert len(files) == 1
        content = files[0].read_text(encoding="utf-8")
        assert "HELLO" in content
        assert "[INFO]" in content

    def test_cleanup_old_logs(self, tmp_path, monkeypatch):
        monkeypatch.setattr(cl, "LOG_DIR", tmp_path)
        old = tmp_path / "sterm-2020-01-01.log"
        old.write_text("old")
        # Mark mtime to 10 days ago
        old_ts = time.time() - 10 * 86400
        import os
        os.utime(old, (old_ts, old_ts))
        new = tmp_path / "sterm-current.log"
        new.write_text("new")
        removed = cl.cleanup_old_logs(keep_days=7)
        assert removed == 1
        assert not old.exists()
        assert new.exists()


# ----- ConciseLogger wrapper --------------------------------------------

class TestConciseLogger:
    def test_default_singleton(self):
        a = cl.default()
        b = cl.default()
        assert a is b

    def test_info_does_not_raise(self, tmp_path, monkeypatch):
        monkeypatch.setattr(cl, "LOG_DIR", tmp_path)
        if cl._fh is not None:
            try:
                cl._fh.close()
            except Exception:
                pass
            cl._fh = None
            cl._fh_date = None
        log = cl.default()
        log.info("TEST_EVENT", foo="bar", n=42)
        files = list(tmp_path.glob("sterm-*.log"))
        assert files
        content = files[0].read_text(encoding="utf-8")
        assert "TEST_EVENT" in content
        assert "foo=bar" in content
        assert "n=42" in content
