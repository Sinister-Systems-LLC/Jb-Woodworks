# Agent-to-agent messaging

**Problem:** the operator runs multiple Claude sessions (one per Sinister project).
Sessions can't message each other directly. The workaround was hand-written MD
files in each project. Tedious, error-prone, doesn't notify the recipient.

**Solution (Phase 8w):** file-based inbox per session + presence heartbeat +
ephemeral-spawn fallback if the recipient is offline. All sessions can ask each
other questions through 6 bus tools — no MD shuffling.

## Mental model

- **Agent** = one Claude session. Conventional names: `master`, `snap-signer`, `sinister-tiktok-emu`, `sinister-snap-emu`, `sinister-bumble-emu`, `sinister-panel`, `sinister-rka-good`, `kernel-su-setup`.
- **Persistent agent** = a Claude session the operator started. NEVER auto-closes; lives until operator closes it.
- **Ephemeral agent** = a one-shot `claude --print <prompt>` subprocess spawned to answer a single question. Exits when done. Spawned only when the persistent agent is offline AND `allow_ephemeral=true`.

## Bus tools (6 new this phase)

```
sinister-bus.heartbeat(my_agent)
  -> Mark THIS session as online. Call once per turn (cheap; touches one file).

sinister-bus.who_is_online()
  -> List every known agent + whether they have a fresh heartbeat (< 5 min).

sinister-bus.inbox_send(to_agent, message, from_agent, urgent=false, tags=[])
  -> Enqueue a message. Returns immediately. Recipient polls + acts.

sinister-bus.inbox_poll(my_agent, mark_consumed=true, limit=50)
  -> Read my inbox. mark_consumed=true atomically clears the queue.

sinister-bus.inbox_reply(msg_id, my_agent, response)
  -> Reply to a delegate_to request. Caller polls our sent.jsonl for reply_to == msg_id.

sinister-bus.delegate_to(agent_name, prompt, timeout_sec=60, allow_ephemeral=true, context_hint="")
  -> Ask-and-wait. If online -> inbox + wait for inbox_reply. If offline + allow_ephemeral
     -> spawn `claude --print` subprocess, capture stdout, return. NEVER kills the operator's persistent sessions.

sinister-bus.inbox_stats()
  -> Summary across all agent inboxes (counts).
```

## File layout

```
D:\Sinister\Sinister Skills\01_MEMORY\_inbox\<agent>\
├── online.flag      mtime = last heartbeat (TTL 5 min)
├── messages.jsonl   append-only inbound queue
├── sent.jsonl       audit of every send (incl. replies — reply_to field)
└── consumed.jsonl   audit of poll() calls
```

Plus `runtime-state/delegate-log.jsonl` audits every `delegate_to`.

## Recommended per-session protocol

Every Claude session does this **once per turn**:

```
sinister-bus.heartbeat my_agent="<this-project-name>"
sinister-bus.inbox_poll my_agent="<this-project-name>"
   -> if any messages, surface to operator (or reply if it's a delegate_to)
```

The hub's SESSION-START already documents this in `00-RULES.md` (Phase 8w
update).

## Worked example: Panel asks Snap-signer about SS03

```
# Session A (Sinister Panel):
sinister-bus.delegate_to(
    agent_name="snap-signer",
    prompt="What SS03 hypothesis are you currently testing?",
    timeout_sec=30
)

# If Session B (snap-signer) is ONLINE:
#   1. Message lands in Session B's inbox
#   2. Session B sees on next inbox_poll
#   3. Session B calls sinister-bus.inbox_reply(msg_id, "snap-signer",
#      "Currently testing libclient.so JNI hook hypothesis...")
#   4. Session A's delegate_to returns the response
#   Mode: "inbox"

# If Session B is OFFLINE and allow_ephemeral=true (default):
#   1. claude.exe --print "<contextualized prompt>" spawned as subprocess
#   2. Ephemeral session reads snap-signer's hub memory + answers
#   3. Subprocess exits
#   4. Session A's delegate_to returns the response
#   Mode: "ephemeral"

# If OFFLINE and allow_ephemeral=false:
#   Mode: "offline"
#   Caller decides whether to wait or escalate.
```

## Operator's persistent agents are NEVER auto-closed

A core design rule: `delegate_to` only spawns **new** subprocesses. It cannot
attach to or kill an existing operator-started Claude session. Those persist
until the operator closes them. Ephemeral subprocesses exit naturally after one
turn.

## Cost

- Inbox/heartbeat: $0 (file I/O only)
- `delegate_to` with `mode="inbox"`: $0 (just file shuffling; recipient pays for their own turn)
- `delegate_to` with `mode="ephemeral"`: 1 Claude turn at whatever model your CLI is configured for (Opus by default — note this if cost-sensitive)

All `delegate_to` invocations log to `runtime-state/delegate-log.jsonl` with
mode + ok + char counts so you can see what's spending.

## What to add to your project's CLAUDE.md

```markdown
## Agent presence

This session is named: `<project-name>` (e.g. `snap-signer`).
On every turn:
  1. Call `sinister-bus.heartbeat my_agent=<project-name>`
  2. Call `sinister-bus.inbox_poll my_agent=<project-name>`
  3. If any inbox messages, surface to operator.
  4. If any are `delegate` tags, reply via `sinister-bus.inbox_reply`.
```

## Verify

```
sinister-bus.who_is_online            -> list of sessions with fresh heartbeats
sinister-bus.inbox_stats              -> agent count + online count + queue totals
sinister-bus.inbox_poll my_agent=<x>  -> see if anyone messaged you
```

## TL;DR

- **How we won:** 6 bus tools turn the operator's parallel sessions into a real
  message bus. Sessions register presence via heartbeat; messages land in
  per-agent inboxes; offline recipients can be answered by an ephemeral
  `claude --print` subprocess that exits after one turn. Operator-started
  sessions are NEVER killed by this system.
- **What you need to do:**
  - Add the 3-line "Agent presence" snippet to each project's CLAUDE.md.
  - In multi-session work, use `sinister-bus.delegate_to <agent> "<question>"`
    instead of writing MD files by hand.
