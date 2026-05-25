# Author: RKOJ-ELENO :: 2026-05-23
# License: AGPL-3.0-or-later

"""Defensive I/O helpers — BOM-tolerant read, BOM-less write.

Doctrine: ``_shared-memory/knowledge/powershell-out-file-bom-bites-python-readers-2026-05-23.md``.

Three properties enforced by every helper here:
  1. BOM-tolerant on read (``utf-8-sig`` strips a leading BOM if present)
  2. Narrow exception catch (``OSError`` + ``UnicodeDecodeError`` +
     ``json.JSONDecodeError`` only; programmer errors propagate)
  3. Logged on swallow (silent failure modes become loud log lines)
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any


_logger = logging.getLogger(__name__)


def load_json_tolerant(
    path: str | os.PathLike,
    default: Any = None,
) -> Any:
    """Read a JSON file with BOM-tolerant + logged-on-swallow semantics.

    Args:
        path: file to read.
        default: returned when read or parse fails; ``None`` if not given.

    Returns:
        The parsed JSON value (any type — dict/list/str/etc.) on success,
        or ``default`` on any of: file missing, OSError, UnicodeDecodeError,
        JSONDecodeError. Every failure emits a ``logging.warning(...)``.
    """
    p = Path(path)
    try:
        with open(p, "r", encoding="utf-8-sig") as fh:
            return json.load(fh)
    except FileNotFoundError:
        _logger.warning("load_json_tolerant: file not found: %s", p)
        return default
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        _logger.warning(
            "load_json_tolerant: %s on %s: %s",
            type(e).__name__, p, e,
        )
        return default


def load_text_tolerant(
    path: str | os.PathLike,
    default: str = "",
) -> str:
    """Read a text file with BOM-tolerant + logged-on-swallow semantics.

    Args:
        path: file to read.
        default: returned when read fails; empty string if not given.

    Returns:
        The file contents (with any leading BOM stripped) or ``default``.
    """
    p = Path(path)
    try:
        with open(p, "r", encoding="utf-8-sig") as fh:
            return fh.read()
    except FileNotFoundError:
        _logger.warning("load_text_tolerant: file not found: %s", p)
        return default
    except (OSError, UnicodeDecodeError) as e:
        _logger.warning(
            "load_text_tolerant: %s on %s: %s",
            type(e).__name__, p, e,
        )
        return default


def write_json_no_bom(
    path: str | os.PathLike,
    data: Any,
    *,
    indent: int | None = 2,
    sort_keys: bool = False,
    atomic: bool = True,
) -> None:
    """Write JSON to disk with **no UTF-8 BOM**.

    PowerShell ``Out-File`` and ``Set-Content -Encoding utf8`` (PS 5.1)
    write a BOM by default; Python's ``open(..., encoding="utf-8")``
    writes WITHOUT a BOM, so callers that go through Python are already
    safe. This helper formalizes that behavior + adds atomic-write
    semantics (write to ``.tmp`` then ``os.replace``).

    Args:
        path: destination file.
        data: any JSON-serializable value.
        indent: passed to ``json.dumps``; default 2.
        sort_keys: passed to ``json.dumps``.
        atomic: write to a temp file in the same directory then
            ``os.replace`` to the target. Default True. Disable only
            when targeting a filesystem that doesn't support replace.

    Raises:
        OSError on filesystem errors.
        TypeError if ``data`` isn't JSON-serializable.
    """
    p = Path(path)
    encoded = json.dumps(data, indent=indent, sort_keys=sort_keys, ensure_ascii=False)
    # Verify no BOM (cheap sanity check)
    encoded_bytes = encoded.encode("utf-8")
    assert not encoded_bytes.startswith(b"\xef\xbb\xbf"), "json.dumps should never emit BOM"
    if atomic:
        p.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(
            prefix=f".{p.name}.", suffix=".tmp", dir=str(p.parent)
        )
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(encoded_bytes)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp_path, p)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
    else:
        with open(p, "wb") as fh:
            fh.write(encoded_bytes)


def write_text_no_bom(
    path: str | os.PathLike,
    text: str,
    *,
    atomic: bool = True,
) -> None:
    """Write text to disk with no UTF-8 BOM + atomic-write semantics.

    Args:
        path: destination file.
        text: text content.
        atomic: write to a temp file in the same directory then
            ``os.replace`` to the target. Default True.

    Raises:
        OSError on filesystem errors.
    """
    p = Path(path)
    encoded_bytes = text.encode("utf-8")
    assert not encoded_bytes.startswith(b"\xef\xbb\xbf"), \
        "input text already had a BOM — caller should strip first"
    if atomic:
        p.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(
            prefix=f".{p.name}.", suffix=".tmp", dir=str(p.parent)
        )
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(encoded_bytes)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp_path, p)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
    else:
        with open(p, "wb") as fh:
            fh.write(encoded_bytes)
