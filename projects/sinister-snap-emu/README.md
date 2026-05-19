# sinister-snap-emu â€” pointer + integration notes

This directory is a Sanctum-side **pointer** to the Snap EMU project. Sanctum does NOT vendor the source â€” it lives in its own GitHub repo with its own per-project Claude session.

## Canonical locations

| What | Where |
|---|---|
| **MAIN WORKING DIR (push origin)** | `D:\Sinister Sanctum\projects\sinister-snap-emu\` ← **this folder** |
| **Push bat (one-click)** | `D:\Sinister Sanctum\projects\sinister-snap-emu\PUSH-TO-GITHUB.bat` |
| **Working source (junctioned)** | `source\` → `D:\Sinister\01_Projects\Sinister\Sinister-Snap-EMU\source\` |
| **Underlying real copy** | `D:\Sinister\01_Projects\Sinister\Sinister-Snap-EMU\source\` (1.2 GB, 6080 files, .git/ history) |
| **Legacy source (Desktop, frozen 2.0 GB backup)** | `C:\Users\Zonia\Desktop\Sinister Snap EMU.API\` (untouched) |
| **GitHub repo (NEW)** | `https://github.com/Sinister-Systems-LLC/Sinister-Snap-EMU-Snap-API-` ← **push target** |
| **Old GitHub repo (legacy)** | `https://github.com/Sinister-Systems-LLC/Sinister-Snap-API-EMU` (initial commit 628163a, replaced by NEW) |
| **Hub memory (operator-private)** | `D:\Sinister\Sinister Skills\01_MEMORY\sinister-snap-emu\` |
| **Per-project agent** | `snap-signer` (lane owner — only this agent edits source) |

**Operator-locked 2026-05-19 PM late:** this Sanctum directory is the canonical "main working dir" for the Snap-EMU project. All future GitHub pushes originate from `D:\Sinister Sanctum\projects\sinister-snap-emu\source\` (which is a transparent junction — same `.git/` inode as the underlying real copy, so commits/pushes are byte-identical to operating on the canonical D: path).

## Current state (snap-signer agent â€” 2026-05-19 PM late)

- HEAD: `f9f5736` ("PM10-G - TikTok agent playbook reviewed; kiib.zck.e input capture attempts")
- 65 commits in history, 8 commits ahead of origin (waiting for operator push timing)
- Working tree on D: post-migration: **1.2 GB** (cleaned 500 MB of regenerable junk from the 1.86 GB Desktop snapshot; details in `source/living-mds/MIGRATION-2026-05-19.md`)
- Frozen Desktop backup preserved (2.0 GB untouched) for rollback if needed
- 6079 files total in D: source (= 6075 from Desktop + 4 intentional additions: `BOT-NETWORK.md`, `MIGRATION-2026-05-19.md`, mirrored `Yurikey51_ECDSA.xml` + `proxyyy.txt` in `wsl-config/`)
- Bot network access: 7 MCPs (160+ tools) + 8 specialist agents reachable from inside the project â€” see `source/BOT-NETWORK.md` for cold-start reference
- 11 memory partition files at `source/.claude/memory/` (R/s/t/d/p/c/b/g + canon-index + resume-point + operator-todo) â€” R.md + s.md + g.md now carry MCP/bot-network awareness for cold-start reads

## Forward path (per current empirical state)

**Wall:** `/snap.security.ArgosService/GetTokens` returns `grpc=16 unauthorized` with our `kiib.zck.g/h` att headers. SS03 (cert-embedding) has been BYPASSED via `kiib.zck.g + h` direct-call. Current verdict on Register fires: SS06 (stale Argos in PSf.12). Need fresh opaque tokens from a proper GetTokens warmup.

**Java-layer breakthrough (tonight's session):**
- Located `com.snap.security.snaptoken.SnapTokenApiGatewayHttpInterface.fetchSnapAccessTokens(KJh) â†’ io.reactivex.rxjava3.core.Single` â€” THE method that mints opaque tokens.
- Hooked `com.snapchat.client.grpc.UnifiedGrpcService.unaryCall(String, ByteBuffer, CallOptionsBuilder, UnaryEventHandler)` â€” gRPC dispatcher (3 live `$CppProxy` instances).
- Captured 249 HttpRequest events across 2 windows (URLs: app-analytics-v2, /bq/network_ping, /v1/metrics â€” no GetTokens during Steps 1-4; fires only at Step 5 final submit).
- UA corrected to `Snapchat/13.88.1.0 (Pixel 6a; Android 14#eng.zonia.20260515.165547#34; gzip) V/MUSHROOM`.
- Step 4 UI Continue button taps silently rejected (Patch #9 SinisterInput confirmed real TOUCHSCREEN dev=4 injection on cvd-1) â€” Snap uses Jetpack Compose UI; `View.performClick()` workaround failed.

**Next session move:**
1. `find_snaptoken_impl.py` (written, not yet run) â€” locate concrete impl of `SnapTokenApiGatewayHttpInterface`
2. Invoke `fetchSnapAccessTokens(KJh)` directly via Frida reflection
3. Embed minted opaque tokens in `PSf.12` of Register body â†’ expected verdict shift SS06 â†’ sc=1 SUCCESS / sc=3 challenge

Full empirical chain: `source/living-mds/SESSION-LOG-2026-05-19-EVE.md`. Cross-port findings: `source/living-mds/TT-CROSS-PORT-PATCH9-OVERLAY-2026-05-19.md`.

## How Sanctum integrates with Snap EMU

Sanctum bots can **READ** Snap EMU state via:
- `researcher.summarize_url url=<deployed-endpoint>` for live health checks
- `librarian.recall query=...` against `01_MEMORY/sinister-snap-emu/`
- `auditor.run` (if pointed at the source via param)

Sanctum bots **must NEVER WRITE** to Snap EMU source. That's the snap-signer agent's lane (per `PARALLEL-AGENT-COORDINATION.md`).

## Pushing Snap EMU to GitHub

When the operator gives the go-ahead:

```powershell
cd 'D:\Sinister\01_Projects\Sinister\Sinister-Snap-EMU\source'
& 'D:\Sinister Sanctum\automations\git-toolkit.ps1' safe-push .   # secret-scrub gate first
```

Or use the multi-repo bat: `C:\Users\Zonia\Desktop\Push-All-Sinister.bat -Live` (dry-run by default).

## Excluded from any push (operator-private)

- `.env`, `credentials.json`, anything matching `secret-redaction-policy.md`
- `living-mds/` may contain operator-only notes â€” review before push
- Yurikey roster / keybox material â€” never push
