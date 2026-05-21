# -*- mode: python ; coding: utf-8 -*-
# Author: RKOJ-ELENO :: 2026-05-21
# PyInstaller spec for RKOJ.exe (native PyQt6 build).

import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# Bundle the Sinister logo icon if it exists.
icon_path = r"D:\Sinister Sanctum\automations\window-manager\web\sinister-logo.ico"
icon_arg = icon_path if os.path.exists(icon_path) else None

hidden = []
hidden += collect_submodules("PyQt6")
hidden += [
    "PyQt6.QtCore",
    "PyQt6.QtGui",
    "PyQt6.QtWidgets",
    "PyQt6.QtSvgWidgets",
    "PyQt6.QtSvg",
]

datas = []

a = Analysis(
    ["__main__.py"],
    pathex=[os.path.dirname(os.path.abspath(SPEC))],
    binaries=[],
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",  # we ship tk only as a fallback — Qt is the primary UI
        "matplotlib",
        "numpy",
        "scipy",
        "pandas",
        "PyQt5",
        "PySide2",
        "PySide6",
        "PyQt6.QtNetwork",  # not used
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

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="RKOJ",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_arg,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="RKOJ",
)
