<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# Sanctum -> Sanctum-B :: Account Manager handoff (replaces Onboarding)

**From:** Sanctum-A (subagent on `agent/sinister-sanctum/account-manager-2026-05-24`)
**To:** Sanctum-B (current `eve.py` owner)
**Operator verbatim 2026-05-24T21:50Z:**
> "change onboarding to account manager and have account managment to set
>  name, login logout. still keep this here tho the accounts status. and
>  switch to a status bar to show usage like jcode. I want the jcode usage
>  popups as well."

## What shipped (Sanctum-A)

New module: `D:\Sinister Sanctum\tools\eve-picker\account_manager.py`

Exports a single entrypoint:
```python
def show_account_manager() -> None: ...
```

Features (sister-B does NOT need to reimplement any of this):
- Header `--- Account Manager ---` (canonical per eve-ui-uniformity-doctrine).
- Calls `eve._render_accounts_panel` for the existing accounts status block
  (operator: "still keep this here tho the accounts status").
- jcode-style **usage status bar** — one line per account with:
  `idx . status-icon  label [tier]  [#########---] 80% window  today N`
  (REPLACES the sessions cur/cap row per operator: "switch to a status bar
  to show usage like jcode").
- Actions menu: `A) Add  L) Login (web)  O) Logout  R) Rename  E) Enable/Disable  D) Delete  U) Usage popup  S) refresh`.
- jcode-style **Usage popup** modal: slot/label/tier/enabled/sessions/today
  + 5h-window %  + rate-limit countdown + creds_file + recent log events
  (operator: "I want the jcode usage popups as well").
- Canonical footer: `--- B) Back  X) Exit  (number to select slot for an action) ---`.
- All shell-outs go to `claude-accounts.ps1` (SetKey / Enable / Disable /
  Remove / ResolveEmails) — no reimplementation of slot logic.
- Rename uses an in-place JSON patch because PS1 has no `-Action SetLabel`
  yet (queued sister-B follow-up: add `SetLabel` action to claude-accounts.ps1).

## What sister-B needs to change in `eve.py`

ONE thing — the bottom menu line (currently around line 1289 of eve.py):

**Before (current):**
```python
print(f"  {PURPLE}T){RESET} Quantum tools   "
      f"{PURPLE}O){RESET} Onboarding (claude accounts)   "
      f"{PURPLE}X){RESET} Exit")
```

**After:**
```python
print(f"  {PURPLE}T){RESET} Quantum tools   "
      f"{PURPLE}M){RESET} Account Manager   "
      f"{PURPLE}X){RESET} Exit")
```

And in the dispatch switch (currently dispatching `O` to `_account_onboarding_flow()`):

**Before:**
```python
elif key == "o":
    _account_onboarding_flow()
```

**After:**
```python
elif key == "m":
    try:
        import account_manager  # tools/eve-picker/ is on sys.path
        account_manager.show_account_manager()
    except ImportError as e:
        print(f"  {FAIL}[!] account_manager unavailable: {e}{RESET}")
        time.sleep(1.5)
```

The old `_account_onboarding_flow()` function can stay defined (no callers
will reach it after the menu swap) or be removed in a follow-up commit.
Sanctum-A did not edit eve.py per the explicit handoff constraint
("Do NOT edit eve.py — sister-B has it").

## Smoke-test results (Sanctum-A side)

```
$ python -c "import sys; sys.path.insert(0,'D:/Sinister Sanctum/tools/eve-picker'); import account_manager"
# parse-clean, no errors

$ python D:/Sinister\ Sanctum/tools/eve-picker/account_manager.py --smoke
# renders status block + usage status bar against live accounts.json
# 4 accounts loaded, OK
```

## Coordination notes

- New file ONLY. No edits to `eve.py`. No edits to `claude-accounts.ps1`.
- `_shared-memory/claude-accounts.json` schema unchanged (read-only except
  for the rename action's `label` field patch — safe, no field additions).
- Sister-B owns the `O -> M` menu hotkey switch + the dispatcher arm.
- Follow-up (sister-B's choice): add `-Action SetLabel -Name X -Label Y`
  to `claude-accounts.ps1` so Rename can use PS1 instead of direct JSON
  patch (current implementation is correct + safe but less consistent).

— Sanctum-A · 2026-05-24T21:55Z
