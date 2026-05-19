---
target: sinister-crawler
kind: case-study
reviewed_by: Sinister Sanctum master agent (via general-purpose subagent)
reviewed_at: 2026-05-19T12:30Z
tags: [case-study, sinister-crawler, KEEP-WITH-CHANGES]
---

# Case study: sinister-crawler

## 1. What it is

Sinister Crawler is a single-file (~795 LOC) Python Telegram bot at `D:\Sinister Sanctum\tools\sinister-crawler\bot.py` that acts as the operator's mobile-first front-end to the Sanctum. Long-polling via `python-telegram-bot>=21`, it accepts URLs (yt-dlp downloads + ffmpeg audio extraction + optional OpenAI Whisper transcription + Claude-CLI tagging, all filed into `library/videos/<platform>/` with a `.md` sidecar), TG-native media (same pipeline → `library/videos/telegram/`), plain text (saved as a dated note in `_shared-memory/notes/`), and slash commands (`/idea`, `/ask`, `/research`, `/progress`, `/start`, `/help`) that shell out to the local `claude --print` CLI. Auth is a `chat_id` allow-list seeded by the first `/start`, persisted to `config.json`. Every event writes a JSONL row to `audit.log`. Status in `tools/_INDEX.md` is `drafting` — built, not yet smoke-tested with a live BotFather token. Designated as the **first Sanctum invention** (see `inventions/2026-05-19-sinister-crawler.md`).

## 2. Strengths

- **Single-file, no-framework architecture is the right call for v1.** `bot.py:1-795` keeps every handler, helper, filer, and bootstrap step in one readable surface — easy to grep, easy to ship, no plugin system to outgrow. Subprocess-only dependency on `claude` (`bot.py:221-227`) means it does NOT consume a Claude session slot, so it parallelizes cleanly with the master agent (per the invention card's design note).
- **Audit log is structured JSONL with no extra deps** (`bot.py:123-135`). Every command, success, and failure becomes one line: `{ts, event, chat_id, ...fields}`. The SMOKE playbook (`SMOKE.md:109`) already shows the operator how to grep it via PowerShell `ConvertFrom-Json`. This is the kind of forever-debuggable telemetry a v1 should have but most don't.
- **Graceful degradation on every external dependency.** No `OPENAI_API_KEY` → `transcribe_audio` returns a labeled `[transcription skipped]` stub (`bot.py:239-240`); `openai` package missing → labeled `[transcription skipped — openai package not installed]` (`bot.py:247-248`); `claude` CLI returning non-zero → `[claude-cli rc=N]` string surfaces back to chat (`bot.py:225-227`); yt-dlp failure logged and reported (`bot.py:564-566`). Nothing crashes the polling loop.
- **Auth gate is brutally simple and correct.** `is_authorized(chat_id)` (`bot.py:178-180`) silently drops every message from an unregistered chat (`bot.py:633`, `bot.py:668`). First `/start` self-enrolls and persists to `config.json` (`bot.py:370-387`). The "silently drop" choice is the right one for a bot exposed to the public Telegram graph — no enumeration leak.
- **`run_subprocess` correctly offloads blocking work to a thread pool** (`bot.py:187-213`) via `loop.run_in_executor`. With `timeout=` plumbed end-to-end (300s for ffmpeg/yt-dlp, 90s for `/ask`, 180s for `/research`, 60s for tagging), the polling loop stays responsive while heavy work happens off-thread. `FileNotFoundError` and `TimeoutExpired` are surfaced as well-known return codes (124, 127), not exceptions.

## 3. Weaknesses + risks

- **`config.json` race on `save_config` is unguarded** (`bot.py:106-107`, called from `cmd_start` at `bot.py:382`). Two concurrent `/start` invocations could clobber each other's writes — the read at line 98 + the write at line 107 are not atomic. Low impact today (single-operator bot) but a real bug when bulk-authorizing or when a second instance starts. Fix: read-modify-write under a single `fcntl` / `portalocker` lock, OR write to a `.tmp` and `os.replace()` atomically.
- **`generate_tags` parses `claude --print` raw stdout with no defense against chatty replies** (`bot.py:290-305`). The prompt says "reply with ONLY the comma-separated tags" but Claude commonly prepends "Sure, here are the tags: ...". `raw.startswith("[")` is the only fallback. Better fix: regex-match a final-line `[a-z, ]+` pattern, or ask for JSON and `json.loads()` with try/except. As-written, the operator will routinely see tags like `sure-here-are-the` polluting filenames.
- **Single-worker polling means slow URLs serialize every message** (`SMOKE.md:108` calls this out directly). Forwarding 5 Instagram links sequentially blocks `/ask` and `/progress` for ~5x download-time. `Application.run_polling` is sequential per-update by default in `python-telegram-bot`. Mitigations: use `concurrent_updates=True` in `ApplicationBuilder` (one-line fix at `bot.py:762`), or split heavy URL/media work into a queue + worker pattern.
- **`audit.log` grows forever with no rotation** (`bot.py:131`). One JSONL line per command on a daily-use bot is ~5-50 KB/day at light use, ~10x that during a transcription session. There's no `RotatingFileHandler` analog for the audit write path. After 6 months of daily use the file is large enough to slow grep. Fix: rotate at 10 MB via a small helper, or write daily files (`audit-YYYY-MM-DD.log`).
- **No webhook mode + no watchdog + no auto-restart.** The README explicitly defers webhook (`README.md:142`) and SMOKE.md notes "the bot does NOT auto-restart on crash; the desktop bat ends and the window closes" (`SMOKE.md:110`). For a "first Sanctum invention" the operator expects to forward links from anywhere, this is the single biggest UX risk — one network hiccup or one unhandled exception in a handler bypassing the registered `on_error` (`bot.py:738-746`), and the bot is silently offline until the operator notices and double-clicks the bat again.
- **`/progress` heuristic is fragile** (`bot.py:520-527`). It assumes "files prepend latest entries" and grabs the first 5 `- ` / `* ` / `## ` / `### ` lines. If any agent's PROGRESS file appends instead of prepends (the canonical-13 rule says "most-recent at top" but it's not enforced), the operator sees stale top-5 forever with no signal. Fix: parse the `## YYYY-MM-DD HH:MM` heading format that DIRECTIVES.md actually mandates and sort by parsed timestamp.

## 4. Better-than-found proposal

**No rebuild — ship as-is after smoking, then apply five small patches.** The architecture is sound, the file is reviewable, and the operator's stated goal ("the first Sanctum invention, callable from anywhere") is met by what's already on disk. A rebuild would burn time on a working artifact. Instead, queue this small patch series for the next session — none of these require redesigning anything:

```python
# Patch 1: concurrent_updates — bot.py:762
app = ApplicationBuilder().token(token).concurrent_updates(True).build()

# Patch 2: atomic config save — replace bot.py:106-107
def save_config(cfg: dict[str, Any]) -> None:
    tmp = CONFIG_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    os.replace(tmp, CONFIG_PATH)

# Patch 3: audit-log rotation — wrap bot.py:131
def _rotate_if_needed() -> None:
    if AUDIT_LOG.exists() and AUDIT_LOG.stat().st_size > 10 * 1024 * 1024:
        ts = datetime.now().strftime("%Y%m%dT%H%M%S")
        AUDIT_LOG.rename(AUDIT_LOG.with_name(f"audit-{ts}.log"))

# Patch 4: robust tag parsing — replace bot.py:301-305
m = re.search(r"([a-z0-9, \-]+)\s*$", raw.lower(), re.MULTILINE)
parts = [slugify(p, 20) for p in (m.group(1) if m else raw).split(",") if p.strip()]

# Patch 5: watchdog wrapper — Sanctum-Crawler-Start.bat
:loop
python bot.py
echo [crawler] exited rc=%errorlevel% — restarting in 5s
timeout /t 5 >nul
goto loop
```

Optional follow-on after the five-patch series lands: extract the URL+media+tagging pipeline into `tools/sinister-crawler/pipeline.py` so a future `sinister-discord` / `sinister-signal` bot can reuse it without copy-paste. This is a refactor, not a rebuild.

## 5. Recommendation

**KEEP-WITH-CHANGES**

The architecture is right, the LOC is appropriate, the audit + auth + graceful-degradation discipline is better than most "v1" bots that land in this fleet, and the file is genuinely easy to read end-to-end. The five concrete weaknesses are all single-function patches (estimated ~40 LOC total) — none of them require redesign and none of them gate first-smoke. Ship via `SMOKE.md` first to confirm the live BotFather token + `/start` + each command path actually work; flip `tools/_INDEX.md` from `drafting` → `shipped` per `SMOKE.md:102-104`; then queue the five patches plus the optional pipeline-extract for the next session. The "first Sanctum invention" framing earns the lower bar of "ship it and iterate." Archiving would discard a working artifact and a clean reusable pipeline; replacing would burn time rebuilding what's already correct.

## Operator decision
*(left blank)*
