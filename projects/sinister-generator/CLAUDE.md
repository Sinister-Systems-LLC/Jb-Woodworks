<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# CLAUDE.md — Sinister Generator

> Project root: `D:\Sinister Sanctum\projects\sinister-generator\`
> Sanctum harness root: `D:\Sinister Sanctum\` (same drive; this project sits inside Sanctum)
> Agent slug: `sinister-generator`
> Display name: `Sinister Generator`
> Persona: EVE (per `_shared-memory/knowledge/agent-identity-eve.md`)

## What this project is

The Sinister fleet's canonical image-generation application layer. Promoted from `tools/nano-banana/` (which stays as the SDK wrapper) into a full project for multi-project routing, per-project memory, organized outputs, operator desktop satellite, and anti-slop discipline. Read `README.md` for the full overview.

Top-level shape:
- `source/` — future `sinister_generator/` Python package (brands/, audit/)
- `config/projects.json` — image-gen project registry
- `config/models.json` — available models + pricing
- `memory/` — prompts-that-worked / failed + per-project brand packs (jkor, showmasters, jb-woodworks)
- `outputs/` — NTFS-junctioned to `C:\Users\Zonia\Desktop\Sinister Generator\` for operator browsing
- `docs/` — WORKFLOW.md, BRAND-PACK-SPEC.md, ANTI-SLOP.md
- `_archive/` — superseded artifacts

The low-level SDK wrapper still lives at `D:\Sinister Sanctum\tools\nano-banana\`. This project is the **application layer** on top.

## Cold-start (every spawn)

1. **Read `D:\Sinister Sanctum\CLAUDE.md`** for fleet-wide doctrine (EVE persona, RKOJ-ELENO authorship, --dangerously-skip-permissions, lane discipline).
2. **Read `D:\Sinister Sanctum\SESSION-START\`** in order.
3. **Read `D:\Sinister Sanctum\_shared-memory\DIRECTIVES.md`** + **`WORK-TOWARD.md`**.
4. **Read this project's `README.md`** for the application overview.
5. **Read `memory/_INDEX.md`** for prompt history + per-project brand packs.
6. **Read `docs/ANTI-SLOP.md`** before generating images (visual review checklist).
7. **Read `_shared-memory/knowledge/_INDEX.md`** rows tagged `nano-banana`, `image-generation`, or `sinister-generator`.
8. **Heartbeat + PROGRESS + resume-point** per the standard fleet pattern (paths below).

## Standard fleet I/O paths

- Heartbeat: `D:\Sinister Sanctum\_shared-memory\heartbeats\sinister-generator.json`
- PROGRESS: `D:\Sinister Sanctum\_shared-memory\PROGRESS\Sinister Generator.md` (display-name file)
- Resume-points: `D:\Sinister Sanctum\_shared-memory\resume-points\Sinister Generator\<UTC>.json`
- Inbox: `D:\Sinister Sanctum\_shared-memory\inbox\sinister-generator\`
- Write a new resume-point:

  ```powershell
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "D:\Sinister Sanctum\automations\resume-point-write.ps1" -SanctumRoot "D:\Sinister Sanctum" -ProjectKey sinister-generator -AgentName sinister-generator -Mode resume
  ```

## Per-agent branch

`agent/sinister-generator/<short-topic>` cut off the latest doctrine HEAD. Push freely per `agent-autonomy-push-and-completion-2026-05-23.md`. The repo is the Sanctum monorepo — no separate GitHub remote (the project lives under Sanctum's tree).

## Operator-gated dependencies

- `GEMINI_API_KEY` env var must be set (operator confirmed 2026-05-23T07:05Z — see OPERATOR-ACTION-QUEUE.md).
- **Billing on Google Cloud project `492031902572`** must be enabled for image-gen models. Until enabled, `gemini-2.5-flash-image` returns `429 RESOURCE_EXHAUSTED`. This is the only blocker for end-to-end generation. Generation cost is ~$0.039 per image at `gemini-2.5-flash-image`.

## Quick start (any fleet agent)

```python
from nano_banana import jkor_image, smpl_image, jbw_image, generate

result = jkor_image(
    prompt="...",
    output_path=r"D:\Sinister Sanctum\projects\sinister-generator\outputs\jkor\banners\next.png",
    ref_images=[r"...\memory\per-project\jkor\reference\00-base-banner-original.png"],
)
```

Other helpers:
- `smpl_image(...)` — Showmasters brand-locked
- `jbw_image(...)` — JB Woodworks brand-locked
- `generate(...)` — generic, no brand-lock (use for ad-hoc)

## What this project NEVER touches

- `tools/nano-banana/` source (that's the SDK wrapper; coordinate via [ASK] inbox)
- `~/.claude/.mcp.json` (operator-owned)
- Other projects' sources under `D:\Sinister Sanctum\projects\<other>/`
- `_vault/` (operator secrets)

## Anti-slop discipline

Per `docs/ANTI-SLOP.md`: every generated image gets:
1. A `.meta.json` sidecar with prompt + seed + model + cost + verdict
2. Visual review (operator OR cross-agent reviewer) before promotion out of `_pending/`
3. Cost discipline — log every spend to `memory/cost-ledger.md`
4. Reproducibility — never delete failed attempts; move to `_rejected/` for learning

## Composes with

- `tools/nano-banana/` (SDK wrapper this project sits on top of)
- `_shared-memory/knowledge/nano-banana-gemini-image.md` (brain entry)
- `projects/showmasters/` + `projects/jb-woodworks/` + JKOR project (consumers via brand-pack helpers)
- `_shared-memory/PROGRESS/Sinister Generator.md` (will be created on first agent log)
