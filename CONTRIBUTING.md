# Contributing to Sinister LLC

For the operator + Leo + future collaborators.

## Before you commit

**Run the secret scrub.** Once, when you set up your local clone:

```powershell
cd 'D:\Sinister Sanctum'
.\automations\secret-scrub.ps1 -DryRun    # report what would be redacted
.\automations\secret-scrub.ps1            # actually redact
```

This walks every file and flags:
- Anthropic / OpenAI / Google API keys (`sk-ant-...`, `AIza...`, etc.)
- GitHub personal access tokens (`ghp_...`, `gho_...`)
- Private keys (`-----BEGIN ... PRIVATE KEY-----`)
- `.env` files (move to `.env.example` with placeholder values)
- `secrets/` directories
- `credentials.json`, `*.pem`, `*.p12`, `keybox*.xml`

If any are found, FIX before commit. The `.gitignore` already excludes the
common patterns, but local edits can still introduce them.

## Bot fleet quickstart

```powershell
cd 'D:\Sinister Sanctum'
.\automations\activate-everything.ps1
```

This installs the 13 Sinister Bots into `~/.claude/.mcp.json`, points them at
the LLC root (`SINISTER_HUB_ROOT=D:\Sinister Sanctum`), and registers the Custodian
backup daemon to snapshot the LLC tree at `D:\_backups\sinister-llc\`.

Restart Claude Code after activation. Verify with `sinister-bus.list_network`
(should report 19 endpoints) and `<bot>.health()`.

## Adding a new bot

1. Author `bots/<bot-name>/server.py` following the FastMCP pattern
   (see `bots/sentinel/server.py` for the simplest example).
2. Author `bots/<bot-name>/SYSTEM-PROMPT.md` + `KNOWN-GOTCHAS.md` + `learned.md`
   (the absorption-protocol trio; see `docs/BOT-MEMORY-PROTOCOL.md`).
3. Add to `automations/install-fleet.ps1`'s default `-Agents` list.
4. Add a row to `bots/README.md`'s status table.
5. Re-run `automations/activate-everything.ps1`.

## Adding a new project

The 8 Sinister-branded projects ship as **directory junctions** from `C:\Users\Zonia\Desktop\<project>\`
into `D:\Sinister Sanctum\projects\<project>\`. The source stays at Desktop;
working there or here is equivalent.

To add a new project:

```powershell
cd 'D:\Sinister Sanctum\projects'
cmd /c mklink /J "<new-project>" "C:\path\to\source"
# Then author projects/<new-project>/README.md if missing.
# Then run .\..\automations\secret-scrub.ps1 -Path projects\<new-project>
```

## Commit conventions

- One commit per logical change. No "wip" or "fixes" without context.
- Subject line under 70 chars. Body explains the WHY.
- Reference the project: `panel: fix StatusBadge href passthrough`.

## What NOT to commit

Per `.gitignore` + the operator's no-leak policy:
- `.env` files, `credentials.json`, `*.pem`, `*.key`, anything under `secrets/`
- `_backups/`, `_logs/`, `runtime-state/`
- `01_MEMORY/_consolidated/` (operator's daily working state)
- `09_REFERENCE/yurikey-roster.md` (operator-private inventory)
- Generated/transient: `*.tmp.*`, `*.bak.*`, FAISS indexes, screenshots
- The Hacker bot (until operator authorizes inclusion of the upstream RE)

## License + attribution

See `LICENSE` at repo root. Currently a placeholder; operator picks MIT /
Apache / Proprietary before any public push.

Inspirations + RE'd projects:
- `bots/stealth-browser/` -- RE'd from [vibheksoni/stealth-browser-mcp](https://github.com/vibheksoni/stealth-browser-mcp) (MIT)
- `bots/hacker/` (deferred) -- would RE [AKCodez/hackingtool-plugin](https://github.com/AKCodez/hackingtool-plugin)
- MCP protocol -- Anthropic

## UI design -- canonical source

**Operator directive (2026-05-19):** use `C:\Users\Zonia\Desktop\dashboard-skeleton\` ONLY for all new UIs.

All new UIs in Sanctum (and in every Sinister product repo that consumes Sanctum) **MUST** consume `dashboard-skeleton` tokens, Liquid Glass classes (`.lg-card`, `.lg-card-hero`, `.lg-rail`, `.lg-pill`, `.lg-pill-active`, `.lg-button`, `.lg-input`, `.lg-popover`), motion vars (`--motion-fast 150ms` / `--motion-med 300ms` / `--motion-slow 600ms` with `cubic-bezier(0.22, 1, 0.36, 1)`), and the 16 doctrine primitives (`TabHeader`, `KpiCard`, `Chart`, `PageShell`, `GeoHeat`, `AdvancedFilter`, `FilterPillRow`, `NumberTicker`, `EmptyState`, `LoadingState`, `ErrorState`, `SectionHeader`, `Glow`, `AuroraBg`, `Calendar`, `GlassDialogHeader`).

**Accent rules:**
- Panel-side surfaces (dashboard, inbox, agency, admin, compliance, audit, vault, fans, calls, analytics, templates, tracking-links, docs, smart-messenger) **MUST** use the iOS blue ramp (primary `#0A84FF`).
- The purple ramp (`#7A3DD4` primary, `#A06EFF` soft, `#4A1F8E` deep) is permitted **ONLY** for Sanctum-specific surfaces — Sanctum Console, EXE chrome, launchers, master agent identity, bot-fleet activator. The Sanctum logo at `C:\Users\Zonia\Desktop\INPO\Things\ART\Img.png` (purple crowned horned demon skull) belongs on those surfaces.
- No bespoke material recipes outside `.lg-*`. No `lucide-react`. No magic-wand Eve icon (it is a geometric crystal).

See **[`docs/UI-DESIGN-SYSTEM.md`](docs/UI-DESIGN-SYSTEM.md)** for the canonical doc — token tables, Liquid Glass catalog, primitive list, type scale, when-to-consume-what guide, and the keep-in-sync process. Upstream authority is `C:\Users\Zonia\Desktop\dashboard-skeleton\THEME-DOCTRINE.md`.
