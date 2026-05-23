<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# Showmasters Stack — aligned with LetsText 2.0 dashboard

Operator directive (2026-05-23): *"make sure we are using all logic, coding language, database setup things like that that lets text is using."*

This doc captures the target stack for Showmasters going forward + the current state of the migration.

---

## Target stack (matches LetsText 2.0 dashboard-local + backend)

### Runtime + language
- **Node.js** ≥ 22.12.0
- **TypeScript** 5
- **React** 19.2
- **Next.js** 15.5 (App Router, Turbopack dev)

### Styling
- **Tailwind CSS** 4.1 + `@tailwindcss/postcss`
- `tailwindcss-animate` for motion utilities
- CSS variables for theme tokens (matches existing `style.css` palette)

### UI primitives
- **shadcn/ui** ("new-york" style, RSC, TSX, neutral base, CSS variables)
- **Radix UI** primitives (accordion, dialog, dropdown-menu, popover, scroll-area, select, tabs, toast, tooltip, etc.)
- Custom SVG icons in `components/icons/` (replace lucide-react — keep `lucide-react` installed only as a fallback, but the doctrine is custom icons everywhere per operator)

### Forms + validation
- **react-hook-form** 7 + `@hookform/resolvers/zod`
- **zod** 3.25 (schemas live in `lib/validations.ts`)
- **@marsidev/react-turnstile** for CAPTCHA on public-facing forms (contact, careers)

### Client state
- **@tanstack/react-query** 5 (for any client-side fetch)

### Motion
- **framer-motion** 12 (component-level transitions, entrance animations)
- **gsap** 3 (timeline-driven hero animations if needed)

### Maps
- **react-simple-maps** 3 + **topojson-client** 3 (replaces the hand-drawn US coverage map with a proper TopoJSON US states map)

### Database
- **Prisma** ORM 5+
- **Postgres** 16+ (self-hosted — see `HOSTING.md` Path B)
- Models: `Inquiry`, `Application`, `NewsletterSub`, `Show` (CMS-like)
- Migrations checked in to `app-v2/prisma/migrations/`

### Testing
- **Vitest** 2 (unit + integration)
- **@vitest/coverage-v8** (coverage)
- ESLint + TypeScript strict checks (`tsc --noEmit`) + EVE-style doctrine audits (later)

### Server-side LLM (when nano banana lands)
- `@anthropic-ai/sdk` or `openai` or Google's image SDK depending on nano banana's actual provider
- Wrapper in `lib/image-gen.ts` that locks the brand prompt suffix (per `BRANDING/NANO-BANANA-INTEGRATION.md`)

### Hosting (already decided)
- Self-hosted per `HOSTING.md` — Path B (Hetzner / DO droplet running Caddy + Next.js + Postgres). NOT Vercel, NOT Railway. Plain VPS.

---

## Migration shape

Showmasters lives in two pieces while we migrate:

```
Showmasters Site/
  ├── index.html, about.html, etc.   <- CURRENT STATIC SITE (live, polished)
  ├── style.css, script.js
  ├── public/                         <- shared assets (used by both old + new)
  ├── BRANDING/                       <- shared brand pack
  ├── MARKETING/                      <- shared docs
  ├── HOSTING.md, STACK.md            <- shared docs
  └── app-v2/                         <- NEW NEXT.JS APP (in progress)
        ├── package.json
        ├── tsconfig.json
        ├── next.config.mjs
        ├── tailwind.config.ts
        ├── postcss.config.mjs
        ├── components.json
        ├── .env.example
        ├── prisma/schema.prisma
        ├── app/                       <- App Router pages
        ├── components/                <- shadcn primitives + SMPL components
        ├── lib/                       <- db client, validations, utils
        └── public/                    <- symlink or copy of ../public/
```

The static site stays the canonical public face until `app-v2/` reaches parity. Then we cut over and retire the .html files.

---

## Migration phases

### Phase 1 — Scaffold (this session)
- `app-v2/package.json` with the exact deps LetsText uses
- `app-v2/next.config.mjs` mirrored from LetsText
- `app-v2/tsconfig.json` + `app-v2/tailwind.config.ts` + `postcss.config.mjs`
- `app-v2/components.json` (shadcn)
- `app-v2/prisma/schema.prisma` with our 4 models
- `app-v2/.env.example`
- `app-v2/app/layout.tsx` (Inter + DM Serif fonts, dark theme)
- `app-v2/app/globals.css` (Tailwind base + SMPL CSS variables)
- `app-v2/app/page.tsx` (home placeholder)
- `app-v2/app/contact/` (page + client form with rhf + zod)
- `app-v2/app/api/inquiry/route.ts` (POST handler)
- `app-v2/lib/db.ts` + `app-v2/lib/validations.ts`
- `app-v2/README.md`
- `app-v2/.gitignore`

### Phase 2 — Page parity
Port each static page to a Next.js route — `app/about/page.tsx`, `app/what/page.tsx`, `app/how/page.tsx`, `app/where/page.tsx`, `app/shows/page.tsx`, `app/careers/page.tsx`, `app/privacy/page.tsx`, `app/terms/page.tsx`. Shared layout components: `<Navbar />`, `<Footer />`, `<HeroVideoSlider />`, `<UsCoverageMap />` (using react-simple-maps), `<ShowsGrid />` (with filter chips).

### Phase 3 — Data wiring
- `/api/inquiry` writes to `Inquiry` table.
- `/api/application` writes to `Application` table.
- Admin dashboard at `/admin` (auth-gated) to list + manage submissions.

### Phase 4 — Animation port
The LetsText "Digital Loom" intro becomes a `<DigitalLoomIntro />` client component using the same canvas pattern (lifted from `script.js`). Page transitions use `framer-motion`'s `<AnimatePresence />` for route changes.

### Phase 5 — Cutover
- Run static site + Next.js side-by-side on the VPS via different paths or different ports.
- A/B test inbound traffic for 1 week.
- Cut DNS over when Next.js parity is confirmed.
- Archive the .html files into `/_legacy/`.

---

## Why not just keep the static site?

The static site is fast, simple, owned, and currently works. But:

1. **Forms need a server.** Estimate inquiries, careers applications, newsletter — these all need persistence. Without a backend they go to `mailto:` or a third party.
2. **Show portfolio needs a CMS.** Manually editing 16+ show cards in `shows.html` doesn't scale. A `Show` model + `/admin/shows` UI does.
3. **Shared design system.** LetsText already has 50+ shadcn primitives in their component library — we'd benefit from the same vocabulary across the operator's product portfolio.
4. **Operator standing order:** "all logic, coding language, database setup like LetsText." Honor that.

---

## What stays the same

- **Brand pack** (`BRANDING/`) — used as-is.
- **Marketing docs** (`MARKETING/`) — used as-is.
- **Public images + videos** (`public/`) — copied or symlinked into `app-v2/public/`.
- **Hosting plan** (`HOSTING.md`) — Path B VPS still works, Caddy now proxies to `next start` instead of static files.
- **Color palette + typography** — exact same tokens, expressed in Tailwind config + CSS variables.
- **Self-host doctrine** — NOT Vercel, NOT Railway. Caddy in front of `next start` on a Hetzner droplet.
