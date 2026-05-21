# sinister-rkoj-qt

> Author: RKOJ-ELENO :: 2026-05-21

Native **PyQt6 6.11.0** desktop GUI for `RKOJ.exe`. Replaces the rejected pywebview path with true Qt widgets, frameless rounded chrome, and the Sinister Panel layout.

## Layout

```
+-----------------------------------------------------------------+
| Sidebar |  Header (chip tabs + clock)            [ _ ] [ # ] [X]|
| 240px   |---------------------------------------------------------|
|         |  Ribbon: VIEW / SPAWN / AGENT / AUTOMATE / MAINTAIN      |
| Mascot  |---------------------------------------------------------|
| EVE     |  KPIs: PHONES / AGENTS / VAULT / PENDING                |
|         |---------------------------------------------------------|
| WORK-   |  Project chips: All  Sanctum  Panel  Forge ...          |
| SPACE   |---------------------------------------------------------|
| OPS     |                                                         |
| AI      |       Agents | Phones | Workstation                    |
| SYSTEM  |       (QStackedWidget — switches by chip tab)           |
|         |                                                         |
| STATUS  |                                                         |
| live N  |                                                         |
+---------+---------------------------------------------------------+
```

- **Frameless** — `Qt.WindowType.FramelessWindowHint` + rounded `QRegion` mask. Drag-to-move bound to the header.
- **Sanctum purple** — every color goes through `theme.py`. No inline hex.
- **EVE persona** — `persona.py` builds the verbatim opening prompt used by `agents_tab.ClaudeRunner` when starting a `claude --dangerously-skip-permissions -p <prompt>` subprocess.
- **Live counters** — `state.py` polls heartbeats / inbox / brain / adb-devices on a 5s/10s/3s cadence.

## Running from source

```bash
cd "D:/Sinister Sanctum/tools/sinister-rkoj-qt"
python -m sinister_rkoj_qt
```

If PyQt6 is missing the entrypoint pops a `tkinter.messagebox` and exits 1.

## Building the EXE

```bash
cd "D:/Sinister Sanctum/tools/sinister-rkoj-qt/sinister_rkoj_qt"
pyinstaller --clean --noconfirm RKOJ.spec
```

Output: `dist/RKOJ/RKOJ.exe` + `_internal/` (one-folder mode, ~50-80 MB).

The build is then copied to `C:\Users\Zonia\Desktop\RKOJ-Workstation\` so the existing `RKOJ.lnk` desktop shortcut continues to work.

## Slash commands

Handled client-side inside each agent terminal:

| slash | effect |
|-------|--------|
| `/help` | show command list |
| `/clear` | clear terminal buffer |
| `/save` | write `{pane_id}.json` resume-point to `_shared-memory/rkoj-qt/resume-points/` |
| `/resume` | (stub) reload last resume-point |
| `/create` | hint to use the FAB |
| all other `/...` | forwarded to the claude subprocess |

## Tabs

- **Agents** — niri scroll of cards, each with a `QPlainTextEdit` terminal + `QLineEdit` input + `QProcess` claude subprocess; status dot online/busy/offline.
- **Phones** — `adb devices -l` poll every 10s, logcat tail every 3s, adb shell with 10s timeout, scrcpy / phone-viewer / list-apps actions.
- **Workstation** — action-card grid for Vault, Brain Graph, Watchdog, Backups, MCP, shared-memory.

## Files

| file | role |
|------|------|
| `__main__.py` | entry; falls back to tk popup if PyQt6 missing |
| `app.py` | QApplication + frameless `MainWindow` |
| `sidebar.py` | 240px Sinister Panel-style sidebar |
| `header.py` | 96px header + chip tabs + drag-to-move |
| `ribbon.py` | Excel-style 5-group ribbon |
| `kpis.py` | 4 KPI tile strip |
| `agents_tab.py` | EVE agent cards + `ClaudeRunner` |
| `phones_tab.py` | device list + logcat + adb shell |
| `workstation_tab.py` | action card grid |
| `theme.py` | Sanctum purple QSS tokens |
| `state.py` | filesystem polling (heartbeats / inbox / brain / adb) |
| `persona.py` | EVE opening-prompt builder |
| `RKOJ.spec` | PyInstaller spec (one-folder, no console, custom icon) |
