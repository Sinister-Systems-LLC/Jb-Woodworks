# Welcome to Sinister Sanctum

**Author:** RKOJ-ELENO :: 2026-05-25

You just opened the `deploy/` folder. This is the one-stop bootstrap kit for
turning a fresh Windows 10/11 machine into a working **Sinister Sanctum**
workstation in under 10 minutes.

If you only read three things in this folder, read this README, then
`GETTING-STARTED.md`, then `TROUBLESHOOTING.md`.

---

## 3-step quickstart

1. **Get the code.** Either:
   - Extract the zip you were given into `D:\Sinister Sanctum\`, OR
   - `git clone https://github.com/Sinister-Systems-LLC/Sinister-Sanctum.git "D:\Sinister Sanctum"`

2. **Run the bootstrapper.** Open PowerShell (any window — admin not required;
   the installer auto-elevates UAC for the pieces that need it):

   ```powershell
   python "D:\Sinister Sanctum\deploy\setup.py"
   ```

   This auto-installs: Git for Windows · Node.js LTS · Claude Code CLI ·
   Python 3.10+ deps · scheduled tasks (auto-push, account watchdog, doctor,
   link poller) · config templates · MCP server seed (without overwriting
   existing). Takes ~5-10 min on a normal connection.

3. **Double-click `EVE.exe`** (this folder ships a copy; the canonical one
   lives at the repo root). The picker opens. Pick a project (`1`-`15`),
   answer the 3-question primer, and Claude spawns into the lane. Done.

---

## What is Sinister Sanctum

Sinister Sanctum is the **orchestration repo** for the Sinister Systems LLC
project universe — the "new Library of Alexandria" that every other Sinister
product repo (Snap-API-EMU, TikTok-API-EMU, Panel, Kernel-APK, JB Woodworks,
Showmasters, LetsText, etc.) consumes for its bots, automations,
session-start protocols, doctrine brain, and cross-lane mesh. The flagship
launcher is **EVE.exe** — a sub-300 ms PyInstaller bundle that opens a
themed mintty + Claude session with all the right configs preloaded into a
single bash prompt.

Under the hood Sanctum runs ~20 parallel lane agents (one per project),
13 MCP bots (sentinel / librarian / custodian / vault / scribe / ...), a
1 TB local-first collaborative vault (Gitea + Syncthing on `localhost`),
multi-account Claude rotation with rate-limit watchdog, cross-machine
pairing via Sinister LINK, and a self-healing doctrine system (brain ceiling
150 entries, daily orphan archive, post-commit cross-lane diff broadcast).
You are EVE — every operator-facing surface uses that identity, every new
file carries `Author: RKOJ-ELENO :: <date>`, and every spawn ships with
`claude --dangerously-skip-permissions`.

---

## What `setup.py` will install on your box

| Component | Purpose | Required? |
|---|---|---|
| Git for Windows (`C:\Program Files\Git\`) | mintty + git-bash spawn target for EVE | yes |
| Node.js LTS | hosts the `claude` CLI | yes |
| `@anthropic-ai/claude-code` (npm global, v2.1+) | the spawned Claude binary | yes |
| Python 3.10+ + `pip install` for tools | EVE.exe rebuild + vault daemon + voice POC | recommended |
| `~/.claude/settings.json` (autonomy grant) | `bypassPermissions: true` + plugin enables | yes |
| `~/.claude/.mcp.json` (seed template) | 12 Sinister bots + 4 npm MCPs | yes (skipped if exists) |
| Scheduled tasks (7) | auto-push, account watchdog, doctor, link poll, etc. | yes |
| `claude-accounts.json` (4-slot starter) | multi-account rotation seed | yes |
| Optional: Docker Desktop + Ollama | Tier-2 bots (librarian/triage/researcher) | optional |
| Optional: Tailscale | Sinister LINK pairing with operator (Mode B) | optional |

`setup.py` is **idempotent** — re-running it skips anything already present
and only repairs what's missing or broken. The wizard always runs in
`-DryRun` mode first; flip `--apply` to actually install.

---

## Where to go next

- **`GETTING-STARTED.md`** — comprehensive onboarding. Prereqs, first launch,
  adding your Anthropic account, pairing with operator via Sinister LINK,
  daily-use commands, and where every important file lives.
- **`TROUBLESHOOTING.md`** — every known first-run failure mode and the
  one-line fix. EVE.exe won't open? mintty exit 126? Defender ate the .exe?
  All here.
- **`DOCS-INDEX.md`** — annotated index of all 27 files in `docs/` so you
  know which deep-dive to read when.
- **Cold-start protocol** — once EVE spawns Claude, it auto-reads `CLAUDE.md`
  steps 0-11 (operator-canonical 2026-05-25). You don't have to do anything;
  just watch the first turn land.

---

## Identity + authorship

- **Agent identity:** EVE (never "Claude" in operator-facing copy).
- **Authorship line on every new `.md` / `.py` / `.ps1` / `.bat`:**
  `Author: RKOJ-ELENO :: <date>`
- **Branch convention:** `agent/<project-key>/<topic>-<utc-date>` — push
  freely to your own branch; only the `sanctum-auto-push` daemon writes
  to `main`.

---

## Need help

- **Smoke test the install:**
  `powershell -File "D:\Sinister Sanctum\automations\eve-first-run-check.ps1" -Format text`
  Exit 0 = green; exit 2 = warns-only (still usable); exit 1 = hard blockers.
- **Re-run setup:** `python "D:\Sinister Sanctum\deploy\setup.py" --apply`
- **Reach the operator:** see `docs/MULTI-OPERATOR-COLLABORATION.md` for the
  out-of-band contact path; or pair via Sinister LINK (header `L` key in
  EVE.exe) for live two-way sync.

Welcome aboard.
