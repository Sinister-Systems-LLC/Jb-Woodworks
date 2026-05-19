# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
"""regen-auth-keys.py :: trigger auth._ensure_keys_file() to regenerate
`_vault/auth-keys.json` + refresh `_vault/auth-keys-DELIVER-TO-LEO.txt`.

Invoked by `Fix-RKOJ-Login.bat` -> `fix-rkoj-login.ps1`. Kept as a permanent
.py file (not an inline `-c` heredoc) because PowerShell 5.1's native-command
argument parsing mangles double-quoted strings on the way to python.exe -- see
`_shared-memory/knowledge/powershell-stderr-wrap.md` for the broader gotcha.

Run from the window-manager dir so `import auth` resolves:

    cd "D:\\Sinister Sanctum\\automations\\window-manager"
    .\\.venv\\Scripts\\python.exe ..\\regen-auth-keys.py

Exits 0 on success, prints structured JSON on stdout.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Make sure `import auth` resolves against window-manager/, regardless of cwd.
_HERE = Path(__file__).resolve().parent
_WM = _HERE / "window-manager"
if _WM.exists():
    sys.path.insert(0, str(_WM))
else:
    # Fall back to cwd
    sys.path.insert(0, ".")

try:
    from auth import _ensure_keys_file, derive_hwid  # type: ignore
except Exception as exc:
    print(json.dumps({"ok": False, "stage": "import", "error": str(exc)}, indent=2))
    sys.exit(2)

try:
    data = _ensure_keys_file()
    hwid = derive_hwid()
    labels = [e.get("label", "?") for e in data.get("keys", [])]
    summary = {
        "ok": True,
        "stage": "complete",
        "key_count": len(data.get("keys", [])),
        "labels": labels,
        "hwid": hwid,
        "vault_dir": str(_HERE.parent / "_vault"),
    }
    print(json.dumps(summary, indent=2))
    sys.exit(0)
except Exception as exc:
    print(json.dumps({"ok": False, "stage": "regen", "error": str(exc)}, indent=2))
    sys.exit(3)
