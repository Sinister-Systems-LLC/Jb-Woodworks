#!/usr/bin/env bash
export PATH="/usr/bin:/bin:/usr/local/bin:$PATH"
cd " '/' + $args[0].Groups[1].Value.ToLower() /Sinister Sanctum" || { echo '[FAIL] could not cd to sanctum root'; read _; exit 1; }
printf '\n'
printf '  ============================================================\n'
printf '  Sinister Setup Wizard -- onboarding %s\n' "z0nian"
printf '  ============================================================\n'
printf '\n'
printf '  Spawning Claude with --dangerously-skip-permissions...\n'
printf '\n'
claude --dangerously-skip-permissions 'You are the Sinister Setup Wizard. Your task is to onboard z0nian to the Sinister Sanctum fleet. Read D:\Sinister Sanctum\docs\LEO-SETUP.md and D:\Sinister Sanctum\docs\LEO-VAULT-SETUP.md first so you know the full bring-up surface. Then walk z0nian through this checklist one item per turn, asking confirmation at each gate:

 1) Verify Anthropic OAuth login is working (claude CLI logged in).
 2) Run automations\eve-first-run-check.ps1 -Format text and surface any remaining gaps.
 3) Set git config user.name='\''z0nian'\'' and ask for their git user.email, set it.
 4) Create their working branch agent/z0nian/onboard-bring-up.
 5) Offer Tailscale install + vault join (point at docs\LEO-VAULT-SETUP.md). Optional; ok to defer.
 6) Smoke test: spawn a tiny shell command (e.g. printf '\''hello'\'') and verify it runs.
 7) Create z0nian'\''s first heartbeat at _shared-memory\heartbeats\z0nian.json with agent='\''z0nian'\'' + ts_utc + status='\''onboarding'\''.
 8) Append a 5-line onboarding report to _shared-memory\setup\z0nian-onboarding-report-<utc>.md (create if missing) summarising what worked + what is pending.

Loop policy: loop=on. Ship one checklist item per turn; do not delete or kill anything without explicit '\''z0nian'\'' confirmation; ask for permission before any write outside _shared-memory\setup\ and _shared-memory\heartbeats\. When all items are DONE, write a final '\''BRING-UP COMPLETE'\'' summary and ScheduleWakeup is not needed -- just end the turn cleanly. If z0nian asks to abort at any point, write whatever was completed to the onboarding report and exit gracefully.'
ec=$?
printf '\n'
if [ $ec -eq 0 ]; then
    printf '[OK] wizard session ended cleanly.\n'
else
    printf '[INFO] wizard exited with code %s.\n' "$ec"
fi
printf 'Press Enter to close this window.\n'
read _