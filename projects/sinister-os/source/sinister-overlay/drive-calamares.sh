#!/usr/bin/env bash
# Author: RKOJ-ELENO :: 2026-05-24
# Drive the Calamares unattended install from inside the CachyOS live VM.
# Push to guest via VBoxManage guestcontrol copyto then execute.
set -euo pipefail

echo "=== drive-calamares.sh start ==="
date -u +%Y-%m-%dT%H:%M:%SZ

# Check overlay landed
if [[ ! -f /tmp/sinister-overlay/apply-calamares-preset.sh ]]; then
    echo "FATAL: /tmp/sinister-overlay/apply-calamares-preset.sh not found"
    echo "Overlay should have been pushed by the prior live-apply agent. Re-push:"
    echo "  tar czf /tmp/sinister-overlay.tar.gz -C source/ sinister-overlay/"
    echo "  VBoxManage guestcontrol ... copyto /tmp/sinister-overlay.tar.gz /tmp/"
    exit 2
fi

# Check Calamares state
RUNNING_PIDS=$(pgrep -af calamares 2>/dev/null | grep -v 'drive-calamares' | awk '{print $1}' || true)
if [[ -n "$RUNNING_PIDS" ]]; then
    echo "Calamares already running, PIDs: $RUNNING_PIDS"
    echo "Operator's interactive Calamares is in foreground. Killing it to relaunch with auto-preset."
    for pid in $RUNNING_PIDS; do
        sudo -n kill -TERM "$pid" 2>&1 || true
    done
    sleep 3
    REMAINING=$(pgrep -af calamares 2>/dev/null | grep -v 'drive-calamares' || true)
    if [[ -n "$REMAINING" ]]; then
        echo "Calamares didn't exit gracefully, force-killing:"
        sudo -n pkill -KILL calamares 2>&1 || true
        sleep 2
    fi
fi

# Apply the preset (copies our config to /etc/calamares/)
echo "=== Applying Calamares preset (Sinister auto-install) ==="
cd /tmp/sinister-overlay
sudo -n bash apply-calamares-preset.sh 2>&1 || {
    echo "WARN: apply-calamares-preset.sh exited non-zero — checking what landed"
    ls -la /etc/calamares/settings.conf /etc/calamares/modules/ 2>&1 | head -20
}

# Verify preset is in place
if [[ ! -f /etc/calamares/settings.conf ]] || ! grep -q "sinister" /etc/calamares/settings.conf 2>/dev/null; then
    echo "WARN: /etc/calamares/settings.conf does not look like our preset"
    head -10 /etc/calamares/settings.conf 2>&1
fi

# Launch Calamares fresh (auto mode kicks in from the preset)
echo "=== Launching Calamares with Sinister auto-preset ==="
# Pull DBus envvars from the active graphical session so calamares can talk to KWin
USER_PID=$(pgrep -u liveuser -x plasmashell | head -1 || pgrep -u liveuser -x kwin_x11 | head -1 || pgrep -u liveuser -x kwin_wayland | head -1 || true)
if [[ -n "$USER_PID" ]]; then
    echo "Importing env from PID $USER_PID"
    while IFS='=' read -r -d '' k v; do
        case "$k" in
            DISPLAY|WAYLAND_DISPLAY|XDG_RUNTIME_DIR|DBUS_SESSION_BUS_ADDRESS|XAUTHORITY)
                export "$k=$v"
                echo "  $k=$v"
                ;;
        esac
    done < "/proc/$USER_PID/environ"
fi

# Calamares needs to run as root for the install
echo "Starting calamares in background (logs -> /tmp/calamares-auto.log)"
sudo -n -E nohup calamares > /tmp/calamares-auto.log 2>&1 &
NEW_PID=$!
echo "Calamares PID: $NEW_PID"
sleep 5
if ps -p "$NEW_PID" >/dev/null; then
    echo "Calamares running. Monitor with: tail -f /tmp/calamares-auto.log"
    echo "Auto-install proceeds: disk wipe -> partition -> base copy -> bootloader -> finalize -> 10s reboot"
else
    echo "Calamares failed to start. Last log:"
    tail -30 /tmp/calamares-auto.log 2>&1
    exit 3
fi
echo "=== drive-calamares.sh done ==="
