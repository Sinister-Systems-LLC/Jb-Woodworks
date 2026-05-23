# JB Woodworks - Deploy

> **Author:** RKOJ-ELENO :: 2026-05-23

**Off Vercel, on Railway.** Same pattern LetsText uses.

## Three paths

| Path | When | URL |
|---|---|---|
| **Local dev** (`npm run dev`) | Daily iteration | http://127.0.0.1:3000 |
| **Local prod smoke** (`npm run build && npm start`) | Verify a build before push | http://127.0.0.1:3000 |
| **Railway** (NIXPACKS) | Public production | `*.up.railway.app` then custom domain |

### Local dev

```bash
bats\jb-install.bat    # one-time
bats\jb-dev.bat
```

Hot reload on. Open <http://127.0.0.1:3000>.

### Local production smoke

```bash
bats\jb-prod.bat
```

Same runner Railway uses (`next start`). Optimized build. No hot reload.

### Railway

```bash
# One-time
gh repo create Sinister-Systems-LLC/Jb-Woodworks --private --source=. --push
railway login
railway init                  # link the repo
railway up                    # first deploy
railway domain                # claim a *.up.railway.app subdomain

# Set environment variables in the Railway dashboard:
#   DATABASE_URL       (Railway provisions Postgres - copy its DATABASE_URL)
#   RESEND_API_KEY     (resend.com)
#   CONTACT_TO_EMAIL   = jbwoodworks8@gmail.com
#   CONTACT_FROM_EMAIL = JB Woodworks <noreply@your-domain.com>
#   NEXT_PUBLIC_SITE_URL = https://your-domain.com
```

`railway.json` declares NIXPACKS builder, `prisma db push --skip-generate && npm start` start command, `/api/healthz` healthcheck, 5-retry restart policy.

Push to `main` triggers a deploy. Push to `agent/jb-woodworks/*` does not.

## Domain wiring

1. Register the production domain.
2. **Railway dashboard** -> Settings -> Custom Domain -> get CNAME target.
3. Set the CNAME at the registrar.
4. Update `NEXT_PUBLIC_SITE_URL` in Railway to the final HTTPS URL.

## Environment variables

| Name | Where | Notes |
|---|---|---|
| `DATABASE_URL` | Railway -> Postgres add-on | Required for ContactInquiry persistence |
| `RESEND_API_KEY` | Resend.com | If unset, falls back to FormSubmit |
| `CONTACT_TO_EMAIL` | Railway | Default `jbwoodworks8@gmail.com` |
| `CONTACT_FROM_EMAIL` | Railway | `noreply@<your-domain>` |
| `CONTACT_FORMSUBMIT_URL` | Railway | Fallback handler, default in `.env.example` |
| `NEXT_PUBLIC_SITE_URL` | Railway | Public base URL, used in OG + canonical |
| `PORT` | Railway-set | Auto |

## Contact form flow (matches LetsText layered pattern)

1. Form `POST /api/contact` (FormData).
2. Server validates with zod.
3. Honeypot (`_honey`) silently accepts spam.
4. **Persist** to Postgres `contact_inquiry` if `DATABASE_URL` set.
5. **Email** via Resend if `RESEND_API_KEY` set.
6. **Fallback** to FormSubmit if Resend not configured (matches v1 Vercel behavior).
7. Always logs to stdout for ops visibility.
8. Client redirects to `/contact/thanks` on 2xx.

## Rollback

- **Railway:** `railway rollback` reverts to previous deploy.
- **Code:** `git revert <sha>` + push.

## Why not Vercel

- Marketing site rebuilds happen 3-5x/week max. Vercel's edge wins are wasted at our traffic.
- Vercel Postgres + serverless functions cost more than Railway's `$5/mo` long-lived process at our scale.
- Sanctum policy: prefer infrastructure we control.
- LetsText already runs on Railway with the same NIXPACKS + Prisma pattern. Operating two stacks is a tax we should not pay.
