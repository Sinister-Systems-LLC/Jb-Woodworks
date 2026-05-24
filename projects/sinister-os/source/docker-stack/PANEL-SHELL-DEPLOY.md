# PANEL-SHELL-DEPLOY.md — Sinister Panel as OS shell (docker-test path)

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Status:** SCAFFOLDED — compose overlay + runbook ready. Live container start needs Docker daemon + a `sinister-panel/source/package.json` that exists at the expected junction.
> **Acks operator utterance:** `2026-05-24T12:47:52Z` (slug `test-os`, tags: `sinister-os`, `priority`, `ship-now`, `panel-as-shell`, `docker-test`).
> **Companion:** `compose.panel-shell.yml`
> **UI base canonical:** `_shared-memory/knowledge/sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24.md` (inherit `dashboard-skeleton`, never fork).

## What the operator asked for (verbatim, 12:47Z)

> *"get this working how i want so we have a perfect operating system to run claude on and be my own open source operating system that i can forever expand that i have complete control of and ai is complete integrated. review github and see what all you can compile from other repos. and complete the entire thing and lets get to testing in docker to all this for me and make everything look like my sinister panel here. grab the exact code from the sinister panel project folder and lets use that and the lets text look as the main OS look. call everything SINISTER and have all our systems direct in the operating system. make sure i have full options i use from my pc like playing steam games and such."*

## What this scaffold does (honest scope)

1. Wraps the **existing** `projects/sinister-panel/` codebase in a docker container — no rewrite, no fork. Panel edits in `projects/sinister-panel/source/` hot-reload via Vite.
2. Exposes the panel on `http://localhost:8088` so the operator can immediately see the look-and-feel that will become the OS shell once we boot into it.
3. Joins the `sinister-mesh` network so the panel can talk to `yjs-server`, `vault-api`, and other Sinister stack services by container name.

## What this scaffold does NOT do (operator-gated next steps)

| # | Item | Gating |
|---|---|---|
| 1 | Boot a real OS where the panel IS the shell. | P3 in `master-plan-2026-05-24.md` — requires Hyprland kiosk-mode + custom `~/.xinitrc`-equivalent that launches a Chromium kiosk pointing at the panel container. |
| 2 | Fold in the Let's Text visual look. | Requires reading the Let's Text styling out of the operator's reference + tokenizing into `dashboard-skeleton` per UI-canonical doctrine. Plan row added below. |
| 3 | Steam / Lutris / gaming integration. | P4 in `master-plan-2026-05-24.md`. Anti-cheat compat table is the long pole. |
| 4 | "Review github and see what all you can compile from other repos." | Step 9 of CLAUDE.md cold-start (github-first sourcing). Plan row added below; will run `automations/github-prior-art.ps1` next iter and surface candidates. |
| 5 | Bake the panel into the airootfs image. | After step 1 above proves operator-acceptable; turns the docker-test artifact into a real installable image. |

## Bringing it up (when docker daemon is reachable)

### Prereqs

```bash
# 1. sinister-panel codebase exists at the expected path
ls -la projects/sinister-panel/source/package.json
# (if missing — clone or restore the project first; the volume mount is path-strict)

# 2. docker daemon up
docker info >/dev/null && echo "daemon up" || echo "daemon down — start Docker Desktop first"
```

### First-time up

```bash
cd projects/sinister-os/source/docker-stack
docker compose -f docker-compose.yml \
                -f compose.hardened.yml \
                -f compose.panel-shell.yml \
                --profile panel-shell \
                up -d sinister-panel-shell

# Wait for the first npm install to complete (~2-5 min depending on cache state):
docker logs -f sinister-panel-shell
```

### Smoke test

```bash
curl -fsS http://localhost:8088/ >/dev/null && echo "panel UP" || echo "panel DOWN"

# Open in operator browser:
# http://localhost:8088
```

### Live-edit cycle

Edit any file in `projects/sinister-panel/source/`. Vite hot-reloads in the container. No rebuild needed.

### Bring it down

```bash
docker compose -f docker-compose.yml \
                -f compose.hardened.yml \
                -f compose.panel-shell.yml \
                --profile panel-shell \
                down
```

## Composition rules (UI canonical 2026-05-24)

Per `_shared-memory/knowledge/sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24.md`:

1. Inherit from `projects/sinister-dashboard-skeleton/dashboard-skeleton/` — its `.lg-*` Liquid Glass classes + `sinister-theme-tokens.css` are the canonical token set.
2. Per-surface accent token is the ONLY allowed divergence. This overlay sets `VITE_ACCENT=#c084fc` (Sinister purple).
3. **EXPAND, never fork.** If the panel needs a primitive `dashboard-skeleton` lacks, add it to the skeleton FIRST, then consume.
4. **Never roll a one-off Button/Card/Input/Chart/StatCard** in this panel-shell when the skeleton lacks one.

## Honesty ledger

What's **shipped (verified by YAML parse)** this turn:

- `compose.panel-shell.yml` — `python yaml.safe_load` exit 0.
- This runbook (`PANEL-SHELL-DEPLOY.md`).
- Counter-arg log row at `_shared-memory/counter-arguments.jsonl` documenting the pivot.
- Operator utterance 2026-05-24T12:47:52Z acknowledged via `ack-operator-utterance.ps1`.

What's **NOT shipped** this turn:

- Live container running. Docker daemon was down at session-start; `docker compose up` deferred.
- Confirmation that `projects/sinister-panel/source/package.json` exists at expected path (sister lane may have moved it).
- Let's Text styling integration.
- GitHub-prior-art sweep on "open-source OS shells based on web apps" (queued for next iter).

## See also

- `master-plan-2026-05-24.md` — full Sinister OS phase plan; this scaffold accelerates the P3 "EVE shell" phase out-of-order.
- `compose.hardened.yml` — security baseline this overlay composes with.
- `validate-merge.sh` — run BEFORE bringing this overlay up alongside others.
- `_shared-memory/knowledge/sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24.md` — UI inheritance binding doctrine.
