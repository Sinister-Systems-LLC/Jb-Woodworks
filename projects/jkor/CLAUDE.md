<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# CLAUDE.md — JKOR

> Project root: `C:\Users\Zonia\Desktop\JKOR\` (image-generation working folder)
> Sanctum harness root: `D:\Sinister Sanctum\`
> Agent slug: `jkor`
> Display name: `JKOR`
> Persona: EVE (per `_shared-memory/knowledge/agent-identity-eve.md`)

## What this project is

The **JKOR** brand surface — image-generation working folder for the JKOR identity (purple demon/jester hybrid, small gold crown, mischievous grin, fan of playing cards, sorcerer's wand). Operates as a thin lane on top of `D:\Sinister Sanctum\projects\sinister-generator\` (the application layer) and `D:\Sinister Sanctum\tools\nano-banana\` (the SDK wrapper).

Working tree:
```
C:\Users\Zonia\Desktop\JKOR\
├── BRAND.md                              ← visual identity + per-prompt style guide
├── generate-banner.bat                   ← one-click first-banner generation
├── reference/
│   ├── 00-base-banner-original.png       ← source the operator shared
│   └── 01-color-scheme-command-center.png ← Sinister Command Center palette ref
├── _prompts/
│   └── banner-v1.txt                     ← exact prompt + flags for reproducibility
└── generated/
    └── (PNGs + .meta.json sidecars land here)
```

Brand-pack canonical doc: `D:\Sinister Sanctum\projects\sinister-generator\memory\per-project\jkor\BRAND.md` (mirrored here for offline edits).

## Cold-start (every spawn)

1. **Read `D:\Sinister Sanctum\CLAUDE.md`** — fleet-wide doctrine.
2. **Read `D:\Sinister Sanctum\SESSION-START\`** in order.
3. **Read `D:\Sinister Sanctum\_shared-memory\DIRECTIVES.md`** + **`WORK-TOWARD.md`**.
4. **Read this folder's `BRAND.md`** — visual identity + style guide.
5. **Read `D:\Sinister Sanctum\projects\sinister-generator\docs\ANTI-SLOP.md`** before generating images.
6. **Read `_shared-memory\knowledge\_INDEX.md`** rows tagged `jkor` / `nano-banana` / `image-generation`.
7. **Grep `D:\Sinister Sanctum\_shared-memory\resume-points\JKOR\`** for latest resume-point.

## Standard fleet I/O paths

| What | Where |
|---|---|
| Heartbeat | `D:\Sinister Sanctum\_shared-memory\heartbeats\jkor.json` |
| PROGRESS log | `D:\Sinister Sanctum\_shared-memory\PROGRESS\JKOR.md` |
| Resume-points | `D:\Sinister Sanctum\_shared-memory\resume-points\JKOR\<UTC>.json` |
| Inbox | `D:\Sinister Sanctum\_shared-memory\inbox\jkor\` |
| Generation outputs (canonical) | `D:\Sinister Sanctum\projects\sinister-generator\outputs\jkor\` |
| Generation outputs (local working copy) | `C:\Users\Zonia\Desktop\JKOR\generated\` |

Write a new resume-point:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "D:\Sinister Sanctum\automations\resume-point-write.ps1" -SanctumRoot "D:\Sinister Sanctum" -ProjectKey jkor -AgentName jkor -Mode resume
```

## Per-agent branch

Work on `agent/jkor/<short-topic>` cut off the latest doctrine HEAD. Push freely per `agent-autonomy-push-and-completion-2026-05-23.md`.

## Image generation quick start

```python
from nano_banana import jkor_image

result = jkor_image(
    prompt="a JKOR banner showing the demon-jester in a smoky neon throne room ...",
    output_path=r"C:\Users\Zonia\Desktop\JKOR\generated\banner-vN.png",
    ref_images=[r"C:\Users\Zonia\Desktop\JKOR\reference\00-base-banner-original.png"],
)
```

`jkor_image` is the brand-locked helper at `tools/nano-banana/nano_banana/api.py`. It auto-enforces the JKOR palette (purple primary, gold accent, dark sidebar bg from `01-color-scheme-command-center.png`) and applies the brand-pack prompt prefix.

For non-brand-locked generation, use `generate(...)` instead.

## Cost discipline + anti-slop

Per `D:\Sinister Sanctum\projects\sinister-generator\docs\ANTI-SLOP.md`:
1. Every generated PNG gets a `.meta.json` sidecar (prompt + seed + model + cost + verdict).
2. Visual review (operator OR cross-agent) before promotion out of `_pending/`.
3. Log every spend to `D:\Sinister Sanctum\projects\sinister-generator\memory\cost-ledger.md`.
4. Never delete failed attempts — move to `generated/_rejected/` for learning.

Operator-gated dependency: Google Cloud billing on project `492031902572` must be enabled for `gemini-2.5-flash-image` to return 200 instead of 429.

## What this project NEVER touches

- `D:\Sinister Sanctum\projects\sinister-generator\source/` (that's owned by the sinister-generator lane)
- `~/.claude/.mcp.json`
- `tools/nano-banana/` source (coordinate via [ASK] inbox)
- Other projects' brand-packs under `sinister-generator/memory/per-project/`

## Composes with

- `D:\Sinister Sanctum\projects\sinister-generator\` (application layer)
- `D:\Sinister Sanctum\tools\nano-banana\` (SDK wrapper)
- `_shared-memory\knowledge\nano-banana-gemini-image.md` (brain entry)
- `BRAND.md` (this folder, visual identity)
