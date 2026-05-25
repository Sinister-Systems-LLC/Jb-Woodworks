# Author: RKOJ-ELENO :: 2026-05-24
# Insert a CTA row at the bottom of each city-page <header class="page-header...">
# so high-intent geo visitors see clear action without scrolling.
import re
from pathlib import Path

ROOT = Path(r"D:\Sinister Sanctum\projects\showmasters\site")
CITY_PAGES = ['orlando.html', 'dallas.html', 'houston.html', 'tampa.html']

CTA_BLOCK = '''      <div class="hero-cta-row" style="margin-top: 32px;">
        <a href="contact.html#estimate" class="btn btn-primary btn-large">Get an Estimate</a>
        <a href="order.html" class="btn btn-ghost btn-large">Place a Crew Order</a>
      </div>
'''

for name in CITY_PAGES:
    p = ROOT / name
    t = p.read_text(encoding='utf-8')
    if 'hero-cta-row' in t and '<header' in t and t.find('hero-cta-row') < t.find('</header>'):
        print(f"  skip {name}: already has CTA in header")
        continue
    # Find the page-header section's container, insert CTA after the subtitle <p>
    pat = re.compile(
        r'(<header class="page-header[^"]*".*?<div class="container"[^>]*>\s*<h1[^>]*>.*?</h1>\s*'
        r'<p class="subtitle"[^>]*>.*?</p>)\s*'
        r'(\s*</div>\s*</header>)',
        re.DOTALL,
    )
    m = pat.search(t)
    if not m:
        print(f"  miss {name}: page-header structure not matched")
        continue
    new_t = t[:m.end(1)] + '\n' + CTA_BLOCK + t[m.start(2):]
    p.write_text(new_t, encoding='utf-8')
    print(f"  ok   {name}: CTA inserted in header")
