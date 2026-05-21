> **Author:** RKOJ-ELENO :: 2026-05-21

# RKOJ Integration Map

How the components wire together into a single running `RKOJ.exe`.

## Process model

`RKOJ.exe` is a one-file PyInstaller bundle. On launch:

1. Bootstrap reads `MANIFEST.json` to know what's available.
2. Forge TUI is the default entrypoint (v1.0.0). `--shell` falls back to the v0.x `>` prompt.
3. The TUI hosts N agent panes; each pane is a `claude` (or `anthropic_direct`) subprocess.
4. The sidebar + ADB tab share the parent process and dispatch into per-pane back-ends.
5. The forge-memory-bridge runs in-proc — BM25 + TF-IDF + Ruflo agentdb stay hot for the session.
6. Sinister-* tools are invoked on demand via the `sinister-cli` dispatcher (subprocess or in-proc shim).
7. The Vault MCP (:5078) and Workstation FastAPI (:5077) run as sibling services when present.

## Wire diagram

```
                            ┌──────────────────────────────────────────┐
                            │              RKOJ.exe (EVE)              │
                            │                                          │
                            │   ┌──────────────────────────────────┐   │
                            │   │           Forge TUI              │   │
                            │   │ ┌──────────┬──────────┬────────┐ │   │
                            │   │ │ Sidebar  │  Pane(s) │ Memory │ │   │
                            │   │ │ Agents   │  claude  │ Panel  │ │   │
                            │   │ │ ADB tab  │  anth.   │  BM25  │ │   │
                            │   │ └────┬─────┴─────┬────┴───┬────┘ │   │
                            │   └────────│───────────│────────│─────┘   │
                            │            │           │        │         │
                            │   ┌────────▼───┐  ┌────▼─────┐  │         │
                            │   │ forge_     │  │ anthropic│  │         │
                            │   │ memory_    │  │ _direct  │  │         │
                            │   │ bridge     │  │  SDK     │  │         │
                            │   │ (BM25 +    │  │  loop    │  │         │
                            │   │  TF-IDF +  │  │ + cache  │  │         │
                            │   │  Ruflo)    │  │ + think  │  │         │
                            │   └────┬───────┘  └─────┬────┘  │         │
                            │        │                │       │         │
                            │   ┌────▼────────────────▼───────▼────┐    │
                            │   │      skill registry +            │    │
                            │   │      sinister-* tools            │    │
                            │   │  login usage swarm model vault   │    │
                            │   │  jcode-shim review chatbot ...   │    │
                            │   └────┬────────────────┬────────────┘    │
                            └────────│────────────────│─────────────────┘
                                     │                │
                            ┌────────▼───┐   ┌────────▼────┐
                            │ sinister-  │   │ Workstation │
                            │ vault MCP  │   │ FastAPI     │
                            │ :5078      │   │ :5077       │
                            └────────────┘   └─────────────┘
```

## Data paths

**User input** → Forge pane → `anthropic_direct.py` (SDK tool-use loop) or `claude` subprocess (jcode shim) → tools (skills + sinister-* + memory bridge) → response → pane → memory bridge (BM25 store) → journal JSONL → operator.

**Slash commands** → Forge command router → per-command handler (in-proc) → optional shell-out → TUI re-render.

**ADB events** → ADB tab → `sinister-phone-viewer` + scrcpy → device list → pane offers `/adb <op>` shorthand.

**Memory recall** → `forge_memory_bridge` → BM25 index (in-proc) → TF-IDF fallback → Ruflo `agentdb_hierarchical-recall` → cached slice injected into system prompt.

**Vault tap** → MCP client → `mcp__vault__*` over loopback → 1 TB collaborative store at `D:/sinister-vault/`.

**Swarm spawn** → sinister-swarm CLI → Ruflo `swarm_init` + `agent_spawn` → spawned panes register back as Forge agents.

## Boot sequence

1. `RKOJ.exe` reads `MANIFEST.json` (bundled at build time from `projects/rkoj/MANIFEST.json`).
2. Loads enabled components in this order: term → forge → memory bridge → skill registry → bots index → tool dispatcher.
3. Starts the TUI; sidebar Agents tab pre-populates from `_shared-memory/heartbeats/`.
4. Pane 0 opens to `/help` overlay by default (operator preference, v1.0.0).
5. `RKOJ.exe info` short-circuits before TUI; prints the manifest + version + persona.

## EVE persona thread

EVE is the operator-facing persona that owns every pane spawned by RKOJ. Heartbeats carry `"agent_identity": "EVE"`. Commit trailers in any auto-commit path use `Co-Authored-By: EVE (Sinister Sanctum orchestration agent)`. Per-lane spawn slugs (`sanctum`, `forge`, `term`, `apk`, `panel`, `freeze`, `rkoj`) are lane IDs — EVE is the voice behind all of them.

## Failure modes

- Vault MCP unreachable → memory bridge falls back to local BM25 only; banner in sidebar.
- Anthropic SDK auth missing → `--shell` mode still works; `sinister-login` printed as the fix.
- Skill load error → skill skipped, sidebar shows red badge, registry continues.
- ADB device gone → ADB tab dims; existing panes unaffected.
- Forge TUI crash → `RKOJ.exe --shell` is the always-on parachute.
