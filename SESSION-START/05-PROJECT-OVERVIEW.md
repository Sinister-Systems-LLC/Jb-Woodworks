# 05-PROJECT-OVERVIEW — what we work on

Neutral one-page summary so a fresh Claude session knows the landscape without
needing to read 14 individual project memories. Operator picks one + we dive in.

## Sinister LLC business projects (will be in GitHub)

| Project | One-line scope | Status |
|---|---|---|
| **RKOJ.exe** | Operator's flagship workstation: 2-tab (ADB Devices / Agents) + Excel-style ribbon + cycle points + scheduler + popout + Vault integration | ✅ Shipped 2026-05-19 |
| **Sinister Vault** | Collaborative 1TB storage: Gitea repos + Syncthing sync + multi-account + MCP for agents | ✅ Shipped 2026-05-19 |
| **Sinister Sanctum** | Orchestration repo: 12 MCP bots + automations + docs + session-start. The library every other repo consumes. | ✅ Ready for first push |
| **Sinister Snap EMU** | Snap platform API client + emulator-based signing pipeline | 🟡 Active — pure-API path in progress; phone-stack track gated on Yurikey52 |
| **Sinister TikTok EMU** | TikTok platform API client + accessibility automation pipeline | 🟡 Active — task #26 (pure-API) is the current path |
| **Sinister Control Center** (a.k.a. Panel) | Live operations dashboard at snap.sinijkr.com (Hetzner-hosted) | ✅ In sync with prod; UI primitives ongoing |
| **Sinister Kernel APK** | Android root + system module distribution; ships the Detector APK | ✅ v0.95.0 shipped 2026-05-17 |
| **snap-signer** | Snap authentication signing pipeline | 🟡 Active — SS03 wall on pure-API; investigating libclient.so JNI surface |
| **library-of-alexandria** | Cross-project knowledge mirror / aggregation | 🟢 Stable — UA graph 27 days stale; optional rebuild |
| **Sinister Bumble EMU** | Bumble platform API automation | 🟡 Blocked — operator needs to fetch v5.465.0 APK from APKMirror |
| **Sinister RKA** | Backend service for distributing root attestation credentials | 🔴 Yurikey51 cert expires 2026-05-24 — operator must source Yurikey52 by 2026-05-23 |
| **Sinister OS** | Linux-based, EVE-controlled, gaming-capable full-PC OS replacement (Arch + linux-cachyos + Hyprland + EVE-as-shell) | 🔵 P0 spec lock SHIPPED 2026-05-24 — master plan at `projects/sinister-os/plans/master-plan-2026-05-24.md`; awaiting operator Q1-Q10 to unlock P1 |

## Out-of-scope for Sinister LLC (operator-private; never in GitHub)

| Project | Why excluded |
|---|---|
| LetsText | Messaging UI / design system; separate venture |
| JOKR-global | Personal property management |
| library-of-jokr-mirror | Subdomain-organized aggregation for JOKR |

## Cross-project critical items right now

- 🔴 **Yurikey52 sourcing by 2026-05-23** — gates the entire phone-stack track for Snap, TikTok, Bumble, RKA, Kernel APK
- 🔴 **PI 0/3 on phones P1 + P2** — interactive Google re-auth needed (Settings → Passwords → Sync now)
- 🟠 **Restart Claude Code** — picks up the 13 Sinister Bots + 28 bus tools (+ vault, 12 `mcp__vault__*` tools, operator-merge pending per `OPERATOR-ACTION-QUEUE.md`)
- 🟠 **Install Custodian 24/7 daemon** — `install-task.ps1` (now uses Register-ScheduledTask; should work)
- 🟡 **First git push of Sanctum** — pick LICENSE, set remote, `git-toolkit safe-push`

## What the bots cover (recap)

12 MCP bots, all $0–$0.05/call. Live in `12_LLM_ORCHESTRATION/agents/` and accessible from every Claude session:

- **sentinel** alarms / deadlines  •  **librarian** archive search  •  **researcher** scrape + summarize
- **watcher** drift detection  •  **auditor** secrets/freshness/dedup  •  **custodian** backup
- **scribe** daily digest  •  **curator** code-library scout  •  **triage** file classifier
- **translator** MCP catalog search  •  **sinister-bus** orchestrator + messaging + codec + vault
- **stealth-browser** undetected browser automation

## Multi-session workflow

Operator typically runs 4-6 Claude sessions in parallel:

- **Master / orchestration** — what you're talking to now if you read this file first
- **Per product repo** — one session per Sinister-* project, each named after the project

Sessions message each other via the bus inbox (see `00-RULES.md` Rule 9 +
`docs/AGENT-MESSAGING.md` in Sanctum). No more hand-written MD files between
sessions.

## How operator picks a project to focus on

After reading this overview, operator says one of:

```
"we're working on Sinister Snap EMU — what's the SS03 status"
"we're working on Sinister Control Center — push the queued commits"
"we're working on Sinister TikTok EMU — pure-API task #26"
"we're working on Sinister Sanctum — git init + first push"
```

The session then reads that project's `01_MEMORY/<project>/TODO.md` +
`SESSION-START` + relevant docs, and proceeds.

## TL;DR

- **How we won:** One-page overview, neutral language, scoped by what's active. Operator picks a project; session loads only what that project needs.
- **What you need to do:** Tell me "we're working on <project>" — I'll load that project's memory and ask what specifically.
