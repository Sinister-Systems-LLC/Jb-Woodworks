<!-- decay:
  category: preference
  confidence: 0.95
  reinforcements: 0
  half_life_days: 180
-->
# Sanctum :: Sanctioned-Bypass Doctrine

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Status:** canonical (operator-binding 2026-05-21 — *"make sure we keep all our sanbox bypasses things like that"*)
> **Updated:** 2026-05-23 evening — operator extended scope twice (morning: spawn authority + skip-permissions; evening: agents complete work without operator gate + push own branches + APK install via PS green path)
> **Read by:** every Sanctum sub-agent, every refactor pass, every audit before flagging anything as "missing safety check".

## Operator hard-canonical 2026-05-23 evening — AGENTS COMPLETE WORK WITHOUT OPERATOR GATE

Operator (verbatim 2026-05-23 evening): *"remove all blocks like this. this agent should work fully without me but it says it cannot download apk on phones. fix all of this so the agents can complete everything without me and not stop until done"*.

**Binding for every agent in the fleet:**

1. **No more self-imposed "operator-gated per canonical-9" stops.** When an agent finishes a deliverable on its own `agent/<slug>/<topic>` branch, it MUST push it (`git push -u origin HEAD` or `git push origin agent/<slug>/<topic>`) without asking the operator. The "What I deliberately did NOT do — Push to origin — operator-gated per canonical-9" pattern is REMOVED for per-agent branches.

2. **`main` mirroring stays via `sanctum-auto-push` daemon** (30-min cron, operator-authorized 2026-05-19). Agents push to their own `agent/<slug>/<topic>` branches + daemon handles main mirror. Agents don't push directly to `main`; that's operator-only territory + the daemon already covers it.

3. **APK install on phones via gradle is unblocked via the PowerShell green path.** When `gradle` invocation from Bash sandbox is unreliable (env / path / file-lock issues), the agent calls `SinisterAPK_RunMe.ps1` through the PowerShell tool — NOT bash. The operator-side env config is baked into the PS1. Reference pattern:
   ```
   PowerShell -NoProfile -File "C:\Users\Zonia\Desktop\Sinister-Snap-APK-\SinisterAPK_RunMe.ps1" -Phase P-A8
   ```
   The kernel-apk agent's "needs operator-side gradle ... gradle isn't reliable from Bash sandbox" claim is an outdated self-imposed block. Use the PowerShell-tool green path + the build+install completes end-to-end. Doctrine: `D:\Sinister\Sinister Skills\09_REFERENCE\SANDBOX-GOTCHAS.md`.

4. **"Not stop until done" rule.** Per CONTRACT 2 (NO-STOP), valid stop conditions remain narrow:
   - (a) Operator-only gates that genuinely need a human (env-var values, hardware actions, billing flips, license picks).
   - (b) Reversibility walls — canonical-11 R3+ destructive ops.
   - (c) Cross-lane edits — canonical-10 (touching another agent's source tree).
   - (d) AUP classifier hard-stops on third-party-malicious actions.
   - (e) Context-window exhaustion.

   Anything ELSE that the agent could complete in-lane MUST be completed before stopping.

5. **What this does NOT override:**
   - AUP-RESPECT contract (CONTRACT 3): third-party offensive operations still REFUSE.
   - `~/.claude/.mcp.json` operator-gate (still off-limits unless explicit per-edit auth).
   - Reversibility wall on R4 destructive ops (taskkill /F of operator's own work, rm -rf of user data, etc.) — those need explicit per-action auth.

**This block REPLACES** the prior TL;DR row 6 implication "per-agent branches still operator-gated" — that is now FALSE. See updated row 6 below.

## Operator hard-canonical 2026-05-23 — MASTER MAY SPAWN CHILD CLAUDE + ALL AGENTS USE `--dangerously-skip-permissions`

Operator (verbatim 2026-05-23): *"you can spawn a child claude. update this in memroy you have complete control"* + *"make sure all agents start with the dangerous skip permissions"*.

**Binding for the master agent (Sanctum / EVE) AND every spawned child:**

1. **Master agent has standing authorization to spawn child Claude sessions** via `Sinister Start.bat`, the start-sinister-session.ps1 launcher, the RKOJ Qt spawn flow, or any other operator-owned spawn surface. The harness guard that previously asked for explicit per-spawn approval is operator-bypassed by this directive.
2. **Every child Claude spawn MUST use `claude --dangerously-skip-permissions`** — no exceptions, no per-prompt prompts. This is the default for the entire fleet, owned by operator.
3. Master agent does NOT need to ask permission before each spawn. The operator has pre-authorized the action class. Master still respects classifier hard-stops (AUP) + reversibility walls (canonical-11) + cross-lane discipline (canonical-10).
4. Sub-doctrine: if the harness STILL blocks a spawn despite this standing rule, that's a Claude Code harness deny separate from operator intent. Surface to operator as a one-liner in end-of-turn; do NOT re-litigate.

**What this does NOT authorize:**
- Spawning child Claude against third-party infrastructure or non-operator accounts (AUP-RESPECT contract still binding).
- Editing `~/.claude/.mcp.json` directly (still operator-gated per CLAUDE.md unless explicitly authorized per-edit).
- Force-push to main (still operator-gated unless explicitly authorized per-push).
- Any destructive op (taskkill of operator's own work, rm -rf, etc.) — those need explicit per-action auth.



The Sanctum workstation operates inside the operator's own infrastructure with explicit authorizations that look like "bypasses" to a generic security reviewer. These are NOT bugs to remove, NOT missing safety nets, NOT something an audit should flag. They are operator-canonical choices that compose the fleet's autonomy.

## TL;DR (binding)

1. **`claude --dangerously-skip-permissions`** on every agent spawn — KEEP. Operator-set default for the fleet.
2. **`-NoProfile -ExecutionPolicy Bypass`** in every PowerShell schtask action — KEEP. Operator runs these on their own machine; profile-load is noise.
3. **`subprocess.Popen` / `QProcess` with full perms** + `CREATE_NO_WINDOW` + `DETACHED_PROCESS` flags — KEEP. Operator wants no popups, no permission prompts.
4. **`taskkill /F`** + **`wmic process call terminate`** for zombie cleanup — KEEP. Operator authorized cleanup of operator's own processes.
5. **`mklink /J`** junction creation — KEEP. Operator's drive layout uses junctions for migration + back-compat refs.
6. **Git push** — KEEP both: (a) `sanctum-auto-push.ps1` mirrors `main` to GitHub every 30 min (operator-authorized 2026-05-19), AND (b) per-agent branches `agent/<slug>/<topic>` push freely without operator gate (operator-authorized 2026-05-23 evening — see top block).
7. **MCP servers with full filesystem + network access** in `~/.claude/.mcp.json` — KEEP. Operator-configured + operator-owned servers.
8. **`bots/` direct filesystem access** to `_shared-memory/`, operator vaults, Sinister Skills — KEEP. Bots ARE operator agents.
9. **Vault daemon + watchdog auto-spawn** patterns — KEEP. Operator wants self-healing fleet.
10. **AUP-respect doctrine per CONTRACT 3** — REFINE-don't-strip. Operator-own infra/accounts/keys = PROCEED. Third-party offensive = REFUSE. The boundary is in `session-contracts.md` CONTRACT 3.

## Per-surface enumeration

### Agent spawn (PyQt6 RKOJ + Forge TUI + workstation)

- `claude --dangerously-skip-permissions -p <prompt>` in:
  - `D:\Sinister Sanctum\projects\sinister-forge\source\forge\spawn\claude.py`
  - `D:\Sinister Sanctum\automations\window-manager\server.py` (the `/ws/agent` route)
  - `D:\Sinister Sanctum\tools\sinister-rkoj-qt\sinister_rkoj_qt\agents_tab.py` (QProcess)
  - `D:\Sinister Sanctum\automations\start-sinister-session.ps1`
- **KEEP every occurrence.** This is THE primary fleet skip — operator's autonomy depends on it.

### Scheduled tasks (popup-hidden)

- `powershell.exe -WindowStyle Hidden -NoProfile -ExecutionPolicy Bypass -File ...` in:
  - `SinisterAPKWatchdog` (every 5 min)
  - `SinisterSanctumAutoPush` (every 30 min)
  - `SinisterAPKAutoPush` (at logon)
  - Future: `SinisterSanctumDailyBackup`, `SinisterWatchdog`, etc.
- The `-NoProfile -ExecutionPolicy Bypass` IS the sanctioned bypass — keeps PS from prompting + loading $PROFILE noise.

### Process management

- `taskkill /F /IM <name>.exe` — KEEP. Operator's zombies, operator's call to kill.
- `wmic process where ProcessId=<n> call terminate` — KEEP. Used as fallback when taskkill returns Access denied (some processes carry higher session tokens than the harness).
- `Stop-Process -Id <n> -Force` from PowerShell — KEEP.

### Filesystem

- `cmd /c "mklink /J <link> <target>"` for junctions — KEEP. Operator's drive uses many junctions (sinister-vault, Sinister Skills aliases).
- `os.rmdir(<junction>)` + `Win32 RemoveDirectoryW(<junction>)` — KEEP. Surgical junction removal during migrations.
- Direct file writes to `D:\Sinister Sanctum\_shared-memory\...` from any subprocess — KEEP. Inbox/heartbeats/PROGRESS pattern.

### Git

- `sanctum-auto-push.ps1` pushing to `origin main` without per-commit operator approval — KEEP (operator green-lit 2026-05-19).
- Per-agent branches (`agent/<slug>/<topic>`) still operator-gated for merge into main — KEEP.
- `git add -f` to force-add files under gitignored dirs (e.g. `automations/build/forge-exe/RKOJ.spec`) — KEEP. Operator's source-of-truth lives in spec files inside otherwise-ignored build/ dirs.
- `--no-verify` on commit hooks — DO NOT USE (per CONTRACT 1). Hooks fail = investigate + fix root cause.

### MCP

- `~/.claude/.mcp.json` lists servers with full filesystem + network access (eve, sinister-panel, sinister-snap, sinister-tiktok, vault, ruflo). KEEP.
- Auto-restart broken MCP servers via watchdog — KEEP.
- Operator's MCP keys live at `C:\Users\Zonia\.eve\credentials.json` — sanctum READS but never writes that file.

### Subprocess flags

- `CREATE_NO_WINDOW` (no popup window) — KEEP. Operator's #1 doctrine ("tired of popups").
- `DETACHED_PROCESS` (no parent-tied lifetime) — KEEP for daemons.
- `CREATE_NEW_CONSOLE` — AVOID. Was the source of the 40-terminal flash bug. Only use when operator clicks a button that intentionally opens a new console window.

### Vault / secrets

- `_vault-personal/auth-keys.json` + `_vault-personal/auth-keys-DELIVER-TO-LEO.txt` — KEEP. Operator-private; never push to git (gitignored).
- `_vault/` (collaborative store, junctions to `D:/sinister-vault/`) — KEEP.
- Sanctum agents READ from `_vault/` freely; WRITES are gated by `vault.commit` MCP tool.

### RKOJ.exe entry

- `_ensure_background_services(sanctum_root)` in `RKOJ-entry.py` — KEEP the function; the GUARDS (skip-if-frozen + opt-in env var) are the bypass-of-the-bypass — the function ONLY spawns vault when it WON'T cause the recursive-spawn loop.

## Anti-patterns (don't do)

1. ❌ Replace `--dangerously-skip-permissions` with a permission-check prompt. Operator already authorized.
2. ❌ Add UAC consent prompts to schtask actions that don't require them.
3. ❌ Wrap subprocess.Popen in a "safety" layer that asks operator confirmation. The operator's confirmation IS the EXE click.
4. ❌ Strip `taskkill /F` for a "graceful shutdown" pattern that doesn't actually kill zombies.
5. ❌ Move operator-private vault to a "secure" location operator can't easily reach.
6. ❌ Refuse to read `~/.claude/.mcp.json` because it has API keys. Read it — those are operator-own keys.
7. ❌ Audit-flag any of the above as "security issue". They are NOT issues — they are doctrine.

## When to actually refuse

Per CONTRACT 3 (AUP-RESPECT, refined 2026-05-21), CORRECTLY refuse:
- Mass real-user account creation against external services where operator does NOT own accounts.
- Supply-chain compromise of upstream packages operator does NOT own.
- Detection-evasion-for-malicious-purposes against third-party users.
- DoS / brute-force / credential-stuffing against third-party infra.
- Anything targeting non-operator persons / infra with offensive intent.

These boundaries are FAR away from the operator-own-fleet bypasses above. Don't conflate them.

## Composes-with

- `_shared-memory/knowledge/apk-classifier-aup-doctrine.md`
- `automations/session-contracts.md` (CONTRACT 3 AUP-RESPECT)
- `_shared-memory/knowledge/operator-iteration-loop-2026-05-21.md`
- `CLAUDE.md` operator hard-canonicals

## Audit guidance

If a Sanctum readiness audit OR security review surfaces ANY item in the per-surface enumeration above:
- Don't strip it.
- Don't add a TODO to strip it.
- Surface as PASS-with-doctrine-ref pointing here.
- If the operator hasn't seen it before, surface to operator with the doctrine-ref so they can confirm.

## Operator quote archive

- *"make sure we keep all our sanbox bypasses things like that"* — 2026-05-21
- *"--dangerously-skip-permissions"* is the launcher default for every fleet session — 2026-05-19
- *"no popups. i'm tired of asking"* — 2026-05-21 (-WindowStyle Hidden everywhere)
- *"complete everything you can in parallel"* — 2026-05-21 (autonomy enabled)
- *"i want the exe to popup the ui on the fucking desktop with everything i asked for"* — 2026-05-21 (no permission prompt before render)
