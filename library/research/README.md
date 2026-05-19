> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# library/research

Auto-populated by **Sinister Crawler** when the operator runs `/research <topic>`
in Telegram.

```
research/
  YYYY-MM-DD-<slug>.md
```

Each file is a Claude CLI output saved verbatim, plus a small header:

- captured timestamp
- origin (which TG chat triggered it)
- the exact prompt used
- findings (5-10 bullets per the standard /research prompt)

## Rules

- **Do NOT manually drop files here.** Use the bot's `/research` command.
- Topics are slugified to ASCII kebab-case, max 40 chars.
- Same-day duplicate slugs will overwrite — re-running `/research foo` later in
  the day replaces today's `foo` file with the newer findings (by design).

## See also

- Tool card: `D:\Sinister Sanctum\tools\sinister-crawler\README.md`
- Bot entry: `D:\Sinister Sanctum\tools\sinister-crawler\bot.py`
- Invention: `D:\Sinister Sanctum\inventions\2026-05-19-sinister-crawler.md`
