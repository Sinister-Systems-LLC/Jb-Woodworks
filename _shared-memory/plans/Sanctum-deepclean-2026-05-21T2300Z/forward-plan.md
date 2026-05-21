# Author: RKOJ-ELENO :: 2026-05-21

# Sanctum :: deep-clean + RKOJ-workstation forward plan
# Created at 2026-05-21T23:03Z

**Operator directive verbatim (2026-05-21, session start):** *"i need you to do a deep audit on the sinsiter sanctum folder in the d drive. make sure eevrything there is concise complete and in order. remove things we dont need. clean it all up. make sure the memory system we use works perfect with the jcode system. remove projects for sinister from the personal folder. make sure we are clean and ready to work on things. i need you to make a porject in projects for rkoj and add everything there that we use for rkoj. the term, jcode stuff all of it. then i need you to create a complete plan to finidh the rkoj workstation how i want it. I want the 1:1 exact ui as sinister panel. 1:1 nothing else everything the same and exact. with two tabs for now. one called devices that is empty but will allow us to view the adb phones. and then i nened the agents tab with the infinite scroll adn features there from jcode dev, etc. When i click new agent it will be like we click the jcode exe and openeed a window. then once you have that down and working continue to make other features i said i watned. do not stop working until all this is done and tested. you do not need me fore shit. always place update exe on the desktop."*

**Operator addendum (2026-05-21T22:59Z, mid-task):** *"here are some notes. I want exact jcode form and function, but with all my branding and the AI calls itself EVE. save source as we are going to add and change many things once its working ... I want to build a complete workstation for everything i do. i can add support for all tools i play with. for example the workstation will have tab called devices that i can connect all my adb devices too. we already worked on this and can view them from there etc. so much potential we can do with this tool. like make our own anydesk to login to my servers from any where in the world complete self hosted so i dont have to use anydesk. intergrate my own browser system like kamelo, my own android emulator system so so many things. note these in the plans but dont build them until we are ready."*

---

## A. Synthesized rules of the session

1. **RKOJ is the workstation** — every Sinister tool/feature can plug into it over time. The forever-expanding-modular doctrine is the load-bearing architecture.
2. **Shell = 1:1 Sinister Panel** (sidebar + 2-row header + chip tabs + folder tabs + niri-scroll grid).
3. **Inside the Agents tab = exact jcode form and function** with EVE branding throughout. The card/pane *behaves* like a jcode session (streaming, slash commands, skill registry, BM25 recall).
4. **Two tabs only for now:** Agents (live) + Devices (empty shell, ADB wiring later).
5. **Source must be preserved** through every iteration — git-tracked, committed often, never lost.
6. **EXE always shipped to Desktop** on every meaningful change.
7. **No "what next" interruptions** — drive end-to-end.

## B. Execution lanes (this session, master-actionable)

| Lane | Subject | Status | Reversibility |
|---|---|---|---|
| R1 | Deep audit Sanctum tree → cleanup proposal | in flight (sub-agent) | R0 |
| R2 | D:/Sinister Sinister-content purge audit | in flight (sub-agent) | R0 |
| R3 | Extract 1:1 Panel UI spec | captured (this session) | R0 |
| R4 | Memory⇄jcode integration audit | captured (this session) | R0 |
| R5 | Move tools/sinister-rkoj-qt → projects/rkoj/source | execute now | R1 (git mv, reversible) |
| R6 | Re-skin header/sidebar/theme → 1:1 Panel pixel-exact | execute after R5 | R1 |
| R7 | Wire New Agent → jcode-form pane (streaming + slash + skills) | execute after R6 | R1 |
| R8 | Devices tab shell (empty hero, ADB wiring deferred) | execute after R6 | R1 |
| R9 | Rebuild RKOJ.exe v1.5.2 onefile + ship to Desktop | execute after R7+R8 | R1 |
| R10 | Tests / smoke milestones M1-M10 per rkoj-ui-exact-spec § 10 | execute after R9 | R0 |
| R11 | Commit + push + PROGRESS + brain entries | execute after R10 | R1 |

## C. Future-workstation roadmap — NOTE but do NOT build yet

These are operator-stated 2026-05-21 (mid-task) as "the workstation will have... so many things... note these in the plans but dont build them until we are ready."

### C.1 Devices tab — full ADB wiring

- All connected ADB phones discoverable + viewable from the Devices tab.
- scrcpy embed inside the tab (no popups; in-tab MJPEG stream like `rkoj-embedded-device-viewer` brain entry).
- Per-device logcat tail strip.
- adb shell input box per device.
- RKA armed/disarmed indicator per device.
- "Containerization" per device (per `adb-containerization` brain entry — each phone is its own container).
- Tagging: P1, P2, etc. per `_shared-memory/knowledge/agent-host-routing*` if present.

### C.2 AnyDesk replacement (self-hosted remote-desktop) — **build later**

Operator: *"make our own anydesk to login to my servers from any where in the world complete self hosted so i dont have to use anydesk"*.

Candidate stack (research-stage):
- **RustDesk** (open source AnyDesk-like) — self-hostable server + client, MIT.
- **Apache Guacamole** (web-based RDP/VNC/SSH gateway).
- **MeshCentral** (NodeJS, full self-hosted RD + management).
- Our spin: Sanctum-branded thin client, EVE persona, deploy daemon at `tools/sinister-remote/`, expose at `:6080` or operator-pick.
- Auth: re-use Vault MCP user-token model + Tailscale-only network plane (zero-trust).
- Hetzner reverse proxy via Caddy → ProBranding.

### C.3 Kameleo-style anti-detect browser — **build later**

Operator: *"intergrate my own browser system like kamelo"* (operator-owned-infra browser, references the commercial Kameleo product as the shape).

Candidate stack:
- Base on undetected Playwright + Chromium with fingerprint randomization layer (canvas / WebGL / fonts / audio / WebRTC / language / TZ / screen).
- Profile manager → operator's profiles live in Vault.
- Per-profile cookie + storage + state persistence.
- Anti-detect plugin layer (operator owns this — no third-party-targeting use).
- UI: integrated into RKOJ.exe as a new chip tab or new sidebar nav item.
- Composes with: `agent-browser-bridge-pattern` (already in brain) for the WebSocket-host driving operator's real logged-in browser.

### C.4 Own Android emulator system — **build later**

Operator: *"my own android emulator system"*.

Candidate stack:
- Existing: Sinister Emulator Bundle (`projects/sinister-emulator-bundle/`) is the foundation.
- Wrap as RKOJ emulator manager: spawn, snapshot, clone, ADB-bridge, container per emu.
- Composes with: Sinister Snap EMU + Sinister TikTok EMU + Sinister Bumble EMU lanes (all operator-owned-infra emu work).
- UI: new Emulators tab inside RKOJ (5th chip tab once we expand beyond Agents/Devices).

### C.5 "So many things" — open registry

Every new tool/feature the operator plays with becomes a candidate extension under `projects/rkoj/source/extensions/<slug>/manifest.json`. The plugin pattern is canonical per `_shared-memory/knowledge/sinister-rkoj-extensibility-doctrine.md` — 7 hook types (sidebar_nav, header_tab, ribbon_group, kpi_tile, slash_command, agent_pane, phone_pane, workstation_card).

Tentative candidate list (snapshot as of this session, append-only):
- Sinister Vault file browser (extensions/vault/)
- Sinister Watchdog status pane (extensions/watchdog/)
- Sinister Brain index browser (extensions/brain/)
- Sinister Skills runner (extensions/skills/)
- Sinister MCP server config editor (extensions/mcp/)
- Sinister Model picker (extensions/model/)
- Sinister Backup status (extensions/backup/)
- Sinister Login wallet (extensions/login/)
- Sinister Usage dashboard (extensions/usage/)
- Sinister Diagnose (extensions/diagnose/)
- Sinister Mermaid graphs (extensions/mermaid/)
- Sinister Swarm controller (extensions/swarm/)

## D. Test plan (Milestones M1-M10) — per rkoj-ui-exact-spec § 10

| M | Surface | Smoke pass criteria |
|---|---|---|
| M1 | EXE boots | Double-click EXE → rounded frameless window appears <2s |
| M2 | Sidebar renders | Mascot + Agents/Devices nav rows visible, active state has purple-deep fill |
| M3 | Header rows | Row 1 menu strip + Row 2 chip tabs + actions all rendered; chip swap works |
| M4 | X button | Click X → window closes <2s; `ps` shows no orphan `claude.exe` |
| M5 | Spawn agent | Click Create Agent → card added to niri-scroll grid; placeholder banner shown |
| M6 | Send input | Type message + Enter → child stdin receives, terminal shows reply <30s |
| M7 | Glow overlay | Spawned agent prints prompt + waits → card border pulses purple |
| M8 | Folder tabs | Spawn 2nd project agent → 2nd folder tab appears; close → tab disappears |
| M9 | EVE persona | Card header reads "EVE on <project>"; spawned agent self-refs as EVE |
| M10 | Forever-expansion | Drop new extension into `extensions/` → reload → new menu item appears |

## E. Operator-gated (surface only, do NOT block on)

- `Rename-Sinister-to-Personal.bat` UAC double-click (D:\Sinister → D:\Personal)
- `Kill-Popups.bat` UAC double-click (last 2 PowerShell-popup tasks)
- `ANTHROPIC_API_KEY` env var (unblocks Anthropic-SDK direct path for v0.6.0+ agentic loop)
- Decide LICENSE (still placeholder)
- Decide Hetzner-reverse-proxy domain for AnyDesk-replacement when we build it

## F. Composes-with brain entries

- `rkoj-ui-exact-spec-2026-05-21` — UI shape
- `sinister-rkoj-extensibility-doctrine` — plugin architecture
- `agent-identity-eve` — EVE persona
- `agent-browser-bridge-pattern` — future browser integration
- `niri-scrollable-column-pattern` — infinite scroll Agents grid
- `forever-expanding-modular-architecture-doctrine` — substrate
- `jcode-feature-matrix` + `jcode-agentic-loop-patterns-port-to-python` + `jcode-feature-parity-targets` — jcode form/function we are cloning
- `apk-classifier-aup-doctrine` — operator-own-infra exception
- `operator-iteration-loop-2026-05-21` — screenshots-are-spec discipline

## G. Risk register

| Risk | Mitigation |
|---|---|
| `git mv` directory operation interferes with auto-push schtask | Auto-push is atomic per ref; if it fires mid-mv, the commit lands cleanly afterwards |
| Sidebar.py modified but uncommitted before move | Stage + commit BEFORE mv or mv will move the modification along (preferred — move first, commit move + staged content together) |
| RKOJ.spec hardcoded `_TOOL_ROOT` relies on parent-of-spec — survives move | Verified |
| Assets path resolution (`asset_path` in theme.py) — uses `__file__.parent.parent / 'assets'` — survives move because relative | Verified |
| Path refs in automations/*.ps1 / *.bat — many | Update all in one pass after move |
| MANIFEST.json references `tools/sinister-rkoj-qt` for `rkoj-qt` + `rkoj-qt-extensions` components | Update after move |
| Sub-agent reports failed to write because Explore is read-only | Capture findings inline (this session) |

---

End of forward plan.
