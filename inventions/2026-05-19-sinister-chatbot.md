> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Sinister Chatbot (Eve Powered) — Snapchat / chat platform conversational AI agent (second Sanctum invention)

**Captured:** 2026-05-19
**Status:** building
**Origin:** Operator directive (2026-05-19): "Absorb the Kameleo chatbot from the Sinister Panel into Sanctum as 'Sinister Chatbot (Eve Powered)'. Create COPIES in Sanctum (since panel agent owns the originals, and the operator wants Sanctum to have its own clean version). Mark this as the SECOND Sanctum invention (after Sinister Crawler). The llmClient.ts REWRITE is the only file that should differ from panel substantively — swap OpenRouter for Anthropic SDK. Port the EVE observation derivation rules from dashboard-skeleton/components/eve/eve-observations-card.tsx into a server-side primitive."

## Idea

> Absorb the Kameleo chatbot from the Sinister Panel into Sanctum as "Sinister Chatbot (Eve Powered)". Swap the LLM client from OpenRouter to the Anthropic SDK. Port the Eve observation derivation logic from the dashboard-skeleton React card into a server-side function so the AI tone shifts in lockstep with the operator's inbox UI.

A clean, Sanctum-owned copy of the Panel's chatbot subsystem — same Kameleo
antidetect browser + Playwright Snapchat automation + per-thread phase &
interest engine, but Claude-first (Anthropic SDK) and wired to surface
Eve's commercial observations ("Top spender", "Premium tier", "Dormant 7d",
"Birthday in 3d") directly into the system prompt that drives every reply.

## Why

The Panel grew the chatbot to production maturity but its LLM lane is
OpenRouter-flavored and its prompt has no awareness of fan commercial
state. Two problems with that:

1. **LLM vendor lock-in.** Sanctum is Claude-first by mandate. Every new
   Sanctum invention should use the Anthropic SDK directly so prompt
   caching, extended thinking, the citations API, and Claude-specific
   features are accessible without an OpenRouter middleman.
2. **No Eve signal in the prompt.** The dashboard-skeleton already shows
   the operator a beautiful "EVE THINKS…" card with observations like
   "Top spender · $1,240 lifetime" — but the AI generating the reply has
   no idea this fan is a top spender. The model talks to a $5 fan and a
   $5,000 fan identically. Wiring Eve's derived observations into the
   system prompt closes that loop: the AI's flirt cadence, urgency, and
   tone now respect what the operator already knows.

It's also the **second Sanctum invention** — proof that the
inventions/ folder isn't just for greenfield ideas (like Sinister Crawler,
the first invention) but is also the natural home for absorbing a mature
Panel subsystem and re-shaping it on Sanctum's terms.

## Sketch

```
Sinister Panel (CANONICAL, OperatorRunning)
  panel/backend/src/
    routes/chatbot.ts
    services/{chatEngine, kameleo, snapActions, runner, llmClient}.ts
    services/llmClient.ts  --[OpenRouter HTTP]--> openrouter.ai
                                  |
                                  | ABSORB (verbatim copy + // Author: header)
                                  v
Sinister Sanctum :: Sinister Chatbot (Eve Powered)
  D:\Sinister Sanctum\tools\sinister-chatbot\
    src/
      index.ts                      <-- new: Express boot on PORT 5099
      routes/chatbot.ts             <-- COPY
      services/
        chatEngine.ts               <-- COPY + TODO(eve) comment
        kameleo.ts                  <-- COPY
        snapActions.ts              <-- COPY
        runner.ts                   <-- COPY
        llmClient.ts                <-- REWRITE: Anthropic SDK
        eveObservations.ts          <-- NEW: port of eve-observations-card.tsx
    prisma/schema.prisma            <-- minimal local stub
    assets/eve-icon.svg             <-- extracted i-eve glyph
    package.json + tsconfig.json + .env.example
```

Runtime path (one fan reply):

1. Snap polling tick in `runner.ts` picks an account.
2. `snapActions.ts::detectAndRespondToUnreads` opens the unread chat in
   Kameleo via Playwright, reads the fan's last message + history.
3. `chatEngine.ts::runChatEngine` loads the ChatThread + last 30 messages,
   adjusts interest level, picks next phase, builds the system prompt.
4. *(Pending Eve wiring)* `eveObservations.ts::deriveEveObservations(fan)`
   produces the top-3 observations; `renderObservationsForPrompt()`
   formats them into an "EVE THINKS" block that chatEngine folds into the
   system prompt.
5. `llmClient.ts::llmComplete` (now using `@anthropic-ai/sdk`) calls
   Claude — default `claude-haiku-4-5-20251001`, per-group override via
   the existing `group.llmModel` field.
6. Response parsed → enforced-style → optional one-typo-per-convo →
   typed back into the open Snap chat → DB updated → chat closed.

## Status

- [x] idea captured
- [x] panel sources audited; only `llmClient.ts` requires substantive rewrite
- [x] folder scaffolded under `D:\Sinister Sanctum\tools\sinister-chatbot\`
- [x] all panel files COPIED verbatim with `// Author: …` headers
- [x] `llmClient.ts` rewritten to Anthropic SDK (default
       `claude-haiku-4-5-20251001`)
- [x] `eveObservations.ts` ported from the React card
- [x] `chatEngine.ts` seeded with `TODO(eve)` comment for wiring
- [ ] chatEngine actually calls `deriveEveObservations()` (deferred)
- [ ] missing dependencies stubbed/ported (`lib/db.ts`, `lib/logger.ts`,
       `services/snapLogin.ts`, `services/rateLimit.ts`) — see INTEGRATION.md
- [ ] operator runs `npm install` + smoke test
- [ ] shipped

## Linked-to

- Tool folder: `D:\Sinister Sanctum\tools\sinister-chatbot\`
- Tool README: `D:\Sinister Sanctum\tools\sinister-chatbot\README.md`
- Integration notes: `D:\Sinister Sanctum\tools\sinister-chatbot\INTEGRATION.md`
- Desktop bat: `C:\Users\Zonia\Desktop\Sanctum-Chatbot-Start.bat`
- Tool row: `D:\Sinister Sanctum\tools\_INDEX.md`
- Skill rows: `D:\Sinister Sanctum\skills\_INDEX.md` (`eveObservations`, `kameleo`)
- Panel canonical source: `C:\Users\Zonia\Desktop\Sinister-Panel\Andrew Panel\Sinister Panel\panel\backend\src\`
- Eve UI source-of-truth: `C:\Users\Zonia\Desktop\dashboard-skeleton\components\eve\eve-observations-card.tsx`
- First Sanctum invention (precedent): `D:\Sinister Sanctum\inventions\2026-05-19-sinister-crawler.md`

## Notes

- Lane discipline: master/orchestration agent created this folder; the
  Panel agent still owns its originals. Edits to either lane do not
  cross-contaminate. Diffs between Panel and Sanctum are intentionally
  minimal so the two stay grep-comparable.
- The Sanctum copy has known TS compile gaps (missing `lib/db.ts`,
  `lib/logger.ts`, `services/snapLogin.ts`, `services/rateLimit.ts`).
  These are listed in INTEGRATION.md and are deliberately deferred so
  this PR has a clean review surface; absorbing those modules is a
  follow-up Sanctum task.
- Default model `claude-haiku-4-5-20251001` chosen for per-fan-reply
  economics. Premium personas can flip to Sonnet via `group.llmModel`
  per-group override — no schema change needed.
