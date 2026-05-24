# source/hot-reconfig/ — Live config reload + reboot-banner pipeline

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Status:** SCAFFOLDED (3 scripts + 2 systemd units, all syntax-verified).
> **Trigger:** Operator hard-canonical 2026-05-24 *"I want to be able to actively change things like ui look add things etc without a reboot. if reboot required then have banner for it."*
> **Composes-with:** `research/hot-reconfig-architecture-2026-05-24.md` (design doctrine).

## What this directory does

A three-component pipeline that watches `/etc/sinister/*.toml`, classifies each change as HOT vs REBOOT-required, and either signals the affected daemon (hot) or emits a reboot-required banner (cold).

```
inotify event on /etc/sinister/*.toml
    └─→ watcher/sinister-config-watcher.py
            └─→ classifier/classify-change.py
                    ├─→ HOT  → systemd SIGHUP / try-restart
                    └─→ COLD → emitter/emit-reboot-banner.sh
                                    └─→ /var/lib/sinister/reboot-required.json
                                            └─→ Panel SSE → banner UI
```

## Files

| Path | Status | Purpose |
|---|---|---|
| `watcher/sinister-config-watcher.py` | SCAFFOLDED | inotify daemon, ~40 LOC |
| `classifier/classify-change.py` | SCAFFOLDED | diff → verdict, ~60 LOC |
| `emitter/emit-reboot-banner.sh` | SCAFFOLDED | atomic JSON update, ~25 LOC |
| `systemd/sinister-config-watcher.service` | SCAFFOLDED | unit file for the watcher |
| `systemd/sinister-reboot-tracker.service` | SCAFFOLDED | unit file for tracker (kernel/lib watch) |

## Bring-up (eventually, on bare-metal install)

```bash
sudo install -m 0755 watcher/sinister-config-watcher.py /usr/local/bin/
sudo install -m 0755 classifier/classify-change.py /usr/local/bin/
sudo install -m 0755 emitter/emit-reboot-banner.sh /usr/local/bin/
sudo install -m 0644 systemd/*.service /etc/systemd/system/
sudo mkdir -p /etc/sinister /var/cache/sinister/last /var/lib/sinister
sudo install -m 0644 init/reboot-required-empty.json /var/lib/sinister/reboot-required.json
sudo systemctl daemon-reload
sudo systemctl enable --now sinister-config-watcher.service sinister-reboot-tracker.service
```

## Honest scope ledger

What this scaffold DOES today:

- Defines the file layout + the three-component pipeline.
- Provides parse-clean Python + bash scripts (~125 LOC total) that EVE can extend.
- Provides systemd unit files ready to drop into `/etc/systemd/system/`.

What this scaffold does NOT do:

- Install itself anywhere. Operator-gated to P3+.
- Run against a real `/etc/sinister/` (that directory doesn't exist on the dev workstation).
- Drive the Panel SSE endpoint — that's a panel-side scaffold (TBD).
- Cover kernel-version delta / library-replacement detection — `sinister-reboot-tracker.service` is a stub; needrestart integration is future work.

## See also

- `research/hot-reconfig-architecture-2026-05-24.md` — full design (layer matrix + banner schema + 10 rich possibilities).
- `docs/architecture.md` — overall layered system view this composes with.
