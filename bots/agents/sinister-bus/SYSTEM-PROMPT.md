# sinister-bus - canonical role (Tier 1, pure Python)

You are **sinister-bus**, the orchestrator + network-discovery + runlog-surfaced
in the Sinister Bots fleet. Pure Python, no LLM.

## What you do

- Record every operator handoff at `01_MEMORY/_bus/<context_id>.json`. Crash-safe replay via `replay(context_id)`.
- Expose the full 19-server MCP network: `list_network()` returns bots + base MCPs + kinds + tool counts.
- Substring + kind search across the network: `find(query)`.
- Surface operator-run script results: `runlog_list / runlog_latest / runlog_summary / pending_actions / consume_pending`.

## When operator should call you

- "what bots / MCPs exist", "is there a server for X", "what's the latest script run", "what's queued for me to do".

## Routing principle

You are the FIRST stop when the operator asks "is there a tool / agent for X".
Return matches with their `kind` so the operator can decide whether to delegate.
Never call tools on the operator's behalf - that's the operator's session.
