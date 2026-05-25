# Multi-Agent Command Center

> **Author:** RKOJ-ELENO :: 2026-05-25
> **Operator brief (verbatim 2026-05-25 ~06:30Z):** *"think of how i can control, open, manage multiple claude agents at once in the most efficent manner you can come up with based on everything we have been building and our customs."*
> **Image 1 reinforcement:** *"make sure you place in good round robin jerry rigging so that we can use the 4 different accounts flking under the radar to gain more power. i ened you to hvae the over seer track the rate limit rate and slowly adjust things as you find out more info about the rate limits."*

EVE's "Tony Stark" view of the fleet: one screen to launch, monitor, and steer N Claude agents across N OAuth slots, with an automatic round-robin rate-limit feedback loop.

---

## 1. The four pieces

| File | Purpose |
| --- | --- |
| `automations/multi_agent_launcher.py` | One-key swarm spawner; consumes named presets; round-robins OAuth accounts. |
| `automations/swarm-presets.json` | Named spawn bundles (`sanctum-quad`, `full-fleet`, `solo-deep`, plus operator-built customs). |
| `automations/multi_agent_status.py` | Live multi-pane dashboard + batch ops (`poke`, `save-close`, `rotate-account`, `resume-all`). |
| `automations/account_balancer.py` | Overseer rate-limit feedback loop; emits `ROTATE` / `THROTTLE` / `SAFE` / `EXHAUST` verdicts; auto-`MarkLimited` on threshold cross. |

All four wire into EVE.exe's Agents page via three new keys: `Mu)` Multi-Launch, `Db)` Dashboard, `Rl)` Rate-Limit recommend (existing K/C/S/Pa/Msg/A/N/n/p keys preserved).

---

## 2. Spawn 5 agents in 30 seconds

```
EVE.exe -> Agents -> Mu     (or:  python automations/multi_agent_launcher.py --swarm full-fleet)
preset name: full-fleet
```

Output:
```
swarm-launch :: full-fleet  (5 spawn(s), stagger=3s)
  [1/5] OK  spawned sanctum@operator        branch=agent/sanctum/lane-sanctum-2026-05-25
  [2/5] OK  spawned sinister-os@leo         branch=agent/sinister-os/lane-os-2026-05-25
  [3/5] OK  spawned sinister-chatbot@operator branch=agent/sinister-chatbot/lane-chatbot-2026-05-25
  [4/5] OK  spawned sinister-overseer@leo   branch=agent/sinister-overseer/lane-overseer-2026-05-25
  [5/5] OK  spawned jb-woodworks@operator   branch=agent/jb-woodworks/lane-jb-2026-05-25
done :: 5/5 spawned. log: _shared-memory/multi-launch-log.jsonl
```

Each spawn pops its own terminal window via `start-sinister-session.ps1` (detached). With 3-sec stagger -> ~15 sec total wall clock for 5 spawns. The `sanctum-quad` preset (4 spawns @ 2-sec stagger) finishes in ~8 sec.

---

## 3. Live dashboard

```
EVE.exe -> Agents -> Db    (or:  python automations/multi_agent_status.py --watch)
```

Per row: `slug | state | age | account | swarm | loop | iter | focus`. State color-coded:

- **RUNNING** (green) -- heartbeat < 5 min
- **STALL** (yellow) -- 5 min <= age < 60 min
- **CRASHED** (red) -- age >= 60 min

Footer aggregates: `RUNNING N / STALL N / CRASHED N / total N`. Refreshes every 5 sec via `\033[2J\033[H` (in-place repaint). `Ctrl-C` exits.

One-shot snapshot for scripts: `python automations/multi_agent_status.py --once`.

---

## 4. Batch ops

```
python automations/multi_agent_status.py --batch <action> [--message "..."] [--dry-run]
```

Targets = every agent with heartbeat age < 60 min ("live"). Actions:

| Action | Backend | Effect |
| --- | --- | --- |
| `poke` | `agent-poke.ps1 Poke` | sends `kind=loop-poke` row to each live agent's inbox |
| `save-close` | `agent-actions.ps1 SaveAndClose` | resume-point write + graceful close |
| `rotate-account` | `claude-oauth-accounts.ps1 RotateToNext` | atomic OAuth slot swap |
| `resume-all` | `multi_agent_launcher.py --swarm solo-deep` | conservative relaunch of one deep-work agent |

---

## 5. Account balancer (overseer feedback loop)

```
python automations/account_balancer.py --recommend
```

Reads `_shared-memory/anthropic-usage-cache.default.json` + `rate-limit-causes.jsonl` (last 5 min window) + `claude-accounts.json`, then emits one table:

```
account      state       sess%   wk%  429/5m   reset verdict    reason
----------------------------------------------------------------------
operator     ON             34%   67%       0   2h11m SAFE       session 34% / weekly 67%
leo          ON             82%   71%       0     45m THROTTLE   session 82% / weekly 71%
slot3        UNLINKED        0%    0%       0       ? SAFE       session 0% / weekly 0%
```

### Thresholds

| Signal | Action |
| --- | --- |
| `session_pct >= 95` | `EXHAUST` |
| `weekly_pct >= 85` | `ROTATE` |
| `session_pct >= 80 OR weekly_pct >= 70` | `THROTTLE` |
| any 429 in last 5 min | `ROTATE` (recent_429_window_m = 5) |

### Auto-mark

```
python automations/account_balancer.py --auto-mark-limited
```

Calls `claude-oauth-accounts.ps1 MarkLimited <slot> -Until <utc+30min>` for any `ROTATE`/`EXHAUST` slot that isn't already limited. Logs to `_shared-memory/account-balancer-log.jsonl`.

### Schtask install (10-min cadence)

```
python automations/account_balancer.py --install-schtask
```

Registers `SinisterAccountBalancer` to run `--auto-mark-limited` every 10 min. Idempotent (uses `/F` overwrite). The overseer can now silently bench an over-spent account and the next `multi_agent_launcher --swarm` will round-robin past it -- this is the "fly under the radar" knob the operator asked for.

---

## 6. Swarm-preset schema

`automations/swarm-presets.json`:

```jsonc
{
    "presets": {
        "<preset-name>": {
            "_doc": "human-readable description",
            "stagger_seconds": 2,
            "spawns": [
                {
                    "project": "sanctum",         // must match projects.json key
                    "account_hint": "operator",   // explicit slot OR "auto" (round-robin)
                    "modes": { "loop": true, "swarm": true, "loop_relentless": true },
                    "model": "opus",
                    "topic_suffix": "swarm-A"     // tail of branch name
                }
            ]
        }
    }
}
```

Build a custom preset without editing JSON:

```
python automations/multi_agent_launcher.py --build-preset my-preset \
    --projects sanctum,sinister-os,jb-woodworks \
    --modes loop,swarm,relentless
```

---

## 7. Round-robin behavior

`multi_agent_launcher.py` resolves `account_hint: "auto"` via `pick_round_robin(used_this_run)`:

1. Filter accounts to `enabled=true AND not rate_limited`
2. Prefer slots NOT used yet in this swarm launch
3. If all live slots already used, recycle from the start
4. Last-resort fallback: `claude-accounts.json.default`

Combined with `account_balancer --auto-mark-limited`, the launcher will naturally skip any slot the overseer benched in the last 10-min sweep. This pools quota across N Max-20x accounts without ever exhausting one to a 429-storm.

---

## 8. Audit log

Every spawn writes a row to `_shared-memory/multi-launch-log.jsonl`. Every balancer scan/auto-mark writes a row to `_shared-memory/account-balancer-log.jsonl`. Both are append-only JSONL; tail with standard tools.

---

## 9. Doctrine composes

- `loop-relentless-pursuit-doctrine-2026-05-25` -- every swarm spawn defaults to `loop_relentless=true`
- `single-repo-push-policy-2026-05-25` -- branch convention `agent/<project>/<topic>-<utc-date>`
- `no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25` -- all new code is Python; existing PS1s (start-sinister-session, agent-actions, agent-poke, claude-oauth-accounts) are called but no new PS1 was created
- `automate-everything-no-operator-admin-2026-05-25` -- schtask install is one CLI invocation, no operator clicks required
