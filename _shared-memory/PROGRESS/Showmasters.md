<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# Agent: Showmasters

Append-only progress log. Most recent at top.

---

## 2026-05-23 02:25 — scaffold completed + privacy/terms stubs landed

Picked up on branch `agent/showmasters/scaffold-and-launch` mid-session. Prior session had landed the bulk of the scaffold at `C:\Users\Zonia\Desktop\Showmasters Site\` per operator decision (canonical location: Desktop, NOT `D:\Sinister Sanctum\projects\showmasters\`).

**Current state of `C:\Users\Zonia\Desktop\Showmasters Site\`:**

| Surface | Count | Status |
|---|---:|---|
| HTML pages | 9 | index, about, careers, contact, how, what, where, privacy (new), terms (new) |
| Stylesheets | 1 | `style.css` (18.5 KB) |
| Scripts | 1 | `script.js` (7 KB) |
| Branding SVGs | 24 | 12 logos, 5 marks, 2 print, 4 social, 2 animated, + README |
| Public images | 9 | favicon, og-card, 5 logo variants, 2 pfp variants |
| Hero videos | 6 | crowd, drummer, color spots, flashing, music stage, stage light |
| MARKETING docs | 4 | 00-START-HERE through 03-GMB-RANKING |
| SEO | 3 | sitemap.xml, robots.txt, JSON-LD on index |

**This session's deliverables:**

1. **Asset-path audit** — grepped every `(href|src)=` in all 7 original HTML pages; cross-checked against on-disk files. All local refs resolve EXCEPT two: `/privacy.html` + `/terms.html` referenced from every page's footer.
2. **Stub pages landed** — `privacy.html` + `terms.html` with full nav + page-header + 4-6 placeholder sections each + footer. `<meta name="robots" content="noindex,follow">` so they don't index pre-launch. Each closes with a yellow "Scaffold note" box telling the operator + future counsel to replace with counsel-reviewed language before going live.

**Operator-gated items (surfaced, not acted):**

- Whether the Site folder should be its own git repo (currently NOT initialized as git)
- Push to `Sinister-Systems-LLC/Showmasters` GitHub repo (needs auth + operator OK)
- Domain/DNS for `showmasters.com` (self-hosted per brief, not Vercel)
- Real counsel-reviewed privacy + terms text

**Branch:** `agent/showmasters/scaffold-and-launch` (already on origin)
**Scaffold brief:** `D:\Sinister Sanctum\projects\showmasters\_SCAFFOLD-BRIEF.md` (acceptance summary appended this session)

---
