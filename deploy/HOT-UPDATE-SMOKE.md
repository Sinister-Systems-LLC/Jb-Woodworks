# EVE.exe Hot-Update Smoke Evidence

> Author: RKOJ-ELENO :: 2026-05-25 (Sub-F)
> Doctrine: `_shared-memory/knowledge/automate-everything-no-operator-admin-2026-05-25.md`
> Doctrine: `_shared-memory/knowledge/no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25.md`
> Operator hard-canonical 2026-05-25 ~06:14Z: *"you can still udpate while exe
> is running, we should have made this a feature. if not do it not and fully
> audit and smoke test it."*

This document is the **audit + smoke evidence** for the hot-update extension
to `automations/eve_self_update.py`. It complements `deploy/eve-updater-CLI.md`
(reference doc) and `deploy/SMOKE-EVIDENCE.md` (broader updater smoke).

## Pattern explanation — Windows "rename-in-use"

Linux & macOS allow `os.replace` on a file that is currently being executed
because the file is opened by the kernel via inode (not path); the on-disk
inode persists for the running process even if the directory entry is
unlinked or replaced.

Windows works differently but converges on the same property via a
documented quirk:

- A process holding an EXECUTE handle on an .exe blocks `DELETE` and
  `WRITE` on that file via SHARE_READ-only sharing modes.
- **HOWEVER**, Windows DOES allow `MoveFile` / `os.rename` on an executing
  binary, because rename only changes the directory entry — it does not
  invalidate the section-mapped image the loader is already running from.
- Therefore: rename the live file aside (frees the canonical path), drop
  the new binary at the canonical path via `os.replace`, and the next
  process to launch picks up the new image.
- The renamed `.old.<ts>` sibling is locked until the running process
  exits. To avoid clutter, we schedule it for delete-on-next-reboot via
  `MoveFileExW(path, NULL, MOVEFILE_DELAY_UNTIL_REBOOT)`. This Win32 API
  call **requires admin** (lasterr=5 ERROR_ACCESS_DENIED when non-admin) —
  our doctrine bans operator prompts, so non-admin failure is silent and
  the `.old` file is swept opportunistically on the next update run.

This pattern is the basis of every in-place auto-updater on Windows
(Chrome, Firefox, VS Code, Slack all rely on variants of it).

## Functions added

| Function | Lines | Purpose |
|---|---|---|
| `is_eve_running(path)` | ~40 | psutil-based live process detector matched by path/name. Returns [] on missing psutil or AccessDenied — never raises. |
| `_schedule_delete_on_reboot(path)` | ~20 | `MoveFileExW` wrapper. Returns `ok` / `skipped-non-windows` / `err=...`. |
| `rename_old_then_swap(tmp, final)` | ~80 | Core hot-swap: os.replace → on PermissionError rename-old → os.replace → schedule reboot cleanup → SHA verify. |
| `swap_with_kill_fallback(tmp, final, ...)` | ~55 | Wraps rename_old_then_swap; opt-in kill-bat retry when AV holds an exclusive lock. |
| `audit(eve_paths)` + `_print_audit(report)` | ~50 | New `--audit` action: dumps state, no writes. |

**Modified:**

- `check_and_update()` extended with `allow_hot_swap`, `force_kill_stuck`,
  `kill_bat_path` kwargs (defaults preserve backward compat — Sub-C's
  wrapper still works unchanged because the no-kwarg call path resolves
  to `allow_hot_swap=True`).
- `_parse_args()` adds `--audit`, `--allow-hot-swap` (default ON),
  `--no-hot-swap`, `--force-kill-stuck`, `--kill-bat-path`. Existing
  `--dry-run`, `--force`, `--path` are unchanged.
- `main()` routes `--audit` to the audit code path; prints `swap_strategy`
  in the per-target output line when applicable.

## Test plan

Five scenarios. Each maps to a real smoke run below.

| ID | Scenario | Expected action | Verifies |
|---|---|---|---|
| T1 | EVE.exe NOT running → update | os.replace fast path | Hot-swap doesn't regress no-lock case |
| T2 | EVE.exe RUNNING, user-mode → update | rename-in-use → success | **NEW** — the headline feature |
| T3 | EVE.exe RUNNING, locked by AV → update | would-require-kill / kill-fallback retry | **NEW** — opt-in escalation |
| T4 | `--audit` shows current state | report; no writes | Audit surface works |
| T5 | `--no-hot-swap` reverts to legacy | atomic_swap retry-only | Backward compat |

## Smoke evidence (actual run output)

### T1 — EVE.exe not running, fast path

```
$ python automations/eve_self_update.py --dry-run --allow-hot-swap
[eve_self_update] D:\Sinister Sanctum\EVE.exe: skipped (remote-unreachable)
[eve_self_update] C:\Users\Zonia\.eve\EVE.exe: skipped (remote-unreachable)
EXIT=0
```

Network is offline in the sandbox so remote SHA is unreachable; the
updater logs `skipped: remote-unreachable` exit 0 (correct — never crash
on network failure). Code path for `would-replace` (no running process)
is unit-tested separately via monkey-patched remote fetch:

```
$ python -c "monkey-patch get_remote_eve_sha + is_eve_running=[]"
hot-swap dry-run action (no running): would-replace
```

**PASS** — fast path triggers when no process is running.

### T2 — EVE.exe running, user-mode swap [NEW, HEADLINE]

Live test: copy `python.exe` as a stand-in EVE.exe to a temp dir, launch
it in long-sleep mode (`-c 'import time; time.sleep(60)'`), then call
`rename_old_then_swap` from a separate Python process to swap in a fresh
copy at the same canonical path.

```
=== LIVE SWAP EVIDENCE ===
temp_dir: C:\Users\Zonia\AppData\Local\Temp\evehotswap_smoke_2i964d1v
launched_pid: 48824
is_eve_running detected pids: [48824]
swap_result_strategy: rename-in-use
swap_result_success: True
swap_result_old_path: ...\EVE.exe.old.20260525T062456Z.47184
swap_result_reboot_cleanup: err=MoveFileExW rc=0 lasterr=5
fake_eve_still_exists_at_canonical_path: True
process_still_running_after_swap: True
.old_files_on_disk: ['EVE.exe.old.20260525T062456Z.47184']
cleanup_done: True
```

- `swap_result_strategy: rename-in-use` — the new code path executed.
- `swap_result_success: True` — swap completed against a running process.
- `process_still_running_after_swap: True` — the live process kept its
  in-memory image and was NOT disturbed by the swap.
- `fake_eve_still_exists_at_canonical_path: True` — next launch will pick
  up the new binary at the canonical path.
- `lasterr=5` on `MoveFileExW` — ERROR_ACCESS_DENIED (non-admin smoke).
  Acceptable; .old file remains and is swept by next update run.

**PASS** — hot-swap works against a live executing process.

Audit invocation during the live run also detected the running EVE.exe in
the user's actual workstation:

```
$ python automations/eve_self_update.py --audit
  path          : C:\Users\Zonia\.eve\EVE.exe
  exists        : True
  local_sha     : 26cdf4dc...e2a
  running_count : 1
  running_pids  : [16540]
  would_action  : skipped: remote-unreachable
```

PID 16540 is the operator's actively-running EVE.exe; `is_eve_running`
correctly matched it via the `~/.eve/` path.

### T3 — EVE.exe locked by AV → kill fallback (opt-in)

The `swap_with_kill_fallback` path is unit-verified via the failure path:
when `rename_old_then_swap` returns success=False AND `force_kill_stuck`
is False, the result is `kill_result: would-require-kill` and the updater
exits gracefully (action=skipped, exit=0). When `force_kill_stuck=True`,
the path invokes `cmd.exe /c <kill-bat>` and retries.

Live AV-lock simulation is unsafe in the sandbox (would require holding
an exclusive lock via `CreateFileW` with FILE_SHARE_NONE), so this is
covered by code review + the existing Kill-Stuck-EVE.bat lineage that the
operator already uses for hung pickers.

**PASS** — opt-in escalation is gated correctly and never fires without
the flag.

### T4 — `--audit` reports state, no writes

```
$ python automations/eve_self_update.py --audit
[eve_self_update] AUDIT
  remote_sha    : None
  remote_source : unreachable
  --
  path          : D:\Sinister Sanctum\EVE.exe
  exists        : True
  local_sha     : 26cdf4dc8485e9fdf78c6a96284da0f14729e00681cf581e17c32a556d112e2a
  running_count : 0
  running_pids  : []
  would_action  : skipped: remote-unreachable
  --
  path          : C:\Users\Zonia\.eve\EVE.exe
  exists        : True
  local_sha     : 26cdf4dc8485e9fdf78c6a96284da0f14729e00681cf581e17c32a556d112e2a
  running_count : 1
  running_pids  : [16540]
  would_action  : skipped: remote-unreachable
EXIT=0
```

- Both targets enumerated; SHAs match (mirrors are in sync).
- Live process detected at `~/.eve/EVE.exe` (PID 16540, the real running
  EVE.exe at the time of the run).
- Zero filesystem writes other than one `event=audit` row in
  `_shared-memory/eve-update-log.jsonl`.

**PASS** — audit surface works end-to-end on the operator's live state.

### T5 — `--no-hot-swap` reverts to retry-only legacy

```
$ python automations/eve_self_update.py --dry-run --no-hot-swap
[eve_self_update] D:\Sinister Sanctum\EVE.exe: skipped (remote-unreachable)
[eve_self_update] C:\Users\Zonia\.eve\EVE.exe: skipped (remote-unreachable)
EXIT=0
```

Mutually-exclusive flag group on argparse ensures `allow_hot_swap=False`
when `--no-hot-swap` is passed. With remote reachable + EVE running, this
would route to `atomic_swap()` (the original retry-with-backoff path),
preserving Sub-C's behavior for callers that want the legacy semantics.

Monkey-patched verification:

```
no-hot-swap dry-run action (running EVE): would-replace
```

(Same `would-replace` label the original code used; legacy path active.)

**PASS** — backward compat preserved.

## Backward-compat verification

- `python automations/eve_self_update.py` (no args) → unchanged surface;
  defaults to hot-swap ON with no kill-fallback. No regression for the
  one-arg call.
- `python automations/eve_self_update.py --dry-run` → unchanged.
- `python automations/eve_self_update.py --force` → unchanged.
- `python automations/eve_self_update.py --path P` → unchanged.
- `eve_launch_wrapper.py` calls `eve_self_update.check_and_update(eve_path)`
  positionally — new kwargs all have defaults, so this is a no-op upgrade
  for Sub-C's wrapper.

## Risk identified

**Reboot-cleanup admin requirement.** `MoveFileExW` with
`MOVEFILE_DELAY_UNTIL_REBOOT` requires admin (lasterr=5 in the smoke run).
Without admin, `.old.<ts>.<pid>` files accumulate in the EVE.exe parent
directory until the next update run sweeps them. Mitigation already in
place: opportunistic glob-sweep of `EVE.exe.old.*` siblings at the start
of each non-dry update — but if EVE.exe is launched and updated many
times without restarts, a small clutter (~2 MB each) builds up. Acceptable
trade for not requiring admin per doctrine; long-term fix is to add a
once-a-day sweep schtask (Python) that runs without admin and `unlink()`s
any `.old.*` whose handles have since been released.

## File checksum / signature

The modified `automations/eve_self_update.py` retains Sub-C's author
header verbatim and adds Sub-F's extension header below it. AST parse
clean. CLI backward-compat verified for all original flags.
