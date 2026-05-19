---
target: sanctum-git-vs-sanctum-vault
kind: compare
reviewed_by: Sinister Sanctum master agent (via Explore subagent)
reviewed_at: 2026-05-19T12:00Z
tags: [compare, sanctum-git, sanctum-vault, keep-both]
---

# Case study: sanctum-git vs sanctum-vault

## 1. What they are

**sanctum-git** is a self-hosted Gitea instance (Docker container, version 1.22-rootless) running on `http://localhost:3000`. It provides the operator an escape hatch from GitHub.com — a private, local-first origin that every Sinister project can mirror to. Per-agent branch discipline (standing rule 2026-05-19) ensures multiple Claude sessions work without collision: each pushes to `agent/<name>/<topic>` on both GitHub and Gitea. No rate limits, no PAT scope dances, offline-capable. Data lives in SQLite at `D:\Sinister Sanctum\tools\sanctum-git\data\gitea.db`; HTTP on port 3000, SSH on 2222.

**sinister-vault** is a 1 TB soft-quota collaborative storage reservation at `D:\sinister-vault\` backed by a FastAPI daemon (port 5078) that monitors usage, surfaces per-subtree breakdowns (repos/sync/snapshots/audit/accounts), and maintains a unified audit log for all storage citizens. Gitea data lives *inside* the vault's `repos/` tier post-migration. Syncthing (peer-to-peer) handles real-time sync of `sync/` between operator and Leo. The vault is the canonical multi-account, multi-device tier that unifies all storage access. Quota is enforced: warns at 950 GB, hard-cap returns HTTP 507 above 1024 GB.

## 2. Strengths (per tool)

**sanctum-git:**
- **GitHub-replacement escape hatch.** Full self-hosted git server (create repos, push/pull, clone over HTTPS/SSH) entirely local. When operator wants to cut over from GitHub.com, set `origin` to Gitea and remove the GitHub remote — done.
- **No external dependencies.** Single Docker image (gitea/gitea:1.22-rootless), SQLite backend, rootless container (UID/GID 1000 avoids host pollution). Works offline, survives internet loss, pushes accumulate locally.
- **Per-agent branch isolation.** Pairs with standing rule 2026-05-19: every Claude session gets its own branch (`agent/<slug>/<topic>`). Two agents never collide on `main` or force-push each other. Operator sees divergent work side-by-side in `git-mirror status`.
- **Mirror automation.** `git-mirror.ps1` calls `POST /api/v1/user/repos` to auto-create repos, adds `sanctum` remote, pushes current branch to both GitHub and Gitea in one call. Operator runs `Mirror-To-Sanctum-Git.bat` on Desktop.
- **Actions runner ready.** Docker Compose has optional `gitea-runner` sidecar (Gitea Actions, GitHub-Actions-compatible CI) commented out but ready. Operator can opt-in with one uncomment + token paste.

**sinister-vault:**
- **Unified 1 TB storage tier.** Repos, sync, snapshots, and audit all rooted at `D:\sinister-vault\`. Single quota check-point. Gitea data-dir is relocated here via `setup-vault-data-dir.ps1`, so every commit/push/file Gitea touches consumes vault quota and fires vault audit events. RKOJ proxies `/api/vault/{quota,audit,health}` so the operator sees live state in the Console's Vault drawer without CORS.
- **Multi-device real-time sync.** Syncthing (peer-to-peer, end-to-end encrypted, Tresorit-alike) replicates `D:\sinister-vault\sync\` between operator's Windows machine and Leo's device in seconds. No central server, no data leaves the devices.
- **Multi-account + HWID binding.** Profiles at `D:\sinister-vault\accounts\{operator,leo,...}.json` paired with hardware IDs. Future audit events can be scoped by user. Commit-as-upload pattern enforces user identity per write.
- **Unified audit stream.** Single JSONL log (`D:\sinister-vault\audit\YYYY-MM-DD.jsonl`) captures every vault write (`commit`, `push`, `pull`, `sync`, `snapshot`, `warn`, `error`). Operator sees who did what and when. Vault daemon appends; users can POST custom events.
- **Quota enforcement.** Soft cap 1024 GB, warn at 950 GB. Daemon recomputes usage every 60 s, persists `_quota.json`, blocks writes above hard cap (returns 507). Reads stay live so operator can still investigate an overfull vault.

## 3. Weaknesses + risks (per tool)

**sanctum-git:**
- **Gitea data NOT under vault quota.** SQLite database and repos live in `D:\Sinister Sanctum\tools\sanctum-git\data\`. The vault's quota check does not see them. `D:\sinister-vault\repos\` is the intended home after operator runs `setup-vault-data-dir.ps1`, but that migration is a pending operator action (PROGRESS.md 2026-05-19 06:50 item SV-B).
- **Single container, single admin.** One `operator` user created in the install wizard. No built-in multi-user auth for git push (SSH key + HTTP Basic Auth both auth as the same user). Multiple Sinister agents pushing require a unified credential store. Mitigated by per-agent branch discipline, but no cryptographic user isolation per push.
- **No integrated sync for non-git files.** Gitea is for versioned source. Unversioned artifacts (notes, media, random files) must go elsewhere (historically `_vault/`, now `D:\sinister-vault\sync\` with Syncthing). Two data lanes = two mental models.
- **Mirror script is operator-run, not automatic.** No cron job to `git-mirror push-all` every 5 minutes. Deferred future work (`FIRST-RUN.md:70`). If operator forgets to mirror, GitHub stays stale. Sanctum HEAD can diverge from GitHub HEAD without notice.

**sinister-vault:**
- **Daemon + Gitea + Syncthing are three separate processes with three separate install scripts.** `install-vault-task.ps1` registers the vault daemon as a scheduled task (pending); `tools/sanctum-git/setup-vault-data-dir.ps1` moves Gitea data (pending); `tools/sinister-vault/syncthing/install.ps1` installs Syncthing service (pending). No single "wire everything" command. Operator must run three scripts in sequence.
- **Vault MCP not registered in `.mcp.json`.** The vault agent at `D:\Sinister Sanctum\bots\agents\vault\server.py` (10 tools) exists but has no entry in `~/.claude/.mcp.json`, so no Claude session can reach the vault tools (`vault.commit`, `vault.push`, `vault.list`, `vault.accounts`, etc.). Vault is shipped-but-disconnected. Fix: add one entry to `.mcp.json` + restart Claude Code.
- **Three different ways to start the vault.** `vault-daemon.bat`, `Sanctum-Vault-Start.bat`, `install-vault-task.ps1` (scheduled task). No single entrypoint. Confusing for future ops.
- **Gitea data migration is manual + irreversible.** `setup-vault-data-dir.ps1` moves the entire Gitea data dir from `tools/sanctum-git/data` to `D:\sinister-vault\gitea`. Until run, Gitea quota is invisible. If run mid-session (without stopping the container), the move could corrupt the database or leave orphan writes. Not yet tested.
- **No auto-cleanup of old snapshots.** Snapshots append-only to `snapshots/`. No pruning policy. If snapshotted daily for a year, `snapshots/` grows to 500+ GB. Quota meter will warn, but daemon does not auto-delete old snapshots. Operator must manually prune or set up a deletion cron job.

## 4. Overlap analysis

**Spatial overlap: Gitea data lives in both.**
- `D:\Sinister Sanctum\tools\sanctum-git\data\` (current, post-install)
- `D:\sinister-vault\repos\` (target, post-migration via `setup-vault-data-dir.ps1`)

sanctum-git is *the git server*. sinister-vault is *the storage tier that houses the git server's data*. They do not overlap — they compose. Gitea is a tenant inside the vault. Until the data-dir migration is run, sanctum-git operates outside the vault's quota boundary.

**Functional overlap: None.**
- sanctum-git = version control (git-protocol server, push/pull, branches, per-agent discipline via naming convention)
- sinister-vault = unified storage (quota, audit, real-time sync, multi-account, multi-device snapshots)

A second git server (GitLab, Gogs, etc.) could replace sanctum-git. A different storage tier (NAS, S3, Backblaze) could replace sinister-vault. But the operator chose both *and* chose to compose them (Gitea data inside the vault). This is intentional: all writes (git + file) feed the same audit stream; all storage hits the same quota; Leo can sync the vault without understanding git branches.

**Should one absorb the other?** No.
- If vault absorbed git, it would need to implement `POST /git/push` and interpret git protocol, duplicating Gitea's code and losing Gitea's UI + Actions runner.
- If sanctum-git absorbed vault, it would need quota enforcement, Syncthing integration, and multi-account HWID binding — adding ~1000 LOC and out-of-scope functionality.
- The current split is clean: Gitea does git; vault does storage + quota + sync + audit. Compose them, do not merge them.

## 5. Recommendation

**KEEP-BOTH**

Both tools cover different, essential gaps. sanctum-git is the GitHub escape hatch + local git server + per-agent branch discipline enforcer. sinister-vault is the collaborative storage tier that unifies repos, sync, snapshots, and audit into one quota-bounded, multi-device pool.

The standing rule 2026-05-19 (DIRECTIVES.md) already pairs them: "sanctum-git tool (self-hosted Gitea on port 3000) pairs with PER-AGENT BRANCH DISCIPLINE." The vault contains Gitea data post-migration. They are intentionally composed, not redundant.

**Immediate actions (operator-side, not blocking the verdict):**
1. Run `install-vault-task.ps1` to register the vault daemon as SinisterVault scheduled task.
2. Run `setup-vault-data-dir.ps1` to relocate Gitea data under the vault quota.
3. Register the vault MCP by adding one entry to `~/.claude/.mcp.json` (see `bots/agents/vault/README.md` option B).
4. Add a cron-like "mirror every 5 minutes" task (deferred in v1; easy to add via Task Scheduler + `git-mirror.ps1 push-all`).

No architectural change required. Both tools ship as-designed and compose correctly.

## Operator decision

*(left blank for operator's thumb + free text)*
