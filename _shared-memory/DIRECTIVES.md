# Sanctum :: Standing Operator Directives (cross-agent)

Every spawned Claude session reads this on cold-start. Most-recent at top.

---

## 2026-05-19 — Plugin discipline (no marketplace cancer) — HARD RULE

Operator (verbatim): "remove all the shit we added. i want everything to be our shit that we have no asana, discord plugins or any of that slop i told you to review things not add of of this junk to the machine. you should know better."

A sibling Sanctum master-lane session shipped `Install-Claude-Plugins.bat` + a 172-plugin clipboard helper. Result: 26 third-party plugins + 7 Anthropic devtools got installed; the broken `hookify` userpromptsubmit.py started blocking every prompt with `[Errno 2]`. Operator scorched-earth-purged the entire `claude-plugins-official` marketplace + all associated cache/data/marketplace dirs + the bulk-installer scaffolding (archived at `D:\Sinister Sanctum\_archive\automations\2026-05-19-plugin-installer-purged\`).

**Standing rule — every Sanctum agent, every action involving Claude Code plugins / marketplaces / hooks:**

1. **NEVER bulk-install plugins** from any marketplace. No `Install-*.bat`, no clipboard-helpers that paste install commands at scale, no `for plugin in list; /plugin install` loops.
2. **Per-plugin operator approval is mandatory** — even for Anthropic-built marketplace tools (`code-review`, `commit-commands`, `claude-md-management`, etc.). Operator must say "review this plugin" via the case-study workflow; only THEN install.
3. **MCPs the operator owns are sacred:** `ruflo` + `vault` (in `~/.claude.json::mcpServers`) + the 13 Sinister-bots in `D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\`. NEVER add a marketplace MCP that competes with or impersonates these.
4. **`~/.claude.json` + `~/.claude/settings.json` edits require either (a) explicit operator approval for that specific edit, or (b) a plan-file-approved cleanup plan like the 2026-05-19 purge.** Self-modification of plugin/MCP configs is blocked by default.
5. **Hooks are operator-owned.** Any plugin that registers a `UserPromptSubmit / PreToolUse / PostToolUse / Stop` hook gets surfaced to the operator BEFORE install; broken hook paths block every prompt (proven by the hookify userpromptsubmit.py incident 2026-05-19).
6. **Reversibility:** any plugin install MUST be reversible via the case-study `_archive/` workflow. The bulk-install scaffolding shipped 2026-05-19 violated this — archived 2026-05-19. Backups of pre-purge configs at `C:\Users\Zonia\.claude\backups\2026-05-19-purge\`.

Brain entry: `D:\Sinister Sanctum\_shared-memory\knowledge\marketplace-plugin-purge.md` (full incident postmortem).

---

## 2026-05-19 — Operator preference: purple default for all new agents

Operator (verbatim): "have all agents color purple by default and make that feature and naming fully work."

**Standing rule:**

- Default accent for ANY new agent spawn = **purple** (Sanctum purple `#7A3DD4`).
- Operator can override per-spawn via `-AccentColor` flag (purple / magenta / cyan / green / yellow / white / random).
- Agent name is persisted in `automations/session-templates/agent-prefs.json` per project — never re-asked unless `-AgentName` flag overrides.
- The `SINISTER_AGENT_NAME` env var is exported to the bash subshell so the cold-start agent reads it via `$env:SINISTER_AGENT_NAME` and uses it consistently in inbox + heartbeat + PROGRESS logs.

`Get-RandomColor` still exists for operators who want variety — invoke explicitly via `-AccentColor random`.

---

## 2026-05-19 — Skill review + case-study workflow (operator thumbs-up/down → fleet or archive)

Operator (verbatim): "add idea to md files. auto tests that i can tell you to do. like review this skill or compare this skil and you do a full case study test. to build a skill better than how we dfounmd it etc. give me results i thumbs up or down on what we do. add to fleet or trow to archives"

**The idea:** operator triggers a structured review of any skill / tool / invention in the Sanctum. Master agent runs the case-study, returns a verdict with concrete recommendations, operator thumbs-up/down → master adds to fleet (`bots/` / `tools/` / `skills/`) OR moves to `_archive/`.

**Standing rule — every Sanctum agent that handles "review this <X>" / "compare <X> and <Y>" / "case-study <X>":**

1. **Inputs accepted:**
   - `review <name>` — single skill/tool review
   - `compare <a> vs <b>` — side-by-side case study
   - `case-study <name>` — deeper investigation (multiple agents in parallel if scope warrants)
   - `improve <name>` — rebuild proposal vs the existing impl

2. **Method:**
   - Locate the target (tool card at `tools/<slug>/`, skill at `skills/<slug>/`, invention at `inventions/<slug>.md`, bot at `bots/agents/<name>/`)
   - Read source + docs + recent changelog + brain entries that mention it
   - Spawn an Explore subagent (or do it inline) for codebase grep + integration usage
   - Produce a structured verdict with **5 sections**:
     1. **What it is** (1 paragraph)
     2. **Strengths** (3-5 bullets, concrete)
     3. **Weaknesses + risks** (3-5 bullets, concrete; cite file:line)
     4. **Better-than-found proposal** — what a rebuild looks like; ~30-100 LOC outline OR "no rebuild, ship as-is"
     5. **Recommendation** — `KEEP` / `KEEP-WITH-CHANGES` / `ARCHIVE` / `REPLACE-WITH-NEW`

3. **Verdict file:** master writes the case study to `_shared-memory/case-studies/<UTC-iso>-<target-slug>.md` (append-only audit log; never edit, only add discoveries below). Includes the 5 sections plus a `## Operator decision` block left blank for the operator's thumb.

4. **Operator decides:** operator reads, drops a `👍 add to fleet` OR `👎 archive` reply (or any free text). Master then either:
   - **Adds to fleet:** updates `tools/_INDEX.md` / `skills/_INDEX.md`, writes the changes proposed in section 4, runs Codex peer-review on any net-new code per the existing standing rule.
   - **Throws to archives:** moves the target folder to `_archive/skills/<slug>/` with a `_archived.md` reason file, updates the `_INDEX.md` to mark `status: archived`. Reversible — the operator can promote it back later.

5. **Tag standard for `_shared-memory/case-studies/*.md`:** `tags: [review|compare|case-study|improve, <target-slug>, <verdict>]` so future agents can grep.

**Entry-points (master-runnable today):**
- `/review <name>` — operator slash-cmd in any Claude session (master agent picks it up)
- `POST /api/case-study` on RKOJ Console (planned; routes to the operator's master session via inbox)
- Direct: operator says "case-study sinister-crawler" or "compare sanctum-git vs sanctum-vault"

**Why this matters:** the fleet grows by accretion today — every new skill / tool / invention lands and stays. Without a review loop, debt accumulates. This loop closes the loop: every artifact gets a thumb at some point, and dead weight moves to `_archive/` so the fleet stays sharp.

**Files added 2026-05-19 by Sinister Sanctum master:**
- `D:\Sinister Sanctum\inventions\2026-05-19-skill-case-study.md` (the invention card with deeper writeup)
- `D:\Sinister Sanctum\_shared-memory\case-studies\.gitkeep` (audit-log directory seeded; future verdicts land here)

---

## 2026-05-19 — `[UPDATE]` inbox pattern (hot-reload without losing agent context)

Operator (verbatim): "get to a point where i can use and test things and actively add things without disrupting my claude agents and they will heartbeat or reping or something without stopping and loosing context they will get the updates if they can."

**Standing rule — every Sanctum agent, every turn:**

In addition to `[CONFIG] model=<X>` (existing rule), every agent that surfaces an inbox message starting with `[UPDATE] <subkind>` MUST:

| Subkind | Action |
|---|---|
| `[UPDATE] refresh-prefs` | re-read `_shared-memory/agent-prefs.json` for own entry; apply changes; ack `[ACK refreshed]` |
| `[UPDATE] branch-switch new=<branch>` | run `git checkout <branch>` in cwd; ack `[ACK on <branch>]` or `[DECLINE reason]` |
| `[UPDATE] palette-rebuild` | (RKOJ-spawned only) refetch palette index; ack |
| `[UPDATE] knowledge-recheck slug=<name>` | re-read the brain entry; if it materially affects current work, apply; ack |
| `[UPDATE] noop` | heartbeat probe; ack with `[ACK alive uptime=<s>]` — operator uses this to verify the session is responsive |

DO NOT restart your loop. DO NOT lose context. The update happens on the NEXT turn boundary; if you're mid-thinking, finish the current turn first then apply.

Senders authorized: RKOJ Console's `POST /api/inbox/broadcast`, `POST /api/inbox/send`, and the dedicated `POST /api/inbox/update-ping` (which always emits tag `update`). Pairs with Rule 9 (heartbeat + inbox_poll) and the `[CONFIG]` rule below.

Companion frontend (workbench UI surface): the RKOJ Console subscribes to `GET /api/sse/changes` and live-patches CSS / assets without a page reload, and toasts a click-to-reload nag for JS/HTML changes. See `_shared-memory/knowledge/rkoj-hot-reload-pattern.md`.

---

## 2026-05-19 — CROSS-AGENT COORDINATION (agents help each other; don't wait for the operator)

Operator (verbatim): "make sure all agents that can help each other do things like this. do everything you can in parallel and use as many local and agents you need to speed this shit up."

**Standing rule — every Sanctum agent, every turn:**

If during your work you realize **another currently-online agent could be helping you OR could benefit from what you just learned**, DO NOT wait for the operator to relay. Coordinate directly via inbox:

1. **Tag-based handshake (the pattern from the 2026-05-19 TT<->Snap mutual-info channel):**
   - You're TT agent + you need Snap-specific knowledge -> `inbox_send(to="Sinister Snap API", body="[ASK] hey — I'm dumping libclient.so for SS03. You hit anything similar in pure-API track? Send back what you remember or [PASS] if nothing.", tags=["ask","cross-agent","cross-info"])`
   - Snap sees on its next `inbox_poll`, replies `[ANSWER]` or `[PASS]`.
2. **Broadcast pattern** (one-to-many): you discovered something useful for the whole fleet -> `POST /api/inbox/broadcast` body `{body: "[DISCOVERY] Yurikey52 cert rotated successfully via rka_keybox_rotate.sh. All phone-stack agents can resume their tracks.", tags: ["discovery","cross-agent"]}`. The RKOJ server fans out the message to every agent in `/api/sessions`. RkojHelpers exposes `broadcastToAllAgents(body, tags)` for convenience.
3. **Delegation pattern** (one-to-one work hand-off): you need help that's specifically in another agent's lane -> `inbox_send(to="<other>", body="[DELEGATE] please run X and reply with the result", tags=["delegate","ask"])`. Per Rule 9, the recipient must surface DELEGATE inboxes to operator BEFORE acting on them — operator decides if cross-lane work is permitted. Recipient replies `[ACK doing it]` then `[DONE result]` or `[DECLINE reason]`.
4. **Knowledge-share pattern** (any agent -> the brain): if you discovered something durable, ALSO append it to `_shared-memory/knowledge/<topic>.md` (per the canonical-13 Rule 5). Inbox messages are ephemeral; brain entries are forever.
5. **Cross-agent etiquette:**
   - Tag every cross-agent message with `cross-agent` so it's grep-able later
   - Lead with `[ASK]` / `[ANSWER]` / `[DISCOVERY]` / `[DELEGATE]` / `[ACK]` / `[DONE]` / `[PASS]` / `[DECLINE]` so the receiver can pattern-match in one glance
   - Don't ping the same agent more than 3 times in 5 minutes without operator OK (avoid storms)
   - If your message is operationally critical, ALSO append to `_shared-memory/PROGRESS/<agent>.md` so the audit trail is durable

**Operator visibility:** RKOJ's Activity Feed surfaces all cross-agent messages (filter by `cross-agent` tag). The bell in the ribbon increments for `[ASK]` messages directed at the currently-viewing operator's agent.

**Why this matters:** the fleet gets smarter when agents coordinate horizontally instead of all routing through the operator. Operator's role becomes orchestration + adjudication, not relay.

---

## Standing rules — canonical 14 (fast-scan index, 2026-05-19)

1. Rule 9 — heartbeat + inbox_poll every turn
2. `[CONFIG] model=<name>` inbox self-apply (no kill-and-respawn)
3. Per-agent branch discipline (`agent/<slug>/<topic>`, double-remote push)
4. Codex peer-review on auth/crypto/payment/secrets/>100 LOC pushes
5. The Sanctum Brain — read before risky actions, write discoveries after
6. ADB phone containerization — `adb -s <SERIAL>` always; PC state never leaks
7. Authorship line on every new `.bat` / `.md` / `.ps1`
8. Log progress to `PROGRESS/<agent>.md` on every meaningful milestone
9. UI design system — dashboard-skeleton canonical; purple Sanctum-only; iOS-blue panel-only
10. Lane discipline — master never touches product-repo `source/` / never modifies `~/.claude/.mcp.json`
11. Expanded authority (sandbox lifted; reversibility still gates destructive ops)
12. **Panel surfaces route loopback-first** via `tools/panel-config/panel-config.json`; tag cells with source (NEW 2026-05-19)
13. Operator-action queue stays mirrored in `_shared-memory/OPERATOR-ACTION-QUEUE.md` for one-glance status
14. **Sanctum auto-pushes to GitHub every 30 min** via `SinisterSanctumAutoPush` task; daemon skips when working-tree clean + no unpushed commits; only commits on `main`; agents work on per-agent branches (NEW 2026-05-19)

Detailed sections below; most-recent ask at the top.

---

## 2026-05-19 — Sinister Vault is the master storage layer (operator + Leo collaborative)

Operator (verbatim): "reserve 1000 gb of my d drive and make the storage server that connects all with mcp so that we can add that to the exe and leo and i can work on same thing at same time and not interfere with each other ... auto start when pc launch ... simple ui control system using our ui system ... multi google claude account support and a way for leo and i to have different commit each time we upload ... make it so we can sync files like tresorit so leo can see and have the exact same file to work out of."

**Standing rule — every Sanctum agent, every cold-start:**

The **Sinister Vault** lives at `D:\sinister-vault\` (1 TB soft quota, warns at 950 GB). It is the canonical collaborative storage layer for operator + Leo. Three tiers:

1. **Repos tier** — `D:\sinister-vault\repos\` (Gitea-backed, browseable at `http://localhost:3000/`). Every meaningful artifact gets versioned here. Each commit is signed by the user's Gitea identity (operator / leo / future users). Commit-as-upload pattern: drop a file → `git add` → `git commit` → `git push` → audit log captures it → RKOJ Vault drawer surfaces it. See `tools/sanctum-git/vault-integration.md`.
2. **Sync tier** — `D:\sinister-vault\sync\` (Syncthing peer-to-peer). Anything dropped here syncs both ways between operator + Leo in seconds, like Tresorit. End-to-end encrypted. See `tools/sinister-vault/syncthing/README.md`.
3. **Snapshots tier** — `D:\sinister-vault\snapshots\` (Vault daemon-managed). Periodic snapshots of repos sub-trees; never overwrite, append-only.

The **Vault daemon** runs on `localhost:5078` (FastAPI, port-distinct from RKOJ's :5077). Auto-starts at logon via `Get-ScheduledTask SinisterVault`. RKOJ proxies `/api/vault/{quota,audit,health}` so the workbench's Vault drawer shows live state.

The **Vault MCP server** (`agents/vault/`) exposes `vault.*` tools to any Claude session: `commit`, `push`, `pull`, `list`, `search`, `sync_status`, `accounts`, `snapshot`, `audit`. Operator must re-run `install-fleet.ps1` to register it.

**Multi-account:** each user has a profile at `D:\sinister-vault\accounts\<name>.json` (operator.json, leo.json, …). Profile references a NAMED env var for the Anthropic API key (operator → `ANTHROPIC_API_KEY`, leo → `LEO_ANTHROPIC_API_KEY`) — per-user billing isolated, no keys on disk. Each profile carries default agent identity + accent color + Gitea user + Syncthing device ID. See `tools/sinister-vault/ACCOUNTS.md`.

**Quota guardrails:** vault daemon writes a warning audit event when used > 950 GB, refuses new snapshot/push when used > 1024 GB (returns HTTP 507). Agents must respect this.

**Cross-cutting:** the existing Custodian backup (`tools/sinister-vault/` is orthogonal — Custodian protects against drive loss; Vault enables collaboration). Both can coexist.

---

## 2026-05-19 — RKOJ.exe is the master workstation (renamed from Sanctum-Console)

Operator (verbatim): "this will be our main project we are going to call it RKOJ.exe ... two tabs ... one for the adb device manager. one for agents to make create rework on make new things ... full customization dev tools per page we are on. this is a work bench ... top bar like the top bar of excel ... full customizable popout system ... cycle points so that we can one click button to pick back up projects ... set times projects will do set things and a scheduler ..."

**Standing rule — every Sanctum-side surface, every agent, every cold-start:**

The flagship console binary is **`RKOJ.exe`** (built from `D:\Sinister Sanctum\automations\window-manager\`, output `dist/RKOJ/RKOJ.exe`). Source folder, endpoints, auth, mobile surface — all unchanged. UI is 2 tabs (`ADB Devices` + `Agents`) + Excel-style ribbon + dev-tools rail + popout system + cycle-points + scheduler. Sanctum purple accent stays binding (master-surface rule from `docs/UI-DESIGN-SYSTEM.md`).

**What every agent must know:**

1. **Don't recreate the 11-sidebar UI** — operator explicitly killed it. Two tabs only. Other features live in dev-tools-rail drawers OR Cmd+K command palette.
2. **Cycle points** = first-class. JSON snapshots at `_shared-memory/cycle-points/<project>/<slug>.json`. POST `/api/cycle-points` to save, `POST /api/cycle-points/{slug}/resume` to relaunch with captured agent + model + mode + custom_prompt + open-files hint.
3. **Scheduler** = first-class. Cron entries in `_shared-memory/schedule.json`. Daemon loop runs inside RKOJ server (asyncio task, 30s tick, Semaphore(5)). Kinds: `script`, `spawn-agent`, `inbox`, `resume-cycle`, `http`.
4. **Popout system** = BroadcastChannel('rkoj-state') for cross-window sync. `window.open()` with `#popout=<view>&state=<base64>` fragment. Tracked in `localStorage.rkoj.popouts`.
5. **Build pipeline** = `Build-Sanctum-Console.bat` (or the `RKOJ.bat` one-click for launch). Knows: `set -o pipefail`, PowerShell-wrapped robocopy, `--disable-pip-version-check`, `croniter` is required (new dep).
6. **Live-update workflow:** source-mode python is the dev surface; rebuild EXE periodically for the deploy artifact.

---

## 2026-05-19 — Panel surfaces route loopback-first + tag the source

Operator (verbatim): "update panel like i said to local host when you update."

**Standing rule for every Sanctum surface that pulls panel data:**

1. Route the primary URL first, fallback URL second. Both come from `D:\Sinister Sanctum\tools\panel-config\panel-config.json`. **Never** hardcode `http://127.0.0.1:5055` or `https://snap.sinijkr.com` in a new caller — call the loader (`Get-PanelConfig` in PowerShell, `_load_panel_config()` in Python).
2. Tag every panel-data cell with which source filled it: `local` / `prod` / `offline`. The trophy-case section header in `start-sinister-session.ps1` and `GET /api/trophy` in `window-manager/server.py` both do this.
3. When you add a new consumer (third script, fourth bat, etc.), document it in `tools/panel-config/README.md` and append a Discoveries entry to `_shared-memory/knowledge/panel-localhost-routing.md`.
4. Keep a hardcoded URL fallback as the safety net if `panel-config.json` parse fails — never trust the disk fully.

**Shipped 2026-05-19 by Sinister Sanctum master:**
- `tools/panel-config/panel-config.json` (the knob)
- `tools/panel-config/README.md` (the tool card)
- `automations/start-sinister-session.ps1` — `Get-PanelConfig` + reworked `Get-PanelStat` + dynamic trophy header
- `automations/window-manager/server.py` — `_load_panel_config()` + `/api/trophy` returns `source` field
- `docs/PANEL-INTEGRATION.md` — appended routing section
- `_shared-memory/knowledge/panel-localhost-routing.md` (brain topic, status: fixed)

---

## 2026-05-19 - EXPANDED AUTHORITY (sandbox restrictions lifted)

Operator (verbatim): "you dont need to build all these bats anymore. we fixed these things so you can do everyting."

**What changed:** classifier-side blocks that historically forced agents to delegate everything risky to operator-clicked `.bat` files are no longer in play. Agents may execute the actions directly when they make sense.

**What stays the same — judgment still required:**

- **Reversibility** — destructive operations (`rm -rf`, `git push --force`, killing shared services, dropping tables, unregistering scheduled tasks) STILL require operator confirmation unless explicitly pre-authorized for the current scope. Scope = what operator said, not beyond.
- **Lane discipline** — master agent still does NOT touch product-repo source under `D:\Sinister Sanctum\projects\<repo>\source\` or `D:\Sinister\01_Projects\Sinister\<repo>\source\`, and never pushes any product repo. Per-agent branch rule still holds. Phone containerization (per-serial `adb -s <SERIAL>`, never bare) still holds.
- **Secrets** — `_vault/` (auth-keys.json, vault passphrases) is still off-limits to bot reads unless operator explicitly OKs the read.
- **`~/.claude/.mcp.json`** — still operator-owned. A bad edit kills every active session in the fleet.
- **Cross-zone external writes** — sending unsolicited inbox messages to another agent's queue about a problem the operator didn't ask you to escalate is still over-reach. Surface to operator; let them decide who handles it.

**What this UNBLOCKS:**

- `Register-ScheduledTask` / `Unregister-ScheduledTask` directly (previously routed through `install-task.ps1` for operator click).
- `robocopy /MIR` to operator paths (Desktop, etc.) directly.
- Process-launch + service-restart cycles (the live-update loop on the Sanctum Console).
- One-shot bash/PowerShell pipelines without needing a `.bat` wrapper.

**Convention for the future:**

`.bat` files are now operator **convenience**, not agent **workaround**. Create one when:
1. Operator will run it repeatedly + wants a double-click entry (e.g. `Build-Sanctum-Console.bat` for periodic EXE rebuilds).
2. Operator wants to run it without a Claude session open.
3. The operation is recurring + benefits from being checked into the repo (audit trail).

Skip the `.bat` when:
1. One-off action you're doing yourself right now.
2. Diagnostic step that won't repeat.
3. Operator hasn't asked for it.

The 5 Desktop bats from the 2026-05-19 workstation sprint (`Build-Sanctum-Console.bat`, `Open-Sanctum-Console.bat`, `Sanctum-Desktop.bat`, `Sanctum-LAN.bat`, `Start-Sanctum-Console.bat`) STAY — durable operator entry-points. Future agents reuse them; don't recreate.

---

## 2026-05-19 - INBOX `[CONFIG]` self-apply rule (pairs with Rule 9 from 00-RULES)

**Standing rule — every Claude session, every project, every turn:**

When `inbox_poll` (or any equivalent inbox read) surfaces a message whose body starts with `[CONFIG] model=<NAME>`:

1. Acknowledge: `inbox_reply msg_id=<id> response="[ACK] swapping to <NAME>"` (or equivalent send).
2. Invoke the slash command `/model <NAME>` yourself (Claude Code honors `claude-opus-4-7`, `claude-opus-4-6`, `claude-sonnet-4-6`, `claude-haiku-4-5-20251001`, plus aliases `opus` / `sonnet` / `haiku`).
3. Continue the prior task at the new intelligence level — DO NOT restart your loop or ask the operator for direction; the operator already chose for you via the Sanctum Console.

Senders: the Console's `POST /api/agents/{name}/intelligence` is the only authorized originator. Tag is `config,model`. Bodies may include `fast=true` for Opus 4.6 fast mode.

Pairs with Rule 9 (heartbeat + inbox_poll). The intent is "operator clicks the intelligence chip in the console, agent continues its task at the new level on its next turn — no kill-and-respawn." Worst case: the swap lands on the next turn boundary, not mid-thinking.


## 2026-05-19 - PER-AGENT BRANCH DISCIPLINE (so we don't step on each other)

Operator directive: "allow us to have our own github self hosted so we can push all our files to a self storage system so that we can get away from github down the road and not step on each other's toes while we work on projects and can in real time not interfere with each other."

This rule pairs with the new `sanctum-git` tool (self-hosted Gitea on `http://localhost:3000` — see `D:\Sinister Sanctum\tools\sanctum-git\`).

**Standing rule — every Claude session, every project, every push:**

1. **Every session works on its OWN branch.** Branch name:
   ```
   agent/<your-SINISTER_AGENT_NAME-slugified>/<short-topic>
   ```
   Examples:
   - `agent/sinister-snap-api/pure-api-ss03`
   - `agent/sinister-sanctum/master-tooling-v6`
   - `agent/sinister-tiktok-emu/argos-port`
   - `agent/sinister-panel/eve-observations-card`

   Slugify: lowercase, ASCII, dashes between words. Drop "Sinister " prefix only if the name already contains a clear lane (e.g. `Sinister Snap API` -> `sinister-snap-api`).

2. **Branch off the integration point the operator names.** Default is `main`. If the operator says "branch from `dev`" or "branch from `release-v2`", use that.

3. **DO NOT merge cross-agent branches without operator OK.** Even trivial merges. Even your own branch into `main`. Even a fast-forward. Every merge needs the operator to say "merge X into Y" first.

4. **When you `git push`, push to YOUR branch on BOTH remotes.**
   - `origin` -> github.com (existing)
   - `sanctum` -> `http://localhost:3000/<gitea-user>/<repo>.git` (new)
   - The mirror tool handles the sanctum side: `git-mirror.ps1 -Cmd push -ProjectKey <key>`. Push to `origin` with your normal `git push` flow.
   - Or `Mirror-To-Sanctum-Git.bat` (Desktop) for one-click push to sanctum.

5. **Conflict-avoidance:** per the existing `PARALLEL-AGENT-COORDINATION.md` ownership zones PLUS this branch rule. Two layers of safety:
   - Ownership zones say "don't touch files in another agent's zone."
   - Branch discipline says "even within your zone, don't push to a branch another agent is using."

6. **Single-pane view:** `git-mirror.ps1 -Cmd status` (or `Mirror-To-Sanctum-Git.bat` -> `status`) shows every project's local HEAD, sanctum HEAD, and github HEAD. Run it before starting work to see who else is currently active.

7. **First-time setup the operator does once:**
   - Double-click `C:\Users\Zonia\Desktop\Sanctum-Git-Start.bat`
   - Open `http://localhost:3000`, complete install wizard, create `operator` admin
   - Fill in `D:\Sinister Sanctum\tools\sanctum-git\.env`
   - Then any agent can run `git-mirror.ps1 -Cmd init -ProjectKey <key>` to wire a project

**Why this matters:** before this rule, two agents working on the same repo could both push to `main` (or worse, force-push) and clobber each other's work. With per-agent branches on a self-hosted mirror, the operator can review divergent work side-by-side and merge in their own time, without GitHub rate limits or PAT scope dances breaking the flow.


## 2026-05-19 - Codex peer-review (cross-check standing rule)

Operator directive: "build in to the agents section a way we can use that codex skill that works alongside claude so they can keep each other in checks. Skills we build, review or look into, tools, inventions all of that update memory for all of this."

**Standing rule — every Claude session, every project, every push:**

If you're about to push code that touches **auth, crypto, payment, secrets, or > 100 LOC**, request a Codex review via:

- **`POST /api/codex/review`** (when Sanctum Console is up — preferred):
  ```json
  { "content": "<diff or file body>", "context": "<what you're changing and why>",
    "language": "python", "depth": "deep" }
  ```
- **CLI fallback** (Console down):
  ```
  python "D:\Sinister Sanctum\tools\codex-companion\codex.py" --review <file> --depth deep
  ```

Document the verdict (`pass` / `warn` / `fail`) in your `_shared-memory/PROGRESS/<agent>.md` entry **and** in the file's runlog. Reference the review id (`<UTC-iso>-<sha1>`) so the operator can audit later.

**If Codex returns `fail` — or `warn` with any `severity: high` findings — BLOCK the push** and surface the findings + summary to the operator. Do not retry-until-pass; fix the underlying issue first.

Depth tier guide:
- `quick` (gpt-4o-mini, 30s) — lint sweep, < 50 LOC.
- `standard` (gpt-4o, 60s) — normal feature PR, 50-500 LOC.
- `deep` (o1-mini, 180s) — auth/crypto/payment, architectural, > 500 LOC.

Graceful degradation: if `OPENAI_API_KEY` is unset the skill returns `{ok: false, error: "no API key ..."}`. For high-risk pushes (auth/crypto/payment) treat that as BLOCK and ask the operator to set the key. For low-risk pushes you may document the skip in your runlog and proceed at your discretion.

Tool home: `D:\Sinister Sanctum\tools\codex-companion\`. Knowledge topic: `D:\Sinister Sanctum\_shared-memory\knowledge\codex-companion-usage.md`. Invention: `D:\Sinister Sanctum\inventions\2026-05-19-codex-companion.md`. Reviews log: `D:\Sinister Sanctum\_shared-memory\codex-reviews\<UTC-iso>-<sha1>.json` (append-only).

The fleet now has a peer-review counterweight from a different model family. Use it. The whole point of having Claude + Codex side-by-side is that they catch each other's blind spots — but only if you actually ask.


## 2026-05-19 - THE SANCTUM BRAIN (shared knowledge base, grows forever)

Operator directive: "i need you to add to the memory system a way i can tell agents to fix things like this they find that needs fixed and update and add the fix to a place all agents can see and use and grow knowledge into like a brain for each thing like this. deeply think on it and update memory files."

**Standing rule — every Claude session, every project, every turn:**

Sanctum has a SHARED BRAIN at `D:\Sinister Sanctum\_shared-memory\knowledge\`. One markdown file per topic. Append-only. ALL agents read and write it.

### When YOU discover a bug, gotcha, fix, or workaround:

1. **Check first** — is this already in the brain?
   ```
   ls "D:\Sinister Sanctum\_shared-memory\knowledge\*.md"
   ```
   Or `GET http://127.0.0.1:5077/api/knowledge?search=<keyword>` (if Console up).

2. **If the topic exists:** append a new "Discoveries" entry to its log (most-recent at top). Format:
   ```markdown
   ### YYYY-MM-DD HH:MM by <SINISTER_AGENT_NAME>
   What you found. New evidence. Edge case. Better fix.
   ```

3. **If the topic doesn't exist:** copy `_TEMPLATE.md` to `<slug>.md`, fill in Problem / Why / Fix / first Discovery. Update `_INDEX.md` to add a row.

4. **Update Status** if your discovery changes it:
   - `open` (no fix) → `workaround` (you found one) → `fixed` (real fix shipped) → `superseded` (newer topic replaces this)

### When you ABOUT TO DO something:

Before attempting any non-trivial action (a push, an install, a phone command, an API call to a new service), grep the brain:
```
grep -l "<your-keyword>" "D:\Sinister Sanctum\_shared-memory\knowledge\"*.md
```

If the brain says "known issue + workaround" — apply the workaround FIRST. Don't waste cycles rediscovering.

### What the brain is FOR

- GitHub auth scopes that confused everyone for 4 minutes
- PowerShell parser quirks (em-dashes without BOM, empty Read-Host prompts)
- Anti-detect gotchas (scrcpy VirtualDisplay, Snap camera blocking)
- Build-system landmines (PyInstaller hooks-contrib missing, pip self-upgrade breaking venv)
- Phone-side things (ADB containerization, frida-server pushing)
- Anything where the next agent shouldn't have to spend the same 5-15 minutes rediscovering it

### What the brain is NOT for

- Time-sensitive operator instructions → DIRECTIVES.md (this file)
- Per-agent progress notes → PROGRESS/<agent>.md
- Domain knowledge that's not actionable ("we use git", "purple is the accent") — only fix-shaped knowledge
- Duplicates — append to the existing topic instead

### Tools to write to the brain

1. **Direct write** — `_TEMPLATE.md` → copy → fill → save (markdown).
2. **`C:\Users\Zonia\Desktop\Log-Knowledge.bat`** — operator-side one-click append.
3. **`POST /api/knowledge/append`** — Sanctum Console endpoint:
   ```json
   { "slug": "...", "agent": "Sinister Snap API", "kind": "discovery",
     "title": "...", "body": "..." }
   ```

### Tools to read the brain

1. **Browse** — `_INDEX.md` is the catalog, sorted by recent activity.
2. **`C:\Users\Zonia\Desktop\Browse-Knowledge.bat`** — operator-side TUI.
3. **`GET /api/knowledge`** — list all topics.
4. **`GET /api/knowledge/{slug}`** — read one topic.
5. **`GET /api/knowledge?search=<query>`** — full-text search across all topics.

### Why this matters (the philosophy)

A single Claude session is bounded by its context window. The fleet is not. Every fix you discover should outlive your session. Every gotcha I (or another agent) hit yesterday shouldn't burn another agent's clock tomorrow.

**The brain is how the Sinister fleet gets smarter than any single agent.** It compounds. By month 3, the brain will have hundreds of topics covering every recurring landmine in the operator's stack. Cold-starts will be 10x faster because new agents will land already knowing what doesn't work.

Treat every "I just figured this out" as an opportunity. Write it down. Twenty minutes saved per future agent x N agents x N weeks = the whole point of having a fleet.


## 2026-05-19 - ADB PHONE CONTAINERIZATION (per-phone isolation)

Operator directive: "in the adb section that each phone is a container and will have no flags from what the pc has like running frida server unless we pass it through to that specific phone. add notes like this to the community md files so all agents will know how to use this."

**Standing rule for every agent that touches ADB / phone control:**

1. **Each connected phone is its OWN sandbox/container.** Operations on phone P1 must not leak to phone P2 (and vice versa).

2. **PC-side flags / state DO NOT leak through ADB by default.** Examples that must be kept on PC unless EXPLICITLY pushed to a phone:
   - frida-server running on the PC (must NOT auto-bind to a phone unless `adb -s <serial> push` + `adb -s <serial> shell` explicitly executed for THAT phone)
   - PC-side proxies (e.g. mitmproxy, charles, burp) — phones must be configured separately per-phone via `adb -s <serial> shell settings put global http_proxy ...` or per-phone WiFi config
   - PC-side env vars (ANTHROPIC_API_KEY, etc.) — never `adb shell setprop` them globally; always per-serial
   - Anti-tamper detection — running on PC must not assume phones have same protections

3. **Required pattern for every adb invocation:**
   ```
   adb -s <SERIAL> shell <cmd>          # GOOD: explicit phone target
   adb shell <cmd>                       # FORBIDDEN unless only one phone is connected AND that's intentional
   ```

4. **Per-phone state lives at:**
   - `D:\Sinister Sanctum\_shared-memory\notes\phones\<SERIAL>.md` — capabilities, last attestation, installed modules, current proxy
   - Read this BEFORE any push-frida / push-module / configure-proxy command
   - Update it AFTER any such command

5. **When pushing frida-server to a phone (example flow):**
   ```
   # P1 only — do NOT run on P2 unless P2 explicitly requested
   adb -s <P1_SERIAL> push frida-server-android-arm64 /data/local/tmp/frida-server
   adb -s <P1_SERIAL> shell "chmod 755 /data/local/tmp/frida-server && /data/local/tmp/frida-server &"
   ```

6. **NEVER use `adb kill-server` / `adb start-server`** — these affect all attached phones at once. Use per-serial commands; if a phone is stuck, `adb -s <SERIAL> reconnect` is the per-phone alternative.

7. **Lane discipline:** Snap-EMU agent owns P1+P2's Snap state. TikTok-EMU owns whatever phones are TikTok-targeted. Master agent doesn't push ANYTHING to phones without operator OK. Cross-talk between Snap operations and TikTok operations on the same phone requires operator confirmation.

The Sanctum Console's Phone-Viewer sidebar tool (in development) will enforce this at the UI layer — each phone gets its own pane with its own command history. The CLI / direct adb usage must observe the same discipline.


## 2026-05-19 - AGENT AUTHORSHIP on every .bat / .md file you create

Operator: "update in memory everytime you make a bat file or md file you say what agent made it based on your name i set or what you think you are."

**Standing rule:** every time you CREATE a `.bat`, `.md`, `.ps1` (or similar text) file, include an authorship line near the top. Format:

For markdown:
```markdown
> **Author:** Sinister Snap API (Claude agent, 2026-05-19 14:32)
```

For bat:
```bat
REM Author: Sinister Snap API (Claude agent, 2026-05-19 14:32)
```

For PowerShell:
```powershell
# Author: Sinister Snap API (Claude agent, 2026-05-19 14:32)
```

Read `$env:SINISTER_AGENT_NAME` — that's the agent name the operator set for this session (exported by the launcher). If it's missing, fall back to your best guess at what you are (e.g. "claude-master-sanctum" / "ephemeral-claude") and still include the line.

The operator scans the line so they know which lane / which agent wrote what, and can chase down regressions or duplicates.


## 2026-05-19 - LOG YOUR PROGRESS (every agent, every session)

Operator directive: "I want to see progress of everything we are working on so I don't have to ask. Update memory on this."

**Standing rule:** when YOU make a meaningful milestone (started X / shipped X / blocked on X / failed X / paused X / note about X), append a section to `D:\Sinister Sanctum\_shared-memory\PROGRESS\<your-SINISTER_AGENT_NAME>.md`.

Format:

```
## YYYY-MM-DD HH:MM - <status>: <one-line title>
1-3 lines of body — what + why + what's next.
```

Status keywords: `started` / `shipped` / `blocked` / `paused` / `note` / `failed`. Most-recent at top.

You can also POST to `http://127.0.0.1:5077/api/progress/append` if the Sanctum Console is running. The console's progress panel aggregates ALL agents so the operator sees the whole fleet at a glance.

**Frequency:** at minimum, once when you start a meaningful task and once when you finish it. Skipping is worse than over-logging — the operator scans, doesn't read every line.


## 2026-05-19 01:55 - smoke-test from console UI

Window-Manager UI POST end-to-end working.

## 2026-05-19 (initial seed) - dashboard-skeleton is the canonical UI source

ALL new Sinister UIs MUST consume tokens from `C:\Users\Zonia\Desktop\dashboard-skeleton\` (junctioned at `D:\Sinister Sanctum\skills\dashboard-skeleton\` if available). See `D:\Sinister Sanctum\docs\UI-DESIGN-SYSTEM.md` for the full canon. Purple ramp is permitted ONLY for Sanctum-specific surfaces (Sanctum Console, launchers, master tooling). Panel-side surfaces MUST use iOS blue.

## 2026-05-19 - Sinister Sanctum logo

The Sinister Sanctum logo is `C:\Users\Zonia\Desktop\INPO\Things\ART\Img.png` (purple crowned horned demon skull). Use it for Sanctum-side branding everywhere (console UI, EXE app, launcher render).

## 2026-05-19 - tools/skills/inventions archive

Every new tool/skill/invention gets its own folder + tool-card README. Append to `D:\Sinister Sanctum\tools\_INDEX.md` or `D:\Sinister Sanctum\skills\_INDEX.md` for catalog. See `D:\Sinister Sanctum\tools\_TEMPLATE.md`.

## 2026-05-19 - per-agent name + accent color

Each spawned Claude session has an agent name (e.g. "Sinister Snap API") and an accent color. Register presence each turn via `sinister-bus.heartbeat my_agent="<name>"` and poll inbox via `sinister-bus.inbox_poll my_agent="<name>"`. Operator's preferred accent for your session is injected in the cold-start phrase — use it for your section headers / status bars.
