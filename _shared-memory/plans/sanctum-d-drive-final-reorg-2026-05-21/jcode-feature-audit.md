# jcode Feature Audit vs Sinister Forge SLASH_COMMANDS

Author: RKOJ-ELENO :: 2026-05-21
Persona: EVE (Sinister Sanctum orchestration agent)
Source binary: `C:\Users\Zonia\Desktop\jcode-windows-x86_64.exe` (72 MB, May-21 build)
Shim: `D:\Sinister Sanctum\tools\sinister-jcode-shim\sinister_jcode_shim\cli.py` (resolves the above)
Comparison target: `D:\Sinister Sanctum\projects\sinister-forge\source\forge\commands.py` (SLASH_COMMANDS dict @ line 3293-3391)

Operator (verbatim 2026-05-21): *"make sure jcode doesnt already have these options. make sure we are using that as a base and building off of it and it has all featrues."*

---

## A. jcode top-level subcommand surface (verified by `--help`)

```
serve         connect       run           login         repl
update        version       usage         self-dev      debug
auth          provider      memory        session       ambient
pair          permissions   transcript    dictate       setup-hotkey
setup-launcher browser      replay        model         auth-test
restart       help
```

**Sub-trees probed:**
- `auth`        → status, doctor
- `provider`    → list, current, add
- `memory`      → list, search, export, import, stats, clear-test
- `session`     → rename                       (sparse! no list/load/delete/save)
- `ambient`     → status, log, trigger, stop
- `model`       → list                         (sparse! no current/set/info)
- `replay`      → `<SESSION>` + many flags (--swarm, --speed, --video, --export, --auto-edit, --centered)
- `run`         → `<MESSAGE>` + --json/--ndjson
- `usage`       → --json
- Global flags: `-p/--provider`, `-m/--model`, `-C/--cwd`, `--resume [<ID>]`, `--socket`, `--debug-socket`, `--trace`, `--quiet`, `--no-update`, `--auto-update`, `--no-selfdev`, `--provider-profile`

---

## B. DUPLICATES (Forge re-implements something jcode already has)

These are duplicates **at the binary CLI surface** — Forge slash commands shadow jcode subcommands. Forge wraps jcode-as-sidecar via `/jcode`, so we MAY delegate down rather than re-implementing — but most of these are kept on purpose because Forge needs the in-pane Textual UX (and our memory/auth back-ends differ).

| Forge slash | jcode equivalent | Verdict |
|---|---|---|
| `/version` | `jcode version` | KEEP — ours adds bundled-tools list (RKOJ.exe-specific) |
| `/auth` | `jcode auth status` | KEEP — ours is 11-provider, jcode's is whatever providers it sees |
| `/login` (providers, doctor, env) | `jcode login`, `jcode auth doctor` | KEEP — ours wires sinister-login wallet (sub-doctrine); could DELEGATE `doctor <p>` to `jcode auth doctor` |
| `/provider` (list, current) | `jcode provider list`, `jcode provider current` | DELEGATE candidate — jcode list is more complete (40+ providers) |
| `/model` (list, current, set, info, providers) | `jcode model list` | KEEP — ours has current/set/info/providers; jcode only has `list` |
| `/usage` | `jcode usage --json` | DELEGATE — jcode already has per-provider quota fetch |
| `/memory` (search, list, write, recall) | `jcode memory list/search/export/import/stats` | KEEP — ours speaks sanctum brain (knowledge/*.md + forge-memory) which jcode doesn't see |
| `/rename` | `jcode session rename` | DELEGATE candidate — equivalent semantics |
| `/dictate` | `jcode dictate` | DELEGATE — jcode has native dictation already |
| `/transcript` | `jcode transcript` | DELEGATE — same |
| `/resume` | global `--resume [<ID>]` | KEEP — ours reads our resume-point bookmarks (different schema) |
| `/jcode` | (n/a — this IS the bridge) | KEEP — sidecar launcher |

**Count: 12 duplicates total. Of those, 5 are KEEP (Sinister-specific back-end), 7 are DELEGATE candidates (could call jcode subprocess instead of re-implementing).**

---

## C. GAPS (jcode has it, Forge doesn't surface it)

These are features jcode ships that Forge SHOULD expose as slash commands (or wire into existing ones):

1. **`jcode serve` / `jcode connect`** — daemon/client split. Forge could add `/serve` + `/connect` for the iOS/web pairing flow.
2. **`jcode pair`** — generates a pairing code for iOS/web. Forge has no equivalent. Add `/pair`.
3. **`jcode permissions`** — review/respond to ambient permission requests. Forge has no equivalent. Add `/permissions`.
4. **`jcode ambient`** (status/log/trigger/stop) — Forge has `/poke` (nudge) but no ambient-mode parity. Add `/ambient`.
5. **`jcode self-dev`** — canary session on shared server. Forge has no equivalent. Possibly add `/selfdev` (low priority).
6. **`jcode browser`** — browser automation setup + status. Forge has no equivalent. Add `/browser`.
7. **`jcode replay`** — replay saved session in TUI (with --swarm, --speed, --video). Forge has none. Add `/replay` (powerful — exports MP4 of session).
8. **`jcode setup-hotkey` / `setup-launcher`** — global hotkey Alt+; to launch + app-launcher install. Forge has none. Add `/hotkey` + `/launcher` (system-level).
9. **`jcode auth-test`** — end-to-end OAuth + refresh + smoke. Forge `/auth` only shows status. Add `/auth-test` (or extend `/login doctor`).
10. **`jcode debug`** — debug socket CLI. Forge has `/debug-visual` but not socket-level. Could add `/debug socket`.
11. **`jcode update`** — self-update. Forge has `/reload` and `/rebuild` but not jcode-specific update. Add `/update jcode` sub-command.
12. **`jcode restart` (windows save/restore across reboot)** — Forge `/restart` only respawns current session. jcode `restart` saves+restores all open windows. Add `/restart --all`.
13. **`--socket` / `--debug-socket` flags** — Forge doesn't surface socket overrides. Wire into `/jcode` opts.
14. **`replay --swarm`** — multi-pane synchronized replay. Tier-1 Sinister feature candidate for `/replay --swarm`.
15. **`replay --video` / `--cols` / `--rows` / `--fps`** — export session as MP4. Worth piping into `/export video`.

**Count: 15 gaps. Of these, ~5 are immediate adds (`/pair`, `/ambient`, `/permissions`, `/replay`, `/browser`); the others are nice-to-haves.**

---

## D. SINISTER-ONLY ADDITIONS (Forge has it, jcode doesn't — keep ours)

These are unique Forge slash commands with no jcode equivalent. Keep all.

**Session/state:** `/start` (project-picker bat parity), `/save` (resume-point bookmark), `/transcript`, `/todos`, `/todo`, `/focus`, `/diff`, `/search`, `/export`, `/catchup`, `/back`, `/transfer`, `/rewind`, `/unsave`

**Swarm/comms:** `/swarm`, `/dm`, `/broadcast`, `/agents`, `/subagent`, `/autoreview`, `/autojudge`

**Memory/brain:** `/memory` (sanctum brain), `/goals` (WORK-TOWARD.md), `/changelog` (PROGRESS), `/context`

**Loops:** `/improve`, `/refactor`, `/overnight`, `/fix`, `/poke`, `/recover`

**UI:** `/splitview`, `/split`, `/workspace`, `/alignment`, `/mermaid`, `/effort`, `/fast`, `/transport`

**System:** `/reload`, `/restart`, `/rebuild`, `/client-reload`, `/server-reload`, `/debug-visual`, `/mcp`, `/tools`, `/skills`, `/skill`, `/backup`, `/subscription`

**Core/info:** `/info`, `/context`, `/git`, `/config`, `/account`, `/quit`, `/exit`, `/clear`, `/compact`

**Plus** (added this session): `/create` (scaffold new project + MANIFEST row).

**Count: 50+ Sinister-only commands. These are the value-add layer. Keep all.**

---

## E. Final tally

- **Duplicates (12 total)** — 5 KEEP (Sinister back-end requires native), 7 DELEGATE candidates.
- **Gaps (15 total)** — 5 immediate adds recommended (`/pair`, `/ambient`, `/permissions`, `/replay`, `/browser`).
- **Sinister-only (50+)** — full keep. Forge is mostly the Sinister-only layer on top of jcode-as-engine.

### Recommended next-touch slash adds (deferred, not done this session)
1. `/pair` → `jcode pair` (10-line passthrough)
2. `/ambient` → `jcode ambient status|log|trigger|stop` (router)
3. `/permissions` → `jcode permissions` (router)
4. `/replay <session> [--video] [--swarm]` → `jcode replay` (router with arg-forward)
5. `/browser` → `jcode browser` (router)

These all become 5-15 line stub handlers that shell out to the jcode binary resolved by the sinister-jcode-shim — zero re-implementation, full feature parity, Sinister env injection baked in.

### Verdict on operator directive
**Bottom line:** Forge is correctly built ON TOP of jcode, not in parallel to it. The 50+ Sinister-only commands are the orchestration layer (sanctum brain, swarm, resume-points, MCP, mermaid, workstation, projects). The 12 overlaps mostly KEEP for Sinister-specific back-ends. The 15 gaps are improvement opportunities, not blockers — 5 should be added next session as thin routers to the jcode binary.
