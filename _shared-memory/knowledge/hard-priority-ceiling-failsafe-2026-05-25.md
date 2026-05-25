<!-- decay:
  category: failsafe
  confidence: 1.0
  reinforcements: 0
  half_life_days: 730
-->
# Hard Priority Ceiling Failsafe (operator hard-canonical 2026-05-25 ~05:30Z)

**Author:** RKOJ-ELENO :: 2026-05-25

## Operator verbatim

> *"ok my whole system is like grey screen and i have a folder and power shell that wont close and i cant see my fuvking desktop. fix this and tweak things so that shit doesnt happen. its fixed now"*

## What happened

Iter-28 operator asked for "more power" → I bumped the `agents-first` profile to `above_normal` / `high` priority + 12-20 GB RAM caps and applied live. Within minutes:
- Operator's desktop went unresponsive (grey screen)
- Explorer + a PowerShell window stopped responding
- Operator had to manually recover

Root cause: Windows foreground apps (DWM, explorer.exe, the user's shell + browser) all run at `NORMAL` priority. When agents elevate to `ABOVE_NORMAL` or `HIGH`, Windows preempts the operator's UI thread → grey/black screen and input freezes. RAM alone doesn't cause this; CPU priority elevation does.

## Binding failsafe

**`HARD_PRIORITY_CEILING = "normal"`** in `automations/resource_quota_governor.py`. The `apply_priority()` function clamps EVERY requested priority through `_clamp_priority()` before passing it to `psutil.Process.nice()`. Even if a profile, env var, or operator override asks for `high` or `realtime`, the ceiling demotes it to `normal`.

```python
_CEILING_ORDER = ("idle", "below_normal", "normal", "above_normal", "high", "realtime")

def _clamp_priority(label: str) -> str:
    req = _CEILING_ORDER.index(label)
    cap = _CEILING_ORDER.index(HARD_PRIORITY_CEILING)
    return _CEILING_ORDER[min(req, cap)]
```

## Rules for every Sanctum agent

1. **NEVER ask for priority above `normal`** when scheduling agent processes. RAM, GPU, parallelism — yes, push hard. CPU priority — never above operator.
2. **"More power" = more RAM / more parallel processes / more GPU**, NOT higher CPU priority.
3. **If a new profile is added**, ensure `default_priority` and `privileged_priority` are `normal` or below.
4. **DWM + explorer.exe + the operator's foreground shell run at NORMAL.** Treat this as the operator's reserve.
5. **Test on a live system before claiming.** If a resource change could starve UI, dry-run first → ask operator → apply.

## Composes with

- `_shared-memory/knowledge/automate-everything-no-operator-admin-2026-05-25.md` (operator is END USER, not sysadmin — never make the desktop unusable)
- `_shared-memory/knowledge/safe-quality-loops-doctrine-2026-05-24.md` (12 guardrails — this is now guardrail #13)
- `_shared-memory/knowledge/sanctum-scope-discipline-2026-05-24.md` (lane discipline — don't touch operator-facing system state aggressively)
- `_shared-memory/knowledge/one-terminal-per-project-no-overlap-doctrine-2026-05-25.md` (one master, no thrash)

## Future safety extension (queued)

- **Live unresponsiveness detector** — daemon polls `dwm.exe` + `explorer.exe` CPU starvation; if either is starved >5s, automatically `apply_priority(slug, "idle")` to ALL agents to free the UI. (P1 next iter.)
- **EVE.exe Account Manager "Throttle All" key** — single keypress drops every agent to `idle` priority in case of emergency.
