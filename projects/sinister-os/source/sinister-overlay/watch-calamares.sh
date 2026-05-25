#!/usr/bin/env bash
# Author: RKOJ-ELENO :: 2026-05-24
# Quick Calamares status probe — used as a guestcontrol one-shot.
set -u
echo "=== process ==="
pgrep -af calamares | grep -v 'watch-calamares' || echo "NOT RUNNING"
echo "=== /tmp/calamares-auto.log tail ==="
tail -30 /tmp/calamares-auto.log 2>&1 || echo "no log yet"
echo "=== settings sanity check ==="
grep -E "disable-cancel|disable-cancel-during-exec|sequence:" /etc/calamares/settings.conf 2>&1 | head -10
echo "=== loaded modules count ==="
ls /etc/calamares/modules/ 2>&1 | wc -l
echo "=== current calamares stage from log ==="
grep -E "Job ID|Starting|Done" /tmp/calamares-auto.log 2>&1 | tail -10 || true
