# Author: RKOJ-ELENO :: 2026-05-23
# License: AGPL-3.0-or-later

"""Sinister Utils — defensive I/O helpers for the fleet.

See `_shared-memory/knowledge/powershell-out-file-bom-bites-python-readers-2026-05-23.md`
for the doctrine these helpers codify.
"""

__version__ = "0.1.0"

from sinister_utils.io import (  # noqa: F401
    load_json_tolerant,
    load_text_tolerant,
    write_json_no_bom,
    write_text_no_bom,
)
