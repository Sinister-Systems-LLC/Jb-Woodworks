# Launcher additions — Resume previous + Guided new-project scaffold

**Captured:** 2026-05-19 00:35
**Status:** building
**Origin:** Operator: "add to the session start a selection to pickup from a previous project or create a new one and then we tell it everything we want and it gets to work to make a new project. what are we working on classes etc"

## Idea

Two new entry points in `Start-Sinister-Session.bat`'s project picker:

- **R) resume previous** — surfaces last 5-10 launched projects from runlog manifests, operator picks one, jumps in with last-used mode.
- **G) guided new project** — instead of just registering a project, walk operator through: project name, description, language, what classes/files to scaffold. Launcher creates folder + `_SCAFFOLD-BRIEF.md` + spawns Claude with a scaffold-mode opening phrase that tells Claude to BUILD the initial source tree.

## Why

- **Resume:** today operator has to remember which project they were on. Manifest data already exists; just surface it.
- **Guided scaffold:** today new projects are empty registry entries — operator still has to type out "create folder, add CLAUDE.md, add SESSION-START.md, scaffold X classes" each time. Wraps that into one launcher flow.

## Sketch

```
[ project picker ]
  *1) Sanctum
   2) Snap EMU
   3) TikTok EMU
   4) Panel
   5) Kernel APK
   R) resume previous     <-- NEW
   G) guided new project  <-- NEW
   C) custom prompt
   N) new project (quick)

  Selection [1-5/R/G/C/N, default=sanctum]:
```

**R flow:**
```
  Recently worked on (last 10 launches):
    1) snap-emu   3h ago    mode=dev
    2) tiktok-emu yesterday mode=push
    3) sanctum    2 days    mode=overview
  Pick [1-3]:
```

**G flow:**
```
  Guided scaffold mode.
  Project name (display)        : Sinister Bumble EMU
  Project slug (folder name)    : sinister-bumble-emu
  One-line description          : Bumble account creation API
  Language (python/ts/kotlin/.) : python
  Classes/files to scaffold     : AccountCreator, SwipeBot, TokenStore
  GitHub repo (optional)        : Sinister-Systems-LLC/Sinister-Bumble-EMU

  Creating D:\Sinister Sanctum\projects\sinister-bumble-emu\...
  Writing _SCAFFOLD-BRIEF.md...
  Launching Claude with scaffold directive...
```

## Status

- [x] idea captured
- [x] design sketched (plan file)
- [ ] implementation in launcher v4 (this phase 8ai)
- [ ] shipped

## Linked-to

- Plan file: `C:\Users\Zonia\.claude\plans\proud-leaping-allen.md`
- Launcher: `D:\Sinister Sanctum\automations\start-sinister-session.ps1`
- Registry: `D:\Sinister Sanctum\automations\session-templates\projects.json`
- Phase: 8ai

## Notes

- `R` uses existing runlog manifests (no new state).
- `G` writes `_SCAFFOLD-BRIEF.md` with sections: Goal / Stack / Classes-or-Files / Acceptance / Out-of-scope.
- The "scaffold" opening phrase is a new mode — Claude reads brief, scaffolds, then summarizes.
- `N` (current quick-add) stays for cases where operator already has the folder + just needs a registry entry.
