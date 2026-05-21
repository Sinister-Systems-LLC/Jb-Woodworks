# Sinister Forge :: panes/adb_panel.py — Phones tab (Sinister Panel style)
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Operator 2026-05-21 (image 28 = Sinister Panel dashboard reference):
#   *"phones (all adb support and what not)"*.
# User-facing label is now "Phones" everywhere — internal class name kept as
# `AdbPanel` so the 10 existing import refs across app.py / __init__.py etc.
# don't need rewiring.
#
# Auto-detects ADB devices on mount, refreshes every 10s, shows a device-card
# grid (model · serial · state · transport). Empty state nudges the operator
# to plug a USB phone or `adb tcpip 5555`.

from __future__ import annotations

import asyncio
import subprocess
from dataclasses import dataclass

from textual.app import ComposeResult
from textual.containers import Grid, Vertical, VerticalScroll
from textual.widgets import Static

from forge.theme import (
    BG, BG_GLASS_1, BG_GLASS_2, BORDER_GLASS, PURPLE_DEEP, PURPLE_ACCENT,
    LIGHT_PURPLE, DIM,
)


@dataclass
class AdbDevice:
    serial: str
    state: str           # device / unauthorized / offline / no_permissions
    model: str = ""
    product: str = ""
    transport: str = ""  # usb / tcp:<port>
    extra: str = ""


def _parse_adb_devices(text: str) -> list[AdbDevice]:
    out: list[AdbDevice] = []
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("List of devices") or ln.startswith("*"):
            continue
        parts = ln.split()
        if len(parts) < 2:
            continue
        serial, state = parts[0], parts[1]
        d = AdbDevice(serial=serial, state=state)
        for kv in parts[2:]:
            if ":" in kv:
                k, v = kv.split(":", 1)
                if k == "model":
                    d.model = v.replace("_", " ")
                elif k == "product":
                    d.product = v
                elif k == "transport_id":
                    d.transport = f"id:{v}"
        out.append(d)
    return out


async def _scan_devices(timeout_s: float = 4.0) -> tuple[list[AdbDevice], str | None]:
    """Run `adb devices -l`; return ([devices], None) or ([], error)."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "adb", "devices", "-l",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_s)
        except asyncio.TimeoutError:
            proc.kill()
            return [], "adb timeout"
        if proc.returncode != 0:
            return [], (stderr.decode("utf-8", errors="replace") or "adb non-zero").strip()
        return _parse_adb_devices(stdout.decode("utf-8", errors="replace")), None
    except FileNotFoundError:
        return [], "adb not on PATH"
    except Exception as e:
        return [], str(e)


class AdbDeviceCard(Static):
    """One purple Pixel-card per ADB device. Mirrors Sinister Panel detector card.

    NOTE 2026-05-21: the underscore-prefixed static helper was renamed to
    `_format_card` to avoid shadowing textual.Widget._render(self) — Static
    inherits a no-arg `_render()` method via the render-cache machinery and
    our 2-arg signature broke the render pipeline once the panel was visible.
    """

    def __init__(self, idx: int, dev: AdbDevice) -> None:
        super().__init__(self._format_card(idx, dev), classes="adb-card")
        self.idx = idx
        self.dev = dev

    @staticmethod
    def _format_card(idx: int, d: AdbDevice) -> str:
        state_color = {
            "device": "[bold green]●[/]",
            "unauthorized": "[bold yellow]●[/]",
            "offline": "[bold red]●[/]",
            "no_permissions": "[bold red]●[/]",
        }.get(d.state, "[dim]●[/]")
        title = (d.model or d.product or d.serial) + ""
        return (
            f"[bold]{state_color}  USB[/]   [dim]{d.transport or '·'}[/]\n"
            f"[bold purple]DETECTOR[/]\n"
            f"[bold]{title}[/]\n"
            f"[dim]{d.serial}[/]   [italic]{d.state}[/]\n"
        )

    def update_dev(self, dev: AdbDevice) -> None:
        self.dev = dev
        self.update(self._format_card(self.idx, dev))


class AdbPanel(VerticalScroll):
    """Scrollable list of ADB devices + refresh + simple action toolbar."""

    # Sinister Panel chrome via forge.theme constants (rounded purple borders,
    # tinted layer-1/layer-2 backgrounds, halo-purple title text).
    DEFAULT_CSS = f"""
    AdbPanel {{
        background: {BG};
        padding: 1 2;
    }}
    AdbPanel #adb-toolbar {{
        height: 3;
        padding: 0 1;
        background: {BG_GLASS_1};
        color: {PURPLE_ACCENT};
        border: round {BORDER_GLASS};
    }}
    AdbPanel #adb-grid {{
        layout: grid;
        grid-size: 2;
        grid-gutter: 1 2;
        margin: 1 0;
    }}
    .adb-card {{
        height: 8;
        padding: 1 2;
        background: {BG_GLASS_2};
        border: round {PURPLE_DEEP};
        color: {LIGHT_PURPLE};
        content-align: left top;
    }}
    .adb-card:hover {{
        border: round {PURPLE_ACCENT};
    }}
    .adb-empty {{
        height: 5;
        content-align: center middle;
        color: {DIM};
    }}
    """

    def __init__(self) -> None:
        super().__init__()
        self._toolbar = Static(
            "[bold]PHONES[/]   "
            "[dim]r=refresh · k=kill-server · s=start-server · t=tcpip 5555[/]",
            id="adb-toolbar",
        )
        self._grid = Grid(id="adb-grid")
        self._empty = Static(
            "[dim]No devices connected. Connect via USB or `adb tcpip 5555`.[/]",
            classes="adb-empty",
        )
        self._cards: list[AdbDeviceCard] = []
        self._refresh_running = False

    def compose(self) -> ComposeResult:
        yield self._toolbar
        yield self._grid
        yield self._empty

    async def on_mount(self) -> None:
        # Operator directive 2026-05-21: refresh every 10s (was 8s).
        self.set_interval(10.0, self._safe_refresh)
        await self._safe_refresh()

    async def _safe_refresh(self) -> None:
        if self._refresh_running:
            return
        self._refresh_running = True
        try:
            devs, err = await _scan_devices()
            await self._apply(devs, err)
        finally:
            self._refresh_running = False

    async def _apply(self, devs: list[AdbDevice], err: str | None) -> None:
        # wipe old cards
        for c in self._cards:
            c.remove()
        self._cards.clear()
        if err and not devs:
            self._empty.update(f"[red]adb error:[/] {err}")
            self._empty.display = True
            return
        if not devs:
            self._empty.update(
                "[dim]No devices connected. Connect via USB or `adb tcpip 5555`.[/]"
            )
            self._empty.display = True
            return
        self._empty.display = False
        for i, d in enumerate(devs, start=1):
            card = AdbDeviceCard(i, d)
            self._cards.append(card)
            await self._grid.mount(card)

    async def on_key(self, event) -> None:
        key = event.key.lower()
        if key == "r":
            await self._safe_refresh()
        elif key == "k":
            await self._adb_subcmd(["adb", "kill-server"])
        elif key == "s":
            await self._adb_subcmd(["adb", "start-server"])
        elif key == "t":
            await self._adb_subcmd(["adb", "tcpip", "5555"])

    async def _adb_subcmd(self, argv: list[str]) -> None:
        try:
            proc = await asyncio.create_subprocess_exec(
                *argv,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await asyncio.wait_for(proc.wait(), timeout=4)
        except Exception:
            pass
        await self._safe_refresh()
