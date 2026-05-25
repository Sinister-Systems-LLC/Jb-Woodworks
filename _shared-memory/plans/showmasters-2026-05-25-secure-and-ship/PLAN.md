<!-- Author: RKOJ-ELENO :: 2026-05-25 -->
# PLAN — Showmasters · secure-and-ship · 2026-05-25

> Spawned: 2026-05-25 ~00:30Z (RESUME mode, showmasters lane, EVE persona)
> Operator brief: *"we are working on the showmasters site i have changes for you. create a plan to complete everything you need to do. make sure its all secure and ready to go"*
> Status: **DRAFT — awaiting operator's "changes for you" before execution**

## Doctrine in force

- **Single-repo push policy 2026-05-25** (CLAUDE.md line 5) — Showmasters is one of 3 carve-out repos; pushes go to Showmasters' OWN GitHub (`Sinister-Systems-LLC/showmasters-site`), NOT Sanctum.
- **Branch convention 2026-05-25** — `agent/showmasters/<short-topic>-<utc-date>`. This plan's branch = `agent/showmasters/p1-secure-and-ship-2026-05-25`.
- **No-bullshit / tested-before-claimed** (2026-05-23) — every `shipped+` claim requires evidence; PROGRESS keeps verified vs in-flight separate.
- **Loop mode + safe-quality-loops** — iterate continuously after each shipped deliverable; respect 12 guardrails.

## Spawn-detect-similar review

No same-project sister agents detected (showmasters lane appears solo). Similar-project lanes: none active that would overlap (panel/freeze/sleight are different domains). **Clean slice — no handoff seams needed.**

## Ground-truth findings (recon done before plan)

### Production posture (LIVE @ `https://showmasters-web-production.up.railway.app`)

✅ **Solid**:
- 35 HTML pages (24 top-level + 11 blog) all return 200
- TTFB 205ms; Cache-Control public 5-min
- Headers landing on prod: HSTS preload (2yr) · CSP · X-Frame SAMEORIGIN · X-Content-Type nosniff · Referrer-Policy strict-origin-when-cross-origin · Permissions-Policy
- Custom 404 routes correctly
- 0 console.log leaks · 0 unsplash refs · 0 unsafe `target="_blank"`
- 24/24 top-level HTML with `<main>` + skip-link · 23/24 with JSON-LD (404 by convention)

⚠️ **Gaps + drift discovered**:

| # | Gap | Severity | Source-of-truth state |
|---|---|---|---|
| 1 | Header source-of-truth invisible to git | **HIGH** | Production has 8 security headers but NO `serve.json` / `_headers` / Caddyfile in working tree. Re-deploy from git could strip them. |
| 2 | CAPTCHA fail-open bug | **HIGH** | `app-v2/app/api/inquiry/route.ts:30-47` silently bypasses Turnstile when client omits `turnstileToken` from POST body. |
| 3 | No honeypot field check | **HIGH** | SECURITY.md §3 specifies honeypot; route.ts has none. |
| 4 | No request-body size limit | MEDIUM | `req.json()` parses arbitrary body — DoS surface on /api/inquiry + /api/application. |
| 5 | No app-layer rate limit | MEDIUM | SECURITY.md §3 acknowledges; not implemented. |
| 6 | CSP `style-src 'unsafe-inline'` | MEDIUM | Only 2 files (`index.html` + `where.html`) have inline `<style>`; extract → tighten CSP. |
| 7 | CSP `script-src 'unsafe-inline'` | MEDIUM | Need full audit for inline event handlers across 35 files; refactor → tighten. |
| 8 | `humans.txt` + `.well-known/security.txt` missing | LOW | PROGRESS claimed commit `b4621cb` shipped them; files absent from working tree. |
| 9 | Email notification TODO | MEDIUM | `route.ts:72` — inquiry+application landings are silent; no SMTP send. |
| 10 | PROGRESS state-drift | LOW | Top entry overstates working-tree state (serve.json, security.txt). |
| 11 | Sitemap canonical = `www.showmasters.com` | LOW | DNS not yet pointed; operator-gated. |

### Working-tree state

- 35 HTML files total (`./` 24 + `./blog/` 11)
- `app-v2/` = Next.js 15 + Prisma + Radix + Turnstile-ready (LetsText 2.0 pattern). Two API routes: `/api/inquiry` + `/api/application`. Not yet deployed.
- `BRANDING/` `MARKETING/` `public/` subtrees intact
- **Branch caution**: cwd's git repo is the Sanctum mono-repo currently on sister-lane branch `agent/sinister-os-mobile/p0-spec-2026-05-24`. Need to cut a proper `agent/showmasters/p1-secure-and-ship-2026-05-25` branch from main (or use `agent-branch-router.ps1`).

## Tracks + execution order

> Each track is **operator-gated** until the operator delivers their "changes for you" and approves sequencing. After approval, execute top-to-bottom — security gaps before cosmetics.

### Track 0 — Branch hygiene (no-op blocker)
- **0.1** Cut `agent/showmasters/p1-secure-and-ship-2026-05-25` via `automations/agent-branch-router.ps1` (or manually off `main`). Verify HEAD is on doctrine baseline before any commit.

### Track 1 — Security hardening (P0 — these are the "make it secure" items)

| Step | Deliverable | Acceptance |
|---|---|---|
| 1.1 | Locate + commit header source-of-truth | Find what Railway uses; add to working tree; `git diff` shows the file; re-deploy preserves headers. |
| 1.2 | Fix CAPTCHA fail-open | When `TURNSTILE_SECRET_KEY` env present, reject 400 if token missing. Smoke: POST without token → 400. POST with bad token → 400. POST with good token → 200. |
| 1.3 | Honeypot field on /api/inquiry + /api/application | zod schema rejects non-empty honeypot; contact-form.tsx adds visually-hidden `<input>`. Smoke: bot-fill honeypot → silent reject. |
| 1.4 | Body-size limit 16 KB | Reject 413 when Content-Length > 16384. Smoke: POST 20 KB body → 413. |
| 1.5 | Rate limit per ipHash | 5/hour/ip on /api/inquiry, 3/hour/ip on /api/application. Returns 429 + Retry-After. Smoke: hammer endpoint → 429 after threshold. |
| 1.6 | Extract inline styles | Move `<style>` blocks from index.html + where.html into style.css (or page-scoped CSS file). 0 `<style>` matches across all HTML. |
| 1.7 | Drop CSP `style-src 'unsafe-inline'` | Update header source; redeploy; verify Inter font still renders + map still styled. |
| 1.8 | Audit + drop CSP `script-src 'unsafe-inline'` | 0 inline event handlers (`on\w+=`); 0 inline `<script>` blocks. Update CSP; redeploy. |

### Track 2 — Forms + notifications (P0 — ship-ready)

| Step | Deliverable | Acceptance |
|---|---|---|
| 2.1 | SMTP notification on /api/inquiry | nodemailer send after `prisma.inquiry.create`; subject + plain-text body; fail-open. Smoke: form submit → row created + email landed at `INQUIRY_NOTIFY_EMAIL`. |
| 2.2 | Same for /api/application | identical pattern; different recipient (HIRING_NOTIFY_EMAIL). |

### Track 3 — Static-asset + a11y hygiene (P1)

| Step | Deliverable | Acceptance |
|---|---|---|
| 3.1 | `humans.txt` + `.well-known/security.txt` | RFC 9116; expires 2027-01-01; lives at site root. Production-curl returns 200 for both. |
| 3.2 | Img-alt audit | `grep -rE '<img(?![^>]*alt=)'` → 0 matches across all 35 HTML. |
| 3.3 | Intro animation localhost verification | Start `python -m http.server 8080`; smoke `?intro=force`; verify 200ms curtain on second nav. Operator visual sign-off required. |

### Track 4 — Pre-launch + operator-gated (operator decides timing)

| Step | Deliverable | Acceptance |
|---|---|---|
| 4.1 | DNS + cert verification (when operator points showmasters.com) | curl apex → HSTS lands; sitemap canonical resolves; no mixed-content. |
| 4.2 | `app-v2/` deploy to VPS or Railway service (when operator picks tier) | Prisma migration runs; `/api/inquiry` POST works in prod env; Turnstile secret set; SMTP creds set. |
| 4.3 | Nano-banana image batch (~$0.94, cost-gated) | 6 service heros + 2 city heros + 5 social templates + 11 blog headers. Per Sinister Generator conservative-balance: cache-first, 6/turn cap, log spend. |
| 4.4 | Marketing-doc drift fix (quantum-sweep iter 103 finding) | Convert `deliverable/03-Marketing.md` to reference doc OR add `<!-- include: ... -->` templating from `site/MARKETING/*`. |

### Track 5 — Hygiene (every turn)

| Step | Deliverable |
|---|---|
| 5.1 | PROGRESS state-drift reconciliation entry (one-time corrective row) |
| 5.2 | Heartbeat + resume-point every shipped deliverable (CONTRACT 7 + Rule 9) |
| 5.3 | Inbox poll each iter; ack 3 already-triaged messages |

## Risk + reversibility

- **Track 1.2-1.5 hot-patches**: low risk; all server-side validation hardening with smoke-test coverage before commit.
- **Track 1.6-1.8 CSP tightening**: medium risk — drops a permissive rule. Mitigation: deploy headers in **report-only mode** first (`Content-Security-Policy-Report-Only`), monitor 48h, then switch to enforce.
- **Track 1.1 header source-of-truth**: HIGH-VALUE; once committed, future regressions visible in PR diff.
- All edits stage on `agent/showmasters/p1-secure-and-ship-2026-05-25`; push to Showmasters repo per single-repo carve-out doctrine; no force-push; no `--no-verify`.
- **No deploys without operator go** — staged in branch + smoke-tested + surfaced before merge to `main` + Railway redeploy.

## Cost ceiling

- Track 1-3: **$0** (server-side code + static-asset edits)
- Track 4.3 image batch: **~$0.94** (operator-explicit go required)
- Track 4.2 VPS: **operator picks tier**

## What I'm waiting on from operator

1. The "changes for you" content — what specifically they want added/changed/removed.
2. Sequencing approval: confirm P0 = Track 1 + Track 2; OK to start Track 1.1 (header SoT hunt) now?
3. Live-prod hotfix vs staged-then-deploy preference: should Track 1.2-1.5 (CAPTCHA + honeypot + size + rate) ship to Railway directly or stage on the branch + operator-review-PR first?
4. Email notification recipient: `INQUIRY_NOTIFY_EMAIL` value (currently env-only).
5. Nano-banana batch: fire this session (cost ~$0.94) or defer.
6. DNS migration timing: any update on `showmasters.com` apex pointer?

## Loop-stop criterion

This plan reaches "queue-empty-or-blocker" when:
- Track 1 + Track 2 fully verified-shipped (smoke evidence in PROGRESS)
- Track 3 verified-shipped
- Track 4 items: each either operator-go-shipped OR operator-defer-acked
- Track 5 hygiene up-to-date

Iterating in /loop mode until that state is reached or operator interrupts with new direction.

---

## File map (where each track touches)

- Track 1.1: TBD (find first); likely `app-v2/next.config.mjs` headers() OR Railway `railway.json` OR a new `serve.json`/`_headers` at root.
- Track 1.2-1.5: `app-v2/app/api/inquiry/route.ts` + `app-v2/app/api/application/route.ts` + `app-v2/lib/validations.ts` + `app-v2/lib/rate-limit.ts` (new).
- Track 1.6: `index.html` + `where.html` + `style.css`.
- Track 1.8: every `*.html` + `script.js`.
- Track 2.1-2.2: `app-v2/lib/email.ts` (new) + both route.ts files + `app-v2/.env.example`.
- Track 3.1: `humans.txt` + `.well-known/security.txt`.
- Track 3.2: every `*.html` with `<img>`.
- Track 3.3: localhost smoke only.
- Track 4: TBD per operator timing.

## Composes with

- Brain entry `single-repo-push-policy-2026-05-25.md` (operator hard-canonical)
- Brain entry `branch-convention-2026-05-25.md`
- Brain entry `no-bullshit-tested-before-claimed-doctrine-2026-05-23.md`
- Brain entry `safe-quality-loops-doctrine-2026-05-24.md`
- `SECURITY.md` § pre-launch checklist
