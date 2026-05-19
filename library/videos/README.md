> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# library/videos

Auto-populated by **Sinister Crawler** (`tools/sinister-crawler/bot.py`).

When the operator forwards a video URL or TG-native video/voice/audio to the
Crawler bot, the file lands here under one of these subfolders:

```
videos/
  instagram/
  tiktok/
  youtube/
  twitter/      (also x.com)
  reddit/
  facebook/
  generic/      (fallback — anything yt-dlp can pull)
  telegram/     (TG-native uploads: video, voice notes, audio files)
```

Each video has a `.md` sidecar with the same basename containing:

- source URL
- download timestamp
- absolute file path
- transcript (Whisper, if `OPENAI_API_KEY` is set)
- Claude-generated tags
- `Auto-categorized: yes`

## Rules

- **Do NOT manually drop files here.** Use the bot.
- You may move a file between platform folders if it was misclassified — just keep the sidecar with it.
- The bot enforces a `max_download_mb` cap from `config.json` (default 200 MB).

## See also

- Tool card: `D:\Sinister Sanctum\tools\sinister-crawler\README.md`
- Bot entry: `D:\Sinister Sanctum\tools\sinister-crawler\bot.py`
- Invention: `D:\Sinister Sanctum\inventions\2026-05-19-sinister-crawler.md`
