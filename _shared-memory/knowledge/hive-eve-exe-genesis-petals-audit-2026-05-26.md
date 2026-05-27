<!-- decay:
  category: fact
  confidence: 0.9
  reinforcements: 0
  half_life_days: 60
-->
# HIVE :: eve-exe lane partition audit — genesis-architect-main + petals-main (2026-05-26)

> Author: RKOJ-ELENO :: 2026-05-26
> Lane: eve-exe :: Tag: hive, port-candidates, launcher, spawn-pipeline
> Composes with: `sanctum-scope-discipline-doctrine-2026-05-24` + `we-have-the-source-read-it-doctrine-2026-05-25` + `full-relentless-swarm-fanout-mindset-doctrine-2026-05-25` + `eve-ui-uniformity-doctrine-2026-05-24` + `single-repo-push-policy-2026-05-25`.

## 1. Operator directive (binding)

2026-05-26T22:47Z (inbox `2026-05-26T2247Z-from-sanctum-HIVE-partition-coord.json`): HIVE = 10 reference repos at `C:\Users\Zonia\Desktop\HIVE\`. Sanctum proposed partition: **eve-exe lane = `genesis-architect-main` + `petals-main`** (architect + launcher / model-partitioning UI). Cite FILE:LINE. Output: brain entry. NO OVERLAP with sanctum (jcode/hivemind/orchestration), memory (DALLE-pytorch + dalle-hivemind + sahajBERT), term (CALM + tessera), os (petals-infra + genesis-build).

## 2. Method

Parallel fan-out: 2 Explore sub-agents (one per repo, ~thorough). Each cited FILE:LINE for every claim. Findings synthesized below. Author this turn DID NOT port any of the ideas — this entry is `triage-shipped, port-candidates-noted` (per `no-bullshit-tested-before-claimed`). Slices land in future iters as concretely needed.

## 3. genesis-architect-main — what it actually IS

A **research-first lifecycle scaffolding skill** (NOT a launcher / NOT a swarm orchestrator). Per `README.md:3-8`: mines 15-20 GitHub repos + Issues BEFORE writing a file, identifies production pitfalls, then scaffolds with tests + CI/CD + security gates + ADR. Post-scaffold stays as "companion" with phases for research resolution + freshness audits. Skill-driven via Claude's native conversation interface — no custom TUI.

## 4. genesis-architect — 5 portable patterns (cite FILE:LINE)

| # | Pattern | Source | Proposed Sanctum target |
|---|---|---|---|
| G1 | **Phase-state checkpointing + resume.** JSON files record floor met (12 repos, 5 deep, evidence signed). On re-open, skip completed phases. | `genesis_state.py:19-63`, `:44-63` (`require_phase2()`) | `automations/sinister_swarm.py` slice-state file; `automations/eve.py` picker can offer "Resume from Phase N" |
| G2 | **Environment probe → cached JSON.** Single Python probe returns `{os, wsl, python_version, package_managers, scripts_path}`. Reused on subsequent launches. | `env_probe.py:32-94`, `:58-94` | NEW `automations/scripts/env_probe.py`; called from `start-sinister-session.ps1` to replace inline PowerShell env detection |
| G3 | **Hard-gate A/B/C/D menu pattern.** "Q2 Archetype: A) Minimalist B) Scalable C) Research-decide D) Custom" with free-text fallback; blocks on explicit letter. | `SKILL.md:99-107`, `:194-237` | `automations/eve.py` picker — replace free-text prompts with structured letter menus (composes with `eve-ui-uniformity-doctrine`) |
| G4 | **Two-layer knowledge resolution.** Vault hit → instant/free; miss → external API with retry-backoff + rate-limit. Vault is `.genesis/vault/` JSON index + per-entry files searched by keyword scoring + popularity. | `vault.py:57-143`; `resolve_engine.py:191-223` | NEW `.sinister/vault/` for project configs / agent prefs / theme choices; loaded by `automations/eve.py` BEFORE prompting |
| G5 | **Evidence pack + downstream mitigation enforcement.** `ARCHITECTURE_EVIDENCE.md` + `.genesis/evidence.json` hold required mitigations (each with `mitigation_file_path` + optional symbol + import). Phase 6 enforcer AST-parses targets, blocks commit if mitigation missing. | `evidence_pack.py:1-24`; `mitigation_enforcer.py:50-174`, `:73-85`; `SKILL.md:226-228`, `:290-307` | `automations/start-sinister-session.ps1` reads `ARCHITECTURE_EVIDENCE.md` if present, injects into spawned-agent system prompt; new `automations/scripts/enforce_architecture.py` runs post-session drift check |

**Anti-overlap call-outs (route AWAY from eve-exe):**
- Genesis does NOT multi-agent / fan-out / multiprocess — single-skill sequential. So **no sanctum-lane overlap** (sanctum owns multi-agent orchestration via `sinister_swarm.py`).
- Subprocess patterns (`env_probe.py:75-84` hardcoded-arg subprocess.run; `scaffold_smoke_test.py` 3-retry test runner; `genesis_subcommands.py` `pip list`/`git log` wrappers) are GENERIC — keep in eve-exe scope only for launcher use.

## 5. petals-main — what it actually IS

**BitTorrent-style distributed inference engine for LLMs** (`README.md:3-4, 40-42`). Servers host model layers, clients route forward/backward passes across remote peers. Up to ~6 tok/s on 70B. Ships a **multi-mode CLI** (via `configargparse`) — NOT a TUI; NOT a dashboard (external monitor lives at `health.petals.dev`, NOT in this repo).

## 6. petals — 5 portable patterns (cite FILE:LINE)

| # | Pattern | Source | Proposed Sanctum target |
|---|---|---|---|
| P1 | **Multi-mode CLI with mutually-exclusive arg groups + YAML fallback.** `configargparse.ArgParser` with `default_config_files=["config.yml"]`; `--config <path>` override; `group.add_mutually_exclusive_group()` for model selection. CLI > YAML > defaults. | `src/petals/cli/run_server.py:19-232`, `:21-23`, `:25-31` | `automations/eve.py`: add `--mode [spawn-agent|list-fleet|health-check]` mutually-exclusive groups; `automations/session-templates/projects.json` gains optional per-project YAML override |
| P2 | **Cached throughput estimation + ETA UX.** One-time `measure_throughput_info()` ("Measuring network and compute throughput. This takes about a minute...") with lockfile to avoid races; result cached + reused. User feedback printed on completion. | `src/petals/server/throughput.py:37-108` | NEW `automations/scripts/throughput.py` or inline in `eve.py`: estimate wall-clock for agent spawn from one-time calibration + cached result; show ETA in mintty before spawn |
| P3 | **ServerState 3-state enum + daemon announcer.** `ServerState ∈ {OFFLINE, JOINING, ONLINE}`. `ModuleAnnouncerThread` periodic DHT announce every `update_period`s with `cache_tokens_left` + RTT pings to next servers. | `src/petals/data_structures.py:33-36`, `:42-82`; `src/petals/server/server.py:650-750`, `:710+` | NEW `automations/fleet-state.py`: `{agent_id → {state ∈ SPAWNING/READY/ERROR/RECYCLED, blocks_held, throughput, spawned_at}}` JSON; **Sinister Panel `/fleet` tab reads from here** (NOT from per-process polling — composes with `sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24`) |
| P4 | **Human-friendly multiaddr / IP shortcuts.** `--port 31330` + `--public_ip` map to complex `--host_maddrs` / `--announce_maddrs` libp2p multiaddrs; visible-addrs string logged on startup; public-vs-private-swarm distinction. | `src/petals/cli/run_server.py:41-57`; `src/petals/server/server.py:152-157` | When spawning a cloud agent or remote slice from eve.py, display `http://<public_ip>:<port>` short-form NOT raw multiaddr/socket; surface in Sinister Panel `/fleet` |
| P5 | **Humanfriendly units + device/quantization presets.** `--max_disk_space "50GB"` parsed via `humanfriendly.parse_size()`; `--torch_dtype` + `--quant_type` + auto-detect of `inference_max_length` / `max_batch_size` from model arch. | `src/petals/cli/run_server.py:87-94`, `:96-165`, `:30-35` | `automations/session-templates/projects.json` + `agent-prefs.json` schema: add `maxCacheGB` (humanfriendly-parsed), `torchDtype`, `quantType`, `inferenceMaxLength`. Loop-checkpoint manager can also adopt parse_size for backup size limits |

**Anti-overlap call-outs (route AWAY from eve-exe):**
- **OS lane (petals-infra):** distributed-inference internals — block selection (`src/petals/server/block_selection.py`), DHT consensus (`src/petals/utils/dht.py`), Hivemind p2p / libp2p multiaddrs / circuit relay NAT traversal, model quantization (LoRA/QLoRA/int8 weight handling). FLAGGED, not claimed.
- **Sanctum lane (orchestration):** rebalancing-on-imbalance, thread+multiprocessing core, Runtime in main-thread pattern (`src/petals/server/server.py:328-384`). FLAGGED, not claimed.
- **Memory lane:** model architecture / Hugging Face hub load mechanics. FLAGGED, not claimed.

## 7. Cross-pattern composition (10 candidates → ranked priority)

Top-5 portable into eve-exe scope (highest first):

1. **P3 — ServerState enum + fleet-state.json** (composes with G1 phase-state + Sinister Panel `/fleet` tab + existing `_shared-memory/heartbeats/*.json` schema). Highest-value because it unifies disparate ad-hoc state files we already write piecemeal. → New module `automations/fleet-state.py`.
2. **G3 — Hard-gate A/B/C/D menus** (composes with `eve-ui-uniformity-doctrine`). Direct fit for `automations/eve.py` picker + first-run wizard. Low-risk single-file change.
3. **P1 — Multi-mode CLI + YAML fallback** (composes with `no-bat-no-ps1-do-it-for-me-doctrine`). Lets us collapse multiple `.bat` entrypoints into one `eve.py --mode X` with project YAML override.
4. **G2 — Cached env probe** (composes with `automate-everything-no-operator-admin`). Replaces brittle inline PowerShell env detection in `start-sinister-session.ps1` with a deterministic Python JSON probe.
5. **P2 — Throughput calibration + ETA UX.** Best when paired with `_shared-memory/eve-incidents.jsonl` spawn timings already captured — calibrate once, ETA every spawn afterwards.

Defer (port only when concretely needed, per safe-quality-loops):

- **G4 vault** — overlaps `sinister-memory` lane's existing forge-memory CLI; route to memory lane for review BEFORE eve-exe ports.
- **G5 evidence-pack mitigation enforcer** — high-value but high-touch (AST parsing, drift detector). Wait for one concrete bug it would have caught.
- **P4 multiaddr shortcuts** — only matters when we actually spawn remote / cloud agents (not local mintty).
- **P5 humanfriendly + quant presets** — nice-to-have, no current pain point.
- **G1 phase checkpointing** — already partially covered by resume-points + loop-checkpoint manager; revisit if/when we add multi-phase plans to eve.py picker.

## 8. Anti-overlap explicit (so other lanes can audit)

eve-exe lane CLAIMS (this audit): launcher / picker / spawn-CLI / fleet-state schema / per-session env probe / per-spawn ETA UX patterns from these two repos.

eve-exe lane DOES NOT CLAIM (route elsewhere):
- **sanctum**: jcode + hivemind + multi-agent orchestration internals.
- **memory**: DALLE-pytorch + dalle-hivemind + sahajBERT (training); knowledge-vault internals overlap (G4) routed to memory for verdict.
- **term**: CALM + tessera.
- **os**: petals-infra (DHT consensus / libp2p / NAT) + genesis-build.

If any future eve-exe slice ports something on the AWAY list, it MUST cross-post the diff to the owning lane's inbox.

## 9. Status

`triage-shipped, no-code-this-iter, 10-port-candidates-ranked` (3 of top-5 are next-iter candidates; remaining 5 deferred per safe-quality-loops rule). Acceptance: brain entry + heartbeat ack + inbox `_acked/`. Composes with: `we-have-the-source-read-it-doctrine-2026-05-25` (read source directly, no RE), `full-relentless-swarm-fanout-mindset-doctrine-2026-05-25` (2 parallel Explore agents), `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (no port claimed shipped without smoke-test). Decay fact / 0.9 / 60 days (port-candidate freshness window).
