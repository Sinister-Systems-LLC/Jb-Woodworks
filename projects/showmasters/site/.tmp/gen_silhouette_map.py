"""Generate a stylized US silhouette map with gold hub markers.
Replaces the tile cartogram with a real geographic outline.
"""

# Approximate US silhouette in a 1000x600 viewBox (Albers-like projection).
# Hand-traced from a public-domain simplified US outline.
US_PATH = (
    "M 142 188 L 140 168 L 154 156 L 178 152 L 198 154 L 215 158 "
    "L 230 158 L 248 154 L 268 156 L 288 158 L 308 156 L 328 154 "
    "L 348 152 L 372 152 L 396 154 L 420 156 L 444 154 L 470 152 "
    "L 498 150 L 528 148 L 560 148 L 596 150 L 632 152 L 668 154 "
    "L 700 156 L 730 158 L 758 162 L 782 168 L 800 178 L 814 188 "
    "L 824 200 L 832 214 L 836 230 L 838 246 L 836 262 L 832 276 "
    "L 826 290 L 816 302 L 808 314 L 802 326 L 800 340 L 802 354 "
    "L 808 366 L 814 378 L 818 392 L 820 408 L 820 424 L 818 440 "
    "L 814 454 L 808 466 L 800 476 L 790 484 L 778 490 L 766 494 "
    "L 752 496 L 738 494 L 724 490 L 712 482 L 702 470 L 694 458 "
    "L 688 446 L 684 432 L 680 418 L 674 406 L 666 396 L 656 388 "
    "L 644 382 L 630 380 L 614 380 L 596 382 L 578 384 L 560 386 "
    "L 542 386 L 524 384 L 508 380 L 492 374 L 478 366 L 464 358 "
    "L 450 350 L 436 344 L 422 340 L 406 338 L 390 338 L 374 340 "
    "L 358 342 L 342 344 L 326 344 L 310 340 L 296 334 L 282 326 "
    "L 268 318 L 254 308 L 240 298 L 226 286 L 214 274 L 202 260 "
    "L 192 246 L 184 230 L 178 214 L 172 198 L 162 188 L 142 188 Z"
)

# Florida peninsula (separate sub-path for the recognizable hook)
FL_PATH = (
    "M 736 462 L 748 466 L 760 470 L 770 478 L 776 490 L 778 504 "
    "L 776 516 L 770 526 L 762 532 L 752 534 L 742 530 L 736 522 "
    "L 732 510 L 730 498 L 728 484 L 730 472 L 736 462 Z"
)

# Hubs and offices with approximate lat-projected coordinates
HUBS = [
    ('orlando', 'Orlando', 770, 500, 'hq', 'ORLANDO HUB'),
    ('dallas',  'Dallas',  520, 410, 'hq', 'DALLAS HQ'),
    ('la',      'Los Angeles',     186, 348, 'hub', 'LA'),
    ('vegas',   'Las Vegas',       228, 318, 'hub', 'NV'),
    ('denver',  'Denver',          376, 304, 'hub', 'CO'),
    ('nashville','Nashville',      632, 354, 'hub', 'TN'),
    ('atlanta', 'Atlanta',         668, 416, 'hub', 'GA'),
    ('nola',    'New Orleans',     576, 472, 'hub', 'LA'),
]

# Subtle constellation lines connecting offices to hubs
CONNECTIONS = [
    ('orlando', 'atlanta'),
    ('orlando', 'nashville'),
    ('orlando', 'nola'),
    ('dallas',  'nola'),
    ('dallas',  'atlanta'),
    ('dallas',  'denver'),
    ('dallas',  'vegas'),
    ('dallas',  'la'),
    ('orlando', 'dallas'),
]

hub_by_id = {h[0]: h for h in HUBS}

lines = []
lines.append('<svg class="smpl-silhouette" viewBox="0 0 1000 600" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Show Masters US service area map">')
lines.append('  <title>Show Masters US service area</title>')
lines.append('  <defs>')
lines.append('    <radialGradient id="usGlow" cx="50%" cy="50%" r="50%">')
lines.append('      <stop offset="0%"  stop-color="rgba(212,162,74,0.18)"/>')
lines.append('      <stop offset="100%" stop-color="rgba(212,162,74,0)"/>')
lines.append('    </radialGradient>')
lines.append('    <linearGradient id="usFill" x1="0" x2="0" y1="0" y2="1">')
lines.append('      <stop offset="0%"  stop-color="#2A2519"/>')
lines.append('      <stop offset="100%" stop-color="#18141A"/>')
lines.append('    </linearGradient>')
lines.append('    <radialGradient id="beacon" cx="50%" cy="50%" r="50%">')
lines.append('      <stop offset="0%"  stop-color="#FFE8B8"/>')
lines.append('      <stop offset="50%" stop-color="#D4A24A"/>')
lines.append('      <stop offset="100%" stop-color="#9C7126"/>')
lines.append('    </radialGradient>')
lines.append('    <filter id="goldBlur" x="-50%" y="-50%" width="200%" height="200%">')
lines.append('      <feGaussianBlur stdDeviation="2.4"/>')
lines.append('    </filter>')
lines.append('  </defs>')
lines.append('  <style>')
lines.append('    .smpl-silhouette .us-glow      { fill: url(#usGlow); }')
lines.append('    .smpl-silhouette .us-shape     { fill: url(#usFill); stroke: rgba(212,162,74,0.55); stroke-width: 1.4; stroke-linejoin: round; }')
lines.append('    .smpl-silhouette .conn-line    { stroke: rgba(212,162,74,0.20); stroke-width: 1; stroke-dasharray: 3 6; }')
lines.append('    .smpl-silhouette .hub-pulse    { fill: rgba(212,162,74,0.5); transform-origin: center; }')
lines.append('    .smpl-silhouette .hub-pulse.is-hq { fill: rgba(255,232,184,0.7); }')
lines.append('    .smpl-silhouette .hub-marker   { cursor: pointer; }')
lines.append('    .smpl-silhouette .hub-dot      { fill: url(#beacon); }')
lines.append('    .smpl-silhouette .hub-label    { font: 800 9px "Inter", system-ui, sans-serif; fill: #FFE8B8; letter-spacing: 2px; pointer-events: none; text-transform: uppercase; }')
lines.append('    .smpl-silhouette .hub-city     { font: 700 7px "JetBrains Mono", monospace; fill: rgba(212,162,74,0.7); letter-spacing: 1.5px; pointer-events: none; text-transform: uppercase; }')
lines.append('    @keyframes hub-pulse-anim { 0%,100% { transform: scale(0.6); opacity: 0.9; } 100% { transform: scale(3); opacity: 0; } }')
lines.append('    @keyframes hub-pulse-anim2 { 0% { transform: scale(0.6); opacity: 0.9; } 100% { transform: scale(3); opacity: 0; } }')
lines.append('    .smpl-silhouette .hub-pulse    { animation: hub-pulse-anim2 2.4s ease-out infinite; }')
lines.append('    .smpl-silhouette .hub-pulse.is-hq { animation-duration: 2s; }')
lines.append('    @media (prefers-reduced-motion: reduce) { .smpl-silhouette .hub-pulse { animation: none; opacity: 0.35; } }')
lines.append('  </style>')

# Background glow
lines.append('  <ellipse class="us-glow" cx="500" cy="320" rx="480" ry="220" />')

# Main US silhouette
lines.append(f'  <path class="us-shape" d="{US_PATH}" />')
lines.append(f'  <path class="us-shape" d="{FL_PATH}" />')

# Constellation lines
for a_id, b_id in CONNECTIONS:
    ax, ay = hub_by_id[a_id][2], hub_by_id[a_id][3]
    bx, by = hub_by_id[b_id][2], hub_by_id[b_id][3]
    lines.append(f'  <line class="conn-line" x1="{ax}" y1="{ay}" x2="{bx}" y2="{by}" />')

# Hub markers (HQs last so they layer on top)
for hub in sorted(HUBS, key=lambda h: 0 if h[4] == 'hub' else 1):
    hid, name, x, y, status, label = hub
    is_hq = status == 'hq'
    radius_outer = 16 if is_hq else 8
    radius_inner = 6 if is_hq else 3.5
    pulse_class = 'hub-pulse is-hq' if is_hq else 'hub-pulse'
    data_hub = f' data-hub="{hid}"' if is_hq else ''
    lines.append(f'  <g class="hub-marker"{data_hub}>')
    lines.append(f'    <title>{name}</title>')
    lines.append(f'    <circle class="{pulse_class}" cx="{x}" cy="{y}" r="{radius_outer}" />')
    lines.append(f'    <circle class="hub-dot" cx="{x}" cy="{y}" r="{radius_inner}" filter="url(#goldBlur)" />')
    lines.append(f'    <circle class="hub-dot" cx="{x}" cy="{y}" r="{radius_inner * 0.6}" />')
    if is_hq:
        lines.append(f'    <text x="{x}" y="{y + radius_outer + 14}" class="hub-label" text-anchor="middle">{label}</text>')
    else:
        lines.append(f'    <text x="{x}" y="{y - radius_outer - 4}" class="hub-city" text-anchor="middle">{label}</text>')
    lines.append('  </g>')

lines.append('</svg>')

out = '\n'.join(lines)
with open(r'C:\Users\Zonia\Desktop\Showmasters Site\.tmp\us-silhouette.svg', 'w', encoding='utf-8') as f:
    f.write(out)
print(f'wrote {len(lines)} lines')
