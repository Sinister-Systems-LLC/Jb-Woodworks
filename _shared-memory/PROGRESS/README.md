# PROGRESS/ — append-only milestone log per agent

Every parallel Claude session writes major milestones here. The operator (and other agents) can see what's being worked on without having to ask any single session.

## How it works

One file per agent, named **after the `SINISTER_AGENT_NAME`** the launcher set for that session. Examples:

```
PROGRESS/
├── Sinister Sanctum.md      # master / orchestration
├── Sinister Snap API.md     # snap-emu agent
├── Sinister TikTok API.md   # tiktok-emu agent
├── Sinister Panel.md        # panel agent
└── Sinister Kernel APK.md   # kernel-apk agent
```

Each entry is one section:

```markdown
## 2026-05-19 14:32 — started: SS03 pure-API hypothesis #4
Auditing libclient.so JNI surface for grpc=16 unhandled status. Looking at GetTokens path.

## 2026-05-19 13:55 — shipped: 5sim adapter into snap-emu signing pipeline
Added `signing/5sim.py` + tests. All 14 unit tests pass. Ready for operator OK.

## 2026-05-19 13:10 — blocked: panel agent on auth route
Asking panel agent via inbox to clarify role middleware. Waiting on reply.
```

Most-recent at top. Append-only — never delete or rewrite old entries.

## How agents write here

Every spawned Claude session reads `D:\Sinister Sanctum\_shared-memory\DIRECTIVES.md` on cold-start, which tells them:

> Log major milestones (started/shipped/blocked) to `D:\Sinister Sanctum\_shared-memory\PROGRESS\<SINISTER_AGENT_NAME>.md`. One section per milestone. Most-recent at top. Operator sees these in the Sanctum Console.

Agents append directly OR call:

```
POST http://127.0.0.1:5077/api/progress/append
Content-Type: application/json
{ "agent": "Sinister Snap API", "status": "shipped", "title": "...", "body": "..." }
```

## How the operator reads here

- **Sanctum Console UI** — bottom of the page shows the live aggregated progress feed across all agents (refreshes every 30 s).
- **Manual** — open any `PROGRESS/<agent>.md` in a text editor.
- **One-click append** — `C:\Users\Zonia\Desktop\Log-Progress.bat` prompts for agent + status + title + body.

## Status keywords (free-form, but these render with icons in the UI)

- `started`   → working on it now
- `shipped`   → done; merged/landed
- `blocked`   → can't proceed; needs operator or another agent
- `paused`    → on hold
- `note`      → general observation, no state change
- `failed`    → tried and didn't work; documenting before moving on

## TL;DR

- **How we won:** One folder, one file per agent, append-only. Console UI aggregates. Operator never has to ask "what are you working on?"
- **What you need to do:** When an agent makes meaningful progress, it appends here. Operator opens Sanctum Console to see the feed.
