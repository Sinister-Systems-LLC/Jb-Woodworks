> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Sinister Crawler — internal skills

These are the agent-capabilities the bot exposes. Each maps to one or more
functions in `bot.py`. This file is the bot's own little skill manifest so the
master agent can reason about what Sinister Crawler can do without reading
the whole source.

| Skill | Implementation | One-liner |
| --- | --- | --- |
| `tg-receive` | `msg_text`, `msg_media`, `cmd_*` handlers | Long-polls Telegram for updates; dispatches by message type / command. |
| `tg-send` | `update.message.reply_text(...)` everywhere | Sends Markdown replies back to the operator's chat. Truncates to 4000 chars. |
| `ai-via-claude-subprocess` | `claude_ask(prompt, timeout)` | Shells `claude --print "<prompt>"` and returns trimmed stdout. Used by `/ask`, `/research`, and `generate_tags`. |
| `url-download` | `download_via_ytdlp(url, dest_dir, slug)` | Uses `yt-dlp` to pull a video into `library/videos/<platform>/`. Respects `max_download_mb`. |
| `audio-extract` | `extract_audio(video_path)` | Spawns `ffmpeg` to pull a 128k mp3 next to the source video. |
| `audio-transcribe` | `transcribe_audio(audio_path)` | OpenAI Whisper API (if `OPENAI_API_KEY` set), else returns a `[skipped]` stub. |
| `capture-invention` | `cmd_idea` | Writes `inventions/YYYY-MM-DD-<slug>.md` from the Sanctum template shape. |
| `file-to-library` | `write_video_sidecar`, `download_via_ytdlp`, `msg_media` | Files videos + sidecar `.md` into `library/videos/<platform>/`. |
| `progress-aggregate` | `cmd_progress` | Walks `_shared-memory/PROGRESS/*.md`, pulls newest 5 entries per agent, returns a Markdown digest. |
| `tag-via-claude` | `generate_tags(transcript)` | Asks claude for 3-5 single-word tags on a transcript snippet. |
| `note-capture` | `msg_text` (non-URL branch) | Saves arbitrary chat text as `_shared-memory/notes/YYYY-MM-DD-tg-<slug>.md`. |
| `auth-gate` | `is_authorized(chat_id)` + `cmd_start` | Only chats recorded via `/start` get responses. All others silently dropped. |
| `audit-log` | `audit(event, **fields)` | Appends a JSONL line per event to `audit.log` next to `bot.py`. |
