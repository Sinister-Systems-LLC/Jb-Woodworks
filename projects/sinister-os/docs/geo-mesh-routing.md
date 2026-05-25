> **Author:** RKOJ-ELENO :: 2026-05-24

# Geo mesh routing — Thailand to NY / FL

> **Operator directive (verbatim 2026-05-24):** *"take note these servers need to link over internet as well and be completely safe with like a VPN setup or something like that for complete anonymity. in all aspects. i need to be able to be in thailand and download my exe file or have the os on the PC and i can connect to my servers i setup in new york and servers i setup in florida with no speed issues or anything like that. all routing needs to pristine and efficient"*
>
> **Companion docs:** [ghost-server-hardening.md](ghost-server-hardening.md) (per-server hardening that complements the network layer), [qol-features.md](qol-features.md) (the operator-facing QoL surface this enables remotely), [live-dev-workflow.md](live-dev-workflow.md) (the HMR flow that must survive 250 ms RTT).
>
> **Status banner.** No working mesh exists today. This entire doc is **PROPOSED** with **SCAFFOLDED** notes where a partial implementation choice has been narrowed. Honest: nothing here has been deployed or speed-tested across continents.

## Topology

```
+--------------------+         +---------------------+
| Operator laptop    |         | Sinister NY node    |
| (Thailand)         |   <-->  | (home server, NYC)  |
| Sinister OS        |    T    | Docker stack live   |
+--------------------+    a    +---------------------+
                          i
+--------------------+    l    +---------------------+
| Leo's machine      |   <-->  | Sinister FL node    |
| (location TBD)     |    s    | (home server, FL)   |
| Sinister OS        |    c    | Docker stack live   |
+--------------------+    a    +---------------------+
                          l
+--------------------+    e    +---------------------+
| Mobile (Android)   |   <-->  | sinister-kernel-apk |
| sinister-kernel    |   mesh  | UI on phone         |
+--------------------+         +---------------------+
```

Every node is a Tailscale peer. The two home servers (NY, FL) double as **exit nodes** — the laptop in Thailand can route specific traffic through NY or FL to appear US-resident.

## Option A — Tailscale (recommended for V1)

| Property | Value |
|---|---|
| Tier | Free (up to 100 nodes; the fleet is < 20) |
| NAT traversal | Automatic (uses DERP relay fallback if direct UDP fails) |
| Key rotation | Automatic via Tailscale auth keys + reusable / ephemeral keys |
| ACLs | JSON policy file editable in the Tailscale admin console; can scope `tag:operator` ↔ `tag:server` |
| Exit nodes | Native feature; toggle on a node via `tailscale up --advertise-exit-node` |
| Multi-account | Tailscale supports multiple accounts on one node via `--login-server` (Headscale for self-host) |

**Why V1.** Zero NAT-traversal work, ACLs are trivial, exit nodes are a one-flag opt-in. The free tier is sufficient for the fleet's current size.

**Trade-off.** Control-plane (the coordination server that hands out keys) is Tailscale-hosted by default. The data plane is peer-to-peer (and end-to-end encrypted via WireGuard under the hood), so Tailscale Inc. cannot read traffic — but they DO know which nodes exist. Mitigation: self-host the control plane via Headscale once the fleet stabilises (M5+).

## Option B — Self-hosted WireGuard (alternative)

| Property | Value |
|---|---|
| Tier | Free, fully self-hosted |
| NAT traversal | **Manual** — requires either a static public IP per peer, port forwarding, or a relay server the operator runs |
| Key rotation | **Manual** — operator regenerates keys + re-distributes peer configs |
| ACLs | Per-interface firewall rules (nftables / `wg set` allowed-ips); no central UI |
| Exit nodes | Possible via `AllowedIPs = 0.0.0.0/0` + masquerade on the exit peer's iptables |
| Multi-account | One config per account; no multi-tenancy primitive |

**Pros.** Full control. Zero third-party (not even Tailscale Inc.). No telemetry. Cheaper at scale (no free-tier cap).

**Cons.** NAT-traversal from a coffee-shop wifi in Thailand → home server behind a residential ISP NAT requires either UPnP/PCP (unreliable) or a public relay. Key rotation across 7+ nodes is a sysadmin chore.

**When we'd switch.** Once the fleet doctrine + operator's "complete anonymity" goal outranks the convenience benefit of Tailscale's coordination server. Estimate: M6 or later.

## Speed expectations (honest)

The operator's directive is "with no speed issues or anything like that. all routing needs to pristine and efficient." This is partially achievable. Be honest about which parts are physics and which parts are tunable.

### Physics (cannot be tuned away)

| Hop | Approx baseline RTT |
|---|---|
| Bangkok → NY (great-circle ~14,000 km) | **~240–280 ms** |
| Bangkok → Miami (~16,000 km) | **~260–300 ms** |
| Bangkok → Singapore (regional) | ~30–60 ms |
| Bangkok → Tokyo | ~80–120 ms |

These are the floor. No VPN, no protocol, no acceleration will get below the speed-of-light-in-fiber budget for a 14,000 km trip.

### VPN overhead

WireGuard (Tailscale's data plane is WireGuard) adds **< 5 ms** per hop on modern hardware. The encryption is so cheap it doesn't measurably hurt throughput on a residential gigabit link.

### Throughput (operator's actual concern, probably)

This is **dominated by local ISP plan, not by the VPN.**

| Scenario | Expected throughput |
|---|---|
| Thailand coffee-shop wifi (typical 20–100 Mbps down) | 20–100 Mbps; VPN passthrough is line-rate |
| Thailand fiber-to-home (300–1000 Mbps) | 300–1000 Mbps; WireGuard maxes around 700 Mbps on a mid-range CPU even at 1 Gbps line |
| Operator's home server uplink (US residential cable) | typically 35–500 Mbps upload depending on plan; this is the bottleneck for downloading the EXE / OS image from Thailand |

**Concrete operator scenario** ("be in Thailand and download my exe file"):
- Bangkok → NY home server: **240–280 ms RTT**, **throughput = MIN(Thailand-down, NY-up, WireGuard-cpu-cap)**
- A 500 MB OS image on a 100 Mbps Thailand connection + 100 Mbps NY upload: ~40–50 seconds wall-clock
- If NY upload is only 25 Mbps (typical US cable): ~160 seconds wall-clock — VPN is not the bottleneck

**Concrete operator scenario** ("connect to my servers ... with no speed issues"):
- Interactive SSH / Guacamole desktop: 240 ms RTT shows up as noticeable latency on keystroke echo. Mitigation: use `mosh` instead of SSH (predictive local echo) or Guacamole's built-in client-side prediction.
- Bulk file copy: throughput-bound, not latency-bound. WireGuard is fine.
- Video over Rocket.Chat: WebRTC handles 240 ms RTT acceptably; perceived as "a little delay" not "broken".

## 3-layer anonymity model (PROPOSED)

| Layer | What it does | Tool | Status |
|---|---|---|---|
| **1. Private network** | Hides the existence + addressing of the Sinister servers from the public internet. Servers listen only on `tailscale0` interface; nothing on `eth0`. | Tailscale (V1), WireGuard (V2) | PROPOSED |
| **2. DNS-over-HTTPS** | Prevents DNS leaks revealing what the operator is browsing even when the rest of traffic is VPN'd. | cloudflared `proxy-dns` sidecar (Cloudflare 1.1.1.1 + 1.0.0.1 + Google fallback) on every node | SCAFFOLDED |
| **3. Per-app proxy routing** | Lets the operator choose per-app whether traffic exits via the NY exit-node, FL exit-node, direct, or Tor. | `eve proxy <app> <route>` CLI (SCAFFOLDED — config-only; nftables/netns enforcement deferred — see [`source/docker-stack/PROXY-DESIGN.md`](../source/docker-stack/PROXY-DESIGN.md)) | SCAFFOLDED |

Layer 1 (private network) was **scaffolded 2026-05-24** via `source/docker-stack/compose.mesh.yml` + `config/tailscale/acl.json` + `MESH-DEPLOY.md`. Layer 2 (DoH per node) was **scaffolded 2026-05-24** via `source/docker-stack/compose.doh.yml` + `config/cloudflared/config.yml` + `DOH-DEPLOY.md` + `eve doh {up,down,status,verify,test,help}` — cloudflared `proxy-dns` sidecar listens on `127.0.0.1:5053`; YAML parse PASS; not yet enforced (no auto-rewrite of `/etc/resolv.conf` on participating nodes). Layer 3 (per-app proxy CLI) was **scaffolded 2026-05-24** via `source/docker-stack/eve proxy {list,set,show,verify}` + `config/proxy/routes.json` + `PROXY-DESIGN.md` — note: config-only, no traffic actually re-routes yet (enforcement layer deferred; see PROXY-DESIGN.md § 2 + § 5).

## Cross-references

| If you want to … | Read |
|---|---|
| Verify the servers you're connecting to are themselves hardened | [ghost-server-hardening.md](ghost-server-hardening.md) + [`source/docker-stack/HARDENING.md`](../source/docker-stack/HARDENING.md) |
| Edit the Panel UI live from Thailand over the mesh | [live-dev-workflow.md § 7 failure modes](live-dev-workflow.md) — HMR over 250 ms RTT works but is noticeable |
| Soft-reboot a remote server via `eve clean` | [qol-features.md § 1 soft-reboot](qol-features.md) |
| See the operator's full original directive in context | [SESSION-HANDOFF-2026-05-24T1442Z.md utterance #15](../SESSION-HANDOFF-2026-05-24T1442Z.md) |

## Honest status summary (2026-05-24 — M5 scaffold landed)

- **Topology design**: PROPOSED (this doc)
- **Tailscale recommendation**: **SCAFFOLDED** — `source/docker-stack/compose.mesh.yml` shipped with the tailscale sidecar service. YAML parse PASS; effective `docker compose config` merge with base + hardened deferred until docker daemon is up. Not yet rolled out to NY/FL hardware.
- **Tailscaled systemd unit (Sinister OS native path)**: **SCAFFOLDED** — `source/iso-build/airootfs/etc/systemd/system/tailscaled.service` + `etc/default/tailscaled` env file + `sinister-tailscale-firstboot.service` one-shot land in the ISO airootfs. Both unit files have valid `[Unit]/[Service]/[Install]` sections (configparser PASS). systemd-analyze verify deferred to a Linux build host. Real first-boot join blocked on operator generating TS_AUTHKEY.
- **DoH proxy (Layer 2)**: **SCAFFOLDED** — `source/docker-stack/compose.doh.yml` (cloudflared sidecar on `127.0.0.1:5053`) + `config/cloudflared/config.yml` (Cloudflare + Google DoH upstreams, 1.1.1.1/1.0.0.1 bootstrap, metrics :42040) + `DOH-DEPLOY.md` (operator runbook including Windows `netsh dns add encryption` path) + `eve doh {up,down,status,verify,test,help}` subcommand. All parse-verified; no live dig probe against running cloudflared yet.
- **ACL policy**: **SCAFFOLDED** — `source/docker-stack/config/tailscale/acl.json` template ships with `tag:operator` / `tag:server` / `tag:agent` / `tag:exit` and rules; JSON parse PASS. Pasted into the Tailscale admin console by the operator (manual step) — see `source/docker-stack/MESH-DEPLOY.md § Step 2`.
- **Mesh CLI**: **SCAFFOLDED** — `eve mesh {up|down|status|peers|ping|verify}` in `source/docker-stack/eve`; bash -n PASS; `eve mesh verify` exit 0.
- **Operator runbook**: **SHIPPED** — `source/docker-stack/MESH-DEPLOY.md` (6 steps + Windows path + Sinister-OS-native path + honesty ledger).
- **WireGuard alternative**: PROPOSED (Option B in this doc; deferred until Tailscale free tier hits a wall or operator's anonymity goal outranks convenience).
- **3-layer anonymity model**: layer 1 (private network) **SCAFFOLDED** via Tailscale (compose.mesh.yml + ACL + eve mesh CLI); layer 2 (DoH) **SCAFFOLDED** via cloudflared proxy-dns (compose.doh.yml + cloudflared/config.yml + DOH-DEPLOY.md + eve doh CLI; YAML parse PASS; enforcement of `/etc/resolv.conf` rewrite still deferred); layer 3 (per-app proxy CLI) **SCAFFOLDED** via routes.json + eve proxy CLI (PROXY-DESIGN.md; config-only, no enforcement). All three layers are scaffold-grade; no live measurements on the operator's actual links yet.
- **Speed expectations**: documented honestly; physics confirmed via public latency-budget tables, NOT measured on the operator's actual links. Step 6 in `MESH-DEPLOY.md` runs `iperf3` to replace estimates with measured numbers.
- **Operator's "download my exe file from Thailand" scenario**: blocked on (a) operator running steps 1–5 in `MESH-DEPLOY.md` and (b) the EXE existing (M6 mobile / desktop installer).
- **Operator's "connect to my servers with no speed issues" scenario**: scaffold ready; achievable for throughput; interactive latency is physics-bound and needs `mosh` / WebRTC prediction to feel snappy.

## What an honest M5 milestone looks like

1. Bring up Tailscale on operator's laptop + Sinister-mesh-NY (the home server) + sinister-mesh-FL (the second home server)
2. Verify peer-to-peer connectivity: `tailscale ping <peer>` from each node
3. Measure: `iperf3` between Thailand laptop and NY server (throughput + RTT)
4. Enable NY as exit node; toggle on the laptop; verify `curl ifconfig.me` returns NY IP
5. Author ACL policy locking down `tag:server` to only accept connections from `tag:operator`
6. Document in this file with REAL numbers replacing the speed-estimate table

Until those six steps land with receipts, this doc stays marked PROPOSED.
