# Sinister Sanctum :: Sinister-Forge PyInstaller spec
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Onefile build mirroring jcode-windows-x86_64.exe shape.
# console=True (Textual TUI needs real terminal).
# Brain doctrine honored:
#   - pyinstaller-distutils-exclude-collision: distutils NOT excluded
#   - exe-silent-crash-no-popup: runtime logger in entry script
#   - sanctum-shared-rename-pyinstaller-collision: collect_submodules used
#   - pyinstaller-tomli-hook-missing: pip force-reinstall hooks-contrib
#     should be run before this build

# ruff: noqa
# flake8: noqa
# pylint: skip-file
# type: ignore

from PyInstaller.utils.hooks import (
    collect_submodules,
    collect_data_files,
    collect_dynamic_libs,
)

# --- forge + sinister-X packages -------------------------------------------

forge_subs = collect_submodules("forge")
forge_data = collect_data_files("forge", include_py_files=False)

sinister_packages = (
    "sinister_cli",
    "sinister_login",
    "sinister_usage",
    "sinister_model",
    "sinister_swarm",
    "sinister_jcode_shim",
    "forge_memory_bridge",
    "memory_graph_render",
    "sanctum_backup",
)
sinister_subs = []
sinister_data = []
for pkg in sinister_packages:
    try:
        sinister_subs += collect_submodules(pkg)
        sinister_data += collect_data_files(pkg, include_py_files=False)
    except Exception:
        # Optional tool not installed in build env — skip gracefully.
        pass

# --- textual + rich + pyyaml + watchdog + flask ----------------------------

textual_subs = collect_submodules("textual")
textual_data = collect_data_files("textual")  # CSS / TCSS resources

rich_subs = collect_submodules("rich")
rich_data = collect_data_files("rich")

pyyaml_subs = collect_submodules("yaml")
watchdog_subs = collect_submodules("watchdog")
flask_subs = collect_submodules("flask")

# `anthropic` SDK powers the spawn/anthropic_direct.py path (multi-step
# visible tool reasoning in the RKOJ shell). collect_submodules pulls in
# its httpx + pydantic dependency surface that PyInstaller would otherwise
# miss because the module is imported lazily.
try:
    anthropic_subs = collect_submodules("anthropic")
    anthropic_data = collect_data_files("anthropic")
except Exception:
    anthropic_subs = []
    anthropic_data = []
try:
    httpx_subs = collect_submodules("httpx")
    httpcore_subs = collect_submodules("httpcore")
except Exception:
    httpx_subs = []
    httpcore_subs = []
try:
    pydantic_subs = collect_submodules("pydantic")
    pydantic_core_subs = collect_submodules("pydantic_core")
except Exception:
    pydantic_subs = []
    pydantic_core_subs = []

# rank_bm25 powers BM25 re-scoring on `forge_memory_bridge.recall()` return
# path (jcode parity, brain entry jcode-agentic-loop-patterns-port-to-python
# pattern 6). v0.1.2 of forge-memory-bridge requires it.
try:
    rank_bm25_subs = collect_submodules("rank_bm25")
except Exception:
    rank_bm25_subs = ["rank_bm25"]

# --- stdlib chain (per pyinstaller-distutils-exclude-collision doctrine) ---

stdlib_hidden = [
    # network + selectors
    "select",
    "_socket",
    "socket",
    "selectors",
    # asyncio internals
    "asyncio",
    "asyncio.selector_events",
    "asyncio.windows_events",
    "asyncio.proactor_events",
    # multiprocessing (watchdog observers may use)
    "multiprocessing",
    "multiprocessing.context",
    "multiprocessing.reduction",
    "multiprocessing.popen_spawn_win32",
    "multiprocessing.queues",
    "multiprocessing.synchronize",
    "multiprocessing.connection",
    # importlib (sinister-cli dispatcher uses importlib.import_module)
    "importlib",
    "importlib.metadata",
    "importlib.resources",
    # pkg_resources runtime hook (pyi_rth_pkgres) requires jaraco namespace
    # — PyInstaller autodetect misses these because they're namespace packages
    # spread across multiple installs. Without them the EXE crashes at startup
    # with ModuleNotFoundError 'jaraco' before our entry script even runs.
    "pkg_resources",
    "pkg_resources.extern",
    "jaraco",
    "jaraco.text",
    "jaraco.functools",
    "jaraco.context",
    "jaraco.collections",
    "more_itertools",
    "platformdirs",
    "packaging",
    "packaging.requirements",
    "packaging.specifiers",
    "packaging.version",
]

hiddenimports = (
    forge_subs
    + sinister_subs
    + textual_subs
    + rich_subs
    + pyyaml_subs
    + watchdog_subs
    + flask_subs
    + anthropic_subs
    + httpx_subs
    + httpcore_subs
    + pydantic_subs
    + pydantic_core_subs
    + rank_bm25_subs
    + stdlib_hidden
    # SkillRegistry (forge/skills.py) loads ~/.sinister/skills/*.md with
    # YAML frontmatter via `yaml.safe_load`. pyyaml_subs already collects
    # the `yaml` package, but we add the explicit names below as
    # belt-and-suspenders in case collect_submodules misses the C-extension
    # shim on a build host (RKOJ-ELENO 2026-05-21).
    + ["yaml", "pyyaml", "_yaml"]
)

datas = forge_data + sinister_data + textual_data + rich_data + anthropic_data

binaries = []
# Textual uses some compiled bits on Windows; pull them via collect_dynamic_libs
try:
    binaries += collect_dynamic_libs("textual")
except Exception:
    pass


# --- Analysis ---------------------------------------------------------------

block_cipher = None

a = Analysis(
    ["RKOJ-entry.py"],
    pathex=[
        # Make Forge + sinister-X discoverable to the analyzer even though
        # they're already installed (editable installs sometimes confuse the
        # collector).
        r"D:\Sinister Sanctum\projects\sinister-forge\source",
        r"D:\Sinister Sanctum\tools\sinister-cli",
        r"D:\Sinister Sanctum\tools\sinister-login",
        r"D:\Sinister Sanctum\tools\sinister-usage",
        r"D:\Sinister Sanctum\tools\sinister-model",
        r"D:\Sinister Sanctum\tools\sinister-swarm",
        r"D:\Sinister Sanctum\tools\sinister-jcode-shim",
        r"D:\Sinister Sanctum\tools\forge-memory-bridge",
        r"D:\Sinister Sanctum\tools\memory-graph-render",
        r"D:\Sinister Sanctum\tools\sanctum-backup",
    ],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Heavy deps we never use at runtime.
        "tkinter",
        "matplotlib",
        "scipy",
        # numpy WAS excluded — re-enabled v0.1.2 because rank_bm25 (BM25
        # re-scoring on forge_memory_bridge.recall() return path) depends
        # on it. ~25 MB cost is acceptable for jcode parity.
        # "numpy",
        "pandas",
        "PIL",
        "PyQt5",
        "PyQt6",
        "PySide2",
        "PySide6",
        "wx",
        # NOT excluding distutils — see brain doctrine.
        "pip",
        "setuptools",
        "pydoc",
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="RKOJ",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                 # UPX often breaks Windows AV scans; skip.
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,              # Textual TUI needs a real terminal.
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=r"D:\Sinister Sanctum\automations\window-manager\web\sinister-logo.ico",
)
