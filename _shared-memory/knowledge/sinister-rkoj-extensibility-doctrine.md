<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Sinister RKOJ :: extensibility doctrine

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Status:** canonical (operator directive 2026-05-21 — *"we have full code i want it to function like jcode but be ours and we can foreever expand. with featres we have that we can add"*)

The RKOJ desktop app (PyQt6 native, frameless, Sinister Panel-style) is the operator's primary surface. Per operator: function like jcode, but **fully ours, forever-expandable**. Every Sinister feature we build is a Sanctum extension that plugs into RKOJ.

## Layers

```
┌─────────────────────────────────────────────────────────────┐
│  CHROME              (PyQt6 native window + frameless)     │
│  ├─ sidebar.py       (4-section nav, mascot, status)        │
│  ├─ header.py        (chip-tabs + clock + actions)          │
│  ├─ ribbon.py        (Excel-style action ribbon)            │
│  └─ kpis.py          (4 live counters)                      │
├─────────────────────────────────────────────────────────────┤
│  PANES               (one per chip-tab, hot-swap on click)  │
│  ├─ agents_tab.py    (niri scroll of jcode-form terminals)  │
│  ├─ phones_tab.py    (ADB fleet + scrcpy + logcat tail)     │
│  └─ workstation_tab.py (action card grid)                   │
├─────────────────────────────────────────────────────────────┤
│  AGENT RUNNER        (per-card, persistent across turns)    │
│  ├─ ClaudeRunner     (QProcess wrapping claude -p)          │
│  ├─ SlashIntercept   (client-side first-token routing)      │
│  └─ Persona inject   (EVE identity in opening prompt)       │
├─────────────────────────────────────────────────────────────┤
│  EXTENSIONS          (plugin layer — forever-expandable)    │
│  ├─ extensions/<slug>/                                      │
│  │  ├─ manifest.json (id, name, hooks)                      │
│  │  ├─ handler.py    (the actual implementation)            │
│  │  └─ README.md     (operator-facing doc)                  │
│  └─ Discovery: scan projects/rkoj/source/extensions/        │
│     at startup + register each manifest's hooks.            │
└─────────────────────────────────────────────────────────────┘
```

## Plugin manifest schema

`projects/rkoj/source/extensions/<slug>/manifest.json`:

```json
{
  "id": "sinister-vault-tab",
  "version": "0.1.0",
  "author": "RKOJ-ELENO",
  "hooks": {
    "sidebar_nav":   { "section": "OPERATIONS", "label": "Vault", "icon": "vault" },
    "header_tab":    { "key": "vault", "glyph": "⛀" },
    "ribbon_group":  { "name": "VAULT", "buttons": [ ... ] },
    "kpi_tile":      { "label": "VAULT USED", "source": "vault.usage()" },
    "slash_command": { "name": "/vault", "summary": "..." },
    "agent_pane":    null,
    "phone_pane":    null,
    "workstation_card": { "title": "Open Vault :5078", "action": "vault.open()" }
  },
  "imports": [ "tools/sinister-vault/sinister_vault" ],
  "requires_python": ">=3.10"
}
```

Each hook is OPTIONAL. An extension can register one hook (e.g. just add a sidebar nav item) or many.

## Bundled Sanctum extensions (ship-in-EXE)

| Slug | Hooks | Description |
|---|---|---|
| `vault`         | sidebar, header, kpi, workstation, slash | sinister-vault 1 TB collab store (:5078) |
| `swarm`         | sidebar, header, slash | multi-agent coordinator (`/swarm spawn N`) |
| `memory`        | sidebar, kpi, slash | forge-memory-bridge BM25 recall (`/memory`) |
| `mermaid`       | ribbon, slash | memory-graph-render (`/mermaid file <path>`) |
| `watchdog`      | sidebar, slash | sinister-watchdog auto-online (`/watchdog status`) |
| `skills`        | sidebar, slash | SkillRegistry (`/skill list|run <name>`) |
| `mcp`           | sidebar, slash | MCP client (`/mcp list|tools|call`) |
| `model`         | ribbon, slash | sinister-model picker (`/model list|set`) |
| `backup`        | ribbon, slash | sanctum-backup (`/backup now`) |
| `login`         | header, slash | sinister-login 11-provider wallet (`/login providers`) |
| `usage`         | header, slash | sinister-usage token tracker (`/usage list`) |
| `diagnose`      | slash | sinister-diagnose health checker (`/diagnose`) |

## Slash command extension pattern

Inside a jcode-form terminal (agent pane), the operator types `/<command> [args]`. The dispatch:

1. **Client intercept** (Python QObject in PyQt6 agent_tab):
   - If `/help|/clear|/save|/resume|/create|/effort|/fast|/git|/version|/info|/context`: handle locally via `forge.commands._cmd_<name>` (imported from existing forge package).
   - If `/skill <name>`: route to `SkillRegistry` → run skill → display.
   - If `/mcp ...`: route to `mcp_client.dispatch` → call MCP server tool → display result.
   - Otherwise: send to claude subprocess as raw turn.

2. **Server-side** (the claude subprocess):
   - Receives the prompt; responds in natural EVE-style with possible tool-use blocks.

3. **Plugin command discovery**:
   - At startup, scan `extensions/<slug>/manifest.json` for `hooks.slash_command`.
   - Register each extension's slash command into the same intercept dispatch.

## Adding a new extension (recipe)

```bash
# 1. scaffold
cd projects/rkoj/source/extensions
mkdir my-thing && cd my-thing
cat > manifest.json << 'EOF'
{ "id": "my-thing", "version": "0.1.0", "author": "RKOJ-ELENO",
  "hooks": { "slash_command": { "name": "/mything", "summary": "what it does" } } }
EOF
cat > handler.py << 'EOF'
def handle(args, pane, app):
    return "[my-thing] ok"
EOF

# 2. rebuild EXE
cd ../..
pyinstaller --clean --noconfirm RKOJ.spec

# 3. operator clicks Desktop RKOJ.lnk → new extension live
```

No code changes needed in chrome/panes — the manifest-driven discovery picks it up.

## Anti-patterns

- ❌ Hardcoding a tool's UI in `agents_tab.py`. Use an extension hook.
- ❌ Adding a slash command directly to `agents_tab.py`'s intercept. Register via manifest.
- ❌ Inlining color hex codes. Always go through `theme.py` tokens.
- ❌ Spawning subprocesses with `subprocess.Popen` from a QWidget. Use `QProcess` so Qt's event loop handles signals.

## Compose-with

- `_shared-memory/knowledge/agent-identity-eve.md` — EVE persona doctrine (RKOJ binds to this).
- `_shared-memory/knowledge/auto-mode-launcher-pattern.md` — autonomous-loop pattern used by /create + /resume agents.
- `_shared-memory/knowledge/multi-agent-branch-contention-isolation-pattern.md` — when multiple Sanctum agents touch the same source.
- `_shared-memory/plans/sanctum-d-drive-final-reorg-2026-05-21/jcode-feature-audit.md` — feature parity matrix vs jcode binary.

## Future expansion ideas (operator queue)

- **VS Code integration** — extension shim that lets RKOJ agents drive an open VS Code instance via `code --command`.
- **Inline Mermaid render in agent pane** — Qt's QSvgWidget loads mermaid SVG output inline.
- **MCP tools quick-call palette** — Ctrl+Shift+K opens picker of every MCP tool across all configured servers; click runs + returns JSON to pane.
- **Per-agent budget overlay** — token-count badge in the agent card header, lights up red when nearing pane's budget cap.
- **Heartbeat-loss alert toast** — when a watchdog-tracked agent goes stale > 5 min, RKOJ toast notifies + offers one-click revive button.

Operator picks any of the above + drops an extension into `extensions/<slug>/` + rebuild. RKOJ grows.
