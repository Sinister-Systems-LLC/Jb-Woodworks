"""Sinister Forge :: regression suite locking in P0-A/B/C fixes.

Author: RKOJ-ELENO :: 2026-05-21

Three Textual 8.x quiet-failure-mode bugs shipped this session:
  - P0-A: ``def _render(self) -> None`` in Widget subclass silently shadowed
    framework ``Widget._render`` -> first paint returned None Visual ->
    AttributeError -> Textual error handler swallowed it -> wrapper bat saw
    exit 0 with no visible UI.
  - P0-B: ``push_screen_wait`` raises ``NoActiveWorker`` unless the caller
    runs inside a ``@work`` worker. Ctrl+W crashed at runtime.
  - P0-C: ``PickerResult`` was missing ``project_display``; ``@work`` defaults
    to ``exit_on_error=True`` so the AttributeError killed the app on Submit.

Run with plain pytest (no pytest-asyncio dep) — each async case wraps
``asyncio.run`` itself so the suite stays portable.
"""

from __future__ import annotations

import asyncio
from dataclasses import fields


def _run(coro):
    """Helper: synchronously run an async test body via asyncio.run."""
    return asyncio.run(coro)


# ---------- pure unit checks (no Textual app) ----------


def test_picker_result_has_project_display_field():
    """P0-C directly: PickerResult dataclass must have project_display."""
    from forge.panes.picker import PickerResult
    field_names = {f.name for f in fields(PickerResult)}
    assert "project_display" in field_names, (
        "PickerResult.project_display missing - regression of P0-C. "
        "app.py:action_new_agent reads result.project_display."
    )
    assert "project_key" in field_names


def test_chrome_widgets_render_non_none():
    """P0-A directly: each chrome widget's _render() must return non-None Content."""
    from forge.panes.chrome import ChromeBar, ProjectChip, StatusFooter
    from forge.panes.status_bar import StatusBar
    for cls in (ChromeBar, ProjectChip, StatusFooter, StatusBar):
        w = cls()
        rendered = w._render()
        assert rendered is not None, (
            f"{cls.__name__}._render() returned None - shadowing regression. "
            f"Check the class doesn't define `def _render(self)` itself; "
            f"helper methods must be named `_refresh_view` or similar."
        )


def test_build_subprocess_dispatches_by_host():
    """F2 wire-up: _build_subprocess picks Claude vs Codex based on host."""
    from forge.app import _build_subprocess
    from forge.panes.picker import PickerResult
    from forge.spawn.claude import ClaudeSubprocess
    from forge.spawn.codex import CodexSubprocess

    common = dict(
        project_key="sanctum",
        project_display="Sanctum",
        objective="resume",
        token_mode="compact",
        speed="turbo",
        agent_name="t",
        accent="purple",
        focus="",
    )
    c = _build_subprocess(PickerResult(host="claude", **common))
    assert isinstance(c, ClaudeSubprocess)
    co = _build_subprocess(PickerResult(host="codex", **common))
    assert isinstance(co, CodexSubprocess)
    # Unknown project key -> None (pane mounts empty + notify warning)
    none = _build_subprocess(PickerResult(
        project_key="nope-no-such", project_display="Nope",
        objective="resume", token_mode="compact", speed="turbo",
        host="claude", agent_name="t", accent="purple", focus="",
    ))
    assert none is None


# ---------- Textual pilot integration ----------


def test_boot_does_not_crash():
    """P0-A: chrome.py + status_bar.py widgets must render without _render shadowing."""
    from forge.app import ForgeApp

    async def body():
        app = ForgeApp()
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause(2.0)
            assert app.return_code is None, "App exited during boot - regression"
    _run(body())


def test_ctrl_w_opens_picker():
    """P0-B: action_new_agent must run inside a @work worker for push_screen_wait."""
    from forge.app import ForgeApp

    async def body():
        app = ForgeApp()
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause(1.5)
            await pilot.press("ctrl+w")
            await pilot.pause(0.5)
            names = [type(s).__name__ for s in app.screen_stack]
            assert "AgentPicker" in names, f"Picker did not push: {names}"
            assert app.return_code is None, "App died on Ctrl+W"
    _run(body())


def test_picker_escape_cancels():
    """Escape inside picker must dismiss without crashing."""
    from forge.app import ForgeApp

    async def body():
        app = ForgeApp()
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause(1.5)
            await pilot.press("ctrl+w")
            await pilot.pause(0.4)
            await pilot.press("escape")
            await pilot.pause(0.4)
            names = [type(s).__name__ for s in app.screen_stack]
            assert "AgentPicker" not in names, "Picker did not dismiss"
            assert app.return_code is None
    _run(body())


def test_picker_submit_mounts_pane():
    """P0-C: Submit must mount a pane without killing the app."""
    from forge.app import ForgeApp

    async def body():
        app = ForgeApp()
        async with app.run_test(size=(200, 60)) as pilot:
            await pilot.pause(1.5)
            await pilot.press("ctrl+w")
            await pilot.pause(0.4)
            picker = app.screen
            result = picker._collect()
            assert hasattr(result, "project_display"), \
                "PickerResult missing project_display - regression of P0-C"
            assert result.project_display, "project_display empty - lookup failed"
            picker.dismiss(result)
            await pilot.pause(2.0)
            assert app.return_code is None, \
                f"App exited on Submit (return_code={app.return_code}) - regression of P0-C"
            assert len(app._tabs.panes) == 1, \
                f"Pane not mounted: count={len(app._tabs.panes)}"
            pane = app._tabs.panes[0]
            assert pane.project_display == result.project_display
            assert pane.agent_name == result.agent_name
    _run(body())


def test_command_palette_open_close():
    """Ctrl+P opens command palette (also @work-wrapped per P0-B), escape closes."""
    from forge.app import ForgeApp

    async def body():
        app = ForgeApp()
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause(1.5)
            await pilot.press("ctrl+p")
            await pilot.pause(0.4)
            names = [type(s).__name__ for s in app.screen_stack]
            assert "CommandPalette" in names, f"Palette did not open: {names}"
            await pilot.press("escape")
            await pilot.pause(0.4)
            names = [type(s).__name__ for s in app.screen_stack]
            assert "CommandPalette" not in names
            assert app.return_code is None
    _run(body())
