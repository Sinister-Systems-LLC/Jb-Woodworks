# PROXY-DESIGN.md — Per-app proxy routing (Layer 3 of geo-mesh anonymity)

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Status:** SCAFFOLDED (config-only). Honest verbs only — see § Honesty ledger.
> **Companions:** [`../../docs/geo-mesh-routing.md`](../../docs/geo-mesh-routing.md) (3-layer model), [`MESH-DEPLOY.md`](MESH-DEPLOY.md) (Layer 1 Tailscale), [`HARDENING.md`](HARDENING.md) (per-server hardening).

## 1. What the CLI does TODAY

`eve proxy` is a JSON-file manager. Nothing more. It reads/writes `config/proxy/routes.json` with this schema:

```json
{
  "version": 1,
  "default": "direct",
  "routes": {
    "firefox": "ny",
    "discord": "direct",
    "telegram": "fl"
  }
}
```

Subcommands:

| Verb | Behavior |
|---|---|
| `list` | Pretty-print default + per-app rows. |
| `set <app> <route>` | Upsert a row. Validates `route` ∈ `{direct, ny, fl, tor}`. `tor` accepted but warns "not implemented". |
| `show <app>` | Print the row's route, falling back to `default`. |
| `verify` | JSON parse + per-row valid-route check. Exit 0 on clean. |
| `help` | Usage. |

**That's it.** The CLI does NOT touch nftables, iptables, network namespaces, cgroups, routing tables, tailscale interface state, or any process's actual egress path. **No traffic re-routes when you run `eve proxy set firefox ny`.** The row exists in JSON. The enforcement layer is deferred.

## 2. What it WILL do (deferred work)

The enforcement layer has two distinct deployment targets — they diverge significantly.

### 2a. Native Sinister-OS path (root + nftables + netns)

When EVE runs as the system shell on the operator's Sinister-OS install (Phase 3 of the master plan), `eve proxy` can drive real per-app routing because it has:

- root (via `sinister-eve.service` + `/etc/sudoers.d/eve` NOPASSWD allowlist)
- nftables (`--mark` rules per route)
- network namespaces (`ip netns add sinister-ny`, `sinister-fl`)
- veth pairs bridging each netns to the corresponding tailscale exit-node selection
- `sinister-app-launcher` wrapper that wraps app exec in the right netns

Flow per app launch:
1. Operator (or wake-word) says "open Firefox routed via NY".
2. EVE looks up `routes.json` → `firefox -> ny`.
3. EVE invokes `ip netns exec sinister-ny firefox` (the netns has its default route through the `tailscale-ny` interface, which is itself an exit-node bind to `sinister-mesh-ny`).
4. Firefox's traffic egresses NY; the rest of the desktop is unaffected.

### 2b. Docker-stack path (containerized, no host root)

When the docker-stack EVE issues proxy commands inside the bridge net (the variant THIS `eve` script targets), it CAN'T touch host nftables. The realistic enforcement options shrink to:

| Strategy | How | Limitations |
|---|---|---|
| Per-service `network_mode` override in compose | Add a tailscale-routed network and set `network_mode: "service:tailscale-ny"` on the panel / yjs / browser-service containers | Coarse — entire container, not per-app inside the container; requires compose redeploy |
| SOCKS5 proxy inside the tailnet | Run a `tinyproxy` / `dante` on `sinister-mesh-ny` and `sinister-mesh-fl`; apps that respect `HTTP_PROXY` / `HTTPS_PROXY` route through them | App must honor proxy env vars; doesn't catch raw TCP / UDP |
| Browser-side container per route | One firefox container with `network_mode: ny`, another with `network_mode: fl`; operator picks via panel UI | RAM cost; multi-profile state |

The docker-stack variant of Layer 3 will most likely settle on **strategy 3 for browsers** (since those are the operator's primary "I want this exit to look like NY" surface) and **strategy 2 for CLI tools** (`curl`, `git`, etc. that already honor proxy env vars).

## 3. Per-app routing strategies — comparison

| Strategy | Granularity | Linux-host requirement | Container-friendly | Catches all protocols | Implementation cost |
|---|---|---|---|---|---|
| nftables `--mark` + `ip rule` | per-cgroup (per-app) | root + nft | no | yes | high |
| Network namespace wrap (`ip netns exec`) | per-process | root + iproute2 | partial (CAP_NET_ADMIN) | yes | medium |
| SOCKS5 / HTTP proxy env vars | per-app (if app respects env) | none | yes | no (TCP-only, app-cooperative) | low |
| Per-container `network_mode` | per-container | none beyond docker | yes | yes (within container) | low |
| LD_PRELOAD shim (`tsocks`, `proxychains`) | per-process | none | yes | most TCP | low-medium |

`eve proxy` is **routing-strategy-agnostic** by design — it stores intent. The enforcement plug-in selected at runtime depends on which EVE variant is calling and what's available on the host.

## 4. Honesty ledger

| Claim | Status |
|---|---|
| `routes.json` is a parseable JSON file with a documented schema | TRUE |
| `eve proxy {list,set,show,verify,help}` works against `routes.json` | TRUE (scaffolded 2026-05-24, `eve proxy verify` exit 0) |
| Setting `eve proxy set firefox ny` causes Firefox traffic to egress NY | **FALSE** — config only; no enforcement layer exists yet |
| Tor route is wired up | **FALSE** — accepted into config with a stderr warning; no Tor proxy is running |
| The CLI works on Windows | partial — JSON management works in git-bash; the routes are still meaningless until the Linux-host enforcement layer ships, and that layer is Linux-only |
| Layer 3 of the geo-mesh anonymity model is "done" | **FALSE** — Layer 3 status is SCAFFOLDED (config schema + CLI), enforcement is the next milestone |

## 5. Acceptance criteria for SHIPPED (moving past SCAFFOLDED)

1. At least one enforcement strategy from § 3 wired up in either the native or docker-stack variant.
2. `iperf3` or `curl ifconfig.me` from the operator's laptop shows traffic egressing the chosen exit node when the route is `ny` or `fl`.
3. The native path: `ip netns list` shows `sinister-ny` and `sinister-fl` netns; `nft list ruleset` shows the mark rules.
4. The docker-stack path: at least one container running with `network_mode: "service:tailscale-ny"` and `docker exec ... curl ifconfig.me` confirming NY egress.
5. PROGRESS log row + commit on this lane referencing the receipt.

Until those land, every claim in geo-mesh-routing.md about Layer 3 stays at SCAFFOLDED.
