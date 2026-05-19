> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# sinister-crawler

A Telegram bot front-end for the Sanctum. **The first Sanctum invention.**

Forward a video link from your phone and Sinister Crawler downloads it,
transcribes it, tags it, and files it into the Sanctum library — automatically.

## What it does

The operator chats with a single Telegram bot. Sinister Crawler handles:

- **URLs** (Instagram / TikTok / YouTube / Twitter / Reddit / generic) — `yt-dlp` downloads, `ffmpeg` extracts audio, OpenAI Whisper transcribes, Claude tags. The video lands in `library/videos/<platform>/YYYY-MM-DD-<slug>.mp4` with a `.md` sidecar.
- **Native TG media** (`message.video` / `audio` / `voice` / `video_note`) — same pipeline, filed under `library/videos/telegram/`.
- **Plain text** — saved as a note in `_shared-memory/notes/YYYY-MM-DD-tg-<slug>.md`.
- **`/idea <text>`** — captures an invention stub in `inventions/` (matches the existing template).
- **`/ask <question>`** — shells out to the local `claude --print` CLI.
- **`/research <topic>`** — longer claude lookup, results saved to `library/research/`.
- **`/progress`** — aggregates newest 5 entries from each `_shared-memory/PROGRESS/*.md`.

Auth is per-chat: only `chat_id`s recorded via `/start` are allowed. All other messages are silently dropped.

## First-time setup

1. Talk to **@BotFather** on Telegram and create a new bot. Save the token.
2. Edit `D:\Sinister Sanctum\tools\sinister-crawler\.env` (copy from `.env.example`):
   ```
   TELEGRAM_BOT_TOKEN=12345:abc...
   OPENAI_API_KEY=sk-...        (optional — enables Whisper transcription)
   ```
   Or paste the token directly into `config.json` (which is auto-created from `config.example.json` on first run).
3. Make sure `ffmpeg`, `yt-dlp`, and `claude` are on `PATH`. Quick checks:
   ```
   ffmpeg -version
   yt-dlp --version
   claude --version
   ```
4. Double-click **`C:\Users\Zonia\Desktop\Sanctum-Crawler-Start.bat`**. First run creates the venv and installs requirements (~60s); later runs just launch.
5. In Telegram, send `/start` to your bot. The bot writes your `chat_id` into `config.json` and replies with `/help`.

## How to invoke (operator-facing)

```
C:\Users\Zonia\Desktop\Sanctum-Crawler-Start.bat
```

The bat opens a console showing logs. Ctrl-C to stop.

## Commands

| Command | What it does |
| --- | --- |
| `/start` | Authorizes the current chat. Idempotent. |
| `/help` | Lists all commands. |
| `/idea <text>` | Writes `inventions/YYYY-MM-DD-<slug>.md`. |
| `/ask <q>` | Runs `claude --print "<q>"` (90s timeout). |
| `/research <t>` | Runs claude with a research prompt (180s); also writes to `library/research/`. |
| `/progress` | Newest 5 entries per agent from `_shared-memory/PROGRESS/`. |

Plain URL = download + transcribe + file. Plain text = note. Forward a video / voice note = same pipeline.

## Folder layout (what the bot writes to)

```
library/
  videos/
    instagram/
    tiktok/
    youtube/
    twitter/
    reddit/
    facebook/
    generic/
    telegram/          (TG-native uploads)
    README.md
  research/
    YYYY-MM-DD-<slug>.md
    README.md
_shared-memory/
  notes/
    YYYY-MM-DD-tg-<slug>.md
inventions/
  YYYY-MM-DD-<slug>.md
tools/sinister-crawler/
  bot.py
  config.json          (auto-created from config.example.json)
  config.example.json
  audit.log            (jsonl, one event per line)
  requirements.txt
  .env.example
  README.md
  skills.md
  AUTHOR.md
```

Each downloaded video gets a `.md` sidecar with:
- source URL
- download timestamp
- file path
- transcript (full)
- `Auto-categorized: yes`
- Claude-generated tags

## Implementation files (absolute paths)

- `D:\Sinister Sanctum\tools\sinister-crawler\bot.py`
- `D:\Sinister Sanctum\tools\sinister-crawler\requirements.txt`
- `D:\Sinister Sanctum\tools\sinister-crawler\config.example.json`
- `D:\Sinister Sanctum\tools\sinister-crawler\.env.example`
- `D:\Sinister Sanctum\tools\sinister-crawler\skills.md`
- `D:\Sinister Sanctum\tools\sinister-crawler\AUTHOR.md`
- `C:\Users\Zonia\Desktop\Sanctum-Crawler-Start.bat`

## Dependencies

- Python 3.10+
- `python-telegram-bot>=21`
- `yt-dlp` (PATH)
- `ffmpeg` (PATH)
- `claude` CLI (PATH) — used for `/ask`, `/research`, tag generation
- Optional: `OPENAI_API_KEY` env var for Whisper transcription

## Lane

master / Sanctum orchestration

## Captured

2026-05-19

## Status

drafting (built; not yet smoke-tested with a live BotFather token)

## Linked-inventions

- `D:\Sinister Sanctum\inventions\2026-05-19-sinister-crawler.md`

## Changelog

- **2026-05-19** — Initial build. First Sanctum invention. Polling-based; webhook deferred. All handlers wired; audit log + per-handler error capture.
