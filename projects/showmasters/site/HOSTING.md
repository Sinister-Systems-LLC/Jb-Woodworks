<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# Showmasters Hosting Plan — Self-Hosted, Off Vercel

The decision is made: this site does not run on Vercel. We own the metal, we own the pipe, we own the records.

This doc captures three viable hosting paths and the recommended one. Pick a path, then follow the deploy checklist at the bottom.

---

## Goals

1. **Owned infrastructure.** No vendor lock, no usage-based pricing surprises, no shadow telemetry.
2. **Cheap.** Under $20/month total recurring.
3. **Fast.** TTFB under 200 ms anywhere in the contiguous US.
4. **No build step.** Static HTML + CSS + JS. `git push` to deploy. No Vercel-style serverless functions, no Next.js, no edge runtime nonsense.
5. **HTTPS by default.** TLS cert auto-renew, no manual.

---

## Path A — Workstation-hosted (current Sanctum machine)

The simplest path. The Sanctum workstation runs the site directly on a local Caddy server, exposed via a Cloudflare tunnel.

**Stack:**
- Caddy (binary, no Docker) → serves `/Showmasters Site/` directly as static files.
- Cloudflare tunnel (free) → exposes the local Caddy without opening ports.
- Cloudflare DNS for `showmasters.com` → CNAME the apex + www at the tunnel address.

**Pros:**
- $0/month recurring (workstation is already running).
- TLS handled by Cloudflare end-to-end.
- DDoS shielding free via Cloudflare.
- Deploy is literally "save the file" — Caddy serves from disk live.

**Cons:**
- If the workstation goes down or moves networks, the site goes down with it.
- Bandwidth is residential (probably fine for the traffic levels expected; site is ~50 MB total).

**When to pick this:** Right now, for the public launch sprint, before we have a real ops cadence.

---

## Path B — Single VPS (Hetzner / DigitalOcean / Vultr)

A $5/mo VPS (1 vCPU, 1 GB RAM, Ubuntu 24.04 LTS). Caddy front, files synced via `rsync` or `git pull` on a webhook.

**Stack:**
- Hetzner CX11 ($4.59/mo, EU) or DO basic droplet ($6/mo, US-East / US-West).
- Ubuntu 24.04 → Caddy 2 (`apt install caddy`).
- Site files in `/var/www/showmasters/`.
- Cloudflare DNS A-record at the VPS IP.
- TLS via Caddy auto-cert (Let's Encrypt).
- Deploy via `git pull` triggered by a tiny webhook script (or just SSH + `rsync`).

**Pros:**
- 24/7 availability decoupled from any local machine.
- Fixed cost, no surprise bills.
- Reachable from anywhere via SSH for troubleshooting.

**Cons:**
- A few hours of one-time setup.
- Need to keep the OS patched (`unattended-upgrades` handles it).

**When to pick this:** As soon as we want SLA-grade availability — recommended for the long-term production deployment.

---

## Path C — Static-only object storage with custom edge

Stash the static files in an S3-compatible bucket (Cloudflare R2, Backblaze B2, or our own MinIO on the workstation) and front them with a Cloudflare Worker that handles routing + headers.

**Pros:**
- Effectively zero compute cost.
- Massively horizontal — handles any traffic spike.

**Cons:**
- Adds a Cloudflare Workers dependency. Slightly violates the "own everything" principle (Workers is still a vendor runtime).
- Routing rules (`/` → `index.html`, `/orlando` → `orlando.html`) require a Worker function.

**When to pick this:** Only if traffic outgrows Path B. Don't start here.

---

## Recommendation

**Phase 1 (this sprint, public launch):** Path A — workstation + Cloudflare tunnel. Get the site live today, no infra to provision.

**Phase 2 (within 90 days, production handoff):** Path B — $5/mo Hetzner droplet. Move once we know the site shape is stable and we want it always-on independent of the workstation.

**Phase 3 (if traffic spikes — months 6+):** Path C — only if the VPS shows CPU strain or we suddenly need global edge.

---

## DNS setup (Cloudflare — both Path A and B)

1. Buy / move `showmasters.com` to Cloudflare DNS (free).
2. Records:
   - `A` `@` → Path B VPS IP (or proxied tunnel for Path A)
   - `CNAME` `www` → `showmasters.com`
   - `CAA` `@` → `0 issue "letsencrypt.org"` (only Let's Encrypt may issue certs)
3. Cloudflare SSL/TLS mode: **Full (strict)** for Path B, **Flexible** is OK for Path A tunnel.
4. Page Rules:
   - `http://*showmasters.com/*` → "Always Use HTTPS"
   - Cache level: "Cache Everything" for `.svg`, `.css`, `.js`, `.mp4`, `.webp`, `.woff2`
5. Email routing: route `Orders@ShowMasters.com` to the operator's inbox. Free.

---

## Caddyfile (Path B — drop in `/etc/caddy/Caddyfile`)

```caddy
showmasters.com, www.showmasters.com {
    root * /var/www/showmasters
    try_files {path} {path}.html /index.html
    file_server
    encode zstd gzip

    # Long-cache static assets
    @static {
        path *.svg *.css *.js *.mp4 *.webp *.woff2 *.ico
    }
    header @static Cache-Control "public, max-age=31536000, immutable"

    # Short-cache HTML
    @html {
        path *.html
    }
    header @html Cache-Control "public, max-age=300"

    # Security headers
    header X-Content-Type-Options "nosniff"
    header Referrer-Policy "strict-origin-when-cross-origin"
    header Permissions-Policy "geolocation=(), camera=(), microphone=()"
    header X-Frame-Options "SAMEORIGIN"

    # Redirect www to apex
    @www host www.showmasters.com
    redir @www https://showmasters.com{uri} 301

    log {
        output file /var/log/caddy/showmasters.log
        format console
    }
}
```

Caddy auto-renews TLS via Let's Encrypt — no cron, no certbot, no manual step. That's why we use it.

---

## Deploy checklist (Path B — first time)

```bash
# On a fresh Ubuntu 24.04 VPS:
ssh root@<vps-ip>
apt update && apt upgrade -y
apt install -y caddy ufw git unattended-upgrades

# Firewall
ufw allow 22
ufw allow 80
ufw allow 443
ufw enable

# Auto patching
dpkg-reconfigure -plow unattended-upgrades

# Site files
mkdir -p /var/www/showmasters
cd /var/www/showmasters
git clone <repo-url> .

# Drop the Caddyfile above into /etc/caddy/Caddyfile
systemctl reload caddy
systemctl enable caddy

# Verify
curl -I https://showmasters.com
# Expect: HTTP/2 200, server: Caddy
```

Subsequent deploys are just `git pull` on the VPS, no restart.

---

## Deploy checklist (Path A — workstation + Cloudflare tunnel)

```bash
# Install Caddy on Windows (Sanctum workstation)
choco install caddy

# Install cloudflared
choco install cloudflared
cloudflared login
cloudflared tunnel create showmasters
cloudflared tunnel route dns showmasters showmasters.com

# Caddyfile (Windows path)
# C:\caddy\Caddyfile
showmasters.com {
    root * "C:/Users/Zonia/Desktop/Showmasters Site"
    file_server
    encode zstd gzip
}

# Run as a service
caddy run --config C:\caddy\Caddyfile
cloudflared tunnel run showmasters
```

Both processes should be wrapped as Windows services (NSSM or sc.exe) so they survive reboots. Add them to the Sanctum auto-start list (`tools/sinister-workstation-setup/`).

---

## Anti-Vercel anti-checklist

When tempted to add any of these — STOP:

- **Vercel CLI** (`vercel`, `vercel dev`) — never installed.
- **`vercel.json`** — not in this repo.
- **`api/`** folder with serverless functions — none. If we need server logic, write a normal HTTP service.
- **Edge runtime imports** (`export const runtime = 'edge'`) — N/A; we don't use Next.js.
- **`@vercel/*` npm packages** — none.
- **`https://*.vercel.app`** — no preview deploys; preview happens on a separate `dev.showmasters.com` subdomain on our own infra.

---

## Move-from-Vercel checklist (if ever found on Vercel)

1. Export site content (it's already static — just zip the public assets).
2. Set up Path B (above).
3. Cloudflare DNS swap A-record from Vercel's IP to our VPS IP.
4. Delete the Vercel project.
5. Remove any `vercel.json`, `.vercel/` folders, `@vercel/*` deps.
6. Verify analytics, forms, and contact submissions still work.
7. Done.

---

## Forms (the one server-side concern)

The contact form on `index.html` and `contact.html` posts to `/api/inquiry`. Right now that endpoint doesn't exist on the static host.

Two options:

**(a) Static-only — email-first:** Use `mailto:` form action with `formsubmit.co` or `web3forms.com` (free), OR have the form `mailto:Orders@ShowMasters.com?subject=...&body=...` which opens the client's email app.

**(b) Self-hosted Go binary on Path B VPS:** A tiny ~50-line Go program that listens on `/api/inquiry`, validates input, appends to `/var/log/showmasters/inquiries.jsonl`, and sends a notification email via SMTP. Total binary size ~5 MB, runs forever.

**Recommended:** start with (a), upgrade to (b) when we deploy to Path B.

---

## Monitoring

Free options that don't require giving up ownership:

- **UptimeRobot** (5-min checks, free 50 monitors): pings `https://showmasters.com/healthz` from 5 regions.
- **Cloudflare Analytics** (built into free DNS): traffic, bandwidth, threats blocked.

Add `/healthz` route serving `200 OK + "ok"` to Caddy (it's already in the JB Woodworks app pattern — mirror that approach if/when we add a server-side component).

---

## When the operator asks about hosting cost

The honest answer:

- Year 1 with Path A: **$0** recurring (workstation already paid for, Cloudflare DNS free, Let's Encrypt free).
- Year 1 with Path B: **~$60** (1× VPS @ $5/mo for 12 months).
- Year 1 with Path C: **~$15** (Cloudflare Workers free tier covers our traffic; R2 storage ~$1.50/mo).

Compare to Vercel Pro: **$20/user/month × 12 = $240+/year** plus per-GB bandwidth fees.
