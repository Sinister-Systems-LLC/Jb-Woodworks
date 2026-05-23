# Cross-project: MCP handoff bus

## Problem

7 MCP servers run in isolation, but `sinister-apk`, `sinister-snap`, `sinister-panel`, `sinister-tiktok` clearly share workflow concerns (sign → deploy → audit → harvest). Today: operator manually orchestrates via 5+ tool calls. Each handoff is an opportunity to lose context.

## Proposed solution

A thin meta-MCP `sinister-bus` that exposes:

```python
@tool("bus.handoff")
def handoff(from_server, to_server, payload, context_id):
    """
    Persist a handoff event, then call the destination tool.
    Allows replay of any handoff by context_id.
    """
    record(context_id, from_server, to_server, payload, ts=now())
    return await call_mcp(to_server, payload)

@tool("bus.replay")
def replay(context_id):
    """Replay all handoffs in a context, useful for crash recovery."""
    ...

@tool("bus.list")
def list_contexts(filter=None):
    """List all handoff contexts, optionally filtered."""
    ...
```

State persists at:
```
D:\Sinister\Sinister Skills\01_MEMORY\_bus\<context_id>.json
```

## Example workflow

Operator says "sign + deploy creator APK to P1":
1. `sinister-bus.handoff(from='operator', to='sinister-apk', tool='apk.creator.build')`
2. `sinister-bus.handoff(from='sinister-apk', to='sinister-apk', tool='apk.creator.install', payload={device: 'P1'})`
3. `sinister-bus.handoff(from='sinister-apk', to='sinister-panel', tool='panel.devices.command', payload={device: 'P1', action: 'start_creation'})`

All 3 handoffs land in `01_MEMORY/_bus/<context>.json`. If anything fails, replay from step N.

## Status

Proposed. Highest-leverage cross-project automation. Would need ~200 lines of Python.

## See also

- `04_MCP/_catalog/ALL-TOOLS.md`
- `04_MCP/_catalog/by-keyword/*.md` — find tools by action verb
