<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Topic: Self-hosting Gitea on localhost:3000 as a github.com replacement

**Slug:** gitea-self-host
**First discovered:** 2026-05-19 by Sinister Sanctum
**Last updated:** 2026-05-19 by Sinister Sanctum
**Status:** workaround
**Tags:** gitea, self-host, docker, git-remote, github-replacement, sanctum-git, mirror

## Problem

Operator wants out of `github.com` dependency long-term ("get away from github down the road") AND wants concurrent multi-agent work without two sessions stepping on each other's pushes. GitHub's API has rate limits, OAuth scope requirements (see `github-auth-workflow-scope`), and a SINGLE remote per project — so two Claude sessions both pushing `main` will clobber each other.

## Why it happens

Centralized SaaS git hosts (github.com, gitlab.com) introduce three problems for a fast-moving multi-agent fleet:

1. **Single point of failure.** Internet drops -> no pushes.
2. **Rate-limit / scope friction.** `gh auth refresh -s workflow` per machine; PAT rotation; secondary rate limits.
3. **No isolation between agents.** Multiple sessions writing to the same remote/branch race for last-write-wins.

A local Gitea instance solves all three. It runs as a Docker container, exposes the standard git HTTPS protocol on `localhost:3000`, and lets us add it as a SECOND remote (`sanctum`) alongside the existing `origin` (github.com). Pushes still go to BOTH, so github.com stays usable until the operator chooses to retire it.

## Fix or workaround

### One-time bootstrap (operator)

```powershell
# 1. Ensure Docker Desktop is running.
docker info | Select-Object -First 3

# 2. Bring the container up (or double-click Sanctum-Git-Start.bat).
cd "D:\Sinister Sanctum\tools\sanctum-git"
docker compose up -d

# 3. Wait until the API answers (the bootstrap script polls this automatically).
Invoke-WebRequest http://localhost:3000/api/v1/version
```

### Wizard (first browser visit only)

Open `http://localhost:3000`. The install wizard appears. Defaults are fine:

- Database: SQLite (`/var/lib/gitea/gitea.db` inside the container, mapped to `./data/`)
- Server domain: `localhost`
- SSH port: `2222` (the host port 22 is usually taken by OpenSSH server)
- HTTP port: `3000`

At the bottom, **check** "Set as administrator" and create the first user. Recommended:

- Username: `operator`
- Email: `andrew.viperrr@gmail.com`
- Password: pick anything; save it to `tools\sanctum-git\.env` in `GITEA_ADMIN_PASSWORD`

### Adding the sanctum remote to an existing GitHub-tracked repo

**Do not remove `origin`.** Add a second remote named `sanctum`:

```bash
cd "D:\Sinister Sanctum\projects\sinister-snap-emu\source"
git remote -v
# origin  https://github.com/Sinister-Systems-LLC/Sinister-Snap-API-EMU.git (fetch)
# origin  ...                                                                (push)

git remote add sanctum http://operator:<password>@localhost:3000/operator/Sinister-Snap-API-EMU.git

git remote -v
# origin   https://github.com/...                                  (fetch / push)
# sanctum  http://operator:***@localhost:3000/operator/...git      (fetch / push)
```

The Sanctum tooling does this for you:

```powershell
& "D:\Sinister Sanctum\automations\git-mirror.ps1" -Cmd init -ProjectKey snap-emu
```

That call:

1. `POST /api/v1/user/repos` (basic auth from `.env`) creates `operator/Sinister-Snap-API-EMU` on Gitea if missing.
2. `git remote add sanctum http://operator:<pw>@localhost:3000/operator/<repo>.git` in the project root.

### Pushing

```bash
# Existing flow (unchanged):
git push origin agent/sinister-snap-api/pure-api-ss03

# New: mirror to Sanctum too
git push sanctum agent/sinister-snap-api/pure-api-ss03

# Or use the tool:
& "D:\Sinister Sanctum\automations\git-mirror.ps1" -Cmd push -ProjectKey snap-emu

# Or one-click:
# C:\Users\Zonia\Desktop\Mirror-To-Sanctum-Git.bat
```

### Why password-in-URL?

Gitea supports HTTP basic auth with the password embedded in the remote URL. This is acceptable on `localhost` because the URL never leaves the host machine. For LAN exposure, swap to SSH (port 2222) with a deploy key:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/sanctum-git -C "operator@sanctum"
# upload .pub via Gitea UI -> User Settings -> SSH Keys
git remote set-url sanctum ssh://git@localhost:2222/operator/<repo>.git
```

## Default ports cheat sheet

| Service | Host port | Container port | Notes |
|---|---|---|---|
| Gitea web UI | `3000` | `3000` | also serves HTTPS-less git over HTTP |
| Gitea SSH   | `2222` | `22`   | 2222 chosen so host sshd / OpenSSH on 22 doesn't conflict |
| API base    | `3000` | `3000` | `http://localhost:3000/api/v1/...` |

## Tested-or-untested

Compose file + scripts authored 2026-05-19. The Docker stack itself has NOT yet been started by this agent (operator must launch Docker Desktop + click `Sanctum-Git-Start.bat`). Once a first push completes, append a Discovery here.

## Discoveries (append-only log, most-recent at top)

### 2026-05-19 by Sinister Sanctum
Initial scaffold. Rootless image chosen over root variant — runs as UID/GID 1000, no host root drift. SQLite chosen over Postgres — one container, simpler backup (just snapshot `./data/`). Actions runner left commented-out by default; opt-in via uncommenting the block in compose.yml. The default branch in the create-repo API call is set to `main` to match operator's existing repos.

## Related topics

- [github-auth-workflow-scope](./github-auth-workflow-scope.md) — the OAuth scope dance that this self-host helps us avoid
- [per-agent-branch-convention](./per-agent-branch-convention.md) — the branch naming rule that complements this stack
