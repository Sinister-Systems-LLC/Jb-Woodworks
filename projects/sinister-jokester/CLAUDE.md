# Sinister Jokester — Intake & Triage Lane

> **Author:** RKOJ-ELENO :: 2026-05-26 (charter ratified by operator scope brief, replaces P0 placeholder)
> **Branch convention:** `agent/sinister-jokester/<short-topic>-<utc-date>`
> **Push policy:** Sinister-Sanctum (single-repo per `single-repo-push-policy-2026-05-25`)

## Mission

Operator (verbatim 2026-05-26): *"intake github links, IG videos (audio) via direct input and eventually a telegram bot. where you deep research everything taht i had and cross refereence that will our entire system to see where those will fit in. ... some shit could be bad, not real, or things we should just not add ... deeply review that and test it and then decide if its something we should add that would improve the system. ... i need a entire data base setup for this so we can easily recall things and see what tools we have in the vault. so each time you decide if good i need a complete md file written on it detauiled on what we ocould use this for in the future or if we should add it now. then i need same thing on projects that we should not add or do anything with and a md files on why from your findings."*

Sinister Jokester is the fleet's **intake + triage lane**: every external candidate (GitHub repo, IG audio, future Telegram bot drop) is deep-reviewed, cross-referenced against existing fleet assets, and given a verdict (`ADOPT` / `WATCH` / `REJECT`) backed by a rationale `.md` and a queryable SQLite row.

## In scope

- Intake adapters for GitHub URLs (clone + metadata).
- Intake adapters for IG video URLs → audio extract → transcript (stubbed; activates when `yt-dlp` + `whisper` available).
- Intake adapters for local paths (e.g. `C:\Users\Zonia\Desktop\GitChain-main` drops).
- Direct-input adapters for raw text/file drops.
- Soft re-review path: a candidate already in the DB is re-reviewed lightly (no re-clone) and any material delta is appended to its existing decision .md.
- Cross-reference engine that compares a candidate against `tools/_INDEX.md`, `inventions/`, `projects.json`, and `_shared-memory/knowledge/`.
- Decision engine that emits per-candidate `.md` to `vault/decisions/{adopt|watch|reject}/`.
- SQLite index at `vault/db/intake.sqlite` so any agent can recall the corpus.
- Top-level CLI `python jokester_cli.py {intake|recall|list|stats|reindex}`.
- (P1) Telegram bot listener that drops links into the intake queue.

## Out of scope

- Actually adopting a candidate into the fleet — Jokester emits the ADOPT decision .md; the relevant lane (sanctum / sinister-tools / sinister-os) does the merge.
- Modifying fleet tools/skills/inventions directly. Jokester only writes within `projects/sinister-jokester/`.
- Per-project bugfixes. Out-of-lane drops get routed to the owning lane's inbox.
- **UI / dashboards / web panels of any kind.** Operator hard-canonical 2026-05-26: *"main goal is speed and efficency. all things like UI or shit like that we will do."* — Jokester is CLI + .md + SQLite only. No HTML, no React, no TUI dressing. If a verdict surfaces a candidate that itself benefits a UI lane (e.g. dashboard), peer-notify `sinister-panel` and let them own it.

## Tech stack

- Python 3.11+ (stdlib + a few well-known deps: `requests`, optional `yt-dlp`, optional `openai-whisper`).
- SQLite (stdlib `sqlite3`).
- `gh` CLI for GitHub metadata (already installed on operator workstation).
- Markdown for every persistent decision artifact.

## Project structure

```
projects/sinister-jokester/
├── CLAUDE.md                 # this file
├── jokester_cli.py           # top-level entrypoint
├── intake/
│   ├── __init__.py
│   ├── github.py             # GitHub URL → clone + metadata
│   ├── ig.py                 # IG URL → audio → transcript (stub-aware)
│   └── local.py              # local directory path → metadata (no clone, in-place)
├── review/
│   ├── __init__.py
│   ├── cross_reference.py    # fleet-asset overlap scoring
│   ├── notify_peers.py       # route verdict to peer-lane inboxes
│   ├── decide.py             # orchestrator + verdict + md writer + peer-notify
│   └── templates/
│       ├── adopt.md.tmpl
│       ├── watch.md.tmpl
│       └── reject.md.tmpl
├── db/
│   ├── __init__.py
│   ├── schema.sql            # canonical schema
│   ├── init_db.py            # initialises vault/db/intake.sqlite
│   └── recall.py             # query helpers + CLI subcommands
├── vault/
│   ├── intake/               # raw downloaded artifacts (cloned repos, audio, transcripts)
│   ├── decisions/
│   │   ├── adopt/            # ADOPT verdicts (one .md per candidate)
│   │   ├── watch/            # WATCH verdicts (re-evaluate later)
│   │   └── reject/           # REJECT verdicts (with why)
│   ├── db/
│   │   └── intake.sqlite     # canonical index (gitignored is fine; rebuildable via reindex)
│   ├── SCHEMA.md             # human-readable schema doc
│   └── INDEX.md              # auto-regenerated summary (top of corpus + counts)
└── tests/
    └── smoke_pipeline.sh     # end-to-end smoke
```

## Cold-start (per spawned agent)

1. Read this `CLAUDE.md`.
2. Read `vault/INDEX.md` for current corpus state.
3. Run `python db/init_db.py --ensure` (idempotent).
4. Poll `_shared-memory/inbox/sinister-jokester/` for delegated candidates.
5. If queue empty: re-poll `_shared-memory/operator-utterances.jsonl` for new URLs tagged `intake` / `jokester`.
6. Heartbeat + PROGRESS append + resume-point at end of every meaningful iter.

## Verdict taxonomy

- **ADOPT** — fits an obvious gap or strictly improves an existing fleet asset. Rationale md includes proposed integration path + which lane should pick up.
- **WATCH** — interesting but not actionable now (e.g., pre-release, niche, requires infra we don't have). Rationale md includes re-evaluation triggers.
- **REJECT** — bad/unsafe/non-real/duplicate/abandoned. Rationale md includes the specific failure mode so we don't re-evaluate it.

Every decision md MUST include: source URL, intake timestamp, verdict, fleet-overlap list with paths, 3-bullet rationale, "if revisited" trigger (for WATCH/REJECT).

## Peer-lane notification (operator hard-canonical 2026-05-26)

Operator (verbatim 2026-05-26): *"if you find something we need for memory for example you need to make sure the memory agent gets its hands on and sees what you are trying to tell them."*
Operator (verbatim 2026-05-26): *"or like if i give you debuggers or RE tools they need to go to sinister emui, snap api, tiktok api. etc"*

After every verdict, `review/notify_peers.py` routes the decision to the lane(s) whose capability area the candidate touches. The route table (`PEER_LANE_ROUTES`) is keyword-based and only emits to lanes that exist in `projects.json`. Each notification = a small `.md` dropped in `_shared-memory/inbox/<peer-slug>/<utc>-from-sinister-jokester-<verdict>-<id>.md` containing: verdict, link to the decision .md, why that lane is getting it. No-slop rule: the route table stays LEAN — if a tag doesn't match a real lane's capability, no message is sent.

Routes live for: `sinister-vault` (vault/blockchain/p2p/crypto), `sinister-memory` (memory/embedding/RAG), `sinister-overseer` (orchestration/swarm), `sinister-term` (TUI/terminal), `sinister-panel` (dashboard), `sinister-snap-api` + `sinister-snap-api-quantum` (snap stuff), `sinister-tiktok-api` (tiktok), `sinister-emulator-bundle` (emulator + all RE/debugger tools — frida/ghidra/ida/radare/decompile/disassemble/smali/jadx), `kernel-apk` (kernel/dex/magisk/zygisk), `sinister-quantum` (qiskit/qubit), `eve-compliance` (CCBill/PhotoDNA/CSAM), `sinister-os` (daemon/cron), `sinister-forge` (codegen/template), `sinister-claw` (scraper/crawler), `letstext` (SMS/Twilio).

## Verdict heuristic (auto)

Conservative-by-default. Most candidates land on **WATCH** unless there's a clear peer-lane fit:

| condition                                                                  | verdict   |
|----------------------------------------------------------------------------|-----------|
| intake failed (clone error, missing path, etc.)                            | REJECT    |
| intake stub (deps missing: yt-dlp/whisper)                                 | WATCH     |
| `peer_hits >= 1` AND `overlap_score < 0.65`                                | **ADOPT** |
| `peer_hits >= 1` AND `overlap_score < 0.80`                                | WATCH     |
| `overlap_score >= 0.80`                                                    | WATCH     |
| `peer_hits == 0` AND `overlap_score < 0.20`                                | WATCH     |
| otherwise                                                                  | WATCH     |

`overlap_score` is computed by `review/cross_reference.py` from the top-5 weighted matching fleet assets (`tools/_INDEX.md` ×2.0, project CLAUDE.md ×1.4, inventions ×1.0, brain `_INDEX.md` ×0.3). Sqrt damping + per-file caps keep any single noisy doc from saturating the score. Manual override always wins: `python jokester_cli.py intake <url> --verdict ADOPT --rationale "..."`.

## Milestones

- **P0 (this iter):** intake pipeline + DB + decision writer + CLI all functional end-to-end on a real GitHub URL. Smoke test green. Peer-lane notification wired (operator hard-canonical 2026-05-26: notify the lane that owns the capability).
- **P1:** drain operator's queued GitHub repos (operator hard-canonical: "we have many github repos to start reviewing").
- **P2:** Telegram bot listener (`telegram_bot.py`) that posts links into `vault/intake/queue.jsonl`. CLI only — no UI.

_(UI / dashboard milestone explicitly removed per operator directive 2026-05-26. If browsing the corpus needs to be nicer, that work belongs to `sinister-panel`; Jokester just exposes the SQLite + .md.)_

## Composes with

- `_shared-memory/knowledge/single-repo-push-policy-2026-05-25.md`
- `_shared-memory/knowledge/branch-convention-2026-05-25.md`
- `_shared-memory/knowledge/loop-relentless-pursuit-doctrine-2026-05-25.md`
- `_shared-memory/knowledge/github-first-sourcing-doctrine-2026-05-24.md`
- `_shared-memory/knowledge/no-bullshit-tested-before-claimed-doctrine-2026-05-23.md`
- `_shared-memory/knowledge/sanctum-scope-discipline-2026-05-24.md` (Jokester respects lane boundaries; it ROUTES not MERGES)
- `D:\Sinister Sanctum\CLAUDE.md` (cold-start protocol)

## Loop condition (default)

> "Drain `_shared-memory/inbox/sinister-jokester/` + `vault/intake/queue.jsonl`. For each candidate: intake → cross-reference → verdict → md → DB row → mark drained. Re-poll every iter. End-of-turn writes resume-point + heartbeat + PROGRESS."
