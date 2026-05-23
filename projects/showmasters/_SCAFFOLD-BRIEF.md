# Showmasters - SCAFFOLD BRIEF

**Slug:** showmasters
**Captured:** 2026-05-23 01:56
**Origin:** Start-Sinister-Session.bat -> G) guided new project scaffold

## CANONICAL PROJECT LOCATION

> **`C:\Users\Zonia\Desktop\Showmasters Site\`** is the main project folder (operator decision 2026-05-23). All site source + MARKETING/ + BRANDING/ live there. This Sanctum directory only holds this brief + agent-lane metadata. Do NOT fragment work between the two paths.

## Goal

Public marketing website for **Show Masters Production Logistics (SMPL)** — live event crewing company, two hubs (Orlando + Fort Worth), 33-state experience, since 2002. Site is static HTML/CSS/JS (no framework, self-hosted, NOT on Vercel). Includes a full MARKETING/ playbook + BRANDING/ asset pack.

## Stack

- Language: python
- GitHub repo (optional): Sinister-Systems-LLC/Showmasters

## Classes / files to scaffold

(Claude picks based on the language + description)

## Acceptance

- Folder under D:\Sinister Sanctum\projects\showmasters\ has an initial source tree
- README.md, CLAUDE.md, SESSION-START.md, .gitignore present
- Source files compile / import cleanly (no runtime needed yet)
- A one-paragraph summary of what was created lives at the bottom of this file

## Out-of-scope

- Real implementation logic (this is just scaffolding)
- CI / Docker / cloud deploys (deferred)
- Tests beyond a smoke check (deferred)

## Status

scaffolded (2026-05-23) — pre-launch, content/legal review pending

## Built (acceptance summary, 2026-05-23)

Public marketing site for Show Masters Production Logistics (SMPL) lives at `C:\Users\Zonia\Desktop\Showmasters Site\` per operator's 2026-05-23 decision (canonical location: Desktop). Self-hosted static HTML/CSS/JS — no framework, no build step, NOT Vercel. **9 HTML pages** (index, about, careers, contact, how, what, where, privacy stub, terms stub) sharing one `style.css` (18.5 KB) + one `script.js` (7 KB) for the mobile menu + scroll behaviors. **Branding pack at `BRANDING/`** has 24 SVGs across 5 categories (logos, marks, print, social, animated) + README. **Public assets at `public/`** include 9 image SVGs (favicon, og-card, 5 logo variants, 2 pfp variants) + 6 hero MP4 videos (drummer, crowd hands, color spots, flashing lights, music stage, stage light). **SEO + structured data**: sitemap.xml, robots.txt, LocalBusiness JSON-LD on the homepage with the Orlando + Fort Worth office locations. **MARKETING/** folder holds the 4-doc playbook (00-START-HERE, 01-MARKETING-PLAN, 02-SEO-STRATEGY, 03-GMB-RANKING) for the operator's launch campaign. All footer links resolve clean — privacy.html + terms.html are stubs with `noindex` meta + explicit "replace with counsel-reviewed language before launch" notes. The Site folder is NOT yet initialized as a git repo (operator gate). Push to `Sinister-Systems-LLC/Showmasters` GitHub repo is the next pending operator click.