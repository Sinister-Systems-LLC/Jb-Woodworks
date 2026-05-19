> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Topic: `pip install --upgrade pip` in a fresh venv can corrupt pip's vendored modules on Py 3.12

**Slug:** pip-self-upgrade-breaks-venv
**First discovered:** 2026-05-19 by Sinister Sanctum
**Last updated:** 2026-05-19 by Sinister Sanctum
**Status:** known-issue
**Tags:** pip, venv, python-3-12, urllib3

## Problem

Standard pattern in a fresh-venv bootstrap script:

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install --upgrade pip
.venv/Scripts/python.exe -m pip install -r requirements.txt
```

The middle step (pip self-upgrade) corrupts pip's vendored modules on Python 3.12. The subsequent install fails with:

```
ImportError: cannot import name 'urllib3' from 'pip._vendor'
   (.../.venv/Lib/site-packages/pip/_vendor/__init__.py)
```

The vendored `pip._vendor.requests` tries to import `urllib3` from the vendor package, but the upgrade left vendor in a half-replaced state.

## Why it happens

pip's vendor modules (`pip._vendor.requests`, `pip._vendor.urllib3`, etc.) are bundled with pip itself. When pip self-upgrades, it replaces itself while still running. On Windows + Python 3.12, this dance occasionally leaves the vendor directory partially written — newer `requests` referencing older `urllib3` (or vice versa).

Once corrupted, the venv's pip is essentially dead. `python -m pip install <anything>` fails with the import error.

## Fix or workaround

### Best fix: don't self-upgrade pip in fresh venvs

```bash
# DO NOT do this in a fresh venv
.venv/Scripts/python.exe -m pip install --upgrade pip

# DO just use the bundled pip
.venv/Scripts/python.exe -m pip install -r requirements.txt
```

pip's bundled version is typically recent enough for any modern requirements.txt. Self-upgrade is unnecessary 99% of the time.

### If you've already broken a venv

Nuke and recreate:

```bash
rm -rf .venv
python -m venv .venv --clear
.venv/Scripts/python.exe -m ensurepip --upgrade   # uses Python's ensurepip, not pip-self
.venv/Scripts/python.exe -m pip install -r requirements.txt
```

`ensurepip` is more robust than `pip install --upgrade pip` because it doesn't replace-while-running.

## Sanctum-specific note

The `Open-Sanctum-Console.bat` v1 had `python -m pip install --upgrade pip` in its first-run setup. This bricked the operator's window-manager venv. Fixed in v2: bat now skips self-upgrade and only installs requirements. Sanctum-Desktop.bat + Sanctum-LAN.bat follow the same fix.

## Discoveries (append-only log, most-recent at top)

### 2026-05-19 01:00 by Sinister Sanctum
First hit on the operator's machine during Sanctum Console first-run. Took ~5 minutes to root-cause because the error doesn't mention pip's self-upgrade as the trigger. After removing the self-upgrade step + recreating the venv, install succeeded cleanly.

## Related topics

- [pyinstaller-tomli-hook-missing](./pyinstaller-tomli-hook-missing.md)
