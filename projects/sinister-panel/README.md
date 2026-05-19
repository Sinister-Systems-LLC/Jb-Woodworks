# sinister-panel â€” pointer + integration notes

This directory is a Sanctum-side **pointer** to the Panel project (Sinister Control Center). Sanctum does NOT vendor the source â€” it lives in its own GitHub repo with its own per-project Claude session.

## Canonical locations

| What | Where |
|---|---|
| **Canonical source (D: drive)** | `D:\Sinister\01_Projects\Sinister\Sinister-Panel\source\` |
| **Legacy source (Desktop, marked read-only by panel agent 2026-05-18 PM)** | `C:\Users\Zonia\Desktop\Sinister-Panel\` |
| **GitHub repo** | `https://github.com/Sinister-Systems-LLC/Sinister-Panel` |
| **Deployed at** | `https://snap.sinijkr.com` (Hetzner) |
| **Hub memory (operator-private)** | `D:\Sinister\Sinister Skills\01_MEMORY\sinister-panel\` |
| **Per-project agent** | `sinister-panel` (lane owner â€” only this agent edits source) |

## Current state (per panel agent's last report)

- HEAD: `ad333ee` ("Overview rail rework â€” both Live activity + Creation log on left + LetsText-style 4-up PlatformTabBar with real platform marks")
- 381 commits in history
- Theme: PURPLE (stable)
- Doctrine: 0/0/0/0/0 (all green)
- `tsc` errors: 0
- `next build`: green
- **Pending operator action:** click `C:\Users\Zonia\Desktop\Deploy-Hetzner.bat` to ship `ad333ee` to prod
- Two deploy bats coexist: legacy Desktop one + canonical `D:\Sinister\Sinister Skills\08_AUTOMATIONS\_OneClick_Deploy.bat`; both target the same source

## How Sanctum integrates with Panel

See `D:\Sinister Sanctum\docs\PANEL-INTEGRATION.md` for the full Leo-facing boundary doc. Summary:

- Sanctum bots can **READ** panel state via `researcher.summarize_url url=https://snap.sinijkr.com/api/health` and `check-hetzner-state` script
- Sanctum bots **must NEVER WRITE** to panel source
- Panel deploys go through the operator's existing `_OneClick_Deploy.bat` (chained via `Deploy-Hetzner.bat`)
- Cross-session messaging via `sinister-bus.delegate_to agent_name="sinister-panel"`

## Pushing Panel to GitHub (operator already initiated)

Panel is already pushed (the repo exists at `Sinister-Systems-LLC/Sinister-Panel`). For subsequent pushes:

```powershell
cd 'D:\Sinister\01_Projects\Sinister\Sinister-Panel\source'
& 'D:\Sinister Sanctum\automations\git-toolkit.ps1' safe-push .
```

Or use the multi-repo bat: `C:\Users\Zonia\Desktop\Push-All-Sinister.bat -Live`.

## Excluded from any push (operator-private)

- `.env*`, all environment-overlay files
- `secrets/`, `credentials/`
- `node_modules/`, `.next/`, `out/`, `dist/`, `build/`, `.turbo/`
