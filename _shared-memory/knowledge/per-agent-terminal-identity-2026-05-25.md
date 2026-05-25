<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
> **Author:** RKOJ-ELENO :: 2026-05-25

# Per-agent terminal identity (name + accent + permanent header + sick transparent look)

Operator hard-canonical 2026-05-25T~03:30Z verbatim (with Image #6 + #7):
*"i need the name and color to be like this agent is [Image #6] i want the terminals them selves to look sick and have the transparent look and i want a permanent header up here: [Image #7] to show me all things on like swarm etc. make it in brand with sinister software."*

## Source-of-truth investigation (jcode read-it doctrine)

Read `C:\Users\Zonia\Desktop\jcode-0.12.4\` directly per `we-have-the-source-read-it-doctrine-2026-05-25.md` — no reverse-engineering.

- `crates/jcode-tui-style/src/theme.rs:50` — `header_session_color()` returns a static `rgb(255,255,255)`. NOT a config-driven key; jcode's TUI hardcodes its own header colour.
- `src/tui/session_picker.rs:660` — same static.
- `src/tui/ui_overlays.rs:493` — serialised to JSON snapshot but read-only.

**Finding:** Image #6's "Sinister OS" purple badge is a screenshot of **jcode's own TUI**, not Claude Code (the upstream Anthropic CLI we actually spawn). Claude Code has NO equivalent in-app `/color`-as-config persistence — there's no `~/.claude/settings.json` key for session badge or session accent. The closest analog Sanctum already has + can extend is the **mintty terminal that wraps the Claude session**: title bar (visible at top of window) + window foreground/background/cursor colour (OSC sequences set in launch.sh) + mintty `-o` palette options.

## What we shipped (single-file edit to `automations/start-sinister-session.ps1`)

### 1. Permanent header in mintty title bar (Image #7 surface)

Old format: `Sinister :: <agent> :: <display> [SWARM] [LOOP]`
New format: `<agent> ◆ swarm=<on|off> ◆ loop=<off|on|relentless> ◆ acct=<slot> ◆ T<tier> ◆ Sinister`

Example: `Sinister OS ◆ swarm=on ◆ loop=relentless ◆ acct=operator ◆ T2 ◆ Sinister`

- `◆` (U+25C6) separator used in bash-side OSC printf (`\033]0;...\007` line 1907 of the .sh).
- mintty `-t` arg uses ASCII-safe `|` separator (Win32 CreateProcess arg parsing has historically choked on multi-byte unicode + spaces + special chars; the bash printf converges to ◆ once shell starts — belt-and-suspenders).
- `loop=relentless` reflects `default_modes.loop_relentless` from `projects.json` v10 (default-on for every loop=true project per `loop-relentless-pursuit-doctrine-2026-05-25.md`).
- Tier read inline (forward-reference fix — `$projTier` was defined ~50 lines later than the title block).

### 2. Per-agent name + accent colour (already existed, now richer)

Already wired pre-existing:
- `$colorMap` in `start-sinister-session.ps1:1825-1830` defines 6 accents (purple/magenta/cyan/green/yellow/white) with fg/bg/cur hex tuples.
- Per-project accent loaded from `agent-prefs.json` via `Get-ProjectAccent` (line 304).
- OSC sequences `\033]10;<fg>\007 \033]11;<bg>\007 \033]12;<cur>\007` in launch.sh (lines 1908-1910) set terminal-wide foreground/background/cursor when shell starts.

The agent NAME shows in:
- mintty title bar (now the canonical permanent header, see #1).
- bash pill banner at row 1 (DECSTBM sticky region, lines 1953-1956) — `$pillA $agentName $pillZ` purple pill.

### 3. Sick transparent look + Sinister-branded mintty options

Reverted the 2026-05-24 "transparency=off" change (which fixed an earlier "on top of browser" optical illusion) — NOW operator-canonical: transparency ON + opaque-when-focused.

New mintty `-o` flags added at line 2249-2275:
```
-o Transparency=low
-o OpaqueWhenFocused=yes
-o Font=Cascadia Mono
-o Black=16,8,32  Red=255,90,110  Green=152,255,180 ...
-o Magenta=192,132,252  (Sinister canonical PURPLE #c084fc)
-o White=232,214,255    (Sinister PALEP #e8d6ff)
-o BoldMagenta=216,180,254 (Sinister BRIGHTP #d8b4fe)
```

Browser-overlay regression NOT reintroduced: `OpaqueWhenFocused=yes` means window is solid while focused (where operator is typing) and only see-through when blurred/background.

Palette colours sourced from `_shared-memory/knowledge/sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24.md` canonical tokens.

## EXACT mintty command line next spawn (Sanctum lane, default modes)

```
mintty.exe \
  --hold error \
  -t "Sinister Sanctum | swarm=off | loop=off | acct=operator | T3 | Sinister" \
  -o ForegroundColour=232,214,255 \
  -o BackgroundColour=21,19,26 \
  -o CursorColour=160,110,255 \
  -o FontSize=11 \
  -o Font="Cascadia Mono" \
  -o Term=xterm-256color \
  -o Transparency=low \
  -o OpaqueWhenFocused=yes \
  -o Black=16,8,32 -o Red=255,90,110 -o Green=152,255,180 \
  -o Yellow=255,210,140 -o Blue=140,180,255 -o Magenta=192,132,252 \
  -o Cyan=140,230,255 -o White=232,214,255 \
  -o BoldBlack=58,40,76 ... (8 bright variants) ... \
  -- /bin/bash <launchShBash>
```

After bash starts inside that window:
- OSC `\033]0;Sinister Sanctum ◆ swarm=off ◆ loop=off ◆ acct=operator ◆ T3 ◆ Sinister\007` overrides the ASCII title with the diamond version.
- OSC `\033]10/11/12` reinforces fg/bg/cursor (matches what mintty already set via `-o`).
- DECSTBM sticky pill banner remains in row 1.

## Smoke test results

- `[scriptblock]::Create((Get-Content -Raw 'automations\start-sinister-session.ps1'))` → **PARSE-OK** (PowerShell tool, 2026-05-25T03:35Z).
- No real spawn performed (would interrupt operator's open sessions).
- Diff scoped to two contiguous blocks — title-build (~20 lines) + mintty-args (~30 lines).

## Limitations / what operator sees next spawn

1. **`-t` ASCII fallback is intentional.** mintty's window title may briefly show `|` separators in the very first frame (taskbar shows ASCII version until bash printf runs ~50ms later). Once bash OSC fires, title becomes the `◆` diamond version. Operator sees `◆` 99% of the time.
2. **Title bar updates are static once set.** If operator flips swarm/loop mid-session via fleet-update, the title bar won't auto-update. Future expansion: bash trap watching `_shared-memory/fleet-updates.jsonl` + re-printf'ing OSC 0 on swarm/loop transitions. Out of scope this iter.
3. **Browser-overlay risk:** `Transparency=low` + `OpaqueWhenFocused=yes` means focused window is opaque (no overlay risk). If operator reports the issue again, knob is `Transparency=off` (revert) or `Transparency=high` (more see-through but more overlay risk).
4. **Per-project accent already works** via `agent-prefs.json` per-project `accent_color` field. Operator can verify by running `eve.py` Onboarding → Customize-Project (or by hand-editing `agent-prefs.json`). No new UI needed.
5. **The "Sinister OS" badge from Image #6** is NOT achievable inside Claude Code (no upstream Anthropic config key for it). Closest equivalent in Sanctum is the title bar header we just shipped (Image #7 surface). If operator wants a pop-up overlay badge specifically, that requires a separate AHK/Win32 sidecar — out of scope this iter and not the operator's primary ask.

## Compose-with

- `we-have-the-source-read-it-doctrine-2026-05-25` (read jcode directly)
- `eve-ui-uniformity-doctrine-2026-05-24` (canonical color tokens)
- `loop-relentless-pursuit-doctrine-2026-05-25` (loop_relentless flag in title)
- `sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24` (Sinister palette source)
- `no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25` (no new .ps1; edited existing)

Decay: preference / 1.0 / 365.
