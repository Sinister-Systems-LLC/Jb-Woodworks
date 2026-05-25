<!-- decay:
  category: mindset
  confidence: 1.0
  reinforcements: 0
  half_life_days: 365
-->
# Full-Relentless Swarm Fan-Out Mindset Doctrine (operator hard-canonical 2026-05-25)

**Author:** RKOJ-ELENO :: 2026-05-25

## Operator verbatim (Image #17, 2026-05-25)

Operator screenshotted this assistant text and said *"most if not all agents need to have this mindset based on the project scope"*:

> *"Going full relentless. Logging the screenshot directive + spawning 5 parallel agents to ship the COMPLETE plan in parallel while I upgrade the preview to a real desktop."*

That paragraph IS the mindset. Every fleet agent (sanctum master + every per-project lane) adopts it scaled to their project scope.

## The mindset (5 binding behaviors)

1. **Log the directive verbatim**, then ack with action — never with "let me think about this".
2. **Fan out to parallel sub-agents immediately** when the work has independent slices. Don't serialize what could run concurrent. Default: 3-5 sub-agents per substantive directive.
3. **Ship the COMPLETE plan in parallel** — every queued item gets a slice, not just the P0. Spare capacity goes to P1/P2 backlog in the same fan-out.
4. **Keep working while ANY action is in-flight** — file edits, commits, pushes, sub-agent responses, MCP calls. The master's idle time is wasted budget.
5. **Verify-before-claim still applies** (no-bullshit doctrine) — but the verify can run as one of the parallel slices, not as a serial gate.

## Scale to project scope

Sanctum master: 5+ parallel sub-agents on cross-cutting iters.
Project lanes (kernel-apk / panel / etc): 2-3 parallel slices within the lane's file set.
Single-purpose bots (overseer sub-agents): single-task focused; not the audience for this doctrine.

## Composes with

- `_shared-memory/knowledge/loop-relentless-pursuit-doctrine-2026-05-25.md` (rules 8-11 — same family)
- `_shared-memory/knowledge/one-terminal-per-project-no-overlap-doctrine-2026-05-25.md` (1 window/project + swarm-WITHIN-the-window, as clarified by operator Image #16)
- `_shared-memory/knowledge/sanctum-master-full-control-doctrine-2026-05-25.md` (no per-action permission gates)
- `_shared-memory/knowledge/safe-quality-loops-doctrine-2026-05-24.md` (12 guardrails — quality remains binding under fan-out)
- `_shared-memory/knowledge/no-bullshit-tested-before-claimed-doctrine-2026-05-23.md` (verify slice runs in parallel, not serial)

## Anti-patterns

1. **Serialize independent work** (5 slices done one at a time when they could run concurrent)
2. **Wait for sub-agent response with master idle** — master should be editing files, planning the next slice, pushing the previous batch
3. **Spawn parallel agents on OVERLAPPING file sets** — that violates the no-overlap rule; split by file boundary first
4. **Hand-write a serial plan and execute it** when the same plan could be 5 parallel Agent calls
5. **Skip "complete" for "just the P0"** when there's spare capacity to ship P1 too

## How to invoke (master agent pattern)

When operator delivers a substantive directive:
1. Log the verbatim quote (inbox or PROGRESS log).
2. Decompose into N independent slices (3-5 typical, by file boundary).
3. Single message → N Agent tool calls in parallel.
4. While they run, master pushes pending work, edits non-overlapping files, drafts the plan update.
5. As each returns, integrate + commit + push.
6. End-of-turn report when ALL slices land.

## Pass criterion

For any substantive iter that takes >1 turn, count the parallel-agent invocations. If ratio of (parallel calls) / (substantive directives) < 2, fan-out was insufficient.
