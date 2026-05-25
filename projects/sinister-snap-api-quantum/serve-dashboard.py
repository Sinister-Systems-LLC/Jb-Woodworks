"""Iter 109 - Live dashboard server: render outputs/sanctum-quantum-dashboard.md → HTML +
serve on localhost. Operator: 'place dshaboard live on lcoal host and open in brwoser'.

Author: RKOJ-ELENO :: 2026-05-24

Inherits dashboard-skeleton design tokens (purple accent per fleet hard-canonical
2026-05-24 15:44Z 'EXPAND-never-fork'). Markdown rendered with a minimal inline
converter (no pip deps). Server: stdlib http.server on port 8765.

Usage:
    python serve-dashboard.py [--port 8765] [--no-browser]
"""
from __future__ import annotations

import argparse
import html
import http.server
import re
import socketserver
import sys
import threading
import time
import webbrowser
from pathlib import Path

PROJ_ROOT = Path(__file__).resolve().parent
OUTPUTS = PROJ_ROOT / 'outputs'
MD_PATH = OUTPUTS / 'sanctum-quantum-dashboard.md'
HTML_PATH = OUTPUTS / 'sanctum-quantum-dashboard.html'

CSS = """
:root {
  --bg: #0a0a0f;
  --bg-elev: #14141d;
  --bg-card: #1a1a26;
  --border: #2a2a3a;
  --text: #e5e5ed;
  --text-dim: #9090a0;
  --text-soft: #b8b8c8;
  --accent: #c084fc;        /* Sinister purple per fleet hard-canonical 2026-05-24 15:44Z */
  --accent-soft: rgba(192, 132, 252, 0.15);
  --accent-ring: rgba(192, 132, 252, 0.40);
  --ok: #4ade80;
  --warn: #fbbf24;
  --fail: #f87171;
  --code-bg: #0f0f17;
}
* { box-sizing: border-box; }
html, body {
  margin: 0; padding: 0;
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
  font-size: 14px;
  line-height: 1.55;
}
.wrap {
  max-width: 1200px;
  margin: 0 auto;
  padding: 32px 24px 64px;
}
.banner {
  background: linear-gradient(135deg, var(--accent-soft) 0%, transparent 60%);
  border: 1px solid var(--border);
  border-left: 3px solid var(--accent);
  border-radius: 8px;
  padding: 20px 24px;
  margin-bottom: 24px;
}
.banner h1 {
  margin: 0 0 6px;
  font-size: 22px;
  font-weight: 600;
  color: var(--text);
}
.banner .sub {
  font-size: 12px;
  color: var(--text-dim);
}
.banner .accent { color: var(--accent); }
h1, h2, h3, h4 {
  color: var(--text);
  font-weight: 600;
}
h1 { font-size: 26px; margin: 32px 0 12px; }
h2 { font-size: 19px; margin: 28px 0 10px; padding-bottom: 6px; border-bottom: 1px solid var(--border); }
h3 { font-size: 16px; margin: 22px 0 8px; color: var(--accent); }
h4 { font-size: 14px; margin: 18px 0 6px; color: var(--text-soft); }
p { margin: 8px 0; color: var(--text-soft); }
ul, ol { margin: 8px 0 12px; padding-left: 24px; color: var(--text-soft); }
li { margin: 3px 0; }
strong { color: var(--text); font-weight: 600; }
em { color: var(--text-dim); }
code {
  background: var(--code-bg);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 1px 6px;
  font-family: "JetBrains Mono", "Consolas", monospace;
  font-size: 12.5px;
  color: var(--accent);
}
pre {
  background: var(--code-bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 12px 16px;
  overflow-x: auto;
  font-family: "JetBrains Mono", "Consolas", monospace;
  font-size: 12.5px;
  color: var(--text-soft);
}
pre code { background: none; border: none; padding: 0; color: inherit; }
hr {
  border: none;
  border-top: 1px solid var(--border);
  margin: 28px 0;
}
table {
  border-collapse: collapse;
  width: 100%;
  margin: 12px 0 20px;
  font-size: 13px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 6px;
  overflow: hidden;
}
th, td {
  padding: 8px 12px;
  text-align: left;
  border-bottom: 1px solid var(--border);
}
th {
  background: var(--bg-elev);
  color: var(--accent);
  font-weight: 600;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
tr:last-child td { border-bottom: none; }
tr:hover { background: var(--accent-soft); }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
blockquote {
  border-left: 3px solid var(--accent);
  background: var(--accent-soft);
  padding: 10px 16px;
  margin: 12px 0;
  color: var(--text-soft);
}
.tag-high { color: var(--fail); }
.tag-med { color: var(--warn); }
.tag-low { color: var(--ok); }
.foot {
  margin-top: 48px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
  font-size: 12px;
  color: var(--text-dim);
  text-align: center;
}
"""


def md_to_html(md: str) -> str:
    """Minimal stdlib markdown → HTML converter for the dashboard's feature set."""
    lines = md.split('\n')
    out: list[str] = []
    i = 0
    in_table = False
    table_rows: list[list[str]] = []
    in_list_ul = False
    in_list_ol = False
    in_blockquote = False
    in_code = False

    def close_table():
        nonlocal in_table, table_rows
        if not table_rows:
            in_table = False
            return
        header = table_rows[0]
        body = table_rows[2:] if len(table_rows) > 2 else []
        out.append('<table>')
        out.append('<thead><tr>' + ''.join(f'<th>{c}</th>' for c in header) + '</tr></thead>')
        if body:
            out.append('<tbody>')
            for row in body:
                out.append('<tr>' + ''.join(f'<td>{c}</td>' for c in row) + '</tr>')
            out.append('</tbody>')
        out.append('</table>')
        table_rows = []
        in_table = False

    def close_list():
        nonlocal in_list_ul, in_list_ol
        if in_list_ul:
            out.append('</ul>')
            in_list_ul = False
        if in_list_ol:
            out.append('</ol>')
            in_list_ol = False

    def inline(s: str) -> str:
        # Escape first, then re-introduce safe inline markdown
        s = html.escape(s, quote=False)
        # Bold **x**
        s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
        # Code `x`
        s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
        # Link [text](url)
        s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', s)
        # Emoji-only or color tags stay as-is
        return s

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Code fence
        if stripped.startswith('```'):
            close_list()
            if in_table:
                close_table()
            if not in_code:
                lang = stripped[3:].strip()
                out.append('<pre><code class="lang-' + html.escape(lang) + '">')
                in_code = True
            else:
                out.append('</code></pre>')
                in_code = False
            i += 1
            continue

        if in_code:
            out.append(html.escape(line, quote=False))
            i += 1
            continue

        # Blockquote
        if stripped.startswith('>'):
            close_list()
            if in_table:
                close_table()
            if not in_blockquote:
                out.append('<blockquote>')
                in_blockquote = True
            out.append(inline(stripped[1:].strip()) + '<br>')
            i += 1
            continue
        elif in_blockquote and not stripped.startswith('>'):
            out.append('</blockquote>')
            in_blockquote = False

        # HTML comment passthrough (skip)
        if stripped.startswith('<!--') and stripped.endswith('-->'):
            i += 1
            continue

        # Table row
        if stripped.startswith('|') and stripped.endswith('|'):
            close_list()
            if not in_table:
                in_table = True
                table_rows = []
            cells = [inline(c.strip()) for c in stripped[1:-1].split('|')]
            table_rows.append(cells)
            i += 1
            continue
        elif in_table:
            close_table()

        # Heading
        m = re.match(r'^(#{1,4})\s+(.*)', stripped)
        if m:
            close_list()
            if in_table:
                close_table()
            level = len(m.group(1))
            out.append(f'<h{level}>{inline(m.group(2))}</h{level}>')
            i += 1
            continue

        # Horizontal rule
        if stripped in ('---', '***', '___'):
            close_list()
            if in_table:
                close_table()
            out.append('<hr>')
            i += 1
            continue

        # Unordered list
        m = re.match(r'^[-*+]\s+(.*)', stripped)
        if m:
            if in_table:
                close_table()
            if in_list_ol:
                out.append('</ol>')
                in_list_ol = False
            if not in_list_ul:
                out.append('<ul>')
                in_list_ul = True
            out.append(f'<li>{inline(m.group(1))}</li>')
            i += 1
            continue

        # Ordered list
        m = re.match(r'^(\d+)\.\s+(.*)', stripped)
        if m:
            if in_table:
                close_table()
            if in_list_ul:
                out.append('</ul>')
                in_list_ul = False
            if not in_list_ol:
                out.append('<ol>')
                in_list_ol = True
            out.append(f'<li>{inline(m.group(2))}</li>')
            i += 1
            continue

        # Blank line / paragraph break
        if not stripped:
            close_list()
            i += 1
            continue

        # Plain paragraph
        close_list()
        out.append(f'<p>{inline(stripped)}</p>')
        i += 1

    close_list()
    if in_table:
        close_table()
    if in_blockquote:
        out.append('</blockquote>')
    if in_code:
        out.append('</code></pre>')
    return '\n'.join(out)


def _live_activity_html() -> str:
    """Inject a Live Activity panel of recent quantum-sweep JSONs (top-15 by mtime)."""
    sweeps_dir = PROJ_ROOT.parent.parent / '_shared-memory' / 'quantum-sweeps'
    if not sweeps_dir.exists():
        return ''
    files = sorted(sweeps_dir.glob('*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return ''
    now = time.time()
    rows = []
    for p in files[:15]:
        age_s = now - p.stat().st_mtime
        if age_s < 60:
            age = f'{int(age_s)}s ago'
        elif age_s < 3600:
            age = f'{int(age_s/60)}m ago'
        elif age_s < 86400:
            age = f'{int(age_s/3600)}h ago'
        else:
            age = f'{int(age_s/86400)}d ago'
        # Extract label from filename
        label = p.stem.replace('-corpus-qbc-', ' :: corpus-qbc ').replace('-reconcile-', ' :: reconcile ')
        # Cut the UTC suffix
        label = re.sub(r'\s+2026-\d{2}-\d{2}T\d{6}Z$', '', label)
        rows.append(f'<tr><td>{html.escape(label)}</td><td class="num">{age}</td></tr>')
    table = (
        '<h2>Live Activity</h2>'
        '<p style="color:var(--text-dim);font-size:12px;margin-bottom:8px">'
        'Most-recent 15 quantum-sweep outputs (refresh browser tab to see new ones).'
        '</p>'
        '<table>'
        '<thead><tr><th>Sweep</th><th class="num">Age</th></tr></thead>'
        '<tbody>' + ''.join(rows) + '</tbody>'
        '</table>'
    )
    return table


def build_html() -> str:
    md = MD_PATH.read_text(encoding='utf-8')
    body = md_to_html(md)
    live_activity = _live_activity_html()
    ts = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sinister Quantum Dashboard</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
  <div class="banner">
    <h1><span class="accent">⟁</span> Sinister Quantum-Tools Dashboard</h1>
    <div class="sub">
      Live fleet rollup from <code>projects/sinister-snap-api-quantum/</code> ·
      Last rendered: {ts} ·
      <a href="/sanctum-quantum-dashboard.md">view raw markdown</a>
    </div>
  </div>
  {body}
  {live_activity}
  <div class="foot">
    Generated by <code>serve-dashboard.py</code> · Author: RKOJ-ELENO :: 2026-05-24 ·
    Inherits dashboard-skeleton tokens (purple accent per fleet hard-canonical 2026-05-24 15:44Z)
  </div>
</div>
</body>
</html>
"""


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        # Suppress per-request log spam; keep only errors
        if '404' in fmt or '500' in fmt:
            super().log_message(fmt, *args)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8765)
    ap.add_argument('--no-browser', action='store_true')
    args = ap.parse_args()

    if not MD_PATH.exists():
        print(f'ERROR: dashboard markdown not found at {MD_PATH}')
        return 2

    html_doc = build_html()
    HTML_PATH.write_text(html_doc, encoding='utf-8')
    print(f'[serve-dashboard] rendered {HTML_PATH}  ({len(html_doc):,} bytes)')

    # Serve outputs/ so the .md raw view also works
    import os
    os.chdir(OUTPUTS)

    with socketserver.TCPServer(('127.0.0.1', args.port), QuietHandler) as httpd:
        url = f'http://127.0.0.1:{args.port}/sanctum-quantum-dashboard.html'
        print(f'[serve-dashboard] serving {OUTPUTS} on {url}')
        print(f'[serve-dashboard] press Ctrl+C to stop')
        if not args.no_browser:
            threading.Timer(0.5, lambda: webbrowser.open(url)).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\n[serve-dashboard] stopped')
            return 0
    return 0


if __name__ == '__main__':
    sys.exit(main())
