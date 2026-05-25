<!--
Author: RKOJ-ELENO :: 2026-05-25
Audience: operator + Leo + any fleet agent reading deploy/
Composes with: deploy/MULTI-AGENT-COMMAND-CENTER.md + deploy/GETTING-STARTED.md
-->

# GPU Bot Fleet + Per-Agent Resource Quotas

> "make sure you get the rate limiting in check and we can run all agents with no issues. add things like when i launch a agent it balances it out over the other claude account we have or use more hardware like i said to do. i have a 4090 we need to be using that. just give me enough so i can still communicate and tell you what to do."
> — operator 2026-05-25 ~07:00Z

This page covers the three new automations Sub-L shipped this iter:

1. `automations/gpu_bot_fleet.py` — local 4090 + Ollama router
2. `automations/resource_quota_governor.py` — per-agent CPU/RAM caps + operator headroom
3. `automations/launch_rate_limit_governor.py` — pre-spawn rate-limit gate + account auto-balance

All three are pure Python (no new `.ps1` / `.bat` per doctrine `no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25`) and idempotent — safe to run repeatedly from schtasks or EVE.exe.

---

## 1. Install Ollama (one-time, you click nothing)

If Ollama isn't already running on `http://localhost:11434`, the fleet runs:

```
python automations/gpu_bot_fleet.py --install-ollama
```

That invokes `winget install Ollama.Ollama --silent --accept-source-agreements --accept-package-agreements`. After install, pull one small model:

```
ollama pull llama3.1:8b
```

The 8B model fits comfortably in 4090 VRAM with ~16 GB to spare for parallel use. Optional bigger picks: `qwen2.5:14b`, `qwen2.5-coder:14b`, `mistral:7b`.

`gpu_bot_fleet.py --status` will then list every pulled model + GPU memory free.

---

## 2. GPU bot fleet (route inference to the 4090)

Verify the 4090 is detected and Ollama is up:

```
python automations/gpu_bot_fleet.py --status
python automations/gpu_bot_fleet.py --health
```

`--health` exits 0 if both GPU and Ollama are usable, 1 with a one-line diagnostic otherwise. The launch governor (below) checks this before recommending the GPU route.

Route a one-off prompt to the local model:

```
echo "summarize this in 30 words: ..." | python automations/gpu_bot_fleet.py --route summarize
```

Every routed call appends a row to `_shared-memory/gpu-bot-fleet-log.jsonl` with model + token counts + duration.

---

## 3. Per-agent resource quotas (operator headroom guarantee)

Invariant — never violated, regardless of profile:

- **>= 4 logical CPU cores reserved** for operator interactive shell / browser
- **>= 6 GB RAM reserved** for the same
- **>= 50% GPU memory free** for operator's own apps

Snapshot of current state:

```
python automations/resource_quota_governor.py --status
```

Sample output on the operator's box (32 cores / 64 GB RAM):

```
System: 32 logical cores | RAM 65298 MB total, 33977 MB free | cpu 3.0%
Operator reserve: 4 cores + 6144 MB RAM + 50% GPU mem
Agent budget: 28 cores + 59154 MB RAM
```

Profiles (`--profile <name>`):

| Profile | Default agents | Privileged (sanctum/leo/operator/focus) | Use case |
| --- | --- | --- | --- |
| `balanced` | below_normal / 4 GB | above_normal / 8 GB | normal day-to-day |
| `operator-first` | idle / 2 GB | normal / 4 GB | gaming / heavy local work |
| `agents-first` | normal / 8 GB | above_normal / 12 GB | overnight long-running swarm |
| `single-agent-focus` | idle / 1 GB | high / 16 GB | one critical agent gets priority |

Dry-run (shows what WOULD change, mutates nothing):

```
python automations/resource_quota_governor.py --profile balanced --dry-run
```

Apply for real:

```
python automations/resource_quota_governor.py --apply --profile balanced
```

Install the 60-second auto-apply schtask:

```
python automations/resource_quota_governor.py --install-schtask
```

Single-agent focus mode (one agent gets the lion's share):

```
python automations/resource_quota_governor.py --apply --profile single-agent-focus --focus-slug sanctum
```

---

## 4. Launch rate-limit governor (auto-balance accounts)

Operator wants spawns to balance over the 4 (or N) Max-20x OAuth slots automatically. The governor consults:

- `_shared-memory/anthropic-usage-cache.default.json` (weekly + session %)
- `_shared-memory/rate-limit-causes.jsonl` (recent 429s)
- `claude-oauth-accounts.ps1 PickBest` (least-burdened slot)

Recommended pre-spawn check:

```
python automations/launch_rate_limit_governor.py --pre-launch sanctum --account auto
```

Output is human-readable by default, or `--json` for piping into the EVE launcher. Example output today:

```
project        : sanctum
chosen_account : operator
route          : claude
reason         : ok
weekly_pct     : 70%
warning        : weekly-warn:70%
```

When weekly hits >= 80% OR session >= 90% OR the chosen slot got a 429 in the last 10 min, the governor flips `route: gpu` and recommends `model: llama3.1:8b`. The launcher (or EVE.exe Settings page) is expected to honor that recommendation and offload to `gpu_bot_fleet.py --route` instead of spawning a Claude session.

Snapshot the full state to disk:

```
python automations/launch_rate_limit_governor.py --snapshot
```

That writes `_shared-memory/rate-limit-snapshot-<utc>.json`. A 5-minute passive schtask is available:

```
python automations/launch_rate_limit_governor.py --install-schtask
```

---

## 5. Sinister OS endgame (operator's vision)

Per the canonical 07:00Z utterance, the long-term plan is:

1. Every project agent spawns inside a per-component resource envelope (CPU / RAM / GPU memory).
2. The operator sets those percentages from an EVE.exe Settings page (future iter — sub-agent picks up the UI in the next iter; the backend below is ready).
3. The launcher consults `launch_rate_limit_governor.py --pre-launch` BEFORE every spawn. Hot accounts route to the GPU bot fleet automatically.
4. The operator always retains ≥ 4 cores + 6 GB RAM + 50% GPU memory. Typing latency in EVE.exe stays < 100 ms even with 5+ agents running.

Doctrine reference: `_shared-memory/knowledge/gpu-fleet-resource-quotas-doctrine-2026-05-25.md` (the binding rules + anti-patterns + composition graph).
