# JB Woodworks - Website

> **Author:** RKOJ-ELENO :: 2026-05-23

Custom-woodworking business marketing site for **JB Woodworks** (Orlando, FL).
Premium Craftsmanship. Built to Last.

## Stack (LetsText parity)

- **Next.js 15** (App Router) + **React 19** + **TypeScript**
- **Tailwind CSS** for styles
- **framer-motion** for animations
- **lucide-react** + custom SVG sprite for icons
- **Prisma 5** + **Postgres** (contact inquiry persistence)
- **Resend** (transactional email; FormSubmit as fallback)
- **Railway** for deploy (NIXPACKS builder, no Vercel)

## Quickstart

```bash
# First time
bats\jb-install.bat            # npm install + prisma generate
copy .env.example .env.local   # then edit DATABASE_URL + RESEND_API_KEY

# Daily
bats\jb-dev.bat                # http://127.0.0.1:3000 with hot reload
# or
npm run dev
```

## Routes

| Path | Page |
|---|---|
| `/` | Hero video slider + services + portfolio preview + FAQ + CTA |
| `/services` | All six services with details |
| `/portfolio` | Full portfolio with category filter (Decks, Docks, Furniture, Outdoor Living) |
| `/portfolio/[slug]` | Single project gallery (videos + photos) |
| `/about` | Process, materials, FAQ |
| `/contact` | Inquiry form |
| `/contact/thanks` | Form confirmation |
| `/api/healthz` | `{"ok": true}` liveness |
| `/api/contact` | POST handler: Prisma + Resend + FormSubmit |
| `/robots.txt`, `/sitemap.xml` | SEO |

## Structure

```
jb-woodworks/
  app/
    layout.tsx, page.tsx, globals.css
    services/, portfolio/, portfolio/[slug]/, about/, contact/, contact/thanks/
    api/healthz/route.ts
    api/contact/route.ts
    not-found.tsx, robots.ts, sitemap.ts
  components/
    sections/  (Nav, Footer, Hero, ServiceCard, PortfolioCard, PortfolioFilter, ContactForm)
    ui/        (Icon, Reveal)
  lib/
    site.ts, utils.ts, db.ts
    content/   (services.json, portfolio.json, faq.json, hero_media.json, index.ts)
  prisma/
    schema.prisma   (ContactInquiry model)
  public/
    img/        (favicon set, og-image, icons.svg, projects/ junction -> Jah Images)
    media/      (transcoded H.264 videos + poster JPGs)
    site.webmanifest
  branding/   (logos + patterns + MANIFEST + GUIDELINES)
  bats/       (jb-dev / jb-prod / jb-kill / jb-restart / jb-install)
  _legacy-flask/  (archived Python/Flask v0.2.1 - kept for media scripts)
  railway.json, next.config.mjs, tailwind.config.ts, tsconfig.json, postcss.config.mjs
  .env.example, package.json, prisma/
```

## Editing content

- **Services:** `lib/content/services.json` - title, blurb, details, icon.
- **Portfolio:** `lib/content/portfolio.json` - cover, media list (videos + raw images).
- **FAQ:** `lib/content/faq.json`.
- **Hero slider:** `lib/content/hero_media.json` - sequence + durations.
- **Site facts** (phone, email, socials, tagline): `lib/site.ts`.

No restart needed in dev - changes hot-reload.

## Media pipeline

- Canonical source library: `D:\Sinister\old\Coding Random\JB Woodworks\Jah Images\` (105 MB total, kept outside the repo).
- Raw originals referenced from `portfolio.json` are copied into `public/img/projects/` as real files (~8 MB, 14 files) so the project folder is self-contained for deploy.
- Hero + portfolio videos are pre-transcoded to web-optimized H.264 + faststart at `public/media/` via `_legacy-flask/scripts/optimize_media.py`. Re-run with `npm run media:optimize` whenever sources change.
- Poster JPGs are extracted alongside each MP4 for instant background paint.
- Favicons are regenerated with `npm run media:favicons` (Pillow-based, produces 16/32/48/180/192/512 PNG + ICO + SVG).
- To add a new raw photo to a portfolio item: drop it under `public/img/projects/<Category>/`, then reference it in `lib/content/portfolio.json` with `{"type": "raw-image", "src": "..."}`.

## Deploy

See `DEPLOY.md`. Short version: **Railway**, not Vercel. Connect repo, set `DATABASE_URL` + `RESEND_API_KEY` + `NEXT_PUBLIC_SITE_URL`, push.

## Brand

`branding/` carries 8 wordmark SVG variants + 2 patterns + `MANIFEST.md` + `BRAND-GUIDELINES.md`. The wordmark is text-based ("JB" Inter 900 + tiny "WOODWORKS" gold below) and is rendered inline in the React components for sharpness at any zoom level.
