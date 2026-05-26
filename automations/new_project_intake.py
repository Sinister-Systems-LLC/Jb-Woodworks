#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-26
"""
new_project_intake.py -- canonical "operator-idea -> shipped-plan" intake pipeline.

OPERATOR HARD-CANONICAL 2026-05-26 (verbatim):
  "make sure each new project takes my idea. deeply reviews it with all knowledge
   we have prior and then does alot of github research to look for repos that
   have code we can use to get it working. then complie all that and see where
   we can make things better and do things better based on all that knowledge.
   then we create plan and get to work. this needs to be flow when i create
   project in eve or if i tell any agent in the network to do this."

PIPELINE (6 stages):

  Stage 1 -- INTAKE
    Operator drops a `<project-key>.idea.md` into projects/<key>/ OR passes the
    raw idea via --idea-text. The CLI ingests it, captures timestamp + slug.

  Stage 2 -- PRIOR-KNOWLEDGE REVIEW (sinister-bus + Ruflo MCP + sinister-memory)
    Compose:
      forge-memory recall '<keywords>' --limit 10        (disk-stored memories)
      grep _shared-memory/knowledge/ for adjacent doctrine
      ls projects/ for adjacent lanes
      grep tools/_INDEX.md + inventions/ for re-usable assets
    Output: prior-knowledge-review.md with adjacent assets + relevant doctrine.

  Stage 3 -- GITHUB RESEARCH (parallel via sinister_swarm.py)
    Fan out 3-5 sub-agents (capped by sinister_swarm.py MAX_SLICES=5) each running
    a different GitHub query strategy:
      - topic search (gh search repos topic:<topic>)
      - language+star search (gh search repos language:<lang> stars:>500)
      - awesome-list crawl (well-curated meta-lists)
      - issue-pattern search (find others solving same problem in issues)
      - keyword search (specific terms from operator idea)
    Each agent writes findings to vault/github-research/<utc>/<slice>.md.

  Stage 4 -- COMPILE + IMPROVE (synthesis)
    Master reads all per-slice findings + the prior-knowledge review. Writes:
      improvements.md  -- where each found repo would help vs adjacent Sanctum asset
      gaps.md          -- where no existing repo covers it (we innovate)
      anti-patterns.md -- what NOT to copy (failures, dead projects, license issues)

  Stage 5 -- PLAN
    Writes _shared-memory/plans/<project-key>-master-<utc>/plan.md with:
      P0 (this iter) | P1 (next 3 iters) | P2 (backlog) milestone breakdown.
      Each item: file_path + acceptance_criteria + smoke_command + composes_with.

  Stage 6 -- SHIP
    Auto-creates project dir scaffold (CLAUDE.md from template + branch_prefix +
    projects.json entry + minimal pytest dir if Python). Then optionally spawns
    a fresh agent on the new project key via start-sinister-session.ps1.

COMPOSES WITH:
  - we-have-the-source-read-it-doctrine-2026-05-25  (Stage 2 reads source directly)
  - github-first-sourcing-doctrine-2026-05-24       (Stage 3 IS the canonical impl)
  - full-relentless-swarm-fanout-mindset-2026-05-25 (Stage 3 fan-out)
  - no-bullshit-tested-before-claimed-2026-05-23    (Stage 5 plan includes smoke per item)
  - sanctum-scope-discipline-2026-05-24             (sanctum master owns this entrypoint)
  - automate-everything-no-operator-admin-2026-05-25 (operator clicks zero buttons)
  - no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25  (Python over .ps1)

INVOCATION:
  python automations/new_project_intake.py --project-key sinister-foo --idea-file projects/sinister-foo/sinister-foo.idea.md
  python automations/new_project_intake.py --project-key sinister-foo --idea-text "EVE for distributed grocery lists; encrypted; tailscale-only"

  Stages can be run individually for debugging:
  python automations/new_project_intake.py --stage prior-knowledge --project-key sinister-foo
  python automations/new_project_intake.py --stage github-research --project-key sinister-foo
  python automations/new_project_intake.py --stage compile --project-key sinister-foo
  python automations/new_project_intake.py --stage plan --project-key sinister-foo
  python automations/new_project_intake.py --stage ship --project-key sinister-foo

OPERATOR ENTRYPOINTS (per "this needs to be flow when i create project in eve"):
  1. EVE.exe new-project picker calls this CLI.
  2. Any agent receiving an operator utterance tagged 'new-project' calls this.
  3. CLAUDE.md cold-start step adds an "if you spawn with NEW_PROJECT_KEY env var,
     run new_project_intake.py first" gate.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

SANCTUM_ROOT = Path(os.environ.get("SINISTER_SANCTUM_ROOT", r"D:\Sinister Sanctum"))
PROJECTS_DIR = SANCTUM_ROOT / "projects"
KNOWLEDGE_DIR = SANCTUM_ROOT / "_shared-memory" / "knowledge"
PLANS_DIR = SANCTUM_ROOT / "_shared-memory" / "plans"
SWARM_CLI = SANCTUM_ROOT / "automations" / "sinister_swarm.py"
FORGE_MEMORY_BIN = "forge-memory"  # in PATH per project doctrine


def _utc_stamp() -> str:
    return time.strftime("%Y-%m-%dT%H%M%SZ", time.gmtime())


def _ensure_dir(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p


def _project_dir(key: str) -> Path:
    return PROJECTS_DIR / key


def _project_vault(key: str) -> Path:
    return _project_dir(key) / "vault" / "intake"


def _safe_run(cmd: list[str], timeout: int = 30, cwd: Path | None = None) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            cwd=str(cwd) if cwd else None,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    except Exception as exc:
        return 1, "", str(exc)


# -----------------------------------------------------------------------------
# Stage 1 -- INTAKE
# -----------------------------------------------------------------------------
def stage_intake(key: str, idea_text: str | None, idea_file: Path | None) -> Path:
    """Capture the operator idea + write canonical intake.md to project vault."""
    pdir = _ensure_dir(_project_dir(key))
    vault = _ensure_dir(_project_vault(key))
    intake_path = vault / "intake.md"

    if idea_file and idea_file.exists():
        idea = idea_file.read_text(encoding="utf-8")
    elif idea_text:
        idea = idea_text
    else:
        raise ValueError("provide --idea-text OR --idea-file")

    stamp = _utc_stamp()
    out = (
        f"# {key} :: Operator Idea Intake\n\n"
        f"**Captured:** {stamp}\n\n"
        f"**Project key:** `{key}`\n\n"
        f"**Branch prefix:** `agent/{key}/`\n\n"
        f"---\n\n"
        f"## Raw operator idea (verbatim)\n\n"
        f"{idea}\n"
    )
    intake_path.write_text(out, encoding="utf-8")
    print(f"[stage-1 intake] {intake_path}")
    return intake_path


# -----------------------------------------------------------------------------
# Stage 2 -- PRIOR-KNOWLEDGE REVIEW
# -----------------------------------------------------------------------------
def _extract_keywords(text: str, max_keywords: int = 8) -> list[str]:
    """Strip stopwords + return the top tokens (5+ chars) by frequency."""
    stop = {
        "the","and","for","with","this","that","have","from","they","them","will",
        "what","make","need","want","your","also","just","like","keep","more","only",
        "when","then","than","some","here","there","where","which","how","our",
        "are","was","were","has","had","its","to","of","in","on","at","as",
        "be","is","an","a","i","we","you","my","do","if","or","no","yes","so",
        "all","any","can","use","add","get","set","fix","run","let","out","off",
        "now","one","two","too","but","not","based","prior","compile","things",
        "agents","reviews","review","knowledge","github","research","look","plan",
        "flow","each","again","ideas","using","working","getting","create",
    }
    clean = re.sub(r"[^a-z0-9\s\-_]", " ", text.lower())
    words = [w for w in clean.split() if len(w) >= 5 and w not in stop]
    freq: dict[str, int] = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    return [w for w, _ in sorted(freq.items(), key=lambda kv: -kv[1])[:max_keywords]]


def stage_prior_knowledge(key: str) -> Path:
    """Compose forge-memory recall + brain grep + project list into prior-knowledge-review.md."""
    vault = _ensure_dir(_project_vault(key))
    intake = (vault / "intake.md").read_text(encoding="utf-8") if (vault / "intake.md").exists() else ""
    if not intake:
        raise FileNotFoundError(f"intake.md missing for {key}; run --stage intake first")

    keywords = _extract_keywords(intake, max_keywords=8)
    lines = [
        f"# {key} :: Prior Knowledge Review",
        f"\n**Generated:** {_utc_stamp()}\n",
        f"\n**Keywords extracted:** {', '.join(keywords) or '(none)'}\n",
        "\n---\n",
        "\n## Section 1 -- forge-memory recall (disk-stored memories)\n",
    ]

    # forge-memory recall (best-effort; never fail the pipeline)
    for kw in keywords[:4]:
        rc, out, _ = _safe_run([FORGE_MEMORY_BIN, "recall", kw, "--limit", "3"], timeout=10)
        if rc == 0 and out.strip():
            lines.append(f"\n### recall: `{kw}`\n")
            lines.append("```\n" + out.strip() + "\n```\n")

    # Brain entry grep
    lines.append("\n## Section 2 -- Adjacent brain entries (`_shared-memory/knowledge/`)\n")
    if KNOWLEDGE_DIR.exists():
        hits: set[str] = set()
        for md in KNOWLEDGE_DIR.glob("*.md"):
            try:
                content = md.read_text(encoding="utf-8", errors="ignore").lower()
                if any(kw in content for kw in keywords):
                    hits.add(md.name)
            except Exception:
                continue
        for h in sorted(hits)[:15]:
            lines.append(f"- `_shared-memory/knowledge/{h}`")

    # Adjacent project list
    lines.append("\n\n## Section 3 -- Adjacent projects (`projects/`)\n")
    if PROJECTS_DIR.exists():
        adj_hits: list[str] = []
        for sub in sorted(PROJECTS_DIR.iterdir()):
            if not sub.is_dir():
                continue
            name_low = sub.name.lower()
            if any(kw in name_low for kw in keywords):
                adj_hits.append(sub.name)
        for n in adj_hits[:10]:
            lines.append(f"- `projects/{n}/`")

    # tools/_INDEX.md + inventions list (lightweight)
    lines.append("\n\n## Section 4 -- Re-usable Sanctum assets\n")
    tools_idx = SANCTUM_ROOT / "tools" / "_INDEX.md"
    if tools_idx.exists():
        lines.append(f"- tools index: `tools/_INDEX.md` (check before re-implementing)")
    inv_dir = SANCTUM_ROOT / "inventions"
    if inv_dir.exists():
        lines.append(f"- inventions catalog: `inventions/` ({len(list(inv_dir.iterdir()))} entries)")

    out_path = vault / "prior-knowledge-review.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[stage-2 prior-knowledge] {out_path}")
    return out_path


# -----------------------------------------------------------------------------
# Stage 3 -- GITHUB RESEARCH (fan-out via sinister_swarm)
# -----------------------------------------------------------------------------
def stage_github_research(key: str, dry_run: bool = False) -> Path:
    """Build slices JSON + invoke sinister_swarm.py fanout for parallel GH research."""
    vault = _ensure_dir(_project_vault(key))
    research_dir = _ensure_dir(vault / "github-research" / _utc_stamp())

    intake = (vault / "intake.md").read_text(encoding="utf-8")
    keywords = _extract_keywords(intake, max_keywords=5)
    primary = " ".join(keywords[:3]) or key

    slices = [
        {
            "id": "topic-search",
            "prompt": (
                f"Run: gh search repos --topic '{primary}' --limit 20 --json name,description,stargazerCount,url. "
                f"Write top-10 hits to {research_dir / 'topic-search.md'} with one paragraph per repo (pitch + 3-line code-reuse opportunity for project '{key}')."
            ),
            "owned_paths": [str(research_dir / "topic-search.md")],
            "lane": "general",
        },
        {
            "id": "lang-stars-search",
            "prompt": (
                f"Run: gh search repos '{primary}' --stars '>500' --limit 20 --json name,description,stargazerCount,language,url. "
                f"Write top-10 by stars to {research_dir / 'lang-stars-search.md'} with pitch + code-reuse opportunity for project '{key}'."
            ),
            "owned_paths": [str(research_dir / "lang-stars-search.md")],
            "lane": "general",
        },
        {
            "id": "awesome-list-crawl",
            "prompt": (
                f"Run: gh search repos 'awesome {primary}' --limit 5 --json name,description,url. "
                f"For each, fetch README and extract direct project links (curl raw README). Write 8-12 best leads to {research_dir / 'awesome-list-crawl.md'}."
            ),
            "owned_paths": [str(research_dir / "awesome-list-crawl.md")],
            "lane": "general",
        },
        {
            "id": "issue-pattern-search",
            "prompt": (
                f"Run: gh search issues '{primary}' --state closed --limit 30. Look for closed issues solving the same problem. "
                f"Write best 5 to {research_dir / 'issue-pattern-search.md'} (issue link + solution summary + applicability to '{key}')."
            ),
            "owned_paths": [str(research_dir / "issue-pattern-search.md")],
            "lane": "general",
        },
        {
            "id": "keyword-deep-search",
            "prompt": (
                f"Run: gh search code '{primary}' --limit 30 --json repository,path,textMatches. "
                f"Write top-5 code matches to {research_dir / 'keyword-deep-search.md'} (repo+path+excerpt+applicability to '{key}')."
            ),
            "owned_paths": [str(research_dir / "keyword-deep-search.md")],
            "lane": "general",
        },
    ]

    slices_file = research_dir / "_slices.json"
    slices_file.write_text(json.dumps(slices, indent=2), encoding="utf-8")
    print(f"[stage-3 github-research] slices file: {slices_file}")

    if dry_run:
        print(f"[stage-3 github-research] --dry-run: NOT invoking sinister_swarm fanout")
        return research_dir

    cmd = [
        "python", str(SWARM_CLI), "fanout",
        "--slug-prefix", f"{key}-gh-research-{_utc_stamp()}",
        "--slices-file", str(slices_file),
        "--timeout-s", "900",
    ]
    print(f"[stage-3 github-research] invoking: {' '.join(cmd)}")
    rc, out, err = _safe_run(cmd, timeout=1000)
    (research_dir / "_swarm-out.txt").write_text(out + "\n---STDERR---\n" + err, encoding="utf-8")
    if rc != 0:
        print(f"[stage-3] swarm exit={rc}; see _swarm-out.txt", file=sys.stderr)
    return research_dir


# -----------------------------------------------------------------------------
# Stage 4 -- COMPILE + IMPROVE
# -----------------------------------------------------------------------------
def stage_compile(key: str) -> Path:
    """Synthesize per-slice findings into improvements.md + gaps.md + anti-patterns.md."""
    vault = _ensure_dir(_project_vault(key))
    research_root = vault / "github-research"
    if not research_root.exists():
        raise FileNotFoundError(f"no github-research/ for {key}; run --stage github-research first")
    latest = sorted(research_root.iterdir())[-1] if list(research_root.iterdir()) else None
    if not latest:
        raise FileNotFoundError(f"empty github-research/ for {key}")

    findings = []
    for md in sorted(latest.glob("*.md")):
        if md.name.startswith("_"):
            continue
        findings.append(f"\n### From `{md.name}`\n")
        findings.append(md.read_text(encoding="utf-8", errors="ignore"))

    out_md = vault / "compile-improvements.md"
    out_md.write_text(
        f"# {key} :: Compile + Improvements\n\n"
        f"**Generated:** {_utc_stamp()}\n\n"
        f"**Synthesis input:** {len(list(latest.glob('*.md')))} per-slice .md files from `{latest.name}`.\n\n"
        f"## Raw per-slice findings (operator + master review before promoting to plan)\n"
        + "\n".join(findings),
        encoding="utf-8",
    )
    print(f"[stage-4 compile] {out_md}")
    return out_md


# -----------------------------------------------------------------------------
# Stage 5 -- PLAN
# -----------------------------------------------------------------------------
def stage_plan(key: str) -> Path:
    """Emit _shared-memory/plans/<key>-master-<utc>/plan.md with P0/P1/P2."""
    plan_dir = _ensure_dir(PLANS_DIR / f"{key}-master-{_utc_stamp()}")
    plan_md = plan_dir / "plan.md"
    plan_md.write_text(
        f"# {key} :: Master Plan\n\n"
        f"**Generated:** {_utc_stamp()}\n\n"
        f"**Inputs:**\n"
        f"- Intake: `projects/{key}/vault/intake/intake.md`\n"
        f"- Prior knowledge: `projects/{key}/vault/intake/prior-knowledge-review.md`\n"
        f"- GitHub research: `projects/{key}/vault/intake/github-research/<utc>/`\n"
        f"- Compile: `projects/{key}/vault/intake/compile-improvements.md`\n\n"
        f"## P0 (this iter)\n\n"
        f"- [ ] scaffold `projects/{key}/CLAUDE.md` (per `new-project-intake-flow-doctrine-2026-05-26.md` template)\n"
        f"- [ ] add `{key}` entry to `automations/session-templates/projects.json` (bump version)\n"
        f"- [ ] pick top 1 ADOPT idea from `compile-improvements.md` + ship to `projects/{key}/src/`\n"
        f"- [ ] smoke (pytest or equivalent) + commit on `agent/{key}/p0-<topic>-<utc-date>` branch\n\n"
        f"## P1 (next 3 iters)\n\n"
        f"- [ ] ADOPT ideas #2 + #3 from `compile-improvements.md`\n"
        f"- [ ] integrate with adjacent Sanctum lane(s) identified in prior-knowledge-review\n\n"
        f"## P2 (backlog)\n\n"
        f"- [ ] WATCH-list re-evaluation triggers (cite specific repo + condition)\n"
        f"- [ ] dashboard surface (sinister-dashboard-skeleton inheritor) if user-facing\n\n"
        f"## Composes with\n\n"
        f"- `_shared-memory/knowledge/new-project-intake-flow-doctrine-2026-05-26.md`\n"
        f"- `_shared-memory/knowledge/single-repo-push-policy-2026-05-25.md`\n"
        f"- `_shared-memory/knowledge/branch-convention-2026-05-25.md`\n"
        f"- `_shared-memory/knowledge/loop-relentless-pursuit-doctrine-2026-05-25.md`\n",
        encoding="utf-8",
    )
    print(f"[stage-5 plan] {plan_md}")
    return plan_md


# -----------------------------------------------------------------------------
# Stage 6 -- SHIP
# -----------------------------------------------------------------------------
def stage_ship(key: str, spawn: bool = False) -> Path:
    """Create the project dir scaffold + projects.json patch hint + optional spawn."""
    pdir = _ensure_dir(_project_dir(key))
    claude_md = pdir / "CLAUDE.md"
    if not claude_md.exists():
        claude_md.write_text(
            f"# {key} :: Project Charter\n\n"
            f"> **Author:** RKOJ-ELENO :: {time.strftime('%Y-%m-%d', time.gmtime())} (auto-scaffold by new_project_intake.py)\n"
            f"> **Branch convention:** `agent/{key}/<short-topic>-<utc-date>`\n"
            f"> **Push policy:** Sinister-Sanctum (single-repo per `single-repo-push-policy-2026-05-25`)\n\n"
            f"## Mission\n\n"
            f"See `vault/intake/intake.md` for the operator's verbatim idea.\n\n"
            f"## Master plan\n\n"
            f"See `_shared-memory/plans/{key}-master-*/plan.md`.\n\n"
            f"## Loop condition (default until first plan ships)\n\n"
            f"> Drain master plan P0 items in order. Re-poll inbox each iter. Heartbeat + PROGRESS + resume-point at iter end.\n",
            encoding="utf-8",
        )
        print(f"[stage-6 ship] scaffold {claude_md}")
    else:
        print(f"[stage-6 ship] {claude_md} already exists; not overwriting")

    # Emit projects.json patch hint (don't auto-edit — projects.json is operator-managed)
    hint = pdir / "projects.json.patch-hint.json"
    hint.write_text(
        json.dumps({
            "_hint": "append this object to .projects[] in automations/session-templates/projects.json + bump .version",
            "key": key,
            "display": " ".join(p.capitalize() for p in key.split("-")),
            "tag": "(auto-scaffold by new_project_intake.py; pending operator one-line tag)",
            "root": str(pdir),
            "lane_dir": str(pdir),
            "session_start": "",
            "claude_md": str(claude_md),
            "github": "Sinister-Sanctum",
            "branch_prefix": f"agent/{key}/",
            "tier": 2,
            "default_modes": {"swarm": True, "loop": "relentless", "loop_relentless": True},
        }, indent=2), encoding="utf-8",
    )
    print(f"[stage-6 ship] projects.json hint -> {hint}")

    if spawn:
        spawn_ps1 = SANCTUM_ROOT / "automations" / "start-sinister-session.ps1"
        if spawn_ps1.exists():
            cmd = [
                "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-File", str(spawn_ps1), "-Project", key,
            ]
            print(f"[stage-6 ship] spawning: {' '.join(cmd)}")
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            print(f"[stage-6 ship] WARN spawn ps1 missing at {spawn_ps1}")

    return claude_md


# -----------------------------------------------------------------------------
# CLI dispatcher
# -----------------------------------------------------------------------------
def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Canonical operator-idea -> shipped-plan intake pipeline")
    p.add_argument("--project-key", required=True, help="kebab-case project slug (e.g. sinister-foo)")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--idea-text", help="raw idea text (use --idea-file for long prose)")
    g.add_argument("--idea-file", type=Path, help="path to operator's idea.md")
    p.add_argument("--stage", choices=["intake","prior-knowledge","github-research","compile","plan","ship","all"], default="all")
    p.add_argument("--dry-run", action="store_true", help="github-research stage: build slices file but don't fan out")
    p.add_argument("--spawn", action="store_true", help="ship stage: also spawn an agent on the new project")
    args = p.parse_args(argv)

    key = args.project_key
    if not re.match(r"^[a-z][a-z0-9-]+$", key):
        print(f"[FAIL] --project-key must be kebab-case lowercase, got: {key}", file=sys.stderr)
        return 2

    try:
        if args.stage in ("intake", "all"):
            stage_intake(key, args.idea_text, args.idea_file)
        if args.stage in ("prior-knowledge", "all"):
            stage_prior_knowledge(key)
        if args.stage in ("github-research", "all"):
            stage_github_research(key, dry_run=args.dry_run)
        if args.stage in ("compile", "all"):
            stage_compile(key)
        if args.stage in ("plan", "all"):
            stage_plan(key)
        if args.stage in ("ship", "all"):
            stage_ship(key, spawn=args.spawn)
    except Exception as exc:
        print(f"[new-project-intake] FAIL stage={args.stage}: {exc}", file=sys.stderr)
        return 1

    print(f"[new-project-intake] OK stage={args.stage} key={key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
