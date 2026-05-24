# eve — docker-stack manager CLI

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Script:** `source/docker-stack/eve` (executable bash, no extension)
> **Version:** 0.1.0
> **Scope:** The docker-stack manager variant. The system-level `eve` daemon (root-equivalent shell control, voice surface, `sinister-eve.service`) is operator-gated for P3 and lives at `source/eve-control/` — this CLI does not overlap with it.

## Synopsis

```bash
eve <command> [args] [flags]
```

Drop-in shell wrapper around the `docker compose` invocations the operator runs daily on the Sinister Mesh stack. One verb per intent so the long compose flags never have to be retyped.

Motivating operator directive (verbatim, 2026-05-24):

> "i can forever expand and update the OS without having to reinstall etc. and have quality of life options ... soft reboot or clearing caches without full restart or fucking with my agents all things like this"

## Sub-commands

| Command | One-liner |
|---|---|
| `eve up [--no-harden]` | Bring the stack up. Hardened overlay (`compose.hardened.yml`) applied by default; `--no-harden` skips it. |
| `eve down [--wipe]` | Bring the stack down. `--wipe` deletes named volumes and prompts the operator to type `WIPE` to confirm. |
| `eve restart [service]` | Restart one or all services. Volumes untouched. |
| `eve status` | `docker compose ps` plus a run of `smoke-test.sh`. |
| `eve smoke` | Run `smoke-test.sh` (HTTP probe of all 10 services). |
| `eve logs [service]` | `tail -f` one service's logs; no arg = follow all. |
| `eve clean` | Soft cache clear: `docker system prune -f` (no volumes) + restart `panel` + restart `rocketchat-mongo-init`. Agents are not touched. |
| `eve theme list` | Show available overlays (`compose.*.yml`) and mark which is active. |
| `eve theme apply <name>` | Symlink `docker-compose.override.yml` -> `compose.<name>.yml` (Compose auto-loads `override.yml` on every `up`). |
| `eve doctor` | Health-check report: daemon up? compose files present? images pulled? volumes exist? ports free? |
| `eve --help` / `eve -h` | Print help. |
| `eve --version` | Print `eve 0.1.0`. |

## Examples — common operator flows

### Bring up the hardened stack from scratch

```bash
cd projects/sinister-os/source/docker-stack
./eve up
./eve status            # verify ps + smoke
```

### Soft-reboot the panel after editing a config file

The "no fucking with my agents" path. Reload the panel without bouncing rocketchat / ollama / gitea (where the agents are talking through).

```bash
./eve restart panel
./eve smoke             # confirm panel still answers HTTP 200
```

### Soft cache clear before bed

```bash
./eve clean             # prune unused images/networks/build cache; restart panel + mongo-init
./eve status            # verify the 10/10 still green
```

### Smoke-check before bed (no changes)

```bash
./eve smoke
```

### Make hardening the default (sticky override)

```bash
./eve theme list                # see what's available
./eve theme apply hardened      # creates docker-compose.override.yml -> compose.hardened.yml
./eve up                        # picks up the override automatically; --no-harden no longer needed
```

### Down + wipe (full reset)

```bash
./eve down --wipe       # prompts: type WIPE to confirm; deletes named volumes
./eve up                # cold start
```

### Health-check the host before bringing the stack up

```bash
./eve doctor            # daemon, compose files, images, volumes, ports
```

## Run from anywhere

The script auto-cd's into its own directory before any `docker compose` call, so you can drop it on your PATH (or symlink it into `~/bin/`) and run `eve status` from any working directory:

```bash
ln -s "$(pwd)/eve" ~/bin/eve   # one-time
eve status                     # now works from anywhere
```

## What's NOT implemented (intentionally)

| Skipped | Why |
|---|---|
| `eve up` does NOT auto-apply `compose.paranoid.yml` | Per `HARDENING.md` § "What this overlay does NOT do", paranoid hardening (custom AppArmor, userns remap, per-service nets, egress firewall) trades speed for paranoia. Layered later as a separate overlay; today's default is the baseline hardened overlay only. |
| No automatic `docker-compose.override.yml` symlink on install | The README / HARDENING.md § "What the operator can do RIGHT NOW" leave the override-as-default decision to the operator. `eve theme apply hardened` is the explicit operator-driven path; the script does not flip it for you. |
| No `eve update` / `eve pull` | Image pulls are explicit operator decisions. Add later if the operator wants a one-shot "bump everything" verb. |
| `eve clean` does NOT prune volumes or networks-in-use | Operator directive: caches only, agents untouched. Use `eve down --wipe` for the destructive path. |
| `eve doctor` does NOT auto-fix | Doctor reports; the operator decides. Auto-fix belongs in a separate `eve repair` verb that we have not specced yet. |
| No `eve exec` shell-into-container helper | `docker compose exec <service> sh` is one line; not enough friction to wrap. Revisit if the operator asks. |
| `source/eve-control/` integration | That's the P3 system-level daemon (root-equivalent shell control + voice). Operator-gated; this CLI is a thin shell wrapper, not the EVE persona. |

## Verification (no daemon required)

```bash
# Parse cleanliness
bash -n eve              # exit 0

# Self-tests
bash eve --help          # prints help, exit 0
bash eve --version       # prints "eve 0.1.0", exit 0

# Shellcheck (if installed)
shellcheck eve           # treat ERROR as must-fix; WARNING as document-and-defer
```

## Composes with

- `docker-compose.yml` — base service definitions.
- `compose.hardened.yml` — the always-on hardening overlay (see `HARDENING.md`).
- `smoke-test.sh` — HTTP probe; `eve status` and `eve smoke` both invoke it.
- `HARDENING.md` — the doctrine row "make hardening the default" — `eve up` operationalises that doctrine by applying the overlay by default; `eve theme apply hardened` operationalises the next step (sticky override symlink).
- Future `compose.paranoid.yml` / `compose.network-segmented.yml` — once they land, `eve theme list` discovers them automatically (the listing globs `compose.*.yml`).
