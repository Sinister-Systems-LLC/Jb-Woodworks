> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# LICENSE candidates for Sinister Sanctum

The LICENSE file is currently a **placeholder**. Operator picks one of the three options below; the master agent (or operator) then overwrites `LICENSE` with the corresponding canonical text before the first `git push`.

## Why the choice matters

Sanctum is the **public-shareable hub** (`D:\Sinister Sanctum\`, intended for GitHub `Sinister-Systems-LLC/Sinister-Sanctum`). Operator-private bits (LetsText, JOKR, Yurikey roster, secrets policy) live in `D:\Sinister\` and are NOT shared. The license here governs what Leo (and any future external collaborator) can do with the public hub.

## Option A — MIT License (recommended for Leo-collaboration)

**Pick this if:** you want Leo + future small-team collaborators to freely use, fork, modify, and redistribute Sanctum. Other Sinister business projects can still be Proprietary; MIT only covers what's in this repo.

- **Permissions:** commercial use, modification, distribution, private use
- **Conditions:** include the license + copyright notice in any copy
- **Limitations:** no warranty, no trademark grant
- **One-line summary:** "Take it, build with it, keep the notice intact."

Canonical text: <https://opensource.org/license/mit/>

## Option B — Apache License 2.0

**Pick this if:** you want MIT-like permissiveness PLUS an explicit patent grant (helps with anti-troll posture if Sinister later patents anything related). Slightly more legalese; large-enterprise-friendly.

- **Permissions:** commercial use, modification, distribution, patent use, private use
- **Conditions:** include license, state changes, NOTICE file
- **Limitations:** no trademark, no warranty, no liability
- **One-line summary:** "MIT with a patent grant + a changes-must-be-stated rule."

Canonical text: <https://www.apache.org/licenses/LICENSE-2.0>

## Option C — Proprietary, All Rights Reserved (no public license)

**Pick this if:** Sanctum's public-shareable nature is enough for now and you want to **explicitly retain all rights** while Leo collaborates under direct authorization. External viewers (recruiters, contractors) can read but not legally fork/redistribute. You can later relicense by appending Option A or B without breaking anything (since you're the sole copyright owner of all current commits).

- **Permissions:** none granted to third parties
- **Conditions:** N/A (no grant)
- **Limitations:** N/A
- **One-line summary:** "Visible, not free; Sinister LLC owns it."

Use the current `LICENSE` placeholder text (already All-Rights-Reserved) or tighten it:

```
Copyright (c) 2026 Sinister LLC

All rights reserved.

No use, reproduction, or distribution is permitted without prior written
consent from Sinister LLC.
```

## Recommended path

**Option A (MIT)** — keeps the Leo collaboration friction-free and lets future contractors land patches without legal back-and-forth. Sinister LLC keeps the trademark and the business assets in private repos; only this public hub is MIT-licensed. The trade-off: anyone who clones this repo can fork it — which is fine, because the bots, the brain protocol, and the Sanctum experience are valuable in *context* (operator's stack + integrations + the inventions). A fork of just the docs/automations isn't a competitive threat.

## How to apply the pick

1. Tell master "use MIT" / "use Apache" / "keep proprietary."
2. Master overwrites `D:\Sinister Sanctum\LICENSE` with the canonical text (substitute "2026 Sinister LLC" for the copyright holder).
3. Master amends `_shared-memory/notes/first-commit-message.md` to reference the license picked.
4. Operator runs `git-toolkit safe-push` (per lane discipline — master does NOT push).

## Files referencing the license today

- `D:\Sinister Sanctum\LICENSE` (placeholder)
- `D:\Sinister Sanctum\CONTRIBUTING.md` (may mention licensing)
- `D:\Sinister Sanctum\SANCTUM.md` (may mention licensing)
- `D:\Sinister Sanctum\README.md`

Master will refresh all four to match the picked license once you choose.
