# Sinister Sanctum :: sinister-jcode-shim :: package
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
"""
Sidecar launcher that runs the prebuilt jcode-windows-x86_64.exe with
Sinister branding/config injected via environment variables.

This is a stop-gap until we fork jcode source-level. The Rust toolchain
is operator-gated (~1.5 GB rustup install + ~5-10 GB cargo workspace
build for the 60+ crates in jcode-0.12.3). Plan lives at
`_shared-memory/plans/jcode-fork-2026-05-21/plan.md`.
"""

__version__ = "0.1.0"

__all__ = ["__version__"]
