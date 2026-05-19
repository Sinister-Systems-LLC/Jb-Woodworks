# 02-OPERATOR-QUEUE â€” what the operator is waiting on right now

**Generated:** 2026-05-18T23:00Z (Phase 8s). Live state via `sinister-bus.pending_actions`
+ `sentinel.check_urgent` once Claude Code is restarted.

## ðŸ”´ CRITICAL (operator action this week)

1. **Yurikey51 root cert expires 2026-05-24** â€” source Yurikey52 from yuriservice (TG `t.me/yuriservice`) by 2026-05-23. Without it, phone-stack + pure-API attestation breaks server-side.
2. **PI 0/3 on phones P1 + P2** â€” interactive Google re-auth: Settings â†’ Passwords & accounts â†’ Google â†’ Account sync â†’ â‹® â†’ Sync now â†’ re-enter password. Both phones.

## ðŸŸ  HIGH (do this session if possible)

3. **Restart Claude Code** so the 12 new MCP servers (Sinister Bots) load + the new bus tools (run_script, memory_garden, codec, vault) are visible.
4. **Install Custodian 24/7 daemon** (sandbox-blocked for me):
   ```powershell
   cd 'D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\custodian'; .\install-task.ps1
   ```

## ðŸŸ¡ MEDIUM (when ready)

5. **Set `ANTHROPIC_API_KEY`** user env var â†’ unlocks Scribe daily-digest + Curator code-scout.
6. **Set `SINISTER_VAULT_PASSPHRASE`** user env var â†’ at-rest vault works for operator-private files.
7. **Sinister LLC migration:**
   ```powershell
   C:\Users\Zonia\Desktop\Prepare-Migration.bat            # already run once; safe to re-run
   cd 'D:\Sinister Sanctum\automations'; .\migrate-projects.ps1
   .\secret-scrub.ps1                                      # MUST PASS (TT capsolver.key flagged)
   ```
8. **Pick LICENSE** for `D:\Sinister Sanctum\LICENSE` (currently placeholder). MIT or Proprietary recommended for Leo-collaboration scope.

## ðŸŸ¢ LOW / OPTIONAL

9. **Pull Ollama models** for Tier-2 bots (Triage / Librarian / Researcher) â€” they run in degraded fallback until then:
   ```powershell
   cd 'D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\docker'; .\setup.bat
   docker exec -it ollama ollama pull qwen2.5:1.5b qwen2.5-coder:7b nomic-embed-text
   ```
10. **Drive encryption** â€” see `04-RECOVERY.md` for the VeraCrypt-container plan researched 2026-05-18. Operator decides; sandbox can't encrypt anything.
11. **Rebuild stale UA graphs** â€” LOA 27d, LOA/RKA 29d. `06_UNDERSTAND/<name>/_LAUNCH.bat`.
12. **Hacker bot** â€” RE'd from `AKCodez/hackingtool-plugin`; deferred pending operator OK to fetch upstream.

## Operator-only because of sandbox boundaries

- All env-var sets
- All scheduled-task installs
- All git pushes to remote
- All source-side file modifications (the stubs at `01_MEMORY/<proj>/_to-copy-to-source/` are dropped in via `Prepare-Migration.bat`)
- All Hetzner deploys

## Live updates

This file is hand-edited at phase boundaries. For LIVE state:

```
sinister-bus.pending_actions     -> aggregated across all runlogs
sentinel.check_urgent             -> 6 default alarms
sinister-bus.runlog_latest <name> -> any specific recent script run
```
