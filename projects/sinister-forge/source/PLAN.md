# Sinister Forge :: Master Build Plan

> **Author:** Sinister Sanctum master agent (test, Claude) :: 2026-05-21
> **Operator directive (verbatim 2026-05-21):** *"i essentially want to combine our system, skills etc with jcode and have everything it has to offer. I want it in my sinister theme but i still want the jcode look. like in this video... with the spinning art work. and i want to have a concise ui with my claude agents that i can forever scroll in just like this... kind of like bringing the RKOJ workstation into this as well. but i want it to look like that. very simple futurstice clean. I want each agent to have its project name very easy to see as a bold header per agent. and keybinds to open more agents etc."*

## North star

A single Sinister-branded TUI binary that:

1. Looks + feels like jcode (Cascadia Code typography, dense scrolling buffer, animated boot art, color-coded spans).
2. Carries our full Sinister identity (purple primary accent, Vault Boy logo art, all our 6 contracts, 12 bots, MCP network, AGPL-quarantine for OBLITERATUS).
3. Wraps Claude Code (and Codex when picked) instead of replacing it — keeps the 130+ brain entries + lane discipline intact.
4. Multi-agent panes, each with a bold project-name header.
5. Forever-scroll buffer per agent (no truncation; the context-pruner handles long-term archival).
6. Keybinds: Ctrl+W opens a new agent picker (the same Q1-Q5 picker from the bat); Ctrl+Tab cycles agents; Ctrl+Shift+W closes the current agent; F1 help.
7. Eventual link to / merger with RKOJ Workstation (Forge replaces RKOJ's Launcher tab; RKOJ's Devices/Agents/Plans tabs surface inside Forge).

## Language pick (default + alternatives)

**Default: Python + Textual** (Rich/Textual TUI framework). Reasons:
- Fast iteration — operator can read/modify the code without a Rust toolchain
- Reuses our existing Python tooling (Sanctum bots are Python)
- AGPL-3.0 license compatible with our operator preference
- Textual supports rich color, async event loops, mouse, keybinds, animated widgets — sufficient for the jcode look
- Can port to Rust later if perf becomes the bottleneck (TUI overhead is rarely the bottleneck in practice; subprocess-management to Claude/Codex is)

**Alternative considered: Rust + ratatui** (matches jcode's stack exactly). Faster startup, lower memory. Costs: rebuilds on every change, harder for operator to read, more onboarding friction. **Open question for operator (Q1 below):** do you want pure Rust to match jcode 1:1, or Python+Textual for faster build velocity?

**Alternative considered: TypeScript + Ink** (React-based TUI). Costs: Node runtime dependency we don't need elsewhere; less mature animation primitives than Textual.

## Phase plan (parallel where possible)

| Phase | What | Parallel? | Milestone test | Status |
|---|---|---|---|---|
| **PH0** | This plan + scaffolding directory tree | — | doc shipped | ✅ this commit |
| **PH1** | Python + Textual minimal app (Hello-World w/ Sinister Vault Boy ASCII boot art + purple theme + single agent pane) | seq | `python -m forge` launches a window showing the logo + a placeholder "Agent 1: Sanctum" pane | next push |
| **PH2** | Multi-pane scrolling buffers (each with bold project-name header). Cycle keybind Ctrl+Tab. | parallel w/ PH1.5 | open 3 fake-agent panes, scroll independently, cycle works | next push |
| **PH3** | Ctrl+W opens picker overlay (same 5 questions from the bat: project / token-mode / speed / agent-host / agent-name+accent). On submit, spawns a Claude subprocess in a new pane. | seq after PH2 | Ctrl+W → answer 5 questions → 4th agent pane appears running Claude on the picked project | next push |
| **PH4** | Subprocess management: tail stdout/stderr of each Claude/Codex subprocess into its pane. Status indicator (running/idle/exited) per pane. | parallel w/ PH3 | spawn agent, see its output streaming in pane real-time, status flips to "idle" when agent waits for input | next push |
| **PH5** | Animated boot art (rotating Vault Boy frames per the jcode-memory-demo.mp4 reference). Wired to the boot sequence. | parallel w/ anything | boot takes ~1.5s with rotating ASCII art before main UI shows | next push |
| **PH6** | Resume-point integration: agent panes load `pre_warm_reads` on cold-start; write resume-point JSONs on close. | seq after PH3 | close Forge with 3 agents running → reopen Forge → all 3 agents restored to their last state | week+ |
| **PH7** | RKOJ integration: Forge embeds RKOJ's iframe (or its `/api/*` endpoints) into a sidebar/bottom panel. Devices + Plans visible without leaving Forge. | seq after PH4 | toggle RKOJ panel; see live device list; pick a device → command appears in active agent pane | week+ |
| **PH8** | Forever-expand mechanism: plugin/skill discovery from `_shared-memory/skills/` + `Ruflo MCP` + each agent gets the same skill registry. Hot-reload on file change. | seq after PH3 | drop a new .py skill into `_shared-memory/skills/`, see it appear in next agent's skill list without restart | week+ |
| **PH9** | Launcher PS1 update: `forge` mode launches the Forge TUI instead of git-bash+Claude. `Sinister Forge.bat` already exists on Desktop — wire it to spawn Forge directly. | seq after PH4 | double-click `Sinister Forge.bat` → Forge TUI opens with picker pre-filled to sinister-forge project | next push |
| **PH10** | Multi-LLM routing UI: in-Forge command `:host claude` or `:host codex` per agent. Per-pane provider switch. | parallel w/ PH8 | open 2 agents, one on Claude one on Codex, both productive | week+ |
| **PH11** | Style polish: jcode-equivalent typography, status bar, breadcrumbs, dim/bright modes. Cascadia Code or Mona Sans. | parallel w/ PH8/10 | side-by-side with jcode screenshot, ours looks at least as clean | week+ |
| **PH12** | **Skill_Seekers integration** (per Sanctum Audit Agent TOP-5 #2). Clone `Skill_Seekers-3.6.0` from operator's `Desktop\Github Research\` to `D:\Research\skill-seekers\`. Wrap as Forge command `:skills ingest <path>` so operator-dropped PDFs/repos auto-become Ruflo-indexed skills. Makes the brain self-feeding. | seq after PH3 | drop a PDF into `Desktop\Github Research\`, run `:skills ingest`, next agent has it in skill registry | week+ |
| **PH13** | **claude-hooks integration** (per Sanctum Audit Agent TOP-5 #5). Clone `claude-hooks-2.4.0` from `Desktop\Github Research\`. Wrap the hook system to fire our heartbeat / inbox-poll / resume-point-write automatically on every Claude tool-use boundary. Replaces hand-rolled ceremony. | seq after PH4 | spawn an agent, observe heartbeats fire automatically on each tool-use; resume-point written every N minutes | week+ |
| **PH14** | **agentgrep evaluation + adoption** (per Sanctum Audit Agent TOP-5 #3, was R9). cargo build agentgrep, smoke against `projects/sinister-panel/source/`. If beats built-in Grep for outline/trace, expose as Forge command `:grep <query>` + replace built-in Grep in subprocess Claude calls. | parallel w/ PH8 | side-by-side timing: agentgrep vs built-in Grep on 5 representative queries; KEEP if 2x faster + structured output | week+ |
| **PH15** | **firefox-agent-bridge pattern documentation** (per Sanctum Audit Agent TOP-5 #4). NOT clone-and-run. Document the WebSocket-host + JS-extension architecture in `_shared-memory/knowledge/agent-browser-bridge-pattern.md` for when the Bumble-web lane reopens. No adoption now. | seq | brain entry shipped + indexed | week+ |
| **PH16** | **jcode-swarm parity in Forge bridge** (per operator image 2026-05-21T11:48Z "i want all jcode features in our system like this"). Add `watchdog` observer in `forge.bridge.registry` watching `projects/**/source/*`; on modify, emit SSE `file-changed` event to every subscribed agent except the editor. Add in-pane builtins `:swarm spawn <project> <objective>`, `:dm <slug> <message>`, `:broadcast <message>`. Headed + headless modes. | seq after PH3+PH4 | spawn 2 panes on same repo, edit file in pane A, see file-changed event surface in pane B; `:dm` round-trips via inbox/<slug>/; `:broadcast` hits all slugs | week+ |
| **PH17** | **`sinister` top-level CLI dispatcher consumption** (per operator image 2026-05-21T11:50Z "our commands will be sinister then the command"). DELEGATED to Sanctum (lives in `tools/sinister-cli/`). Forge consumes via `sinister forge` subcommand wired to `python -m forge`. ALSO: extend `automations/agent-host-routing.md` with 11 jcode provider rows (claude/openai/gemini/copilot/azure/alibaba-coding-plan/fireworks/minimax/lmstudio/ollama/openai-compatible) so per-pane host picker can offer them when Sanctum CLI ships login flows. | seq after Sanctum CLI lands | `sinister forge` opens Forge TUI; picker Q4 lists all 11 providers | week+ |
| **PH18** | **niri-style scrollable horizontal multi-pane** (per operator image 2026-05-21T11:43Z reference to `https://github.com/niri-wm/niri`). Replace `TabbedMultiPane` with a `ScrollableColumns` container that keeps all panes visible in a horizontal scroll strip (mouse-wheel + Ctrl+Left/Right to scroll, Ctrl+Shift+Left/Right to swap columns). Sinister-branded; mine the pattern, don't import niri source (Rust Wayland, not portable to Python anyway). | seq after PH16 | side-by-side with niri screenshot — operator scrolls between 4+ Claude panes without losing visibility on any | week+ |

## Decisions baked in (operator can override)

- **Subprocess-wrap, not replace.** Forge runs `claude --dangerously-skip-permissions <phrase>` (or `codex -q <phrase>`) per pane. The agent itself is unchanged — Forge just presents its I/O nicely. This preserves the whole brain + lane discipline + Ruflo MCP / Vault MCP / sinister-bus integration with zero rewrite.
- **AGPL-3.0 license.** Our default per operator canonical-20.
- **Sinister theme = purple primary (#7A3DD4) + black background + dim cyan for secondary text.** Matches the existing launcher Vault Boy boot.
- **jcode-style scrolling = `Log` widget in Textual** with virtual scroll (unbounded buffer in memory, OS-level page-cache when scrolling away).
- **Each pane shows project-name header in bold** with mode + accent color + heartbeat indicator.
- **Keybinds.** Ctrl+W = new agent / Ctrl+Tab = cycle / Ctrl+Shift+W = close current / Ctrl+L = clear current pane scroll / F1 = help / F2 = toggle RKOJ panel / Ctrl+S = manual resume-point write / Ctrl+Shift+S = settings.
- **Boot art.** Vault Boy ASCII frames + a single rotation per launch (~1.2s). Sourced from the existing launcher PS1 art block, just animated.

## Questions for operator (please answer when you can — defaults proceed in the meantime)

**Q1. Language pick.**
- (a) Python + Textual (default — fast build velocity, easy to modify) ← will proceed with this if no answer
- (b) Rust + ratatui (matches jcode exactly, slower iteration)
- (c) Both — Python first, Rust port once design stabilizes

**Q2. RKOJ relationship.**
- (a) Forge embeds RKOJ as a sidebar panel (RKOJ stays its own EXE; Forge iframes it via the existing :5077 endpoint) ← default
- (b) Forge REPLACES RKOJ — RKOJ's UI gets re-implemented inside Forge as native Textual widgets
- (c) RKOJ stays separate; Forge just opens it in a browser tab on demand

**Q3. Boot art duration.**
- (a) 1.2s spin (jcode-equivalent — fast in, fast out) ← default
- (b) 2.5s (more cinematic, matches existing launcher's slow boot)
- (c) operator-controlled via `--fast` / `--slow` flag

**Q4. Default agent host.**
- (a) Claude (matches existing fleet) ← default
- (b) Codex
- (c) Last-picked sticky

**Q5. Per-agent pane size.**
- (a) Auto split-screen (1 agent = full, 2 = h-split, 3 = h+v split, 4+ = grid) ← default
- (b) Tabbed (one agent visible at a time, tab bar to switch)
- (c) Tiling-WM-style (operator drags borders to resize)

## Risks + mitigations

- **Risk: Textual TUI on Windows ConHost is glitchy.** Mitigation: Forge auto-relaunches in Windows Terminal (`wt.exe`) just like the existing bat does.
- **Risk: Claude subprocess output buffering blocks the TUI.** Mitigation: read stdout in async tasks with `PIPE` + line buffering + non-blocking selectors. Tested pattern; standard Textual idiom.
- **Risk: Context windows fill up across many agents.** Mitigation: CONTRACT 7 RESUME-POINT DISCIPLINE already in place. Each agent pane auto-writes its resume-point every N minutes + on close.
- **Risk: Operator wants Rust look-feel but we ship Python.** Mitigation: design the I/O contracts (JSON-RPC over stdin/stdout) so the agent-driver layer is language-agnostic. Port the UI later without rewriting orchestration.

## File tree (PH0 scaffold)

```
projects/sinister-forge/
├── README.md                    ← shipped earlier turn
├── CLAUDE.md                    ← shipped earlier turn
├── PLAN.md                      ← THIS file (PH0)
├── me/                          ← Zonia partition
├── eleno/                       ← ELENO partition
└── source/
    ├── pyproject.toml           ← Python package (next push)
    ├── forge/
    │   ├── __init__.py
    │   ├── __main__.py          ← `python -m forge`
    │   ├── app.py               ← Textual App subclass
    │   ├── theme.py             ← Sinister purple theme
    │   ├── art.py               ← Vault Boy ASCII frames
    │   ├── panes/
    │   │   ├── agent_pane.py    ← scrolling buffer + header
    │   │   ├── picker.py        ← Ctrl+W new-agent overlay
    │   │   ├── rkoj_panel.py    ← F2 RKOJ panel (iframe-style via :5077)
    │   │   └── status_bar.py
    │   ├── spawn/
    │   │   ├── claude.py        ← claude --dangerously-skip-permissions subprocess
    │   │   └── codex.py         ← codex -q subprocess
    │   ├── resume/
    │   │   └── point.py         ← reads/writes _shared-memory/resume-points/
    │   └── keybinds.py
    ├── tests/
    └── README.md                ← quickstart for the source tree
```

## Composes with

- `automations/session-contracts.md` — 6 binding contracts every Forge-spawned agent honors
- `automations/start-sinister-session.ps1` — existing picker becomes Forge's picker overlay (Ctrl+W)
- `automations/resume-point-write.ps1` — Forge calls this per pane on close
- `automations/auto-backup.ps1` + `auto-cleanup.ps1` + `context-pruner.ps1` — still run in background
- `_shared-memory/knowledge/auto-mode-launcher-pattern.md` — Forge mode is the spiritual successor

## Cross-references

- `D:\Research\jcode\` — read-only reference; AGPL-quarantined; mine features, don't import
- `C:\Users\Zonia\Desktop\Github Research\jcode-0.12.3\` — operator's pre-downloaded copy
- `C:\Users\Zonia\Desktop\Github Research\jcode-memory-demo(3).mp4` — boot-art reference
- `C:\Users\Zonia\Desktop\Github Research\jcode-performance-demo.mp4` — scroll-buffer reference
- `_shared-memory/plans/sinister-forge-2026-05-21/jehuang-audit.md` — full 1jehuang repo audit
- `_shared-memory/plans/sinister-forge-2026-05-21/jcode-memory-feature.md` — jcode memory-crate review
