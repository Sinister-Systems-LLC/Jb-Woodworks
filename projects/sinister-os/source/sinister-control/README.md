# sinister-control — hot-reconfig + reboot-banner pipeline

> Author: RKOJ-ELENO :: 2026-05-25
> Lane: sinister-os
> Composes with: `source/docker-stack/compose.{desktop,headless}.yml`, panel banner widget, vault-api KV.

Three small artifacts that satisfy the operator directive *"actively change things like UI look add things etc without a reboot. if reboot required then have banner for it"* (massive-expansion plan iter 10, 2026-05-24T21:10Z).

## Pieces

| File | Role | Where it runs |
|---|---|---|
| `reboot-required.sh` | Write-side: emit `/var/lib/sinister/reboot-required.json` | called by anything that knows it touched a reboot-required surface (kernel apt-hook, sysctl-immutable change, bootloader config) |
| `reboot-banner-watch.sh` | Read-side: inotify watch → vault KV publish → panel banner | `sinister-banner-watch.service` (systemd unit, Restart=always) |
| `hot-reconfig-classifier.py` | Diff classifier: `hot` / `service` / `reboot` verdict over TOML config diffs | called by `eve apply config <file>` before deciding reload strategy |

## End-to-end flow

```
  operator edits /etc/sinister/panel.toml
            │
            ▼
  eve apply config /etc/sinister/panel.toml
            │
            ▼
  hot-reconfig-classifier.py --pre <snap> --post <live>
            │
       ┌────┴────┬────────────┐
       ▼         ▼            ▼
     hot      service       reboot
       │         │            │
       │         ▼            ▼
       │   systemctl    reboot-required.sh "<reason>"
       │   restart           │
       │   <unit>            ▼
       │                /var/lib/sinister/reboot-required.json
       │                     │
       │                     ▼
       │           inotify -> reboot-banner-watch.sh
       │                     │
       │                     ▼
       │            curl PUT vault-api KV mesh/banner/reboot-required
       │                     │
       │                     ▼
       │            panel Banner.tsx polls KV every 5s
       │                     │
       ▼                     ▼
   live reload         red banner "kernel.upgrade — reboot recommended"
```

## Classifier rules (terse)

- `kernel.cmdline`, `boot.{bootloader,initramfs,secureboot}`, `fs.root.*`, `sysctl.immutable`, `selinux.policy`, `apparmor.profile.builtin`, `audit.kernel`, `ima.policy`, `net.bridge.module` → **reboot**
- prefixes `service.` / `daemon.` / `agent.` / `mesh.` / `vault.` / `panel.` / `eve.` → **service** (systemctl restart)
- explicit hot-override keys (`panel.accent`, `panel.theme`, `panel.layout.density`, `panel.layout.sidebar`, `eve.accent`, `mesh.banner.message`) → **hot** even though they match a service prefix. These are the operator's "actively change UI look without reboot" surface.
- anything else → **hot** (signal SIGHUP / re-read on next request)

Edit `REBOOT_KEYS` / `SERVICE_PREFIXES` / `HOT_OVERRIDE` in `hot-reconfig-classifier.py` to extend.

## Smoke test (per no-bullshit doctrine — every claim of "works" carries a receipt)

```bash
# parse-clean gate (this iter's claim level)
bash -n source/sinister-control/reboot-required.sh
bash -n source/sinister-control/reboot-banner-watch.sh
python -m py_compile source/sinister-control/hot-reconfig-classifier.py

# sample diff classification (use $TMPDIR for portability — git-bash and Python
# disagree on what "/tmp" resolves to on Windows hosts).
WORK="$(mktemp -d)"
mkdir -p "$WORK/pre" "$WORK/post"
printf '[panel]\naccent="purple"\n' > "$WORK/pre/cfg.toml"
printf '[panel]\naccent="crimson"\n' > "$WORK/post/cfg.toml"
python source/sinister-control/hot-reconfig-classifier.py \
  --pre-dir "$WORK/pre" --post-dir "$WORK/post"
# expected: verdict=hot
rm -rf "$WORK"
```

## Acceptance criteria (iter 10 plan)

- [x] `bash -n` clean on both shell scripts (verified this turn)
- [x] `python -m py_compile` clean on classifier (verified this turn)
- [x] sample diff returns expected verdict — 3/3 cases (hot / service / reboot) verified this turn after HOT_OVERRIDE fix
- [ ] vault-api PUT smoke against running vault (deferred to iter where vault-api is live in dev compose; out of scope this iter — no production claim)

## Out of scope (this iter)

- systemd unit file for `sinister-banner-watch.service` (sandboxed under iter 12 rollout doctrine)
- Panel Banner.tsx component (sinister-panel lane, not sinister-os)
- inotify-tools install gate (handled by P0a docker rollout phase)
