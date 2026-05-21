# -*- mode: python ; coding: utf-8 -*-
# Author: RKOJ-ELENO :: 2026-05-21
# PyInstaller spec for RKOJ.exe (native PyQt6 build) — ONEFILE mode.
#
# Operator directive 2026-05-21: "only the exe is to be on desktop".
# Folder-mode (RKOJ.exe + _internal/) does not satisfy that; this spec
# produces a single self-contained dist/RKOJ.exe (~50-80 MB).

import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

_SPEC_DIR = os.path.dirname(os.path.abspath(SPEC))
_PROJECT_ROOT = os.path.dirname(_SPEC_DIR)  # projects/rkoj/source/ (relocated 2026-05-21 from tools/sinister-rkoj-qt/)
_ASSETS_ROOT = os.path.join(_PROJECT_ROOT, "assets")

# Brand icon — convert PNG -> ICO done at theme build time
# (see assets/icon.ico). PyInstaller on Windows wants .ico, not .png.
_BRAND_ICON = os.path.join(_ASSETS_ROOT, "icon.ico")
# Fallback to legacy window-manager logo if brand icon missing.
_LEGACY_ICON = r"D:\Sinister Sanctum\automations\window-manager\web\sinister-logo.ico"
icon_arg = _BRAND_ICON if os.path.exists(_BRAND_ICON) else (_LEGACY_ICON if os.path.exists(_LEGACY_ICON) else None)

hidden = []
hidden += collect_submodules("PyQt6")
hidden += [
    "PyQt6.QtCore",
    "PyQt6.QtGui",
    "PyQt6.QtWidgets",
    "PyQt6.QtSvgWidgets",
    "PyQt6.QtSvg",
]

# Bundle brand assets into the EXE — extracted at runtime under sys._MEIPASS/assets/.
# theme.asset_path() resolves both frozen and dev contexts.
datas = []
if os.path.isdir(_ASSETS_ROOT):
    datas.append((_ASSETS_ROOT, "assets"))

a = Analysis(
    ["__main__.py"],
    pathex=[_SPEC_DIR],
    binaries=[],
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib",
        "numpy",
        "scipy",
        "pandas",
        "PyQt5",
        "PySide2",
        "PySide6",
        "PyQt6.QtNetwork",
        "PyQt6.QtMultimedia",
        "PyQt6.QtWebEngineWidgets",
        "PyQt6.QtWebEngineCore",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ── ONEFILE: bundle scripts + binaries + zipfiles + datas into single EXE ──
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="RKOJ",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,  # default: extract to %TEMP%
    console=False,         # PyQt6 windowed app — no cmd console flash
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_arg,
)
# NOTE: COLLECT() intentionally omitted — onefile mode requires only the EXE step.
