# Plan :: jcode source-level fork → `sinister-rkoj`

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Status:** PROPOSED — operator-gated. **DO NOT EXECUTE** until rustup install greenlit.
> **Owner lane:** Sinister Sanctum (master) until fork lands; then handoff to `projects/sinister-rkoj/`.

## TL;DR

Fork the public jcode-0.12.3 Rust workspace into our own
`projects/sinister-rkoj/` and rebrand top-to-bottom (cargo name, persona,
telemetry, default sessions dir, authorship). Until we can run `cargo`,
the **sidecar shim** at `tools/sinister-jcode-shim/` (shipped 2026-05-21)
wraps the prebuilt binary with our env config — that's the bridge.

## Toolchain audit (2026-05-21)

| Tool | Path | Status |
|---|---|---|
| `rustc` | `which rustc` | **MISSING** |
| `cargo` | `which cargo` | **MISSING** |
| `rustup` | `which rustup` | **MISSING** |

No Rust toolchain on workstation. **Install path:**
[https://rustup.rs](https://rustup.rs) → download `rustup-init.exe`
(stable-x86_64-pc-windows-msvc). Footprint:

- `rustup-init.exe` itself: ~10 MB
- After running `rustup-init.exe` with default profile: ~1.5 GB
  (`%USERPROFILE%\.rustup\` + `%USERPROFILE%\.cargo\`)
- Note: the MSVC linker requires Visual Studio Build Tools or full VS —
  another ~5-7 GB. If Build Tools are already installed (likely — operator
  has Antigravity + Eclipse + many SDKs in PATH), this cost vanishes.

**Verify Build Tools before installing rustup:**
```
where link.exe       # should resolve to MSVC linker
where cl.exe         # MSVC compiler driver
```
If absent, install via `winget install Microsoft.VisualStudio.2022.BuildTools`
(operator-gated; ~6 GB additional).

## Source audit

- **Upstream snapshot:** `C:/Users/Zonia/Desktop/Github Research/jcode-0.12.3/`
- **Source size:** 378 MB on disk (working tree only — no `target/` yet)
- **Crate count:** 60+ crates in the cargo workspace (`crates/*` + root)
- **Estimated build artifacts:** ~5-10 GB in `target/` after first
  `cargo build --release` (Rust artifacts are notoriously heavy; debug
  build is even bigger)
- **Recurring build cost:** subsequent incremental builds ~500 MB-1 GB delta
- **Prebuilt operator drop:** `C:/Users/Zonia/Desktop/jcode-windows-x86_64.exe`
  (72 MB) — keep as reference for parity smoke-tests

## Fork target

`D:/Sinister Sanctum/projects/sinister-rkoj/` — **a real source directory,
NOT a junction**. Rationale:

- A junction to the upstream snapshot would tie our fork to an external
  path that lives outside Sanctum's git boundary.
- The fork IS ours. Source-of-truth lives inside Sanctum from day one.
- `_shared-memory/knowledge/junctions-vs-real-dirs.md` (TBD) will codify
  this — fork lanes are real, vendor mirrors are junctions.

Project scaffold inside `projects/sinister-rkoj/`:
```
projects/sinister-rkoj/
├── README.md                  # RKOJ-ELENO authored, AGPL
├── source/                    # the fork (copied, not junctioned)
│   ├── Cargo.toml             # name = "rkoj", authors = ["RKOJ-ELENO"]
│   ├── crates/
│   └── ...
├── EXACT-INSTRUCTIONS.md      # spawned-agent guidance for this lane
└── .gitignore                 # target/, *.pdb, *.rlib
```

## Rebrand checklist (do not execute yet)

Run these as a single sweep AFTER `cargo check` confirms the fork compiles
unmodified on this host (otherwise rebrand changes pile on top of build
breaks and triage becomes a nightmare).

- [ ] Cargo metadata
  - [ ] Root `Cargo.toml`: `name = "rkoj"`, `authors = ["RKOJ-ELENO"]`,
        `license = "AGPL-3.0-or-later"`, `repository = "https://github.com/<TBD>/sinister-rkoj"`
  - [ ] Each crate `Cargo.toml`: `name = "rkoj-..."` (or scope to `rkoj_` underscore),
        `authors`, `license` mirrored
  - [ ] Binary names: `jcode-windows-x86_64.exe` → `RKOJ.exe` (matches our existing PyInstaller binary's name; this is OK because the PyInstaller RKOJ.exe IS the Python Forge shell — the Rust RKOJ will live at a different path until we collapse them)
- [ ] Persona / branding
  - [ ] String replace: `"garden Panda"` → `"Sinister Garden EVE"` (operator persona; Joe gets `"Sinister Garden Frost"` in `PERSONA-FROST.md`)
  - [ ] All `"Panda"` mentions → `"EVE"` (Sinister Sanctum persona; preserve case)
  - [ ] ASCII art / splash banner → Sinister Sanctum logo glyph
  - [ ] Help text / man-page strings → "Sinister RKOJ" branding
- [ ] Telemetry
  - [ ] Disable upstream telemetry endpoint by default (probably hits Anthropic or first-party — audit `crates/*/src/telemetry.rs` paths)
  - [ ] Optional: point at our own opt-in endpoint (out of scope for v1; just kill the default)
- [ ] Session storage
  - [ ] Default `JCODE_SESSIONS_DIR` → `<sanctum>/_shared-memory/forge-memory/rkoj-sessions/`
  - [ ] Default `JCODE_CONFIG_DIR` → `~/.sinister/rkoj/`
  - [ ] Default `JCODE_SKILLS_DIR` → `D:/Sinister Sanctum/skills/`
- [ ] License header sweep
  - [ ] Every NEW `.rs` file: `// Author: RKOJ-ELENO :: <date>` + `// License: AGPL-3.0-or-later`
  - [ ] Upstream files keep their original headers + we append a `// Fork-modifier: RKOJ-ELENO :: 2026-05-XX` line on changed files
- [ ] License compliance
  - [ ] Read jcode's actual license (presumably MIT or Apache) — confirm AGPL re-license is permissible OR keep upstream license and add AGPL-3.0-or-later only to NEW code
  - [ ] Capture verdict in `_shared-memory/case-studies/jcode-license-compat-2026-05-XX.md`

## Sequencing — when operator unblocks

1. **Build Tools check** (`where link.exe`) — if missing, install VS Build Tools first
2. **`rustup-init.exe`** with default profile (`stable-x86_64-pc-windows-msvc`)
3. **Copy** `C:/Users/Zonia/Desktop/Github Research/jcode-0.12.3/` → `projects/sinister-rkoj/source/` (378 MB; use robocopy with `/MIR /XD target /XD .git`)
4. **`cargo check`** in `projects/sinister-rkoj/source/` — confirms toolchain + workspace integrity BEFORE rebrand. Expected: first run downloads ~600 MB of crates.io deps to `%CARGO_HOME%`, then ~3-5 min check pass.
5. **`cargo build --release`** — generates `target/release/jcode.exe` (or whatever the current bin name is). Smoke-test against operator's existing prebuilt to confirm byte-for-byte parity (or close).
6. **Rebrand sweep** (checklist above). Single commit per category for easy revert.
7. **`cargo build --release`** again post-rebrand. Output binary renamed to `RKOJ-rust.exe` (temporary name; collision with PyInstaller `RKOJ.exe` resolved later).
8. **Cutover**: shim retires, `/jcode` in Forge re-points to our binary.

## Risk register

| Risk | Mitigation |
|---|---|
| Disk fill (Rust toolchain + 60-crate build) | Operator-gated; document costs above; install on D:\ if C:\ is tight |
| Upstream license incompatibility with AGPL | Audit FIRST (step 0 before any rebrand commits); case-study verdict |
| Telemetry endpoint phones home during rebrand work | Block at firewall during dev; flip the default in source as priority-1 rebrand item |
| Drift between our fork + upstream jcode features | Pin upstream commit hash; quarterly merge-from-upstream sweep tracked in `_shared-memory/PROGRESS/Sinister RKOJ.md` (file TBD) |
| MSVC Build Tools missing → linker errors | Verify `link.exe` exists BEFORE running rustup-init |
| Cargo dep download bandwidth (~600 MB on first build) | Schedule for off-peak; operator already on residential bandwidth |

## What ships in the interim (already landed 2026-05-21)

- `tools/sinister-jcode-shim/` v0.1.0 — sidecar that runs the prebuilt
  binary with Sinister env injected. Wired into Forge as `/jcode` slash
  command. Adds `sinister_jcode_shim` to `RKOJ.spec` hiddenimports so it
  survives PyInstaller packaging.

This shim retires the day `projects/sinister-rkoj/source/target/release/RKOJ-rust.exe`
ships green.

## Operator gate

**This plan does not execute itself.** It is queued in
`_shared-memory/OPERATOR-ACTION-QUEUE.md` as a 🟠 high-priority item with
the disk + toolchain cost called out. Operator click required.

## References

- Upstream snapshot: `C:/Users/Zonia/Desktop/Github Research/jcode-0.12.3/`
- Operator prebuilt: `C:/Users/Zonia/Desktop/jcode-windows-x86_64.exe`
- Sidecar shim: `D:/Sinister Sanctum/tools/sinister-jcode-shim/`
- Persona doctrine: `D:/Sinister Sanctum/projects/sinister-freeze/PERSONA-FROST.md` (Joe's Frost) + `_shared-memory/knowledge/agent-identity-eve.md` (EVE)
- Rustup: [https://rustup.rs](https://rustup.rs)
- Brain entry to author after first cargo build: `cargo-target-disk-cost-on-windows.md`
