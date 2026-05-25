<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Sinister Term (`sterm`) = default shell for every console we spawn

> **Status:** hard-canonical (operator verbatim 2026-05-23T15:33Z: *"use our sinsiter term for all consoles we run. update that in the memory and start it"*)
> **Scope:** every interactive terminal opened by the Sanctum fleet — launchers, post-Claude shells, manual operator consoles, helper consoles spawned for one-off tasks.
> **Composes with:** `handterm-vs-sinister-term-clarification-2026-05-23` (the layering), `launcher-v6.1-jcode-style-directives-2026-05-23` (post-Claude `exec sterm`), `do-not-revert-operator-canonical-protections-2026-05-23` (anti-revert).

## The rule

When the Sanctum fleet needs to open a visible interactive terminal window, the **shell inside that window MUST be `sterm`** (a.k.a. `sinister-term`), not bare `bash` / `pwsh` / `cmd`. The window itself is still `mintty.exe` (the OS-level terminal-emulator surface — sterm is layer-2 only, per the clarification doctrine).

Canonical spawn line:

```bash
mintty.exe --title "Sinister Term" -e sterm
```

Or via cmd:

```cmd
start "" "C:\Program Files\Git\usr\bin\mintty.exe" -e sterm
```

`mintty -e <prog>` runs `<prog>` as the in-window shell. When sterm exits, the window closes. Add `--hold always` if you want the window to stay open after exit.

## What "all consoles" means in practice

| Spawn surface | Pre-rule behaviour | Post-rule behaviour |
|---|---|---|
| `Sinister Start.bat` → claude session, then post-Claude shell | already `exec sterm` (launcher v6.1) | unchanged ✓ |
| Manual operator console (operator clicks "open terminal") | bash | `mintty -e sterm` |
| Agent helper console for one-off task | `cmd /c …` window | `mintty -e sterm -c "…"` (when interactive feedback needed) |
| Headless automation / hooks / scheduled tasks | hidden `pythonw.exe` / `powershell -WindowStyle Hidden` | unchanged — headless ≠ console; this rule applies only to VISIBLE interactive terminals |
| `bash` chord inside Forge / RKOJ Qt panes | shell embedded by the host TUI | unchanged for now — host owns its pane shell; rule applies to free-standing OS windows |

Headless automation stays headless (per `headless-spawn-pattern-2026-05-23`). This rule is orthogonal: sterm is the **operator-facing shell**, hidden-spawn is for non-interactive automation.

## When the operator says "open a terminal" / "start a console"

Default: spawn one mintty window with sterm inside. One-liner the master agent runs:

```bash
"C:\Program Files\Git\usr\bin\mintty.exe" -i "/mingw64/share/git/git-for-windows.ico" --title "Sinister Term" -e sterm &
```

The `&` detaches so the master agent's bash returns immediately.

## Why mintty (window) + sterm (shell) — not jcode / Windows Terminal / conhost

- mintty is already on disk (Git for Windows ships it); zero extra install.
- mintty supports 256-color + transparency + custom title — matches the purple Sanctum theme.
- sterm wraps PowerShell / git-bash transparently; the operator gets bash semantics + our slash commands + history persistence + auto-completion from `projects.json` / `bots/_INDEX.md` / `skills/_INDEX.md`.
- Windows Terminal and conhost are valid alternates but require per-machine settings.json configuration; mintty is portable + matches the launcher.

## Anti-patterns

1. **Spawn `cmd /k` or `powershell` for "give me a console"** — bypasses the slash commands + history. Always go through sterm.
2. **Replace mintty with sterm.exe directly as a window** — sterm is a layer-2 shell, not a window. There IS no sterm window without a terminal-emulator host.
3. **Remove the bash fallback in the launcher** — the post-Claude shell falls back to bash if sterm is somehow not on PATH. Removing the fallback turns a sterm install glitch into a no-shell session.
4. **Apply this rule to headless surfaces** — automation hooks / scheduled tasks / pythonw.exe stay headless. This rule covers VISIBLE terminals only.

## Verification

```bash
where sterm    # → C:\Users\Zonia\AppData\Local\Programs\Python\Python312\Scripts\sterm.exe
where mintty   # → C:\Program Files\Git\usr\bin\mintty.exe
```

If either misses, install:

- `mintty` ships with Git for Windows (`https://git-scm.com/download/win`).
- `sterm` ships from `projects/sinister-term/source/` via `pip install -e .` (entry-point `sterm` + `sinister-term`).

## Empirical anchor

2026-05-23T15:33Z — operator directive after JOKR sorter-folder fix landed; operator wanted the next interactive console for the sort workflow to be sterm. Master agent spawned `mintty -e sterm` with title "Sinister Term", confirmed window open + slash commands available.
