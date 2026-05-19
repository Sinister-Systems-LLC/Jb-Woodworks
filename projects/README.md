# projects/ â€” Sanctum-side pointer + integration notes

Sanctum does NOT vendor the product repos. Each Sinister product repo lives in its own GitHub repo + its own canonical D: drive path, and is owned by its own per-project Claude session (lane discipline per `D:\Sinister\Sinister Skills\PARALLEL-AGENT-COORDINATION.md`).

This directory holds **pointer + integration README**s only â€” one per product repo â€” so Sanctum readers can:
- Find the canonical source path
- Know the GitHub repo URL
- Understand how Sanctum bots interact with that project (read-only, never writing source)
- See the current head state without leaving Sanctum

## The 5 product repos (Sinister LLC universe)

| Pointer | Canonical source | GitHub | Owner agent |
|---|---|---|---|
| [sinister-snap-emu](./sinister-snap-emu/README.md) | `D:\Sinister\01_Projects\Sinister\Sinister-Snap-EMU\source\` | [Sinister-Snap-API-EMU](https://github.com/Sinister-Systems-LLC/Sinister-Snap-API-EMU) | snap-signer |
| [sinister-tiktok-emu](./sinister-tiktok-emu/README.md) | `D:\Sinister\01_Projects\Sinister\Sinister-TikTok-EMU\source\` | [Sinister-TikTok-API-EMU](https://github.com/Sinister-Systems-LLC/Sinister-TikTok-API-EMU) (pending init) | sinister-tiktok |
| [sinister-panel](./sinister-panel/README.md) | `D:\Sinister\01_Projects\Sinister\Sinister-Panel\source\` | [Sinister-Panel](https://github.com/Sinister-Systems-LLC/Sinister-Panel) | sinister-panel |
| [sinister-kernel-apk](./sinister-kernel-apk/README.md) | `D:\Sinister\01_Projects\Sinister\Sinister-APK\` | [Sinister-Kernel-APK](https://github.com/Sinister-Systems-LLC/Sinister-Kernel-APK) (pending init) | sinister-apk |
| [sinister-emulator-bundle](./sinister-emulator-bundle/README.md) | `D:\Sinister\01_Projects\Sinister\Sinister-Emulator-Bundle\source\` | _(auxiliary â€” not in public GitHub scope)_ | _(holding; touched by snap-signer when needed)_ |
| **Sanctum itself** | `D:\Sinister Sanctum\` (= `D:\Sinister Sanctum\` junction) | [Sinister-Sanctum](https://github.com/Sinister-Systems-LLC/Sinister-Sanctum) (pending first push) | master |

## Optional: populate this directory with junctions

If you want `D:\Sinister Sanctum\projects\<name>\source\` to actually resolve to the project source (without leaving Sanctum), run:

```powershell
cd 'D:\Sinister Sanctum\automations'
.\migrate-projects.ps1 -DryRun    # preview
.\migrate-projects.ps1            # actually junction
```

This creates Windows directory junctions in `projects/`. The pointer READMEs above are preserved (junctions only get added as siblings).

## Pushing to GitHub

**Single repo (Sanctum):** double-click `C:\Users\Zonia\Desktop\Push-Sanctum-To-GitHub.bat`.

**All Sinister repos (dry-run):** double-click `C:\Users\Zonia\Desktop\Push-All-Sinister.bat`. Reports status per repo. Re-run with `-Live` to actually push (each repo gated by secret-scrub).

Both bats refuse to push if any of:
- `secret-scrub.ps1` finds secrets
- Working tree has untracked files matching `.env`, `credentials.json`, `*.pem`, `*.key`, etc.
- Branch is detached HEAD

## Per-project TODO + delegation tables

Per-project work queues live in the hub at:
- `D:\Sinister\Sinister Skills\01_MEMORY\<project>\TODO.md`
- `D:\Sinister\Sinister Skills\01_MEMORY\<project>\NEXT.md`

Cross-project orchestration happens via `sinister-bus.delegate_to agent_name=<project>`.
