# Author: RKOJ-ELENO :: 2026-05-23
# License: AGPL-3.0-or-later

"""Sinister wrapper around firefox-agent-bridge (jcode-feature-matrix row 26).

Layer A (probe) is shipped in v0.1.0. Layers B (pythonic API), C (Forge/Term
slash), D (skill mirror) are deferred per the integration-shape doctrine at
`_shared-memory/knowledge/browser-bridge-integration-shape-2026-05-23.md`.
"""

__version__ = "0.1.0"

from sinister_browser.probe import probe, ProbeResult  # noqa: F401
