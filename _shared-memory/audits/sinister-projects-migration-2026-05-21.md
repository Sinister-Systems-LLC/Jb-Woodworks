# D:\Sinister\01_Projects Audit — Phase 3 Migration Plan

Author: RKOJ-ELENO :: 2026-05-21
Branch: agent/sinister-sanctum/cli-dispatcher-2026-05-21
Mode: READ-ONLY audit. No moves, no git changes.

## Summary table

| Project | Size | Files (top/total) | git? | Remote | Conflict in Sanctum? | Recommended action |
|---|---|---|---|---|---|---|
| Cell-Network | 0.01 MB | 2 / 2 | no | n/a | no (`sinister-cell-network` absent) | MOVE (docs-only stub) |
| Dashboard-Skeleton | 0.80 MB | 3 / 149 | no | n/a | no (`sinister-dashboard-skeleton` absent) | MOVE |
| EVE | 0.01 MB | 5 / 12 | no | n/a | no (`sinister-eve` absent) | MOVE |
| Inventions | 0.01 MB | 2 / 2 | no | n/a | no | MOVE into `inventions/` (Sanctum already has `inventions/` root) — **MERGE flag** |
| JOKR | 478.11 MB | 7 / 23886 | no | n/a | no (`sinister-jokr` absent) | MOVE (large; verify free space) |
| LetsText | 0.16 MB | 7 / 33 | no | n/a | no (`sinister-letstext` absent) | MOVE |
| RKOJ | 0.14 MB | 6 / 34 | no | n/a | **YES** — `projects/rkoj/` already exists in Sanctum | **MERGE** (operator decides: rename incoming to `rkoj-legacy` or fold subprojects into existing `rkoj/MANIFEST.json`) |
| Sinister | 11247.76 MB | 18 / 67397 | no | n/a | **YES** — multiple subprojects already in Sanctum as physical dirs (sinister-panel, sinister-bumble-emu, sinister-snap-emu, sinister-tiktok-emu, sinister-emulator-bundle, sinister-kernel-apk-adjacent) | **MERGE** subdir-by-subdir |

Global findings:
- **No `.git` directories** in any of the 8 audited subdirs. None are tracked repos at this layer (history lives in Sanctum or in product-repo junctions elsewhere).
- **No junctions/reparse points** — every path is a real directory, including `D:\Sinister\01_Projects\` itself.
- No `README.md`, `pyproject.toml`, or `package.json` at the top of any audited subdir. Only CLAUDE.md / SESSION-START.md / `_README.md` markers.
- Sanctum target slugs proposed below follow `sinister-<lowercase-dash-slug>` convention to match existing Sanctum projects (`sinister-forge`, `sinister-term`, `sinister-panel`, etc.).

---

## 1. Cell-Network

1. **Size**: 0.01 MB
2. **File count**: 2 top-level / 2 total
3. **Git repo?**: No (`.git` absent)
4. **Git details**: n/a
5. **Markers present**: CLAUDE.md = **yes**, README = no, pyproject.toml = no, package.json = no, SESSION-START.md = yes
6. **Suggested target**: `projects/sinister-cell-network/`
7. **Conflict**: None. `D:\Sinister Sanctum\projects\sinister-cell-network\` does not exist.
8. **Junction?**: No (regular directory, attrs=Directory, target empty)

Notes: Docs-only scaffold (CLAUDE.md + SESSION-START.md). Trivial MOVE.

---

## 2. Dashboard-Skeleton

1. **Size**: 0.80 MB
2. **File count**: 3 top-level / 149 total
3. **Git repo?**: No
4. **Git details**: n/a
5. **Markers**: CLAUDE.md = no, README = no (`_README.md` present, non-canonical), pyproject.toml = no, package.json = no
6. **Suggested target**: `projects/sinister-dashboard-skeleton/`
7. **Conflict**: None.
8. **Junction?**: No

Notes: Top-level layout = `dashboard-skeleton/`, `_vault/`, `_README.md`. The 149 files imply a real codebase under `dashboard-skeleton/`. MOVE intact, then inspect for build files inside the subdir.

---

## 3. EVE

1. **Size**: 0.01 MB
2. **File count**: 5 top-level / 12 total
3. **Git repo?**: No
4. **Git details**: n/a
5. **Markers**: CLAUDE.md = **yes**, README = no (`_README.md` present), pyproject.toml = no, package.json = no, SESSION-START.md = yes
6. **Suggested target**: `projects/sinister-eve/`
7. **Conflict**: None.
8. **Junction?**: No

Notes: Layout = `eve-mcp/`, `_vault/`, CLAUDE.md, SESSION-START.md, `_README.md`. Contains `eve-mcp/` (likely the MCP server scaffold tied to the new EVE agent identity). MOVE.

---

## 4. Inventions

1. **Size**: 0.01 MB
2. **File count**: 2 top-level / 2 total
3. **Git repo?**: No
4. **Git details**: n/a
5. **Markers**: CLAUDE.md = **yes**, README = no, pyproject.toml = no, package.json = no, SESSION-START.md = yes
6. **Suggested target**: `inventions/` (Sanctum already has a root-level `inventions/` per CLAUDE.md catalog table)
7. **Conflict**: **YES at concept level.** Sanctum already canonicalizes inventions under `D:\Sinister Sanctum\inventions\` (one .md per invention). Source dir here is just two stub files (CLAUDE.md + SESSION-START.md), so risk is low.
8. **Junction?**: No

Notes: **MERGE** — fold any non-stub content into Sanctum's existing `inventions/` index. The CLAUDE.md/SESSION-START.md here are stub markers, not invention entries, so likely discard after operator review.

---

## 5. JOKR

1. **Size**: 478.11 MB (478.08 MB concentrated in `JOKR-Global/`)
2. **File count**: 7 top-level / 23,886 total
3. **Git repo?**: No (top-level)
4. **Git details**: n/a — sub-checks did not find `.git` under any of the three subprojects either
5. **Markers**: CLAUDE.md = **yes**, README = no (`_README.md` present), pyproject.toml = no, package.json = no, SESSION-START.md = yes
6. **Suggested target**: `projects/sinister-jokr/`
7. **Conflict**: None — `sinister-jokr` not in Sanctum yet.
8. **Junction?**: No

Subprojects: `JOKR-Global/` (478 MB, the bulk), `Library-of-JOKR/` (~0 MB), `Logo-Options/` (0.02 MB), `_vault/`.

Notes: Large move (478 MB). Verify Sanctum partition headroom before move. MOVE.

---

## 6. LetsText

1. **Size**: 0.16 MB
2. **File count**: 7 top-level / 33 total
3. **Git repo?**: No
4. **Git details**: n/a (no subproject has `.git`)
5. **Markers**: CLAUDE.md = no, README = no (`_README.md` present), pyproject.toml = no, package.json = no
6. **Suggested target**: `projects/sinister-letstext/`
7. **Conflict**: None.
8. **Junction?**: No

Subprojects: `LetsText/`, `letstext-assets/` (0.15 MB — the bulk), `LetsText-Legal/`, `letstext-logos/`, `letstext-pfp-animations/`, `_vault/`. Mostly brand/asset bundle.

Notes: MOVE.

---

## 7. RKOJ

1. **Size**: 0.14 MB
2. **File count**: 6 top-level / 34 total
3. **Git repo?**: No
4. **Git details**: n/a
5. **Markers**: CLAUDE.md = **yes**, README = no (`_README.md` present), pyproject.toml = no, package.json = no, SESSION-START.md = yes
6. **Suggested target**: `projects/rkoj/` (Sanctum-canonical slug is `rkoj`, no `sinister-` prefix per existing layout)
7. **Conflict**: **YES.** `D:\Sinister Sanctum\projects\rkoj\` already exists with its own `MANIFEST.json` (per CLAUDE.md). Operator decision required.
8. **Junction?**: No

Subprojects: `Sinister-Drone/`, `Sinister-Mobile/`, `_vault/` (all minimal).

Notes: **MERGE.** Recommended: fold the two subprojects into the existing `projects/rkoj/MANIFEST.json` as nested entries (`rkoj/sinister-drone/`, `rkoj/sinister-mobile/`), or alternatively elevate them as `projects/sinister-drone/` + `projects/sinister-mobile/`. Operator picks.

---

## 8. Sinister

1. **Size**: 11,247.76 MB (~11 GB)
2. **File count**: 18 top-level / 67,397 total
3. **Git repo?**: No (top-level)
4. **Git details**: n/a — none of the 15 subprojects has a top-level `.git` (deeper history may live in product repos junctioned from elsewhere)
5. **Markers**: CLAUDE.md = no, README = no (`_README.md` + `_status.md` present), pyproject.toml = no, package.json = no
6. **Suggested target**: not a single slug — explode into per-subproject Sanctum entries
7. **Conflict**: **YES, heavy.** Multiple subprojects already physically exist in Sanctum:
   - `Sinister-Panel` (1161 MB) ↔ `projects/sinister-panel/` **EXISTS**
   - `Sinister-Bumble-EMU` (~0 MB) ↔ `projects/sinister-bumble-emu/` **EXISTS**
   - `Sinister-Snap-EMU` (1138 MB) ↔ `projects/sinister-snap-emu/` **EXISTS**
   - `Sinister-TikTok-EMU` (4868 MB) ↔ `projects/sinister-tiktok-emu/` **EXISTS**
   - `Sinister-Emulator-Bundle` (363 MB) ↔ `projects/sinister-emulator-bundle/` **EXISTS**
   - `Sinister-APK` (3719 MB) ↔ likely overlaps `projects/sinister-kernel-apk/`
   - `Sinister-Workstation-Setup`, `Sinister-Sandbox`, `Snap-Signer`, `Library-of-Alexandria`, `Sinister-iMessage-Bridge`, `Sinister-RKA`, `Sinister-TG`, `Kernel-SU-Setup`, `sinister-helper` — no obvious Sanctum match yet
8. **Junction?**: No (neither parent nor any subproject is a reparse point)

Notes: **MERGE subdir-by-subdir.** This 11 GB tree is the largest and most entangled item. Recommended Phase 3 sub-plan:
1. For each Sinister-* subproject that **already exists** in Sanctum, run a content-diff pass before any move. Where Sanctum copy is newer/canonical, leave source for archive only; otherwise reconcile.
2. For new-to-Sanctum subprojects (Sinister-Workstation-Setup, Snap-Signer, Sinister-iMessage-Bridge, Sinister-RKA, Sinister-TG, Kernel-SU-Setup, sinister-helper, Library-of-Alexandria, Sinister-Sandbox), MOVE individually as `projects/sinister-<slug>/`.
3. Defer the bulky emu subprojects (TikTok=4.8 GB, APK=3.7 GB, Panel=1.1 GB, Snap=1.1 GB) until reconciliation is decided to avoid double-counting disk usage.

---

## Phase 3 recommended order

1. **Low-risk MOVEs first** (no conflict, <1 MB): Cell-Network, Dashboard-Skeleton, EVE, LetsText.
2. **Operator-decision MERGEs**: Inventions (fold into root `inventions/`), RKOJ (fold into existing `projects/rkoj/`).
3. **Large MOVE**: JOKR (478 MB) — verify free space on Sanctum partition.
4. **Subdir-by-subdir reconciliation**: Sinister (~11 GB). Highest-priority reconciliation: Sinister-Panel, Sinister-APK, Sinister-Snap-EMU, Sinister-TikTok-EMU, Sinister-Emulator-Bundle vs their Sanctum counterparts.

## Flags for operator

- **RKOJ collision**: do not auto-rename; pick merge strategy.
- **Inventions collision**: low risk (source is stub-only), still confirm.
- **Sinister subproject collisions**: 5+ subprojects have same-name (case-different) physical dirs in Sanctum. Each needs content-diff before any move to avoid clobber.
- **Disk budget**: Sinister (~11 GB) + JOKR (478 MB) ≈ 11.5 GB to absorb. Confirm Sanctum partition free space ≥ 15 GB before executing Phase 3.
- **No git history** at any audited layer — preserve nothing on git side at the top level; any commit history lives further down (or doesn't exist).
