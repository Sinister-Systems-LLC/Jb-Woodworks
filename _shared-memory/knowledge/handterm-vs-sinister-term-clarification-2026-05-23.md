<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# Naming clarification :: "handterm" in operator-speak = our `sinister-term`

> **Status:** binding (operator clarified verbatim 2026-05-23 evening)
> **Origin:** operator screenshot 2026-05-23 evening referencing `github.com/1jehuang/handterm` followed by clarification *"make sure your using all our own shit that we have been building like by handterm i mean sinister term. just make sure its all complete and ready to go with full control like i want"*

## The naming trap

When the operator types "handterm" they're referencing **our own `sinister-term`** package, NOT the upstream Wayland-only Rust binary at `github.com/1jehuang/handterm`. The upstream is a **reference / inspiration source** documented in `projects/sinister-term/README.md`; we cannot port it as-is (Wayland + Kitty graphics protocol + Niri compositor — none speak Windows).

| Term | What it is | Where it lives | What to do |
|---|---|---|---|
| **handterm** (upstream) | jehuang's Wayland+Linux+Rust terminal | `github.com/1jehuang/handterm` (NOT cloned locally) | Read-only reference. Do NOT clone, do NOT port code. |
| **sinister-term** (ours) | Windows-native Python+prompt_toolkit terminal shell | `projects/sinister-term/source/` + installed entry-point `sterm` / `sinister-term` | Use everywhere. Track A is shipped (PH1-PH6 ✅). Track B Rust port deferred 30 days. |

## The layering

`sinister-term` is a **shell** (runs inside a terminal emulator window), NOT a terminal emulator window itself. There are TWO layers:

1. **Terminal emulator (window)** — mintty.exe, Windows Terminal, conhost — provides the actual OS-level window with text rendering, font, cursor, colors. The Sanctum launcher spawns mintty.
2. **Shell (process inside the window)** — bash, PowerShell, `sterm` — the interactive command prompt the operator types into. Started by the terminal emulator.

`sinister-term` is a layer-2 shell. It wraps PowerShell/git-bash transparently, adds purple theme + Vault Boy ASCII boot + builtin `/forge` `/mind` `/launch` `/bot` slash-commands + auto-completion from `projects.json` / `bots/_INDEX.md` / `skills/_INDEX.md` + history persistence to `_shared-memory/sinister-term-history/`.

For the launcher to "use sinister-term" while still spawning a window: keep mintty for the window, switch the SHELL inside that window from `bash` to `sterm`.

## What was done (launcher v6.1 + sterm integration)

`automations/start-sinister-session.ps1` Launch-Session shell content — the post-claude-exit shell is now `sterm` with bash fallback:

```bash
claude --dangerously-skip-permissions '<phrase>'
# (claude exits; close-hook fires resume-point-write)
if command -v sterm >/dev/null 2>&1; then
  exec sterm
elif command -v sinister-term >/dev/null 2>&1; then
  exec sinister-term
else
  exec bash  # graceful fallback
fi
```

Operator drops into our purple-themed shell after every spawn, with our slash commands + auto-completion available.

## Why not switch claude → sterm wholesale

Two reasons:

1. **Claude is a bash CLI.** `claude --dangerously-skip-permissions '<phrase>'` is the only spawn syntax we have. `sterm` doesn't host `claude` natively as a subprocess (yet). PH-future could add a `/claude` slash command to sterm; until then bash is the right layer for claude invocation.
2. **The mintty terminal-emulator window** (with our purple color scheme + `Transparency=medium`) is OS-level rendering — sterm can't replace that. mintty is the window, sterm is the shell inside it.

## Future Rust port (Track B)

Per `projects/sinister-term/README.md` Phase 7: "Rust port evaluation (only if operator says go after 30 days v0)". If/when Track B greenlit:

- `projects/sinister-term/source/term-rs/` (Rust + ratatui — same toolkit jcode + handterm use)
- Could potentially BE the terminal emulator window if it implements its own font + cursor rendering (would replace mintty entirely)
- Single-binary distribution (per the upstream handterm philosophy operator highlighted)
- <2ms keypress latency target

Track B is **operator-gated** — do not start without explicit approval. Until then Track A (Python+prompt_toolkit) is the only path.

## "Full control like i want" — what that means

Operator-control checklist for sinister-term + launcher:

- ✅ `claude --dangerously-skip-permissions` standing default per `sanctioned-bypasses-doctrine-2026-05-21` 2026-05-23 block
- ✅ sterm fallback chain is graceful (bash if missing)
- ✅ All session env vars exported (`SINISTER_AGENT_NAME` / `SINISTER_PROJECT_KEY` / `SINISTER_MODE` / `SINISTER_MCP_COUNT` / `SINISTER_BOT_COUNT`) so sterm can read them
- ✅ Operator-canonical protections referenced inline in spawn phrase (per peer sanctum coordination)
- ✅ Resume-point close-hook fires before exec sterm
- ✅ Per-project agent_name + accent color persisted to `agent-prefs.json`

## Anti-patterns

1. **Cloning upstream `handterm` to `D:\Research\handterm\`.** Operator already said no — it's Wayland-only and won't run. Don't clone. Reference the github URL in docs, don't pull.
2. **Treating sinister-term as a terminal-emulator-window replacement.** It's a shell. mintty / Windows Terminal / conhost is the window. Don't mix layers.
3. **Spawning `claude` from inside sterm.** Sterm doesn't host claude. Spawn claude from bash, then exec sterm after claude exits.
4. **Removing the bash fallback.** If sterm isn't installed on a fresh PC, the launcher must still spawn cleanly. Always graceful-degrade.

## Composes with

- `launcher-v6.1-jcode-style-directives-2026-05-23` (the sterm-as-post-claude-shell ships in the same launcher)
- `launcher-v6-concise-rewrite-2026-05-23` (baseline)
- `sanctioned-bypasses-doctrine-2026-05-21` (--dangerously-skip-permissions remains)
- `do-not-revert-operator-canonical-protections-2026-05-23` (cold-start phrase preserves 7-step references)
- `forge-memory-usage-2026-05-23` (sterm sessions can use forge-memory via `/forge` or python -c at the prompt)
- `agent-identity-eve` (sterm boot displays purple + EVE persona)
- `jcode-feature-matrix` (sterm PH7 Rust port is one of the 📋 planned rows, delegated to sinister-term lane)
