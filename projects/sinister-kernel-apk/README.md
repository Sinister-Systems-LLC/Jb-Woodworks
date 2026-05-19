# sinister-kernel-apk â€” pointer + integration notes

This directory is a Sanctum-side **pointer** to the Kernel APK project. Sanctum does NOT vendor the source.

## Canonical locations

| What | Where |
|---|---|
| **Canonical source (D: drive)** | `D:\Sinister\01_Projects\Sinister\Sinister-APK\` (= junction of `Kernel-SU-Setup\`) |
| **Legacy source (Desktop)** | `C:\Users\Zonia\Desktop\Kernel-SU-Setup\` |
| **GitHub repo** | `https://github.com/Sinister-Systems-LLC/Sinister-Kernel-APK` (pending init / confirm) |
| **MCP server module** | `leo-version/mcp-server/sinister_apk_mcp/` |
| **Hub memory (operator-private)** | `D:\Sinister\Sinister Skills\01_MEMORY\sinister-apk\` |
| **Per-project agent** | `sinister-apk` (lane owner â€” only this agent edits source) |

## Note on the dual name

`Sinister APK` IS `Kernel-SU-Setup` (Windows directory junction). They are the same content; `Sinister-APK` is the preferred display name in the LLC universe, `Kernel-SU-Setup` is the historical name still used by `~/.claude/.mcp.json` cwd.

The MCP `cwd` in `~/.claude/.mcp.json` for `sinister-apk` should point at: `C:\Users\Zonia\Desktop\Kernel-SU-Setup\leo-version\mcp-server`. Audit fix script: `D:\Sinister\Sinister Skills\08_AUTOMATIONS\fix-sinister-apk-mcp-path.ps1` (already run; restart required for changes).

## How Sanctum integrates with Kernel APK

Sanctum bots can **READ** APK state via:
- `librarian.recall query=...` against `01_MEMORY/sinister-apk/`
- The `sinister-apk` MCP server (when registered in Claude's main mcp.json) exposes its own tools

Sanctum bots **must NEVER WRITE** to APK source. That's the apk agent's lane.

## Pushing Kernel APK to GitHub (when ready)

```powershell
cd 'D:\Sinister\01_Projects\Sinister\Sinister-APK'
& 'D:\Sinister Sanctum\automations\git-toolkit.ps1' init .
& 'D:\Sinister Sanctum\automations\git-toolkit.ps1' remote-set . git@github.com:Sinister-Systems-LLC/Sinister-Kernel-APK.git
& 'D:\Sinister Sanctum\automations\git-toolkit.ps1' safe-push .
```

## Excluded from any push

- `keybox/Yurikey*.xml` â€” operator-private
- `.gradle/`, `build/`, `*.apk`, `*.aab`, `*.dex` (build artifacts)
- `local.properties`, `captures/`
