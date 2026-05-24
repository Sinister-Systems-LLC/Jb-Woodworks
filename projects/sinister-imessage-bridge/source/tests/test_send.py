"""Send-path tests with subprocess monkeypatched. RKOJ-ELENO :: 2026-05-24."""
from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import patch

import pytest

from send_worker import send as send_module  # NOTE: this imports the submodule, not the re-exported fn
from send_worker.send import send, reset_rate_limiter


@pytest.fixture(autouse=True)
def _isolate_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Each test gets a fresh contact-policy.md path + cleared rate limiter."""
    policy = tmp_path / "contact-policy.md"
    policy.write_text(
        "## p2_allowed\n"
        "| handle | added_ts | operator_signed |\n"
        "|---|---|---|\n"
        "| +15551112222 | 2026-05-24 | yes |\n"
        "| +15553334444 | 2026-05-24 | yes |\n"
        "| +15559999999 | 2026-05-24 | no  |\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(send_module, "POLICY_PATH", policy)
    reset_rate_limiter()


def test_blocks_without_operator_ok() -> None:
    r = send("iMessage", "+15551112222", "hi")
    assert r["status"] == "blocked"
    assert r["reason"] == "operator_ok=False"


def test_blocks_recipient_not_in_allowlist() -> None:
    r = send("iMessage", "+15550000000", "hi", operator_ok=True)
    assert r["status"] == "blocked"
    assert "p2_allowed" in r["reason"]


def test_blocks_unsigned_allowlist_row() -> None:
    # +15559999999 is in the policy file but signed=no
    r = send("iMessage", "+15559999999", "hi", operator_ok=True)
    assert r["status"] == "blocked"
    assert "p2_allowed" in r["reason"]


def test_dry_run_skips_subprocess() -> None:
    with patch.object(send_module.subprocess, "run") as mock_run:
        r = send("iMessage", "+15551112222", "hi", operator_ok=True, dry_run=True)
    assert r["status"] == "dry_run"
    assert r["body_len"] == 2
    mock_run.assert_not_called()


def test_rate_limit_blocks_second_send_within_window() -> None:
    fake_ok = type("R", (), {"stdout": "OK\n", "stderr": "", "returncode": 0})()
    with patch.object(send_module.subprocess, "run", return_value=fake_ok):
        r1 = send("iMessage", "+15551112222", "msg1", operator_ok=True)
        r2 = send("iMessage", "+15551112222", "msg2", operator_ok=True)
    assert r1["status"] == "ok"
    assert r2["status"] == "blocked"
    assert r2["reason"] == "rate_limit"


def test_rate_limit_clears_after_window(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_ok = type("R", (), {"stdout": "OK\n", "stderr": "", "returncode": 0})()
    t = [0.0]

    def fake_monotonic() -> float:
        return t[0]

    monkeypatch.setattr(send_module.time, "monotonic", fake_monotonic)
    with patch.object(send_module.subprocess, "run", return_value=fake_ok):
        t[0] = 0.0
        r1 = send("iMessage", "+15551112222", "msg1", operator_ok=True)
        assert r1["status"] == "ok"
        t[0] = 4.5
        r2 = send("iMessage", "+15551112222", "msg2", operator_ok=True)
        assert r2["status"] == "blocked"
        t[0] = 6.0
        r3 = send("iMessage", "+15551112222", "msg3", operator_ok=True)
        assert r3["status"] == "ok"


def test_rate_limit_per_recipient_not_global() -> None:
    fake_ok = type("R", (), {"stdout": "OK\n", "stderr": "", "returncode": 0})()
    with patch.object(send_module.subprocess, "run", return_value=fake_ok):
        r1 = send("iMessage", "+15551112222", "msg1", operator_ok=True)
        r2 = send("iMessage", "+15553334444", "msg2", operator_ok=True)
    assert r1["status"] == "ok"
    assert r2["status"] == "ok"


def test_applescript_error_returns_error_status() -> None:
    fake_err = type("R", (), {"stdout": "ERR 1700 user canceled\n", "stderr": "", "returncode": 0})()
    with patch.object(send_module.subprocess, "run", return_value=fake_err):
        r = send("iMessage", "+15551112222", "hi", operator_ok=True)
    assert r["status"] == "error"
    assert "ERR" in r["stdout"]
