<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
<!-- SANDBOX-ALERT v1 -->
> **Sandbox handling.** Doc-only doctrine; no runtime ops.

> **Author:** RKOJ-ELENO :: 2026-05-24

# Sub-Agent ASCII-Only Prompt-Template Doctrine — 2026-05-24

**Slug:** sub-agent-ascii-only-prompt-template-doctrine-2026-05-24
**Status:** standing-rule (codified from empirical session 2026-05-24)
**Lane:** kernel-apk (originated; fleet-wide binding)
**Tags:** doctrine, standing-rule, binding, sub-agent, prompt-template, ascii-only, em-dash, powershell-5.1, parse-fail, mid-turn-fix

## Operator-facing summary

When you spawn a sub-agent (via `Agent` tool) to write a `.ps1` deliverable that will run on Windows PowerShell 5.1, the spawn prompt MUST include an explicit "ASCII only — no em-dashes, smart-quotes, ellipsis, or non-ASCII punctuation" rule. Without this rule, sub-agents reliably emit Unicode punctuation that PS 5.1's `ParseFile` rejects (even though the file runs fine on PS 7+ / Linux / VS Code).

## Empirical anchor

2026-05-24T19:32Z (kernel-apk lane): swarm-spawned 4 parallel sub-agents for Phase A/B/C pre-flight. Sub-agent #3 (PC-leak audit scanner) returned `tools/sinister-cast/leak-audit.ps1` (505 LOC) with 11 em-dashes embedded in comments + Write-Host strings. First `[Parser]::ParseFile` invocation FAILED with `Unexpected token '—'`. Mid-turn fix: `sed 's/—/--/g'` against the file; re-verified PARSE_OK; dry-run smoke PASS. The 1 quality issue caught + fixed mid-turn is the source of this doctrine.

This is the SECOND time the em-dash gotcha has surfaced (prior brain entry: `powershell-emdash-non-ascii.md` Discoveries 2026-05-24). The first surfacing fixed a single-script case. This second surfacing demonstrates that without a prompt-level guardrail, sub-agents will re-emit the bad output on the next deliverable.

## The rule

Every sub-agent spawn prompt that asks for a `.ps1`, `.psm1`, or `.psd1` deliverable MUST include this exact paragraph (or equivalent):

> **ASCII-only constraint.** Output must be pure ASCII (codepoints 0x20-0x7E plus `\r\n` / `\t`). Do NOT use em-dashes (`—` U+2014), en-dashes (`–` U+2013), smart-quotes (`"` `"` `'` `'` U+201C-U+201D / U+2018-U+2019), ellipsis (`…` U+2026), bullet (`•` U+2022), or any other Unicode punctuation. Use `--` for em-dash, `"` `'` for quotes, `...` for ellipsis, `*` or `-` for bullets. This file will be parsed by Windows PowerShell 5.1 which rejects non-ASCII in many positions. Validate before declaring done: run `[System.Management.Automation.Language.Parser]::ParseFile(<path>, [ref]$null, [ref]$null)` — if it raises any token error, you have non-ASCII content; clean it up.

Optional acceptance-criterion line (recommended):

> **Acceptance test:** the sub-agent runs `Select-String -Pattern '[^\x00-\x7F]' <path>` against its own output before returning. If any match exists, fix it before returning the deliverable. Self-validating sub-agents save the master a mid-turn fix-loop.

## Why sub-agents emit non-ASCII by default

LLM tokenizers + training corpora bias towards "publication-quality" punctuation: em-dashes for parenthetical asides, smart-quotes for prose, ellipsis for omission. When an agent is asked to "write a clean, well-documented PowerShell script" the prose-mode default takes over and Unicode punctuation slips in. PowerShell 7.0+ tolerates it (full UTF-8 native parser); Windows PowerShell 5.1 does not — and 5.1 remains the canonical shell on every fleet Windows machine.

## Scope

- **In-scope:** every `.ps1` deliverable any fleet sub-agent writes (kernel-apk / sanctum / sinister-os / panel / forge / term / generator / freeze / chatbot / showmasters / jb-woodworks)
- **In-scope:** every `.bat` deliverable (cmd.exe also fails on non-ASCII in some positions)
- **Adjacent (recommended):** any `.md` / `.txt` deliverable that will be consumed by a Windows tool whose encoding pipeline isn't UTF-8 (defensive even if not strictly required)
- **Out-of-scope:** sub-agents writing pure Python / Rust / JavaScript / Kotlin / Java / Swift / Go — those parsers accept UTF-8 source by default

## Anti-patterns

1. **Re-fixing without codifying.** Catching the em-dash in turn N, fixing it, and moving on without writing this doctrine means turn N+1 will re-bite. This entry IS the codification.
2. **Adding the rule once then forgetting.** The rule belongs in every sub-agent prompt template, not in a one-off "please" instruction in a single spawn.
3. **Auto-stripping non-ASCII as the universal fix.** Sometimes the user wants the em-dash (e.g. a generated email body); strip-by-default destroys those cases. The rule applies to deliverables PARSED BY PS 5.1, not to all sub-agent output.
4. **Trusting `python -m py_compile` as the validation gate.** That validates Python, not PowerShell. The validation must be the same parser that will read the file at use time.

## Composes with

- `powershell-emdash-non-ascii.md` (prior brain entry; this doctrine is the prompt-template-level corollary)
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (rule 2: test-before-claim; the parse-test is the test)
- `forge-memory-usage` (sub-agent prompt templates are a forge-memory candidate)
- `forever-improve-review-doctrine-2026-05-24` (this doctrine is itself a forever-improve output from the 19:32Z incident)

## Discoveries (append-only)

### 2026-05-24T20:04Z by kernel-apk (initial codification)

First codification. Empirical anchor: 1 mid-turn em-dash fix on `leak-audit.ps1` during the 19:35Z 4-sub-agent swarm wave. Lesson: codify the prompt-level rule, not just the per-incident fix.
