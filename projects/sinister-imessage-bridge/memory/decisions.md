# decisions — architectural log

> **Author:** RKOJ-ELENO :: 2026-05-24
> Append at top; most-recent first. Each row = one decision + date + alternatives considered + why-this-one.

---

## 2026-05-24 — UI inherits sinister-dashboard-skeleton (NO accent override — LetsText brand)

**Context:** new operator hard-canonical (15:44Z) mandates every UI surface inherit from `projects/sinister-dashboard-skeleton/dashboard-skeleton/`. Per-project override is `--accent` only. **Operator directive 2026-05-24 16:08Z (verbatim):** *"this needs the letstext branding and look"*.

**Decision:** the iMessage Bridge dashboard inherits the skeleton via Tailwind 4 `@import` + tsconfig `@skeleton/*` alias, and keeps the skeleton's default `--accent: #0A84FF` (iOS dark-mode system blue — literally the iMessage outbound-bubble color). This IS the LetsText brand; the dashboard-skeleton was extracted from LetsText 2.0's sandbox in the first place.

**Why no purple override:**
- The iMessage Bridge surfaces LetsText's product flow (an iMessage tool). Sinister-fleet purple `#c084fc` is right for sanctum / forge / mind / other internal lanes; wrong for a LetsText-facing surface.
- iOS-blue `#0A84FF` is the exact hex of the iMessage outbound bubble color — using anything else would feel off-brand on a screen that LITERALLY RENDERS iMessage bubbles.
- Skeleton ships iOS-blue as the default — no override is the simplest possible expression of "inherit + don't fork".

**Earlier decision reversed:** an initial version of this row chose Sinister purple per the fleet standing-accent pattern. Operator clarified the LetsText branding requirement at 16:08Z; reverted in the same /loop iteration. Net: zero re-work since no commits had landed yet.

**Alternatives rejected:**
- Roll our own — violates the new doctrine
- Sinister fleet purple — wrong brand fit for a LetsText surface (per 16:08Z)
- Embed in an existing Sanctum panel — the bridge is its own surface

---

## 2026-05-24 — AppleScript-as-canonical-send-path (defer private framework)

**Decision:** every send during P1-P3 uses `osascript send.applescript`. Private-framework (`IMCore.framework`) recon is reserved for P4+ if AppleScript proves insufficient.

**Why:**
- Stable across macOS releases (private framework breaks ~yearly)
- Documented public surface (no reverse-engineering maintenance)
- Sufficient for 1:1 text sends (the P1-P3 scope)
- Operator-auditable (the `.applescript` file is plain text)

**Tradeoff accepted:** no group messages, no tapbacks, no attachments at P1-P3. Adds when operator requests them.

---

## 2026-05-24 — Per-thread operator OK during P1-P3 (no auto-respond until P4)

**Decision:** the wrapper at `send_worker/send.py` requires `operator_ok=True` for every send. Bridge_daemon's `POST /send` requires `{ "operator_ok": true }` in the body. Auto-respond rules are P4 only, operator-curated per-contact-per-pattern.

**Why:**
- The bridge sends from the operator's iMessage account — false sends look like the OPERATOR sent them
- Per-thread OK is the smallest unit of trust the operator can grant
- Auto-respond becomes safe only once the bridge has weeks of clean per-thread data behind it
- Sanctum no-bullshit doctrine §1 — tested before claimed; auto-respond claims need many smoke-tests first

---

## 2026-05-24 — Farm-only execution (operator owns the Apple ID surface)

**Decision:** every chat.db read + every AppleScript send runs on the operator's Mac farm. NOTHING runs on operator's daily-driver Mac, on a cloud Mac (MacStadium etc), or on a non-operator-controlled host.

**Why:** Apple ID surface is sensitive. Mac farm = operator-physically-controlled, dedicated, isolatable. Cloud Mac = third-party + the contract terms vary + risk to the operator's Apple ID. Daily-driver = mixing operator's primary identity with bridge identity.

**Mitigation if the operator doesn't have a farm yet:** P0-P1 lanes the canned chat.db fixture; everything else stays on hold.

---

## 2026-05-24 — `is_from_me=0` only on bus-emit (don't echo our own sends)

**Decision:** bridge_daemon's `dispatch_inbound` filters `if msg["is_from_me"] == 1: return` BEFORE posting to the bus.

**Why:** the tail picks up every new message, including ones WE just sent (delivery confirmation). Subscribers like vault should see all (P4.1), but `iMessageReceived` semantics are "an other party sent me a message". Echoing self-sends as `Received` would trigger auto-respond loops in P4.

---

## 2026-05-24 — Mock-friendly architecture (everything runs on Windows without farm)

**Decision:** every Python module in `source/` runs on Windows with no farm. The canned chat.db fixture (`source/fixtures/make_canned_chatdb.py`) materialises a real-schema SQLite with sample data. Tests monkeypatch `subprocess.run` for AppleScript.

**Why:** keeps the dev loop under 5s. Doesn't need the farm to land bug fixes, refactors, or new features against the read-path. Test suite stays green cross-platform.

---

## 2026-05-24 — SQLite URI `mode=ro` always (never take write locks)

**Decision:** every `sqlite3.connect()` call against any chat.db uses `file:<path>?mode=ro` URI mode with `uri=True`.

**Why:** Messages.app owns chat.db at runtime. Any write lock from us could corrupt the database OR be killed by Messages.app's own lock attempts. RO is the only safe posture; we never need to write to chat.db (vault snapshots are full-copy, not in-place).

---

## 2026-05-24 — bridge_daemon HTTP API on 127.0.0.1 only (Bearer token gate on /send for P4)

**Decision:** `bridge_daemon` binds to `127.0.0.1:8731` by default. `/send` is open to localhost callers in P0-P3 (the dashboard runs on the same host). P4 adds Bearer-token gate on `/send` for cross-host callers (e.g., showmasters lane on a different host posting via vault tunnel).

**Why:** localhost-only avoids any LAN exposure surprise. Token gate at P4 because that's when cross-host calls actually start.

---

## 2026-05-24 — chat.db schema fingerprint persists per-farm (per-macOS-version row)

**Decision:** `memory/chat-db-schema.md` carries observed-schema rows per farm + per macOS version. P1 PASS adds the first row; subsequent macOS upgrades on the farm add new rows.

**Why:** Apple periodically adds tables to chat.db (Sonoma added `unsynced_removed_items` etc). The fingerprint history lets us detect schema-changing upgrades that might break our queries.
