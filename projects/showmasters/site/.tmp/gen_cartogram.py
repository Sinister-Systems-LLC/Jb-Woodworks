#!/usr/bin/env python3
TILES = [
    (10, 0, 'ME', 'Maine',          'other'),
    ( 9, 1, 'VT', 'Vermont',        'other'),
    (10, 1, 'NH', 'New Hampshire',  'other'),
    (10, 2, 'MA', 'Massachusetts',  'served'),
    ( 0, 3, 'WA', 'Washington',     'served'),
    ( 1, 3, 'ID', 'Idaho',          'other'),
    ( 2, 3, 'MT', 'Montana',        'other'),
    ( 3, 3, 'ND', 'North Dakota',   'other'),
    ( 4, 3, 'MN', 'Minnesota',      'served'),
    ( 6, 3, 'WI', 'Wisconsin',      'served'),
    ( 7, 3, 'MI', 'Michigan',       'served'),
    ( 9, 3, 'NY', 'New York',       'served'),
    (10, 3, 'CT', 'Connecticut',    'other'),
    (11, 3, 'RI', 'Rhode Island',   'other'),
    ( 0, 4, 'OR', 'Oregon',         'served'),
    ( 1, 4, 'NV', 'Nevada',         'hub'),
    ( 2, 4, 'WY', 'Wyoming',        'other'),
    ( 3, 4, 'SD', 'South Dakota',   'other'),
    ( 4, 4, 'IA', 'Iowa',           'other'),
    ( 5, 4, 'IL', 'Illinois',       'served'),
    ( 6, 4, 'IN', 'Indiana',        'served'),
    ( 7, 4, 'OH', 'Ohio',           'served'),
    ( 8, 4, 'PA', 'Pennsylvania',   'served'),
    ( 9, 4, 'NJ', 'New Jersey',     'served'),
    ( 0, 5, 'CA', 'California',     'hub'),
    ( 1, 5, 'UT', 'Utah',           'other'),
    ( 2, 5, 'CO', 'Colorado',       'hub'),
    ( 3, 5, 'NE', 'Nebraska',       'other'),
    ( 4, 5, 'MO', 'Missouri',       'served'),
    ( 5, 5, 'KY', 'Kentucky',       'other'),
    ( 6, 5, 'WV', 'West Virginia',  'other'),
    ( 7, 5, 'VA', 'Virginia',       'served'),
    ( 8, 5, 'MD', 'Maryland',       'served'),
    ( 9, 5, 'DE', 'Delaware',       'other'),
    ( 1, 6, 'AZ', 'Arizona',        'served'),
    ( 2, 6, 'NM', 'New Mexico',     'served'),
    ( 3, 6, 'KS', 'Kansas',         'served'),
    ( 4, 6, 'AR', 'Arkansas',       'served'),
    ( 5, 6, 'TN', 'Tennessee',      'hub'),
    ( 6, 6, 'NC', 'North Carolina', 'served'),
    ( 7, 6, 'SC', 'South Carolina', 'served'),
    ( 8, 6, 'DC', 'D.C.',           'served'),
    ( 2, 7, 'OK', 'Oklahoma',       'served'),
    ( 3, 7, 'LA', 'Louisiana',      'hub'),
    ( 4, 7, 'MS', 'Mississippi',    'served'),
    ( 5, 7, 'AL', 'Alabama',        'served'),
    ( 6, 7, 'GA', 'Georgia',        'hub'),
    ( 3, 8, 'TX', 'Texas - Dallas HQ',   'hq'),
    ( 7, 8, 'FL', 'Florida - Orlando Hub', 'hq'),
    ( 0, 0, 'AK', 'Alaska',         'other'),
    (11, 0, 'HI', 'Hawaii',         'other'),
]

TILE = 58
GAP  = 6
STRIDE = TILE + GAP
COLS = 12
ROWS = 10
PAD = 20
VW = PAD * 2 + COLS * STRIDE - GAP
VH = PAD * 2 + ROWS * STRIDE - GAP

STATUS_CLASS = {
    'hq':     'tile-hq',
    'hub':    'tile-hub',
    'served': 'tile-served',
    'other':  'tile-other',
}

order = ['other', 'served', 'hub', 'hq']
TILES_SORTED = sorted(TILES, key=lambda t: order.index(t[4]))

STYLE = """  <style>
    .smpl-cartogram .cartogram-tile rect { transition: fill 240ms ease, stroke 240ms ease; }
    .smpl-cartogram .tile-other rect    { fill: #18181F; stroke: rgba(255,255,255,0.05); stroke-width: 1; }
    .smpl-cartogram .tile-served rect   { fill: #2A2519; stroke: rgba(212,162,74,0.32); stroke-width: 1; }
    .smpl-cartogram .tile-hub rect      { fill: #3A2E18; stroke: rgba(212,162,74,0.85); stroke-width: 1.5; }
    .smpl-cartogram .tile-hq rect       { fill: url(#hqGrad); stroke: #FFE8B8; stroke-width: 2; filter: drop-shadow(0 0 14px rgba(212,162,74,0.55)); }
    .smpl-cartogram .cartogram-abbr     { font: 700 14px 'Inter', system-ui, sans-serif; fill: #6E6E78; letter-spacing: 1px; pointer-events: none; }
    .smpl-cartogram .tile-served .cartogram-abbr { fill: #B59A6F; }
    .smpl-cartogram .tile-hub .cartogram-abbr    { fill: #FFE8B8; }
    .smpl-cartogram .tile-hq .cartogram-abbr     { font-size: 18px; font-weight: 900; fill: #0A0A0F; letter-spacing: 2px; }
    .smpl-cartogram .cartogram-city              { font: 700 9px 'Inter', system-ui, sans-serif; fill: #0A0A0F; letter-spacing: 2.5px; pointer-events: none; }
    .smpl-cartogram .tile-hub:hover rect         { fill: #4D3B1F; }
  </style>
  <defs>
    <linearGradient id="hqGrad" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0%"  stop-color="#FFE8B8"/>
      <stop offset="100%" stop-color="#D4A24A"/>
    </linearGradient>
  </defs>"""

lines = []
lines.append(f'<svg class="smpl-cartogram" viewBox="0 0 {VW} {VH}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="US coverage map showing Show Masters service area">')
lines.append('  <title>Show Masters US service area</title>')
lines.append(STYLE)
for col, row, abbr, full, status in TILES_SORTED:
    x = PAD + col * STRIDE
    y = PAD + row * STRIDE
    cls = STATUS_CLASS[status]
    extra_attr = f' data-hub="{ "orlando" if abbr == "FL" else "dallas" }"' if status == 'hq' else ''
    lines.append(f'  <g class="cartogram-tile {cls}" data-state="{abbr.lower()}" data-status="{status}"{extra_attr}>')
    lines.append(f'    <title>{full}</title>')
    lines.append(f'    <rect x="{x}" y="{y}" width="{TILE}" height="{TILE}" rx="8" />')
    if status == 'hq':
        city = 'ORLANDO' if abbr == 'FL' else 'DALLAS'
        lines.append(f'    <text x="{x + TILE/2}" y="{y + 24}" class="cartogram-abbr" text-anchor="middle">{abbr}</text>')
        lines.append(f'    <text x="{x + TILE/2}" y="{y + 44}" class="cartogram-city" text-anchor="middle">{city}</text>')
    else:
        lines.append(f'    <text x="{x + TILE/2}" y="{y + TILE/2 + 4}" class="cartogram-abbr" text-anchor="middle">{abbr}</text>')
    lines.append('  </g>')
lines.append('</svg>')

with open(r'C:\Users\Zonia\Desktop\Showmasters Site\.tmp\cartogram.svg', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print(f'wrote {len(lines)} lines, viewBox {VW}x{VH}')

# Also compute FL and TX center positions as percentages for marker overlay
def center_pct(col, row):
    cx = PAD + col * STRIDE + TILE / 2
    cy = PAD + row * STRIDE + TILE / 2
    return (cx / VW * 100, cy / VH * 100)

fl_x, fl_y = center_pct(7, 8)
tx_x, tx_y = center_pct(3, 8)
print(f'Orlando (FL) marker: x={fl_x:.1f}% y={fl_y:.1f}%')
print(f'Dallas  (TX) marker: x={tx_x:.1f}% y={tx_y:.1f}%')
