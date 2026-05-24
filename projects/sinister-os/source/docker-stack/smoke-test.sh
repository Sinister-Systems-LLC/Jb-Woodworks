#!/usr/bin/env bash
# smoke-test.sh — verify every Sinister Mesh service is healthy
# Author: RKOJ-ELENO :: 2026-05-24
#
# Run after `docker compose up -d`. Exits 0 if every endpoint returns 200,
# 1 otherwise. Prints per-service status.

set -u

PASS=0
FAIL=0

check() {
  local name="$1"; shift
  local url="$1"; shift
  if curl -fsS -o /dev/null --max-time 5 "$url"; then
    printf "  [PASS] %-12s %s\n" "$name" "$url"
    PASS=$((PASS + 1))
  else
    printf "  [FAIL] %-12s %s\n" "$name" "$url"
    FAIL=$((FAIL + 1))
  fi
}

echo "==> Sinister Mesh OS — service smoke test"
echo

check "gitea"     "http://127.0.0.1:3000/api/healthz"
check "syncthing" "http://127.0.0.1:8384/rest/noauth/health"
check "nats"      "http://127.0.0.1:8222/healthz"
check "yjs"       "http://127.0.0.1:1234/healthz"
check "ollama"    "http://127.0.0.1:11434/"
check "vault-api" "http://127.0.0.1:5078/api/vault/health"
check "panel"     "http://127.0.0.1:3080/"

echo
echo "==> Result: $PASS pass, $FAIL fail"

if [ "$FAIL" -eq 0 ]; then
  exit 0
else
  echo
  echo "Diagnose: docker compose ps; docker compose logs <service>"
  exit 1
fi
