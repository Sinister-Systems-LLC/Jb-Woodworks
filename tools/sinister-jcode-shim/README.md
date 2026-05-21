# sinister-jcode-shim

> **Author:** RKOJ-ELENO :: 2026-05-21
> **License:** AGPL-3.0-or-later
> **Status:** v0.1.0 — sidecar mode (operator-gated source fork still TBD)

## What this is

A small Python launcher that runs the **prebuilt** `jcode-windows-x86_64.exe`
(the operator's copy at `C:/Users/Zonia/Desktop/jcode-windows-x86_64.exe`) with
**Sinister branding / config / auth / model env vars injected** before exec.

This is a **sidecar** — we do NOT rebuild jcode from source for v0.1.0. The
source-level fork (rebrand "Panda" → "Sinister Garden EVE", flip telemetry,
swap default sessions dir, etc.) is operator-gated because it requires:

- Installing Rust via `rustup-init.exe` (~1.5 GB)
- Cloning jcode-0.12.3 source (378 MB)
- `cargo build` of a 60+ crate workspace (~5-10 GB additional disk)

The full fork plan lives at
`_shared-memory/plans/jcode-fork-2026-05-21/plan.md`. Until that lands, this
shim is the fastest way to give the operator a Sinister-branded jcode
experience with our wallet + model selection wired in.

## What gets injected

Resolution order for the jcode binary:

1. `$JCODE_BIN` env var (if set + exists)
2. `C:/Users/Zonia/Desktop/jcode-windows-x86_64.exe` (operator's canonical drop)
3. `shutil.which("jcode-windows-x86_64.exe")` then `"jcode"`

Env vars (filled only if not already set — operator overrides always win):

| Var | Value |
|---|---|
| `JCODE_CONFIG_DIR` | `~/.sinister/jcode/` |
| `JCODE_SKILLS_DIR` | `D:/Sinister Sanctum/skills/` |
| `JCODE_SESSIONS_DIR` | `<sanctum>/_shared-memory/forge-memory/jcode-sessions/` |
| `JCODE_BRANDING` | `sinister` |
| `JCODE_VENDOR` | `RKOJ-ELENO` |
| `JCODE_MODEL` | from `sinister_model.get_current()` (if installed + set) |
| `ANTHROPIC_API_KEY` | from `sinister_login` wallet (if claude provider configured) |
| `OPENAI_API_KEY` | from `sinister_login` wallet (if openai provider configured) |

## Usage

```
pip install -e "D:/Sinister Sanctum/tools/sinister-jcode-shim"

sinister-jcode-shim run                  # exec jcode with injected env
sinister-jcode-shim run -- --help        # forward args to jcode
sinister-jcode-shim run --dry-run        # print resolved env + argv, don't exec
sinister-jcode-shim run --print-bin      # print binary path + exit
sinister-jcode-shim doctor               # diagnose shim readiness
```

From Forge / RKOJ, the slash command is `/jcode` (registered in
`forge.commands` as a thin delegate to this CLI's `run` subcommand).

## Where the fork plan lives

`_shared-memory/plans/jcode-fork-2026-05-21/plan.md` — Rust toolchain audit,
disk-cost estimates, rebrand checklist, fork-target path
(`projects/sinister-rkoj/`), operator gate.

## Why a shim instead of a fork right now

- **No Rust toolchain.** `rustc`, `cargo`, and `rustup` are all absent from
  PATH on this workstation (verified 2026-05-21).
- **Disk cost.** The full toolchain + source + build output runs ~7-12 GB
  before anything ships. Operator decision.
- **The prebuilt binary already works.** Sitting at 72 MB on the Desktop, it
  responds to env vars for config-dir / skills-dir / sessions-dir. Wrapping
  it is a 5-minute job; forking is a multi-session sweep.

Once the operator approves rustup install, mission 2 (the source fork)
unblocks and this shim retires.
