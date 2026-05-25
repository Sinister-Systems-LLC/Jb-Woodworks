<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Author: RKOJ-ELENO :: 2026-05-21

# Topic: Research Import Pipeline — operator-drop → audit → integrate-or-archive

> Status: doctrine + scaffolded (PH1 of github-research-watcher already shipped)
> Tags: standing-rule, research, github-imports, audit-pipeline, agpl-quarantine, archive-flow, watcher, drop-folder, operator-throughput
> First codified: 2026-05-21 (operator directive)
> Composes with: `auto-mode-launcher-pattern` + `sinister-forge-harness-pattern` + `apk-classifier-aup-doctrine`

## Operator directive (verbatim 2026-05-21)

> *"I want to be able to mass give you github repos, videos etc to review to get ideas or logic for our system that will expand it. not break it and you can take that info get what you need, update and then place it in archives."*

## The pipeline

```
   Operator drops repo / .zip / .mp4 to:
   C:\Users\Zonia\Desktop\Github Research\
              │
              ▼
   automations\github-research-watcher.ps1
   (fires on every session-start, 6h gate)
              │
   ┌──────────┼──────────┐
   ▼          ▼          ▼
[ASK]  audit       sentinel
in     stub       state
inbox/ at         tracker
test/  plans/...
              │
              ▼
   Next test-agent session picks up [ASK]
   - reads README / LICENSE / package manifest
   - decides USE / EVALUATE / SKIP
              │
   ┌──────────┼──────────┐
   ▼          ▼          ▼
  USE     EVALUATE     SKIP
   │          │          │
   │          │          ▼
   │          │     archived to:
   │          │     _shared-memory/external-imports/<slug>/
   │          │     with verdict + reasoning in NOTES.md
   │          │
   │          ▼
   │     clone to D:\Research\<slug>\
   │     30-min trial; brain entry codifying findings;
   │     then USE-or-SKIP final
   │
   ▼
  port relevant ideas/patterns into our project under
  AGPL-3.0 + RKOJ-ELENO authorship + attribution in NOTICES.md;
  source stays at D:\Research\ (subprocess-callable, NOT imported)
```

## Verdict rubric (the audit step uses this)

| Field | USE | EVALUATE | SKIP |
|---|---|---|---|
| License compatibility w/ AGPL-3.0 | MIT/Apache/BSD/AGPL OK | restrictive OK to read | GPL-incompatible commercial = SKIP |
| Platform | Windows-native OR cross-platform | Linux-only but core idea applies | Wayland-only / Kitty-only / iOS-only = SKIP |
| Stack overlap | Python/JS/Rust we already run | New stack but justified | New stack with no fleet use |
| Capability gap | fills a real gap | adjacent to existing | duplicates existing |
| Maintenance signal | active commits last 30 days | active last 90 days | dead repo |
| Solo-maintainer risk | low (multi-contributor) | acceptable if narrow scope | high if we'd depend on it |

Five greens = USE. Three+ yellows = EVALUATE. Any red on platform / license = SKIP.

## Archive locations

- `D:\Research\<slug>\` — fresh clone, read-only reference. AGPL-quarantine per OBLITERATUS pattern. NEVER imported into Sanctum tree.
- `_shared-memory/external-imports/<slug>/` — audit trail: NOTES.md + VERDICT.md + ATTRIBUTION.md if patterns ported. Sanctum tracks this.
- `_shared-memory/external-imports/_archive/<slug>/` — SKIP verdicts go here with the reasoning, so the next session doesn't re-evaluate.

## How we PORT patterns (not code) when verdict = USE

When we want a feature from an external repo:

1. Read the implementation in `D:\Research\<slug>\` (or wherever the operator dropped it).
2. Identify the design pattern + algorithm — NOT the literal code.
3. Re-implement in our stack, under AGPL-3.0 + RKOJ-ELENO authorship.
4. Add an attribution line in `projects/<our-proj>/source/NOTICES.md`:
   ```
   ## <pattern-name>
   Inspired by <repo-url> (license: MIT). Original concept by <author>.
   Sinister Forge implementation: see <file:line>.
   ```
5. Commit the new file. The external source is NEVER `cp`-ed into our tree.

This keeps us license-clean + lets us continue to evolve the pattern without being downstream of someone else's repo.

## TOP-3 audit verdicts so far (2026-05-21)

- **jcode** (1jehuang) — USE-AS-INSPIRATION for Sinister Forge. Don't adopt the binary; mine the design patterns (memory graph, swarm-mode, multi-provider routing). Forge PH0-PH17 ports them.
- **mermaid-rs-renderer** (1jehuang) — USE direct (Apache 2.0). Subprocess invocation from Mind + Forge for diagram rendering.
- **handterm** (1jehuang) — INSPIRATION ONLY for Sinister Term. handterm itself is Wayland-only Rust; we mine the philosophy + status-bar pattern + per-keypress latency mindset, NOT the code. See `projects/sinister-term/README.md`.

## Anti-patterns

- Cloning a Linux-only project + spending a day trying to make it run on Windows
- Copying GPL code into our AGPL tree without confirming compatibility (AGPL is GPL-compatible going IN, but check the specific clauses)
- Importing a repo's source into `projects/<X>/source/` instead of keeping it at `D:\Research\` as subprocess-only reference
- Skipping the NOTICES.md attribution when porting patterns
- Letting `Desktop\Github Research\` grow without audit + archive — operator's drop folder isn't infinite storage

## Where it lives

| File | Role |
|---|---|
| `automations/github-research-watcher.ps1` | the watcher (already shipped) |
| `_shared-memory/inbox/test/<UTC>-github-research-imports.json` | per-scan [ASK] |
| `_shared-memory/plans/sinister-forge-2026-05-21/desktop-imports-audit.md` | append-only audit log |
| `_shared-memory/external-imports/<slug>/` | per-import audit trail (NOTES + VERDICT + ATTRIBUTION) |
| `_shared-memory/external-imports/_archive/<slug>/` | SKIP-verdict archive |
| `D:\Research\<slug>\` | EVALUATE/USE clones (read-only reference, AGPL-quarantined) |

## Related

- `_shared-memory/plans/sinister-forge-2026-05-21/jehuang-audit.md` — full audit of 1jehuang's profile
- `_shared-memory/plans/sinister-forge-2026-05-21/sanctum-audit-findings.md` — Sanctum Audit Agent TOP-5
- `projects/sinister-forge/source/PLAN.md` — Forge PH12-PH15 are direct ports of audit findings
