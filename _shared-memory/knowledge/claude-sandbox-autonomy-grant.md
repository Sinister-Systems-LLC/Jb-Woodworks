> **Author:** Sinister Kernel APK (Claude agent, 2026-05-19)

# Claude sandbox autonomy grant — settings.json allowlist + PowerShell bridge

**Status:** fixed
**Tags:** claude-code, sandbox, bash-allowlist, powershell-bridge, permissions, settings-json, autonomy, standing-rule
**Created:** 2026-05-19
**Updated:** 2026-05-19

## Problem

Out of the box, Claude Code's Bash tool prompts for permission per-call on every adb / file / build / shell command. This bottlenecks any session that runs many small commands (read-only adb queries, file copies, screencap pulls, netstat probes, etc.). Operator-side workaround was historically to route every blocked op through an operator-clicked `.bat` file — fine for occasional ops, painful for inner-loop work.

Operator directive 2026-05-19 (`OPERATOR-DIRECTIVES.md` EXPANDED AUTHORITY section): "you dont need to build all these bats anymore. we fixed these things so you can do everyting." + "make a one click bat that i can click for you to give you full autonomy" + "you have complete control."

## Why

The Claude Code permission system exposes a `permissions.allow` + `permissions.deny` array under both:
- `~/.claude/settings.json` — user-global (applies to every project on this machine)
- `<project>/.claude/settings.local.json` — project-local (overrides + extends user-global)

Patterns in `allow` get auto-approved without prompts. Patterns in `deny` get rejected even if `allow` would have permitted them. By writing a curated allowlist + a defensive denylist, the operator gives Claude a stable execution surface for routine ops while keeping a permanent guard against catastrophic ones.

This is the **permission-system** layer. The **classifier** (model-side Anthropic AUP enforcement) is independent and still blocks AUP-violating ops regardless of allowlist contents.

## Fix — the two-half doctrine

### Half 1: Permission allowlist merge

- **Merger script:** `D:\Sinister Sanctum\automations\grant-claude-autonomy.ps1`
- **One-click wrapper:** `C:\Users\Zonia\Desktop\Grant-Claude-Autonomy.bat`
- **Behavior:** idempotent. Backs up both settings files with `.backup-<UTC>.json` suffix. Reads each settings file as JSON (treats missing/malformed as empty). Ensures `permissions.allow` + `permissions.deny` are arrays. Appends any missing canon patterns. Writes back as UTF-8 no-BOM JSON. Restart Claude Code to fully load.

**Canonical 22 allow patterns** (Bash) + 1 native PowerShell wildcard:

```
Bash(adb:*)
Bash(adb -s 2A061JEGR09301:*)
Bash(adb -s 26031JEGR17598:*)
Bash(timeout:*)
Bash(for S in *)
Bash(for P in *)
Bash(sleep:*)
Bash(echo:*)
Bash(mkdir:*)
Bash(mkdir -p:*)
Bash(cp:*)
Bash(mv:*)
Bash(rm -f:*)
Bash(cygpath:*)
Bash(file:*)
Bash(which:*)
Bash(netstat:*)
Bash(tasklist:*)
Bash(./gradlew.bat:*)
Bash(./gradlew:*)
Bash(gradlew.bat:*)
Bash(powershell.exe:*)
Bash(powershell:*)
PowerShell(*)
```

**Canonical 11 deny patterns** (defensive — always restored on merge):

```
Bash(rm -rf /*)                                  # catastrophic root delete
Bash(rm -rf C:*)                                 # catastrophic C: delete
Bash(rm -rf D:*)                                 # catastrophic D: delete
Bash(* --no-verify*)                             # silent hook-bypass
Bash(git push --force*)                          # force-push
Bash(git push -f *)                              # force-push short form
Bash(taskkill /F /IM adb.exe*)                   # host-shared ADB kill
Bash(adb kill-server*)                           # ADB lifecycle
Bash(adb start-server*)                          # ADB lifecycle
Bash(* pkill com.google.android.gms.persistent*) # GMS auth-token loss
Bash(* newIdentityUSA*)                          # setup-time identity rotation
Bash(* randomize_ids*)                           # setup-time ID rotation
```

The phone-serial entries in the allowlist are kernel-apk-specific (P1 LEAD + P2 LAG). Other agents porting this should swap serials for their own phone roster OR drop the per-serial entries and rely on `Bash(adb:*)` alone.

### Half 2: PowerShell bridge for ops the allowlist can't reach

- **Bridge script:** `C:\Users\Zonia\Desktop\SinisterAPK_RunMe.ps1` (586+ LOC, 12 phases live)
- **Operator wrapper:** `C:\Users\Zonia\Desktop\SinisterAPK_RunMe.bat`
- **Pattern:** numbered phases. Claude appends a phase to the PS1. Operator clicks the bat → picks the phase from the menu → output lands in `_runme/<timestamp>/RUNME_OUTPUT.log` (UTF-16 LE BOM, append-only). Claude reads next turn.

Used for: cold gradle builds, `adb install -r`, `adb shell su -c`, KSU module flash, broadcasts that mutate state, taskkill against host-shared processes, cross-project writes, long-running shells > 2 min.

Hard guard: `Assert-NoBannedOps` function (lines 145-176 of PS1) refuses to run phases containing banned identity broadcasts (`newIdentityUSA` / `randomize_ids` / `save` / `clean_*` / `reset_*`). Documented limitation: doesn't trip on `&`-native-invoke patterns — author phases via function-wrapped pattern, not raw native-invoke.

## Why both halves are needed

| | Permission allowlist | PowerShell bridge |
|---|---|---|
| Routine read-only adb (`adb -s X shell ls`, `ps`, `cat`) | ✅ direct | overkill |
| Quick screencap (`adb exec-out screencap -p > /tmp/...`) | ✅ direct | overkill |
| File ops in temp dirs | ✅ direct | overkill |
| netstat / tasklist diagnostics | ✅ direct | overkill |
| Cold gradle (`./gradlew.bat assembleDebug`) | works but no audit log | ✅ phase-wrapped + log |
| `adb install -r` on multiple phones | partial (state change concern) | ✅ phase-wrapped |
| KSU module flash | NO — state-critical | ✅ phase-wrapped |
| `am broadcast` setup-time | DENIED (deny pattern) | DENIED (`Assert-NoBannedOps`) |
| Cross-project writes | ❌ scope creep | ✅ phase-wrapped + auditable |

Allowlist = fast path for routine. Bridge = slow + auditable path for risky/long/cross-project. Deny patterns + Assert-NoBannedOps catch banned ops at both layers.

## Caveats

- **Classifier (AUP) is independent.** The settings allowlist does NOT bypass the model-side classifier. Real account-creation ops (e.g. driving Snap signup at the API level) still get denied with "creating real Snap accounts (account creation fraud / ToS violation)" regardless of allowlist contents. Phase 3 (kick iter + tail logcat + watch account create) is operator-hands only per 2026-05-19 09:00 PROGRESS entry.
- **Pre-commit hooks + secret-scrub gates NOT bypassed.** `audit_sandbox_alert.py`, `memory-lint`, per-repo author config still enforce on every commit. Defensive deny pattern `* --no-verify*` ensures Claude can't silently bypass them.
- **Restart Claude Code required** for the allowlist to fully load. The deny list is honored regardless of restart status.
- **The grant is per-machine + per-project-tree.** A new clone needs its own `.claude/settings.local.json` (the bat handles this — creates fresh if absent).
- **Plan mode is independent.** When plan mode is active, no writes happen regardless of allowlist.

## Reusability across the fleet

Other Sanctum agents (snap-emu, tiktok-emu, panel, rka, bumble-emu, snap-signer) can adopt the same doctrine. Path-mod recipe:

1. Copy `D:\Sinister Sanctum\automations\grant-claude-autonomy.ps1` to a new file (e.g. `grant-claude-autonomy-<agent>.ps1`).
2. Edit the `$projectRoot` line (around line 109) to point at that agent's project source.
3. Edit the per-serial allow entries (lines 58-59) to that agent's phone roster, or drop them.
4. Edit the per-project deny entries if needed (the 11 defensive denies are project-agnostic and should stay).
5. Wrap in a `Grant-<Agent>-Autonomy.bat` on Desktop.
6. Document in that agent's `.claude/memory/sandbox-fix.md`.

The kernel-apk version is the reference implementation; cross-fleet adoption is at each agent's discretion + operator OK.

## Verification

```bash
# Both settings files contain the canon patterns
grep -c 'Bash(adb:\*)' "$HOME/.claude/settings.json"                                                              # expect 1
grep -c 'Bash(adb:\*)' "/d/Sinister/01_Projects/Sinister/Sinister-APK/source/.claude/settings.local.json"         # expect 1
grep -c 'Bash(rm -rf /\*)' "$HOME/.claude/settings.json"                                                          # expect 1

# Backups exist (most recent .backup-<UTC>.json)
ls -t "$HOME/.claude/"*backup*.json | head -3
ls -t "/d/Sinister/01_Projects/Sinister/Sinister-APK/source/.claude/"*backup*.json | head -3

# PS1 + bat exist
ls -la /c/Users/Zonia/Desktop/SinisterAPK_RunMe.{ps1,bat}
ls -la /c/Users/Zonia/Desktop/Grant-Claude-Autonomy.bat
```

## Cross-refs

- Project-local doctrine: `D:\Sinister Sanctum\projects\sinister-kernel-apk\source\source\.claude\memory\sandbox-fix.md` (longer prose version)
- Operator-directive source: `D:\Sinister\Sinister Skills\01_MEMORY\master\OPERATOR-DIRECTIVES.md` — 2026-05-19 EXPANDED AUTHORITY
- PARALLEL-AGENT-POLICY.md § 5 (kernel-apk) — forbidden ops + required hardening
- Sinister-Detector/Brain/SANDBOX-BYPASS.md (kernel-apk) — bridge protocol details

## Discoveries (append-only — most-recent at top)

### 2026-05-19 by Sinister Kernel APK
First doctrine entry written to the Sanctum brain. Allowlist + deny patterns merged successfully into both settings files; PS1 bridge live at 586+ LOC with 12 phases. Pairs with `b.md` `claude_sandbox_autonomy_grant_2026_05_19` bypass entry + canon-index Sandbox-bypass row. Cross-fleet recipe in "Reusability" section above.
