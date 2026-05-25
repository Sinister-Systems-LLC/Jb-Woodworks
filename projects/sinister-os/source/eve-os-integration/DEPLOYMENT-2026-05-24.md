# EVE-OS Integration — Deployment Notes (2026-05-24)

> Author: RKOJ-ELENO :: 2026-05-24
> Lane: `sinister-os` :: scope: post-Calamares first boot of Sinister OS

## TL;DR

When Calamares finishes installing Sinister OS and the operator reboots into the installed system, `sinister-eve.service` SHOULD already be enabled (the sinister-overlay `install.sh` step 8/9 dropped + enabled it during overlay apply). On first boot the unit auto-starts, listens on `127.0.0.1:7331` (HTTP) + `/run/sinister/eve.sock` (UNIX).

**One-line verify:**

```bash
systemctl status sinister-eve --no-pager && curl -s http://127.0.0.1:7331/health
```

**Full smoke test** (recommended; bundled with the install):

```bash
bash /usr/lib/sinister-eve/post-install-smoke.sh
```

## What got installed where

| File | Path on installed system | Mode | Owner |
|---|---|---|---|
| Wrapper (exec) | `/usr/local/bin/sinister-eve` | 0755 | root:root |
| Python prototype | `/usr/lib/sinister-eve/sinister-eve-mcp-bridge.py` | 0644 | root:root |
| systemd unit | `/etc/systemd/system/sinister-eve.service` | 0644 | root:root |
| Config (live) | `/etc/sinister/eve.toml` | 0644 | root:root |
| Config (example) | `/etc/sinister/eve.toml.example` | 0644 | root:root |
| MCP tool drop-ins | `/etc/sinister/mcp/*.json` | 0644 | root:root |
| Memory root | `/var/lib/sinister/memory/` | 0750 | eve:sinister |

Two MCP tools ship by default:
- `/etc/sinister/mcp/eve-cli.json` — EVE self-control (status / restart / etc.)
- `/etc/sinister/mcp/panel-control.json` — open URLs, switch tabs in Sinister Panel

## Post-boot verification (operator-runnable)

### 1) Service status

```bash
systemctl status sinister-eve --no-pager
```

Expect: `Active: active (running)`. The unit is `Type=notify`, so it only flips to `active` after the Python prototype emits the readiness notify back to systemd.

### 2) HTTP health check

```bash
curl -s http://127.0.0.1:7331/health
```

Expect a JSON body containing `ok`, `tools`, and `memory` keys, e.g.:

```json
{"ok": true, "tools": 2, "memory": {"root": "/var/lib/sinister/memory", "writable": true}}
```

### 3) If it failed

```bash
journalctl -u sinister-eve --no-pager | tail -30
```

Common causes:
- **`User=eve` missing.** The systemd unit declares `User=eve` + `Group=sinister`. The overlay creates the `sinister` group but does NOT create the `eve` user (that is a Calamares postinstall step / out-of-scope for branding overlay). Create with: `sudo useradd -r -g sinister -d /var/lib/sinister -s /usr/sbin/nologin eve`.
- **No `ANTHROPIC_API_KEY`.** The unit reads `/etc/sinister/eve.env` (mode 0640, root:sinister). Create with one line: `ANTHROPIC_API_KEY=sk-ant-...`. Without it the prototype falls back to ollama if configured, else logs WARN and runs intent-only mode.
- **TOML parse error.** Validate with `python3 -c "import tomllib; tomllib.load(open('/etc/sinister/eve.toml','rb'))"`.

## Configuration

The config lives at `/etc/sinister/eve.toml` and reloads on `SIGHUP` (the daemon registers a handler). To edit:

```bash
sudo $EDITOR /etc/sinister/eve.toml
sudo systemctl reload sinister-eve     # SIGHUP, no restart
```

Key knobs (full reference: `/etc/sinister/eve.toml.example`):

- `daemon.unix_socket` — peer-cred socket for in-host callers (default `/run/sinister/eve.sock`)
- `daemon.tcp_bind` — HTTP `/health` + JSON-RPC (default `127.0.0.1:7331`)
- `memory.root` — Layer-1 store root (default `/var/lib/sinister/memory`)
- `llm.anthropic.model` — fleet default `claude-opus-4-7`
- `auth.trusted_group` — UNIX socket peer-cred allow group (default `sinister`)

The daemon also reads three env vars (set by the systemd unit):

- `EVE_CONFIG=/etc/sinister/eve.toml`
- `EVE_MEMORY_ROOT=/var/lib/sinister/memory`
- `EVE_MCP_TOOL_DIR=/etc/sinister/mcp`

These override TOML values for the running process; operator can drop overrides into `/etc/systemd/system/sinister-eve.service.d/override.conf` instead of editing the shipped unit.

## Adding a new MCP tool

The daemon watches `/etc/sinister/mcp/*.json` (inotify + a 60s rescan as belt-and-suspenders). Drop a new JSON file and the tool appears at `/health` within 60s — no restart required.

Minimum schema (copy from `eve-cli.json`):

```json
{
  "name": "my-tool",
  "description": "What this tool does.",
  "command": ["/usr/local/bin/my-tool", "--json"],
  "subcommands": {
    "ping": { "args": [] }
  }
}
```

Install:

```bash
sudo install -m 0644 my-tool.json /etc/sinister/mcp/my-tool.json
# verify the daemon picked it up:
curl -s http://127.0.0.1:7331/health | grep -o '"tools":[0-9]*'
```

To remove a tool, delete the JSON file and the daemon drops it on the next scan.

## Uninstall

The overlay's `uninstall.sh` step 8 reverses everything in `install_eve`:

```bash
sudo bash projects/sinister-os/source/sinister-overlay/uninstall.sh
```

What it does:
- `systemctl disable --now sinister-eve.service`
- Removes `/etc/systemd/system/sinister-eve.service`, `/usr/local/bin/sinister-eve`, `/usr/lib/sinister-eve/`
- Removes shipped MCP drop-ins (`eve-cli.json`, `panel-control.json`); leaves operator-added ones
- Empties `/etc/sinister/mcp` + `/etc/sinister` if nothing else remains
- Removes the `sinister` group if no users belong to it
- **Preserves `/var/lib/sinister/memory`** — the brain is sacred; delete manually if intended

## Where the Rust port will land (P3.5)

The Python prototype is the validation layer. The Rust port (`projects/sinister-os/source/sinister-eve-rs/`, scaffolded later in P3) will produce a single static binary at `/usr/bin/sinister-eve`, replacing the wrapper at `/usr/local/bin/sinister-eve`. The systemd unit's `ExecStart=` will be flipped from `/usr/local/bin/sinister-eve` to `/usr/bin/sinister-eve` at that point — single-line patch, no overlay rebuild needed.

## Cross-references

- Prototype source: `projects/sinister-os/source/eve-os-integration/scaffold/sinister-eve-mcp-bridge.py`
- systemd unit: `projects/sinister-os/source/eve-os-integration/scaffold/sinister-eve.service`
- Wrapper: `projects/sinister-os/source/eve-os-integration/scaffold/usr/local/bin/sinister-eve`
- Config example: `projects/sinister-os/source/eve-os-integration/scaffold/etc/sinister/eve.toml.example`
- MCP tools: `projects/sinister-os/source/eve-os-integration/scaffold/etc/sinister/mcp/*.json`
- Smoke test: `projects/sinister-os/source/eve-os-integration/scaffold/post-install-smoke.sh`
- Overlay installer step 8: `projects/sinister-os/source/sinister-overlay/install.sh` (`install_eve` function)
- Overlay uninstaller step 8: `projects/sinister-os/source/sinister-overlay/uninstall.sh` (`uninstall_eve` function)
