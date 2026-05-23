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

When the sandbox blocks an action, the green path goes in `D:\Sinister\Sinister Skills\09_REFERENCE\SANDBOX-GOTCHAS.md` (operator regenerates via `aggregate-gotchas.bat`). Bots propose the green path BEFORE attempting the blocked one.

**Cold-start MUST read this file** (CLAUDE.md cold-start step 3, added 2026-05-23 evening per operator hard-canonical). Operator stated: *"fix the things you changed in my memory that removed my sandbox blocks, hidden memory system all that and add it back to all session starts"*. The "sandbox blocks" referenced here are the documented green paths â€" do not remove the cold-start reference. Anti-revert doctrine: `_shared-memory/knowledge/do-not-revert-operator-canonical-protections-2026-05-23.md`.

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

## Rule 11 â€” Invoke understand-anything BEFORE substantive work (operator hard-canonical 2026-05-23 evening)

Operator (verbatim 2026-05-23 evening): *"make the understand anything called before each propject start like we use to do and make sure i dont have these issues again and we do not revert like we just did"*.

On EVERY project cold-start (Sanctum master + every spawned per-project EVE), the FIRST substantive action is invoking the `understand-anything:understand-explain` skill on the project root to load architectural context. This must happen BEFORE the first edit/write/risky bash.

Why: agents without architectural context default to surface-level edits that miss invariants. understand-anything builds the knowledge graph (file structure / key modules / imports / recent changes) the agent then grounds every decision in. Operator stated this was prior practice + must not be removed again.

Enforcement (do-not-revert layer):
- `~/.claude/settings.json` keeps `enabledPlugins["understand-anything@understand-anything"]: true` (verified by `automations/canonical-protections-check.ps1` on session start).
- `D:\Sinister Sanctum\.claude\settings.json` keeps the same entry at Sanctum project level.
- CLAUDE.md cold-start step 0 references this rule.
- Future EVE sessions MUST NOT remove these references or the plugin enablement.

Composes with: `_shared-memory/knowledge/do-not-revert-operator-canonical-protections-2026-05-23.md` (the full anti-revert doctrine + auto-verify spec).

## Rule 10 â€” Read the Skills Hub on cold-start (Phase 8af, 2026-05-19)

After reading `_shared-memory/DIRECTIVES.md` + `_shared-memory/WORK-TOWARD.md` on cold-start, every agent ALSO reads `D:\Sinister Sanctum\skills\HUB.md`.

The Skills Hub is the single discovery surface for every bot, tool, skill, external import, and invention currently available in Sanctum. Status / install_state / security posture / one-line "when to use it" for each artifact in one place.

**Source of truth:** `D:\Sinister Sanctum\skills\_REGISTRY.yaml` (YAML registry). `skills\HUB.md` is regenerated from it by `D:\Sinister Sanctum\automations\sync-fleet.ps1 -Apply`.

**Why it matters:** without HUB, agents grep `.mcp.json` + `tools/_INDEX.md` + `skills/_INDEX.md` + `inventions/` separately to know what's available. With HUB, one read tells you the full surface area + what's pending operator click + what security gates apply.

**Adding a new artifact:** append a row to `_REGISTRY.yaml` (one entry per artifact), then `sync-fleet.ps1 -Apply`. Never hand-edit `HUB.md` once sync-fleet is live â€” the next regen overwrites manual changes.

Full posture: `D:\Sinister Sanctum\skills\SECURITY.md` covers deny-list / allow-list / Vault / Codex / lane / external-imports / MCP hygiene in one doc.
