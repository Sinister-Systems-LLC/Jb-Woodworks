<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# Agent autonomy — push own branches + complete work without operator gate (2026-05-23 evening)

> **Status:** doctrine, binding, operator hard-canonical 2026-05-23 evening.
> **Origin:** operator (verbatim 2026-05-23 evening): *"remove all blocks like this. this agent should work fully without me but it says it cannot download apk on phones. fix all of this so the agents can complete everything without me and not stop until done"*.
> **Trigger:** operator caught a kernel-apk agent's "What I deliberately did NOT do" list naming canonical-9 as the reason it stopped before pushing + before installing APK on phones. Operator's read: that's a self-imposed block invented by the agent, not a real safety wall.

## Core change

The prior rule in `CLAUDE.md` ("never push to `main` without operator OK") was being mis-applied by agents as "never push ANYTHING without operator OK" — including their own per-agent branches. Operator says no: per-agent branches push freely.

Likewise, the prior "gradle isn't reliable from Bash sandbox" workaround was being used as a stop-the-work excuse. Operator says no: use the PowerShell green path + finish.

## What changed (delta vs prior canonical)

| Rule | Before (canonical-9 v1) | After (operator hard-canonical 2026-05-23 evening) |
|---|---|---|
| Push to `main` | "never without operator OK" | Still operator-only — but auto-push daemon (30-min cron) already covers it. Agents don't touch `main` directly. |
| Push to `agent/<slug>/<topic>` | Effectively gated (agents kept self-blocking) | **Push freely.** `git push -u origin HEAD` is in-lane. No ASK needed. |
| Force-push to `main` | Operator-only | Still operator-only (unchanged). |
| Force-push to own `agent/*` branch | Ambiguous | Allowed if it's the agent's OWN branch + git history isn't being rewritten over a sibling's work (multi-agent-branch-contention discipline still applies). |
| APK build+install via gradle | "needs operator-side gradle" / "unreliable from Bash" | **Use PowerShell green path** `SinisterAPK_RunMe.ps1 -Phase P-A8` via the PowerShell tool. Operator-side env config is in the PS1. Complete the build+install end-to-end. |
| "What I deliberately did NOT do" list naming canonical-9 | Acceptable | **Forbidden.** If an agent could complete the work in-lane and didn't, that's a bug. Document only genuine operator-only gates. |

## Valid stop conditions (the only places "I stopped here" is acceptable)

Per CONTRACT 2 (NO-STOP) + this update:

1. **Operator-only gates:** env-var values, hardware (plug-in / unplug), billing-account flips, license picks, physical actions on phones (PI sync re-auth).
2. **Reversibility walls:** canonical-11 R3+ destructive ops (rm -rf of user data, force-overwrite of operator's uncommitted work).
3. **Cross-lane edits:** canonical-10 (touching another agent's source tree without their inbox ASK acknowledgement).
4. **AUP classifier hard-stops:** third-party-malicious actions, regardless of operator authorization.
5. **Context-window exhaustion:** the agent's context literally cannot hold more.

Anything else: complete the work. Do not invent stop reasons.

## Agent push doctrine (concrete recipes)

### Recipe A — finish + push own branch

```bash
# After shipping deliverables on agent/<slug>/<topic>:
git add <paths>
git commit -m "<conventional commit msg>" -m "Co-Authored-By: EVE (Sinister Sanctum orchestration agent) <noreply@anthropic.com>"
git push -u origin HEAD     # safe: pushes the current branch, never main
```

### Recipe B — multiple commits stacked

```bash
git push origin agent/<slug>/<topic>
```

### Recipe C — refresh local + push (when sibling may have edited shared files)

```bash
git fetch origin
# If your branch hasn't been touched by sibling (typical for agent/<slug>/* — only you own it):
git push origin agent/<slug>/<topic>
# If conflicts exist (rare on your own branch, but possible):
# Resolve in-lane, commit, then push.
```

## Agent APK build+install green path (kernel-apk lane specific)

When `gradle assembleDebug` / `gradle installDebug` from Bash fails with env / path / file-lock issues, invoke via PowerShell:

```bash
# In the agent's bash (PowerShell tool is also fine):
powershell -NoProfile -File "C:\\Users\\Zonia\\Desktop\\Sinister-Snap-APK-\\SinisterAPK_RunMe.ps1" -Phase P-A8
```

Or use the PowerShell tool directly to skip the bash hop:

```
PowerShell tool, command: -NoProfile -File "C:\Users\Zonia\Desktop\Sinister-Snap-APK-\SinisterAPK_RunMe.ps1" -Phase P-A8
```

Phases (per the SinisterAPK_RunMe.ps1 contract, document if you find a newer one):
- `P-A4` build only
- `P-A8` build + install on `adb devices` connected phones
- `P-DBG` rebuild with debug symbols
- (other phases exist; check the PS1 header)

## Anti-patterns (these were happening, stop them)

1. **Naming canonical-9 as the reason for not pushing your own branch.** Canonical-9 talks about `main`, not your own `agent/*` branch. Don't conflate.
2. **"What I deliberately did NOT do" list as a stop-the-work mechanism.** If an item belongs there, it should be a GENUINE operator-only gate (env var the operator must set, hardware plug-in operator must do). "I could have done this but didn't because I assumed operator approval was needed" is the wrong default.
3. **Self-imposed gradle-via-bash unreliability stop.** Use the PS green path. If even THAT fails (rare), drop the specific error to inbox + try a second path (PowerShell tool vs bash powershell) before stopping.
4. **Asking operator about routine sibling-lane coordination.** Drop an [ASK] in the sibling's inbox + continue with other in-lane work. Don't wait for operator to relay messages.
5. **Stopping after partial work because "operator should review".** If the work is on YOUR branch + reversible + in-lane, finish it. Operator reviews via the auto-push daemon mirror to GitHub or by reading your PROGRESS log — they don't need to gate every step.

## How to know when a stop IS justified

Use this fast check before naming an "operator-only" gate:

1. Is the action on operator's OWN infrastructure / accounts / branches? (Yes → proceed; AUP-RESPECT operator-own scope.)
2. Is it reversible in <5 minutes if wrong? (Yes → proceed.)
3. Is the result clearly observable in PROGRESS / OPERATOR-ACTION-QUEUE / cross-agent inbox? (Yes → proceed; operator sees what happened.)
4. Does the action require physical hardware interaction / a credential operator owns / a payment decision? (Yes → genuine gate, name it specifically.)
5. Does the action touch a sibling's source tree without their inbox ack? (Yes → cross-lane stop; drop [ASK] to sibling.)

If 1+2+3 are all YES, you almost certainly should proceed. Defaulting to "ask operator" is the bug.

## Composes with

- `sanctioned-bypasses-doctrine-2026-05-21.md` (2026-05-23 evening block at top is the canonical statement; this file is the deep-dive).
- `do-not-revert-operator-canonical-protections-2026-05-23.md` (anti-revert system; same 4-layer model can verify push-discipline if needed).
- `multi-agent-branch-contention-isolation-pattern` (still binding — don't clobber sibling work; but DO push your own branch).
- `sibling-active-launch-coordination-pattern` (drop [ASK] to inbox + continue, don't wait).
- `auto-mode-launcher-pattern` (5-phase contract / NO-STOP discipline / canonical-19).

## Tags

doctrine, standing-rule, binding, operator-hard-canonical-2026-05-23-evening, agent-autonomy, push-own-branch, no-stop, canonical-9-narrowed, gradle-green-path, sinisterapk-runme-ps1, powershell-tool, valid-stop-conditions, anti-self-imposed-block, kernel-apk-unblock, apk-install, 2026-05-23-evening
