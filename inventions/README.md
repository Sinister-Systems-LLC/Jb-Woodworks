# inventions/ — idea capture stream

This folder is for **capturing ideas as they arrive** so they don't get lost in a conversation thread or a half-remembered side-comment.

## How it works

- **One markdown file per idea.** Naming: `YYYY-MM-DD-slug.md` (e.g. `2026-05-19-claude-window-manager.md`).
- **Append-only.** Never delete or rewrite an old invention — if status changes, edit the Status section at the bottom of the file.
- **Capture is cheap.** Stub now, flesh out later. The point is the idea doesn't vanish.

## Capture in one click

Double-click **`C:\Users\Zonia\Desktop\Capture-Invention.bat`**:

1. Prompts for a slug (3-5 dash-separated words)
2. Prompts for a one-line summary
3. Creates `inventions/YYYY-MM-DD-<slug>.md` pre-filled from `_template.md`
4. Opens the new file in notepad (window auto-closes after operator saves + closes)

## Manual capture

```bash
cd "D:/Sinister Sanctum/inventions"
cp _template.md "$(date +%Y-%m-%d)-my-idea-slug.md"
# edit
```

## What goes here vs elsewhere

- **inventions/** = ideas, sketches, "wouldn't it be cool if". Pre-implementation.
- **docs/** = current-state docs, integration guides, RFC-style design docs that are being implemented or already shipped.
- **_logs/restore-points/** (in the hub) = post-implementation history (what shipped + when).

When an invention becomes real, it can move/cross-reference to docs/ — but the original stays here as the "first capture" record.

## How master uses this folder

Master agent scans `inventions/` on cold-start (per `01_MEMORY/master/OPERATOR-DIRECTIVES.md`) to learn what the operator has imagined-but-not-built. That keeps cross-session memory durable for future builds.

## Naming examples

- `2026-05-19-claude-window-manager.md`
- `2026-05-19-session-resume-and-scaffold.md`
- `2026-05-22-obsidian-canvas-bot-graph.md`
- `2026-06-01-voice-trigger-for-deploy.md`
