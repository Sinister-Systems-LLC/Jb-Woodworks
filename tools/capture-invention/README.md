# capture-invention

One-shot invention capture. Operator types a slug and a one-line summary; a stub markdown file is created in `D:\Sinister Sanctum\inventions\` matching the existing `_template.md` shape.

## What it does

Prompts for:

1. **Slug** — short kebab-case identifier (becomes the filename).
2. **Summary** — one-line description of the idea.

Writes `D:\Sinister Sanctum\inventions\<slug>.md` populated from the invention template, with the date and summary pre-filled. The operator can then expand the stub later or promote it to a full tool registration under `D:\Sinister Sanctum\tools\`.

The goal is friction-free idea capture: the moment an invention shows up, it lands on disk in a known place with a known shape.

## How to invoke (operator-facing)

Double-click the desktop shortcut:

```
C:\Users\Zonia\Desktop\Capture-Invention.bat
```

The .bat shells into the PowerShell entry point, prompts the operator, and writes the stub.

## Implementation files (absolute paths)

- `D:\Sinister Sanctum\automations\capture-invention.ps1`
- `C:\Users\Zonia\Desktop\Capture-Invention.bat`
- `D:\Sinister Sanctum\inventions\_template.md` (consumed at runtime)
- `D:\Sinister Sanctum\inventions\README.md` (operator reference)

## Dependencies

- Windows PowerShell 5.1+
- Write access to `D:\Sinister Sanctum\inventions\`.

## Lane

master / Sanctum orchestration

## Captured

2026-05-19

## Status

shipped

## Linked-inventions

- (this tool is the entry point that creates them — see `D:\Sinister Sanctum\inventions\` for the growing catalog)

## Changelog

- **2026-05-19** — Initial registration. Slug + summary prompt, template-based stub generation, desktop .bat wired up.
