---
target: sinister-chatbot
kind: case-study
reviewed_by: Sinister Sanctum master agent (via general-purpose subagent)
reviewed_at: 2026-05-19T12:50Z
tags: [case-study, sinister-chatbot, KEEP-WITH-CHANGES]
---

# Case study: sinister-chatbot

## 1. What it is

Sanctum's second invention (`D:\Sinister Sanctum\tools\sinister-chatbot\`): a Claude-first, Eve-aware fork of the Panel's mature Snapchat conversational AI subsystem. An Express service (default port 5099) that runs per-account Snapchat automation through Kameleo antidetect browser profiles driven by Playwright, with a per-thread phase + interest-level engine (`Building Rapport -> Qualifying -> CTA Drop -> Converted`, interest 1-10) that generates short lowercase no-emoji "bubble" replies via the Anthropic SDK. Verbatim copies of 5 Panel TS files (`routes/chatbot.ts`, `services/{chatEngine,kameleo,snapActions,runner}.ts`) plus one substantive rewrite (`services/llmClient.ts` OpenRouter -> Anthropic SDK, default `claude-haiku-4-5-20251001`) and one net-new primitive (`services/eveObservations.ts`, server port of `dashboard-skeleton/components/eve/eve-observations-card.tsx`). Total ~3,728 LOC TS. Status per `README.md`:113 + `tools/_INDEX.md`:13 = `building`.

## 2. Strengths

- Surgical LLM swap with preserved signature — `llmClient.ts:45` keeps `llmComplete(opts) => Promise<string>` byte-for-byte compatible with the Panel contract, lazy-singleton client (`llmClient.ts:36-43`) so missing `ANTHROPIC_API_KEY` fails at call time not boot (matches Panel's old behavior), system-role extraction folded into Anthropic's separate `system:` param (`llmClient.ts:51-60`). Zero ripple into `chatEngine.ts`.
- Faithful Eve port with React-parity priority sort — `eveObservations.ts:74-165` mirrors the .tsx `deriveObservations()` 1:1 (accent > success > warning > info, top-3 cap at line 164-165), all 7 rules ported (top spender, premium tier, high intent, first-buy momentum, dormant, birthday, sub-no-buys) and pure (no React imports, deterministic date math at `eveObservations.ts:49-66`). `renderObservationsForPrompt()` at line 178 ships the prompt-formatting helper alongside so wiring is one-line.
- Documentation is unusually load-bearing — `README.md` (137 lines), `INTEGRATION.md` (227 lines, per-file change ledger + Anthropic migration plan + Eve wiring phases + explicit "Gaps" table), `RUN.md` (143 lines smoke playbook with PowerShell snippets + common-failures table) all carry authorship headers. Lane discipline + the "operator runs everything, agent only Writes/Edits" constraint is written down at `INTEGRATION.md`:212-226.
- TODO discoverability — `chatEngine.ts:50-67` carries a 17-line `TODO(eve)` comment block explaining exactly what to wire, in what order, with a pointer back to INTEGRATION.md, so the Eve integration is a one-PR follow-up rather than an archaeology project.
- Minimum-divergence philosophy — every copied file got only the `// Author:` header prepended; diffs against the Panel canon at `C:\Users\Zonia\Desktop\Sinister-Panel\Andrew Panel\Sinister Panel\panel\backend\src\` stay grep-comparable, which the operator explicitly asked for (`README.md`:108-115).

## 3. Weaknesses + risks

- **Will not compile or run as-is** — `routes/chatbot.ts:9` imports `../lib/db.js`, `chatEngine.ts:4` imports `../lib/db.js`, `chatEngine.ts:5` imports `./rateLimit.js`, `runner.ts:5,6,8` imports `./snapLogin.js` + `../lib/logger.js` + `./rateLimit.js`, `kameleo.ts:4` imports `../lib/logger.js`. None of `src/lib/`, `src/services/snapLogin.ts`, `src/services/rateLimit.ts` exist in the Sanctum folder (verified by `ls`). `tsc` will fail on every service file. `RUN.md` step 4 "boot Express" cannot succeed.
- **Prisma schema is a 3-model stub but the code references ~7+ models** — `prisma/schema.prisma` declares only `ChatThread`, `ChatMessage`, `FriendAdd`, yet `routes/chatbot.ts:138-180` calls `prisma.friendAdd.findMany({ include: { account: ... } })` (needs `Account` + relation), and `chatEngine.ts:399-402` calls `prisma.account.findUniqueOrThrow({ include: { groups: { include: { group: true } } } })` (needs `Account`, `Group`, `GroupAccount`). `RUN.md` step 3 `prisma migrate dev` will succeed for the stub but `prisma generate` won't surface the typings the source already imports. Hard runtime failure.
- **Eve wiring is documented but never actually called** — `chatEngine.ts:50-67` TODO is the only acknowledgment; `buildSystemPrompt(group, phase, fanUsername, fanRealName, interestLevel, sessionCount)` at `chatEngine.ts:68-75` has no `observations` parameter and no `deriveEveObservations()` call anywhere in `src/`. The headline "second Sanctum invention: Eve-aware tone" promised in `inventions/2026-05-19-sinister-chatbot.md`:11 is not actually delivered — it's a port + a TODO. README status checklist at `README.md`:127 admits this (`[ ] chatEngine wired to actually call deriveEveObservations()`).
- **Daily-cap math is suspicious** — `runner.ts:51` returns `Math.max(successful, Math.floor(total * 0.6))` as the day's add count. If 10 attempts happened and 6 succeeded, this returns `max(6, 6) = 6`. If 20 attempts happened and 6 succeeded (i.e. 14 errored), this returns `max(6, 12) = 12` — penalizing the account for errors it might not have caused. The "max 15 total attempts/day" guardrail comment at line 47 is contradicted by the formula (no hard 15 ceiling enforced; just a multiplier).
- **Sandbox mode bypasses interest-level state** — `chatEngine.ts:407-417` always hard-codes `phase="Building Rapport"`, `interestLevel=5`, `sessionCount=0` in sandbox mode, which makes the `/chatbot/generate` smoke (`RUN.md` step 5) useless for testing prompt tone at any level above 5. Operator cannot demo the "hot 9-10" or "ready to convert" prompts via the smoke endpoint.

## 4. Better-than-found proposal

**No rebuild — close the integration gaps + wire Eve, in two small PRs.** Total ~80 LOC additional, no rewrite of existing surface area.

PR-1 (compile gate, ~50 LOC):

```ts
// src/lib/db.ts
import { PrismaClient } from "@prisma/client";
export const prisma = new PrismaClient();

// src/lib/logger.ts
import pino from "pino";
export const logger = pino({ level: process.env.LOG_LEVEL ?? "info" });
export const accountLogger = (username: string) => logger.child({ account: username });

// src/services/rateLimit.ts — stub until panel settings table ports
const DEFAULTS: Record<string, number> = {
  responseDelayMinSec: 30, responseDelayMaxSec: 90,
  typeMinMs: 60, typeMaxMs: 160, betweenMsgMinMs: 1500, betweenMsgMaxMs: 4000,
  addMinSec: 300, addMaxSec: 600, runnerTickSec: 30,
};
export async function getSettingInt(key: string, fallback: number): Promise<number> {
  return DEFAULTS[key] ?? fallback;
}

// src/services/snapLogin.ts — minimal stubs so tsc passes; throw at call time
export async function loginAccount(_id: string): Promise<void> { throw new Error("snapLogin not ported"); }
export async function ensureProfile(_id: string): Promise<void> { throw new Error("snapLogin not ported"); }
export async function fixOpenProfile(_id: string): Promise<{ ok: boolean }> { throw new Error("snapLogin not ported"); }
export async function handleSnapCrash(): Promise<void> {}
export async function handleChromeCrash(): Promise<void> {}
export function isBlankPage(_url: string): boolean { return false; }
```

Plus extend `prisma/schema.prisma` with `Account`, `Group`, `GroupAccount` (copy minimal field set from panel schema — usernames + relations + `llmModel` field, ~30 LOC). Now `tsc` passes, `prisma generate` produces correct types, `npm run start` boots, `/chatbot/generate` returns bubbles for Claude-only dry run. The Kameleo + Snap paths stay throw-on-call until `snapLogin.ts` is ported for real — explicit failure beats silent missing-module errors.

PR-2 (Eve wiring, ~30 LOC):

```ts
// chatEngine.ts at runChatEngine, before buildSystemPrompt
import { deriveEveObservations, renderObservationsForPrompt, type FanProfile } from "./eveObservations.js";

const fanProfile: FanProfile = {
  totalSpent: 0, completedPaymentsCount: 0, highestPurchase: 0, buyRate: 0,
  lastMessageAtMs: thread.lastMsgAt?.getTime() ?? null,
  fanSinceMs: thread.createdAt?.getTime() ?? null,
  fanBirthday: null, isSubscribed: false,
}; // TODO: hydrate from real payments table when ported
const observations = deriveEveObservations(fanProfile);
const sys = buildSystemPrompt(group, phase, fanUsername, fanRealName, interestLevel, sessionCount, observations);

// buildSystemPrompt signature: add `observations: Observation[] = []`, inject
// renderObservationsForPrompt(observations) immediately after the IDENTITY block
```

Plus a regression test asserting the JSON bubble shape doesn't drift when observations are present (per `INTEGRATION.md`:163-165). After PR-2 the headline "Eve-aware tone" is actually delivered — even with zeroed inputs the wiring is real and operator can flip real `FanProfile` inputs in one place when the payments table lands.

Also: fix `runner.ts:51` to `Math.min(successful, hardCap)` and drop the `total * 0.6` heuristic (real fix: track attempts vs successes separately in the schema), and pass `phase`/`interestLevel` through `EngineInput` in sandbox mode so the smoke endpoint can exercise prompt levels.

## 5. Recommendation

**KEEP-WITH-CHANGES**

The invention is structurally sound and the philosophy (minimum-divergence absorption, swap one file, document the wiring, defer the schema port) is exactly the right way to onboard a mature Panel subsystem into the Sanctum lane. The Anthropic SDK rewrite is clean. The Eve observation port is faithful. The docs are exceptional for a 0.1.0. But shipping the headline ("second Sanctum invention: Eve-aware Snapchat AI") requires PR-1 (4 stub files + Prisma schema extension) before `tsc` even passes, and PR-2 (~30 LOC) before the Eve story is real instead of TODO. Both are small, scoped, low-risk. Do not rebuild — close the gap, flip status from `building` to `shipped`, then iterate on real fan data when the payments table is ready.

## Operator decision
*(left blank)*
