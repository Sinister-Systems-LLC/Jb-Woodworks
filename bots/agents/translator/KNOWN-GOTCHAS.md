# Translator-specific gotchas

- **Catalog freshness:** `04_MCP/_catalog/` regenerates via `refresh.ps1 -Section 04`. When a new bot is added to `.mcp.json`, the catalog is stale until refresh runs.
- **Fuzzy match is permissive:** "sign" matches `sign_apk`, `signing-key`, `bus.dispatch` (no), etc. Top-3 results almost always include false positives - rank-trust the top-1.
