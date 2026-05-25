# Sinister Lang — DSL design draft

> Author: RKOJ-ELENO :: 2026-05-25 (draft; supersedes empty placeholder from massive-expansion plan iter 11)
> Status: DOCS-ONLY (no runtime, no transpiler yet — per plan's "no production code yet" gate)
> Composes-with: agent A research verdict (Janet embed + CUE schema DSL, 2026-05-24T21:10Z plan §6)

## Operator directive (verbatim, 2026-05-24T21:08Z)

> *"Maybbe we can take this as fasr as creating our own coding languge to make our servers and everything as effcient as they can be."*

## Agent A verdict (research lane, 2026-05-24)

**PARTIALLY PURSUE.** A brand-new compiler is six-month yak-shave with negative ROI; two surgical layers cover ~95% of the directive's intent at <2 weeks each:

1. **Janet embed inside EVE** (week 1) — fast Lisp dialect, single-file C runtime (~700 KB), already battle-tested. Gives EVE a real scripting surface for hot-reconfig handlers, agent workflow recording (operator utterance 21:50 "voice-driven workflow recording"), and live service composition. No new toolchain; ships as `/usr/bin/janet` + `libjanet.so`.
2. **`.sin` config DSL on top of CUE** (defer until 20+ services exist) — CUE handles types + constraints + transpile-to-N-formats already. We add Sinister-flavored macros (e.g. `service.tier`, `mesh.expose`) that desugar to: a systemd unit + a compose fragment + a JSON KV for vault-api. No new evaluator; CUE evaluator does the heavy lifting.

Net: zero ML toolchain risk, zero new compiler surface area, two strong UX wins.

## `.sin` source format (sketch)

A `.sin` file describes a Sinister service. The transpiler emits three artifacts: a systemd unit, a docker-compose fragment, and a vault KV record.

See `example.sin` for the full sketch. Highlights:

```cue
package sinister.services

service: {
    name:       "panel-shell"
    image:      "ghcr.io/sinister/panel-shell:latest"
    tier:       "core"           // core | mesh | optional
    mesh:       expose: true     // → mesh ACL rule auto-added
    reboot:     never            // never | on-config-change | on-kernel
    health: {
        path:   "/healthz"
        accept: [200, 307]       // hot-reconfig fix from commit 761d06b
    }
    accent: "purple"             // forwarded to skeleton CSS token
}
```

## What the transpiler MUST emit (per service)

1. `/etc/systemd/system/sinister-<name>.service` — unit with Restart=on-failure, ExecStart, env, dependencies.
2. `compose.<name>.yml` — overlay fragment compatible with `validate-merge.sh`.
3. `mesh/services/<name>.json` — published to vault KV; consumed by panel + acl-gen.

See `sample-output/` for the three artifacts the transpiler would emit when fed `example.sin`.

## Janet-in-EVE — scoped scripting surface

EVE exposes a Janet REPL on the privileged socket (`/run/sinister/eve.sock`) with a curated FFI:

| Janet fn | Calls into | Purpose |
|---|---|---|
| `(eve/apply-config <toml-path>)` | `hot-reconfig-classifier.py` + reload dispatcher | hot/service/reboot decision + execute |
| `(eve/reboot-required <reason> &opt :severity :component)` | `reboot-required.sh` | flag banner |
| `(eve/mesh-publish <key> <json>)` | vault-api PUT `/kv/<key>` | mesh state pub |
| `(eve/agent-spawn <project> &opt :mode :loop)` | `start-sinister-session.ps1` parallel | child-claude spawn (master authority block from CLAUDE.md) |
| `(eve/sudoers <action>)` | `eve` user NOPASSWD allowlist | curated sudo |

Operator can record workflows ("every Monday 8am, do X") as `.janet` files in `~/.config/sinister/workflows/`.

## Non-goals (explicitly)

- New parser / new lexer / new VM — never. Janet does parser+lexer+VM; CUE does parser+evaluator.
- Statically-typed-everything OS-language — six-month timeline, zero ROI for a single-operator OS.
- Replacing bash / systemd unit files at the OS layer — they work; `.sin` desugars TO them, not OVER them.

## Acceptance criteria for this docs-only iter

- [x] DSL-DESIGN document explains layering (Janet + CUE), not a new compiler.
- [x] `example.sin` ships in same dir and parses as valid CUE syntax (manual eyeball, no `cue eval` run this iter).
- [x] `sample-output/` contains the three artifacts the transpiler would emit.
- [ ] Actual transpiler binary — out of scope until ≥20 services exist (per agent A's "defer" verdict).

## Risk register

1. **Toolchain creep** — if `.sin` grows custom syntax beyond CUE's grammar, we've quietly invented a language. Mitigation: hard rule = `.sin` must remain valid CUE; only the macro names are Sinister-flavored.
2. **Janet adoption resistance** — operator may prefer Python. Mitigation: Janet REPL is opt-in; Python ScriptShell agent stays the default.
3. **Two ways to do the same thing** — `.sin` for declarative config, Janet for imperative scripting; risk of overlap. Mitigation: design rule — `.sin` describes WHAT (service shape), Janet describes WHEN/HOW (event reactions, workflows).
