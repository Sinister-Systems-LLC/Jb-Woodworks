# Author: RKOJ-ELENO :: 2026-05-21

# RKOJ project-shape promotion pattern — `tools/<slug>/` → `projects/<slug>/source/`

**Status:** doctrine
**Composes with:** `rkoj-ui-exact-spec-2026-05-21`, `sinister-rkoj-extensibility-doctrine`, `forever-expanding-modular-architecture-doctrine`, `junction-based-path-migration-pattern`.

---

## When to use

A capability lives in `tools/<slug>/` while it's "just a CLI / utility" — single-purpose, self-contained. When it grows into a **product** with its own lifecycle (versions, releases to Desktop, plugin substrate, multi-tab UI, operator-facing surfaces) — promote it to `projects/<slug>/source/`.

Empirical anchor: 2026-05-21 — `tools/sinister-rkoj-qt/` → `projects/rkoj/source/` after the operator said *"i need you to make a porject in projects for rkoj and add everything there that we use for rkoj. the term, jcode stuff all of it"*.

## The 7-step promotion

1. **Verify the destination exists with docs only** — `projects/<slug>/{CHANGELOG.md, INTEGRATION.md, MANIFEST.json, README.md}` should already exist as the umbrella; if not, create them first.
2. **`git mv tools/<slug> projects/<slug>/source`** — single directory move. Git auto-detects renames at content-similarity >= 50% by default. Modified-but-uncommitted files may show as delete+add (acceptable; same content, slightly less elegant log).
3. **Verify `_SPEC_DIR` / `_TOOL_ROOT` / asset-path resolution stays relative-to-spec** — PyInstaller specs that use `os.path.dirname(os.path.abspath(SPEC))` survive the move unchanged.
4. **Update default path params in companion automations** — `ship-*.ps1`, `smoke-*.ps1`, `install-*.ps1`. Check for `$DistDir` / `$ExePath` / `$RootDir` defaults. The actual pyinstaller output sits at `projects/<slug>/source/<package>/dist/` (NOT `projects/<slug>/source/dist/`) because pyinstaller writes `dist` relative to its working dir.
5. **Update catalog rows**:
   - `tools/_INDEX.md` — remove the `<slug>` row OR mark "promoted-to-projects".
   - `projects/<slug>/MANIFEST.json` — update component `path` fields from `tools/<slug>` to `projects/<slug>/source`.
6. **Update `RKOJ.exe info` / build-pipeline references** — anything that reads the manifest at runtime gets the new paths automatically; anything with hard-coded paths needs a sweep.
7. **PROGRESS append + commit + push** — single commit with message `ship(<slug>): promoted to projects/<slug>/source + <delta>`.

## Anti-patterns

| Anti-pattern | Why bad |
|---|---|
| Junction `projects/<slug>/source → tools/<slug>` instead of full move | The tool is no longer a tool. Junction obscures the promotion + makes git history ambiguous. |
| `git mv` with uncommitted modifications | Modified files show as delete+add instead of rename. Stage and commit before the mv, OR accept the slightly noisier log. |
| Promote without updating `_INDEX.md` | Catalog drifts from reality; future agents (incl. you) re-add a stale row. |
| Hard-coded `tools/<slug>` paths in companion automations | Causes silent breakage at next CI/smoke run. Grep before commit. |
| Ship EXE before path-refs updated | The new EXE works, but the smoke/ship scripts break on the next iteration. |

## Empirical residue

- 69 files renamed via single `git mv`. Git auto-detected 67 as renames; 2 went delete+add (one had unstaged mods).
- 4 companion-script defaults updated (ship + smoke + 3 milestone smokes).
- MANIFEST.json 2 component entries patched (rkoj-qt + rkoj-qt-extensions).
- tools/_INDEX.md 1 row removed.
- Build pipeline unchanged — `RKOJ.spec` used `_SPEC_DIR`-relative paths throughout.
- Smoke M1 PASS within 8s of ship — chrome boots cleanly.
- 75,160,157 byte onefile (+4 KB vs prior — bootstrap helpers).
- Commit `caa66d4`, push `2d51a8b..caa66d4`.

## What stays in `tools/` permanently

- Pure CLIs (`sinister-cli`, `sinister-login`, `sinister-usage`, `sinister-swarm`, `sinister-model`, `sinister-vault`, etc.).
- Single-script utilities (`capture-invention`, `md-trash-bin`, `panel-config`, `mcp-discover`).
- Daemons + sidecars (`sinister-watchdog`, `sinister-recovery-watchdog`, `sinister-jcode-shim`).
- Library shims with no UI (`forge-memory-bridge`, `memory-graph-render`).

## What gets promoted to `projects/`

- Anything with a multi-tab UI.
- Anything that ships an EXE/APK/build artifact.
- Anything with its own version stamp.
- Anything with plugin substrate (`extensions/` dir).
- Anything operator-facing as a primary surface (RKOJ, Forge TUI, Panel web app, Sinister Term).
