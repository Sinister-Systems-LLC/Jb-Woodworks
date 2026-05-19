"""
Curator agent — code-library extraction scout.

Tier 3 (Claude Haiku). Walks recent project source files, asks Haiku to identify
helper functions that appear in 2+ projects and recommends extraction to
11_CODE_LIBRARY/. Cost ~$0.05 per scan.

Tools:
  curator.scan_candidates(roots=None, top_k=10)      -> [{name, language, origins, score, suggestion}]
  curator.assess_file(path)                          -> {recommend, reasons, candidates: [...]}
  curator.write_proposal(out_path=None)              -> {ok, path}  (markdown summary)
  curator.list_origins()                             -> source roots being scanned
  curator.health()                                   -> {ok, api_key_present, model}
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("[curator] FastMCP not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

# Bot memory loader (see 12_LLM_ORCHESTRATION/BOT-MEMORY-PROTOCOL.md)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
try:
    from _shared import bot_memory  # type: ignore
    HAS_BOT_MEMORY = True
except Exception:
    HAS_BOT_MEMORY = False

HUB_ROOT = Path(os.environ.get("SINISTER_HUB_ROOT", r"D:\Sinister\Sinister Skills"))
AGENT_DIR = HUB_ROOT / "12_LLM_ORCHESTRATION" / "agents" / "curator"
AGENT_DIR.mkdir(parents=True, exist_ok=True)
PROPOSAL_DIR = HUB_ROOT / "11_CODE_LIBRARY" / "_proposals"
PROPOSAL_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST_PATH = HUB_ROOT / "_manifest.json"
USAGE_LOG = HUB_ROOT / "12_LLM_ORCHESTRATION" / "runtime-state" / "token-usage.jsonl"
USAGE_LOG.parent.mkdir(parents=True, exist_ok=True)

DEFAULT_MODEL = os.environ.get("CURATOR_MODEL", "claude-haiku-4-5-20251001")
# Haiku 4.5 pricing
COST_INPUT = 0.00080
COST_OUTPUT = 0.00400
COST_CACHE_WRITE = 0.00100
COST_CACHE_READ = 0.00008

LANG_BY_EXT = {
    ".py": "python", ".ts": "typescript", ".tsx": "typescript", ".js": "javascript",
    ".kt": "kotlin", ".java": "java", ".sh": "bash", ".ps1": "powershell",
    ".bat": "batch", ".rs": "rust", ".go": "go",
}

# Patterns that strongly hint at reusable utility code
DEF_PATTERNS = {
    "python":    re.compile(r"^def\s+([a-z_][a-z0-9_]*)\s*\(", re.MULTILINE),
    "typescript":re.compile(r"^(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", re.MULTILINE),
    "javascript":re.compile(r"^(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", re.MULTILINE),
    "kotlin":    re.compile(r"^(?:fun|inline\s+fun)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", re.MULTILINE),
    "java":      re.compile(r"\b(?:public|private|protected|static)\s+[\w<>\[\],\s]+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", re.MULTILINE),
    "bash":      re.compile(r"^(?:function\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\)\s*\{", re.MULTILINE),
    "powershell":re.compile(r"^function\s+([a-zA-Z_][a-zA-Z0-9_-]*)\s*\{", re.MULTILINE | re.IGNORECASE),
}

# Boilerplate to skip — almost never worth extracting
BORING = {"main", "run", "test", "setup", "init", "__init__", "tearDown", "setUp", "toString", "hashCode"}

SYSTEM_PROMPT = """You are Curator, an extraction scout for the Sinister Skills hub
11_CODE_LIBRARY (reusable function library).

You receive a JSON list of candidate functions that appeared in 2+ project source files.
Your job: rank them by extraction value and suggest a canonical name + domain bucket.

Rules:
- Only recommend candidates with genuine cross-project reuse value (auth, proxy, signing,
  harvesting, a11y, keybox, fingerprint, RKA, bat-prelude, robocopy helpers).
- SKIP main()/test()/setup()/run()/init/etc — they are coordination, not utilities.
- SKIP one-off domain glue (e.g. "snap_signer_v3_specific_hack").
- SKIP UI components — those live in 11_CODE_LIBRARY/by-domain/ui/ only if truly primitive.
- Domain buckets: auth, proxy, rka, harvesting, a11y, keybox, fingerprint, bat-prelude,
  ui, fs, network, crypto, misc.
- Output STRICT JSON only — no prose, no markdown fences.

Output shape:
{
  "recommendations": [
    {"name": "...", "language": "...", "domain": "...", "origins": ["..."],
     "score": 0..1, "rationale": "...", "suggested_path": "by-language/<lang>/<file>.<ext>"}
  ],
  "skip": [{"name": "...", "reason": "..."}]
}
"""


def log_call(tool: str, model: str | None = None, **extra: Any) -> None:
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent": "curator",
        "model": model,
        "input_tokens": extra.pop("input_tokens", 0),
        "output_tokens": extra.pop("output_tokens", 0),
        "cache_read_tokens": extra.pop("cache_read_tokens", 0),
        "cache_write_tokens": extra.pop("cache_write_tokens", 0),
        "cost_usd": extra.pop("cost_usd", 0.0),
        "tool": tool,
        **extra,
    }
    with USAGE_LOG.open("a", encoding="utf-8", buffering=1) as f:
        f.write(json.dumps(rec) + "\n")


def atomic_write(path: Path, content: str) -> None:
    tmp = path.with_suffix(path.suffix + f".tmp.{os.urandom(4).hex()}")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


def load_source_roots() -> list[Path]:
    """Source paths from _manifest.json's projects list (their actual roots, not hub mirrors)."""
    if not MANIFEST_PATH.exists():
        return []
    try:
        m = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    out = []
    for proj in m.get("projects", []):
        src = proj.get("source_path")
        if src and Path(src).exists():
            out.append(Path(src))
    return out


def extract_definitions(path: Path) -> list[tuple[str, str]]:
    """Return [(name, language)] for all top-level definitions in a source file."""
    lang = LANG_BY_EXT.get(path.suffix.lower())
    if not lang or lang not in DEF_PATTERNS:
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []
    if len(text) > 200_000:  # skip huge files
        return []
    pattern = DEF_PATTERNS[lang]
    out = []
    for m in pattern.finditer(text):
        name = m.group(1)
        if name in BORING or name.startswith("_"):
            continue
        if len(name) < 4:  # skip 1-3 letter ad-hoc helpers
            continue
        out.append((name, lang))
    return out


def gather_candidates(roots: list[Path], max_files_per_root: int = 400, recent_days: int = 30) -> list[dict[str, Any]]:
    """Walk source roots, collect function names that appear in 2+ projects."""
    by_name: dict[tuple[str, str], dict[str, Any]] = {}  # (name, lang) -> {origins: set, files: list}
    cutoff = datetime.now(timezone.utc).timestamp() - recent_days * 86400
    for root in roots:
        seen = 0
        for f in root.rglob("*"):
            if not f.is_file():
                continue
            if f.suffix.lower() not in LANG_BY_EXT:
                continue
            # skip vendored / build paths
            parts = {p.lower() for p in f.parts}
            if parts & {"node_modules", ".venv", "__pycache__", "build", "dist", ".git", "target"}:
                continue
            try:
                if f.stat().st_mtime < cutoff:
                    continue
            except OSError:
                continue
            for name, lang in extract_definitions(f):
                key = (name, lang)
                slot = by_name.setdefault(key, {"origins": set(), "files": []})
                slot["origins"].add(root.name)
                slot["files"].append(str(f))
            seen += 1
            if seen >= max_files_per_root:
                break
    # Keep only multi-project candidates
    candidates = []
    for (name, lang), slot in by_name.items():
        if len(slot["origins"]) < 2:
            continue
        candidates.append({
            "name": name,
            "language": lang,
            "origins": sorted(slot["origins"]),
            "occurrence_count": len(slot["files"]),
            "sample_files": slot["files"][:3],
        })
    candidates.sort(key=lambda c: (-len(c["origins"]), -c["occurrence_count"]))
    return candidates


def get_system_prompt() -> str:
    if HAS_BOT_MEMORY:
        loaded = bot_memory.load_memory("curator")
        if loaded and "[no SYSTEM-PROMPT.md found" not in loaded:
            return loaded
    return SYSTEM_PROMPT


def call_haiku(user_payload: str, model: str) -> dict[str, Any]:
    if not HAS_ANTHROPIC:
        return {"ok": False, "error": "anthropic SDK not installed (pip install anthropic)"}
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {"ok": False, "error": "ANTHROPIC_API_KEY env var not set"}
    client = Anthropic(api_key=api_key)
    try:
        resp = client.messages.create(
            model=model,
            max_tokens=2000,
            system=[{
                "type": "text",
                "text": get_system_prompt(),
                "cache_control": {"type": "ephemeral"},
            }],
            messages=[{"role": "user", "content": user_payload}],
        )
    except Exception as e:
        return {"ok": False, "error": f"Anthropic API error: {e}"}
    text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
    u = resp.usage
    input_tokens = getattr(u, "input_tokens", 0) or 0
    output_tokens = getattr(u, "output_tokens", 0) or 0
    cache_read = getattr(u, "cache_read_input_tokens", 0) or 0
    cache_write = getattr(u, "cache_creation_input_tokens", 0) or 0
    cost = (
        (input_tokens / 1000) * COST_INPUT
        + (output_tokens / 1000) * COST_OUTPUT
        + (cache_write / 1000) * COST_CACHE_WRITE
        + (cache_read / 1000) * COST_CACHE_READ
    )
    return {
        "ok": True, "text": text,
        "input_tokens": input_tokens, "output_tokens": output_tokens,
        "cache_read_tokens": cache_read, "cache_write_tokens": cache_write,
        "cost_usd": round(cost, 6),
    }


mcp = FastMCP("curator")


@mcp.tool()
def scan_candidates(roots: list[str] | None = None, top_k: int = 10, recent_days: int = 30) -> dict[str, Any]:
    """Scan recent project source for cross-project helper-function candidates.

    Returns the deterministic candidate list AND (if Anthropic available) Haiku-ranked recommendations.
    """
    if roots:
        root_paths = [Path(r) for r in roots if Path(r).exists()]
    else:
        root_paths = load_source_roots()
    if not root_paths:
        return {"ok": False, "error": "no source roots found (no roots given + _manifest.json empty/missing)"}
    candidates = gather_candidates(root_paths, recent_days=recent_days)
    if not candidates:
        log_call("scan_candidates", model=None, candidates=0)
        return {"ok": True, "candidates": [], "recommendations": [], "note": "no multi-project helpers detected"}
    # Send top 30 to Haiku for ranking + suggestion
    payload_for_llm = candidates[:30]
    user_payload = (
        f"Here are {len(payload_for_llm)} candidate functions appearing in 2+ projects. "
        f"Rank the top {top_k} by extraction value.\n\n"
        f"```json\n{json.dumps(payload_for_llm, indent=2)}\n```"
    )
    llm_result = call_haiku(user_payload, model=DEFAULT_MODEL)
    if not llm_result.get("ok"):
        log_call("scan_candidates", model=DEFAULT_MODEL, error=llm_result.get("error"))
        return {"ok": True, "candidates": candidates[:top_k], "recommendations": [], "llm_error": llm_result.get("error")}
    log_call("scan_candidates", model=DEFAULT_MODEL,
             input_tokens=llm_result["input_tokens"], output_tokens=llm_result["output_tokens"],
             cache_read_tokens=llm_result["cache_read_tokens"], cache_write_tokens=llm_result["cache_write_tokens"],
             cost_usd=llm_result["cost_usd"], candidates=len(candidates))
    try:
        parsed = json.loads(llm_result["text"])
    except json.JSONDecodeError:
        return {"ok": True, "candidates": candidates[:top_k], "recommendations": [],
                "llm_raw": llm_result["text"][:1000], "llm_error": "non-JSON response"}
    return {
        "ok": True,
        "candidates": candidates[:top_k],
        "recommendations": parsed.get("recommendations", [])[:top_k],
        "skip": parsed.get("skip", []),
        "cost_usd": llm_result["cost_usd"],
        "model": DEFAULT_MODEL,
    }


@mcp.tool()
def assess_file(path: str) -> dict[str, Any]:
    """Pure-Python single-file assessment — lists definitions + flags BORING ones. No LLM call."""
    log_call("assess_file", path=path[:200])
    p = Path(path)
    if not p.exists():
        return {"ok": False, "error": f"file not found: {path}"}
    defs = extract_definitions(p)
    if not defs:
        return {"ok": True, "recommend": False, "reasons": ["unsupported language or no defs"], "candidates": []}
    return {
        "ok": True,
        "recommend": len(defs) > 0,
        "language": defs[0][1] if defs else None,
        "candidates": [{"name": n, "language": l} for n, l in defs],
        "reasons": ["multi-project verification needed — call scan_candidates for cross-project view"],
    }


@mcp.tool()
def write_proposal(out_path: str | None = None) -> dict[str, Any]:
    """Generate proposal markdown to 11_CODE_LIBRARY/_proposals/<utc-stamp>.md."""
    result = scan_candidates(top_k=15)
    if not result.get("ok"):
        return result
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = Path(out_path) if out_path else (PROPOSAL_DIR / f"curator-{stamp}.md")
    lines = [
        f"# Curator extraction proposal - {stamp}",
        "",
        f"Model: `{result.get('model', 'n/a')}`  |  Cost: ${result.get('cost_usd', 0)}",
        "",
        "## Recommended extractions",
        "",
    ]
    for r in result.get("recommendations", []):
        origins = ", ".join(r.get("origins", []))
        lines.append(f"- **{r.get('name')}** ({r.get('language')}, score {r.get('score')}) -> `{r.get('suggested_path')}`")
        lines.append(f"  - origins: {origins}")
        lines.append(f"  - rationale: {r.get('rationale')}")
        lines.append(f"  - domain: `{r.get('domain')}`")
    if result.get("skip"):
        lines.append("")
        lines.append("## Skipped")
        for s in result["skip"]:
            lines.append(f"- {s.get('name')} - {s.get('reason')}")
    lines.append("")
    lines.append("## Raw candidate list (top 10)")
    for c in result.get("candidates", [])[:10]:
        lines.append(f"- `{c['name']}` ({c['language']}) - origins: {', '.join(c['origins'])} - {c['occurrence_count']} occurrences")
    atomic_write(target, "\n".join(lines))
    log_call("write_proposal", path=str(target))
    return {"ok": True, "path": str(target.relative_to(HUB_ROOT)) if HUB_ROOT in target.parents else str(target),
            "cost_usd": result.get("cost_usd")}


@mcp.tool()
def list_origins() -> list[str]:
    """Source roots Curator scans (derived from _manifest.json)."""
    log_call("list_origins")
    return [str(p) for p in load_source_roots()]


@mcp.tool()
def absorb(fact: str, source: str, tags: list[str] | None = None) -> dict[str, Any]:
    """Persist a fact into curator's memory. Audit-logged. See BOT-MEMORY-PROTOCOL.md."""
    if not HAS_BOT_MEMORY:
        return {"ok": False, "error": "bot_memory module not loadable"}
    return bot_memory.absorb_fact("curator", fact, source, tags or [])


@mcp.tool()
def list_facts(limit: int = 50) -> list[dict[str, Any]]:
    if not HAS_BOT_MEMORY:
        return []
    return bot_memory.list_facts("curator", limit=limit)


@mcp.tool()
def forget(fact_substring: str) -> dict[str, Any]:
    if not HAS_BOT_MEMORY:
        return {"ok": False, "error": "bot_memory module not loadable"}
    return bot_memory.forget_fact("curator", fact_substring)


@mcp.tool()
def health() -> dict[str, Any]:
    log_call("health")
    mem_stats = bot_memory.memory_stats("curator") if HAS_BOT_MEMORY else {}
    return {
        "ok": True,
        "agent": "curator",
        "has_anthropic_sdk": HAS_ANTHROPIC,
        "api_key_present": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "model": DEFAULT_MODEL,
        "source_roots": len(load_source_roots()),
        "proposal_dir": str(PROPOSAL_DIR.relative_to(HUB_ROOT)),
        "bot_memory": {"loaded": HAS_BOT_MEMORY, **mem_stats},
    }


if __name__ == "__main__":
    mcp.run()
