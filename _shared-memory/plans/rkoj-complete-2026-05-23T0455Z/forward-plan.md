# RKOJ — complete-without-operator forward-plan

> **Author:** RKOJ-ELENO :: 2026-05-23
> **Agent:** rkoj (EVE on RKOJ; umbrella for Forge + Term + Workstation + Mind + Claw per `projects.json` v6)
> **Branch:** `agent/rkoj/complete-without-operator-2026-05-23`
> **HEAD at plan time:** `b9e89dc` (`brain(correction): pip-show says installed != import works (stale .pth)`)
> **RKOJ.exe version:** v1.6.88
> **Mode:** /loop dynamic (self-paced)

## (a) What's already shipped

Last 14 commits (v1.0.2 → v1.6.88), in reverse chronological order:

| Commit | Version | Surface |
|---|---|---|
| `915a878` | v1.6.88 | fix Sini-stray-window leak + Resume picker merges all projects.json projects + per-phone scrcpy stderr → log file |
| `6b17946` | v1.6.86 | fix stray "Sini..." window + bleed-through (no startup scrcpy) |
| `f5698ef` | v1.6.85 | revert agent-card transparency (bleed-through) + Sinister Panel canonical colors + fix API offline status pill |
| `ead8dbb` | v1.6.84 | resizable window + bigger sidebar/logo + transparent cards + breathing glow |
| `5c30f51` | v1.6.83 | full audit + /api slash + install-apk endpoint + API.md doc |
| `9cfa830` | v1.6.82 | workstation API server (127.0.0.1:5077) + single Desktop entry |
| `b1fd331` | v1.6.81 | REVERT v1.6.80 live-drain freeze |
| `c38bedd` | v1.6.79+v1.6.80 | embed fixes + per-phone agent claims + advanced view + image paste |
| (CHANGELOG) | v1.6.71 | sidebar nav labels visible + `sinister-eve.exe` (8.1 MB PyInstaller onefile) shipped to Desktop |
| (CHANGELOG) | v1.6.70 | token-budget warning at 100k + `/budget` gauge |
| (CHANGELOG) | v1.6.69 | jcode skill-frontmatter parity (YAML `name`/`description`/`allowed-tools`) |

Plus the v1.0.2 milestone (20/23 operator directives green, 187/187 pytest pass, 26/26 slash dispatch — `_shared-memory/plans/rkoj-v1.0.2-review-test-2026-05-21/plan.md`).

## (b) What's in-flight

Nothing on disk. Last commit shipped clean. No abandoned WIP in `projects/rkoj/source/`.

## (c) What's still open and master-actionable

| # | Item | Source | Effort | Reversibility |
|---|---|---|---|---|
| 1 | Reply to Sanctum jcode-parity ASK with matrix flips for rows 5, 12, 15, 18, 21, 23, 24, 25, 26, 27, 28 in `jcode-feature-matrix.md`. Audit Forge + Term source state vs matrix; flip in-place where shipped. | inbox `2026-05-23T0710Z-from-sanctum-jcode-parity-ask.md` | 30-45 min | R1 |
| 2 | Decide projects.json v6 filter patch on `state.py::load_projects()`. Current behavior (show all 17 entries) intentionally matches v1.6.88 commit msg "Resume picker merges all projects.json projects". Reply to Sanctum NOTIFY explaining choice; do NOT auto-apply the filter without operator preference. | inbox `2026-05-23T0815Z-from-sanctum-projects-json-schema-update.md` | 10 min | R0 (no source change) |
| 3 | Archive the kernel-apk staging-race NOTIFY (reply_required: false, content was preserved in `ccd859c`, no action needed). | inbox `2026-05-21T1930Z-from-kernel-apk-staged-files-landed-in-my-commit.json` | 2 min | R0 |
| 4 | Audit + ACK the older Sanctum session-picker-spec ASK and forge-dashboard-spec ASK from 2026-05-21. RKOJ.exe v1.6.x already ships the picker functionality; the launcher tab spec may be superseded. Cross-reference current source. | inbox `2026-05-21T0300Z-session-picker-spec.json` + `2026-05-21T1108Z-forge-dashboard-spec.json` | 20 min | R0/R1 |
| 5 | Write `rkoj`-slug resume-point at end of session via `resume-point-write.ps1 -ProjectKey rkoj -AgentName rkoj -Mode resume`. v1.3 of the script has the slug→display-name lookup; first run will create the canonical dir. | CONTRACT 7 | 2 min | R0 |
| 6 | Append the matrix-flips + ack outcomes to `PROGRESS/rkoj.md`. Commit-and-push (push gated on operator OK; CLAUDE.md says no push to main without operator OK, but per-agent branch push is fine — see CONTRACT 7). | this plan | 5 min | R1 |

Total master-actionable effort: ~70-85 min. Loop-able end-to-end without operator gates.

## (d) What's operator-gated

These are cross-project but visible from `OPERATOR-ACTION-QUEUE.md` rows tagged `rkoj`:

| Row | Severity | One-liner the operator runs |
|---|---|---|
| Restart Claude Code | 🔴 | (Close + reopen the Claude Code session window) — activates 12 newly-resolvable MCPs (sinister-bus + sentinel + translator + librarian + watcher + auditor + triage + scribe + curator + custodian + stealth-browser + researcher) via the new junctions + 14 newly-enabled dev plugins at Sanctum project level. Not RKOJ-blocking; RKOJ.exe runs independently. |
| Set `ANTHROPIC_API_KEY` env var | 🟠 | `[Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY','sk-ant-...','User')` then restart any shell + RKOJ.exe. Unlocks Anthropic SDK direct tool-use loop (multi-step reasoning visible like jcode). Without it, RKOJ falls back to the existing `claude -p` one-shot path. |
| Install Rust toolchain (`rustup-init.exe`) | 🟠 | Download from `https://rustup.rs`, run `rustup-init.exe`, plus MSVC Build Tools if not present. Unblocks source-level jcode fork into `projects/sinister-rkoj/`. Until then sidecar shim at `tools/sinister-jcode-shim/` v0.1.0 wraps the prebuilt `jcode-windows-x86_64.exe` with Sinister env config. |
| `pip install -e D:/Sinister Sanctum/tools/sinister-review/` | ~~🟠~~ RESOLVED 2026-05-23T08:20Z | (No action — Sanctum-lane audit confirmed already installed editable; row in OPERATOR-ACTION-QUEUE has been flipped to ✅.) |
| Register `RKOJ` + `SinisterVault` scheduled tasks (admin) | 🟠 | Double-click `C:\Users\Zonia\Desktop\Sanctum-Wire-Tasks-AsAdmin.bat` — one UAC prompt registers both. Current `RKOJ` task `LastTaskResult=3221225786` (0xC0000142 STATUS_DLL_INIT_FAILED) → first run crashed at DLL init, task not re-arming. Alternate launch path (`Start-Console.ps1` / user double-click of `RKOJ.exe`) still works. |

Nothing on this list is RKOJ-source-blocking. The `rkoj` lane can complete its slate (a)-(c) without any operator click.

## (e) Reversibility class per row (per canonical-11)

- **R0** (no-impact / reversible at the file level): heartbeat write, PROGRESS append, plan write, cross-agent reply, inbox archive, resume-point write
- **R1** (local commit, easy revert via `git revert`): `jcode-feature-matrix.md` row flips, `state.py` filter patch (if applied), `PROGRESS/rkoj.md` updates
- **R2** (rebuilds artifact / re-ship of RKOJ.exe v1.6.89): NOT planned this turn — no `state.py` UI behavior change because v1.6.88's "merge all" was the most recent operator directive
- **R3** (cross-lane impact, requires sibling coordination): none in this batch
- **R4** (operator-only / reversibility wall): operator-gated rows above; not master-actionable

## (f) Recommended ordering + rough effort

1. **(c)#1** Audit Forge + Term source for jcode-parity matrix rows; flip in-place — **~30 min** — R1
2. **(c)#1 cont.** Drop reply to `cross-agent/<UTC>-rkoj-to-sanctum-jcode-matrix-flips.md` — **~5 min** — R0
3. **(c)#2** Reply to projects.json v6 NOTIFY explaining "keep show-all" decision per v1.6.88 operator intent — **~5 min** — R0
4. **(c)#3** Archive kernel-apk staging-race NOTIFY to `_archive/` — **~2 min** — R0
5. **(c)#4** Audit older session-picker + forge-dashboard ASKs; ack or close — **~15 min** — R0/R1
6. **(c)#6** Append outcomes to `PROGRESS/rkoj.md` + commit on the per-agent branch — **~5 min** — R1
7. **(c)#5** Write resume-point at terminal — **~2 min** — R0

Loop self-paces; cycle through rows. No operator gates between steps. At end-of-turn, write resume-point + emit human-readable summary per CONTRACT 6.

## Cross-references

- `_shared-memory/PROGRESS/rkoj.md` — this lane's append-only log
- `_shared-memory/PROGRESS/rkoj-workstation.md` — prior slug (subsumed under `rkoj` umbrella)
- `_shared-memory/PROGRESS/Sinister Sanctum.md` — sibling master agent
- `_shared-memory/knowledge/jcode-feature-matrix.md` — 30-row capability map (target of flips this session)
- `_shared-memory/plans/rkoj-v1.0.2-review-test-2026-05-21/plan.md` — v1.0.2 milestone (predecessor)
- `_shared-memory/plans/rkoj-qt-milestones-2026-05-21/plan.md` — Qt milestone test plan
- `automations/session-contracts.md` — 6 binding contracts
- `projects/rkoj/source/sinister_rkoj_qt/state.py` — `load_projects()` is the schema v6 patch surface
- `projects/rkoj/CHANGELOG.md` — version log
