# Agent: Sinister Claw

Mobile (iOS + Android) companion built on Expo + React Native + TypeScript. Drives the entire Sanctum fleet from operator's phone over Tailscale. jcode `Native OpenClaw` as base + Sinister expansion.

Branch convention: `agent/sinister-claw/<topic>`. Accent: purple. Authorship: RKOJ-ELENO :: <date>.

Most-recent at top. Append-only.

---

## 2026-05-21 13:50 — start: sinister-claw lane bootstrap (first dedicated agent)

First time the `sinister-claw` agent slug has been registered. Prior Claw work shipped via `rkoj-workstation` (4 commits on main: scaffold + Forge bridge + Inbox/Projects + Panel WebView) and one orphaned commit `10cd7ce` (native PanelScreen + api/panel.ts) sitting on locked worktree branch `worktree-agent-a99fd0c85bc618fd4`.

This session: register heartbeat + create inbox dir + create proper `agent/sinister-claw/lane-bootstrap-2026-05-21` branch with native-Panel cherry-pick, then proceed with PH9 push scaffold + SanctumScreen UX polish + cross-lane [ASK] to sinister-forge for the `/api/panel/*` proxy required by the native PanelScreen.
