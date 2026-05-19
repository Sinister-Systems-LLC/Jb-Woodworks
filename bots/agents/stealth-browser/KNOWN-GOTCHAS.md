# stealth-browser-specific gotchas

- **Default `headless=False`** so operator can SEE what the bot's doing. Catch unintended scrapes.
- **`evaluate(js)` runs ARBITRARY JS** in the page context - only call with vetted snippets. Never paste operator-provided JS without explicit confirmation.
- **First launch downloads/locates Chrome** - 5-10s extra latency. Subsequent calls reuse the open browser.
- **Cloudflare hard-block:** if `open` returns the Cloudflare interstitial, retry with `wait_for_selector="body"` + a longer timeout. Don't loop forever.
