# EVE Update over Sinister LINK + Popup Doctrine

> **Author:** RKOJ-ELENO :: 2026-05-25 (Sub-O)
> **Created:** 2026-05-25
> **Status:** active
> **Tags:** eve-self-update, sinister-link, popup, leo-deploy, vault-mirror

## Operator verbatim (2026-05-25 ~07:12Z)

> *"make the eexe update oiver sinsiter link and leo will have popup to say update availabe or something"*

## TL;DR

Two transports, three popup layers, one keystroke install:

- **Primary transport (LINK):** read EVE.exe + EVE.exe.sha256 from `_vault/sanctum-mirror/<peer-id>/` (already replicated by Sub-M vault daemon). Filesystem-local copy, no HTTP.
- **Fallback transport (github):** `https://raw.githubusercontent.com/Sinister-Systems-LLC/Sinister-Sanctum/main/EVE.exe[.sha256]` (preserves Sub-C/F's original logic).
- **Selector:** `--transport <github|link|auto>` (default `auto` = LINK first, GitHub fallback).
- **Popup waterfall (notifier daemon, 60s schtask):** A) marker file consumed by EVE.exe main_menu banner → B) Windows toast (ToastNotificationManager COM, best-effort) → C) stdout banner.
- **Install:** one keystroke (`U`) in EVE.exe re-runs `eve_self_update.py --transport link --peer <id>`; hot-swap via Sub-F's rename-in-use; marker cleared automatically.

## Pass criterion

- Operator pushes new EVE.exe → Sub-N mirrors to vault → Sub-M replicates to Leo's mirror → Leo's `SinisterEveUpdateNotifier` schtask detects drift within 60s → popup fires (A+B+C) → Leo presses U → hot-swap succeeds without restarting running EVE.exe → marker auto-clears → total elapsed ≤120 seconds + ≤5 seconds for keystroke→swap.
- `python automations/eve_self_update.py --audit` with NO transport flag returns exit 0 + reports github transport unchanged (backward compat).
- `python automations/eve_self_update.py --transport link --dry-run --audit` returns exit 0 + reports `link-unreachable` gracefully when vault mirror empty.
- `python automations/eve_update_notifier.py --scan --once` returns exit 0 with no marker when no peer mirror present.
- `python automations/eve_update_notifier.py --clear` returns exit 0 whether marker exists or not.

## 2-transport architecture

| Layer | Source | Function | New in Sub-O |
|---|---|---|---|
| LINK resolver | `_vault/sanctum-mirror/<peer>/EVE.exe.sha256` | `_resolve_link_update_source(peer)` | yes |
| LINK copier | `_vault/sanctum-mirror/<peer>/EVE.exe` | `copy_from_link(peer_bin, dest)` | yes |
| GitHub resolver | `raw.githubusercontent.com/.../EVE.exe.sha256` | `get_remote_eve_sha()` | preserved |
| GitHub downloader | same with `EVE.exe` | `download_with_retry(url, dest)` | preserved |
| Transport selector | union of both | `_resolve_transport(transport, peer)` | yes |
| Swap (locked or not) | Sub-F | `swap_with_kill_fallback()` + `rename_old_then_swap()` | preserved |

Peer pick order: explicit `--peer` → hint file `_shared-memory/eve-update-peer.txt` → first peer with full payload → first peer with sha sidecar → none.

## 3-layer popup waterfall

| Layer | Mechanism | Consumed by | Failure behavior |
|---|---|---|---|
| **A. Marker file** | Write `_shared-memory/eve-update-available.json` with peer/sha/install_cmd | `eve.py` main_menu re-render (Sub-G integration TODO documented in `deploy/EVE-UPDATE-OVER-LINK.md`) | If eve.py not yet integrated, marker is harmless human-readable JSON |
| **B. Toast** | PowerShell COM bridge to `ToastNotificationManager` | Windows Action Center | Silent skip on non-Windows / no PowerShell / Focus Assist |
| **C. Stdout** | `print(...)` to caller's terminal | Terminal foreground user | Always works (no dependencies) |

All three fire on every detected drift; later layers DON'T depend on earlier success. Layer A is idempotent — same (peer_sha, local_sha, peer) tuple skips rewrite.

## 5 anti-patterns

1. **Silent update without consent** — DO NOT install on drift detection. The notifier ONLY detects + popups; install is delegated to the operator/Leo pressing U. Reason: hot-swap of a running EVE.exe is mostly safe but still a side-effect; Leo deserves to know.
2. **No fallback transport** — `--transport link` with vault unreachable must NOT mask the failure by hanging or crashing. Auto mode falls back to GitHub silently; explicit `link` returns `link-unreachable` + exit 0 + structured log row.
3. **Popup spam every poll** — marker writer is idempotent. Toast fires once per drift transition (deduped via marker presence check in next iter). Stdout always fires (CLI ergonomics expectation).
4. **Not clearing marker after install** — `eve_self_update.py` post-install (or eve.py U-handler) MUST call `eve_update_notifier.py --clear` so the banner disappears. Leaving a stale marker = phantom "update available" indefinitely.
5. **Breaking existing GitHub transport** — Sub-O's flags ADD; they don't remove. `--transport github` (or omitted on legacy callers) yields identical behavior to pre-Sub-O. Audit with no transport flag still returns exit 0 + same output shape (just adds `transport`/`peer_resolved` keys to the JSON log row).

## Files

| Path | LOC | Role |
|---|---|---|
| `automations/eve_self_update.py` | ~970 (was 834; +136) | Extended: LINK transport + `--transport`/`--peer` flags |
| `automations/eve_update_notifier.py` | ~340 | NEW: drift detector + 3-layer popup + schtask installer + `--clear` |
| `deploy/EVE-UPDATE-OVER-LINK.md` | ~150 | NEW: operator + Leo facing doc |
| `_shared-memory/eve-update-available.json` | runtime marker | Written by notifier; consumed by EVE.exe banner |
| `_shared-memory/eve-update-notifier-log.jsonl` | append-only | Structured event log |
| `_shared-memory/eve-update-peer.txt` | optional | Operator hint for default peer |

## Composes with

- `eve-self-update` doctrine (Sub-C original transport, Sub-F hot-swap) — preserved verbatim.
- `leo-deploy-folder-bootstrap-doctrine-2026-05-25` — Leo's deploy/ folder ships EVE.exe; this doctrine keeps it fresh post-install.
- `sinister-vault-live` (Sub-M) — provides the `_vault/sanctum-mirror/<peer>/` filesystem subtree this doctrine reads.
- `vault-github-sync` (Sub-N) — provides operator-side push from repo root → vault mirror.
- `automate-everything-no-operator-admin-2026-05-25` — no operator clicks; notifier installs its own schtask via `schtasks.exe`.
- `no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25` — pure Python; schtasks.exe + powershell.exe called inline only.
- `eve-ui-uniformity-doctrine-2026-05-24` — banner uses canonical color tokens (ORANGE/BRIGHTP/RESET).

## CLI cheat-sheet

```bash
# Updater (Sub-C+F+O combined)
python automations/eve_self_update.py                                  # default: github transport, hot-swap on
python automations/eve_self_update.py --transport auto                 # LINK first, github fallback
python automations/eve_self_update.py --transport link --peer rkoj     # force LINK from specific peer
python automations/eve_self_update.py --audit                          # report only (no flags = backward compat)
python automations/eve_self_update.py --audit --transport link         # report LINK state

# Notifier (Sub-O)
python automations/eve_update_notifier.py --scan --once                # one-shot check
python automations/eve_update_notifier.py --watch                      # 60s loop
python automations/eve_update_notifier.py --install-schtask            # register SinisterEveUpdateNotifier
python automations/eve_update_notifier.py --clear                      # remove marker after install
```

## Future work

- Sub-G follow-up: wire the marker-check into `tools/eve-picker/main_menu.py` (~25 LOC; details in `deploy/EVE-UPDATE-OVER-LINK.md`).
- Sub-M follow-up: when vault HTTP at :5078 is up, optionally bypass filesystem mirror via `sinister_link_vault_transport.py --pull <invite> --payload EVE.exe` for peers behind NAT.
- Multi-peer election: if two peers diverge with different shas, currently pick first-alphabetical; future = pick the highest-sha-seen-most-recently per `vault-github-sync` ledger.
