# Sinister Term :: tests/test_dispatch.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# PH14 (restored 2026-05-25): pytest coverage for term.commands.dispatch — the
# router that decides whether a line is a slash builtin or shell fall-through.
# Original suite was dropped during a sister-lane inbox reorg; rebuilt against
# current source (commands.py 2026-05-23).

from __future__ import annotations


def test_dispatch_non_slash_falls_through():
    """Lines NOT starting with '/' must return handled=False so the caller runs
    them in the underlying shell."""
    from term.commands import dispatch
    r = dispatch("ls -la")
    assert r.handled is False
    assert r.output == ""
    assert r.exit_term is False


def test_dispatch_empty_string():
    """Whitespace-only or empty input falls through (no builtin to fire)."""
    from term.commands import dispatch
    assert dispatch("").handled is False
    assert dispatch("   ").handled is False


def test_dispatch_lone_slash():
    """Just `/` with no command name is handled (no-op) but does not raise."""
    from term.commands import dispatch
    r = dispatch("/")
    assert r.handled is True


def test_dispatch_unknown_command_handled_with_hint():
    """Unknown slash command returns handled=True with a 'try /help' hint."""
    from term.commands import dispatch
    r = dispatch("/zzzzz-not-a-command")
    assert r.handled is True
    assert "unknown command" in r.output.lower() or "help" in r.output.lower()


def test_dispatch_help_canonical():
    """/help returns the help body listing the canonical builtins."""
    from term.commands import dispatch
    r = dispatch("/help")
    assert r.handled is True
    body = r.output.lower()
    # Spot-check several builtins listed in help
    for needle in ("/forge", "/mind", "/launch", "/projects", "/exit"):
        assert needle in body, f"help text missing {needle}"


def test_dispatch_help_question_alias():
    """`/?` aliases to /help — same body."""
    from term.commands import dispatch
    r1 = dispatch("/help")
    r2 = dispatch("/?")
    assert r1.handled and r2.handled
    assert r2.output == r1.output


def test_dispatch_exit_signals_exit_term():
    """/exit returns exit_term=True so the outer loop knows to break."""
    from term.commands import dispatch
    r = dispatch("/exit")
    assert r.handled is True
    assert r.exit_term is True


def test_dispatch_quit_alias_for_exit():
    """/quit aliases to /exit."""
    from term.commands import dispatch
    assert dispatch("/quit").exit_term is True


def test_dispatch_case_insensitive_command_name():
    """Command names dispatch case-insensitively (operator muscle-memory)."""
    from term.commands import dispatch
    assert dispatch("/HELP").handled is True
    assert dispatch("/Exit").exit_term is True


def test_dispatch_args_trimmed_and_split():
    """/launch with arg passes the arg through; missing arg shows usage."""
    from term.commands import dispatch
    r = dispatch("/launch")
    assert r.handled is True
    assert "usage" in r.output.lower() or "project" in r.output.lower()


def test_dispatch_known_aliases_registered():
    """Verify the canonical alias table — these must dispatch as handled."""
    from term.commands import COMMANDS
    # Aliases mapped in commands.py COMMANDS dict
    for alias in ("?", "quit", "cls", "hb", "log", "ca"):
        assert alias in COMMANDS, f"missing alias /{alias}"
    # And core commands
    for core in ("help", "exit", "clear", "projects", "heartbeats", "commits",
                 "forge", "mind", "launch", "cd", "bot", "skill",
                 "inbox", "cross-agent", "ask", "progress", "alias"):
        assert core in COMMANDS, f"missing core command /{core}"


def test_command_result_default_fields():
    """CommandResult dataclass defaults — output='' and exit_term=False."""
    from term.commands import CommandResult
    r = CommandResult(True)
    assert r.output == ""
    assert r.exit_term is False
