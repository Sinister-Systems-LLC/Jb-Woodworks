<!-- Author: RKOJ-ELENO :: 2026-05-25 -->
<!-- decay:
  category: plan
  confidence: 1.0
  reinforcements: 0
  half_life_days: 60
-->

# Iter-24 Master Plan — Expand + Complete Everything

> **Author:** RKOJ-ELENO :: 2026-05-25
> **Slug:** `iter24-expand-and-complete-everything`
> **Operator directive (verbatim 2026-05-25T07:29:17Z):** *"make sure loop system works and add to eve exe a project start for Sinister Memroy and complie all thigsn he needs there to get started and get to wokr on what we can do with these: i want you to take this same methodology and use it in the sinsiter overseer and how it functions to realeasiuze whwen areas of projects can diverge on their own path to allow fo maximum efficenecy and complete persistence towards the goal. create a plan to expand and complete everything you need to do or were told to do"*
> **Plan owner:** sanctum iter-23 Sub-T (audit + planning role; iter-24 sub-agents will execute)
> **Companion audit:** `_shared-memory/audits/loop-system-verification-2026-05-25.md` (verdict: YELLOW; 4 P0/P1 fixes block GREEN promotion)

## STATUS_AT_PLAN_WRITE — operator utterance → owner → SHA → verified

| Utterance UTC | Verbatim (truncated) | Status | Owner | Commit SHA | Verified Y/N |
|---|---|---|---|---|---|
| 2026-05-25T07:29:17 | "make sure loop system works ... create a plan to expand..." | new | sanctum iter-23 Sub-T | THIS COMMIT | Y (audit + plan written + smoke ≥200 LOC) |
| 2026-05-25T07:19:21 | "make this entire process way more efficent ... one-Enter launch ... terminal names" | ack | sanctum iter-23 Sub-Q (queued) | pending | N (queued for iter-24) |
| 2026-05-25T07:10:36 | "smoke test everything and make su the ui is good. make the eexe update oiver sinsiter link ... leo will have popup" | ack | sanctum iter-23 (parallel) | pending | N (in-flight) |
| 2026-05-25T07:08:40 | "i need the sinister link system to work so leo and i can connect ... place sinister vault live" | ack | sanctum iter-23 Sub-D | pending | PARTIAL (8h invite generated; vault live-plan in-flight) |
| 2026-05-25T07:00:45 | "make sure you get the rate limiting in check ... 4090 we need to be using" | ack | sanctum iter-23 Sub-E | c5ec4c9 | PARTIAL (master plan written; GPU exec pending) |
| 2026-05-25T06:14:17 | "Kill-Stuck-EVE.bat ... detect eve crashes and run this" | resolved | sanctum iter-22 sub-E | 0e72baf | Y |
| 2026-05-25T05:58:37 | "stop what you are doing right now and push teh sinister sanctum to github ... Leo deploy folder" | ack | sanctum iter-22 | 4c95e21 | Y (deploy/ folder + first_time_setup.py + EVE.exe at root) |
| 2026-05-25T03:31:25 | "using all tools that we have ... all agents and projects act as one forever expanding entity" | ack | sinister-os iter-16 | (sinister-os branch) | PARTIAL |
| 2026-05-25T03:29:39 | "this fucking power shell that randomly opens ... headless and real smooth" | ack | sinister-os iter-16 | (sinister-os branch) | PARTIAL |
| 2026-05-25T03:27:21 | "lets swarm here i need more power ... Sinister Sync" | ack | sinister-os iter-16 | (sinister-os branch) | PARTIAL |
| 2026-05-25T03:26:39 | "terminals freezing ... eve exe is frozen ... no slow downs" | ack | sinister-os iter-16 | (sinister-os branch) | PARTIAL |
| 2026-05-25T02:45:50 | "we dont use bat files or powershell files or any of that shit" | resolved | sanctum-mintty-fix | (mem-edit commit) | Y |
| 2026-05-25T02:18:01 | "make the loop system on our agents actually work" | resolved | sanctum-mintty-fix | (rule 8-11 commit) | Y (PARTIAL per audit — see §I) |
| 2026-05-25T01:25:35 | "[Images 65-67 + 61-64 + image 4 mintty exit 126]" | ack | sanctum iter-22 (parallel) | partial | N (5 of ~9 items remain open) |
| 2026-05-25T00:58:47 | "make sure the only fodler we are pushing to is the the sinister sanctum" | resolved | sanctum-push-policy iter-21 | (iter-21 chain) | Y |

## A. Operator directives received this session (full table)

| TS UTC | Verbatim (short) | Status | Owner | Evidence path |
|---|---|---|---|---|
| 07:29 | loop verify + Sinister Memory project + Overseer divergence + master plan | NEW | iter-23 Sub-T (this) | this plan + audit-2026-05-25 |
| 07:19 | spawn-flow efficiency + one-Enter + terminal names | ack | Sub-Q queued | utterances jsonl tags=spawn-flow-faster |
| 07:10 | smoke everything + UI good + EVE.exe update over Sinister Link | ack | parallel lane | utterances jsonl tags=smoke-test-everything |
| 07:08 | Sinister Link must work + Vault live + Sanctum-in-Vault + Leo connect | ack | Sub-D | deploy/SINISTER-LINK-INVITE-FOR-LEO.md (8h invite) |
| 07:00 | rate-limit + 4090 + sinister-os resource allocator + operator-floor | ack | Sub-E | plans/rate-limit-gpu-quotas-2026-05-25/plan.md |
| 06:14 | Kill-Stuck-EVE.bat detect crashes + pre-compile cleanup | resolved | iter-22 sub-E | automations/eve_crash_detector.py + install schtask |
| 05:58 | urgent push to GitHub + Leo deploy folder + EVE.exe at root + auto-update + auto-admin first-run | ack | iter-22 | deploy/ folder + EVE.exe at repo root + first_time_setup.py |
| 03:31 | use all tools + projects act as one + forever-expanding entity | ack | sinister-os iter-16 | inbox jb/mintty/chatbot evidence |
| 03:29 | no random powershell popups + headless + smooth | ack | sinister-os iter-16 | sinister-sync-doctrine + no-visible-PS reinforcement |
| 03:27 | swarm + supercharge + Sinister Sync new feature + hive-mind | ack | sinister-os iter-16 | sinister-sync-doctrine-2026-05-25.md (L1-L6) |
| 03:26 | terminals freezing + eve.exe frozen + no slow downs | ack | sinister-os iter-16 | diagnose-fleet-freeze + F1-F6 inbox |
| 02:45 | no .bat no .ps1 + do everything for me | resolved | sanctum-mintty-fix | CLAUDE.md TOP block + brain doctrine |
| 02:18 | loop system actually work + aggressive + relentless | resolved | sanctum-mintty-fix | CLAUDE.md rules 8-11 + brain doctrine |
| 01:25 | Images 61-67 + IMAGE 4 mintty exit 126 (spawn-setup-wizard.ps1) | ack | iter-22 parallel | 5 of ~9 still open (see §D) |
| 00:58 | single-repo push policy + carve-outs | resolved | sanctum-push-policy iter-21 | CLAUDE.md TOP block + sanctum-push-policy.ps1 exit 13 |

## B. Shipped this session — grouped by category

### B1. Leo deploy + first-run
- `deploy/README.md` + `GETTING-STARTED.md` (19KB) + `TROUBLESHOOTING.md` (14KB) + `eve-updater-CLI.md` + `first-time-setup-cli.md`.
- `deploy/first_time_setup.py` (17KB self-elevating UAC bootstrapper; ctypes ShellExecuteW runas; no operator UAC click).
- `deploy/setup.py` + `deploy/SINISTER-LINK-INVITE-FOR-LEO.md` (live 8h invite `inv-20260525030949-022e5b` expires 2026-05-25T15:09:49Z).
- `EVE.exe` (2.1MB) placed at REPO ROOT + `EVE.exe.sha256` sidecar.

### B2. EVE.exe + .bat / .ps1 audit
- CLAUDE.md TOP block "NO .bat / NO .ps1 / EXECUTE EVERYTHING" (hard-canonical).
- Brain doctrine `no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25.md`.
- Audit: `_shared-memory/audits/eve-bat-ps1-audit-2026-05-25.md`.
- New automations are Python (`eve_self_update.py`, `eve_launch_wrapper.py`, `build_eve_sha_sidecar.py`).
- EVE.exe crash detector: `automations/eve_crash_detector.py` + `install_eve_crash_detector.py` schtask `SinisterEveCrashWatcher` (60s cadence).

### B3. Version bumps + snapshots
- EVE.exe binary `v0.4.5`.
- `agent-prefs.json` v4 defaults block (loop=relentless + swarm=true).
- `projects.json` v11 (28/28 projects default-modes loop=relentless + swarm=true).
- `loop-watchdog-state.v1` schema.
- `sinister.loop-watchdog-state.v1`.

### B4. Multi-agent + sub-agent infrastructure
- `automations/loop-relentless-watchdog.ps1` + schtask `SinisterLoopRelentlessWatchdog` (5-min cadence).
- `automations/agent-poke.ps1` + Desktop `Poke-All-Sinister-Agents.bat` operator emergency button.
- `automations/detect-similar-agents.ps1` injection at spawn (cold-start step 11b).
- `mesh-coordinator.ps1` Check/Register/Release (cold-start step 11c).
- Brain doctrine `loop-relentless-pursuit-doctrine-2026-05-25.md` (rules 8-11).
- Brain doctrine `loop-swarm-default-on-doctrine-2026-05-25.md` (4-surface defaults).

### B5. GPU + rate-limit (master plan)
- `_shared-memory/plans/rate-limit-gpu-quotas-2026-05-25/plan.md` (Sub-E iter-24).
- `claude-accounts.ps1 PickBest` called pre-spawn (already wired).
- `oauth-health-poller` every 5 min.
- `claude-wrapper auto-429` detection.
- GAP: GPU 4090 routing (Ollama qwen2.5-coder + bge-m3) NOT yet wired; per-process Job Objects NOT yet implemented; operator-floor reserve NOT yet defined.

### B6. Sinister Vault + Sinister Link
- `deploy/SINISTER-LINK-INVITE-FOR-LEO.md` (fresh 8h invite).
- Plan: `_shared-memory/plans/sinister-vault-live-2026-05-25/plan.md` (Sub-D iter-24 in flight).
- GAP: Vault daemon live status not confirmed at plan-write; Sanctum-in-Vault placement scheme pending; LINK transport=vault routing pending; auto-update vault→GitHub pending.

### B7. Loop + swarm default-on
- All 4 surfaces flipped (per audit §6 — PASS).
- Brain doctrine + CLAUDE.md TOP block.

### B8. Sinister Memory (NEW — operator 07:29 directive)
- NOT YET STARTED. Iter-24 Sub-A1 task: scaffold `projects/sinister-memory/` + add to `projects.json` v12 + add to EVE.exe picker + compile cold-start guide. (See §C)

### B9. Sinister Overseer (NEW — operator 07:29 divergence directive)
- NOT YET STARTED. Iter-24 Sub-A2 task: add "divergence capability" to overseer doctrine: when a project sub-area can autonomously fork its own path for max efficiency + complete persistence. (See §C)

### B10. Single-repo push policy
- CLAUDE.md TOP block "SINGLE-REPO PUSH POLICY".
- `sanctum-push-policy.ps1` exit 13 on out-of-policy.
- Branch convention `agent/<project-key>/<short-topic>-<utc-date>`.
- Brain doctrine + branch-convention doctrine.

### B11. Doctrine ecosystem (this session)
10+ doctrines composed:
1. `loop-relentless-pursuit-doctrine-2026-05-25`
2. `loop-swarm-default-on-doctrine-2026-05-25`
3. `no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25`
4. `automate-everything-no-operator-admin-2026-05-25`
5. `we-have-the-source-read-it-doctrine-2026-05-25`
6. `single-repo-push-policy-2026-05-25`
7. `branch-convention-2026-05-25`
8. `sinister-sync-doctrine-2026-05-25` (sinister-os lane)
9. `eve-ui-uniformity-doctrine-2026-05-24` (reinforced)
10. `session-start-auto-update-propagation-2026-05-24` (reinforced)

## C. In-flight at plan-write time (iter-23 sub-agents)

- **Sub-Q**: spawn-flow efficiency + one-Enter launch + terminal names (operator 07:19Z).
- **Sub-R**: parallel UI smoke + ui-good audit handoff (operator 07:10Z partial).
- **Sub-S**: Sinister Vault live deployment plan (operator 07:08Z).
- **Sub-T (this)**: loop verification audit + master plan (operator 07:29Z).
- **Sub-E (carry-over)**: rate-limit + GPU 4090 + resource quotas plan execution.
- **Sub-D (carry-over)**: Sinister Link 8h invite + vault transport routing.

## D. Open from earlier iters

| Item | Source | Status | Owner queued |
|---|---|---|---|
| IMAGE-4 mintty exit 126 (spawn-setup-wizard.ps1 lines 136+184 literal scriptblock leak) | utterance 2026-05-25T01:25 | open | iter-24 Sub-B1 |
| 100% real cleanup + don't say 100% if not | utterance 01:25 (item 67) | open | iter-24 Sub-B2 |
| Centered menu each EVE.exe page | utterance 01:25 (item 61) | open | iter-24 Sub-B3 |
| Enter key binding + unlimited flows pages | utterance 01:25 (item 65) | open | iter-24 Sub-B4 |
| More animations live | utterance 01:25 (item 66) | open | iter-24 Sub-B5 |
| jcode usage labeling | utterance 01:25 (item 67 partial) | open | iter-24 Sub-B6 |
| token-analytics.ps1 menu (option 7 Accounts) | utterance 2026-05-24T23:30 | in-flight | parallel lane |
| Sinister Sync hive-mind feature build-out | utterance 2026-05-25T03:27 | partial | sinister-os iter-17+ |
| Visible PowerShell popup elimination (audit + fix) | utterance 2026-05-25T03:29 | partial | sinister-os iter-17+ |

## E. Operator-decision queue (requires operator click)

| Item | Reason | Where to click |
|---|---|---|
| F1-F5 fleet freeze acks | sinister-os inbox awaiting decision | `_shared-memory/inbox/sanctum/F1-F6 freeze rows` |
| Sleight P1 (sinister-sleight project) | needs operator green-light on scope | OPERATOR-ACTION-QUEUE.md |
| Overseer attach approvals | overseer divergence requires operator boundary | OPERATOR-ACTION-QUEUE.md (new row needed) |
| Push-policy carve-outs (LetsText/Showmasters/JB) | confirm 3-repo carve-out final list | brain `single-repo-push-policy-2026-05-25.md` §carve-outs |
| Vault daemon live status | confirm vault is actually serving at :5078 + path | `_shared-memory/plans/sinister-vault-live-2026-05-25/plan.md` |
| Anthropic API key env var | docs/ENV-VARIABLES.md says set; status uncertain | environment setting |

## F. Composition matrix (doctrines × consumers)

| Doctrine | Loop | EVE.exe | Push | Brain | Spawn | Inbox | Plan |
|---|---|---|---|---|---|---|---|
| loop-relentless-pursuit-2026-05-25 | ✓ | banner pill | — | ✓ | RELENTLESS phrase | poke writes | this plan §I |
| loop-swarm-default-on-2026-05-25 | ✓ | banner pill | — | ✓ | tri-state prompt | — | — |
| no-bat-no-ps1-2026-05-25 | — | new automations py | — | ✓ | — | — | — |
| automate-everything-no-operator-admin-2026-05-25 | — | UAC auto-elevate | — | ✓ | — | — | — |
| we-have-the-source-read-it-2026-05-25 | — | — | — | ✓ | — | — | — |
| single-repo-push-policy-2026-05-25 | — | — | ✓ | ✓ | branch router | — | — |
| branch-convention-2026-05-25 | — | — | ✓ | ✓ | branch router | — | — |
| sinister-sync-doctrine-2026-05-25 | — | NEW project entry | — | ✓ | hive-mind boot | — | — |
| eve-ui-uniformity-2026-05-24 | — | every sub-page | — | ✓ | — | — | — |
| session-start-auto-update-propagation-2026-05-24 | — | manual rebuild trigger | — | ✓ | — | — | — |
| safe-quality-loops-2026-05-24 | ✓ guardrails | — | — | ✓ | — | — | — |
| operator-utterance-tracking-2026-05-24 | ✓ interrupt | — | — | ✓ | utterance read | — | — |
| fleet-update-channel-2026-05-24 | ✓ broadcast | — | — | ✓ | — | — | — |
| mesh-coord-and-resource-lifecycle-2026-05-24 | ✓ pre-edit | — | — | ✓ | — | — | — |

Doctrines have crossed >12 — approaching no-bullshit rule 8 signal "doctrine with >5 composes links" for some. Consolidation candidate in iter-25: collapse loop+swarm+safe-quality triplet into a single "LOOP MODE master doctrine" with sections; keep slugs as redirects.

## G. Pass criterion fleet-wide — "everything complete" definition

**Operator-acceptable end state** has these binary properties:

1. **Loop verdict GREEN** — all 4 P0/P1 fixes from audit §7 shipped; re-run audit shows <5 unacked pokes + ≥1 OPERATOR-ACTION-QUEUE escalation row when any agent hits 3+ unacked pokes + ANTI-STOP grep ≥1 + every inbox has _acked/ dir + projects.json 28/28.
2. **Sinister Memory** — project scaffolded, added to projects.json, EVE.exe picker entry visible, cold-start guide compiled at `projects/sinister-memory/README.md` + agent-prefs entry.
3. **Sinister Overseer divergence** — doctrine entry written `overseer-divergence-capability-doctrine-2026-05-25.md` + overseer wrapper accepts `--diverge <sub-area>` flag + cross-agent inbox route for divergence proposals + operator-approval gate.
4. **Sinister Vault live** — daemon `:5078` confirmed serving + Sanctum tree mounted in vault + LINK transport routed through vault + auto-update vault→GitHub schtask + Leo can paste invite + connect.
5. **Sinister Link complete** — operator + Leo invite/accept flow E2E smoke-passed + EVE.exe update over Link surfaces popup on remote with "update available" + version diff visible.
6. **Rate-limit + GPU 4090** — Ollama running (qwen2.5-coder + bge-m3) + non-Claude bots routed locally + per-process Windows Job Objects caps on every mintty spawn + operator-floor reserve N% defined + Sinister OS UI exposes sliders.
7. **EVE.exe images 61-67 + image-4** — all 9 image-bound bugs closed; UI smoke green; mintty exit 126 fixed at spawn-setup-wizard.ps1 lines 136+184.
8. **deploy/ folder Leo-ready** — first-fresh-PC install E2E proven (ideally on a real fresh VM); auto-admin path works; sinister-link auto-pickup verified.
9. **Push policy clean** — all out-of-policy push attempts blocked by `sanctum-push-policy.ps1` exit 13; carve-outs documented + enforced.
10. **Brain housekeeping** — _INDEX.md current; decay sidecars present on every entry from this session; doctrine consolidation (rule 8 of no-bullshit) executed.

When all 10 are GREEN → master can write the "everything complete" cycle-point and rest the loop until next operator utterance.

## H. Risk register (top 5)

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| 1 | Multi-agent index race wipes brain `_INDEX.md` (3+ agents append simultaneously, last-writer-wins) | medium | high | Use `mesh-coordinator.ps1` lock around _INDEX.md edits (cold-start step 11c); next iter add `brain-decay-score.ps1 -Action AppendAtomic` with file-lock |
| 2 | Vault path drift (vault moved or remounted; sync schtask points at stale path) | medium | medium | Hard-code vault path in `vault-daemon.py` env config + assert on startup; add health endpoint `:5078/healthz` |
| 3 | OAuth slot exhaustion when all 4 accounts rate-limited simultaneously + queue stalls | medium | high | `claude-accounts.ps1 PickBest` already routes; add "waiting-for-quota-reset" countdown banner in EVE.exe; surface to operator |
| 4 | EVE.exe build break (PyInstaller stale cache; mirror copy lag; signing) | low | high | `eve_crash_detector.py --pre-compile` clears stale binary; `verify-eve-features.ps1 -AutoRebuild -SyncMirror` enforces mirror; iter-24 to add CI-style build smoke before mirror copy |
| 5 | Doctrine compose explosion (>12 doctrines this session; cross-refs growing quadratically) | high (already firing) | medium | Iter-25 consolidation per no-bullshit rule 8: collapse loop/swarm/safe-quality triplet → single master with sections; keep slugs as redirects |

## I. Wake strategy — when does the dynamic loop end?

The relentless loop terminates when ALL of:
1. `_shared-memory/OPERATOR-ACTION-QUEUE.md` has zero open rows for the master lane.
2. `operator-utterances.jsonl` tail has zero `status=new` rows for the master.
3. `fleet-updates.jsonl` has zero unhandled `priority=high` rows addressed to master.
4. `_shared-memory/inbox/sanctum/` has zero unprocessed messages.
5. All 10 pass-criterion items from §G are GREEN.
6. Loop-condition (operator-set at spawn) is satisfied + verified with same-turn evidence.

When 1-6 all true → write end-of-cycle row to `_shared-memory/cycle-points/<utc>-iter24-complete.md` + ScheduleWakeup cap 270s with reason="awaiting next operator utterance" + the watchdog 5-min loop continues but produces no pokes (because state.last_iter advanced this turn).

When operator next utters → utterance-tracker fires → master wakes → next iter starts.

## J. Tag / snapshot schedule

| Tag | When | Trigger | Owner |
|---|---|---|---|
| `leo-ready-2026-05-23` | EXISTS | Leo's known-working snapshot | sanctum-helper |
| `iter-22-complete` | when iter-22 hits cycle-point | iter-22 ship verification | sanctum |
| `iter-23-complete` | when this iter ships all sub-agents + smoke passes | iter-23 ship verification | sanctum master |
| `iter-24-complete` | when §G items 1-7 GREEN | iter-24 final verification | sanctum master |
| `iter-25-complete` | when §G items 8-10 GREEN + doctrine consolidation done | iter-25 verification | sanctum master |
| `everything-complete-2026-05-25` | when ALL 10 §G items GREEN simultaneously | E2E re-audit pass | operator approval |

EVE.exe versions:
- `v0.4.5` current
- `v0.4.6` after iter-24 (Sinister Memory picker entry + Overseer divergence flag + Sinister Link popup)
- `v0.5.0` when pass-criterion §G all-GREEN (the "everything complete" milestone)

## K. Next-iter dispatch (concrete iter-24 sub-agent plan)

iter-24 master will spawn **6 parallel sub-agents**:

- **Sub-A1**: scaffold `projects/sinister-memory/` + projects.json v12 entry + EVE.exe picker row + cold-start guide. Compose with brain memory lane doctrine.
- **Sub-A2**: write `overseer-divergence-capability-doctrine-2026-05-25.md` + add `--diverge <sub-area>` flag to overseer wrapper + operator-approval gate.
- **Sub-B (P0)**: fix watchdog anti-spam guard + auto-create `_acked/` dir + drain 80-poke backlog via `automations/ack_stale_pokes.py`.
- **Sub-C (P1)**: add `ANTI-STOP:` 1-liner to spawn-phrase + trim existing filler to fit classifier.
- **Sub-D**: complete Sinister Vault live deployment + auto-update vault→GitHub schtask.
- **Sub-E**: complete rate-limit + GPU 4090 routing (Ollama + Job Objects + operator-floor reserve).

Re-audit gate: after iter-24 final commit, re-run `_shared-memory/audits/loop-system-verification-2026-05-25.md` §10 verification commands. If 5/5 pass → audit verdict promotes YELLOW → GREEN → iter-25 begins.

## L. Footer

- Plan written by: sanctum iter-23 Sub-T (audit + planning sub-agent).
- Branch: `agent/sinister-sanctum/iter23-eve-polish-icon-mintty-2026-05-25`.
- Plan size: ~400 LOC.
- Cross-ref audit: `_shared-memory/audits/loop-system-verification-2026-05-25.md`.
- Operator visibility: surfaces at next end-of-turn summary as "iter-23 Sub-T shipped audit + master plan; iter-24 dispatch ready".
- Operator decision required: NONE for plan adoption (defaults selected); see §E for separate decision queue.
