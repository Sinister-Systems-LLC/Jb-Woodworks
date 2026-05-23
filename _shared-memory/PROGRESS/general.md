> **Author:** RKOJ-ELENO :: 2026-05-23

# PROGRESS — general (EVE, ad-hoc lane)

Most-recent at top. The `general` lane has no fixed project scope — it's the operator's default surface for ad-hoc queries, cross-lane routing, and one-off investigations.

---

## 2026-05-23 07:45 — shipped: JKOR banner v9 (PIL composite, on-spec)

Operator restated brief: "use v6 as a base" + the 4 fixes (drop whimsical text, less-loud bg, no neon edge, match panel palette).

v8 (LLM edit-mode): MISSED — model interpreted "reshape to wider aspect" as "embed v6 as a smaller inset inside a larger dark frame with a glow border." Wrong direction.

v9 (PIL composite): NAILED IT. Cropped v6 tight to character+JOKR+runic-circle (320,65,1216,665), pasted onto a 1620x648 dark-purple #1A1729 canvas at left-aligned position, feathered edges (140px right / 40px left / 30px top+bottom) for seamless blend, subtle vertical gradient on the canvas matching Command Center sidebar. Pixel-perfect brand preservation, zero LLM cost.

Codified the operation as `projects/sinister-generator/source/sinister_generator/compose.py::left_aligned_banner()` so future agents can do the same reshape on any project. Also added `erase_region()` for UI artifact removal (cleanest path for download icons / captions).

Lesson added to prompts-that-worked.md: "when the brand is already correct in a base image, finish in PIL — don't re-prompt."

Spend this session ~$0.31 of $10 (v9 was free).

---

## 2026-05-23 07:35 — shipped: Sinister Generator project promoted from tool, JKOR banners v4-v7 + audit doc + operator satellite

Operator's verbatim 07:20Z: "as we work review and audit how i work with image gen and in the sanctum folder lets start working out of a sinister generator project with memory setup all that. that we can use for memory gen with the setup approach so that all our agents can use it to gen images etc."

Operator's verbatim 07:32Z: "then have a satelite folder on my desktop called sinister generator that has a folder for each project we gen images for based on image type, rejected images all that. that i can see the images we make in a quick way from the desktop"

Built `D:\Sinister Sanctum\projects\sinister-generator\` — full project structure with multi-project routing, per-project memory, output organization by image type, audit + workflow docs, project + model config JSON.

Desktop satellite via NTFS junction: `C:\Users\Zonia\Desktop\Sinister Generator\` -> `projects\sinister-generator\outputs\`. Operator browses every project's outputs from desktop with no copy step.

Directory tree (truncated):
```
projects/sinister-generator/
├── README.md
├── source/sinister_generator/{brands,audit}/  (Python package — TBD)
├── config/{projects,models}.json
├── memory/
│   ├── _INDEX.md + prompts-that-{worked,failed}.md
│   └── per-project/{jkor,showmasters,jb-woodworks}/
├── outputs/
│   ├── jkor/{banners,social,thumbs,cutouts,_rejected}/
│   ├── showmasters/{banners,social,blog-heroes,service-illustrations,_rejected}/
│   ├── jb-woodworks/{banners,social,blog-heroes,portfolio-teasers,_rejected}/
│   └── _shared/references/
├── docs/{WORKFLOW,ANTI-SLOP,BRAND-PACK-SPEC}.md
└── _archive/
```

JKOR outputs migrated from `Desktop\JKOR\generated\` to `projects\sinister-generator\outputs\jkor\banners\`. JKOR brand-pack metadata (BRAND.md + reference/ + _prompts/) mirrored to `memory/per-project/jkor/` for fleet-agent use; original kept on Desktop for direct operator access.

Banner cycle this session:
- v1/v2/v3: REJECTED by operator ("i hate all of them"). I over-corrected — read "less loud" as "remove the design language entirely." Lost the cartoony jester face, runic backdrop, JOKR text. Brand-lock style suffix was the root cause: it had `NO runes, NO swirls, NO sparkles` which deleted core JKOR elements.
- v4/v5/v6: Preservation edits of source. Near-clones of the original with the download icon removed. Operator superseded these when they pivoted to the ART/banner.png layout brief.
- v7: First on-target banner. Character preserved, no whimsical caption, no neon edge, calm muted purple bg matching the Command Center palette direction, JOKR text intact. Caveats: aspect came out ~square (Gemini ignores pixel-size instructions), bg slightly more medium-purple than the deep-dark sidebar target. Still — the brief finally landed.

Spend this session: ~$0.27 of $10 ($0.12 on v1/v2/v3 rejected + $0.12 on v4/v5/v6 + $0.04 on v7).

Workflow audit doc at `docs/WORKFLOW.md` codifies 7 lessons:
1. "Use this as a base" = edit mode, not generate mode
2. Brand-lock suffix describes what the brand IS, not enforces a new look
3. One image first, then variants — never burn $0.12 on assumed direction
4. PIL surgical erase > re-generation for UI artifact removal
5. References are positional (image-first for edits)
6. Aspect ratio isn't controllable via pixel-count (use a wide ref image)
7. Cost discipline: operator attention is the real budget, not API spend

Brain entry updated with 3 new anti-patterns (#11/#12/#13). Inbox messages sent to showmasters + jb-woodworks pointing at the new paths.

Open next-step decisions for operator:
- Iterate v7 (force wider aspect via wider ref, deepen bg to match panel exactly)
- Start on other JKOR image types (social, thumbs, cutouts)
- Move to another project's first generation

---

## 2026-05-23 07:15 — shipped: 3 JKOR banners generated (v1/v2/v3)

Operator enabled billing on Cloud project `492031902572` + added $10 credit. Three JKOR banners generated via `gemini-2.5-flash-image` (Nano Banana GA):

- `banner-v1.png` — 906 KB, 10.08s — hero portrait, character centered, cards + wand visible, "sorcerer prince" tone
- `banner-v2.png` — 667 KB, 10.47s — most cinematic, circular purple rim-light halo behind head, three-quarter body
- `banner-v3.png` — 1.13 MB, 10.15s — true wide aspect, action shot mid-card-throw, motion trail, closest to source's playful jester feel

All three pass the JKOR brand-lock (no runes/swirls/UI artifacts/baked-in text/download icons, calm dark backdrop with Sanctum-purple glow only where it belongs).

Total spend ≈ $0.12 of $10. Each PNG paired with a `.meta.json` sidecar (prompt + model + ts + elapsed + ref count) for reproducibility.

Surfaced 4 next-step options to operator: iterate a winner / lock aspect ratio / other JKOR assets (pfp, social card, cutout) / move to another project (Showmasters or JB Woodworks).

Brain entry updated with 2 new anti-patterns (#9 free-tier-doesn't-cover-image-gen, #10 don't-use-preview-suffix-after-GA).

---

## 2026-05-23 07:00 — shipped: JKOR brand pack scaffolded at `C:\Users\Zonia\Desktop\JKOR\`

Operator dropped a screenshot of the existing JOKR banner (purple demon-jester w/ crown, cards fan, sorcerer wand, busy lavender-runic bg, JOKR text, download icon bottom-right) + a Sinister Command Center dashboard for color reference. Said: "make jkor folder on desktop. use this as a base. make the background less loud remove download button from bottom right. make the color scheme fit this look perfectly".

Built the brand folder:
```
C:\Users\Zonia\Desktop\JKOR\
├── BRAND.md                                              — full spec + palette + anti-slop
├── generate-banner.bat                                   — one-click v1 generation
├── reference\00-base-banner-original.png                 — operator's source
├── reference\01-color-scheme-command-center.png          — Sinister Command Center palette ref
├── _prompts\banner-v1.txt                                — exact prompt + flags (reproducibility)
└── generated\                                            — output lands here
```

Added `jkor_image()` brand-lock helper to `tools/nano-banana/nano_banana/api.py` (v0.1.0 → v0.2.0) — auto-appends a locked style suffix that enforces deep-near-black background (#0A0B1E), subtle Sanctum-purple glow (#7A3DD4 → #4B1F8B), and explicit NO-list: no runes, no swirls, no sparkles, no UI chrome, no download icons, no text, no emojis. CLI `--brand jkor` flag works.

Installed the wrapper editable (`pip install -e tools/nano-banana`) so `python -m nano_banana` resolves from any cwd — first call had failed with `No module named nano_banana` (the package was on disk but not site-package-visible). Fixed.

Banner v1 generation attempted, blocked on `GEMINI_API_KEY` unset. Wrapper raised the clean error with the exact setx command. Once operator sets the key + restarts this session (or double-clicks the .bat), one command produces `generated/banner-v1.png` + meta sidecar.

The character carries over from the operator's source banner (passed as a `--ref` so the model uses it for style transfer). The Command Center screenshot is also passed as `--ref` to lock the calm-dark palette.

---

## 2026-05-23 06:55 — shipped: Nano Banana wired fleet-wide (`tools/nano-banana/`)

Operator: "i have a gemini pro account with nano banna features i want you to install nano banna and prepare for image generation that we are about to do. tell jb woodworks and show masters agents that we now have nano banaa support for things and that all agents can now use this. note in memory and let me know when you are ready to get to work".

Built `tools/nano-banana/` — fleet-wide wrapper around Gemini 2.5 Flash Image via the `google-genai` SDK. Three public callables: `generate()` (base), `smpl_image()` (Showmasters dark+gold brand-lock), `jbw_image()` (JB Woodworks gold/black photoreal). Each call writes the PNG + a sidecar `.meta.json` (prompt + model + ts + elapsed + byte size). CLI mirrors the API (`python -m nano_banana --prompt … --output … --brand smpl|jbw`).

Env-var resolution: `GEMINI_API_KEY` → `NANO_BANANA_API_KEY` (Showmasters contract alias) → `GOOGLE_API_KEY`. Wrapper raises a clear `RuntimeError` with the setx command if none set.

`pip install google-genai` ran clean — `google-genai 2.6.0` + transitive `tenacity 9.1.4` and `google-auth 2.27.0 → 2.53.0` upgrade. Module imports + CLI `--help` smoke-tested. Live API call deferred until operator sets the key.

Showmasters' explicit contract honored verbatim: `BRANDING/NANO-BANANA-INTEGRATION.md` listed dark+gold style, ref-image style transfer, on-disk meta sidecar, local-fallback pattern (commit generated assets, never live-fetch on render), anti-slop visual review rules. All wired through.

Files written:
- `tools/nano-banana/{nano_banana/{__init__,api,cli,__main__}.py, README.md, AUTHOR.md, .env.example, requirements.txt, pyproject.toml, quick_test.bat}`
- `_shared-memory/knowledge/nano-banana-gemini-image.md` (brain entry, status `workaround` until key lands)
- `_shared-memory/inbox/showmasters/2026-05-23T0655Z-from-general-nano-banana-ready.json`
- `_shared-memory/inbox/jb-woodworks/2026-05-23T0655Z-from-general-nano-banana-ready.json`
- `tools/_INDEX.md` (new row)
- `docs/ENV-VARIABLES.md` (`GEMINI_API_KEY` section)
- `_shared-memory/OPERATOR-ACTION-QUEUE.md` (🟠 High: set the env var)

Gate: operator sets `GEMINI_API_KEY` user env var, then we can do real generations. Tool is otherwise ready.

Not yet done (intentional):
- No git commit — current branch (`agent/showmasters/scaffold-and-launch`) belongs to the sibling Showmasters lane; per multi-agent branch-contention doctrine I'm not switching branches on the shared working tree mid-session. Surfacing to operator for the commit call.
- No live image generation yet (no key). The first real call will validate the response-parsing path (inline_data → bytes).

---

## 2026-05-23 06:50 — started: cold-start as `general` agent (EVE)

First session under the `general` slug. Branch `agent/showmasters/scaffold-and-launch` was already checked out on cwd (carried over from a sibling Showmasters spawn — flagging not auto-switching, lane discipline).

Read on cold-start:
- `automations/session-contracts.md` (7 contracts; speed = turbo)
- `_shared-memory/DIRECTIVES.md` (canonical 14 + RKOJ-ELENO authorship + EVE persona)
- `_shared-memory/WORK-TOWARD.md` (Yurikey52 gate, PI 0/3, Snap SS03, Panel sync, 5-repo push)
- `_shared-memory/OPERATOR-ACTION-QUEUE.md` (Rust toolchain + `ANTHROPIC_API_KEY` env + Desktop bat parity drift + wayward Forge commit + new GitHub-linkage audit items)
- `_shared-memory/knowledge/_INDEX.md` (107 topics; most-recent: RKOJ introspection cluster v1.6.45-56)
- `_shared-memory/WORKSTATION.md` (full fleet overview)
- `SESSION-START/00-RULES.md` (rule 9 heartbeat + rule 10 Skills Hub)

Heartbeat fallback written to `_shared-memory/heartbeats/general.json` (sinister-bus MCP not loaded in this session — verified by tool-list inspection).

Awaiting first operator query.
