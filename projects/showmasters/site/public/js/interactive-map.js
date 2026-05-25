/* Author: RKOJ-ELENO :: 2026-05-23
 * Interactive US-coverage cartogram. Click the FL or TX tile in the inline SVG
 * → popup of representative shows we've crewed there. The previous PNG-overlay
 * marker approach was replaced when the static PNG was swapped for a clean
 * SVG state-tile cartogram in where.html. Now we attach clicks directly to
 * the `data-hub` <g> tile groups in the SVG.
 */

(function () {
  const root = document.getElementById('smplMap');
  if (!root) return;
  const svg = root.querySelector('svg.smpl-cartogram, svg.smpl-silhouette, svg.smpl-realmap');
  if (!svg) return;

  const SHOWS = {
    orlando: {
      label: 'Orlando, FL — Florida Hub',
      tagline: '9 representative shows · since 2002',
      shows: [
        { title: 'Fortune-100 Sales Kickoff', venue: 'Orange County Convention Center', year: 2026 },
        { title: 'Enterprise Software Annual', venue: 'Gaylord Palms Resort · Kissimmee', year: 2025 },
        { title: 'Headliner Pop Tour', venue: 'Amway Center', year: 2026 },
        { title: 'Touring Comedy Special', venue: 'Hard Rock Live', year: 2025 },
        { title: 'Healthcare Conference I&D', venue: 'OCCC', year: 2026 },
        { title: 'Touring Broadway Engagement', venue: 'Dr. Phillips Center', year: 2025 },
        { title: 'Multi-Service Easter Production', venue: 'Megachurch Campus · Tampa', year: 2026 },
        { title: 'Florida Music Weekend', venue: 'Bayfront Park · Miami', year: 2025 },
        { title: 'Annual Foundation Gala', venue: 'Ritz-Carlton Ballroom', year: 2025 },
      ],
    },
    dallas: {
      label: 'Fort Worth, TX — Texas HQ',
      tagline: '6 representative shows · DFW + statewide',
      shows: [
        { title: 'Healthcare Provider Annual Meeting', venue: 'Hilton Anatole · Dallas', year: 2026 },
        { title: 'Automotive OEM Reveal', venue: 'Convention Center · Fort Worth', year: 2025 },
        { title: 'Country Tour Date', venue: 'Globe Life Field · Arlington', year: 2025 },
        { title: 'Manufacturing Trade Show I&D', venue: 'Kay Bailey Hutchison Center · Dallas', year: 2025 },
        { title: 'NFL Pre-Game + Halftime', venue: 'AT&T Stadium · Arlington', year: 2025 },
        { title: 'Music Festival, Day-Stage Crew', venue: 'Zilker Park · Austin', year: 2025 },
      ],
    },
  };

  const popup = document.createElement('div');
  popup.className = 'smpl-map-popup';
  popup.setAttribute('role', 'dialog');
  popup.setAttribute('aria-hidden', 'true');
  popup.innerHTML = `
    <button type="button" class="smpl-map-popup-close" aria-label="Close">
      <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><line x1="6" y1="6" x2="18" y2="18"/><line x1="18" y1="6" x2="6" y2="18"/></svg>
    </button>
    <p class="smpl-map-popup-tag"></p>
    <h4 class="smpl-map-popup-state"></h4>
    <ul class="smpl-map-popup-shows"></ul>
    <a href="shows.html" class="smpl-map-popup-cta">See the full portfolio →</a>
  `;
  root.appendChild(popup);

  const popupTag   = popup.querySelector('.smpl-map-popup-tag');
  const popupTitle = popup.querySelector('.smpl-map-popup-state');
  const popupList  = popup.querySelector('.smpl-map-popup-shows');
  const popupClose = popup.querySelector('.smpl-map-popup-close');

  function tileCenterPct(g) {
    // Resolve the center of a hub marker across all map generations:
    //   - Cartogram era used <rect>
    //   - Silhouette era used <circle class="hub-dot">
    //   - Albers era (current) uses <polygon class="hub-star">
    const viewBox = svg.viewBox.baseVal;
    const rect = g.querySelector('rect');
    if (rect) {
      const x = parseFloat(rect.getAttribute('x'));
      const y = parseFloat(rect.getAttribute('y'));
      const w = parseFloat(rect.getAttribute('width'));
      const h = parseFloat(rect.getAttribute('height'));
      return {
        x: ((x + w / 2 - viewBox.x) / viewBox.width) * 100,
        y: ((y + h / 2 - viewBox.y) / viewBox.height) * 100,
      };
    }
    const polygon = g.querySelector('polygon.hub-star') || g.querySelector('polygon');
    if (polygon) {
      const pts = (polygon.getAttribute('points') || '').trim().split(/\s+/);
      let sx = 0, sy = 0, n = 0;
      for (const p of pts) {
        const [px, py] = p.split(',').map(Number);
        if (Number.isFinite(px) && Number.isFinite(py)) { sx += px; sy += py; n++; }
      }
      if (n) {
        return {
          x: ((sx / n - viewBox.x) / viewBox.width) * 100,
          y: ((sy / n - viewBox.y) / viewBox.height) * 100,
        };
      }
    }
    const circle = g.querySelector('circle.hub-dot') || g.querySelector('circle');
    if (circle) {
      return {
        x: ((parseFloat(circle.getAttribute('cx')) - viewBox.x) / viewBox.width) * 100,
        y: ((parseFloat(circle.getAttribute('cy')) - viewBox.y) / viewBox.height) * 100,
      };
    }
    return { x: 50, y: 50 };
  }

  function openPopup(key, g) {
    const data = SHOWS[key];
    if (!data) return;
    popupTag.textContent = data.tagline;
    popupTitle.textContent = data.label;
    popupList.innerHTML = data.shows.map(s => `
      <li>
        <strong>${escapeHtml(s.title)}</strong>
        <span>${escapeHtml(s.venue)} · ${s.year}</span>
      </li>
    `).join('');
    const c = tileCenterPct(g);
    const onLeft = c.x > 55;
    popup.style.left  = onLeft ? '' : `${Math.min(Math.max(c.x + 4, 6), 60)}%`;
    popup.style.right = onLeft ? `${Math.min(Math.max(100 - c.x + 4, 6), 60)}%` : '';
    popup.style.top   = `${Math.min(Math.max(c.y - 18, 4), 60)}%`;
    popup.classList.add('is-open');
    popup.setAttribute('aria-hidden', 'false');
    svg.querySelectorAll('.cartogram-tile.is-active, .hub-marker.is-active').forEach(t => t.classList.remove('is-active'));
    g.classList.add('is-active');
  }
  function closePopup() {
    popup.classList.remove('is-open');
    popup.setAttribute('aria-hidden', 'true');
    svg.querySelectorAll('.cartogram-tile.is-active, .hub-marker.is-active').forEach(t => t.classList.remove('is-active'));
  }

  /* Click handlers on the FL & TX tile groups */
  svg.querySelectorAll('[data-hub]').forEach(g => {
    g.style.cursor = 'pointer';
    g.setAttribute('role', 'button');
    g.setAttribute('tabindex', '0');
    g.setAttribute('aria-label', g.getAttribute('data-hub') === 'orlando'
      ? "Shows we've crewed from Orlando"
      : "Shows we've crewed from Dallas");
    const handler = (e) => {
      e.preventDefault();
      openPopup(g.getAttribute('data-hub'), g);
    };
    g.addEventListener('click', handler);
    g.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') handler(e);
    });
  });

  popupClose.addEventListener('click', closePopup);
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closePopup(); });

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => ({
      '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
    }[c]));
  }
})();
