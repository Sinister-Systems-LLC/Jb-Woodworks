"""Acceptance L2 + multi-select edge cases.

Author: RKOJ-ELENO :: 2026-05-23
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import eve_picker_lib as lib


class ParseMultiTests(unittest.TestCase):

    def test_L2_canonical(self):
        # Plan Section 4.4 L2
        self.assertEqual(lib.parse_multi("1,3-5,7", 14), [1, 3, 4, 5, 7])

    def test_single_token_returns_empty(self):
        # Single index is not "multi" — caller handles via resolve_pick numeric branch
        self.assertEqual(lib.parse_multi("3", 10), [])

    def test_simple_comma_list(self):
        self.assertEqual(lib.parse_multi("1,3,5", 10), [1, 3, 5])

    def test_range(self):
        self.assertEqual(lib.parse_multi("1-3", 10), [1, 2, 3])

    def test_reversed_range_normalizes(self):
        self.assertEqual(lib.parse_multi("5-2", 10), [2, 3, 4, 5])

    def test_dedupes(self):
        self.assertEqual(lib.parse_multi("1,2,2,3-3,1", 10), [1, 2, 3])

    def test_clamps_to_max_n(self):
        self.assertEqual(lib.parse_multi("8-12", 10), [8, 9, 10])

    def test_drops_out_of_range_low(self):
        self.assertEqual(lib.parse_multi("0,1,2", 10), [1, 2])

    def test_empty_string(self):
        self.assertEqual(lib.parse_multi("", 10), [])

    def test_malformed_returns_empty(self):
        self.assertEqual(lib.parse_multi("abc,def", 10), [])

    def test_malformed_range_returns_empty(self):
        self.assertEqual(lib.parse_multi("1-x", 10), [])

    def test_whitespace_tolerant(self):
        self.assertEqual(lib.parse_multi(" 1 , 3 - 5 , 7 ", 14), [1, 3, 4, 5, 7])


if __name__ == "__main__":
    unittest.main()
