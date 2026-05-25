<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Sinister OS Mobile — Doctrine (Pixel 6a target)

> **Status:** project lane bootstrapped 2026-05-24; P0 spec lock open pending operator Q1-Q10.
> **Origin:** operator hard-canonical 2026-05-24T15:56:34Z verbatim: *"create a new sessions start in the project for the Sinister OS Mobile for our google pixel 6a. and a full project for it in the sanctum memory all of that with a detailed plan to move forward and use our quantum tools and all tools. once ready start the agent from bat file for me"*

## What this lane is

Custom Android distribution for Google Pixel 6a (`bluejay` / Tensor G1) where:
1. EVE runs as a privileged Android system service with root-equivalent control (no UAC-style prompts for routine actions).
2. Sinister fleet (Panel, Vault, Mind, RKOJ-mobile, Chatbot) is preinstalled + integrated.
3. Voice surface (whisper-cpp on-device) is always-on; transcription pipes to EVE.
4. Sinister Vault syncs operator data (Syncthing on-device client).
5. Phone-as-phone preserved — calls, signal, optional GApps.
6. UI inherits from `projects/sinister-dashboard-skeleton/` via Jetpack Compose theme bridge (per `sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24`).

Sister to `projects/sinister-os/` (Linux PC replacement). Same EVE-control DNA, different metal.

## 5-phase plan (operator-gated boundaries)

| Phase | Output | Gate-out |
|---|---|---|
| **P0** | Spec lock — operator answers Q1-Q10 | Operator click → P1 |
| **P1** | Base-ROM pick (GrapheneOS / LineageOS / CalyxOS / DivestOS / AOSP) via seraphim ZZ-FM r=1 K=4 audit | Operator click → P2 |
| **P2** | Build env provisioned (Linux x86_64, 250 GB, `repo sync` complete) | Operator click → P3 |
| **P3** | Vanilla cuttlefish boot + adb shell + wifi up | Operator click → P4 |
| **P4** | EVE service + Sinister Panel + Vault + voice surface on cuttlefish; 7 consecutive green smoke runs | Operator click → P5 |
| **P5** | Flash to physical Pixel 6a (operator hands-on; types `sinister-os-mobile flash-pixel`) | Operator-final |

Full plan: `projects/sinister-os-mobile/plans/master-plan-2026-05-24.md`.

## Tool stack expected (operator directive: "use our quantum tools and all tools")

- **understand-anything** plugin — every spawn invokes on `projects/sinister-os-mobile/` BEFORE work
- **github-prior-art.ps1** (cold-start step 9) — base ROMs + every subsystem before writing from scratch
- **operator-idea-intake.ps1** (new 2026-05-24) — operator drops candidate repos; lane marks adopted/rejected
- **seraphim audit** (`quantum-memory-kernel-fleet-action-items-2026-05-23`) — ZZ-FM r=1 K=4 triad similarity on candidate ROM corpora; expect 25-35pp quantum advantage over TF-IDF
- **bot fleet** (`bot-fleet-quick-reference.md`): `triage.classify_file` (vendor blob detection), `librarian.search` (ROM manifest), `auditor.scan_secrets` (pre-commit), `custodian.snapshot_now` (pre-destructive)
- **canonical-protections-check** (P11 ensures UI-base hard-canonical is honored)
- **forever-improve.ps1** (cold-start step 10) — review every meaningful unit
- **fleet-update channel** — JSONL seeded at `_shared-memory/fleet-updates.jsonl` for hot-pickup of doctrine/feature changes

## EVE-control design (mobile-specific)

- `com.sinister.eve` system_app at `/system/priv-app/SinisterEVE/`, signature|privileged permissions
- AIDL service + unix socket `/dev/socket/sinister-eve`
- Voice surface (whisper-cpp child process) — hotword on always-on core, AP wakes on detect
- Routine actions auto-yes; destructive (factory reset / partition format) require fingerprint or Panel PIN
- Mesh: Tailscale on-device → Pixel becomes fleet node; EVE can off-route heavy work to Hetzner if battery low

## What this lane NEVER touches

- Operator's physical Pixel 6a (until P5 operator hands-on)
- Vendor blobs in git (Google firmware terms forbid redistribution)
- `~/.claude/.mcp.json` (operator-owned)
- Other project source trees
- `main` branch (routes through `sanctum-auto-push` daemon)

## Composes with

- `sinister-os-doctrine-2026-05-24` — PC sister project (shared EVE control patterns / voice surface / Sinister Panel theme tokens)
- `sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24` — UI base + EXPAND principle (Android Compose theme bridge maps skeleton tokens)
- `quantum-memory-kernel-fleet-action-items-2026-05-23` — seraphim ZZ-FM r=1 K=4 recipe for ROM selection
- `github-first-sourcing-doctrine-2026-05-24` — vendor before write
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` — verbs at gate (`scaffolded` → `parse-clean` → `smoke-tested` → `acceptance-tested` → `shipped`)
- `agent-identity-eve` — persona
- `agent-autonomy-push-and-completion-2026-05-23` — push `agent/sinister-os-mobile/*` freely
- `do-not-revert-operator-canonical-protections-2026-05-23` — P11 protects this
- `operator-utterance-tracking-doctrine-2026-05-24` — originating utterance ts_utc 2026-05-24T15:56:34Z

## First-turn checklist (every fresh sinister-os-mobile EVE)

1. `understand-anything:understand-explain` on `projects/sinister-os-mobile/`
2. Read CLAUDE.md + SESSION-START.md
3. Read `plans/master-plan-2026-05-24.md` cover-to-cover
4. Heartbeat + inbox poll
5. Confirm current phase = P0 (until Q1-Q10 answered)
6. Pick one P0 queue row; mark in_progress; work; verified-only claims; commit on `agent/sinister-os-mobile/<topic>`; push

## Bat launch

Operator's one-click: `C:\Users\Zonia\Desktop\Start-Sinister-Session.bat` → picker → `sinister-os-mobile`. Or via PowerShell: `automations/start-sinister-session.ps1 -ProjectKey sinister-os-mobile`. Visible in `projects.json` picker.visible_keys[] after the projects.json entry insertion 2026-05-24T16:00Z by test-modes-verify lane.
