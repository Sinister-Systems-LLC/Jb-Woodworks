# Sinister-Lang Feasibility Research

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Lane:** sinister-os
> **Trigger:** Operator hard-canonical 2026-05-24 *"Maybbe we can take this as fasr as creating our own coding languge to make our servers and everything as effcient as they can be."*
> **Research-agent source:** A (general-purpose; see _shared-memory/plans/sinister-os-massive-expansion-2026-05-24T2110Z/plan.md ITER 8).

## 1. Verdict — PARTIALLY PURSUE

Building a full general-purpose programming language is a multi-year sinkhole for a one-operator + small-fleet team — the compiler / tooling / LSP / docs burden alone consumes more cycles than the entire OS build. **However**, a narrow DSL for service config + EVE action scripts is genuinely defensible, ships in days, and yields measurable efficiency (config validation + EVE-native action primitives).

**Build "Sinister-script the DSL", NOT "Sinister-lang the language."**

## 2. Recommended path — hybrid (CUE schema + Janet embed)

- **Tier A (config):** Sinister-specific DSL for services / stacks / EVE-actions, transpiled to `systemd` units + `docker compose` + Hyprland config. NixOS-modules-lite but operator-tuned. Built on **CUE** (schema + constraint solving) with a ~500-line Rust/Zig codegen shim.
- **Tier B (scripting):** Embed **Janet** (or Lua) as the in-process scripting language for EVE itself — fast, ~300 KB, dynamically typed, sandboxable, parses Lisp-like S-exprs that LLMs emit reliably.
- **No new compiler.** Tier A transpiles via a small tool; Tier B is a library embed.

## 3. Steal-worthy prior art

| System | License | What we steal |
|---|---|---|
| **Nickel** (Tweag) | MIT/Apache-2.0 | Gradual typing + merge semantics for config; record contracts |
| **CUE** (Google) | Apache-2.0 | Schema-as-value, constraint solving, `cue vet` for validation |
| **Janet** (bakpakin) | MIT | Embeddable Lisp, ~300 KB, PEG parser built-in, fibers for green threads |
| **Dhall** | BSD-3 | Total-functional config (no infinite loops in config) |
| **NixOS module system** | MIT | Module composition + option types |
| **Zig comptime** | MIT | Model for macro-route on Rust/Zig host code |

**Foundation:** CUE-style schema + Janet runtime. Both permissive, mature, zero new-language tax.

## 4. MVP (1-week shippable)

A `.sin` config format + `sinctl` transpiler:

```
service "stable-diffusion" {
  image: "auto/sd:latest"
  gpu: required
  port: 7860
  eve.action "generate" { args: [prompt], runs: "curl localhost:7860/api" }
}
```

Transpiles to:
- `systemd` unit
- `docker-compose.yml` fragment
- EVE action registry JSON

Built on CUE (validation + schema) + small Rust shim (codegen).

**Wins:** single source of truth, schema-validated at edit-time, EVE can introspect available actions without parsing 10 disparate config formats. **No new language runtime — just a transpiler over CUE.**

**Tier B (week 2+):** embed Janet in `sinister-eve.service` for hot-reloadable action scripts.

## 5. Risks

1. **Bus factor of one** — if operator + EVE both stop maintaining the transpiler, every service config becomes unreadable to outside contributors (Leo onboarding pain).
   - *Mitigation:* keep `.sin` files alongside generated artifacts; transpiler output is human-readable.
2. **Ecosystem isolation** — community Docker / systemd tooling assumes standard formats. Every `docker compose up` workflow now requires `sinctl render` first.
   - *Mitigation:* bidirectional (parse existing compose → `.sin`).
3. **Premature abstraction** — operator has ~10 services today; a config DSL pays off at 50+ services or multi-machine fleet. Risk we build the DSL before the scale justifies it.
   - *Mitigation:* gate Tier A behind "do we have 20+ services?" checkpoint; ship Tier B (Janet embed) first since EVE action scripting is needed regardless.

## Bottom line

Ship Janet embed in EVE this week (real efficiency win for AI-driven actions), defer the `.sin` config DSL until service count justifies it. **Avoid the "build our own language" trap entirely.**

## Recommended ship order

| Week | Deliverable | Owner |
|---|---|---|
| 1 | Janet embed prototype inside `sinister-eve.service` | sinister-os lane + agent-fleet |
| 2 | EVE action registry consumed by Janet runtime | sinister-os lane |
| 3 | CUE schema for current ~10 services (validation-only, no codegen yet) | sinister-os lane |
| 4 | `sinctl render` codegen prototype (one service end-to-end) | sinister-os lane |
| 5 | Decision checkpoint: pursue full `.sin` DSL or stop at CUE-schema validation | operator-gated |

## Composes-with

- `_shared-memory/plans/sinister-os-massive-expansion-2026-05-24T2110Z/plan.md` (ITER 11)
- `projects/sinister-os/plans/master-plan-2026-05-24.md` (architecture L0-L7 — `.sin` would generate L4 service units)
- `projects/sinister-os/source/eve-control/DESIGN.md` (Janet would embed in the EVE daemon)
