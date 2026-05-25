<!-- Author: RKOJ-ELENO :: 2026-05-23 (jkor->JOKR display rename 2026-05-24) -->
# CLAUDE.md — JOKR

> Project root: `C:\Users\Zonia\Desktop\JOKR\` (image-generation working folder)
> Sanctum harness root: `D:\Sinister Sanctum\`
> Agent slug: `jkor` (kept lowercase for path stability; display name is JOKR)
> Display name: `JOKR`
> Persona: EVE (per `_shared-memory/knowledge/agent-identity-eve.md`)

## What this project is

The **JOKR** brand surface — image-generation working folder for the JOKR identity (purple demon/jester hybrid, small gold crown, mischievous grin, fan of playing cards, sorcerer's wand). Operates as a thin lane on top of `D:\Sinister Sanctum\projects\sinister-generator\` (the application layer) and `D:\Sinister Sanctum\tools\nano-banana\` (the SDK wrapper).

Working tree:
```
C:\Users\Zonia\Desktop\JOKR\
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

Brand-pack canonical doc: `D:\Sinister Sanctum\projects\sinister-generator\memory\per-project\jkor\BRAND.md` (mirrored here for offline edits; folder path kept on `jkor/` for back-compat).

## Cold-start (every spawn)

1. **Read `D:\Sinister Sanctum\CLAUDE.md`** — fleet-wide doctrine.
2. **Read `D:\Sinister Sanctum\SESSION-START\`** in order.
3. **Read `D:\Sinister Sanctum\_shared-memory\DIRECTIVES.md`** + **`WORK-TOWARD.md`**.
4. **Read this folder's `BRAND.md`** — visual identity + style guide.
5. **Read `D:\Sinister Sanctum\projects\sinister-generator\docs\ANTI-SLOP.md`** before generating images.
6. **Read `_shared-memory\knowledge\_INDEX.md`** rows tagged `jkor` / `jokr` / `nano-banana` / `image-generation`.
7. **Grep `D:\Sinister Sanctum\_shared-memory\resume-points\jkor\`** for latest resume-point.

## Standard fleet I/O paths

| What | Where |
|---|---|
| Heartbeat | `D:\Sinister Sanctum\_shared-memory\heartbeats\jkor.json` |
| PROGRESS log | `D:\Sinister Sanctum\_shared-memory\PROGRESS\JOKR.md` |
| Resume-points | `D:\Sinister Sanctum\_shared-memory\resume-points\jkor\<UTC>.json` |
| Inbox | `D:\Sinister Sanctum\_shared-memory\inbox\jkor\` |
| Generation outputs (canonical) | `D:\Sinister Sanctum\projects\sinister-generator\outputs\JOKR\` |
| Generation outputs (local working copy) | `C:\Users\Zonia\Desktop\JOKR\generated\` |
| Sorter dashboard | `http://127.0.0.1:7099/` (watches `C:\Users\Zonia\Desktop\JOKR\`) |

Write a new resume-point:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "D:\Sinister Sanctum\automations\resume-point-write.ps1" -SanctumRoot "D:\Sinister Sanctum" -ProjectKey jkor -AgentName jkor -Mode resume
```

Launch the sorter dashboard:

```bash
cd "D:/Sinister Sanctum/projects/sinister-generator/source"
PYTHONPATH=. nohup python -X utf8 -m sinister_generator.sorter_web --folder "C:/Users/Zonia/Desktop/JOKR" --port 7099 > /tmp/jokr-sorter.log 2>&1 &
```

## Per-agent branch

Work on `agent/jkor/<short-topic>` cut off the latest doctrine HEAD. Push freely per `agent-autonomy-push-and-completion-2026-05-23.md`.

## Image generation quick start

```python
from nano_banana import jokr_image

result = jokr_image(
    prompt="a JOKR banner showing the demon-jester in a smoky neon throne room ...",
    output_path=r"C:\Users\Zonia\Desktop\JOKR\generated\banner-vN.png",
    ref_images=[r"C:\Users\Zonia\Desktop\JOKR\reference\00-base-banner-original.png"],
)
```

`jokr_image` is the brand-locked helper at `tools/nano-banana/nano_banana/api.py` (older callers `jkor_image` kept as a back-compat alias). It auto-enforces the JOKR palette (purple primary, gold accent, dark sidebar bg from `01-color-scheme-command-center.png`) and applies the brand-pack prompt prefix.

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
