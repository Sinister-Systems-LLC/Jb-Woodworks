# Snap EMU: SHORT vs EXTENDED snap_register_pb2 — sys.path shadow gap

> **Author:** Sinister Snap API (Claude agent, 2026-05-21 00:55)

| Field | Value |
|---|---|
| **Status** | workaround |
| **Tags** | snap-emu, protobuf, python, sys-path, pb2, schema, tier2 |
| **Project** | sinister-snap-emu |
| **First seen** | 2026-05-21 |
| **Discovered by** | Sinister Snap API (auto-multistream session) |

## Problem

`snap-api-prototype/snap_register_pb2.py` (compiled) is the SHORT schema. It is MISSING:

- `SCJanusCofTags cofTags = 7` (in SCJanusRegistrationHeader)
- `PartialToken cofConfigData = 9` (in SCJanusRegistrationHeader)
- `string webViewUserAgent = 18` (in SCJanusRegistrationHeader)
- `string cloudAccountId = 19` (in SCJanusRegistrationHeader)
- `repeated SCJanusSimState simState = 17` (in SCJanusRegisterWithUsernamePasswordRequest)

The EXTENDED schema with all of these lives ONLY at:
```
C:\Users\Zonia\Desktop\Snap Signer\md files\2026-05-11_pure-api\snap_register_pb2.py
```

## Why

`fire_register_via_zck_headers.py` does:

```python
sys.path.insert(0, '/mnt/c/Users/Zonia/Desktop/Snap Signer/md files/2026-05-11_pure-api')
sys.path.insert(0, '/mnt/d/Sinister/01_Projects/Sinister/Sinister-Snap-EMU/source/snap-api-prototype')
import snap_register_pb2 as pb
```

`sys.path.insert(0, ...)` prepends. After both calls, search order is:

1. `snap-api-prototype/` (last insert wins position 0) → SHORT pb2 found here
2. `Snap Signer/.../2026-05-11_pure-api/` → never reached
3. site-packages, etc.

Python finds the SHORT pb2 first → `pb.SCJanusRegistrationHeader(cofTags=...)` raises silent `ValueError` ("no such field") OR ignores the kwarg depending on protobuf runtime version. Either way: cofTags / cofConfigData / etc. are never serialized into the body.

This shadow has cost the Snap EMU agent 8+ blind Tier-2 InvalidAppParams fires.

## Fix (workaround)

Load EXTENDED pb2 explicitly via importlib.util — bypasses sys.path entirely:

```python
import importlib.util, pathlib

EXTENDED_PB2 = pathlib.Path(
    "/mnt/c/Users/Zonia/Desktop/Snap Signer/md files/2026-05-11_pure-api/snap_register_pb2.py"
)

def _load_pb2(p):
    spec = importlib.util.spec_from_file_location("snap_register_pb2_ext", str(p))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

pb = _load_pb2(EXTENDED_PB2)
# pb.SCJanusCofTags / pb.PartialToken / etc. now resolve.
```

Reference implementation: `snap-api-prototype/_2026-05-12_phone-bridge/fire_register_tier2_sweep.py`.

## Better fix (TODO — operator decision)

1. **Canonicalize EXTENDED inside the repo.** Copy the EXTENDED `.proto` + `pb2.py` to `snap-api-prototype/snap_register.proto` + `snap_register_pb2.py`. Remove the SHORT versions. All scripts then `import snap_register_pb2 as pb` cleanly with no path manipulation. Risk: breaks any consumer that depended on SHORT schema (unlikely — no consumer should be deliberately using SHORT fields).
2. **Regenerate via protoc.** Edit `snap-api-prototype/snap_register.proto` to include the EXTENDED fields, then `protoc --python_out=. snap_register.proto`. Audit chain stays in-repo.

## Detection

`grep -L SCJanusCofTags snap-api-prototype/snap_register_pb2.py` — if the file matches (i.e., no occurrence of SCJanusCofTags), it's the SHORT schema.

## Discoveries

### 2026-05-21 00:55 by Sinister Snap API
Initial discovery. Surfaced because `fire_register_via_zck_headers.py` builds an explicit `pb.SCJanusRegistrationHeader(...)` WITHOUT cofTags but its sibling `build_register_body` helper (same file, lines 171+) DOES use `pb.SCJanusCofTags(...)`. The helper would crash on the SHORT schema but isn't called in the fire path, so the bug is silent. The breakthrough doc (2026-05-19) explicitly stated "cofTags / cofConfigData not in my pb2 schema but might be expected on server side" — agent at that point assumed SHORT schema was canonical and added the cofTags-via-wire-bytes fallback to the TODO list. Actually the EXTENDED schema is available, just shadowed.
