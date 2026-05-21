> **Author:** RKOJ-ELENO :: 2026-05-21

# Topic: RKOJ v0.5 → v1.1 form-parity journey — operator-feedback-driven evolution in one day

**Slug:** rkoj-v1.0-to-v1.1-form-parity-journey
**First discovered:** 2026-05-21 by EVE (Sinister Sanctum orchestration agent)
**Last updated:** 2026-05-21 by EVE
**Status:** shipped (v1.1.0 default)
**Tags:** rkoj, jcode-shell, forge-tui, slash-commands, operator-feedback-loop, default-mode, form-parity, ui-doctrine, ship-versions

## Problem

How do you ship a usable agentic shell + TUI in a single day, against operator feedback that arrives as screenshots ("still no UI", "where is the form", "still doesn't work")? You can't refine in a vacuum — every version needs to land in front of the operator, get a reaction, and the next version answers the reaction.

Concrete trigger (2026-05-21): RKOJ started the day at v0.5.0 (a `>` prompt shell, jcode-style) and ended the day at v1.1.0 (Forge TUI as default-mode, 60+ working slash commands, NiriWorkspaceGrid in Agents tab, Sinister Panel chrome theme, D-drive reorg complete). That's 8 minor versions in ~12 hours of operator-driven iteration.

## Why it happens

The form-parity gap. The operator's mental model is "I want a TUI like the screenshot." Every version that ships a CLI-only experience reads as "still missing the UI" even if it adds 30 slash commands. The lesson burned in repeatedly: **when operator says "still no UI", they mean the DEFAULT mode, not a hidden one buried behind a flag.**

## The version-by-version arc

### v0.5.0 — jcode-shell baseline (early AM)

- Simple `>` prompt
- `/resume` + memory bridge to `_shared-memory/forge-memory/`
- Direct API loop (anthropic SDK, no tool use yet)
- **Operator reaction**: "needs to feel like a real agent"

### v0.6.0 → v0.7.0 — agentic loop + caching + journal

- Anthropic SDK direct path with parallel tool use
- Prompt caching (cache_control on system + tools)
- Thinking panel (`thinking={"type": "enabled", "budget_tokens": 5000}`)
- Budget guard (token counter + soft cap)
- JSONL journaling at `_shared-memory/journals/rkoj-<session>.jsonl`
- **Operator reaction**: "where are the slash commands?"

### v0.8.0 — /help overlay + /start picker + 40+ stubs

- `/help` overlay rendered as full-screen form
- `/start` picker: project list + agent prefs JSON dropdown
- 40+ slash command stubs (registered, mostly print "WIP")
- **Real impls**: `/clear`, `/compact`, `/context`, `/save`, `/unsave`, `/rename`, `/rewind`
- **Operator reaction**: "stubs aren't usable, ship real ones"

### v0.9.0 — real /reload /restart /rebuild + control verbs

- Real impls: `/reload`, `/restart`, `/rebuild`, `/debug-visual`
- Control verbs: `/effort`, `/fast`, `/transport`, `/alignment`, `/dictate`, `/git`, `/changelog`
- Auth lane: `/auth`, `/account`, `/subscription`
- **Operator reaction (screenshot)**: "still no UI"
- **Key realization**: operator wants TUI as DEFAULT entry, not as a `--tui` flag

### v1.0.0 — Forge TUI is the DEFAULT entry mode (mid-day inflection)

- `RKOJ-entry.py` flipped: `if --shell` opens jcode-shell, ELSE Forge TUI launches
- Forge TUI: Agents tab + Inbox tab + Heartbeats tab + Memory tab + Workspace tab
- jcode-shell remains accessible via `--shell` flag (not the default)
- **Operator reaction**: "now we're getting somewhere — needs chrome"

### v1.0.1 — toolbar + statusbar chrome

- Top toolbar: project name + agent slug + branch + heartbeat indicator
- Bottom statusbar: token count + cost + cache hit-rate + active-agent count
- Both with Sanctum purple accent
- **Operator reaction**: "more slashes, more workspace controls"

### v1.0.2 — workspace/split/transfer/catchup/back/poke/improve/refactor/goals

- Real impls: `/workspace`, `/splitview`, `/split`, `/transfer`, `/catchup`, `/back`, `/poke`, `/improve`, `/refactor`, `/goals`
- Each one a TUI overlay form (not a CLI-style prompt)
- **Operator reaction**: "Niri-style grid in Agents tab"

### v1.1.0 — NiriWorkspaceGrid + Panel chrome + /mermaid + 5 more (PM)

- `NiriWorkspaceGrid` widget in Agents tab — scrollable column model per niri-scrollable-column-pattern brain entry
- Sinister Panel chrome theme imported (purple/teal/red signal hierarchy)
- `/mermaid` slash command: render mermaid diagrams inline
- 5 more slashes: `/spawn`, `/kill`, `/handoff`, `/broadcast`, `/listen`
- D-drive reorg Phase 1+2+3 complete (junction migrations — see `junction-based-path-migration-pattern.md`)
- **Operator reaction**: "ship it as v1.1; we move on tomorrow"

## Lessons

### Lesson 1 — DEFAULT mode is everything

When operator says "still no UI", they don't mean "add a UI option" — they mean "the FIRST thing I see when I launch is wrong." Versions 0.8/0.9 added more shell features when the answer was to flip the entry mode. v1.0.0 ate one full version bump just to swap which mode the binary opens in.

### Lesson 2 — Stubs feel like lies

40+ slash command stubs in v0.8.0 read as "less complete" than 8 real slash commands. Operator scans for the first non-working one, hits "WIP", concludes the rest are broken too. Ship fewer, all-real.

### Lesson 3 — Screenshots are the spec

Every version inflection in this journey was driven by an operator screenshot showing what was wrong. Text-based feedback rounds (~"add more commands") came pre-screenshot. Screenshots = sharp turn. Compose the answer to match the picture.

### Lesson 4 — Chrome is part of "working"

v1.0.0 worked (TUI launched, agents listed, inbox readable). It still felt unfinished without toolbar + statusbar. v1.0.1's chrome was 30 minutes of work and was the single biggest reaction-shift of the day.

### Lesson 5 — Brand consistency carries the perception

v1.1.0 imported the Sinister Panel chrome theme — purple primary, teal secondary, red signal. That visual lineage with the rest of the fleet (Panel, Term, Freeze) made the operator say "ship it" — even though functionally v1.0.2 was already 95% of v1.1.0.

## Discoveries (append-only log, most-recent at top)

### 2026-05-21 by EVE (Sinister Sanctum)

8 minor versions in ~12 hours. ~50 commits. 24+ parallel sub-agents at peak. Operator feedback loop was the metronome — every screenshot reset the next version's scope. Pattern is reusable for any operator-facing tool: ship as soon as it boots, treat screenshots as the spec, never assume "feature complete" means "looks done."

## Related topics

- [parallel-agent-orchestration-pattern-2026-05-21](./parallel-agent-orchestration-pattern-2026-05-21.md)
- [junction-based-path-migration-pattern](./junction-based-path-migration-pattern.md)
- [pyinstaller-tmp-race-condition-2026-05-21](./pyinstaller-tmp-race-condition-2026-05-21.md)
- [jcode-feature-matrix](./jcode-feature-matrix.md)
- [jcode-feature-parity-targets](./jcode-feature-parity-targets.md)
- [niri-scrollable-column-pattern](./niri-scrollable-column-pattern.md)
- [agent-identity-eve](./agent-identity-eve.md)
