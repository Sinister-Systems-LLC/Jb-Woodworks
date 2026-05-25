<!-- Author: RKOJ-ELENO :: 2026-05-24 -->

<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 30
-->
# Drop-link ingest system spec + Phase 1 ship

**Created:** 2026-05-24 20:28Z
**Authority:** Operator hard-canonical 2026-05-24T20:15Z (verbatim):
> *"a system where i can drop and instagram video link into or github link, you download the video listen to what its saying and make a move or download github source and review and place it into our archieves or start project with it or update our systems where you see fit with this. make sure this system grows with us and learns from its mistakes and gets better"*

---

## Pipeline (6 stages)

```
URL --> classify --> download --> extract --> analyze --> decide --> act
                                                                       |
                                                                       +--> learn (operator feedback drives improvement)
```

## Phase 1 SHIPPED (this iter)

**Surface:** `automations/link-ingest.ps1`

**Actions:**
- `-Action Add -Url <URL> [-Note "..."]` — classify + queue
- `-Action List [-Status pending|processed|all]` — view queue
- `-Action Process [-Limit N]` — DRY-RUN preview (Phase 2 wires real download)
- `-Action Status` — counters

**Classifiers (regex on URL):**
- `instagram-video` — `instagram.com/(p|reel|reels|tv)/...`
- `github-repo` — `github.com/<owner>/<repo>`
- `github-issue` — `github.com/<o>/<r>/issues/<N>`
- `github-pr` — `github.com/<o>/<r>/pull/<N>`
- `github-file` — `github.com/<o>/<r>/blob/...`
- `github-other` — github but no specific pattern
- `youtube-video` — `youtube.com` / `youtu.be`
- `generic-url` — anything else valid
- `invalid` — empty / no scheme / no host

**Storage:**
```
_shared-memory/inbox/link-ingest/
  queue.jsonl                       # operator drops URLs here OR via CLI Add
  processed/<UTC>-<slug>/           # one dir per processed URL (Phase 2+)
    source.url
    download/
    analysis.json
    action.json
    operator-feedback.json
  link-ingest-log.jsonl             # append-only event log
  .queue.lock                       # sentinel-file lock (10s stale-reclaim)
```

**Smoke 8/8 PASS** (2026-05-24T20:26Z): Status empty / Add github-repo / Add instagram-video / Add youtube-video / Add invalid (rejected with clear reason) / Add empty (param-required) / List pending (3 rows) / Process DRY-RUN (correct per-kind plan).

## Phase 2 spec (next iter)

Per-kind download:
- `github-repo` → `gh repo clone <url> processed/<id>/download/` (depth 50)
- `github-issue|pr|file` → `gh api` fetch + save JSON/markdown
- `instagram-video` → stealth-browser session + yt-dlp/instaloader → `*.mp4` + `caption.txt`
- `youtube-video` → yt-dlp + whisper.cpp transcribe → `*.mp4` + `transcript.srt`
- `generic-url` → stealth-browser fetch + readability extract → `page.html` + `text.txt`

## Phase 3 spec — analyze + decide + act

`link-analyze.ps1` (or .py): route through `scribe` bot (Haiku, ~$0.02/call) OR `mcp__ruflo__wasm_agent_prompt` (Haiku-on-WASM, $0) to classify content → propose action.

Decision matrix:

| Signal | Proposed Action |
|---|---|
| Repo has LICENSE + recent commits + topic matches active project | Add to `_shared-memory/external-imports/CANDIDATES.md` |
| Repo is complete app/tool we lack | New `projects/_pending-from-links/<slug>/` with `_SCAFFOLD-BRIEF.md` |
| Repo is single function/snippet | Extract to `tools/` with attribution |
| Video describes new technique | Brain row `_shared-memory/knowledge/from-ingest-<slug>-<date>.md` + operator queue row |
| Video matches existing brain row | Compare; if drift propose update; if match log as confirmation in `improvement-log.jsonl` |

Action surface: every decision lands as a row in `OPERATOR-ACTION-QUEUE.md` with diff-preview. Operator approves → action executes; no approve → row rots, swept after N days.

## Phase 4 spec — learn-from-mistakes loop (D8 of master plan)

`link-ingest-self-audit.ps1` weekly cron:
- Aggregate `link-ingest-log.jsonl` rows per classifier kind
- Cross-reference with `operator-feedback.json` (if present per processed entry)
- Compute per-kind precision (correct decision / total decisions)
- When precision < 0.7 for a kind, surface to OPERATOR-ACTION-QUEUE for rule/threshold tuning
- Compose with `forever-improve.ps1 -Action Review` on every 10 ingests OR every operator correction

No ML training; just rule + threshold tuning + brain accumulation. Gradual + auditable per operator R3.

## Anti-patterns

1. Operator drops URL → system auto-executes without queue-row review. Always queue + ack first.
2. Phase 2 downloads without bandwidth/disk guard. Add per-kind size caps (instagram-video: 100 MB; github-repo: 500 MB; abort + queue-row "size-cap-hit" otherwise).
3. Storing transcribed audio without consent gate (privacy). For instagram-video, default to caption-only; full transcribe gated on operator opt-in.
4. Brain row spam — one brain row per ingest defeats the "growth" goal. Phase 3 only writes brain rows for novel-technique kind; archive others.

## Composes with

- `gradual-growth-memory-push-eve-exe-ready-2026-05-24` (R1 push memory updates; R3 grow gradually never stop)
- `sanctum-scope-discipline-2026-05-24` (this stays Sanctum-level; per-project agents consume from `_pending-from-links/<slug>/`)
- `fleet-update-channel-doctrine-2026-05-24` (Phase 1 announce row pushed same turn)
- `forever-improve-review-doctrine-2026-05-24` (Phase 4 learning loop)
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (Phase 1 claim = smoke 8/8 PASS in same turn)
- Master plan: `_shared-memory/plans/sanctum-master-plan-2026-05-24T2020Z/plan.md` section 4

## Verification

```powershell
# Operator workflow
powershell -File automations/link-ingest.ps1 -Action Add -Url "https://github.com/openai/whisper" -Note "look at this"
powershell -File automations/link-ingest.ps1 -Action List
powershell -File automations/link-ingest.ps1 -Action Process -Limit 1   # Phase 1: DRY-RUN only

# Phase 1 smoke (re-runnable)
powershell -File automations/link-ingest.ps1 -Action Status
```
