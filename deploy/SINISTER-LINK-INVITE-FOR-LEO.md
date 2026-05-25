# Sinister LINK invite — for Leo

**Author:** RKOJ-ELENO :: 2026-05-25

> Fresh invite generated 2026-05-25T07:09:49Z by operator-pairing flow.
> Expires **2026-05-25T15:09:49Z** (8h window). ID: `inv-20260525030949-022e5b`.

## Code (paste this verbatim into Leo's EVE.exe -> L) Sinister LINK -> C) Accept invite)

```
eyJleHBpcmVzX3V0YyI6IjIwMjYtMDUtMjVUMTU6MDk6NDlaIiwiaXNzdWVyX25vdGUiOiJTaW5pc3RlciBMSU5LIGludml0ZSBmcm9tIG9wZXJhdG9yIiwiaXNzdWVkX3V0YyI6IjIwMjYtMDUtMjVUMDc6MDk6NDlaIiwicGVlcl9kaXNwbGF5Ijoib3BlcmF0b3IiLCJwZWVyX25hbWUiOiJkZXNrdG9wLWx0bzRsdXMiLCJwc2siOiIxQnVfaTNCalQ5RXo4dWNuVU04MWNSZzAiLCJ2IjoxLCJ0cmFuc3BvcnQiOiJnaXQiLCJwZWVyX3RhaWxzY2FsZV9pcCI6IiJ9
```

## CLI fallback (if EVE.exe isn't open)

```
powershell -File "D:\Sinister Sanctum\automations\sinister-link.ps1" -Action AcceptInvite -InviteCode "eyJleHBpcmVzX3V0YyI6IjIwMjYtMDUtMjVUMTU6MDk6NDlaIiwi...g0In0="
```
(Paste the full code from above between the quotes.)

## Transport

`git` — both peers push/pull each other's `agent/*` branches via `sanctum-auto-push` daemon. Sub-minute sync via Sinister Vault path is reserved for the LIVE Vault wire-up tracked in `_shared-memory/plans/sinister-vault-live-2026-05-25/plan.md` (iter-24 sub-D).

## Security

- PSK is a 22-char URL-safe random string; hashed to `psk_hash` in `_shared-memory/sinister-link-invites/inv-20260525030949-022e5b.json` (committed). Plaintext PSK is ONLY in the base64 invite code above — share OOB (Signal / iMessage / email).
- Invite is one-shot: once Leo runs AcceptInvite, the invite file flips `consumed_utc` and the PSK rotates into the live `sinister-link-state.json`.
- If you don't redeem by **2026-05-25T15:09:49Z**, regenerate via `powershell -File automations\sinister-link.ps1 -Action GenerateInvite -ExpiresMin 480`.

## After Leo redeems

Both sides run `powershell -File automations\sinister-link.ps1 -Action Status` and confirm `state=paired`. Then `sinister-link-poller` schtask (5 min cadence, Python per `automations/sinister_link_poller.py`) keeps the peer branches synced.
