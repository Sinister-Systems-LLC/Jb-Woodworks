<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# Security — Showmasters

What's protected, what's not, what to lock down before public launch.

---

## Surface area today (static-site phase)

The static `.html` site has no backend. No user data is persisted client-side. The site is read-only HTML/CSS/JS served by Caddy (production) or Python http.server (local dev).

### Forms

| Form | Where | State |
|---|---|---|
| Estimate form | `/contact.html#estimate`, `/index.html#estimate` | Submits to JS demo handler; no real persistence yet |
| Order Online | `/order.html` | Submits to JS demo handler; no real persistence yet |
| Crew Application | `/careers.html` | mailto: link, opens user's mail client |

Neither form currently posts to a server. Once `app-v2/` is deployed, both will POST to `/api/inquiry` and `/api/application` (Next.js route handlers wired to Prisma + Postgres).

### Third-party network calls

- **Google Fonts** (`fonts.googleapis.com` + `fonts.gstatic.com`) — preconnect + stylesheet. Browser fetches `Inter` + `DM Serif Display` + `JetBrains Mono`. No tracking concerns; subresource integrity not yet enabled.
- **Cloudflare Turnstile** (when app-v2 lands) — CAPTCHA. Currently not loaded.
- **No third-party analytics.** No GA4, no Meta Pixel, no Hotjar.

### Sensitive paths kept out of search indexes

`robots.txt` blocks crawlers from:
- `/BRANDING/` (brand source files)
- `/MARKETING/` (internal playbook)
- `/app-v2/` (Next.js source)
- `/STACK.md`, `/HOSTING.md`
- `/privacy.html`, `/terms.html` (also `<meta name="robots" content="noindex,follow">`)

Crawlers can be malicious — robots.txt is a request, not enforcement. Sensitive data must NOT live in any web-served path. The vault lives at `D:\Sinister Sanctum\_vault\` (not on the Desktop site).

---

## Pre-launch security checklist (when going live on a public domain)

### 1. HTTPS only

Caddy (per `HOSTING.md` Path B) provisions Let's Encrypt automatically. Verify after first start:

```bash
curl -sI https://showmasters.com | grep -i strict-transport
# expect: strict-transport-security: max-age=...
```

The Caddyfile in `HOSTING.md` already sets `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, `X-Frame-Options`. Verify those land.

### 2. Content Security Policy (CSP)

Add to Caddyfile (NOT yet present — add before launch):

```
header Content-Security-Policy "default-src 'self'; img-src 'self' data:; style-src 'self' https://fonts.googleapis.com 'unsafe-inline'; font-src 'self' https://fonts.gstatic.com; script-src 'self'; frame-ancestors 'self'"
```

`'unsafe-inline'` for style is needed by current inline CSS (page-specific styles in HTML). Audit + extract those to `style.css` later to drop the unsafe rule.

### 3. Form abuse protection (when app-v2 deploys)

- `app-v2/.env.example` already provisions `TURNSTILE_SECRET_KEY` + `NEXT_PUBLIC_TURNSTILE_SITE_KEY`. The inquiry route handler verifies the token before writing.
- IP-hash rate limiting: implement at Caddy level via `rate_limit` plugin (not stock — install separately). Or use a Postgres-side rolling-window check in the route handler.
- Honeypot field on every form — invisible, bots fill it, real users don't. Reject anything with a non-empty honeypot.

### 4. Database posture (Prisma + Postgres)

- Postgres user for the app has ONLY `INSERT` + `SELECT` on the 4 tables. No `DROP`, no `TRUNCATE`, no superuser.
- Daily `pg_dump` to a separate disk (or rclone to Backblaze B2).
- `.env` file mode `chmod 600`. Owner = app user only.
- Connection over local socket OR over a private network — never the public internet.

### 5. Email notification path

- SMTP creds in `.env` only.
- Notification emails contain `Subject: New SMPL inquiry from ...` and the inquiry summary; never include raw form values that could carry attacker-controlled HTML.

### 6. Static asset hygiene

- Every `<img>` carries explicit `alt`. Audit:

```bash
grep -rEn '<img(?![^>]*alt=)' *.html
# expect: no matches
```

- Every external link should consider `rel="noopener noreferrer"` if it ever uses `target="_blank"`. Today no `target="_blank"` exists on this site.

### 7. Dependency posture (app-v2)

- `pnpm audit` weekly in CI. (No CI yet — manual until set up.)
- Pin to exact versions in `package.json` once initial install lands.
- No automatic dependency updates without review.

### 8. Operator's lane (not my path)

- API keys → `.env`, never in any file in this repo.
- Vault for backups → `D:\Sinister Sanctum\_vault\` (master-agent denied; correct).
- ~/.claude/.mcp.json → operator-owned.

---

## What I CAN test right now (static-site phase)

```bash
# Headers (when behind Caddy):
curl -sI https://showmasters.com | head -30

# Open ports (after VPS provisioning):
sudo ss -tlnp | grep -E ':(22|80|443)'
# expect ONLY 22, 80, 443; nothing else exposed

# TLS grade:
# Run https://www.ssllabs.com/ssltest/ — target: A or A+

# Mixed content:
curl -s https://showmasters.com | grep -oE 'http://[^"]+'
# expect: no matches

# robots.txt is what we ship:
curl -s https://showmasters.com/robots.txt
```

---

## Incident response (minimal)

If something looks wrong:

1. Take the site offline at Cloudflare → "Under Attack" mode OR pull the DNS record.
2. Snapshot the VPS (Hetzner / DO console).
3. Rotate every key in `.env`.
4. Check Postgres for unexpected rows in `Inquiry`/`Application`.
5. Re-deploy from a known-good git ref.

---

## What's deliberately NOT done yet (and the reason)

| Item | Why not yet |
|---|---|
| CSP header | Need to extract inline styles first |
| SRI on Google Fonts | Google rotates the font URLs; SRI breaks on each rotation |
| Rate limiting | No backend yet to rate-limit |
| WAF rules | Cloudflare free tier covers the basics; revisit at scale |
| 2FA on operator login | No operator login surface exists yet (no /admin) |
| Audit logging | No DB yet |

Re-audit this list whenever a new surface lands (form, route, integration).
