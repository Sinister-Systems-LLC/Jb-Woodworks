> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# sanctum-git — first-run wizard

Pure step list to bring localhost:3000 Gitea online and wire it as a secondary remote for Sanctum. Each step is operator-driven (per the deferred sandbox-blocks; Docker daemon and the Gitea install wizard need a human).

## 0. Prereqs

```powershell
docker version           # expects Server: Docker Desktop running
docker compose version   # expects Docker Compose v2+
```

If Docker Desktop is not running, start it from the Start menu and wait until the tray icon says "Docker Desktop is running."

## 1. Bring the container up

```cmd
C:\Users\Zonia\Desktop\Sanctum-Git-Start.bat
```

Expected console output:

```
[sanctum-git] docker compose up -d ...
[sanctum-git] container 'sanctum-gitea' is up
[sanctum-git] polling http://localhost:3000/api/v1/version ...
[sanctum-git] OK — Gitea responded with v1.22.x
```

If polling stalls beyond 90 s, the script bails out. Check `docker ps` for the `sanctum-gitea` container and `docker logs sanctum-gitea` for the boot trail.

## 2. Run the install wizard (browser, 60 s)

Open `http://localhost:3000` in a browser. The wizard appears on first visit:

| Field | Value |
| --- | --- |
| Database type | `SQLite3` (default) |
| Database path | leave default |
| App name | `Sanctum Git` |
| Server domain | `localhost` |
| SSH port | `2222` |
| HTTP port | `3000` |
| Application URL | `http://localhost:3000/` |
| Log path | leave default |
| Email service | skip (operator can wire later) |
| **Administrator account** | username `operator`, email = `GITEA_ADMIN_EMAIL` from `.env`, password = your pick. Check `Set as administrator`. |

Submit. Gitea persists this config inside the container's volume — you only do this once.

## 3. Save creds into `.env`

```powershell
cd "D:\Sinister Sanctum\tools\sanctum-git"
Copy-Item .env.example .env -Force
notepad .env
```

Fill:

```
GITEA_URL=http://localhost:3000
GITEA_ADMIN_USER=operator
GITEA_ADMIN_PASS=<the-password-you-picked>
GITEA_ADMIN_EMAIL=operator@sinister.local
```

The mirror script reads these to call the Gitea API (`POST /api/v1/user/repos`) on the operator's behalf.

## 4. Smoke the Gitea API

```powershell
$creds = "${env:GITEA_ADMIN_USER}:${env:GITEA_ADMIN_PASS}"  # or paste from .env
$pair = [System.Text.Encoding]::ASCII.GetBytes($creds)
$auth = [Convert]::ToBase64String($pair)
Invoke-RestMethod -Uri http://localhost:3000/api/v1/user `
  -Headers @{ Authorization = "Basic $auth" }
# expects: { id: 1, login: "operator", ... }
```

If you get 401 → wrong creds. 200 → you're set.

## 5. Mirror Sanctum to Gitea

```cmd
C:\Users\Zonia\Desktop\Mirror-To-Sanctum-Git.bat
```

Pick `sanctum` (or `all` to push every project). The script:

1. Calls `POST /api/v1/user/repos` if the `Sinister-Sanctum` repo doesn't exist yet.
2. Adds `sanctum` remote → `http://localhost:3000/operator/Sinister-Sanctum.git` to the local repo (already done as part of master-sweep 2026-05-19; check `git remote -v`).
3. Pushes the current branch.

Expected console tail:

```
[mirror] sanctum/Sinister-Sanctum → push OK (branch=agent/sinister-sanctum/master-sweep-2026-05-19)
```

## 6. Verify in browser

Open `http://localhost:3000/operator/Sinister-Sanctum`. You should see the branch list with `agent/sinister-sanctum/master-sweep-2026-05-19` at the top.

## 7. Single-pane status

```powershell
& "D:\Sinister Sanctum\tools\sanctum-git\git-mirror.ps1" -Cmd status
# (or via Desktop bat: Mirror-To-Sanctum-Git.bat → choose 'status')
```

Expected (per project): `local <sha>`, `sanctum <sha>`, `github <sha-or-NA>` — three columns that should match when synced.

## Optional: enable Actions runner

Uncomment the `runner` service in `docker-compose.yml`, run `docker compose up -d` again. Then in Gitea web UI: Site Administration → Runners → grab the registration token → edit `runner/.runner` config or use the env var. Not required for first push.

## Stop the container

```powershell
cd "D:\Sinister Sanctum\tools\sanctum-git"
docker compose down       # keeps data; restart with docker compose up -d
# OR
docker compose down -v    # WIPES data — destructive; do NOT run unless you mean it
```

## Common failures

| Symptom | Cause | Fix |
| --- | --- | --- |
| `port 3000 already in use` | another local server | `Get-NetTCPConnection -LocalPort 3000`; either kill it or change `HTTP_PORT` in `.env` + `docker-compose.yml` |
| `port 2222 already in use` | another SSH server (rare) | change `SSH_PORT` to e.g. 2223 in both files |
| API returns 401 with right creds | special chars in password broken by shell | wrap in single quotes when passing |
| Install wizard never appears | container died mid-boot | `docker logs sanctum-gitea` — look for permission errors on the rootless volume (chown 1000:1000 inside data/ if needed) |
| `git push sanctum ...` says auth required | git asking for HTTP basic | configure once: `git config --global credential.helper manager-core` and let Windows Credential Manager cache it |

## When this passes

1. The operator has a working `http://localhost:3000/operator/Sinister-Sanctum` repo.
2. Every Sinister project can mirror to it via `git-mirror push <key>`.
3. `git-mirror status` shows three columns: local / sanctum / github.
4. **GitHub is now optional.** When operator wants to fully cut over, set `origin` to the sanctum URL and remove the GitHub remote — that's it.

## Lane reminder

Master created the `sanctum` remote in the Sanctum repo as part of the 2026-05-19 master sweep. Master does NOT push (operator runs `git-toolkit safe-push` or the Mirror bat). Master does NOT wire product-repo remotes — each product agent does its own.
