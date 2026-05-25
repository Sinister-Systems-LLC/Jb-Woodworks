<!-- decay:
  category: preference
  confidence: 0.9
  reinforcements: 1
  half_life_days: 180
-->
> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Cross-agent coordination — agents help agents, not just operator

**Status:** `fixed`
**Tags:** `coordination, inbox, broadcast, delegate, cross-agent, multi-agent, fleet, standing-rule`
**Created:** 2026-05-19
**Updated:** 2026-05-19

---

## Problem

How should agents talk to each other?

Concrete trigger (2026-05-19): operator screenshot showed the **TikTok agent** asking the **Snap agent** to set up a "mutual info-sharing channel" — TT wanted Snap's pure-API findings to inform its libclient.so dump, Snap wanted TT's libsigi cross-references back. They tried to negotiate the channel format through the operator. That's a bottleneck.

Before this rule, the typical pattern was:

```
Agent A (working) -> operator (DM) -> operator decides -> operator relays -> Agent B
```

Three round-trips of human latency for what's usually `[ASK] / [ANSWER]`. The fleet is N=10+ agents now; if every cross-agent interaction routes through the operator, the operator becomes the bottleneck and lateral knowledge transfer dies.

## Why it matters

- **Parallel speedup.** When TT is mid-dump and needs Snap's input on a JNI signature, waiting for operator relay adds 5–30 minutes of dead air per question. Direct inbox = seconds.
- **Shared learning.** When Snap discovers `Yurikey52` cert rotated, every phone-stack agent (Snap, TT, IG, KSU, RKA) needs to know. Operator relay = N messages typed by hand. Broadcast = 1 message, fan-out by server.
- **Operator role compression.** Operator's job becomes *orchestration + adjudication*, not telephone-switchboard. Cross-lane work hand-offs still need approval (per Rule 9 / 10), but lateral info-sharing should be ambient.
- **Audit trail stays intact.** All cross-agent messages flow through `_shared.inbox`, which already writes to `01_MEMORY/_inbox/<agent>/`. The RKOJ Activity Feed surfaces them. Nothing's hidden.

## Fix — the 5 patterns

Every Sanctum agent, every turn, scans its own work for two opportunities:
- "Could another **currently-online** agent help me right now?"
- "Did I just learn something another agent **would want to know**?"

If yes, use one of these five patterns.

### 1) Tag-based handshake (ASK / ANSWER / PASS)

The pattern from the 2026-05-19 TT<->Snap mutual-info channel.

You're TT agent, mid-dump, you wonder if Snap saw the same SIG-32 byte pattern in its pure-API track:

```python
inbox_send(
    to_agent="Sinister Snap API",
    message="[ASK] hey — I'm dumping libclient.so for SS03. You hit anything similar in pure-API track? Send back what you remember or [PASS] if nothing.",
    from_agent="Sinister TikTok",
    tags=["ask", "cross-agent", "cross-info"],
)
```

Snap sees on its next `inbox_poll` (Rule 9 = every turn), replies:

```python
# Snap agent's reply
inbox_send(
    to_agent="Sinister TikTok",
    message="[ANSWER] yeah — SIG-32 is the post-rotation handshake nonce. Snap pure-API treats it as opaque 32-byte token. Saw it in /api/auth/v3/handshake bodies. Not in libsigi.",
    from_agent="Sinister Snap API",
    tags=["answer", "cross-agent", "cross-info"],
)
```

Or, if Snap has nothing useful:

```python
inbox_send(to_agent="Sinister TikTok", message="[PASS] no idea, libsigi not my surface", ...)
```

`[PASS]` is critical — it tells the asker "I heard you, nothing to add" so they don't wait.

### 2) Broadcast (DISCOVERY → all online agents)

You discovered something the whole fleet (or a sub-fleet) needs to know. Don't N-send by hand; use the broadcast endpoint.

```bash
curl -X POST http://127.0.0.1:5077/api/inbox/broadcast \
  -H "Content-Type: application/json" \
  -d '{
    "body": "[DISCOVERY] Yurikey52 cert rotated successfully via rka_keybox_rotate.sh. All phone-stack agents can resume their tracks.",
    "tags": ["discovery", "cross-agent"],
    "from_agent": "Sinister RKA",
    "exclude": []
  }'
```

The RKOJ server (`automations/window-manager/server.py`) fans out to every agent listed in `/api/sessions` (i.e. every agent with a fresh `online.flag` heartbeat). Returns `{ok, delivered: [...], skipped: [...], count: N}`.

From the browser console (RKOJ UI):

```js
RkojHelpers.broadcastToAllAgents(
    "[DISCOVERY] Panel API now requires X-Sanctum-Tag header.",
    ["discovery", "cross-agent", "panel"],
);
```

Use `exclude: ["Some Agent"]` if you specifically don't want it to land somewhere (e.g. the agent that just told you).

### 3) Delegation (DELEGATE → ACK → DONE / DECLINE)

You need help that's specifically in another agent's lane. **This is cross-lane work and gates on operator OK** per Rule 9 / 10 — recipient must surface it to operator before acting.

```python
inbox_send(
    to_agent="Sinister Snap API",
    message="[DELEGATE] please grep /api/auth/v3/login responses for x-sanctum-tag header presence. Reply with first 10 distinct values.",
    from_agent="Sinister TikTok",
    tags=["delegate", "ask", "cross-agent"],
)
```

Recipient flow:
1. `inbox_poll` surfaces the `[DELEGATE]`.
2. Recipient shows operator: "Got delegate from TT. Cross-lane work — OK to proceed?"
3. If operator OK: reply `[ACK doing it]`, do the work, reply `[DONE result: ...]`.
4. If operator NO or recipient busy: reply `[DECLINE reason: ...]`.

Delegation has a heavier protocol than handshake because it commits the recipient's time, not just their attention.

### 4) Knowledge-share (any agent → brain)

Inbox messages are ephemeral (rolling tail). Discoveries that matter beyond the next 24h MUST also go to the brain:

```bash
# Append to existing topic OR create new
edit  D:\Sinister Sanctum\_shared-memory\knowledge\<topic>.md
edit  D:\Sinister Sanctum\_shared-memory\knowledge\_INDEX.md  # add/update row
```

Pattern:
- Broadcast the **what** (short, actionable, fresh).
- Brain entry is the **why + reproducer + caveats** (durable, indexed).

Per canonical-13 Rule 5 — read brain before risky actions, write discoveries after.

### 5) Cross-agent etiquette

- **Tag every cross-agent message with `cross-agent`** so future-you can `grep` for the whole conversation. Add `cross-info` for handshakes, `discovery` for broadcasts, `delegate` for hand-offs.
- **Lead with a bracketed verb tag** so the receiver pattern-matches in one glance:
  - `[ASK]` — I need info, please answer or PASS
  - `[ANSWER]` — answering your ASK
  - `[PASS]` — heard your ASK, nothing to add
  - `[DISCOVERY]` — sharing something the fleet should know
  - `[DELEGATE]` — please do work for me (operator-gated)
  - `[ACK]` — got your delegate, working on it
  - `[DONE]` — finished delegated work, here's the result
  - `[DECLINE]` — cannot/won't do the delegated work, here's why
- **Rate-limit yourself:** don't ping the same agent more than 3 times in 5 minutes without operator OK. Inbox storms make agents miss the signal.
- **Operationally critical?** ALSO append to `_shared-memory/PROGRESS/<agent>.md` so the audit trail survives the inbox rolling-tail.
- **Don't whisper.** Cross-agent messages are visible to operator in the Activity Feed by design. No private channels.

## Operator visibility

- RKOJ's Activity Feed surfaces all cross-agent messages.
- Filter by tag `cross-agent` to see only the horizontal traffic.
- The bell in the ribbon increments for `[ASK]` messages directed at the currently-viewing operator's agent (operator can override / answer manually if the addressee is slow).

## API surface (this change ships)

| Surface | Path | Purpose |
|---|---|---|
| Backend endpoint | `POST /api/inbox/broadcast` | Fan-out one message to all online agents |
| JS helper | `window.RkojHelpers.broadcastToAllAgents(body, tags, from_agent?, exclude?)` | Browser convenience |
| Ribbon tile | `BROADCAST` (Agents tab → SPAWN group, action `broadcast`) | Modal with body + tags |
| Modal template | `tpl-broadcast-modal` | body textarea + tags input + Send |

Existing surface that already works (no change):

| Surface | Path | Purpose |
|---|---|---|
| Backend endpoint | `POST /api/inbox/send` | One-to-one inbox |
| Python API | `_shared.inbox.inbox_send(to_agent, message, from_agent, tags=[...])` | Same, from agent code |
| Discovery | `GET /api/sessions` | Who's online right now (what `broadcast` iterates) |

## Why this exists as a standing rule, not a doc

This is durable expected behavior, not "nice-to-have." Every cold-start agent reads DIRECTIVES, sees this rule on turn 1, and is expected to behave accordingly from turn 1. The brain entry exists as the long-form why + reproducer; the DIRECTIVES rule is the binding short-form.

## Related canonical-13 rules

- **Rule 1 (heartbeat + inbox_poll every turn)** — without this, ASK / DELEGATE messages sit unread.
- **Rule 5 (brain)** — knowledge-share pattern (#4) is the brain side of cross-agent.
- **Rule 8 (PROGRESS/<agent>.md)** — operationally-critical cross-agent messages get mirrored here.
- **Rule 9 / 10 (lane discipline)** — `[DELEGATE]` crosses lanes, so it gates on operator approval.

## Anti-patterns (what NOT to do)

- **Asking the operator to relay** trivial info between agents — that's what this whole rule kills.
- **Whisper channels** — anything outside `_shared.inbox` (e.g. file-based dead-drops, custom sockets) hides the conversation from the audit trail. Don't.
- **Untagged messages** — `[some thought]` with no bracketed verb forces the receiver to read the whole body to decide if they care. Always lead with the tag.
- **Storming an agent** — N messages in 30 seconds. The recipient batches their `inbox_poll`; one well-formed message is better than five.
- **Discovering something, sharing only via inbox** — inbox is rolling-tail. If it'll matter next week, brain it too.
