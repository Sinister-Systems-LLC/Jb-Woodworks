# 08_AUTOMATIONS — cross-project workflows + glue scripts

## Layout

```
08_AUTOMATIONS/
  README.md
  cross-project/
    01-unified-device-state.md      # single device-state.json
    02-yurikey-roster-sync.md       # nightly Yurikey diff
    03-session-start-aggregator.md  # ALL-SESSION-STARTS.md (✅ implemented)
    04-proxy-pool-shared.md         # single proxy-pool.json
    05-mcp-handoff-bus.md           # cross-server replay bus
  glue-scripts/
    collect-all-session-starts.ps1  # (pending — extracted from Step 1 logic)
    collect-all-md.ps1              # (pending — extracted from Step 2 logic)
    diff-ua-graphs.ps1              # (pending — Step 6 powering)
    emit-daily-digest.ps1           # (pending — daily-digest skill backend)
  inventory/
    existing-bats.tsv               # 250+ bats across 9 projects
    existing-ps1.tsv                # 70+ ps1 across 9 projects
```

## Bat inventory by project

(Counts from Step 8 walk)

| Project | bats | ps1 |
|---|---|---|
| snap-signer | 69 | 25 |
| library-of-alexandria | 80 | 33 |
| sinister-tiktok-emu | 16 | 1 |
| sinister-snap-emu | 18 | 9 |
| sinister-bumble-emu | 5 | 0 |
| sinister-panel | 26 | 0 |
| kernel-su-setup | 34 | 2 |
| letstext | 0 | 1 |
| jokr-global | 0 | 0 |
| Desktop root (loose) | 2 | 0 |

## Refresh

```powershell
.\refresh.ps1 -Section 08
```

Re-walks all projects for `*.bat` / `*.ps1`. Hand-edited `cross-project/` MDs are preserved.
