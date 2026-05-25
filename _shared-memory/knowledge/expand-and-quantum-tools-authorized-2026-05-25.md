<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Expand + Quantum Tools Authorized Doctrine — 2026-05-25

> **Author:** RKOJ-ELENO :: 2026-05-25
> **Lane:** fleet-wide (sinister-os captured it; binding on every Sanctum agent)
> **Originating utterance (verbatim 2026-05-25T09:26Z):** *"note in memory all agents can use expand tools and quantum tools as needed just be cautious on the seconds we use."*
> **Composes with:** `loop-relentless-pursuit-doctrine-2026-05-25` rule 10 (tool-reach first) · `safe-quality-loops-doctrine-2026-05-24` (12 guardrails) · `forever-improve-review-doctrine-2026-05-24` · `sanctum-scope-discipline-2026-05-24` · `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (verify before claiming).

## TL;DR

Every fleet agent is **authorized** to invoke expand-tier and quantum-tier tools (Agent sub-spawns with `subagent_type=general-purpose` / `Explore` / `Plan`, parallel multi-tool dispatch, multi-agent swarms, ToolSearch deep loads) when the work warrants it. **Cautious posture:** every invocation is budgeted in seconds — prefer shorter focused queries over wide unbounded scans.

## Authorized tool tiers

| Tier | Tools | Cost gate | When to use |
|---|---|---|---|
| **Routine** | Read, Edit, Write, Grep, Glob, Bash (short) | Free | Default for ≤3-step tasks; single file edits |
| **Expand** | Agent (Explore/Plan/general-purpose), parallel multi-tool dispatch, WebFetch/WebSearch, ToolSearch on-demand schemas | Sub-second per dispatch + agent's own token budget | Non-trivial multi-file work; research questions; cross-codebase audits |
| **Quantum** | Multi-Agent swarms (3-5 parallel general-purpose), background long-running Bash (>2min), worktree isolation, `understand-anything:*` skills | Burns more seconds + tokens | True parallelizable research; massive cross-lane audits; design-trilogy spawns; ISO build pipelines |

## Cautious posture (the "be cautious on the seconds" half)

1. **Bounded prompts.** Every sub-agent prompt has a word-count cap ("under 800 words"), a citation requirement ("cite source URL"), and a "don't speculate" anti-hallucination clause.
2. **Time budget per swarm.** Default cap: 5 minutes wall-clock for a single swarm of 4 parallel agents. If results haven't come back, downgrade to sequential or end gracefully.
3. **Parallel only when truly independent.** Spawn parallel agents ONLY when their findings don't depend on each other. Two sequential agents > four-way parallel for chained research.
4. **Cache + reuse.** Search prior brain rows + cross-agent inbox + recent PROGRESS before spawning a fresh agent. Sub-agent spawns are NOT for things you can answer from disk in <30s of grep.
5. **Surface cost in heartbeat.** Every turn that uses quantum-tier tools logs `tool_seconds_used` in the heartbeat under a `cost_register` block. Operator can see the spend roll-up.
6. **No infinite spirals.** A sub-agent's report is the end of the spawn chain unless the work specifically requires recursive sub-spawning. Default: 1 layer deep.
7. **Background long-running work.** Use `run_in_background:true` for any Bash >2min so the main thread keeps shipping in parallel.

## Anti-patterns (forbidden)

- ❌ Spawning a quantum swarm for a question answerable by a single `Grep`
- ❌ Asking 4 parallel agents the same question to "ensemble" — pick the right one
- ❌ Spawning agents recursively without a base case
- ❌ Using `Agent` to do something that's literally one `Read` away
- ❌ Letting a background process run with no monitor or completion signal

## Specific tool reminders

- **`Agent` tool**: use `subagent_type=Explore` for codebase searches; `Plan` for design; `general-purpose` for research/web; `understand-anything:*` for graph-backed deep dives. Always include enough context that the agent doesn't need follow-ups.
- **`WebSearch` / `WebFetch`**: prefer when the question is "what's the current state of X" or "how does Y work upstream". Cite source URLs in any claim derived from these.
- **`ToolSearch`**: load deferred MCP schemas just-in-time; don't pre-load everything.
- **Background `Bash`**: kick off long builds/tests, then keep working in the main thread. Read the output file when notified.

## How this composes with loop-relentless

Loop-relentless rule 10 says "TOOL-REACH FIRST — reach for `bot-fleet-quick-reference.md` / `automations/fleet-update.ps1` / `mesh-coordinator.ps1` / `agent-poke.ps1` / `forever-improve.ps1` / `Agent` subagent_type / `ToolSearch` BEFORE defaulting to Read/Grep/Edit." This doctrine PERMITS the reach (no need to ask operator). The cautious posture above is the rate-limit.

## How this composes with safe-quality-loops

Safe-quality-loops 12 guardrails include "no destructive loops" and "verify before claiming". Expand/quantum tools don't change those guardrails — every sub-agent's output is `claimed-but-unverified` until the parent agent verifies (smoke-test, source-read, etc).

## Pass criterion

A fleet agent is doctrine-compliant when:

- It uses expand/quantum tools without asking operator permission
- It surfaces tool-seconds spend per turn in heartbeat (when material — i.e. when quantum-tier used)
- It bounds sub-agent prompts with word caps + citation requirements
- It does NOT spawn sub-agents for trivially-answerable questions
- It verifies every sub-agent claim before promoting to `shipped` status
