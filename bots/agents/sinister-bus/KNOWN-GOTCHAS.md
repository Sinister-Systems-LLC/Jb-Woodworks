# sinister-bus-specific gotchas

- **You record intent, not execution.** When operator says `bus.dispatch(target="researcher.lookup", args={...})`, you write the handoff record. The operator's session still has to actually call `researcher.lookup`. Future Phase 8k will add real HTTP relay.
- **`list_network` is statically defined.** Adding a new bot requires editing `KNOWN_AGENTS` in `server.py`. There is no auto-discovery from `.mcp.json` yet.
- **Context IDs are operator-pickable.** If the operator passes a `context_id`, you reuse it; otherwise you mint `ctx-<utc>-<6hex>`.
