> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Sanctum brain :: topic index

Append-only catalog of every knowledge topic. New topics added at top with `Created: YYYY-MM-DD`. Status flips edit-in-place. Most-recent first.

| Slug | Title | Status | Tags | Created | Updated |
|---|---|---|---|---|---|
| powershell-unicode-blockdraw-parse-fail | PowerShell 5.1 cannot parse Unicode box-drawing chars (U+2588/2557/etc.) even with UTF-8 BOM — use ASCII `##` block letters | workaround | powershell, encoding, utf-8, bom, unicode, box-drawing, ascii-art, logo, ps1, parser | 2026-05-19 | 2026-05-19 |
| ruflo-mcp-integration | Ruflo MCP integration — multi-agent orchestration sidecar for Claude Code (MCP wire-up + 5-7 skill forks pending Phase C) | workaround | ruflo, mcp, claude-code, swarm, orchestration, multi-agent, vector-memory, external-import, standing-rule | 2026-05-19 | 2026-05-19 |
| sanctum-auto-push | Sanctum auto-push daemon — 30-min GitHub mirror (`SinisterSanctumAutoPush` scheduled task, branch-guard on `main`, secret regex, lock file, log rotation) | fixed | github, push, scheduled-task, daemon, mirror, sanctum, automation, standing-rule | 2026-05-19 | 2026-05-19 |
| windows-npm-spawn-from-powershell | `Start-Process powershell -Command "npm run dev"` hangs silently — use cmd.exe + npm.cmd | workaround | powershell, npm, windows, start-process, spawn, dev-server, next-js, npm.cmd | 2026-05-19 | 2026-05-19 |
| snap-tt-rka-chain-attestation-insufficient | RKA cert-chain attestation alone does NOT pass either Snap (SS03) or TT (bd-tt-error-code 16) anti-abuse gate — structural-shape wall confirmed across both projects | known-issue | snap-emu, tiktok-emu, rka, attestation, argos, libpipo, libscplugin, libclient, anti-abuse, cross-port | 2026-05-19 | 2026-05-19 |
| rkoj-hot-reload-pattern | RKOJ hot-reload — SSE asset channel + uvicorn --reload + `[UPDATE]` inbox + heartbeat (operator updates without dropping agent context) | fixed | hot-reload, sse, broadcast, [update], heartbeat, dev-loop, rkoj, watchdog, uvicorn | 2026-05-19 | 2026-05-19 |
| rkoj-embedded-device-viewer | RKOJ in-EXE embedded ADB device viewer (no scrcpy popup, no flags — operator's spoofing is upstream) | fixed | embedded, screen, adb, exec-out, mjpeg, no-flags, agent-visibility | 2026-05-19 | 2026-05-19 |
| cross-agent-coordination | Agents coordinate horizontally via inbox: ASK / ANSWER / DISCOVERY / DELEGATE / BROADCAST patterns + etiquette | fixed | coordination, inbox, broadcast, delegate, cross-agent, multi-agent, fleet, standing-rule | 2026-05-19 | 2026-05-19 |
| sinister-vault-architecture | Sinister Vault — 1TB collaborative storage (repos via Gitea, sync via Syncthing, snapshots, MCP, multi-account) | fixed | vault, storage, gitea, syncthing, mcp, multi-account, collaboration, leo, rkoj | 2026-05-19 | 2026-05-19 |
| rkoj-workbench-architecture | RKOJ.exe — workbench architecture (2-tab + ribbon + popout + cycle-points + scheduler) | fixed | rkoj, workbench, ui, 2-tab, ribbon, popout, cycle-points, scheduler, liquid-glass, sanctum-purple | 2026-05-19 | 2026-05-19 |
| panel-localhost-routing | Panel surfaces must route loopback-first with snap-fallback + source tag (centralized `tools/panel-config/panel-config.json`) | fixed | panel, localhost, routing, launcher, window-manager, trophy-case, source-tag, sanctum, master-sweep | 2026-05-19 | 2026-05-19 |
| snap-emu-pb2-schema-shadow | Snap EMU: SHORT vs EXTENDED snap_register_pb2 — sys.path shadow gap (cofTags / cofConfigData / webViewUserAgent / cloudAccountId / simState missing from local pb2) | workaround | snap-emu, protobuf, python, sys-path, pb2, schema, tier2 | 2026-05-21 | 2026-05-21 |
| agent-intelligence-control | Per-agent intelligence-level control (Sanctum Console -> live Claude session) | fixed | claude-code, model, intelligence, console, agent, inbox, two-track | 2026-05-19 | 2026-05-19 |
| exe-silent-crash-no-popup | EXE silent-crash: `sys.__stderr__` is None in PyInstaller windowed builds — guard before .write | fixed | pyinstaller, exe, sanctum-console, silent-crash, stderr, windowed, excepthook | 2026-05-19 | 2026-05-19 |
| exe-dll-crash-incomplete-copy | EXE launches with `Failed to load Python DLL python312.dll` (incomplete copy / locked DLL) | workaround | pyinstaller, exe, dll, python312, sanctum-console, onedir, robocopy | 2026-05-19 | 2026-05-19 |
| console-phone-viewer-integration | Console Phone-Viewer full integration (per-pane ADB exec + history + lane awareness) | fixed | phone-viewer, adb, console, lane, containerization, async | 2026-05-19 | 2026-05-19 |
| enrollment-buildconfig-gate | BuildConfig feature-flag gate for first-boot network-call wire-up | fixed | android, buildconfig, feature-flag, kotlin, lifecycle, panel-client | 2026-05-19 | 2026-05-19 |
| ksu-manager-sister-app-pattern | Sister-app pattern when KSU Manager cert hash is kernel-pinned | workaround | ksu-manager, rebrand, kernel-trust, cert-hash, sister-app, signing | 2026-05-19 | 2026-05-19 |
| apk-orchestrator-pattern | Sinister Detector APK as single phone-side orchestrator for KSU modules | workaround | apk, orchestrator, ksud, module-install, asset-bundle, sinister-detector | 2026-05-19 | 2026-05-19 |
| service-apk-hash-check | Sinister-RKA service.apk runtime hash-checks module.prop bytes | known-issue | ksu, tricky-store, module.prop, hash-verification, rebrand, sinister-rka | 2026-05-18 | 2026-05-19 |
| gitea-self-host | Self-hosting Gitea on localhost:3000 as a github.com replacement | workaround | gitea, self-host, docker, git-remote, github-replacement, sanctum-git, mirror | 2026-05-19 | 2026-05-19 |
| per-agent-branch-convention | Per-agent branch convention so parallel Claude sessions don't collide | workaround | git, branch, multi-agent, lane-discipline, coordination, sanctum-git | 2026-05-19 | 2026-05-19 |
| codex-companion-usage | When to invoke Codex Companion (OpenAI peer review) | fixed | codex, openai, peer-review, cross-check, workflow, standing-rule | 2026-05-19 | 2026-05-19 |
| github-auth-workflow-scope | gh CLI needs `workflow` scope to push .github/workflows changes | workaround | github, gh, auth, oauth-scope, push | 2026-05-19 | 2026-05-19 |
| scrcpy-virtual-display-detected | scrcpy's default mirror creates a VirtualDisplay Snapchat detects | known-issue | scrcpy, adb, snap, virtualdisplay, anti-detect | 2026-05-19 | 2026-05-19 |
| powershell-readhost-empty-prompt | `Read-Host ""` crashes with "name cannot be null or empty" | fixed | powershell, read-host, ui | 2026-05-19 | 2026-05-19 |
| powershell-emdash-non-ascii | em-dash `—` in PS scripts without UTF-8 BOM breaks parsing | fixed | powershell, encoding, utf-8, bom | 2026-05-19 | 2026-05-19 |
| adb-containerization | each ADB-attached phone is its own container; PC state doesn't leak | known-issue | adb, phone, container, frida, lane-discipline | 2026-05-19 | 2026-05-19 |
| pyinstaller-tomli-hook-missing | PyInstaller 6.20 fresh install misses hook-tomli.py | workaround | pyinstaller, build, hooks-contrib | 2026-05-19 | 2026-05-19 |
| pip-self-upgrade-breaks-venv | `pip install --upgrade pip` in a fresh venv can corrupt pip's vendored modules on Py 3.12 | known-issue | pip, venv, python-3-12, urllib3 | 2026-05-19 | 2026-05-19 |
