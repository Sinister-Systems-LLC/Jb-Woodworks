# Cross-machine mesh coordination

> Author: RKOJ-ELENO :: 2026-05-25

## Why

`mesh-coordinator.ps1` was built for the multi-EVE-session-on-one-machine
scenario. With Sinister LINK pairing operator (eleno) + Leo's workstations,
the same lock primitive now spans two machines. Without `owner_machine` in
the lock record, both peers would see the same `<focus>.json` lock and
neither could tell whether the holder was a local sister agent or the peer.

## The extension (this iteration)

- **New field** in every lock written by `Register`: `owner_machine`
  (lowercased `$env:COMPUTERNAME` OR — preferred — the `local_machine`
  field from `_shared-memory/sinister-link-state.json` so the value
  matches what the peer sees in their synced copy).
- **`Check` action**: now prints `LOCKED [PEER]:` when the lock's
  `owner_machine` differs from the local machine id. Exit code 1 unchanged
  (still a conflict — pick a different slice).
- **New `List` columns**: `Loc` (`LOCAL`/`PEER`/`UNK`) and `Machine`.
- **New `ListPeer` action**: scoped to peer-owned locks only. Reads
  `sinister-link-state.json` to determine peer machine id; returns a
  table of every active peer lock so operator can see "what is Leo doing
  right now".

## Backward compatibility

Locks written before this iteration lack `owner_machine`. `Check` treats
those as `UNK` (no `[PEER]` flag; just `LOCKED:`). New locks immediately
get the field. `Sweep` removes expired locks regardless; in 30 minutes
all locks will carry the new field.

## Consume in agent workflows

Before editing a shared file (anything in `automations/`, `CLAUDE.md`,
brain `_INDEX.md`, `projects.json`, etc.):

```
powershell -File automations\mesh-coordinator.ps1 -Action Check -Focus <path-or-topic>
```

- Exit 0 + `CLEAR:` -> safe, proceed.
- Exit 1 + `LOCKED:` -> local sister agent owns; inbox them or pick
  different slice.
- Exit 1 + `LOCKED [PEER]:` -> peer (Leo) owns; inbox or pick different
  slice OR (if blocking) ping operator OOB.

## Future: handoff protocol

Composes with cross-agent inbox: when a peer-owned lock blocks you, drop
an inbox row addressed to the peer's slug describing what you want and
when you need it by. Peer's lane agent reads it on next cold-start poll
and either Releases the lock + responds OR explains the conflict.

## Smoke evidence

Synthetic peer lock written to `_shared-memory/mesh-locks/projects_
sinister-os_kernel-apk.ts.json` with `owner_machine: "fake-leo-machine"`
while sinister-link-state declared `peer.name: "fake-leo-machine"`:

- `ListPeer` -> "Peer (fake-leo-machine) active locks: ... leo-kernel-apk
  / projects/sinister-os/kernel-apk.ts / ACTIVE"
- `Check -Focus projects/sinister-os/kernel-apk.ts` ->
  `LOCKED [PEER]: ... by leo-kernel-apk@fake-leo-machine ... exit 1`

Verified 2026-05-25.

## Composes with

- `sinister-link-doctrine-2026-05-25` — provides the peer id used here
- `mesh-coordination-and-resource-lifecycle-2026-05-24` — base doctrine
- `gradual-growth-memory-push-eve-exe-ready-2026-05-24` — operator sees
  peer locks in EVE.exe `L)` sub-page `V)` action
