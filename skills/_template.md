---
name: _template
description: Example skill — copy this to make a new one
allowed-tools: [bash, read_file, write_file]
---
# Active Skill: _template

This skill activates when the operator runs `/_template`. Replace this content
with your skill's instructions for EVE.

## What a skill is

A skill is a markdown file with optional YAML frontmatter. When EVE encounters
`/<skillname>` in a Forge pane, the body below the frontmatter is injected
into the active system prompt as `# Active Skill: <skillname>`.

## Frontmatter fields

- `name` — slug used for `/name`. Defaults to the filename stem.
- `description` — one-line summary shown in `/skill list`.
- `allowed-tools` — optional list constraining the tool surface for this skill.
  EVE should refuse calls outside this list during the skill's run.

## When to write a skill vs. a slash-command

- **Skill** — natural-language instructions for EVE (cold-start checklist,
  rebuild walkthrough, security review template).
- **Slash-command** — deterministic Python in `commands.py` (always behaves
  the same, doesn't need LLM reasoning).
