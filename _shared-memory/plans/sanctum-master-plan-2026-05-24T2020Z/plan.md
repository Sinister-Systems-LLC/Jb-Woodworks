<!-- Author: RKOJ-ELENO :: 2026-05-24 -->

# Sanctum Master Plan -- 2026-05-24T20:20Z

**Lane:** Sinister Sanctum (high-level only per scope-discipline canonical)
**Trigger:** Operator 2026-05-24T20:15Z stacked directive:
> *"register the scheduled task for fleet-autostart at logon ... complete everything else in parrallel ... make sure all agents session starts are good and everyone has the correct mcp tools and bots ... in parrallel work on a system where i can drop and instagram video link into or github link, you download the video listen to what its saying and make a move or download github source and review and place it into our archieves or start project with it or update our systems where you see fit with this. make sure this system grows with us and learns from its mistakes and gets better ... create a plan to complete everythin gi said above and everything i have said ... do a complete audit of our memory and compare it to the full audit of rufus, underrstand anything, ubsidan, and most imporatnly JCODE"*

This plan composes all pending Sanctum-scope work into a single source of truth.

---

## 1. Open operator directives consolidated

| # | Source | Directive | Owner | Status |
|---|---|---|---|---|
| D1 | 19:45Z | Docker AutoStart=true + fleet-autostart on bootup | sanctum | SHIPPED (Docker flag + fleet-autostart.ps1 + Startup .bat) |
| D2 | 19:55Z | Spawn-time sibling detection + plan-around | sibling sanctum | SHIPPED by sibling (detect-similar-agents.ps1 wired) |
| D3 | 20:02Z | Memory-push to agents + EVE.exe-ready + grow gradually | sanctum | SHIPPED (gradual-growth doctrine + fleet-update channel) |
| D4 | 20:15Z | Register fleet-autostart logon task | sanctum | PARTIAL (user-level Startup .bat installed; elevated-register helper for full scheduled-task path queued for operator) |
| D5 | 20:15Z | All-agent session-start correctness + MCP tools + bots audit | sanctum + siblings | OPEN (verification matrix below) |
| D6 | 20:15Z | Drop-link ingest system (Instagram video + GitHub link) | sanctum | OPEN -- spec in section 4 |
| D7 | 20:15Z | Complete memory audit comparing Sanctum vs Ruflo + understand-anything + Obsidian + JCODE | sanctum | IN-FLIGHT (4 parallel agents, JCODE returned) |
| D8 | 20:15Z | "Grows with us and learns from its mistakes and gets better" -- continuous improvement on the drop-link system | sanctum | OPEN -- folded into ingest-spec section 4.5 |

---

## 2. Fleet-autostart logon -- detailed state

**User-level path (no admin needed; ALREADY ACTIVE):**
- `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\SinisterFleetAutostart.bat`
- Fires on user logon; runs `fleet-autostart.ps1 -Mode Full -Quiet`
- Inherits user privileges; sufficient for warming bot fleet + sweeps + fleet-update push

**Elevated path (proper scheduled task; OPERATOR-RUN ONCE):**
- `D:\Sinister Sanctum\automations\register-fleet-autostart-task.ps1`
- Run from elevated PowerShell: `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\Sinister Sanctum\automations\register-fleet-autostart-task.ps1"`
- Creates `SinisterFleetAutostart` scheduled task at logon with `RunLevel=Highest`
- Includes `-Unregister` switch for clean rollback

**Why both:** User-level .bat is the baseline (works today, no operator action). Elevated task gives operator Task Scheduler GUI visibility + ability to start manually for testing (`Start-ScheduledTask -TaskName SinisterFleetAutostart`).

---

## 3. All-agent session-start + MCP correctness audit (D5)

Verification matrix for "all agents session starts are good and everyone has the correct mcp tools and bots":

| Surface | Check | How |
|---|---|---|
| Cold-start phrase | Step 0-11 present, no regression | `grep -c "^[0-9]\+\." D:\Sinister\ Sanctum\CLAUDE.md` should show 11 |
| Bypass permissions | `~/.claude/settings.json` has `bypassPermissions: true` | `Get-Content ~/.claude/settings.json | Select-String bypassPermissions` |
| MCP fleet | `~/.claude/.mcp.json` paths valid | per-bot path verify via `Test-Path` on each `cwd` entry |
| Project default modes | All 25 projects have `default_modes` block | per `projects.json` audit (sibling shipped 25/25) |
| Spawn phrase composability | `start-sinister-session.ps1` `Build-Phrase` injects: forge-memory recall + detect-similar-agents + resume-point + modes + loop-condition | grep verification |
| Fleet-autostart | Docker AutoStart=true + Startup .bat present | this plan section 2 |
| Mesh-coord cron | `SinisterMeshCoordSweep` task `State=Ready` | `Get-ScheduledTask -TaskName SinisterMeshCoordSweep` |
| Heartbeat hygiene | <50 active files (post-sweep) | `Get-ChildItem _shared-memory/heartbeats/ -File | Measure-Object` |
| Operator-utterance queue | All `status=new` rows from last 24h have a tag indicating intended lane | jsonl scan |

Sanctum lane will run this audit next iter (after parallel agents finish) and publish results as a fleet-update.

---

## 4. Drop-link ingest system (D6) -- spec

**Operator's words verbatim:** *"a system where i can drop and instagram video link into or github link, you download the video listen to what its saying and make a move or download github source and review and place it into our archieves or start project with it or update our systems where you see fit with this. make sure this system grows with us and learns from its mistakes and gets better"*

### 4.1 Surface

Single CLI + queue file:

```
automations/link-ingest.ps1 -Url <URL> [-Note "context"]
```

OR drop into a watched file:

```
_shared-memory/inbox/link-ingest/queue.jsonl   # operator appends one URL per line
```

Either path lands in the same processing pipeline.

### 4.2 Pipeline

```
URL -> classify -> download -> extract -> analyze -> decide -> act -> log
```

**Per stage:**

| Stage | Component | What it does | Reuse |
|---|---|---|---|
| Classify | `link-classify.py` (NEW, ~50 LOC) | Regex match: instagram.com/* / github.com/* / generic-url | stdlib re |
| Download (Instagram) | `link-download-instagram.py` (NEW) | Stealth-browser-driven, save .mp4 + thumbnail + caption | `bots/stealth-browser/` (existing) |
| Download (GitHub) | `link-download-github.py` (NEW) | `gh repo clone` OR `git clone --depth 50` for source repos; `gh issue view` / `gh pr view` for issue/PR links | `gh` CLI (already installed) |
| Extract (video -> text) | `link-transcribe.py` (NEW, ~80 LOC) | Whisper.cpp local OR Ollama-whisper if available; output .txt + .srt | local Ollama, no API cost |
| Analyze | `link-analyze.py` (NEW, ~100 LOC) | Use Haiku via existing `scribe` bot OR Ruflo `wasm_agent_prompt` for $0 cost: classify topic, extract action items, propose next move (archive / fork into project / update doctrine / add to brain) | reuse scribe |
| Decide + Act | `link-act.ps1` (NEW, ~120 LOC) | Routes by proposed action: archive -> `_shared-memory/external-imports/<slug>/` + brain row; project-start -> `projects/_pending-from-links/<slug>/` + operator queue row; doctrine-update -> append candidate to existing `.md` (operator approves); update-system -> fleet-update push announcing the proposed change | composes with `fleet-update.ps1` + `OPERATOR-ACTION-QUEUE.md` |
| Log | `link-ingest-log.jsonl` (NEW state file) | Append-only history per URL: classification, download path, transcription, analysis, action taken, operator feedback | sentinel-lock pattern |

### 4.3 Storage layout

```
_shared-memory/inbox/link-ingest/
  queue.jsonl                       <- operator drops URLs here OR via CLI
  processed/<UTC>-<slug>/           <- one dir per processed URL
    source.url
    download/                       <- .mp4 / .srt / .txt / git-repo
    analysis.json                   <- structured analysis output
    action.json                     <- decided action + result
    operator-feedback.json (opt)    <- if operator corrects the decision (drives learning)
  link-ingest-log.jsonl             <- audit trail
```

### 4.4 Stage 2: archive vs fork-project decision criteria

| Signal | Action |
|---|---|
| Repo has clear LICENSE + recent commits + topic matches an active project | Add to `_shared-memory/external-imports/CANDIDATES.md` for sibling project lane to consume |
| Repo is a complete app/tool we don't have | New entry in `projects/_pending-from-links/<slug>/` with `_SCAFFOLD-BRIEF.md` for operator to promote |
| Repo is a single function/snippet | Extract to `tools/` with attribution |
| Video describes a new technique we don't use | Brain row in `_shared-memory/knowledge/from-ingest-<slug>-<date>.md` + operator queue row |
| Video describes an existing technique we DO use | Compare against existing brain entry; if drift, propose update; if match, log as confirmation in `improvement-log.jsonl` |

### 4.5 Learning + improvement loop (D8)

Composes with `forever-improve.ps1 -Action Review`:

- Each processed URL emits a `link-ingest-log.jsonl` row.
- Operator-feedback.json (if present) marks `decision_correct: bool` + `correct_action: <enum>`.
- Weekly cron runs `link-ingest-self-audit.ps1`: aggregate per-classifier accuracy, surface mistakes (where operator-feedback != decided), update classify thresholds.
- `forever-improve` checkpoint triggers on every 10 ingests OR every operator correction.
- The system gets better gradually -- no monolithic ML training, just rule + threshold tuning + brain accumulation.

### 4.6 Minimum viable demo

Smoke target for first ship:
1. Operator drops a GitHub URL into queue.jsonl
2. System detects, clones to `processed/<UTC>-<owner>-<repo>/download/`
3. Scribe reads README + LICENSE; emits 1-paragraph summary + recommended action
4. Action lands in `OPERATOR-ACTION-QUEUE.md` with diff-preview ("propose adding to external-imports/CANDIDATES.md")
5. Operator approves -> brain row written; no approve -> entry rots, sweep deletes after N days

**Estimated ship size:** 5-6 small scripts (link-classify, link-download-instagram, link-download-github, link-transcribe, link-analyze, link-act) + 1 brain doctrine + 1 OPERATOR-ACTION-QUEUE landing-zone row. ~500 LOC total. Two-iter ship if done laser-focus.

---

## 5. Memory backbone canonical decision (D7)

In-flight sub-agents (4 parallel Explore): JCODE (returned), Ruflo, understand-anything, Obsidian.

**JCODE findings (received):** Per-session `MemoryGraph` JSON with typed edges (HasTag / RelatesTo / Supersedes / Contradicts), 384-dim ONNX MiniLM embeddings, exponential decay scoring (category half-lives: Correction 365d / Preference 90d / Fact 30d), BFS graph traversal for recall, dedup via signature + set-overlap (180s window), pending-memory queue (120s TTL). Auditable JSON files; in-process for zero latency.

**Open until other 3 agents return:** Ruflo agentdb actual size + wire-status; understand-anything graph format on disk; Obsidian vault pattern fit assessment.

**Decision-pending recommendation (subject to confirmation):** Hybrid approach:
- **Primary:** jcode-style per-session MemoryGraph JSON at `_shared-memory/forge-memory/sessions/<slug>/<UTC>.graph.json` -- replaces current empty forge-memory stub
- **Secondary index:** librarian FAISS for cross-session embedding search (keep existing; add periodic sync from MemoryGraph)
- **Tertiary cache:** Ruflo agentdb_hierarchical-store as the fleet-distributed read-through cache (single backend for multi-agent recall)
- **Retire:** forge-memory CLI stub (replaced by MemoryGraph file format)

Update to OPERATOR-ACTION-QUEUE row 19:48Z when remaining 3 agents return.

---

## 6. Sequence + dependencies

```
NOW (iter ship now):
  [DONE]  fleet-autostart.ps1 + Startup .bat
  [DONE]  SinisterMeshCoordSweep cron
  [DONE]  gradual-growth doctrine + brain index
  [DONE]  CLAUDE.md step 11 composed
  [DONE]  JCODE memory deep-dive
  [DONE]  master plan (this file)

NEXT ITER (auto-fires per loop-mode continuous):
  [..]    Aggregate remaining 3 memory-audit agents
  [..]    Update OPERATOR-ACTION-QUEUE row 19:48Z with full backbone recommendation
  [..]    Run all-agent session-start audit matrix (section 3)
  [..]    Ship `link-classify.ps1` + queue file + log (skeleton; smoke test with one GitHub URL)
  [..]    Brain row: drop-link-ingest-spec-2026-05-24

ITER N+2:
  [..]    Ship `link-download-github.py` (gh clone wrapper)
  [..]    Ship `link-download-instagram.py` (stealth-browser flow)
  [..]    Ship `link-transcribe.py` (whisper.cpp wrap)
  [..]    Ship `link-analyze.py` (scribe wrap)
  [..]    Ship `link-act.ps1` (router)
  [..]    Smoke E2E with one Instagram + one GitHub URL
  [..]    Wire `link-ingest-self-audit.ps1` to weekly cron

ITER N+3:
  [..]    Operator memory-backbone decision -> migrate brain markdown into chosen backbone (gated)
  [..]    Compaction: cold-start step 11 NOT exceeded; brain rows pruned per quality signals
```

---

## 7. Quality gates (no-bullshit + prune-as-add compliance)

- Each ship in this plan: smoke-tested before claimed-shipped.
- Each new file: prune one stale/duplicate counterpart (logged in PROGRESS row).
- End-of-iter: forever-improve Review on the day's work.
- No iter ends with queueable work remaining (loop-mode continuous canonical).
- Brain rows >150 OR cold-start >11 steps OR script >1500 LOC -> consolidate not expand.

---

## 8. Composes with

- `gradual-growth-memory-push-eve-exe-ready-2026-05-24` (R1/R2/R3 of this plan's execution discipline)
- `mesh-coordination-and-resource-lifecycle-2026-05-24` (lock + refcount foundations)
- `sanctum-scope-discipline-2026-05-24` (this plan stays in Sanctum scope -- high-level only)
- `loop-mode-continuous-iteration-2026-05-24` (continuous iter cadence)
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (every "DONE" above has same-turn smoke evidence)
- Existing `forever-improve-review-doctrine-2026-05-24` (drives D8 learning loop)
- Existing `fleet-update-channel-doctrine-2026-05-24` (D1/D3/D4 distribution path)
