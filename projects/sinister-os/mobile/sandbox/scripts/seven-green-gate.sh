#!/usr/bin/env bash
# seven-green-gate.sh — Gate 2 (anti-brick): 7 consecutive clean cvd boots
# RKOJ-ELENO :: 2026-05-24
#
# Reads the seven-green log + asserts:
#   (a) Top 7 rows are all result=pass
#   (b) All 7 rows share the same src_sha (no rebuilds between)
#   (c) Gate 1 (static grep for fastboot/sideload/heimdall) passes
#   (d) Gate 4 (rollback asset present + hash verified)
#
# If all 4 gates pass, prints "PHYSICAL-ELIGIBLE" + the src_sha + opens a
# physical-flash advisory at sandbox/.physical-flash-advisory.md (operator
# reads, types the flash commands by hand if they choose).

set -euo pipefail

WORKDIR="${SINISTER_CVD_HOME:-$HOME/sinister-cvd}"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
SANDBOX_ROOT="$( cd "$SCRIPT_DIR/.." >/dev/null 2>&1 && pwd )"
LOG="$WORKDIR/seven-green/.seven-green-log.jsonl"
ADVISORY="$SANDBOX_ROOT/.physical-flash-advisory.md"
LOG_PREFIX="[seven-green-gate]"

log()  { echo "${LOG_PREFIX} $*"; }
fail() { echo "${LOG_PREFIX} FAIL: $*" >&2; exit 1; }

[[ -f "$LOG" ]] || fail "no seven-green log at $LOG — run boot-check.sh first"

# ----- Gate 1 (static grep) -----
log "Gate 1: static grep for forbidden physical-device commands"
BANNED=(fastboot sideload heimdall)
for term in "${BANNED[@]}"; do
  if grep -RIniw "$term" "$SANDBOX_ROOT" 2>/dev/null \
       | grep -vE "(README|anti-brick-safety|seven-green-gate|physical-flash-advisory)" \
       >/dev/null; then
    fail "Gate 1 violated — found '$term' in sandbox file:" \
         "$(grep -RIniw "$term" "$SANDBOX_ROOT" | grep -vE "README|anti-brick-safety|seven-green-gate|physical-flash-advisory" | head -5)"
  fi
done

# ----- Gate 2 (consecutive passes + same sha) -----
log "Gate 2: parsing seven-green log"
python3 - "$LOG" <<'PY' || fail "Gate 2 — see python output above"
import json, sys
rows = []
for line in reversed(open(sys.argv[1]).read().splitlines()):
    try: rows.append(json.loads(line))
    except: pass
    if len(rows) == 7: break
if len(rows) < 7:
    print(f"Gate 2 short: only {len(rows)} rows", file=sys.stderr); sys.exit(2)
if not all(r["result"] == "pass" for r in rows):
    print(f"Gate 2 — non-pass row in top 7: {[r['result'] for r in rows]}", file=sys.stderr); sys.exit(3)
shas = {r["src_sha"] for r in rows}
if len(shas) != 1:
    print(f"Gate 2 — multiple src_sha in top 7: {shas}", file=sys.stderr); sys.exit(4)
print(f"Gate 2 OK — src_sha={shas.pop()} (7/7 pass)")
PY

# ----- Gate 4 (rollback asset) -----
log "Gate 4: verifying rollback asset"
bash "$SCRIPT_DIR/verify-rollback-asset.sh" || fail "Gate 4 failed"

# ----- All gates green -----
SHA="$(tail -1 "$LOG" | python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["src_sha"])')"

cat > "$ADVISORY" <<EOF
# Physical-flash advisory — Sinister OS Mobile

> **Generated:** $(date -u +%Y-%m-%dT%H:%M:%SZ)
> **Kernel src_sha:** $SHA
> **Gates passed:** 1 (static grep) · 2 (7-green cvd) · 4 (rollback asset)
> **NOT a script.** This is an advisory the operator reads + executes by hand.

## You are about to flash a kernel artifact to your physical Pixel 6a.

Per anti-brick doctrine, no automation does this for you. The steps below
are the canonical physical-flash sequence — operator types each by hand.

### Pre-flight checklist (operator confirms each)

- [ ] Pixel 6a is plugged into USB-C, screen unlocked
- [ ] Developer options enabled (Settings → System → About → tap Build number 7×)
- [ ] OEM unlocking enabled (Settings → System → Developer options)
- [ ] USB debugging enabled
- [ ] Bootloader unlocked (\`fastboot flashing unlock\` — separate operator-typed step; required once per device)
- [ ] Rollback asset on disk: \$SINISTER_CVD_HOME/rollback/bluejay-stock-boot.img (verified)
- [ ] Current device data backed up (this lane backs up via Sinister Vault if configured)

### The flash sequence (operator types EACH line)

\`\`\`
# 1. Reboot to bootloader
adb reboot bootloader

# 2. Confirm device is in fastboot mode
fastboot devices

# 3. Flash the custom boot.img
fastboot flash boot \$SINISTER_CVD_HOME/builds/out-bluejay/dist/boot.img

# 4. Reboot
fastboot reboot

# 5. Observe device boots to OS
adb wait-for-device
adb shell uname -a
\`\`\`

### Rollback path (if anything goes wrong)

\`\`\`
adb reboot bootloader        # or hold Power+VolDown to enter bootloader
fastboot flash boot \$SINISTER_CVD_HOME/rollback/bluejay-stock-boot.img
fastboot reboot
\`\`\`

### After successful flash

1. Run \`adb shell\` smokes you'd run on cuttlefish (kernel up, /system mounted, keystore present)
2. Log the physical-device serial + observed-uname to \`_shared-memory/PROGRESS/Sinister OS Mobile.md\`
3. Mark kernel src_sha=$SHA as \`acceptance-tested\` on physical device

## What this advisory is NOT

- Not a script. There is no executable here.
- Not authorisation to proceed — operator decides, by reading + understanding.
- Not a guarantee. The sandbox gates raise confidence; the physical world is the operator's call.
EOF

log ""
log "==============================================================="
log "PHYSICAL-ELIGIBLE — all 3 gates green for src_sha=$SHA"
log "==============================================================="
log ""
log "Advisory written: $ADVISORY"
log "Read it. The flash sequence is operator-typed-by-hand only."
