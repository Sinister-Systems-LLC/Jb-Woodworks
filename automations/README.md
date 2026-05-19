# automations/ — operator-runnable scripts

All scripts in this directory:
- Emit a runlog manifest to `D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\runtime-state\script-runs\<script>-<utc>.json`
- Auto-close their window on success (operator clicks bat, walks away)
- Are operator-only — they write to source projects / shell out to git / call other PowerShell scripts. NOT in the `bus.run_script` whitelist by default.

## Files

| Script | What | When operator runs |
|---|---|---|
| `git-toolkit.ps1` | 10-subcommand GitHub workflow helper | per-project init / push / release / status |
| `secret-scrub.ps1` | secret pattern + danger-filename scan | before every push to ANY public repo |
| `migrate-projects.ps1` | junction product-repo sources into `projects/` for the navigation view | once, when populating Sanctum from operator's Desktop |
| `hub-scripts/` (junction) | the hub's own automations (activate-everything, verify-backups, check-hetzner-state, prepare-for-migration, run-all-checks, aggregate-gotchas, _runlog helper, install-fleet) | from the operator's Desktop bats |

## git-toolkit.ps1 subcommands

```powershell
.\git-toolkit.ps1 help                            # full reference
.\git-toolkit.ps1 status-summary                  # branch + ahead + dirty across ALL projects
.\git-toolkit.ps1 init <project-path>             # git init + .gitignore + first commit
.\git-toolkit.ps1 remote-set <path> <git-url>     # add origin + optional gh verify
.\git-toolkit.ps1 safe-push <path>                # secret-scrub THEN push; abort on hits
.\git-toolkit.ps1 pre-commit-install <path>       # .githooks/pre-commit runs scrub
.\git-toolkit.ps1 release <path> <semver>         # tag + push (e.g. v1.2.3)
.\git-toolkit.ps1 ci-bootstrap <path>             # drop .github/workflows/sinister-ci.yml
.\git-toolkit.ps1 doc-bootstrap <path>            # README + CLAUDE + LICENSE templates
.\git-toolkit.ps1 scrub <path>                    # secret-scrub one project
.\git-toolkit.ps1 gitignore-tune <path>           # detect language + add ignores
```

Desktop one-clicks: `Git-Status.bat` (status-summary) + `Git-Safe-Push.bat` (safe-push of dragged-onto project).

## Adding a new automation

1. Drop the `.ps1` here.
2. Dot-source `_runlog.ps1` (via hub-scripts/) so it emits a manifest.
3. Add an entry to this README.
4. If safe + read-only, add to the `bus.run_script` whitelist in `bots/agents/sinister-bus/server.py`.
5. If operator-only (destructive / long-running), do NOT add to whitelist — operator owns it.

## TL;DR

- **How we won:** All scripts share the runlog convention so bots can read outcomes.
- **What you need to do:** Per-project workflow = init → doc-bootstrap → ci-bootstrap → pre-commit-install → remote-set → safe-push. The `git-toolkit.ps1 help` subcommand shows the full reference.
