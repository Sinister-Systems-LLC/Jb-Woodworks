# Author: Sinister Sanctum master agent (test, Claude) :: 2026-05-20T23:40Z

# Sanctum :: complete autonomous scope-plan (auto-mode dogfood walk)

> Generated per `auto-mode-launcher-pattern.md` PHASE 2 contract.
> Branch context: `agent/sinister-sanctum/launcher-auto-mode-2026-05-20` (isolated; immune to sibling contention).
> Plan-review inputs (PHASE 1): MASTER-PLAN.md + prior turn audit + knowledge/_INDEX.md + this turn's PROGRESS entry.

## PHASE 1 inputs surveyed

- `_shared-memory/MASTER-PLAN.md` — URGENT A1-A10 mostly SHIPPED; B6-B14 mostly SHIPPED or operator-gated; C1-C9 medium operator-gated; D1-D4 low operator-gated; deferred-table 8 items all operator-side blockers.
- `_shared-memory/PROGRESS/Sinister Sanctum.md` — top entry is THIS turn's 23:35 launcher auto-mode ship (commit c145aff + 7e90b09).
- `_shared-memory/knowledge/_INDEX.md` — auto-mode-launcher-pattern at top; 100+ entries cataloged.
- Prior turn's drift audit (23:00) — 14 unindexed brain entries indexed; 8 sibling-lane M files left for sibling commits.
- Multi-agent contention observed this session — sibling-lane hard-reset clobbered uncommitted master-lane work mid-edit (recovery: cut isolated branch off main).

## 1. Shipped (last 7 days, with commit hashes)

This session walk only — see MASTER-PLAN.md `## ✅ Shipped` for the full ledger.

| Commit | Branch | What |
|---|---|---|
| `c145aff` | `agent/sinister-sanctum/launcher-auto-mode-2026-05-20` | Launcher auto-mode (`'auto'` BuiltinPhrase + picker row `9` + modeMap['9'] + custom-prompts-renumber + Desktop one-click bat + canonical-tree mirror + brain doctrine + _INDEX row). |
| `7e90b09` | same | PROGRESS milestone + multi-agent contention lesson note. |
| `be8726e` | `agent/sinister-os/ph1-bootstrap-2026-05-20` | Brain-index drift sweep — 14 unindexed entries indexed + master-lane drift commit (`Sinister Sanctum.md` PROGRESS + cygpath fix in `build-sanctum-console.sh` + `Merge-To-Main.bat` durable bat + test-agent broadcast + inbox mode-switch). |

## 2. Open master-actionable (each row carries EXACT-INSTRUCTIONS + EXPECTED-OUTPUT + VERIFICATION + COMMIT-MESSAGE)

### M1 — Brain entry: multi-agent-branch-contention-isolation-pattern

**Hypothesis:** sibling-lane sessions can do `git reset --hard HEAD` on the shared workspace mid-edit, clobbering uncommitted master-lane changes. Need a doctrine entry that codifies the isolation pattern.

- **EXACT-INSTRUCTIONS:** Write `_shared-memory/knowledge/multi-agent-branch-contention-isolation-pattern.md` (~150 lines) covering: the failure mode (reflog evidence + my own loss this turn), the fix (cut isolated branch off main BEFORE significant edits; commit FIRST then push; never trust the working tree across multi-second pauses on shared D:); composes-with table (canonical-10 + cross-agent-coordination + canonical-3); anti-patterns (uncommitted work spanning multiple turns; assuming branch stays put while you edit; pushing without verifying HEAD).
- **EXPECTED-OUTPUT:** the .md file + a row in `_INDEX.md` at top.
- **VERIFICATION:** `grep -c "## TL;DR\|## Related topics\|## Anti-patterns" multi-agent-branch-contention-isolation-pattern.md` → 3.
- **COMMIT-MESSAGE:** `docs(brain): multi-agent-branch-contention-isolation-pattern + _INDEX row`
- **Status:** in_progress this turn (Task #11).

### M2 — Index the auto-mode brain entry on the source-of-truth branch

Currently `auto-mode-launcher-pattern.md` is indexed in `_INDEX.md` only on `agent/sinister-sanctum/launcher-auto-mode-2026-05-20`. When that branch merges to main, the index addition merges with it. Confirm at merge time; no separate action needed pre-merge.

- **EXACT-INSTRUCTIONS:** N/A (handled automatically by merge).
- **VERIFICATION:** post-merge: `grep auto-mode-launcher-pattern _INDEX.md` on `main`.
- **Status:** blocked-by M3 (operator merge).

### M3 — Smoke-test auto-mode end-to-end (spawn the launcher with `-Mode auto`)

The PSParser + composed-phrase smoke is green. The HARNESS-spawn smoke is not — i.e. fire the actual launcher (not `-NoLaunch`) to confirm a spawned Claude session lands on the AUTONOMOUS LOOP MODE phrase correctly.

- **EXACT-INSTRUCTIONS:** Operator (or master via `Start-Process powershell`) launches `C:\Users\Zonia\Desktop\Start-Sinister-Auto-Session.bat`, picks a project (e.g. snap-emu), agent-name + accent, observes the spawned git-bash + Claude window receives the AUTONOMOUS LOOP MODE phrase in clipboard.
- **EXPECTED-OUTPUT:** spawned Claude window shows the multi-PHASE prompt; agent begins PHASE 1 plan-review.
- **VERIFICATION:** PROGRESS/<agent>.md gets a turn entry within ~5 min of spawn.
- **Status:** operator-gated only because it requires a fresh launcher-window the operator drives interactively. Master can verify the phrase composition (already done); master can't sit at the operator's keyboard.

### M4 — Brain entry: launcher-mode-evolution (v1 dev/audit → v8 auto)

The BuiltinPhrases dict has accumulated 9 modes (rkoj + overview + dev + audit + deploy + push + debug + explore + auto). Worth codifying the evolution + the mode-picking matrix so future agents pick the right mode.

- **EXACT-INSTRUCTIONS:** Write `_shared-memory/knowledge/launcher-mode-evolution.md` covering: v1-v8 changelog with PR/commit links, mode-picking decision tree (single-feature → `dev`; full-scope → `auto`; etc.), when to add a NEW mode vs reuse existing.
- **EXPECTED-OUTPUT:** the .md file + `_INDEX.md` row.
- **VERIFICATION:** grep for v1-v8 markers and decision-tree section.
- **COMMIT-MESSAGE:** `docs(brain): launcher-mode-evolution v1-v8 + mode-picking decision tree`
- **Status:** pending.

### M5 — Re-mirror Desktop bat for byte-parity with canonical tree

Desktop bat md5 `62acbbd...`; canonical tree md5 `1eee494...`. 47-byte diff. Likely a line-ending / trailing-newline mismatch. Re-copy Desktop → tree (or vice-versa) so they match.

- **EXACT-INSTRUCTIONS:** `cp /c/Users/Zonia/Desktop/Start-Sinister-Auto-Session.bat /d/Sinister\ Sanctum/tools/session-launcher/Start-Sinister-Auto-Session.bat`; verify with `md5sum`.
- **EXPECTED-OUTPUT:** identical md5.
- **VERIFICATION:** `md5sum` returns same hash for both.
- **COMMIT-MESSAGE:** `chore(launcher): byte-parity Desktop ↔ canonical tree auto-session bats`
- **Status:** pending (1-min fix).

### M6 — Verify launcher branch can merge to main cleanly

Pre-flight check: does the current branch merge clean to main? If yes, the operator merge is single-click.

- **EXACT-INSTRUCTIONS:** `git checkout main && git merge --no-commit --no-ff agent/sinister-sanctum/launcher-auto-mode-2026-05-20 && git merge --abort` (just probes for conflicts).
- **EXPECTED-OUTPUT:** no conflict markers, clean merge possible.
- **VERIFICATION:** `git merge --no-commit` returns exit 0.
- **Status:** pending (low risk — branch was cut from main).

## 3. Operator-gated (one-liner unblocks per row)

Reproduced from MASTER-PLAN.md unchanged. Most are durable env-var / decision / physical-action gates that NO master sweep can collapse.

- **O1 ANTHROPIC_API_KEY** → `[Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", "<key>", "User")` then restart Claude Code. Unblocks Scribe / Curator / Chatbot.
- **O2 SINISTER_VAULT_PASSPHRASE** → same pattern with vault passphrase.
- **O3 Restart Claude Code** → load ruflo + vault MCPs into the session.
- **O4 Sanctum LICENSE pick** → operator decides AGPL-3.0 (master recommendation) vs MIT/Apache-2 (see LICENSE-CANDIDATES.md). Repo is Private so no immediate urgency.
- **O5 Register `SinisterAgentWatchdog`** scheduled task → Double-click `Sinister-Install-Custodian.bat`-style installer OR run `Start-Process -Verb RunAs powershell -File install-watchdog-task.ps1`. Custodian already shipped per prior R1.
- **O6 RKOJ stuck on :5077** (A5 in MASTER-PLAN) → Close broken RKOJ window OR double-click upgraded `Stop-All-RKOJ.bat` (self-elevating).
- **O7 B13 RKOJ UI 1:1** plan operator thumb → review `_shared-memory/plans/rkoj-ui-1to1-2026-05-20/pass-1-draft.md` → 👍 to execute.
- **O8 Yurikey52 sourcing** → physical-world action (operator buy keybox).
- **O9 PI 0/3 phones** → interactive Google re-auth on phones.
- **O10 `gh auth refresh -s workflow`** → browser-interactive scope grant.
- **O11 Pull Ollama models** → operator-side `docker exec ollama ollama pull qwen2.5:1.5b` etc.
- **O12 Sinister LLC migration** → `Prepare-Migration.bat` + `migrate-projects.ps1` + `secret-scrub.ps1` MUST PASS, then operator chooses migration window.
- **O13 Operator merge** `agent/sinister-sanctum/launcher-auto-mode-2026-05-20` → main → unblocks auto-mode for all future cold-starts via the canonical Start-Sinister-Session.bat picker (Desktop one-click already works on the topic branch via path-discovery).

## 4. Sibling-lane (cross-agent asks; do NOT touch source)

- **S1 Kernel APK** — camera-harvest-network plan in flight (`plans/kernel-apk-camera-harvest-network-2026-05-20T2030Z/plan.md`); lyric-hal A1 silicon structural wall + cameraspoof auto-load gap. Master cannot drive (cross-lane edit per canonical-10). Surface as a cross-agent watching item.
- **S2 Sinister Panel** — heartbeat-500 schema-drift fix landed on `agent/sinister-panel/heartbeat-500-hardening`; awaits merge to main + bat-fire to backend. Cross-agent ASK status: ✅ ACK already sent (commit `5f98278` panel: ACK close sanctum /analytics + Hetzner-sync ASK).
- **S3 Snap-EMU** — autonomous lane EXHAUSTED at 5-angle ceiling; 6 untested-angles ladder mapped (`snap-emu-untested-angles-ladder-2026-05-20.md`). Master cannot drive without snap-emu agent claiming.
- **S4 TT-API** — Phase 1 libpipo bridge SHIPPED; Phase 2 active-invoke gated on real register/v3 capture. Master cannot drive.
- **S5 Sinister Bumble** — Phase 1+2 deliverables ready, operator-gated on APK+AOSP rebuild.
- **S6 LetsText** — Round 56 tab-perf doctrine shipped (cross-fleet reusable). Sanctum should pull pattern into local doctrine if applicable.

## 5. Deferred (with named blocker)

| Item | Blocker | Mitigation |
|---|---|---|
| ANTHROPIC_API_KEY | Operator-side env var | [NO KEY] chip planned slice O |
| SINISTER_VAULT_PASSPHRASE | Operator-side env var | same |
| Yurikey52 sourcing | Physical-world buy | brain entry tracks deadline |
| PI 0/3 phones | Phone-side interactive Google auth | brain entry + operator screenshot |
| LICENSE pick | Operator decision | placeholder All-Rights-Reserved (repo Private) |
| `gh auth refresh -s workflow` | Browser-interactive | auto-push daemon logs warn-only when workflow scope needed |
| Pull Ollama models | Disk/docker | brain entry; Tier-2 bots run in degraded fallback |
| Snap β scrcpy capture | Operator track-pick | sibling-routed (snap-emu agent) |
| Sinister OS hardware buys | Physical-world purchase | Sinister OS plan IS the deliverable; execution is operator-paced |
| RKOJ UI 1:1 operator 👍 | Operator decision on B13 | plan + smoke + doctrine landed; awaits go |

## Next-slice surface

After M1 (multi-agent contention brain entry) → M4 (launcher-mode-evolution brain entry) → M5 (bat byte-parity) → M6 (merge probe). All four are <30min total master work, fully in-lane, no operator gates.

The /loop continues with M1 next.
