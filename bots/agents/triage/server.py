"""
Triage agent — file/text classifier.

Tier 2 default: Ollama small (qwen2.5:1.5b ~1s/call, $0).
Fallback: deterministic Python rules (path patterns + content heuristics) when Ollama down.

Tools:
  triage.classify_file(path)                  -> {category, suggested_section, project, tags, confidence, mode}
  triage.classify_text(text, hint=None)       -> same
  triage.classify_batch(paths)                -> [...]
  triage.list_categories()                    -> [{key, hub_section, description}]
  triage.health()                             -> {ok, ollama_healthy, mode}
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("[triage] FastMCP not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

HUB_ROOT = Path(os.environ.get("SINISTER_HUB_ROOT", r"D:\Sinister\Sinister Skills"))
AGENT_DIR = HUB_ROOT / "12_LLM_ORCHESTRATION" / "agents" / "triage"
AGENT_DIR.mkdir(parents=True, exist_ok=True)
USAGE_LOG = HUB_ROOT / "12_LLM_ORCHESTRATION" / "runtime-state" / "token-usage.jsonl"
USAGE_LOG.parent.mkdir(parents=True, exist_ok=True)

OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
CLASSIFY_MODEL = os.environ.get("TRIAGE_MODEL", "qwen2.5:1.5b")

# ===== Category catalog (also returned by list_categories) =====
CATEGORIES = [
    {"key": "memory", "hub_section": "01_MEMORY", "description": "Per-project memory anchors, SESSION-START, RESUME, WHERE-I-STOPPED"},
    {"key": "archive", "hub_section": "02_MD_ARCHIVE", "description": "Long-form markdown notes / documentation worth long-term archival"},
    {"key": "project_capsule", "hub_section": "03_PROJECTS", "description": "One-pager capsule per project (overview, status, deps)"},
    {"key": "mcp_tool", "hub_section": "04_MCP", "description": "MCP server config, tool catalog entries"},
    {"key": "skill", "hub_section": "05_SKILLS", "description": "Existing or proposed Claude skill / agent contract"},
    {"key": "graph", "hub_section": "06_UNDERSTAND", "description": "Knowledge graph data, UA outputs"},
    {"key": "dashboard", "hub_section": "07_DASHBOARD", "description": "Status dashboard, daily digest, per-project dashboards"},
    {"key": "automation", "hub_section": "08_AUTOMATIONS", "description": "Cross-project workflow scripts, .bat/.ps1 glue, scheduled jobs"},
    {"key": "reference", "hub_section": "09_REFERENCE", "description": "Yurikey roster, proxy pool, vocabulary, secrets policy"},
    {"key": "plan", "hub_section": "10_PLANS", "description": "Phase plan, /plans/ snapshot, implementation strategy doc"},
    {"key": "code", "hub_section": "11_CODE_LIBRARY", "description": "Reusable source code (Python/TS/Kotlin/Bash/PowerShell helpers)"},
    {"key": "orchestration", "hub_section": "12_LLM_ORCHESTRATION", "description": "Agent fleet code, model registry, escalation ladder"},
    {"key": "log", "hub_section": "_logs", "description": "Run logs, refresh history, restore points"},
    {"key": "secret_risk", "hub_section": "QUARANTINE", "description": "Contains apparent secret/key/token — flag operator, do not auto-archive"},
    {"key": "ephemeral", "hub_section": "DROP", "description": "Cache, temp, lock, build artifact — safe to drop"},
    {"key": "unknown", "hub_section": "?", "description": "Could not classify — operator to triage manually"},
]
CATEGORY_KEYS = {c["key"] for c in CATEGORIES}

# ===== Heuristic rules (Tier 1 fallback when Ollama down) =====
PATH_RULES = [
    (re.compile(r"SESSION-START|WHERE-I-STOPPED|RESUME(?:-HERE)?\.md|_claude_memory", re.I), "memory"),
    (re.compile(r"02_MD_ARCHIVE|/docs/.*\.md$|/notes/", re.I), "archive"),
    (re.compile(r"03_PROJECTS|/capsule\.md$", re.I), "project_capsule"),
    (re.compile(r"\.mcp\.json$|_catalog/ALL-TOOLS|MCP\b", re.I), "mcp_tool"),
    (re.compile(r"/skills/|05_SKILLS|skill\.md$", re.I), "skill"),
    (re.compile(r"06_UNDERSTAND|knowledge-graph|graph\.json$", re.I), "graph"),
    (re.compile(r"07_DASHBOARD|daily-digest|dashboard", re.I), "dashboard"),
    (re.compile(r"08_AUTOMATIONS|\.(bat|ps1|sh)$|cron|scheduled", re.I), "automation"),
    (re.compile(r"09_REFERENCE|yurikey-roster|secrets-redaction", re.I), "reference"),
    (re.compile(r"10_PLANS|/plans/|PLAN-.*\.md$|MASTER-PLAN", re.I), "plan"),
    (re.compile(r"11_CODE_LIBRARY|\.(py|ts|tsx|kt|java)$", re.I), "code"),
    (re.compile(r"12_LLM_ORCHESTRATION|agents?/.*server\.py$", re.I), "orchestration"),
    (re.compile(r"_logs/|refresh-.*\.log$|restore-point", re.I), "log"),
    (re.compile(r"\.(tmp|cache|lock|pyc|class|o|so|dll)$|__pycache__|/node_modules/|/\.venv/", re.I), "ephemeral"),
]

SECRET_PATTERNS = [
    re.compile(r"sk-ant-[a-zA-Z0-9]{30,}"),
    re.compile(r"BEGIN\s+(RSA\s+)?PRIVATE\s+KEY"),
    re.compile(r"AIza[a-zA-Z0-9_-]{30,}"),
    re.compile(r"ghp_[a-zA-Z0-9]{30,}"),
    re.compile(r"(OPENROUTER|OPENAI|ANTHROPIC)[_-]?(API[_-]?)?KEY\s*=\s*\S{20,}", re.I),
]

PROJECT_HINTS = [
    "snap-signer", "library-of-alexandria", "sinister-tiktok-emu", "sinister-snap-emu",
    "sinister-bumble-emu", "sinister-panel", "sinister-rka-good", "kernel-su-setup",
    "letstext", "jokr-global", "library-of-jokr-mirror",
]

TAG_VOCAB = [
    "yurikey", "rka", "proxy", "harvest", "a11y", "keybox", "fingerprint",
    "signing", "attestation", "panel", "dashboard", "automation", "secret",
    "operator-action", "ollama", "mcp", "skill", "agent",
]


def log_call(tool: str, model: str | None = None, **extra: Any) -> None:
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent": "triage",
        "model": model,
        "input_tokens": extra.pop("input_tokens", 0),
        "output_tokens": extra.pop("output_tokens", 0),
        "cost_usd": 0.0,
        "tool": tool,
        **extra,
    }
    with USAGE_LOG.open("a", encoding="utf-8", buffering=1) as f:
        f.write(json.dumps(rec) + "\n")


def ollama_healthy() -> bool:
    if not HAS_REQUESTS:
        return False
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def detect_secret(text: str) -> bool:
    return any(p.search(text) for p in SECRET_PATTERNS)


def detect_project(haystack: str) -> str | None:
    low = haystack.lower()
    for p in PROJECT_HINTS:
        if p in low:
            return p
    return None


def detect_tags(haystack: str) -> list[str]:
    low = haystack.lower()
    return [t for t in TAG_VOCAB if t in low]


def classify_by_rules(path: str | None, text: str) -> dict[str, Any]:
    """Pure-Python rule classifier (Tier 1 fallback)."""
    haystack = (path or "") + "\n" + text[:2000]
    # Secret check first — overrides everything
    if detect_secret(text):
        return {
            "category": "secret_risk",
            "suggested_section": "QUARANTINE",
            "project": detect_project(haystack),
            "tags": ["secret"] + detect_tags(haystack),
            "confidence": 0.95,
            "mode": "rules",
            "reason": "secret_pattern_matched",
        }
    if path:
        for pattern, cat in PATH_RULES:
            if pattern.search(path):
                section = next(c["hub_section"] for c in CATEGORIES if c["key"] == cat)
                return {
                    "category": cat,
                    "suggested_section": section,
                    "project": detect_project(haystack),
                    "tags": detect_tags(haystack),
                    "confidence": 0.85,
                    "mode": "rules",
                    "reason": f"path_pattern:{pattern.pattern[:40]}",
                }
    # Content-only heuristics
    low = text[:1000].lower()
    if any(k in low for k in ("session start", "where i stopped", "resume here", "pickup at")):
        return {"category": "memory", "suggested_section": "01_MEMORY", "project": detect_project(haystack),
                "tags": detect_tags(haystack), "confidence": 0.75, "mode": "rules", "reason": "content:memory_anchor"}
    if low.startswith(("def ", "class ", "import ", "from ", "function ", "#!/", "package ")):
        return {"category": "code", "suggested_section": "11_CODE_LIBRARY", "project": detect_project(haystack),
                "tags": detect_tags(haystack), "confidence": 0.70, "mode": "rules", "reason": "content:source_code"}
    return {"category": "unknown", "suggested_section": "?", "project": detect_project(haystack),
            "tags": detect_tags(haystack), "confidence": 0.30, "mode": "rules", "reason": "no_rule_matched"}


def classify_by_ollama(path: str | None, text: str, hint: str | None = None) -> dict[str, Any] | None:
    """Ollama small-model classifier. Returns None on failure (caller falls back)."""
    if not HAS_REQUESTS or not ollama_healthy():
        return None
    cat_list = "\n".join(f"  {c['key']}: {c['description']}" for c in CATEGORIES)
    snippet = text[:1500]
    prompt = f"""You are a strict file classifier for the Sinister Skills hub. Pick ONE category key from this list:

{cat_list}

Rules:
- If the content contains an apparent API key, private key, or secret token, return "secret_risk".
- Pick "ephemeral" for caches, locks, build artifacts.
- Pick "unknown" only as last resort.
- Output STRICT JSON only, no prose, no markdown fences.

Input:
PATH: {path or '(none)'}
HINT: {hint or '(none)'}
SNIPPET:
{snippet}

Output JSON shape:
{{"category": "<one_key>", "confidence": <0..1>, "reason": "<short>"}}
"""
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": CLASSIFY_MODEL, "prompt": prompt, "stream": False, "format": "json",
                  "options": {"temperature": 0.0, "num_predict": 120}},
            timeout=20,
        )
        if r.status_code != 200:
            return None
        body = r.json()
        raw = body.get("response", "").strip()
        parsed = json.loads(raw)
        cat = parsed.get("category", "unknown")
        if cat not in CATEGORY_KEYS:
            return None  # validation fail -> fall back
        haystack = (path or "") + "\n" + text[:2000]
        section = next(c["hub_section"] for c in CATEGORIES if c["key"] == cat)
        return {
            "category": cat,
            "suggested_section": section,
            "project": detect_project(haystack),
            "tags": detect_tags(haystack),
            "confidence": float(parsed.get("confidence", 0.6)),
            "mode": "ollama",
            "reason": parsed.get("reason", "")[:200],
            "model": CLASSIFY_MODEL,
        }
    except Exception:
        return None


def read_snippet(path: Path, max_bytes: int = 4096) -> str:
    try:
        with path.open("rb") as f:
            raw = f.read(max_bytes)
        return raw.decode("utf-8", errors="ignore")
    except Exception:
        return ""


mcp = FastMCP("triage")


@mcp.tool()
def classify_file(path: str, use_llm: bool = True) -> dict[str, Any]:
    """Classify a file by its path + first 4KB of content. Tries Ollama first when use_llm=True."""
    p = Path(path)
    text = read_snippet(p) if p.exists() else ""
    result: dict[str, Any] | None = None
    if use_llm:
        result = classify_by_ollama(path, text)
    if result is None:
        result = classify_by_rules(path, text)
    log_call("classify_file", model=result.get("model"), path=path[:200], category=result["category"], mode=result["mode"])
    result["path"] = path
    result["exists"] = p.exists()
    return result


@mcp.tool()
def classify_text(text: str, hint: str | None = None, use_llm: bool = True) -> dict[str, Any]:
    """Classify a raw text snippet. hint can describe context (e.g., 'pasted from chat')."""
    result: dict[str, Any] | None = None
    if use_llm:
        result = classify_by_ollama(None, text, hint=hint)
    if result is None:
        result = classify_by_rules(None, text)
    log_call("classify_text", model=result.get("model"), category=result["category"], mode=result["mode"])
    return result


@mcp.tool()
def classify_batch(paths: list[str], use_llm: bool = True) -> list[dict[str, Any]]:
    """Classify many files. Returns a list aligned with input order."""
    log_call("classify_batch", count=len(paths))
    return [classify_file(p, use_llm=use_llm) for p in paths]


@mcp.tool()
def list_categories() -> list[dict[str, Any]]:
    """Return the full category catalog (key, hub_section, description)."""
    log_call("list_categories")
    return CATEGORIES


@mcp.tool()
def health() -> dict[str, Any]:
    """Health check — reports Ollama status + active classifier mode."""
    log_call("health")
    ollama_ok = ollama_healthy() if HAS_REQUESTS else False
    return {
        "ok": True,
        "agent": "triage",
        "has_requests": HAS_REQUESTS,
        "ollama_healthy": ollama_ok,
        "model": CLASSIFY_MODEL,
        "active_mode": "ollama" if ollama_ok else "rules",
        "categories_count": len(CATEGORIES),
    }


if __name__ == "__main__":
    mcp.run()
