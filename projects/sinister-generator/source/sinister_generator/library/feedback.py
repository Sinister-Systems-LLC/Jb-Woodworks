"""Feedback scanner — reads the operator's ✅ Yes / ❌ No / 📥 Refs sorting
and embeds learning into memory/learning/<brand>.json.

The operator's file moves ARE the training signal. This module turns those
file moves into structured memory that the next generation uses.
"""
# Author: RKOJ-ELENO :: 2026-05-23

from __future__ import annotations

import json
import pathlib
import time
from dataclasses import asdict, dataclass, field
from typing import List, Optional

from .registry import BrandConfig, ensure_sorter_folders, get_brand

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp")


@dataclass
class LearningEntry:
    """One row of operator feedback derived from a file in ✅ Yes / ❌ No / 📥 Refs."""
    kind: str  # "endorsed" | "rejected" | "reference"
    path: str  # absolute path to the image (in the desktop library)
    name: str  # basename
    sidecar_meta: Optional[dict] = None  # contents of .meta.json sidecar if present
    note: Optional[str] = None  # contents of .endorse.txt / .reject.txt / .ref.txt if present
    discovered_utc: str = ""


@dataclass
class LearningState:
    brand: str
    refreshed_utc: str = ""
    great: List[LearningEntry] = field(default_factory=list)          # 💎 top tier
    good: List[LearningEntry] = field(default_factory=list)           # ✅ on-theme but needs work
    size_off: List[LearningEntry] = field(default_factory=list)       # 📐 reshape candidate
    wrong_guy: List[LearningEntry] = field(default_factory=list)      # 👤 good concept, char drift
    wrong_style: List[LearningEntry] = field(default_factory=list)    # 🎨 good comp, wrong vibe
    skip_concept: List[LearningEntry] = field(default_factory=list)   # ♻️ drop this prompt direction
    rejected: List[LearningEntry] = field(default_factory=list)       # ❌ anti-patterns
    references: List[LearningEntry] = field(default_factory=list)     # 📥 operator-supplied refs

    # Legacy alias for any pre-3-tier consumers that read `endorsed`.
    @property
    def endorsed(self) -> List[LearningEntry]:
        return [*self.great, *self.good]


def _scan_dir(d: pathlib.Path, kind: str) -> List[LearningEntry]:
    out: List[LearningEntry] = []
    if not d.is_dir():
        return out
    for p in sorted(d.iterdir()):
        if not p.is_file():
            continue
        if p.suffix.lower() not in IMAGE_EXTS:
            continue
        meta_path = p.with_suffix(p.suffix + ".meta.json")
        meta_data = None
        if meta_path.is_file():
            try:
                meta_data = json.loads(meta_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                meta_data = None
        note = None
        for ext in (".endorse.txt", ".reject.txt", ".ref.txt", ".note.txt"):
            note_path = p.with_suffix(p.suffix + ext)
            if note_path.is_file():
                try:
                    note = note_path.read_text(encoding="utf-8").strip()
                except OSError:
                    pass
                break
        out.append(
            LearningEntry(
                kind=kind,
                path=str(p),
                name=p.name,
                sidecar_meta=meta_data,
                note=note,
                discovered_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            )
        )
    return out


def refresh_feedback(brand: str) -> LearningState:
    """Scan the brand's desktop library + write a fresh learning JSON.

    Call this:
      - Before any generation (so the next call honors the latest operator feedback)
      - After the operator moves files around (so the learning catches up)
      - On a schedule (a watch-mode is possible but not required)
    """
    cfg: BrandConfig = get_brand(brand)
    # Self-heal: seed brands don't get their sorter folders scaffolded by
    # init_brand(); ensure they exist before scanning so the operator always
    # has a drag-drop target.
    ensure_sorter_folders(cfg)
    # Scan the 7-tier sort folders + legacy ✅ Yes / ❌ No so existing content
    # surfaces in the right bucket while the operator migrates.
    great_entries = _scan_dir(cfg.great_dir, "great")
    good_entries = _scan_dir(cfg.good_dir, "good")
    size_off_entries = _scan_dir(cfg.size_off_dir, "size_off")
    wrong_guy_entries = _scan_dir(cfg.wrong_guy_dir, "wrong_guy")
    wrong_style_entries = _scan_dir(cfg.wrong_style_dir, "wrong_style")
    skip_concept_entries = _scan_dir(cfg.skip_concept_dir, "skip_concept")
    bad_entries = _scan_dir(cfg.bad_dir, "rejected")

    # Legacy paths
    legacy_yes = cfg.desktop_dir / "✅ Yes"
    legacy_no = cfg.desktop_dir / "❌ No"
    if legacy_yes.is_dir():
        good_entries.extend(_scan_dir(legacy_yes, "good"))
    if legacy_no.is_dir():
        bad_entries.extend(_scan_dir(legacy_no, "rejected"))

    state = LearningState(
        brand=brand,
        refreshed_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        great=great_entries,
        good=good_entries,
        size_off=size_off_entries,
        wrong_guy=wrong_guy_entries,
        wrong_style=wrong_style_entries,
        skip_concept=skip_concept_entries,
        rejected=bad_entries,
        references=_scan_dir(cfg.refs_dir, "reference"),
    )
    cfg.learning_path.parent.mkdir(parents=True, exist_ok=True)
    cfg.learning_path.write_text(
        json.dumps(asdict(state), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return state


def get_endorsed_refs(brand: str, max_refs: int = 4) -> List[pathlib.Path]:
    """Return paths of operator-endorsed images + operator-supplied references,
    ranked so the most-recent + explicitly-referenced come first."""
    cfg = get_brand(brand)
    refs: List[pathlib.Path] = []
    if not cfg.learning_path.is_file():
        refresh_feedback(brand)
    try:
        data = json.loads(cfg.learning_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return refs
    # References dir first (operator's explicit "use these as canonical")
    for entry in data.get("references", []):
        refs.append(pathlib.Path(entry["path"]))
    # Then GREAT tier (operator would actually use these)
    for entry in data.get("great", []):
        refs.append(pathlib.Path(entry["path"]))
    # Then GOOD tier (on theme but needs work — secondary signal)
    for entry in data.get("good", []):
        refs.append(pathlib.Path(entry["path"]))
    # Legacy `endorsed` field still consulted for older learning.json files
    for entry in data.get("endorsed", []):
        refs.append(pathlib.Path(entry["path"]))
    # De-dup + cap
    seen: set = set()
    deduped = []
    for r in refs:
        key = str(r).lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)
        if len(deduped) >= max_refs:
            break
    return deduped


def get_anti_patterns(brand: str) -> str:
    """Return a prompt-ready string describing what the operator has flagged
    as wrong. Pulls notes from ❌ Bad (hard rejects) + 👤 Wrong Guy + 🎨 Wrong
    Style (specific failure modes that should NOT repeat). Skips 📐 Size Off
    notes — those describe aspect/framing fixes, not prompt mistakes.

    Empty string when no notes yet.
    """
    cfg = get_brand(brand)
    if not cfg.learning_path.is_file():
        refresh_feedback(brand)
    try:
        data = json.loads(cfg.learning_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""

    sections: List[str] = []

    def collect(key: str, label: str, cap: int = 6) -> None:
        entries = data.get(key, []) or []
        notes = [e["note"] for e in entries if e.get("note")]
        if not notes:
            return
        bullets = "\n".join(f"  • {n}" for n in notes[:cap])
        sections.append(f"{label}:\n{bullets}")

    collect("rejected", "ANTI-PATTERNS (operator rejected outright — do NOT repeat)")
    collect("wrong_guy", "CHARACTER-DRIFT ANTI-PATTERNS (concept ok but character was wrong)")
    collect("wrong_style", "STYLE ANTI-PATTERNS (composition ok but wrong vibe/lighting/palette)")
    collect("skip_concept", "CONCEPT ANTI-PATTERNS (operator said drop this prompt direction)")

    return "\n\n".join(sections)
