# -*- mode: python ; coding: utf-8 -*-
# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
# RKOJ.spec :: PyInstaller spec for RKOJ.exe (renamed 2026-05-19 from
# Sanctum-Console.spec). The rename + sanctum_shared/ package swap is the
# fix for HR-B audit finding: the previous data-tuple form
# ('_shared', '_shared') was being silently dropped by PyInstaller's
# underscore-prefix collection logic, so the EXE shipped without
# cycle_points + scheduler. We now use collect_submodules +
# collect_data_files against the renamed `sanctum_shared` package, which
# PyInstaller picks up cleanly.
#
# server.py import surface confirmed:
#   fastapi: FastAPI, HTTPException, Request, responses.{FileResponse,JSONResponse,
#            RedirectResponse,Response,StreamingResponse}, staticfiles.StaticFiles
#   pydantic: BaseModel  |  httpx: top-level  |  qrcode: qrcode.make() only
#   starlette: NOT imported directly (transitive via fastapi)
#   webview: desktop_app.py only (keep collect_all - many backend files)
#   sanctum_shared: cycle_points, scheduler (local, ./sanctum_shared/)
from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_data_files

datas = [
    ('web', 'web'),
    ('auth.py', '.'),
    ('server.py', '.'),
    ('memory_sanitizer.py', '.'),
]
binaries = []
hiddenimports = [
    'uvicorn.logging',
    'uvicorn.loops.auto',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan.on',
    'websockets',
    'httptools',
    'multiprocessing',
    # 2026-05-19 master sweep: bootloader crash repro showed
    # `ModuleNotFoundError: No module named 'select'` during
    # pyi_rth_multiprocessing -> selectors.py:12. PyInstaller's autodetect
    # missed it on this build; declare the stdlib network/select chain
    # explicitly so it ships in _internal/.
    'select',
    '_socket',
    'socket',
    'selectors',
    'multiprocessing.context',
    'multiprocessing.reduction',
    'multiprocessing.popen_spawn_win32',
    'multiprocessing.queues',
    'multiprocessing.synchronize',
    'multiprocessing.connection',
    'multiprocessing.shared_memory',
    'multiprocessing.heap',
    'asyncio',
    'asyncio.selector_events',
    'asyncio.windows_events',
    'asyncio.proactor_events',
]

# --- sanctum_shared: explicit collection so cycle_points + scheduler ship in
# the bundle. Was the silent-drop bug as `_shared` (underscore prefix).
hiddenimports += collect_submodules('sanctum_shared')
datas += collect_data_files('sanctum_shared', include_py_files=True)

tmp_ret = collect_all('uvicorn')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('fastapi')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('starlette')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('httpx')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('httpcore')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('h11')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('anyio')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('pydantic')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('pydantic_core')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('webview')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('qrcode')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['desktop_app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # 2026-05-19 PERF-B: prune definitely-unused stdlib + tooling from _internal/.
    # All entries verified by grep across server.py / desktop_app.py / auth.py /
    # memory_sanitizer.py - none reference any of these. Each saves cold-import
    # scan time + disk bytes (rough estimate: ~5-15 MB + 1-3s boot).
    # Skipped (need rebuild-and-test cycle): email.message (httpx flows),
    # xml.etree.ElementTree (qrcode SVG factory - unused but qrcode imports it),
    # removing collect_all('starlette') (fastapi pulls it transitively but hook
    # behavior varies by version - leaving intact until measurable rebuild test).
    excludes=[
        'tkinter',        # using pywebview, never tkinter
        '_tkinter',       # tkinter C-ext
        'turtle',         # depends on tkinter
        'turtledemo',
        'unittest',       # no in-EXE tests
        'test',           # stdlib test suite
        'tests',          # package test suites
        'pytest',         # no in-EXE pytest
        '_pytest',
        'setuptools',     # no runtime install
        'pip',            # no runtime install
        # 'distutils' INTENTIONALLY NOT EXCLUDED here -- PyInstaller's own
        # hook-distutils.py aliases distutils to a vendored name during the
        # pre_safe_import_module phase. If we exclude distutils first, that
        # alias fails with "Target module 'distutils' already imported as
        # 'ExcludedModule'". Brain entry: distutils-exclude-collision.md.
        # The actual cost of including distutils is tiny (~50KB), not worth
        # the build failure. Reproduced 2026-05-19 with PyInstaller 6.20.0.
        'pydoc',          # no in-EXE doc browser
        'pydoc_data',
        'doctest',        # no doctests in EXE
        'idlelib',        # IDLE shell
        'lib2to3',        # Python 2 -> 3 converter
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='RKOJ',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['web\\sinister-logo.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='RKOJ',
)
