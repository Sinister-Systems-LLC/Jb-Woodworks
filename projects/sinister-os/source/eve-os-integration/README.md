# source/eve-os-integration/

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Status:** Design + runnable Python prototype. Pre-P3. Operator reviews + approves; then we open `agent/sinister-os/p3-eve-shell-<date>` and port to Rust.
> **Parent lane:** `agent/sinister-os/p0-spec-2026-05-24`
> **Not to be confused with:** `source/eve-control/` (the P3-gated Rust daemon). This folder is the OS-integration design + prototype that unblocks that folder.

## What this is

The system that puts EVE directly into Sinister OS as a first-class system service, so every app on the OS reaches Claude through one well-known endpoint instead of each app shipping its own SDK boilerplate.

Three layers (full detail in `DESIGN.md`):

1. **EVE daemon** — `sinister-eve.service`, runs at boot, exposes UNIX socket + loopback HTTP + MCP.
2. **MCP server** — auto-discovers tool registrations from `/etc/sinister/mcp/*.json`; any app drops a JSON file to plug in.
3. **Memory layer** — the Sanctum brain (`_shared-memory/`) ported to `/var/lib/sinister/memory/`; mapping in `brain-port-map.md`.

## What ships in this commit

| File | What it is |
|---|---|
| `DESIGN.md` | Architecture doc. Operator reads this once + approves to unblock the Rust phase. |
| `brain-port-map.md` | Per-slot mapping of `_shared-memory/<thing>/` → `/var/lib/sinister/memory/<thing>/` with read/write/sync rules. |
| `scaffold/sinister-eve.service` | The systemd unit (production-shape, hardened). |
| `scaffold/sinister-eve-mcp-bridge.py` | Runnable Python prototype of the daemon. Single file, ~430 lines. |
| `scaffold/usr/local/bin/sinister-eve` | Bash wrapper that exec's the prototype. Real install replaces with Rust binary. |
| `scaffold/etc/sinister/eve.toml.example` | Daemon config (model + memory + intent regexes). |
| `scaffold/etc/sinister/mcp/eve-cli.json` | Example tool registration: the `eve` CLI. |
| `scaffold/etc/sinister/mcp/panel-control.json` | Example tool registration: the Panel web UI. |

## Run the prototype on the booted CachyOS VM

```
# In the VM, with the source/eve-os-integration/ folder available (via virtfs / scp / git):

cd source/eve-os-integration/scaffold/
python3 sinister-eve-mcp-bridge.py --dev

# in another shell on the VM:
curl -s http://127.0.0.1:7331/health | python3 -m json.tool
curl -s http://127.0.0.1:7331/v1/tools/list | python3 -m json.tool
curl -s -X POST http://127.0.0.1:7331/v1/intent/dispatch \
    -H 'content-type: application/json' \
    -d '{"intent":"status"}' | python3 -m json.tool
curl -s -X POST http://127.0.0.1:7331/v1/memory/set \
    -H 'content-type: application/json' \
    -d '{"key":"knowledge/hello.md","value":"# hello\nfrom eve\n"}' | python3 -m json.tool
curl -s 'http://127.0.0.1:7331/v1/memory/get?key=knowledge/hello.md' | python3 -m json.tool
```

In `--dev` mode the prototype writes to `${XDG_RUNTIME_DIR}/sinister-eve-dev/memory/` (or a temp dir) instead of `/var/lib/sinister/memory/`, so it runs as the regular operator without `sudo`.

## Working in prototype vs deferred to Rust

| Capability | Python prototype | Rust (P3) |
|---|---|---|
| HTTP REST surface (`/v1/*`) | yes | yes |
| MCP JSON-RPC surface | no (REST only) | yes |
| Tool registration discovery (inotify) | poll-load on startup | inotify watcher + poll fallback |
| Memory atomic writes (fsync + rename) | yes | yes |
| Intent regex matching | yes | yes |
| LLM call (Anthropic / Ollama) | stub (does not make network calls) | real client |
| systemd `Type=notify` integration | no | yes (via libsystemd / sd-notify) |
| UNIX-socket peer-cred auth | no | yes |
| Tool exec sandboxing (cgroup / namespaces) | no | yes |
| Vault sync mirror | no | yes |
| HTTP→tool proxy for `transport: "http"` tools | dry-run report only | real proxy |

## What the operator approves in one read

By reading `DESIGN.md` + `brain-port-map.md` (and optionally running the prototype on the CachyOS VM), the operator can sign off on:

1. The three-layer split
2. The endpoint plan
3. The JSON drop-in tool-registration format
4. The brain-port mapping
5. The sudoers-NOPASSWD auth model
6. Cloud-LLM-first / local-LLM-fallback ordering

Six yes → EVE opens `agent/sinister-os/p3-eve-shell-<date>` and ports the prototype to Rust. The Rust crate layout is already documented at `source/eve-control/README.md`.

## Verification status (this commit)

| Check | Status |
|---|---|
| `python -c "import ast; ast.parse(open('scaffold/sinister-eve-mcp-bridge.py').read())"` | PASS |
| `bash -n scaffold/usr/local/bin/sinister-eve` | PASS |
| `python -c "import json; json.load(open('scaffold/etc/sinister/mcp/eve-cli.json'))"` | PASS |
| `python -c "import json; json.load(open('scaffold/etc/sinister/mcp/panel-control.json'))"` | PASS |
| `python -c "import tomllib; tomllib.load(open('scaffold/etc/sinister/eve.toml.example','rb'))"` | PASS |
| `systemd-analyze verify scaffold/sinister-eve.service` | unavailable on Windows host; text-parse of standard fields shows all required directives present |
| Cross-references in `DESIGN.md` resolve to existing files in this folder | PASS |

## Cross-references

- `plans/master-plan-2026-05-24.md` (Phase P3)
- `source/eve-control/README.md` (Rust daemon home, P3-gated)
- `D:\Sinister Sanctum\_shared-memory\knowledge\agent-identity-eve.md` (EVE persona doctrine)
- `D:\Sinister Sanctum\_shared-memory\knowledge\sanctioned-bypasses-doctrine-2026-05-21.md` (auth doctrine)
