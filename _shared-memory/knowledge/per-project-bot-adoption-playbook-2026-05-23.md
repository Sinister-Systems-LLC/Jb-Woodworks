<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Per-Project Bot-Adoption Playbook

**Created:** 2026-05-23 (EVE on Sanctum, Phase-2 C.10 of `sanctum-complete-and-expand-2026-05-23T1145Z`)
**Triggering audit:** `jcode-swarm-token-parity-audit-2026-05-23` found per-project lanes (Panel 1 / APK 5 / RKOJ 0 / RKOJ-workstation 0 bot mentions in 7 days) effectively ignoring the 13-bot MCP fleet while master uses them heavily (22 mentions). This playbook closes the adoption gap.
**Composes with:** `bot-fleet-quick-reference-2026-05-23` (the lookup table this references) + `jcode-swarm-token-parity-audit-2026-05-23` (the diagnosis) + `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (every claim below is grounded in shipped surfaces) + `forge-memory-usage-2026-05-23` (orthogonal — that doctrine covers per-agent working memory; this one covers fleet-service calls).

---

## The 60-second cold-start template

Every per-project agent — Panel, APK, RKOJ, Showmasters, JB Woodworks, Forge, Term, anyone — adds these three steps to **the first turn of every session**, before substantive work:

```text
1. Heartbeat        sinister-bus.heartbeat(my_agent="<display name>")
2. Inbox poll       sinister-bus.inbox_poll(my_agent="<display name>")
3. ONE bot call     pick the one most likely to short-circuit the task ahead
```

That's it. 60 seconds. If the MCP isn't loaded (deferred), the call is:

```text
ToolSearch select:mcp__sinister_bus__heartbeat,mcp__sinister_bus__inbox_poll
```

…then call them. After that the schemas persist for the rest of the session at no per-call cost.

**Why these three:**

- **Heartbeat** is canonical Rule 9 (CLAUDE.md). Without it, master agent can't tell you're online — siblings can't coordinate.
- **Inbox poll** surfaces `[DELEGATE]` / `[ASK]` / `[INFO]` messages from other lanes. Acting on stale assumptions when a sibling already told you the answer is the #1 waste pattern.
- **One bot call** anchors the habit. The fleet exists; calling it once per session keeps it warm in the mental model.

---

## Which bot to call on step 3 (lane-specific cheat sheet)

| Lane | Most-likely-useful bot | Why | Example call |
|---|---|---|---|
| **Panel** (Snap consumer flows) | `triage.classify_text` or `librarian.search` | Classify a paste from a runlog; find prior consumer-flow docs without 5 KB context | `librarian.search(query="att_sign phase a b c", top_k=5)` |
| **APK** (kernel + gradle) | `auditor.scan_secrets` or `custodian.snapshot_now` | Pre-build secret scan; backup before risky kernel edit | `custodian.snapshot_now(path="<file before patch>")` |
| **RKOJ** (PyQt6 workstation app) | `librarian.search` or `translator.find_tool` | Find prior slash-command implementations; locate the right MCP for a new feature | `translator.find_tool(query="qt window state persistence")` |
| **RKOJ-workstation** (per-user runtime state) | `sentinel.check_urgent` + `custodian.list_versions` | Surface upcoming deadlines; check backup history before workspace shuffle | `sentinel.check_urgent(window_days=7)` |
| **Showmasters** (Snap pro flows) | `librarian.search` + `researcher.summarize_url` | Find prior brand+brand-lock decisions; summarize external Snap docs without WebFetch tokens | `researcher.summarize_url(url="<snap doc>", focus="business profile")` |
| **JB Woodworks** (Next.js site) | `librarian.search` + `auditor.scan_secrets` | Find prior copy/brand decisions; pre-deploy secret scan | `librarian.search(query="jb portfolio component patterns")` |
| **Forge** (CLI substrate) | `translator.find_tool` + `sinister-bus.list_network` | Locate the right MCP surface; map the network before adding a new wire | `sinister-bus.list_network()` |
| **Term** (sterm shell) | `librarian.search` + `sinister-bus.who_is_online` | Find prior shell-integration patterns; see which agents are live for cross-pane handoff | `sinister-bus.who_is_online()` |
| **Sinister Generator** (image gen) | `custodian.list_versions` on `outputs/` | Avoid re-generating something already cached | `custodian.list_versions(path="projects/sinister-generator/outputs/<concept>.png")` |
| **Kernel APK + RKOJ + Panel** (any active dev lane) | `sentinel.check_urgent(7)` | Surface time-pressured items operator wants surfaced (Yurikey expiries, deadlines) | `sentinel.check_urgent(window_days=7)` |

If the table doesn't suggest something obviously useful, default to `librarian.search` for the task's keywords — it almost always returns something relevant from the 8,500+ `.md` archive.

---

## Cold-start drop-in (copy into your lane's CLAUDE.md)

Paste this block into your project's `CLAUDE.md` under a `## Cold-start (every turn)` heading. Edit `<display name>` once per lane.

```markdown
## Cold-start (every turn)

1. Heartbeat: `sinister-bus.heartbeat(my_agent="<display name>")` (or write `_shared-memory/heartbeats/<slug>.json` as fallback)
2. Inbox poll: `sinister-bus.inbox_poll(my_agent="<display name>")` — surface `[DELEGATE]` / `[ASK]` / `[INFO]` BEFORE substantive work
3. Pick one bot from `_shared-memory/knowledge/bot-fleet-quick-reference.md` most likely to short-circuit the task ahead. Default: `librarian.search(query=<task keywords>, top_k=5)`
4. If MCPs aren't loaded: `ToolSearch select:mcp__sinister_bus__heartbeat,mcp__sinister_bus__inbox_poll,mcp__librarian__search` then proceed
```

---

## What "good adoption" looks like (target metrics for next 7-day audit)

| Lane | Current (2026-05-23) | Target (next audit) | Signal |
|---|---|---|---|
| Sanctum master | 22 bot mentions / 32 swarm | (stay healthy) | reference baseline |
| Sinister Panel | 1 bot mention | ≥ 5 | PROGRESS log search hits |
| Sinister Kernel APK | 5 | ≥ 8 | PROGRESS log search hits |
| RKOJ | 0 | ≥ 3 | PROGRESS log search hits |
| RKOJ-workstation | 0 | ≥ 2 | heartbeat + sentinel calls |
| Showmasters | (audit pending) | ≥ 5 | PROGRESS log search hits |
| JB Woodworks | (audit pending) | ≥ 3 | PROGRESS log search hits |
| Forge | (audit pending) | ≥ 5 | PROGRESS log search hits |

### Baseline run 2026-05-23T14:30Z (rkoj-lane /loop iter 7)

Captured by running the measurement command below from the rkoj-lane session
mid-/loop. Records the absolute starting point so the next 7-day audit can
diff against it. Per-project-lane CLAUDE.md drop-in (rkoj's just landed in
/loop iter 2 of 2026-05-23) should start moving these counters; lanes still
at zero are the most-likely-non-adopters.

| Lane (file in `_shared-memory/PROGRESS/`) | Count @ 14:30Z |
|---|---|
| Sinister Panel | 0 |
| Sinister Kernel APK | 1 |
| rkoj | 0 |
| rkoj-workstation | 1 |
| Showmasters | 0 |
| jb-woodworks | 0 |
| Sinister Forge | 0 |
| Sinister Sanctum | 4 |
| **TOTAL across 8 lanes** | **6** |

Note: the "Current (2026-05-23)" column above is the jcode-swarm-parity-audit's
*sampled* count (uses different keyword patterns + may include
cross-references in the same file). This baseline is the strict regex per the
measurement-command block (only the lowercase-bot-with-trailing-dot pattern).
Both numbers are useful; treat them as orthogonal signals.

Measurement command (run from Sanctum, any session):

```bash
for lane in "Sinister Panel" "Sinister Kernel APK" "rkoj" "rkoj-workstation" "Showmasters" "jb-woodworks" "Sinister Forge"; do
  count=$(grep -ci "sinister-bus\.\|librarian\.\|triage\.\|researcher\.\|scribe\.\|curator\.\|auditor\.\|sentinel\.\|custodian\.\|stealth-browser\." "_shared-memory/PROGRESS/${lane}.md" 2>/dev/null || echo 0)
  printf "%-30s %s\n" "$lane" "$count"
done
```

---

## Why this matters (the token math)

Per `jcode-swarm-token-parity-audit-2026-05-23` recommendation #1:

- A typical "find prior decision X" task done via Read + Grep + reasoning burns **~3-8 KB input context + 1 reasoning turn** = ~5-10K tokens at Opus rates.
- The same task via `librarian.search(query="X", top_k=5)` burns **~500 bytes input + the result summary** = ~1-2K tokens.
- Net savings: **60-80%** per substitution, with the saved capacity available for the actual work.

A per-project lane that does 5 such substitutions per session saves enough headroom to avoid one mid-session context-pruner cycle entirely. Across the 7-lane active fleet that's **~30-50K tokens saved per parallel session-hour** — operator's bill is operator's bill, but the latency win is immediate.

---

## Anti-patterns

1. **"I'll add bots later, this task is small."** Adoption habit forms in the first 3 turns. If you skip step 3 on turn 1, you'll skip it on turn 50. Default to one call always.
2. **Replacing critical reasoning with bot output.** `librarian.search` is great for "find the file"; it is NOT good for "decide the architecture". Bots are first-pass filters, not last-pass deciders.
3. **Calling Tier-3 bots in a loop.** `scribe` and `curator` are paid (Haiku, ~$0.02-0.05/call). Batch. Preview with `list_inputs()` / `assess_file()` before committing to the LLM call.
4. **Forgetting the deferred-tool load.** New session = schemas not in context = first call fails. Always pre-load via `ToolSearch select:...` once per session.
5. **Heartbeat-only adoption (no actual bot calls).** Heartbeat is cheap but signals nothing about token-efficiency. Counting heartbeats as "adoption" defeats the audit. Adoption = real work routed to bots.
6. **Re-implementing bot functionality inside your project.** If you find yourself building a "search the archive" feature in your project code, you've reinvented `librarian`. Stop. Use the bot.

---

## Lane-specific adoption checklist (one-time setup)

For each per-project agent:

- [ ] Add the cold-start drop-in block to `projects/<lane>/CLAUDE.md` (or product-repo `CLAUDE.md` if it mirrors).
- [ ] Pick the lane's "most-likely-useful bot" from the table above; document it as the default in the per-lane drop-in.
- [ ] On the next turn after install, verify the call works (one round-trip) and record in PROGRESS as `Bot adoption: <bot>.<tool> shipped in cold-start`.
- [ ] Re-run the measurement command in 7 days; surface the count in the next sanctum audit.

---

## What this playbook does NOT cover

- Bot **implementation** (server.py edits) → lives in `D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\<bot>\` and is owned by sinister-bus lane.
- Bot **memory protocol** (absorb / list_facts / forget) → see `docs/BOT-MEMORY-PROTOCOL.md`.
- Bot **registration** (`~/.claude/.mcp.json`) → operator-owned per canonical-11.
- Cross-bot composition (`researcher` → `librarian` → `scribe`) → covered in `bot-fleet-quick-reference.md` "Composition recipes" section.

This file is **adoption-side only**: how every per-project agent gets the habit + lane-specific defaults + how to measure success.

---

## Maintenance

- When a new bot lands: add a row to the per-lane cheat sheet if it's lane-specific; otherwise just reference `bot-fleet-quick-reference.md`.
- When a lane changes ownership or scope: re-pick the "most-likely-useful bot" for that lane.
- On every weekly audit: re-run the measurement command + update the "current" column of the metrics table.
