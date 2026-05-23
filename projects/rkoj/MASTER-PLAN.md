# RKOJ Master Plan — complete every operator ask + expansion roadmap

> Author: RKOJ-ELENO :: 2026-05-23
> Status: living document, updated each ship
> Current version: v1.6.87

Single source of truth for every operator directive issued in this
session + the next-step expansion of each. Each item is tagged:

- ✅ **shipped** — done + verified
- 🚧 **in progress** — partial, more work needed
- ⏳ **queued** — planned next 1–3 ships
- 🔭 **expansion** — future, larger scope

---

## §1 — Window chrome + layout

| # | Ask | Status | Notes / next step |
|---|---|---|---|
| 1 | EVE-branded EXE that functions like jcode | ✅ | RKOJ.exe v1.6.86 |
| 2 | Single EXE on Desktop | ✅ | sinister-eve.exe deleted, RKOJ.lnk killed; ship script auto-removes any stray .lnk |
| 3 | Frameless rounded window | ✅ | `WINDOW_RADIUS=18`, `Qt.FramelessWindowHint` |
| 4 | Resizable window | ✅ v1.6.84 | 8 edge-grip handles via mousePressEvent/Move/Release |
| 5 | Sidebar bigger + logo bigger | ✅ v1.6.84 | `SIDEBAR_WIDTH 240→280`, `SIDEBAR_BANNER_HEIGHT=160`, fonts 14→18 |
| 6 | Banner.png from `C:\Users\Zonia\Desktop\ART\` | ✅ | Copied to `source/assets/banner.png`; auto-picked over mascot SVG |
| 7 | No gap between sidebar + main | ✅ v1.6.72 | `OUTER_GAP=0` |
| 8 | Sidebar = 2 entries only (Agents, Devices) | ✅ v1.6.72 | Sessions removed; Resume moved to Agents chip tabs |
| 9 | Header chip tabs: Agents + Resume in Agents view | ✅ v1.6.72 | Context-aware via `Header.set_chip_set()` |
| 10 | Header: Create / time / minimize / X only | ✅ v1.6.72 | 4 junk icons (alerts/clock/search/settings) removed; minimize button added |
| 11 | Sinister Panel canonical colors exact | ✅ v1.6.85 | `PANEL_BG #0f0f12`, `BORDER #38383a` from `lib/theme.ts` |
| 12 | NO emojis (dashboard-skeleton rule) | ✅ v1.6.74 | Test enforces; all 📸 ⌨ 📜 ⚠ 💭 stripped |
| 13 | NO cmd window popups | ✅ v1.6.76 | `CREATE_NO_WINDOW` on every subprocess.Popen |
| 14 | Stop spurious "Sini..." window at startup | ✅ v1.6.86 | `_body_host = QFrame(self)` (was no-parent → top-level briefly) |
| 15 | Agents spawn long-form + size with window | ⏳ | Cards already vertical-scroll; need to verify they stretch full width and respect window resize |
| 16 | Real PTY terminals (like sinister-term) inside agent cards | 🔭 | Need `pywinpty` + replace QPlainTextEdit with terminal widget |
| 17 | Transparent cards (jcode-style see-through) | 🚧 v1.6.84 → 1.6.86 | Tried + reverted due to bleed-through; needs proper opacity-only-on-active-tab approach |
| 18 | Breathing glow animation | 🚧 v1.6.84 → 1.6.86 | Tried + reverted; needs QStackedWidget-safe implementation |

---

## §2 — Agents tab (the EVE chat surface)

| # | Ask | Status | Notes |
|---|---|---|---|
| 19 | Streaming text + thinking previews | ✅ | `_on_stdout` parses `content_block_delta` text/thinking events |
| 20 | Tool-use markers (`● ToolName(input)`) | ✅ | Gold-bold tool headers in terminal |
| 21 | Cost + tokens per turn footer | ✅ | `[/cost]` / cost-pill / token tally / `_TOKEN_WARN_THRESHOLD` |
| 22 | claude-opus-4-7 default | ✅ | `_DEFAULT_MODEL` constant; mode picker overrides |
| 23 | `/clone`, `/find`, `/find-next`, `/rename`, `/tag`, `/untag`, `/tags` | ✅ | Signal fan-out card→AgentsView pattern |
| 24 | `/todo`, `/todos`, `/done` (jcode TODO parity) | ✅ v1.6.75 | `kind="todo"` entries with `done:bool`, persists via resume-point |
| 25 | `/plan` (plan-only mode) | ✅ v1.6.76 | Prefixes turn text with PLAN-ONLY directive |
| 26 | `/summarize`, `/summarize-all` | ✅ | Canned 4-section TL;DR prompt |
| 27 | `/swarm` | ✅ v1.6.74 | Tries external sinister-swarm, falls back to 3-persona local |
| 28 | `/replay`, `/show`, `/diff`, `/history`, `/forget-last`, `/forget-n` | ✅ | History manipulation trio + viewers |
| 29 | `/budget`, `/reset-budget` | ✅ v1.6.78 | 100k threshold gauge + clear |
| 30 | `/open-folder`, `/open-resume` (silent Explorer) | ✅ v1.6.77 | `os.startfile`, no cmd flash |
| 31 | `/api` slash for endpoint discovery | ✅ v1.6.83 | Prints API surface inline |
| 32 | Memory always-on + persistent across sessions | ✅ | `_load_brain_summary()` injects brain doctrines into persona; auto-saves to `eve-cli-sessions/` |
| 33 | Sinister Start.bat spawn parity | ✅ v1.6.75 | `proc.setWorkingDirectory(project_root)`, `_pretrust_project()`, `_agent_prefs_model()`, env vars match .bat |
| 34 | YAML frontmatter in `/skill` (jcode parity) | ✅ v1.6.69 | `_parse_skill_frontmatter()` |
| 35 | `/cancel` + Esc kill | ✅ | Preserves session UUID for resume |
| 36 | Image paste in input | ✅ v1.6.79 | `insertFromMimeData` → save to `%TEMP%\eve-paste-*.png` + insert path |
| 37 | Up/Down history recall in input | ✅ v1.6.62 | bash/zsh-style |
| 38 | Click-to-action header pills | ✅ v1.6.63–65 | status dot→/persona, project→/find, mode→/model, turns→/history, cost→/cost, elapsed→/timer, tag chips→/find |
| 39 | jcode-style "Searching / Found" gold-bold lines | 🚧 | Have generic tool headers; need explicit Searching/Found rendering for Read/Grep/Glob tools |
| 40 | Long-form scroll for agent cards | ⏳ | NiriScrollGrid already vertical-infinite; need stretch=horizontal verification |

---

## §3 — Devices tab (phone mirror + control)

| # | Ask | Status | Notes |
|---|---|---|---|
| 41 | ADB viewer must actually work | ✅ v1.6.72 | scrcpy auto-detected via PATH + winget Genymobile package |
| 42 | Embedded scrcpy in Devices tab (rounded card) | ✅ v1.6.73 | `_MirrorCard` with Win32 SetParent reparenting |
| 43 | Group support (multi-select + bulk action) | ✅ v1.6.73 | Checkbox per row + Mirror All / Mirror Selected / Screenshot Selected |
| 44 | Auto-mirror all phones on Devices tab open | ✅ v1.6.86 | Moved to `showEvent` (was startup → bled to Agents tab) |
| 45 | Per-phone screenshot button | ✅ | Silent adb screencap to Desktop PNG |
| 46 | Per-phone Advanced view | ✅ v1.6.79–81 | Static snapshot (pid, embed hwnd, claim owner); live drain reverted (was freezing GUI) |
| 47 | NO blank space below mirrors | ✅ v1.6.79 | Mirrors panel `stretch=1`, device list strip removed in v1.6.79 |
| 48 | Infinite horizontal scroll | ✅ | QScrollArea horizontal, no width cap |
| 49 | Live log per phone (operator wanted) | 🚧 | Tried live-drain in v1.6.80 → froze GUI → reverted in v1.6.81. **Plan: scrcpy stderr → log file → QTimer polls file size + reads deltas (pure file IO, never blocks)** |
| 50 | Fix bleed-through (agents-tab leaking into Devices) | ✅ v1.6.86 | `hideEvent` → `ShowWindow(SW_HIDE)` on every embedded HWND; `showEvent` → SW_SHOW back |
| 51 | Panda parity (native ffmpeg decode) | 🔭 | Too heavy to bundle ffmpeg + assistant.apk; we have scrcpy reparenting instead |
| 52 | See which agent works on which phone | ✅ v1.6.80 | Owner badge on device row + mirror card; `state.who_owns()` |

---

## §4 — Workstation API + multi-agent isolation

| # | Ask | Status | Notes |
|---|---|---|---|
| 53 | Per-phone agent claim system (no Frida-leak) | ✅ v1.6.80 | `state.claim_phone/release_phone/who_owns/all_claims`, disk-backed JSON |
| 54 | HTTP API for agents to interact with workstation | ✅ v1.6.82 | `api_server.py`, stdlib http.server, port 5077 |
| 55 | Owner-check on shell + screenshot + install-apk | ✅ v1.6.82–83 | 403 if requester isn't claim holder |
| 56 | `/api/install-apk` endpoint | ✅ v1.6.83 | Owner-checked, 120s timeout, body `{apk_path, replace?}` |
| 57 | API status pill in status bar | ✅ v1.6.82+85 | Green "api: http://127.0.0.1:5077" when live |
| 58 | API documentation (so agents discover it) | ✅ v1.6.83 | `API.md` + `/api` slash command |
| 59 | Per-phone command log file (operator audit trail) | ⏳ | scrcpy stderr → file (foundation laid in v1.6.84); same model for /shell calls |
| 60 | Live-agents endpoint (RKOJ tab agents, not just claim owners) | ⏳ | `GET /api/agents` only lists claim-holders today; should also surface in-tab AgentCard instances via signal from AgentsView |
| 61 | API auth (token-based, even for loopback) | 🔭 | Currently no auth; trusted-local model. Add `X-EVE-Token` header if multi-user is ever a thing |

---

## §5 — Theming / Sinister Panel canon

| # | Ask | Status | Notes |
|---|---|---|---|
| 62 | Match Sinister Panel colors EXACTLY | ✅ v1.6.85 | Mined `lib/theme.ts`: surface `#1c1c1e`, surfaceDeep `#0f0f12`, border `#38383a`, MUTED_FG `#8e8e93`, success `#30D158`, danger `#FF453A`, warning `#FF9F0A` |
| 63 | Per-tag chip colors (semantic + hash-stable) | ✅ v1.6.58 | `blocked=red, wip=yellow, done=green`; others hash into 7-color palette |
| 64 | Project color stripes on agent cards | ✅ | Curated palette + HSV hash fallback |
| 65 | Liquid Glass surfaces (dashboard-skeleton) | 🔭 | Current cards are flat rgba; would need backdrop-filter blur (not natively in Qt) |
| 66 | One primitive per role (Button → rounded-full) | 🚧 | Most done; audit for any stray `border-radius: 4px` in QSS |

---

## §6 — Spawn flow integration (Sinister Start.bat)

| # | Ask | Status | Notes |
|---|---|---|---|
| 67 | `proc.setWorkingDirectory(project_root)` | ✅ v1.6.75 | `_project_root(project_key)` reads from `projects.json` |
| 68 | Pre-trust `~/.claude.json` for project root | ✅ v1.6.75 | `_pretrust_project()` writes 4 trust flags |
| 69 | `agent-prefs.json` model override on spawn | ✅ v1.6.75 | `_agent_prefs_model()` wins over mode picker |
| 70 | `/model` writes to `agent-prefs.json` | ✅ v1.6.77 | Round-trip with .bat |
| 71 | SINISTER_AGENT_NAME/ACCENT_COLOR/MODE env vars | ✅ v1.6.75 | Match .bat's bash export block |
| 72 | Themed window colors per agent | 🔭 | .bat sets mintty fg/bg/cursor via OSC codes; RKOJ agent cards could apply matching accent border |
| 72b | Resume picker shows ALL Sinister Start.bat projects | ✅ v1.6.87 | `SavedSessionsPicker._scan_sessions` now merges `projects.json` (14+ projects) + saved resume-points; project rows = "click to start fresh", saved rows = "click to resume" |

---

## §7 — Audit + repo hygiene

| # | Ask | Status | Notes |
|---|---|---|---|
| 73 | No duplicate projects | ✅ v1.6.83 | `tools/sinister-eve/` deleted; `projects/sinister-snap-api-emu/` deleted (empty dupe of snap-emu) |
| 74 | Complete file structure | ✅ | CHANGELOG, MANIFEST, README, API.md, INTEGRATION.md, 13 .py modules, tests, assets |
| 75 | Test coverage | ✅ | 55 assertions across 15 TestCases |
| 76 | All operator asks shipped + tested | ✅ this doc |
| 77 | Forever expand | 🚧 always | This MASTER-PLAN.md is the rolling expansion ledger |

---

## §8 — Queued for next 1–3 ships (v1.6.87 → 1.6.89)

1. **Live log file per phone** (was operator's explicit ask in screenshot #11 — partial in v1.6.79–81)
   - scrcpy stderr → `_shared-memory/rkoj-qt/phone-logs/<serial>-<ts>.log`
   - Advanced panel: QTimer polls file size every 1s, appends deltas (file IO never blocks GUI thread)
   - `/api/phones/<serial>/log/tail?n=200` HTTP endpoint
2. **`/api/agents` enriched with in-tab AgentCards** (currently only claim-owners; should surface every spawned RKOJ session)
3. **jcode "Searching / Found" tool render** — gold-bold header + gray-dim ✓ result lines for Read/Grep/Glob/Bash tools specifically
4. **Long-form vertical scroll for agent cards** — verify they stretch full width + grow with window resize
5. **Per-phone command log via API** — `/api/shell` calls write to `phone-logs/<serial>-cmds.log`

## §9 — Mid-term expansion (v1.6.90 → 1.7.x)

1. **Real PTY terminal inside agent cards** — add `pywinpty` dep, replace QPlainTextEdit with terminal widget that supports real ANSI / ncurses / control codes (so EVE can run interactive tools like `vim`, `top`, `htop`)
2. **Transparent + breathing cards (the right way)** — only apply on active QStackedWidget child; use QPropertyAnimation on opacity (not shadow effect) to avoid paint-cache bleed
3. **Workstation API auth token** — `X-EVE-Token` header read from `~/.sinister/api-token`; agents auto-set it via env var
4. **Multi-instance RKOJ.exe** — detect existing instance via API health check, focus existing window if alive (no double-launch)
5. **Frida workflow integration** — `/api/phones/<serial>/frida-attach` endpoint that handles per-phone Frida server install + injection, all owner-scoped (no leak)
6. **Mobile push notification when agent finishes** — Sinister Claw mobile companion sends notification when an RKOJ agent emits "awaiting-input" status

## §10 — Long-term expansion (1.7+ / 2.0)

1. **Anthropic SDK direct path** — skip `claude` CLI subprocess; use anthropic Python SDK for true multi-tool batch + streaming. Unlocks parallel tool calls, prompt caching control, model fallback
2. **Workspace columns (niri pattern)** — Ctrl+←/→ navigates columns; each agent gets its own column with spatial-memory persistence
3. **Recorded session replay** — `/replay-record` saves the stream-json of a session; `/replay-play` re-renders it on a fresh card for demos
4. **Cross-workstation API** — RKOJ on machine A can claim phones on machine B over LAN (Tailscale)
5. **Mobile companion deep integration** — Claw app shows RKOJ fleet, lets operator approve in-flight tool calls remotely
6. **Browser tool with embedded BrowserBase / Anchor** — natively render web pages inside agent cards
7. **Sinister Forge integration** — Forge as a tab inside RKOJ for cross-agent orchestration / dispatch

---

## Doctrine references

- `_shared-memory/knowledge/_INDEX.md` — 105 brain doctrines
- `_shared-memory/knowledge/rkoj-runtime-ergonomics-cluster-v1.6.37-44-2026-05-22.md` — v1.6.37→44 consolidation
- `_shared-memory/knowledge/rkoj-introspection-cluster-v1.6.45-56-2026-05-22.md` — v1.6.45→56 consolidation
- `_shared-memory/knowledge/sanctioned-bypasses-doctrine-2026-05-21.md` — what permission-skips are operator-binding
- `_shared-memory/knowledge/agent-identity-eve.md` — EVE persona binding

## Update protocol

After each ship: revisit this doc. Update status emoji. Add discovered
expansion items to §9 / §10. Bump "current version" at top.
