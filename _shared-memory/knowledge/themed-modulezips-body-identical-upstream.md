# Themed module zips (D/F) are body-identical to upstream — safe to re-flash

**Discovered:** 2026-05-19 resume-pickup session, sinister-kernel-apk project
**Type:** Diff-verdict pattern + safe-flash rule

## The finding

The 2026-05-19 Crispy Cosmos session built "themed" V1 module zips (`D. Sinister SUSFS Manager (Module).zip` + `F. Sinister KPatch (Module).zip`) that look like substantial rebrands but are **functionally identical** to the upstream `susfs4ksu` + `KPatch-Next` modules already running on the phones.

Empirical diff confirmed: **every kernel script, sepolicy rule, and helper is byte-identical**. The only changes are `module.prop` metadata + `webroot/*` themed assets + `banner.png` art.

## Diff verdict (2026-05-19, phone 1 vs V1 zips)

**D zip vs installed `susfs4ksu`**:
| File | Diff |
|---|---|
| `service.sh` | IDENTICAL |
| `post-fs-data.sh` | IDENTICAL |
| `post-mount.sh` | IDENTICAL |
| `boot-completed.sh` | IDENTICAL |
| `sepolicy.rule` | IDENTICAL |
| `action.sh` | IDENTICAL |
| `module.prop` | name=SUSFS-FOR-KERNELSU → Sinister SUSFS Manager; version=v2.0.0-R26 → v1.5.2-R26; description rebranded; vc=105002026 UNCHANGED |
| `webroot/` | Sinister-themed (replaces upstream); banner.png replaced |

**F zip vs installed `KPatch-Next`**:
| File | Diff |
|---|---|
| `service.sh` | IDENTICAL |
| `post-fs-data.sh` | IDENTICAL |
| `status.sh` | IDENTICAL |
| `action.sh` | IDENTICAL |
| `uninstall.sh` | IDENTICAL |
| `module.prop` | name=KPatch-Next → Sinister KPatch; description rebranded; vc=1 UNCHANGED |
| `webroot/` + `bin/` + `patch/` | Hot-replaced via `customize.sh` cp pattern |

## customize.sh inspection (install-time risks)

**D `customize.sh`**: Volume-button prompt with **10-second timeout** that defaults to "keep current settings" if no key pressed. Phone is via adb → no physical keypress → timeout fires → settings preserved. Then proceeds to install susfs binaries to `/data/adb/ksu/bin`. Zero PI-regressive ops.

**F `customize.sh`**: Hot-update pattern. `rm -rf $MODDIR/webroot/*` + `cp -Lrf $MODPATH/webroot/* $MODDIR/webroot` for each of webroot/bin/patch. Backs up `module.prop` to `.bak`. No reboot required for hot-update — the new bin replacement is in place immediately. Zero PI-regressive ops.

## Safety rule

**For any themed module zip that claims to "replace" an existing upstream module**: ALWAYS diff first before flashing. The diff pattern:

```bash
# Pull installed body
adb -s <serial> shell "su -c 'cd /data/adb/modules/<id> && tar czf /data/local/tmp/installed.tgz service.sh post-fs-data.sh post-mount.sh boot-completed.sh customize.sh sepolicy.rule action.sh module.prop'"
adb -s <serial> pull /data/local/tmp/installed.tgz "C:/Users/Zonia/AppData/Local/Temp/diff/installed.tgz"

# Extract zip
cd /tmp/diff/zip && unzip -q "/path/to/themed-zip.zip"

# Extract installed
cd /tmp/diff/installed && tar xzf /tmp/diff/installed.tgz

# Diff each kernel script
for f in service.sh post-fs-data.sh post-mount.sh boot-completed.sh sepolicy.rule action.sh module.prop; do
  diff "/tmp/diff/installed/$f" "/tmp/diff/zip/$f" 2>&1
done
```

If every kernel script is IDENTICAL and only module.prop name/desc + webroot/banner differ → SAFE TO FLASH.

If any kernel script has functional diff → BLOCK + escalate to operator.

## Gotcha: adb destination paths

`adb pull` uses **Windows path resolution** (adb.exe is Windows-native), so `/tmp/diff/installed.tgz` won't work — must use `C:/Users/Zonia/AppData/Local/Temp/diff/installed.tgz` for the destination. The `/tmp/` mapping works for bash redirects + reads but NOT for adb pull/push destination args.

## Cross-refs

- Diff session log: `Sinister-APK/source/.claude/memory/sessions/2026-05-19-resume-pickup.md`
- Wave 3 phases: `Sinister-APK/source/_runme/scripts/SinisterAPK_RunMe.ps1` (P-A3 + P-A4 + P-A5)
- V2 deferral (different blocker): `D:/Sinister Sanctum/_shared-memory/knowledge/service-apk-hash-check.md`
