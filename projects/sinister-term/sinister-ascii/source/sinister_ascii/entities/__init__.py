# Sinister ASCII (sub-project of Sinister Term)
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# Per-project entity registry. Each entity is a tiny dataclass instance —
# adding a new project means adding one line here + (optionally) a custom
# glyph ramp.

from __future__ import annotations

from sinister_ascii.entities._base import Entity, DEFAULT_GLYPH_RAMP
from sinister_ascii.palette import PROJECT_PALETTES


# Glyph ramps per personality
_GLYPHS_ORBITAL    = ("·", "∘", "○", "◌", "◍", "◉", "●", "✦", "✷", "❖", "✶")
_GLYPHS_SPARK      = ("·", "˙", "ˆ", "*", "✦", "✧", "✪", "✸", "✺", "✹", "✷")
_GLYPHS_DEEP       = ("·", "•", "◦", "○", "◍", "◉", "◈", "◆", "❖", "❒", "▣")
_GLYPHS_GROW       = ("·", "˖", "✿", "❀", "✾", "❁", "✼", "✻", "✺", "✦", "❋")
_GLYPHS_ARCHIVE    = ("·", "▱", "▰", "▦", "▩", "▣", "❖", "◈", "◆", "✦", "❀")
_GLYPHS_GLYPH_KEEP = ("·", "∙", "◌", "◯", "◍", "◉", "✦", "✷", "❖", "◈", "❉")


# Operator-named characters per project. Each is one canonical Entity.
ENTITIES: dict[str, Entity] = {
    "sinister-sanctum": Entity(
        name="EVE-prime",
        project_key="sinister-sanctum",
        motion_kind="orbit",
        palette=PROJECT_PALETTES["sinister-sanctum"],
        glyphs=_GLYPHS_ORBITAL,
        motion_kwargs={"radius": 0.75, "period_s": 8.0, "wobble": 0.14},
    ),
    "sinister-term": Entity(
        name="Glyph-keeper",
        project_key="sinister-term",
        motion_kind="pulse",
        palette=PROJECT_PALETTES["sinister-term"],
        glyphs=_GLYPHS_GLYPH_KEEP,
        motion_kwargs={"period_s": 2.0},
    ),
    "sinister-forge": Entity(
        name="Forge-spark",
        project_key="sinister-forge",
        motion_kind="spiral",
        palette=PROJECT_PALETTES["sinister-forge"],
        glyphs=_GLYPHS_SPARK,
        motion_kwargs={"period_s": 7.5, "growth": 0.7},
    ),
    "sinister-mind": Entity(
        name="Mind-weave",
        project_key="sinister-mind",
        motion_kind="drift",
        palette=PROJECT_PALETTES["sinister-mind"],
        glyphs=_GLYPHS_DEEP,
        motion_kwargs={"x_period_s": 14.0, "y_period_s": 19.0},
    ),
    "sinister-overseer": Entity(
        name="Watcher",
        project_key="sinister-overseer",
        motion_kind="orbit",
        palette=PROJECT_PALETTES["sinister-overseer"],
        glyphs=_GLYPHS_GROW,
        motion_kwargs={"radius": 0.55, "period_s": 11.0, "wobble": 0.08},
    ),
    "sinister-chatbot": Entity(
        name="Spark-tongue",
        project_key="sinister-chatbot",
        motion_kind="pulse",
        palette=PROJECT_PALETTES["sinister-chatbot"],
        glyphs=_GLYPHS_SPARK,
        motion_kwargs={"period_s": 1.6},
    ),
    "sinister-vault": Entity(
        name="Vault-warden",
        project_key="sinister-vault",
        motion_kind="breathe",
        palette=PROJECT_PALETTES["sinister-vault"],
        glyphs=_GLYPHS_ARCHIVE,
        motion_kwargs={"inhale_s": 3.0, "exhale_s": 5.0},
    ),
    "sinister-memory": Entity(
        name="Memory-river",
        project_key="sinister-memory",
        motion_kind="drift",
        palette=PROJECT_PALETTES["sinister-memory"],
        glyphs=_GLYPHS_DEEP,
        motion_kwargs={"x_period_s": 17.0, "y_period_s": 23.0},
    ),
    "sinister-kernel-apk": Entity(
        name="Hammer-of-cores",
        project_key="sinister-kernel-apk",
        motion_kind="spiral",
        palette=PROJECT_PALETTES["sinister-kernel-apk"],
        glyphs=_GLYPHS_DEEP,
        motion_kwargs={"period_s": 6.0, "growth": 0.55},
    ),
    "sinister-panel": Entity(
        name="Panel-conductor",
        project_key="sinister-panel",
        motion_kind="orbit",
        palette=PROJECT_PALETTES["sinister-panel"],
        glyphs=_GLYPHS_ORBITAL,
        motion_kwargs={"radius": 0.7, "period_s": 10.0},
    ),
    "sinister-link": Entity(
        name="Linksmith",
        project_key="sinister-link",
        motion_kind="drift",
        palette=PROJECT_PALETTES["sinister-link"],
        glyphs=_GLYPHS_GROW,
        motion_kwargs={"x_period_s": 11.0, "y_period_s": 13.0},
    ),
    "sinister-os": Entity(
        name="Sovereign",
        project_key="sinister-os",
        motion_kind="orbit",
        palette=PROJECT_PALETTES["sinister-os"],
        glyphs=_GLYPHS_ORBITAL,
        motion_kwargs={"radius": 0.85, "period_s": 12.0, "wobble": 0.18},
    ),
    # SA-PH7 (iter-48) — remaining 13 projects from projects.json.
    "sinister-emulator": Entity(
        name="Phantom-shell",
        project_key="sinister-emulator",
        motion_kind="spiral",
        palette=PROJECT_PALETTES["sinister-emulator"],
        glyphs=_GLYPHS_SPARK,
        motion_kwargs={"period_s": 8.0, "growth": 0.6},
    ),
    "sinister-bus": Entity(
        name="Synapse",
        project_key="sinister-bus",
        motion_kind="drift",
        palette=PROJECT_PALETTES["sinister-bus"],
        glyphs=_GLYPHS_DEEP,
        motion_kwargs={"x_period_s": 12.0, "y_period_s": 15.0},
    ),
    "sinister-designer": Entity(
        name="Loom-keeper",
        project_key="sinister-designer",
        motion_kind="breathe",
        palette=PROJECT_PALETTES["sinister-designer"],
        glyphs=_GLYPHS_GLYPH_KEEP,
        motion_kwargs={"inhale_s": 2.7, "exhale_s": 4.1},
    ),
    "sinister-sleight": Entity(
        name="Sleight-hand",
        project_key="sinister-sleight",
        motion_kind="orbit",
        palette=PROJECT_PALETTES["sinister-sleight"],
        glyphs=_GLYPHS_SPARK,
        motion_kwargs={"radius": 0.65, "period_s": 9.0, "wobble": 0.15},
    ),
    "sinister-snap-emu": Entity(
        name="Cartridge-priest",
        project_key="sinister-snap-emu",
        motion_kind="pulse",
        palette=PROJECT_PALETTES["sinister-snap-emu"],
        glyphs=_GLYPHS_DEEP,
        motion_kwargs={"period_s": 1.9},
    ),
    "sinister-hieroglyphics": Entity(
        name="Glyph-scribe",
        project_key="sinister-hieroglyphics",
        motion_kind="drift",
        palette=PROJECT_PALETTES["sinister-hieroglyphics"],
        glyphs=_GLYPHS_ARCHIVE,
        motion_kwargs={"x_period_s": 19.0, "y_period_s": 23.0},
    ),
    "sinister-watcher": Entity(
        name="Veil-eye",
        project_key="sinister-watcher",
        motion_kind="orbit",
        palette=PROJECT_PALETTES["sinister-watcher"],
        glyphs=_GLYPHS_GROW,
        motion_kwargs={"radius": 0.5, "period_s": 13.0, "wobble": 0.06},
    ),
    "sinister-bumble": Entity(
        name="Pollen-rover",
        project_key="sinister-bumble",
        motion_kind="drift",
        palette=PROJECT_PALETTES["sinister-bumble"],
        glyphs=_GLYPHS_GROW,
        motion_kwargs={"x_period_s": 11.0, "y_period_s": 9.0},
    ),
    "eve-exe": Entity(
        name="EVE-conduit",
        project_key="eve-exe",
        motion_kind="orbit",
        palette=PROJECT_PALETTES["eve-exe"],
        glyphs=_GLYPHS_ORBITAL,
        motion_kwargs={"radius": 0.8, "period_s": 11.0, "wobble": 0.12},
    ),
    "eve-compliance": Entity(
        name="Auditor",
        project_key="eve-compliance",
        motion_kind="pulse",
        palette=PROJECT_PALETTES["eve-compliance"],
        glyphs=_GLYPHS_SPARK,
        motion_kwargs={"period_s": 2.2},
    ),
    "letstext": Entity(
        name="Whisper-net",
        project_key="letstext",
        motion_kind="drift",
        palette=PROJECT_PALETTES["letstext"],
        glyphs=_GLYPHS_GROW,
        motion_kwargs={"x_period_s": 13.0, "y_period_s": 17.0},
    ),
    "showmasters": Entity(
        name="Curtain-caller",
        project_key="showmasters",
        motion_kind="spiral",
        palette=PROJECT_PALETTES["showmasters"],
        glyphs=_GLYPHS_ARCHIVE,
        motion_kwargs={"period_s": 10.0, "growth": 0.7},
    ),
    "jb-woodworks": Entity(
        name="Grain-shaper",
        project_key="jb-woodworks",
        motion_kind="breathe",
        palette=PROJECT_PALETTES["jb-woodworks"],
        glyphs=_GLYPHS_DEEP,
        motion_kwargs={"inhale_s": 3.3, "exhale_s": 4.7},
    ),
}


def for_project(project_key: str | None) -> Entity:
    """Return the entity for a project key, falling back to Sanctum-master."""
    if not project_key:
        return ENTITIES["sinister-sanctum"]
    return ENTITIES.get(project_key, ENTITIES["sinister-sanctum"])


__all__ = ["Entity", "ENTITIES", "for_project", "DEFAULT_GLYPH_RAMP"]
