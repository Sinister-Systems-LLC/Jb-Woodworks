"""Keybox parsing + manifest verification tests.

RKOJ-ELENO :: 2026-05-24

These tests run on Windows without cvd. Real-keybox-against-running-cvd
PI tests live in test_play_integrity.py and require the cvd path.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

# Add the keybox dir to sys.path so we can import parse_keybox without packaging
KEYBOX_DIR = Path(__file__).resolve().parents[1] / "keybox"
sys.path.insert(0, str(KEYBOX_DIR))

from parse_keybox import parse_keybox_file  # noqa: E402

MANIFEST_PATH = KEYBOX_DIR / "manifest.json"


def _operator_keybox_path() -> Path | None:
    """Operator-supplied keybox path. Returns None if not present (test skips)."""
    # Standard hint per docs/keybox/README.md
    p = Path(r"C:\Users\Zonia\Desktop\keybox_20260523.xml")
    if p.exists():
        return p
    # Allow override via env for portability across operator hosts
    env = os.environ.get("OPERATOR_KEYBOX_PATH")
    if env and Path(env).exists():
        return Path(env)
    return None


def test_manifest_exists_and_parses() -> None:
    assert MANIFEST_PATH.exists(), "keybox manifest.json missing"
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert data["schema_version"] == "sinister.keybox-manifest.v1"
    assert isinstance(data["keyboxes"], list)


def test_manifest_no_private_key_material() -> None:
    """Sanity gate: the manifest must NEVER contain private key bytes."""
    raw = MANIFEST_PATH.read_text(encoding="utf-8")
    for banned in (
        "-----BEGIN PRIVATE KEY-----",
        "-----BEGIN EC PRIVATE KEY-----",
        "-----BEGIN RSA PRIVATE KEY-----",
    ):
        assert banned not in raw, f"manifest contains banned marker {banned!r}"


def test_manifest_rows_have_required_fields() -> None:
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    required = {
        "filename", "sha256", "size_bytes", "first_seen_utc",
        "device_id", "primary_key_algorithm", "cert_chain_length_per_key",
        "primary_chain_root_der_sha256", "status",
    }
    for row in data["keyboxes"]:
        missing = required - set(row)
        assert not missing, f"row missing fields {missing}: {row}"


def test_operator_keybox_parses_if_present() -> None:
    path = _operator_keybox_path()
    if not path:
        pytest.skip("operator keybox not on Desktop or in OPERATOR_KEYBOX_PATH")
    parsed = parse_keybox_file(path)
    assert parsed["filename"]
    assert len(parsed["sha256"]) == 64  # hex sha256
    assert parsed["number_of_keys_parsed"] >= 1
    # The parser must NOT propagate private key bytes
    serialized = json.dumps(parsed)
    assert "-----BEGIN" not in serialized, "parse_keybox leaked PEM into its output"


def test_operator_keybox_sha_matches_manifest_if_present() -> None:
    path = _operator_keybox_path()
    if not path:
        pytest.skip("operator keybox not available")
    parsed = parse_keybox_file(path)
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    matched = [r for r in manifest["keyboxes"] if r["sha256"] == parsed["sha256"]]
    assert len(matched) == 1, (
        f"keybox sha {parsed['sha256']} not in manifest — run "
        f"`python keybox/verify_keybox.py --path <path> --accept-new` to register"
    )
    row = matched[0]
    assert row["status"] in ("active", "superseded", "revoked")


def test_keybox_structure_samsung_ecdsa_chain() -> None:
    """Smoke check against the specific operator-supplied keybox.

    Expected shape: Samsung DeviceID + ECDSA primary key + 3-cert chain.
    If operator rotates to a different keybox, this test gets a new expected.
    """
    path = _operator_keybox_path()
    if not path:
        pytest.skip("operator keybox not available")
    parsed = parse_keybox_file(path)
    primary = parsed["keys"][0]
    assert primary["device_id"].startswith("Samsung_"), \
        f"expected Samsung DeviceID, got {primary['device_id']!r}"
    assert primary["key_algorithm"] == "ecdsa", \
        f"expected ECDSA primary key, got {primary['key_algorithm']!r}"
    assert primary["cert_chain_length"] == 3, \
        f"expected 3-cert chain, got {primary['cert_chain_length']}"
