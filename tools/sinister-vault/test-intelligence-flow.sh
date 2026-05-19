#!/bin/bash
# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
# Smoke-test the per-agent intelligence-level flow end-to-end.
#
# What this verifies:
#   1) /api/auth/login returns a session token
#   2) POST /api/agents/<name>/intelligence persists to agent-prefs.json
#   3) GET  /api/agents/<name>/intelligence reads it back correctly
#   4) The [CONFIG] message lands in the inbox (the agent self-applies via Rule 9)
#
# IMPORTANT FILE PATHS (do not change without updating the launcher hook):
#   - prefs:  D:\Sinister Sanctum\_shared-memory\agent-prefs.json
#   - inbox:  D:\Sinister\Sinister Skills\01_MEMORY\_inbox\<sanitized-agent>\messages.jsonl
#     (sanitized = alnum + "-_" only; spaces stripped. "Sinister Snap API" -> "SinisterSnapAPI")
#
# Usage:
#   bash test-intelligence-flow.sh <operator-key>
#   OR  OPERATOR_KEY=... bash test-intelligence-flow.sh

set -e
KEY="${1:-$OPERATOR_KEY}"
[ -z "$KEY" ] && { echo "Usage: $0 <operator-key>  OR  export OPERATOR_KEY=..."; exit 1; }

BASE="${RKOJ_BASE:-http://127.0.0.1:5077}"
PREFS="/d/Sinister Sanctum/_shared-memory/agent-prefs.json"
INBOX_ROOT="/d/Sinister/Sinister Skills/01_MEMORY/_inbox"

echo "[1/5] Login at $BASE ..."
# NOTE: server returns {ok, label, token} -- NOT session_token. Older drafts of
# this script (and some operator notes) used session_token; that key does not
# exist and silently produced an empty token. The correct field is "token".
RESP=$(curl -s -w "\nHTTP=%{http_code}" -X POST "$BASE/api/auth/login" \
    -H "Content-Type: application/json" -d "{\"key\":\"$KEY\"}")
BODY=$(echo "$RESP" | sed '$d')
CODE=$(echo "$RESP" | tail -n1 | sed 's/HTTP=//')
if [ "$CODE" != "200" ]; then echo "    [FAIL] login HTTP=$CODE body=$BODY"; exit 2; fi
TOKEN=$(echo "$BODY" | python -c "import json,sys; print(json.load(sys.stdin).get('token',''))")
if [ -z "$TOKEN" ]; then echo "    [FAIL] login OK but no token in body: $BODY"; exit 2; fi
echo "    [OK] token acquired (len=${#TOKEN})"

AGENT="intel-test-$(date +%s)"
echo "    test agent: $AGENT"

echo "[2/5] POST intelligence ..."
RESP=$(curl -s -w "\nHTTP=%{http_code}" -X POST "$BASE/api/agents/$AGENT/intelligence" \
    -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
    -d '{"model":"claude-haiku-4-5-20251001","fast":false}')
BODY=$(echo "$RESP" | sed '$d')
CODE=$(echo "$RESP" | tail -n1 | sed 's/HTTP=//')
if [ "$CODE" != "200" ]; then echo "    [FAIL] POST HTTP=$CODE body=$BODY"; exit 3; fi
echo "    [OK] $BODY"

echo "[3/5] GET intelligence (read-back) ..."
RESP=$(curl -s -w "\nHTTP=%{http_code}" -H "Authorization: Bearer $TOKEN" \
    "$BASE/api/agents/$AGENT/intelligence")
BODY=$(echo "$RESP" | sed '$d')
CODE=$(echo "$RESP" | tail -n1 | sed 's/HTTP=//')
if [ "$CODE" != "200" ]; then echo "    [FAIL] GET HTTP=$CODE body=$BODY"; exit 4; fi
echo "    [OK] $BODY"
echo "$BODY" | grep -q "claude-haiku-4-5" || { echo "    [FAIL] model didn't round-trip"; exit 4; }

echo "[4/5] Verify agent-prefs.json contains $AGENT ..."
if [ ! -f "$PREFS" ]; then echo "    [FAIL] prefs file missing: $PREFS"; exit 5; fi
if grep -q "\"$AGENT\"" "$PREFS"; then
    echo "    [OK] prefs persisted (entry present)"
else
    echo "    [FAIL] $AGENT not found in $PREFS"; exit 5
fi

echo "[5/5] Verify [CONFIG] inbox message landed ..."
# Sanitize agent name the same way _shared.inbox._agent_dir does (alnum + -_ only).
SAFE=$(echo "$AGENT" | tr -cd 'A-Za-z0-9_-')
INBOX_FILE="$INBOX_ROOT/$SAFE/messages.jsonl"
if [ ! -f "$INBOX_FILE" ]; then
    echo "    [FAIL] no inbox file at $INBOX_FILE"
    echo "    (hub root expected at D:\\Sinister\\Sinister Skills -- check SINISTER_HUB_ROOT env)"
    exit 6
fi
if tail -5 "$INBOX_FILE" | grep -q "\[CONFIG\] model=claude-haiku-4-5"; then
    echo "    [OK] [CONFIG] message present"
    echo "    last line: $(tail -1 "$INBOX_FILE")"
else
    echo "    [FAIL] inbox file exists but no [CONFIG] match in last 5 lines"
    tail -5 "$INBOX_FILE"
    exit 6
fi

echo
echo "[DONE] intelligence flow PASS"
echo "       Operator clicked [Intelligence] -> POST persists -> inbox notifies."
echo "       Live agent next inbox_poll surfaces [CONFIG] -> self-applies /model."
echo "       Next launcher spawn for $AGENT will boot with --model claude-haiku-4-5-20251001."
