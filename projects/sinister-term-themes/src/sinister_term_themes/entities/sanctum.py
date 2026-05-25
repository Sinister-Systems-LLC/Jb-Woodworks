# Author: RKOJ-ELENO :: 2026-05-25
"""Sanctum entity — "The Seed".

Personality: the violet hub from which every other entity grew. Patient.
Concentric. Vast.

Idle palette: violet-core
High-energy palette: violet-core-burning
Rule: shimmer (hue rotates per frame); on high energy, the dot density also
rotates one position right.
"""

from __future__ import annotations

GLYPH: list[str] = [
    "        .   .       *  .  .       .       ",
    "     .       *           .     *           ",
    "   .    .::::SINISTER::::.     .           ",
    " *     ::                ::         *      ",
    " .   ::    o  E V E  o    ::    .          ",
    "   ::      \\  / | \\  /      ::             ",
    "    ::      \\/  |  \\/      ::      *       ",
    " .    ::    /\\  |  /\\    ::      .         ",
    "      ::  /    \\|/    \\  ::                ",
    "    *  ::::::::SANCTUM:::::::  *           ",
]


def definition() -> dict:
    return {
        "name": "The Seed",
        "project_key": "sanctum",
        "glyph": list(GLYPH),
        "idle_palette": "violet-core",
        "high_energy_palette": "violet-core-burning",
        "rule": "shimmer",
        "personality": (
            "The violet hub from which every other entity grew. "
            "Patient. Concentric. Vast."
        ),
    }
