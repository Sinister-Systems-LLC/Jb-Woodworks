# sinister-eve.service — typed state machine + socket protocol design

> **Author:** RKOJ-ELENO :: 2026-05-25
> **Lane:** sinister-os :: iter 18 (deferred from iter 16 per operator-interrupt priority)
> **Phase:** P3 prerequisite (operator-gated; this doc is design only, no execution)
> **Composes with:** `plans/master-plan-2026-05-24.md` §8 (Daemon spec) · `docs/architecture.md` L5 (EVE control surface) · `docs/no-function-loss-doctrine-2026-05-24.md` (typed states for cutover gate) · `_shared-memory/knowledge/sinister-sync-doctrine-2026-05-25.md` L5 (cold-start sync replay protocol)
> **Status:** draft for review — no source code lands until P2 → P3 gate flips.

## 1. Why typed states

Master-plan §8.1 describes the daemon as an untyped command loop ("receive → classify → execute → log"). That works for happy path but provides nothing to:

- Resume a partial install across a crash (no checkpoint).
- Distinguish "EVE is unhealthy" from "EVE is busy" (operator can't tell which → freeze symptoms like 2026-05-25 03:21Z reinforcement).
- Reject stale socket clients after a service restart (no epoch).
- Drive the EVE.exe Sinister Sync L5 (cold-start replay) — Sync needs a queryable state to know WHAT to replay.

This doc closes those gaps with 5 typed states + explicit transition table + socket protocol + epoch + on-disk checkpoint.

## 2. The five states

```
        ┌────────┐  start ok        ┌──────────┐
        │  BOOT  │ ───────────────► │ RUNNING  │ ──┐
        └────┬───┘                  └──────────┘   │ cmd=reboot
             │                            │ ▲      │
       start │                     SIGHUP │ │      ▼
       fails │                     reload │ │ ┌──────────┐
             ▼                            │ │ │REBOOTING │
        ┌────────┐                        ▼ │ └────┬─────┘
        │ FAILED │ ◄──── unrecoverable ───┴─┘      │ post-reboot
        └────┬───┘                                 │
             │   operator: systemctl reset-failed  │
             ▼                                     ▼
        ┌────────┐  cmd=halt        ┌──────────────┴───┐
        │ HALTED │ ◄──────────────  │      RUNNING     │
        └────────┘                  └──────────────────┘
```

| State | Meaning | Health probe response | Accepts new commands? | systemd unit state |
|---|---|---|---|---|
| `BOOT` | Reading `/etc/sinister/eve.toml`, opening socket, replaying journal | `{state:"BOOT", since_unix, progress_pct}` | NO — buffered, executed when RUNNING | `active (start)` |
| `RUNNING` | Steady state, accepting commands | `{state:"RUNNING", since_unix, in_flight_count}` | YES | `active (running)` |
| `REBOOTING` | Draining in-flight, persisting checkpoint, re-exec | `{state:"REBOOTING", since_unix, drain_left}` | NO — returns 503 | `active (reload)` |
| `HALTED` | Operator-requested stop; socket open for status only | `{state:"HALTED", since_unix, halt_reason}` | NO — returns 423 | `inactive (dead)` ‐ via `ExecStop` |
| `FAILED` | Crash / unrecoverable config / sudoers mismatch | `{state:"FAILED", since_unix, last_error, last_error_code}` | NO — returns 500 | `failed` |

State is **persisted to disk** at every transition (`/var/lib/sinister/eve/state.json`, atomic rename) so a kernel panic → reboot can resume with the last known state + epoch.

## 3. Transition table (the only legal moves)

| From | Trigger | To | Pre-condition | Post-condition |
|---|---|---|---|---|
| `init` | service start | `BOOT` | none | epoch bumped, state.json written |
| `BOOT` | journal replay done + socket bound + sudoers verified | `RUNNING` | toml parsed, sudoers allowlist hash matches `/etc/sinister/eve.lock` | clients unblocked |
| `BOOT` | toml parse error / sudoers hash mismatch / socket bind fail | `FAILED` | — | `last_error` populated |
| `RUNNING` | `SIGHUP` | `REBOOTING` | drain timeout configured | new cmds 503 |
| `RUNNING` | socket cmd `{op:"reboot"}` | `REBOOTING` | operator polkit-authorized | as above |
| `RUNNING` | socket cmd `{op:"halt"}` | `HALTED` | operator polkit-authorized | systemd `ExecStop` fires |
| `RUNNING` | unhandled exception in command loop | `FAILED` | — | `last_error` populated, journal flushed |
| `REBOOTING` | drain complete (in_flight=0 OR timeout `drain_max_sec`) | `BOOT` | — | re-exec via `systemctl restart` or exec self |
| `REBOOTING` | drain timeout AND in_flight>0 | `FAILED` | — | `last_error="drain_timeout"`, list of stuck cmd_ids in `last_error_detail` |
| `HALTED` | systemd start | `BOOT` | — | epoch bumped |
| `FAILED` | operator `systemctl reset-failed sinister-eve` + restart | `BOOT` | — | epoch bumped |

**No other transitions are legal.** Any state transition not in this table = bug → log critical + go to `FAILED`.

## 4. Epoch (the stale-client guard)

Every BOOT → RUNNING transition increments a monotonic `epoch` (u64) persisted to `/var/lib/sinister/eve/state.json`. Every socket reply embeds the epoch. Clients (eve CLI, eve-overlay, sinister-voice user service, MCP DBus bridge) cache the epoch from their first reply. If a subsequent reply's epoch is higher, the client **invalidates its session token + re-handshakes**.

This is what kills the "EVE.exe frozen on screen" symptom: the overlay client sees epoch mismatch, drops the dead socket connection, reconnects against the fresh daemon. No operator close+reopen needed.

## 5. UNIX socket protocol (the wire format)

Socket path: `/run/sinister/eve.sock` (mode `0660`, group `wheel`, owner `eve:eve`, created by systemd-tmpfiles).

Frame: length-prefixed JSON. `u32 little-endian length || utf-8 json body`. Max body 1 MiB; over → connection reset.

### 5.1 Client → daemon

```json
{
  "cmd_id": "01HZ...",         // ULID, client-generated
  "epoch_seen": 42,            // client's cached epoch; 0 = first handshake
  "op": "intent",              // intent | status | cancel | subscribe
  "args": { ... },             // op-specific
  "timeout_ms": 30000          // client-side deadline hint
}
```

### 5.2 Daemon → client (sync)

```json
{
  "cmd_id": "01HZ...",
  "epoch": 43,
  "state": "RUNNING",
  "result": "ok",              // ok | err | queued | denied | stale_epoch
  "data": { ... },
  "elapsed_ms": 12
}
```

### 5.3 Daemon → client (streaming, for long-running ops e.g. `pacman -S`)

```json
{"cmd_id":"01HZ...","epoch":43,"state":"RUNNING","stream":"progress","chunk":"resolving deps...","seq":1}
{"cmd_id":"01HZ...","epoch":43,"state":"RUNNING","stream":"progress","chunk":"60%","seq":2}
{"cmd_id":"01HZ...","epoch":43,"state":"RUNNING","stream":"end","result":"ok","exit":0,"seq":3}
```

### 5.4 Reserved `op` values

| op | args | semantics |
|---|---|---|
| `handshake` | `{client:"eve-cli|eve-overlay|sinister-voice|mcp-dbus"}` | Returns epoch + state; required first frame for new connections. |
| `status` | none | Returns full status object (state, epoch, in_flight, drain_left, last_error). |
| `intent` | `{utterance, source:"voice|hotkey|cli|mcp"}` | The command bus. Classified per master-plan §8.1 (informational / observable / mutating / destructive). |
| `cancel` | `{target_cmd_id}` | Best-effort cancel of an in-flight cmd. |
| `subscribe` | `{topics:["state","intent","log"]}` | Streams state transitions + intent results + log lines until connection closes. Used by EVE.exe Sinister Sync L5 (cold-start replay). |
| `reboot` | `{reason}` | Polkit-gated; triggers RUNNING → REBOOTING. |
| `halt` | `{reason}` | Polkit-gated; triggers RUNNING → HALTED. |

### 5.5 Reserved `result` values

| result | meaning | http-analog |
|---|---|---|
| `ok` | command completed | 200 |
| `err` | command failed; `data.error` populated | 500 |
| `queued` | mutating-action awaiting operator confirm hotkey | 202 |
| `denied` | sudoers allowlist miss + destructive policy hit | 403 |
| `stale_epoch` | client epoch < daemon epoch; client must re-handshake | 409 |
| `unavailable` | state ∈ {BOOT, REBOOTING}; retry after `data.retry_after_ms` | 503 |
| `halted` | state == HALTED; only `status` accepted | 423 |

## 6. Sudoers allowlist hash binding

`/etc/sudoers.d/eve` is the curated NOPASSWD allowlist (CLAUDE.md hard rule). To prevent drift:

1. At BOOT, daemon hashes the file (sha256) and compares against `/etc/sinister/eve.lock` (operator-signed at install time).
2. Mismatch → `FAILED` with `last_error="sudoers_hash_drift"` + the two hashes in `last_error_detail`.
3. Operator-only recovery: `eve admin sudoers-update` (a separate root tool, NOT the daemon) re-signs the lock file after operator confirms via hotkey + voice.

This prevents a malicious or accidental edit to `/etc/sudoers.d/eve` from silently expanding EVE's privilege surface.

## 7. On-disk state file format

`/var/lib/sinister/eve/state.json` (`0640`, owner `eve:wheel`):

```json
{
  "schema_version": "sinister.eve.state.v1",
  "epoch": 43,
  "state": "RUNNING",
  "since_unix": 1748143200,
  "boot_unix": 1748143198,
  "in_flight": [
    {"cmd_id":"01HZ...", "op":"intent", "started_unix":1748143405}
  ],
  "last_error": null,
  "last_error_detail": null,
  "halt_reason": null,
  "sudoers_hash": "sha256:abc123...",
  "config_hash":  "sha256:def456..."
}
```

Atomic write: `state.json.tmp` → fsync → rename to `state.json`. Read on BOOT only; runtime state is in-memory after that.

## 8. Failure-mode catalogue (the things that go FAILED)

| Trigger | Detection | `last_error` value | Recovery |
|---|---|---|---|
| `/etc/sinister/eve.toml` parse error | toml crate result | `config_parse:<line>:<col>` | operator edit + `systemctl restart sinister-eve` |
| Sudoers hash drift | sha256 compare | `sudoers_hash_drift` | `eve admin sudoers-update` |
| Socket bind fails | bind() errno | `socket_bind:<errno>` | operator check `/run/sinister/` perms |
| Drain timeout in REBOOTING | timer > `drain_max_sec` | `drain_timeout` + stuck cmd_ids | operator: `systemctl reset-failed` then restart |
| Unhandled command-loop panic | catch_unwind | `panic:<thread>:<msg>` | restart; if loops → operator inspect journal |
| Disk full on state.json write | fs errno | `state_write:<errno>` | operator: free disk, restart |
| Polkit denial on privileged op | polkit reply | `polkit_denied:<action_id>` | non-FAILED — returns `denied` to caller; logged WARN |

## 9. How this drives Sinister Sync L5 cold-start replay

Per `sinister-sync-doctrine-2026-05-25.md` L5: a fresh agent re-attaches to a project's hive-mind by replaying recent state. For sinister-os, that's the daemon journal. The `subscribe` op (5.4) with `topics:["state","intent"]` streams every state transition + intent result since the requested epoch — so a Sinister Sync client (EVE.exe overlay, agent spawn cold-start) gets a complete catch-up without polling logs.

This is the seam that connects the OS-layer daemon to the fleet-wide hive-mind. Without typed states + epoch, Sync would have to grep `/var/log/sinister/eve.jsonl` and guess.

## 10. Test plan (gates the P2 → P3 transition)

When P3 opens, the implementation gate requires every row below to pass in a VM:

| # | Test | Pass criterion |
|---|---|---|
| 1 | Cold boot from snapshot | journalctl shows BOOT → RUNNING within 2s; state.json epoch incremented |
| 2 | SIGHUP from RUNNING | state.json shows RUNNING → REBOOTING → BOOT → RUNNING; epoch +1 |
| 3 | `eve admin halt --reason test` | state=HALTED in state.json; socket returns 423 on intent |
| 4 | Corrupt toml then restart | state=FAILED; last_error=`config_parse:N:M` |
| 5 | Tamper sudoers + restart | state=FAILED; last_error=`sudoers_hash_drift` |
| 6 | Stale-epoch client | client gets `stale_epoch`; re-handshake works |
| 7 | Drain timeout (sleep cmd > drain_max_sec) | state=FAILED; stuck cmd_ids listed |
| 8 | Subscribe replay from epoch 0 | client receives every transition + intent since boot, in order, no gaps |
| 9 | Concurrent intent storm (100 parallel) | all complete or properly queue; no deadlock; in_flight stable |
| 10 | Polkit deny on destructive | result=`denied`; state still RUNNING |

All 10 must PASS before the P3 gate releases.

## 11. What is explicitly NOT in this doc

- The Rust crate layout (deferred to P3 implementation).
- Concrete `eve.toml` schema beyond master-plan §8.2 (deferred to P3).
- DBus surface (separate doc; `org.sinister.Eve` interface).
- Voice surface (`sinister-voice` user service; separate doc).
- Hotkey overlay UX (`eve-overlay`; separate doc, GTK4 already chosen).
- Recovery automation (e.g. auto-restart on FAILED) — intentionally manual until VM-stable.

## 12. Open questions (operator-gated)

1. Should `REBOOTING → FAILED` on drain timeout auto-restart, or stay FAILED until operator? (Default in this doc: stay FAILED — fail-loud over fail-silent.)
2. Polkit policy granularity — per-op, per-allowlist-entry, or coarse "operator can talk to eve"? (Default: per-op; matches systemd convention.)
3. Should `subscribe` persist across REBOOTING (re-attach by epoch) or force re-subscribe? (Default: force re-subscribe; subscription is cheap, simpler invariant.)

## 13. Author trail

- 2026-05-25 (this doc) — iter 18, sinister-os lane, RKOJ-ELENO. Drafted offline against master-plan §8 and Sinister Sync doctrine L5. No code lands until P3 opens.
- Composes with iter-16 freeze-triage inbox row (the typed-state design directly addresses the "frozen EVE.exe" failure mode via epoch invalidation, §4).
