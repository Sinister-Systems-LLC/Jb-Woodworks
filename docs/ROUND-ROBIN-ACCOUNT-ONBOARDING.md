<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# Round-Robin Claude Account Onboarding

Operator-facing walkthrough for adding the 2nd / 3rd / 4th Claude account to the round-robin rotation. Sanctum currently has 4 slots: `operator`, `leo`, `slot3`, `slot4` — only `operator` is enabled by default.

**Verify current state first:**
```
powershell -File "D:\Sinister Sanctum\automations\claude-accounts.ps1" -Action Status
```
You'll see a table with `[ON]` or `[OFF]` per slot and `sessions=N/M` counts.

---

## Path A — API Key onboarding (recommended, works today)

Use this when you have an **Anthropic API key** (`sk-ant-...`) for the account. The launcher exports it as `ANTHROPIC_API_KEY` before spawning `claude`, so each round-robin pick uses the right key automatically.

**Steps (≈30 seconds per account):**

1. **Get the key.** Log into `console.anthropic.com` under that account → **Settings → API Keys → Create Key**. Copy the `sk-ant-…` string.

2. **Bind it to a slot.** Pick a slot name from the disabled list (run `-Action Status` if unsure). For your 2nd account you'd usually use `leo`; for the 3rd, `slot3`:
   ```
   powershell -File "D:\Sinister Sanctum\automations\claude-accounts.ps1" -Action SetKey -Name leo -ApiKey sk-ant-XXXXX -Label "Account 2 (your-email)"
   ```
   That single command (a) writes the credentials file to `C:\Users\Zonia\.claude\credentials.leo.json`, (b) flips `enabled=true`, (c) saves config. Output ends with `[OK] Slot 'leo' configured + enabled.`

3. **Verify rotation sees it:**
   ```
   powershell -File "D:\Sinister Sanctum\automations\claude-accounts.ps1" -Action Status
   ```
   You should now see `[ON]` next to `leo` and `enabled: 2 / 4`.

4. **Smoke test the lease:**
   ```
   powershell -File "D:\Sinister Sanctum\automations\claude-accounts.ps1" -Action Test -Name leo
   ```
   Expected: `[PASS] 'leo' credentials valid (api_key=sk-ant-...)`.

5. **Watch it in action.** Launch EVE.exe (Sinister Start.bat). The new banner line `accounts  ON operator/N  ON leo/N  off slot3  off slot4    rotation=round-robin-strict` confirms the slot is live. Each new spawn alternates — the `successful_spawns_today` counter on each account is the proof.

**Repeat for slot3 / slot4** when you have keys for those.

---

## Path B — Claude Max plan (OAuth) — **not yet supported, gap noted**

If you have multiple Claude Max plan **subscriptions** (claude.ai logins) and want to round-robin across them WITHOUT pulling per-account API keys, that path doesn't work yet in the current launcher.

**Why:** `claude login` (OAuth flow) writes to a single fixed path `~/.claude/credentials.json`. There's no built-in way to keep 2+ active OAuth credentials and tell `claude` which one to use per spawn. The launcher's current rotation only injects `ANTHROPIC_API_KEY`, which forces metered-API billing (the API key gets charged), not Max-plan billing.

**Workaround options if you want OAuth-mode rotation:**

- **(A)** Stay on API-key mode (Path A) for round-robin; keep your Max-plan OAuth as a fallback for the `operator` slot only. Metered API isn't free but for sub-account spawns it's fine.
- **(B)** I build a per-slot OAuth shim — back up `credentials.json` to `credentials.<name>.json` after each `claude login`, then symlink/copy the right one in before each spawn. Doable in ~50 LOC. Ask if you want this and I'll ship it.
- **(C)** Wait for upstream `claude` CLI to support `--credentials <path>`. Not on their public roadmap as of 2026-05-24.

---

## Common operator questions

**Q: Do I need an API key per account?**
A: For Path A (current working rotation): yes — one `sk-ant-…` per slot. For Path B (Max plan rotation): no, but that mode isn't supported today.

**Q: Can I mix? (1 OAuth account + 2 API keys?)**
A: Yes. Leave the `operator` slot using OAuth (its `credentials_file` can be empty / not yet written — the launcher then falls back to `claude`'s own login at `~/.claude/credentials.json`). Use SetKey for `leo` / `slot3` / `slot4`. Mixed rotation works; the operator slot just doesn't get an env-injected key.

**Q: How do I disable a slot temporarily?**
A: `powershell -File "...claude-accounts.ps1" -Action Disable -Name leo` (flips `enabled=false` — rotation skips it). Re-enable with `-Action Enable -Name leo`.

**Q: How do I rotate API keys?**
A: Re-run `-Action SetKey -Name <slot> -ApiKey sk-ant-NEW`. It overwrites the credentials file in-place.

**Q: Where do the spawns actually pick which account?**
A: `automations/start-sinister-session.ps1` line ~1290 (`Get-NextAvailableAccount`) → reads `_shared-memory/claude-accounts.json` → applies the rotation strategy (currently `round-robin-strict` per the file's top field) → returns the slot name → its `api_key` is env-injected into the spawned shell via `ANTHROPIC_API_KEY='…'`.

**Q: Will the new banner line show all accounts?**
A: Yes — after the latest eve.py change, the banner has a one-line `accounts` row showing each slot's enabled state + spawns today + the rotation strategy.

---

## Doctrine + lineage

- Strategy choices (`round-robin-strict` / `burn-first` / `load-balance`) defined in `claude-accounts.ps1` `Get-NextAvailableAccount`.
- Atomic round-robin (4-parallel-safe) shipped 2026-05-24 19:31Z (mesh-safety doctrine).
- Reconcile-AccountSessions (stale-lease drain) shipped 2026-05-24 19:48Z (refcount-cleanup doctrine).
- Composes with: `agent-autonomy-push-and-completion-2026-05-23`, `resource-refcount-cleanup-sleep-wake-doctrine-2026-05-24`, `no-bullshit-tested-before-claimed-doctrine-2026-05-23`.
