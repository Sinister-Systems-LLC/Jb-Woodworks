# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
"""
Sanctum :: memory-poisoning defense for shared-memory write endpoints.

Defense-in-depth. Claude's own harness already blocks classifier-bypass
patterns inside Claude. This is the SECOND layer — on the API side — so that
even if a compromised agent, an inbox webhook, or a future LAN client tries to
POST a memory-poisoning payload into Sanctum's shared brain, we refuse it +
audit the attempt.

What we block (with reasoning):

 1. **"Ignore previous instructions / disregard prior context"** — classic
    prompt-injection primer. Memory entries written this way are designed to
    derail future agents' cold-start protocol.

 2. **"From now on (you/agents) will..."** — future-session directives that
    look like jailbreak set-up. Real operator directives are dated, signed,
    and reference concrete artifacts — never start "from now on, ignore..."

 3. **"You are now <pretend mode>"** — roleplay-shift primers. Future agents
    cold-start with this and lose sight of actual operator policy.

 4. **"Bypass / disable / override (safety|classifier|harness|guardrails)"** —
    direct anti-safety language. Operator's documented directive (Rule 5 +
    Rule 7) is that Sanctum does NOT try to bypass classifiers; the codec is
    open and the vault is at-rest only. Memory writes that say otherwise are
    not from the operator.

 5. **"Do not refuse / never refuse / you must comply"** — coercive framing
    aimed at future agents.

 6. **Large all-caps directive blocks (>200 chars with >70% caps)** — jailbreak
    primer style. Operator's real directives use sentence case.

The sanitizer returns:
    {"ok": True, "blocked": False, "patterns": []}      # safe
    {"ok": True, "blocked": True,  "patterns": [...]}   # poison; REJECT
    {"ok": True, "blocked": False, "patterns": [...]}   # warn-but-allow (low severity)

Every block also writes a row to `_shared-memory/blocked-writes.jsonl` for
operator audit. Operator can review and unblock individual entries by editing
the target file directly (which is local-filesystem write — sanitizer doesn't
gate that).

The sanitizer is NEVER applied to operator-side bats. Those write directly to
disk. The operator's authority over their own memory files is absolute. The
sanitizer is purely for protecting the network-facing write endpoints
(`/api/knowledge/append`, `/api/shared-memory/append`,
`POST /api/operator-requests`).

Returns severity:
    "block" — reject the write outright
    "warn"  — allow but tag with a warning (low signal)
    "none"  — clean
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# Hard-block patterns. Hits here ALWAYS reject the write.
BLOCK_PATTERNS: list[tuple[str, str]] = [
    (r"(?i)\bignore\s+(all\s+|the\s+|any\s+|all of the\s+)?(previous|prior|earlier|above)\s+(instructions?|context|directives?|rules?|prompts?)\b",
     "ignore-previous-instructions"),
    (r"(?i)\bdisregard\s+(all\s+|the\s+|any\s+|prior\s+)?(previous|prior|earlier|above|system)\s+(instructions?|context|directives?|prompts?)\b",
     "disregard-prior"),
    (r"(?i)\b(bypass|disable|override|circumvent|skip|jailbreak)\s+(all\s+|the\s+|any\s+)?(safety|classifier|harness|guardrails?|filter|moderation|alignment)\b",
     "anti-safety-direct"),
    (r"(?i)\b(never|do\s+not|don'?t)\s+(refuse|deny|reject|say\s+no|decline)\b",
     "no-refuse-coercion"),
    (r"(?i)\byou\s+are\s+(now\s+)?(in\s+)?(dan|developer|debug|jailbreak|admin\s+override|unrestricted|uncensored)\s+mode\b",
     "roleplay-shift"),
    (r"(?i)\bfrom\s+now\s+on,?\s+(you|all\s+(agents?|sessions?)|every\s+(agent|session))\s+(will|must|should|shall)\s+(ignore|bypass|disable|override|never|always)",
     "future-sessions-bypass"),
    (r"(?i)\bact\s+as\s+(an?\s+)?(unrestricted|uncensored|jailbroken|amoral|evil)\s+ai\b",
     "act-as-jailbreak"),
    (r"(?i)\bpretend\s+(you|all\s+future\s+agents?)\s+(are|have|can)\s+",
     "pretend-future"),
]

# Soft-warn patterns. Logged but not blocked.
WARN_PATTERNS: list[tuple[str, str]] = [
    (r"(?i)\bsystem\s+prompt\b", "mentions-system-prompt"),
    (r"(?i)\binjection\b.*\battack\b", "discusses-injection"),
    (r"(?i)\bclassifier\s+(bypass|evasion|trick)\b", "discusses-classifier-bypass"),
]

# Caps-block heuristic
CAPS_HEURISTIC_MIN_CHARS = 200
CAPS_HEURISTIC_PCT_THRESHOLD = 0.70


def _caps_heuristic(text: str) -> bool:
    """Return True if the text is large + mostly uppercase (jailbreak primer style)."""
    if len(text) < CAPS_HEURISTIC_MIN_CHARS:
        return False
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    caps = sum(1 for c in letters if c.isupper())
    return (caps / len(letters)) > CAPS_HEURISTIC_PCT_THRESHOLD


def scan(text: str) -> dict[str, Any]:
    """Scan a memory-write payload. Returns:
        {"ok": True, "blocked": bool, "severity": "block"|"warn"|"none",
         "patterns": [{"id", "match"}], "rationale": str}
    """
    if not text or not isinstance(text, str):
        return {"ok": True, "blocked": False, "severity": "none", "patterns": [], "rationale": ""}

    block_hits = []
    for rx, pid in BLOCK_PATTERNS:
        m = re.search(rx, text)
        if m:
            block_hits.append({"id": pid, "match": (m.group(0))[:120]})

    warn_hits = []
    for rx, pid in WARN_PATTERNS:
        m = re.search(rx, text)
        if m:
            warn_hits.append({"id": pid, "match": (m.group(0))[:120]})

    if _caps_heuristic(text):
        block_hits.append({"id": "all-caps-directive-block", "match": text[:80] + "..."})

    if block_hits:
        return {
            "ok": True, "blocked": True, "severity": "block",
            "patterns": block_hits,
            "rationale": "Sanctum blocks memory-poisoning patterns at the API layer. "
                         f"Triggered: {', '.join(p['id'] for p in block_hits)}. "
                         "If this is a legitimate operator-set directive, edit the target file directly "
                         "from your own machine instead of POSTing through the API.",
        }

    if warn_hits:
        return {
            "ok": True, "blocked": False, "severity": "warn",
            "patterns": warn_hits,
            "rationale": f"Soft warning: {', '.join(p['id'] for p in warn_hits)}. Allowed.",
        }

    return {"ok": True, "blocked": False, "severity": "none", "patterns": [], "rationale": ""}


def audit_block(target: str, agent: str, title: str, snippet: str, scan_result: dict[str, Any],
                audit_path: Path) -> None:
    """Append one row to blocked-writes.jsonl whenever a write is rejected.
    Operator audits this file periodically."""
    try:
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "target": target,
            "agent": agent,
            "title": title,
            "snippet": (snippet or "")[:240],
            "patterns": scan_result.get("patterns", []),
            "rationale": scan_result.get("rationale", ""),
        }
        with audit_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # never fail the response on audit-log failure
