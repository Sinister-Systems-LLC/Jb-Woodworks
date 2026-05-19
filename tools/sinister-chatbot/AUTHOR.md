> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

Author: Sinister Sanctum (master Claude agent, 2026-05-19, master/orchestration lane).

This folder is the **second Sanctum invention** — Sinister Chatbot (Eve
Powered). It absorbs the Kameleo chatbot from the Sinister Panel
(`C:\Users\Zonia\Desktop\Sinister-Panel\Andrew Panel\Sinister Panel\panel\backend\src\`)
into a clean Sanctum copy, swaps the LLM client from OpenRouter to the
Anthropic SDK, and ports the Eve observation derivation rules from
`dashboard-skeleton/components/eve/eve-observations-card.tsx` into a
server-side primitive (`src/services/eveObservations.ts`).

The Panel agent owns the original-canonical OperatorRunning version of
the chatbot. Diffs between Sanctum and Panel should remain limited to:

- the prepended `// Author: …` headers (cosmetic)
- `src/services/llmClient.ts` (substantive rewrite)
- `src/services/eveObservations.ts` (new)
- the seeded `TODO(eve)` comment in `src/services/chatEngine.ts`
