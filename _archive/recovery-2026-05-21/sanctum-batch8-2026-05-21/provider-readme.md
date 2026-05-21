# sinister-provider

> **Author:** RKOJ-ELENO :: 2026-05-21
> **License:** AGPL-3.0-or-later
> **Status:** v0.1.0 (light wrapper)
> **Implements:** jcode-full-audit P2 row 14 (provider list/current/add)

## What it is

Light wrapper around `sinister-login` that exposes the jcode-`provider`-style verbs (list / current / add). Operators who prefer the jcode UX (`jcode provider list`, `jcode provider current`) get the same shape in our umbrella (`sinister provider list`).

## CLI

```
sinister provider list                          # all 11 providers + configured status
sinister provider current                        # most-recently-used (heuristic)
sinister provider add --provider claude --use-env
sinister provider add --provider ollama --endpoint http://127.0.0.1:11434
sinister provider remove --provider gemini
```

Behaviorally equivalent to:

```
sinister login --list
sinister login --use-env --provider claude
sinister login --provider ollama --endpoint http://127.0.0.1:11434
sinister login --logout --provider gemini
```

This tool exists for operator UX parity with jcode CLI conventions. Both invocations write to the same `~/.sinister-login/providers.json` store.

## Composes with

- `tools/sinister-login/` — backend (all calls delegate)
- `tools/sinister-cli/` — `sinister provider <op>` umbrella entry
- `automations/agent-host-routing.md` — provider table source

## v0.1.0 scope

- ✅ list / current / add / remove (delegate to sinister-login)
- ✅ heuristic "current" = most-recently-stored provider
- 📋 v0.2.0: per-call provider-routing override (compose with sinister-model)
