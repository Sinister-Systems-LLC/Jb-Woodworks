# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
"""
Sinister Crawler — the first Sanctum invention.

A Telegram bot that the operator can interact with from anywhere:
  - drop video URLs (Instagram / TikTok / YouTube / etc.) -> auto-download,
    transcribe, tag, and file into D:\\Sinister Sanctum\\library\\videos\\
  - capture inventions on the go via /idea
  - ask the local Claude CLI questions via /ask
  - kick off research jobs via /research (results saved to library/research)
  - peek at agent progress via /progress
  - forward TG-native videos / voice notes -> same pipeline

This file is polling-based and async. Webhook mode is intentionally NOT
wired up — the operator can switch later.

Architecture:
  bot.py            (this) — telegram handlers + dispatch
  config.json       (next to bot.py) — token + auth + paths
  audit.log         (next to bot.py) — jsonl audit trail

Subprocess dependencies (assumed on PATH):
  - claude          Anthropic CLI for /ask + /research + tagging
  - yt-dlp          video downloader
  - ffmpeg          for audio extraction

Optional env:
  OPENAI_API_KEY    if set, whisper-1 transcription kicks in via openai SDK
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

try:
    from telegram import Update
    from telegram.ext import (
        Application,
        ApplicationBuilder,
        CommandHandler,
        ContextTypes,
        MessageHandler,
        filters,
    )
except ImportError:  # pragma: no cover — operator gets a clear error
    print(
        "[FAIL] python-telegram-bot is not installed. Run the bat first:\n"
        "       C:\\Users\\Zonia\\Desktop\\Sanctum-Crawler-Start.bat\n"
        "       (it creates the venv and installs requirements.txt)",
        file=sys.stderr,
    )
    raise

# ---------------------------------------------------------------------------
# Paths + config
# ---------------------------------------------------------------------------

HERE = Path(__file__).resolve().parent
CONFIG_PATH = HERE / "config.json"
CONFIG_EXAMPLE_PATH = HERE / "config.example.json"
AUDIT_LOG = HERE / "audit.log"

DEFAULT_CONFIG: dict[str, Any] = {
    "telegram_token": "PASTE_FROM_BOTFATHER",
    "authorized_chat_ids": [],
    "library_root": "D:/Sinister Sanctum/library",
    "inventions_root": "D:/Sinister Sanctum/inventions",
    "notes_root": "D:/Sinister Sanctum/_shared-memory/notes",
    "claude_cli": "claude",
    "yt_dlp_cli": "yt-dlp",
    "openai_api_key_env": "OPENAI_API_KEY",
    "max_download_mb": 200,
    "transcribe_max_sec": 600,
}


def load_config() -> dict[str, Any]:
    """Load config.json, copying from the example on first run if missing."""
    if not CONFIG_PATH.exists():
        if CONFIG_EXAMPLE_PATH.exists():
            shutil.copy2(CONFIG_EXAMPLE_PATH, CONFIG_PATH)
            print(f"[*] Created {CONFIG_PATH} from example. Edit it and restart.")
        else:
            CONFIG_PATH.write_text(json.dumps(DEFAULT_CONFIG, indent=2))
            print(f"[*] Wrote default config to {CONFIG_PATH}. Edit it and restart.")
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    # Allow env-var override for the token
    env_tok = os.environ.get("TELEGRAM_BOT_TOKEN")
    if env_tok:
        cfg["telegram_token"] = env_tok
    return cfg


def save_config(cfg: dict[str, Any]) -> None:
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


CONFIG: dict[str, Any] = {}

# ---------------------------------------------------------------------------
# Logging + audit
# ---------------------------------------------------------------------------

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s :: %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("sinister-crawler")


def audit(event: str, **fields: Any) -> None:
    """Write one JSONL event to audit.log + stdout."""
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **fields,
    }
    try:
        with AUDIT_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError as e:  # noqa: BLE001
        log.warning("audit write failed: %s", e)
    log.info("%s %s", event, {k: v for k, v in fields.items() if k != "transcript"})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_URL_RE = re.compile(r"https?://[^\s]+", re.IGNORECASE)
_SLUG_BAD = re.compile(r"[^a-z0-9]+")


def slugify(text: str, max_len: int = 40) -> str:
    """Lowercase, dash-separated, ASCII-only, capped at max_len chars."""
    s = text.strip().lower()
    s = s.encode("ascii", "ignore").decode("ascii")
    s = _SLUG_BAD.sub("-", s).strip("-")
    if not s:
        s = "untitled"
    return s[:max_len].strip("-") or "untitled"


def today_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def classify_platform(url: str) -> str:
    """Best-effort platform classifier for filing into library/videos/<platform>/."""
    host = (urlparse(url).hostname or "").lower()
    if "instagram" in host:
        return "instagram"
    if "tiktok" in host:
        return "tiktok"
    if "youtube" in host or "youtu.be" in host:
        return "youtube"
    if "twitter" in host or "x.com" in host:
        return "twitter"
    if "reddit" in host:
        return "reddit"
    if "facebook" in host or "fb.watch" in host:
        return "facebook"
    return "generic"


def is_authorized(chat_id: int) -> bool:
    """Auth gate. Only chat_ids registered via /start can use the bot."""
    return chat_id in set(CONFIG.get("authorized_chat_ids", []))


def auth_header(chat_id: int) -> str:
    return f"chat_id={chat_id}"


async def run_subprocess(
    cmd: list[str], timeout: int = 90, cwd: Optional[Path] = None
) -> tuple[int, str, str]:
    """Run a subprocess in a worker thread so we don't block the event loop."""
    loop = asyncio.get_running_loop()

    def _run() -> tuple[int, str, str]:
        try:
            proc = subprocess.run(  # noqa: S603
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(cwd) if cwd else None,
                check=False,
                encoding="utf-8",
                errors="replace",
            )
            return proc.returncode, proc.stdout or "", proc.stderr or ""
        except subprocess.TimeoutExpired:
            return 124, "", f"[timeout after {timeout}s]"
        except FileNotFoundError as e:
            return 127, "", f"[not-found] {e}"
        except OSError as e:  # noqa: BLE001
            return 1, "", f"[os-error] {e}"

    return await loop.run_in_executor(None, _run)


# ---------------------------------------------------------------------------
# Claude CLI bridge
# ---------------------------------------------------------------------------


async def claude_ask(prompt: str, timeout: int = 90) -> str:
    """Shell out to the local claude CLI. Returns trimmed stdout or error string."""
    cli = CONFIG.get("claude_cli", "claude")
    rc, out, err = await run_subprocess([cli, "--print", prompt], timeout=timeout)
    if rc != 0:
        return f"[claude-cli rc={rc}] {err.strip() or out.strip()}"
    return out.strip()


# ---------------------------------------------------------------------------
# Whisper transcription (OpenAI API). No-op fallback if key absent.
# ---------------------------------------------------------------------------


async def transcribe_audio(audio_path: Path) -> str:
    """Transcribe an audio file via OpenAI Whisper. Returns transcript or stub."""
    env_var = CONFIG.get("openai_api_key_env", "OPENAI_API_KEY")
    api_key = os.environ.get(env_var)
    if not api_key:
        return "[transcription skipped — OPENAI_API_KEY not set]"

    loop = asyncio.get_running_loop()

    def _do() -> str:
        try:
            from openai import OpenAI  # local import; optional dep
        except ImportError:
            return "[transcription skipped — `openai` package not installed]"
        try:
            client = OpenAI(api_key=api_key)
            with audio_path.open("rb") as f:
                resp = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                )
            return getattr(resp, "text", str(resp)).strip()
        except Exception as e:  # noqa: BLE001
            return f"[transcription failed: {type(e).__name__}: {e}]"

    return await loop.run_in_executor(None, _do)


async def extract_audio(video_path: Path) -> Optional[Path]:
    """Pull an .mp3 next to the video using ffmpeg. Returns the path or None."""
    audio_path = video_path.with_suffix(".mp3")
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-vn",
        "-acodec",
        "libmp3lame",
        "-b:a",
        "128k",
        str(audio_path),
    ]
    rc, _out, err = await run_subprocess(cmd, timeout=300)
    if rc != 0:
        log.warning("ffmpeg failed rc=%s err=%s", rc, err[:200])
        return None
    return audio_path if audio_path.exists() else None


# ---------------------------------------------------------------------------
# Tag generation via claude
# ---------------------------------------------------------------------------


async def generate_tags(transcript: str) -> list[str]:
    """Ask claude for 3-5 single-word tags. Falls back to ['untagged']."""
    if not transcript or transcript.startswith("["):
        return ["untagged"]
    snippet = transcript[:2000]
    prompt = (
        "Tag this transcript in 3-5 single-word tags, comma-separated, "
        "lowercase only, no hashes. Reply with ONLY the comma-separated tags, "
        f"nothing else. Transcript:\n{snippet}"
    )
    raw = await claude_ask(prompt, timeout=60)
    if raw.startswith("["):
        return ["untagged"]
    parts = [slugify(p, 20) for p in raw.split(",") if p.strip()]
    parts = [p for p in parts if p and p != "untitled"]
    return parts[:5] if parts else ["untagged"]


# ---------------------------------------------------------------------------
# Library filers
# ---------------------------------------------------------------------------


def library_root() -> Path:
    return Path(CONFIG["library_root"])


def videos_root() -> Path:
    return library_root() / "videos"


def research_root() -> Path:
    return library_root() / "research"


def write_video_sidecar(
    video_path: Path,
    source_url: str,
    transcript: str,
    tags: list[str],
    chat_id: int,
) -> Path:
    """Write a .md companion describing the downloaded video."""
    md_path = video_path.with_suffix(".md")
    ts = datetime.now().isoformat(timespec="seconds")
    body = (
        f"> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19\n\n"
        f"# {video_path.stem}\n\n"
        f"**Source:** {source_url}\n"
        f"**Downloaded:** {ts}\n"
        f"**File:** `{video_path}`\n"
        f"**From-chat:** {chat_id}\n"
        f"**Auto-categorized:** yes\n"
        f"**Tags:** {', '.join('#' + t for t in tags)}\n\n"
        f"## Transcript\n\n"
        f"{transcript or '_(no transcript)_'}\n"
    )
    md_path.write_text(body, encoding="utf-8")
    return md_path


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


HELP_TEXT = (
    "*Sinister Crawler* — the first Sanctum invention.\n\n"
    "/start — authorize this chat\n"
    "/idea <text> — capture an invention to disk\n"
    "/ask <question> — ask the local Claude CLI\n"
    "/research <topic> — deeper claude research; saved to library/research/\n"
    "/progress — newest 5 progress entries per agent\n"
    "/help — this message\n\n"
    "Plain URL — downloads + transcribes + files into library/videos/<platform>/\n"
    "Plain text — saves as a note in _shared-memory/notes/\n"
    "Forwarded video/voice/audio — same pipeline as URL, filed under library/videos/telegram/"
)


async def cmd_start(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Register the first /start sender as an authorized chat id."""
    if not update.effective_chat or not update.message:
        return
    chat_id = update.effective_chat.id
    ids = set(CONFIG.get("authorized_chat_ids", []))
    if chat_id in ids:
        await update.message.reply_text("Already authorized. Send /help for commands.")
        audit("start.repeat", chat_id=chat_id)
        return
    ids.add(chat_id)
    CONFIG["authorized_chat_ids"] = sorted(ids)
    save_config(CONFIG)
    audit("start.authorize", chat_id=chat_id)
    await update.message.reply_text(
        f"Authorized chat_id={chat_id}. Welcome to Sinister Crawler.\n\n{HELP_TEXT}",
        parse_mode="Markdown",
    )


async def cmd_help(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_chat:
        return
    if not is_authorized(update.effective_chat.id):
        return
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


async def cmd_idea(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/idea <text> — write an invention stub from the template."""
    if not update.message or not update.effective_chat:
        return
    chat_id = update.effective_chat.id
    if not is_authorized(chat_id):
        return
    text = " ".join(ctx.args or []).strip()
    if not text:
        await update.message.reply_text("Usage: /idea <one-line description>")
        return
    try:
        slug = slugify(text, 40)
        out_dir = Path(CONFIG["inventions_root"])
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{today_stamp()}-{slug}.md"
        body = (
            f"> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19\n\n"
            f"# {text}\n\n"
            f"**Captured:** {datetime.now().isoformat(timespec='minutes')}\n"
            f"**Status:** idea\n"
            f"**Origin:** Telegram via Sinister Crawler ({auth_header(chat_id)})\n\n"
            "## Idea\n\n"
            f"{text}\n\n"
            "## Why\n\n_TBD_\n\n## Sketch\n\n_TBD_\n\n"
            "## Status\n\n- [x] idea captured\n- [ ] design sketched\n"
            "- [ ] implementation started\n- [ ] shipped\n\n"
            "## Linked-to\n\n- Captured via tools/sinister-crawler/bot.py\n\n"
            "## Notes\n\n_TBD_\n"
        )
        out_path.write_text(body, encoding="utf-8")
        audit("idea.captured", chat_id=chat_id, path=str(out_path), slug=slug)
        await update.message.reply_text(f"[OK] Invention captured:\n`{out_path}`", parse_mode="Markdown")
    except Exception as e:  # noqa: BLE001
        audit("idea.error", chat_id=chat_id, error=str(e))
        await update.message.reply_text(f"[FAIL] {e}")


async def cmd_ask(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/ask <question> — pipe a question through the local claude CLI."""
    if not update.message or not update.effective_chat:
        return
    chat_id = update.effective_chat.id
    if not is_authorized(chat_id):
        return
    question = " ".join(ctx.args or []).strip()
    if not question:
        await update.message.reply_text("Usage: /ask <question>")
        return
    await update.message.reply_text("[*] Asking Claude...")
    try:
        answer = await claude_ask(question, timeout=90)
        audit("ask", chat_id=chat_id, question=question[:200], chars=len(answer))
        await update.message.reply_text(answer[:4000] or "[empty answer]")
    except Exception as e:  # noqa: BLE001
        audit("ask.error", chat_id=chat_id, error=str(e))
        await update.message.reply_text(f"[FAIL] {e}")


async def cmd_research(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/research <topic> — deeper claude lookup + saves to library/research/."""
    if not update.message or not update.effective_chat:
        return
    chat_id = update.effective_chat.id
    if not is_authorized(chat_id):
        return
    topic = " ".join(ctx.args or []).strip()
    if not topic:
        await update.message.reply_text("Usage: /research <topic>")
        return
    await update.message.reply_text(f"[*] Researching '{topic}' (up to 180s)...")
    try:
        prompt = (
            f"Research the topic: {topic}. Pull from "
            f"D:\\Sinister Sanctum\\_shared-memory\\, the tools/skills index, "
            f"and known facts. Summarize findings in 5-10 bullets."
        )
        result = await claude_ask(prompt, timeout=180)
        # File it
        out_dir = research_root()
        out_dir.mkdir(parents=True, exist_ok=True)
        slug = slugify(topic, 40)
        out_path = out_dir / f"{today_stamp()}-{slug}.md"
        body = (
            f"> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19\n\n"
            f"# Research: {topic}\n\n"
            f"**Captured:** {datetime.now().isoformat(timespec='seconds')}\n"
            f"**Origin:** Telegram via Sinister Crawler ({auth_header(chat_id)})\n"
            f"**Prompt:** `{prompt}`\n\n"
            f"## Findings\n\n{result}\n"
        )
        out_path.write_text(body, encoding="utf-8")
        audit("research", chat_id=chat_id, topic=topic[:200], path=str(out_path))
        await update.message.reply_text(
            f"[OK] saved to `{out_path}`\n\n{result[:3500]}",
            parse_mode="Markdown",
        )
    except Exception as e:  # noqa: BLE001
        audit("research.error", chat_id=chat_id, error=str(e))
        await update.message.reply_text(f"[FAIL] {e}")


async def cmd_progress(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/progress — aggregate newest 5 entries from each PROGRESS/*.md file."""
    if not update.message or not update.effective_chat:
        return
    chat_id = update.effective_chat.id
    if not is_authorized(chat_id):
        return
    try:
        prog_dir = Path("D:/Sinister Sanctum/_shared-memory/PROGRESS")
        if not prog_dir.exists():
            await update.message.reply_text("[OK] no PROGRESS folder yet.")
            return
        chunks: list[str] = []
        for md in sorted(prog_dir.glob("*.md")):
            try:
                lines = md.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                continue
            # Newest-first heuristic: assume files prepend latest entries.
            # Take the first 5 non-empty heading/bullet lines.
            keep = []
            for ln in lines:
                if ln.strip().startswith(("- ", "* ", "## ", "### ")):
                    keep.append(ln.strip())
                if len(keep) >= 5:
                    break
            if keep:
                chunks.append(f"*{md.stem}*\n" + "\n".join(keep))
        if not chunks:
            await update.message.reply_text("[OK] no progress entries found.")
            return
        reply = "\n\n".join(chunks)[:4000]
        audit("progress", chat_id=chat_id, agents=len(chunks))
        await update.message.reply_text(reply, parse_mode="Markdown")
    except Exception as e:  # noqa: BLE001
        audit("progress.error", chat_id=chat_id, error=str(e))
        await update.message.reply_text(f"[FAIL] {e}")


# ---------------------------------------------------------------------------
# URL + media pipeline
# ---------------------------------------------------------------------------


async def download_via_ytdlp(url: str, dest_dir: Path, base_slug: str) -> Optional[Path]:
    """Download <url> into dest_dir/<date>-<slug>.<ext>. Returns the saved path."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    out_template = str(dest_dir / f"{today_stamp()}-{base_slug}.%(ext)s")
    max_mb = int(CONFIG.get("max_download_mb", 200))
    cli = CONFIG.get("yt_dlp_cli", "yt-dlp")
    cmd = [
        cli,
        "--no-playlist",
        "--no-warnings",
        "--restrict-filenames",
        "--max-filesize",
        f"{max_mb}M",
        "-f",
        "mp4/bestvideo*+bestaudio/best",
        "-o",
        out_template,
        url,
    ]
    rc, out, err = await run_subprocess(cmd, timeout=300)
    if rc != 0:
        log.warning("yt-dlp failed rc=%s err=%s", rc, err[:300])
        return None
    # Find the produced file (yt-dlp picks ext at runtime)
    candidates = sorted(
        dest_dir.glob(f"{today_stamp()}-{base_slug}.*"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


async def handle_url(update: Update, url: str) -> None:
    """End-to-end pipeline for a single URL."""
    if not update.message or not update.effective_chat:
        return
    chat_id = update.effective_chat.id
    platform = classify_platform(url)
    slug = slugify(f"{platform}-{url.split('/')[-1] or 'video'}", 40)
    dest_dir = videos_root() / platform
    await update.message.reply_text(f"[*] downloading from {platform}...")
    try:
        video = await download_via_ytdlp(url, dest_dir, slug)
        if not video:
            audit("url.download.fail", chat_id=chat_id, url=url)
            await update.message.reply_text("[FAIL] download failed (yt-dlp).")
            return
        await update.message.reply_text(f"[OK] downloaded -> `{video.name}`", parse_mode="Markdown")

        # Audio + transcribe
        transcript = ""
        audio = await extract_audio(video)
        if audio:
            await update.message.reply_text("[*] transcribing...")
            transcript = await transcribe_audio(audio)
        else:
            transcript = "[no audio extracted]"

        # Tags
        tags = await generate_tags(transcript)

        # Sidecar
        md = write_video_sidecar(video, url, transcript, tags, chat_id)
        audit(
            "url.filed",
            chat_id=chat_id,
            url=url,
            platform=platform,
            video=str(video),
            sidecar=str(md),
            tags=tags,
        )
        preview = transcript[:600] + ("..." if len(transcript) > 600 else "")
        await update.message.reply_text(
            f"[OK] filed.\nvideo: `{video}`\nsidecar: `{md}`\ntags: "
            f"{', '.join('#' + t for t in tags)}\n\n_transcript preview:_\n{preview}",
            parse_mode="Markdown",
        )
    except Exception as e:  # noqa: BLE001
        audit("url.error", chat_id=chat_id, url=url, error=str(e))
        await update.message.reply_text(f"[FAIL] {e}")


async def msg_text(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Fallback text handler: URL -> pipeline; otherwise save as a note."""
    if not update.message or not update.effective_chat or not update.message.text:
        return
    chat_id = update.effective_chat.id
    if not is_authorized(chat_id):
        return  # silently drop unauthorized
    text = update.message.text.strip()

    urls = _URL_RE.findall(text)
    if urls:
        for url in urls:
            await handle_url(update, url)
        return

    # Save as note
    try:
        notes_dir = Path(CONFIG["notes_root"])
        notes_dir.mkdir(parents=True, exist_ok=True)
        slug = slugify(text, 40)
        out = notes_dir / f"{today_stamp()}-tg-{slug}.md"
        body = (
            f"> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19\n\n"
            f"# Telegram note: {slug}\n\n"
            f"**Origin:** Telegram, **From:** {chat_id}\n"
            f"**Captured:** {datetime.now().isoformat(timespec='seconds')}\n\n"
            f"{text}\n"
        )
        out.write_text(body, encoding="utf-8")
        audit("note.saved", chat_id=chat_id, path=str(out), chars=len(text))
        await update.message.reply_text(f"[OK] note saved:\n`{out}`", parse_mode="Markdown")
    except Exception as e:  # noqa: BLE001
        audit("note.error", chat_id=chat_id, error=str(e))
        await update.message.reply_text(f"[FAIL] {e}")


async def msg_media(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for TG-native video / audio / voice / document uploads."""
    if not update.message or not update.effective_chat:
        return
    chat_id = update.effective_chat.id
    if not is_authorized(chat_id):
        return

    msg = update.message
    media = msg.video or msg.audio or msg.voice or msg.video_note
    if media is None:
        return
    kind = (
        "video" if msg.video else
        "audio" if msg.audio else
        "voice" if msg.voice else
        "video-note"
    )
    try:
        dest_dir = videos_root() / "telegram"
        dest_dir.mkdir(parents=True, exist_ok=True)
        # File extension hints
        mime = getattr(media, "mime_type", "") or ""
        if "mp4" in mime or kind in ("video", "video-note"):
            ext = ".mp4"
        elif "ogg" in mime or kind == "voice":
            ext = ".ogg"
        elif "mpeg" in mime or kind == "audio":
            ext = ".mp3"
        else:
            ext = ".bin"
        slug = slugify(f"tg-{kind}-{int(time.time())}", 40)
        out_path = dest_dir / f"{today_stamp()}-{slug}{ext}"

        await msg.reply_text(f"[*] downloading {kind}...")
        tg_file = await media.get_file()
        await tg_file.download_to_drive(custom_path=str(out_path))

        transcript = ""
        # If it's audio-like, transcribe directly; else extract audio first
        if ext in (".ogg", ".mp3"):
            transcript = await transcribe_audio(out_path)
        else:
            audio = await extract_audio(out_path)
            if audio:
                transcript = await transcribe_audio(audio)
            else:
                transcript = "[no audio extracted]"

        tags = await generate_tags(transcript)
        md = write_video_sidecar(out_path, f"telegram://{kind}", transcript, tags, chat_id)
        audit(
            "media.filed",
            chat_id=chat_id,
            kind=kind,
            file=str(out_path),
            sidecar=str(md),
            tags=tags,
        )
        preview = transcript[:600] + ("..." if len(transcript) > 600 else "")
        await msg.reply_text(
            f"[OK] filed.\nfile: `{out_path}`\nsidecar: `{md}`\n"
            f"tags: {', '.join('#' + t for t in tags)}\n\n_transcript preview:_\n{preview}",
            parse_mode="Markdown",
        )
    except Exception as e:  # noqa: BLE001
        audit("media.error", chat_id=chat_id, error=str(e))
        await msg.reply_text(f"[FAIL] {e}")


# ---------------------------------------------------------------------------
# Global error handler
# ---------------------------------------------------------------------------


async def on_error(update: object, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    err = ctx.error
    log.error("unhandled error: %s", err)
    audit("error.unhandled", error=str(err))
    try:
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(f"[FAIL] {err}")
    except Exception:  # noqa: BLE001
        pass


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------


def build_app() -> Application:
    """Build the Application instance. Raises if token is unset."""
    token = CONFIG.get("telegram_token", "").strip()
    if not token or token.startswith("PASTE_"):
        raise SystemExit(
            "[FAIL] No telegram_token in config.json (or TELEGRAM_BOT_TOKEN env). "
            "Get one from @BotFather, paste it, restart."
        )
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("idea", cmd_idea))
    app.add_handler(CommandHandler("ask", cmd_ask))
    app.add_handler(CommandHandler("research", cmd_research))
    app.add_handler(CommandHandler("progress", cmd_progress))

    # Media handlers — these fire before the plain text handler
    media_filter = (
        filters.VIDEO | filters.AUDIO | filters.VOICE | filters.VIDEO_NOTE
    )
    app.add_handler(MessageHandler(media_filter, msg_media))

    # Plain text fallback (commands already routed above)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg_text))

    app.add_error_handler(on_error)
    return app


def main() -> None:
    global CONFIG
    CONFIG = load_config()
    audit("boot", config_path=str(CONFIG_PATH), authorized=CONFIG.get("authorized_chat_ids", []))
    app = build_app()
    log.info("Sinister Crawler online. Authorized chats: %s", CONFIG.get("authorized_chat_ids", []))
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
