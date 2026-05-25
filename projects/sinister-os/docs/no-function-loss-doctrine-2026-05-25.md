# No-function-loss doctrine

> Author: RKOJ-ELENO :: 2026-05-25
> Lane: sinister-os
> Binds: every phase from P0a docker onward.
> Composes with: `research/feature-parity-audit-2026-05-25.md` (the inventory), `docs/rollout-doctrine-2026-05-25.md` (the P0a/b/c gates).

## Operator directive (verbatim, 2026-05-24T21:08Z)

> *"make sure i loose no function that i use on this pc"*

This doctrine is the binding **policy** that turns the parity audit into a hard gate. Any phase promotion that drops a Windows function without operator OK is a doctrine violation.

## Core invariants

1. **Coverage is per-operator, not per-distro.** "Linux can do it" is not coverage. Coverage means: the operator's actual workflow on the new OS achieves the same outcome with no extra steps the operator did not consent to.
2. **Rollback is a feature, not a fallback.** Every phase MUST be reversible from a single keystroke. `eve rollback` (btrfs snapper) is the canonical mechanism.
3. **Surprises are first-class.** Any audit-row regression discovered MID-PHASE adds a row to the audit + emits `reboot-required.sh` if it changed a reboot-class surface. No silent shrugs.
4. **No dual-boot removal without gate.** P5 cutover (full Windows wipe) is operator-only; never agent-initiated.

## Promotion checklist (referenced by every phase-promotion claim)

A phase claims `green` only when ALL of:

- [ ] The phase's audit-row coverage is 100% COVERED, OR every non-COVERED row has an operator-OK comment in this file's "Operator deferrals" section below.
- [ ] Rollback drill executed + recorded in `_shared-memory/PROGRESS/Sinister OS.md`.
- [ ] No proprietary blob arrived undeclared (per CLAUDE.md hard rule 4).
- [ ] The operator's daily-driver workflow for the duration of the phase showed no critical regression.
- [ ] All `reboot-required.json` rows from the phase were acked by the operator OR cleared with explanation.

## Operator deferrals (append-only — operator hand-edited)

Each row needs operator initials + date.

| Audit row | Defer reason | Operator | Date | Re-evaluate at |
|---|---|---|---|---|
| (empty; operator populates during P0b/P0c) | | | | |

## Loss-classification taxonomy

When the audit shows a regression, classify it:

| Class | Definition | Action |
|---|---|---|
| **Hard loss** | Operator workflow becomes impossible (e.g. specific app refuses to run, hardware unsupported). | BLOCKER. Phase does NOT promote. Mitigation = dual-boot for this workflow indefinitely OR find replacement. |
| **Friction loss** | Operator workflow takes more clicks / a workaround / a context switch. | NOT a blocker; appears in operator deferrals with deferral rationale. |
| **UX-different loss** | Same outcome, different muscle memory (e.g. Hyprland binds vs Win+arrow). | NOT a blocker; document in `docs/operator-workflow-deltas.md` for the operator to skim before P0b spawn. |
| **Latent loss** | No regression observed in audit but real risk surfaces in P0c daily use. | Triggers rollback IF operator flags it; otherwise queued for next-iter audit refresh. |

## Anti-patterns (explicit)

- **"Steam works on Linux"** as a claim without testing the operator's actual library. The operator's library is the unit of test.
- **"It's just a config flip"** as a justification for friction loss the operator didn't consent to.
- **"We'll fix it in P5"** as a way to slip a hard loss past a P0c gate. No: hard loss is a blocker, not a deferral.
- **Silent driver upgrades** that change behavior. Every kernel / driver bump emits a `reboot-required.json` row that names what changed.

## How this doctrine composes with CLAUDE.md

- **CLAUDE.md hard rule 1 (VM-only).** Audit smoke happens in a VM until P0b.
- **CLAUDE.md hard rule 2 (operator-gated phases).** Promotion decisions are operator-clicks; doctrine documents the bar.
- **CLAUDE.md hard rule 4 (proprietary blobs).** Every blob in `docs/proprietary-blobs.md` IS a row implicitly added to the audit's "potential regression" surface.
- **CLAUDE.md no-bullshit (2026-05-23).** Every "covered" claim carries a receipt — `VM session id + command + exit code`, recorded in `_shared-memory/PROGRESS/Sinister OS.md`.

## Living-document protocol

This doctrine is updated only by:

- The operator (deferrals + classification overrides)
- The sinister-os lane agent (after audit smokes, with the receipt commit referenced)

Never auto-updated by sister lanes; the no-function-loss responsibility is owned by sinister-os.
