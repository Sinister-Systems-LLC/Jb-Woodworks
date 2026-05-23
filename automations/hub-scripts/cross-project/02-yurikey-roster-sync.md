# Cross-project: Yurikey roster sync

## Problem

`Yurikey51_ECDSA.xml` lives at `C:\Users\Zonia\Yurikey51_ECDSA.xml` and is referenced by Snap Signer, RKA, Panel, Kernel-SU. Operator manually rotates the file every ~30-60 days; updates don't propagate consistently.

## Proposed solution

Nightly cron via `/schedule`:

```
0 3 * * *  refresh.ps1 -Section 09 -SubSection yurikey-roster
```

Job:
1. Compute sha256 of `C:\Users\Zonia\Yurikey51*.xml` (any variant).
2. Diff against `09_REFERENCE/yurikey-roster.md` last entry.
3. If changed:
   - Append new row to `yurikey-roster.md` with sha + mtime + filename
   - Update `_manifest.json` `current_keybox` field
   - Update `device-state.json` if active keybox changed
   - Emit digest entry: "Yurikey rotated from X to Y on <date>"

## Watch for expiry

`09_REFERENCE/yurikey-roster.md` includes computed `days_until_expiry`. Daily-digest skill reads this; warns at ≤ 14 days, critical at ≤ 7 days, blocker at ≤ 0.

## Status

Proposed. Critical for the 2026-05-23 Yurikey52 deadline.

## See also

- `09_REFERENCE/yurikey-roster.md`
- `05_SKILLS/proposed/07-daily-digest.md`
