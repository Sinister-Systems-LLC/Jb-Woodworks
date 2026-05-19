# Researcher-specific gotchas

(Hand-edited. Universal gotchas at `09_REFERENCE/SANDBOX-GOTCHAS.md` are loaded automatically.)

- **nodriver downloads Chrome on first call.** If the operator's machine is offline, `stealth.open` will fail. Mention this; fall back to `requests` only if explicitly authorized (most pages won't render JS).
- **Cloudflare-walled sites** may need `wait_for_selector="<body>"` + retry. Don't loop forever; cap at 2 retries.
- **Social-media scraping** is brittle and often against ToS. Recommend the operator use the official API path if available.
- **researcher.lookup(query) without url** is not yet wired. It returns guidance saying to provide a URL. When a search-engine MCP integration ships (Phase 8l), this changes.
