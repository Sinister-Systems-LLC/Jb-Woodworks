"""Acceptance L1 / L3 / L4 + resolve_pick behavior.

Author: RKOJ-ELENO :: 2026-05-23
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import eve_picker_lib as lib  # noqa: E402

FIXTURE_PROJECTS = HERE / "fixtures" / "projects.json"
FIXTURE_PREFS = HERE / "fixtures" / "agent-prefs.json"


def _state_from_fixtures(boot_ms: int = 0) -> lib.PickerState:
    pj = json.loads(FIXTURE_PROJECTS.read_text(encoding="utf-8-sig"))
    pf = json.loads(FIXTURE_PREFS.read_text(encoding="utf-8-sig"))
    return lib.build_picker_state(boot_ms=boot_ms, projects_json=pj, prefs=pf)


class BuildStateTests(unittest.TestCase):

    def test_L1_visible_only(self):
        s = _state_from_fixtures()
        self.assertEqual([r.key for r in s.rows], ["sanctum", "rkoj", "jb-woodworks"])

    def test_default_marked(self):
        s = _state_from_fixtures()
        sanctum = next(r for r in s.rows if r.key == "sanctum")
        self.assertTrue(sanctum.is_default)
        self.assertFalse(next(r for r in s.rows if r.key == "rkoj").is_default)

    def test_customized_flag_from_prefs(self):
        s = _state_from_fixtures()
        rkoj = next(r for r in s.rows if r.key == "rkoj")
        # accent_color="cyan" + agent_name="rkoj" -> customized via accent
        self.assertTrue(rkoj.customized)
        self.assertEqual(rkoj.accent, "cyan")

    def test_project_color_curated(self):
        s = _state_from_fixtures()
        sanctum = next(r for r in s.rows if r.key == "sanctum")
        self.assertEqual(sanctum.project_color, "#BF5AF2")

    def test_project_color_fallback_stable(self):
        # Unknown key falls into HSV-from-hash branch; same key returns same color
        c1 = lib.project_color("xyz-never-defined")
        c2 = lib.project_color("xyz-never-defined")
        self.assertEqual(c1, c2)
        self.assertTrue(c1.startswith("#") and len(c1) == 7)


class ResolvePickTests(unittest.TestCase):

    def setUp(self):
        self.state = _state_from_fixtures()

    def test_L3_numeric_one(self):
        # Plan Section 4.4 L3
        r = lib.resolve_pick("1", self.state)
        self.assertEqual(r.verb, "numeric")
        self.assertEqual(r.keys, ["sanctum"])

    def test_L4_Q(self):
        # Plan Section 4.4 L4
        self.assertEqual(lib.resolve_pick("Q", self.state).verb, "quit")

    def test_default_on_empty(self):
        r = lib.resolve_pick("", self.state)
        self.assertEqual(r.verb, "default")
        self.assertEqual(r.keys, ["sanctum"])

    def test_general(self):
        r = lib.resolve_pick("G", self.state)
        self.assertEqual(r.verb, "general")
        self.assertEqual(r.keys, ["general"])

    def test_auto_resume(self):
        self.assertEqual(lib.resolve_pick("a", self.state).verb, "auto-resume")

    def test_new(self):
        self.assertEqual(lib.resolve_pick("N", self.state).verb, "new")

    def test_rename(self):
        self.assertEqual(lib.resolve_pick("r", self.state).verb, "rename")

    def test_clear(self):
        self.assertEqual(lib.resolve_pick("K", self.state).verb, "clear")

    def test_autonomy(self):
        self.assertEqual(lib.resolve_pick("S", self.state).verb, "autonomy")
        self.assertEqual(lib.resolve_pick("autonomy", self.state).verb, "autonomy")

    def test_full(self):
        self.assertEqual(lib.resolve_pick("f", self.state).verb, "full")

    def test_quit_aliases(self):
        for raw in ("q", "Q", "quit", "exit"):
            self.assertEqual(lib.resolve_pick(raw, self.state).verb, "quit", msg=raw)

    def test_multi(self):
        r = lib.resolve_pick("1,3", self.state)
        self.assertEqual(r.verb, "multi")
        self.assertEqual(r.keys, ["sanctum", "jb-woodworks"])

    def test_unknown(self):
        self.assertEqual(lib.resolve_pick("zzz", self.state).verb, "unknown")

    def test_out_of_range_numeric_is_unknown(self):
        self.assertEqual(lib.resolve_pick("99", self.state).verb, "unknown")


if __name__ == "__main__":
    unittest.main()
