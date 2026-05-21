# agentgrep evaluation verdict (PH14 / was R9)

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Status:** STATIC-only verdict shipped. Live benchmark blocked behind operator unlock.
> **Plan rows:** R9 / PH14 of `_shared-memory/plans/sinister-forge-2026-05-21/plan.md` + `projects/sinister-forge/PLAN.md`.

## Verdict (TL;DR)

**Hold for live benchmark.** Static analysis says it's a genuine fit for Forge's agent-pane workflow, but the deciding question — does it beat the built-in `Grep` tool on a real Sinister Panel outline/trace query — needs an actual binary, which currently sits behind an AUP classifier wall (see *Live-benchmark blocker* below).

If the binary lands on PATH and the live numbers match the README's `40.3s vs 44.9s` claim, the recommendation flips to **KEEP** and wire it as Forge command `:grep` plus the optional bridge endpoint `POST /api/forge/grep`. If the benchmark gap is under 10%, **SKIP** — the built-in Grep already returns structured results from the harness.

## What agentgrep offers (from README + `Cargo.toml` static read)

Source: `D:\Research\agentgrep\` (commit fetched 2026-05-21T11:00Z, `0.1.2`, MIT).

Four modes:

| Mode | What it does | Built-in `Grep` equivalent |
|---|---|---|
| `grep` | Exact lexical search, grouped by file + enclosing symbol | `Grep` (no symbol-grouping) |
| `find` | Ranked file discovery with structure summaries | `Glob` (no rank, no summary) |
| `outline` | Known-file structural scan without reading the whole body | `Read` (full body) |
| `trace` | Ranked files **and** ranked code regions for an investigative ask | No direct equivalent |

The pitch: replace an agent's first noisy probe (one `rg` + one `Glob` + N `Read`s) with **one** `agentgrep trace` call that returns a compact structured result packet. The README's own demo run claims a **~10% wall-clock reduction** on a `jcode` task (`40.3s` vs `44.9s`).

Key static-analysis observations:

- **No daemon, no index, no embeddings.** Index-free + daemon-free is operator-canonical hygiene (matches `daemon-liveness-heartbeats` ethos — minimal background state).
- **`ignore` + `globset` deps.** Same crates ripgrep uses → respects `.gitignore` out of the box. No risk of accidentally indexing `_vault/` or `__pycache__/`.
- **JSON output mode.** Scriptable from any Forge pane. Good fit for the `forge.bridge` REST endpoint pattern.
- **Stated "harness-provided retrieval context" feature.** Optional — Forge can decide whether to feed in context or call it stateless.
- **License: MIT.** AGPL-3.0 compatible (one-way; we can call the binary as a subprocess without re-licensing Forge).

## Where Forge would wire it

If KEEP:

1. **Forge command `:grep <query>`** — operator types `:grep` inside a Forge pane → routes to `agentgrep grep` → renders the structured packet into the pane scrollback.
2. **Bridge endpoint `POST /api/forge/grep`** — Sinister Claw + RKOJ Forge tab (R7) can both call it. Same auth as the other bridge routes.
3. **Spawn-time injection** — when Forge spawns a Claude subprocess, prepend a one-liner to the cold-start phrase: "Code search: try `agentgrep` for outline/trace queries; fall back to built-in `Grep` for hot-path matches." Agent picks per query.
4. **NOT a replacement for the built-in Grep tool.** The harness's Grep is in-process and zero-startup-cost; agentgrep is a subprocess. Use it where the structured packet matters; keep Grep for tight loops.

If SKIP:

1. Document in this verdict why (benchmark gap too small / startup overhead dominates / structured packet not worth the subprocess hop).
2. Leave the clone at `D:\Research\agentgrep\` for future re-evaluation when a 0.2+ release ships with bigger gains.

## Live-benchmark blocker

`cargo build --release` inside `D:\Research\agentgrep\` was attempted and refused by the Anthropic AUP classifier at 2026-05-21T11:11Z. Refusal text (paraphrased): *"Building/compiling code from an externally cloned repo constitutes executing untrusted external code; not authorized as a declared dependency."*

This is the canonical `apk-classifier-aup-doctrine` situation: hard-stop INDEPENDENT of the operator's autonomy grant. Per Contract 3 (AUP-RESPECT), surface to operator + don't route around.

**To unlock the live benchmark, the operator can either:**

1. **One-shot manual build** (preferred, lowest blast radius):
   ```powershell
   Set-Location D:\Research\agentgrep
   cargo build --release
   Move-Item .\target\release\agentgrep.exe C:\Users\Zonia\bin\agentgrep.exe   # or anywhere on PATH
   ```
   Then a future Forge agent picks up the binary and runs the benchmark below.

2. **Add a Bash allow-rule** for `cd D:\Research\* && cargo build*` in `~/.claude/settings.json` and re-spawn the agent — but per `marketplace-plugin-purge` ethos this isn't the operator's preferred path (they manage settings additions deliberately).

3. **Skip the live benchmark entirely** — accept the static verdict and either ship the wire-in based on the README claim, or table PH14 indefinitely.

## Live-benchmark protocol (when unblocked)

Run from `D:\Sinister Sanctum\projects\sinister-panel\source\`:

```bash
# Setup
hyperfine --warmup 1 --runs 5 \
  'agentgrep grep "useEffect" -o json' \
  'rg "useEffect" --json | head -100'

# Outline mode — find component renderers
hyperfine --warmup 1 --runs 5 \
  'agentgrep outline app/components/*.tsx' \
  'rg -l --type tsx . app/components/'

# Trace mode — investigative
hyperfine --warmup 1 --runs 5 \
  'agentgrep trace "where is the LinkScope dashboard rendered?"' \
  'rg -l "LinkScope" && rg "dashboard" app/'
```

KEEP threshold: `agentgrep` ≥ 2x faster for ≥ 2 of 3 queries AND structured packet shows enclosing-symbol context that `rg` lacks.

SKIP threshold: gap under 10% across the board OR structured packet collapses to the same lines `rg` already returns.

## Cross-references

- `D:\Research\agentgrep\README.md` — source claims
- `D:\Research\agentgrep\Cargo.toml` — `agentgrep 0.1.2`, MIT
- `_shared-memory/knowledge/apk-classifier-aup-doctrine.md` — AUP hard-stop pattern
- `_shared-memory/plans/sinister-forge-2026-05-21/sanctum-audit-findings.md` — TOP-5 #3 ranking origin
- `automations/agent-host-routing.md` — multi-provider routing contract (where the `:grep` command would land)
- `projects/sinister-forge/PLAN.md` PH14 row
