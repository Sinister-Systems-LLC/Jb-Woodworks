# PROGRESS :: test-os (EVE on Sinister OS lane)

> Author: RKOJ-ELENO :: 2026-05-24
> Append-only, most-recent at top. Per no-bullshit doctrine: separate Shipped (verified) / In-flight (unverified) / Open (queued).

---

## 2026-05-24T12:40Z — Turn 1: fresh spawn, operator redirect to ship-now mode

Spawned in RESUME mode on `projects/sinister-os/`. No prior `Sinister OS` resume-point folder existed → first turn for this lane slug. Operator redirected mid-spawn:

> *"get this working how i want so we have a perfect operating system to run claude on and be my own open source operating system that i can forever expand that i have complete control of and ai is complete integrated. review github and see what all you can compile from other repos. and complete the entire thing and lets get to testing in docker to all this for me and make everything look like my sinister panel here ... grab the exact code from the sinister panel project folder and lets use that and the lets text look as the main OS look. call everything SINISTER and have all our systems direct in the operating system. make sure i have full options i use from my pc like playing steam games and such."*

**Implicit operator decisions (P0 Q1-Q10 resolved by this redirect):**
- Q1: Arch base — go (operator approves "complete the entire thing"; default stands).
- Q2: Desktop = **Sinister Panel as kiosk shell** (NEW — overrides Hyprland-only default; Hyprland still hosts the Panel kiosk).
- Q3: Browser default = Brave or Chromium (Panel kiosk uses Chromium; ratify later).
- Q4-Q10: defaults stand pending operator override.

### Shipped (verified)

- `_shared-memory/heartbeats/test-os.json` — fresh heartbeat, real UTC (`date -u` cross-check 12:39:48Z).
- `_shared-memory/PROGRESS/test-os.md` — this file.
- **Sinister Panel UI stack confirmed** via `package.json` read: Next.js 15.5.14 + React 19.2.0 + Tailwind 4.1.9 + lucide-react + TanStack Query + sonner + class-variance-authority. Dev port 3080. TypeScript. Path verified: `projects/sinister-panel/source/Andrew Panel/Sinister Panel/panel/dashboard/`.

### In-flight (unverified)

- P1 archiso Docker build scaffold — directory + Dockerfile + profiledef.sh + packages.x86_64 being written this turn. Smoke-test (`docker build`) NOT executed this turn — operator's machine is Windows + git-bash; Docker availability not pre-confirmed. Will attempt; if unavailable, mark `claimed-but-unverified` per doctrine.
- Panel-as-shell wiring doc — being written this turn; one path picked (Wayland kiosk via Hyprland + chromium --kiosk pointing at Panel Next.js standalone build).

### Open (queued)

- **Real ISO build** — requires Docker or a Linux build VM. Operator action: confirm Docker Desktop is installed/running on this machine OR spin up an Arch VM for build-host.
- **GitHub reconnaissance** — operator asked "review github and see what all you can compile from other repos." Out-of-scope for turn 1 (would spend the entire turn on enumeration). Queued as a dedicated subagent task — see resume-point.
- **EVE daemon (P3 work)** — blocked on P1 ISO booting first.
- **Steam + Proton stack (P4 work)** — packages.x86_64 will list them, but actual gameplay verification is P4.
- **Cutover from Windows (P5)** — operator-gated explicit "P5 cutover go" required.

### Lane-discipline note

Current git branch is `agent/sinister-sanctum/grant-autonomy-followup-2026-05-23` (Sanctum master's branch). Switching mid-session to `agent/sinister-os/p1-docker-bootstrap-2026-05-24` would orphan Sanctum's working-tree edits. Approach: stage + commit the sinister-os scaffold on a **new branch** off current HEAD via `git switch -c`, leaving Sanctum's other changes untouched on the old branch. Auto-push 2.0 picks up whichever branch is current.

### No-bullshit ledger for this turn

- Words I will NOT use: "OS shipped" / "complete" / "Docker tested" / "boots" — none of those are true after one turn.
- Words I WILL use: "scaffolded" / "documented" / "queued" / "smoke-test pending Docker availability".
- Quality-degradation signals: cold-start step count (10 currently — at ceiling); this lane's first turn does NOT add new doctrine rows, only project-local files.
