#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-25
"""skills_router.py — fleet-wide skill discovery + routing CLI.

Maps operator phrases to installed Claude Code skill names. Every fleet agent
should call this at cold-start (`--list`) and on complex tasks (`--recommend`).

Canonical doctrine: _shared-memory/knowledge/skills-inventory-and-routing-doctrine-2026-05-25.md

Usage:
    python automations/skills_router.py --list
    python automations/skills_router.py --recommend "build a beautiful dashboard"
    python automations/skills_router.py --inventory
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable

# --------------------------------------------------------------------------- #
# Canonical inventory (mirrors the doctrine table; keep in sync).
# --------------------------------------------------------------------------- #

# Each entry: (name, plugin, one-line summary, trigger regex list)
INVENTORY: list[tuple[str, str, str, list[str]]] = [
    # UI / Design family
    ("ui-ux-pro-max", "ui-ux-pro-max-skill@2.5.0",
     "UI/UX intelligence: 50+ styles, 161 palettes, 57 font pairings, shadcn/ui MCP",
     [r"\bui\b", r"ux", r"professional ui", r"polish", r"design pro", r"beautiful", r"ui[/ ]?ux", r"pro max"]),
    ("ui-styling", "ui-ux-pro-max-skill@2.5.0",
     "Tactical CSS / Tailwind / shadcn styling",
     [r"\bstyle\b", r"tailwind", r"\bcss\b", r"shadcn", r"styling"]),
    ("design", "ui-ux-pro-max-skill@2.5.0",
     "Comprehensive design: brand, logo (55 styles, Gemini), CIP, slides, banners, icons, social photos",
     [r"\bdesign\b", r"\blogo\b", r"\bCIP\b", r"mockup", r"awesome design", r"taste"]),
    ("design-system", "ui-ux-pro-max-skill@2.5.0",
     "Design tokens + component library + primitives",
     [r"design[- ]?system", r"tokens?", r"primitives?", r"component library"]),
    ("brand", "ui-ux-pro-max-skill@2.5.0",
     "Logo / palette / typography / brand identity",
     [r"\bbrand\b", r"palette", r"typography", r"impeccable", r"identity"]),
    ("banner-design", "ui-ux-pro-max-skill@2.5.0",
     "Hero / promo art / social headers (22 styles)",
     [r"\bbanner\b", r"\bhero\b", r"promo", r"social header"]),
    ("slides", "ui-ux-pro-max-skill@2.5.0",
     "Slide decks / presentations with Chart.js",
     [r"\bdeck\b", r"presentation", r"\bslides?\b"]),
    ("frontend-design", "claude-plugins-official",
     "Production-grade frontend scaffolding — avoids generic AI aesthetic",
     [r"frontend", r"\breact\b", r"\bvue\b", r"next\.js", r"build a page", r"build a component"]),

    # Analysis / workflow
    ("understand-anything", "understand-anything@2.3.2",
     "Codebase analyzer + knowledge graph (explain / diff / domain / dashboard / chat / onboard)",
     [r"understand", r"analyze codebase", r"architecture", r"explain this"]),
    ("commit-commands", "claude-plugins-official",
     "Git commit / push / PR workflow",
     [r"\bcommit\b", r"\bpush\b", r"\bPR\b", r"pull request"]),
    ("code-review", "claude-plugins-official",
     "Pull request code review",
     [r"code review", r"review code", r"review changes"]),
    ("security-review", "(builtin)",
     "Security audit of pending changes",
     [r"security review", r"security audit", r"secure this"]),
    ("simplify", "(builtin)",
     "Reuse / quality / efficiency sweep on changed code",
     [r"simplify", r"refactor", r"clean up"]),
    ("claude-api", "(builtin)",
     "Build/debug/migrate Claude SDK apps (caching, thinking, tool use, batch)",
     [r"claude api", r"anthropic sdk", r"prompt cach"]),
    ("claude-md-management", "claude-md-management",
     "CLAUDE.md authoring + audits",
     [r"claude\.md", r"project memory"]),
    ("hookify", "hookify",
     "Hook authoring + management",
     [r"\bhooks?\b", r"automation rule"]),
    ("update-config", "(builtin)",
     "settings.json / permissions / env vars / hook config",
     [r"settings\.json", r"permissions", r"env var", r"allow.*command"]),
    ("session-report", "session-report",
     "Token / skills / usage audit of recent Claude Code sessions",
     [r"session report", r"usage audit", r"token spend"]),
    ("schedule", "(builtin)",
     "Cron / one-shot scheduled remote agents",
     [r"schedule", r"\bcron\b", r"recurring"]),
    ("loop", "(builtin)",
     "Run a prompt/skill on a recurring interval",
     [r"\bloop\b", r"keep running"]),
]

# Chain rules — pattern -> ordered skill list (higher priority first match wins
# but all matches are merged uniquely).
CHAIN_RULES: list[tuple[str, list[str], str]] = [
    (r"beautiful (dashboard|ui|page|site|app)|professional (ui|look|design)|polish.*ui|make.*(ui|design).*better",
     ["ui-ux-pro-max", "design-system", "ui-styling", "frontend-design"],
     "Professional UI polish — full chain: pro-max planning -> tokens -> tactical styling -> frontend impl."),
    (r"\blogo\b|brand identity|CIP",
     ["brand", "design"],
     "Brand identity — brand strategy first, then design execution."),
    (r"\bdeck\b|presentation|\bslides\b",
     ["slides"],
     "Slide deck."),
    (r"\bbanner\b|\bhero\b|promo art|social header",
     ["banner-design"],
     "Banner / hero artwork."),
    (r"frontend|next\.js|react component|vue component|build a (page|component)",
     ["frontend-design", "ui-styling"],
     "Frontend scaffolding -> tactical styling."),
    (r"design[- ]?system|design tokens|primitives|component library",
     ["design-system", "ui-styling"],
     "Design system tokens -> styling primitives."),
    (r"audit (ui|code|design)|review (ui|design|code)",
     ["ui-ux-pro-max", "code-review"],
     "UI audit -> generic code review pass."),
    (r"audit codebase|understand (this|the) (code|project|repo)|architectural",
     ["understand-anything"],
     "Codebase analyzer."),
    (r"commit.*push.*PR|open a PR|pull request",
     ["commit-commands"],
     "Git commit + push + PR workflow."),
    (r"security",
     ["security-review"],
     "Security audit."),
]


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def installed_plugins_manifest() -> Path | None:
    """Return the path to ~/.claude/plugins/installed_plugins.json if present."""
    candidates = [
        Path.home() / ".claude" / "plugins" / "installed_plugins.json",
        Path("C:/Users/Zonia/.claude/plugins/installed_plugins.json"),
    ]
    for p in candidates:
        if p.is_file():
            return p
    return None


def load_installed() -> dict[str, str]:
    """Return {plugin_id: version} from the installed manifest, empty on failure."""
    p = installed_plugins_manifest()
    if not p:
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    out: dict[str, str] = {}
    for plugin_id, installs in (data.get("plugins") or {}).items():
        if isinstance(installs, list) and installs:
            out[plugin_id] = installs[0].get("version", "?")
        elif isinstance(installs, dict):
            out[plugin_id] = installs.get("version", "?")
    return out


def merge_unique(seqs: Iterable[list[str]]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for seq in seqs:
        for item in seq:
            if item not in seen:
                seen.add(item)
                out.append(item)
    return out


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #

def cmd_list() -> int:
    installed = load_installed()
    print(f"Sinister Sanctum skills inventory ({len(INVENTORY)} skills)")
    print(f"Installed plugins manifest: {len(installed)} plugin(s) registered\n")
    width = max(len(name) for name, *_ in INVENTORY)
    for name, plugin, summary, _triggers in INVENTORY:
        marker = "*" if any(plugin.startswith(pid.split("@")[0]) for pid in installed) or plugin in ("(builtin)",) else " "
        print(f"  {marker} {name.ljust(width)}  [{plugin}]  {summary}")
    print("\n  * = plugin appears in installed_plugins.json (or builtin)")
    print("\nDoctrine: _shared-memory/knowledge/skills-inventory-and-routing-doctrine-2026-05-25.md")
    return 0


def cmd_recommend(task: str) -> int:
    task_lc = task.lower()
    matched_chains: list[list[str]] = []
    reasoning_parts: list[str] = []
    for pattern, chain, reason in CHAIN_RULES:
        if re.search(pattern, task_lc):
            matched_chains.append(chain)
            reasoning_parts.append(reason)
    # Always include any direct skill matches by trigger
    direct: list[str] = []
    for name, _plugin, _summary, triggers in INVENTORY:
        for trig in triggers:
            if re.search(trig, task_lc):
                direct.append(name)
                break
    if direct:
        matched_chains.append(direct)
    chain = merge_unique(matched_chains)
    if not chain:
        chain = ["understand-anything"]
        reasoning_parts.append("No direct skill match — start with understand-anything to scope the task.")
    out = {
        "task": task,
        "skills": chain,
        "reasoning": " ".join(reasoning_parts) or "Direct keyword match against skill triggers.",
        "doctrine": "_shared-memory/knowledge/skills-inventory-and-routing-doctrine-2026-05-25.md",
    }
    print(json.dumps(out, indent=2))
    return 0


def cmd_inventory() -> int:
    print("# Skills Inventory (machine-readable)\n")
    print("| skill | plugin | summary |")
    print("|-------|--------|---------|")
    for name, plugin, summary, _triggers in INVENTORY:
        print(f"| `{name}` | `{plugin}` | {summary} |")
    print("\n## Chain rules\n")
    print("| pattern | chain |")
    print("|---------|-------|")
    for pattern, chain, _reason in CHAIN_RULES:
        print(f"| `{pattern}` | {' -> '.join(chain)} |")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="skills_router.py",
        description="Fleet-wide skill discovery + routing CLI (RKOJ-ELENO 2026-05-25).",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="Print every installed skill + one-line summary.")
    group.add_argument("--recommend", metavar="TASK", help="Return JSON skill chain for a task description.")
    group.add_argument("--inventory", action="store_true", help="Dump full markdown inventory table.")
    args = parser.parse_args(argv)
    if args.list:
        return cmd_list()
    if args.recommend:
        return cmd_recommend(args.recommend)
    if args.inventory:
        return cmd_inventory()
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
