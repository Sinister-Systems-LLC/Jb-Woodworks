# CLAUDE.md - jb-woodworks

> **Author:** RKOJ-ELENO :: 2026-05-23

## Project

Public marketing website for JB Woodworks (custom-woodworking shop in Orlando, FL).
**Stack:** Next.js 15 + Tailwind + framer-motion + Prisma + Postgres + Resend
(mirrors LetsText). Deployed on Railway, never Vercel.

## Identity

- Slug: `jb-woodworks`
- Display: `Jb Woodworks`
- Accent: purple (operator standing order)
- Branch: `agent/jb-woodworks/<short-topic>`
- PROGRESS: `D:\Sinister Sanctum\_shared-memory\PROGRESS\jb-woodworks.md`
- Heartbeat fallback: `_shared-memory/heartbeats/jb-woodworks.json`
- Desktop junction: `C:\Users\Zonia\Desktop\JB-Woodworks` -> this folder

## Hard rules

- Author every new `.ts` / `.tsx` / `.md` / `.css` / `.bat` with `Author: RKOJ-ELENO :: <date>`.
- Never edit shared Sanctum infra (`~/.claude/.mcp.json`, etc).
- Never push to `main`; per-agent branch only.
- Brand identity comes from the canonical v1 site (gold #c9a84c + black #080808, DM Serif Display + Inter, text wordmark). Do not invent.
- All content data lives in `lib/content/*.json`. Real socials, real phone (407) 561-1453, real email jbwoodworks8@gmail.com. Do not fabricate.

## Run

```bash
bats\jb-install.bat   # first-time setup
bats\jb-dev.bat       # http://127.0.0.1:3000
```

## Add a service / portfolio item / FAQ entry

Edit the matching JSON in `lib/content/`. TypeScript types in `lib/content/index.ts` keep them in sync.

## Media

Re-run `npm run media:optimize` after dropping new MP4s into `Jah Images/`. Re-run `npm run media:favicons` after changing the wordmark.

## DB

Prisma schema lives at `prisma/schema.prisma`. Single model `ContactInquiry` for form submissions. `npm run db:push` to sync schema after edits.
