"""Self-contained HTML dashboard generator for sinister-seraphim.

Author: RKOJ-ELENO :: 2026-05-23

`seraphim dashboard [--out path]` writes a single static HTML file with
the current budget + provenance ledger + recent QRNG/fingerprint calls
embedded directly. No server, no JS framework, no operator setup —
just open the file in a browser.

Default output: _shared-memory/dashboards/seraphim.html
"""
from __future__ import annotations

import html
import json
import os
import time
from pathlib import Path

SANCTUM_ROOT = Path(os.environ.get('SINISTER_SANCTUM_ROOT', r'D:\Sinister Sanctum'))
PROVENANCE_DIR = SANCTUM_ROOT / '_shared-memory' / 'qrng-provenance'
LEDGER_FILE = SANCTUM_ROOT / '_shared-memory' / 'seraphim-cloud-ledger.jsonl'
BUDGET_FILE = SANCTUM_ROOT / '_shared-memory' / 'seraphim-cloud-budget.json'
DEFAULT_OUT = SANCTUM_ROOT / '_shared-memory' / 'dashboards' / 'seraphim.html'


def _load_budget() -> dict:
    if not BUDGET_FILE.exists():
        return {'total_seconds': 120.0, 'used_seconds': 0.0, 'reserve_seconds': 10.0}
    try:
        return json.loads(BUDGET_FILE.read_text(encoding='utf-8'))
    except Exception:
        return {'total_seconds': 120.0, 'used_seconds': 120.0, 'note': 'CORRUPT'}


def _load_provenance(limit: int = 50) -> list[dict]:
    if not PROVENANCE_DIR.exists():
        return []
    files = sorted(
        PROVENANCE_DIR.glob('*.json'),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )[:limit]
    out = []
    for f in files:
        try:
            rec = json.loads(f.read_text(encoding='utf-8'))
            rec['_filename'] = f.name
            out.append(rec)
        except Exception:
            continue
    return out


def _load_ledger() -> list[dict]:
    if not LEDGER_FILE.exists():
        return []
    out = []
    for line in LEDGER_FILE.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def render_html() -> str:
    budget = _load_budget()
    provenance = _load_provenance(limit=50)
    ledger = _load_ledger()

    total = float(budget.get('total_seconds', 120.0))
    used = float(budget.get('used_seconds', 0.0))
    remaining = max(0.0, total - used)
    used_pct = (used / total * 100.0) if total > 0 else 0.0
    now_utc = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())

    # Stats from provenance
    by_backend: dict[str, int] = {}
    by_purpose: dict[str, int] = {}
    total_bytes = 0
    for rec in provenance:
        b = str(rec.get('backend', 'unknown'))
        by_backend[b] = by_backend.get(b, 0) + 1
        p = str(rec.get('purpose', 'unknown'))
        by_purpose[p] = by_purpose.get(p, 0) + 1
        nb = rec.get('n_bytes')
        if isinstance(nb, int):
            total_bytes += nb

    backend_rows = ''.join(
        f'<tr><td>{html.escape(b)}</td><td class="num">{n}</td></tr>'
        for b, n in sorted(by_backend.items(), key=lambda kv: -kv[1])
    ) or '<tr><td colspan="2" class="dim">no calls yet</td></tr>'

    purpose_rows = ''.join(
        f'<tr><td>{html.escape(p)}</td><td class="num">{n}</td></tr>'
        for p, n in sorted(by_purpose.items(), key=lambda kv: -kv[1])[:10]
    ) or '<tr><td colspan="2" class="dim">no calls yet</td></tr>'

    prov_rows = ''
    for rec in provenance[:30]:
        ts = html.escape(str(rec.get('ts_utc', '?')))
        purp = html.escape(str(rec.get('purpose', '?')))
        bk = html.escape(str(rec.get('backend', '?')))
        nb = rec.get('n_bytes') or rec.get('n_shots') or ''
        lic = html.escape(str(rec.get('license_fp_sha256_12') or '—'))
        prov_rows += f'<tr><td class="mono dim">{ts}</td><td>{purp}</td><td>{bk}</td><td class="num">{nb}</td><td class="mono dim">{lic}</td></tr>'
    if not prov_rows:
        prov_rows = '<tr><td colspan="5" class="dim">no provenance records yet — run `seraphim qrng -n 16` or similar to populate</td></tr>'

    ledger_rows = ''
    for rec in ledger[-20:][::-1]:
        ts = html.escape(str(rec.get('ts_utc', '?')))
        purp = html.escape(str(rec.get('purpose', '?')))
        secs = rec.get('actual_seconds', 0)
        rem = rec.get('remaining_after_seconds', '?')
        ledger_rows += f'<tr><td class="mono dim">{ts}</td><td>{purp}</td><td class="num">{secs:.3f}s</td><td class="num">{rem}</td></tr>'
    if not ledger_rows:
        ledger_rows = '<tr><td colspan="4" class="dim">no cloud calls yet — sim-local + sim-pilotos do not debit the budget</td></tr>'

    bar_color = '#7A3DD4' if used_pct < 70 else '#FFB627' if used_pct < 90 else '#FF4D4D'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Sinister Seraphim Dashboard</title>
<style>
  body {{ font-family: 'Cascadia Code', 'Consolas', monospace; background: #0E0A1A; color: #E8D6FF; margin: 0; padding: 24px; }}
  h1 {{ color: #A06EFF; margin: 0 0 4px; font-size: 26px; }}
  h2 {{ color: #C8A4FF; margin: 28px 0 12px; font-size: 16px; text-transform: uppercase; letter-spacing: 1px; }}
  .meta {{ color: #888; font-size: 12px; margin-bottom: 24px; }}
  .card {{ background: #1A1228; border: 1px solid #2D1F40; border-radius: 6px; padding: 16px; margin-bottom: 16px; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }}
  .big {{ font-size: 28px; color: #A06EFF; font-weight: bold; }}
  .label {{ font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
  th, td {{ padding: 6px 10px; text-align: left; border-bottom: 1px solid #2D1F40; }}
  th {{ color: #C8A4FF; font-weight: normal; text-transform: uppercase; letter-spacing: 1px; font-size: 11px; }}
  td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  td.mono {{ font-family: 'Cascadia Code', 'Consolas', monospace; }}
  td.dim {{ color: #666; }}
  .bar-track {{ background: #1A1228; height: 14px; border-radius: 7px; overflow: hidden; margin-top: 8px; }}
  .bar-fill {{ height: 100%; background: {bar_color}; transition: width 0.3s; width: {used_pct:.1f}%; }}
  .warn {{ color: #FFB627; }}
  .danger {{ color: #FF4D4D; }}
  .ok {{ color: #6EFFA0; }}
</style>
</head>
<body>

<h1>Sinister Seraphim</h1>
<div class="meta">Operator's quantum-compute application layer · Origin PilotOS V4.2 wrapper · generated {html.escape(now_utc)}</div>

<div class="card">
  <h2 style="margin-top:0">Cloud-Wukong-180 Budget</h2>
  <div class="grid">
    <div>
      <div class="big">{remaining:.1f}<span style="font-size:18px;color:#888">s</span></div>
      <div class="label">remaining</div>
    </div>
    <div>
      <div class="big">{used:.1f}<span style="font-size:18px;color:#888">s</span></div>
      <div class="label">used</div>
    </div>
    <div>
      <div class="big">{total:.1f}<span style="font-size:18px;color:#888">s</span></div>
      <div class="label">total (operator cap)</div>
    </div>
  </div>
  <div class="bar-track"><div class="bar-fill"></div></div>
  <div class="meta" style="margin-top:8px">Operator hard-canonical 2026-05-23: 120s total on the license key. {budget.get('reserve_seconds', 10.0):.0f}s emergency reserve. Default backend is <strong>sim-local</strong> (os.urandom + audit trail; zero cloud cost). <strong>sim-pilotos</strong> backend runs the local V4.2 quantum sim (also zero cloud cost) once the operator extracts the python_simulator tarball.</div>
</div>

<div class="grid" style="grid-template-columns: 2fr 1fr 1fr;">
  <div class="card">
    <h2 style="margin-top:0">Recent QRNG / Provenance Calls (last 30)</h2>
    <table>
      <thead><tr><th>Time UTC</th><th>Purpose</th><th>Backend</th><th>Bytes/Shots</th><th>License FP</th></tr></thead>
      <tbody>{prov_rows}</tbody>
    </table>
  </div>
  <div class="card">
    <h2 style="margin-top:0">By Backend</h2>
    <table>
      <thead><tr><th>Backend</th><th>Calls</th></tr></thead>
      <tbody>{backend_rows}</tbody>
    </table>
    <div class="meta" style="margin-top:12px">Total provenance records: <strong>{len(provenance)}</strong><br>Total bytes (sim-local): <strong>{total_bytes:,}</strong></div>
  </div>
  <div class="card">
    <h2 style="margin-top:0">Top Purposes</h2>
    <table>
      <thead><tr><th>Purpose</th><th>Calls</th></tr></thead>
      <tbody>{purpose_rows}</tbody>
    </table>
  </div>
</div>

<div class="card">
  <h2 style="margin-top:0">Cloud-Wukong-180 Ledger (last 20)</h2>
  <table>
    <thead><tr><th>Time UTC</th><th>Purpose</th><th>Seconds</th><th>Remaining After</th></tr></thead>
    <tbody>{ledger_rows}</tbody>
  </table>
</div>

<div class="meta">
  Source files (read-only by this dashboard):<br>
  &nbsp;&nbsp;Budget: <span class="mono">{html.escape(str(BUDGET_FILE))}</span><br>
  &nbsp;&nbsp;Ledger: <span class="mono">{html.escape(str(LEDGER_FILE))}</span><br>
  &nbsp;&nbsp;Provenance dir: <span class="mono">{html.escape(str(PROVENANCE_DIR))}</span><br>
  <br>
  Regenerate this dashboard: <span class="mono">python "{html.escape(str(SANCTUM_ROOT / 'tools' / 'sinister-seraphim' / 'cli.py'))}" dashboard</span>
</div>

</body>
</html>
"""


def write_dashboard(out_path: Path | None = None) -> Path:
    p = out_path or DEFAULT_OUT
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(render_html(), encoding='utf-8')
    return p


if __name__ == '__main__':
    import sys
    out = write_dashboard()
    print(f'[seraphim.dashboard] wrote {out}')
    print(f'[seraphim.dashboard] open in browser: file:///{str(out).replace(chr(92), "/")}')
