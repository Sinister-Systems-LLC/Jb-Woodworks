<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# Sanctum → Sinister TERM — handterm fork brief

**From:** Sanctum (research subagent — no implementation) → **To:** Sinister TERM (owns source)
**Trigger:** Operator 2026-05-24 ~20:18Z — *"everything in our control ... just like jcode dev did ... snappy and fast comes before branding"*
**Heads-up:** sinister-term is a **Python + prompt_toolkit shell**; handterm is a **Wayland-native Rust emulator** — different layers. Brief assumes operator wants the *control surface + snappy feel*, not a Linux-only emulator rewrite. See §7.

## 1. What handterm is
Single-process Wayland-native terminal emulator in Rust (~24.2k LOC, 6 Cargo crates) benchmarked against hardware ceilings. MIT, 28 stars, 195 commits, active. Shared-GPU host: ~61 MB first window, **1-2 MB per extra**, ~16 ms new-window startup, 330 MB/s throughput, 3.4 MB binary.

## 2. Architecture map
| Path | Role | LOC |
|---|---|---|
| `handterm-common/` | grid + VT100/220 parser + protocol + state | ~5k |
| `handterm-server/` | daemon (soft-deprecated) | ~2k |
| `handterm-client/` + `-cpu/` + `-gpu/` | thin clients per backend | ~2k |
| `src/{main,lib,app,cli}.rs` | entry + clap CLI | ~1.5k |
| `src/{render,gpu_app,gpu_frame,gpu_runtime,visual,font}.rs` | wgpu + FreeType/rustybuzz | ~6k |
| `src/{input,host_input,host_commands}.rs` | kitty-kbd, mouse, bracketed paste | ~2k |
| `src/{frontend,native_scroll,color}.rs` | window + inertial scroll + truecolor | ~1.5k |
| `src/{pty,daemon,daemon_mode}.rs` | PTY + daemon path | ~1k |
| `src/{ipc,remote*,client,server}.rs` | **Unix-socket remote control** (`@ send-key-event`, `@ open-window`, `@ get-text`) | ~2.5k |
| `src/{config,platform,metrics,profiling,runtime,fd_watcher,backend,workloads}.rs` | TOML config + perf metrics + bench | ~1.5k |

## 3. Lift FIRST (snappy-first)
1. **Unix-socket remote-control IPC** — `src/ipc.rs` + `remote*.rs` + `host_commands.rs`. Lets callers drive the terminal: send keys, open windows, read screen text. Sinister-term has `/inbox` `/cross-agent` already; IPC means **other fleet agents (Sanctum/Forge/RKOJ) drive term programmatically** — direct hit on "everything in our control". Port: **3-5 days** as Python `asyncio` Unix-socket / Windows named-pipe alongside prompt_toolkit.
2. **Perf metrics + profiling surface** — `src/metrics.rs` `profiling.rs` `workloads.rs`. Per-frame timing, throughput, repaint/sec. Surfacing in PH7 toolbar makes "snappy" *measurable* and defends against regressions. Port: **1-2 days** as `term/metrics.py` wrapping `time.perf_counter_ns()` around redraw.
3. **Damage-tracked redraw + ring-buffer scrollback (10k)** — `handterm-common/` grid+parser. Sinister-term repaints every keystroke today; damage-tracking + bounded ring-buffer is the biggest perceptible "snap" upgrade. Port: **4-7 days** (touches redraw path; prompt_toolkit has primitives, policy is bespoke).

## 4. Do NOT port
1. **wgpu/softbuffer rendering** (`render.rs` + `gpu_*.rs`) — sinister-term runs INSIDE the host emulator (Windows Terminal/iTerm); GPU belongs to the host. Weeks of Rust+wgpu for nothing.
2. **Wayland frontend + winit** (`frontend.rs` `gpu_app.rs`) — Windows-first fleet, no Wayland users. winit cross-platform but surrounding code is Wayland-shaped; scope-creep huge.
3. **Daemon/multi-client** (`handterm-server/` `daemon*.rs`) — sinister-term is one-process-per-spawn via `Start-Sinister-Session.bat`. Lift §3.1 IPC WITHOUT the daemon.

## 5. Branding overlay points (AFTER snappy ships)
Per `_shared-memory/knowledge/sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24.md`: PH7 toolbar, PH8 breadcrumb, `/help` formatter are brand-able. Inherit `.lg-*` Liquid Glass tokens via truecolor (purple `#c084fc` = `\e[38;2;192;132;252m`), JOKR/Sinister-M in MOTD, per-project accent via `term-branding.json`. **EXPAND the skeleton** with a new `terminal-ansi-tokens` row — never fork.

## 6. License — MIT (safe to fork)
`Cargo.toml` declares MIT. No GPL contagion. Copy files with attribution in `LICENSE-THIRD-PARTY.md`. No operator gate. Commit trailers credit upstream `1jehuang/handterm`.

## 7. Next-step (one line)
**Port handterm's IPC socket + metrics surface into sinister-term FIRST (Python, ~1 week); defer any Rust emulator-layer rewrite** — IPC + measurable-snappy delivers operator intent at ~5% of full-rewrite cost.
