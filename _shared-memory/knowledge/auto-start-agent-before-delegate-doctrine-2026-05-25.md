# Auto-Start Agent Before Cross-Lane Delegate Doctrine

> **Author:** RKOJ-ELENO :: 2026-05-25
> **Operator hard-canonical 2026-05-25T11:39:56Z:** *"you need to open a sanctum agent so they can work on it. you also need to update memory to check if you have an agent to complete the project if now auto start them in the correctmanner"*
> **Status:** binding for every Sinister Sanctum fleet agent
> **Composes with:** `automate-everything-no-operator-admin-2026-05-25.md` + `no-gate-questions-execute-directly-2026-05-25.md` + `sanctum-scope-discipline-2026-05-24.md` + `full-relentless-swarm-fanout-mindset-doctrine-2026-05-25.md`

---

## TL;DR

When you write a `[DELEGATE]` (or `[ASK]`) message to another lane's inbox,
you MUST first check that the target lane has a fresh heartbeat (≤30 min).
If it does not, you MUST auto-launch a session for that lane in the same
turn — never leave a delegated message sitting in a dead inbox.

A delegate that lands in a stale inbox = a directive that never executes.
This is a silent failure mode the operator hard-canonical above closes.

---

## The 3-step pattern

```
Before every cross-lane handoff:

1. CHECK    target heartbeat age <30 min?
            powershell -File automations/check-heartbeat.ps1 -Slug <target>
            (or fallback: stat _shared-memory/heartbeats/<target>.json mtime)

2. IF NO    auto-launch the target lane:
            powershell -File automations/start-sinister-session.ps1 -Project <target>
            (run in background; do NOT block on it)

3. WRITE    the [DELEGATE] inbox row (json with operator_verbatim + spec_extracted).
            Include a "delegate_target_launched" boolean field set to true if
            you just auto-started it, false if it was already alive.
```

## Anti-patterns (BANNED)

- "I wrote the [DELEGATE] — done." → without checking heartbeat, the delegate is dead air
- "Should I launch a sanctum agent?" → NO GATE QUESTIONS doctrine forbids asking
- "The operator can launch sanctum manually." → AUTOMATE EVERYTHING doctrine forbids surfacing manual asks
- Writing the delegate but not the launch → silent regression
- Launching but skipping the delegate write → the new agent has no instruction

## What counts as "fresh heartbeat"

Default threshold: **30 minutes**. Use this unless the work is genuinely time-critical (operator says "now") in which case use **5 minutes**.

Two sources of truth:
1. **File mtime** of `_shared-memory/heartbeats/<slug>.json` (fastest, fallback)
2. **`ts_utc` field inside the json** (more accurate — survives file-touch noise)

When in doubt, use the older of the two.

## Composes with FULL-RELENTLESS SWARM FAN-OUT (doctrine 2026-05-25)

When fan-out mode is on, the delegating agent doesn't just launch ONE child — it can spawn 3-5 in parallel for the same delegate if the work has independent slices. Example: launching 8 agents like the operator asked 2026-05-25T11:37Z = spawn one sanctum master + check if the 7 children's individual lanes have live agents, auto-launch any that don't.

## What we DON'T do

- Don't launch the same lane twice (check heartbeat first).
- Don't spawn for trivial info-only `[INFO]` messages — only for `[DELEGATE]` / `[ASK]` / `[REQUEST]` tags requiring action.
- Don't spawn cross-product (don't launch all N lanes "just in case") — only launch what your delegate(s) target.

## Detection on cold-start (every fleet agent)

Cold-start step 11(a) already polls `fleet-updates.jsonl` — add an analogous
poll for STALE inbox messages targeting lanes with dead heartbeats. Surface
them as "delegates landed in dead inboxes" early-warning in the first
response, so the operator sees the rescue queue at session-open.

## Pass criterion (binary)

Any new `[DELEGATE]` written to an inbox under `_shared-memory/inbox/<slug>/`
AFTER 2026-05-25T11:40Z must satisfy:

- The corresponding `<slug>` heartbeat is <30 min old at write time, OR
- The same turn the delegate was written, the launching agent ALSO
  executed `start-sinister-session.ps1 -Project <slug>` (recorded in
  `_shared-memory/sinister-term-history/` or similar lane history log).

## Cross-references

- `_shared-memory/knowledge/automate-everything-no-operator-admin-2026-05-25.md`
- `_shared-memory/knowledge/sanctum-scope-discipline-2026-05-24.md`
- `_shared-memory/knowledge/full-relentless-swarm-fanout-mindset-doctrine-2026-05-25.md`
- `_shared-memory/knowledge/no-gate-questions-execute-directly-doctrine-2026-05-25.md`
- `_shared-memory/knowledge/single-repo-push-policy-2026-05-25.md`
- `automations/start-sinister-session.ps1` (the launcher this doctrine drives)
- `_shared-memory/inbox/<slug>/` (the inboxes this doctrine protects)
