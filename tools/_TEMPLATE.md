# <Tool name>

Short one-line description of what this tool is.

## What it does

A paragraph (or short bulleted list) describing the tool's purpose, the problem it solves, and who/what invokes it. Write this for an operator who has never seen the tool before.

## How to invoke (operator-facing)

The exact command, shortcut, .bat path, or UI step the operator uses. Include any required arguments, env vars, or prerequisites.

```
<command or path here>
```

## Implementation files (absolute paths)

- `D:\path\to\primary\entrypoint.ext`
- `D:\path\to\support\file.ext`
- `D:\path\to\config\or\template.json`

## Dependencies

- Runtime (PowerShell 5+ / Python 3.x / Node / etc.)
- Third-party packages (FastAPI, pywebview, etc.)
- External services (none / Anthropic API / OAuth tokens / etc.)
- Other Sanctum tools or skills this depends on

## Lane

Which lane owns this tool (e.g. master / Sanctum orchestration, per-bot lane name, project lane name).

## Captured

YYYY-MM-DD — date this card was first written.

## Status

One of: `drafting` | `shipped` | `deprecated` | `archived`.

## Linked-inventions

Markdown links to any files under `D:\Sinister Sanctum\inventions\` that seeded or evolved this tool. Use absolute paths.

- `D:\Sinister Sanctum\inventions\<slug>.md`

## Changelog

Append-only. Newest entries on top.

- **YYYY-MM-DD** — Initial registration. Status: shipped.
