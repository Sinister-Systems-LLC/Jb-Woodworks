<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# app-v2 — Showmasters Next.js

This is the Next.js 15 + React 19 + Prisma + Postgres rebuild of the static Showmasters site. Stack aligned with LetsText 2.0 dashboard-local. See [`../STACK.md`](../STACK.md) for the full alignment doc.

The static `.html` site one level up stays live until v2 reaches parity.

## Stack snapshot

| Layer | Tech |
|---|---|
| Runtime | Node 22+ |
| Framework | Next.js 15.5 (App Router, Turbopack dev) |
| Language | TypeScript 5 strict |
| UI runtime | React 19.2 |
| Styling | Tailwind 4.1 + tailwindcss-animate + CSS variables |
| Components | shadcn/ui ("new-york") + Radix primitives |
| Forms | react-hook-form 7 + zod 3.25 |
| Data | Prisma 5 + Postgres |
| Server state | @tanstack/react-query 5 |
| Motion | framer-motion 12 |
| Maps | react-simple-maps 3 + topojson-client 3 |
| Icons | Custom SVG in `components/icons/` (lucide-react installed but doctrine-fenced) |
| Tests | Vitest 2 |

## First-time setup

```bash
cd app-v2
cp .env.example .env.local
# Edit .env.local — set DATABASE_URL to your local Postgres
pnpm install     # or npm install / yarn / bun
pnpm db:generate # generate the Prisma client
pnpm db:push     # push the schema to your Postgres
pnpm dev         # http://localhost:5050
```

Postgres is required. For local dev:

```bash
# Mac / Linux
brew install postgresql && brew services start postgresql
createdb showmasters

# Windows (or any platform) — Docker
docker run -d --name smpl-pg -e POSTGRES_PASSWORD=devsecret -p 5432:5432 -e POSTGRES_DB=showmasters postgres:16
# Then in .env.local:
# DATABASE_URL="postgresql://postgres:devsecret@localhost:5432/showmasters?schema=public"
```

## Folder map

```
app-v2/
  package.json          deps — mirrors LetsText 2.0 dashboard-local
  next.config.mjs       headers + image config + Radix tree-shaking
  tsconfig.json
  tailwind.config.ts    SMPL brand tokens
  postcss.config.mjs
  components.json       shadcn (new-york)
  .env.example          copy → .env.local

  prisma/
    schema.prisma       Inquiry · Application · NewsletterSub · Show

  app/
    layout.tsx          fonts + metadata + html shell
    globals.css         Tailwind 4 entry + brand vars
    page.tsx            home (scaffold placeholder; full port in Phase 2)
    contact/
      page.tsx          server shell
      contact-form.tsx  client rhf + zod form
    api/
      inquiry/route.ts        POST → Inquiry row
      application/route.ts    POST → Application row

  components/
    ui/                 shadcn primitives (added via `pnpm dlx shadcn@latest add ...`)
    icons/              custom SVG icons (no lucide-react)
    site/               SMPL site components (Navbar, Footer, HeroVideoSlider, etc. — Phase 2)

  lib/
    db.ts               Prisma client singleton
    validations.ts      zod schemas (shared client + server)
    utils.ts            cn(), hashIp()
```

## Adding shadcn components

```bash
pnpm dlx shadcn@latest add button input label textarea card dialog
```

Components land in `components/ui/` and use the tokens from `tailwind.config.ts`.

## Database migrations

```bash
# After editing prisma/schema.prisma:
pnpm db:migrate           # creates a migration + applies it
pnpm db:generate          # regen the client
```

In production, on the VPS:

```bash
DATABASE_URL=... pnpm prisma migrate deploy
DATABASE_URL=... pnpm db:generate
```

## Deploy (mirrors HOSTING.md Path B)

```bash
pnpm build
DATABASE_URL=... NEXT_PUBLIC_BASE_URL=https://showmasters.com pnpm start
# bind to 0.0.0.0:5050, then Caddy reverse-proxies https://showmasters.com → :5050
```

Caddyfile addition:

```
showmasters.com, www.showmasters.com {
    reverse_proxy localhost:5050
    encode zstd gzip

    @www host www.showmasters.com
    redir @www https://showmasters.com{uri} 301

    log { output file /var/log/caddy/showmasters.log }
}
```

No Vercel. No Railway. Just Node + Postgres + Caddy on the droplet.

## Doctrine

- **Custom icons only.** No `lucide-react` imports outside `components/icons/`. Same rule LetsText uses.
- **No emojis.** Anywhere. UI, copy, commits.
- **No AI slop.** Every string is hand-written.
- **Author lines.** Every new `.ts` / `.tsx` / `.css` carries `Author: RKOJ-ELENO :: <date>`.
- **All forms validated with zod** on both client and server.
- **Self-host doctrine.** No platform-specific deploy code.

## Phase 2 work — what's still to port

Existing static-site pages that need Next.js equivalents:

- [ ] `/` (home) — hero video slider + trust strip + services preview + how preview + testimonial + locations + estimate form
- [ ] `/what` — 12 service categories + 8 event types
- [ ] `/how` — 4-step process + "what's baked in" FAQ
- [ ] `/where` — US coverage map (react-simple-maps), regional city cards
- [ ] `/shows` — DB-backed portfolio (replaces hard-coded cards in static `shows.html`) with filter chips
- [ ] `/about` — 3 divisions + values
- [ ] `/careers` — 8 role categories + apply form (port to `/api/application`)
- [ ] `/contact` — DONE in scaffold
- [ ] `/privacy`, `/terms` — counsel-pending stubs
- [ ] `/admin` — auth-gated inquiry + application list

## Why this stack

Operator standing order, 2026-05-23: *"make sure we are using all logic, coding language, database setup things like that that lets text is using."*

Honored. Every dep version in `package.json` was lifted from LetsText 2.0 `dashboard-local/package.json` with the LetsText-specific ones (Anthropic SDK, OpenAI, three, recharts, react-virtual, gsap) dropped since Showmasters doesn't need them yet. Re-add when use cases land.
