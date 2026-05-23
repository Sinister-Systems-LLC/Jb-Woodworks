<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# LEO :: Missing Sub-Project `source/` — One-Click Fix

## What you're seeing

When you launch a Sinister Sanctum session and try to pick **Sinister Panel**,
**Kernel APK**, **Sinister Snap-API-EMU**, or **Sinister TikTok-API-EMU**, the
picker shows a `[missing root]` badge and the spawn aborts with:

```
sanctum sub-projects are missing their `source/` content on this workstation
```

This is because the operator's box uses NTFS directory junctions to other
`D:\` paths that don't exist on yours. Your Sanctum clone is fine — the
per-project source folders just need to be cloned from their own GitHub
repos into `projects/<key>/source/`.

## The fix (1 command)

```powershell
cd "D:\Sinister Sanctum"
powershell -ExecutionPolicy Bypass -File automations\clone-missing-sources.ps1
```

Or **double-click**: `automations/Clone-Missing-Sources.bat`

That script reads `automations/session-templates/projects.json`, finds every
project whose `root` is missing AND has a `github` remote, and runs:

```
git clone git@github.com:Sinister-Systems-LLC/<repo>.git <target-path>
```

If SSH fails (no key) it falls back to HTTPS (uses `$env:GH_TOKEN` if set).

## What it will clone (on your box specifically)

The script targets every project with a `github` field in `projects.json`.
Your screenshot showed 4 missing — typically these:

| Key | GitHub repo | Target path |
|---|---|---|
| `sinister-panel` | `Sinister-Systems-LLC/Sinister-Panel` | `projects/sinister-panel/source/` |
| `kernel-apk` | `Sinister-Systems-LLC/Sinister-Kernel-APK` | `projects/sinister-kernel-apk/source/` |
| `snap-emulator-api` | `Sinister-Systems-LLC/Sinister-Snap-API-EMU` | `projects/sinister-snap-emu/source/` |
| `tiktok-emulator-api` | `Sinister-Systems-LLC/Sinister-TikTok-API-EMU` | `projects/sinister-tiktok-emu/source/` |

(Other projects with remotes already exist on your box because they were
included in the original `git clone` of the umbrella Sanctum repo.)

Total clone size: ~50-200 MB depending on history depth + media. Time:
30s-2 min on a normal connection.

## After it finishes

- Re-launch `Sinister Start.bat` — the 4 projects should now show clean
  in the picker (no `[missing root]` badge).
- Pick any of them — Claude session spawns into the right working directory.
- Each cloned dir is its own git repo. To pull updates: `cd <root> && git pull`.

## Troubleshooting

### "Permission denied (publickey)"
Your SSH key isn't registered with GitHub. Two paths:

**SSH (preferred)**:
```
ssh-keygen -t ed25519 -C your-email@example.com
type ~/.ssh/id_ed25519.pub      # copy this
```
Paste at <https://github.com/settings/keys>, then re-run the script.

**HTTPS with token**:
```
# Mint at https://github.com/settings/tokens (scope: repo)
[Environment]::SetEnvironmentVariable('GH_TOKEN','<your-token>','User')
```
Restart your shell, re-run the script.

### "Repository not found" or "not authorized"
The org `Sinister-Systems-LLC` must have invited your GitHub account.
Confirm at <https://github.com/Sinister-Systems-LLC/people> — or ask
the operator to invite you.

### Some clones succeed but others fail
The script reports per-project status. Failed ones can be retried
individually:
```powershell
.\automations\clone-missing-sources.ps1 -Only kernel-apk
```

## What this does NOT do

- Does not modify `projects.json` — that's operator-owned.
- Does not register additional MCP servers — already in `~/.claude/.mcp.json`.
- Does not change your Claude Code config — `.claude/settings.json` is yours to manage.

## Reference

- Script: `automations/clone-missing-sources.ps1`
- Bat wrapper: `automations/Clone-Missing-Sources.bat`
- Auth doctrine: `_shared-memory/knowledge/non-interactive-auth-doctrine-2026-05-23.md`
- Pre-spawn guard origin: Leo screenshot 2026-05-23 + operator directive
- Author: RKOJ-ELENO :: 2026-05-23
