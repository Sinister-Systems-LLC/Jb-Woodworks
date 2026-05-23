"""
crypto - at-rest passphrase-locked AES-128-CBC + HMAC-SHA256 (Fernet) for
operator-private Sinister files.

Threat model: someone gets physical access to the Sinister drive while operator
is away. They should not be able to read Yurikey roster / per-project absorbed
facts / _bus context logs. Files marked `.locked` on disk; operator runs
`unlock_all` once per session (passphrase prompt) to surface them.

Explicitly NOT for:
  - Hiding from Anthropic (the absorbed facts get DECRYPTED + sent in prompts when
    operator is using the bot; otherwise they're not sent at all).
  - Hiding from the operator (operator controls the passphrase).
  - Hiding from the audit log (absorption-log.jsonl stays plain).

Passphrase source (in priority order):
  1. SINISTER_VAULT_PASSPHRASE env var
  2. Key file at ~/.sinister/vault-key (NOT in any repo, NOT backed up)
  3. Interactive getpass prompt (operator types it)

Key derivation: PBKDF2-HMAC-SHA256 (200k iterations) with per-vault salt.
Salt persisted at <hub>/12_LLM_ORCHESTRATION/runtime-state/vault.salt (NOT a secret;
required for derivation but not exploitable alone).
"""

from __future__ import annotations

import base64
import getpass
import hashlib
import json
import os
from pathlib import Path
from typing import Any

try:
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

HUB_ROOT = Path(os.environ.get("SINISTER_HUB_ROOT", r"D:\Sinister\Sinister Skills"))
SALT_PATH = HUB_ROOT / "12_LLM_ORCHESTRATION" / "runtime-state" / "vault.salt"
KEY_FILE = Path(os.path.expanduser("~")) / ".sinister" / "vault-key"
LOCK_SUFFIX = ".locked"

# In-process derived key cache. Reset on process exit. Never persisted.
_cached_key: bytes | None = None
_cached_pass_id: str | None = None


def _ensure_salt() -> bytes:
    """Get-or-create the per-vault salt. Not a secret; required for derivation."""
    SALT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if SALT_PATH.exists():
        return SALT_PATH.read_bytes()
    salt = os.urandom(16)
    SALT_PATH.write_bytes(salt)
    return salt


def _get_passphrase() -> str:
    """Read passphrase from env / file / prompt. Cached for the process."""
    p = os.environ.get("SINISTER_VAULT_PASSPHRASE")
    if p:
        return p
    if KEY_FILE.exists():
        try:
            return KEY_FILE.read_text(encoding="utf-8").strip()
        except Exception:
            pass
    # Interactive fallback. Only works when running with a TTY; MCP servers run
    # headless, so the operator must set the env var or key file before bots
    # try to unlock.
    return getpass.getpass("Sinister vault passphrase: ")


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    """PBKDF2-HMAC-SHA256 -> 32 bytes -> base64 (Fernet format)."""
    if not HAS_CRYPTO:
        raise RuntimeError("cryptography not installed: pip install cryptography")
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=200_000)
    raw = kdf.derive(passphrase.encode("utf-8"))
    return base64.urlsafe_b64encode(raw)


def _get_key() -> bytes:
    global _cached_key, _cached_pass_id
    passphrase = _get_passphrase()
    pass_id = hashlib.sha256(passphrase.encode("utf-8")).hexdigest()[:16]
    if _cached_key is not None and _cached_pass_id == pass_id:
        return _cached_key
    salt = _ensure_salt()
    _cached_key = _derive_key(passphrase, salt)
    _cached_pass_id = pass_id
    return _cached_key


def is_locked(path: str | Path) -> bool:
    return str(path).endswith(LOCK_SUFFIX) or Path(str(path) + LOCK_SUFFIX).exists()


def lock_path(path: str | Path) -> dict[str, Any]:
    """Encrypt a single file in-place (write `<path>.locked`, atomic remove original)."""
    if not HAS_CRYPTO:
        return {"ok": False, "error": "cryptography not installed"}
    p = Path(path)
    if not p.exists():
        return {"ok": False, "error": f"path not found: {p}"}
    if str(p).endswith(LOCK_SUFFIX):
        return {"ok": False, "error": "already locked"}
    out = Path(str(p) + LOCK_SUFFIX)
    try:
        data = p.read_bytes()
        key = _get_key()
        token = Fernet(key).encrypt(data)
        tmp = out.with_suffix(out.suffix + f".tmp.{os.urandom(4).hex()}")
        tmp.write_bytes(token)
        os.replace(tmp, out)
        p.unlink()
    except Exception as e:
        return {"ok": False, "error": str(e)}
    return {"ok": True, "locked_path": str(out), "original_bytes": len(data), "locked_bytes": out.stat().st_size}


def unlock_path(path: str | Path, keep_locked: bool = False) -> dict[str, Any]:
    """Decrypt a single `.locked` file. By default removes the .locked + writes the original path."""
    if not HAS_CRYPTO:
        return {"ok": False, "error": "cryptography not installed"}
    p = Path(path)
    if not str(p).endswith(LOCK_SUFFIX):
        p = Path(str(p) + LOCK_SUFFIX)
    if not p.exists():
        return {"ok": False, "error": f"locked file not found: {p}"}
    out = Path(str(p)[:-len(LOCK_SUFFIX)])
    try:
        token = p.read_bytes()
        key = _get_key()
        data = Fernet(key).decrypt(token)
        tmp = out.with_suffix(out.suffix + f".tmp.{os.urandom(4).hex()}")
        tmp.write_bytes(data)
        os.replace(tmp, out)
        if not keep_locked:
            p.unlink()
    except InvalidToken:
        return {"ok": False, "error": "passphrase incorrect OR file corrupted (InvalidToken)"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    return {"ok": True, "unlocked_path": str(out), "original_bytes": out.stat().st_size}


def lock_glob(root: str | Path, patterns: list[str]) -> dict[str, Any]:
    """Lock every file under root matching any glob pattern. Skips already-locked."""
    root = Path(root)
    if not root.exists():
        return {"ok": False, "error": f"root not found: {root}"}
    locked = []
    skipped = []
    errors = []
    for pat in patterns:
        for f in root.rglob(pat):
            if not f.is_file():
                continue
            if str(f).endswith(LOCK_SUFFIX):
                skipped.append(str(f))
                continue
            r = lock_path(f)
            if r.get("ok"):
                locked.append(r["locked_path"])
            else:
                errors.append({"path": str(f), "error": r.get("error")})
    return {"ok": True, "locked_count": len(locked), "skipped_count": len(skipped), "errors": errors, "locked": locked[:20]}


def unlock_glob(root: str | Path, keep_locked: bool = False) -> dict[str, Any]:
    """Unlock every `*.locked` under root."""
    root = Path(root)
    if not root.exists():
        return {"ok": False, "error": f"root not found: {root}"}
    unlocked = []
    errors = []
    for f in root.rglob(f"*{LOCK_SUFFIX}"):
        if not f.is_file():
            continue
        r = unlock_path(f, keep_locked=keep_locked)
        if r.get("ok"):
            unlocked.append(r["unlocked_path"])
        else:
            errors.append({"path": str(f), "error": r.get("error")})
    return {"ok": True, "unlocked_count": len(unlocked), "errors": errors, "unlocked": unlocked[:20]}


def status() -> dict[str, Any]:
    return {
        "ok": True,
        "has_cryptography": HAS_CRYPTO,
        "salt_exists": SALT_PATH.exists(),
        "key_file_exists": KEY_FILE.exists(),
        "env_passphrase_set": "SINISTER_VAULT_PASSPHRASE" in os.environ,
        "salt_path": str(SALT_PATH),
        "key_file_path": str(KEY_FILE),
    }
