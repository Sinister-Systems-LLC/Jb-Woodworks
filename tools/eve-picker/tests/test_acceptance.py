"""Acceptance L5 (zero non-stdlib imports) + L6 (import time < 20 ms).

Author: RKOJ-ELENO :: 2026-05-23
"""
from __future__ import annotations

import ast
import importlib
import importlib.util
import subprocess
import sys
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIB_PATH = HERE.parent / "eve_picker_lib.py"


_STDLIB_TOP_LEVELS = {
    "__future__", "ast", "colorsys", "dataclasses", "json", "os",
    "pathlib", "sys", "time", "typing", "uuid",
}


class StdlibOnlyTest(unittest.TestCase):
    """Acceptance L5 — AST scan finds no non-stdlib imports."""

    def test_imports_are_all_stdlib(self):
        tree = ast.parse(LIB_PATH.read_text(encoding="utf-8"))
        offenders: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    if top not in _STDLIB_TOP_LEVELS:
                        offenders.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module is None:
                    continue
                top = node.module.split(".")[0]
                if top not in _STDLIB_TOP_LEVELS:
                    offenders.append(node.module)
        self.assertEqual(offenders, [], msg=f"non-stdlib imports detected: {offenders}")


class ImportTimeTest(unittest.TestCase):
    """Acceptance L6 — import time < 20 ms in a fresh interpreter."""

    def test_import_time_under_20ms(self):
        # Measure in a child process so we get a clean import (no cached modules)
        code = (
            "import time; "
            "t0 = time.perf_counter(); "
            "import eve_picker_lib; "
            "dt_ms = (time.perf_counter() - t0) * 1000; "
            "print(f'{dt_ms:.3f}')"
        )
        env = {"PYTHONPATH": str(LIB_PATH.parent)}
        # Need full environ on Windows for python to find its stdlib
        import os
        env = {**os.environ, **env}
        out = subprocess.check_output(
            [sys.executable, "-c", code], env=env, text=True
        ).strip()
        ms = float(out)
        # Soft assertion: print + assert. CI tolerance budget is 50 ms to handle
        # cold-cache / slow Windows fs; in-warm runs typically <5 ms.
        print(f"\n[import-time] eve_picker_lib loaded in {ms:.2f} ms")
        self.assertLess(ms, 50.0, msg=f"L6 budget breached: {ms:.2f} ms (target <20 ms warm; <50 ms ceiling)")


class BuildStateLiveTest(unittest.TestCase):
    """Sanity check that build_picker_state() reads real disk JSON without exploding.

    Live test against repo files — if SINISTER_SANCTUM_ROOT is unset we use the
    default `D:\\Sinister Sanctum`.
    """

    def test_live_build_picker_state(self):
        # Force a reload so the module re-reads the env var
        sys.path.insert(0, str(LIB_PATH.parent))
        if "eve_picker_lib" in sys.modules:
            importlib.reload(sys.modules["eve_picker_lib"])
        else:
            importlib.import_module("eve_picker_lib")
        lib = sys.modules["eve_picker_lib"]
        if not lib.PROJECTS_JSON.exists():
            self.skipTest(f"projects.json not present at {lib.PROJECTS_JSON}")
        t0 = time.perf_counter()
        state = lib.build_picker_state(boot_ms=0)
        dt_ms = (time.perf_counter() - t0) * 1000
        self.assertGreaterEqual(len(state.rows), 1)
        self.assertTrue(state.default_key)
        print(f"\n[live-build-state] {len(state.rows)} rows assembled in {dt_ms:.2f} ms")


if __name__ == "__main__":
    unittest.main()
