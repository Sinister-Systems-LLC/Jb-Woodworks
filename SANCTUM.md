# Sinister Sanctum Ã¢â‚¬â€ what this repo is

**Local path:** `D:\Sinister Sanctum\` (canonical real folder, as of Phase 8ad). `D:\Sinister LLC\` is kept as a backwards-compat junction shim so legacy script refs still resolve. Parent-side junction `D:\Sinister\Sanctum\` exists so the operator can navigate from the hub parent into the public child. Existing scripts that hardcode `D:\Sinister Sanctum\` continue to work; new scripts may use either.
**GitHub:** `https://github.com/Sinister-Systems-LLC/Sinister-Sanctum`
**Scope:** ALL Sinister company projects (Sanctum + Snap-API-EMU + TikTok-EMU + Panel + Kernel-APK). **Excluded:** LetsText, JOKR-global, library-of-jokr-mirror, personal stuff, operator-private references (Yurikey roster, secrets policy).

Sanctum is the new Library of Alexandria for Sinister LLC Ã¢â‚¬â€ the orchestration
repo that gives every other Sinister product repo (Snap EMU, TikTok EMU, Control
Center/Panel, Kernel APK) access to the same bot fleet, automations, design docs, and
session-start protocols.

## The 5 GitHub repos (Sinister LLC universe)

**GitHub organization:** `Sinister-Systems-LLC` (org URL: https://github.com/Sinister-Systems-LLC).

| Repo (GitHub) | Local path | What it is |
|---|---|---|
| **[Sinister Sanctum](https://github.com/Sinister-Systems-LLC/Sinister-Sanctum)** | `D:\Sinister Sanctum\` | THIS repo. Orchestration + 12 Sinister Bots + docs + automations + session-start. The "new library of alexandria". |
| **[Sinister Snap API EMU](https://github.com/Sinister-Systems-LLC/Sinister-Snap-API-EMU)** | `D:\Sinister\01_Projects\Sinister\Sinister-Snap-EMU\` (canonical) or `C:\Users\Zonia\Desktop\Sinister Snap EMU.API` (legacy) | Snap API client + cvd signing oracle. **Already pushed (initial commit 628163a, 1058 files).** |
| **[Sinister TikTok EMU](https://github.com/Sinister-Systems-LLC/Sinister-TikTok-API-EMU)** | `D:\Sinister\01_Projects\Sinister\Sinister-TikTok-EMU\` (canonical) or `C:\Users\Zonia\Desktop\Sinister Tiktok EMU.API` (legacy) | TikTok API + a11y + signing pipeline. (Repo name may be `Sinister-TikTok-API-EMU` matching Snap pattern; operator confirms.) |
| **[Sinister Panel](https://github.com/Sinister-Systems-LLC/Sinister-Panel)** (Sinister Control Center) | `D:\Sinister\01_Projects\Sinister\Sinister-Panel\source\` (canonical; note `source/` wrapper) or `C:\Users\Zonia\Desktop\Sinister-Panel` (legacy fallback, marked read-only by panel agent 2026-05-18 PM) | Live dashboard at `snap.sinijkr.com`. HEAD: `ad333ee` (Overview rail rework). |
| **[Sinister Kernel APK](https://github.com/Sinister-Systems-LLC/Sinister-Kernel-APK)** | `D:\Sinister\01_Projects\Sinister\Sinister-APK\` (canonical; mcp at `leo-version/mcp-server/`) or `C:\Users\Zonia\Desktop\Kernel-SU-Setup` (legacy) | Detector + KernelSU + LukeShield modules. |

**Note:** the operator runs per-project Claude sessions in parallel; each session is robocopying its source from Desktop Ã¢â€ â€™ `D:\Sinister\01_Projects\Sinister\` (MASTER-PLAN Phase 1). Once all 4 product repos are fully in `01_Projects\Sinister\`, the Desktop fallbacks retire. `automations/migrate-projects.ps1` auto-prefers `01_Projects` when present.

Additional Sinister-group projects in `D:\Sinister\01_Projects\Sinister\` (operator may or may not include in GitHub): snap-signer, library-of-alexandria, kernel-su-setup, sinister-rka, sinister-bumble-emu, sinister-sandbox, sinister-tg, sinister-imessage-bridge, sinister-workstation-setup, sinister-emulator-bundle.

## How the 3 product repos consume Sanctum

Each product repo's `CLAUDE.md` references Sanctum's:

- **Bot fleet** Ã¢â‚¬â€ 12 MCP bots (sentinel, librarian, custodian, etc.) for recall, audit, scrape, backup
- **`docs/ARCHITECTURE.md`** Ã¢â‚¬â€ the 3-layer model + data flows
- **`docs/BOT-MEMORY-PROTOCOL.md`** Ã¢â‚¬â€ how absorb()/learn/forget works
- **`docs/MEMORY-CODEC-AND-CRYPTO.md`** Ã¢â‚¬â€ token codec + at-rest vault
- **`docs/DRIVE-ENCRYPTION.md`** Ã¢â‚¬â€ VeraCrypt container plan
- **`SESSION-START/`** Ã¢â‚¬â€ universal rules + gotchas + operator queue + recovery
- **`automations/`** Ã¢â‚¬â€ `git-toolkit.ps1` (init / safe-push / ci-bootstrap / etc.); `secret-scrub.ps1`; etc.

Product repos do NOT vendor Sanctum Ã¢â‚¬â€ they reference it by path on the operator's
machine + by GitHub URL for Leo's machine. (When ready for full cross-machine
share, Sanctum could ship as a git submodule into each.)

## What lives in Sanctum vs what doesn't

**Sanctum HAS:**

- `bots/agents/` Ã¢â‚¬â€ 12 Sinister Bots (junction to `D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\` on operator's machine)
- `automations/` Ã¢â‚¬â€ Git toolkit, secret-scrub, migrate-projects + `hub-scripts/` junction
- `docs/` Ã¢â‚¬â€ ARCHITECTURE, SETUP, DEPLOYMENT, AGENT-BOOTSTRAP, BOT-MEMORY-PROTOCOL, MCP-NETWORK, ALIVE-ARCHITECTURE, MEMORY-CODEC-AND-CRYPTO, DRIVE-ENCRYPTION
- `SESSION-START/` Ã¢â‚¬â€ cold-resume anchor (mirrored to/from the hub)
- `_vault/_index.md` Ã¢â‚¬â€ master Obsidian vault entry
- `CONTRIBUTING.md` + `LICENSE` + `.gitignore`
- `.github/workflows/bots-smoke.yml` Ã¢â‚¬â€ CI
- `automations/window-manager/` Ã¢â‚¬â€ RKOJ.exe source (flagship workstation binary, built via PyInstaller; previously named Sanctum-Console.exe)
- `tools/sinister-vault/` Ã¢â‚¬â€ the **Sinister Vault** — 1TB collaborative storage server (Gitea + Syncthing + MCP + multi-account)
- `agents/vault/` Ã¢â‚¬â” MCP server wrapping the vault for any Claude session (10 tools: commit/push/pull/list/search/sync_status/accounts/snapshot/audit/health)
- `docs/WORKBENCH.md` Ã¢â‚¬â” RKOJ operator one-pager (2 tabs / ribbon / cycle points / scheduler / popouts / Vault drawer)

**Sanctum does NOT have:**

- Snap EMU / TikTok EMU / Panel source Ã¢â‚¬â€ those are their own repos
- LetsText, JOKR-global, library-of-jokr-mirror Ã¢â‚¬â€ operator-private; never in Sinister LLC scope
- Operator-private references (Yurikey roster, secrets policy)
- `_backups/`, `_logs/`, `runtime-state/`, `01_MEMORY/_consolidated/`

## Per-repo workflow

### One-click bats (the easy way)

| Bat | What it does |
|---|---|
| `C:\Users\Zonia\Desktop\Push-Sanctum-To-GitHub.bat` | Pushes Sanctum only. Auto-inits git if needed, scrubs secrets, commits + pushes. Operator-triggered, never scheduled, never force-pushes. |
| `C:\Users\Zonia\Desktop\Push-All-Sinister.bat` | Loops Sanctum + 4 product repos. **Defaults to dry-run** (status report only). Pass `/Live` or answer Y at the prompt to actually push. Per-repo secret-scrub gate. |
| `C:\Users\Zonia\Desktop\Sync-Sanctum.bat` | Operator-triggered ff-pull of Leo's commits. Refuses if working tree dirty. |

### Manual / per-project workflow

```powershell
# Each product repo (when its agent says ready)
cd 'D:\Sinister\01_Projects\Sinister\Sinister-Snap-EMU\source'
& 'D:\Sinister Sanctum\automations\git-toolkit.ps1' safe-push .   # secret-scrub gate FIRST
```

For repos still needing first-time setup (TikTok-EMU, Kernel-APK currently):

```powershell
cd 'D:\Sinister\01_Projects\Sinister\Sinister-TikTok-EMU\source'
& 'D:\Sinister Sanctum\automations\git-toolkit.ps1' init .
& 'D:\Sinister Sanctum\automations\git-toolkit.ps1' doc-bootstrap .
& 'D:\Sinister Sanctum\automations\git-toolkit.ps1' ci-bootstrap .
& 'D:\Sinister Sanctum\automations\git-toolkit.ps1' pre-commit-install .
& 'D:\Sinister Sanctum\automations\git-toolkit.ps1' remote-set . git@github.com:Sinister-Systems-LLC/Sinister-TikTok-API-EMU.git
& 'D:\Sinister Sanctum\automations\git-toolkit.ps1' safe-push .
```

Sanctum itself ships from `D:\Sinister Sanctum\` (or the `D:\Sinister Sanctum\` junction). The `Push-Sanctum-To-GitHub.bat` handles its first-time setup automatically.

## Note on Sinister Kernel APK

The Kernel-SU-Setup folder also hosts the `sinister_apk_mcp` module at
`leo-version/mcp-server/sinister_apk_mcp/`. The operator's `~/.claude/.mcp.json`
needs `cwd` set to `C:\Users\Zonia\Desktop\Kernel-SU-Setup\leo-version\mcp-server`
(audit 2026-05-18 found old path stale Ã¢â‚¬â€ fix via
`D:\Sinister\Sinister Skills\08_AUTOMATIONS\fix-sinister-apk-mcp-path.ps1`).

## UI design lineage

**Operator directive (2026-05-19):** use `C:\Users\Zonia\Desktop\dashboard-skeleton\` ONLY for all new UIs.

Every UI surface across the Sinister LLC universe consumes the `dashboard-skeleton` token set + Liquid Glass classes + 16 doctrine primitives. Canonical real folder lives at `C:\Users\Zonia\Desktop\dashboard-skeleton\`; Sanctum mounts it read-only at `D:\Sinister Sanctum\skills\dashboard-skeleton\` (intended junction).

**Sanctum branding:** the master/orchestration logo is `C:\Users\Zonia\Desktop\INPO\Things\ART\Img.png` (purple crowned horned demon skull). Use it everywhere Sanctum branding appears — Sanctum Console, EXE chrome, launchers, master agent identity, bot-fleet activator. The Sanctum-specific purple ramp (`#7A3DD4` / `#A06EFF` / `#4A1F8E`) is the Sanctum accent and is back-compat-legal alongside the panel-side iOS blue accent (`#0A84FF`).

Full doc: **[`docs/UI-DESIGN-SYSTEM.md`](docs/UI-DESIGN-SYSTEM.md)**. Upstream authority: `C:\Users\Zonia\Desktop\dashboard-skeleton\THEME-DOCTRINE.md`.

## TL;DR

- **How we won:** Sanctum = `D:\Sinister Sanctum\`, the "library of alexandria" for all 4 Sinister repos. Bots + docs + automations live here; product source lives in their own repos.
- **What you need to do:**
  - For each of the 3 product repos, run the 6-step git-toolkit workflow above.
  - Sanctum itself: pick LICENSE, add GitHub remote, run `safe-push`.
