# JB Woodworks — Complete-Without-Operator Forward Plan

> **Author:** RKOJ-ELENO :: 2026-05-23
> **Agent:** jb-woodworks (EVE on jb-woodworks, purple accent)
> **Branch in worktree at plan-write:** `agent/sinister-sanctum/anti-revert-doctrine-2026-05-23` (foreign — same monorepo, multi-agent worktree)
> **Project root:** `D:\Sinister Sanctum\projects\jb-woodworks\`
> **Stack:** Next.js 15 + Tailwind + framer-motion + Prisma + Postgres + Resend (per `CLAUDE.md`)
> **Version:** v0.3.0 (Next.js 15 pivot — scaffold still untracked in working tree)

## How this plan was built

Synthesized from:

- `_shared-memory/PROGRESS/jb-woodworks.md` — top 8 entries (2026-05-23 evening session: icon audit, Nano Banana backdrops, themed 404, hero in-construction removal, folder self-containment, v0.3.0 scaffold verified live, v0.2.1 favicon set, v0.2.0 canonical brand port).
- Latest resume-point `_shared-memory/resume-points/Jb Woodworks/2026-05-23T054009Z.json` — pre-warm reads = PROGRESS + session-contracts.
- `_shared-memory/inbox/jb-woodworks/*.json` × 3 — Nano Banana ready + Sinister Generator project promoted + canonical-9 narrowed (per-agent branches push freely).
- `_shared-memory/OPERATOR-ACTION-QUEUE.md` — jb-woodworks-tagged rows: none direct, but generator key + billing already live.
- `_shared-memory/knowledge/_INDEX.md` — zero entries tagged jb-woodworks (the brain hasn't been seeded with JB-specific gotchas yet — opportunity later).
- `git log -20` on the sanctum monorepo (rkoj + sanctum lanes recent; no jb-woodworks/* commits yet).
- Direct file inspection of `app/`, `components/`, `lib/`, `public/img/`, `package.json`.

## (a) Already shipped (verified on disk)

| Capability | Evidence | Status |
|---|---|---|
| Next.js 15 + Tailwind + framer-motion scaffold | `package.json` v0.3.0 | ✅ done |
| Canonical brand identity (gold/black/DM Serif/Inter) | layout.tsx + globals.css + Footer | ✅ done |
| 6 real services in lib/content/services.json | (referenced by services-list.tsx) | ✅ done |
| Portfolio JSON + dynamic /portfolio/[slug] | app/portfolio/[slug]/page.tsx | ✅ done |
| Hero 6-slide rotation (in-construction shot removed) | lib/content/hero_media.json | ✅ done |
| 15-symbol custom SVG icon sprite | public/img/icons.svg + components/ui/icon.tsx | ✅ done |
| 3 Nano Banana atmospheric backdrops | public/img/generated/{about-workshop,error-quiet-shop,grain-texture}.png + .meta.json | ✅ done |
| Themed 404 (full-bleed error-quiet-shop bg) | app/not-found.tsx | ✅ done |
| Long brand splash on cold load | components/ui/splash.tsx (sessionStorage-gated, MIN 1400ms, MAX 3500ms, reduced-motion safe) | ✅ done |
| Short route-progress bar on internal nav | components/ui/route-progress.tsx | ✅ done |
| App-router loading skeleton | app/loading.tsx | ✅ done |
| Themed error.tsx + global-error.tsx | both files exist with brand voice | ✅ done |
| Legal coverage parity (privacy / terms / cookies / accessibility + /legal index) | app/legal/{,privacy,terms,cookies,accessibility}/*.tsx + lib/legal.ts | ✅ done |
| Footer wired to all 4 legal pages | components/sections/footer.tsx lines 46-53 | ✅ done |
| Full favicon set (PNG 16/32/48/180/192/512 + ICO + SVG + apple-touch) | public/img/favicon-*.png + manifest | ✅ done |
| Self-contained `public/img/projects/` (no symlink) | (per PROGRESS 05:30 entry) | ✅ done |
| JBW BRAND.md dropped in sinister-generator memory | projects/sinister-generator/memory/per-project/jb-woodworks/BRAND.md | ✅ done |

## (b) In-flight / partial

| Capability | Where it stops | Recovery |
|---|---|---|
| v0.3.0 scaffold git history | Entire app/components/lib tree is untracked in working tree | Need clean worktree for `agent/jb-woodworks/scaffold-and-launch` to commit cleanly without yanking rkoj's branch out from under active rkoj session |
| `lib/db.ts` + Prisma `ContactInquiry` schema | Files exist but the contact form POST still uses FormSubmit per v0.2.0 legacy | Implement `app/api/contact/route.ts` with Resend + Prisma persist (Task #7) |
| Image optimization | Originals served (Pergola 10.8 MB, Boat Dock 4.2 MB) | Switch portfolio cards to `<Image>` + add `preload="metadata"` to non-first hero videos (Task #4) |

## (c) Open + master-actionable (no operator needed)

Priority-ordered:

| # | Task ID | Row | R-class | Effort | Order |
|---|---|---|---|---|---|
| 1 | T#1 | Smoke-test loading/legal/error on dev server | R0 | 10 min | NOW |
| 2 | T#5 | Sitemap lastmod uses file mtime | R0 | 15 min | next |
| 3 | T#4 | Image optimization (`<Image>` + lazy hero) | R0 | 30 min | next |
| 4 | T#6 | Before/After image-comparison slider | R0 | 45 min | medium |
| 5 | T#2 | Commit v0.3.0 scaffold to agent/jb-woodworks/* | R1 | 20 min | medium (worktree-gated) |
| 6 | T#7 | Wire Resend transactional contact-form | R1 | 1 hr | medium (env-gated below) |
| 7 | (new) | Seed `_shared-memory/knowledge/jb-woodworks-*.md` brain entries for the gotchas hit this session (Next.js 15 themeColor deprecation, sessionStorage splash gating, framer-motion + reduced-motion, self-contained `public/img/projects/`) | R0 | 20 min | low-priority |

## (d) Operator-gated rows (with exact one-liners)

| Item | One-liner |
|---|---|
| `RESEND_API_KEY` env var (transactional email) | `[Environment]::SetEnvironmentVariable('RESEND_API_KEY','re_...','User')` then restart shell |
| `DATABASE_URL` env var (Prisma Postgres) | `[Environment]::SetEnvironmentVariable('DATABASE_URL','postgresql://user:pass@host:5432/jbw','User')` |
| Real domain pick | Operator picks; replace placeholder in `lib/site.ts::SITE.url` |
| Railway vs Sanctum self-host | Operator decides; deploy config follows the pick |
| GitHub repo creation `Sinister-Systems-LLC/Jb-Woodworks` | Operator creates the empty repo; agent adds remote + pushes |
| Production media: re-run `npm run media:optimize` after new MP4s land in `Jah Images/` | Operator drops new clips when shop has fresh work to show |

## (e) Reversibility classes (per canonical-11)

- **R0** = pure code edits, no infra. Reversible by git revert. All Task #1, #3, #4, #5, #6 are R0.
- **R1** = local infra touches (git branch creation, worktree creation, env var reads). Task #2, #7 are R1.
- **R2** = remote-visible (push to a per-agent branch on origin). Doctrine allows per-agent push freely.
- **R3** = deploy / merge to main. Operator-gated.
- **R4** = destructive (force-push, schema migrations against prod DB). Operator-gated.

## (f) Recommended ordering + effort estimates

```
Phase A (this turn, R0 only) ~1 hr
  1. Smoke-test loading + legal + error + 404 on dev server     [T#1] ~10 min
  2. Sitemap mtime audit + fix                                  [T#5] ~15 min
  3. Image optimization sweep (next/image + lazy hero)          [T#4] ~30 min
  4. Brain entries for Next.js 15 + splash + reduced-motion     [new] ~15 min

Phase B (next slice, R0-R1) ~2 hr
  5. Before/After image-comparison slider                       [T#6] ~45 min
  6. Worktree creation + scaffold commit                        [T#2] ~30 min
  7. Resend contact form (only if RESEND_API_KEY in env)        [T#7] ~1 hr

Phase C (operator-gated)
  8. Domain pick + Railway/self-host pick
  9. GitHub repo creation + first push
```

## Heartbeat / progress contract

- Heartbeat written each turn to `_shared-memory/heartbeats/jb-woodworks.json` (MCP offline; direct fs fallback).
- Progress appended to `_shared-memory/PROGRESS/jb-woodworks.md` after every deliverable, most-recent at top.
- New resume-point written via `automations/resume-point-write.ps1 -ProjectKey jb-woodworks -AgentName jb-woodworks -Mode resume` after every meaningful deliverable.

## What I am NOT doing (lane discipline)

- Not touching `~/.claude/.mcp.json`.
- Not touching other `projects/<other>/source/` trees.
- Not switching the worktree branch (it would yank rkoj's branch out from under any active rkoj session in this same checkout). The worktree creation in T#2 is the safe path.
- Not pushing to `main`.
- Not picking the operator's domain / deploy target / LICENSE.
