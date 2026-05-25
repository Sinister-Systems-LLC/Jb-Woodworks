<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Cross-Machine Non-Interference Doctrine

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Status:** canonical (operator-binding 2026-05-24 ~20:21Z)
> **Scope:** Sanctum lane orchestration. Coordination doctrine — no code ships.
> **Read by:** every EVE session on Zonia's box AND every EVE session on Leo's clone.

## Operator hard-canonical 2026-05-24 ~20:21Z

Operator (verbatim): *"by account rotation i mean claude account logged in. not leo for example but yes we do need to take note of those things so i can run agents on my end and leo on his and we won interfere with each other"*.

"Account rotation" = Claude login rotation (max-plan slots). It does NOT mean operators rotate. Zonia and Leo each run their OWN fleet against the SAME Sanctum repo (cloned to `D:\Sinister Sanctum` on each box). This doctrine defines how the two fleets stay out of each other's way.

## 1. Threat model

Four interference classes possible when both fleets are live:

1. **Git push collisions on `main`** — both auto-push daemons writing to origin/main concurrently → non-fast-forward rejects, lost commits, dirty merge state.
2. **Per-agent branch overlap** — both machines pushing the same branch name (e.g. both spawn `agent/sinister-sanctum/master-sweep-2026-05-19`) → force-push wars.
3. **Shared Claude account 429s** — both fleets using the same `operator` slot key concurrently → cross-machine 5-hour rate-limit thrash where each fleet thinks the OTHER is the offender.
4. **Shared-memory file overwrites** — both fleets writing the SAME shared-memory file (heartbeats, queue, JSONL log) within the vault-sync window → Syncthing conflict copies (`*.sync-conflict-<ts>-<dev>.<ext>`) and dropped updates.

## 2. Account isolation (the operator-clarified core)

- **Zonia's `D:\Sinister Sanctum\_shared-memory\claude-accounts.json`** is HERS. Slot `operator` = Sinister Sanctum (Zonia); slots `leo` / `slot3` / `slot4` remain `enabled:false` on her box unless she personally configures them for her own use.
- **Leo's `D:\Sinister Sanctum\_shared-memory\claude-accounts.json`** on HIS clone is HIS. He configures HIS slots against HIS own credentials files at `C:\Users\<leo>\.claude\credentials.*.json`. His `operator` slot (or a slot he names) points at HIS key, never Zonia's.
- **`claude-accounts.json` is per-machine state and MUST NOT round-trip through the vault.** If Syncthing replicates it, the receiving machine clobbers its own slot bookkeeping (current_sessions counters, last_spawn_at_utc, rate_limit timers). Add `_shared-memory/claude-accounts.json` to the Syncthing folder ignore list on both ends. (Same for `claude-accounts.log` + `account-watchdog.log` — local burn logs only.)
- **Credentials files (`C:\Users\<user>\.claude\credentials.*.json`) NEVER enter the repo or the vault.** Operator-private filesystem only; `.gitignore` already covers `_vault/` but the credentials live OUTSIDE the repo entirely.
- **No key sharing.** Zonia's `sk-ant-…` key stays on Zonia's machine. Leo's key stays on Leo's. If both fleets accidentally use the same key, the second one gets 429'd and the rotation library logs cross-machine confusion.

## 3. Branch isolation

- **Zonia's lane prefix:** `agent/sinister-sanctum/<topic>` (and per-project `agent/<slug>/<topic>` for spawned lanes — kernel-apk, sinister-os, etc., all originating from Zonia's box).
- **Leo's lane prefix:** `agent/leo-<slug>/<topic>` (NEW convention — Leo's per-project spawns prepend `leo-` to the slug so `agent/leo-sanctum/<topic>`, `agent/leo-kernel-apk/<topic>`, etc.).
- **`main` merges are operator-only.** The `sanctum-auto-push` daemon on each box pushes the CURRENT branch (per agent-autonomy doctrine 2026-05-23). On `agent/*` branches it only pushes existing commits. On `main` it stages + commits + pushes — so to avoid both boxes mutating `main`, **only Zonia's daemon runs on `main`**; Leo's daemon should stay on per-agent branches and PR into `main` via Gitea/GitHub for operator review.
- **`git fetch --all --prune`** runs every cycle on both sides, so each box sees the other's `agent/*` branches without ever clobbering them.

## 4. Shared-memory file conflict avoidance

Slug-namespaced (safe — concurrent writes don't collide):

- `_shared-memory/heartbeats/<slug>.json` — Leo's sessions write `leo-<slug>.json` (`leo-sanctum.json`, `leo-forge.json`, etc.) so two `sanctum.json` files don't fight.
- `_shared-memory/inbox/<slug>/` — already per-slug subdirs.
- `_shared-memory/PROGRESS/<DisplayName>.md` — Leo's sessions use `Leo on <Project>.md` (e.g. `Leo on Sanctum.md`) so they don't overwrite `EVE on Sanctum.md`.
- `_shared-memory/cross-agent/` — message files are timestamped + slug-prefixed.

**Append-only JSONL files BOTH fleets write — append is safe at line granularity, but Syncthing can still produce conflict copies if mid-second writes overlap. Mitigation: each line carries `"machine": "zonia" | "leo"` so dedupe is trivial:**

- `_shared-memory/fleet-updates.jsonl`
- `_shared-memory/improvement-log.jsonl`
- `_shared-memory/operator-utterances.jsonl`
- `_shared-memory/counter-arguments.jsonl`
- `_shared-memory/operator-ideas.jsonl` / `operator-requests.jsonl`

**Single-writer files — only ONE fleet edits, the other treats as read-only:**

- `_shared-memory/OPERATOR-ACTION-QUEUE.md` — Zonia's queue (Leo opens rows via fleet-update instead of editing).
- `_shared-memory/DIRECTIVES.md` / `WORK-TOWARD.md` / `WORKSTATION.md` — Zonia (operator-owned).
- `_shared-memory/knowledge/_INDEX.md` — either fleet may APPEND rows; never reorder. Conflict copy → manual merge by operator.
- `_shared-memory/claude-accounts.json` — per-machine, vault-ignored (see §2).

## 5. Coordination tools

- **`automations/fleet-update.ps1`** — cross-machine announcements. `kind=command -TargetSlugs leo-*` reaches only Leo's lanes; default broadcast reaches both.
- **Vault Syncthing folder** — file sync. Replicates the repo tree minus the per-machine ignore list (§2).
- **Per-agent inboxes (`_shared-memory/inbox/<slug>/`)** — direct messages between specific lanes regardless of which machine they spawned on.
- **Gitea (vault `:3000`) + GitHub** — PR review for `agent/leo-*` → `main`; operator merges.

## 6. What NOT to share

- `_vault/` (operator-private auth blobs, per-machine).
- `~/.claude/.mcp.json` (per-machine MCP wiring; operator-gated).
- Anthropic API keys / `credentials.*.json` (per-machine filesystem only).
- OS-specific absolute paths inside shared files (`C:\Users\Zonia\…`). When writing shared docs, use `$env:USERPROFILE` / `~/.claude/` / `D:\Sinister Sanctum\…` (the repo root is the one shared absolute path).
- Per-machine logs: `claude-accounts.log`, `account-watchdog.log`, `auto-push.log`, `_daemon-logs/`.

## 7. Pass criterion

Both operators can run 3 EVE agents simultaneously and observe:

(a) Zero Claude 429s caused by the OTHER fleet (each fleet's `_shared-memory/heartbeats/*.json` `rate_limited_until_utc` stays `null` unless THAT fleet exhausted its OWN slot).
(b) Zero `git push` rejects on `main` (only Zonia's daemon writes; Leo PRs in).
(c) Zero Syncthing `*.sync-conflict-*` files in `_shared-memory/` after a 30-min two-fleet co-run (heartbeats slug-namespaced; JSONLs use machine-stamped append; single-writer files respected).

## 8. Composes with

- `_shared-memory/knowledge/per-agent-branch-convention` (2026-05-19) — base branch naming the `leo-` prefix extends.
- `_shared-memory/knowledge/sanctioned-bypasses-doctrine-2026-05-21.md` (spawn authority + per-machine auto-push autonomy on agent branches).
- `_shared-memory/knowledge/agent-autonomy-push-and-completion-2026-05-23.md` (auto-push daemon ownership of `main` vs agent branches).
- `_shared-memory/knowledge/sinister-vault-architecture.md` (Syncthing folder model that both fleets share).
