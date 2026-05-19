# Claude Window Manager — UI for managing Sanctum Claude sessions

**Captured:** 2026-05-19 00:30
**Status:** designing
**Origin:** Operator screenshot + ask: "make a UI based system of this that matches the sinister apk look and feel to manage claude windows in the sanctum for now"

## Idea

A small purple-themed web UI (matching DETECTOR look + Sinister Panel palette) for managing Claude Code sessions inside Sanctum. Operator opens one URL, sees: active sessions, project list (one-click launch), recent runlogs, trophy case stats. Replaces the need to remember which git-bash window is which.

## Why

Operator runs multiple parallel Claude sessions (master + per-project agents). Currently each lives in its own git-bash window with no central index. As the fleet grows (snap-emu, tiktok-emu, panel, kernel-apk, plus future projects), the operator loses track of which sessions are alive and what they're doing. A single dashboard:

- Surfaces live state without alt-tabbing through windows
- Becomes the "front door" for launching new sessions (replaces clicking Desktop bats one by one)
- Future-proofs for multi-window orchestration (e.g. "start 3 sessions with role bindings")

## Sketch

```
+----------------------------------------------------------------+
| [skull]  SINISTER SANCTUM :: CLAUDE WINDOWS    00:32 UTC       |
+----------------------------------------------------------------+
| PROJECTS         | ACTIVE SESSIONS         | TROPHY CASE       |
|------------------|-------------------------|-------------------|
| * Sanctum        | [snap-signer]           | panel    ONLINE   |
|   Snap EMU       |   last beat 12s ago     | rka      ONLINE   |
|   TikTok EMU     |   8 ahead, ready push   | accounts   1,234  |
|   Panel          |   inbox: 0              | videos     5,678  |
|   Kernel APK     |   [send msg]            | devices       3   |
|                  |                         |                   |
| + new project    | [sinister-panel]        | RUNLOGS           |
| + custom phrase  |   last beat 3m ago      | do-everything OK  |
| ~ resume         |   panel at ad333ee      | push-all-sinister |
|                  |   inbox: 2 unread       | start-session  OK |
+----------------------------------------------------------------+
```

## Stack (per plan)

- Backend: FastAPI single-file at `D:\Sinister Sanctum\automations\window-manager\server.py`, port 5077, calls `sinister-bus` tools as Python imports
- Frontend: vanilla JS + HTML + CSS (no bundler), purple theme via CSS variables matching panel's `lib/theme.ts`
- Skull glyph: inline SVG (avoids depending on operator-private APK PNG path)
- Desktop entry: `Open-Sanctum-Console.bat`
- Auth: none (localhost-only + operator-only)

## Status

- [x] idea captured
- [x] design sketched (plan file)
- [ ] implementation started (paused — operator confirming scope)
- [ ] shipped

## Linked-to

- Plan file: `C:\Users\Zonia\.claude\plans\proud-leaping-allen.md`
- Phase: 8ai (planned)
- Exploration: 3 Explore agent reports in Phase 8ai plan-context

## Notes

- Operator framed as "for now" → v1 minimal, future phases can add embedded terminal viewers, drag-rearrange, Obsidian-canvas style links between sessions.
- Lane discipline: window-manager is STANDALONE, doesn't modify panel source. Panel theming is reused via copy (CSS variables), not import. Phase 8aj could merge into panel-as-route if operator approves.
