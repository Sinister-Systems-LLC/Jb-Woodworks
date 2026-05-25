<!-- Author: RKOJ-ELENO :: 2026-05-25 -->
<!-- decay:
  category: preference
  confidence: 1.0
  reinforcements: 1
  half_life_days: 365
-->
# JCode-style condensed log discipline (fleet-wide binding)

**Status:** HARD-CANONICAL 2026-05-25T02:10Z (operator verbatim binding for every terminal-output surface Sanctum + spawned agents render).

**Operator verbatim 2026-05-25T~02:10Z:** *"i want you to over deatil how he does all of what he does so we can be as efficent as possible. for example we show full logs in the terminals... see how they have stuff like this saying what its doing and really condensed logs in their terminals... we need to save where we can on everything... i dont want to do taht shit we can save resources by doing it jcodes way"*.

Operator reference (screenshot #26):
```
1> i need you to start writing a game for me
[*] connecting... 1.3s · opening websocket
2> _
```

Operator anti-reference (screenshot #27): a Sinister Quantum terminal scrolling a 50-line file diff hunk-by-hunk + `Bootstrapping... (19m 12s)` — verbose, dense, expensive to render and impossible to scan.

## The rule

**ONE line per status event.** Format:
```
<icon> <verb_phrase>... <elapsed>s · <sub_phase>
```

- `<icon>`: a single character glyph color-coded by state (`[*]` cyan = in-progress, `[+]` green = ok, `[!]` yellow = warn, `[x]` red = fail, `[?]` gray = waiting)
- `<verb_phrase>`: present-participle action ("connecting", "downloading", "spawning", "indexing")
- `<elapsed>s`: total seconds the verb has been running, updated in place on the same line via `\r`
- `<sub_phase>`: the current granular sub-step the verb is on ("opening websocket", "auth handshake", "ws connected")

**Update in place** (carriage return overwrite) NOT new line per tick. The line stays on the screen for the lifetime of the verb; only when the verb finishes does a NEW line scroll in (the next verb).

**Persist verbose to disk; render condensed to terminal.** Operator only sees one line per event in the terminal. The full trace (every sub-event, every API request body, every diff hunk) goes to `_shared-memory/sinister-term-history/history.jsonl` for forensic recall when explicitly requested.

## Why this saves resources

1. **Token cost** — Claude sees the operator's terminal via screenshot; a 50-line scroll wastes 10-20× the vision-tokens of a 1-line status. Multiply by N agents.
2. **Operator cognitive load** — One line scanned in <100ms; 50-line scroll requires scroll-back + parsing.
3. **Cache stickiness** — Heartbeat / status writes to disk less often, so prompt cache doesn't churn on noise.
4. **Bandwidth (for Sinister LINK cross-machine)** — Less stdout = less to mirror to peer.

## Implementation surfaces (Sanctum)

| Surface | File | Today | Target |
|---|---|---|---|
| EVE.exe main_menu status bar | `tools/eve-picker/main_menu.py` | multi-line panels | one-line `<icon> <verb>... <elapsed>s · <sub>` (in-place update) |
| start-sinister-session.ps1 spawn output | `automations/start-sinister-session.ps1` | 50+ lines (preflight, plugin, autonomy, etc.) | one line per phase (preflight → plugin-install → spawning → connected) |
| sanctum-auto-push.ps1 | `automations/sanctum-auto-push.ps1` | per-file commit chatter | one line per push attempt (push → up-to-date or N commits ahead → push ok 0.4s) |
| fleet-update.ps1 List | `automations/fleet-update.ps1` | full row dump | one-line tail summary + count of unread by priority |
| overseer-agent.ps1 Watch | `automations/overseer-agent.ps1` | full table per iter | one line `[*] watching... 47 healthy, 3 stalled, 0 dead` |
| EVE per-page sub-flow output | every action in `account_manager.py` etc | multi-line subprocess.run output dump | one-line phase + optional `--verbose` flag for full |
| Per-agent transcript surface | Claude Code itself | full agent narration | sanctum can't change Claude's tongue; but can wrap its own ps1/py output |

## Implementation primitive (Python)

Status line module to ship next: `tools/eve-picker/status_line.py`:

```python
class StatusLine:
    """One-line condensed status renderer.
    
    Usage:
        with StatusLine("connecting") as s:
            s.sub("opening websocket")
            ...
            s.sub("auth handshake")
            ...
            s.ok()  # or s.warn("retrying") / s.fail("timeout")
    """
    ICONS = {"run": "[*]", "ok": "[+]", "warn": "[!]", "fail": "[x]", "wait": "[?]"}
    COLORS = {"run": CYAN, "ok": OK, "warn": WARN, "fail": FAIL, "wait": DIM}
    
    def __init__(self, verb): ...
    def sub(self, phase): ...  # update in-place via \r
    def tick(self): ...        # called by background thread every 0.1s to refresh elapsed
    def ok(self, msg=""): ...  # finalize green; newline so next verb scrolls in
    def warn(self, msg): ...
    def fail(self, msg): ...
```

PowerShell counterpart: `automations/status-line.ps1` with `New-StatusLine`, `Set-StatusSub`, `Complete-Status -State Ok|Warn|Fail`.

## Composes with

- `eve-ui-uniformity-doctrine-2026-05-24` (this is the LOG portion of that doctrine; UI panels stay multi-line, status emissions go condensed)
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (rule 7 concise summaries — log discipline is the per-line analog of the summary discipline)
- `loop-mode-continuous-iteration-2026-05-24` (cheaper logs = cheaper loop iters = more iters per cache window)
- `sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24` (UI base; status-line is the terminal cousin of the dashboard status pill)
- `jcode-full-audit-2026-05-25` (the audit will surface the exact jcode Rust functions; this doctrine documents the discipline we extract from it)

## Anti-patterns

1. Multi-line panel for status events — that's for menus + dashboards, NOT for "doing X" emissions
2. Scrolling new line every second instead of `\r` in-place update — wastes screen + scrollback
3. Showing full file diffs in a spawn terminal — diffs belong in `git diff` on operator demand, not auto-emitted
4. Showing raw subprocess stdout — wrap it. Capture, parse, condense.
5. Showing `Bootstrapping... (19m 12s)` with no sub-phase — operator can't tell if it's making progress vs stuck

## Measurable pass criterion

- After ship, average lines-per-event in `_shared-memory/sinister-term-history/history.jsonl` for terminal-rendered events drops by ≥80% compared to pre-doctrine baseline
- EVE.exe spawn flow: <10 visible terminal lines from `Sinister-Start.bat` click to "ready to type" (vs current ~50+)
- `start-sinister-session.ps1` background launch: 1 line per major phase (preflight → spawning → connected), not per sub-action

Updated: 2026-05-25
