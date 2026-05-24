# Operator-utterance tracking doctrine

> Author: RKOJ-ELENO :: 2026-05-24

Operator hard-canonical 2026-05-24 verbatim: *"make sure that everything i ever say is tracked and flagged for a few and evertyhing that needs to get sdone gets done. with every agent i am in"*.

## Why

Operator drops directives across many parallel agent lanes (sanctum, forge, panel, apk, rkoj, jb-woodworks, showmasters, seraphim, chatbot, sinister-os, etc). Without a shared, append-only ledger, directives fall through cracks: one agent acts, the others never know; resolution status is unknown; the operator has no single surface to ask "is this done yet?".

This doctrine codifies a fleet-wide JSONL store + two stdlib-only PowerShell CLIs (log + ack) + a cold-start ingestion step so every spawned EVE session surfaces the most-recent open directives in its first response.

## Data model

Path: `D:\Sinister Sanctum\_shared-memory\operator-utterances.jsonl` (append-only, one JSON object per line).

Schema per row:

```json
{
  "ts_utc": "2026-05-24T12:43:32Z",
  "session_slug": "sanctum",
  "session_id": null,
  "preview": "first 120 chars of the message, single-line",
  "tags": ["tracked","flagged","everything","needs","agent"],
  "status": "new",
  "agents_acked": [],
  "deliverables": [],
  "resolved_at_utc": null,
  "message_full": "...full operator message text..."
}
```

Status transitions:

- `new` — captured but no agent has read/acted yet
- `acknowledged` — at least one agent has read the row and (typically) committed at least one deliverable referencing it
- `resolved` — agent explicitly closes the row via `-Resolve` flag AND has at least one deliverable on file. Resolution is sticky; further work re-opens via a new utterance row, not by mutating the resolved row.

Tag extraction (auto): split on whitespace, lowercase, drop tokens length < 5, drop a stopword set (the/and/with/etc), rank by frequency, top 5 wins. Caller may override via `-Tags "k1,k2,k3"`.

Lock: `_shared-memory/.operator-utterances.lock` (exclusive-create file lock; 10s timeout; release on completion).

## CLIs

### log-operator-utterance.ps1

```powershell
powershell -File "D:\Sinister Sanctum\automations\log-operator-utterance.ps1" `
    -SessionSlug sanctum `
    -MessageFull "...verbatim operator message..." `
    [-Tags "comma,separated"] `
    [-SessionId "uuid"] `
    [-TsUtc "2026-05-24T12:34:56Z"]
```

Prints the assigned `ts_utc` to stdout so the caller can use it as the row-id for a later `ack` call. Stdlib-only (no third-party PowerShell modules).

### ack-operator-utterance.ps1

```powershell
powershell -File "D:\Sinister Sanctum\automations\ack-operator-utterance.ps1" `
    -TsUtc "2026-05-24T12:34:56Z" `
    -AgentSlug sanctum `
    [-Deliverable "commit-sha or file/path or _shared-memory/..."] `
    [-Resolve]
```

Locates the row by `ts_utc`, appends `AgentSlug` to `agents_acked` (idempotent), appends `Deliverable` to `deliverables` (additive), flips `status: new -> acknowledged` automatically. `-Resolve` is required to flip to `resolved` (and demands at least one deliverable already on file or supplied in the same call).

## Cold-start ingestion

CLAUDE.md cold-start adds a step (after step 7) to every fresh EVE session:

> **Step 8 — Operator utterance backlog.** Read the last 10 rows of `_shared-memory/operator-utterances.jsonl` where `status` is `new` or `acknowledged`. Surface them in the first response under a heading "Open operator utterances". This is how EVE catches the directives that landed in sibling agents or in this lane while you were cold.

## Anti-patterns

1. Mutating a `resolved` row instead of opening a fresh utterance — resolution is sticky for audit-trail integrity.
2. Calling the logger without `-MessageFull` populated verbatim — preview alone is not enough; the full text must survive for grep + replay.
3. Sneak-extracting tags into editorial categories — keep tags raw / keyword-derived. Editorial taxonomy belongs in the brain index, not here.
4. Skipping the lock (`File.WriteAllText` direct) — concurrent agents will clobber each other.
5. Manually editing the JSONL with a text editor — leads to invalid JSON; always go through the CLIs.
6. Flipping `status` to `resolved` from an agent that hasn't shipped a real deliverable — operator-visible commitment requires evidence on file.

## Composes with

- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` — utterance tracking IS the evidence ledger; `deliverables` field is the verified-claim cite.
- `agent-autonomy-push-and-completion-2026-05-23` — agents that "don't stop until done" need this ledger to know what "done" means.
- `do-not-revert-operator-canonical-protections-2026-05-23` — the cold-start step is anti-revert-protected (operator: "make sure i dont have these issues again and we do not revert").
- `agent-identity-eve` — every EVE on every lane consults the same JSONL.
- `multi-agent-git-coordination-2026-05-23` — many agents, one ledger; lock-based append prevents the same race-class.
- `bot-fleet-quick-reference` — future bot integration: `sinister-bus.list_open_utterances()` could surface these via MCP.

## Future work (not in this doctrine)

- EVE picker overlay row: surface unresolved count in the launcher chrome ("3 open operator utterances").
- Sinister-bus MCP tool: `list_open_utterances(agent_slug=None)` returning the same data over the bot fleet bus.
- Auto-resolve heuristic: when an utterance's `deliverables` list contains a commit SHA whose message mentions the utterance ts_utc, propose auto-resolve via a daily sweep.
- Per-lane CLAUDE.md acknowledgement of the doctrine (mirrors the `no-bullshit` pattern).

## P11 (future protection)

Future canonical-protections-check additions to enforce non-revert:

- P11a: `automations/log-operator-utterance.ps1` exists + signature matches
- P11b: `automations/ack-operator-utterance.ps1` exists + signature matches
- P11c: CLAUDE.md cold-start contains "operator-utterances.jsonl" reference
- P11d: brain `_INDEX.md` indexes this doctrine slug

Deferred to follow-up turn (operator queue row already drops the click; protection wiring lives with the canonical-protections doctrine owner).
