# Sinister Sanctum :: sinister-model :: CLI + state tests
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
from __future__ import annotations
import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from sinister_model.cli import cli, main
from sinister_model.state import (
    get_current,
    set_current,
    clear_current,
    state_path,
    SCHEMA_VERSION as STATE_SCHEMA,
)


@pytest.fixture
def runner():
    return CliRunner()


# ---------- state.py ---------------------------------------------------------

def test_state_path_honors_env_override(tmp_path, monkeypatch):
    custom = tmp_path / "subdir" / "x.json"
    monkeypatch.setenv("SINISTER_MODEL_STATE_PATH", str(custom))
    assert state_path() == custom


def test_get_current_returns_none_when_missing():
    assert get_current() is None


def test_set_current_then_get_current_roundtrip():
    out = set_current("claude-opus-4-7", provider="anthropic")
    assert out["model_id"] == "claude-opus-4-7"
    assert out["provider"] == "anthropic"
    assert out["schema"] == STATE_SCHEMA
    got = get_current()
    assert got is not None
    assert got["model_id"] == "claude-opus-4-7"


def test_set_current_creates_parent_dirs(tmp_path, monkeypatch):
    nested = tmp_path / "a" / "b" / "c" / "model.json"
    monkeypatch.setenv("SINISTER_MODEL_STATE_PATH", str(nested))
    set_current("gpt-5", provider="openai")
    assert nested.exists()


def test_clear_current_removes_file():
    set_current("gpt-4o", provider="openai")
    assert get_current() is not None
    assert clear_current() is True
    assert get_current() is None


def test_clear_current_returns_false_when_no_file():
    assert clear_current() is False


def test_corrupt_state_file_returns_none(tmp_path, monkeypatch):
    p = tmp_path / "corrupt.json"
    p.write_text("not-json{{{", encoding="utf-8")
    monkeypatch.setenv("SINISTER_MODEL_STATE_PATH", str(p))
    assert get_current() is None


# ---------- CLI: providers ---------------------------------------------------

def test_cli_providers_text(runner):
    res = runner.invoke(cli, ["providers"])
    assert res.exit_code == 0
    assert "anthropic" in res.output
    assert "openai" in res.output


def test_cli_providers_json(runner):
    res = runner.invoke(cli, ["providers", "--json"])
    assert res.exit_code == 0
    data = json.loads(res.output)
    assert data["ok"] is True
    assert len(data["providers"]) == 11
    assert data["total_models"] >= 30


# ---------- CLI: list --------------------------------------------------------

def test_cli_list_anthropic_text(runner):
    res = runner.invoke(cli, ["list", "anthropic"])
    assert res.exit_code == 0
    assert "claude-opus-4-7" in res.output


def test_cli_list_openai_json(runner):
    res = runner.invoke(cli, ["list", "openai", "--json"])
    assert res.exit_code == 0
    data = json.loads(res.output)
    assert data["ok"] is True
    assert data["provider"] == "openai"
    assert any(m["model_id"] == "gpt-5" for m in data["models"])
    assert data["source"] == "arg"


def test_cli_list_unknown_provider_exits_2(runner):
    res = runner.invoke(cli, ["list", "doesnotexist"])
    assert res.exit_code == 2


def test_cli_list_unknown_provider_json(runner):
    res = runner.invoke(cli, ["list", "doesnotexist", "--json"])
    assert res.exit_code == 2
    data = json.loads(res.output)
    assert data["ok"] is False
    assert "unknown" in data["error"]


def test_cli_list_alias_claude_works(runner):
    """sinister-login uses 'claude' for anthropic; CLI should accept it."""
    res = runner.invoke(cli, ["list", "claude", "--json"])
    assert res.exit_code == 0
    data = json.loads(res.output)
    assert data["provider"] == "anthropic"


def test_cli_list_no_provider_falls_back(runner, monkeypatch):
    """No provider arg + no sinister-login -> falls back to anthropic."""
    # Force the sinister-login detector to return None by faking import failure.
    import sys
    monkeypatch.setitem(sys.modules, "sinister_login", None)
    res = runner.invoke(cli, ["list", "--json"])
    assert res.exit_code == 0
    data = json.loads(res.output)
    assert data["provider"] == "anthropic"
    assert data["source"] in ("fallback", "login")  # 'login' if real sinister_login installed


# ---------- CLI: current -----------------------------------------------------

def test_cli_current_when_unset(runner):
    res = runner.invoke(cli, ["current"])
    assert res.exit_code == 2
    assert "no model set" in res.output


def test_cli_current_json_when_unset(runner):
    res = runner.invoke(cli, ["current", "--json"])
    assert res.exit_code == 2
    data = json.loads(res.output)
    assert data["ok"] is False


def test_cli_current_after_set(runner):
    set_current("claude-sonnet-4-6", provider="anthropic")
    res = runner.invoke(cli, ["current"])
    assert res.exit_code == 0
    assert "claude-sonnet-4-6" in res.output
    assert "anthropic" in res.output


def test_cli_current_json_after_set(runner):
    set_current("gpt-4o", provider="openai")
    res = runner.invoke(cli, ["current", "--json"])
    assert res.exit_code == 0
    data = json.loads(res.output)
    assert data["ok"] is True
    assert data["model_id"] == "gpt-4o"
    assert data["known"] is True
    assert data["details"]["model_id"] == "gpt-4o"


# ---------- CLI: set ---------------------------------------------------------

def test_cli_set_known_model(runner):
    res = runner.invoke(cli, ["set", "claude-opus-4-7[1m]"])
    assert res.exit_code == 0
    state = get_current()
    assert state["model_id"] == "claude-opus-4-7[1m]"
    assert state["provider"] == "anthropic"


def test_cli_set_unknown_refused_without_force(runner):
    res = runner.invoke(cli, ["set", "nonsense-model"])
    assert res.exit_code == 2
    assert "unknown" in res.output.lower()


def test_cli_set_unknown_force_allowed(runner):
    res = runner.invoke(cli, ["set", "custom-foo", "--force"])
    assert res.exit_code == 0
    assert get_current()["model_id"] == "custom-foo"


def test_cli_set_json(runner):
    res = runner.invoke(cli, ["set", "gpt-5-mini", "--json"])
    assert res.exit_code == 0
    data = json.loads(res.output)
    assert data["ok"] is True
    assert data["model_id"] == "gpt-5-mini"
    assert data["provider"] == "openai"


# ---------- CLI: info --------------------------------------------------------

def test_cli_info_known(runner):
    res = runner.invoke(cli, ["info", "gemini-1.5-pro"])
    assert res.exit_code == 0
    assert "Gemini 1.5 Pro" in res.output
    assert "2,000,000" in res.output  # 2M context formatted


def test_cli_info_unknown(runner):
    res = runner.invoke(cli, ["info", "nonsense"])
    assert res.exit_code == 2


def test_cli_info_json(runner):
    res = runner.invoke(cli, ["info", "deepseek-reasoner", "--json"])
    assert res.exit_code == 0
    data = json.loads(res.output)
    assert data["ok"] is True
    assert data["model_id"] == "deepseek-reasoner"
    assert data["provider"] == "deepseek"
    assert "reasoning" in data["capabilities"]


# ---------- CLI: clear -------------------------------------------------------

def test_cli_clear_then_current_unset(runner):
    set_current("gpt-4o", provider="openai")
    res = runner.invoke(cli, ["clear"])
    assert res.exit_code == 0
    assert get_current() is None


def test_cli_clear_json(runner):
    set_current("o1", provider="openai")
    res = runner.invoke(cli, ["clear", "--json"])
    assert res.exit_code == 0
    data = json.loads(res.output)
    assert data["ok"] is True
    assert data["removed"] is True


# ---------- main(argv) entry point ------------------------------------------

def test_main_returns_zero_on_providers():
    rc = main(["providers", "--json"])
    assert rc == 0


def test_main_returns_two_on_unknown_provider():
    rc = main(["list", "nonsense", "--json"])
    assert rc == 2


def test_main_help_returns_zero():
    rc = main(["--help"])
    assert rc == 0


def test_main_version_returns_zero():
    rc = main(["--version"])
    assert rc == 0
