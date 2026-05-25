# Fleet Tools Port to Sinister OS Doctrine — 2026-05-25

> **Author:** RKOJ-ELENO :: 2026-05-25
> **Lane:** fleet-wide (sinister-os captured it; binding on every Sanctum tool / project lane)
> **Originating utterance (verbatim 2026-05-25T09:41Z):** *"make sure all things like this come with us when we setup the OS and os installed and ready"*
> **Prior context (screenshot):** *"make this entire login process actually work and be fully automated and add refresh and detection for auto relogin all things like that use our sinister browser system"*
> **Composes with:** `sinister-os/MASTER-AUDIT-EXPANSION-2026-05-25` Block N (full design) · `agent-containment-failsafe-doctrine-2026-05-25` (containerization model) · `no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25` (Python-first ports) · `automate-everything-no-operator-admin-2026-05-25`.

## TL;DR

Every Sanctum fleet tool — Sinister Browser System (auto-relogin / refresh / detect), EVE.exe, eve-picker, sinister-term, panel, MCP bots, automation scripts, sinister-generator, sinister-memory, sinister-vault, sinister-overseer, and every successor — ships **preinstalled and ready** in the Sinister OS image. Operator boots Sinister OS and every tool he used on Windows works on Day 1.

**Binding rule for new tools:** any NEW fleet tool authored from this commit forward MUST include a Linux-port plan in its first PROGRESS row. No "we'll port later" — port plan is shipped alongside the Windows version, even if implementation lags.

## What "comes with the OS"

| Category | Examples | Port strategy default |
|---|---|---|
| **Python tools** | sinister-bus, sinister-vault, sinister-memory, sinister-overseer, sinister-generator, automations/*.py | Port directly — Python is cross-platform |
| **Browser automation** | Ruflo `browser_*` MCP, Sinister Browser System, auto-relogin | Playwright + Chromium-flatpak; native Linux port |
| **PyQt apps** | EVE.exe picker, eve-picker variants | PyQt6 native (cross-platform); re-skin where needed |
| **GTK/Qt re-implementations** | Anything where the Windows version uses Win32 API directly | Re-implement as GTK4 (preferred Linux-native) or PyQt6 |
| **Web apps** | Sinister Panel | No port — already web; ship as local PWA |
| **PowerShell scripts** (~250 legacy) | automations/*.ps1 | Python rewrite per `no-bat-no-ps1` doctrine on next touch |
| **PyInstaller bundles** | EVE.exe | Re-implement as native Linux service + GTK4 frontend; NOT WINE-wrapped (Win32 deps too tangled) |
| **Win32-only tools** (rare) | RKOJ workbench if Qt-tangled with Win32 | Linux re-implementation OR drop in favor of native Linux compositor primitives (e.g. Hyprland scratchpads) |

## Login automation (the screenshot ask) — concrete spec

The Sinister Browser System (cookie capture + session record/replay + template apply) plus auto-relogin + refresh + detect must work on Sinister OS via `sinister-browser-bot.service` user service:

1. **Record once** — `sinister-browser record --domain snap.sinijkr.com` opens visible Chromium; operator logs in; tool captures full flow (URL chain, form fills, MFA entry, cookies + localStorage + sessionStorage). Saves to `/var/lib/sinister/browser-sessions/<domain>.toml`.
2. **Replay automatically** — on cookie expiry OR 401/403 OR detected login-redirect, headless Chromium re-runs the recorded flow. No operator click.
3. **TTL refresh proactively** — `sinister-browser-refresh.timer` (15-min cadence) checks every active session; if `now > expiry - refresh_buffer`, fires replay before failure.
4. **Auto-detect failure** — context heartbeat (small periodic `GET /me`) confirms session liveness. 3 consecutive failures → notification + flag `manual-intervention-required`.
5. **MFA** — TOTP secrets stored in encrypted Vault; replay auto-fills OTP at the right step. Yubikey OTPs route via `pyhidapi`.
6. **Audit** — every replay logged to `/var/log/sinister/browser-bot.jsonl` with timestamp + domain + result + duration.

## Preinstall manifest — single source of truth

`source/iso-build/preinstall-manifest.toml` is the canonical list. Every tool entry has:

- `package` — Arch PKGBUILD name (built from this repo's `projects/*/source/`)
- `service` — systemd unit name (omit if CLI-only)
- `user_service` — bool (user@.service vs system)
- `slice` — cgroup slice (per Block M containment)
- `auto_start` — bool
- Tool-specific config (mfa_vault_path, session_dir, port, etc.)

ISO build script (`source/iso-build/build.sh`) consumes the manifest → generates `packagelist.txt` + systemd unit symlinks + first-boot wizard config.

## State migration (Windows → Linux)

The operator's existing state on Windows migrates via a first-boot wizard:

- `D:\Sinister Sanctum\` → `/srv/sinister-sanctum/`
- `D:\sinister-vault\` → `/srv/sinister-vault/`
- `D:\LetsText\` → `/srv/sinister-projects/letstext/`
- `C:\Users\Zonia\.claude\` → `~/.claude/`
- Browser sessions → re-recorded on Linux (cookies rarely survive cross-OS)
- MFA secrets → operator re-enrolls (security best practice anyway)

Validation: `eve verify migration --since <ts>` runs sanity checks.

## Containment composition (with Block M doctrine)

Every fleet tool ported per this doctrine ALSO runs in an OCI container per `agent-containment-failsafe-doctrine-2026-05-25`. There is no exception. The port doctrine handles "WHERE the code runs"; the containment doctrine handles "WITH WHAT POLICIES the code runs". Both apply simultaneously.

## Anti-patterns

- ❌ Shipping a NEW Windows-only tool without a Linux port plan
- ❌ Wrapping a Win32-heavy app in WINE as "the port" — that's a debt-laden hack; rewrite native
- ❌ Skipping the preinstall manifest entry "to keep the ISO small" — every fleet tool is preinstalled; size is the wrong axis to optimize for an operator-private OS
- ❌ Asking operator to "install X manually after first boot" — violates `automate-everything-no-operator-admin`
- ❌ Letting browser sessions silently expire because "the operator will re-login when prompted" — the whole point of the browser system is the operator NEVER sees login prompts

## Pass criterion

Every fleet tool is doctrine-compliant when:

- It has a row in `source/iso-build/preinstall-manifest.toml`
- It has a Containerfile in `source/iso-build/containers/<tool>/Containerfile`
- It has an AppArmor profile in `source/iso-build/apparmor-profiles/<tool>.profile`
- It has a systemd unit (system or user@.service) in `source/iso-build/systemd/<tool>.service`
- Its PROGRESS row mentions "Linux port: shipped/in-flight/queued"
- The operator can run the tool on a fresh Sinister OS install without manual setup beyond the first-boot wizard

## Reference

Full design: `projects/sinister-os/plans/MASTER-AUDIT-EXPANSION-2026-05-25/plan.md` § 3.14 Block N (N.1 - N.8).

Implementation lands at sinister-os P1-P4 (per master plan rollout). Doctrine binding from this commit forward.
