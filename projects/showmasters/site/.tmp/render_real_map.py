"""Render a real US states SVG from the us-atlas topojson with proper
Albers USA projection at a sane scale (output ~1100w × 700h viewBox).
Uses gold styling + hub beacons + constellation lines.
"""

import json, math

with open(r'C:\Users\Zonia\Desktop\Showmasters Site\.tmp\states-10m.json', 'r', encoding='utf-8') as f:
    topo = json.load(f)

transform = topo['transform']
scale_t = transform['scale']
translate = transform['translate']
arcs = topo['arcs']
states = topo['objects']['states']['geometries']

# Decode topojson delta-encoded arcs into absolute lon/lat coords
def decode_arc(idx):
    arc = arcs[idx if idx >= 0 else ~idx]
    pts = []
    px = py = 0
    for d in arc:
        px += d[0]; py += d[1]
        pts.append((px * scale_t[0] + translate[0], py * scale_t[1] + translate[1]))
    if idx < 0: pts = list(reversed(pts))
    return pts

# Albers USA projection — outputs in approx unit-square coords near (0, 0).
# Standard d3-geo Albers projection with parallels 29.5 and 45.5, center 38N/-96W.
def albers_lower48(lon, lat):
    lon_r = math.radians(lon)
    lat_r = math.radians(lat)
    phi1 = math.radians(29.5)
    phi2 = math.radians(45.5)
    n = 0.5 * (math.sin(phi1) + math.sin(phi2))
    c = math.cos(phi1)**2 + 2 * n * math.sin(phi1)
    lat0 = math.radians(38)
    lon0 = math.radians(-96)
    rho0 = math.sqrt(c - 2 * n * math.sin(lat0)) / n
    val = c - 2 * n * math.sin(lat_r)
    if val < 0: return None
    rho = math.sqrt(val) / n
    theta = n * (lon_r - lon0)
    return (rho * math.sin(theta), rho0 - rho * math.cos(theta))

def albers_alaska(lon, lat):
    """Alaska with a fixed shift to lower-left of map."""
    p = albers_lower48(lon + 130, lat - 20)  # rough re-projection
    if not p: return None
    return (p[0] * 0.35 - 0.35, p[1] * 0.35 + 0.25)

def albers_hawaii(lon, lat):
    """Hawaii with a fixed shift, just below Alaska."""
    return (-0.20 + (lon + 157) * 0.02, 0.45 + (lat - 21) * 0.02)

def project(lon, lat):
    # Alaska bounds: lat ~52-70, lon -170 to -130
    if lat > 50 and lon < -130:
        return albers_alaska(lon, lat)
    # Hawaii bounds: lat 18-22, lon -160 to -154
    if lat < 23 and lat > 18 and lon < -154 and lon > -161:
        return albers_hawaii(lon, lat)
    return albers_lower48(lon, lat)

# Build per-state SVG paths
state_features = []
for geom in states:
    fips = geom.get('id', '')
    name = geom.get('properties', {}).get('name', 'Unknown')
    arcs_list = geom.get('arcs', [])
    geom_type = geom['type']
    polygons = arcs_list if geom_type == 'MultiPolygon' else [arcs_list]
    rings_d = []
    for poly in polygons:
        for ring in poly:
            pts = []
            for arc_idx in ring:
                pts.extend(decode_arc(arc_idx))
            if not pts: continue
            projected = []
            for lon, lat in pts:
                p = project(lon, lat)
                if p: projected.append(p)
            if len(projected) < 3: continue
            rings_d.append(projected)
    if rings_d:
        state_features.append((fips, name, rings_d))

# Compute bounds across all projected points
all_x = []; all_y = []
for fips, name, rings in state_features:
    for ring in rings:
        for x, y in ring:
            all_x.append(x); all_y.append(y)

x_min, x_max = min(all_x), max(all_x)
y_min, y_max = min(all_y), max(all_y)

# Scale the projected coordinates to fit a target viewBox.
# US aspect ratio is roughly width 1.65 : height 1.0, but Albers compresses
# the visual a bit. We scale so the output fills a 1100 × 700 box.
target_w = 1100
target_h = 700
pad = 40
content_w = target_w - 2 * pad
content_h = target_h - 2 * pad

raw_w = x_max - x_min
raw_h = y_max - y_min
sx = content_w / raw_w
sy = content_h / raw_h
s = min(sx, sy)
shift_x = -x_min * s + pad + (content_w - raw_w * s) / 2
shift_y = -y_min * s + pad + (content_h - raw_h * s) / 2

def to_svg(x, y):
    return (x * s + shift_x, y * s + shift_y)

def path_d(rings):
    parts = []
    for ring in rings:
        pts_svg = [to_svg(x, y) for x, y in ring]
        parts.append('M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts_svg) + ' Z')
    return ' '.join(parts)

# Status tiers
HQ_FIPS = {'48'}            # Texas
HUB_FIPS = {'12'}           # Florida (Orlando hub)
HUB_STATES = {'06','32','08','47','13','22'}  # CA NV CO TN GA LA
SERVED_FIPS = {'53','04','35','40','05','28','01','45','37','24','11','51','21','17','18','39','42','34','36','25','09','44','23','50','33','20','38','46','31','19','27','55','26','29'}

# Hub markers (geographic city coords)
HUBS = [
    ('fort_worth', 'Fort Worth', -97.33, 32.75, True,  'TEXAS HQ'),
    ('orlando',    'Orlando',     -81.38, 28.54, False, 'ORLANDO HUB'),
    ('la',         'Los Angeles',-118.24, 34.05, False, 'CA'),
    ('vegas',      'Las Vegas',  -115.14, 36.17, False, 'NV'),
    ('denver',     'Denver',     -104.99, 39.74, False, 'CO'),
    ('nashville',  'Nashville',   -86.78, 36.16, False, 'TN'),
    ('atlanta',    'Atlanta',     -84.39, 33.75, False, 'GA'),
    ('nola',       'New Orleans', -90.07, 29.95, False, 'LA'),
]
CONNECTIONS = [
    ('fort_worth','orlando'),
    ('fort_worth','nola'),
    ('fort_worth','atlanta'),
    ('fort_worth','denver'),
    ('fort_worth','vegas'),
    ('fort_worth','la'),
    ('orlando','atlanta'),
    ('orlando','nashville'),
    ('orlando','nola'),
]

hub_pos = {}
for hid, name, lon, lat, is_hq, label in HUBS:
    p = project(lon, lat)
    if p:
        x, y = to_svg(*p)
        hub_pos[hid] = (x, y)

# Build SVG
out = []
out.append(f'<svg class="smpl-realmap" viewBox="0 0 {target_w} {target_h}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Show Masters US service area map">')
out.append('  <title>Show Masters US service area</title>')
out.append('  <defs>')
out.append('    <linearGradient id="rmFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#1A1A22"/><stop offset="100%" stop-color="#12121A"/></linearGradient>')
out.append('    <linearGradient id="rmHub" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#3A2E18"/><stop offset="100%" stop-color="#2A2218"/></linearGradient>')
out.append('    <linearGradient id="rmHq" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#FFE8B8"/><stop offset="100%" stop-color="#9C7126"/></linearGradient>')
out.append('    <radialGradient id="rmBeacon" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="#FFE8B8"/><stop offset="50%" stop-color="#D4A24A"/><stop offset="100%" stop-color="#9C7126"/></radialGradient>')
out.append('    <filter id="rmGlow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3"/></filter>')
out.append('  </defs>')
out.append('  <style>')
out.append('    .smpl-realmap { display: block; width: 100%; height: auto; }')
out.append('    .smpl-realmap .state         { fill: url(#rmFill); stroke: rgba(212,162,74,0.20); stroke-width: 0.7; stroke-linejoin: round; transition: fill 240ms ease; }')
out.append('    .smpl-realmap .state-served  { fill: rgba(212,162,74,0.10); stroke: rgba(212,162,74,0.32); }')
out.append('    .smpl-realmap .state-hub     { fill: url(#rmHub); stroke: rgba(212,162,74,0.78); stroke-width: 1; }')
out.append('    .smpl-realmap .state-hq      { fill: url(#rmHq); stroke: #FFE8B8; stroke-width: 1.2; filter: drop-shadow(0 0 10px rgba(212,162,74,0.55)); }')
out.append('    .smpl-realmap .state:hover   { fill: rgba(212,162,74,0.20); }')
out.append('    .smpl-realmap .conn          { stroke: rgba(212,162,74,0.25); stroke-width: 0.9; stroke-dasharray: 2 5; fill: none; }')
out.append('    .smpl-realmap .hub-marker    { cursor: pointer; }')
out.append('    .smpl-realmap .hub-pulse     { fill: rgba(212,162,74,0.5); animation: rm-pulse 2.4s ease-out infinite; transform-origin: center; transform-box: fill-box; }')
out.append('    .smpl-realmap .hub-pulse.is-hq { fill: rgba(255,232,184,0.7); animation-duration: 2s; }')
out.append('    .smpl-realmap .hub-dot       { fill: url(#rmBeacon); }')
out.append('    .smpl-realmap .hub-label     { font: 800 11px "Inter", system-ui, sans-serif; fill: #FFE8B8; letter-spacing: 2.5px; pointer-events: none; text-transform: uppercase; paint-order: stroke; stroke: rgba(10,10,15,0.8); stroke-width: 3; }')
out.append('    .smpl-realmap .hub-city      { font: 700 9px "JetBrains Mono", monospace; fill: rgba(255,232,184,0.95); letter-spacing: 1.5px; pointer-events: none; text-transform: uppercase; paint-order: stroke; stroke: rgba(10,10,15,0.7); stroke-width: 2.5; }')
out.append('    @keyframes rm-pulse { 0% { transform: scale(0.6); opacity: 0.9; } 100% { transform: scale(3); opacity: 0; } }')
out.append('    @media (prefers-reduced-motion: reduce) { .smpl-realmap .hub-pulse { animation: none; opacity: 0.35; } }')
out.append('  </style>')

# Render states
for fips, name, rings in state_features:
    cls = 'state'
    if fips in HQ_FIPS: cls = 'state state-hq'
    elif fips in HUB_FIPS: cls = 'state state-hub'
    elif fips in HUB_STATES: cls = 'state state-hub'
    elif fips in SERVED_FIPS: cls = 'state state-served'
    d = path_d(rings)
    out.append(f'  <path class="{cls}" data-state="{name}" d="{d}"><title>{name}</title></path>')

# Connection lines
for a, b in CONNECTIONS:
    if a in hub_pos and b in hub_pos:
        ax, ay = hub_pos[a]; bx, by = hub_pos[b]
        out.append(f'  <line class="conn" x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}" />')

# Hub markers — HQ on top
hub_sorted = sorted(HUBS, key=lambda h: 0 if not h[4] else 1)
for hid, name, lon, lat, is_hq, label in hub_sorted:
    if hid not in hub_pos: continue
    x, y = hub_pos[hid]
    r_outer = 18 if is_hq else 9
    r_inner = 7 if is_hq else 4
    pulse_cls = 'hub-pulse is-hq' if is_hq else 'hub-pulse'
    data_attr = ''
    if hid == 'fort_worth':
        data_attr = ' data-hub="dallas"'  # JS expects 'dallas' key
    elif hid == 'orlando':
        data_attr = ' data-hub="orlando"'
    out.append(f'  <g class="hub-marker"{data_attr}>')
    out.append(f'    <title>{name}</title>')
    out.append(f'    <circle class="{pulse_cls}" cx="{x:.1f}" cy="{y:.1f}" r="{r_outer}" />')
    out.append(f'    <circle class="hub-dot" cx="{x:.1f}" cy="{y:.1f}" r="{r_inner}" filter="url(#rmGlow)" />')
    out.append(f'    <circle class="hub-dot" cx="{x:.1f}" cy="{y:.1f}" r="{r_inner * 0.6:.1f}" />')
    if is_hq:
        out.append(f'    <text x="{x:.1f}" y="{y + r_outer + 16:.1f}" class="hub-label" text-anchor="middle">{label}</text>')
    else:
        out.append(f'    <text x="{x:.1f}" y="{y - r_outer - 5:.1f}" class="hub-city" text-anchor="middle">{label}</text>')
    out.append('  </g>')

out.append('</svg>')

content = '\n'.join(out)
with open(r'C:\Users\Zonia\Desktop\Showmasters Site\public\img\us-realmap.svg', 'w', encoding='utf-8') as f:
    f.write(content)
with open(r'C:\Users\Zonia\Desktop\Showmasters Site\.tmp\us-realmap.svg', 'w', encoding='utf-8') as f:
    f.write(content)
print(f'wrote {len(out)} lines, viewBox 0 0 {target_w} {target_h}, {len(state_features)} states')
