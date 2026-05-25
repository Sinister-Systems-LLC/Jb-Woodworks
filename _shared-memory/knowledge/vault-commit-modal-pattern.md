<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Topic: Vault commit modal — file picker + repo + author + message

**Slug:** vault-commit-modal-pattern
**First discovered:** 2026-05-19 13:30 by Sinister Sanctum master agent
**Last updated:** 2026-05-19 13:30 by Sinister Sanctum master agent
**Status:** fixed
**Tags:** vault, modal, ui, commit, lg-popover, frontend

## Problem

`web/app.js:openCommitModal()` was a stub that just toasted "TODO: pre-populate
from active projects." The RKOJ Vault drawer's "Commit file" button (visible at
`web/index.html:715`) didn't actually let the operator commit anything.

## Why it happens

The vault commit MCP (`bots/agents/vault/server.py`) shipped 2026-05-19 with
the `vault.commit` tool. The vault daemon (`tools/sinister-vault/daemon.py`)
exposes `POST /api/vault/commit`. The template `tpl-vault-commit-modal` exists
in `index.html:723` with all the form fields. The only missing piece was the
JS to clone the template, populate the repo dropdown, and wire the submit.

A prior session shipped the analogous `openBroadcastModal()` for inbox
broadcast — same pattern, same overlay, same form-clone flow. The vault modal
follows the same recipe.

## Fix or workaround

**Tested 2026-05-19 (Phase 1.3 of complete-everything sweep).**

```javascript
async function openCommitModal() {
    const tpl = document.getElementById('tpl-vault-commit-modal');
    if (!tpl) { _toast('Commit modal template missing', true); return; }
    const overlay = document.createElement('div');
    overlay.className = 'rkoj-modal-overlay';
    overlay.style.cssText = 'position:fixed;inset:0;z-index:9800;...';
    overlay.appendChild(tpl.content.cloneNode(true));
    document.body.appendChild(overlay);

    // Populate repo dropdown from /api/launcher/options
    const repoSel = overlay.querySelector('[data-bind="vc-repo"]');
    // ... fetch projects, populate select

    // Submit -> POST /api/vault/commit
    overlay.querySelector('[data-act="save"]').addEventListener('click', async () => {
        // Validate + POST + close on success
    });
}
```

Full implementation at `web/app.js:openCommitModal` (~85 LOC).

## Pattern shape (re-usable for any future modal in RKOJ)

1. **HTML template** in `index.html` — `<template id="tpl-XXX-modal">` with form fields tagged via `data-bind="…"` and action buttons tagged `data-act="cancel" | "save"`.
2. **JS modal helper** in `app.js` — clones the template, wraps in `.rkoj-modal-overlay`, wires:
   - Click-outside to close
   - `[data-act="cancel"]` to close
   - `[data-act="save"]` to validate + POST + close-on-success
   - Initial focus on the first input (50ms timeout)
3. **Server endpoint** — POST returns `{ok: true|false, error?, ...}`. JSON shape lets the modal display server errors verbatim.

`openBroadcastModal` (app.js ~L2444) and `openCommitModal` (app.js ~L3275) are
the two canonical examples. Future modals (snapshot picker, account creator,
etc.) follow the same shape — keeps the operator's muscle memory consistent.

## Discoveries (append-only log, most-recent at top)

### 2026-05-19 13:30 by Sinister Sanctum master agent
First landing. The repo dropdown source was the only judgment call — picked
`/api/launcher/options.projects` since it's the same source the launcher pane
uses (consistency over creating a new endpoint). Falls back to a single
`sinister-sanctum` option if the launcher options call fails.

## Related topics

- [rkoj-workbench-architecture](./rkoj-workbench-architecture.md) — RKOJ.exe surface this modal lives in
- [sinister-vault-architecture](./sinister-vault-architecture.md) — the vault subsystem this modal commits into
