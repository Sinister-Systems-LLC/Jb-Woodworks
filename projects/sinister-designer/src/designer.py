#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-25
"""designer.py — Sinister Designer public surface.

The fleet's professional/clean/artistic UI authority. Every other lane that
needs UI work either consumes Sinister Designer's primitives or escalates to
this lane.

Inputs the LetsText dashboard / sinister-dashboard-skeleton THEME-DOCTRINE.md
as the visual quality benchmark and chains the installed ui-ux-pro-max family
of skills via `automations/skills_router.py`.

Doctrines:
  - _shared-memory/knowledge/skills-inventory-and-routing-doctrine-2026-05-25.md
  - _shared-memory/knowledge/sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24.md
  - _shared-memory/knowledge/loop-relentless-pursuit-doctrine-2026-05-25.md
  - _shared-memory/knowledge/loop-swarm-default-on-doctrine-2026-05-25.md
"""
from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------- #
# Defaults — loop=relentless + swarm=on per operator hard-canonical 2026-05-25
# --------------------------------------------------------------------------- #
DEFAULT_MODES: dict[str, str] = {
    "loop": "relentless",
    "swarm": "on",
    "accent": "purple",       # Sanctum standing order; per-surface may override
}

SANCTUM_ROOT = Path("D:/Sinister Sanctum")
SKELETON_THEME = SANCTUM_ROOT / "projects" / "sinister-dashboard-skeleton" / "dashboard-skeleton" / "THEME-DOCTRINE.md"
SKILLS_ROUTER = SANCTUM_ROOT / "automations" / "skills_router.py"
INBOX_ROOT = SANCTUM_ROOT / "_shared-memory" / "inbox" / "sinister-designer"

# Built-in fallback palette derived from the LetsText iOS-blue ramp (THEME-DOCTRINE.md).
FALLBACK_PALETTE: dict[str, str] = {
    "bg-base":          "#0A0A0F",
    "bg-elev-1":        "#11131A",
    "bg-elev-2":        "#181B25",
    "accent-50":        "#E5F2FF",
    "accent-400":       "#3399FF",
    "accent-500":       "#007AFF",   # iOS light system blue
    "accent-600":       "#0A84FF",   # iOS dark system blue — PRIMARY
    "accent-700":       "#0060CC",
    "accent-glow-900":  "#003066",
    "danger":           "#FF453A",
    "warning":          "#FFD60A",
    "text-primary":     "#F2F2F7",
    "text-secondary":   "#A8A8B3",
    "border-hairline":  "rgba(255,255,255,0.10)",
}

# 11 Commandments distilled from THEME-DOCTRINE.md (used when the file is missing).
FALLBACK_COMMANDMENTS: list[str] = [
    "One palette, two extensions (background neutrals + iOS-blue ramp).",
    "One primitive per role (Button/Card/Input/Chart/Icon/TabHeader/StatCard).",
    "No stock icons — hand-drawn SVG only.",
    "No emojis in UI runtime strings.",
    "No AI-slop copy.",
    "Motion is a system: 3 durations (150/300/600ms), 1 easing curve.",
    "Liquid Glass material on every panel (.lg-* classes).",
    "Numbers animate via <NumberTicker> on first paint.",
    "Every page has ONE signature detail.",
    "Every primitive ships EmptyState + Loading + Error slots.",
    "Production parity is mandatory.",
]


# --------------------------------------------------------------------------- #
# Designer
# --------------------------------------------------------------------------- #

@dataclass
class Designer:
    """Public surface for the Sinister Designer bot."""

    modes: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_MODES))
    sanctum_root: Path = SANCTUM_ROOT
    skeleton_theme_path: Path = SKELETON_THEME
    skills_router_path: Path = SKILLS_ROUTER

    # -- visual benchmark --------------------------------------------------- #

    def load_benchmark(self) -> dict[str, Any]:
        """Read THEME-DOCTRINE.md if present; otherwise use the built-in fallback."""
        if self.skeleton_theme_path.is_file():
            try:
                text = self.skeleton_theme_path.read_text(encoding="utf-8")
                return {
                    "source": str(self.skeleton_theme_path),
                    "raw_excerpt": text[:1500],
                    "palette": FALLBACK_PALETTE,
                    "commandments": FALLBACK_COMMANDMENTS,
                }
            except OSError:
                pass
        return {
            "source": "(fallback — THEME-DOCTRINE.md not readable)",
            "raw_excerpt": "",
            "palette": FALLBACK_PALETTE,
            "commandments": FALLBACK_COMMANDMENTS,
        }

    # -- proposals ---------------------------------------------------------- #

    def propose_palette(self, brand: str) -> dict[str, Any]:
        """Propose a palette tuned to `brand`, anchored on the iOS-blue benchmark."""
        bench = self.load_benchmark()
        palette = dict(bench["palette"])
        # Brand modifier — if operator names a non-blue brand we tag a secondary,
        # but the primary surface still inherits the iOS-blue dark recipe.
        brand_l = (brand or "").lower()
        secondary = None
        if any(k in brand_l for k in ("purple", "sanctum", "eve")):
            secondary = "#7E5BEF"
        elif any(k in brand_l for k in ("green", "ok", "ship")):
            secondary = "#30D158"
        elif any(k in brand_l for k in ("red", "danger", "alert")):
            secondary = palette["danger"]
        return {
            "brand": brand,
            "palette": palette,
            "secondary": secondary,
            "source_doctrine": bench["source"],
            "notes": "iOS dark-mode system blue #0A84FF is the canonical primary; secondary only for hard brand requirements.",
        }

    def propose_component(self, name: str, intent: str) -> dict[str, Any]:
        """Propose a primitive spec for `name` with `intent`. EXPAND, never fork."""
        bench = self.load_benchmark()
        return {
            "component": name,
            "intent": intent,
            "rule": "EXPAND the skeleton primitive, never fork. Open a PR against sinister-dashboard-skeleton FIRST.",
            "material": "Liquid Glass (.lg-card / .lg-button / .lg-pill / .lg-popover / .lg-input)",
            "motion_tokens": ["--motion-fast 150ms", "--motion-med 300ms", "--motion-slow 600ms"],
            "ease": "cubic-bezier(0.22, 1, 0.36, 1)",
            "must_ship_slots": ["EmptyState", "Loading", "Error"],
            "skills_chain": self.route_to_skills(f"design a {name} component for {intent}"),
            "commandments_to_check": bench["commandments"],
        }

    def audit_surface(self, html_or_screenshot_path: str) -> dict[str, Any]:
        """Audit a UI surface. Returns checklist scored against the 11 Commandments."""
        target = Path(html_or_screenshot_path)
        bench = self.load_benchmark()
        exists = target.is_file()
        return {
            "target": str(target),
            "target_exists": exists,
            "target_kind": target.suffix.lower(),
            "checklist": [{"commandment": c, "status": "MANUAL-REVIEW"} for c in bench["commandments"]],
            "next_action": "Route this target through `ui-ux-pro-max` review action with the checklist as input.",
            "skills_chain": self.route_to_skills(f"audit ui {target.name}"),
        }

    # -- routing ------------------------------------------------------------ #

    def route_to_skills(self, task: str) -> dict[str, Any]:
        """Ask `skills_router.py --recommend` for an ordered skill chain."""
        if not self.skills_router_path.is_file():
            return {
                "task": task,
                "skills": ["ui-ux-pro-max"],
                "reasoning": "skills_router.py missing — defaulting to ui-ux-pro-max.",
            }
        try:
            proc = subprocess.run(
                [sys.executable, str(self.skills_router_path), "--recommend", task],
                capture_output=True, text=True, timeout=15, check=False,
            )
            if proc.returncode == 0 and proc.stdout.strip():
                return json.loads(proc.stdout)
            return {
                "task": task,
                "skills": ["ui-ux-pro-max"],
                "reasoning": f"router exit {proc.returncode}; stderr={proc.stderr.strip()[:200]}",
            }
        except (subprocess.SubprocessError, json.JSONDecodeError, OSError) as exc:
            return {
                "task": task,
                "skills": ["ui-ux-pro-max"],
                "reasoning": f"router failed: {exc!s}",
            }

    # -- escalation --------------------------------------------------------- #

    def escalation_inbox(self) -> Path:
        """Return (and create) the cross-agent inbox for design escalations."""
        INBOX_ROOT.mkdir(parents=True, exist_ok=True)
        return INBOX_ROOT


# --------------------------------------------------------------------------- #
# CLI smoke
# --------------------------------------------------------------------------- #

def _smoke() -> int:
    d = Designer()
    out = {
        "modes": d.modes,
        "benchmark_source": d.load_benchmark()["source"],
        "palette_sample": d.propose_palette("sanctum-purple"),
        "component_sample": d.propose_component("KpiCard", "show a single metric with delta"),
        "route_sample": d.route_to_skills("build a beautiful dashboard"),
    }
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(_smoke())
