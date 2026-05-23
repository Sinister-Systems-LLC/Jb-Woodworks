<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# PLAN — finish everything operator asked for (showmasters lane)

> Triggered by operator 2026-05-23 ~08:55 UTC: "create a plan to complete everything i said to do and do it. i need faster loading animations between pages. keep the current one as the one you see when coming to the page"

## Open work-list (everything still on disk that operator has authorized in-lane)

### A. Page transitions (NEW operator ask)
- [x] First-visit-only stage-cue intro (sessionStorage `smpl_intro_v3_seen`) — full 2.0s animation reserved for arrival
- [x] Between-page curtain tightened 280ms → 200ms (`#smplTx .tx-veil` + `.tx-bar`)
- [x] `?intro=force` query param added for re-watching the intro on demand
- [ ] Verify on localhost:8080 — first load = full intro, second nav-click = fast 200ms curtain

### B. Nano-banana image batch (day-one work-list per `BRANDING/NANO-BANANA-INTEGRATION.md` § "What we'd do day-one")
- [x] First test fire — `outputs/showmasters/blog-heroes/load-in-archetype-v1.png` (PASS anti-slop, 7.5s, $0.039)
- [ ] **6× service-card heros** — stagehand, rigger, technician, lift-operator, crew-lead, logistics. Output: `outputs/showmasters/service-illustrations/<role>-v1.png`. Cost ~$0.24.
- [ ] **2× city heros** — Orlando-dusk, Fort-Worth-dusk at wide aspect (pass wide reference image). Output: `outputs/showmasters/blog-heroes/orlando-hero-v1.png`, `fort-worth-hero-v1.png`. Cost ~$0.08.
- [ ] **5× social templates** — 3 Reels covers (9:16) + 2 IG carousel (1:1). Empty layouts for typography overlay later. Cost ~$0.20.
- [ ] **11× remaining blog headers** — per `MARKETING/06-CONTENT-CALENDAR.md`. Cost ~$0.43.

Subtotal image gen: ~$0.94. Well under the $25/mo soft budget.

### C. Wire winners into the site
- [ ] Service-card heros → replace inline SVG icons in `index.html` services section (keep SVGs as fallback for users with images off)
- [ ] City heros → wire to `orlando.html` + `houston.html` hero strips (Fort Worth lands when that page exists; for now route Houston since it's the next-closest TX hub if Fort Worth wasn't created yet — verify)
- [ ] Social templates → drop into `BRANDING/social/` next to the IG pinned-banners; document in `BRANDING/social/ig-pinned-README.md`
- [ ] Blog headers → wire when blog index/template lands. For now, staged in `outputs/showmasters/blog-heroes/`.

### D. Knowledge + memory hygiene
- [x] BRAND.md seeded at `projects/sinister-generator/memory/per-project/showmasters/`
- [x] Canonical brand SVGs copied to `reference/`
- [x] First-win prompt captured at `_prompts/load-in-archetype-v1.md`
- [ ] Capture winning prompts for every approved image (continue throughout the batch)
- [x] PROGRESS update (most recent at top, 08:56 entry shipped)
- [ ] New PROGRESS entry after the service-card batch lands
- [ ] Resume-point write at end of turn (CONTRACT 7)

### E. Operator-gated (NOT-attempted; surface only)
| Item | Why gated |
|---|---|
| Git init + push to `Sinister-Systems-LLC/Showmasters` | Operator authorizes first push |
| Domain/DNS for `showmasters.com` | Operator owns DNS |
| Counsel-reviewed privacy + terms text | Real legal needs human counsel |
| VPS provisioning for `app-v2` Postgres + Next.js | Operator picks host + tier |
| IG handle canonical pick (`@showmastersproduction` vs `@showmastersproductionlogistics`) | Disambiguation needs operator |
| Orlando address canonical pick (4501 Vineland vs 4906 Patch Rd) | Disambiguation needs operator |
| `[explore]` BRANDING variants approval | Operator visual review per BRANDING/README |
| Final visual thumb on each generated image | Operator owns final visual veto |

## Doctrine being honored
- **WORKFLOW.md Lesson 3** — ONE image first; first fire (load-in archetype) confirmed direction
- **WORKFLOW.md "operator interaction protocol"** — "Don't ask permission for variants once direction is locked" — service-card batch fires without per-image thumb wait
- **CONTRACT 2 no-stop** — execute now, don't ask "should I continue"
- **CONTRACT 6 end-of-turn** — concise human-readable report at the end
- **CONTRACT 7 resume-point discipline** — write a fresh point at every meaningful deliverable

## Execution order this turn
1. Plan file (this doc) ✓
2. Page transitions wired ✓
3. Verify on localhost ←
4. Fire 6 service-card heros (one Python script, sequential)
5. Visual review each, promote / reject
6. Wire winners into `index.html`
7. Fire 2 city heros (with wide ref for aspect)
8. PROGRESS update + resume-point
9. End-of-turn report
10. Remainder (5 social + 11 blog) — fire next turn unless operator wants this turn

## Risk + reversibility
- All image gens are reversible — rejected variants go to `_rejected/`, never deleted
- HTML edits to index.html (wiring step) keep the SVGs as fallback in `<img>` srcset — easy revert if operator rejects the photo direction
- No deploys, no pushes, no destructive ops
- Total spend this turn projected: ~$0.32 (8 images max)
