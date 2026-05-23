# nano-banana

> **Author:** RKOJ-ELENO :: 2026-05-23

Fleet-wide wrapper around **Gemini 2.5 Flash Image** ("Nano Banana"). Every Sinister agent can call this to generate images — same code path, same brand-lock helpers, same on-disk audit trail.

Operator owns a Gemini Pro account; the key lives in a user env var, never in this repo.

## Install

```powershell
pip install google-genai
[Environment]::SetEnvironmentVariable('GEMINI_API_KEY','<your-key>','User')
```

Restart any open Claude / PowerShell session after setting the env var.

The wrapper also accepts `NANO_BANANA_API_KEY` and `GOOGLE_API_KEY` as fallbacks (precedence: `GEMINI_API_KEY` -> `NANO_BANANA_API_KEY` -> `GOOGLE_API_KEY`).

## Use it from Python

```python
from nano_banana import generate, smpl_image, jbw_image

# Plain
generate(
    prompt="A vintage road case under stage lights",
    output_path="C:/Users/Zonia/Desktop/Showmasters Site/public/img/generated/road-case.png",
)

# Showmasters brand-locked (dark + gold)
smpl_image(
    prompt="Stagehand pushing a road case across a backstage corridor",
    output_path="C:/Users/Zonia/Desktop/Showmasters Site/public/img/generated/stagehand.png",
)

# JB Woodworks brand-locked (gold/black wood)
jbw_image(
    prompt="Close-up of a hand-finished walnut tabletop, raking light revealing grain",
    output_path="C:/Users/Zonia/Desktop/JB-Woodworks/static/img/generated/walnut-grain.png",
)
```

Each call writes `<output>.png` AND `<output>.png.meta.json` (prompt + model + timestamp + elapsed + ref-image count).

## Use it from the shell

```bash
python -m nano_banana \
  --prompt "Stagehand silhouette against a wall of par-can lights" \
  --output ./out.png \
  --brand smpl
```

Flags:

| flag | what |
|---|---|
| `--prompt` | the image prompt (required) |
| `--output` | destination PNG path (required) |
| `--ref <path>` | reference image for style transfer; repeatable |
| `--brand {none,smpl,jbw}` | append a brand-lock style suffix |
| `--model <id>` | override default `gemini-2.5-flash-image` |
| `--no-meta` | skip the `.meta.json` sidecar |

CLI exits `0` on `ok`, `1` on error. Prints JSON with `status / output_path / meta_path / elapsed_seconds / image_bytes / error / text_excerpt`.

## Brand-lock contracts

| Helper | Audience | Style suffix |
|---|---|---|
| `smpl_image()` | Showmasters lane | cinematic stage lighting, deep black bg, gold gradient accent, no text/emojis/logos |
| `jbw_image()` | JB Woodworks lane | premium craftsmanship, hand-finished wood close-up, gold-on-black, photoreal, no text/emojis/faux finishes |

Per Showmasters' `BRANDING/NANO-BANANA-INTEGRATION.md`: never bake text into images (typography stays in SVG), reject hallucinated hands/faces during human review, prefer real photography for any face-shot.

## On-disk audit (every call)

Every generation drops a sidecar:

```
generated/stagehand.png
generated/stagehand.png.meta.json   ← prompt, model, ts, elapsed, byte size, text excerpt
```

`meta.json` lets future agents reproduce or refine without guessing. Commit BOTH files together when you save a generated image into a project repo.

## Smoke test

```cmd
tools\nano-banana\quick_test.bat
```

Writes a single banana into `%TEMP%`. Requires `GEMINI_API_KEY` set.

## Operator action needed

- [ ] Set `GEMINI_API_KEY` user env var (one-time)
- [ ] Restart any active Claude Code / PowerShell sessions so they pick up the new env

Tracked in `_shared-memory/OPERATOR-ACTION-QUEUE.md`.

## See also

- `_shared-memory/knowledge/nano-banana-gemini-image.md` — fleet brain entry
- `C:\Users\Zonia\Desktop\Showmasters Site\BRANDING\NANO-BANANA-INTEGRATION.md` — Showmasters' contract
- `docs/ENV-VARIABLES.md` — `GEMINI_API_KEY` section
