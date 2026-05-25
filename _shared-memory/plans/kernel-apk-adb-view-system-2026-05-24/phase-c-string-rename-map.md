# Phase C — UI String-Rename Mapping (pre-flight; source-tree-gated apply)

> Author: RKOJ-ELENO :: 2026-05-24
> Lane: kernel-apk
> Status: PRE-FLIGHT — apply once source-tree restored (Phase D unblock)
> Parent plan: `_shared-memory/plans/kernel-apk-adb-view-system-2026-05-24/plan.md`

## Why this doc exists

Phase C of the parent plan removes "Luke Spoofer" naming from the APK's user-facing UI per operator directive 2026-05-24T18:14:03Z (*"clean up ui to not have luke spoofer mention or anything like that in the apk kui"*). Source edits are blocked this turn by clone out-of-sync. This doc is the **exact rename table** that will be applied as a single commit the moment the block clears — letting the operator review every label change before it ships.

## Naming policy (3 buckets)

| Bucket | Rule | Examples |
|---|---|---|
| **A. User-visible label** | Rename to "Sinister Spoofer" / "Privacy Spoofer" | strings.xml `<string>` bodies, hardcoded text in layout XMLs, Toast/Snackbar text, About screen |
| **B. Internal symbol (binary-compat)** | KEEP as-is | Kotlin class `LukePrivacyBridge`, KPM module package `lukeprivacy-kpm-5.17`, drawable filename `ic_luke_status.xml` (rename optional, low priority), Resource ID `R.id.luke_status_indicator` (keeping avoids `findViewById` churn) |
| **C. Doc/comment** | Annotate only — leave operator-internal | Brain entries, dev docs, KDoc comments referencing the upstream lukeprivacy KPM project |

## Recommended substitution map

| Old (substring) | New | Bucket | Notes |
|---|---|---|---|
| `Luke Spoofer` | `Sinister Spoofer` | A | Two-word, space-separated, capitalized |
| `LukeSpoofer` | `SinisterSpoofer` | A | PascalCase camera (rare; mostly in feature flags) |
| `luke spoofer` | `sinister spoofer` | A | Lowercase form (Toast messages) |
| `LukePrivacy` (in user-visible string) | `Sinister Privacy` | A | Only in `<string>` bodies — DO NOT rename in class names |
| `LukePrivacy` (in class/package/import) | KEEP | B | Internal symbol; renaming would break KPM bridge |
| `Luke's Spoofer` (possessive) | `Sinister Spoofer` | A | If any |
| `lukeprivacy` (lowercase, in package name `lukeprivacy-kpm-*`) | KEEP | B | Upstream KPM module identifier |
| `Luke` as standalone display name | `Sinister` | A | About / credits screens |

## Discovery commands (run once source-tree restored)

```bash
# from kernel-apk source root (the case-clean repo, post-Phase-D)
SRC=app/src/main

# user-visible strings (Bucket A — must rename)
git grep -n -i 'luke' -- "$SRC/res/values*/strings.xml"
git grep -n -i 'luke' -- "$SRC/res/layout/**/*.xml"
git grep -n -i 'luke' -- "$SRC/res/menu/**/*.xml"
git grep -n -i 'luke' -- "$SRC/res/navigation/**/*.xml"

# hardcoded UI strings in Kotlin/Java (must externalize FIRST, then rename)
git grep -n -E '"[^"]*[Ll]uke[^"]*"' -- "$SRC/java/**/*.kt"
git grep -n -E '"[^"]*[Ll]uke[^"]*"' -- "$SRC/java/**/*.java"

# Bucket B (internal symbols — verify, do NOT rename)
git grep -n 'class.*Luke\|object.*Luke\|fun.*[Ll]uke' -- "$SRC/java/**/*.kt"
git grep -n 'import.*luke' -- "$SRC/java/**/*.kt"

# Bucket C (docs/comments — annotate only)
git grep -n -i 'luke' -- '*.md' 'docs/**' 'Rooting Guide/**'
```

## Locale handling

If `values-es/`, `values-fr/`, `values-de/` etc. exist:
- Apply the substitution in EVERY locale's `strings.xml`.
- For locales where "Sinister Spoofer" sounds odd in-language (e.g. French "Sinister" lacks the right register), keep the English brand-name in those locales — brand names typically don't translate. Operator decision point: if any per-locale alternate is needed, surface before commit.

## Drawables + IDs

Lower priority — operator can choose to defer:

| File pattern | Action |
|---|---|
| `res/drawable/ic_luke_*.xml` | Optional rename to `ic_spoofer_*` + update XML references. Touch 2-5 layout files. |
| `R.id.luke_*` IDs in layouts | Keep — renaming requires `findViewById` updates in every consuming Kotlin file. Net visibility gain = 0 (IDs aren't user-visible). |
| `R.string.luke_*` resource keys | Keep — same logic. Only the VALUE matters for user-visible text; the KEY is internal. |

## Apply order (single-commit recipe)

```bash
# 1. Externalize any hardcoded Luke strings to strings.xml
#    (manual; depends on what git grep reveals)

# 2. String-resource substitution (idempotent)
for f in $(git grep -l -i 'luke' -- "$SRC/res/values*/strings.xml"); do
  sed -i 's/Luke Spoofer/Sinister Spoofer/g'    "$f"
  sed -i 's/LukeSpoofer/SinisterSpoofer/g'      "$f"
  sed -i 's/luke spoofer/sinister spoofer/g'    "$f"
  sed -i 's/LukePrivacy/Sinister Privacy/g'     "$f"   # only safe inside <string> bodies
done

# 3. Hardcoded-in-layout substitution
for f in $(git grep -l -i 'luke' -- "$SRC/res/layout"); do
  sed -i 's/Luke Spoofer/Sinister Spoofer/g'    "$f"
  sed -i 's/LukePrivacy/Sinister Privacy/g'     "$f"
done

# 4. Build + install
./gradlew.bat assembleDebug
adb -s P1 install -r app/build/outputs/apk/debug/app-debug.apk
adb -s P2 install -r app/build/outputs/apk/debug/app-debug.apk

# 5. Manual walkthrough (operator-visible regression check)
#    - Every tab title
#    - Settings → Privacy / Spoofer sections
#    - About / version-info screen
#    - Any Toast that fires on app-launch / on-tab-switch

# 6. Commit
git commit -am "v0.97.48: UI cleanup — drop 'Luke Spoofer' user-visible mention (Sinister Spoofer rename across strings.xml + layouts; internal class+KPM symbols unchanged)"
```

## Risk / regression check

| Risk | Mitigation |
|---|---|
| Accidentally rename internal class name via `sed -i` | Restrict sed scope to `res/values*/` and `res/layout/` only — Kotlin/Java source untouched |
| `LukePrivacy` substring renames inside a string that references the upstream KPM module identifier | Manually inspect each `LukePrivacy` hit before global replace; flag any that read like "Built on top of LukePrivacy KPM v32" — those are docs, NOT user-visible operator-naming |
| KPM module identifier changes | NONE — `lukeprivacy-kpm-5.17` is a Bucket B symbol; sed scope excludes it |
| Localized strings break layout (Sinister Spoofer is longer than Luke?) | "Sinister Spoofer" = 16 chars vs "Luke Spoofer" = 12 chars. Manual walkthrough catches any overflow |

## Acceptance — what "Phase C done" looks like

1. `git grep -i 'luke'` in `res/values*/strings.xml` → ZERO hits.
2. `git grep -i 'luke'` in `res/layout/` → ZERO hits.
3. APK installed on P1 + P2; every tab + every settings screen visited; screenshot diff shows zero "Luke" mention.
4. KPM module still binds correctly (verified by SpooferConfigPoller heartbeat reading `spoofer_state=ON` post-rename — proves `lukeprivacy-kpm-5.17` still loads).
5. Operator sign-off via screenshot walkthrough.

## Composes with

- Parent plan `_shared-memory/plans/kernel-apk-adb-view-system-2026-05-24/plan.md`
- Operator-paced-outage discipline (`_shared-memory/knowledge/operator-paced-outage-discipline-2026-05-21.md`) — this doc is the canonical example of "pre-flight" output during a source-tree gate
- Audit-pass-is-output (`_shared-memory/knowledge/audit-pass-is-output-2026-05-21.md`) — the doc IS the deliverable; no source touched yet
