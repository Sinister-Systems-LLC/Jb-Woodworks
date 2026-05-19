# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
"""sanctum_shared :: window-manager-local persistence + scheduler modules.

This package holds the modules that ship inside the RKOJ.exe bundle and are
exclusive to the window-manager backend:

  * :mod:`sanctum_shared.cycle_points` - one-click project-state resume
    snapshots stored under ``_shared-memory/cycle-points/``.
  * :mod:`sanctum_shared.scheduler` - cron-like daemon that fires due
    actions (http / script / spawn-agent) on a 30 s tick.

These were previously co-located in a local ``_shared/`` package which
shadowed (and merged via ``__path__``-extension into) the hub's
``_shared/`` package at
``D:/Sinister/Sinister Skills/12_LLM_ORCHESTRATION/agents/_shared/``.

PyInstaller's underscore-prefix data-tuple collection silently dropped the
local ``_shared/`` directory from the frozen bundle (audit HR-B,
2026-05-19), so cycle-points + scheduler were broken inside the EXE. The
fix splits the two responsibilities: this package now exclusively owns
the local-only modules under a non-underscore name (``sanctum_shared``)
so PyInstaller's ``collect_submodules`` + ``collect_data_files`` pick it
up cleanly, and ``server.py`` keeps importing the hub modules via the
plain ``_shared`` name (resolved by inserting the hub agents directory
into ``sys.path``).
"""
from __future__ import annotations

__all__ = ["cycle_points", "scheduler"]
