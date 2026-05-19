# Adding MCP servers — operator-decides review

Operator asked (2026-05-19) about adding these MCP servers to the Sinister network:

1. **Playwright** — browser automation
2. **Context7** — live library/framework docs at query time
3. **Sequential thinking** — step-by-step reasoning scaffold
4. **Codex (to challenge Claude)** — OpenAI Codex as a second-opinion code reviewer
5. **Knowledge graph memory** — persistent KG memory across sessions

This doc reviews each, recommends fit + install steps. **Operator decides** — none auto-installed (touching `~/.claude/.mcp.json` requires a restart and could break a session in progress with snap/tiktok agents).

---

## 1) Playwright MCP

**What:** Microsoft's Playwright wrapped as MCP. Gives Claude tools to drive a real Chromium/Firefox/WebKit browser — navigate, click, fill forms, screenshot, scrape rendered DOM.

**Sinister fit:** **High.** Overlaps with `stealth-browser` (which we already have via nodriver), but Playwright is the industry standard with broader API coverage (multi-tab, network interception, mobile emulation, CDP access).

**Tradeoff with stealth-browser:**
- `stealth-browser` — anti-bot evasion focus (nodriver, Cloudflare/Turnstile bypass)
- `playwright` — testing/automation focus (broader API, but easier for sites to fingerprint)

**Recommendation:** Add as a SECOND browser tool alongside stealth-browser. Use playwright for trusted sites + general automation; use stealth-browser for hardened anti-bot targets. Both can coexist.

**Install:**
```jsonc
// ~/.claude/.mcp.json — add to mcpServers
"playwright": {
  "command": "npx",
  "args": ["-y", "@playwright/mcp@latest"]
}
```

Then restart Claude. First run will install Chromium (~150 MB).

**Risk:** Low. Operator can disable any time.

---

## 2) Context7 MCP

**What:** Upstash's Context7 — fetches up-to-date library docs at query time. Solves "Claude's training data is stale for newer libraries" problem.

**Sinister fit:** **Medium-high.** Useful for Panel (Next.js + React updates), TikTok-EMU (recent Frida/Android libs), Snap-EMU (gRPC + protobuf). Less useful for AOSP / kernel work where docs change slowly.

**Recommendation:** Add. Cost = $0 (Upstash hosts free tier). Reduces hallucination on library APIs.

**Install:**
```jsonc
"context7": {
  "command": "npx",
  "args": ["-y", "@upstash/context7-mcp@latest"]
}
```

**Risk:** Low. Read-only.

---

## 3) Sequential thinking MCP

**What:** Anthropic's official sequential-thinking server. Exposes a tool that lets Claude record explicit reasoning steps with revision/branching. Improves multi-step problem solving when the problem benefits from think-aloud.

**Sinister fit:** **Medium.** Sinister is mostly system-orchestration work where the bot fleet already provides delegation (sinister-bus.delegate_to). Sequential thinking would mostly help during:
- Snap-emu Frida hook debugging (genuinely complex multi-step reasoning)
- Panel architecture decisions
- Audit triage (rare)

**Recommendation:** Add for snap-emu and panel sessions specifically. Master orchestrator session won't use it much.

**Install:**
```jsonc
"sequential-thinking": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
}
```

**Risk:** Low. Inflates token usage on every reasoning step; can be disabled per-session.

---

## 4) Codex (to challenge Claude) — second-opinion code review

**What:** Operator's framing — "Codex to challenge Claude". Likely refers to running OpenAI's Codex/GPT-4 as a parallel code reviewer that questions Claude's outputs. Not a standard MCP package; needs custom wiring.

**Sinister fit:** **Conditional.** Useful pattern:
- Master writes a fix
- Codex MCP reviews the diff, flags issues
- Master reconciles

But:
- Costs OpenAI API credits ($) — Anthropic-only fleet is currently $0
- Adds latency (every fix doubles round-trip)
- Requires OPENAI_API_KEY (operator-private env var)

**Recommendation:** **DEFER** until operator has specific failure mode it'd solve. The 12-bot Sinister fleet already has `auditor` for static-analysis-style review. Adding paid LLM second-opinion is a "we hit X bug 3 times" reaction, not a default.

**If operator wants it:**
- No off-the-shelf MCP exists; would need a thin custom wrapper (similar to how Scribe + Curator call Haiku via Anthropic SDK). Estimate 2-3 hours.
- Better immediate alternative: use `auditor.run` more aggressively.

---

## 5) Knowledge graph memory MCP

**What:** Anthropic's official knowledge-graph-memory server. Persistent typed-entity graph that survives across sessions. Claude can `create_entities`, `add_observations`, `read_graph`, etc.

**Sinister fit:** **HIGH** and OVERLAPS with what we already have:
- The `librarian` bot already does memory recall (vector + grep) over `01_MEMORY/<project>/`
- The `understand-anything` knowledge graphs at `06_UNDERSTAND/<project>/graph.json` already provide structured project-wide nodes/edges
- The `bot_memory.absorb()` pattern in each bot already records observations

But the KG-memory MCP provides a UNIFIED cross-session graph that's API-callable from any tool, with automatic entity disambiguation.

**Recommendation:** **Add — but carefully.** Risk: if Claude starts writing to KG-memory in addition to bot_memory + librarian + UA graphs, we get 3 conflicting sources of truth. Need a clear write-path policy:
- KG-memory = **cross-session persistent observations** (operator decisions, breakthroughs, contracts between agents)
- bot_memory.absorb() = **per-bot working state** (last call, recent errors)
- librarian = **read-side aggregator** (queries across both)
- UA graph = **code-structure graph** (rebuilt from source on demand)

**Install:**
```jsonc
"memory": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-memory"],
  "env": {
    "MEMORY_FILE_PATH": "D:\\Sinister\\Sinister Skills\\01_MEMORY\\_kg-memory\\graph.json"
  }
}
```

The `MEMORY_FILE_PATH` env keeps it under existing Sinister memory tree so Custodian backs it up.

**Risk:** Medium. Write-path policy needs to be documented before any agent starts writing to it. Otherwise we get the "3 sources of truth" antipattern.

---

## Summary — operator decision matrix

| Server | Fit | Cost | Risk | Master rec |
|---|---|---|---|---|
| Playwright | High | $0 (npx) | Low | **ADD** — complements stealth-browser |
| Context7 | Medium-high | $0 (Upstash) | Low | **ADD** — kills library hallucinations |
| Sequential thinking | Medium | Token inflation | Low | **ADD** — useful for snap/panel sessions |
| Codex | Conditional | OpenAI $$ | Medium | **DEFER** — auditor covers this for now |
| KG memory | High but overlap | $0 (local) | Medium | **ADD with policy** — needs write-path doc |

## Install order (recommended)

1. Add Playwright + Context7 + Sequential thinking + KG memory to `~/.claude/.mcp.json` (one restart)
2. Document KG-memory write-path policy in `docs/MEMORY-CODEC-AND-CRYPTO.md`
3. Smoke-test each from a fresh Claude session
4. Decide Codex later

**Master will NOT auto-install** — touching `.mcp.json` requires a restart that would interrupt snap-emu + tiktok-emu agents mid-push. Operator runs the install when ready (`Edit-MCP-Config.bat` could be built for this if helpful).
