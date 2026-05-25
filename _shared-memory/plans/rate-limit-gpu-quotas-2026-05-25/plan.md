# Plan :: rate-limit governance + 4090 GPU utilization + per-process quotas + operator floor

Author: RKOJ-ELENO :: 2026-05-25 (sub-E, iter-24)
Operator trigger: utterance ts=2026-05-25T07:00:45Z

> *"make sure you get the rate limiting in check and we can run all agents with no issues. add things like when i launch a agent it balances it out over the other claude account we have or use more hardware like i said to do. i have a 4090 we need to be using that. just give me enough so i can still communicate and tell you what to do. thats what i want to do with the sinister os. i want to be able to set usage that you can have to those partrs on the pc. crate a plan to complete everything you need"*

This iter (24) is PLAN-ONLY. Code edits land in iter-25 swarm.

Compose-with doctrine:
- `automate-everything-no-operator-admin-2026-05-25` (no UAC clicks, no "run elevated")
- `no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25` (new files = `.py`)
- `safe-quality-loops-doctrine-2026-05-24` (governors run continuously, never destroy)
- `sanctum-scope-discipline-2026-05-24` (high-level orchestration; no per-project quota slicing yet)

---

## Section 1 — Current state (what ALREADY works on disk today)

| Surface | Path | Status | Evidence |
|---|---|---|---|
| OAuth slot scoring (5min poll) | `automations/oauth-health-poller.ps1` (269 lines) | code-shipped, schtask NOT installed | grep PickBest score; `schtasks /Query` -> NOT-INSTALLED |
| Best-slot picker | `automations/claude-oauth-accounts.ps1` Invoke-OAuthPickBest (line 627) | code-shipped, callable | `PickBest` action exits 0/1, prints slot name on stdout |
| Legacy round-robin / load-balance | `automations/claude-accounts.ps1` Get-NextAvailableAccount (line 229) | code-shipped, in production | 3 strategies: `burn-first` / `round-robin-strict` / `load-balance`; atomic lock; tier-aware |
| Auto-429 wrapper | `automations/claude-wrapper.ps1` (374 lines) | code-shipped, NOT enforced fleet-wide | regex matches 13 rate-limit patterns; rotates + retries; AutoMark429 |
| Pre-spawn PickBest in launcher | `automations/start-sinister-session.ps1` lines 1745-1818 | wired + in production | env override -> PickBest -> Get-NextAvailableAccount -> full-power fallback |
| Account-watchdog feedback loop | `automations/account_balancer.py` (299 lines, RKOJ-ELENO 2026-05-25) | code-shipped, schtask NOT installed | `--auto-mark-limited` invokes MarkLimited on HOT slots |
| Pre-launch rate-limit gate | `automations/launch_rate_limit_governor.py` (341 lines) | code-shipped, NOT consumed by launcher | reads usage cache + 429 log; recommends `claude` vs `gpu` route |
| GPU 4090 router | `automations/gpu_bot_fleet.py` (390 lines) | code-shipped, Ollama install NOT done | detects nvidia-smi + Ollama; `--route` does `/api/generate` |
| Per-process quotas | `automations/resource_quota_governor.py` (439 lines) | code-shipped, schtask NOT installed | 4 profiles; psutil priority; Job Object attach (basic; not the RAM-cap struct) |

**Working today:** every spawn through Start-Sinister-Session.bat ALREADY auto-picks the best account via `PickBest -> Get-NextAvailableAccount -> full-power fallback`. The auto-429 wrapper exists but is not wrapping the real spawn path — children call `claude` directly inside mintty, not through `claude-wrapper.ps1`.

**Critical inferred state:** 4 of the 4 governor schtasks (Account Balancer, Resource Quota, OAuth Health Poll, Launch Rate Limit) are **NOT installed**. The code is on disk; nothing is scheduled to run it.

---

## Section 2 — Gap 1: auto-balance on spawn (SMALLEST gap; mostly already done)

### Status: 80% complete

Already-wired evidence (start-sinister-session.ps1 :: 1749-1818):
1. `SINISTER_FORCE_SLOT` env override (advanced manual)
2. `claude-oauth-accounts.ps1 -Action PickBest` invoked, stdout = slot name
3. Legacy `Get-NextAvailableAccount -Tier $tierForRouting` fallback
4. Full-power fallback (pick first enabled even if locally capped)

### Remaining edits (iter-25)

1. **Install the OAuth Health Poll schtask** (one-shot via subprocess in `eve.py` startup or `deploy/first_time_setup.py`):
   - command: `& powershell -File "automations/install-oauth-health-poller.ps1"` (existing) OR rewrite as Python `subprocess.run([schtasks, '/Create', ...])`
   - cadence: 5min (already coded in `install-oauth-health-poller.ps1`)
   - pass criterion: `schtasks /Query /TN SinisterOAuthHealthPoll` returns RC 0 + Status=Ready

2. **Install AccountBalancer schtask** (10-min cadence):
   - `python automations/account_balancer.py --install-schtask` (already implemented at line 241)
   - pass criterion: `_shared-memory/account-balancer-log.jsonl` gains a row every 10min

3. **Pre-spawn governor call** in `start-sinister-session.ps1` AFTER PickBest, BEFORE mintty.exe spawn:
   - call: `python automations/launch_rate_limit_governor.py --pre-launch <project> --account <picked> --json`
   - parse `.route` field; if `"gpu"` emit `[ROUTE-OVERRIDE] account quota hot -> deferring to local GPU bot fleet for this task` and skip the claude spawn for this iteration OR proceed with reduced spawn count (operator's choice). Default: warn, do not block.
   - file: `automations/start-sinister-session.ps1` lines 1818-1830 (immediately after `$selectedAccountName = $next.name`)

4. **Wrap `claude` in the wrapper** so 429s self-rotate:
   - edit: `launch.sh` template inside `start-sinister-session.ps1` Build-Phrase (~line 2000s) to invoke `claude` via `powershell -File claude-wrapper.ps1 -- <args>` OR convert wrapper to Python and call directly.
   - pass criterion: simulated 429 in stdout triggers `Mark-AccountRateLimited` + auto-rotate on retry (already tested by smoke in claude-wrapper.ps1 line 350)

### Binary pass:
- All 4 governor schtasks installed; verifiable via `schtasks /Query /TN Sinister*` returning RC 0 for all four.
- Spawning agent A while account "operator" is at session_pct=92% routes the new spawn to slot "leo" automatically (log row in `account-balancer-log.jsonl` shows `verdict=ROTATE`).

---

## Section 3 — Gap 2: GPU 4090 utilization

### Status: 30% complete (router code exists, Ollama not installed, bots not routed)

### Remaining edits (iter-25)

1. **Install Ollama** (operator-clicks-nothing):
   - `python automations/gpu_bot_fleet.py --install-ollama` (already at line 338, uses `winget install Ollama.Ollama --silent --accept-source-agreements`)
   - pass criterion: `gpu_bot_fleet.py --health` returns RC 0

2. **Pull base models** (sized for 4090's 24 GB VRAM):
   - `ollama pull qwen2.5-coder:7b` (code-RAG, summarization; ~4.7 GB)
   - `ollama pull llama3.1:8b` (general fallback; ~4.7 GB)
   - `ollama pull nomic-embed-text` (embeddings for librarian; ~274 MB)
   - `ollama pull bge-m3` (multilingual reranker; ~1.2 GB)
   - **Total VRAM ceiling: ~11 GB used, 13 GB free** (well under the 50% operator-reserve from `resource_quota_governor.py:67`)
   - automate via `gpu_bot_fleet.py --pull-defaults` (add this CLI flag in iter-25; one subprocess loop)

3. **Route Tier-2 bots to local GPU** (`librarian`, `triage`, `researcher`):
   - Each bot's `server.py` (in `D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\<bot>\server.py`) already hits `OLLAMA_URL=http://localhost:11434` per `bot-fleet-quick-reference.md` Tier-2 row.
   - **No code change required** beyond `ollama serve` being live + model pulled. Bots auto-detect on first call.
   - pass criterion: `mcp__librarian__search` over the 8.5k-md archive completes <2s on first call (warm-cache <500ms).

4. **Route non-routine work AWAY from Claude**:
   - File classification -> `triage.classify_file` (qwen2.5-coder:7b)
   - URL summarize -> `researcher.summarize_url` (qwen2.5-coder:7b)
   - Archive search -> `librarian.search` (nomic-embed-text + bge-m3 reranker)
   - File: update `_shared-memory/knowledge/bot-fleet-quick-reference.md` (line 17-31 TL;DR table) with GPU-routing badges.

### Binary pass:
- `nvidia-smi` shows ollama process holding 5-12 GB VRAM during a librarian.search call.
- `_shared-memory/gpu-bot-fleet-log.jsonl` shows >=1 `routed` event per minute during a typical iter.
- A trial fleet-wide Anthropic-token-spend measurement (before/after) shows >=20% reduction over a 24h window.

---

## Section 4 — Gap 3: per-process resource quotas (Sinister OS)

### Status: 35% complete (governor code exists, RAM cap is advisory only, no UI)

### Remaining edits (iter-25)

1. **Install resource_quota_governor schtask** (60s cadence):
   - `python automations/resource_quota_governor.py --install-schtask` (already at line 379)
   - default profile: `balanced` (4 cores + 6 GB RAM reserved for operator)
   - pass criterion: `_shared-memory/resource-quota-log.jsonl` gains an `apply` row every 60s

2. **Fix the JOBOBJECT_EXTENDED_LIMIT_INFORMATION struct** in `resource_quota_governor.py:246-279`:
   - Currently attaches to job object but does NOT set the actual RAM cap (comment at line 264 acknowledges this).
   - Iter-25 edit: define the full `JOBOBJECT_EXTENDED_LIMIT_INFORMATION` struct via `ctypes.Structure`; set `LimitFlags |= JOB_OBJECT_LIMIT_PROCESS_MEMORY` (0x100); call `SetInformationJobObject(h_job, JobObjectExtendedLimitInformation=9, ...)`.
   - Reference: https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_extended_limit_information
   - pass criterion: spawn a Python process that allocates 8 GB; with `default_ram_mb=4096` profile applied, process gets killed with exit code -1073741801 (STATUS_QUOTA_EXCEEDED).

3. **CPU affinity caps** (new function `apply_cpu_affinity_via_job`):
   - `JOB_OBJECT_LIMIT_AFFINITY` + `Affinity` bitmask = N lowest-bit cores
   - default: spawned agents get cores 4..N-1 (cores 0..3 reserved for operator per `RESERVE_CORES`)
   - pass criterion: a spawned claude process pinned to cores 4..11 (on a 16-core CPU) shows util concentrated there in nvidia-smi/task manager.

4. **Sinister OS UI sliders** (operator-set quotas):
   - File: NEW `projects/sinister-os/source/control-panel/resource-sliders.tsx` (Tauri/React per existing Sinister OS stack)
   - Sliders: operator-CPU-reserve (1-8 cores), operator-RAM-reserve (4-16 GB), GPU-VRAM-reserve (10-90%), max-concurrent-agents (1-12), default-profile-picker
   - Persist to: `_shared-memory/resource-quota-prefs.json` (governor reads this on each tick)
   - Governor edit: `resource_quota_governor.py` lines 64-67 -> read from `resource-quota-prefs.json` if exists, fall back to constants
   - Inheritance: dashboard-skeleton CSS per `sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24`

### Binary pass:
- Operator moves "operator CPU reserve" slider from 4 to 6; within 60s, ALL agent processes' affinity masks drop cores 4 and 5; operator's shell stays responsive under load.
- A runaway agent process at 12 GB RAM gets killed back to 4 GB within 60s (governor logs `STATUS_QUOTA_EXCEEDED`).

---

## Section 5 — Gap 4: operator-floor protection

### Status: 25% complete (CPU/RAM reserve constants exist, no Claude-quota carve-out)

### Remaining edits (iter-25)

1. **Operator-CPU + RAM floor** -- already coded as constants in `resource_quota_governor.py:64-67` (RESERVE_CORES=4 / RESERVE_RAM_MB=6144 / RESERVE_GPU_PCT=50). Wire to the UI from Section 4.

2. **Operator-Claude-quota floor** (NEW; biggest carve-out):
   - File: NEW `automations/operator_quota_reservation.py`
   - Logic: read `claude-accounts.json`; identify "operator's slot" (= `cfg.default`); refuse to spawn ANY non-operator agent on the operator slot when `successful_spawns_today > operator_floor_pct * max_sessions_concurrent`.
   - Edit point: `claude-accounts.ps1 :: _Is-AccountAvailable` (line 207) -- add check: if account_name == cfg.default AND requesting_slug != "sanctum" AND requesting_slug != cfg.default_user_slug, return $false when reservation triggered.
   - Operator UI slider in Section 4: "reserve X% of operator slot for operator's lane" (default 30%).
   - Doctrine compose: tier-aware routing already prefers operator slot for T1 spawns (claude-accounts.ps1:239). Inverse: when operator slot is hot, DEFLECT T2-T4 spawns to OTHER slots even if rotation_strategy=burn-first.

3. **Communication-channel guarantee**:
   - The master "sanctum" lane always runs at `above_normal` priority (already in `PROFILES['balanced']:privileged_priority`). Confirm `classify_slug` in `resource_quota_governor.py:167` recognizes `sanctum` slug -- it does (line 79-84 PRIVILEGED_SLUGS).
   - Add `eve` process (operator's main UI) to PRIVILEGED_SLUGS so it never drops below `above_normal`.
   - File: `automations/resource_quota_governor.py:79-84` add `"eve.exe"` to the tuple.

4. **Emergency operator-mode hotkey**:
   - When operator presses `Ctrl+Shift+O` in EVE.exe, run `python automations/resource_quota_governor.py --apply --profile single-agent-focus --focus-slug sanctum` (already a coded profile at line 105-110).
   - This drops all non-sanctum agents to `idle` priority + 1024 MB RAM; sanctum keeps `high` priority + 16 GB.
   - Recovery: same hotkey toggles back to `balanced`.

### Binary pass:
- With operator slot at 80% usage AND `reserve_operator_pct=30`, a queued T3 swarm spawn picks slot "leo" not "operator" (log row + slot name in stdout).
- Operator presses `Ctrl+Shift+O`; within 5s, every claude process drops to nice=idle except the one with `agent/sinister-sanctum/*` cmdline.

---

## Section 6 — Phasing

### P0 (iter-25 swarm; ship within 24h)
- **P0.a** Install all 4 governor schtasks (one Python script: `automations/install_all_governors.py`).
- **P0.b** Install Ollama via `gpu_bot_fleet.py --install-ollama` + pull qwen2.5-coder:7b + nomic-embed-text.
- **P0.c** Wire `launch_rate_limit_governor.py --pre-launch` call into `start-sinister-session.ps1` between PickBest and mintty spawn (5-line edit).
- **P0.d** Add `eve` to `PRIVILEGED_SLUGS` in `resource_quota_governor.py`.

Pass: `schtasks /Query /TN Sinister*` shows 4 RC=0; `ollama list` shows 2 models; `git log` shows the 4 edits in one commit; smoke spawn picks slot, logs verdict, succeeds.

### P1 (iter-26-27; ship within 72h)
- **P1.a** Fix JOBOBJECT_EXTENDED_LIMIT_INFORMATION struct for real RAM cap in `resource_quota_governor.py`.
- **P1.b** Add `apply_cpu_affinity_via_job` for hard core pinning.
- **P1.c** Write `automations/operator_quota_reservation.py` + hook into `claude-accounts.ps1::_Is-AccountAvailable`.
- **P1.d** Route Tier-2 bots (librarian/triage/researcher) by updating bot-fleet-quick-reference doctrine + verifying server.py auto-detects local Ollama.

Pass: Spawning 8 concurrent claude processes never starves operator's shell of >2s response time; runaway 12-GB agent gets killed back to 4 GB within 60s.

### P2 (iter-28+; ship within 1 week)
- **P2.a** Sinister OS UI sliders + persistence to `resource-quota-prefs.json`.
- **P2.b** Ctrl+Shift+O emergency single-agent-focus hotkey in EVE.exe.
- **P2.c** Telemetry dashboard: live token spend (Claude) vs GPU minutes (Ollama) ratio.
- **P2.d** Auto-tune thresholds: if 7-day rolling 429 count > 50, automatically drop `WEEKLY_HOT_PCT` from 85 to 75.

Pass: Operator drags slider, governor reflects within 60s; 7-day token spend drops >=30% vs pre-Ollama baseline; zero "operator can't communicate" reports.

---

## Files touched (iter-25 swarm preview)

NEW (Python, per `no-bat-no-ps1` doctrine):
- `automations/install_all_governors.py` -- one-shot installer
- `automations/operator_quota_reservation.py` -- Claude-quota floor
- `projects/sinister-os/source/control-panel/resource-sliders.tsx` -- UI

EDIT:
- `automations/start-sinister-session.ps1` (legacy; touching to wire governor call -- per doctrine, OK to edit existing .ps1)
- `automations/resource_quota_governor.py` (struct fix + affinity + privileged slug)
- `automations/gpu_bot_fleet.py` (add `--pull-defaults` CLI flag)
- `automations/claude-accounts.ps1` (_Is-AccountAvailable operator-floor check)
- `_shared-memory/knowledge/bot-fleet-quick-reference.md` (GPU-routing badges)

NEW DOCTRINE:
- `_shared-memory/knowledge/rate-limit-and-resource-governance-2026-05-25.md` (composes Sections 1-5)

---

## Out-of-scope for iter-25 (deferred)

- Multi-GPU support (operator has one 4090; no plan needed yet)
- Cross-machine federation of GPU pool with Leo's box (separate doctrine; Sinister Vault first)
- Anthropic Org account swapping (operator has personal Max plans; org plans are a different billing surface)
- Cardputer-class low-power inference fallback (off-roadmap for this plan)
