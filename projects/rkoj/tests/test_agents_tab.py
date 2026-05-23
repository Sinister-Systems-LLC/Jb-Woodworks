# Author: RKOJ-ELENO :: 2026-05-22
"""Programmatic tests for sinister_rkoj_qt.agents_tab.

Runs without a Qt event loop — exercises pure-Python invariants
(dataclass fields, SLASH_COMMANDS uniqueness, signal declarations,
_fmt_duration formatting, _tag_colors stability, _SUMMARIZE_PROMPT
non-empty, valid sort keys for /fleet).

Run from repo root:
    PYTHONPATH=projects/rkoj/source python -m pytest projects/rkoj/tests/
    or just:
    python -m unittest projects.rkoj.tests.test_agents_tab
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Hoist project source onto sys.path so the test can `import sinister_rkoj_qt`
# without an editable install.
_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "source"
sys.path.insert(0, str(_SRC))

# QtWidgets needs a QApplication to import anything that touches signals
# at class-construction time — set up a headless instance lazily.
from PyQt6.QtWidgets import QApplication  # noqa: E402
_APP = QApplication.instance() or QApplication(sys.argv[:1])

import sinister_rkoj_qt  # noqa: E402
from sinister_rkoj_qt import agents_tab  # noqa: E402


class TestSlashCommands(unittest.TestCase):
    def test_registry_is_unique(self) -> None:
        names = [c for c, _ in agents_tab.SLASH_COMMANDS]
        self.assertEqual(len(names), len(set(names)), "duplicate slash command names")

    def test_registry_minimum_count(self) -> None:
        # v1.6.68 ships >=55 (was 52 at v1.6.67; +8 new minus possible drift).
        self.assertGreaterEqual(len(agents_tab.SLASH_COMMANDS), 55)

    def test_all_start_with_slash(self) -> None:
        for cmd, _ in agents_tab.SLASH_COMMANDS:
            self.assertTrue(cmd.startswith("/"), f"missing leading slash: {cmd}")

    def test_descriptions_non_empty(self) -> None:
        for cmd, desc in agents_tab.SLASH_COMMANDS:
            self.assertTrue(desc.strip(), f"empty description for {cmd}")


class TestFmtDuration(unittest.TestCase):
    fmt = staticmethod(agents_tab.AgentCard._fmt_duration)

    def test_none_returns_dashes(self) -> None:
        self.assertEqual(self.fmt(None), "--")

    def test_negative_returns_dashes(self) -> None:
        self.assertEqual(self.fmt(-1), "--")

    def test_seconds_under_minute(self) -> None:
        self.assertEqual(self.fmt(0.0), "0.0s")
        self.assertEqual(self.fmt(12.3), "12.3s")
        self.assertEqual(self.fmt(59.9), "59.9s")

    def test_minutes_under_hour(self) -> None:
        self.assertEqual(self.fmt(60), "1m 0s")
        self.assertEqual(self.fmt(75), "1m 15s")
        self.assertEqual(self.fmt(3599), "59m 59s")

    def test_hours(self) -> None:
        self.assertEqual(self.fmt(3600), "1h 0m")
        self.assertEqual(self.fmt(3700), "1h 1m")
        self.assertEqual(self.fmt(7320), "2h 2m")


class TestTagColors(unittest.TestCase):
    def test_reserved_colors_stable(self) -> None:
        for tag in ("blocked", "wip", "todo", "done", "shipped", "review"):
            self.assertIn(tag, agents_tab._TAG_RESERVED)

    def test_reserved_blocked_is_red(self) -> None:
        fg, _, _ = agents_tab._tag_colors("blocked")
        self.assertEqual(fg, "#FF453A")

    def test_reserved_wip_is_yellow(self) -> None:
        fg, _, _ = agents_tab._tag_colors("wip")
        self.assertEqual(fg, "#FFD60A")

    def test_reserved_done_is_green(self) -> None:
        fg, _, _ = agents_tab._tag_colors("done")
        self.assertEqual(fg, "#30D158")

    def test_arbitrary_tag_stable(self) -> None:
        # Same string → same color across calls (no Python-hash salt).
        a = agents_tag = agents_tab._tag_colors("xyzzy")
        b = agents_tab._tag_colors("xyzzy")
        self.assertEqual(a, b)

    def test_palette_indexable(self) -> None:
        # Hash-derived; must return a 3-tuple of strings.
        fg, bg, border = agents_tab._tag_colors("anything")
        self.assertTrue(fg.startswith("#"))
        self.assertTrue(bg.startswith("rgba("))
        self.assertTrue(border.startswith("rgba("))


class TestAgentSession(unittest.TestCase):
    def test_dataclass_has_required_fields(self) -> None:
        fields = agents_tab.AgentSession.__dataclass_fields__
        for required in (
            "pane_id", "project_key", "project_display", "agent_name",
            "mode", "status", "turns", "pinned",
            "tags",         # v1.6.45
            "input_draft",  # v1.6.59
        ):
            self.assertIn(required, fields, f"missing AgentSession.{required}")

    def test_tags_defaults_to_list(self) -> None:
        s = agents_tab.AgentSession(
            pane_id="x", project_key="p", project_display="P",
            agent_name="a",
        )
        self.assertEqual(s.tags, [])
        self.assertEqual(s.input_draft, "")
        self.assertEqual(s.turns, [])
        self.assertFalse(s.pinned)


class TestSignals(unittest.TestCase):
    """Sanity-check that every fleet-fan signal exists on AgentCard.
    Doesn't instantiate (Qt event loop overhead) — just inspects class."""

    def test_signals_exist(self) -> None:
        for name in (
            "closed", "status_changed", "pin_changed",
            "broadcast_requested",
            "minimize_all_requested", "expand_all_requested",
            "clone_requested",         # v1.6.41
            "find_requested",          # v1.6.42
            "tags_census_requested",   # v1.6.51
            "export_all_requested",    # v1.6.55
            "summarize_all_requested", # v1.6.60
            "fleet_table_requested",   # v1.6.66
            "uptime_all_requested",    # v1.6.68
        ):
            self.assertTrue(
                hasattr(agents_tab.AgentCard, name),
                f"AgentCard missing signal: {name}",
            )


class TestSummarizePrompt(unittest.TestCase):
    def test_summarize_prompt_is_substantive(self) -> None:
        self.assertGreaterEqual(len(agents_tab._SUMMARIZE_PROMPT), 80)
        self.assertIn("TL;DR", agents_tab._SUMMARIZE_PROMPT)
        # Validates the 4-section template
        for sec in ("goal:", "working:", "blocked:", "next:"):
            self.assertIn(sec, agents_tab._SUMMARIZE_PROMPT)


class TestSkillFrontmatter(unittest.TestCase):
    parse = staticmethod(agents_tab._parse_skill_frontmatter)

    def test_no_frontmatter_passthrough(self) -> None:
        text = "Just a plain skill body.\nNo dashes here."
        fm, body = self.parse(text)
        self.assertEqual(fm, {})
        self.assertEqual(body, text)

    def test_basic_frontmatter(self) -> None:
        text = (
            "---\n"
            "name: review-pr\n"
            "description: Review a pull request for issues\n"
            "---\n"
            "Body content here."
        )
        fm, body = self.parse(text)
        self.assertEqual(fm["name"], "review-pr")
        self.assertEqual(fm["description"], "Review a pull request for issues")
        self.assertEqual(body, "Body content here.")

    def test_quoted_values_stripped(self) -> None:
        text = '---\nname: "quoted-name"\ndescription: \'single-quoted\'\n---\nbody'
        fm, _ = self.parse(text)
        self.assertEqual(fm["name"], "quoted-name")
        self.assertEqual(fm["description"], "single-quoted")

    def test_allowed_tools_list(self) -> None:
        text = "---\nallowed-tools: Read, Edit, Bash\n---\nbody"
        fm, _ = self.parse(text)
        self.assertEqual(fm["allowed-tools"], ["Read", "Edit", "Bash"])

    def test_missing_closing_returns_passthrough(self) -> None:
        text = "---\nname: never-closed\nbody body body"
        fm, body = self.parse(text)
        self.assertEqual(fm, {})
        self.assertEqual(body, text)


class TestSidebarV172(unittest.TestCase):
    """v1.6.72 — sidebar reduced to Agents + Devices only."""

    def test_sections(self) -> None:
        from sinister_rkoj_qt import sidebar
        self.assertEqual(len(sidebar.SECTIONS), 1)
        sect_label, items = sidebar.SECTIONS[0]
        self.assertEqual(sect_label, "WORKSPACE")
        keys = [k for k, _, _ in items]
        self.assertEqual(keys, ["agents", "devices"])
        self.assertNotIn("sessions", keys)


class TestHeaderV172(unittest.TestCase):
    """v1.6.72 — chip sets are context-aware; HEADER_ACTIONS empty."""

    def test_chip_sets(self) -> None:
        from sinister_rkoj_qt import header
        self.assertIn("agents", header.CHIP_SETS)
        self.assertIn("devices", header.CHIP_SETS)
        agents_keys = [k for k, _ in header.CHIP_SETS["agents"]]
        self.assertEqual(agents_keys, ["agents", "resume"])
        self.assertEqual(header.CHIP_SETS["devices"], [])

    def test_header_actions_empty(self) -> None:
        from sinister_rkoj_qt import header
        # Operator removed the 4 junk icons (alerts/clock/search/settings)
        self.assertEqual(header.HEADER_ACTIONS, [])

    def test_minimize_signal_exists(self) -> None:
        from sinister_rkoj_qt import header
        self.assertTrue(hasattr(header.Header, "minimize_clicked"))
        self.assertTrue(hasattr(header.Header, "close_clicked"))


class TestThemeV172(unittest.TestCase):
    """v1.6.72 — sidebar connected to main (no gap)."""

    def test_outer_gap_is_zero(self) -> None:
        from sinister_rkoj_qt import theme
        self.assertEqual(theme.OUTER_GAP, 0)


class TestDevicesV172(unittest.TestCase):
    """v1.6.72 — Devices viewer has scrcpy / adb action wiring."""

    def test_scrcpy_finder_works(self) -> None:
        from sinister_rkoj_qt import devices_tab
        # On the operator's machine scrcpy is installed via winget
        sc = devices_tab._find_scrcpy()
        self.assertIsNotNone(sc, "scrcpy not found — operator has it via winget")
        from pathlib import Path
        self.assertTrue(Path(sc).exists())

    def test_adb_finder_works(self) -> None:
        from sinister_rkoj_qt import devices_tab
        adb = devices_tab._find_adb()
        self.assertIsNotNone(adb, "adb not found via PATH or scrcpy bundle")

    def test_device_row_has_action_methods(self) -> None:
        from sinister_rkoj_qt import devices_tab
        cls = devices_tab._DeviceRow
        # v1.6.73 — _launch_scrcpy moved into _MirrorCard (embed flow);
        # _DeviceRow now emits mirror_requested signal instead.
        for m in ("_take_screenshot", "_open_shell", "_tail_logcat"):
            self.assertTrue(hasattr(cls, m), f"_DeviceRow missing {m}")
        self.assertTrue(hasattr(cls, "mirror_requested"))
        self.assertTrue(hasattr(cls, "group_toggled"))

    def test_mirror_card_class_exists(self) -> None:
        """v1.6.73 — embedded scrcpy mirror card with reparented HWND."""
        from sinister_rkoj_qt import devices_tab
        cls = devices_tab._MirrorCard
        for m in ("_spawn_scrcpy", "_try_embed", "_on_close",
                  "_take_screenshot", "_open_shell", "_tail_logcat"):
            self.assertTrue(hasattr(cls, m), f"_MirrorCard missing {m}")
        self.assertTrue(hasattr(cls, "closed"))

    def test_devices_view_has_group_features(self) -> None:
        """v1.6.73 — group select + mirror-all/screenshot-selected."""
        from sinister_rkoj_qt import devices_tab
        cls = devices_tab.DevicesView
        for m in ("_embed_mirror", "_on_mirror_closed", "_on_group_toggled",
                  "_mirror_all", "_mirror_selected", "_screenshot_selected"):
            self.assertTrue(hasattr(cls, m), f"DevicesView missing {m}")

    def test_devices_view_has_auto_mirror_v174(self) -> None:
        """v1.6.74 — auto-mirror all phones on first tab build."""
        from sinister_rkoj_qt import devices_tab
        self.assertTrue(hasattr(devices_tab.DevicesView, "_auto_mirror_all"))

    def test_mirror_card_uses_win32_setparent_v174(self) -> None:
        """v1.6.74 — _try_embed must include Win32 SetParent call
        (not QWindow.fromWinId, which previously rendered black)."""
        import inspect
        from sinister_rkoj_qt import devices_tab
        src = inspect.getsource(devices_tab._MirrorCard._try_embed)
        self.assertIn("SetParent", src)
        self.assertIn("WS_CHILD", src)


class TestSinisterStartParityV175(unittest.TestCase):
    """v1.6.75 — spawn flow must match Sinister Start.bat (cwd, pretrust,
    agent-prefs.json model, AGENT_NAME/ACCENT/MODE env vars)."""

    def test_env_has_bat_parity_vars(self) -> None:
        from sinister_rkoj_qt import agents_tab
        sess = agents_tab.AgentSession(
            pane_id="x", project_key="sanctum",
            project_display="Sanctum", agent_name="Test",
            mode="claude-opus", accent="purple",
        )
        env = agents_tab._make_child_env(sess)
        for k in ("SINISTER_AGENT_NAME", "SINISTER_ACCENT_COLOR",
                  "SINISTER_MODE", "SINISTER_AGENT_IDENTITY"):
            self.assertTrue(env.contains(k), f"_make_child_env missing {k}")
        self.assertEqual(env.value("SINISTER_AGENT_NAME"), "Test")
        self.assertEqual(env.value("SINISTER_ACCENT_COLOR"), "purple")
        self.assertEqual(env.value("SINISTER_MODE"), "claude-opus")
        self.assertEqual(env.value("SINISTER_AGENT_IDENTITY"), "EVE")

    def test_helpers_exist(self) -> None:
        from sinister_rkoj_qt import agents_tab
        for fn in ("_project_root", "_pretrust_project",
                   "_agent_prefs_model"):
            self.assertTrue(hasattr(agents_tab, fn),
                            f"agents_tab missing {fn}")

    def test_pretrust_silent_on_missing_config(self) -> None:
        from sinister_rkoj_qt import agents_tab
        # Should not raise even if path doesn't exist
        agents_tab._pretrust_project(r"D:\nonexistent\path")

    def test_prefs_model_returns_none_when_absent(self) -> None:
        from sinister_rkoj_qt import agents_tab
        # Random agent name → no prefs entry → None
        self.assertIsNone(agents_tab._agent_prefs_model(
            "definitely-not-a-real-agent-name-xyzzy"
        ))


class TestTodoV175(unittest.TestCase):
    """v1.6.75 — /todo + /todos + /done jcode-parity task tracking."""

    def test_slash_registry_has_todo_trio(self) -> None:
        from sinister_rkoj_qt import agents_tab
        names = {c for c, _ in agents_tab.SLASH_COMMANDS}
        for slash in ("/todo", "/todos", "/done"):
            self.assertIn(slash, names, f"SLASH_COMMANDS missing {slash}")


class TestPlanModeV176(unittest.TestCase):
    """v1.6.76 — /plan jcode-parity toggle for plan-only mode."""

    def test_slash_registry_has_plan(self) -> None:
        from sinister_rkoj_qt import agents_tab
        names = {c for c, _ in agents_tab.SLASH_COMMANDS}
        self.assertIn("/plan", names)

    def test_devices_view_auto_mirror_retry(self) -> None:
        from sinister_rkoj_qt import devices_tab
        self.assertTrue(hasattr(devices_tab.DevicesView, "_auto_mirror_all_retry"))


class TestApiServerV182(unittest.TestCase):
    """v1.6.82 — workstation API surface tests (don't actually start
    the server, just verify module imports + endpoint surface)."""

    def test_api_server_imports(self) -> None:
        from sinister_rkoj_qt import api_server
        self.assertTrue(hasattr(api_server, "start_api_server"))
        self.assertTrue(hasattr(api_server, "stop_api_server"))
        self.assertTrue(hasattr(api_server, "api_status"))
        self.assertEqual(api_server.API_PORT, 5077)
        self.assertEqual(api_server.API_HOST, "127.0.0.1")

    def test_api_status_when_stopped(self) -> None:
        from sinister_rkoj_qt import api_server
        # If not started, running=False; doesn't crash
        st = api_server.api_status()
        self.assertIn("running", st)
        self.assertIn("url", st)


class TestPhoneClaimsV180(unittest.TestCase):
    """v1.6.80 — per-phone agent claim system (no cross-phone leaks)."""

    def setUp(self) -> None:
        from sinister_rkoj_qt import state
        # Clear any test residue
        try:
            if state.PHONE_CLAIMS_FP.exists():
                state.PHONE_CLAIMS_FP.unlink()
        except Exception:
            pass

    def test_claim_release_cycle(self) -> None:
        from sinister_rkoj_qt import state
        # Free phone → claim grants
        self.assertTrue(state.claim_phone("TEST-SERIAL-001", "agent-a", "AgentA"))
        rec = state.who_owns("TEST-SERIAL-001")
        self.assertIsNotNone(rec)
        self.assertEqual(rec["agent_id"], "agent-a")
        # Second agent can't claim
        self.assertFalse(state.claim_phone("TEST-SERIAL-001", "agent-b"))
        # Same agent re-claiming is idempotent True
        self.assertTrue(state.claim_phone("TEST-SERIAL-001", "agent-a"))
        # Release frees it
        state.release_phone("TEST-SERIAL-001", "agent-a")
        self.assertIsNone(state.who_owns("TEST-SERIAL-001"))
        # Now agent-b can claim
        self.assertTrue(state.claim_phone("TEST-SERIAL-001", "agent-b"))
        state.release_phone("TEST-SERIAL-001")

    def test_all_claims_snapshot(self) -> None:
        from sinister_rkoj_qt import state
        state.claim_phone("A", "ag1")
        state.claim_phone("B", "ag2")
        snap = state.all_claims()
        self.assertIn("A", snap)
        self.assertIn("B", snap)
        state.release_phone("A"); state.release_phone("B")


class TestNoEmojisV174(unittest.TestCase):
    """v1.6.74 — dashboard-skeleton rule: no emojis in UI chrome."""

    BANNED = ["⏱", "💭", "📸", "⌨", "📜", "⚠"]

    def test_no_emojis_in_devices_tab(self) -> None:
        from pathlib import Path
        fp = Path(__file__).resolve().parents[1] / "source" / "sinister_rkoj_qt" / "devices_tab.py"
        txt = fp.read_text(encoding="utf-8")
        for ch in self.BANNED:
            self.assertNotIn(ch, txt, f"devices_tab.py contains banned emoji {ch!r}")

    def test_no_emojis_in_agents_tab(self) -> None:
        from pathlib import Path
        fp = Path(__file__).resolve().parents[1] / "source" / "sinister_rkoj_qt" / "agents_tab.py"
        txt = fp.read_text(encoding="utf-8")
        for ch in self.BANNED:
            self.assertNotIn(ch, txt, f"agents_tab.py contains banned emoji {ch!r}")

    def test_banner_png_present(self) -> None:
        from pathlib import Path
        bp = (Path(__file__).resolve().parents[1]
              / "source" / "assets" / "banner.png")
        self.assertTrue(bp.exists(), f"banner.png missing at {bp}")
        # Sanity: should be > 100 KB (operator's banner is ~2.3 MB)
        self.assertGreater(bp.stat().st_size, 100_000)


class TestTokenBudget(unittest.TestCase):
    def test_threshold_constant_present(self) -> None:
        self.assertTrue(hasattr(agents_tab, "_TOKEN_WARN_THRESHOLD"))
        self.assertGreater(agents_tab._TOKEN_WARN_THRESHOLD, 0)

    def test_threshold_is_realistic(self) -> None:
        # Should be a substantial but not full-context number so operator
        # gets runway before truncation. Bounded 25k..200k.
        self.assertGreaterEqual(agents_tab._TOKEN_WARN_THRESHOLD, 25_000)
        self.assertLessEqual(agents_tab._TOKEN_WARN_THRESHOLD, 200_000)


class TestModuleSurface(unittest.TestCase):
    def test_version_matches(self) -> None:
        self.assertEqual(sinister_rkoj_qt.__version__, "1.6.82")

    def test_classes_present(self) -> None:
        for name in (
            "AgentCard", "AgentSession", "AgentsView",
            "_TagChip", "_ClickPill", "_MultiLineInput", "_SlashPopup",
            "NiriScrollGrid",
        ):
            self.assertTrue(
                hasattr(agents_tab, name),
                f"agents_tab missing class: {name}",
            )

    def test_summarize_constant_present(self) -> None:
        self.assertIsInstance(agents_tab._SUMMARIZE_PROMPT, str)


if __name__ == "__main__":
    unittest.main(verbosity=2)
