> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Sinister Crawler — TG bot front-end for the Sanctum (first Sanctum invention)

**Captured:** 2026-05-19
**Status:** building
**Origin:** Operator directive (2026-05-19): "telegram bot i can send videos too. give ideas to. tell it to start research on things ask it things about my work etc. just for sinister sanctum for now. for example if i send instagram link to video it downloaded it and review audio. etc etc and places it in correct place. this will be the first sanctum invention, Called Sinister Crawler. make it in parrallel with all features we need and tools from our warehouse"

## Idea

> telegram bot i can send videos too. give ideas to. tell it to start research on things ask it things about my work etc. just for sinister sanctum for now. for example if i send instagram link to video it downloaded it and review audio. etc etc and places it in correct place. this will be the first sanctum invention, Called Sinister Crawler. make it in parrallel with all features we need and tools from our warehouse

A single Telegram bot the operator can chat with from anywhere. Forward a video link, drop a thought, ask a question, kick off research — the bot routes each message to the right Sanctum tool and files results in the right place.

## Why

The operator already lives in Telegram and is constantly grabbing reference videos (Instagram reels, TikToks, YouTube clips) that today either get screenshotted, lost in DMs, or saved to camera roll with no metadata. Sinister Crawler turns that everyday flow into structured Sanctum library content with zero extra clicks:

- video links auto-download, auto-transcribe, auto-tag, auto-file
- ideas land in `inventions/` instead of being forgotten
- questions answered against the operator's own knowledge graph (via local `claude` CLI) instead of generic Google
- progress checks ("how are my agents doing?") possible from the couch

It's also the **first Sanctum invention** — the proof that the inventions/ folder isn't just a journal but the genesis of real tools. Future inventions follow the same path: capture → build → register in `tools/_INDEX.md` → ship.

## Sketch

```
Telegram (operator's phone)
   |
   v
+--------------------------------------------------+
|  bot.py (long-poll, python-telegram-bot v21)      |
|                                                    |
|  /start /idea /ask /research /progress /help       |
|  URL handler  -> yt-dlp -> ffmpeg -> whisper -> md |
|  TG media     -> get_file -> ffmpeg -> whisper     |
|  Plain text   -> note in _shared-memory/notes/     |
|                                                    |
|  Subprocess: claude --print  (ask/research/tags)   |
|  Auth: chat_id allowlist in config.json            |
|  Audit:  audit.log (jsonl)                         |
+--------------------------------------------------+
       |                         |                 |
       v                         v                 v
  library/videos/<plat>/   inventions/      _shared-memory/notes/
  library/research/
```

Pipeline for a forwarded Instagram link:

1. `_URL_RE` matches → `classify_platform()` → `"instagram"`
2. `download_via_ytdlp(url, library/videos/instagram/, slug)` → `<date>-<slug>.mp4`
3. `extract_audio()` → `<date>-<slug>.mp3` via ffmpeg
4. `transcribe_audio()` → Whisper API (OPENAI_API_KEY) → transcript
5. `generate_tags()` → `claude --print "Tag this..."` → `["fashion","makeup","tutorial"]`
6. `write_video_sidecar()` → `<date>-<slug>.md` with URL + tags + transcript
7. Reply to chat with file paths + transcript preview

## Status

- [x] idea captured
- [x] design sketched
- [x] implementation started (bot.py, ~500 lines, all handlers wired)
- [ ] shipped (pending: live BotFather token + smoke test by operator)

## Linked-to

- Tool folder: `D:\Sinister Sanctum\tools\sinister-crawler\`
- Bot entry:   `D:\Sinister Sanctum\tools\sinister-crawler\bot.py`
- Desktop bat: `C:\Users\Zonia\Desktop\Sanctum-Crawler-Start.bat`
- Skills card: `D:\Sinister Sanctum\tools\sinister-crawler\skills.md`
- Tool card:   `D:\Sinister Sanctum\tools\sinister-crawler\README.md`
- Index row:   `D:\Sinister Sanctum\tools\_INDEX.md`
- Author tag:  `D:\Sinister Sanctum\tools\sinister-crawler\AUTHOR.md`

## Notes

- Polling-based for v1; webhook mode deferred. No webhook is registered.
- Designed to run in parallel with other Sanctum agents — uses `subprocess` for `claude`, so it does not steal a Claude session slot. Master agent stays free.
- Audit log is jsonl so future tooling can grep / aggregate without parsing free-form logs.
- Auth is intentionally minimal — `chat_id` allowlist seeded by first `/start`. Operator can add more chat_ids by editing `config.json` directly.
