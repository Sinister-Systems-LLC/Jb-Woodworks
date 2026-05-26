"""Instagram audio intake (P1 stub).

Author: RKOJ-ELENO :: 2026-05-26

Activates when `yt-dlp` (download) and `openai-whisper` (transcribe) are importable.
Otherwise records the URL as `status=pending` with a clear `short_summary` explaining what is missing.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
VAULT_INTAKE = REPO_ROOT / "vault" / "intake"

IG_URL_RE = re.compile(
    r"^https?://(?:www\.)?instagram\.com/(?:reel|p|tv|reels)/(?P<shortcode>[A-Za-z0-9_\-]+)",
    re.IGNORECASE,
)


def parse_ig_url(url: str) -> str:
    m = IG_URL_RE.match(url.strip())
    if not m:
        raise ValueError(f"not an instagram URL: {url!r}")
    return m.group("shortcode")


def compute_id(shortcode: str) -> str:
    h = hashlib.sha1(shortcode.encode("utf-8")).hexdigest()[:8]
    safe = re.sub(r"[^a-z0-9]+", "-", shortcode.lower()).strip("-")
    return f"ig-{safe}-{h}"


def _has(bin_name: str) -> bool:
    return shutil.which(bin_name) is not None


def intake(url: str, force: bool = False) -> dict[str, Any]:
    shortcode = parse_ig_url(url)
    item_id = compute_id(shortcode)
    intake_dir = VAULT_INTAKE / item_id
    intake_dir.mkdir(parents=True, exist_ok=True)

    missing = []
    if not _has("yt-dlp"):
        missing.append("yt-dlp")
    # whisper-cli OR python whisper module; we treat absence of both as "transcribe unavailable"
    if not _has("whisper") and not _has("whisper-cli"):
        try:
            import whisper  # noqa: F401
        except ImportError:
            missing.append("whisper (python module or whisper-cli binary)")

    audio_path = intake_dir / "audio.m4a"
    transcript_path = intake_dir / "transcript.txt"

    raw_meta: dict[str, Any] = {
        "shortcode": shortcode,
        "missing_deps": missing,
    }

    if missing:
        short = (
            f"IG intake pending — missing: {', '.join(missing)}. "
            "Re-run when deps installed; URL recorded for later."
        )
        return {
            "id": item_id,
            "source_url": url,
            "source_type": "ig_audio",
            "intake_ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "status": "pending",
            "title": f"ig/{shortcode}",
            "short_summary": short,
            "tags": "ig,audio,deps-missing",
            "raw_metadata_json": json.dumps(raw_meta),
            "clone_dir": str(intake_dir),
            "intake_dir": str(intake_dir),
            "readme_excerpt": "",
            "_intake_ok": False,
            "_reason": "deps-missing",
        }

    # Deps present — do the real flow.
    if not audio_path.exists() or force:
        cmd = ["yt-dlp", "-x", "--audio-format", "m4a", "-o", str(audio_path), url]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if proc.returncode != 0:
            raw_meta["yt_dlp_error"] = proc.stderr.strip()[:500]
            return {
                "id": item_id,
                "source_url": url,
                "source_type": "ig_audio",
                "intake_ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "status": "pending",
                "title": f"ig/{shortcode}",
                "short_summary": f"yt-dlp failed: {proc.stderr.strip()[:200]}",
                "tags": "ig,audio,download-failed",
                "raw_metadata_json": json.dumps(raw_meta),
                "clone_dir": str(intake_dir),
                "intake_dir": str(intake_dir),
                "readme_excerpt": "",
                "_intake_ok": False,
                "_reason": "yt-dlp-error",
            }

    transcript = ""
    if not transcript_path.exists() or force:
        try:
            import whisper  # type: ignore

            model = whisper.load_model("base")
            result = model.transcribe(str(audio_path))
            transcript = (result.get("text") or "").strip()
            transcript_path.write_text(transcript, encoding="utf-8")
        except Exception as e:  # noqa: BLE001
            raw_meta["whisper_error"] = repr(e)[:500]
            transcript = ""
    else:
        transcript = transcript_path.read_text(encoding="utf-8", errors="replace")

    short_summary = (transcript[:200] + ("..." if len(transcript) > 200 else "")) or "(no transcript)"

    return {
        "id": item_id,
        "source_url": url,
        "source_type": "ig_audio",
        "intake_ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "analyzing",
        "title": f"ig/{shortcode}",
        "short_summary": short_summary,
        "tags": "ig,audio",
        "raw_metadata_json": json.dumps(raw_meta),
        "clone_dir": str(intake_dir),
        "intake_dir": str(intake_dir),
        "readme_excerpt": transcript[:4_000],
        "_intake_ok": True,
    }


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    out = intake(args.url, force=args.force)
    out.pop("readme_excerpt", None)
    print(json.dumps(out, indent=2, default=str))
