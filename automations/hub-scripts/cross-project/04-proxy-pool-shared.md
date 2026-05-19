# Cross-project: shared proxy pool

## Problem

`Tiktok Proxy].txt` (Desktop root), Library-of-JOKR/infrastructure/, Sinister TikTok EMU, Sinister Snap EMU, LetsText 2.0 backend all reference proxy pools. Each maintains its own copy / config.

The canonical SinisterSOCKS pool config (per Snap Signer Policy memory):
- Upstream: `proxyyy.txt` (sinister.services:20006, creds 2K9SGQBR:2K9SGQBR, rotation token `c7482e62…`)
- Local bridge: `10.0.2.2:8888` (sinister_proxy_bridge.py)
- Carrier exit: T-Mobile USA 174.x.x.x

## Proposed solution

Single source of truth:
```
D:\Sinister\Sinister Skills\09_REFERENCE\proxy-pool.json
```

Schema:
```json
{
  "active_pool": "sinistersocks-t-mobile-usa",
  "pools": {
    "sinistersocks-t-mobile-usa": {
      "upstream": "sinister.services:20006",
      "creds_file": "proxyyy.txt",
      "rotation_url": "http://sinister.services/selling/rotate?token=c7482e62...",
      "carrier": "T-Mobile",
      "region": "USA",
      "exit_pattern": "174.x.x.x"
    }
  },
  "local_bridge": {
    "host": "10.0.2.2",
    "port": 8888,
    "script": "sinister_proxy_bridge.py"
  }
}
```

Every consumer reads from here. Each project's MCP exposes a `get_proxy()` tool that hits this canonical path.

## Note

Per Snap Signer 2026-05-17 entry: T-Mobile USA pool empirically downgraded (Path 1 wall). Need DIFFERENT carrier pool. Future config rows: AT&T, Verizon, MetroPCS, etc.

## Status

Proposed. Pre-requisite for Step 4 of the cross-project unified pool.

## See also

- `09_REFERENCE/proxies.md` — consolidated proxy doc (TBD in Step 9)
- `02_MD_ARCHIVE/_index/by-keyword/proxy.md` — keyword shard with refs across all projects
