#!/bin/bash
# Author: RKOJ-ELENO :: 2026-05-25
# Beta helper batch stage+commit+push with retry on lock contention.
# Args: batch-id msg-file pathspec1 pathspec2 ...
set +e
cd "D:/Sinister Sanctum" || exit 9
BATCH=$1; shift
MSG=$1; shift
echo "BATCH=$BATCH MSG=$MSG PATHS=$*"
for attempt in $(seq 1 40); do
  if [ -f .git/index.lock ]; then
    age=$(powershell -NoProfile -Command "((Get-Date) - (Get-Item 'D:\Sinister Sanctum\.git\index.lock').LastWriteTime).TotalSeconds" 2>/dev/null | tr -d '\r\n ')
    echo "attempt=$attempt lock-held age=${age}s waiting 15s"
    # Stale-lock recovery: > 120s + no live git proc = orphan, remove
    if [ -n "$age" ] && awk -v a="$age" 'BEGIN{exit !(a>120)}'; then
      echo "attempt=$attempt removing-orphan-lock"
      rm -f .git/index.lock 2>/dev/null
    fi
    sleep 15
    continue
  fi
  out=$(git -c core.fsmonitor=false add "$@" 2>&1)
  rc=$?
  if [ $rc -ne 0 ]; then
    echo "attempt=$attempt add-failed rc=$rc: $(echo "$out" | head -1)"
    sleep 8
    continue
  fi
  staged=$(git -c core.fsmonitor=false diff --cached --name-only 2>/dev/null | wc -l)
  if [ "$staged" -eq 0 ]; then
    echo "attempt=$attempt nothing-staged (sibling raced), retrying"
    sleep 5
    continue
  fi
  cout=$(git -c core.fsmonitor=false commit -F "$MSG" 2>&1)
  crc=$?
  if [ $crc -ne 0 ]; then
    if echo "$cout" | grep -qE "nothing to commit"; then
      echo "attempt=$attempt nothing-to-commit-edge"
      exit 0
    fi
    echo "attempt=$attempt commit-failed rc=$crc: $(echo "$cout" | head -1)"
    sleep 5
    continue
  fi
  echo "COMMITTED $BATCH: $(echo "$cout" | head -1)"
  pout=$(git push origin HEAD 2>&1)
  prc=$?
  if [ $prc -ne 0 ]; then
    echo "push-failed rc=$prc: $(echo "$pout" | head -1)"
    exit 11
  fi
  echo "PUSHED $BATCH OK"
  exit 0
done
echo "EXHAUSTED retries for $BATCH"
exit 99
