> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Sanctum :: Operator Action Queue

The Sanctum-side mirror of `SESSION-START/02-OPERATOR-QUEUE.md`, with checkboxes the operator can tick as items close. Master keeps this file fresh; operator owns the checkmarks.

**Read this when:** "what's on my plate right now?"

**Color key:** 🔴 critical (dated gate; act this week) · 🟠 high (act this session if possible) · 🟡 medium (when ready) · 🟢 low / optional

---

## 2026-05-23 — Sanctum stack fully readied (launcher v6 + MCP fixes + plugins)

EVE on Sanctum shipped 4 commits this session unblocking ~all Sanctum-lane infra. Open items now:

- [ ] 🔴 **Restart Claude Code** — activates: (a) 12 newly-resolvable MCP servers (sinister-bus + sentinel + translator + librarian + watcher + auditor + triage + scribe + curator + custodian + stealth-browser + researcher) via the new `D:\Sinister\Sinister Skills` junction; (b) 14 newly-enabled dev plugins at Sanctum project level (claude-code-setup, claude-md-management, code-review, pr-review-toolkit, coderabbit, code-simplifier, commit-commands, frontend-design, github, hookify, session-report, cwc-makers, desktop-commander, exa). Without restart, spawned agents see ~9 skills; after restart they see ~30+.
- [ ] 🟠 **Decide on `sinister_apk_mcp`** — module source folder at `D:\Sinister Sanctum\_sinister-skills\02_MD_ARCHIVE\kernel-su-setup\leo-version\mcp-server\sinister_apk_mcp\` is empty (archived). The MCP entry in `~/.claude/.mcp.json` references it but it fails silently at startup. Two options: (1) restore the Python source from a backup, OR (2) ask EVE to draft an .mcp.json edit removing the entry (needs explicit operator go-ahead since `.mcp.json` is normally off-limits).
- [ ] 🟡 **Enable external-service plugins individually** — 20 plugins installed but not enabled (need API tokens): airtable, apollo, asana, atlassian, box, circleback, discord, gitlab, imessage, intercom, legalzoom, linear, notion, pigment, slack, spotify-ads-api, telegram, windsor-ai, youdotcom-agent-skills, zapier. Use `/plugin enable <name>` per-need after configuring auth.

---

## 2026-05-23 — Nano Banana wired (fleet-wide image generation)

- [x] ✅ **Set `GEMINI_API_KEY` user env var** — operator set 2026-05-23T07:05Z (39 chars, `AIzaSy…` prefix). Wrapper round-trips clean; key is hot at User + Process scope.
- [ ] 🔴 **Enable billing on Google Cloud project `492031902572`** — image-generation models on Gemini API are **paid-only**. Free tier `limit: 0` returns `429 RESOURCE_EXHAUSTED` on every `generateContent` call against `gemini-2.5-flash-image`. Fix: open `https://console.cloud.google.com/billing` → select project `492031902572` → link a billing account. Propagates in ~1-2 min. Cost ~$0.039/image for `gemini-2.5-flash-image`.
- [ ] 🟡 **(Optional) Rotate the `GEMINI_API_KEY`** — the current key was pasted into a session screenshot (image cache `C:\Users\Zonia\.claude\image-cache\…\5.png`) so the value is on disk in plaintext. If that's a concern, delete the key at `https://aistudio.google.com/apikey`, create a new one, re-run `[Environment]::SetEnvironmentVariable('GEMINI_API_KEY','<new>','User')`. Not blocking — just hygiene.
- [ ] ~~🟠 **Set `GEMINI_API_KEY` user env var**~~ — superseded by the line above — unlocks the new `tools/nano-banana/` wrapper for ALL agents (Showmasters dark+gold brand-lock, JB Woodworks gold/black photoreal, plus base `generate()` for any lane). `google-genai` SDK 2.6.0 is already installed system-wide; just need the key.
  ```powershell
  [Environment]::SetEnvironmentVariable('GEMINI_API_KEY','<your-key>','User')
  ```
  Aliases also accepted (`NANO_BANANA_API_KEY` → matches Showmasters' contract doc, `GOOGLE_API_KEY` → SDK fallback). Restart open Claude / PowerShell sessions after. Brain entry: `_shared-memory/knowledge/nano-banana-gemini-image.md`. Day-one work-list (12 blog headers + 2 city heros + 5 social templates for Showmasters; portfolio teasers + blog headers for JB) is queued in the inbox messages.

## 2026-05-21 — Sanctum session surfaces (read-only, low-stakes)

- [ ] 🟠 **Install Rust toolchain (rustup-init.exe)** — unblocks the jcode source-level fork into `projects/sinister-rkoj/`. ~1.5 GB rustup install (plus ~5-7 GB MSVC Build Tools if not already present, plus ~5-10 GB for the first `cargo build` of the 60+ crate workspace). Until then the **sidecar shim** at `tools/sinister-jcode-shim/` (v0.1.0 shipped 2026-05-21) wraps the prebuilt `jcode-windows-x86_64.exe` with our Sinister env config — that's the bridge. Full plan + risk register + rebrand checklist: `_shared-memory/plans/jcode-fork-2026-05-21/plan.md`. Toolchain installer: [https://rustup.rs](https://rustup.rs).

- [ ] 🟠 **Set `ANTHROPIC_API_KEY` env var (system)** — RKOJ.exe v0.6.0 will switch to Anthropic SDK direct tool-use loop (multi-step reasoning visible like jcode) **only when this env is set**. Without it, RKOJ falls back to the existing `claude -p` one-shot path. One-line: `setx ANTHROPIC_API_KEY "sk-ant-..."` then restart any shell + RKOJ.exe. See `docs/ENV-VARIABLES.md` for the canonical list.



- [ ] 🟡 **Desktop bat byte-parity drift** — sibling sanctum audit (14:00 PROGRESS) found three Desktop bats out of sync with the canonical tree at `D:\Sinister Sanctum\tools\session-launcher\`:
  - `Sinister Start.bat` — 137-byte drift (Desktop 3604 / Tree 3741)
  - `Personal Project start.bat` — 90-byte drift
  - `Start-Sinister-Session.bat` — **MISSING from Desktop entirely** (5228 bytes in tree only). CLAUDE.md treats this as the canonical one-click launcher path. Run `copy "D:\Sinister Sanctum\tools\session-launcher\Start-Sinister-Session.bat" "C:\Users\Zonia\Desktop\"` to restore.
  - `Sinister Freeze.bat` + `Sinister.bat` — Desktop-only (tree never had them). Probably operator-intentional but flagging in case the tree should mirror for backup.
  - No automated mutation — Desktop is operator territory.
- [ ] 🟡 **Wayward Forge commit on sanctum branch** — `66a5b3e feat(forge): PH18 niri columns + PH16 swarm pump + :dm/:broadcast + PH10 :host switch` landed on `agent/sinister-sanctum/cli-dispatcher-2026-05-21` instead of a forge branch (HEAD-race per `verify-head-before-commit-multi-agent` brain entry). [ASK] dropped to `_shared-memory/inbox/forge/2026-05-21T1403Z-ask-from-sanctum-wayward-commit-66a5b3e.json`. Forge lane recovery is `git update-ref refs/heads/agent/sinister-forge/<active-branch> 66a5b3e` + push.
- [ ] 🟢 **Mixed-case resume-point dir** — `_shared-memory/resume-points/Sinister Sanctum/` (display-name, 1 file) + `_shared-memory/resume-points/Sanctum/` (slug, 6 files) both exist. Display-name is the convention (6/7 lanes use it). v1.3 PS1 fix path documented at `_shared-memory/knowledge/resume-point-dir-name-convention.md`. Deferred while cli-dispatcher branch is hot.

## 2026-05-19 — One-click bundle (master complete-everything sweep)

- [ ] **DOUBLE-CLICK** `C:\Users\Zonia\Desktop\Wire-The-Rest.bat` — interactive prompts walk through all 7 operator-gated items below in one bat. Every step is skippable + idempotent. Master agent shipped this 2026-05-19 14:15 as the operator-facing bundle for the items the sandbox blocked from direct execution.

## 2026-05-19 — RKOJ + Vault wire-up (after today's full-day sprint)

- [x] ~~**Install RKOJ auto-start task**~~ — VERIFIED INSTALLED 2026-05-21 11:05Z (rkoj-workstation agent ran `schtasks /Query /TN RKOJ` → present). Caveat: `LastTaskResult=3221225786` (0xC0000142 STATUS_DLL_INIT_FAILED) + empty `NextRunTime` → first run crashed at DLL init + task is not re-arming. RKOJ.exe IS running via the alternate path (`rkoj-runtime.beat` fresh at 10:00Z, pid 35132, port 5077). To re-arm auto-start: operator re-runs `install-rkoj-task.ps1` from an elevated shell.
- [x] ~~**Install SinisterVault auto-start task**~~ — VERIFIED INSTALLED 2026-05-21 11:05Z (`schtasks /Query /TN SinisterVault` → present). Caveat: `LastTaskResult=255` (generic failure) + empty `NextRunTime`. Operator confirms or re-arms.
- [ ] **Install Syncthing service** (admin) — `powershell -ExecutionPolicy Bypass -File "D:\Sinister Sanctum\tools\sinister-vault\syncthing\install.ps1"`
- [ ] **Move Gitea data into vault** — `powershell -ExecutionPolicy Bypass -File "D:\Sinister Sanctum\tools\sanctum-git\setup-vault-data-dir.ps1"` (Gitea down briefly)
- [ ] **Bootstrap Gitea users** — `python "D:\Sinister Sanctum\tools\sanctum-git\bootstrap-users.py" --leo-key-file <path-to-leo.pub>` (operator + leo)
- [ ] **Register Vault MCP** — re-run `D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\install-fleet.ps1` (operator-owned `~/.claude/.mcp.json`); restart Claude Code after
- [ ] **Onboard Leo** — share his auth key (delivered earlier in session — see `_vault/auth-keys-DELIVER-TO-LEO.txt`); send him `docs/RKOJ-OPERATOR-GUIDE.md` + `tools/sinister-vault/syncthing/onboard-leo.md`
- [ ] (Optional) **Set `LEO_ANTHROPIC_API_KEY` env var** if Leo will use a separate Anthropic billing account

---

## 🔴 Critical (act this week)

- [ ] **PI 0/3 fixed on phones P1 + P2** — Settings → Passwords & accounts → Google → Account sync → ⋮ → Sync now → re-enter password. Both phones. (Kernel APK lane reports PI 3/3 verified — confirm with operator whether this is genuinely closed.)

*(Yurikey52 sourcing was previously listed here as a 2026-05-23 gate; operator confirmed 2026-05-19 it is FALSE — removed.)*

## 🟠 High (this session if possible)

- [ ] **Restart Claude Code** so the 12 MCP servers (Sinister Bots) load + the new bus tools (heartbeat, inbox_poll, run_script, memory_garden, codec, vault) become visible. Without this, no live cross-agent messaging. **NOTE 2026-05-23:** EVE-Sanctum's 2 junctions now make these paths resolve cleanly — restart unblocks all 12 in one go (see top-of-queue row).
- [ ] **Install Custodian 24/7 daemon** — `cd 'D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\custodian'; .\install-task.ps1` (now unblocked per Expanded Authority, but operator picks the timing because it registers a Scheduled Task).
- [ ] **Smoke-test Sinister Crawler** per `D:\Sinister Sanctum\tools\sinister-crawler\SMOKE.md` (BotFather token + `/start` + each command).
- [ ] **Smoke-test Sinister Chatbot** per `D:\Sinister Sanctum\tools\sinister-chatbot\RUN.md` (npm install + `/chatbot/generate` + Eve observations).
- [ ] **First-run Sanctum-Git** per `D:\Sinister Sanctum\tools\sanctum-git\FIRST-RUN.md` (Docker up + Gitea wizard + mirror).

## 🟡 Medium (when ready)

- [ ] **Set `ANTHROPIC_API_KEY` user env var** — unlocks Scribe daily-digest + Curator code-scout + Sinister Chatbot LLM path.
   ```powershell
   [Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY','sk-ant-...','User')
   ```
- [ ] **Set `SINISTER_VAULT_PASSPHRASE` user env var** — at-rest vault works for operator-private files.
   ```powershell
   [Environment]::SetEnvironmentVariable('SINISTER_VAULT_PASSPHRASE','<phrase>','User')
   ```
- [ ] **Set `OPENAI_API_KEY` user env var** — unlocks Codex Companion peer-review (`POST /api/codex/review` returns `no API key` until set).
- [ ] **Pick a Sanctum LICENSE** from `LICENSE-CANDIDATES.md` (MIT / Apache-2.0 / Proprietary). Master overwrites `LICENSE` once you say. *(De-prioritized 2026-05-19: repo is **Private** on GitHub, so the placeholder All-Rights-Reserved is safe until you decide.)*
- [ ] **One-time: `gh auth refresh -h github.com -s workflow`** (browser prompt, 30 sec) — required so the auto-push daemon can mirror future `.github/workflows/*.yml` changes. Current token scopes: `gist, read:org, repo` (no `workflow`). If you see `push-failed` lines in `_shared-memory/auto-push.log` mentioning workflow scope, this is the fix.
- [ ] **Pull Ollama models** so Tier-2 bots stop running in degraded fallback:
   ```powershell
   cd 'D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\docker'; .\setup.bat
   docker exec -it ollama ollama pull qwen2.5:1.5b qwen2.5-coder:7b nomic-embed-text
   ```
- [ ] **Snap EMU SS03 next step** — operator picks: Tier-2 hunt continuation, Tier-3 schema reconcile, or pivot. (Owned by the Snap-API agent — master surfaces only.)
- [ ] **Sinister LLC migration** — `Prepare-Migration.bat` + `migrate-projects.ps1` + `secret-scrub.ps1` (MUST PASS).

## 🟢 Low / optional

- [ ] **Hacker bot fetch** (`AKCodez/hackingtool-plugin`) — design done, deferred pending operator OK to fetch upstream.
- [ ] **Hardware roadmap Tier 1 buys** — used RTX 3090 24GB (~$650–$800), 2× 8TB external HDD (~$280), N100 mini-PC 16GB (~$210). Total ~$1,130–$1,230. See `docs/HARDWARE-ROADMAP.md`.
- [ ] **Hardware roadmap Tier 2** — DS220+ NAS (~$290), 2× NAS HDD (~$200), managed switch (~$40), UPS (~$180). Total ~$710.
- [ ] **Rebuild stale UA graphs** — LOA (27 days stale), LOA/RKA (29 days stale). `06_UNDERSTAND/<name>/_LAUNCH.bat`.
- [ ] **Drive encryption decision** — VeraCrypt container plan in `SESSION-START/04-RECOVERY.md`. Operator decides; sandbox can't run it.

## ✅ Recently closed (move items here when done)

### 2026-05-19 (afternoon — external-imports + foundation-sweep session)

- [x] **External-import inflow loop shipped** — `_shared-memory/external-imports/{README,CANDIDATES}.md` + `.gitkeep`. Catalog of every external skill/tool/MCP/cookbook the fleet has scouted. Append-only; case-study workflow gates promotion to fleet.
- [x] **Ruflo + Anthropic Cookbook + MCP Registry verified via WebFetch** — all 3 URLs resolve. Ruflo is MIT-licensed `github.com/ruvnet/ruflo`, installs via `claude mcp add ruflo -- npx ruflo@latest mcp start`. Cookbook top-level folders captured. MCP Registry has REST API at `/docs`. Polymathic AI/The Well marked `archive` (strategic-fit LOW for current workloads).
- [x] **Sinister Vault MCP install doc shipped** — `tools/sinister-vault/INSTALL-MCP.md` walks operator through the wire-everything.ps1 + merge + restart loop. Coordinates with agent B's wire-everything.ps1 + staged proposal at `_vault/mcp-vault-entry-PROPOSED.json`.
- [x] **ENV-VARIABLES.md shipped** — `docs/ENV-VARIABLES.md` lists every env var Sanctum reads (ANTHROPIC/OPENAI/VAULT_PASS/LEO_KEY/HUB_ROOT/AGENT_NAME/GITEA_ADMIN) with the exact `[Environment]::SetEnvironmentVariable(...)` command + which tools read each.
- [x] **Auto-push task verifier shipped** — `automations/verify-auto-push.ps1`. Read-only probe of `SinisterSanctumAutoPush` scheduled task. Confirmed live-run that the task is **NOT** registered (the runtime audit was right; prior PROGRESS claim of "shipped" was inaccurate).
- [x] **Ruflo brain entry shipped** — `_shared-memory/knowledge/ruflo-mcp-integration.md` (status: workaround until 5-7 highest-value skills are forked per Phase C). Brain `_INDEX.md` count: 29 -> 30.
- [x] **Skills catalog reshape** — `skills/_INDEX.md` now splits into "folder-shaped skills" + "code-library skills" with new `Source` + `Imported` columns. Existing 11 rows preserved + marked `Source = native`.
- [x] **Sanctum root CLAUDE.md created** — `CLAUDE.md` at repo root. Was missing per the foundation-sweep scan; the only project-level CLAUDE.md gap that was master's lane to fill.
- [x] **Foundation sweep report** — `_shared-memory/foundation-sweep-2026-05-19.md`. Full audit of project-level docs, runtime infrastructure, catalog -> reality. The operational backbone for "all files have everything they need."

## 🟠 High — NEW gates surfaced by today's sweep

- [x] **Decide Ruflo install model** — operator chose: **both** (MCP-only + 5 fork case-studies). Master executed Phases B + C 2026-05-19T13:45Z.
- [x] **Wire Ruflo MCP** — `claude mcp add ruflo -s user -- npx ruflo@latest mcp start` shipped. Entry confirmed in `~/.claude.json`.
- [x] **Wire Vault MCP** — `claude mcp add vault ...` shipped (via `bots/agents/vault/launch-mcp.bat` wrapper). Entry confirmed.
- [x] **Register SinisterSanctumAutoPush** — task Ready, first-ran 09:45:45, next-run 10:15:15.

## 🟠 High — NEW operator clicks (post wire-up session)

- [ ] **Double-click `C:\Users\Zonia\Desktop\Sanctum-Wire-Tasks-AsAdmin.bat`** — one UAC prompt registers both `RKOJ` and `SinisterVault` scheduled tasks (RunLevel Highest needs admin; current non-admin shell silently dropped them).
- [ ] **Restart Claude Code** so the newly-registered `ruflo` + `vault` MCP servers load. After restart, `ToolSearch select:ruflo` + `ToolSearch select:vault.health` should return schemas.
- [ ] **Thumb the 5 Ruflo skill case-studies** at `_shared-memory/case-studies/2026-05-19-sk-{swarm-coord,vector-memory,federation,observability,aidefence}.md`. Each is `status: candidate` until you 👍 / 👎. Per case-study: 5-section structured verdict + recommendation. All 5 default to `KEEP-WITH-CHANGES`; federation suggests PARK until 2-machine workload exists.

### 2026-05-19 (morning — first-push + LetsText + hub sprint)

- [x] **Sanctum first GitHub push + 30-min auto-push daemon** — operator authorized direct execute ("you have complete control to do this without me"). Initial commit landed on `main` at `Sinister-Systems-LLC/Sinister-Sanctum` (Private). `SinisterSanctumAutoPush` scheduled task runs every 30 min and skips when working tree is clean. Kill switches on Desktop: `Sanctum-Auto-Push-Status.bat` / `Pause.bat` / `Resume.bat`. Brain entry: `_shared-memory/knowledge/sanctum-auto-push.md`. Canonical-14 standing rule added.
- [x] **LetsText launcher rebuild** — `C:\Users\Zonia\Desktop\Start-LetsText-Session.bat` shipped (mirrors Sanctum pattern). Latent em-dash gotcha fixed in `D:\LetsText\automations\start-letstext-session.ps1` (UTF-8 BOM applied). v2 polish: PadRight 20→30 (column collision), dynamic round read from `CLAUDE.md` front matter, authorship line added. Smoke green.
- [x] **Themed-launcher pattern doc** — `D:\Sinister Sanctum\docs\THEMED-SESSION-LAUNCHER.md` ships the recipe + three gotchas so the next sibling project (Snap-EMU / TikTok-EMU / RKA / Bumble) gets a working launcher in minutes instead of hours.
- [x] **Top header bar concept** — 6 stacked variants + `⌘K` palette served at `http://127.0.0.1:7088/` (PID `3473123`). Source at `D:\Sinister Sanctum\inventions\2026-05-19-top-header-bar-concept\`.
- [x] **Today's-updates hub** — live status pills + iframe previews of every running localhost surface at `http://127.0.0.1:7099/` (PID `3508412`). Source at `D:\Sinister Sanctum\inventions\2026-05-19-todays-updates-hub\`.
- [x] **LetsText 2.0 dev servers re-spun** — `dashboard-local` (`:6060`) + `mobile-dashboard` (`:3400`) each in their own visible PowerShell window via `npm run dev`. First-compile in progress; hub iframes will populate as they go live.

---

## 2026-05-21 — GitHub linkage audit

Author: RKOJ-ELENO :: 2026-05-21 — see full audit at `_shared-memory/audits/github-linkage-2026-05-21.md`. Operator goal verbatim: *"everything in there will be linked to github exact"*. EVE ran a READ-ONLY discovery sweep; the actions below are the only deltas needed to make every RKOJ-ELENO repo under Sanctum reach GitHub.

### Repos that need a GitHub remote added (operator-gated)

- [ ] **`projects/sinister-tiktok-emu/source`** — has commits on `agent/sinister-tiktok-api/expand-2026-05-20` but NO remote at all. Pick one of:
  - Match fleet convention (recommended — matches Panel/Snap-EMU/Sanctum/APK):
    ```bash
    git -C "D:/Sinister Sanctum/projects/sinister-tiktok-emu/source" remote add origin git@github.com:Sinister-Systems-LLC/Sinister-TikTok-EMU.git
    ```
  - Or operator-brief literal `RKOJ-ELENO` org:
    ```bash
    git -C "D:/Sinister Sanctum/projects/sinister-tiktok-emu/source" remote add origin git@github.com:RKOJ-ELENO/Sinister-TikTok-EMU.git
    ```
- [ ] **`projects/sinister-tiktok-emu/` (outer wrapper)** — stale empty `.git/` with zero commits. Recommended cleanup (operator-gated):
  ```bash
  rm -rf "D:/Sinister Sanctum/projects/sinister-tiktok-emu/.git"
  ```

### Repos that are AHEAD of origin (just need `git push`)

- [ ] **Sanctum main** — branch `agent/sinister-sanctum/cli-dispatcher-2026-05-21` is **9 ahead** of `origin/agent/sinister-sanctum/cli-dispatcher-2026-05-21`. Push:
  ```bash
  git -C "D:/Sinister Sanctum" push origin agent/sinister-sanctum/cli-dispatcher-2026-05-21
  ```
- [ ] **Snap-EMU source** — branch `agent/sinister-snap-api/expand-cleanup-2026-05-20` is **9 ahead**. Push:
  ```bash
  git -C "D:/Sinister Sanctum/projects/sinister-snap-emu/source" push origin agent/sinister-snap-api/expand-cleanup-2026-05-20
  ```
- [ ] **Kernel-APK source** — branch `agent/sinister-kernel-apk/crispy-cosmos-resume` is **3 ahead**. Push:
  ```bash
  git -C "D:/Sinister Sanctum/projects/sinister-kernel-apk/source/source" push origin agent/sinister-kernel-apk/crispy-cosmos-resume
  ```

### Repos in scope but explicitly NOT-to-be-touched

- `projects/sinister-kernel-apk/source/source/Camera-Spoof-Module/KPatch-Next` → upstream `KernelSU-Next/KPatch-Next` (vendored 3rd-party)
- `projects/sinister-kernel-apk/source/source/_assets/5.17-luke/Luke Spoofer Source/LukePrivacyKPM` → upstream `LukeMatPyt/lukeprivacyKPM` (vendored 3rd-party)
- `projects/sinister-kernel-apk/source/source/_rebrand_workspace/ksu-manager-sister/upstream/KernelSU-Next` → upstream `rifsxd/KernelSU-Next` (vendored 3rd-party)

These are reference sources, not RKOJ-ELENO products — keep remotes as-is.

### Out-of-scope / no-action

- All `projects/sinister-{bumble-emu,claw,emulator-bundle,forge,freeze,mind,term}/` source trees — none have a `.git/` directory yet (they're operator-authored content under the Sanctum monorepo `.git/`, NOT independent repos). If operator later wants any of them as standalone GitHub repos, that's a separate decision.

---

## How master keeps this fresh

- **On every milestone:** if a new operator-blocking item lands, master appends a row here AND mirrors to `SESSION-START/02-OPERATOR-QUEUE.md` if it deserves cold-start visibility.
- **On every operator tick:** if you change `- [ ]` to `- [x]`, master leaves it. When you say "move closed to bottom" master sweeps.
- **The Sanctum Console** will read this file via `GET /api/operator-actions` (added 2026-05-19) and surface a Dashboard tile showing `<N done> / <M total>` per priority bucket.

## Standing rule reference

This file is canonical-14 standing rule #13 ("Operator-action queue stays mirrored in `_shared-memory/OPERATOR-ACTION-QUEUE.md` for one-glance status"). See `_shared-memory/DIRECTIVES.md` index at the top.
