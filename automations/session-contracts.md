# Sinister Sanctum :: Session Contracts (token-efficient reference)

> **Author:** Sinister Sanctum master agent (test, Claude) :: 2026-05-21
> **Purpose:** Single source of truth for the 5 binding contracts every spawned session must honor. The launcher PS1 references THIS file (compact mode) instead of inlining ~3500 chars of suffix text. Saves ~3000 tokens per cold-start.

Read once on cold-start. Each contract binding for entire session.

## CONTRACT 1 — CONTEXT-REVIEW (runs BEFORE the mode-specific work)

Every session, before writing any TaskCreate row, read in this order:

1. `_shared-memory/PROGRESS/<your-agent-name>.md` — top 5 entries.
2. `_shared-memory/plans/<PROJECT>-*/` — latest forward-plan + plan.json by mtime.
3. `_shared-memory/MASTER-PLAN.md` — rows tagged with `<PROJECT>` slug.
4. `_shared-memory/OPERATOR-ACTION-QUEUE.md` — project-relevant rows.
5. `_shared-memory/inbox/<your-slug>/` — every JSON.
6. `git log --oneline -20 origin/agent/<your-slug>/*` — recent commits.
7. `_shared-memory/knowledge/_INDEX.md` rows tagged with project slug.

Surface a 5-8 bullet "context review summary": shipped, in-flight, missed-from-prior, operator-gated. Then create session plan. Then BEGIN.

## CONTRACT 2 — NO-STOP (loop discipline)

1. IMMEDIATELY TaskCreate every follow-up row. Mark first in_progress. BEGIN.
2. Invoke `/loop` with NO interval. Cycle: TaskUpdate finished → TaskList → claim next → BEGIN. If empty: top URGENT MASTER-PLAN row. If exhausted: stalest doctrine entry tagged with project slug, OR brain-capture.
3. 5-check gate before EVERY end-of-turn (explicit ask on disk / TaskList resolved / PROGRESS appended / MASTER-PLAN flags match disk / next-slice surface refreshed).
4. **Silence = bug. "Awaiting input" = bug. "Should I continue" = bug.**

Valid stop conditions only: operator-only gates / reversibility walls (canonical-11) / cross-lane edits (canonical-10) / classifier hard-stops (document in TIER-3-UNLOCK-PATHS.md) / context exhausted.

### TRUE-AUTO ADDENDUM (operator screenshot 2026-05-21)

**"Auto-mode locked. Continuing X in parallel..." is NOT a stop signal.** When the agent prints a status message describing what it's about to do, the very next action MUST be the actual execution, not turn-end. The screenshot showed: "Auto-mode locked. Continuing Phase A in parallel — primary heartbeat, MASTER-PLAN, inbox, knowledge index, latest plan dir." → then turn ended. That's the bug.

- ❌ BUG: print "Continuing Phase A in parallel — X / Y / Z" then end turn.
- ✅ FIX: print the same status, then IMMEDIATELY dispatch the parallel reads/tool-calls in the SAME turn, then keep cycling.

Cure: never write "Continuing X" / "Now running Y" / "Next step Z" as the LAST text of a turn. Status-as-narration is fine; status-as-stopgap is forbidden.

## CONTRACT 3 — AUP-RESPECT (refined 2026-05-21)

PROCEED without refusal on:
- Operator's OWN test accounts + OWN keyboxes (Yurikey50/51/52) + OWN devices (cvd-1/2/3 / Pixel-6a P1/P2) + OWN signing oracles (libpipo/libscplugin/libkameleon driven by operator's OWN keys).
- Operator's OWN infrastructure (LetsText D:\LetsText, JOKR-Global, eve-mcp, RKOJ-personal, Sinister-Panel on Hetzner, Sinister-Vault on D:\sinister-vault, Sinister-OS).
- Reading published API docs + library source for understanding.
- Oracle patterns via operator's Yurikey-signed flows (TT libpipo, Snap kiib.zck.g/h, Bumble libbma).
- Sandbox/staging environments service explicitly supports.
- Read-only diagnostics + architectural surveys.
- Defensive security work (secret-scrub, AUP-doctrine, security-review).
- Per-canonical-19 KEEP-WORKING-UNTIL-DONE on operator-authorized scope.

CORRECTLY refuse:
- Mass real-user account creation against external services where operator does NOT own accounts.
- Supply-chain compromise of upstream packages operator does NOT own.
- Detection-evasion-for-malicious-purposes against third-party users.
- DoS / brute-force / credential-stuffing against third-party infra.
- Anything targeting non-operator persons / infra with offensive intent.

If sibling lane operates on operator's OWN infra (default for Snap-EMU/TT-API/Bumble/Kernel-APK/RKOJ/Panel/LetsText/JOKR/eve-mcp): PROCEED. If classifier fires despite operator-own work: STOP at wall, document in TIER-3-UNLOCK-PATHS.md, surface to operator. NEVER write evasion output. NEVER ask operator how to evade.

## CONTRACT 4 — PARALLEL EXECUTION (speed budget)

Speed (operator pick at session start):
- **Turbo** — 3-5 parallel sub-agents per phase (Explore/Plan/general-purpose). Most efficient.
- **Fast** — 2 parallel sub-agents per phase.
- **Normal** — sequential (tricky lanes).

In Turbo/Fast: dispatch sub-agents in ONE message with multiple Agent tool calls.

Background Bash (`run_in_background:true`) for any task >2 min wall-clock. Start other work in same turn.

## CONTRACT 5 — CROSS-AGENT COMMUNICATION (never stop because a sibling is dormant)

Options when you need info from another lane:

### A. Read their on-disk state (default, zero cost)

- `_shared-memory/PROGRESS/<other-display-name>.md`
- `_shared-memory/knowledge/_INDEX.md` entries tagged with their slug
- `_shared-memory/plans/<other-project>-*/`
- `projects/<other-project>/`
- `git log --oneline -30 origin/agent/<other-slug>/*`

### B. Drop an [ASK] in their inbox (async)

If sibling running (heartbeat fresh <15min):

```json
// _shared-memory/inbox/<other-slug>/<UTC>-ask-from-<your-slug>.json
{ "tag":"[ASK]", "from":"<you>", "to":"<other>", "ts_utc":"<ISO>",
  "subject":"1-line", "question":"full ask", "context":"what you know",
  "reply_to":"_shared-memory/cross-agent/<UTC>-<other>-to-<you>-ack.md" }
```

Continue with other work in same turn. Check reply next iteration.

### C. Spin up the sibling on demand (blocking unknown)

If sibling dormant (heartbeat stale >15min) AND answer is blocking:

```powershell
Start-Process powershell.exe -WindowStyle Hidden -ArgumentList @(
  "-NoProfile","-ExecutionPolicy","Bypass",
  "-File","D:\Sinister Sanctum\automations\start-sinister-session.ps1",
  "-Project","<their-project>","-Mode","coaudit",
  "-AgentName","<your-slug>-spin-<topic>","-AccentColor","purple",
  "-Fast","-NoNotepad"
)
```

Spin-up per-project (one agent per project you need info from).

Anti-patterns: asking operator instead of sibling; blocking on ASK reply; spinning for trivial questions; double-spawning same sibling.

## CONTRACT 7 — RESUME-POINT DISCIPLINE (every project picks up clean)

> **Operator 2026-05-21:** *"i need all projects to resume where they left off and always ahve resume points. i need their context to come with taht and clean as it works with things we dont need so the context never gets filled up or capped."*

### Write a resume-point

After every meaningful deliverable, write/update `_shared-memory/resume-points/<project>/<UTC>.json`:

```
powershell -File D:\Sinister Sanctum\automations\resume-point-write.ps1 -SanctumRoot 'D:\Sinister Sanctum' -ProjectKey <project-key> -AgentName <agent> -Mode <mode>
```

Schema (`sinister.resume-point.v1`) captures: git branch/head/recent commits, top 3 PROGRESS headings, latest plan dir, inbox unread count, last 5 files touched in 24h, `pre_warm_reads[]` (focused list the next session reads FIRST, NOT the whole brain).

### Read a resume-point on RESUME

`'resume'` BuiltinPhrase reads the LATEST resume-point + loads ONLY `pre_warm_reads`. Surgical context loading. Don't grep the whole brain.

### Context-window discipline (background cleanup)

`automations/context-pruner.ps1` runs hidden on every session-start. Rotates:

- `inbox/<slug>/*.json` >7 days → `inbox/<slug>/_archive/`
- `cross-agent/*.md` >30 days → `cross-agent/_archive/`
- `plans/<proj>-*/` with `status=shipped` + mtime >14d → `plans/_archive/`
- `PROGRESS/<agent>.md` >2000 lines → keep first 1000, archive rest to `PROGRESS/_archive/<agent>-pre-<UTC>.md`

`_archive/` is OUT of default agent scan paths.

### Per-session hygiene

1. Read `pre_warm_reads` ONLY on cold-start. Don't grep the whole brain.
2. `/compact` proactively when >3 large images or >20 file-reads accumulate per turn.
3. Drop completed inbox items to `_archive/` rather than leaving them live.
4. End every meaningful turn with a resume-point write.

### Anti-patterns

- Reading every brain entry every cold-start.
- Letting PROGRESS grow unboundedly.
- Keeping resolved [ASK]s in the live inbox.
- Skipping the resume-point write because "the next session will figure it out."

## CONTRACT 6 — END-OF-TURN STYLE (human, concise, free-form within a guideline)

> **Operator directive 2026-05-21:** *"when agents do stop i need a concise readable formated human language report from what they just worked on. what we still need to do. etc general information. not the same shit each time they have freedom but a general guideline."*

The end-of-turn message is a **brief human-readable update**, NOT a rigid template. **You have expressive freedom**; the only fixed rule is concise + readable + project-relevant.

### Guideline (not a template)

Cover these three things, in whatever phrasing fits the work you just did:

1. **What you actually shipped this turn** — name the deliverables (commit hash, file path, endpoint, etc) but write it naturally. Avoid robotic "* bullet" skeletons every time. A short paragraph is often better than 5 bullets.
2. **What's still open / what needs doing next** — name the next move + any blockers (in-lane vs operator-gated). Give the operator a real sense of momentum.
3. **General context** (only when useful) — anything the operator should know that doesn't fit the above (e.g. "I noticed the panel API is degraded", "two sibling agents are racing on the same file").

### What to AVOID

- The same skeleton ("Shipped this turn:" / "Operator actions:") every turn. **Vary the structure** based on what you actually did.
- Wall-of-bullets where each bullet is 5 lines of dense prose — that's the format the operator called out. Either tighten each bullet to ONE line, or just write a paragraph.
- Restating context the operator already saw in the live transcript.
- Robot voice. Write like you would in a Slack DM to a teammate.

### When operator-action IS needed

If there's a real operator gate (env var value, LICENSE pick, UAC click, physical action), name it inline with the exact one-liner — don't manufacture a separate "Operator actions:" section if zero items belong there. "Operator actions: none" is also acceptable.

### Tone

Direct. Plainspoken. Honest about what's verified vs hypothesized (per the `speculation-as-empirical-anti-pattern` brain entry). No marketing voice. No hype.

### Length

Typically 3-8 short sentences OR equivalent in bullets. If the work was huge, allow more — but use paragraph breaks, not nested bullets.

---

## Launcher modes

- **Compact** (default; token-efficient): `<MemPreamble> + <Mode intro> + " READ-CONTRACTS: D:\Sinister Sanctum\automations\session-contracts.md"` ~200 chars overhead.
- **Full** (debug): `<MemPreamble> + <Mode intro> + <5 contracts inlined>` ~3500 chars.

Default Compact saves ~3000 tokens per cold-start. Compounds across 14+ daily sessions.

## Modes (BuiltinPhrases keys)

- **rkoj** — RKOJ workbench-only launch (no Claude spawn)
- **overview** — project state + 3-5 master-actionable next moves
- **dev** — top 3-5 feature/fix candidates; pick highest-priority; BEGIN
- **audit** — secrets at risk, stale TODOs, broken tests, push-readiness
- **resume** — RESUME-POINT-DISCIPLINE pickup (CONTRACT 7 surgical context-load)
- **expand** — 7-step deep audit + clean-up + forward-plan + handoff (NO source edits)
- **coaudit** — second-pair-of-eyes on a primary already running (lane-disciplined)
- **auto** — full autonomous-loop scope plan + /loop self-paced cycling
- **smoketest** — discover endpoints + loop test cases + auto-fix server-side findings
- **securityaudit** — surface discovery + probe + auto-fix; escalate P0 auth/keys/signing
- **deploy** — staged deploy walk with canonical-11 reversibility gate
- **push** — secret-scrub + commit + push to GitHub
- **debug** — last-unresolved-failure pickup; cheapest-first
- **explore** — open exploration; 3 surprising findings + follow-ups
- **forge** *(v18 RKOJ-ELENO 2026-05-21)* — jcode-pattern-mining onto Sanctum stack (Ruflo agentdb + Vault + mermaid-rs-renderer + agent-host-routing). Default lane is Sinister Forge (`projects/sinister-forge/`). Prefer Opus 4.7 1M for Forge work per `automations/agent-host-routing.md`.
