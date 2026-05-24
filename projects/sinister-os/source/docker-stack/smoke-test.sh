#!/usr/bin/env bash
# smoke-test.sh — verify every Sinister Mesh service is healthy
# Author: RKOJ-ELENO :: 2026-05-24
set -u
PASS=0; FAIL=0
check() { local n="$1"; local u="$2"
  code=$(curl -sS --max-time 8 -o /dev/null -w "%{http_code}" "$u" 2>/dev/null)
  if [ "$code" = "200" ] || [ "$code" = "302" ] || [ "$code" = "301" ]; then
    printf "  [PASS] %-12s HTTP %s  %s\n" "$n" "$code" "$u"; PASS=$((PASS+1))
  else
    printf "  [FAIL] %-12s HTTP %s  %s\n" "$n" "${code:-000}" "$u"; FAIL=$((FAIL+1))
  fi
}

echo "==> Sinister Mesh OS — service smoke test"
echo
check "panel"       "http://127.0.0.1:3081/"
check "gitea"       "http://127.0.0.1:8030/api/healthz"
check "syncthing"   "http://127.0.0.1:28384/"
check "nats"        "http://127.0.0.1:8222/healthz"
check "yjs"         "http://127.0.0.1:1234/healthz"
check "ollama"      "http://127.0.0.1:11434/"
check "vault-api"   "http://127.0.0.1:5079/api/vault/health"
check "guacamole"   "http://127.0.0.1:8060/guacamole/"
check "filebrowser" "http://127.0.0.1:8090/"
check "rocketchat"  "http://127.0.0.1:8050/api/info"

echo
echo "==> $PASS / 10 services healthy"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
