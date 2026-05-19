# Cross-project: unified device state

## Problem

Sinister APK, Sinister RKA, Sinister-Panel, Kernel-SU-Setup, and Snap Signer all reference "device pin" / "Pixel 6 Pro" / "Yurikey51" state — same information, redundantly maintained.

Concrete example: phone serial `2A061JEGR09301` is referenced in:
- `Snap Signer/SESSION-START.md` Policy 6, 8, 14.2, 31
- `Sinister-Panel/SESSION-START.md`
- `Kernel-SU-Setup/Sinister-Detector/SESSION-START.md`
- `Sinister Library Of Alexandria/SESSION-START.md`
- 50+ bat files across all projects

## Proposed solution

Single source of truth at:
```
D:\Sinister\Sinister Skills\09_REFERENCE\device-state.json
```

Schema:
```json
{
  "phones": {
    "P1": {"serial": "2A061JEGR09301", "model": "Pixel 6a", "rka_token": "66d4fb0b…", "active": true},
    "P2": {"serial": "26031JEGR17598", "model": "Pixel 6a", "rka_token": "3782e97a…", "active": true}
  },
  "active_phone_pin": "P1",
  "current_keybox": "Yurikey51_ECDSA.xml",
  "keybox_expiry": "2026-05-24",
  "rka_vps": "95.216.240.227",
  "rka_keybox_port": 59348,
  "rka_command_port": 59349,
  "panel_url": "https://snap.sinijkr.com/"
}
```

Every bat / script / MCP server reads from this. Hub `refresh.ps1` regenerates the JSON from per-project SESSION-START.md authoritative values (current rule: Snap Signer is canonical).

## Migration path

1. Author `09_REFERENCE/device-state.json`.
2. Update `refresh.ps1` to emit it from per-project sources.
3. Document in each project capsule: "device state pulled from hub `09_REFERENCE/device-state.json`".
4. New bats reference: `for /f %%i in ('jq -r .active_phone_pin D:\Sinister\Sinister Skills\09_REFERENCE\device-state.json') do set PHONE=%%i`.
5. Existing bats migrate on next edit (not a one-shot rewrite).

## Status

Proposed. Not yet implemented. Operator approval needed.

## See also

- `09_REFERENCE/device-state.json` (TBD)
- `09_REFERENCE/yurikey-roster.md`
- Snap Signer Policy 14.2 (single active phone)
