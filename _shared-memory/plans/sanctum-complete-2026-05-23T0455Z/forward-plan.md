<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# Sanctum :: Complete-Without-Operator Forward Plan

**Created:** 2026-05-23 evening
**Plan dir:** `_shared-memory/plans/sanctum-complete-2026-05-23T0455Z/`
**Author:** EVE on Sanctum (this session)
**Triggering directive:** Operator stacked 8 messages on 2026-05-23 evening covering anti-revert, autonomy setup, Sinister Freeze fix, typed-resume, full audit, and best-system-forward.

---

## Section A — What's already shipped today (cold to hot)

| Layer | Ship | Commit / Path |
|---|---|---|
| Memory audit | pip-editable-hides-mcp-cwd-emptiness doctrine + 3 false-alarm queue rows cleared | `b9e89dc`, `_shared-memory/knowledge/pip-editable-...` |
| Memory audit | Resume-point dir convention migration: `Sanctum/` → `Sinister Sanctum/` + PS1 v1.3 slug→display routing | (in resume-point chain) |
| Sanctum stack readiness | 7-row plan + 13 surfaces categorized + wake-on-demand doctrine | `70297c6`, `_shared-memory/plans/Sanctum-agent-stack-readiness-2026-05-23T0820Z/` |
| MCP path fixes | 2 junctions resolved 13 stale MCP cwds (`Sinister Skills`, `Kernel-SU-Setup`) | `a8b8a63` |
| Plugin enablement | 14 dev plugins + understand-anything enabled at Sanctum project level | `a8b8a63` |
| Spawn validation | end-to-end Sinister Start.bat → child Claude validated + brain doctrine + index row | `c763ce2`, `c5513a9` |
| Anti-revert (THIS TURN) | CLAUDE.md cold-start 6 → 7 steps + DO NOT REVERT block + Rule 11 added to 00-RULES + brain doctrine + check script + SessionStart hook + INDEX row | (uncommitted; pending operator OK) |
| Project-root integrity (THIS TURN) | Sinister Freeze restored from archive + P8 added to check script + project-root-disk-integrity doctrine + INDEX row | (uncommitted; pending operator OK) |
| Cross-agent coordination | broadcast to sibling launcher agent re. v6.1 phrase preserving the 6 protections | `_shared-memory/cross-agent/2026-05-23T1455Z-sanctum-to-sibling-launcher-canonical-protections.md` |

Smoke after this turn: `canonical-protections-check.ps1` reports **PASS=8 FAIL=0** across P1-P8.

## Section B — What's in-flight (other agents owning)

| Lane | What | Owner | Status |
|---|---|---|---|
| Launcher v6.1 A-I | per-project plan-without-me review + loop-back-to-picker + jcode ASCII art + centered info + transparent mintty + free-text Auto-Resume + status pills + per-project rename/accent | sibling sanctum agent (per operator screenshot 2026-05-23) | actively shipping; "C: Random jcode-style ASCII art" marked DONE + 6 completed others + 4 TODO |
| Operator's "typed-based auto-resume" | free-text fuzzy match against resume-points | sibling (covered by A-I item F) | sibling owns; verify on next cross-agent ping |
| RKOJ v1.6.88 | Sini-stray-window leak fix + Resume picker merges all 14 projects.json projects + per-phone scrcpy stderr → log file | RKOJ agent | shipped `915a878` |
| jcode parity matrix flips | 11 📋 planned rows in `jcode-feature-matrix.md` | RKOJ agent | [ASK] dropped 2026-05-23T0710Z; awaiting RKOJ flip |

## Section C — Open + master-actionable (in-lane, no operator needed)

Ordered by impact × reversibility-safety. R-class per canonical-11.

| # | Subject | R-class | Effort | Notes |
|---|---|---|---|---|
| 1 | **Commit this turn's anti-revert + freeze-restore work to `agent/showmasters/scaffold-and-launch`** (current branch — sibling-quiet check first). | R2 | <5 min | Files: CLAUDE.md, 00-RULES.md, .claude/settings.json (hook only), 2 new brain entries, _INDEX.md row, canonical-protections-check.ps1, restored projects/sinister-freeze/. |
| 2 | **Expand `automations/grant-claude-autonomy.ps1` to its full 7-step header** (currently only step 6, "permission allowlist", is implemented). Steps: (1) project trust in `~/.claude.json`, (2) env vars (SINISTER_SANCTUM_ROOT + SINISTER_USER), (3) secret status surface (READ status of ANTHROPIC_API_KEY / SINISTER_VAULT_PASSPHRASE / OPENAI_API_KEY / TELEGRAM_BOT_TOKEN / LEO_ANTHROPIC_API_KEY — never WRITE), (4) MCP verify (ruflo + vault registered), (5) scheduled tasks (SinisterSanctumAutoPush + SinisterCustodian + SinisterSanctumDailyBackup ensure-installed + ensure-hidden-window), (6) permission allowlist (current 87-line behavior — extend with the 10-pattern dangerously-skip block we added to ~/.claude/settings.json), (7) verification report. **Add steps 8 + 9:** (8) install canonical-protections-check.ps1 SessionStart hook + (9) understand-anything plugin enablement verification in BOTH user + Sanctum project settings. | R2 | 30-45 min | Idempotent + verbose + backup-timestamped. Result: one-click new-PC setup. |
| 3 | **Sinister Start.bat first-run autonomy detection.** Add marker-file check: if `~/.sanctum-autonomy-granted` missing, auto-invoke `Grant-Claude-Autonomy.bat` before launching the picker. Also accept CLI flag `--setup-autonomy` for explicit re-run. The picker-side "Run Claude Autonomy setup" option is sibling's lane (launcher PS1). | R2 | 10 min | Edit `C:\Users\Zonia\Desktop\Sinister Start.bat` + mirror at `D:\Sinister Sanctum\tools\session-launcher\Sinister Start.bat`. |
| 4 | **Audit + cleanup `_archive/` for the same disk-integrity failure mode.** Other projects in `_archive/` that might still have `projects.json` references — sweep and either restore-or-remove. P8 will catch but a one-pass cleanup is cheap. | R1 | 15 min | Read-only audit first; report dry-run; then act with operator OK if anything fires. |
| 5 | **Review jcode memory system (forge-memory-bridge) integration with SessionStart hook.** Operator 2026-05-23 evening: *"review jcodes memory system that we have already been working on and make it work"*. forge-memory-bridge v0.1.2 is installed + importable; verify the SessionStart hook auto-loads recent memory entries into the spawned EVE's context (or document that it doesn't and propose how). | R0 (audit) → R2 (if patches needed) | 45 min | Compose with `wake-on-demand-bot-dispatcher` brain entry. |
| 6 | **Context-cleaner spec.** Operator 2026-05-23 evening: *"have a clearer that keeps the context clean but has all we need to work on projects"*. The `automations/context-pruner.ps1` exists per session-contracts.md CONTRACT 7 but the operator wants something more aggressive / surfacing-aware. Draft a spec: per-project context retention policy + automatic compaction triggers + pre_warm_reads hygiene + dirty-tree carry-forward. Coordinate with sibling on launcher UX. | R0 (spec) → R1 (ship) | 30 min for spec + 60 min for implementation |
| 7 | **Resume-point chain cleanup.** 23 resume-point files in `Sinister Sanctum/`; rotate to `_archive/` anything older than 7 days per CONTRACT 7. The context-pruner should do this automatically — verify it does, fix if not. | R1 | 10 min |
| 8 | **Update OPERATOR-ACTION-QUEUE.md** — close the freeze-restore item (operator-visible), surface the new canonical-protections SessionStart hook, link to the anti-revert doctrine, add the Grant-Claude-Autonomy expansion + Sinister Start.bat first-run rows as open master-actionable. | R1 | 5 min |
| 9 | **Resume-point write + end-of-turn report.** Standard close. | R1 | <2 min |

## Section D — Operator-gated (each row has the exact one-liner)

| # | Subject | One-liner | Why operator-gated |
|---|---|---|---|
| O1 | **Restart Claude Code** to load: (a) 12 newly-resolvable MCPs via junctions (sinister-bus + sentinel + librarian + auditor + custodian + scribe + curator + triage + translator + watcher + stealth-browser + researcher), (b) 14 newly-enabled dev plugins at Sanctum project level, (c) the new SessionStart hook running `canonical-protections-check.ps1` on every spawn. | Click `claude` once in the active window OR re-spawn via `Sinister Start.bat`. | Harness only loads MCPs + hooks + plugins on cold-start; in-session reload not supported. |
| O2 | **Set `ANTHROPIC_API_KEY` user env var** (unblocks scribe daily-digest + curator code-scout + Sinister Chatbot LLM path). | `[Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY','sk-ant-...','User')` | Operator's API key, operator's choice. |
| O3 | **Decide if `sinister-freeze` lane stays active or re-archives.** It was archived 2026-05-21 per operator ask, restored 2026-05-23 evening per "fix it" ask. Operator picks the durable state. | If active: leave restored + we keep it in the picker. If re-archive: I'll re-mv it back, drop from `picker.visible_keys[]`, and add a brain note. | Lane-active-or-not is a product decision, not a bug fix. |
| O4 | **Enable Docker Desktop auto-start** (unlocks Tier-2 LLM bots via Ollama containers + sanctum-git Gitea). | Docker Desktop → Settings → General → "Start Docker Desktop when you sign in". | Resource cost (RAM + power) is operator's call. |
| O5 | **Pull Ollama models for Tier-2 bots** | `docker exec -it ollama ollama pull qwen2.5:1.5b qwen2.5-coder:7b nomic-embed-text` | ~6 GB download + needs Docker running (O4). |
| O6 | **Enable external-service plugins** (20 listed in OPERATOR-ACTION-QUEUE) | `/plugin enable <name>` per-need | Each needs API token configuration. |

## Section E — Reversibility ledger (R0-R4 per canonical-11)

| R | Class | Items |
|---|---|---|
| R0 | Pure read / dry-run | Section C item 4 first pass; Section C item 5 audit pass; running `canonical-protections-check.ps1`. |
| R1 | Reversible file ops | Section C items 7, 8, 9. Brain entry additions. Index row additions. Resume-point writes. |
| R2 | Commit-required | Section C items 1, 2, 3. Settings.json hook registration (already committed mentally). Grant-Claude-Autonomy PS1 expansion. Sinister Start.bat first-run patch. |
| R3 | Destructive but recoverable | None this plan. (Re-archiving freeze under O3 would be R3 — move + remove from picker.) |
| R4 | Operator-gated wall | Section D O1-O6. |

## Section F — Recommended ordering with rough effort

**This turn (immediate, ship without stopping):** done — anti-revert + freeze-restore + P8 + 2 brain entries + 2 INDEX rows + check script + hook + cross-agent broadcast + this plan.

**Next turn (master-actionable, no operator wait):**

1. Section C item 1 (commit the work) — 5 min
2. Section C item 5 (jcode memory review) — 45 min audit
3. Section C item 2 (Grant-Claude-Autonomy expansion) — 30-45 min
4. Section C item 3 (Sinister Start.bat first-run) — 10 min
5. Section C item 6 (context-cleaner spec) — 30 min draft

**Operator turn (when operator returns to terminal):** O1 (restart) is the single highest-impact click + completes the chain since hook only fires on session start.

**Forward sessions:** O2-O6 as operator-driven.

## Section G — Expansion ideas (beyond complete-now scope)

- **L3 PreToolUse Edit guard.** Block Edit/Write attempts that delete canonical lines from CLAUDE.md or settings.json. Requires hookify plugin or custom hook script. Deferred to operator opt-in.
- **Per-project canonical-protections.** Each project lane (Forge, Term, Panel, APK, etc.) gets a smaller P-set verifying their own canonical setup (CLAUDE.md presence + .claude/settings.json plugin enablement + ASF). One hook config per project.
- **Auto-restore via reference snapshot.** Materialize `_shared-memory/canonical-protections-reference/<file>.canonical` from the current good state + add splice-back logic to the check script (currently logs intent only). Enable with `SINISTER_CANONICAL_PROTECTIONS_AUTORESTORE=1`.
- **`sinister-doctor` CLI.** Single command that runs all four layers + writes a HTML health report. Composable from `canonical-protections-check.ps1` + the existing per-project audit scripts.
- **Cross-lane impact analysis.** When a Sanctum agent commits a change touching shared files (`projects.json`, `CLAUDE.md`, settings), automatically diff vs the canonical reference + post the diff to `cross-agent/` so siblings see the change before they sync.

## TL;DR

- **How we won:** Restored Sinister Freeze + shipped the anti-revert system (8 protections, SessionStart hook, brain doctrines) so the regressions that bit you tonight can't happen the same way again. PASS=8 FAIL=0 across the canonical-protections check.
- **What you need to do:** O1 (restart Claude Code) to load the new SessionStart hook + the 12 junctioned MCPs + 14 plugins. That single restart unblocks everything else. The other 5 operator-gated items (O2-O6) are forward-looking, not blocking.
