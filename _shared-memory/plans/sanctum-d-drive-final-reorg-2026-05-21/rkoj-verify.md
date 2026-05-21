# RKOJ v1.3.0 Manifest Verification

Author: RKOJ-ELENO :: 2026-05-21
Branch: `agent/sinister-sanctum/cli-dispatcher-2026-05-21`
Scope: read-only audit of `projects/rkoj/MANIFEST.json` (schema_version 1, version 1.3.0, 26 components)

## Results

| # | name | kind | path | verdict | notes |
|---|---|---|---|---|---|
| 1 | forge | forge | projects/sinister-forge/source/forge | GREEN | app.py, panes/, commands.py, theme.py, bridge/, spawn/ all present + __main__.py + 12 modules |
| 2 | forge-agents-dashboard | forge-pane | .../panes/agents_dashboard.py | GREEN | clean textual + forge.* imports, AGPL-3.0 header, RKOJ-ELENO authorship |
| 3 | forge-workstation-tab | forge-pane | .../panes/workstation_panel.py | GREEN | imports textual + forge.theme cleanly; WorkstationPanel class defined |
| 4 | forge-niri-workspace | forge-pane | .../panes/niri_workspace.py | GREEN | v1.1 niri-scrollable-column-pattern port, header intact |
| 5 | forge-theme | forge-theme | .../forge/theme.py | GREEN | THEME_CSS / SINISTER_CSS exports, purple-glass canon |
| 6 | term | term | projects/sinister-term/source/term | GREEN | dir exists (kind=term — not in audit rule set; not blocking) |
| 7 | workstation | workstation | automations/window-manager | GREEN | FastAPI entry in server.py + desktop_app.py, RKOJ.spec + dist/ present |
| 8 | skills-sanctum | skill-dir | skills | GREEN | _INDEX.md present |
| 9 | bots | bot-dir | bots | GREEN | junction to agents/ resolves to 9 sub-dirs (auditor, curator, custodian, librarian, researcher, scribe, sentinel, sinister-bus, _shared) |
| 10 | sinister-cli | tool | tools/sinister-cli | GREEN | sinister_cli/__main__.py + pyproject.toml |
| 11 | sinister-login | tool | tools/sinister-login | GREEN | sinister_login/__main__.py + pyproject.toml |
| 12 | sinister-usage | tool | tools/sinister-usage | GREEN | sinister_usage/__main__.py + pyproject.toml |
| 13 | sinister-swarm | tool | tools/sinister-swarm | GREEN | sinister_swarm/__main__.py + pyproject.toml |
| 14 | sinister-model | tool | tools/sinister-model | GREEN | __main__.py + cli.py in sinister_model/ |
| 15 | sinister-vault | tool | tools/sinister-vault | YELLOW | no Python package; entry is daemon.py + vault-daemon.bat + Sanctum-Vault-Start.bat (MCP daemon, not a CLI module) |
| 16 | sinister-jcode-shim | tool | tools/sinister-jcode-shim | GREEN | sinister_jcode_shim/__main__.py + cli.py + pyproject.toml |
| 17 | sinister-review | tool | tools/sinister-review | GREEN | sinister_review/__main__.py + pyproject.toml |
| 18 | sinister-chatbot | tool | tools/sinister-chatbot | YELLOW | Node.js project (package.json + src/ + prisma/) — kind=tool but not Python; entry via npm scripts |
| 19 | sinister-crawler | tool | tools/sinister-crawler | YELLOW | flat script entry bot.py (no package, no __main__) — works but inconsistent with sibling tools |
| 20 | sinister-phone-viewer | tool | tools/sinister-phone-viewer | YELLOW | flat script entry viewer.py (no package, no __main__) |
| 21 | build-forge-exe | build | automations/build/forge-exe | YELLOW | manifest rule expects `build.ps1` — absent. Has RKOJ.spec + RKOJ-entry.py + smoke-test-rkoj.ps1 + build-rkoj.log instead. Pipeline functional via PyInstaller spec, but file path in audit rule is wrong |
| 22 | sinister-cell-network | project | projects/sinister-cell-network | RED | only 2 files: CLAUDE.md + SESSION-START.md — pure skeleton, no migrated content |
| 23 | sinister-dashboard-skeleton | project | projects/sinister-dashboard-skeleton | GREEN | 125 files migrated |
| 24 | sinister-eve | project | projects/sinister-eve | YELLOW | 6 files (CLAUDE.md + SESSION-START.md + _README.md + _vault/ + eve-mcp/) — thin but non-skeletal |
| 25 | sinister-jokr | project | projects/sinister-jokr | GREEN | 2082 files migrated |
| 26 | sinister-letstext | project | projects/sinister-letstext | GREEN | 14 files across 6 sub-projects (LetsText, LetsText-Legal, letstext-assets, letstext-logos, letstext-pfp-animations) |

## Summary

- GREEN: **18 / 26**
- YELLOW: **6 / 26** (sinister-vault, sinister-chatbot, sinister-crawler, sinister-phone-viewer, build-forge-exe, sinister-eve)
- RED: **1 / 26** (sinister-cell-network)
- Not-classifiable by rule set: **1** (term — kind=term has no audit rule; treated as GREEN by directory-existence)

## Gap-fix recommendations

1. **sinister-cell-network (RED).** Migration left only the CLAUDE.md skeleton — source content from `D:/Sinister/01_Projects/Cell-Network` did not transfer. Re-run Phase-3 copy or mark `enabled: false` in MANIFEST until populated.
2. **build-forge-exe (YELLOW).** Audit rule 6 expects `automations/build/forge-exe/build.ps1`; actual build entry is `RKOJ.spec` invoked via PyInstaller. Either add a thin `build.ps1` wrapper (`pyinstaller RKOJ.spec`) for naming consistency, or update the audit rule.
3. **sinister-vault / sinister-chatbot / sinister-crawler / sinister-phone-viewer (YELLOW × 4).** Mixed entry patterns (bat-launched daemon, Node project, flat .py scripts). Consider standardizing — wrap each in a Python package (`sinister_xxx/__main__.py`) or add an explicit `entry` field to MANIFEST.json schema_version 2 so the dispatcher knows how to launch each.
4. **sinister-eve (YELLOW).** Migration appears partial vs. the 2082-file sinister-jokr. Verify if eve-mcp/ contents are complete or if more was expected from `D:/Sinister/01_Projects/EVE`.
5. **Schema enhancement.** Add `entry` (path) + `runtime` (`python`/`node`/`bat`/`ps1`) fields to MANIFEST so RKOJ.exe info can render launch commands without heuristics.

Overall: v1.3.0 is structurally sound (no missing paths, all forge code imports clean, build artifact present). Two of the seven non-GREEN rows are doctrinal/cosmetic (build.ps1 naming, schema entry-field), four are inconsistent-but-functional tool entries, and one (cell-network) is a genuine missed migration.
