# DOH-DEPLOY — Sinister M5 Layer-2 DoH rollout runbook

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Status:** SCAFFOLDED. Compose overlay + cloudflared config land in this commit; no live cloudflared daemon is running yet, no host resolv.conf has been rewritten. The operator runs the steps below to actually light up Layer 2.
> **Composes with:** `docs/geo-mesh-routing.md` (the design), `compose.hardened.yml` (per-node baseline), `compose.mesh.yml` (Layer 1 — tailnet), `compose.doh.yml` (this overlay — Layer 2), `config/cloudflared/config.yml` (DoH config).

## Why this exists

Three-layer anonymity model from `docs/geo-mesh-routing.md`:

| Layer | What it encrypts | Artifact |
|---|---|---|
| 1 — Mesh | Peer ↔ peer traffic + exit-node egress | `compose.mesh.yml` (Tailscale) |
| **2 — DoH** | **DNS queries → upstream resolver** | **`compose.doh.yml` (cloudflared) — THIS FILE** |
| 3 — Per-app proxy | Selective per-app egress routing | Deferred (Layer 3 needs polkit/nftables) |

Without Layer 2, DNS leaks via plain UDP/53 even when traffic rides the tailnet — the resolver (and any on-path eavesdropper before the resolver) sees every domain you visit. cloudflared in `proxy-dns` mode shifts that DNS over HTTPS to Cloudflare (or NextDNS), closing the leak.

## What's in this commit (verified)

| Artifact | Verification |
|---|---|
| `compose.doh.yml` — cloudflared sidecar overlay | `python -c "import yaml; yaml.safe_load(open('compose.doh.yml'))"` exit 0 (see verify section below) |
| `config/cloudflared/config.yml` — proxy-dns config | `python -c "import yaml; yaml.safe_load(open('config/cloudflared/config.yml'))"` exit 0 |
| `DOH-DEPLOY.md` — this file | exists at the path above |

## What the operator runs

### Step 1 — Bring up the DoH overlay on a Linux node

```bash
# On the NY/FL home server (or any Linux node in the sinister-os checkout):
cd projects/sinister-os/source/docker-stack

# Bring up the full stack with hardening + mesh + DoH overlays
docker compose \
  -f docker-compose.yml \
  -f compose.hardened.yml \
  -f compose.mesh.yml \
  -f compose.doh.yml \
  up -d
```

### Step 2 — Verify cloudflared answers DoH from the host

```bash
# Plain probe (UDP):
dig @127.0.0.1 -p 5053 example.com +short
# Expected: a non-empty A record (e.g. 93.184.216.34)

# TCP probe (proves the TCP listener):
dig @127.0.0.1 -p 5053 example.com +short +tcp

# Container-internal probe (proves other services on the mesh net resolve via cloudflared):
docker run --rm --network=sinister-mesh tutum/dnsutils \
  dig @sinister-cloudflared -p 5053 example.com +short
```

Acceptance: every probe returns the same record without error, in < 200 ms steady-state.

### Step 3 — (Optional) Point the Linux host's resolver at cloudflared

> **Operator-gated.** This rewrites `/etc/resolv.conf` / systemd-resolved config. Do not run until you've watched cloudflared for an hour or two from step 2 and trust it.

```bash
# Option A — systemd-resolved (Ubuntu/Debian/Arch with systemd-resolved):
sudo mkdir -p /etc/systemd/resolved.conf.d
sudo tee /etc/systemd/resolved.conf.d/sinister-doh.conf <<'EOF'
[Resolve]
DNS=127.0.0.1:5053
FallbackDNS=1.1.1.1 1.0.0.1
DNSStubListener=yes
EOF
sudo systemctl restart systemd-resolved

# Verify:
resolvectl status | grep -E "(DNS Servers|Current DNS Server)"

# Option B — plain /etc/resolv.conf (no systemd-resolved):
sudo cp /etc/resolv.conf /etc/resolv.conf.bak
echo "nameserver 127.0.0.1" | sudo tee /etc/resolv.conf
# Note: many DHCP clients overwrite this on next lease renew. Add `chattr +i`
# at your own risk, or use NetworkManager's dns=none + a static unit.
```

### Step 4 — (Optional) Switch upstream to NextDNS for filtering

If the operator opens a NextDNS account ( https://my.nextdns.io ) and gets a profile ID (e.g. `abcd12`), swap the upstream:

```bash
# Edit compose.doh.yml — replace the --upstream= flags with the NextDNS DoH endpoint:
#   --upstream=https://dns.nextdns.io/abcd12
# (Profile ID goes in the path; cloudflared does no extra auth.)

# Then:
docker compose -f docker-compose.yml -f compose.hardened.yml \
               -f compose.mesh.yml   -f compose.doh.yml up -d --force-recreate cloudflared
```

NextDNS upstream gains: per-profile ad/tracker/malware filtering, query-log dashboard, parental controls, allow/block lists. Tradeoff: NextDNS now sees the query stream (instead of Cloudflare).

### Step 5 — Confirm DNS is no longer leaking in clear UDP/53

```bash
# Sniff UDP/53 on the host's primary interface — should see ZERO queries after step 3:
sudo tcpdump -i any -n 'udp port 53' -c 20

# Sniff TCP/443 to 1.1.1.1 — should see steady traffic during browsing:
sudo tcpdump -i any -n 'host 1.1.1.1 and tcp port 443' -c 20
```

Acceptance: UDP/53 sniff stays empty (or only sees the `5053`-bound packets from cloudflared->kernel loopback, which is fine); TCP/443 sniff shows cloudflared's DoH connections.

### Step 6 — Restart on config change

```bash
# Whenever config/cloudflared/config.yml changes:
docker compose -f docker-compose.yml -f compose.hardened.yml \
               -f compose.mesh.yml   -f compose.doh.yml restart cloudflared
```

## Windows host path (operator's Sanctum dev box)

Windows 11 ships native DoH support — no cloudflared container needed on the Sanctum dev box. The Windows path:

```powershell
# Run as Administrator. Add Cloudflare as a known DoH resolver:
netsh dns add encryption server=1.1.1.1 dohtemplate=https://cloudflare-dns.com/dns-query autoupgrade=yes
netsh dns add encryption server=1.0.0.1 dohtemplate=https://cloudflare-dns.com/dns-query autoupgrade=yes

# Set the active adapter's DNS to 1.1.1.1 / 1.0.0.1 (replace "Ethernet" with your adapter name):
Get-NetAdapter | Where-Object Status -eq 'Up'
Set-DnsClientServerAddress -InterfaceAlias "Ethernet" -ServerAddresses 1.1.1.1,1.0.0.1

# Verify Windows uses DoH for the adapter:
Get-DnsClientDohServerAddress
netsh dns show encryption
```

Settings → Network & Internet → (adapter) → Edit DNS server assignment → set **DNS over HTTPS** to **On (automatic template)** to enable the GUI path.

The cloudflared container in `compose.doh.yml` still runs cleanly on Docker Desktop for Windows; it's just redundant when the host DNS Client is already doing DoH natively. Useful for testing or when you want the metrics endpoint on :42040.

## Sinister OS path (eventual)

When the ISO bake lands (`source/iso-build/`), cloudflared ships as a real systemd unit on the installed OS — no sidecar needed. The unit file template will live at `source/iso-build/airootfs/etc/systemd/system/cloudflared-doh.service` (added in a future iteration, parallel to the planned `tailscaled.service`). systemd-resolved will be pre-configured to point at 127.0.0.1:5053.

## Verification commands (run anywhere; no docker daemon required)

```bash
cd projects/sinister-os/source/docker-stack

# 1. YAML parse of the overlay
python -c "import yaml; yaml.safe_load(open('compose.doh.yml')); print('doh overlay parse OK')"

# 2. YAML parse of the cloudflared config
python -c "import yaml; yaml.safe_load(open('config/cloudflared/config.yml')); print('cloudflared config parse OK')"

# 3. Confirm DOH-DEPLOY.md exists
test -f DOH-DEPLOY.md && echo "DOH-DEPLOY.md exists"
```

When docker is up, also:

```bash
# 4. Effective config render with all four overlays
docker compose -f docker-compose.yml -f compose.hardened.yml \
               -f compose.mesh.yml   -f compose.doh.yml config --services

# 5. Live DoH probe (the real acceptance test)
dig @127.0.0.1 -p 5053 example.com +short
```

## What's intentionally deferred

| Deferred | Why |
|---|---|
| NextDNS account creation + profile ID | Requires operator signup at https://my.nextdns.io . Default Cloudflare upstream works without account. |
| Automated `/etc/resolv.conf` rewrite enforcement | Different distros rewrite resolv.conf via different agents (systemd-resolved, NetworkManager, resolvconf, dhcpcd). One enforcer-per-distro is M5+ work. Operator runs step 3 manually for now. |
| Per-app DNS routing | Layer 3 of the 3-layer model. Needs polkit/nftables wrapping on the Linux host; lives in a separate iteration. |
| DoT (DNS-over-TLS) fallback | cloudflared `proxy-dns` does DoH only. If a future deploy needs DoT, swap to `stubby` or `dnsdist`. |
| Pinned image digest (`@sha256:...`) | Tag-pinning to `cloudflare/cloudflared:latest` for M5 scaffold; bump to a specific stable tag (e.g. `2025.5.0`) + digest pin when the deploy lands. |
| Metrics scrape into Prometheus | cloudflared exposes :42040 inside the container; Prometheus scrape config not wired yet. |
| `eve doh` CLI subcommand | Mirroring `eve mesh`, this would wrap `up/down/status/probe`. Defer until a second daily-use surface beyond `eve mesh` justifies the CLI growth. |

## What this overlay does NOT change

- Existing stack ports + bindings: unchanged. cloudflared binds 127.0.0.1:5053 only — no clash with anything else in the stack.
- The hardened overlay's `read_only` / `cap_drop` settings: unchanged for the other services.
- Operator's existing host DNS settings: unchanged until step 3 is run (opt-in).
- The tailnet (compose.mesh.yml): unchanged. Layer 1 and Layer 2 compose cleanly.

## End-of-runbook honesty ledger

- `compose.doh.yml` validated by YAML parse, **not** verified end-to-end with a real `docker compose up` against a live cloudflared image pull.
- `config/cloudflared/config.yml` validated by YAML parse, **not** tested against cloudflared's actual config loader.
- No `dig @127.0.0.1 -p 5053` probe has been run against a live container — that lands when step 2 runs on a real Linux node.
- No host resolv.conf rewrite has been performed — step 3 is operator-gated and intentionally untouched.
- The Windows `netsh dns add encryption` commands are documented from Microsoft's published Windows 11 DoH support; not executed in this commit.
- This is M5 Layer-2 **scaffold**, not Layer-2 **deployed**.
