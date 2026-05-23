# PROGRESS - jb-woodworks

> **Author:** RKOJ-ELENO :: 2026-05-23

## 2026-05-23 05:40 - ship: icon audit (all custom SVG already) + 3 Nano Banana in-theme backdrops wired

**Operator (verbatim 2026-05-23):** *"i need all icons to be custom svg icons
and palces you need to gen in theme ai images with nano banan"*, with a
Showmasters screenshot showing the mixed photo-card + icon-card services grid.

**Icon audit (no work needed):**
- Every icon on the site is already a custom SVG via the sprite at
  `public/img/icons.svg` (15 hand-drawn symbols: dock, deck, table, trim,
  pergola, wrench, arrow-right, phone, mail, pin, menu, instagram, facebook,
  tiktok, twitter).
- Single `Icon` component (`components/ui/icon.tsx`) references symbols via
  `<use href="/img/icons.svg#i-<name>">`. No font icons, no emoji, no image
  icons anywhere in the codebase (grepped `.tsx`, `.ts`, `.css`, `.json` —
  zero hits for unicode emoji ranges).

**Nano Banana imagery (3 atmospheric backdrops, ~$0.12 total):**

Memory file dropped at
`projects/sinister-generator/memory/per-project/jb-woodworks/BRAND.md`
documenting the palette / typography / voice / anti-slop rules + acceptable
subjects for future generations. Generation script:
`projects/sinister-generator/outputs/jb-woodworks/_gen_atmospherics_2026-05-23.py`.

| Image | Used at | Subject | Time | Bytes |
|---|---|---|---|---|
| `about-workshop.png` | About hero (22% opacity backdrop) | Quiet shop, walnut plank on bench, raking window light, hand planes + chisels in shadow | 8.4s | 1.2 MB |
| `error-quiet-shop.png` | 404 page (32% opacity full-bleed backdrop) | Single curled wood shaving on dark floor, gold rim light, lonely | 11.3s | 1.0 MB |
| `grain-texture.png` | Home Process Timeline section (10% screen-blend right-edge accent) | Macro walnut grain, raking warm light, fades to pure black on right | 6.6s | 1.6 MB |

All three respect the operator's anti-slop guardrails (no people, no fake
project photos, atmosphere only). Each PNG has a `.meta.json` sidecar with the
prompt + model + timestamp committed alongside. Copied into the project at
`public/img/generated/` as real files (project is self-contained).

**Themed 404 page:**
- Rewrote `app/not-found.tsx`. Now full-bleed atmospheric backdrop + radial
  vignette + 3-button rescue row (Home / Portfolio / Contact). Returns HTTP 404
  on unmatched routes (verified via `/this-page-does-not-exist` → 404).

**Smoke verified live:**

| Route | Status | Bytes |
|---|---|---|
| `/` | 200 | 109 KB (now with grain-texture accent in Process Timeline section) |
| `/about` | 200 | 69 KB (now with workshop backdrop) |
| `/this-page-does-not-exist` | 404 | 43 KB (themed) |
| `/img/generated/about-workshop.png` | 200 | 1.2 MB |
| `/img/generated/error-quiet-shop.png` | 200 | 1.0 MB |
| `/img/generated/grain-texture.png` | 200 | 1.6 MB |

**Queued (operator asked, working on them next):**
- Task #6 — Loading animations (long on hard refresh + short on nav transition).
- Task #7 — Legal coverage (policies / cookies / terms) parity with
  Showmasters/LetsText.

---

## 2026-05-23 05:30 - ship: hero in-construction shot removed + folder self-contained for push

**Operator interrupts this turn:**

1. Screenshot of hero slide 03/07 ("PERGOLA" static image showing an unfinished
   pergola with construction tools/materials visible). Direction: *"dont use this one"*.
   - Removed `Pergola/IMG_1866.jpg` entry from `lib/content/hero_media.json`.
   - Hero rotation now 6 slides, all videos. No more still-image of in-construction work.

2. *"dont worry about github for now. just make sure we have all we nbeed in
   one folder when we do push to github"*.
   - Audited external dependencies. Found exactly one: the `public/img/projects`
     symlink pointing to `D:\Sinister\old\Coding Random\JB Woodworks\Jah Images\`.
   - Converted to self-contained: deleted the symlink, created real subdirs,
     copied the 14 raw-image files actually referenced from `portfolio.json`
     (~8 MB total: 4 Pergola, 3 Boat Dock, 1 Custom Pool Table, 1 Trex Deck,
     5 Custom Furniture).
   - Removed `public/img/projects/` from `.gitignore` (the files are now real
     project content, intended to be committed when the time comes).
   - Updated `README.md` "Media pipeline" section + the `mediaUrl` comment in
     `lib/content/index.ts` to reflect the real-files model.

**Smoke after both interrupts:**

| Route | Status | Notes |
|---|---|---|
| `/` | 200 | 6-slide hero rotation, no in-construction still |
| `/portfolio` | 200 | listing intact |
| `/portfolio/pergola` | 200 | 4 raw-image gallery items load from new path |
| `/portfolio/custom-pool-tables` | 200 | `is_raw_cover` cover loads from new path |
| `/img/projects/Pergola/IMG_0037.jpg` | 200 | real file, 849 KB |
| `/img/projects/Custom%20Pool%20Table/Resized_1000014068_733961905721315.jpg` | 200 | real file, 575 KB |

**Project folder is now self-contained.** A future `git add . && git push`
will carry everything the deployed site needs - no external symlink dependencies.
The canonical Jah Images store at `D:\Sinister\old\Coding Random\JB Woodworks\`
remains the source-of-truth library for any future portfolio additions.

---

## 2026-05-23 05:25 - resume: v0.3.0 scaffold verified live + themeColor deprecation fixed

Picked up after the Flask -> Next.js 15 pivot (v0.3.0 in `package.json`) that a
prior session executed but did not log here. All scaffold files were untracked
in the working tree on the wrong branch (see "Branch state" below).

**State at pickup:**
- Next.js 15 + Tailwind + framer-motion + Prisma + Postgres + Resend stack
  (mirrors LetsText per project `CLAUDE.md`).
- Flask v0.2.x preserved under `_legacy-flask/` (intact, used as a referenced
  reading material + the source of `media:optimize` / `media:favicons` scripts).
- App-router pages: `/`, `/about`, `/services`, `/portfolio`, `/portfolio/[slug]`,
  `/contact`, `/contact/thanks`, `/api/contact`, `/api/healthz`, `/robots`, `/sitemap`.
- 11 section components (hero with framer-motion slider, marquee, nav, footer,
  services-list, numbers-band, portfolio-feature, portfolio-card,
  portfolio-filter, process-timeline, contact-form) + 2 ui (icon, reveal).
- Content: `lib/content/{services,portfolio,faq,hero_media}.json` + typed
  loaders in `lib/content/index.ts`.
- `public/img/projects` is a symlink to the canonical `D:\Sinister\old\Coding Random\JB Woodworks\Jah Images\` - Next.js serves through it cleanly.
- `public/media/{Boat Dock,Custom Furniture,Deck,Pergola,Trex Deck}/` has the
  optimized H.264 + JPG posters wired from the hero slider (Custom Pool Table
  not in the hero rotation, served from the symlink only).
- Brand identity intact: gold #c9a84c on black #080808, DM Serif Display + Inter,
  italic-emphasis voice, real (407) 561-1453 + jbwoodworks8@gmail.com, real
  social handles, six real services.

**Smoke verified live on `npm run dev` @ http://127.0.0.1:3000:**

| Route | Status | Size | First-hit compile |
|---|---|---|---|
| `/` | 200 | 108 KB | 4.0s |
| `/about` | 200 | 66 KB | 12.3s |
| `/services` | 200 | 75 KB | 9.1s |
| `/portfolio` | 200 | 53 KB | 7.4s |
| `/portfolio/pergola` | 200 | 54 KB | 9.1s |
| `/contact` | 200 | 53 KB | 0.8s |
| `/api/healthz` | 200 | 43 B | 1.4s |
| `/img/favicon-32.png` | 200 | 568 B | (static) |
| `/media/Pergola/IMG_0047.mp4` | 200 | 10.8 MB | (static) |
| `/img/projects/Boat%20Dock/IMG_1605.mp4` | 200 | 4.2 MB | (symlink) |

**Fixed this turn:**
- `app/layout.tsx` - Moved `themeColor: "#080808"` out of `metadata` export
  into a new `viewport: Viewport` export (Next.js 15 deprecation - every route
  was printing the warning on first compile). Also added `width: "device-width"`
  + `initialScale: 1`. Warning is gone on subsequent compiles.

**Branch state (operator decision needed):**
- Worktree at `D:\Sinister Sanctum` is currently checked out on
  `agent/rkoj/complete-without-operator-2026-05-23` (rkoj agent's branch).
- The `agent/jb-woodworks/scaffold-and-launch` branch exists but is stale at
  `df7d37f` (an old rkoj v1.6.74 commit). The Next.js v0.3.0 scaffold has
  never been committed anywhere; it lives only in the working tree as untracked
  files.
- Cannot cleanly commit the scaffold onto `agent/jb-woodworks/scaffold-and-launch`
  without either (a) creating a separate worktree (preferred - leaves rkoj
  undisturbed), or (b) branch-switching here, which would yank rkoj's branch
  out from under the active rkoj session.
- Logged to task #3 for operator review.

**Standing by for:**
- Operator OK on branch placement strategy (worktree vs. switch vs. defer).
- Real domain + Railway/Sanctum-self-host decision (still placeholder per v0.2.0
  notes).
- nano-banana / sinister-generator integration once GEMINI_API_KEY is set
  (inbox notes from 06:55 + 07:35 acknowledged; not blocking).

**Branch:** `agent/jb-woodworks/scaffold-and-launch` (target - not currently checked out)

---

## 2026-05-23 06:45 - ship: v0.2.1 favicon set wired (PNG + ICO + manifest + apple-touch)

Operator screenshot showed the browser falling back to the default globe icon
on jbwoodworks.co. The SVG-only favicon link was not enough for older browsers,
search engines, and iOS. Generated a full set:

- `scripts/make_favicons.py` - Pillow-based generator (no SVG renderer dependency).
  Draws **JB** in Arial Black + gold underline at any size, exports PNG + ICO.
- `static/img/favicon-{16,32,48,180,192,512}.png` + `favicon.ico` (multi-res).
- Refined `static/img/favicon.svg` to use vector paths (not a text element)
  so it renders identically across browsers regardless of installed fonts.
- `static/site.webmanifest` - PWA manifest with theme color `#080808`.
- `base.html` head: 5 favicon link tags + apple-touch-icon + msapplication-TileColor.
- Verified favicon-180.png renders cleanly: white "JB" + gold underline on black.

Regenerate after any wordmark change: `python scripts/make_favicons.py`.

---

## 2026-05-23 06:35 - ship: v0.2.0 canonical-brand port + portfolio + Jah Images live

Operator interrupted the v0.1.0 scaffold with: "make sure all logo and branding
is based on the image these companies already have and does not change them
fully but enhances them in ways." Pivot from fabricated brand to porting the
real canonical JB Woodworks identity from the prior Vercel build, then enhancing.

**Canonical sources found:**
- Old site: `D:\Sinister\old\Coding Random\JB Woodworks\` (Vercel, plain HTML/CSS/JS, FormSubmit contact, 6 services, ~80 photo/video assets in `Jah Images/`).
- Mirror: `C:\Users\Zonia\Desktop\INPO\Things\Coding\JB Woodworks\` (same content).
- Photos: 6 categories (Boat Dock, Custom Furniture, Custom Pool Table, Deck, Pergola, Trex Deck).

**Brand reality (gold/black, not the amber I invented):**
- Palette: `#080808` black, `#c9a84c` gold, `#e2c47a` gold-light + white opacity ramp.
- Type: DM Serif Display (italic = brand voice) + Inter (300-900, wordmark uses 900).
- Wordmark: text-only "JB" Inter 900 with tiny "WOODWORKS" gold letter-spaced below. No monogram, no icon.
- Tagline: "Premium Craftsmanship. Built to Last."
- Service area: Orlando, FL.
- Real contact: (407) 561-1453 / jbwoodworks8@gmail.com.
- Real socials: IG @jb.woodworkss, FB /people/JB-Woodworks/61581118061434, TT @jbwoodworks_, X @jbwoodworks8.
- Real services (6): Docks / Custom Decks / Furniture and Tables / Interior Trim and Millwork / Outdoor Living Spaces / Repairs and Staining.

**Shipped in v0.2.0 (replaces v0.1.0 fabrications):**
- `app.py` - 9 routes incl. dynamic `/portfolio/<slug>`, real site dict, security headers, robots.txt, sitemap.xml.
- `data/portfolio.json` + `hero_media.json` + `faq.json` (replaces fabricated gallery/testimonials).
- Hero video slider with the 7 real Jah Images clips (Pergola, Trex, Boat Dock, Deck, Pool Table). Honors prefers-reduced-motion.
- `static/img/projects/` is a **Windows junction** to `D:\Sinister\old\Coding Random\JB Woodworks\Jah Images\` - photos serve straight from the canonical store, no duplication.
- `static/css/site.css` - rebuilt around the canonical gold/black palette + DM Serif Display + Inter. Sticky nav with scroll-state, hero video slider, services grid, portfolio cards, FAQ grid, footer.
- `static/js/site.js` - hero auto-cycle slider, sticky-nav scroll behavior, mobile hamburger toggle, IntersectionObserver fade-in, ?service= prefill on /contact.
- `static/img/icons.svg` - new 15-symbol sprite matching the real services (dock, deck, table, trim, pergola, wrench) + UI + 4 social marks.
- `branding/` rebuilt: 8 wordmark SVG variants (primary, horizontal, stacked, mono-dark, mono-light, favicon, social-card 1200x630, email-signature) + 2 patterns. MANIFEST.md + BRAND-GUIDELINES.md updated to document "enhanced from canonical v1" status and codify the italic-emphasis brand voice.
- Contact form points at canonical FormSubmit endpoint (`https://formsubmit.co/jbwoodworks8@gmail.com`) - same as the prior build, no server-side handler needed.
- `railway.json` + `DEPLOY.md` retained - the off-Vercel pattern Operator asked for.
- `bats/` retained: jb-dev / jb-prod / jb-kill / jb-restart / jb-install.
- Desktop junction at `C:\Users\Zonia\Desktop\JB-Woodworks` retained - single source of truth, same folder as canonical.

**Live:** Flask dev on `http://127.0.0.1:5000`, background `bf7b507qq`. All 12 smoke checks pass (8 page routes, /robots.txt, /sitemap.xml, real photo JPG, real video MP4).

**Branch:** `agent/jb-woodworks/scaffold-and-launch`

**Standing by for:** nano-banana image-gen integration (operator coordinating from another lane). The brand guidelines doc has a pending section reserved for it; new imagery must respect gold/black palette + italic-tagline voice.

**Operator gates surfaced (not blocking):**
- Real domain pick (currently `jbwoodworks.example` placeholder in schemas).
- Decide Railway vs Sanctum self-host for production.
- Create GitHub repo `Sinister-Systems-LLC/Jb-Woodworks` (does not exist yet) when ready to push.
- Old `vercel.json` exists in the v1 folder - delete after Railway / self-host cuts over.

**Next slice ideas:**
- Before/After image-comparison slider (from v1, applied to dock + pool-table builds).
- Lazy-load + AVIF/WebP for the Jah Images at production (currently serves originals).
- Auto-build sitemap lastmod from data-file mtime instead of "today".
- Sinister tunnel route registration if we go self-host.
- Nano-banana generated hero / blog / project covers once that integration lands.

---

## 2026-05-23 06:15 - ship: v0.1.0 scaffold (superseded by v0.2.0)

Initial scaffold from `_SCAFFOLD-BRIEF.md`. Fabricated services/testimonials/brand
under the wrong assumption that no canonical existed. Replaced wholesale by
v0.2.0 once the canonical Vercel build was located.
