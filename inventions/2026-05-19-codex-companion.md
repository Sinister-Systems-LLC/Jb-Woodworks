> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Codex Companion — OpenAI peer-review skill that runs alongside Claude agents (third Sanctum invention)

**Captured:** 2026-05-19
**Status:** shipped
**Origin:** Operator directive (2026-05-19): "build in to the agents section a way we can use that codex skill that works alongside claude so they can keep each other in checks. Skills we build, review or look into, tools, inventions all of that update memory for all of this."

## Idea

> A thin skill that lets any Claude agent in the Sanctum hand a code blob /
> diff / proposed change to an OpenAI Codex-grade model (gpt-4o-mini / gpt-4o
> / o1-mini), then receive structured feedback —
> `{verdict: pass|warn|fail, findings:[{severity,area,body}], summary}` — so
> Claude and Codex can cross-check each other on every non-trivial push.

The Codex Companion is the peer-review counterweight to a fleet of Claude
agents shipping code. When one Claude writes a non-trivial change, another
agent (or the Sanctum Console) asks Codex "is this actually right?" before
it lands. Every review is logged append-only to
`_shared-memory/codex-reviews/<UTC-iso>-<sha1>.json` for audit.

## Why

Single-model review has known blind spots:

1. **Same-family bias.** Two Claude agents reviewing each other's work share
   training-data biases and prompt-style preferences. They tend to converge
   on "looks fine" for code that a *different* model family (OpenAI / o1)
   might flag immediately.
2. **Self-review weakness.** A Claude agent reviewing code it just wrote (or
   delegated to a subagent) is biased toward "ship it." The proposed code is
   in-context; the path of least resistance is to approve.
3. **Auth / crypto / payment landmines.** These categories of bug are exactly
   where blind spots matter most — and exactly where a second model family
   pays for itself in one catch.
4. **Operator audit trail.** Without persisted reviews, the operator has no
   way to ask "what did the second model think of this change?" after the
   fact. The codex-reviews log fixes that — every review is on disk forever,
   queryable by sha1 of the reviewed content.

Three depth tiers map cost-to-stakes:

- `quick` (gpt-4o-mini, 30s) — lint sweep, < 50 LOC, cheap.
- `standard` (gpt-4o, 60s) — normal feature PR, default.
- `deep` (o1-mini, 180s) — auth/crypto/payment, architectural, > 500 LOC.

## Sketch

```
Any Claude agent in the Sanctum
        |
        | (HTTP via Sanctum Console)            (direct import in Python lane)
        |                                                |
        v                                                v
POST /api/codex/review          <----lazy-import---->  tools/codex-companion/codex.py
   |                                                     |
   +----- {content, context, language, depth} ---------->+
                                                         |
                                                         v
                                       OpenAI ChatCompletions (system prompt:
                                       "You are Codex, return strict JSON only:
                                        {verdict, findings, summary}")
                                                         |
                                          (validate shape; retry once if bad)
                                                         |
                                                         v
                                       Persist to:
                                       _shared-memory/codex-reviews/
                                         <UTC-iso>-<sha1>.json
                                                         |
                                                         v
                                       Return verdict dict to caller
```

Three response surfaces:

- `POST /api/codex/review` — request a review.
- `GET  /api/codex/reviews?limit=N` — list recent reviews.
- `GET  /api/codex/review/{id}` — read one in full.

Plus a CLI (`python codex.py --review <file> --depth deep`) and a desktop
one-click `Codex-Review-Test.bat` for paste-and-go operator use.

## Status

- [x] idea captured
- [x] design sketched
- [x] implementation started
- [x] codex.py shipped (review() + CLI + graceful no-API-key)
- [x] requirements.txt shipped
- [x] README.md + AUTHOR.md shipped
- [x] Sanctum Console endpoints wired (`/api/codex/review`, `/api/codex/reviews`, `/api/codex/review/{id}`)
- [x] Desktop one-click bat shipped (`Codex-Review-Test.bat`)
- [x] Knowledge topic shipped (`_shared-memory/knowledge/codex-companion-usage.md`)
- [x] DIRECTIVES.md standing rule added
- [x] tools/_INDEX.md + skills/_INDEX.md rows added
- [x] shipped

## Linked-to

- Tool folder: `D:\Sinister Sanctum\tools\codex-companion\`
- Tool card: `D:\Sinister Sanctum\tools\codex-companion\README.md`
- Main module: `D:\Sinister Sanctum\tools\codex-companion\codex.py`
- Reviews log dir: `D:\Sinister Sanctum\_shared-memory\codex-reviews\`
- Knowledge topic: `D:\Sinister Sanctum\_shared-memory\knowledge\codex-companion-usage.md`
- Standing rule (DIRECTIVES): `D:\Sinister Sanctum\_shared-memory\DIRECTIVES.md` (entry dated 2026-05-19)
- Tool row: `D:\Sinister Sanctum\tools\_INDEX.md`
- Skill row: `D:\Sinister Sanctum\skills\_INDEX.md` (`codex-review`)
- Desktop bat: `C:\Users\Zonia\Desktop\Codex-Review-Test.bat`
- First Sanctum invention: `D:\Sinister Sanctum\inventions\2026-05-19-sinister-crawler.md`
- Second Sanctum invention: `D:\Sinister Sanctum\inventions\2026-05-19-sinister-chatbot.md`

## Notes

- **Lane discipline:** master/orchestration agent built this. Any Claude
  session in the fleet can call it. The skill itself is stateless — every
  review is independent and logged separately.
- **OpenAI SDK is NOT installed** by the tool. Operator runs
  `pip install -r tools/codex-companion/requirements.txt` (or just
  `pip install openai>=1.20.0`) once for their global Sanctum Python.
- **Graceful no-key behavior:** the tool never raises on missing
  `OPENAI_API_KEY` or missing SDK — it returns `{ok: false, error: ...}` so
  the caller decides whether to skip review or block.
- **JSON-only contract:** the system prompt mandates strict JSON. If the model
  ignores instructions, `_parse_response` strips code fences and retries
  once with a "REMINDER: return STRICT JSON only" suffix.
- **Model selection rationale:** `gpt-4o-mini` for cost-efficient quick checks;
  `gpt-4o` as the balanced default; `o1-mini` for deep reasoning on high-stakes
  changes (auth/crypto/payment, architectural). The o1 family branch passes
  `max_completion_tokens` (not `max_tokens`) and omits `temperature` —
  `_call_openai` handles both API contracts.
- **Third Sanctum invention.** First was Sinister Crawler (the Telegram bot
  frontend). Second was Sinister Chatbot (the Eve-powered Snap chat lane).
  Third is the Codex Companion — proof that the Sanctum is now meta enough
  to invent its own quality-control machinery.
