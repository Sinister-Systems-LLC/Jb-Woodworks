# Sinister OS Mobile — Master Plan (P0 spec lock)

> Author: RKOJ-ELENO :: 2026-05-24
> Status: **P0 spec lock — DRAFT for operator review**
> Sister doc: `projects/sinister-os/plans/master-plan-2026-05-24.md` (Linux PC plan)
> Operator verbatim 2026-05-24: *"create a new sessions start in the project for the Sinister OS Mobile for our google pixel 6a. and a full project for it in the sanctum memory all of that with a detailed plan to move forward and use our quantum tools and all tools."*

## § 1 Goal

Custom Android distribution for Google Pixel 6a (`bluejay` / Tensor G1) where:

1. EVE runs as a privileged system service with root-equivalent control.
2. Sinister fleet (Panel, Vault, Mind, RKOJ-mobile, Chatbot) is preinstalled + integrated.
3. Voice surface (whisper-cpp on-device) is always-on; transcription pipes to EVE.
4. Operator's phone-as-phone experience is preserved (calls / signal / optional GApps).
5. The whole thing inherits the Sinister UI canon (dashboard-skeleton theme) via Jetpack Compose theme bridge.

## § 2 Non-goals (out of scope for v1)

- Carrier provisioning (operator handles SIM-on-device manually).
- Cellular modem firmware modifications (Google blobs as-is).
- Proprietary anti-detect features (these belong in the emu lanes, not the daily-driver phone).
- Custom hardware (no boards, no SBC variants — Pixel 6a only for P0-P5).

## § 3 Hardware (Pixel 6a / `bluejay`)

Already enumerated in `README.md` § "Why Pixel 6a". TL;DR: Tensor G1, 6 GB RAM, 128 GB UFS, AVB 2.0 unlockable, Treble GSI compatible, kernel 5.10 LTS, current LineageOS official support, current GrapheneOS official support, security updates through ~Q3 2027.

## § 4 Base-ROM candidates (P1 picks one)

| Candidate | Why consider | Why hesitate |
|---|---|---|
| **GrapheneOS** | Hardened security baseline; AVB with custom key; sandboxed GApps; active Pixel 6a support; ~95k LOC patches | Hardening conflicts with EVE root-control unless we relax sepolicy; sandboxed GApps reduces user-visible surface |
| **LineageOS 21** | Largest community; familiar to operator's earlier lanes; broad app compat; clean root via Magisk/KernelSU | Less security baseline; magisk + AVB don't compose cleanly; root-via-Magisk means EVE-as-system-service is harder than just shipping the service in `/system/priv-app/` |
| **CalyxOS** | MicroG out of box; reasonable security baseline; smaller patch surface than Graphene | Smaller community; Pixel 6a official but less active |
| **DivestOS** | Hardened LineageOS fork; per-device security backports | Smaller community; less frequent updates than Lineage proper |
| **AOSP from scratch** | Full control; no upstream conflicts | ~4-6 weeks build-engineer work; no community support; high maintenance burden |

**P1 decision tool**: run `seraphim audit --variant zzfm-r1 --triad <readme1> <readme2> <readme3> --corpus pool` against each pair of candidate ROMs' README + manifest corpus. Per `quantum-memory-kernel-fleet-action-items-2026-05-23`: quantum-kernel highlights structural overlap classical TF-IDF misses; expect K=4 ZZ-FM r=1 to surface "GrapheneOS vs LineageOS" patch-philosophy divergence at a quantum advantage ~25-35pp.

Default lean (subject to operator override): **GrapheneOS** with relaxed sepolicy for EVE — combines best-in-class security with the longest Pixel-6a support runway. Trade-off: sandboxed GApps means MicroG or no Google services; operator picks.

## § 5 Build environment (P2)

- **Host:** Linux x86_64 (Ubuntu 22.04 LTS or Arch Linux). 250 GB free disk, 32 GB RAM recommended, fast NVMe.
- **Tools:** `repo`, `git`, `lfs`, `python3`, `openjdk-11`, `bc`, `ccache`, `aapt`, fastboot, adb.
- **Source pull:** ~120 GB after `repo sync -c -j8 --no-tags --no-clone-bundle`.
- **Build output:** ~25 GB per device target after `lunch <target>_userdebug && m otatools systemimage`.
- **CI:** start with local builds; phase-3+ consider Hetzner builder VM (`projects/sinister-os/build/`-style) once cuttlefish loop is green.
- **GitHub-first sourcing:** before writing any glue, run `automations/github-prior-art.ps1 -Topic "<sub-feature>"` — surface candidates via `operator-idea-intake.ps1 -Action Add -Url <repo>` for fleet-wide review.

## § 6 Cuttlefish-first development (P3)

- Daily build target: `aosp_cf_x86_64_phone-userdebug` (cuttlefish virtual device).
- `cvd start` brings up a graphical Android shell on the build host; adb forwards over `tcp:6520`.
- All EVE integration work (P4) runs against cuttlefish first. **Never flash physical Pixel 6a until P5 operator hands-on gate.**
- Smoke matrix per build: boot success → adb shell → wifi up → Sinister Panel APK installs → Panel hits Sanctum vault → EVE service announces.
- Cuttlefish constraints: no real radios; emulate calls/SMS via test harness; sensors are mock.

## § 7 EVE integration (P4)

### § 7.1 EVE service

- Package: `com.sinister.eve`
- Path: `/system/priv-app/SinisterEVE/SinisterEVE.apk` (preinstalled in `out/target/product/<dev>/system/priv-app/`)
- Permissions: `signature|privileged` for INSTALL_PACKAGES, MANAGE_USERS, REBOOT, WRITE_SECURE_SETTINGS, FOREGROUND_SERVICE, RECORD_AUDIO, ACCESS_FINE_LOCATION (operator opt-in).
- IPC: AIDL service exposed at `com.sinister.eve.IEveService`; companion unix socket `/dev/socket/sinister-eve` for native callers.
- Lifecycle: `BOOT_COMPLETED` receiver starts the service; sticky foreground notification (icon = Sinister purple).
- Voice surface (whisper-cpp) runs as a child process under the EVE service UID, hotword detection on-device.

### § 7.2 Sinister Panel mobile

- Jetpack Compose + Material 3 + dashboard-skeleton theme bridge (per `sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24`).
- **EXPAND principle applies**: any new primitive added here goes BACK to `projects/sinister-dashboard-skeleton/dashboard-skeleton/` first, then consumed.
- Routes: `/` (overview) `/agents` `/vault` `/inbox` `/voice` `/devices` (mesh) `/settings`.
- Comms backend: same WebSocket / REST endpoints Sanctum panel uses (no fork — `composes` with `sinister-panel`).

### § 7.3 Vault on-device

- Syncthing fork (already vendored in sinister-vault) compiled for Android (`gomobile bind`).
- Auto-pair with operator's primary vault via QR code or pre-shared device ID.
- Vault data lives under `/data/data/com.sinister.vault/files/` (per-user sandboxed).

### § 7.4 Mesh (composes with operator's "no downtime" + "agents 24/7" doctrine)

- Tailscale on-device (already used by Leo's machine). Mobile becomes a fleet node.
- EVE can spawn off-device sub-agents via the mesh if the Pixel battery is low → continue work on Hetzner.
- Composes with `agent-autonomy-push-and-completion-2026-05-23` + `agent-continuity-no-long-naps-2026-05-24`.

## § 8 Physical flash (P5 — operator hands-on only)

1. Operator confirms backups (vault sync + Google account export if applicable).
2. Operator unlocks bootloader: `fastboot flashing unlock` (wipes device).
3. Operator flashes `sinister-os-mobile-bluejay-vN-factory.zip` via `flash-all.sh`.
4. First boot: EVE service launches, pairs vault via shown QR on operator's PC.
5. Operator re-enrolls accounts manually (no migration script in v1).
6. Optional: re-lock bootloader with custom AVB key (GrapheneOS path). Reduces root capability — operator picks.

**Gate:** P4 must show 7 consecutive green cuttlefish smoke runs (boot / panel install / vault sync / EVE announce / voice loopback / battery monitor / reboot survive) before P5 unlocks.

## § 9 Tool stack expected per phase

| Phase | Tools to invoke |
|---|---|
| P0 | `understand-anything` (every spawn), `github-prior-art.ps1` (candidate base ROMs), `operator-idea-intake.ps1` (operator dumps repos) |
| P1 | `seraphim audit --variant zzfm-r1` (base-ROM triad audit, quantum advantage), `librarian.search` (ROM manifest lookup), `triage.classify_file` (vendor blob detection) |
| P2 | `auditor.scan_secrets` (before any build-config commit), `custodian.snapshot_now` (snapshot scripts before destructive runs), `github-prior-art.ps1` per subsystem |
| P3 | `stealth-browser` (fetch cuttlefish docs), bot fleet for log triage on first-boot failures |
| P4 | `researcher.summarize_url` (AOSP API changes between versions), `curator.scan_candidates` (find existing Compose components before writing new ones), `scribe.generate_digest` (daily build status) |
| P5 | Operator hands-on; no agent autonomous flashing. EVE-on-Pixel reports `system-ready` heartbeat once paired. |

## § 10 Operator-gate questions (Q1-Q10)

The plan can't advance to P1 until operator answers:

1. **Carrier** — US Verizon / T-Mobile / AT&T / Mint Mobile / international? (affects band lock + IMS setup)
2. **GApps policy** — full GApps / sandboxed GApps (Graphene) / MicroG / none?
3. **AVB policy** — locked bootloader with custom key (loses root capability, gains hardware-backed verified boot) vs permanent unlock (keeps root, loses some banking apps)?
4. **Daily-driver intent** — is this replacing operator's primary phone, or is this an EVE-resident secondary device?
5. **Voice surface always-on** — yes / no / wake-word gated?
6. **Vault auto-pair** — pair with operator's primary vault on first boot, or manual QR each time?
7. **Update channel** — operator pulls OTA from Sanctum, or operator builds locally and sideloads?
8. **Telemetry** — any anonymized telemetry (boot success rate, crash logs to Sentry-self-hosted) or strictly local?
9. **App-compat tier** — banking apps must work (push toward locked AVB with sandboxed GApps) or doesn't matter (Magisk on Lineage path)?
10. **Mesh participation** — Pixel joins Tailscale fleet on first boot, or operator manually adds it?

Until 10/10 answered, P0 stays open. Once locked, P1 ROM-selection runs the seraphim audit.

## § 11 Risk register

| Risk | Mitigation |
|---|---|
| Cuttlefish doesn't match Pixel 6a hardware closely enough → "works in cvd, fails on metal" surprises in P5 | Run cuttlefish + a Pixel-3a-rooted-as-proxy (older but real hardware) in P3-P4 |
| Vendor blob licensing — Google's Pixel firmware terms forbid redistribution | Pull blobs at flash time from operator's existing device backup; never commit |
| Tensor G1 kernel quirks (custom blocks not in upstream Linux) | Stay close to Google's upstream `private/google-modules/`; don't backport features |
| Battery drain from EVE always-on | Run voice surface on a tiny tensor-G1 always-on core; defer to AP only on hotword |
| Banking apps detect root via SafetyNet/Play Integrity | Operator decision Q9; if banking matters → locked AVB path (no root) |
| Operator bricks Pixel during P5 flash | Pre-flash backup; Google's `bootloader-flash-recovery` is recoverable; document fastboot-mode entry (Vol-Down + Power) prominently |

## § 12 Phase status board

| Phase | Status | Started | Closed | Gate-out criterion |
|---|---|---|---|---|
| **P0 spec lock** | 🟡 **OPEN** | 2026-05-24 | — | Operator answers Q1-Q10 + clicks "P0 lock" |
| P1 base-ROM select | ⏳ pending P0 | — | — | seraphim audit + operator pick |
| P2 build env | ⏳ pending P1 | — | — | first `repo sync` complete + `m otatools` green |
| P3 cuttlefish vanilla | ⏳ pending P2 | — | — | cvd boots + adb shell + wifi up |
| P4 EVE integration | ⏳ pending P3 | — | — | 7 consecutive green smoke runs |
| P5 physical flash | ⏳ pending P4 | — | — | operator types `sinister-os-mobile flash-pixel` |

## § 14 Branding lock (operator hard-canonical 2026-05-24T16:09:10Z)

Operator utterance 2026-05-24T16:09:10Z (Turn 1 of this lane): *"take note this needs the sinister branding and look"*. Binding for the entire ROM, not just first-party apps.

**Inheritance:** every chrome surface in the OS inherits from `projects/sinister-dashboard-skeleton/dashboard-skeleton/` via a Jetpack Compose theme bridge (P4 deliverable). Per-surface accent override: Sinister purple `#c084fc` (purple-400) replaces the skeleton's iOS-blue `#0A84FF` reference — the ONLY allowed divergence per Sanctum CLAUDE.md hard-canonical 2026-05-24.

**Surfaces covered** (full enumeration in `research/branding-spec-2026-05-24.md`):

1. Bootloader unlock warning + fastboot chrome (custom AVB-signed images, P5 gate)
2. Boot animation — Sinister crystal stroke-in over purple-950 → purple-400 glow at `BOOT_COMPLETED`
3. Lock screen — wallpaper, clock font, lock glyph, notification chips (`.lg-card` recipe)
4. SystemUI — status bar icons, quick-settings tiles (`.lg-pill`), nav bar, sliders
5. Launcher (Trebuchet fork or `Sinister-Launcher.apk` in `/system/priv-app/`)
6. Settings app (theme retint first, full Compose port deferred to P4.5 polish)
7. Recovery (TWRP custom theme JSON — purple accent + fake-blur stripes)
8. First-party apps — Panel, Vault, EVE, Inbox, Mind — all use the Compose theme bridge

**EXPAND principle hard rule:** if a Compose-mobile primitive is needed and skeleton doesn't have it (likely candidates: `<BottomSheet>`, mobile `<TabBar>`, `<SegmentedControl>`, `<SwipeAction>`, `<Sheet>` modal), the new primitive lands in `projects/sinister-dashboard-skeleton/dashboard-skeleton/components/` FIRST, gets a `PATTERNS.md` row SECOND, then is consumed by this lane. Never write a one-off here.

**Image budget on P0 → P1 unlock:** 8 generated assets total (3 wallpapers + 5 first-party app glyphs) via `sinister-generator` brand-lock helper. Well under the conservative-balance 6-per-task cap (one batch task = wallpapers, second batch task = icons).

**Verbs at gate for this section:** SPEC IS **scaffolded** (`research/branding-spec-2026-05-24.md` exists + parse-clean). Will move to **shipped** when § 6 deliverables in branding-spec.md land in `source/` with cuttlefish screenshot evidence (purple accent visible on boot).

## § 15 Composes with

- `sinister-os-doctrine-2026-05-24` (PC sister project)
- `sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24` (UI inheritance + EXPAND)
- `quantum-memory-kernel-fleet-action-items-2026-05-23` (seraphim ZZ-FM r=1 K=4)
- `github-first-sourcing-doctrine-2026-05-24` (vendor before write)
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (verbs at gate)
- `agent-identity-eve` (persona)
- `agent-autonomy-push-and-completion-2026-05-23` (push agent/sinister-os-mobile/* freely)
- `do-not-revert-operator-canonical-protections-2026-05-23` (P11 protects UI inheritance)
- `operator-utterance-tracking-doctrine-2026-05-24` (originating utterances ts 2026-05-24T15:56:34Z scaffold + 2026-05-24T16:09:10Z branding lock)
- `research/branding-spec-2026-05-24.md` (this lane's full per-surface branding enumeration)
