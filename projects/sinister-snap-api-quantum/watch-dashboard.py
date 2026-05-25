"""Iter 109 - Auto-re-render the dashboard HTML when its markdown changes.

Author: RKOJ-ELENO :: 2026-05-24

Companion to serve-dashboard.py. Polls outputs/sanctum-quantum-dashboard.md every
3s; when mtime changes, regenerates outputs/sanctum-quantum-dashboard.html.
Operator hits browser-refresh → sees latest content.

Usage:
    python watch-dashboard.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

PROJ_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJ_ROOT))

# Reuse build_html() from serve-dashboard.py
import importlib.util
spec = importlib.util.spec_from_file_location('serve_dashboard', PROJ_ROOT / 'serve-dashboard.py')
serve_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(serve_mod)

MD_PATH = serve_mod.MD_PATH
HTML_PATH = serve_mod.HTML_PATH


def main() -> int:
    if not MD_PATH.exists():
        print(f'ERROR: dashboard markdown not found at {MD_PATH}')
        return 2
    last_mt = 0.0
    print(f'[watch-dashboard] watching {MD_PATH}')
    print(f'[watch-dashboard] re-renders to {HTML_PATH} on change')
    while True:
        try:
            mt = MD_PATH.stat().st_mtime
            if mt != last_mt:
                html_doc = serve_mod.build_html()
                HTML_PATH.write_text(html_doc, encoding='utf-8')
                ts = time.strftime('%H:%M:%S', time.localtime())
                print(f'[{ts}] re-rendered ({len(html_doc):,} bytes)')
                last_mt = mt
            time.sleep(3)
        except KeyboardInterrupt:
            print('\n[watch-dashboard] stopped')
            return 0


if __name__ == '__main__':
    sys.exit(main())
