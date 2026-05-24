"""CLI smoke tests with click's test runner. RKOJ-ELENO :: 2026-05-24."""
from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from cli.imessage_cli import main as cli


def test_threads_command_lists_three(canned_chatdb: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["threads", "--chatdb", str(canned_chatdb)])
    assert result.exit_code == 0
    assert "3 thread(s)" in result.output


def test_threads_command_json(canned_chatdb: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["threads", "--chatdb", str(canned_chatdb), "--json"])
    assert result.exit_code == 0
    rows = json.loads(result.output)
    assert len(rows) == 3


def test_show_command_renders_messages(canned_chatdb: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["show", "1", "--chatdb", str(canned_chatdb), "--limit", "5"])
    assert result.exit_code == 0
    assert "chat 1" in result.output
    assert "canned sample msg" in result.output


def test_show_command_unknown_chat_exits_nonzero(canned_chatdb: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["show", "999", "--chatdb", str(canned_chatdb)])
    assert result.exit_code != 0


def test_schema_command_passes(canned_chatdb: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["schema", "--chatdb", str(canned_chatdb)])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["pass"] is True


def test_send_dry_run_succeeds(canned_chatdb: Path, tmp_path: Path, monkeypatch) -> None:
    # dry_run does not consult policy; --to is still required + body too
    policy = tmp_path / "contact-policy.md"
    policy.write_text(
        "## p2_allowed\n| handle | added_ts | operator_signed |\n|---|---|---|\n"
        "| +15551112222 | 2026-05-24 | yes |\n",
        encoding="utf-8",
    )
    from send_worker import send as send_mod  # submodule (re-export removed)
    monkeypatch.setattr(send_mod, "POLICY_PATH", policy)
    runner = CliRunner()
    result = runner.invoke(cli, [
        "send", "--to", "+15551112222", "--body", "hi", "--dry-run",
    ])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["status"] == "dry_run"
