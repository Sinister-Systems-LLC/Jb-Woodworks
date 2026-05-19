# md-trash-bin

Drop-and-forget markdown router. The operator (or Leo) drops `.md` files into a
desktop trash-bin folder; a scheduled sweeper categorizes each file by topic,
prepends an auto-categorized timestamp, and moves it into the Sanctum library.

## What it does

A friction-zero capture-and-sort pipeline for stray markdown notes. The trash
bin is the only thing the operator interacts with: anything dropped there is
gone within ~6 hours and reappears, properly slugged and dated, inside the
right topic folder of `D:\Sinister Sanctum\library\`.

The sweeper:

1. Scans `C:\Users\Zonia\Desktop\MD-Trash-Bin\*.md` (skipping `README.md`).
2. Extracts a title (first `# Header` or filename) and first-paragraph summary.
3. Detects topic via static keyword map (snap / tiktok / panel / kernel /
   signing / api / ui / ops / security / idea / misc).
4. Picks destination
   `D:\Sinister Sanctum\library\<topic>\YYYY-MM-DD-<slug>.md`,
   prepends `**Auto-categorized:** YYYY-MM-DD HH:MM by md-trash-bin sweeper.`
   under the title, then **moves** the file (not copies).
5. Writes a sweep manifest to
   `D:\Sinister Sanctum\library\_manifests\sweep-YYYY-MM-DD-HHMM.json`.
6. Emits a runlog manifest via the shared `_runlog.ps1` helper.

Leo's onboarding copy of Sanctum ships with the same trash bin folder
pre-created, so his downloaded notes auto-flow into the same library.

## How to invoke (operator-facing)

Manual sweep:

```
C:\Users\Zonia\Desktop\Sweep-MD-Trash.bat
```

Auto sweep (every ~6 hours, random minute offset):

```
D:\Sinister Sanctum\automations\install-md-sweep-task.ps1
```

Run that installer **once, elevated** (right-click -> Run as administrator).
It registers Windows scheduled task `SinisterMDSweep` with daily triggers at
04:XX / 10:XX / 16:XX / 22:XX, where XX is a random minute chosen at install
time.

## Implementation files (absolute paths)

- `D:\Sinister Sanctum\automations\sweep-md-trash.ps1` (sweeper core)
- `D:\Sinister Sanctum\automations\install-md-sweep-task.ps1` (one-shot task registrar)
- `C:\Users\Zonia\Desktop\Sweep-MD-Trash.bat` (manual trigger, purple-branded)
- `C:\Users\Zonia\Desktop\MD-Trash-Bin\README.md` (drop-zone doc)
- `D:\Sinister Sanctum\library\README.md` (archive doc)
- `D:\Sinister Sanctum\library\_manifests\.gitkeep` (manifest directory placeholder)

## Dependencies

- Windows PowerShell 5.1+
- Windows Task Scheduler (for the every-6h cadence; manual `.bat` does not need it)
- Optional: `D:\Sinister\Sinister Skills\08_AUTOMATIONS\_runlog.ps1` (shared
  runlog helper — sweeper auto-detects and dot-sources if present)
- Write access to `D:\Sinister Sanctum\library\` and `C:\Users\Zonia\Desktop\MD-Trash-Bin\`

## Lane

master / Sanctum orchestration

## Captured

2026-05-19

## Status

shipped

## Linked-inventions

- (none yet — direct operator directive 2026-05-19)

## Changelog

- **2026-05-19** — Initial registration. Sweeper, manual `.bat`, scheduled-task
  installer, library archive, and trash-bin drop zone all wired up.
  Status: shipped.
