# Sanctum Master Plan — Complete Everything (iter-25, 2026-05-25T07:25Z)

**Author:** RKOJ-ELENO :: 2026-05-25 (sanctum lane, master orchestration)
**Trigger:** operator `/loop ... create a plan to complete everything we need to complete` (2026-05-25T~07:25Z)
**Scope:** sanctum lane high-level only per `sanctum-scope-discipline-2026-05-24`. Lane work routes to lane owners — not duplicated here.
**Supersedes:** `sanctum-master-finish-everything-2026-05-25T0700Z/plan.md` (sibling plan; 5 of 6 priority items now SHIPPED — see Done table).
**Composes with:** `safe-quality-loops-doctrine-2026-05-24` + `loop-relentless-pursuit-doctrine-2026-05-25` + `single-repo-push-policy-2026-05-25` + `no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25` + `eve-ui-uniformity-doctrine-2026-05-24`.

---

## North-star (operator verbatim, last 24h)

1. **2026-05-25T05:58:37Z** — push Sanctum to GitHub + deploy/ folder for Leo + EVE.exe at root + auto-update + LINK + UAC self-elevate + first-time-setup. ✅ ALL DONE iter-22.
2. **2026-05-25T07:00:45Z** — rate-limit auto-balance + GPU 4090 + per-process resource quotas + operator-floor. 🟡 PLAN + RUNTIME SHIPPED iter-24 (P0); code edits P1.
3. **2026-05-25T07:08:40Z** — LINK live + Vault live + Sanctum-in-vault + auto-update GitHub + backup. 🟡 PLAN + 5 SCHTASKS LIVE iter-24; Leo redeem pending.
4. **2026-05-25T07:10:36Z** — smoke-test everything + UI good + EVE.exe update over LINK + Leo update popup. 🟡 NEW (this iter).
5. **2026-05-25T07:19:21Z** — faster spawn flow + one-Enter launch + terminal names + quick-launch + picker bypass. 🟡 NEW (this iter).
6. **2026-05-24T22:45:33Z** — phase-2 jcode animations + EXE logo. ✅ logo DONE iter-23; jcode phase-2 queued.
7. **2026-05-25T01:25:35Z** — image 61/65/66/67. ✅ 61/65/67 DONE iter-23; 66 PARTIAL.

---

## Status legend

| Glyph | Meaning |
|---|---|
| ✅ | DONE (commit/PR + smoke verified) |
| 🟢 | READY (code exists; needs runtime activation only) |
| 🟡 | IN-FLIGHT (sub-agent working OR partial ship; binary criterion not yet met) |
| 🟠 | QUEUED (concrete plan exists; awaiting iter slot) |
| 🔴 | OPEN (root-cause unclear OR design unresolved) |

---

## Done since iter-21 (iter-22/23/24 + sibling lanes)

| # | Item | Where | Iter |
|---|---|---|---|
| 1 | GitHub push for Leo (origin/main + tag) | `8e4ead3` + `leo-ready-2026-05-25-iter22` | 22 |
| 2 | `deploy/` folder (README + GETTING-STARTED + TROUBLESHOOTING + setup.py + first_time_setup.py + EVE.exe + 3 CLI guides) | `deploy/` | 22 |
| 3 | EVE.exe at repo root + `EVE.exe.sha256` sidecar | repo root | 22 |
| 4 | Auto-update (raw GitHub fetch + atomic swap + locked-file retry + Defender exclusion + AppData fallback) | `automations/eve_self_update.py` | 22 |
| 5 | UAC self-elevate (ctypes ShellExecuteW runas) | `deploy/first_time_setup.py:115` | 22 |
| 6 | First-time-setup 9-step (admin/clone/pip/winget/schtasks/claude-config/EVE-copy/spawn/summary) | `deploy/first_time_setup.py` | 22 |
| 7 | EVE crash detector + Kill-Stuck-EVE.bat wiring + --pre-compile guard | `automations/eve_crash_detector.py` | 22 (sub-E) |
| 8 | Sinister LINK invite system + 8h Leo invite | `deploy/SINISTER-LINK-INVITE-FOR-LEO.md` + `inv-20260525030949-022e5b` | 24 |
| 9 | Sinister Vault LIVE (1TB, 127.0.0.1:5078) + 6 subtrees + `_quota.json` | `D:\sinister-vault\` + `D:\Sinister Sanctum\_vault\` | (pre-existing) |
| 10 | EVE.exe icon embed (7-PNG .ico) + Python build script | `automations/eve-launcher/assets/eve-icon.ico` + `build-eve-exe.py` | 23 |
| 11 | eve.py items 61 centered menu + 65 Enter/X/unlimited + 67 100%-real cleanup + jcode-inspired labels | `automations/eve-launcher/eve.py` | 23 |
| 12 | spawn-setup-wizard mintty exit 126 fix (quoted path with space) | `automations/spawn-setup-wizard.ps1` | 23 |
| 13 | fleet-updates.jsonl rotate 80 MB → 18 KB (2 corrupt rows + 10 oversized) | `_shared-memory/fleet-updates.jsonl` | 23 |
| 14 | 5 governor schtasks installed (VaultGitHubSync 15m / LinkPoller 5m / OAuthHealthPoll 5m / AccountBalancer 10m / ResourceQuota 60s) | `schtasks /Query` | 24 |
| 15 | Ollama 0.5.7 + qwen2.5-coder:7b + nomic-embed-text pulls (GPU 4090) | winget + ollama pull | 24 |
| 16 | sinister-link-poller.ps1 0-byte gap + Python replacement | `automations/sinister_link_poller.py` | 22 |
| 17 | Sub-K (Leo MCP+Docker+bots+autonomy) + Sub-L (Overseer first-fire audit Sinister Term) | leo-handoff-readiness audit + PROGRESS/Sinister Overseer.md | 21 |
| 18 | Loop+swarm default ON + L) Sinister LINK menu wiring | `agent-prefs.json` + `projects.json` + `main_menu.py` | 22-23 |

---

## P0 — Activate this iter (24h max)

### P0.1 — Smoke-test EVE.exe end-to-end UI (operator 07:10:36Z + 07:19:21Z)

Operator: "smoke test everything and make su the ui is good".

- **WHAT:** spawn EVE.exe in a fresh mintty, click through every menu key (R/G/T/O/N/W/L/X), confirm: centered menu renders, Enter→back works, X→exit works, accounts page shows >4 slots (infinite-accounts doctrine), Sinister LINK page renders state + invite generation, no `100% real` string anywhere, all helper helpers labeled `jcode-inspired`.
- **WHERE:** `D:/Sinister Sanctum/EVE.exe`
- **WHO:** sub-agent `iter25-eve-ui-smoke`
- **HOW:** spawn EVE.exe via `Start-Process -PassThru` capturing stdout to a transcript; walk pages programmatically by piping keystrokes; OR use the new `--profile single-agent-focus` flag if it exists; record before/after screenshots-equivalent (terminal dumps) into `_shared-memory/audits/eve-ui-smoke-iter25-2026-05-25.md`.
- **PASS:** every of 8 menu keys returns to main; X exits cleanly; ≥3 minor doctrine drifts logged (or zero, with proof).

### P0.2 — Quick-launch mode + terminal-name persistence (operator 07:19:21Z)

Operator: "make this entire process way more efficient with the quickest way to open my terminals and make the names work and set here". Image 7 = picker. Image 8 = Sinister Sanctum label (terminal title shows the lane).

- **WHAT:** add `Q) Quick-launch` to picker that bypasses the 3-question primer (`SINISTER_QUICK_LAUNCH=1`) → uses last-spawn defaults from `_shared-memory/script-runs/last-spawn.json`. Make mintty title persist as `Sinister <Lane>` (e.g. `Sinister Sanctum`) using `--title` flag, not the volatile bash `\033]0;...\007` escape.
- **WHERE:** `automations/eve-launcher/eve.py` (picker dispatch + key handler) + `automations/start-sinister-session.ps1` (mintty `--title` flag, lines ~1700-1900) + new `_shared-memory/script-runs/last-spawn.json` (one row per lane).
- **WHO:** sub-agent `iter25-quick-launch`
- **HOW:** read existing spawn code in `start-sinister-session.ps1`, identify the 3 primer prompts, gate them on `if (-not $env:SINISTER_QUICK_LAUNCH) { ... }`. After spawn, append a normalized row to `last-spawn.json` so `Q` can recall. mintty title: ensure `--title "Sinister $LaneDisplay"` is on the command line.
- **PASS:** Q in picker → mintty opens in <2 s, title = exact "Sinister Sanctum" (or other lane), no primer prompts, no operator clicks.

### P0.3 — EVE.exe update notification over LINK (operator 07:10:36Z)

Operator: "make the eexe update oiver sinsiter link and leo will have popup to say update availabe or something".

- **WHAT:** when `eve_self_update.py` detects a new remote sha, write a `_shared-memory/cross-agent/eve-update-available-<sha>.md` note that the LINK poller propagates to the peer's repo via git pull. EVE.exe's main picker reads that file on every render and prints a `BRIGHTP [UPDATE AVAILABLE — new EVE.exe ready; press U)] RESET` banner at top of the picker.
- **WHERE:** `automations/eve_self_update.py` (detect-only mode writes update-available file) + `automations/eve-launcher/eve.py` (picker banner row + U) keystroke) + `automations/sinister_link_poller.py` (no edit; git pull surfaces the file on peer).
- **WHO:** sub-agent `iter25-update-notify`
- **HOW:** add `_write_update_available_marker()` to eve_self_update.py inside the existing `check-sha-differs` branch; pick file path `_shared-memory/eve-update-available.json`. In eve.py, in `banner()` or `render_picker()`, if marker file exists AND mtime > last-ack, print the banner row + add U) handler that runs `python automations/eve_self_update.py --apply`.
- **PASS:** operator: trigger sha drift (e.g., `echo bump >> EVE.exe.sha256.test`); within 5 min the marker file appears; EVE.exe picker shows the banner on next render; U) keystroke applies the update. Leo side: same banner after LINK sync.

### P0.4 — Wire `launch_rate_limit_governor.py --pre-launch` into launcher (sub-E plan P0)

- **WHAT:** add 5 lines to `start-sinister-session.ps1` right after PickBest (currently lines 1745-1818) that call `python automations/launch_rate_limit_governor.py --pre-launch --slug $forcedSlug` and abort spawn if the governor returns non-zero (e.g., slot exhausted + no fallback). Surface "operator-floor" reservation here.
- **WHERE:** `automations/start-sinister-session.ps1` ~line 1820
- **WHO:** main (sanctum lane)
- **HOW:** 5-line patch; AST-equivalent verify via `pwsh -Command "[ScriptBlock]::Create((Get-Content $f -Raw)) | Out-Null"`.
- **PASS:** spawning sanctum lane with all 4 slots rate-limited → governor returns non-zero with `slot-exhausted` reason; launcher aborts with operator-readable message instead of failing mid-spawn.

### P0.5 — Bulk-ack 22 `status=new` utterances (housekeeping)

Older utterances (2026-05-24T16:00-18:00Z) are addressed via CLAUDE.md hard-canonical blocks but never flipped to `acknowledged`.

- **WHAT:** Python sweep `automations/utterance_sweep_ack.py` with hardcoded `{ts → doctrine-ref}` map. For each NEW utterance with a doctrine match, flip status `new → acknowledged` + append a deliverable pointer.
- **WHERE:** new `automations/utterance_sweep_ack.py`
- **WHO:** main
- **HOW:** read `operator-utterances.jsonl` line-by-line, lookup ts in map, write `_acked` row.
- **PASS:** `grep -c '"status":"new"' operator-utterances.jsonl` drops from 22 → ≤5.

---

## P1 — This week (5-50 line edits each)

### P1.1 — Resource quota governor: RAM cap struct fix

Per sub-E plan: code comment in `automations/resource_quota_governor.py` admits the `JOBOBJECT_EXTENDED_LIMIT_INFORMATION` struct attaches to the job but doesn't enforce RAM cap. Fix the ctypes struct layout + flag bits.

- **OWNER:** sub-agent `iter25-quota-ram-cap` (specialized Windows ctypes work)
- **PASS:** spawn a `python -c "import numpy; numpy.zeros((1<<30,), dtype='float64')"` under the governor with 256 MB cap → OOM kill within 2 s, not 8 GB allocation success.

### P1.2 — Route `claude` through `claude-wrapper.ps1` (auto-429)

Wrapper exists but isn't on the real spawn path (mintty calls `claude` directly).

- **OWNER:** main + sub-agent `iter25-wrapper-route`
- **WHERE:** `automations/start-sinister-session.ps1` — replace bare `claude` invocations with `& "$SanctumRoot\automations\claude-wrapper.ps1"` call.
- **PASS:** spawn with a known-rate-limited account → wrapper detects 429 → auto-MarkLimited + auto-rotate-to-next-slot → spawn completes on healthy slot.

### P1.3 — Tier-2 bots auto-detect Ollama (librarian + triage + researcher)

Per sub-E plan section 3: bots already check `localhost:11434` for Ollama — no code edit needed, just confirm Ollama service is running + models pulled.

- **OWNER:** main (verify only after qwen2.5-coder pull completes)
- **PASS:** `curl http://localhost:11434/api/tags` returns ≥1 model; `python bots/librarian/cli.py --test` succeeds with Ollama as the LLM backend (instead of Claude API).

### P1.4 — Vault → GitHub auto-sync first successful run

`SinisterVaultGitHubSync` schtask installed iter-24 but first run found "vault mirror not yet present". Mirror dir bootstrapped this turn; verify next 15-min fire actually syncs.

- **OWNER:** main (verify only)
- **PASS:** `tail _shared-memory/vault-github-sync-log.jsonl` shows ≥1 row with `action=synced` + non-zero file count.

### P1.5 — Sinister Vault Sanctum mirror — full bootstrap

Per sub-D plan section 2: `_vault/sanctum-mirror/desktop-lto4lus/` exists (empty); needs initial copy of the live Sanctum repo content (excluding gitignored paths).

- **OWNER:** sub-agent `iter25-vault-bootstrap`
- **HOW:** `python automations/vault_github_sync.py --push-to-github --dry-run` first; if scan shows expected file set, drop `--dry-run`.
- **PASS:** mirror has ≥1000 files matching `git ls-files` output; SHA of `CLAUDE.md` in mirror = SHA in repo.

### P1.6 — Leo redeems invite (Sinister LINK paired)

Operator hands Leo the base64 invite (already in `deploy/SINISTER-LINK-INVITE-FOR-LEO.md`).

- **OWNER:** Leo (out-of-band)
- **PASS:** `automations/sinister-link.ps1 -Action Status` on both sides → `state=paired`; LINK poller's next fire writes `event=poll` row instead of `event=skip-unpaired`.

### P1.7 — 5 minor UI fixes from sibling sub-2 audit

`_shared-memory/audits/eve-ui-flow-audit-2026-05-25.md` flagged 5 sub-5-LOC fixes (missing `clear_screen()` entry + DRY-up `_clear_screen` duplicates).

- **OWNER:** sub-agent `iter25-ui-fix-5`
- **PASS:** each fix is a single edit; AST parse PASS; `EVE.exe --version` PASS after rebuild.

### P1.8 — 9 .bat DELETE candidates (sibling sub-1 audit)

`_shared-memory/audits/eve-bat-ps1-audit-2026-05-25.md` flagged 9 high-confidence DELETE candidates. Per-file Grep "zero-refs" pre-flight required before each `git rm`.

- **OWNER:** sub-agent `iter25-bat-cleanup` (per-file Grep + single batch commit)
- **PASS:** 9 files removed; `git grep -l "<basename>" -- ':!_shared-memory/audits'` returns nothing for each.

### P1.9 — Phase-2 jcode animations (operator 22:45Z deferred)

eve.py item 66 PARTIAL: idle-polling shimmer on blocking `getwch` deferred. Need a thread-safe non-blocking input or an event-loop rewrite of `_arrow_input`.

- **OWNER:** sub-agent `iter25-jcode-idle-shimmer` (specialized: read jcode source at `C:/Users/Zonia/Desktop/jcode-0.12.4/` for thread pattern)
- **PASS:** EVE.exe picker idle for ≥10 s → shimmer continues without blocking input; pressing a key still responds within 50 ms.

### P1.10 — Multi-agent Command Center W-key fill (sibling sub-4 plan)

`tools/eve-picker/main_menu.py:1112` has W-key placeholder. Sub-4 plan: 10-column dashboard, 8 per-row hotkeys (P/R/K/V/M/F/S/L), 6 bulk actions.

- **OWNER:** sub-agent `iter25-command-center-w-key`
- **PASS:** W in picker → dashboard renders ≤2 s + lists ≥10 heartbeat slugs + P) Poke action works on selected row.

### P1.11 — Backups off-drive (sub-D risk flag)

24h SinisterSanctumDailyBackup writes to D: drive. Same-drive failure = backup loss.

- **OWNER:** main (decision) + sub-agent `iter25-backup-offdrive` (impl)
- **OPTIONS:** (a) cheap: vault↔GitHub propagates as free 3rd copy (already in flight). (b) S3/B2 bucket weekly snapshot. (c) Tailscale to a remote backup peer.
- **PASS:** restore-roundtrip from secondary location succeeds for one chosen file (`CLAUDE.md`); SHA-equality.

---

## P2 — Next week (50-500 line implementations)

### P2.1 — Sinister OS Tauri UI with quota sliders

Per sub-E plan section 4: surface per-process CPU/mem/Claude-quota caps in a Tauri (Rust+React) UI; persist to `resource-quota-prefs.json`; bind to `resource_quota_governor.py` via local socket.

### P2.2 — Sinister Sync hive-mind (operator 03:25-27Z)

Each project becomes alive — its agents pulling shared brain on every loop iter; cross-lane federation.

### P2.3 — Operator-floor reservation in claude-accounts.ps1

PRIVILEGED_SLUGS allow-list with reserved Claude quota %; `_Is-AccountAvailable` returns false for non-privileged when reserve hits.

### P2.4 — Per-agent terminal identity (already P0 shipped per brain entry)

Verify: every spawn shows `{LANE-COLOR}---{RESET} Sinister <Lane> ...` header on first frame.

### P2.5 — 4 MEDIUM proposals from Overseer Sinister Term audit

M1 orphan cli.py / M2 DRY refactor / M3 inert IPC / M4 test gaps (`_shared-memory/knowledge/overseer-audit-sinister-term-2026-05-25.md`).

### P2.6 — Sub-1 audit MIGRATE pass (~145 .ps1 → .py on next non-trivial touch)

Not a single iter; lifetime task. Tracked in iter PR descriptions.

---

## P3 — Stretch (post-Leo-paired, after smoke-everything green)

- Ctrl+Shift+O emergency operator hotkey (single-agent-focus mode)
- Auto-tune resource quotas based on rolling 24h CPU/mem averages
- Multi-OAuth Max-20x pool across N emails (rotation under combined quota)
- Per-project-brain auto-sync via Sinister Sync
- Voice-prompt POC (`_shared-memory/plans/voice-prompting-poc-2026-05-23/`)

---

## Owner assignments (sub-agent slugs for parallel execution)

| Slug | Items | Effort |
|---|---|---|
| `iter25-eve-ui-smoke` | P0.1 | 30 min |
| `iter25-quick-launch` | P0.2 | 1 h |
| `iter25-update-notify` | P0.3 | 45 min |
| `iter25-ui-fix-5` | P1.7 | 30 min |
| `iter25-bat-cleanup` | P1.8 | 45 min |
| `iter25-vault-bootstrap` | P1.5 | 45 min |
| `iter25-quota-ram-cap` | P1.1 | 1.5 h |
| `iter25-wrapper-route` | P1.2 | 45 min |
| `iter25-jcode-idle-shimmer` | P1.9 | 1.5 h |
| `iter25-command-center-w-key` | P1.10 | 2 h |
| `iter25-backup-offdrive` | P1.11 | 1 h |
| **main** (this lane) | P0.4 + P0.5 + verifies | 1 h |

---

## Phase pass criteria (binary)

- **P0 done:** all 5 P0 items SHIPPED + acknowledged in operator-utterances.jsonl; EVE.exe smoke transcript saved; `Q` key works in <2 s; UPDATE-AVAILABLE banner renders when fed a fake sha; `launch_rate_limit_governor` blocks the broken case; utterance NEW count ≤5.
- **P1 done:** all 11 P1 items SHIPPED + each has its smoke evidence committed; Leo `state=paired`; vault↔GitHub sync producing rows; backup off-drive verified.
- **P2 done:** Tauri UI live + Sinister Sync running on ≥2 lanes + operator-floor enforced + per-agent identity verified + ≥3 of 4 Overseer MEDIUMs closed.

---

## Risk register

1. **Sub-agent overlap** — iter-25 spawns 10 parallel sub-agents on eve.py adjacencies. Mitigation: mesh-coordinator lock for any single-file editor; non-overlapping slice contracts in each prompt.
2. **Git lock contention** — known iter-22/23 issue with sibling agents. Mitigation: each sub-agent uses `git --no-pager` reads only; main does all commits.
3. **Background pull stalls** — Ollama model pulls might fail on flaky network. Mitigation: schtask retries on next fire; manual retry CLI documented in `deploy/eve-updater-CLI.md`.
4. **Operator-floor over-reservation** — if reserve % too high, fleet starves. Mitigation: dynamic threshold based on observed concurrent agent count; default 15%.

---

## End-of-iter checkpoint cadence

After each P0 item ships: 1 commit + 1 push + 1 PROGRESS row + 1 utterance ack (if mapped). After all P0 done: write a resume-point + bump iter counter + decide whether to continue to P1 same turn or hand off to next loop fire.
