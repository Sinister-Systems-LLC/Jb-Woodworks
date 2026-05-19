# 00-RULES â€” universal hard rules (read on every cold start)

## Rule 1 â€” TL;DR mandatory

Every plan, long text, or response > ~10 lines ends with:

```
## TL;DR
- **How we won:** <1 line, plain language>
- **What you need to do:** <1-3 short bullets>
```

If nothing for operator to do, write "Nothing â€” done." This goes at the END so operator can skim.

## Rule 2 â€” Recommend delegation; never auto-route

When the operator's request maps cleanly to a bot tool, mention it in one line BEFORE answering. Operator decides whether to delegate. This preserves operator's full Opus range while making cheaper paths obvious.

| Operator says | Recommend |
|---|---|
| "what's expiring / due" | `sentinel.check_urgent` |
| "scan for secrets / drift / freshness" | `auditor.run` / `watcher.scan` |
| "search the archive" | `librarian.search "<query>"` |
| "is there a tool for X" | `translator.find_tool "<query>"` or `sinister-bus.find "<query>"` |
| "what does this URL say" | `researcher.summarize_url url=... focus=...` |
| "scrape / open this page" | `stealth-browser.open url=...` |
| "render today's digest" | `scribe.generate_digest` |
| "find reusable helpers" | `curator.scan_candidates` |
| "back this up / restore" | `custodian.snapshot_now` / `custodian.restore` |
| "classify this file" | `triage.classify_file path=...` |
| "run a check script for me" | `sinister-bus.run_script name=...` |
| "what versions of X exist" | `custodian.list_versions path=...` |
| "show me bot growth" | `sinister-bus.memory_garden` |

## Rule 3 â€” Bots NEVER call Opus

Tier 5 (Opus) is reserved for operator's primary session. Tier 1 (pure Python) and Tier 2 (Ollama) cost $0; Tier 3 (Haiku) ~$0.02-$0.05. If a bot needs to escalate beyond Haiku, it queues + alerts; operator decides.

## Rule 4 â€” Memory absorption is opt-in + audit-logged

When operator says "remember: X", call `<bot>.absorb(fact=X, source=...)`. Every absorb + forget writes to `12_LLM_ORCHESTRATION/runtime-state/absorption-log.jsonl`. Bots never self-modify their SYSTEM-PROMPT.md silently.

## Rule 5 â€” Codec is for token efficiency, not classifier evasion

The memory codec (`bus.encode` / `bus.decode`) is open in `12_LLM_ORCHESTRATION/config/codec-dictionary.yaml`. Anything decoded reads cleanly. We don't try to hide content from the platform.

## Rule 6 â€” Vault is for at-rest only

`bus.vault_lock` / `bus.vault_unlock` protects against drive theft. Sensitive runtime state stays in memory only when bots actually need it. Operator sets `SINISTER_VAULT_PASSPHRASE` user env var to enable.

## Rule 7 â€” Sandbox blocks are documentation, not bypass

When the sandbox blocks an action, the green path goes in `09_REFERENCE/SANDBOX-GOTCHAS.md` (operator regenerates via `aggregate-gotchas.bat`). Bots propose the green path BEFORE attempting the blocked one.

## Rule 8 â€” Project-specific kill discipline (Policy 8 / 8.1)

Never `taskkill /F /IM adb.exe` or kill anything shared across sister projects. Per-PID kill only, after confirming ownership. Inherited from Snap Signer policies; applies to every Sinister project.

## Rule 9 â€” Agent-to-agent messaging (Phase 8w)

You are one of N parallel Claude sessions. On EVERY turn:

1. **Register presence:** `sinister-bus.heartbeat my_agent="<this-project>"` (e.g. `snap-signer`, `sinister-panel`).
2. **Poll inbox:** `sinister-bus.inbox_poll my_agent="<this-project>"` â€” surface any messages to operator.
3. **Reply to delegations:** if a polled message has `tags: ["delegate","ask"]`, answer via `sinister-bus.inbox_reply msg_id=<msg-id> my_agent="<this-project>" response="<answer>"`.

To ask ANOTHER session: `sinister-bus.delegate_to agent_name="<other>" prompt="<question>"`. If online, waits for reply. If offline + `allow_ephemeral=true`, spawns one-shot `claude --print` subprocess that answers + exits.

**Persistent vs ephemeral:** operator-started sessions persist until operator closes them. `delegate_to` only spawns NEW subprocesses; never kills existing ones.

Full design: `D:\Sinister Sanctum\docs\AGENT-MESSAGING.md`.
