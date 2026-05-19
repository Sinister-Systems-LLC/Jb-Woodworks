# sinister-emulator-bundle â€” pointer + integration notes

This directory is a Sanctum-side **pointer** to the Sinister Emulator Bundle. Sanctum does NOT vendor the source â€” it lives at its own canonical D: drive path.

The Bundle is the **AOSP emulator track** â€” companion to Snap-EMU's API track. UI reactive looper (uiautomator classify + tap) that drives cvd-1 Snap APK through the signup flow, plus operator one-clickers + AOSP patches + keybox + `host_tools/proxy_bridge.py`.

## Canonical locations

| What | Where |
|---|---|
| **Canonical source (D: drive)** | `D:\Sinister\01_Projects\Sinister\Sinister-Emulator-Bundle\source\` |
| **Legacy source (Desktop, 363 MB frozen backup)** | `C:\Users\Zonia\Desktop\Sinister_Emulator_Bundle\` |
| **GitHub repo** | _(none â€” bundle is an internal/auxiliary project, not in Sinister LLC public-repo scope)_ |
| **Hub memory** | _(no hub memory entry â€” minor project; referenced from Snap-EMU's g.md)_ |
| **Per-project agent** | _(currently no dedicated agent; touched by snap-signer when needed)_ |

## Current state (2026-05-19 PM late)

- **HOLDING** per 2026-05-06 PM3 build halt (AOSP rebuild gate)
- 362.78 MB on D: (full copy from Desktop, byte-identical content)
- Migration log: `D:\Sinister\01_Projects\Sinister\Sinister-Emulator-Bundle\migration-2026-05-19.log`
- 11 top-level entries: 3 one-click bats (`0_DEPLOY_TO_CVD.bat`, `1_RUN_SIGNUP_LOOPER.bat`, `2_VERIFY_CVD_STATE.bat`) + 4 docs (ARCHITECTURE.md, README.md, RUNBOOK.md, TROUBLESHOOTING.md) + 4 subdirs (docs/, host_tools/, keybox/, patches/, scripts/)
- Companion to Snap-EMU (which is the **API track**); this is the **UI track** for the same cvd-1 + Snap APK target

## How Sanctum integrates with the Bundle

Sanctum bots can **READ** Bundle state via:
- `librarian.recall query=...` against this README + the cross-ref in Snap-EMU's `g.md`
- `researcher.summarize_url` for any deployment endpoints documented in `RUNBOOK.md`
- `auditor.run` (if pointed at the source via param)

Sanctum bots **must NEVER WRITE** to Bundle source. When the Bundle resumes from HOLDING, a dedicated agent lane will be assigned per `PARALLEL-AGENT-COORDINATION.md`.

## Relationship to Snap-EMU

The Bundle and Snap-EMU target the same cvd-1 Snap APK from two angles:

| Project | Approach | Lane owner |
|---|---|---|
| Sinister-Snap-EMU | Pure-API: gRPC RegisterWithUsernamePassword + Frida-attached signing oracle (`kiib.zck.g/h`) | snap-signer |
| Sinister-Emulator-Bundle | UI-reactive: uiautomator classify + tap loop driving Snap UI from inside cvd-1 | _(holding)_ |

Both share: cvd-1 instance, Yurikey51_ECDSA keybox (canonical), SinisterSOCKS proxy bridge :8888, RKA daemon @ :59450.

## Optional junction

Run `migrate-projects.ps1` from `D:\Sinister Sanctum\automations\` to materialize `source/` as a junction here (Bundle is in the script's project list per line 35).

## Pushing to GitHub

Bundle is **not currently in the Sinister LLC GitHub scope**. If operator decides to push it later:

```powershell
cd 'D:\Sinister\01_Projects\Sinister\Sinister-Emulator-Bundle\source'
& 'D:\Sinister Sanctum\automations\git-toolkit.ps1' init .
& 'D:\Sinister Sanctum\automations\git-toolkit.ps1' safe-push .
```

## Excluded from any push (operator-private)

- `keybox/` â€” sensitive keybox material; never push
- `.env`, anything matching `secret-redaction-policy.md`
