# AppleScript surface — Messages.app

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Status:** baseline reference (no farm yet; numbers + behavior verified against public corpus + Apple docs; deltas from real farm land in `memory/gotchas.md` after P1+)

The canonical send path until P3+ recon proves we need the private framework (`IMCore.framework`). Everything below is osascript-callable; nothing requires private SPI.

## Invocation pattern

```bash
osascript send.applescript "<service>" "<recipient>" "<body>"
# service:    "iMessage" | "SMS"
# recipient:  E.164 phone "+15551234567" OR email "name@example.com"
# body:       UTF-8 text (no \n escape; pass literal newlines)
```

Return values (stdout):
- `OK` — accepted by Messages.app for queueing (NOT a delivery confirmation — see §4)
- `ERR <num> <msg>` — AppleScript error number + message

Exit code is always 0 if osascript ran (errors come back as `ERR`). Non-zero exit = osascript itself failed (binary missing / script not found / permission denied).

## The script (committed at `source/send_worker/send.applescript`)

```applescript
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

## Buddy resolution

`participant <recipient> of targetService` resolves to an existing buddy record. If `recipient` doesn't yet have a buddy in `targetService`:
- For an existing chat thread: Messages.app creates the buddy implicitly. Send succeeds.
- For a brand-new recipient never messaged before: implicit create works ~80% of the time; ~20% the send hits `ERR -1728` (can't get object). Workaround: open the thread once manually in Messages.app to seed the buddy record, then automation works.

P2 sidesteps this by ONLY targeting recipients that already have an existing thread (verified via the chat.db schema query before allowlisting).

## Service resolution

`1st account whose service type is "iMessage"` picks the FIRST iMessage account if multiple are signed in. If the farm has both `operator@apple.com` and `bridge@apple.com` signed in:
- Sends go from whichever was added first to Messages.app preferences.
- To target a specific account, use `account "<account_id>"` instead — the account_id is the iCloud/email string Messages stores per-account.

Recommendation: dedicate the bridge farm to a SINGLE bridge Apple ID. Don't mix with operator's primary.

## Receipts + delivery confirmation

AppleScript send returns immediately after Messages.app accepts the queue. Delivery confirmation happens asynchronously:
- `is_sent=1` in chat.db when Messages.app handed off to APNS
- `is_delivered=1` when APNS confirmed delivery
- `is_read=1` when recipient's device sent the read receipt (if recipient enabled them)

The bridge_daemon polls chat.db on a 5s cadence after each send to capture the delivery state and surface to the dashboard. No AppleScript event listener exists for delivery state — chat.db is the only signal.

## Known error numbers

| Num | Meaning | Action |
|---|---|---|
| -1700 | User canceled | Won't happen for headless; surface to log |
| -1728 | Can't get object | Buddy doesn't exist for that service; seed via manual thread |
| -10004 | Privilege violation | Automation not granted to ssh user; grant in System Settings |
| -1701 | Parameter error | Bad service name (use literal "iMessage" or "SMS") |
| -2700 | Script error | Syntax issue; re-check `send.applescript` |

When a send returns `ERR <num>`, log the number + message in `_shared-memory/PROGRESS/Sinister iMessage Bridge.md` and append to `memory/gotchas.md` if novel.

## Permissions required on the farm

macOS gates AppleScript+Messages access through TCC. Headless / SSH invocation requires:

1. **Full Disk Access** for `sshd-keygen-wrapper` (to read `chat.db`)
2. **Automation: Messages** for the SSH session's shell (`/bin/bash` or `/bin/zsh`) — grants `tell application "Messages"` over SSH
3. **Accessibility** — NOT required for the `send/participant` API used in the script (only required if scripting GUI clicks)
4. **Privacy & Security → Automation** — must list the user-shell as having Messages automation permission

Granting steps documented in `memory/gotchas.md` once verified on the real farm.

## What this surface does NOT do

- **Group messages.** The script targets `participant`, not `chat`. Group-chat send requires the `chat` AppleScript object — different shape. Add when P4 adds group support.
- **Attachments.** No file-attach in the P2 script. AppleScript supports `with attachments {<file ref>}` — add when operator requests image/video bridging.
- **Tapbacks / reactions.** Not exposed in the AppleScript Messages dictionary at any macOS version we've tracked. Would require private framework recon.
- **Read receipts.** Sending a read-receipt back requires either the private framework OR poking chat.db (which writes — banned for our read-only posture).
- **Typing indicators.** Not exposed in AppleScript at all.

## When to switch to private framework

Move to `IMCore.framework` SPI calls only if BOTH:
- Operator hits a real limit (group messages / tapbacks / read receipts they need)
- AppleScript surface above genuinely doesn't cover it

Until then: AppleScript is the canonical send path. Private framework adds maintenance burden (breaks every macOS major release) and isn't justified for P1-P3.
