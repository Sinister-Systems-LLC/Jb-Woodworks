> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# sanctum-git — self-hosted Gitea + per-agent branch discipline (fourth Sanctum invention)

**Captured:** 2026-05-19
**Status:** shipped (Docker stack + scripts authored; first-run wizard is operator-side and not automated by design)
**Origin:** Operator directive (2026-05-19): "allow us to have our own github self hosted so we can push all our files to a self storage system so that we can get away from github down the road and not step on each other's toes while we work on projects and can in real time not interfere with each other."

## Idea

> allow us to have our own github self hosted so we can push all our files to a self storage system so that we can get away from github down the road and not step on each other's toes while we work on projects and can in real time not interfere with each other.

A self-hosted Gitea instance running locally on `http://localhost:3000` becomes the Sinister fleet's private origin. Every Sanctum project adds it as a SECOND git remote named `sanctum` (alongside the existing `origin` -> github.com). A mirror script pushes both. Paired with a per-agent branch convention (`agent/<slug>/<topic>`), parallel Claude sessions never collide.

This is the fourth Sanctum invention — joining Sinister Crawler (TG bot front-end), Sinister Chatbot (ChatGPT-style UI), and Sinister Phone Viewer (per-phone scrcpy).

## Why

Three concrete problems this solves:

1. **GitHub dependency.** Operator wants the option to fully cut github.com out of the loop. By mirroring everything to a local Gitea now, the cut-over later is a one-line change to remove `origin` and rename `sanctum` -> `origin`.

2. **GitHub friction.** Real OAuth scope dance every time we add a workflow (`gh auth refresh -s workflow`, per `knowledge/github-auth-workflow-scope.md`). Secondary rate limits on bulk pushes. PAT rotation. None of that on a local server.

3. **Multi-agent collisions.** Five+ Claude sessions can be running at once. Today, two sessions both pushing `main` for the same repo is a foot-gun. With per-agent branches (`agent/sinister-snap-api/pure-api-ss03`, etc.) on a local mirror, the operator sees divergent work side-by-side in `git-mirror status` and merges in their own time.

A nice bonus: offline-capable. Internet drops, Sanctum stays pushable, GitHub catches up later.

## Sketch

```
Per-project layout (existing):
  D:\Sinister Sanctum\projects\sinister-snap-emu\source\
     \.git\config
        [remote "origin"]   url = https://github.com/Sinister-Systems-LLC/Sinister-Snap-API-EMU.git
        [remote "sanctum"]  url = http://operator:<pw>@localhost:3000/operator/Sinister-Snap-API-EMU.git   <-- NEW

Stack:
  D:\Sinister Sanctum\tools\sanctum-git\
     docker-compose.yml         gitea/gitea:1.22-rootless on 3000 + 2222, SQLite
     .env.example -> .env       GITEA_ADMIN_USER / EMAIL / PASSWORD / SECRET_KEY
     data/                      repos + LFS + sqlite db (volume-mounted)
     config/                    app.ini (volume-mounted)
     AUTHOR.md
     README.md                  tool card

Bootstrap (operator, one-time):
  C:\Users\Zonia\Desktop\Sanctum-Git-Start.bat
    -> D:\Sinister Sanctum\automations\setup-sanctum-git.ps1
       1. docker info
       2. cd tools\sanctum-git\ && docker compose up -d
       3. poll http://localhost:3000/api/v1/version (max 90s)
       4. print next steps (open wizard, fill .env, then git-mirror init)

Mirror tool (any agent):
  D:\Sinister Sanctum\automations\git-mirror.ps1
    -Cmd init     -ProjectKey <key>   POST /api/v1/user/repos + add `sanctum` remote
    -Cmd push     -ProjectKey <key>   git push sanctum <current-branch>
    -Cmd push-all                     loop over projects.json
    -Cmd status                       per-project: local HEAD / sanctum HEAD / github HEAD
  Reads creds from tools\sanctum-git\.env (gracefully fails if absent or placeholder).
  Logs every run to 12_LLM_ORCHESTRATION\runtime-state\script-runs\git-mirror-<UTC>.json

Per-agent branch rule (DIRECTIVES.md 2026-05-19):
  Every Claude session works on branch: agent/<your-SINISTER_AGENT_NAME-slugified>/<topic>
  - examples: agent/sinister-snap-api/pure-api-ss03, agent/sinister-sanctum/master-tooling-v6
  - branch off integration point (default: main)
  - no cross-agent merges without operator OK
  - every push goes to YOUR branch on BOTH origin and sanctum
```

## Status

- [x] idea captured
- [x] design sketched
- [x] implementation started (compose file, bootstrap script, mirror tool, two knowledge files, DIRECTIVES section, indexes updated)
- [x] shipped — Docker stack + scripts authored; operator still has to launch Docker Desktop, run the wizard, fill .env

## Linked-to

- Tool folder:     `D:\Sinister Sanctum\tools\sanctum-git\`
- Compose:         `D:\Sinister Sanctum\tools\sanctum-git\docker-compose.yml`
- Tool card:       `D:\Sinister Sanctum\tools\sanctum-git\README.md`
- Author tag:      `D:\Sinister Sanctum\tools\sanctum-git\AUTHOR.md`
- Bootstrap PS1:   `D:\Sinister Sanctum\automations\setup-sanctum-git.ps1`
- Mirror PS1:      `D:\Sinister Sanctum\automations\git-mirror.ps1`
- Desktop start:   `C:\Users\Zonia\Desktop\Sanctum-Git-Start.bat`
- Desktop mirror:  `C:\Users\Zonia\Desktop\Mirror-To-Sanctum-Git.bat`
- Standing rule:   `D:\Sinister Sanctum\_shared-memory\DIRECTIVES.md` (2026-05-19 PER-AGENT BRANCH DISCIPLINE)
- Brain entry 1:   `D:\Sinister Sanctum\_shared-memory\knowledge\gitea-self-host.md`
- Brain entry 2:   `D:\Sinister Sanctum\_shared-memory\knowledge\per-agent-branch-convention.md`
- Tools index:     `D:\Sinister Sanctum\tools\_INDEX.md`
- Skills index:    `D:\Sinister Sanctum\skills\_INDEX.md`
- Knowledge index: `D:\Sinister Sanctum\_shared-memory\knowledge\_INDEX.md`

## Notes

- Rootless image chosen for security (no host-side root drift on `./data/`).
- SQLite over Postgres for simplicity — backups are just a snapshot of `./data/`.
- Actions runner sidecar is commented out by default in `docker-compose.yml`. The operator opts in by uncommenting the block + supplying a registration token; that lights up Gitea Actions (the GitHub-Actions-compatible CI runner) for repos hosted locally.
- The mirror tool deliberately does NOT auto-push from any agent at any cadence. Every push is an explicit invocation (`-Cmd push` or `-Cmd push-all`). Future work could schedule `push-all` every 5 minutes via Task Scheduler — left as operator opt-in.
- Per the constraints for this build: no real `docker compose up` was run, no real network calls were made, no real `git push` happened. Everything is authored and ready; first-run is operator-driven.
- The mirror script reads `$env:SINISTER_AGENT_NAME` when stamping runlog entries so the operator can trace which agent did each push.
- Constraints honored: panel source untouched, `start-sinister-session.ps1` untouched, `window-manager/server.py` + `desktop_app.py` untouched (they're being heavily edited by two parallel agents right now), `~/.claude/.mcp.json` untouched.
