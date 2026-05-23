# Sinister Freeze :: CLAUDE.md (cold-start protocol)

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Lane:** `sinister-freeze` :: branch `agent/sinister-freeze/<topic>` :: purple accent
> **External user:** Joe at Ferrari of Winter Park (operator's friend) — every UX choice optimizes for HIM, not operator

## Cold-start (when launched as `-Project sinister-freeze`)

Inherit `automations/session-contracts.md` (6 binding contracts). Plus Freeze-specific:

1. Read `projects/sinister-freeze/README.md` (north star + operator directive verbatim)
2. Read latest `_shared-memory/plans/sinister-freeze-2026-05-21/deep-research.md` — research-agent output
3. Read latest `_shared-memory/plans/sinister-freeze-2026-05-21/plan.md` — phase plan
4. Read latest `_shared-memory/resume-points/sinister-freeze/<UTC>.json` if exists
5. Check `_shared-memory/inbox/sinister-freeze/` for [ASK] / [DELEGATE] / [HELLO] tags from sibling fleet
6. Check `_shared-memory/forge-memory/freeze/` for Joe's accumulated context (lead notes, drafts, briefs)

## Lane rules (extra to canonical)

### JOE-SAFETY (7th contract, Freeze-specific)

- **No automated send** of any email / DM / SMS without Joe's explicit click. The agent DRAFTS; Joe SENDS.
- **No social post auto-publish** without Joe's preview-and-approve. Scheduled posts queue; Joe confirms.
- **No customer-data exfiltration** to non-operator-owned infra. Everything stays in `_shared-memory/forge-memory/freeze/` or Joe's local DB.
- **No TCPA / CAN-SPAM violations**: SMS opt-in double-confirmed; emails carry unsubscribe; rate-limits enforced at the bridge layer.
- **No Ferrari brand violations**: no F-corporate imagery generated; only Joe's own photos used.

### Friendly-by-default UX

- Joe is not a programmer. Every CLI prompt is plain English ("Draft a reply", not "Invoke draft_reply()")
- Error messages are debuggable BY JOE — "Couldn't reach Gmail; check you're logged in" not stack traces
- Every action has an UNDO within 30 seconds
- Default response style: concierge (matches Ferrari clientele)

### Data sovereignty

- Joe's PC = primary storage when self-hosted
- Sanctum host = backup + sync hub (encrypted in Sinister Vault)
- No third-party SaaS without operator's OK + Joe's signed consent
- Customer PII tagged + grep-auditable from day 1

## Sibling agents to coordinate with

| Slug | Display | Purpose | What we share |
|---|---|---|---|
| `sanctum` | Sinister Sanctum | master orchestration | tools/forge-memory-bridge, brain, automations |
| `forge` | Sinister Forge | multi-pane TUI | spawn Freeze sub-agents via Ctrl+W picker entry |
| `sinister-term` | Sinister Term | shell | `/freeze` builtin drops Joe into Freeze session |
| `rkoj` | RKOJ Workstation | window-mgr | Freeze tab in RKOJ once Joe-friendly UI lands |
| `panel` | Sinister Panel | Hetzner dashboard | dealership-wide rollup once Freeze v2 ships |
| `apk` | Kernel APK | n/a | no overlap |

## Branding (locked)

- Purple primary `#7A3DD4`
- Black / very-dark-grey background
- Dim cyan secondary text
- Vault Boy ASCII boot art (1.2s spin per Forge convention)
- Cascadia Code (CLI) / Mona Sans (web)
- Concierge voice in all generated text

## Authorship

Every new `.bat`, `.md`, `.ps1`, `.py`, `.ts`, `.tsx` from this lane:
```
Author: RKOJ-ELENO :: <date>
```

## Composes with (see README.md for full map)

`forge-memory-bridge` · `memory-graph-render` · `memory-consolidate` · `agent-host-routing` · `session-contracts` · sibling lanes
