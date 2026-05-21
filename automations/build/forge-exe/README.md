# RKOJ.exe build pipeline

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Output:** `C:\Users\Zonia\Desktop\RKOJ.exe` (29 MB onefile PyInstaller build)

The Sinister Sanctum click-to-launch executable. Replaces the old `Sinister Forge.bat` + `Start-Sinister-Session.bat` two-step flow with one EXE that boots into a **jcode-style `>` prompt** — interactive multi-step tool-using agent shell.

## What v0.6.0 ships

1. **jcode-style `>` prompt** — natural-language input box; type a question, get a streaming response with visible tool use. No more ASCII-art boot picker; the shell IS the surface.
2. **Anthropic SDK direct path (preferred)** — when `ANTHROPIC_API_KEY` is set, `forge/spawn/anthropic_direct.py` runs an in-process `anthropic.Anthropic.messages.stream` loop with 12 turns / 8K tokens-per-turn / `claude-opus-4-7` model. Streams `thinking_delta` (💭) + `text_delta` live. See `docs/ENV-VARIABLES.md` for the unlock — direct path beats `claude -p` fallback on latency, observability, and tool-use depth.
3. **`claude -p` fallback** — when API key absent OR SDK crashes, falls back to the legacy `claude -p` subprocess path. Same 6 tools wired; same memory bridge before/after each turn.
4. **6 tools wired** — `bash` (safety-gated against `rm -rf` / `format c:` / `shutdown` / fork-bombs), `read_file`, `write_file`, `glob_search`, `grep_search`, `session_search`.
5. **Batch tool-call rendering** — multiple `tool_use` blocks in one assistant turn render as `● tool {name} {preview}` + gray-boxed first-6-lines result preview. Matches jcode's visual idiom (brain entry pattern 2, 3).
6. **Pre-turn + post-turn memory bridge** — `forge_memory_bridge.recall()` injects relevant memories before the turn; `forge_memory_bridge.write()` saves outcomes after. Memory store at `_shared-memory/forge-memory/`.
7. **Sinister-CLI umbrella** — `RKOJ.exe login providers`, `RKOJ.exe usage check-all`, `RKOJ.exe swarm list`, `RKOJ.exe memory recall ...`, `RKOJ.exe model list`, etc. Same dispatch as the `sinister` binary.

## What v0.7.0+ ships

1. **Parallel read-only tool execution** — `read_file`, `glob_search`, `grep_search` run concurrently when batched in one turn (jcode parity pattern 2 fuller form). Serial-write tools (`write_file`, `bash`) still serialize.
2. **Prompt caching** — Anthropic SDK `cache_control` ephemeral blocks on the static system prompt + tool definitions. Operator sees `cache_read_input_tokens` rise across turns; brain entry `claude-api` skill auto-applied per Anthropic docs.
3. **Thinking-panel render** — `thinking_delta` deltas accumulate into a dedicated Rich panel (gray-italic, collapsible) so reasoning is visible without flooding the assistant text track. Per brain entry pattern 1.
4. **Skill-file loader** — `~/.sinister/skills/*.md` and `D:/Sinister Sanctum/skills/*.md` with YAML frontmatter (name, description, allowed-tools) auto-register as `/skillname` slash commands. Shipped via `forge/skills.py::SkillRegistry`.
5. **BM25 memory recall** — `forge_memory_bridge.recall()` now re-orders the TF-IDF top-k with Okapi BM25 as a final pass (rank_bm25 dependency). Records carry both `_recall_score` (TF-IDF) and `_bm25_score`. jcode parity pattern 6.

## Rebuild

```bash
cd "D:/Sinister Sanctum/automations/build/forge-exe"
pyinstaller --clean --noconfirm RKOJ.spec
cp dist/RKOJ.exe "C:/Users/Zonia/Desktop/RKOJ.exe"
```

Build time: ~45 sec on the operator's box. Output: `dist/RKOJ.exe` (~29 MB).

## Pre-build setup (do once per fresh Python env)

```bash
pip install pyinstaller
pip install --force-reinstall --no-deps pyinstaller-hooks-contrib   # brain doctrine: pyinstaller-tomli-hook-missing
pip install jaraco.text jaraco.functools jaraco.context              # pkg_resources runtime hook needs these
pip install -e "D:/Sinister Sanctum/tools/sinister-cli"              # umbrella
pip install -e "D:/Sinister Sanctum/tools/sinister-login"
pip install -e "D:/Sinister Sanctum/tools/sinister-usage"
pip install -e "D:/Sinister Sanctum/tools/sinister-swarm"
pip install -e "D:/Sinister Sanctum/tools/forge-memory-bridge"
pip install -e "D:/Sinister Sanctum/tools/memory-graph-render"
pip install -e "D:/Sinister Sanctum/projects/sinister-forge/source"
```

## Files

| File | What it is |
|---|---|
| `RKOJ-entry.py` | The Python entry script PyInstaller bundles. Boot art, picker, EVE persona, launcher delegate. |
| `RKOJ.spec` | PyInstaller spec — hiddenimports, datas, excludes, console=True, icon. |
| `.gitignore` | Excludes `build/`, `dist/`, `*.log` — those are ephemeral artifacts. |

## Brain doctrine honored

- `pyinstaller-distutils-exclude-collision` — `distutils` NOT in excludes
- `exe-silent-crash-no-popup` — runtime crash-log hook in entry script
- `sanctum-shared-rename-pyinstaller-collision` — `collect_submodules` + `collect_data_files` for every package
- `pyinstaller-tomli-hook-missing` — pre-build force-reinstall of hooks-contrib
- `sinister-cli-subcommand-pattern` — every shipped sinister-X tool is bundled as a hidden import

## What to test after rebuild

1. `RKOJ.exe version` → enumerates 6 sinister tools + sinister-cli umbrella version.
2. `RKOJ.exe login providers` → 11-row provider wallet table.
3. `RKOJ.exe usage list` → 11-row endpoint registry.
4. `RKOJ.exe` (no args) → jcode-style `>` prompt; type a question, observe live `thinking_delta` + tool-use streaming. With `ANTHROPIC_API_KEY` set, the SDK direct path engages; without it, falls back to `claude -p`.
5. Memory smoke — `RKOJ.exe memory recall "test query"` should print top-k records with both `_recall_score` and `_bm25_score` fields (v0.7.0+ BM25 re-scoring).
6. Skills smoke — `RKOJ.exe` → `/skill list` lists shipped skills from `skills/*.md` + `~/.sinister/skills/*.md`.
7. Check `RKOJ.crash.log` next to the EXE if anything fails silently (sidecar log per `exe-silent-crash-no-popup` doctrine).
