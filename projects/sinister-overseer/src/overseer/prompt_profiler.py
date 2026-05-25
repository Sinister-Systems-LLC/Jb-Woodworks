# Author: RKOJ-ELENO :: 2026-05-25
"""prompt_profiler.py -- Overseer prompt style profiler.

Scans operator-utterances.jsonl, extracts style traits, builds per-user
profiles, and provides a --suggest-prompt helper that enhances vague prompts
using the learned profile.

Profiles saved to: _shared-memory/prompt-profiles/<profile_id>.json

CLI usage:
    python prompt_profiler.py --scan [--profile operator|leo|all]
    python prompt_profiler.py --show <profile_id>
    python prompt_profiler.py --suggest-prompt "some vague text"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

SANCTUM_ROOT = Path("D:/Sinister Sanctum")
SHARED_MEM = SANCTUM_ROOT / "_shared-memory"
UTTERANCES_LOG = SHARED_MEM / "operator-utterances.jsonl"
PROFILES_DIR = SHARED_MEM / "prompt-profiles"

# Known urgency / profanity / shorthand patterns from operator style
_URGENCY_PATTERNS = re.compile(
    r"\b(now|asap|immediately|stop|fix|do this|get to work|right now|fast|quick|dont|do not)\b",
    re.IGNORECASE,
)
_PROFANITY = re.compile(
    r"\b(fuck|shit|damn|ass|crap|wtf|holy)\b",
    re.IGNORECASE,
)
_SHORTHAND = re.compile(
    r"\b(u|ur|gonna|wanna|hafve|taht|geneartor|autoinmous|efficent|parralll|iwhen|agetnts|deminsh)\b",
    re.IGNORECASE,
)

# Common action verbs used by RKOJ in directives
_VERB_RE = re.compile(
    r"\b(make|add|fix|update|create|build|run|stop|start|check|review|test|ship|push|set|get|do|use|read|write|remove|enable|disable|deploy|install|scan|log|track|load|show|send|loop|keep|let)\b",
    re.IGNORECASE,
)

# Domain vocab specific to Sinister Sanctum operator
_DOMAIN_VOCAB = re.compile(
    r"\b(sinister|sanctum|overseer|eve|fleet|agent|loop|swarm|spawn|lane|doctrine|brain|memory|orchestrat|terminal|session|skill|tool|utterance|heartbeat|inbox|queue|push|branch|commit|deploy|keybox|pi|snap|tiktok|rka|ksu|susfs|lukeshield|tricky|panel|chatbot|sleight|generator|phantom|quantum|vault|link|mesh|coordinator|boot|worker|relay|proxy|gateway|blueprint|scaffold|smoke|claim|acked|resolved|pending|operator|operator-action|schtask|winget|pip|git|gh|mcp|oauth|apikey)\b",
    re.IGNORECASE,
)

# Frustration signals (ALL-CAPS sentences, repeated punctuation, etc.)
_FRUSTRATION_RE = re.compile(r"[A-Z]{5,}|!{2,}|\?{2,}|fuck|WHY|STOP|FIX.*AGAIN|ONCE AGAIN")

# Sentence pattern templates commonly used by operator
_ACTION_PATTERNS = [
    (re.compile(r"\b(make sure|always|never|dont|do not)\b.*", re.IGNORECASE), "imperative-directive"),
    (re.compile(r"\b(update (the|this|memory|claude\.md|docs|brain))\b", re.IGNORECASE), "update-memory"),
    (re.compile(r"\b(get to work|ship it|do this|now)\b", re.IGNORECASE), "urgency-cue"),
    (re.compile(r"\b(loop|swarm|agent|spawn)\b", re.IGNORECASE), "fleet-management"),
    (re.compile(r"\b(test|verify|confirm|smoke|check)\b", re.IGNORECASE), "verification-request"),
    (re.compile(r"\b(remember|dont forget|never forget|canonical|hard rule)\b", re.IGNORECASE), "memory-anchor"),
]


# ---------------------------------------------------------------------------
# Profile building
# ---------------------------------------------------------------------------

def _empty_profile(profile_id: str, display: str) -> dict:
    return {
        "profile_id": profile_id,
        "display": display,
        "last_updated": "",
        "utterance_count": 0,
        "style": {
            "avg_words_per_message": 0.0,
            "uses_urgency": False,
            "uses_profanity": False,
            "uses_shorthand": False,
            "directness": "unknown",
            "avg_sentence_length": 0.0,
        },
        "top_verbs": [],
        "domain_vocab": [],
        "action_patterns": [],
        "learned_preferences": [],
        "frustration_signals": [],
    }


def _identify_speaker(row: dict, profile: str) -> bool:
    """Return True if this row belongs to the requested profile."""
    if profile == "all":
        return True
    slug = row.get("session_slug", "").lower()
    agent = row.get("agent", "").lower()
    # "operator" = anything not from a specific named agent (or any row)
    if profile == "operator":
        # operator utterances don't have an agent field pointing at a bot;
        # they come from session_slug = 'sanctum' or similar master slugs
        return slug in ("sanctum", "master", "operator", "") or agent in ("", "operator")
    if profile == "leo":
        return slug in ("leo", "leo-setup") or agent == "leo"
    return True


def _analyze_texts(texts: list[str]) -> dict:
    """Compute style metrics from a list of message texts."""
    if not texts:
        return {}

    word_counts = [len(t.split()) for t in texts]
    avg_words = sum(word_counts) / len(word_counts)

    urgency_hits = sum(1 for t in texts if _URGENCY_PATTERNS.search(t))
    profanity_hits = sum(1 for t in texts if _PROFANITY.search(t))
    shorthand_hits = sum(1 for t in texts if _SHORTHAND.search(t))

    # Directness heuristic: ratio of imperative starters
    imperative_count = sum(
        1 for t in texts
        if re.match(r"^\s*(make|add|fix|update|create|build|run|stop|do|get|use|set|push|check|enable|deploy|install|ship|scan|loop)\b", t, re.IGNORECASE)
    )
    directness_ratio = imperative_count / len(texts)
    directness = "high" if directness_ratio >= 0.4 else ("medium" if directness_ratio >= 0.2 else "low")

    # Sentence length approximation (split on . ! ?)
    all_sentences = []
    for t in texts:
        parts = re.split(r"[.!?]+", t)
        all_sentences.extend(p.strip() for p in parts if p.strip())
    avg_sentence_len = (
        sum(len(s.split()) for s in all_sentences) / len(all_sentences)
        if all_sentences else 0.0
    )

    # Verb extraction
    verb_counter: Counter = Counter()
    for t in texts:
        for m in _VERB_RE.finditer(t):
            verb_counter[m.group(0).lower()] += 1
    top_verbs = [v for v, _ in verb_counter.most_common(20)]

    # Domain vocab
    domain_counter: Counter = Counter()
    for t in texts:
        for m in _DOMAIN_VOCAB.finditer(t):
            domain_counter[m.group(0).lower()] += 1
    domain_vocab = [v for v, _ in domain_counter.most_common(30)]

    # Action pattern classification
    pattern_counter: Counter = Counter()
    for t in texts:
        for pat_re, pat_label in _ACTION_PATTERNS:
            if pat_re.search(t):
                pattern_counter[pat_label] += 1
    action_patterns = [p for p, _ in pattern_counter.most_common(10)]

    # Frustration signals
    frustration_examples: list[str] = []
    for t in texts:
        for m in _FRUSTRATION_RE.finditer(t):
            snippet = t[max(0, m.start() - 20) : m.end() + 20].strip()
            frustration_examples.append(snippet)
    # Deduplicate and cap
    seen: set[str] = set()
    unique_frustration: list[str] = []
    for ex in frustration_examples:
        key = ex[:40]
        if key not in seen:
            seen.add(key)
            unique_frustration.append(ex)
        if len(unique_frustration) >= 15:
            break

    # Learned preferences inferred from patterns
    learned_prefs: list[str] = []
    if "fleet-management" in action_patterns:
        learned_prefs.append("loop=relentless + swarm=on by default")
    if "verification-request" in action_patterns:
        learned_prefs.append("test and verify before claiming done (no-bullshit doctrine)")
    if "memory-anchor" in action_patterns:
        learned_prefs.append("update brain/CLAUDE.md after every doctrine-class finding")
    if "update-memory" in action_patterns:
        learned_prefs.append("agent writes memory updates without being re-asked")
    if profanity_hits / max(len(texts), 1) > 0.1:
        learned_prefs.append("operator uses direct profanity-laced language when frustrated — don't hedge")
    if "urgency-cue" in action_patterns:
        learned_prefs.append("execute immediately, do not ask for confirmation on routine tasks")
    if directness == "high":
        learned_prefs.append("operator prefers precise imperative directives — mirror that tone in replies")

    return {
        "avg_words_per_message": round(avg_words, 1),
        "uses_urgency": urgency_hits > len(texts) * 0.3,
        "uses_profanity": profanity_hits > 0,
        "uses_shorthand": shorthand_hits > len(texts) * 0.05,
        "directness": directness,
        "avg_sentence_length": round(avg_sentence_len, 1),
        "top_verbs": top_verbs,
        "domain_vocab": domain_vocab,
        "action_patterns": action_patterns,
        "learned_preferences": learned_prefs,
        "frustration_signals": unique_frustration,
    }


# ---------------------------------------------------------------------------
# PromptProfiler class
# ---------------------------------------------------------------------------

class PromptProfiler:
    """Builds and manages per-user prompt style profiles."""

    def __init__(self, sanctum_root: Path = SANCTUM_ROOT) -> None:
        self.sanctum_root = sanctum_root
        self.utterances_log = sanctum_root / "_shared-memory" / "operator-utterances.jsonl"
        self.profiles_dir = sanctum_root / "_shared-memory" / "prompt-profiles"

    def _load_utterances(self) -> list[dict]:
        if not self.utterances_log.is_file():
            return []
        rows: list[dict] = []
        try:
            for line in self.utterances_log.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        except OSError:
            pass
        return rows

    def scan(self, profiles: list[str] | None = None) -> dict[str, dict]:
        """Scan utterances and build/refresh the requested profiles."""
        if profiles is None:
            profiles = ["operator"]

        rows = self._load_utterances()
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

        results: dict[str, dict] = {}
        for profile_id in profiles:
            if profile_id == "all":
                # Expand "all" to known profiles
                results.update(self.scan(["operator", "leo"]))
                continue

            display_map = {
                "operator": "RKOJ-ELENO (operator)",
                "leo": "Leo (collaborator)",
            }
            display = display_map.get(profile_id, profile_id)

            # Filter texts for this profile
            texts: list[str] = []
            for row in rows:
                if not _identify_speaker(row, profile_id):
                    continue
                text = (row.get("message_full") or row.get("text") or row.get("preview") or "").strip()
                if text:
                    texts.append(text)

            profile = _empty_profile(profile_id, display)
            profile["utterance_count"] = len(texts)
            profile["last_updated"] = datetime.now(timezone.utc).isoformat()

            if texts:
                analysis = _analyze_texts(texts)
                profile["style"].update({
                    "avg_words_per_message": analysis.get("avg_words_per_message", 0.0),
                    "uses_urgency": analysis.get("uses_urgency", False),
                    "uses_profanity": analysis.get("uses_profanity", False),
                    "uses_shorthand": analysis.get("uses_shorthand", False),
                    "directness": analysis.get("directness", "unknown"),
                    "avg_sentence_length": analysis.get("avg_sentence_length", 0.0),
                })
                profile["top_verbs"] = analysis.get("top_verbs", [])
                profile["domain_vocab"] = analysis.get("domain_vocab", [])
                profile["action_patterns"] = analysis.get("action_patterns", [])
                profile["learned_preferences"] = analysis.get("learned_preferences", [])
                profile["frustration_signals"] = analysis.get("frustration_signals", [])

            out_path = self.profiles_dir / f"{profile_id}.json"
            try:
                out_path.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
                print(f"[profiler] Wrote profile: {out_path}  ({len(texts)} utterances)")
            except OSError as e:
                print(f"[profiler] ERROR writing profile {profile_id}: {e}", file=sys.stderr)

            results[profile_id] = profile

        return results

    def show(self, profile_id: str) -> dict | None:
        """Load and return a saved profile, or None if not found."""
        path = self.profiles_dir / f"{profile_id}.json"
        if not path.is_file():
            print(f"[profiler] Profile not found: {path}", file=sys.stderr)
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            print(f"[profiler] ERROR reading profile {profile_id}: {e}", file=sys.stderr)
            return None

    def suggest_prompt(self, text: str, profile_id: str = "operator") -> dict:
        """Enhance a short/vague prompt using the loaded operator profile."""
        profile = self.show(profile_id)
        if profile is None:
            # Try to scan first
            self.scan([profile_id])
            profile = self.show(profile_id)

        enhanced = text.strip()
        prefs = profile.get("learned_preferences", []) if profile else []
        style = profile.get("style", {}) if profile else {}

        # Heuristic 1: too short → add working directory context
        word_count = len(enhanced.split())
        if word_count < 10:
            enhanced += " in D:\\Sinister Sanctum"

        # Heuristic 2: fleet preference → add loop/swarm hint
        if any("loop" in p or "swarm" in p for p in prefs):
            if not re.search(r"\b(loop|swarm)\b", enhanced, re.IGNORECASE):
                enhanced += " — loop and swarm mode on"

        # Heuristic 3: no-bullshit doctrine → verification request
        if any("test and verify" in p or "no-bullshit" in p for p in prefs):
            if not re.search(r"\b(test|verify|confirm|smoke|check|before claiming)\b", enhanced, re.IGNORECASE):
                enhanced += "; test and verify before claiming done"

        # Heuristic 4: memory-anchor tendency → remind to update brain
        if any("update brain" in p or "CLAUDE.md" in p for p in prefs):
            if not re.search(r"\b(update|memory|brain|doctrine)\b", enhanced, re.IGNORECASE):
                enhanced += "; update memory / brain with findings"

        # Heuristic 5: high directness → ensure imperative opener
        if style.get("directness") == "high":
            if not re.match(r"^\s*(make|add|fix|update|create|build|run|stop|do|get|use|set|push|check|enable|deploy|install|ship|scan|loop)\b", enhanced, re.IGNORECASE):
                enhanced = "Do: " + enhanced

        return {
            "original": text,
            "enhanced": enhanced,
            "profile_used": profile_id,
            "utterances_trained_on": profile.get("utterance_count", 0) if profile else 0,
        }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="prompt-profiler",
        description="Overseer Prompt Profiler — scan utterances + build style profiles.",
    )
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument(
        "--scan",
        action="store_true",
        help="Scan operator-utterances.jsonl and build/refresh profiles.",
    )
    g.add_argument(
        "--show",
        metavar="PROFILE_ID",
        help="Print a saved profile as JSON.",
    )
    g.add_argument(
        "--suggest-prompt",
        metavar="TEXT",
        dest="suggest",
        help="Enhance a short/vague prompt using the operator profile.",
    )
    p.add_argument(
        "--profile",
        default="operator",
        choices=["operator", "leo", "all"],
        help="Which profile(s) to scan/use (default: operator).",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    profiler = PromptProfiler(SANCTUM_ROOT)

    if args.scan:
        profiles_to_scan = ["operator", "leo"] if args.profile == "all" else [args.profile]
        results = profiler.scan(profiles_to_scan)
        for pid, prof in results.items():
            summary = {
                "profile_id": pid,
                "utterance_count": prof["utterance_count"],
                "directness": prof["style"]["directness"],
                "uses_urgency": prof["style"]["uses_urgency"],
                "uses_profanity": prof["style"]["uses_profanity"],
                "top_verbs_preview": prof["top_verbs"][:8],
                "domain_vocab_preview": prof["domain_vocab"][:8],
                "learned_preferences": prof["learned_preferences"],
            }
            print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0

    if args.show:
        profile = profiler.show(args.show)
        if profile is None:
            return 1
        print(json.dumps(profile, indent=2, ensure_ascii=False))
        return 0

    if args.suggest:
        result = profiler.suggest_prompt(args.suggest, profile_id=args.profile)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
