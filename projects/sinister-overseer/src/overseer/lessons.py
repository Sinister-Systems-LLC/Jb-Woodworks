# Author: RKOJ-ELENO :: 2026-05-24
"""Fails-to-learn store -- SQLite at lessons.db (gitignored).

P0 SCAFFOLD. P3 ships the schema migration + UPSERT logic.

See docs/05-fails-to-learn.md for the full schema + semantics.
"""

from __future__ import annotations

import hashlib
import json


def compute_symptom_hash(features: dict) -> str:
    """Stable 16-char hash of normalized symptom features.

    Real impl identical at P3+; helper available at P0 so adapters can
    pre-bucket their evidence features even before lessons.db exists.
    """
    canonical = json.dumps(features, sort_keys=True).encode("utf-8")
    return hashlib.sha1(canonical).hexdigest()[:16]


def upsert_lesson(row: dict, project_key: str) -> int:
    """P0 stub -- P3 ships the SQLite UPSERT."""
    raise NotImplementedError("upsert_lesson() is a P3 deliverable")


def query_lessons(symptom_hash: str, project_key: str) -> list[dict]:
    """P0 stub -- P3 ships the SQLite query."""
    raise NotImplementedError("query_lessons() is a P3 deliverable")
