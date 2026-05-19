> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# sanctum-git

A self-hosted Gitea instance running locally on `http://localhost:3000`. This is the operator's escape hatch from `github.com` — a private origin every Sinister project can mirror to, with per-agent branch discipline so multiple parallel Claude sessions never step on each other.

## What it is

- **One Docker container** (`gitea/gitea:1.22-rootless`) at `D:\Sinister Sanctum\tools\sanctum-git\`
- **Two endpoints:** HTTP at `localhost:3000` (web UI + git HTTPS clone) and SSH at `localhost:2222`
- **SQLite-backed.** No separate database service. Data lives in `tools/sanctum-git/data/`. Config in `tools/sanctum-git/config/`.
- **Rootless variant.** Container runs as UID/GID `1000` — no sudo / no root drift on the host.
- **Optional Gitea Actions runner** sidecar (commented out by default; opt-in).

## Why it exists

Operator directive (2026-05-19): "allow us to have our own github self hosted so we can push all our files to a self storage system so that we can get away from github down the road and not step on each other's toes while we work on projects and can in real time not interfere with each other."

Concretely:

1. **Long-term escape from github.com.** Every Sanctum project can keep its `origin` remote on GitHub AND add a `sanctum` remote pointing at this Gitea. Mirror script (`git-mirror.ps1`) pushes to both. When the operator is ready to fully cut over, GitHub becomes optional.
2. **No rate limits, no scope-refresh dance.** No more `gh auth refresh -s workflow` (see `knowledge/github-auth-workflow-scope.md`). No more PAT rotation. Pushes are auth'd locally, instantly.
3. **Multi-agent concurrency without collisions.** Per-agent branch convention (see `DIRECTIVES.md` 2026-05-19) means every Claude session pushes to its OWN branch — `agent/<agent-slug>/<topic>` — on BOTH remotes. No two sessions ever touch the same branch unless the operator says so.
4. **Real-time visibility.** `git-mirror status` shows every project's local HEAD, sanctum HEAD, and github HEAD side-by-side so the operator sees who's where.
5. **Offline-capable.** Internet drops? Sanctum stays pushable. GitHub catches up later.

## How to bootstrap (one-time, operator runs once)

1. **Ensure Docker Desktop is running.** Whale icon in the tray, "Docker Desktop is running".
2. **Double-click** `C:\Users\Zonia\Desktop\Sanctum-Git-Start.bat`.
   - It runs `D:\Sinister Sanctum\automations\setup-sanctum-git.ps1`.
   - That cd's into `tools\sanctum-git\`, runs `docker compose up -d`, and polls `http://localhost:3000/api/v1/version` until it answers (max 90 s).
3. **Open** `http://localhost:3000` in a browser.
   - Complete the install wizard (defaults are fine — SQLite, domain `localhost`, port 3000).
   - Create your first user; check **"Set as administrator"**. Recommended username: `operator`. Email: the value of `GITEA_ADMIN_EMAIL` in `.env`.
4. **Save your credentials** into `tools\sanctum-git\.env` (copy from `.env.example`). The `git-mirror.ps1` script reads them when it calls the Gitea API to create repos.
5. **Run** `C:\Users\Zonia\Desktop\Mirror-To-Sanctum-Git.bat`, choose `all` (or a single project key). The mirror script:
   - calls `POST /api/v1/user/repos` to create each Gitea repo if missing,
   - adds a `sanctum` remote to each local project,
   - pushes the current branch.

## Per-agent branch convention (standing rule)

See `D:\Sinister Sanctum\_shared-memory\DIRECTIVES.md` 2026-05-19 section "PER-AGENT BRANCH DISCIPLINE" and `_shared-memory\knowledge\per-agent-branch-convention.md`.

TL;DR — every Claude session works on its OWN branch:

```
agent/<your-SINISTER_AGENT_NAME-slugified>/<short-topic>

# examples:
agent/sinister-snap-api/pure-api-ss03
agent/sinister-sanctum/master-tooling-v6
agent/sinister-tiktok-emu/argos-port
```

- Branch off the integration point the operator names (default `main`).
- DO NOT merge cross-agent branches without operator OK.
- Every push goes to YOUR branch on **both** github.com AND sanctum-git (the mirror tool handles both — you just `git push`).
- `git-mirror status` is the single-pane view of who's where.

## Mirror schedule

There's **no automatic cron** in v1. Mirroring is operator-driven via:

- `Mirror-To-Sanctum-Git.bat` (interactive — pick a project or `all`)
- `git-mirror push <project-key>` (single project)
- `git-mirror push-all` (loops over `automations\session-templates\projects.json`)

Future work (deferred): a scheduled task that runs `git-mirror push-all` every 5 minutes. Easy to add — Task Scheduler entry pointing at `git-mirror.ps1 -Cmd push-all`.

## Files in this folder

- `docker-compose.yml` — Gitea container definition + commented-out Actions runner.
- `.env.example` — admin creds + secret key template. Copy to `.env`.
- `AUTHOR.md` — authorship marker (per `DIRECTIVES.md` standing rule).
- `data/` — Gitea repos, LFS, attachments (created on first `docker compose up`).
- `config/` — `app.ini` + custom templates (created on first wizard run).

## Implementation files (absolute paths)

- `D:\Sinister Sanctum\tools\sanctum-git\docker-compose.yml`
- `D:\Sinister Sanctum\tools\sanctum-git\.env.example`
- `D:\Sinister Sanctum\automations\setup-sanctum-git.ps1`
- `D:\Sinister Sanctum\automations\git-mirror.ps1`
- `C:\Users\Zonia\Desktop\Sanctum-Git-Start.bat`
- `C:\Users\Zonia\Desktop\Mirror-To-Sanctum-Git.bat`

## Dependencies

- Docker Desktop for Windows (already installed per operator's standard kit)
- Windows PowerShell 5.1+
- Sinister Sanctum project layout (so `git-mirror.ps1` can find `automations\session-templates\projects.json`)

## Lane

master / Sanctum orchestration

## Captured

2026-05-19

## Status

shipped (Docker stack + scripts authored; first-run wizard is operator-side and not automated by design)

## Linked-inventions

- `D:\Sinister Sanctum\inventions\2026-05-19-sanctum-git.md` — fourth Sanctum invention

## Changelog

- **2026-05-19** — Initial registration. Compose file (Gitea 1.22 rootless on 3000/2222), bootstrap script, mirror tool, per-agent branch convention added to `DIRECTIVES.md`.
