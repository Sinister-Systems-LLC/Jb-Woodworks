# P2 — Send acceptance plan

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Phase:** P2 (AppleScript send via SSH; per-thread operator OK; mock + live round-trip)
> **Unlock condition:** P1 (`plans/p1-readonly-acceptance.md`) is `smoke-tested` PASS AND operator has explicitly authorized a dedicated bridge Apple ID OR confirmed the farm Apple ID is non-primary
> **Estimated bench time:** 30–60 min once P1 closes

P2 proves the bridge can SEND. Every send during P2 is operator-gated per-thread — no auto-respond, no batch, no schedule.

---

## 0. Pre-flight (depends on P1 PASS)

| Check | Pass condition |
|---|---|
| P1 row in PROGRESS marked `smoke-tested` | One PROGRESS row contains all six §6 checkboxes from `plans/p1-readonly-acceptance.md` |
| `memory/farm-inventory.md` shows `is_primary=false` for the target farm | Operator confirms or has provisioned a dedicated bridge Apple ID |
| Test recipient identified | Operator names a single contact identifier — typically the operator's own 2nd device, NEVER a third party for P2 |
| Test recipient's chat thread already exists in `chat.db` | Verified via P1 §5c query — sending into a fresh thread requires Messages.app onboarding state we don't want to debug in P2 |

If any line above is `false` → P2 does NOT open. Park as queue row + return to picker.

---

## 1. AppleScript send surface — the canonical script

The script below is the entire P2 send surface. It is committed at `source/send_worker/send.applescript`. Every send during P2-P3 routes through it.

```applescript
-- send.applescript :: RKOJ-ELENO :: 2026-05-24
-- Invocation: osascript send.applescript "<service>" "<recipient>" "<body>"
-- service: "iMessage" or "SMS"
-- recipient: phone E.164 (+15551234567) or email
-- body: UTF-8 text, double-quotes escaped
on run argv
    if (count of argv) is not 3 then
        return "ERR usage: send.applescript <service> <recipient> <body>"
    end if
    set theService to item 1 of argv
    set theRecipient to item 2 of argv
    set theBody to item 3 of argv
    try
        tell application "Messages"
            set targetService to 1st account whose service type is (theService as text)
            set theBuddy to participant theRecipient of targetService
            send theBody to theBuddy
        end tell
        return "OK"
    on error errMsg number errNum
        return "ERR " & errNum & " " & errMsg
    end try
end run
```

**Why exactly this shape:**
- `account whose service type is "iMessage"` resolves the right account when multiple are signed in.
- `participant ... of targetService` is the canonical buddy resolution; falls back to creating a participant record if Messages.app doesn't have one yet (rare — that's why P2 only targets pre-existing threads).
- `try/on error` returns `ERR <num> <msg>` instead of a raw stack to stderr → easier for the Python wrapper to parse.
- No `Messages` UI activation — script runs headless when Messages.app is already running (and signed in).

---

## 2. Python wrapper — `source/send_worker/send.py`

The wrapper enforces three guards that AppleScript can't:

1. **Operator-OK gate** — every send call requires `operator_ok=True` OR the call returns immediately as `DRY_RUN`.
2. **Per-thread allowlist** — sends are blocked unless `recipient` is in `memory/contact-policy.md`'s `p2_allowed` set.
3. **Rate-limit** — max 1 send / 5s per recipient during P2 (prevents test loops from spamming).

```python
# source/send_worker/send.py :: RKOJ-ELENO :: 2026-05-24
import subprocess, time, json, pathlib
from typing import Literal

POLICY = pathlib.Path(__file__).resolve().parents[1] / "memory" / "contact-policy.md"
RATE_GAP_SEC = 5
_last_send: dict[str, float] = {}

def send(
    service: Literal["iMessage", "SMS"],
    recipient: str,
    body: str,
    *,
    operator_ok: bool = False,
    dry_run: bool = False,
    ssh_target: str | None = None,
) -> dict:
    if not operator_ok and not dry_run:
        return {"status": "blocked", "reason": "operator_ok=False"}
    if recipient not in _load_allowed():
        return {"status": "blocked", "reason": "recipient not in p2_allowed"}
    if time.monotonic() - _last_send.get(recipient, 0) < RATE_GAP_SEC:
        return {"status": "blocked", "reason": "rate_limit"}
    if dry_run:
        return {"status": "dry_run", "service": service, "recipient": recipient, "body_len": len(body)}
    _last_send[recipient] = time.monotonic()
    cmd = ["osascript", "send.applescript", service, recipient, body]
    if ssh_target:
        cmd = ["ssh", ssh_target, "osascript", "/path/to/send.applescript", service, recipient, _shquote(body)]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return {"status": "ok" if out.stdout.startswith("OK") else "error", "stdout": out.stdout.strip(), "stderr": out.stderr.strip(), "exit": out.returncode}

def _load_allowed() -> set[str]:
    # parses a markdown table from memory/contact-policy.md; format see that file
    ...

def _shquote(s: str) -> str:
    return "'" + s.replace("'", "'\"'\"'") + "'"
```

Companion test at `source/tests/test_send.py` — monkeypatches `subprocess.run` to return canned `OK` / `ERR` outputs; verifies all four guards (operator_ok, allowlist, rate-limit, dry_run). Runs on Windows.

---

## 3. Live round-trip smoke

Once §1+§2 land + operator names a test recipient + contact-policy.md adds them to `p2_allowed`:

```bash
# Operator authorizes the send via interactive prompt; EVE never sets operator_ok=True itself
python -m send_worker.send --service iMessage --to "+15551234567" --body "P2-ping-$(date +%s)" --operator-ok
```

**Pass:**
- Python wrapper returns `{"status": "ok", "stdout": "OK"}` within 30s.
- A new row appears in the farm's `chat.db` with `is_from_me=1` and `text` matching the body, within 5s of the wrapper returning (verified via P1 query §5b inverted to `is_from_me=1`).
- Operator's 2nd device receives the iMessage (operator visually confirms).

**Verb if all three:** `acceptance-tested` (above smoke — this is round-trip-proven).

---

## 4. Reverse round-trip (operator-initiated)

Operator manually sends a reply from the 2nd device → EVE polls `chat.db` (using the §5b query) → confirms the new `is_from_me=0` row appears within 30s of the operator hitting send (`recv` is poll-based in P2; FSEvents is P3).

**Pass:** row appears + matches body + matches sender handle.
**Verb if PASS:** `acceptance-tested` (reverse direction).

---

## 5. Acceptance criteria — what makes P2 a PASS

P2 is `acceptance-tested` (per no-bullshit doctrine §1, top tier) when **all** of the following land in one PROGRESS row, with command + exit code + per-step ts:

- [ ] `source/send_worker/send.applescript` committed
- [ ] `source/send_worker/send.py` + `source/tests/test_send.py` committed; pytest exit 0 on Windows
- [ ] `memory/contact-policy.md` has at least 1 row in `p2_allowed`
- [ ] §3 live forward round-trip — wrapper `ok`, chat.db `is_from_me=1` row, operator visual confirm
- [ ] §4 reverse round-trip — chat.db `is_from_me=0` row, body match, handle match
- [ ] §6 abuse-rate-limit smoke — second send to same recipient within 5s returns `{"status": "blocked", "reason": "rate_limit"}`
- [ ] Brain entry `_shared-memory/knowledge/imessage-bridge-p2-send-2026-MM-DD.md` summarizing AppleScript quirks observed + indexed in `_INDEX.md`

P2 deliberately does NOT auto-respond. P2 deliberately does NOT batch. P2 deliberately does NOT schedule. Auto-respond rules are P4 (operator-curated per-contact).

---

## 6. Abuse rate-limit smoke

```python
r1 = send("iMessage", "+15551234567", "rate-test-1", operator_ok=True)
assert r1["status"] == "ok"
r2 = send("iMessage", "+15551234567", "rate-test-2", operator_ok=True)
assert r2["status"] == "blocked" and r2["reason"] == "rate_limit"
time.sleep(6)
r3 = send("iMessage", "+15551234567", "rate-test-3", operator_ok=True)
assert r3["status"] == "ok"
```

**Pass:** all three asserts hold. Confirms the wrapper guards rate-limit even when AppleScript would happily send.

---

## 7. Safety + reversibility wall

| Risk | Mitigation |
|---|---|
| Sending to wrong recipient | `p2_allowed` allowlist enforced by wrapper; AppleScript only invoked after allowlist check |
| Accidental loop (bot replying to bot) | RATE_GAP_SEC=5 + `is_from_me=1` filter in any future poll-based responder |
| Operator's primary Apple ID accidentally used | `is_primary=false` enforced in P2 pre-flight §0 |
| Message body containing shell metachars (rm -rf via curl-pipe) | `_shquote` for SSH path; AppleScript arg passing isn't shell — `osascript` argv is positional so no injection |
| Spammy retries on transient AppleScript error | NO auto-retry in P2; single attempt, surface error, operator decides |

If §3 or §4 round-trip takes >30s, abort and surface to operator. Default AppleScript send latency is <2s.

---

## 8. After P2 PASS — what's next

- Open `agent/sinister-imessage-bridge/p3-bridge-daemon-<date>` branch
- Wire up `source/recv_worker/tail.py` for FSEvents-based live tail (replacing P2's poll-based receive)
- Build the bus posting layer (`org.sinister.Bus.iMessageReceived` on sinister-os; sanctum inbox message until then)
- Start the dashboard UI (`I4` of /loop iteration plan) and confirm it can render a thread list against the bridge's HTTP surface
