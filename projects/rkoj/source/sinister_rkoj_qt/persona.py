# Author: RKOJ-ELENO :: 2026-05-21
"""EVE opening-prompt builder — ported verbatim from automations/window-manager/server.py.

Operator-canonical 2026-05-21: every spawned claude subprocess is EVE on <project>.
RKOJ-ELENO authorship, Sanctum purple, full Sinister fleet tools available.
"""

from __future__ import annotations


def build_opening_prompt(
    project_key: str,
    agent_name: str,
    mode: str = "claude",
    accent: str = "purple",
) -> str:
    """Returns the EVE opening prompt seeded into every new agent.

    Trimmed in v1.6.2 from ~500 chars to ~220 chars so first-turn latency
    isn't dominated by persona-block size. Identity + key contracts only;
    the fleet-tools enumeration is now available via the `/persona` slash
    command on demand.
    """
    return (
        f"You are EVE, the Sinister Sanctum orchestration agent on project "
        f"`{project_key}`. Always self-reference as EVE (never Claude / assistant / AI). "
        f"Author new files with `Author: RKOJ-ELENO :: <date>`. Branch as "
        f"`agent/{project_key}/<topic>` from main. Sanctum purple branding, "
        f"frameless PyQt6 RKOJ.exe shell."
    )


def eve_label(agent_name: str, project_key: str = "") -> str:
    """Format the operator-facing 'EVE on <project>' label."""
    base = f"EVE on {agent_name}"
    if project_key:
        base = f"{base} :: {project_key}"
    return base
