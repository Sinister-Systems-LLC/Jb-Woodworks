"""Fleet cross-reference for a Jokester intake candidate.

Author: RKOJ-ELENO :: 2026-05-26

Given a candidate (title + tags + readme/transcript), grep the fleet's known
catalogues for token overlap and return:
  - overlap_score: 0.0 - 1.0 (saturating)
  - overlapping_assets: list of {path, hits, snippet}

The intent is NOT to be perfect; it's to give the deciding agent a head start
on "do we already have this / is it adjacent to anything we own?"
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SANCTUM_ROOT = Path(r"D:\Sinister Sanctum")

# Scan-targets are read-only; cheap to grep.
SCAN_TARGETS: list[Path] = [
    SANCTUM_ROOT / "tools" / "_INDEX.md",
    SANCTUM_ROOT / "inventions",
    SANCTUM_ROOT / "_shared-memory" / "knowledge" / "_INDEX.md",
    SANCTUM_ROOT / "automations" / "session-templates" / "projects.json",
    SANCTUM_ROOT / "projects",  # walks for CLAUDE.md files
]

STOPWORDS = {
    # English filler
    "the","and","for","with","this","that","have","from","they","them","will",
    "what","make","need","want","your","also","just","like","keep","more","only",
    "when","then","than","some","here","there","where","which","how","our",
    "are","was","were","has","had","its","it","to","of","in","on","at","as",
    "be","is","an","a","i","we","you","my","do","if","or","no","yes","so",
    "all","any","can","use","add","get","set","fix","run","let","out","off",
    "now","one","two","too","but","not","its","his","her","him","she","he",
    # URL / file glue
    "https","http","com","org","www","github","github.com","md","py","ps1",
    "readme","license","main","master","branch","author","rkoj","eleno",
    # Generic doc/code chrome (these show up in every fleet asset; useless for routing)
    "read","file","files","list","command","output","input","data","value","name",
    "path","line","code","text","string","number","type","types","function",
    "method","class","object","return","import","export","module","package",
    "version","release","update","change","changes","note","notes",
    "doc","docs","logs","info","error","warning","debug","trace",
    "build","builds","install","installs","installed","setup","config","configs",
    "configure","option","options","flag","flags","args","param","params",
    "default","defaults","local","global","remote","origin","branches",
    "commit","commits","stage","staged","fetch","clone","clones",
    "create","created","creating","delete","deletes","deleted","updated",
    "render","rendered","rendering","support","supports","supported",
    "available","unavailable","center","badge","badges","find","finds",
    "latest","first","start","stops","stopping","running","status",
    "bash","linux","windows","sudo","brew","actions","android","current",
    "browse","addition","assets","width","winget","pager","string","strings",
    "feature","features","project","projects","agent","agents","operator",
    "shipped","scoped","scope","spawn","spawns","sinister","fleet","claude",
    "session","sessions","memory","memories","update","brain","knowledge",
    "doctrine","doctrines","verbatim","canonical","hard-canonical",
    "iter","iters","iter-","integration","integrations",
}

# Tokens shorter than 5 chars are noise (e.g. "read","file"); enforce >=5 to catch real names.
TOKEN_RE = re.compile(r"[a-z][a-z0-9_\-]{4,}")


def _tokenize(text: str) -> list[str]:
    raw = TOKEN_RE.findall(text.lower())
    return [t for t in raw if t not in STOPWORDS]


def _candidate_tokens(candidate: dict[str, Any], top: int = 40) -> list[str]:
    parts: list[str] = []
    for k in ("title", "short_summary", "tags", "readme_excerpt"):
        v = candidate.get(k)
        if v:
            parts.append(str(v))
    text = "\n".join(parts)
    toks = _tokenize(text)
    freq: dict[str, int] = {}
    for t in toks:
        freq[t] = freq.get(t, 0) + 1
    ranked = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))
    return [t for t, _ in ranked[:top]]


def _iter_files(target: Path) -> list[Path]:
    if not target.exists():
        return []
    if target.is_file():
        return [target]
    out: list[Path] = []
    # For projects/, only walk per-project CLAUDE.md so we don't slurp gigabytes.
    if target.name == "projects":
        for child in target.iterdir():
            if child.is_dir():
                cm = child / "CLAUDE.md"
                if cm.exists():
                    out.append(cm)
        return out
    # For inventions/, walk one level of .md files.
    if target.name == "inventions":
        out.extend(sorted(target.glob("*.md")))
        return out
    return [target]


PER_TOKEN_CAP = 2                   # one file can contribute at most 2 hits per token
DISTINCT_TOKENS_CAP = 6             # skip files matching >6 distinct tokens (catch-all noise)
MIN_DISTINCT_TOKENS_PER_FILE = 2    # file must match >=2 distinct tokens to count at all

# Per-source weights: how strongly a match in this kind of file evidences that the fleet
# already HAS the candidate's capability (vs merely mentions the idea).
# tools/_INDEX.md = actual implementations -> strong evidence.
# projects/*/CLAUDE.md = scoped lanes -> medium-strong.
# inventions/*.md = ideas we've discussed -> medium.
# projects.json = lane registry -> medium.
# _shared-memory/knowledge/_INDEX.md = brain mentions -> weak (knowing about X != having X).
SOURCE_WEIGHTS: dict[str, float] = {
    "tools/_INDEX.md": 2.0,
    "automations/session-templates/projects.json": 1.2,
    "_shared-memory/knowledge/_INDEX.md": 0.3,
}
DEFAULT_INVENTION_WEIGHT = 1.0
DEFAULT_PROJECT_CLAUDE_WEIGHT = 1.4


def _source_weight(rel_path: str) -> float:
    if rel_path in SOURCE_WEIGHTS:
        return SOURCE_WEIGHTS[rel_path]
    if rel_path.startswith("projects/") and rel_path.endswith("/CLAUDE.md"):
        return DEFAULT_PROJECT_CLAUDE_WEIGHT
    if rel_path.startswith("inventions/"):
        return DEFAULT_INVENTION_WEIGHT
    return 1.0


def _scan_file(path: Path, tokens: list[str], max_bytes: int = 200_000) -> dict[str, Any] | None:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")[:max_bytes].lower()
    except OSError:
        return None
    hits: dict[str, int] = {}
    for tok in tokens:
        c = text.count(tok)
        if c:
            hits[tok] = min(c, PER_TOKEN_CAP)
    if not hits or len(hits) < MIN_DISTINCT_TOKENS_PER_FILE:
        return None
    if len(hits) > DISTINCT_TOKENS_CAP:
        return None
    # Snippet around first hit of the highest-frequency token.
    top_tok = max(hits.items(), key=lambda kv: kv[1])[0]
    idx = text.find(top_tok)
    start = max(0, idx - 80)
    end = min(len(text), idx + 120)
    snippet = text[start:end].replace("\n", " ").strip()
    try:
        rel = path.relative_to(SANCTUM_ROOT).as_posix()
    except ValueError:
        rel = str(path)
    weight = _source_weight(rel)
    hit_total = sum(hits.values())
    return {
        "path": rel,
        "hits": hits,
        "hit_total": hit_total,
        "weighted_hit": round(hit_total * weight, 2),
        "weight": weight,
        "snippet": snippet,
    }


def cross_reference(candidate: dict[str, Any]) -> dict[str, Any]:
    tokens = _candidate_tokens(candidate)
    if not tokens:
        return {"overlap_score": 0.0, "tokens": [], "overlapping_assets": []}

    assets: list[dict[str, Any]] = []
    for target in SCAN_TARGETS:
        for fp in _iter_files(target):
            row = _scan_file(fp, tokens)
            if row:
                assets.append(row)

    assets.sort(key=lambda r: r["weighted_hit"], reverse=True)
    assets = assets[:25]

    # Score from the top-5 most-relevant (by weighted hit). Sqrt damping keeps any single
    # very-dense file from dominating; divisor 25 calibrated so realistic candidates fall in
    # 0.0-0.7 range, leaving 0.7-1.0 for genuine "this is already implemented in fleet".
    top = assets[:5]
    weighted = sum(a["weighted_hit"] ** 0.5 for a in top)
    score = min(weighted / 25.0, 1.0)
    return {
        "overlap_score": round(score, 3),
        "tokens": tokens,
        "overlapping_assets": assets,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate-json", type=Path, required=True, help="Path to a JSON file produced by intake.*.")
    args = ap.parse_args(argv)
    cand = json.loads(args.candidate_json.read_text(encoding="utf-8"))
    out = cross_reference(cand)
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
