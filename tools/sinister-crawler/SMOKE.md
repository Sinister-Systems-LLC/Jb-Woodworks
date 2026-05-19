> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# sinister-crawler — smoke test

Step-by-step from "I have nothing" to "I sent /start and the bot replied." Each step has one command and one expected output. If a step diverges, stop and read README.md.

## 0. Prereqs (15 seconds each)

```powershell
ffmpeg -version    | Select-Object -First 1   # expects "ffmpeg version N.N.N ..."
yt-dlp --version                                # expects "YYYY.MM.DD"
claude --version                                # expects "claude X.Y.Z"
python --version                                # expects "Python 3.10+"
```

Any "command not found" → install via `winget install <name>` (ffmpeg, yt-dlp) or run `claude` once from a fresh git-bash shell.

## 1. Get a Telegram bot token (30 seconds)

1. In Telegram, search `@BotFather`.
2. Send `/newbot`.
3. Reply with a display name (e.g. `Sinister Crawler`).
4. Reply with a username ending in `bot` (e.g. `sinister_crawler_test_bot`).
5. Save the token BotFather hands back. Format: `12345:abcDEF...` (~46 chars).

## 2. Wire the token (15 seconds)

```powershell
cd "D:\Sinister Sanctum\tools\sinister-crawler"
Copy-Item .env.example .env -Force
notepad .env
```

In notepad, set:

```
TELEGRAM_BOT_TOKEN=<paste-the-BotFather-token-here>
OPENAI_API_KEY=                                     # optional, leave blank for now
```

Save + close.

## 3. First boot (~60 seconds; creates venv)

```cmd
C:\Users\Zonia\Desktop\Sanctum-Crawler-Start.bat
```

Expected console output:

```
[crawler] creating venv ...
[crawler] installing requirements (this may take ~60s) ...
[crawler] OK — bot polling started as @<your-bot-username>
```

Leave the window open.

## 4. Authorize the chat (5 seconds)

In Telegram, open a chat with your new bot and send:

```
/start
```

Expected reply (instant):

```
Sinister Crawler online. /help for commands.
Chat authorized.
```

The bot writes your `chat_id` into `D:\Sinister Sanctum\tools\sinister-crawler\config.json`. Future restarts honor this — no re-auth needed.

## 5. Smoke each command (30 seconds each)

| You send | Bot replies / does | Verify |
| --- | --- | --- |
| `/help` | List of commands | reply within 1s |
| `/idea Test invention from smoke` | "Idea captured: <slug>.md" | check `D:\Sinister Sanctum\inventions\` for new `.md` |
| `/ask hello` | claude response (90s timeout) | reply within 90s |
| `/progress` | top-5 progress entries per agent | reply within 3s |
| Forward a 30s YouTube short | download starts → "transcribing" → "filed at library/videos/..." | check `D:\Sinister Sanctum\library\videos\youtube\` |

## 6. Stop the bot

In the Sanctum-Crawler console window: `Ctrl+C`. Wait for "bot shutdown complete." Window closes.

## Common failures

| Symptom | Cause | Fix |
| --- | --- | --- |
| `telegram.error.InvalidToken` on boot | wrong token | re-read step 1; tokens look like `12345:abc...` ~46 chars |
| `/ask` hangs > 90s | claude CLI not on PATH or unauthorized | run `claude --version` in same shell — fix PATH first |
| `/idea` writes but no slug | inventions dir missing | `mkdir "D:\Sinister Sanctum\inventions"` |
| URL forward fails | yt-dlp can't reach the URL | run `yt-dlp <url>` manually to see real error |
| `OPENAI_API_KEY` warning every transcript | optional Whisper key not set | either set it or ignore — local fallback uses claude-CLI transcription |

## When this smoke passes

1. Edit `D:\Sinister Sanctum\tools\_INDEX.md` → flip status from `drafting` → `shipped`.
2. Edit `D:\Sinister Sanctum\inventions\2026-05-19-sinister-crawler.md` → bump status to `shipped`.
3. Append a `shipped` entry to `D:\Sinister Sanctum\_shared-memory\PROGRESS\<your-agent>.md`.

## Notes for the operator

- Bot polling is single-threaded; one URL at a time. Bulk drops queue.
- `audit.log` (jsonl, one event per line) records every command + outcome. Search with PowerShell: `Get-Content audit.log | ConvertFrom-Json | Where-Object kind -eq 'idea'`.
- The bot does NOT auto-restart on crash; the desktop bat ends and the window closes. Future work: wrap in a watchdog (see `06_LAUNCHER.md` for the pattern).
