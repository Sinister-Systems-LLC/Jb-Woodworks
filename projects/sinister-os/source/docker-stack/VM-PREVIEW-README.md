# Sinister OS — VM PREVIEW (Phase 1A)

> **Author:** RKOJ-ELENO :: 2026-05-25
> **Phase:** 1A — operator-review preview, before the real ISO ships
> **Operator directive that asked for this:** *"create a plan to complete everything i have said to do then open the OS in VM so i can test things and tell you what to do then we can talk about pushing to laptop"*
> **Plan:** `projects/sinister-os/plans/EXECUTION-PLAN-2026-05-25/plan.md`

## What this is

A **same-day operator-bootable preview** of Sinister OS, running in a Docker container, viewed in your browser at `http://localhost:6080`. NOT the real OS — that's Phase 1B (Day 1-2). This is so you can click around, file feedback, and we iterate without you having to wait for the full ISO build.

## What you need

- **Docker Desktop** (Windows / Mac). Most operators have this already.
- About **2 GB** disk free for the image.
- About **90 seconds** for first-run build (rebuilds are ~30s).

That's it. No VirtualBox, no VMware, no QEMU, no ISO. Browser is the VM client.

## Run it

From this directory (`projects/sinister-os/source/docker-stack/`):

```
python eve-vm.py up
```

That's the whole command. Within ~90 seconds:

1. Browser opens to `http://localhost:6080/vnc.html?autoconnect=1&resize=remote`.
2. You see a purple-themed i3 desktop with an xterm window already open showing the Sinister banner.
3. You type commands. Try these in order:

```
eve status
eve chat "hello — what can you do?"
eve game-mode arm
eve game-mode status
eve actions --limit 5
eve info
```

## What works in the preview

| Surface | Status |
|---|---|
| Desktop (purple, tiled) | REAL i3 + Xvfb |
| `eve` CLI | REAL Python client talking to daemon stub |
| EVE daemon | STUB Python HTTP — state machine, action log, intent ack |
| EVE-LLM bridge / chat | STUB Python + mock-panel returning canned replies |
| Game mode toggle | UI-state stub (cycles DISARMED → ARMING → ARMED) |
| Sinister Panel | REAL via `compose.panel-shell.yml` at `http://localhost:8443/` |
| Sanctum tree access | REAL — operator's `D:\Sinister Sanctum\` mounted read-only at `/srv/sinister-sanctum` |

## What's NOT in this preview

| Surface | Why deferred |
|---|---|
| Hyprland (Wayland) | Needs real GPU + Wayland — Phase 1B real ISO |
| sinister-voice | Needs mic access — Phase 2 |
| GPU arbiter | Needs real NVIDIA — Phase 2 |
| Sinister Browser auto-relogin | Needs real Playwright + Vault — Phase 2 |
| Real Anthropic chat | Stub uses canned replies; real bridge needs license key — Phase 2 |
| First-boot wizard | Container has no first-boot concept — Phase 1B real ISO |

## Operator commands

| Action | Command |
|---|---|
| Start preview | `python eve-vm.py up` |
| Stop preview | `python eve-vm.py down` |
| Stop + wipe state | `python eve-vm.py down -v` |
| Rebuild from scratch | `python eve-vm.py rebuild` |
| Show running state | `python eve-vm.py status` |
| Tail logs | `python eve-vm.py logs` |
| T0 smoke test | `python eve-vm.py test --suite t0` |

## What to file as feedback

When you're poking around and find something to fix, just paste in this session:

- **Screenshot** of the issue (browser screenshot is fine)
- **One-line description** of what's wrong / what you want
- **Optional:** what you tried

Examples of fixable feedback:
- *"The xterm banner is too wide on my monitor"*
- *"I want the game-mode toggle to also stop my Tailscale tray"*
- *"Add a button for opening the Sanctum brain `_INDEX.md`"*

Examples of feedback that requires Phase 1B+ (real ISO):
- *"The window manager should be Hyprland, not i3"* — agreed, Phase 1B.
- *"Why doesn't voice work?"* — Phase 2 (needs real mic + sandbox).
- *"GPU arbiter doesn't show real utilization"* — Phase 2 (needs real GPU passthrough).

## Troubleshooting

### "docker compose: command not found"
Install Docker Desktop. The Compose v2 plugin ships with it. If you have only Compose v1 (`docker-compose`), upgrade Docker Desktop.

### "Port 6080 already in use"
Something else (probably an old preview run) holds the port. Run `python eve-vm.py down` then `python eve-vm.py up` again.

### Browser shows "Connection failed"
Wait 15 more seconds (first-run can be slow). If it persists, check `python eve-vm.py logs`.

### "Docker Desktop not installed"
The launcher will print a WSL2 fallback path. For now, install Docker Desktop — easiest path on Windows. WSL2-native preview lands Phase 1A.2.

### Preview is sluggish
i3 + Xvfb in a container is light, but noVNC over a slow loopback can stutter. Try:
- Open `http://localhost:5900` directly in a real VNC client (TigerVNC, RealVNC)
- Or in noVNC settings (gear icon) drop the quality to "low"

## When the operator says "ship to laptop"

That's Phase 4. **Don't** ask for that until you've poked at the preview AND we've shipped Phase 1B real ISO AND T1 acceptance test is green. See `plans/EXECUTION-PLAN-2026-05-25/plan.md` § 5 for the full laptop deploy path.

## Files in this preview

```
docker-stack/
├── eve-vm.py                       # the launcher you run
├── compose.os-preview.yml          # this preview's compose overlay
├── Containerfile.os-preview        # Arch + i3 + xvfb + novnc image
├── VM-PREVIEW-README.md            # THIS FILE
├── preview-stubs/
│   ├── Containerfile.eve-daemon-stub
│   ├── Containerfile.mock-panel
│   ├── eve-daemon-stub.py          # HTTP shim implementing state machine + chat proxy
│   ├── mock-panel.py               # canned-reply panel
│   ├── start-preview.sh            # container entrypoint
│   └── eve-cli                     # the `eve` Python CLI installed at /usr/local/bin/eve
└── preview-config/
    ├── banner.txt                   # what you see on first xterm open
    ├── xterm/Xresources             # purple xterm theme
    └── i3/config                    # i3 hotkeys + colors
```

— sinister-os lane, RKOJ-ELENO 2026-05-25
