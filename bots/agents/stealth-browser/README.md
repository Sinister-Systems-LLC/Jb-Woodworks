# Stealth-Browser agent

Tier 1 (no LLM cost). Undetected browser automation for the Sinister Bots fleet.

**Origin pattern:** RE'd from [`vibheksoni/stealth-browser-mcp`](https://github.com/vibheksoni/stealth-browser-mcp) — same `nodriver + Chrome DevTools Protocol + FastMCP` backbone, but a minimal 11-tool surface (vs the upstream's 96) tailored to what our agents actually need. Extend later by porting more of the upstream's element-cloner / network-interceptor modules if a real use case lands.

## Tools

| Tool | What |
|---|---|
| `stealth.open(url, wait_for_selector?)` | Navigate; launches Chrome on first call |
| `stealth.screenshot(path?, full_page?)` | PNG capture; default `agents/stealth-browser/screenshots/` |
| `stealth.html()` | Full HTML of current page |
| `stealth.scrape_text(max_chars=20000)` | Rendered visible text (`document.body.innerText`) |
| `stealth.scrape_links()` | Up to 200 `<a href>` entries |
| `stealth.click(selector)` | Click matching element |
| `stealth.type(selector, text, delay_ms=30)` | Type into matching element |
| `stealth.wait_for(selector, timeout_sec=10)` | Wait for element |
| `stealth.evaluate(js)` | Run arbitrary JavaScript |
| `stealth.close()` | Free the browser |
| `stealth.health()` | Driver + browser status |

## Setup

```powershell
cd 'D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\stealth-browser'
.\.venv\Scripts\pip install nodriver
```

`nodriver` ships an undetected Chromium wrapper and reuses a local Chrome install if one exists. First launch downloads only what's missing.

## Why this exists

Plain `requests`/`httpx` reads static HTML; modern sites (Cloudflare, JS-heavy SPAs, fingerprint-walled APIs) require a real browser. Without this, the only options were:
- Opus reading rendered pages itself (expensive, slow, brittle on JS-rendered content)
- Manual operator scrape (interrupts flow)

Stealth-Browser lets cheaper agents (`researcher`, `librarian`, `triage`) hand off "go fetch the rendered text of URL X" without paying Opus rates or being detected as a bot.

## Cost

$0 per call (pure Python + local Chrome). Operator's Opus session never sees raw HTML; it only sees the summary the `researcher` agent produces from this.

## Environment

- `SINISTER_HUB_ROOT` — defaults to `D:\Sinister\Sinister Skills`
- Browser binary: nodriver auto-detects Chrome/Edge/Chromium

## Safety

- Default `headless=False` so operator can SEE what the bot is doing (catch unintended scrapes).
- `evaluate(js)` runs ARBITRARY JavaScript — only call with vetted snippets.
- Per upstream's design, this is a dual-use scraping tool. Use against properties you control or have explicit permission to test.
