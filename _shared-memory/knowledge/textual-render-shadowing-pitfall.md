# Textual: `def _render(self)` in a subclass SILENTLY shadows framework render

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Slug:** `textual-render-shadowing-pitfall`
> **Status:** known-issue, fix-doctrine
> **Tags:** textual, python, forge, widget, _render, override, framework-pitfall, root-cause, p0, sinister-forge, debug-doctrine

## The bug in one paragraph

A Textual `Widget` subclass that defines `def _render(self) -> None:` as a *private content-update helper* will silently override `textual.widget.Widget._render`, which the framework calls every paint to obtain a `Visual`. The override returns `None`, the framework hands that to `Visual.to_strips(self, None, ...)`, and the next paint crashes with `AttributeError: 'NoneType' object has no attribute 'render_strips'`. Textual's app-level error handler catches the exception, so the process *exits 0* with a multi-page Rich traceback dumped to stderr — easy to miss in a launcher bat that immediately closes the window.

## Empirical origin

Sinister Forge boot, operator-reported 2026-05-21T11:30Z: "Sinister Start.bat → forge → Windows alert + bunch of code goes by + crash." Three widgets in `projects/sinister-forge/source/forge/panes/` triggered it: `ProjectChip`, `StatusFooter` (both in `chrome.py`), and `StatusBar` (in `status_bar.py`). `ChromeBar` in the same file did NOT trigger because its helper was named `_refresh` instead of `_render`. Pure naming luck.

## Why it slips past review

- `_render` *looks* private enough to grab — the leading underscore is the Python convention for "do not call from outside the class."
- The override doesn't fire at `__init__` time — only on the first paint, which is after `on_mount`, which is after CSS application, which is after compose. So the import test (`python -c "from forge.app import ForgeApp"`) succeeds; the launch test (`python -m forge`) crashes.
- Textual's framework error handler catches the exception and produces a Rich-formatted traceback, then exits the app with code 0. Wrapper bats see exit-0 and report "Forge installed but window didn't stay open."
- The traceback's terminal control codes (`[?1049h[?1000h…`) corrupt logs if you grep for them, so silent-loss is easy.

## The fix (two-part per widget)

1. **Rename** the helper. `_render` → `_refresh_view` (or `_redraw`, `_update_content`, `_paint` — anything but `_render`).
2. **Initial content** must be passed positionally to `super().__init__(...)` so the *first* paint has a `Content`. Calling `self.update(...)` from inside `__init__` is NOT a substitute — that path appears to no-op or run too late in Textual 8.x.

### Wrong (will crash):

```python
class StatusFooter(Static):
    def __init__(self) -> None:
        super().__init__(id="status-footer", markup=True)
        self._branch = ""
    def on_mount(self) -> None:
        self.set_interval(5.0, self._read_branch)
        self._read_branch()
    def _read_branch(self) -> None:
        self._branch = ...
        self._render()
    def _render(self) -> None:        # ← shadows Widget._render, returns None
        self.update(f"[dim]branch[/] [purple]{self._branch}[/]")
```

### Right:

```python
class StatusFooter(Static):
    def __init__(self) -> None:
        super().__init__(
            "[dim]branch[/] [purple]?[/]",     # initial content, positional
            id="status-footer",
            markup=True,
        )
        self._branch = ""
    def on_mount(self) -> None:
        self.set_interval(5.0, self._read_branch)
        self._read_branch()
    def _read_branch(self) -> None:
        self._branch = ...
        self._refresh_view()                    # renamed
    def _refresh_view(self) -> None:            # no longer shadows
        self.update(f"[dim]branch[/] [purple]{self._branch}[/]")
```

## How to detect this fast

When a Textual subclass crashes at first paint with `AttributeError: 'NoneType' object has no attribute 'render_strips'`:

```bash
grep -rn "def _render(self" projects/<your-project>/source/
```

Any hit on a `Widget` subclass is suspect. Sanity-check via REPL:

```python
from your.module import YourWidget
w = YourWidget()
print(type(w._render()).__name__)   # MUST be 'Content' (or Visual subclass), not 'NoneType'
```

## Other reserved method names to AVOID on Widget subclasses

(Same shadowing risk; check the Textual source before naming a helper.)

- `_render` — returns Visual
- `render` — returns RenderableType (subclasses override this on purpose)
- `_compose` — returns ComposeResult
- `compose` — returns ComposeResult
- `on_mount`, `on_unmount`, `on_show`, `on_hide` — framework lifecycle
- `_refresh` — refresh queue (this one is borderline; ChromeBar uses it as a public-ish helper without crashing, but it's brittle)

## Composes with

- `pyinstaller-distutils-exclude-collision` — also a "framework method shadowing causes silent failure" pattern, this one inside PyInstaller hooks.
- `marketplace-plugin-purge` — same fleet ethos: don't blindly trust short-names that look local.
- `multi-agent-branch-contention-isolation-pattern` — the *fix commit* for this bug ended up on the wrong branch via sibling-checkout race; the contention doctrine kicked in to recover via cherry-pick.

## Cross-references

- Bug commit: `cebf6cf` (landed on Sanctum branch by accident)
- Fix commit on Forge branch: `34af6a8`
- Files fixed: `projects/sinister-forge/source/forge/panes/chrome.py`, `projects/sinister-forge/source/forge/panes/status_bar.py`
- Textual version: `8.2.7` (issue exists across 8.x — new visual system removed the implicit fallback that earlier versions tolerated)
- Operator report origin: 2026-05-21T11:30Z "Sinister Start.bat → forge → Windows alert + crash"
