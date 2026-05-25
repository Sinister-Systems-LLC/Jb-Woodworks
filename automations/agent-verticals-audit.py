# Author: RKOJ-ELENO :: 2026-05-25
"""agent-verticals-audit.py -- compile all available fleet verticals for a new agent.

Reads skills/_REGISTRY.yaml + skills/_INDEX.md and outputs a concise markdown
cross-reference of every shipped bot, candidate skill, pending tool, and scouted
external so the spawning agent can plan which verticals to use for its project setup.

Usage (called by start-sinister-session.ps1 Build-Phrase at scaffold + resume spawn):
  python automations/agent-verticals-audit.py --agent <slug> [--root <sanctum-root>]

Outputs one-line per vertical, collapsed to a single spawn-phrase-safe block.
Exit 0 always; errors are swallowed so spawn is never blocked.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml  # type: ignore
    _HAVE_YAML = True
except ImportError:
    _HAVE_YAML = False


def _default_root() -> Path:
    import os
    env = os.environ.get("SINISTER_SANCTUM_ROOT")
    if env:
        return Path(env)
    p = Path(r"D:\Sinister Sanctum")
    if p.exists():
        return p
    return Path.cwd()


def _load_registry(root: Path) -> dict:
    reg_path = root / "skills" / "_REGISTRY.yaml"
    if not reg_path.exists():
        return {}
    try:
        text = reg_path.read_text(encoding="utf-8", errors="replace")
        if _HAVE_YAML:
            return yaml.safe_load(text) or {}
        # Minimal YAML parse without PyYAML: extract name+status+description lines
        return {"_raw": text}
    except Exception:
        return {}


def _parse_registry_raw(text: str) -> list[dict]:
    """Fallback parser for _REGISTRY.yaml without PyYAML. Extracts name/slug/status/description."""
    items: list[dict] = []
    current: dict = {}
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- name:"):
            if current.get("name"):
                items.append(current)
            current = {"name": stripped[7:].strip().strip('"')}
        elif stripped.startswith("slug:") and current:
            current["slug"] = stripped[5:].strip().strip('"')
        elif stripped.startswith("status:") and current:
            current["status"] = stripped[7:].strip().strip('"').split("#")[0].strip()
        elif stripped.startswith("description:") and current:
            current["description"] = stripped[12:].strip().strip('"')
        elif stripped.startswith("kind:") and current:
            current["kind"] = stripped[5:].strip().strip('"')
        elif stripped.startswith("install_state:") and current:
            current["install_state"] = stripped[14:].strip().strip('"').split("#")[0].strip()
    if current.get("name"):
        items.append(current)
    return items


def _collect_items(registry: dict) -> list[dict]:
    if not registry:
        return []
    if "_raw" in registry:
        return _parse_registry_raw(registry["_raw"])
    items: list[dict] = []
    for section in ("bots", "tools", "skills", "externals", "inventions"):
        for entry in registry.get(section, []) or []:
            if isinstance(entry, dict):
                entry.setdefault("kind", section.rstrip("s"))
                items.append(entry)
    return items


def _format_block(items: list[dict], agent_slug: str) -> str:
    if not items:
        return "## Fleet Verticals\n_(registry not found)_\n"

    shipped_bots = [i for i in items if i.get("kind") in ("bot",) and i.get("status") == "shipped"]
    candidate_skills = [i for i in items if i.get("kind") == "skill" and i.get("status") == "candidate"]
    shipped_skills = [i for i in items if i.get("kind") == "skill" and i.get("status") == "shipped"]
    shipped_tools = [i for i in items if i.get("kind") == "tool" and i.get("status") == "shipped"]
    pending_tools = [i for i in items if i.get("kind") == "tool" and i.get("status") in ("building", "pending", "scouted")]
    scouted_ext = [i for i in items if i.get("kind") == "external" and i.get("status") in ("scouted", "shipped")]

    lines: list[str] = [f"## Fleet Verticals audit for {agent_slug} (2026-05-25)\n"]

    def _row(item: dict) -> str:
        slug = item.get("slug") or item.get("name", "?")
        desc = item.get("description", "")
        if len(desc) > 90:
            desc = desc[:87] + "..."
        install = item.get("install_state", "")
        tag = f" [{install}]" if install and install not in ("registered", "not-applicable") else ""
        return f"  - {slug}: {desc}{tag}"

    if shipped_bots:
        lines.append("### Shipped bots (free, always available)")
        lines.extend(_row(i) for i in shipped_bots)
    if shipped_skills:
        lines.append("### Shipped skills (usable now)")
        lines.extend(_row(i) for i in shipped_skills)
    if shipped_tools:
        lines.append("### Shipped tools")
        lines.extend(_row(i) for i in shipped_tools)
    if candidate_skills:
        lines.append("### Candidate skills (Ruflo-backed; pending operator thumb)")
        for i in candidate_skills:
            slug = i.get("slug") or i.get("name", "?")
            desc = i.get("description", "")
            if len(desc) > 90:
                desc = desc[:87] + "..."
            lines.append(f"  - {slug}: {desc} [case-study at _shared-memory/case-studies/2026-05-19-{slug}.md]")
    if pending_tools:
        lines.append("### Pending/building tools (need activation)")
        lines.extend(_row(i) for i in pending_tools)
    if scouted_ext:
        lines.append("### Scouted externals")
        lines.extend(_row(i) for i in scouted_ext[:5])  # cap at 5

    lines.append("\nAudit complete. Cross-reference the above, pick relevant verticals, and create a plan in _shared-memory/plans/ before coding.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compile fleet verticals cross-reference for a spawning agent.")
    parser.add_argument("--agent", default="unknown", help="Agent slug being spawned")
    parser.add_argument("--root", type=Path, default=None, help="Sanctum root")
    parser.add_argument("--inline", action="store_true", help="Output spawn-phrase-safe single line instead of full markdown")
    args = parser.parse_args(argv)

    root = args.root or _default_root()
    registry = _load_registry(root)
    items = _collect_items(registry)
    block = _format_block(items, args.agent)

    if args.inline:
        # Collapse to single line for embedding in the spawn phrase
        one = block.replace("\n", " | ").replace("  - ", "").replace("## ", "").replace("### ", "[").replace(": [", ":[")
        # Remove double pipes
        import re
        one = re.sub(r"\s*\|\s*\|+\s*", " | ", one)
        if len(one) > 900:
            one = one[:897] + "..."
        print(one)
    else:
        print(block)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
