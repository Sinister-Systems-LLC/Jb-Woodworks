# Author: RKOJ-ELENO :: 2026-05-23
# License: AGPL-3.0-or-later

"""Unit tests for sinister_utils.io defensive I/O helpers."""

from __future__ import annotations

import json
import logging
import os
import tempfile
import unittest
from pathlib import Path

from sinister_utils.io import (
    load_json_tolerant,
    load_text_tolerant,
    write_json_no_bom,
    write_text_no_bom,
)


BOM = b"\xef\xbb\xbf"


class TestLoadJsonTolerant(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="sinister_utils_test_")

    def tearDown(self):
        for f in Path(self.tmp).iterdir():
            f.unlink()
        os.rmdir(self.tmp)

    def _write(self, name: str, content: bytes) -> Path:
        p = Path(self.tmp) / name
        p.write_bytes(content)
        return p

    def test_loads_clean_utf8_json(self):
        p = self._write("clean.json", b'{"a": 1, "b": "two"}')
        self.assertEqual(load_json_tolerant(p), {"a": 1, "b": "two"})

    def test_loads_bom_prefixed_json(self):
        p = self._write("bom.json", BOM + b'{"a": 1}')
        self.assertEqual(load_json_tolerant(p), {"a": 1})

    def test_missing_file_returns_default(self):
        with self.assertLogs("sinister_utils.io", level="WARNING") as cm:
            result = load_json_tolerant(Path(self.tmp) / "missing.json", default={"x": 0})
        self.assertEqual(result, {"x": 0})
        self.assertTrue(any("file not found" in m for m in cm.output))

    def test_missing_file_returns_none_by_default(self):
        result = load_json_tolerant(Path(self.tmp) / "missing.json")
        self.assertIsNone(result)

    def test_bad_json_returns_default(self):
        p = self._write("bad.json", b'{"a": this is not valid json')
        with self.assertLogs("sinister_utils.io", level="WARNING") as cm:
            result = load_json_tolerant(p, default=[])
        self.assertEqual(result, [])
        self.assertTrue(any("JSONDecodeError" in m for m in cm.output))

    def test_empty_file_returns_default(self):
        p = self._write("empty.json", b"")
        result = load_json_tolerant(p, default={"empty": True})
        self.assertEqual(result, {"empty": True})

    def test_bom_only_file_returns_default(self):
        p = self._write("just_bom.json", BOM)
        result = load_json_tolerant(p, default="fallback")
        self.assertEqual(result, "fallback")


class TestLoadTextTolerant(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="sinister_utils_test_")

    def tearDown(self):
        for f in Path(self.tmp).iterdir():
            f.unlink()
        os.rmdir(self.tmp)

    def test_loads_clean_text(self):
        p = Path(self.tmp) / "clean.txt"
        p.write_bytes(b"hello world\n")
        self.assertEqual(load_text_tolerant(p), "hello world\n")

    def test_strips_bom(self):
        p = Path(self.tmp) / "bom.txt"
        p.write_bytes(BOM + b"hello")
        result = load_text_tolerant(p)
        self.assertEqual(result, "hello")
        self.assertFalse(result.startswith("﻿"))

    def test_missing_returns_empty_string_default(self):
        result = load_text_tolerant(Path(self.tmp) / "nope.txt")
        self.assertEqual(result, "")

    def test_missing_returns_custom_default(self):
        result = load_text_tolerant(Path(self.tmp) / "nope.txt", default="fallback")
        self.assertEqual(result, "fallback")


class TestWriteJsonNoBom(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="sinister_utils_test_")

    def tearDown(self):
        for f in Path(self.tmp).iterdir():
            f.unlink()
        os.rmdir(self.tmp)

    def test_writes_clean_utf8_no_bom(self):
        p = Path(self.tmp) / "out.json"
        write_json_no_bom(p, {"a": 1, "b": "two"})
        raw = p.read_bytes()
        self.assertFalse(raw.startswith(BOM), f"BOM leaked into output: {raw[:8]!r}")
        self.assertEqual(json.loads(raw.decode("utf-8")), {"a": 1, "b": "two"})

    def test_unicode_no_escape(self):
        p = Path(self.tmp) / "u.json"
        write_json_no_bom(p, {"name": "Sinister 🔮"})
        raw = p.read_bytes()
        self.assertFalse(raw.startswith(BOM))
        self.assertIn("🔮".encode("utf-8"), raw)

    def test_atomic_replace(self):
        # First write
        p = Path(self.tmp) / "atom.json"
        write_json_no_bom(p, {"v": 1})
        first = p.read_bytes()
        # Overwrite atomically — no temp file left behind
        write_json_no_bom(p, {"v": 2})
        second = p.read_bytes()
        self.assertNotEqual(first, second)
        # No leftover .tmp files
        leftover = list(p.parent.glob("*.tmp"))
        self.assertEqual(leftover, [])

    def test_indent_none(self):
        p = Path(self.tmp) / "compact.json"
        write_json_no_bom(p, {"a": 1, "b": 2}, indent=None)
        raw = p.read_bytes().decode("utf-8")
        self.assertNotIn("\n  ", raw)

    def test_sort_keys(self):
        p = Path(self.tmp) / "sorted.json"
        write_json_no_bom(p, {"z": 1, "a": 2}, sort_keys=True)
        raw = p.read_bytes().decode("utf-8")
        self.assertLess(raw.index('"a"'), raw.index('"z"'))


class TestWriteTextNoBom(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="sinister_utils_test_")

    def tearDown(self):
        for f in Path(self.tmp).iterdir():
            f.unlink()
        os.rmdir(self.tmp)

    def test_writes_clean_text_no_bom(self):
        p = Path(self.tmp) / "out.txt"
        write_text_no_bom(p, "hello world\n")
        raw = p.read_bytes()
        self.assertFalse(raw.startswith(BOM))
        self.assertEqual(raw, b"hello world\n")

    def test_rejects_input_with_existing_bom(self):
        p = Path(self.tmp) / "out.txt"
        with self.assertRaises(AssertionError):
            write_text_no_bom(p, "﻿hello")


class TestRoundTrip(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="sinister_utils_test_")

    def tearDown(self):
        for f in Path(self.tmp).iterdir():
            f.unlink()
        os.rmdir(self.tmp)

    def test_json_round_trip(self):
        p = Path(self.tmp) / "rt.json"
        original = {"projects": [{"key": "rkoj", "display": "RKOJ"}], "n": 17}
        write_json_no_bom(p, original)
        loaded = load_json_tolerant(p)
        self.assertEqual(loaded, original)

    def test_bom_corruption_recovery(self):
        # Simulate PS Out-File having written a BOM-prefixed file —
        # our reader still recovers correctly.
        p = Path(self.tmp) / "rt.json"
        original = {"v": 42}
        p.write_bytes(BOM + json.dumps(original).encode("utf-8"))
        # Sanity: a naive utf-8 reader would fail
        with self.assertRaises(json.JSONDecodeError):
            with open(p, "r", encoding="utf-8") as fh:
                json.load(fh)
        # But load_json_tolerant handles it
        self.assertEqual(load_json_tolerant(p), original)


if __name__ == "__main__":
    unittest.main()
