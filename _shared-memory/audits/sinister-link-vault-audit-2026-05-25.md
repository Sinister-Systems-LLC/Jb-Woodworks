# Sinister LINK + Vault Audit (iter-23 sub-5)

**Author:** RKOJ-ELENO :: 2026-05-25 (sanctum lane; sub-agent a98fd007facfa0370, persisted by sanctum master)
**Operator utterance:** 2026-05-25T07:08:40Z — *"[Image 5: EVE Sinister LINK page state=unlinked, operator hit P) Generate invite at 'expires in N minutes [60]' prompt] i need the sinister link system to work so leo and i can connect our eve's like we talked about. place the sinister vault live and place the entire sinster sanctum there and link to leo over sinister link and auto update that and github. and backup."*

## Root cause (3 sentences)

The LINK page shows `state=unlinked` after invite generation because `sinister-link-state.json` is only written by the `AcceptInvite` action; `GenerateInvite` does NOT write the state file. The state-flip logic (`sinister-link.ps1:225-226`) checks `if ($s) { $stateWord = 'linked' }`, meaning state is unlinked until the state file exists. Operator pressing P at the "expires in N minutes [60]" prompt triggers `GenerateInvite -ExpiresMin N` (`eve.py:2280`) — working-as-designed: it generates an invite but does NOT pair; Leo must accept it first (AcceptInvite action) on his end.

## 1. State diagnosis

- `sinister-link-state.json` is **absent** (confirmed by poll log: `"state": "absent"`).
- State-flip logic at `sinister-link.ps1:225-226`: `if ($s) { $stateWord = 'linked' }` — hardcodes `unlinked` when state file doesn't exist.
- `GenerateInvite` action (`sinister-link.ps1:285-356`) creates invite record in `_shared-memory/sinister-link-invites/` but **never calls `Write-State`**.
- `AcceptInvite` action (`sinister-link.ps1:359-405`) **does** call `Write-State` (line 391).
- Header render reads state file: `main_menu.py:322-330` (`LINK_STATE_JSON.exists()`).

**Verdict:** by design; but UX is opaque.

## 2. Invite-expiry prompt flow

| Step | What happens | Where |
|---|---|---|
| 1 | Operator presses `L` → LINK page | `eve.py:_sinister_link_page` |
| 2 | Operator presses `P` → prompt `"expires in N minutes [60]:"` | `eve.py:2275` |
| 3 | Operator enters value or Enter (defaults to 60) | `eve.py:2276` |
| 4 | System invokes `GenerateInvite -ExpiresMin <N>` | `eve.py:2280` |
| 5 | System prints base64 invite code | `sinister-link.ps1:323`, displayed `eve.py:2287-2288` |
| 6 | Operator copies + sends OOB to Leo |  |
| 7 | (Expected) Leo pastes into his EVE → `L) Accept invite Code` → both `state=linked` |  |

**Bug:** step 4 succeeds but operator's state file stays missing. Main menu still shows `unlinked`. **UX bug; mostly WAD otherwise.**

## 3. Sinister Vault status

- **NOT live in production.** Daemon NOT running on `:5078`.
- Exists in worktrees only (`tools/sinister-vault/`, `tools/sanctum-git/vault-integration.md`).
- Install artifacts present: `install-vault-task.ps1` + `vault-daemon.bat` + `AUTOSTART.md`.
- **No `_vault/` directory at repo root; no data committed.**
- All 4 existing invites use `"transport": "git"` (none use vault transport).
- Poller assumes git (`sinister_link_poller.py:110-111`).

**Vault readiness: 0% live.**

## 4. Gap to operator's ask — 4 deliverables

| # | Deliverable | Files to touch | Effort |
|---|---|---|---|
| **A** | State-file feedback post-invite (operator sees "invited (awaiting Leo)" instead of "unlinked") | `sinister-link.ps1:356` (write state stub); `main_menu.py:306-351` (render new state) | ~15 LOC |
| **B** | Sinister Vault live on `:5078` (both machines) | `deploy/vault-setup.py` (NEW); `automations/install-sinister-link-poller.ps1` (append vault call); `tools/sinister-vault/install-vault-task.ps1` (idempotent) | ~40 LOC + 2 scripts |
| **C** | Auto-place Sanctum into Vault every 5min | `automations/vault-sync.py` (NEW); called by daemon or poller; populates `_vault/<machine>/sanctum/<utc>/` snapshot | ~80 LOC + schedule |
| **D** | Auto-sync to Leo + GitHub + backup (3-day rolling) | poller already syncs (existing); `sanctum-auto-push.ps1` already does GitHub (existing); add `_vault/` retention policy | ~30 LOC + cleanup |

## 5. Quick wins (<30 LOC each)

1. **State stub on invite gen** (`sinister-link.ps1:356`) — after persist invite, write `{state:"invited", invited_at_utc:$now, peer:{...}}`. Main menu shows orange "LINK :: invited (awaiting Leo)". ~12 LOC.
2. **P prompt sub-menu** (`eve.py:2274-2278`) — `[60] / [120] / [480] / [custom]` quick picks. ~18 LOC.
3. **"Last invite" in Status output** (`sinister-link.ps1:249-282`) — read `_shared-memory/sinister-link-invites/`, show most-recent + remaining minutes. ~25 LOC.

## 6. Larger items

| Item | Effort |
|---|---|
| Vault live (daemon + schtask + snapshot machinery) | 4-6h |
| Sanctum auto-place into Vault | 6-8h |
| Leo auto-setup wizard (paste invite at first launch) | 3-5h |
| Backup + retention policy | 2-3h |
| **Total** | **~15-22h to fully ship** |

## 7. Immediate blockers

1. Leo must run `AcceptInvite` to write paired state file.
2. Vault daemon unstarted — no `:5078`.
3. Leo doesn't have EVE.exe or sanctum branch yet — needs onboard wizard or manual clone.

## Path forward (ordered)

1. Ship quick win #1 (state stub) THIS iter — operator gets visual feedback immediately.
2. Inbox-handoff to parallel sanctum exec lane: quick win #2 + #3 (eve.py sub-menu + Status invite list).
3. Queue larger items #B / #C / #D as separate sub-plans under `_shared-memory/plans/sinister-vault-live-2026-05-25/` etc.
4. Leo onboard wizard intersects with existing `deploy/first_time_setup.py` (commit e9e4379) — extend, don't duplicate.

(Full per-line evidence available in sub-agent transcript a98fd007facfa0370; this file is the actionable summary.)
