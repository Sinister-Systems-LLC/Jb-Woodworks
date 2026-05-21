# sinister-model

> **Author:** RKOJ-ELENO :: 2026-05-21
> **License:** AGPL-3.0-or-later
> **Status:** v0.1.0
> **Implements:** jcode-full-audit P3 row 26 (model list)

## What it is

Light wrapper that surfaces the model routing rules from `automations/agent-host-routing.md`. Operators can `sinister model list` to see which model handles which task class; `sinister model current --task-class deep-reasoning` to look up a single row.

## CLI

```
sinister model list                                       # all task-class rows
sinister model current --task-class "Deep reasoning"      # one row
sinister model switch --task-class "Search" --primary "agentgrep"  # propose a switch (writes brain entry)
sinister model providers                                   # all providers per agent-host-routing.md
```

## Public API

| Function | Purpose |
|---|---|
| `list_models()` | parse agent-host-routing.md task-class table |
| `current(task_class)` | one row |
| `providers()` | the 11 sinister-login providers |
| `propose_switch(task_class, primary, rationale=None)` | append brain entry suggesting a switch (operator-clicks to adopt) |

## Composes with

- `automations/agent-host-routing.md` — source of truth
- `tools/sinister-login/` — provider list
- `tools/sinister-cli/` — `sinister model <op>`
- `tools/sinister-permissions/` — switch proposals land in OPERATOR-ACTION-QUEUE

## v0.1.0 scope

- ✅ list / current / providers / propose_switch
- 📋 v0.2.0: actual switch applies the change to agent-host-routing.md (currently proposal-only)
