> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Sanctum Skills Hub :: SECURITY

Single security overview for the Sanctum fleet. Cross-linked from `skills/HUB.md` and from every external-import case-study. **Codex-peer-reviewed at creation** (review id will be logged at `_shared-memory/codex-reviews/` after writing).

## 1. Deny-list — patterns blocked by `~/.claude/settings.json`

These are blocked at the Claude Code permission layer; the deny-list is the safety floor even when `bypassPermissions: true`.

| Pattern | Why blocked |
|---|---|
| `rm -rf /*` | Root-level recursive delete. Operator data loss. |
| `rm -rf C:*`, `rm -rf D:*` | Drive-level recursive delete. Total loss. |
| `git push --force*` (against `main`/`master`) | Force-push to default branch overwrites collaborator history. |
| `taskkill /F /IM adb.exe` | Kills all-phones ADB; violates phone-containerization standing rule. |
| `gpg --delete-secret-keys`, `gpg --import-ownertrust *` | Identity loss. |
| Frida-spawn against TikTok / Snap apps | Anti-tamper trip; pure-API is the green path. |
| `Register-ScheduledTask` registering arbitrary persistent tasks | Operator owns scheduler. |
| Edits to `~/.claude/.mcp.json` | A bad entry kills every active session in the fleet. |
| Reads/writes matching `sk-ant-*` patterns | Anthropic API key handling — env-var only. |

**Catalog:** `SESSION-START/03-GOTCHAS.md` for the always-on subset; full mined catalog at `09_REFERENCE/SANDBOX-GOTCHAS.md` (regenerate via `aggregate-gotchas.bat`).

## 2. Allow-list scope — `~/.claude/settings.json`

- **Scope:** 210+ specific Bash patterns pre-authorized (git, npm, docker, gh, schtasks query, etc.). Plus `Read`, `Write`, `Edit`, `Glob`, `Grep`, `Agent`, `Skill`, `PowerShell` tools fully allowed.
- **Posture:** `bypassPermissions: true` + `skipAutoPermissionPrompt: true` — operator trusts the config; no interactive prompts.
- **Write/Edit paths allowed:** `D:/Sinister/**`, `D:/Sinister LLC/**`, `D:/Sinister Sanctum/**`, `C:/Users/Zonia/Desktop/**`, `C:/Users/Zonia/.claude/**`.
- **Implication:** the deny-list (above) is what stops a rogue or wrong action. The allow-list determines what doesn't prompt the operator.
- **Standing rule (EXPANDED AUTHORITY 2026-05-19, in `DIRECTIVES.md`):** sandbox restrictions are lifted; agents may execute most things directly. Reversibility + lane discipline still gate destructive ops + cross-zone touches.

## 3. Vault — at-rest secrets

- **Location:** `D:\Sinister Sanctum\_vault\` (master + operator only; never in product-repo source).
- **Encryption:** Fernet AES-128-CBC + HMAC-SHA256. Implementation: `D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\_shared\crypto.py` (`skills/crypto`).
- **Key derivation:** PBKDF2-HMAC-SHA256, 200,000 iterations. Salt embedded per-file.
- **Passphrase chain (priority order):**
  1. `SINISTER_VAULT_PASSPHRASE` env var (`User` scope on Windows).
  2. `~/.sinister/vault-key` file (legacy fallback).
  3. Interactive `getpass()` prompt (CLI use only; never inside an MCP server).
- **What goes in:** Yurikey roster (private), auth-keys.json (HWID-bound + per-account keys), operator-private notes the fleet may surface but should not store plain.
- **What doesn't:** anything `.gitignore` already covers — `_vault/`, `_shared-memory/heartbeats/`, `agent-prefs.json`, `operator-requests.jsonl`, `spawned-windows.jsonl`, codex-reviews payloads gated with `.gitkeep`, window-manager `_build-logs/` + `dist/`, `*.exe`.
- **Different from Sinister Vault (storage):** the **storage tier** at `D:\sinister-vault\` is a quota-managed collaborative store (Gitea + Syncthing + multi-account). The `_vault/` here is the at-rest crypto blob the FERNET layer protects. They're orthogonal — secrets pass through Fernet; storage tier is filesystem-grade.

## 4. Codex peer-review gate

**Standing rule #4** (in `_shared-memory/DIRECTIVES.md`):

> If you're about to push code that touches **auth, crypto, payment, secrets, or > 100 LOC** — request a Codex review BEFORE pushing.

- **Tool:** `D:\Sinister Sanctum\tools\codex-companion\codex.py` (Python CLI + RKOJ Console `POST /api/codex/review`).
- **Depth tiers:**
  - `quick` (gpt-4o-mini, ~30 s) — lint sweep, < 50 LOC.
  - `standard` (gpt-4o, ~60 s) — normal feature PR, 50-500 LOC.
  - `deep` (o1-mini, ~180 s) — auth/crypto/payment, architectural, > 500 LOC.
- **Outcome semantics:**
  - `pass` — proceed.
  - `warn` — proceed IF no `severity: high` findings; document in PROGRESS.
  - `fail` OR `warn`+`severity: high` — **BLOCK** the push; fix the underlying issue.
- **Audit log:** every review → `_shared-memory/codex-reviews/<UTC>-<sha1>.json` (append-only).
- **Graceful degradation:** if `OPENAI_API_KEY` unset, returns `{ok:false, error:"no API key ..."}`. For high-risk pushes treat as BLOCK; for low-risk, document the skip + proceed at discretion.

## 5. Lane discipline — who touches what

Per `PARALLEL-AGENT-COORDINATION.md` ownership zones + every `DIRECTIVES.md` mention:

- **Master agent** owns: Sanctum docs, `bots/_shared/`, `automations/`, `SESSION-START/`, `_vault/`, `skills/`, `tools/_INDEX.md`, this file.
- **Master agent NEVER touches:**
  - `~/.claude/.mcp.json` (one bad edit kills every active session).
  - `~/.claude/settings.json` (operator-owned; documents but doesn't modify).
  - `projects/<project>/source/` (product-repo sources; per-project agents own).
  - `D:\Sinister\01_Projects\Sinister\<project>\source\` (junction targets).
  - `LICENSE` (operator picks).
  - Any LetsText / JOKR / Yurikey roster artifacts in parent `D:\Sinister\Sinister Skills\`.
  - Another agent's branch (each agent works on `agent/<slug>/<topic>` only).
- **Per-project agents** own: their project's source + their branch + their `CLAUDE.md`.
- **Operator** owns: env vars, scheduled tasks, MCP registration, GitHub pushes, LICENSE pick, secrets, account rotation.

## 6. External-imports workflow

Every external skill / tool / MCP server / dataset goes through the inflow loop at `_shared-memory/external-imports/`:

```
URL scouted -> CANDIDATES.md row added (state: scouted)
            -> snapshot folder created (external-imports/<slug>/)
            -> ATTRIBUTION.md written (license + SHA + what-we-took)
            -> [Phase B] MCP wire-up if applicable (operator-clicked)
            -> [Phase C] fork files into skills/sk-<slug>/ (per skill)
            -> Codex peer-review (>100 LOC or auth/crypto/secrets)
            -> case-study _shared-memory/case-studies/<UTC>-<slug>.md (5 sections)
            -> Operator thumb (KEEP / KEEP-WITH-CHANGES / ARCHIVE / REPLACE-WITH-NEW)
            -> promote (skills/_INDEX.md status flip) OR archive (move to _archive/)
```

Reversibility: `archive` is move, not delete. Operator can promote back later via reverse `git mv`.

**License compliance:** every forked file carries its upstream notice (MIT/Apache/etc.) plus a Sanctum authorship line. See `_shared-memory/external-imports/ruflo/ATTRIBUTION.md` for the canonical pattern.

## 7. MCP hygiene — adding a new server safely

1. **Never hand-edit `~/.claude/.mcp.json`** — lane discipline (master); operator-only if hand-editing.
2. **Use the install scripts:**
   - Sanctum bots: `D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\install-fleet.ps1`
   - Vendor MCPs (Image 2 set): `D:\Sinister Sanctum\automations\install-mcp-servers.ps1`
   - One-offs (e.g. Ruflo): `claude mcp add <name> -- <command>` (operator-clicked from terminal).
3. **The install script ALWAYS backs up `.mcp.json` first** (to `.mcp.json.bak-<UTC>`).
4. **Restart Claude Code in a fresh window after registering.** Existing sessions don't pick up new MCP servers — they cache at spawn.
5. **Verify in a fresh session via `ToolSearch select:<server>.<tool>`** before relying on it.
6. **If a server breaks:** copy the most recent `.mcp.json.bak-<UTC>` back over `.mcp.json` and restart. The install scripts ALL create timestamped backups.

## 8. Cross-agent message etiquette (security-relevant)

Per `_shared-memory/DIRECTIVES.md` cross-agent coordination rule:

- Tag every cross-agent message with `cross-agent` (grep-able later).
- Lead with `[ASK]` / `[ANSWER]` / `[DISCOVERY]` / `[DELEGATE]` / `[ACK]` / `[DONE]` / `[PASS]` / `[DECLINE]`.
- Don't ping the same agent more than 3 times in 5 minutes without operator OK (avoid storms).
- `[DELEGATE]` to another agent's lane requires operator surface before the recipient acts.
- `[CONFIG] model=<X>` and `[UPDATE] <subkind>` are operator-originated only (RKOJ Console endpoints).

## 9. Audit trails (write-once, append-only)

| Log | Path | What lands |
|---|---|---|
| Bot absorption | `12_LLM_ORCHESTRATION/runtime-state/absorption-log.jsonl` | every `<bot>.absorb` / `<bot>.forget` |
| Script runs | `12_LLM_ORCHESTRATION/runtime-state/script-runs/<script>-<UTC>.json` | every `sync-fleet`, `verify-fleet-state`, `install-fleet`, etc. |
| Codex reviews | `_shared-memory/codex-reviews/<UTC>-<sha1>.json` | every peer-review verdict |
| Case-studies | `_shared-memory/case-studies/<UTC>-<slug>.md` | every external-import verdict |
| External imports | `_shared-memory/external-imports/CANDIDATES.md` | every scouted/imported source |
| Progress | `_shared-memory/PROGRESS/<agent>.md` | every meaningful agent milestone |
| Operator queue | `_shared-memory/OPERATOR-ACTION-QUEUE.md` | tickable operator todos |
| Auto-push | `_shared-memory/auto-push.log` | every `SinisterSanctumAutoPush` daemon tick |
| Brain | `_shared-memory/knowledge/<slug>.md` (Discoveries append-only) | every fix / gotcha / workaround |

None of these are ever deleted. Old entries get archived/superseded in place.

## 10. What's NOT covered here (operator scope)

- Drive encryption (VeraCrypt container plan in `SESSION-START/04-RECOVERY.md`; operator decides).
- LICENSE pick (`LICENSE-CANDIDATES.md`; operator decides).
- Phone Yurikey rotation (Yurikey52 sourcing; operator schedule).
- Hetzner deploy credentials (operator-owned `Sinister_OneClick_Deploy.bat` patterns).

## See also

- `~/.claude/settings.json` — allow/deny lists, plugins, hooks
- `SESSION-START/03-GOTCHAS.md` — always-on sandbox/classifier gotchas
- `_shared-memory/DIRECTIVES.md` — standing operator directives (canonical-14 standing rules)
- `_shared-memory/knowledge/codex-companion-usage.md` — Codex deep-dive
- `_shared-memory/knowledge/sinister-vault-architecture.md` — Vault architecture
- `_shared-memory/knowledge/adb-containerization.md` — per-phone isolation discipline
- `_shared-memory/external-imports/README.md` — inflow-loop spec
- `_shared-memory/external-imports/CANDIDATES.md` — every imported source
