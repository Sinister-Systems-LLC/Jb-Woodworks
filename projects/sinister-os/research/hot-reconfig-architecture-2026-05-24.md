# Hot-Reconfig + Reboot-Banner Architecture

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Lane:** sinister-os
> **Trigger:** Operator hard-canonical 2026-05-24 *"I want to be able to actively change things like ui look add things etc without a reboot. if reboot required then have banner for it. think fo all the rick possibilities we could add."*
> **Research-agent source:** C (general-purpose; see _shared-memory/plans/sinister-os-massive-expansion-2026-05-24T2110Z/plan.md ITER 8).

## 1. Layer hot-reload matrix

| Layer | Mechanism | Hot? | Notes |
|---|---|---|---|
| CSS tokens (`sinister-theme-tokens.css`) | CSS custom properties + `MutationObserver` on `<html>` data-attrs | YES | Panel SSE-subscribes to `/etc/sinister/theme.toml`; swaps `--accent` live |
| Panel routes / components | Next.js HMR (dev) / blue-green container swap via `panel-current` symlink (prod) | YES | nginx upstream switches atomic; zero flash |
| Systemd unit edits | `systemctl daemon-reload && systemctl try-restart <unit>` | YES (most) | Reboot only if unit is `basic.target` / `sysinit.target` dep |
| Kernel modules | `modprobe -r <mod> && modprobe <mod>` | YES (most) | Reboot for in-use storage/network drivers, KASLR-affected modules |
| Kernel image itself | `kexec -l && kexec -e` (warm) OR full reboot | NO (banner) | Banner trigger; offer kexec as "fast reboot" |
| Hyprland compositor | `hyprctl reload` (config) / `hyprctl dispatch exec` (new bindings) | YES | Reboot only if Wayland protocol version changes |
| eve daemon | `SIGHUP` to `sinister-eve.service` → re-reads `/etc/sinister/eve.toml` | YES | Socket survives; in-flight requests drain |
| Voice service | `systemctl --user restart sinister-voice` | YES | Wake-word interrupted ~200 ms |
| Tailscale / WG mesh | `tailscale set --advertise-routes=...` / `wg syncconf` | YES | Routes shift without tunnel teardown |
| glibc / ld-linux / PAM | Needs reboot | NO | `needrestart -k` detects |
| `/etc/sudoers.d/eve` | `visudo -c` validate then write | YES | sudo re-reads per-invocation |
| GPU driver swap (NVIDIA → nouveau) | NO | NO | Banner: "GPU stack change" |

## 2. Reboot-banner architecture

- **State file:** `/var/lib/sinister/reboot-required.json` — schema: `{required: bool, severity: "info"|"warn"|"critical", reasons: [{trigger, since_utc, layer, hint}], kexec_capable: bool, snooze_until: iso8601|null}`
- **Emitter:** `sinister-reboot-tracker.service` watches:
  - `dpkg/pacman` post-install hooks → kernel-version delta
  - `needrestart -b` output
  - `/etc/sinister/*.toml` classifier verdicts
  - `lsof | grep DEL` for replaced libs
- **Surface (primary):** Panel header strip — fixed top, amber for `warn`, red pulse for `critical`. Reads via SSE `/api/system/reboot-required`. One-click actions: `Reboot now` / `Kexec (fast)` / `Snooze 8h` / `View reasons`.
- **Surface (fallback):** Hyprland `waybar` module reads same JSON when panel unavailable.
- **Snooze rule:** writes `snooze_until` ISO timestamp into same JSON; tracker honors it but `critical` ignores snooze after 24 h.

## 3. Rich possibilities (AI-as-shell exclusives — operator-prompted)

1. **Predictive cache pre-warm** — eve learns "operator opens panel + vault at 8 am" → systemd timer pre-warms containers + DNS at 7:55.
2. **Voice workflow record-and-replay** — `eve, record workflow "deploy"` captures next N actions (clicks / typed cmds / file edits) into replayable `.eve-flow` files.
3. **Per-app proxy routing** — eve detects app launch (`exec` / cgroup events), routes traffic through per-app exit node (Tailscale userspace) — Chrome via US-east, dev SSH direct, torrents via WG-fallback.
4. **AI-driven backup decisions** — eve watches file-edit hot-paths; auto-snapshots `~/projects/<hot>` to vault every 5 min during active editing, hourly when cold, never when reproducible-from-git.
5. **Intent-aware notifications** — eve reads incoming alert + operator's current focus (active window + last 30 s of voice) → suppresses non-critical pings during deep-work, batches them for next idle window.
6. **Live config A/B test** — apply new Hyprland gap settings to one monitor only for 60 s, eve asks "keep it?" via voice; auto-revert on no answer.
7. **Self-healing service watchdog** — eve sees `sinister-vault.service` flap 3× in 10 min → reads journalctl, proposes fix, executes on operator nod.
8. **Cross-machine context bridge** — operator says "continue this on laptop" → eve serializes current window stack + open files + clipboard to vault; laptop's eve restores on next login.
9. **Power-aware deferral** — on battery <30 %, eve auto-defers `at`-scheduled rebuilds + dims non-focused monitors + suspends idle docker containers.
10. **Predictive UI surfacing** — eve notices operator hovers over "Sinister Generator" tab 3× without clicking → surfaces "looking for recent outputs? here's last 5" inline.

## 4. MVP pipeline scaffold

```
projects/sinister-os/source/hot-reconfig/
├── watcher/sinister-config-watcher.py       # inotify daemon
├── classifier/classify-change.py            # diff → verdict
├── emitter/emit-reboot-banner.sh            # writes JSON
├── systemd/sinister-config-watcher.service  # unit file
├── systemd/sinister-reboot-tracker.service  # tracker unit
└── README.md
```

**watcher** (`sinister-config-watcher.py`, ~40 LOC):
```python
# inotifywait -m -e modify,create /etc/sinister/ → on event:
#   diff = git diff --no-index /var/cache/sinister/last/$f /etc/sinister/$f
#   verdict = subprocess(classify-change.py, diff, filename)
#   if verdict.hot: signal_hup(verdict.target_unit)
#   else: emit-reboot-banner.sh add $f "$verdict.reason"
#   cp /etc/sinister/$f /var/cache/sinister/last/$f
```

**classifier** (`classify-change.py`, ~60 LOC) — TOML key allowlist per file:
```python
# THEME_HOT_KEYS = {"accent","radius","font","density"}   -> signal panel
# EVE_HOT_KEYS   = {"voice.wake_word","allowlist","model"}-> SIGHUP eve
# EVE_COLD_KEYS  = {"socket_path","run_as_user"}          -> reboot
# unknown key -> conservative: reboot-required
# emit JSON: {hot: bool, target_unit: str, reason: str, severity: str}
```

**emitter** (`emit-reboot-banner.sh`, ~25 LOC) — jq-based atomic update:
```bash
# STATE=/var/lib/sinister/reboot-required.json
# flock $STATE.lock jq --arg t "$1" --arg r "$2" --arg now "$(date -uIs)" \
#   '.required=true | .reasons += [{trigger:$t, reason:$r, since_utc:$now}]' \
#   $STATE > $STATE.tmp && mv $STATE.tmp $STATE
# systemd-notify --status="reboot pending: $2"
```

**Panel hook:** add `/api/system/reboot-required` SSE route in panel routes; tail the JSON via `fs.watch`.

## Composes-with

- `projects/sinister-os/docs/architecture.md` (existing layered view)
- `projects/sinister-os/docs/live-dev-workflow.md` (review before scaffolding to avoid forking design)
- `projects/sinister-os/source/eve-control/` (eve daemon owner — SIGHUP target)
- `projects/sinister-os/source/eve-os-integration/DESIGN.md` (theme-token propagation)
- `projects/sinister-os/docs/panel-as-os-shell.md` (banner surface placement)
- `_shared-memory/plans/sinister-os-massive-expansion-2026-05-24T2110Z/plan.md` (ITER 10)
