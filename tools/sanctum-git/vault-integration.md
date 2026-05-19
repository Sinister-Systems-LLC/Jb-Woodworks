> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# sanctum-git :: Vault Integration

How the existing sanctum-git (Gitea on `http://localhost:3000`) plugs into the **Sinister Vault** — the 1TB operator-only storage volume defined under `tools/sinister-vault/` — so that every commit becomes a per-user, audited file-share event surfaced in the RKOJ.exe UI.

Cross-reference:
- Vault daemon + 1TB quota + audit log :: `D:\Sinister Sanctum\tools\sinister-vault\README.md` (SV-A)
- Real-time sync (Syncthing for the operator <-> Leo channel) :: `D:\Sinister Sanctum\tools\sinister-vault\sync-setup.md` (SV-C)
- Per-agent branch discipline :: `D:\Sinister Sanctum\_shared-memory\DIRECTIVES.md` (2026-05-19)
- Workaround log :: `D:\Sinister Sanctum\_shared-memory\knowledge\gitea-self-host.md`

---

## 1. Where Gitea data lives (under the Vault quota)

Before vault integration, Gitea data lived at:

```
D:\Sinister Sanctum\tools\sanctum-git\data\          (repos, LFS, sqlite db)
D:\Sinister Sanctum\tools\sanctum-git\config\        (app.ini, custom templates)
```

After running **`setup-vault-data-dir.ps1`** (one-time, operator), data lives at:

```
D:\sinister-vault\gitea\data\                        (repos, LFS, sqlite db)
D:\sinister-vault\gitea\config\                      (app.ini, custom templates)
```

`docker-compose.yml` is rewritten to mount those vault paths into the container at `/var/lib/gitea` and `/etc/gitea`. The original tool-folder paths are renamed `.old` as a safety net for the first verification — the operator deletes them once they've confirmed the vault copy is healthy.

This means **every byte Gitea writes counts toward the Vault's 1TB quota** (enforced by the vault daemon SV-A). Repos, LFS objects, attachments, the sqlite db — all of it.

### Why we do it

1. **One quota, one audit log.** The vault daemon (SV-A) already watches `D:\sinister-vault\` for every file change. Moving Gitea inside means every push, every commit, every uploaded file enters the vault's audit stream automatically — no new instrumentation in Gitea itself.
2. **Backups are one rclone snapshot.** When the operator runs `tools/sinister-vault/backup.ps1` (planned), the Gitea tree comes along for free.
3. **Cross-machine sync via Syncthing (SV-C).** The Syncthing folder pointed at `D:\sinister-vault\` is the single source of truth for the operator <-> Leo channel; Gitea repos ride along.

### Why we don't put the vault inside Gitea instead

Gitea is a git server, not a quota-aware blob store. The vault daemon needs to apply size limits, content-type policies, and per-account caps that Gitea doesn't know about. Owning the filesystem (vault) and letting Gitea live inside it as a regular consumer keeps responsibilities clean.

---

## 2. How `bootstrap-users.py` provisions operator + leo

`bootstrap-users.py` is the **idempotent** account-provisioning script. It reads `.env` for Gitea admin creds, then walks a fixed user-spec list (`operator`, `leo`) and:

| Step | What it does | API call |
|---|---|---|
| 2a | Smoke-test that Gitea is alive | `GET /api/v1/version` |
| 2b | Detect whether `<user>` already exists | `GET /api/v1/users/<user>` |
| 2c | If missing, create the user | `POST /api/v1/admin/users` |
| 2d | List the user's installed SSH keys | `GET /api/v1/users/<user>/keys` |
| 2e | If the chosen public key isn't in that list, install it | `POST /api/v1/admin/users/<user>/keys` |

Two users, two key-source policies:

- **`operator`** — admin user; reuses `GITEA_ADMIN_PASSWORD` from `.env`; key auto-discovered from `~/.ssh/id_ed25519.pub` (falls back to `id_rsa.pub`, skips entirely if neither exists).
- **`leo`** — non-admin collaborator; password from `LEO_INITIAL_PASSWORD` in `.env` (or `--leo-password` CLI arg); `must_change_password=True` so Leo rotates on first login; key must be supplied by operator via `--leo-key-file <path-to-leo.pub>` (operator pastes/uploads it during onboarding).

### Output

The script emits a JSON manifest on stdout describing exactly what changed. Example trimmed output:

```json
{
  "started_at_utc": "2026-05-19T18:00:00Z",
  "gitea_url": "http://localhost:3000",
  "gitea_version": "1.22.x",
  "admin_user": "operator",
  "users": [
    { "username": "operator", "user_action": "skipped_exists",
      "key_action": "added", "details": { "key_id": 1, "key_title": "operator-ssh::id_ed25519.pub" } },
    { "username": "leo", "user_action": "created",
      "key_action": "skipped_no_cli_arg",
      "details": { "email": "leo@sinister.local",
                   "hint": "re-run with --leo-key-file <path-to-leo.pub>",
                   "must_change_password": true } }
  ],
  "exit_code": 0
}
```

Pass `--json-out manifest.json` to also persist the manifest to disk for the audit trail.

### Re-running is safe

Every step is gated by a pre-check. Re-runs after Leo pastes his `.pub` only do the missing piece (`POST /api/v1/admin/users/leo/keys`); everything else reports `skipped_exists`.

---

## 3. Commit-as-upload workflow

The Vault treats Gitea as a **per-user, append-only, attributed file share**. The end-to-end flow when an operator (or Leo) wants to share a file:

```
                +---------------------+         git push           +-----------------+
  operator  ->  | local working copy  |  --------------------->    |  sanctum-git    |
  or Leo        | (anywhere on disk)  |  (HTTP basic or SSH 2222)  | localhost:3000  |
                +---------------------+                            +--------+--------+
                                                                            |
                                                                            v
                                                                   D:\sinister-vault\gitea\
                                                                            |
                                                  vault daemon (SV-A) sees new files
                                                                            |
                                                                            v
                                                                  per-user audit log entry
                                                                  (who pushed, what bytes,
                                                                  which repo, which commit sha)
                                                                            |
                                                                            v
                                                                  RKOJ.exe Vault drawer
                                                                  refreshes (commit appears
                                                                  in feed with author chip)
```

### Concretely, in 5 steps

1. The user (operator or Leo) drops the file(s) into a repo working copy on their machine.
2. `git add <path> && git commit -m "<intent>" && git push`.
3. The push lands at `http://localhost:3000/<user>/<repo>.git`. Because the host volume is `D:\sinister-vault\gitea\data\`, the bytes hit the vault.
4. The vault daemon (SV-A, file-watcher on `D:\sinister-vault\`) sees new objects under `gitea/data/repositories/<user>/<repo>.git/` and writes a row into `D:\sinister-vault\audit.log` (or whatever path SV-A finalizes).
5. RKOJ.exe's Vault drawer (IR-A) polls the audit log and surfaces the commit with the **author chip** (operator vs. leo), commit message, and a link back to `http://localhost:3000/<user>/<repo>/commit/<sha>` for the full diff.

The audit log is the source of truth — neither Gitea's own activity feed nor the vault daemon alone tells the full story; they line up because they share the filesystem.

---

## 4. Per-user attribution

Every commit is signed by the **Gitea identity** of the user pushing — `operator` or `leo`. That identity flows through three layers:

1. **HTTP basic auth or SSH key** identifies the user at push time (their `.pub` is registered via `bootstrap-users.py`).
2. **Git author / committer header** on the commit object identifies who *made* the commit (set by `git config user.name` / `user.email` on the user's machine; should match the Gitea identity).
3. **Gitea action record** stamps the push with the API-level user id, visible in the repo's Activity tab and queryable via `GET /api/v1/repos/<owner>/<repo>/activities/feeds`.

The RKOJ UI keys off the Gitea action record (most authoritative — it's the server's own view), with the git author header as a fallback for commits pushed by a third party on the user's behalf.

### Why two users now and not later

We provision **two** identities (operator, leo) on day one so:

- Every commit has an unambiguous author from the very first push (no "system" commits to migrate later).
- The vault audit log gets a clean two-tone trail (no rewriting history when Leo joins).
- Leo's `must_change_password=true` ensures the initial password we drop in `.env` is a single-use bootstrap value, not a long-lived credential.

---

## 5. Sync-via-clone pattern (operator <-> Leo)

Leo is **not on the same machine** as the operator. He has his own laptop. The pattern:

```
                                    operator's PC (sanctum-git host)
                                    +----------------------------------+
                                    |  http://<operator-ip>:3000       |
                                    |  D:\sinister-vault\gitea\        |
                                    +-----------------+----------------+
                                                      |
                                                      | (a) Leo: git clone http://operator:3000/operator/<repo>.git
                                                      |        -> Leo has the files locally
                                                      |
                                                      | (b) Leo edits, commits, pushes:
                                                      |     git push origin agent/leo/<topic>
                                                      |     -> commit lands back in operator's Gitea
                                                      |        -> bytes hit D:\sinister-vault\gitea\
                                                      |        -> vault daemon (SV-A) logs the event
                                                      |
                                                      v
                                                  Leo's laptop
```

### Step-by-step for Leo's first session

1. Operator runs `bootstrap-users.py --leo-key-file <path-to-leo.pub>` once (registers Leo's SSH key on Gitea).
2. Operator opens port `3000` (or `2222` for SSH) on the LAN, or sets up a tailscale / wireguard tunnel between Leo's laptop and the operator's PC. Public exposure is **not** required and is **not recommended**.
3. Leo, on his laptop:
   ```bash
   git clone http://leo@<operator-ip>:3000/operator/<repo>.git
   cd <repo>
   git checkout -b agent/leo/<short-topic>
   # ... edit files ...
   git add . && git commit -m "<intent>"
   git push -u origin agent/leo/<short-topic>
   ```
4. Push hits operator's Gitea, which writes to `D:\sinister-vault\gitea\`. Vault audit log records: `actor=leo, repo=operator/<repo>, sha=<...>, bytes=<n>, ts=<...>`.
5. RKOJ.exe Vault drawer (IR-A) on operator's side surfaces the new commit with Leo's chip.

### Why not Syncthing for source code

Syncthing (SV-C) is excellent for **binary / static-asset** sync — large files, images, recordings — where you want them on multiple machines at once. It is **not** good for source code: there's no merge support, two-sided edits clobber, and there's no audit trail per change.

Git solves all three of those problems. So the split is:
- **Source code, configs, anything text-and-mergeable** -> push to sanctum-git -> lands in `D:\sinister-vault\gitea\`.
- **Large blobs (videos, datasets, snapshots, screenshots that aren't worth blob-storing in git)** -> drop in `D:\sinister-vault\shared\` -> Syncthing replicates.

Both routes feed the same vault quota and the same audit log.

---

## 6. What to read next

| Goal | File |
|---|---|
| Stand up the 1TB vault daemon | `D:\Sinister Sanctum\tools\sinister-vault\README.md` (SV-A) |
| Set up Syncthing for the operator <-> Leo channel | `D:\Sinister Sanctum\tools\sinister-vault\sync-setup.md` (SV-C) |
| First-time Gitea wizard + creds | `D:\Sinister Sanctum\tools\sanctum-git\FIRST-RUN.md` |
| Why we self-host Gitea at all | `D:\Sinister Sanctum\_shared-memory\knowledge\gitea-self-host.md` |
| Per-agent branch rule | `D:\Sinister Sanctum\_shared-memory\DIRECTIVES.md` (2026-05-19 PER-AGENT BRANCH DISCIPLINE) |

---

## 7. Operator runbook (sequence)

```text
1. Complete Gitea install wizard at http://localhost:3000 (FIRST-RUN.md)
2. Fill in tools\sanctum-git\.env (admin creds, optional LEO_INITIAL_PASSWORD)
3. Run: powershell -NoProfile -ExecutionPolicy Bypass -File `
        "D:\Sinister Sanctum\tools\sanctum-git\setup-vault-data-dir.ps1"
   (moves Gitea data to D:\sinister-vault\gitea\, restarts container, verifies)
4. Run: python "D:\Sinister Sanctum\tools\sanctum-git\bootstrap-users.py" `
                --leo-key-file <path-to-leo.pub>
   (provisions operator + leo, registers SSH keys, emits JSON manifest)
5. Bring up vault daemon (SV-A) so audit log starts catching pushes
6. Bring up RKOJ Vault drawer (IR-A) so the operator sees the live feed
```

Done. From here, every `git push` to `http://localhost:3000/...` becomes a per-user audited file-share event visible in RKOJ.exe.
