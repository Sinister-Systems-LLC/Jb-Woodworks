# Scribe-specific gotchas

(Hand-edited. Add Scribe-only landmines here. Universal gotchas live at
`09_REFERENCE/SANDBOX-GOTCHAS.md` and are loaded automatically.)

- **Don't render the same urgent item twice** if it appears in both Sentinel and ALL-FOLLOWUPS. Dedupe by short hash of the message text.
- **Token-usage section** must include only the prior 24h. Scribe's own call IS in that window - subtract its own input/output to avoid self-counting drift.
- **API-key absence** is fine. If `ANTHROPIC_API_KEY` env var is missing, Scribe returns `{ok: false, error: ...}` cleanly - do not try to call without it.
