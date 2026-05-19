# Researcher agent

Tier 2 (Ollama; $0). Chains stealth-browser scrapes through local Ollama
summarization. The point: operator never burns Opus tokens reading raw HTML.

## Tools

| Tool | What |
|---|---|
| `researcher.lookup(query, url, top_k=3)` | Summarize a URL with `query` as the focus |
| `researcher.summarize_url(url, focus?)` | Bullet summary of one page |
| `researcher.compare(urls, focus)` | Cross-source comparison with agreement/contradiction call-outs |
| `researcher.health()` | Ollama + stealth-browser status |

## Wire-up

`researcher` calls `stealth-browser` directly by importing its `server.py` module
(no MCP-to-MCP layer needed yet). If `stealth-browser` deps aren't installed, the
tools return `{ok: false, error: ...}` immediately and the operator sees what's missing.

## Default cheap-path

```
operator: "what does <url> say about <thing>?"
   |
   v
researcher.summarize_url(url=<url>, focus=<thing>)
   |  (no Opus tokens spent on raw HTML)
   v
stealth-browser.open + scrape_text  ->  ~20KB rendered text
   |
   v
Ollama qwen2.5-coder:7b summarize  ->  ~500 tokens
   |
   v
operator gets the summary
```

## When Ollama is down

Falls back to `mode: "raw"` and returns the first 2KB of scraped text + the
total text length, letting the operator decide if escalation to Haiku is worth it.

## Environment

- `SINISTER_HUB_ROOT` — defaults to `D:\Sinister\Sinister Skills`
- `OLLAMA_HOST` — defaults to `http://localhost:11434`
- `RESEARCHER_MODEL` — defaults to `qwen2.5-coder:7b`

## Roadmap

- Add brave-search / duckduckgo MCP dispatch so `lookup(query)` works without a URL.
- Add citation tracking back into `01_MEMORY/_consolidated/` for traceability.
- Add a "cite_in_md" tool that returns Markdown footnote-formatted citations.
