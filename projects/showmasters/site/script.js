/*
 * Author: RKOJ-ELENO :: 2026-05-23
 * Show Masters site. Dependency-free interactivity, three motion durations.
 */

/* ---- STARTUP INTRO — STAGE CUE ("lights up") ----
   Brand-specific reveal: a horizontal gold scan-bar sweeps left-to-right
   across a dark veil. Each letter of SMPL ignites as the scan-bar passes
   its position. Tagline + gold rule fade in after the scan, then the veil
   rises like a stage curtain. ~2.0s total, pure CSS — no canvas / no RAF. */
/* Helper used by both the intro path and the skip path. */
function smplRevealHero() {
  document.querySelectorAll('.hero-reveal').forEach(el => {
    const d = parseFloat(getComputedStyle(el).getPropertyValue('--reveal-delay')) || 0;
    setTimeout(() => el.classList.add('is-revealed'), d);
  });
}

/* The "skip-on-load" early return above this block needs the helper defined
   first; everything below references it. */

(function startupIntro() {
  /* Homepage gets the full stage-cue animation on every load + refresh.
     All other pages skip the full intro and just reveal the hero.
     Between-page navigation uses the fast #smplTx curtain in the click
     handler below (~320ms). ?intro=skip suppresses; ?intro=force overrides. */
  const params = new URLSearchParams(window.location.search);
  const skipIntro = params.get('intro') === 'skip';
  const forceIntro = params.get('intro') === 'force';
  const prefersReduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const path = window.location.pathname || '/';
  const isHomepage = (path === '/' || path === '' || /\/index(\.html)?$/i.test(path));
  if (prefersReduced || skipIntro || (!isHomepage && !forceIntro)) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', smplRevealHero);
    } else {
      smplRevealHero();
    }
    return;
  }

  const root = document.documentElement;
  root.classList.add('is-booting');

  /* DOM structure: a full-bleed dark veil, a horizontal scan-bar that
     traverses left-to-right, and the SMPL wordmark whose letters light up
     sequentially as the scan-bar passes their horizontal position. */
  const intro = document.createElement('div');
  intro.id = 'intro';
  intro.innerHTML = `
    <div class="intro-veil"></div>
    <div class="intro-stage">
      <div class="intro-wordmark" aria-hidden="true">
        <span class="intro-letter" data-l="S">S</span>
        <span class="intro-letter" data-l="M">M</span>
        <span class="intro-letter" data-l="P">P</span>
        <span class="intro-letter" data-l="L">L</span>
        <span class="intro-triangle"></span>
      </div>
      <div class="intro-tagline">SHOW MASTERS · PRODUCTION LOGISTICS</div>
      <div class="intro-rule"></div>
    </div>
    <div class="intro-scanbar"></div>
  `;
  document.documentElement.appendChild(intro);

  /* Schedule letter-by-letter illumination matched to scan-bar position.
     Scan bar takes ~1100ms to traverse; SMPL letters sit roughly at 35/45/55/65% — light them at those points. */
  const letters = intro.querySelectorAll('.intro-letter');
  const scanDurationMs = 1100;
  [0.34, 0.46, 0.58, 0.70].forEach((pct, idx) => {
    setTimeout(() => letters[idx]?.classList.add('lit'), Math.round(scanDurationMs * pct));
  });
  /* After scan completes, fade in tagline + rule. */
  setTimeout(() => intro.querySelector('.intro-tagline')?.classList.add('lit'), scanDurationMs + 80);
  setTimeout(() => intro.querySelector('.intro-rule')?.classList.add('lit'), scanDurationMs + 240);

  /* Tear down. Curtain rises ~1.9s. Total intro ~2.0s. */
  setTimeout(() => {
    intro.classList.add('is-gone');
    setTimeout(() => {
      intro.remove();
      root.classList.remove('is-booting');
      smplRevealHero();
    }, 650);
  }, 1900);
})();

/* ---- DOM-ready interactivity ---- */
document.addEventListener('DOMContentLoaded', () => {

  /* Navbar scroll state */
  const navbar = document.getElementById('navbar');
  if (navbar) {
    const onScroll = () => navbar.classList.toggle('scrolled', window.scrollY > 40);
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* Nav active state — highlight current page + dot visited paths */
  (function smplNavActive() {
    let currentPage = (window.location.pathname.split('/').pop() || 'index.html').toLowerCase();
    if (!currentPage || currentPage === '') currentPage = 'index.html';
    let visited = [];
    try { visited = JSON.parse(sessionStorage.getItem('smpl_paths_visited') || '[]'); } catch (_) {}
    const PATH_SLUGS = ['what','how','where','shows','order'];
    document.querySelectorAll('.nav-links a, .mob-link').forEach(a => {
      const raw = (a.getAttribute('href') || '').toLowerCase();
      if (!raw || raw.startsWith('#') || raw.startsWith('mailto:') || raw.startsWith('tel:')) return;
      const href = raw.replace(/^\//,'').replace(/^https?:\/\/[^\/]+\//,'').split('#')[0].split('?')[0];
      const slug = href.replace(/\.html$/,'');
      if (href === currentPage || (currentPage === 'index.html' && (href === '' || href === '/'))) {
        a.classList.add('is-active');
      } else if (PATH_SLUGS.includes(slug) && visited.includes(slug)) {
        a.classList.add('is-visited');
      }
    });
  })();

  /* Hamburger / mobile menu */
  const hamburger  = document.getElementById('hamburger');
  const mobileMenu = document.getElementById('mobileMenu');
  if (hamburger && mobileMenu) {
    hamburger.addEventListener('click', () => mobileMenu.classList.toggle('open'));
    document.querySelectorAll('.mob-link').forEach(link =>
      link.addEventListener('click', () => mobileMenu.classList.remove('open'))
    );
  }

  /* Page-transition curtain — every internal link click plays a quick
     stage-cue scan before navigating. Skips: external links, mailto/tel,
     anchor jumps, modifier-key clicks, downloads, target="_blank". */
  function isInternalNav(a) {
    if (!a || !a.href) return false;
    const url = new URL(a.href, window.location.href);
    if (url.origin !== window.location.origin) return false;
    if (a.target && a.target !== '' && a.target !== '_self') return false;
    if (a.hasAttribute('download')) return false;
    const href = a.getAttribute('href') || '';
    if (href.startsWith('#') || href.startsWith('mailto:') || href.startsWith('tel:')) return false;
    if (url.pathname === window.location.pathname && url.search === window.location.search && url.hash) return false;
    return true;
  }
  document.addEventListener('click', (e) => {
    if (e.defaultPrevented) return;
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    if (e.button !== 0) return;
    const a = e.target.closest('a');
    if (!a || !isInternalNav(a)) return;
    if (a.dataset.noTransition === 'true') return;
    /* If destination is the homepage, skip the page-transition flash — the
       homepage already plays its own full intro animation on load. Avoids
       the operator-reported "two animations stacked" double-play.
       2026-05-23. */
    const destUrl = new URL(a.href, window.location.href);
    const isGoingHome = destUrl.pathname === '/' || destUrl.pathname === '' || destUrl.pathname.endsWith('/index.html');
    if (isGoingHome) {
      // Let the navigation happen naturally; homepage intro will play on load.
      return;
    }
    e.preventDefault();
    const dest = a.href;
    /* Per-page SMPL flash. Veil drops, SMPL wordmark + gold scan-bar passes
       once, navigate. ~340ms — shorter than the first-visit intro on purpose. */
    const tx = document.createElement('div');
    tx.id = 'smplTx';
    tx.innerHTML = '<div class="tx-veil"></div><div class="tx-mark" aria-hidden="true">SMPL</div><div class="tx-bar"></div>';
    document.body.appendChild(tx);
    void tx.offsetWidth;
    tx.classList.add('is-active');
    setTimeout(() => { window.location.href = dest; }, 320);
  });

  /* Smooth anchor scroll */
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const href = this.getAttribute('href');
      if (href === '#' || href.length < 2) return;
      const target = document.querySelector(href);
      if (target) {
        e.preventDefault();
        window.scrollTo({ top: target.getBoundingClientRect().top + window.scrollY - 80, behavior: 'smooth' });
      }
    });
  });

  /* Fade-in on scroll */
  const fadeObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) { entry.target.classList.add('visible'); fadeObserver.unobserve(entry.target); }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });
  document.querySelectorAll('.fade-in-up').forEach(el => fadeObserver.observe(el));

  /* Hero rotating slider — kept only as fallback for pages that still use
     .hero-slide markup. The home now uses a single .hero-video element which
     autoplays/loops natively, so this block is a no-op there. */
  const slides = document.querySelectorAll('.hero-slide');
  if (slides.length > 1) {
    let i = 0;
    const bumpPreload = (idx) => {
      const v = slides[idx]?.querySelector('video');
      if (!v) return;
      if (v.preload !== 'auto') { v.preload = 'auto'; v.load(); }
    };
    const playActive = () => {
      const slide = slides[i];
      const duration = parseInt(slide.getAttribute('data-duration'), 10) || 7000;

      slides.forEach(s => { const v = s.querySelector('video'); if (v) v.pause(); });

      const video = slide.querySelector('video');
      if (video) {
        try { video.currentTime = parseFloat(slide.getAttribute('data-video-start')) || 0; } catch (_) {}
        video.play().catch(() => { /* autoplay blocked, ignore */ });
      }

      /* Lookahead: bump next slide's video to preload="auto" so the crossfade
         doesn't catch a black frame waiting for bytes. */
      bumpPreload((i + 1) % slides.length);

      const prev = i;
      i = (i + 1) % slides.length;
      setTimeout(() => {
        slides[prev].classList.remove('active');
        slides[i].classList.add('active');
        playActive();
      }, duration);
    };
    /* Also preload next slide immediately on first paint so the very first
       transition is smooth. */
    bumpPreload(1);
    playActive();
  }

  /* Counter ticker */
  const countEls = document.querySelectorAll('[data-count]');
  const countUp = (el) => {
    const target = parseInt(el.getAttribute('data-count'), 10);
    const suffix = el.getAttribute('data-suffix') || '';
    const duration = 1800;
    const start = performance.now();
    const step = (now) => {
      const p = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.floor(eased * target).toLocaleString() + suffix;
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  };
  const countObs = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting) { countUp(e.target); countObs.unobserve(e.target); } });
  }, { threshold: 0.5 });
  countEls.forEach(el => countObs.observe(el));

  /* Shows portfolio filter chips — pure client-side filter. */
  const filterBar = document.getElementById('filterBar');
  const showsGrid = document.getElementById('showsGrid');
  if (filterBar && showsGrid) {
    const chips = filterBar.querySelectorAll('.filter-chip');
    const cards = showsGrid.querySelectorAll('.show-card');

    /* Update chip counts on first paint */
    const counts = { all: cards.length };
    cards.forEach(c => {
      const cat = c.getAttribute('data-category');
      counts[cat] = (counts[cat] || 0) + 1;
    });
    filterBar.querySelectorAll('[data-count-for]').forEach(span => {
      span.textContent = counts[span.getAttribute('data-count-for')] || 0;
    });

    filterBar.addEventListener('click', (e) => {
      const chip = e.target.closest('.filter-chip');
      if (!chip) return;
      const filter = chip.getAttribute('data-filter');
      chips.forEach(c => {
        const active = c === chip;
        c.classList.toggle('is-active', active);
        c.setAttribute('aria-selected', active ? 'true' : 'false');
      });
      cards.forEach(card => {
        const cat = card.getAttribute('data-category');
        card.classList.toggle('is-hidden', filter !== 'all' && cat !== filter);
      });
    });
  }

  /* Stagger-in observer — animates direct children of .stagger-in containers
     sequentially when the container scrolls into view. */
  const staggerObs = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-staggered');
        staggerObs.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15, rootMargin: '0px 0px -50px 0px' });
  document.querySelectorAll('.stagger-in').forEach(el => staggerObs.observe(el));

  /* Let's Chat — global floating widget. Mounted lazily after intro completes
     to avoid layout shift during the curtain rise. */
  if (!document.getElementById('smplChatBtn')) {
    const root = document.createElement('div');
    root.id = 'smplChat';
    root.innerHTML = `
      <button type="button" id="smplChatBtn" aria-label="Open chat with Show Masters" aria-expanded="false">
        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 11.5a8 8 0 0 1-11.5 7.2L4 21l1.6-4.6A8 8 0 1 1 21 11.5z"/>
        </svg>
        <span class="chat-btn-label">Let's Chat</span>
      </button>
      <div id="smplChatPanel" role="dialog" aria-label="Show Masters chat" aria-hidden="true">
        <header class="chat-panel-head">
          <div>
            <span class="chat-panel-tag">SMPL · ORDERS DESK</span>
            <h4>How can we help?</h4>
          </div>
          <button type="button" id="smplChatClose" aria-label="Close chat">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="6" y1="6" x2="18" y2="18"/><line x1="18" y1="6" x2="6" y2="18"/></svg>
          </button>
        </header>
        <div class="chat-panel-greet">
          <p>Live event crew on call. Fastest reply by phone — same-day on email + this form during business hours.</p>
          <div class="chat-quicklinks">
            <a href="tel:+18777652267" class="chat-ql">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z"/></svg>
              <span><strong>(877) 765-2267</strong><br/><em>Orders desk · 24/7 for active loads</em></span>
            </a>
            <a href="mailto:Orders@ShowMasters.com" class="chat-ql">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 7 9-7"/></svg>
              <span><strong>Orders@ShowMasters.com</strong><br/><em>Same-day reply</em></span>
            </a>
            <a href="order.html" class="chat-ql">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="4" width="14" height="18" rx="1"/><rect x="9" y="2" width="6" height="3" rx="0.5"/><line x1="8" y1="10" x2="16" y2="10"/><line x1="8" y1="14" x2="16" y2="14"/></svg>
              <span><strong>Drop a crew order</strong><br/><em>Self-serve form</em></span>
            </a>
          </div>
        </div>
        <form id="smplChatForm" class="chat-panel-form">
          <label class="chat-row"><span>Name</span><input type="text" name="name" required placeholder="Your name" /></label>
          <label class="chat-row"><span>Email</span><input type="email" name="email" required placeholder="you@company.com" /></label>
          <label class="chat-row"><span>Quick note</span><textarea name="msg" rows="3" required placeholder="What show, when, what crew? We'll take it from there."></textarea></label>
          <button type="submit" class="chat-send">Send</button>
          <p class="chat-success" hidden>Got it. We'll reach you the same business day.</p>
        </form>
      </div>
    `;
    document.body.appendChild(root);
    const btn = document.getElementById('smplChatBtn');
    const panel = document.getElementById('smplChatPanel');
    const close = document.getElementById('smplChatClose');
    const open = (state) => {
      const isOpen = typeof state === 'boolean' ? state : !panel.classList.contains('is-open');
      panel.classList.toggle('is-open', isOpen);
      btn.classList.toggle('is-open', isOpen);
      btn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
      panel.setAttribute('aria-hidden', isOpen ? 'false' : 'true');
    };
    btn.addEventListener('click', () => open());
    close.addEventListener('click', () => open(false));
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && panel.classList.contains('is-open')) open(false); });
    const cf = document.getElementById('smplChatForm');
    cf.addEventListener('submit', (e) => {
      e.preventDefault();
      const sendBtn = cf.querySelector('.chat-send');
      const success = cf.querySelector('.chat-success');
      sendBtn.disabled = true;
      sendBtn.textContent = 'Sending...';
      setTimeout(() => {
        cf.querySelectorAll('input,textarea').forEach(i => i.value = '');
        sendBtn.style.display = 'none';
        success.hidden = false;
        setTimeout(() => {
          sendBtn.style.display = '';
          sendBtn.disabled = false;
          sendBtn.textContent = 'Send';
          success.hidden = true;
        }, 4000);
      }, 700);
    });
  }

  /* Cookie banner is initialized in the secondary smplCookieBanner block
     below (line ~520). The older duplicate that lived here was removed
     2026-05-23 because it stored 'accepted' while the newer one stores
     'ok'/'declined' — they didn't recognize each other's dismissal and
     both fired. One canonical banner only now. */

  /* ---- PATH FLOATER ----
     Five-path tracker. On any of the 5 path-pages (what/how/where/shows/order),
     a floater appears showing which paths have been visited + a one-click next
     path + return-home + get-quote. Visited paths persist in sessionStorage. */
  (function smplPathFloater() {
    const PATHS = [
      { slug: 'what',  href: 'what.html',  label: 'What' },
      { slug: 'how',   href: 'how.html',   label: 'How' },
      { slug: 'where', href: 'where.html', label: 'Where' },
      { slug: 'shows', href: 'shows.html', label: 'Shows' },
      { slug: 'order', href: 'order.html', label: 'Order' }
    ];
    const path = window.location.pathname.toLowerCase();
    /* Reset the visited path-trail every time the user lands on the homepage
       so each session starts fresh. Operator-requested behavior 2026-05-23. */
    const isHome = path === '/' || path.endsWith('/index.html') || path === '' || path === '/index.html';
    if (isHome) {
      try { sessionStorage.removeItem('smpl_paths_visited'); } catch (_) {}
    }
    const current = PATHS.find(p => path.endsWith('/' + p.href) || path.endsWith(p.href));
    if (!current) return;
    let visited = [];
    try { visited = JSON.parse(sessionStorage.getItem('smpl_paths_visited') || '[]'); } catch (_) {}
    if (!visited.includes(current.slug)) {
      visited.push(current.slug);
      try { sessionStorage.setItem('smpl_paths_visited', JSON.stringify(visited)); } catch (_) {}
    }
    /* Path floater now re-appears on every path-page navigation.
       The × button hides it for the current page-view only — no longer
       sessionStorage-persistent (operator reported never seeing the
       guide after first dismissal). */
    const nextPath = PATHS.find(p => !visited.includes(p.slug)) || null;
    const root = document.createElement('div');
    root.id = 'smplPath';
    root.setAttribute('role', 'complementary');
    root.setAttribute('aria-label', 'Your path through Show Masters');
    const dots = PATHS.map(p => {
      const cls = [
        'path-dot',
        visited.includes(p.slug) ? 'is-visited' : '',
        p.slug === current.slug ? 'is-current' : '',
        (nextPath && p.slug === nextPath.slug) ? 'is-next' : ''
      ].filter(Boolean).join(' ');
      return `<a class="${cls}" href="${p.href}" data-no-transition="false">${p.label}</a>`;
    }).join('');
    const nextBtn = nextPath
      ? `<a href="${nextPath.href}" class="path-next">Next: ${nextPath.label} &rarr;</a>`
      : `<a href="contact.html#estimate" class="path-next">All done &rarr;</a>`;
    root.innerHTML = `
      <div class="path-head">
        <p class="path-title">Your path</p>
        <button type="button" class="path-close" aria-label="Hide path tracker">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="6" y1="6" x2="18" y2="18"/><line x1="18" y1="6" x2="6" y2="18"/></svg>
        </button>
      </div>
      <div class="path-dots">${dots}</div>
      <div class="path-actions">
        <a href="/" class="path-home">← Start</a>
        ${nextBtn}
        <a href="contact.html#estimate" class="path-quote">Quote</a>
      </div>
    `;
    document.body.appendChild(root);
    requestAnimationFrame(() => setTimeout(() => root.classList.add('is-up'), 500));
    root.querySelector('.path-close').addEventListener('click', () => {
      root.classList.remove('is-up');
      setTimeout(() => root.remove(), 400);
    });
  })();

  /* Form submission router. Builds a mailto: URL from the form fields and
     opens the user's email client to Orders@ShowMasters.com. Until a real
     backend is wired (Formspree, Netlify Forms, etc.), this is the no-
     infrastructure-required path to actually deliver submissions.
     2026-05-23 — operator requested orders go to the correct email. */
  function smplBuildMailto(form, subject) {
    const data = new FormData(form);
    const lines = [];
    data.forEach((v, k) => {
      if (v === '' || v == null) return;
      const label = k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
      // multi-value checkboxes flatten
      if (Array.isArray(v)) v = v.join(', ');
      lines.push(`${label}: ${v}`);
    });
    // Handle multi-select checkbox groups (FormData repeats keys)
    const grouped = {};
    new FormData(form).forEach((v, k) => {
      if (!grouped[k]) grouped[k] = [];
      grouped[k].push(v);
    });
    const finalLines = [];
    Object.keys(grouped).forEach(k => {
      const vals = grouped[k].filter(x => x && String(x).trim() !== '');
      if (!vals.length) return;
      const label = k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
      finalLines.push(`${label}: ${vals.join(', ')}`);
    });
    const body = finalLines.join('\n');
    return `mailto:Orders@ShowMasters.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  }

  /* Estimate form (contact.html) */
  const form        = document.getElementById('estimateForm');
  const formSuccess = document.getElementById('formSuccess');
  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const btn = document.getElementById('submitBtn');
      if (btn) { btn.disabled = true; btn.textContent = 'Opening email...'; }
      const mailto = smplBuildMailto(form, 'Estimate Request — ShowMasters.com');
      window.location.href = mailto;
      setTimeout(() => {
        form.style.display = 'none';
        if (formSuccess) formSuccess.style.display = 'block';
      }, 900);
    });
  }

  /* Order form (order.html) — SMPL-CREW-REQ */
  const orderForm = document.getElementById('orderForm');
  const orderSuccess = document.getElementById('orderSuccess');
  if (orderForm) {
    orderForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const btn = orderForm.querySelector('button[type="submit"]');
      if (btn) { btn.disabled = true; btn.textContent = 'Opening email...'; }
      const mailto = smplBuildMailto(orderForm, 'Crew Order — SMPL-CREW-REQ');
      window.location.href = mailto;
      setTimeout(() => {
        orderForm.style.display = 'none';
        if (orderSuccess) orderSuccess.style.display = 'block';
      }, 900);
    });
  }

  /* Apply form (careers.html) — SMPL-CREW-APP */
  const applyForm = document.getElementById('applyForm');
  const applySuccess = document.getElementById('applySuccess');
  if (applyForm) {
    applyForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const btn = applyForm.querySelector('button[type="submit"]');
      if (btn) { btn.disabled = true; btn.textContent = 'Opening email...'; }
      const mailto = smplBuildMailto(applyForm, 'Crew Application — SMPL-CREW-APP');
      window.location.href = mailto;
      setTimeout(() => {
        applyForm.style.display = 'none';
        if (applySuccess) applySuccess.style.display = 'block';
      }, 900);
    });
  }

  /* FAQ single-open accordion. When one <details> opens, close the others
     in the same list. Applies to .home-faq-item on the homepage. */
  (function smplFaqAccordion() {
    const items = document.querySelectorAll('.home-faq-item');
    if (items.length < 2) return;
    items.forEach(item => {
      item.addEventListener('toggle', () => {
        if (!item.open) return;
        items.forEach(other => { if (other !== item && other.open) other.open = false; });
      });
    });
  })();

  /* Scroll-to-top button. Appears bottom-left after 600px scroll.
     Avoids the path-floater's bottom-right corner. */
  (function smplScrollTop() {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.id = 'smplScrollTop';
    btn.setAttribute('aria-label', 'Back to top');
    btn.innerHTML = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 14 12 8 18 14"/></svg>';
    document.body.appendChild(btn);
    const onScroll = () => {
      btn.classList.toggle('is-visible', window.scrollY > 600);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    btn.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  })();

  /* Cookie consent banner. Shows once per browser; dismissal stored in
     localStorage. Slim bottom-center bar, links to /cookies.html. */
  (function smplCookieBanner() {
    try { if (localStorage.getItem('smpl_cookies_v1') === 'ok') return; } catch (_) {}
    const bar = document.createElement('div');
    bar.id = 'smplCookieBar';
    bar.setAttribute('role', 'dialog');
    bar.setAttribute('aria-label', 'Cookie consent');
    bar.innerHTML = `
      <div class="cookie-inner">
        <p class="cookie-text">We use a minimal set of cookies to make this site work. <a href="/cookies.html" class="gold">See our cookie policy</a>.</p>
        <div class="cookie-actions">
          <button type="button" class="btn btn-ghost cookie-decline" data-cookie="decline">Decline</button>
          <button type="button" class="btn btn-primary cookie-accept" data-cookie="accept">Got it</button>
        </div>
      </div>
    `;
    document.body.appendChild(bar);
    requestAnimationFrame(() => setTimeout(() => bar.classList.add('is-up'), 700));
    bar.addEventListener('click', (e) => {
      const b = e.target.closest('button[data-cookie]');
      if (!b) return;
      try { localStorage.setItem('smpl_cookies_v1', b.dataset.cookie === 'accept' ? 'ok' : 'declined'); } catch (_) {}
      bar.classList.remove('is-up');
      setTimeout(() => bar.remove(), 360);
    });
  })();
});
