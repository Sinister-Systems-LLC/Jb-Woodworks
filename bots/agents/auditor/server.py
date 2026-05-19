"""
Auditor agent — secrets scan + dedup check + freshness check across hub.

Pure Python (Tier 1, no LLM). Runs hourly via Task Scheduler.

Tools:
  auditor.run()                    -> {secrets, duplicates, stale, summary}
  auditor.scan_secrets(path=None)  -> [{path, line, pattern}]
  auditor.scan_duplicates()        -> [{sha, paths}]
  auditor.scan_stale(days=30)      -> [{path, age_days}]
  auditor.health()                 -> health
"""

from __future__ import annotations

import hashlib
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
    print("[auditor] FastMCP not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

HUB_ROOT = Path(os.environ.get("SINISTER_HUB_ROOT", r"D:\Sinister\Sinister Skills"))
AGENT_DIR = HUB_ROOT / "12_LLM_ORCHESTRATION" / "agents" / "auditor"
FINDINGS_DIR = AGENT_DIR / "findings"
USAGE_LOG = HUB_ROOT / "12_LLM_ORCHESTRATION" / "runtime-state" / "token-usage.jsonl"

AGENT_DIR.mkdir(parents=True, exist_ok=True)
FINDINGS_DIR.mkdir(parents=True, exist_ok=True)
USAGE_LOG.parent.mkdir(parents=True, exist_ok=True)


SECRET_PATTERNS = [
    (re.compile(r'OPENROUTER[_-]?KEY', re.IGNORECASE), "OpenRouter API key"),
    (re.compile(r'OPENAI[_-]?API[_-]?KEY', re.IGNORECASE), "OpenAI API key"),
    (re.compile(r'ANTHROPIC[_-]?API[_-]?KEY', re.IGNORECASE), "Anthropic API key"),
    (re.compile(r'BEGIN\s+(RSA\s+)?PRIVATE\s+KEY'), "PEM private key"),
    (re.compile(r'SUPER[_-]?ADMIN[_-]?CREDENTIALS', re.IGNORECASE), "Super admin creds"),
    (re.compile(r'sk-ant-[a-zA-Z0-9]{30,}'), "Anthropic API key (full)"),
    (re.compile(r'AIza[a-zA-Z0-9_-]{30,}'), "Google API key"),
    (re.compile(r'ghp_[a-zA-Z0-9]{30,}'), "GitHub personal access token"),
    (re.compile(r'eve[_-]?credentials', re.IGNORECASE), "Eve credentials reference"),
]

# Files explicitly allowed (the policy docs themselves quote secret patterns)
ALLOWLIST = {
    "09_REFERENCE/secrets-redaction-policy.md",
    "05_SKILLS/proposed/09-secrets-scan.md",
    "12_LLM_ORCHESTRATION/agents/auditor/server.py",
    "12_LLM_ORCHESTRATION/AGENT-BOOTSTRAP.md",
    "12_LLM_ORCHESTRATION/AUTONOMY-CONTRACT.md",
    "12_LLM_ORCHESTRATION/config/model-registry.yaml",
    "12_LLM_ORCHESTRATION/docker/.env.example",
}


def log_call(tool: str, **extra: Any) -> None:
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent": "auditor",
        "model": None,
        "input_tokens": 0,
        "output_tokens": 0,
        "cost_usd": 0.0,
        "tool": tool,
        **extra,
    }
    with USAGE_LOG.open("a", encoding="utf-8", buffering=1) as f:
        f.write(json.dumps(rec) + "\n")


def relpath(p: Path) -> str:
    try:
        return str(p.relative_to(HUB_ROOT)).replace("\\", "/")
    except ValueError:
        return str(p)


mcp = FastMCP("auditor")


@mcp.tool()
def scan_secrets(path: str | None = None) -> list[dict[str, Any]]:
    """Scan files under HUB_ROOT (or specified subpath) for secret patterns."""
    log_call("scan_secrets")
    scan_root = HUB_ROOT / path if path else HUB_ROOT
    if not scan_root.exists():
        return [{"error": f"path not found: {scan_root}"}]
    findings: list[dict[str, Any]] = []
    for f in scan_root.rglob("*"):
        if not f.is_file():
            continue
        if f.suffix not in {".md", ".txt", ".json", ".yaml", ".yml", ".py", ".ts", ".js", ".ps1", ".bat"}:
            continue
        rp = relpath(f)
        if rp in ALLOWLIST:
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for pat, label in SECRET_PATTERNS:
            for m in pat.finditer(text):
                # Get the line number
                lineno = text[:m.start()].count("\n") + 1
                line_content = text.splitlines()[lineno - 1] if lineno <= len(text.splitlines()) else ""
                findings.append({
                    "path": rp,
                    "line": lineno,
                    "pattern": label,
                    "match_preview": line_content.strip()[:120],
                })
    return findings


@mcp.tool()
def scan_duplicates() -> list[dict[str, Any]]:
    """Find MD files with identical sha256 (potential dedups)."""
    log_call("scan_duplicates")
    by_sha: defaultdict[str, list[str]] = defaultdict(list)
    for f in HUB_ROOT.rglob("*.md"):
        if not f.is_file():
            continue
        rp = relpath(f)
        # Skip pointer files (already deduped)
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
            if "Pointer — duplicate consolidated" in text[:300]:
                continue
            h = hashlib.sha256(text.encode("utf-8")).hexdigest()
            by_sha[h].append(rp)
        except Exception:
            continue
    dups = [{"sha": sha, "paths": paths, "count": len(paths)} for sha, paths in by_sha.items() if len(paths) > 1]
    dups.sort(key=lambda x: x["count"], reverse=True)
    return dups[:50]


@mcp.tool()
def scan_stale(days: int = 30) -> list[dict[str, Any]]:
    """Find files in 01_MEMORY/_consolidated/ older than `days`."""
    log_call("scan_stale", days=days)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    stale: list[dict[str, Any]] = []
    consolidated = HUB_ROOT / "01_MEMORY" / "_consolidated"
    if consolidated.exists():
        for f in consolidated.rglob("*.md"):
            if not f.is_file():
                continue
            mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
            if mtime < cutoff:
                stale.append({
                    "path": relpath(f),
                    "age_days": (datetime.now(timezone.utc) - mtime).days,
                    "mtime": mtime.isoformat(),
                })
    return stale


@mcp.tool()
def run() -> dict[str, Any]:
    """Run full audit. Persists findings to findings/<ts>.json."""
    log_call("run")
    findings = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "secrets": scan_secrets(),
        "duplicates": scan_duplicates(),
        "stale": scan_stale(),
    }
    summary = {
        "secrets_count": len(findings["secrets"]),
        "duplicates_count": sum(d["count"] - 1 for d in findings["duplicates"]),
        "stale_count": len(findings["stale"]),
    }
    findings["summary"] = summary
    out = FINDINGS_DIR / f"audit-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}.json"
    out.write_text(json.dumps(findings, indent=2), encoding="utf-8")
    return {"ok": True, **summary, "findings_file": str(out.relative_to(HUB_ROOT))}


@mcp.tool()
def health() -> dict[str, Any]:
    log_call("health")
    recent_audit = sorted(FINDINGS_DIR.glob("audit-*.json"), reverse=True)
    last_audit = str(recent_audit[0].relative_to(HUB_ROOT)) if recent_audit else None
    return {"ok": True, "agent": "auditor", "last_audit": last_audit}


if __name__ == "__main__":
    mcp.run()
