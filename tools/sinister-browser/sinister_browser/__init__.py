# Author: RKOJ-ELENO :: 2026-05-23
# License: AGPL-3.0-or-later

"""Sinister wrapper around firefox-agent-bridge (jcode-feature-matrix row 26).

Layer A (probe) shipped v0.1.0. Layer B (pythonic action API) shipped
v0.2.0. Layer C (Forge/Term slash) and Layer D (skill mirror) deferred
per the integration-shape doctrine at
`_shared-memory/knowledge/browser-bridge-integration-shape-2026-05-23.md`.
"""

__version__ = "0.2.0"

from sinister_browser.probe import probe, ProbeResult  # noqa: F401
from sinister_browser.api import (  # noqa: F401
    Browser,
    BrowserError,
    BrowserConnectError,
    BrowserProtocolError,
    BrowserActionError,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_TIMEOUT,
)
