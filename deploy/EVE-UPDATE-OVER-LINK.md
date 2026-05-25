# EVE.exe Update over Sinister LINK + Popup

> **Author:** RKOJ-ELENO :: 2026-05-25 (Sub-O)
> **Operator directive (verbatim 2026-05-25 ~07:12Z):** *"make the eexe update oiver sinsiter link and leo will have popup to say update availabe or something"*
> **Audience:** operator + Leo (deploy/ partner workstation)
> **Doctrine:** `_shared-memory/knowledge/eve-update-over-link-and-popup-doctrine-2026-05-25.md`

This document explains how EVE.exe updates flow from the operator's machine to Leo's machine over the Sinister LINK vault (peer-to-peer), how the popup wakes Leo up within ~120 seconds, and how the install completes in one keystroke without restarting a running EVE.exe.

---

## 2-transport architecture

Updates ride one of two transports. The default is `auto`: try LINK first, fall back to GitHub if the vault mirror is empty/unreachable.

| Transport | Source | Speed | Auth required | Notes |
|---|---|---|---|---|
| `link` | `_vault/sanctum-mirror/<peer-id>/EVE.exe` (filesystem) | sub-second | none (already replicated) | Sub-M vault daemon must be running on BOTH peers. |
| `github` | `https://raw.githubusercontent.com/Sinister-Systems-LLC/Sinister-Sanctum/main/EVE.exe` | seconds | none (public raw URL) | The fallback path. Operator must `git push` first. |
| `auto` | LINK → GitHub | best-effort | none | Default. Quietly falls back when LINK unreachable. |

CLI surface added by Sub-O (existing flags unchanged):

```
python automations/eve_self_update.py --transport auto                 # default
python automations/eve_self_update.py --transport link --peer <id>     # force LINK
python automations/eve_self_update.py --transport github               # force github
python automations/eve_self_update.py --audit --transport link         # report only
```

`--peer` selection precedence:
1. Explicit `--peer <machine-id>` on CLI.
2. Hint file `_shared-memory/eve-update-peer.txt` (operator override; single line).
3. First peer dir under `_vault/sanctum-mirror/` containing BOTH `EVE.exe` + `EVE.exe.sha256`.
4. First peer alphabetically with at least `EVE.exe.sha256`.
5. None → falls back to GitHub (in `auto`) or `link-unreachable` (in `link`).

---

## Popup mechanism — 3 layers (waterfall, NOT exclusive)

`automations/eve_update_notifier.py` runs as a 60-second schtask (`SinisterEveUpdateNotifier`). On every tick it compares the LOCAL sha against every peer's `EVE.exe.sha256` under `_vault/sanctum-mirror/`. On drift, ALL three layers fire (later layers don't depend on earlier success):

### Layer A — EVE.exe banner marker (preferred)
Writes `_shared-memory/eve-update-available.json` with shape:
```json
{
  "available_from_peer": "<machine-id>",
  "peer_sha": "<64-hex>",
  "local_sha": "<64-hex>",
  "detected_utc": "2026-05-25T07:14:00Z",
  "install_cmd": "python automations/eve_self_update.py --transport link --peer <id>"
}
```
EVE.exe's main menu (Sub-G's `tools/eve-picker/main_menu.py`) re-renders on every loop tick. When the marker exists, render a bright-orange banner at the top:
```
!!! UPDATE AVAILABLE — press U to install !!!
```
The U key handler invokes the install_cmd from the marker; on success it calls `eve_update_notifier.py --clear` to remove the marker.

**Idempotent:** if a marker for the SAME (peer_sha, local_sha, peer) already exists, the notifier does NOT rewrite it — prevents file-mtime churn / spam.

### Layer B — Windows toast notification
Fires via PowerShell COM bridge using `ToastNotificationManager` (no `BurntToast` dependency). Best-effort: silently skipped when:
- Running on non-Windows
- PowerShell not on PATH
- Corporate policy blocks Windows Runtime COM activation
- User is in Focus Assist / Do Not Disturb

Toast text:
> **EVE Update Available**
> From peer `<machine-id>` (sha `<first-8-hex>`). Open EVE.exe and press U to install.

### Layer C — Stdout banner (always fires when --scan/--once invoked)
Useful when the notifier is run manually from a terminal:
```
[EVE UPDATE AVAILABLE] from peer <id> (sha <12-hex>...); run: python automations/eve_self_update.py --transport link --peer <id>
```

---

## Leo's experience (happy path)

1. Operator commits + pushes a new EVE.exe; Sub-N's `vault_github_sync.py --auto` mirrors the bytes into the operator's `_vault/sanctum-mirror/<operator-id>/` subtree.
2. Sub-M's vault daemon replicates that subtree to Leo's `_vault/sanctum-mirror/<operator-id>/` (cross-machine sync over Tailscale or LAN).
3. Within 60 seconds: `SinisterEveUpdateNotifier` schtask on Leo's box runs `--scan`; detects drift; writes marker + fires toast + (if EVE.exe is open) the banner appears.
4. Leo opens EVE.exe (or it's already open) → sees the orange banner → presses **U**.
5. EVE invokes `python automations/eve_self_update.py --transport link --peer <operator-id>` → copies bytes from local vault mirror → SHA-verifies → hot-swaps via Windows rename-in-use (no restart needed; Sub-F's logic).
6. EVE invokes `eve_update_notifier.py --clear` → marker gone → banner disappears.
7. Total: ≤120 seconds from `git push` to Leo seeing the popup; ≤5 seconds from keystroke to swapped binary.

---

## Operator's role

Just push:
```bash
git add EVE.exe EVE.exe.sha256
git commit -m "EVE: <change>"
git push
python automations/vault_github_sync.py --auto   # Sub-N daemon usually runs this on a schtask
```

Sub-M's vault daemon does the rest. Operator's machine NEVER has to touch Leo's machine directly.

---

## 5 failure modes + recovery

| # | Symptom | Cause | Auto-recovery |
|---|---|---|---|
| 1 | `link-unreachable` in audit | Vault not running OR mirror dir empty | `--transport auto` automatically falls back to GitHub. No human action. |
| 2 | `sha-mismatch (got X expected Y)` | Bytes corrupted in vault transit OR partial write | `eve_self_update.py` deletes tmp + exits non-zero; next schtask tick retries from scratch. |
| 3 | `kill_result: would-require-kill` | EVE.exe locked the file AND hot-swap rename also failed (rare AV scenario) | Sub-F's hot-swap retries; if persistent, surface `--force-kill-stuck` in next operator session. |
| 4 | Marker present but banner doesn't show | EVE.exe was launched before Sub-G's marker-check integration ships | Operator/Leo closes + reopens EVE.exe; toast (Layer B) still fires; stdout banner (Layer C) on manual `--scan` works. |
| 5 | Toast doesn't appear, no banner, marker present | Layer A pending integration + Layer B blocked | Layer C still works on manual scan; `_shared-memory/eve-update-available.json` is human-readable JSON. Operator can `python automations/eve_self_update.py --transport link` directly. |

---

## Integration TODO for eve.py (handoff to next Sub-G iteration)

Add a marker-check render at the top of the main menu loop in
`tools/eve-picker/main_menu.py` (Sub-G's file, ~1293 LOC). Suggested integration:

```python
# Near the top of the render loop (after header, before menu items):
from pathlib import Path
import json
_MARKER = Path(__file__).resolve().parent.parent.parent / "_shared-memory" / "eve-update-available.json"
if _MARKER.exists():
    try:
        m = json.loads(_MARKER.read_text(encoding="utf-8"))
        peer = m.get("available_from_peer", "?")
        # Render bright-orange banner (use existing color tokens):
        print(f"{ORANGE}!!! UPDATE AVAILABLE from peer {peer} — press U to install !!!{RESET}")
    except Exception:
        pass

# In the key dispatcher, add:
elif key.lower() == "u":
    install_cmd = m.get("install_cmd")
    if install_cmd:
        subprocess.run(install_cmd, shell=True)
        subprocess.run([sys.executable, "automations/eve_update_notifier.py", "--clear"])
```

`ORANGE`/`RESET` tokens already exist in Sub-G's color palette; the canonical EVE.exe UI uniformity doctrine (`eve-ui-uniformity-doctrine-2026-05-24.md`) defines these.

---

## Smoke-test the notifier yourself

```bash
# Single-shot scan (works even with no peers; exits 0)
python automations/eve_update_notifier.py --scan --once

# 60s watch loop
python automations/eve_update_notifier.py --watch

# Install the schtask so it runs every minute
python automations/eve_update_notifier.py --install-schtask

# Clear the marker (after manually installing an update)
python automations/eve_update_notifier.py --clear
```

`_shared-memory/eve-update-notifier-log.jsonl` shows every event (drift detected, popup fired, marker written/cleared, toast result).
