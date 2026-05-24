# contact-policy — per-recipient send + auto-respond rules

> **Author:** RKOJ-ELENO :: 2026-05-24
> The send wrapper at `source/send_worker/send.py` parses the `## p2_allowed` table below to decide whether a send is allowed during P2-P3. Auto-respond rules (P4) live in `## p4_autorespond`. Operator-signed rows ONLY are honored.

## p2_allowed

> Recipients EVE is authorized to send to during P2-P3 (per-thread operator OK still required per-message). Add a row only after operator confirms.

| handle | added_ts | operator_signed |
|---|---|---|
| _none yet_ | — | no |

**Schema:**
- `handle` — E.164 phone OR email string. Must MATCH what `chat.db.handle.id` stores for that contact (run P1 §5b to confirm before allowlisting).
- `added_ts` — UTC date row added (`YYYY-MM-DD`).
- `operator_signed` — `yes` (required for rows to be honored; `no` rows are stored as candidates but ignored by `send.py`).

## p4_autorespond

> Operator-curated auto-respond rules. Each rule fires up to 5×/hour per (handle, pattern). One auto-reply per inbound (no chains). Empty until P4.

| handle | pattern | action | template | operator_signed | added_ts |
|---|---|---|---|---|---|
| _none yet_ | — | — | — | no | — |

**Schema:**
- `handle` — same as p2_allowed
- `pattern` — Python regex applied to inbound `body`. Anchored (`^...$` required by the parser).
- `action` — `reply_template` for now; `webhook` planned for P4.5+
- `template` — literal text to send. NO interpolation in P4 (deliberately — interpolation adds escape-injection risk).
- `operator_signed` — `yes` to activate; `no` rows ignored.
- `added_ts` — UTC date row added.

## Kill-switch

If the operator needs to immediately disable all auto-respond rules:
```bash
curl -X POST http://127.0.0.1:8731/autorespond/disable
```
Sets an in-memory flag; bridge_daemon refuses every auto-respond send until cleared via `/autorespond/enable`.

## Add-rule checklist (operator-facing)

When operator says "add <contact> to p2_allowed":
1. EVE confirms the contact exists in `chat.db` (runs P1 §5c filtered by chat_identifier).
2. EVE appends a `signed=no` row to `## p2_allowed` and surfaces it to operator-action-queue.
3. Operator flips `signed=no` → `signed=yes` in the row (the act of operator-editing this file IS the signature).
4. EVE re-loads policy (or auto-reload on file change — see `source/send_worker/send.py`).

## What this file does NOT do

- Does NOT store message content / drafts / templates beyond the `p4_autorespond.template` column.
- Does NOT store any Apple ID, SSH key, or vault token (those live in `_vault/`).
- Does NOT carry per-recipient rate-limits beyond the global `RATE_GAP_SEC` (per-recipient rate-limits land at P4 when needed).
- Does NOT carry phone-number-formatting conversion logic — the handle MUST already match what chat.db stores.
