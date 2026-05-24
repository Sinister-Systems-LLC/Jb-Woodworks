# EVE-as-OS Integration — Design Document

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Scope:** P3-prep design pass. Read once, approve, then we open `agent/sinister-os/p3-eve-shell-<date>` and build the Rust daemon.
> **Status:** Design + runnable Python prototype. NO host deployment in this pass.
> **Companion code:** `scaffold/` (this folder)

---

## 0. Operator directive (verbatim 2026-05-24)

> *"i want everything to have direct communication to claude. like the entire os has its own api/mcp server that claude is built direct into. well outr claude system memory how it works all of that. the perfect system to run and do evrything i need to do"*

Decoded into requirements:

| Op-stated need | Concrete requirement |
|---|---|
| "direct communication to claude" | Every app on the OS reaches EVE over a single well-known endpoint. No per-app SDK boilerplate. |
| "entire os has its own api/mcp server" | A system-level daemon listens on a UNIX socket + loopback TCP and speaks both an HTTP/JSON API and MCP. |
| "claude is built direct into" | EVE is not a userland convenience — it is a `systemd` unit that starts at boot, survives compositor crashes, has root-equivalent on a curated allowlist. |
| "our claude system memory how it works" | The Sanctum brain (`_shared-memory/`) ports into the OS as `/var/lib/sinister/memory/` so EVE remembers across reboots, sessions, and apps. |
| "the perfect system" | Reproducible, no telemetry, no UAC prompts, recoverable, voice-driven when needed, hotkey-driven when speed matters. |

---

## 1. The three layers

```
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 3 — Tools & Apps                                          │
│  eve CLI · Panel (web UI) · sinister-voice · sinister-vault     │
│  any user-installed app that drops a /etc/sinister/mcp/*.json   │
└────────────────────┬────────────────────────────────────────────┘
                     │  MCP (stdio or HTTP) + REST /v1/*
┌────────────────────▼────────────────────────────────────────────┐
│ LAYER 2 — EVE Daemon (sinister-eve.service)                     │
│  • Discovers MCP tool registrations from /etc/sinister/mcp/     │
│  • Routes /v1/intent/dispatch → matching tool                   │
│  • Talks to Anthropic API (cloud) or Ollama (local) for LLM     │
│  • UNIX socket /run/sinister/eve.sock (in-host, low-latency)    │
│  • TCP 127.0.0.1:7331 (loopback, for browser/HTTP-only callers) │
└────────────────────┬────────────────────────────────────────────┘
                     │  File I/O (atomic write, fsync, fcntl-lock)
┌────────────────────▼────────────────────────────────────────────┐
│ LAYER 1 — Memory (/var/lib/sinister/memory/)                    │
│  heartbeats/ · knowledge/ · resume-points/ · inbox/             │
│  cross-agent/ · PROGRESS/ · operator-utterances.jsonl           │
│  (port of D:\Sinister Sanctum\_shared-memory\)                  │
│  Optional sync to /sinister-vault/ for multi-machine            │
└─────────────────────────────────────────────────────────────────┘
```

The three layers are deployable independently. You can boot a machine with only Layer 1 + Layer 2 (no Layer 3 tools) and EVE still answers questions from the brain. You can add a Layer 3 tool at any time by dropping a JSON file — no daemon restart, no recompile.

---

## 2. Layer 2 in detail — the EVE Daemon

### 2.1 Process model

- **Binary:** `/usr/bin/sinister-eve` (Rust in production; Python prototype in this scaffold).
- **Unit:** `sinister-eve.service` (`Type=notify`, `Restart=on-failure`, `User=eve`, `Group=sinister`).
- **Runtime dir:** `/run/sinister/` (systemd-managed; mode 0750, group `sinister`).
- **State dir:** `/var/lib/sinister/memory/` (mode 0750, group `sinister`).
- **Config:** `/etc/sinister/eve.toml` (the only file the operator hand-edits).

### 2.2 Listening surface

| Endpoint | Protocol | Purpose |
|---|---|---|
| `/run/sinister/eve.sock` | UNIX socket + HTTP/1 | In-host calls from `eve` CLI, Panel, voice bridge. Fastest. |
| `127.0.0.1:7331` | TCP + HTTP/1 | Loopback only. Browsers, dev tools, anything that hates UNIX sockets. |
| `/run/sinister/mcp.sock` | UNIX socket + JSON-RPC (MCP) | Native MCP clients (Claude Code, future MCP-aware apps). |

Both HTTP endpoints serve the same REST surface (`/v1/*`). The MCP endpoint exposes the same tools via the standard MCP JSON-RPC.

### 2.3 REST surface

| Path | Method | Purpose |
|---|---|---|
| `/health` | GET | Liveness + readiness + LLM-backend availability. |
| `/v1/tools/list` | GET | Every registered MCP tool, with input schemas. |
| `/v1/tools/call` | POST | `{tool, args}` → run the tool, return stdout/exit-code. |
| `/v1/memory/get` | GET `?key=<path>` | Read a memory slot. |
| `/v1/memory/set` | POST `{key, value}` | Atomic write (temp + rename + fsync). |
| `/v1/memory/list` | GET `?prefix=<path>` | Directory listing under memory root. |
| `/v1/intent/dispatch` | POST `{intent: "..."}` | Match intent to tool(s); execute matching tool with extracted args. Falls back to LLM-mediated tool-call if no regex matches. |
| `/v1/llm/chat` | POST `{messages, model?}` | Direct passthrough to the active LLM backend (Anthropic or Ollama). |
| `/v1/heartbeat` | POST | Apps signal liveness; daemon writes to `memory/heartbeats/<slug>.json`. |

### 2.4 LLM backend selection

```
1. If ANTHROPIC_API_KEY set + reachable  → claude-opus-4-7 (per fleet doctrine)
2. Else if OLLAMA_HOST reachable          → llama3.1:70b or operator-chosen local model
3. Else                                    → 503 with explanation; intent-dispatch still works for regex-matched intents
```

Cloud-first by default. Operator can flip to local-first in `eve.toml` for offline / privacy mode.

---

## 3. Layer 1 in detail — the memory port

The brain at `D:\Sinister Sanctum\_shared-memory\` is the operator's lived knowledge graph. Porting it into the OS means EVE on Sinister OS knows what EVE on Windows knew.

| Sanctum path | Sinister OS path | Notes |
|---|---|---|
| `_shared-memory/heartbeats/<slug>.json` | `/var/lib/sinister/memory/heartbeats/<slug>.json` | App liveness. Apps POST `/v1/heartbeat`. |
| `_shared-memory/knowledge/*.md` + `_INDEX.md` | `/var/lib/sinister/memory/knowledge/` | The brain. Read-mostly. |
| `_shared-memory/resume-points/<lane>/*.json` | `/var/lib/sinister/memory/resume-points/<lane>/` | Cross-session continuity. |
| `_shared-memory/inbox/<slug>/*.json` | `/var/lib/sinister/memory/inbox/<slug>/` | Inter-agent / inter-app message drops. |
| `_shared-memory/cross-agent/*.md` | `/var/lib/sinister/memory/cross-agent/` | Broadcast log. |
| `_shared-memory/PROGRESS/<lane>.md` | `/var/lib/sinister/memory/PROGRESS/<lane>.md` | Append-only milestone log. |
| `_shared-memory/operator-utterances.jsonl` | `/var/lib/sinister/memory/operator-utterances.jsonl` | Every operator utterance. |

Full mapping (read pattern × write pattern × sync strategy) lives in `brain-port-map.md`.

Sync to the Sinister Vault daemon (`tools/sinister-vault-daemon/`) is optional. With vault sync enabled, the operator's laptop and desktop share one brain.

---

## 4. Layer 3 — how apps register

Any app drops one JSON file into `/etc/sinister/mcp/<app>.json`:

```json
{
  "tool": "eve-cli",
  "description": "The eve command-line client",
  "exec": "/usr/bin/eve",
  "subcommands": [
    {"name": "status", "args": [], "description": "Show daemon status"},
    {"name": "up",     "args": [],  "description": "Bring service up"},
    {"name": "down",   "args": [],  "description": "Take service down"}
  ],
  "intents": [
    {"regex": "^(restart|reboot) ?eve$", "subcommand": "restart"},
    {"regex": "^status$", "subcommand": "status"}
  ]
}
```

Daemon auto-discovers the file (inotify watcher), validates the schema, and exposes each subcommand as an MCP tool. The operator can list every available tool with:

```
$ eve tools
eve-cli.status      Show daemon status
eve-cli.up          Bring service up
eve-cli.down        Take service down
panel-control.tab.open    Open a Panel tab
panel-control.tab.refresh Refresh the active Panel tab
…
```

Two example registrations ship in `scaffold/etc/sinister/mcp/`:
- `eve-cli.json` — the EVE CLI itself
- `panel-control.json` — the Sinister Panel web UI

---

## 5. The "operator says X → every app reacts" flow

```
1.  Operator: "EVE, open my JB Woodworks dashboard"
       │
       ▼
2.  sinister-voice (user service) wake-word triggers, transcribes via whisper.cpp
       │
       │  POST UNIX-socket /run/sinister/eve.sock /v1/intent/dispatch
       │  { "intent": "open my JB Woodworks dashboard" }
       ▼
3.  EVE daemon
       a. Regex pass over registered intents — no match for free-form
       b. LLM-mediated: build tool-call prompt with /v1/tools/list result, ask claude-opus-4-7
       c. Claude returns tool_use: panel-control.tab.open(url="https://jb-woodworks.local")
       d. Daemon executes the tool, returns result
       │
       ▼
4.  Panel opens the tab. Daemon writes the interaction to
    /var/lib/sinister/memory/operator-utterances.jsonl + memory/cross-agent/<ts>-voice.md
       │
       ▼
5.  Future invocations: regex now matches first because we learned the intent
```

Three things make this materially better than Cortana / Siri:

1. **Memory persists** across reboots and across apps — the daemon writes every interaction to the brain, and the brain is queryable by the next session.
2. **Tools are pluggable without daemon changes** — JSON drop-in instead of recompiling the OS shell.
3. **The LLM is replaceable** — Anthropic today, Ollama tomorrow, anything else next year. The MCP contract is stable.

---

## 6. Auth + escalation ladder

Matches `source/eve-control/README.md` so the P3 daemon and this OS-integration layer land on the same auth model.

```
Caller (eve CLI, Panel, voice)
    │
    │  UNIX socket peer-cred check → must be uid in group `sinister`
    ▼
EVE daemon
    │
    ├── Tool execution
    │     ├── If tool.exec lives in /usr/bin/eve-* → run as user `eve`
    │     └── If tool.requires_root → `sudo -n /usr/bin/<tool> …`
    │           (sudoers allowlist at /etc/sudoers.d/eve, NOPASSWD,
    │            curated commands only: apt, pacman, systemctl, nmcli,
    │            xdotool, mount, umount, ip, ufw, etc.)
    │
    ├── LLM call
    │     └── HTTPS to api.anthropic.com (cloud) or unix:/ollama/sock (local)
    │
    └── Memory write
          └── /var/lib/sinister/memory/ (always owned by eve:sinister)
```

Anything NOT in the sudoers allowlist requires the operator to hotkey-confirm via `eve-overlay` (the GTK4 prompt in the P3 daemon). That's the entire escalation ladder. No nested UAC, no popup chains.

---

## 7. Comparison — Sinister OS + EVE vs the assistant-OS field

| Capability | Cortana (Windows) | Siri (macOS) | Alexa Desktop | Microsoft Copilot | **Sinister OS + EVE** |
|---|---|---|---|---|---|
| System-service-level integration | partial | partial | no | partial (Windows 11) | **yes** (`sinister-eve.service`, PID 1 child) |
| Persistent cross-session memory | no (per-query) | per-app, opaque | minimal | conversation-window only | **yes** (`/var/lib/sinister/memory/`, structured, queryable, versionable) |
| Multi-app intent routing | very limited | apps must implement App Intents | smart-home only | Windows + Office only | **yes** (any app drops a JSON file) |
| Pluggable LLM backend | no (locked to Cortana stack) | no | no | no | **yes** (Anthropic, Ollama, llama.cpp, anything that speaks OpenAI-shape API) |
| Voice + hotkey + CLI parity | mostly voice | mostly voice | voice-only | mostly chat | **all four** + REST + MCP |
| Telemetry to vendor | mandatory | mandatory | mandatory | mandatory | **none** (cloud LLM calls go to Anthropic on operator's API key; daemon itself ships nothing) |
| Operator owns the source | no | no | no | no | **yes** (every line ships in `source/`) |
| Agent-of-agents (spawning sub-agents) | no | no | no | no | **yes** (Sanctum bot fleet pattern ports over) |
| Custom tool authoring | requires SDK + signing | requires Xcode + entitlements | requires AWS dev acct | requires Power Platform | **drop a JSON file in /etc/sinister/mcp/** |

The differentiator is not "EVE is smarter" — Claude is just an LLM. The differentiator is **the OS is built around the assumption that an LLM agent owns it**, instead of bolted on after the fact.

---

## 8. What this design intentionally defers

| Deferred | Reason | When |
|---|---|---|
| The Rust daemon implementation | Python prototype proves the surface; Rust gets us performance + memory-safety for a 24/7 PID-1-child. | P3 (operator gates) |
| The GTK4 `eve-overlay` (confirm prompt) | Belongs to `source/eve-control/`; that's the P3 lane. | P3 |
| ML-embedding intent matching | Regex covers the operator's first 50 routines; embeddings are an optimization. | P4 |
| Multi-machine vault sync of memory | Single-machine first; sync after the brain settles. | P4 |
| polkit policy file | NOPASSWD sudoers is simpler and covers every curated command. polkit comes in if we need finer-grained per-action auth. | P4 |
| SELinux / AppArmor profile | Distro-base decision (CachyOS = Arch = AppArmor available). Profile after the daemon stabilizes. | P4 |
| DBus surface for KDE/Hyprland desktop-integration | `sinister-eve.service` could expose `org.sinister.eve` on the session bus so Hyprland binds can call `dbus-send`. Nice-to-have. | P4 |

---

## 9. What the operator approves in one read to unblock the Rust phase

By reviewing this file + `brain-port-map.md` + running the Python prototype in the CachyOS VM, the operator can sign off on:

1. The three-layer split (daemon · MCP-server · memory) — yes / no
2. The endpoint plan (`/run/sinister/eve.sock` + `127.0.0.1:7331` + `/run/sinister/mcp.sock`) — yes / no
3. The JSON drop-in tool-registration format (`/etc/sinister/mcp/<tool>.json`) — yes / no
4. The brain-port mapping (`_shared-memory/` → `/var/lib/sinister/memory/`) — yes / no
5. The sudoers-NOPASSWD auth model — yes / no
6. Cloud-LLM-first (Anthropic), local-LLM-fallback (Ollama) — yes / no

If all six are "yes," EVE opens `agent/sinister-os/p3-eve-shell-<date>` and ports the prototype to Rust. The Rust crate layout already lives at `source/eve-control/README.md`.

---

## 10. Cross-references

- Phased plan: `plans/master-plan-2026-05-24.md` (Phases P0-P5)
- P3 daemon home (gated, untouched in this pass): `source/eve-control/`
- Sanctum brain doctrine: `D:\Sinister Sanctum\_shared-memory\knowledge\_INDEX.md`
- Sanctum MCP heartbeat/inbox (the pattern we mirror in `/v1/heartbeat`): `tools/sinister-bus.mcp` (Sanctum master)
- Vault daemon (optional Layer 1 sync target): `tools/sinister-vault-daemon/`
- Voice surface (Layer 3 client): `source/sinister-overlay/` (when populated) + `sinister-voice` package on the ISO

---

## 11. Verification commands run on this scaffold

```
python -c "import ast; ast.parse(open('scaffold/sinister-eve-mcp-bridge.py').read())"
bash -n scaffold/usr/local/bin/sinister-eve
python -c "import json; json.load(open('scaffold/etc/sinister/mcp/eve-cli.json'))"
python -c "import json; json.load(open('scaffold/etc/sinister/mcp/panel-control.json'))"
python -c "import tomllib; tomllib.load(open('scaffold/etc/sinister/eve.toml.example','rb'))"
```

All pass in this commit. See `README.md` for runnability of the prototype on the booted CachyOS VM.
