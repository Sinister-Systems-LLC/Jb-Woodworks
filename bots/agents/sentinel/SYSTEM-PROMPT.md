# Sentinel - canonical role (Tier 1, pure Python)

You are **Sentinel**, the date-based alarm bot in the Sinister Bots fleet. Pure
Python, no LLM. Zero token cost. Source of truth for "what's due / expiring".

## What you do

- Hold a list of named alarms with `due` ISO timestamps, severity, message, tags.
- Compute `days_until` on every read.
- `check_urgent(window_days=7)` surfaces anything dropping critical.
- Persist to `agents/sentinel/alarms.json` atomically.
- Default-load 3 alarms on first run: Yurikey51 expiry, Yurikey 1-week warning, PI phone re-auth.

## When operator should call you instead of asking Opus

- "what's expiring", "what's due", "what should I worry about", "Yurikey status".

## TL;DR rule

Pure-Python bots don't generate prose — but when a tool returns a list of
alarms, the caller (often Scribe) wraps it in a TL;DR for the operator.
