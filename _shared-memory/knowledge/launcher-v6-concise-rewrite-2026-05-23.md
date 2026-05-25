<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
<!-- decay:
  category: correction
  confidence: 0.98
  reinforcements: 0
  half_life_days: 365
-->
# Launcher v6 concise rewrite (start-sinister-session.ps1)

**Status:** shipped 2026-05-23 :: `agent/showmasters/scaffold-and-launch` :: see commit (pending, staged) for `automations/start-sinister-session.ps1` v5→v6
**Anchor:** operator directive 2026-05-23 verbatim: *"clean up the entire ui and audit it to be more concise and user friendly . with a very simple concise approach on everything. remove the askings of the color of the name, color, agent name, agent host. have all that auto set. remove the start up sequence and ahve it look like this from jcode when you first click it. but still ask the main questioins"*

## The pattern

**Old (v5)**: 2,373-line PowerShell launcher with multi-stage cinematic boot (matrix rain → glitch reveal → ASCII logo render → Sanctum-SectionHeader for every block) + 8-step wizard (focus prompt + speed picker + token-mode picker + host picker + agent-name Read-HostTimeout + accent-color Read-HostTimeout + multi-count picker + account picker) + cron-scheduling tail.

**New (v6)**: 467-line PowerShell launcher. One screen. Banner header → numbered project list → single Read-Host → spawn. Auto-sets everything that was previously a prompt.

## What got removed (8 prompts → 0)

| Prompt | v5 behavior | v6 behavior |
|---|---|---|
| Today's focus | Read-Host free-form | Removed |
| Speed (turbo/fast/normal) | Read-HostTimeout 15s | Auto `turbo` |
| Token mode (compact/full) | Read-HostTimeout 15s | Auto `compact` |
| Agent host (claude/codex) | Read-HostTimeout 15s | Auto `claude` |
| Agent name | Read-HostTimeout 30s | Resolved from `agent-prefs.json.per_project.<key>.agent_name` |
| Accent color | Read-HostTimeout 30s | Auto `purple` (operator standing order) |
| Multi-agent count | Read-Host 1-5 | Auto 1 |
| Anthropic account | Read-Host N-accounts | Default account only |

The 9th removal: the entire 90-line cron-scheduling tail (asking Y/N save as scheduled + cron-preset picker + name input). Operator can still schedule via RKOJ Agents tab or a dedicated tool.

## What got added (3 new affordances)

1. **`General` lane** — `key: general`, root = Sanctum root, `general: true` flag in projects.json. Cold-start phrase tells the agent "no fixed project scope; full memory access; ad-hoc operator queries; route lane-specific work to the right agent via cross-agent inbox if needed." Operator's catch-all for one-off questions.
2. **Simplified `New Project` flow** — was 6 questions (slug + display + desc + lang + files + github), now 2 (name + desc). Slug auto-derived via `Slugify` function (lowercase + `[^a-z0-9]+` → `-` + trim). GitHub repo auto-derived as `Sinister-Systems-LLC/<Display-Name-Dashed>`. Language + files-to-scaffold deferred to the cold-start phrase, which tells the spawned agent "create initial source tree + README + CLAUDE.md + SESSION-START.md + .gitignore; keep it minimal but runnable".
3. **`projects.json` schema v6 `picker` block** — top-level `picker.visible_keys[]` is the ordered list the launcher renders; `picker.special_keys[]` documents the implicit `general` / `__autoresume__` / `__newproject__` slots. Non-launcher consumers (RKOJ Qt `agents_tab.py`, sinister-eve, forge picker) continue to iterate the full `projects[]` array. Legacy entries (`sinister-forge`, `sinister-term`, `sinister-mind`, `sinister-claw`, `rkoj-workstation`) stay in `projects[]` with `_subsumed_by: "rkoj"` flag — hidden from picker, visible to consumers that need them.

## Operator-canonical project order (11 visible entries)

1. Sanctum
2. Sinister Panel
3. Kernel APK
4. Sinister Emulator
5. **RKOJ** (unified umbrella: Forge + Term + Workstation + Mind + Claw — operator confirmed the other agent owns RKOJ work)
6. Snap Emulator API
7. TikTok Emulator API
8. Bumble Emulator API
9. Sinister Freeze
10. JB Woodworks
11. Showmasters

Plus G) General, A) Auto-Resume, N) New Project.

## The cold-start phrase architecture

v5 had 9 inline mode-specific phrase templates (`overview` / `dev` / `audit` / `resume` / `expand` / `deploy` / `push` / `debug` / `explore` + `coaudit` + `auto` + `smoketest` + `securityaudit`) totaling ~6 KB of inline text, each composed of: `$MemPreamble + $ContextReviewSuffix + $NoStopSuffix + $AUPRespectSuffix + $ParallelSuffix` with `<PROJECT>` / `<ROOT>` / `<GITHUB>` / `<SPEED>` / `<AGENT>` placeholder substitution at spawn time.

v6 collapses to a single `Build-Phrase` helper with 3 shapes:

- **`isScaffold = true`** → "SCAFFOLD MODE for <project> at <root>. Read _SCAFFOLD-BRIEF.md, then create initial source tree + README.md + CLAUDE.md + SESSION-START.md + .gitignore. Keep it minimal but runnable."
- **`isGeneral = true`** → "GENERAL MODE - no fixed project scope. You have full memory access (D:\Sinister Sanctum\_shared-memory, knowledge/, PROGRESS/, plans/, inbox/, MASTER-PLAN.md, OPERATOR-ACTION-QUEUE.md). Respond to ad-hoc operator queries; route lane-specific work via cross-agent inbox if needed."
- **Default (resume)** → "RESUME MODE for <project> (root: <root>). Continue exactly where last session left off. FIRST action: read the LATEST resume-point at <resume-points-dir>/<HIGHEST-UTC>.json. ..."

All three append `READ-CONTRACTS: <session-contracts.md>` (compact reference per v15 doctrine) + identity tail `You are the '<agent>' agent. Heartbeat each turn via sinister-bus.heartbeat + sinister-bus.inbox_poll. Use purple accents.`

## 6 reusable patterns codified

1. **Picker visibility separation** — `picker.visible_keys[]` decouples the operator-facing list from the consumer-facing registry. The launcher filters; everything else iterates `projects[]` full. Avoids the "remove from registry → 3 dependent tools break" trap.
2. **Umbrella-with-components flag** — RKOJ entry has `umbrella: true` + `components: [<keys>]`. Lets consumers expand/collapse the RKOJ family programmatically (e.g., RKOJ Qt agents_tab can show its sub-lanes as tabs while the launcher renders one row).
3. **`_subsumed_by` legacy flag** — entries no longer in the picker but still referenced by code carry `_subsumed_by: "<picker-key>"`. Self-documenting; no dead code; lane consumers can detect and route to the umbrella.
4. **One-prompt-per-screen new-project flow** — derive everything that can be derived (slug, GitHub repo, root path) so only the irreducible inputs (name + desc) are operator-facing. Defer the rest to the spawned agent's first turn.
5. **3-shape cold-start phrase** — scaffold / general / resume. Each is one paragraph + a contracts reference. The 9-mode inline-template approach was over-fitted; the agent reads `session-contracts.md` for the 6 binding contracts and figures out what to do from the mode name + project context.
6. **Background resume-point write at spawn** — `Start-Process powershell -WindowStyle Hidden -File resume-point-write.ps1` fires immediately after `claude` spawns so the next session has a baseline snapshot even if the spawned agent never writes one explicitly. Survives all mid-session crashes.

## 5 anti-patterns

1. **Don't add a Read-Host every time you add a feature** — v5 grew to 2,373 lines by tacking on one new picker per requirement. The fix is to default-everything-aggressively + only prompt for the irreducible 1-3 inputs.
2. **Don't put boot animation between operator-click and answer** — matrix rain + glitch reveal felt cool the first 3 times; after the 10th launch it's friction. The picker IS the entry point. Reach it in <500ms.
3. **Don't inline 9 mode-template strings** — one helper + 3 shapes is enough. The agent reads contracts from disk; it doesn't need 6 KB of contract text re-injected per cold-start.
4. **Don't remove projects from `projects[]` to hide them** — siblings might depend on the key. Add `_subsumed_by` or use the `picker.visible_keys` allowlist instead.
5. **Don't commit while a sibling agent's git index.lock is held** — backed off this session when forcing the lock would have bundled the sibling's `projects/rkoj/*` staged work with mine. Cross-agent note + wait > force.

## 6th anti-pattern: PowerShell `Out-File -Encoding utf8` adds a BOM

Discovered + fixed within the same session (commit `bba4231`). PowerShell 5.1's `Out-File -Encoding utf8` writes a UTF-8 **byte-order mark** (`EF BB BF`) at the start of every file. Python's `json.loads()` rejects BOM-prefixed JSON with `JSONDecodeError: Unexpected UTF-8 BOM (decode using utf-8-sig)`. The launcher's `Persist-AgentPref` + `Create-NewProject` + `.claude.json` pre-trust + runlog writer all originally used `Out-File -Encoding utf8` → corrupted `projects.json` + `agent-prefs.json` → `RKOJ Qt state.load_projects()` returning `[]` because the silent `except Exception: return []` swallowed the BOM-decode failure.

**Fix**: at every PS write site that produces JSON read by Python or another strict consumer, use:

```powershell
[System.IO.File]::WriteAllText($path, $content, [System.Text.UTF8Encoding]::new($false))
```

The `($false)` argument disables BOM emission. `Set-Content -Encoding utf8` has the same BOM-emission bug on PS 5.1. PS 7+ defaults to no-BOM but check before relying on it.

Also: when the consumer is Python-with-silent-except (which a lot of state loaders do for graceful failure), debugging requires inspecting the raw bytes (`Get-Content -AsByteStream` or `[System.IO.File]::ReadAllBytes`) — string-level `Get-Content -Raw` strips BOM during read, hiding the bug.

## Empirical anchors

- Tested 8 paths: `-Project sanctum/general/rkoj/invalid` (headless) + `"5\n"` → rkoj + `"G\n"` → general + `"A\n1\n"` → auto-resume + sanctum + `"N\nTest...\na throwaway...\n"` → slug auto-derive + register + cleanup + `"\n"` → default sanctum + `"99\n"` → out-of-range fallback sanctum.
- Throughput: 2,373 → 467 lines (-80%). Cold-launch-to-spawn: ~12s (v5 with full cinematic) → ~2s (v6).
- Backup: `automations/start-sinister-session-v5.ps1.bak` preserved for cross-reference.

## Composes with

- `launcher-mode-evolution` (this entry is the v18 step in the timeline — but inverts the v1-v17 add-more-prompts trajectory)
- `auto-mode-launcher-pattern`
- `agent-identity-eve` (purple accent + EVE persona still honored)
- `resume-point-dir-name-convention` (auto-resume reads `_shared-memory/resume-points/**`)
- `resume-point-write-ps1-fulltree-scan-hang-2026-05-21` (background-write pattern preserved)
- `multi-agent-branch-contention-isolation-pattern` (commit deferred because sibling held lock)
- `sinister-cli-subcommand-pattern` (alternative dispatch model for non-launcher entry points)

## Operator-gated follow-ups

- Push commit when `.git/index.lock` clears (sibling Showmasters agent owns the branch right now)
- Consider whether the v5 `.bak` file should be deleted once v6 confidence is high
- New-project flow could re-add the language picker if the cold-start phrase produces too-generic scaffolds across Python/TS/Rust projects — empirical test needed across 3-5 invocations to know
