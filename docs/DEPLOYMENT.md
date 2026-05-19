# Sinister LLC — deployment (per-project)

Each project owns its own deploy. This doc indexes them + lists the common pre-deploy checklist.

## Pre-deploy checklist (every project)

1. `.\automations\secret-scrub.ps1 -Path projects\<name>` -> must PASS
2. `auditor.run` (in Claude session) -> review findings; resolve any "secret" hits
3. `watcher.scan project=<name>` -> confirm no unexpected drift
4. `custodian.snapshot_now` -> back up before push
5. Per-project deploy (below)
6. Update `01_MEMORY/<name>/SESSION-START.md` with deploy timestamp

## Per-project deploy

| Project | How |
|---|---|
| **sinister-panel** | `Sinister_OneClick_Deploy.bat` (operator-side) -> pushes to Hetzner `/opt/sinister-panel/`, restarts containers. Verify at https://snap.sinijkr.com/ |
| **sinister-rka-good** | `docker compose up -d --build` on Hetzner. Verify health endpoint. Critical: Yurikey51 cert must be current. |
| **snap-signer** | Local-only; runs against the operator's cvd farm. No "deploy" per se. |
| **sinister-snap-emu** | Local-only. Phase 5 builds AOSP image with custom signing-oracle hooks. |
| **sinister-tiktok-emu** | Local-only. Pure-API task #26 is the active path (Frida-spawn route sandbox-blocked). |
| **sinister-bumble-emu** | Local-only. Blocked on APK acquisition; see project TODO. |
| **kernel-su-setup** | `_BUILD-DETECTOR-APK.bat` -> outputs to `_dist/`. Push to phones via Detector flow. |
| **library-of-alexandria** | Static mirror; no deploy. |

## Rollback

Every project's deploy script SHOULD emit a runlog manifest (template at `08_AUTOMATIONS/_runlog.ps1`). If a deploy fails:

```
sinister-bus.runlog_latest <project>-deploy   # find the manifest
sinister-bus.runlog_summary <id>              # one-paragraph rollup
custodian.restore <changed-file> <pre-deploy-ts>   # revert any single file
```

For sinister-panel specifically, the deploy script keeps the previous container image alive — re-tag + restart restores in <30s.

## TL;DR

- **How we won:** Every project has a documented deploy path + the same pre-deploy checklist.
- **What you need to do:**
  - Run the pre-deploy checklist before any push.
  - Use `Sinister_OneClick_Deploy.bat` for the panel today (2 commits queued: `a563c87` + `4bda966`).
