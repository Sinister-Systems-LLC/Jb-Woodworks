# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
"""
Sinister Sanctum :: Desktop App (pywebview wrapper)

Boots uvicorn in a background thread and opens a native window pointing at
http://127.0.0.1:5077. Works as a real desktop application (no browser
chrome). Logo + icon use the operator's Sinister logo PNG.

Self-discovers the Sanctum folder across common locations so this .exe works
even when given to Leo on a different machine.

Run:
    .venv\\Scripts\\python.exe desktop_app.py
or via the Sanctum-Console.exe (built via PyInstaller from this file).
"""
from __future__ import annotations

import argparse
import multiprocessing
import os
import sys
import threading
import time
from pathlib import Path

# PyInstaller multiprocessing hook MUST be called before anything else when
# running as a frozen .exe. Otherwise child processes re-execute the launcher
# and we get infinite respawn / port-bind failures.
multiprocessing.freeze_support()


# ---- Bootloader-error capture: redirect early-boot exceptions to a log file
# next to the EXE BEFORE any other import that could fail. This catches
# ModuleNotFoundError thrown by PyInstaller's bootstrap (e.g. 'select',
# 'selectors') which fire BEFORE our excepthook is installed.
# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
def _early_boot_log(msg: str) -> None:
    try:
        if getattr(sys, "frozen", False):
            log_dir = Path(sys.executable).resolve().parent
        else:
            log_dir = Path(__file__).resolve().parent / "_daemon-logs"
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            return
        with open(log_dir / "_exe-boot.log", "a", encoding="utf-8") as f:
            f.write(f"[{time.time():.3f}] {msg}\n")
    except Exception:
        pass


try:
    _early_boot_log(f"boot: frozen={getattr(sys, 'frozen', False)} argv={sys.argv}")
except Exception:
    pass


# ---- Patch None stdout/stderr in PyInstaller windowed builds ----
# In console=False frozen builds, ALL of sys.stdout/stderr/__stdout__/__stderr__
# are None. uvicorn's DefaultFormatter calls sys.stdout.isatty() at config time
# -> AttributeError -> server never starts. Replace with devnull-backed streams
# BEFORE any uvicorn / fastapi import. See knowledge: exe-silent-crash-no-popup.md
import io as _io
def _ensure_stream(attr_name: str) -> None:
    s = getattr(sys, attr_name, None)
    if s is None:
        try:
            setattr(sys, attr_name, open(os.devnull, 'w', encoding='utf-8'))
        except Exception:
            # io.StringIO works as a last-resort fake stream
            setattr(sys, attr_name, _io.StringIO())
for _attr in ('stdout', 'stderr', '__stdout__', '__stderr__'):
    _ensure_stream(_attr)


# ---- Runtime safety-net: log uncaught exceptions to a file next to the EXE ----
# Why: PyInstaller windowed builds (console=False) close stdout/stderr in the
# child process. Any runtime exception dies silently — no popup, no Event Log
# entry. Without this hook, debugging an EXE crash requires rebuilding with
# console=True. With it, the operator just sends us `_exe-runtime.log`.
# See knowledge: exe-silent-crash-no-popup.md
def _install_runtime_logger() -> None:
    import logging
    import traceback
    # Log file lives next to the EXE (or next to this script when running from source).
    if getattr(sys, "frozen", False):
        log_dir = Path(sys.executable).resolve().parent
    else:
        log_dir = Path(__file__).resolve().parent / "_daemon-logs"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        return
    log_path = log_dir / "_exe-runtime.log"
    try:
        logging.basicConfig(
            filename=str(log_path),
            level=logging.DEBUG,
            format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
            force=True,
        )
        logging.info("===== EXE boot =====")
        logging.info("frozen=%s sys.executable=%s argv=%s",
                     getattr(sys, "frozen", False), sys.executable, sys.argv)

        def _excepthook(exctype, value, tb):
            logging.critical("UNCAUGHT EXCEPTION:\n%s",
                             "".join(traceback.format_exception(exctype, value, tb)))
            # PyInstaller windowed builds (console=False) set sys.__stderr__ to None.
            # Touching .write on None throws AttributeError -> cascading silent crash.
            # Guard so the EXE survives even if a downstream excepthook is fired.
            if sys.__stderr__ is not None:
                try:
                    sys.__stderr__.write("UNCAUGHT EXCEPTION (see _exe-runtime.log)\n")
                    sys.__stderr__.flush()
                except Exception:
                    pass

        sys.excepthook = _excepthook

        # threading exceptions need a separate hook in 3.8+
        try:
            import threading as _th
            def _thread_excepthook(args):
                logging.critical("UNCAUGHT THREAD EXCEPTION in %s:\n%s",
                                 args.thread.name,
                                 "".join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback)))
            _th.excepthook = _thread_excepthook
        except Exception:
            pass
    except Exception:
        # Logging is best-effort. Never break boot because logging setup failed.
        pass


_install_runtime_logger()


def _frozen() -> bool:
    return getattr(sys, "frozen", False)


# When frozen via PyInstaller, files bundled by `--add-data` live next to the
# executable in `sys._MEIPASS`. When running from source, they live next to
# this script.
if _frozen():
    HERE = Path(sys._MEIPASS)  # type: ignore[attr-defined]
else:
    HERE = Path(__file__).resolve().parent

WEB_DIR = HERE / "web"
LOGO_PNG = WEB_DIR / "sinister-logo.png"


def discover_sanctum_root() -> Path | None:
    """Find the Sinister Sanctum folder across common drive letters / paths.
    The .exe needs to talk to projects.json, _vault, _shared-memory, etc.
    Order: env var > D:\\Sinister Sanctum > C:\\Sinister Sanctum > E:\\... >
    parent folder of this script (dev mode)."""
    env = os.environ.get("SINISTER_SANCTUM_ROOT")
    if env and Path(env).is_dir():
        return Path(env)
    candidates = [
        Path(r"D:\Sinister Sanctum"),
        Path(r"C:\Sinister Sanctum"),
        Path(r"E:\Sinister Sanctum"),
        Path(r"F:\Sinister Sanctum"),
        Path(r"G:\Sinister Sanctum"),
        Path.home() / "Sinister Sanctum",
    ]
    # Also try parent-of-parent (dev mode: this lives in <root>/automations/window-manager/)
    if not _frozen():
        candidates.insert(0, HERE.parent.parent)
    for c in candidates:
        try:
            if c.is_dir() and (c / "SANCTUM.md").exists():
                return c
        except Exception:
            continue
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=5077)
    ap.add_argument("--lan", action="store_true", help="bind 0.0.0.0 (LAN access)")
    ap.add_argument("--no-window", action="store_true", help="server only, no desktop window")
    # Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
    # Hot-reload sprint. uvicorn --reload watches source files and respawns
    # the worker on change. SOURCE-MODE ONLY — the PyInstaller frozen EXE
    # doesn't carry .py source paths watchdog can follow, so the flag is a
    # no-op there (we explicitly suppress with a warning). For the live
    # surface (CSS/JS/templates) the SSE channel + watchdog observer inside
    # server.py do the work without restarting the worker.
    ap.add_argument("--reload", action="store_true",
                    help="(dev-mode only) hot-reload uvicorn worker on .py change. Ignored in frozen EXE.")
    args = ap.parse_args()

    # Discover Sanctum root + export for server.py to use
    root = discover_sanctum_root()
    if root:
        os.environ["SINISTER_SANCTUM_ROOT"] = str(root)
        print(f"[OK] Sinister Sanctum found at: {root}", flush=True)
    else:
        print("[WARN] Sinister Sanctum folder not auto-discovered.", flush=True)
        print("       Set SINISTER_SANCTUM_ROOT env var or place Sanctum at D:\\Sinister Sanctum\\", flush=True)
        # Continue anyway — server.py will use its hard-coded fallback paths.

    host = "0.0.0.0" if args.lan else "127.0.0.1"
    public_url = f"http://127.0.0.1:{args.port}/"

    # ---- start uvicorn in background ----
    def run_uvicorn():
        import os
        os.environ["SINISTER_SERVER_HOST"] = host
        os.environ["SINISTER_SERVER_PORT"] = str(args.port)
        if args.lan:
            os.environ["SINISTER_LAN"] = "1"
        import uvicorn
        # Inject sys.path so `server` is importable from this dir
        if str(HERE) not in sys.path:
            sys.path.insert(0, str(HERE))
        # Hot-reload: only honor --reload when running from source. The frozen
        # EXE has no .py paths watchdog can map back, so attempting reload there
        # just spawns ghost processes that fail to import.
        reload_on = bool(args.reload) and not _frozen()
        if args.reload and _frozen():
            print("[WARN] --reload requested but frozen EXE doesn't support it; ignoring", flush=True)
        if reload_on:
            print(f"[OK] uvicorn --reload watching {HERE} for .py changes", flush=True)
            cfg = uvicorn.Config(
                "server:app", host=host, port=args.port, log_level="warning",
                loop="asyncio", reload=True, reload_dirs=[str(HERE)],
            )
        else:
            cfg = uvicorn.Config("server:app", host=host, port=args.port, log_level="warning", loop="asyncio")
        srv = uvicorn.Server(cfg)
        try:
            srv.run()
        except Exception as e:
            print(f"[uvicorn fatal] {e}", file=sys.stderr)

    t = threading.Thread(target=run_uvicorn, daemon=True)
    t.start()

    # Wait for the server to bind.
    # SS-D speed audit (Sinister Sanctum master agent (Claude) :: 2026-05-19):
    # Poll interval was 300 ms which meant ~150 ms average extra wait after
    # uvicorn had already bound. Tightened to 25 ms (10x more responsive) plus
    # a shorter connect timeout — measured EXE cold boot dominated by fastapi
    # import (~26 s on first launch, ~250 ms warm) so any 100-300 ms here that
    # we can shave is a noticeable subjective win on warm restarts (e.g. after
    # `--reload`). Keep the 15s overall deadline.
    import socket
    deadline = time.time() + 15
    bound = False
    while time.time() < deadline:
        try:
            s = socket.create_connection(("127.0.0.1", args.port), timeout=0.25)
            s.close()
            bound = True
            break
        except Exception:
            time.sleep(0.025)
    if not bound:
        print(f"[ERR] uvicorn did not bind on port {args.port} within 15s", file=sys.stderr)
        return 2
    print(f"[OK] Sanctum console up at {public_url}", flush=True)
    if args.lan:
        try:
            host_ip = socket.gethostbyname(socket.gethostname())
            print(f"[LAN] also reachable at http://{host_ip}:{args.port}/", flush=True)
        except Exception:
            pass

    if args.no_window:
        # Block forever so uvicorn keeps running
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            return 0

    # ---- desktop window via pywebview ----
    import webview
    win = webview.create_window(
        title="RKOJ :: Workbench",
        url=public_url,
        width=1280,
        height=820,
        min_size=(900, 600),
        background_color="#0E0E12",
        text_select=True,
        confirm_close=False,
    )

    # Optional: try to set a window icon (pywebview's icon support varies; Edge
    # WebView2 picks up the page's <link rel="icon"> which already points to
    # /static/sinister-logo.png).

    webview.start(debug=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
