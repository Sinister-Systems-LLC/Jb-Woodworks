# DNS-SPLIT-HORIZON.md — DNS coexistence doctrine (DoH + Tailscale MagicDNS + WG-fallback)

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Status:** DOCTRINE (configuration recipes; no per-node enforcement yet).
> **Composes-with:** `DOH-DEPLOY.md`, `MESH-DEPLOY.md`, `WG-FALLBACK.md`.

## The problem

Three independent DNS resolvers may try to answer queries on a Sinister mesh node simultaneously:

1. **Cloudflared / DoH** (`compose.doh.yml`) — forwards EVERY query to Cloudflare 1.1.1.1 over HTTPS. Wins by default if listening on 127.0.0.1:53.
2. **Tailscale MagicDNS** (`compose.mesh.yml` with `--accept-dns=true`) — answers `*.<tailnet>.ts.net` queries by querying tailscaled at 100.100.100.100; for everything else, forwards to the operator-configured DNS in the Tailscale admin console.
3. **systemd-resolved** (host default on most Linux distros) — has its own search domains, /etc/resolv.conf merging logic, and may shadow either of the above depending on `/etc/nsswitch.conf` + interface metric.

If all three run with default settings, **the loser depends on `/etc/resolv.conf` ordering** — undefined behavior across NY/FL/laptop nodes. Symptom: `ping ny-server.tail-scale-id.ts.net` works on one node and times out on another.

## The doctrine

Pick **one authoritative resolver per node** and explicitly delegate the other zones to it.

### Three-tier authority (recommended)

| Zone | Authority | Why |
|---|---|---|
| `*.ts.net` (Tailscale MagicDNS) | tailscaled (100.100.100.100) | Only tailscaled knows the dynamic tailnet IPs. |
| `*.sinister.internal` (operator-private fleet) | sinister-coredns (127.0.0.1:5353) | Future fleet-local zone; not yet active. |
| everything else | cloudflared / DoH (127.0.0.1:53) | Privacy + DoH benefits. |

### The recipes

#### A. With `systemd-resolved` (Arch/Debian/Ubuntu/Fedora default)

Drop this file at `/etc/systemd/resolved.conf.d/sinister.conf`:

```ini
[Resolve]
# Disable the global DNS fallback to upstream resolvers - we own this.
FallbackDNS=
# Cloudflared listens here for the DoH path.
DNS=127.0.0.1
# Cache aggressively (we trust our local stack).
Cache=yes
CacheFromLocalhost=yes
# Use stub listener at 127.0.0.53 (legacy compat for apps reading resolv.conf).
DNSStubListener=yes
```

Drop this file at `/etc/systemd/network/10-tailscale.network` (adjust interface name):

```ini
[Match]
Name=tailscale0

[Network]
DNS=100.100.100.100
Domains=~ts.net
# The `~` prefix means "this DNS server is authoritative for this domain only,
# not the global fallback." Critical — without `~`, tailscaled steals all queries.
```

Restart: `systemctl restart systemd-resolved systemd-networkd`.

Verify:

```bash
resolvectl status              # tailscale0 should show "DNS Domain: ~ts.net"
resolvectl query example.com   # should resolve via 127.0.0.1 (DoH)
resolvectl query <node>.<tailnet>.ts.net  # should resolve via 100.100.100.100
```

#### B. Without systemd-resolved (raw resolv.conf — minimal containers, ISO airootfs)

`/etc/resolv.conf`:

```
# Sinister Mesh split-horizon — order matters
nameserver 127.0.0.1
nameserver 100.100.100.100
options ndots:2 timeout:1 attempts:2 single-request-reopen
search ts.net sinister.internal
```

Plus a `dnsmasq` shim at 127.0.0.1:5354 that knows the zones:

```
# /etc/dnsmasq.d/sinister-split.conf
no-resolv
server=/ts.net/100.100.100.100
server=/sinister.internal/127.0.0.1#5353
server=127.0.0.1#53
listen-address=127.0.0.1
bind-interfaces
port=5354
```

Point `/etc/resolv.conf` at 127.0.0.1:5354 (or use port 53 if no other resolver wants it).

#### C. Cloudflared `config.yml` — explicit zone exclusion

`source/docker-stack/config/cloudflared/config.yml` should contain (additive — keep existing upstreams):

```yaml
proxy-bypass:
  # Never DoH-tunnel these — they belong to other authorities.
  - "*.ts.net"
  - "*.sinister.internal"
```

If `cloudflared` doesn't support `proxy-bypass` in your version, place the split at the systemd-resolved or dnsmasq layer instead (recipes A or B).

## The flow chart

```
                     query: "example.com"
                              │
                              ▼
                   systemd-resolved (stub at 127.0.0.53)
                              │
                       "is this *.ts.net?"
                              │
                  yes ───────┴─────── no
                   │                   │
                   ▼                   ▼
              tailscaled         "is this *.sinister.internal?"
            (100.100.100.100)                │
                              yes ───────┴─────── no
                               │                   │
                               ▼                   ▼
                       sinister-coredns       cloudflared
                       (127.0.0.1:5353)       (127.0.0.1:53 → DoH → 1.1.1.1)
```

## Failure modes + recovery

| Symptom | Likely cause | Fix |
|---|---|---|
| `ping <peer>.ts.net` works on NY, fails on FL | FL `/etc/resolv.conf` missing `100.100.100.100` for `ts.net` zone | Apply Recipe A or B to FL. |
| All DNS slow (~5s timeouts) | Two resolvers racing for port 53 | `ss -tulnp \| grep :53` to find duplicate listener; disable one. |
| `resolvectl query example.com` shows "RCODE: 5 (REFUSED)" | systemd-resolved configured to skip the global fallback but DoH not actually listening | Check `docker ps | grep cloudflared`; restart `compose.doh.yml` overlay. |
| WG-fallback peer can't resolve other peers by name | No split-zone DNS for the 10.42.0.0/24 subnet | Add `address=/<peer>.sinister.wg/10.42.0.X` lines to dnsmasq, OR use IPs. |

## Honesty ledger

What this doctrine DOES:

- Pins one resolver per zone authoritative.
- Provides three concrete config recipes (systemd-resolved / dnsmasq / cloudflared).
- Documents the failure modes that DON'T appear if doctrine is followed.

What this doctrine does NOT do:

- Self-apply. The operator (or future `eve dns apply` subcommand — NOT YET WRITTEN) installs the recipes on each node.
- Cover Windows DNS — the operator's Windows laptop should configure Tailscale's "Override local DNS" off and let the Tailscale Windows client handle the `.ts.net` zone via its own NRPT (Name Resolution Policy Table) entry. DoH on Windows is a separate setup (Cloudflare 1.1.1.1 Windows app or DoH-via-EDNS-Client-Subnet config in `netsh dnsclient`).
- Cover the `sinister.internal` zone — that's M6+ work; the doctrine pre-pins authority so M6 doesn't require a doctrine rewrite.

## See also

- `DOH-DEPLOY.md` — cloudflared overlay; this doctrine governs ITS coexistence with mesh DNS.
- `MESH-DEPLOY.md` — Tailscale overlay; § Coexistence cross-references this file.
- `WG-FALLBACK.md` — WG overlay; uses recipe B for ISO/minimal images.
