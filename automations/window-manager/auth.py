# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
"""
Sanctum Console :: HWID-locked auth-key login

No usernames. Just an auth key per person. First time a key is entered,
it gets bound to the current machine's HWID. After that, the same key on
a different machine is rejected.

HWID = sha256(machine-guid + volume-serial-C + hostname)[0:32]

Keys live at `_vault/auth-keys.json` (operator-private; gitignored). Generated
on first server boot if missing — 2 keys: operator + leo.

Session token issued on successful login (32-byte url-safe). Persisted in
the same json so the server survives restarts. Client stores in localStorage.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import secrets
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VAULT_DIR = Path(r"D:\Sinister Sanctum\_vault")
AUTH_KEYS_FILE = VAULT_DIR / "auth-keys.json"
PRINT_FILE = VAULT_DIR / "auth-keys-DELIVER-TO-LEO.txt"


def derive_hwid() -> str:
    """Combine machine-guid + volume-serial(C:) + hostname into a stable HWID."""
    parts = []
    # 1. Windows machine GUID (stable across reboots)
    try:
        if platform.system() == "Windows":
            out = subprocess.run(
                ['reg', 'query', r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Cryptography', '/v', 'MachineGuid'],
                capture_output=True, text=True, timeout=3,
            )
            for line in (out.stdout or "").splitlines():
                if "MachineGuid" in line and "REG_SZ" in line:
                    parts.append(line.split()[-1].strip())
                    break
    except Exception:
        pass
    # 2. Volume serial of C:
    try:
        if platform.system() == "Windows":
            out = subprocess.run(
                ['cmd', '/c', 'vol', 'C:'],
                capture_output=True, text=True, timeout=3,
            )
            for line in (out.stdout or "").splitlines():
                if "Serial Number" in line or "Serial-Nummer" in line:
                    parts.append(line.strip().split()[-1])
                    break
    except Exception:
        pass
    # 3. Hostname
    try:
        parts.append(socket.gethostname())
    except Exception:
        parts.append("unknown-host")
    # 4. Fallback if nothing collected
    if not parts:
        parts = [platform.node() or "fallback"]
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def _ensure_keys_file() -> dict[str, Any]:
    """Load auth-keys.json, generating two starter keys (operator + leo) on first boot."""
    VAULT_DIR.mkdir(parents=True, exist_ok=True)
    if AUTH_KEYS_FILE.exists():
        try:
            return json.loads(AUTH_KEYS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    op_key = secrets.token_urlsafe(24)
    leo_key = secrets.token_urlsafe(24)
    data = {
        "_comment": "Sanctum Console auth keys. Each key binds to one HWID on first use. No usernames — just key + HWID.",
        "version": 1,
        "keys": [
            {"label": "operator", "key": op_key, "bound_hwid": None, "bound_at": None, "session_token": None, "session_issued_at": None},
            {"label": "leo",      "key": leo_key, "bound_hwid": None, "bound_at": None, "session_token": None, "session_issued_at": None},
        ],
    }
    AUTH_KEYS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    # Also write a plain-text "deliver to leo" file the operator can read once + share securely
    PRINT_FILE.write_text(
        f"""SINISTER SANCTUM :: CONSOLE AUTH KEYS
=========================================================
Generated: {datetime.now().isoformat()}
HWID (this machine): {derive_hwid()}

OPERATOR KEY: {op_key}
LEO KEY:      {leo_key}

Each key binds to the FIRST MACHINE it is entered on. The operator key is
expected to bind to this machine the first time the operator logs in.
Deliver the Leo key to Leo via a SECURE channel (Signal / 1Password / in person).
After Leo logs in once, his key is locked to his machine.

If a key needs to be reset (e.g. Leo got a new PC), edit auth-keys.json:
clear `bound_hwid` and `bound_at` for that entry.

Do NOT commit auth-keys.json or this file. They are in .gitignore by default.
""",
        encoding="utf-8",
    )
    return data


def _save_keys(data: dict[str, Any]) -> None:
    AUTH_KEYS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def login(submitted_key: str, current_hwid: str | None = None) -> dict[str, Any]:
    """Try to authenticate. Returns {ok, label, token, message}.
    - First time a key is entered: binds to current HWID + issues token.
    - Subsequent: HWID must match.
    """
    if not submitted_key or not isinstance(submitted_key, str):
        return {"ok": False, "error": "no key provided"}
    data = _ensure_keys_file()
    if current_hwid is None:
        current_hwid = derive_hwid()
    now = datetime.now(timezone.utc).isoformat()
    for entry in data["keys"]:
        if entry["key"] == submitted_key:
            if entry["bound_hwid"] is None:
                # First-time bind
                entry["bound_hwid"] = current_hwid
                entry["bound_at"] = now
            elif entry["bound_hwid"] != current_hwid:
                return {"ok": False, "error": "this key is bound to a different machine (HWID mismatch)"}
            entry["session_token"] = secrets.token_urlsafe(32)
            entry["session_issued_at"] = now
            _save_keys(data)
            return {"ok": True, "label": entry["label"], "token": entry["session_token"]}
    return {"ok": False, "error": "invalid key"}


def validate_token(token: str, current_hwid: str | None = None) -> dict[str, Any]:
    """Validate a session token + HWID. Used by the auth middleware on every request."""
    if not token:
        return {"ok": False, "error": "no token"}
    data = _ensure_keys_file()
    if current_hwid is None:
        current_hwid = derive_hwid()
    for entry in data["keys"]:
        if entry.get("session_token") == token:
            if entry.get("bound_hwid") != current_hwid:
                return {"ok": False, "error": "HWID mismatch on token"}
            return {"ok": True, "label": entry["label"]}
    return {"ok": False, "error": "invalid token"}


def logout(token: str) -> dict[str, Any]:
    """Revoke a session token."""
    data = _ensure_keys_file()
    for entry in data["keys"]:
        if entry.get("session_token") == token:
            entry["session_token"] = None
            entry["session_issued_at"] = None
            _save_keys(data)
            return {"ok": True}
    return {"ok": False, "error": "token not found"}


def status() -> dict[str, Any]:
    """Diagnostic — counts only, no key material."""
    data = _ensure_keys_file()
    return {
        "ok": True,
        "hwid_self": derive_hwid(),
        "keys": [
            {
                "label": e["label"],
                "bound": e["bound_hwid"] is not None,
                "bound_at": e["bound_at"],
                "has_active_session": e.get("session_token") is not None,
            }
            for e in data["keys"]
        ],
    }
