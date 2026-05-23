<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# Do-not-revert operator-canonical protections (2026-05-23 evening)

> **Status:** doctrine, standing-rule, binding for every spawned EVE session.
> **Origin:** operator 2026-05-23 evening, verbatim:
> 1. *"i need you to fix the things you changed in my memory that removed my sandbox blocks, hidden memory system all that and add it back to all session starts"*
> 2. *"make the understand anything called before each propject start like we use to do and make sure i dont have these issues again and we do not revert like we just did"*
> 3. *"make the best system moving forward"*

## What got removed (root cause)

The launcher v6 concise rewrite (`bba4231` polish-launcher + earlier v6 commits) compressed the cold-start phrase from ~6 KB of inline templates to a single `Build-Phrase` helper with 3 shapes (scaffold/general/resume) + a `session-contracts.md` reference. Token-saving win (~3000 tokens/spawn), but the compression dropped explicit references to:

- The understand-anything pre-call (used to be invoked before first edit in older sessions).
- `D:\Sinister\Sinister Skills\09_REFERENCE\SANDBOX-GOTCHAS.md` (the sandbox green-path doctrine).
- The "hidden memory hub" at `D:\Sinister\Sinister Skills\01_MEMORY\master\OPERATOR-DIRECTIVES.md` (this one survived in CLAUDE.md but was dropped from streamlined spawn phrases).

Operator caught the regression on 2026-05-23 evening + ordered restoration + anti-revert protection so it cannot happen again.

## Six protections that MUST be preserved

| # | Location | Required state | Verify how |
|---|---|---|---|
| P1 | `~/.claude/settings.json` | `bypassPermissions: true` AND `defaultMode: "bypassPermissions"` AND `permissions.allow[]` contains `Bash(claude --dangerously-skip-permissions*)` + `PowerShell(*claude --dangerously-skip-permissions*)` | `automations/canonical-protections-check.ps1` |
| P2 | `~/.claude/settings.json` + `D:\Sinister Sanctum\.claude\settings.json` | `enabledPlugins["understand-anything@understand-anything"]: true` in BOTH files | check script |
| P3 | `D:\Sinister Sanctum\CLAUDE.md` | Cold-start step 0 = invoke `understand-anything:understand-explain` BEFORE substantive work | grep `understand-anything:understand-explain` in CLAUDE.md |
| P4 | `D:\Sinister Sanctum\CLAUDE.md` | Cold-start step 2 references `D:\Sinister\Sinister Skills\01_MEMORY\master\OPERATOR-DIRECTIVES.md` | grep `01_MEMORY\\master\\OPERATOR-DIRECTIVES.md` |
| P5 | `D:\Sinister Sanctum\CLAUDE.md` | Cold-start step 3 references `D:\Sinister\Sinister Skills\09_REFERENCE\SANDBOX-GOTCHAS.md` | grep `09_REFERENCE\\SANDBOX-GOTCHAS.md` |
| P6 | `_shared-memory/knowledge/` | Both this entry AND `sanctioned-bypasses-doctrine-2026-05-21.md` present AND indexed in `_INDEX.md` | check script + INDEX.md grep |

If ANY protection fails, the check script logs to `_shared-memory/canonical-protections-violations.log` + surfaces to the operator-action queue. Optionally (operator opt-in) it can auto-restore from the canonical reference snapshot at `_shared-memory/canonical-protections-reference/` (see "Auto-restore option" below).

## Enforcement layer (do-not-revert system)

### Layer 1 â€" Cold-start documentation (immediate)

Two source-of-truth files name the protections explicitly:
- `D:\Sinister Sanctum\CLAUDE.md` "DO NOT REVERT" block + Cold-start 7 steps.
- `D:\Sinister Sanctum\SESSION-START\00-RULES.md` Rule 7 + new Rule 11.

Every EVE session reads these on cold-start, so removal becomes visible to the next agent.

### Layer 2 â€" Auto-verify SessionStart hook (durable)

`D:\Sinister Sanctum\.claude\settings.json` registers a `hooks.SessionStart` entry that runs `automations/canonical-protections-check.ps1` on every session start. The script:

1. Reads each protection's expected state from this brain entry (parsed from the table above).
2. Verifies on disk.
3. Logs PASS/FAIL per protection to `_shared-memory/canonical-protections-violations.log`.
4. If any FAIL: prints a HIGH-VISIBILITY warning to the agent's startup output + appends a `[REVERT-DETECTED]` row to `OPERATOR-ACTION-QUEUE.md`.
5. (Opt-in flag) auto-restore from `_shared-memory/canonical-protections-reference/`.

### Layer 3 â€" Pre-write Edit guard (opt-in, future)

A PreToolUse hook on `Edit`+`Write` can block modifications to CLAUDE.md or settings.json that delete any of the canonical lines. Implementation: regex-check the new_string for required tokens; if a required token is in old_string but NOT new_string, reject the tool call with the violation reason. Deferred until operator opts in (hooks-blocking can be friction; doctrine + auto-verify covers most cases).

### Layer 4 â€" Brain entry (permanent, this file)

This entry IS the source-of-truth referenced by all other layers. It must remain indexed in `_shared-memory/knowledge/_INDEX.md`. The check script verifies INDEX.md row presence as protection P6.

## Auto-restore option

Operator can set env var `SINISTER_CANONICAL_PROTECTIONS_AUTORESTORE=1` to enable auto-restore mode. When set + check script detects a violation:

1. Read the canonical reference snapshot at `_shared-memory/canonical-protections-reference/<file>.canonical`.
2. Splice the missing/changed line back in (NOT a full overwrite; targeted patch).
3. Log the restore action to `_shared-memory/canonical-protections-restores.log` with diff + originating session.
4. Drop a `[AUTO-RESTORED]` row in `OPERATOR-ACTION-QUEUE.md` so operator sees what happened.

Default OFF. Operator opts in when ready to trust the auto-patcher.

## Composability

This doctrine composes with:

- `sanctioned-bypasses-doctrine-2026-05-21.md` (lists what bypasses are sanctioned; this entry pins them in place).
- `launcher-v6-concise-rewrite-2026-05-23.md` (root-cause origin of the regression).
- `agent-identity-eve.md` (defines who must obey: every EVE session).
- `forever-expanding-modular-architecture-doctrine.md` (no-hard-imports / append-only rules; this anti-revert layer is append-only itself).
- `spawn-validation-end-to-end-2026-05-23.md` (spawn surfaces all inherit these protections via `--dangerously-skip-permissions`).
- `pip-editable-stale-pth-correction-2026-05-23.md` (similar audit-anti-trap pattern: verify ground truth, not file-cache state).

## Anti-patterns to never repeat

1. **Streamlining-without-doctrine-check.** v6 concise rewrite saved ~3000 tokens/spawn but dropped semantically-required references. RULE: any token-saving rewrite of cold-start surfaces must enumerate which protections it preserves vs drops, and operator approves drops explicitly.
2. **Cold-start phrase as source-of-truth.** The launcher phrase is a CONVENIENCE for spawned sessions; the SOURCE-OF-TRUTH is CLAUDE.md + SESSION-START/. When the phrase shrinks, the source-of-truth files MUST still contain the canonical references â€" so the agent re-discovers them via the documented cold-start protocol.
3. **Trusting that the launcher phrase covers everything.** Even with v6.1's expanded phrase, the cold-start protocol in CLAUDE.md is what makes the session canonical. Future shrinkages of the phrase must not drop the CLAUDE.md side.
4. **Removing plugin enablement to "clean up settings".** Future EVE sessions touching `~/.claude/settings.json` or `.claude/settings.json` MUST diff their change vs the canonical reference + flag any plugin removal.

## Implementation status (2026-05-23 evening)

- [x] CLAUDE.md cold-start expanded from 6 to 7 steps + "DO NOT REVERT" block at top.
- [x] SESSION-START/00-RULES.md Rule 7 updated (explicit SANDBOX-GOTCHAS path).
- [x] SESSION-START/00-RULES.md Rule 11 added (understand-anything pre-call mandatory).
- [x] This brain entry shipped.
- [ ] `automations/canonical-protections-check.ps1` shipped (Layer 2 auto-verify).
- [ ] `.claude/settings.json` SessionStart hook registered (Layer 2 wiring).
- [ ] `_shared-memory/canonical-protections-reference/` snapshot dir created (auto-restore source).
- [ ] `_INDEX.md` row added for this entry.
- [ ] Cross-agent [ASK] to sibling launcher agent: v6.1 phrase preserves these six.

## Tags (for INDEX.md)

doctrine, standing-rule, binding, anti-revert, operator-hard-canonical-2026-05-23-evening, sandbox-blocks, hidden-memory-hub, understand-anything, sandbox-gotchas, operator-directives, cold-start, claude-md, session-start, settings-json, dangerously-skip-permissions, bypass-permissions, plugin-enablement, check-script, hooks-sessionstart, auto-restore-option, layer-1-documentation, layer-2-auto-verify, layer-3-pre-write-guard, layer-4-brain-entry, six-protections, p1-p6, no-revert, no-streamline-without-doctrine-check, 2026-05-23-evening
