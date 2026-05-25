<!-- decay:
  category: doctrine
  confidence: 1
  reinforcements: 0
  half_life_days: 365
-->
# GPU bot fleet + per-agent resource quotas + launch rate-limit governor (operator hard-canonical 2026-05-25)

**Author:** RKOJ-ELENO :: 2026-05-25
**Status:** binding for every spawn / scheduler / EVE.exe Settings surface
**Composes with:**
- `account-balancer` (Sub-I, `automations/account_balancer.py`)
- `multi-agent-launcher` (Sub-I, `automations/multi_agent_launcher.py`)
- `fleet-freeze-and-zombie-windows-diagnosis-2026-05-25.md` (Ollama not yet a Windows service)
- `bot-fleet-quick-reference.md` (13 local MCP bots already inventoried)
- `single-repo-push-policy-2026-05-25.md` (these files commit to Sanctum)
- `frequent-detailed-commits-per-agent-2026-05-25.md` (per-deliverable commit cadence)
- `no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25.md` (all 3 new files are Python)
- `loop-relentless-pursuit-doctrine-2026-05-25.md` (rule 10: tool-reach first)

## Operator verbatim (2026-05-25 ~07:00Z)

> "make sure you get the rate limiting in check and we can run all agents with no issues. add things like when i launch a agent it balances it out over the other claude account we have or use more hardware like i said to do. i have a 4090 we need to be using that. just give me enough so i can still communicate and tell you what to do. thats what i want to do with the sinister os. i want to be able to set usage that you can have to those partrs on the pc."

## Three-pillar approach

1. **Account rotation** (existing — Sub-I) — `claude-oauth-accounts.ps1 PickBest` + `account_balancer.py` already rotate the OAuth slot to the least-burdened Max 20x account. We do not duplicate that here.
2. **GPU bot offload** (new — Sub-L) — `automations/gpu_bot_fleet.py` detects the 4090 + Ollama and routes non-critical inference tasks to the local model so we stop burning Max-20x quota on summarisation / classification / template work.
3. **Per-agent resource quotas** (new — Sub-L) — `automations/resource_quota_governor.py` assigns each running Claude/EVE/Ollama process a priority class + (best-effort) RAM cap so the operator always retains a guaranteed headroom envelope.

## Operator headroom invariant (NEVER violated)

- **>= 4 logical CPU cores** reserved for operator's interactive shell, browser, EVE.exe foreground.
- **>= 6 GB RAM** reserved for the same.
- **>= 50% GPU memory free** for operator's own apps (browser GPU accel, Photoshop, gaming).

These reserves are HARD-CODED at the top of `resource_quota_governor.py` (`RESERVE_CORES`, `RESERVE_RAM_MB`, `RESERVE_GPU_PCT`) and apply across ALL profiles. The 4 profiles only redistribute the REMAINING budget between agents:

| Profile | Default agent | Privileged (sanctum/leo/operator) |
| --- | --- | --- |
| `balanced` | below_normal / 4 GB | above_normal / 8 GB |
| `operator-first` | idle / 2 GB | normal / 4 GB |
| `agents-first` | normal / 8 GB | above_normal / 12 GB |
| `single-agent-focus` | idle / 1 GB | high / 16 GB |

## Pre-spawn protocol (binding for every new spawn)

```
python automations/launch_rate_limit_governor.py --pre-launch <project> --account auto --json
```

The launcher MUST honor the returned `route` field:

- `route=claude` — proceed with spawn against the chosen OAuth slot.
- `route=gpu` — DO NOT spawn a Claude session. Instead pipe the task to `gpu_bot_fleet.py --route <task>` (model recommended in the same payload).

Trigger thresholds (in `launch_rate_limit_governor.py`):

- `WEEKLY_HOT_PCT = 80` — weekly usage >= 80% flips to GPU
- `SESSION_HOT_PCT = 90` — session usage >= 90% flips to GPU
- `RECENT_429_WINDOW_M = 10` — any 429 in the last 10 min on the chosen account flips to GPU

## Anti-patterns (forbidden — quality-degradation signals)

1. **Max-CPU agents starving the operator.** Setting `normal` or higher priority for non-privileged agents without consulting headroom budget. Symptom: operator typing latency in EVE.exe > 100 ms. Fix: rerun with `--profile operator-first`.
2. **GPU bot bypassing Claude when Claude is the right tool.** The GPU fleet is for offload of routine inference (summarisation, classification, JSON reshaping) — NOT for editing source, calling MCP tools, or anything requiring Claude's tool-use loop. Symptom: agent produces lower-quality patches. Fix: only route when `launch_rate_limit_governor` explicitly recommends `route=gpu`.
3. **No quotas = OOM crash.** Running 5+ agents simultaneously without `--apply` once = system OOM kills random processes (often the operator's browser). Fix: install the schtask once: `python automations/resource_quota_governor.py --install-schtask`.
4. **Forgetting Ollama can't reach SYSTEM-context schtasks.** Ollama runs as a per-user process today (per `fleet-freeze-and-zombie-windows-diagnosis-2026-05-25.md` — not yet a Windows service). Schtasks created with `/RU SYSTEM` cannot reach `localhost:11434` because the user-context Ollama listener is in a different session. Fix: install Ollama as a Windows service OR run the governor schtasks as the current user (the default in our `--install-schtask` commands).

## Pass criterion (must be measurable)

With 5 agents simultaneously active under `--profile balanced`:

- `nvidia-smi` shows the GPU is being used (non-zero memory) whenever the launch governor recommends `route=gpu`.
- `resource_quota_governor.py --status` shows >= 4 cores idle in operator reserve.
- Operator's typing latency in EVE.exe stays < 100 ms (subjective — operator confirms during smoke).
- `_shared-memory/launch-rate-limit-log.jsonl` shows non-zero `route=gpu` events when weekly_pct crosses 80%.

## File map (single source of truth)

| Path | LOC | Purpose |
| --- | --- | --- |
| `automations/gpu_bot_fleet.py` | ~340 | 4090 + Ollama router (--status / --health / --route) |
| `automations/resource_quota_governor.py` | ~340 | per-agent priority + RAM cap + 4 profiles |
| `automations/launch_rate_limit_governor.py` | ~250 | pre-spawn gate + account auto-balance + GPU fallback |
| `deploy/GPU-RESOURCE-QUOTAS.md` | ~150 | operator-facing how-to |
| `_shared-memory/gpu-bot-fleet-log.jsonl` | (audit) | every routed inference, with token counts |
| `_shared-memory/resource-quota-log.jsonl` | (audit) | every quota apply/dry-run |
| `_shared-memory/launch-rate-limit-log.jsonl` | (audit) | every pre-launch decision |
| `_shared-memory/rate-limit-snapshot-<utc>.json` | (audit) | passive 5-min snapshot |

## Future work (out of scope for this iter)

- EVE.exe Settings sub-page that surfaces the 4 profiles as one-click buttons + per-component sliders for the reserve invariants. Backend is ready; UI is the next iter's pickup.
- Job-object RAM HARD-cap (currently advisory — attaches process to a job but does not redefine the full `JOBOBJECT_EXTENDED_LIMIT_INFORMATION` struct). When Ollama becomes a Windows service we can do this without elevation prompts.
- Cross-machine GPU fleet (mesh routing to Leo's box if/when his GPU is also usable).
