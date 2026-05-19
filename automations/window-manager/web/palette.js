// Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
// RKOJ.exe command palette (Cmd/Ctrl+K) — fuzzy search across projects, agents,
// knowledge, skills, tools, inventions, cycle points, schedule entries + ribbon actions.

(function () {
  'use strict';

  var CACHE_TTL_MS = 30 * 1000;
  var MODAL_ID = 'rkoj-palette-modal';
  var STYLE_ID = 'rkoj-palette-style';

  var _cache = null; // { ts, items }
  var _ribbonActions = []; // [{id,label,icon,category,shortcut,handler}]
  var _open = false;
  var _selectedIndex = 0;
  var _currentItems = [];

  function _helpers() {
    return (typeof window !== 'undefined' && window.RkojHelpers) ? window.RkojHelpers : null;
  }

  function _toast(msg) {
    var h = _helpers();
    if (h && typeof h.toast === 'function') {
      try { h.toast(msg); return; } catch (e) {}
    }
    try { console.log('[RkojPalette]', msg); } catch (e) {}
  }

  function _fetchJson(url, opts) {
    var h = _helpers();
    if (h && typeof h.fetchJson === 'function') {
      try { return h.fetchJson(url, opts); } catch (e) {}
    }
    var init = opts || {};
    init.headers = init.headers || {};
    if (h && typeof h._authHeaders === 'function') {
      try {
        var ah = h._authHeaders();
        for (var k in ah) if (Object.prototype.hasOwnProperty.call(ah, k)) init.headers[k] = ah[k];
      } catch (e) {}
    }
    return fetch(url, init).then(function (r) {
      if (!r.ok) throw new Error(url + ' -> ' + r.status);
      return r.json();
    });
  }

  function _switchTab(tabId) {
    var h = _helpers();
    if (h && typeof h.switchTab === 'function') {
      try { h.switchTab(tabId); return true; } catch (e) {}
    }
    // Fallback: dispatch event app.js can listen to.
    try {
      window.dispatchEvent(new CustomEvent('rkoj:switch-tab', { detail: { tab: tabId } }));
    } catch (e) {}
    return false;
  }

  function _openDrawer(name, ctx) {
    var h = _helpers();
    if (h && typeof h.openDrawer === 'function') {
      try { h.openDrawer(name, ctx); return true; } catch (e) {}
    }
    try {
      window.dispatchEvent(new CustomEvent('rkoj:open-drawer', { detail: { drawer: name, ctx: ctx || {} } }));
    } catch (e) {}
    return false;
  }

  function _ensureStyles() {
    if (document.getElementById(STYLE_ID)) return;
    var css = [
      '.rkoj-palette-overlay{position:fixed;inset:0;z-index:9999;display:flex;align-items:flex-start;justify-content:center;padding-top:14vh;',
      'background:rgba(8,8,14,.55);backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);animation:rkojPaletteIn 150ms ease-out;}',
      '.rkoj-palette{width:600px;max-width:92vw;max-height:70vh;display:flex;flex-direction:column;border-radius:14px;overflow:hidden;',
      'background:rgba(28,28,36,.96);backdrop-filter:blur(36px) saturate(180%);-webkit-backdrop-filter:blur(36px) saturate(180%);',
      'border:1px solid color-mix(in oklab,#7A3DD4 40%,transparent);box-shadow:0 24px 80px rgba(0,0,0,.55), 0 0 0 1px rgba(255,255,255,.04) inset;}',
      '.rkoj-palette-input{appearance:none;border:0;outline:0;background:transparent;color:var(--text-primary,#fff);font:13px/1.4 var(--font-sans,system-ui);',
      'padding:14px 16px;border-bottom:1px solid rgba(255,255,255,.06);width:100%;}',
      '.rkoj-palette-list{flex:1;overflow-y:auto;padding:6px 0;}',
      '.rkoj-palette-item{display:flex;align-items:center;gap:10px;padding:8px 14px;cursor:pointer;color:var(--text-secondary,#a1a1aa);font-size:13px;line-height:1.3;}',
      '.rkoj-palette-item:hover,.rkoj-palette-item.is-active{background:color-mix(in oklab,#7A3DD4 18%,transparent);color:var(--text-primary,#fff);}',
      '.rkoj-palette-item .pi-icon{width:18px;text-align:center;opacity:.85;}',
      '.rkoj-palette-item .pi-label{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}',
      '.rkoj-palette-item .pi-cat{font-size:11px;color:var(--text-tertiary,#71717a);padding:2px 8px;border-radius:999px;background:rgba(255,255,255,.05);}',
      '.rkoj-palette-item .pi-shortcut{font-family:var(--font-mono,monospace);font-size:10.5px;color:var(--text-tertiary,#71717a);}',
      '.rkoj-palette-empty{padding:20px 16px;color:var(--text-tertiary,#71717a);font-size:12px;text-align:center;}',
      '.rkoj-palette-footer{padding:6px 14px;border-top:1px solid rgba(255,255,255,.05);font-size:10.5px;color:var(--text-tertiary,#71717a);display:flex;gap:14px;justify-content:flex-end;}',
      '@keyframes rkojPaletteIn{from{opacity:0;transform:translateY(-6px);}to{opacity:1;transform:translateY(0);}}',
      '@media (prefers-reduced-motion: reduce){.rkoj-palette-overlay{animation:none;}}'
    ].join('');
    var s = document.createElement('style');
    s.id = STYLE_ID;
    s.textContent = css;
    document.head.appendChild(s);
  }

  // ---- index build -------------------------------------------------------

  function _safePromise(p, fallback) {
    return Promise.resolve(p).then(function (v) { return v; }, function () { return fallback; });
  }

  function _addItem(arr, item) {
    if (!item || !item.label) return;
    arr.push(item);
  }

  function _normalize(items) {
    // Dedup by id; cap label length softly.
    var seen = {};
    var out = [];
    for (var i = 0; i < items.length; i++) {
      var it = items[i];
      if (!it.id) it.id = (it.category || 'item') + ':' + (it.label || '?') + ':' + i;
      if (seen[it.id]) continue;
      seen[it.id] = true;
      out.push(it);
    }
    return out;
  }

  function index(force) {
    if (!force && _cache && (Date.now() - _cache.ts < CACHE_TTL_MS)) {
      return Promise.resolve(_cache.items);
    }
    var jobs = [
      _safePromise(_fetchJson('/api/launcher/options'), null),
      _safePromise(_fetchJson('/api/sessions'), null),
      _safePromise(_fetchJson('/api/knowledge'), null),
      _safePromise(_fetchJson('/api/skills'), null),
      _safePromise(_fetchJson('/api/tools'), null),
      _safePromise(_fetchJson('/api/inventions'), null),
      _safePromise(_fetchJson('/api/cycle-points'), null),
      _safePromise(_fetchJson('/api/schedule'), null)
    ];
    return Promise.all(jobs).then(function (results) {
      var items = [];
      var opts = results[0];
      var sessions = results[1];
      var knowledge = results[2];
      var skills = results[3];
      var tools = results[4];
      var inventions = results[5];
      var cycles = results[6];
      var schedules = results[7];

      // Projects
      if (opts && Array.isArray(opts.projects)) {
        for (var i = 0; i < opts.projects.length; i++) {
          var pj = opts.projects[i];
          var pname = (typeof pj === 'string') ? pj : (pj.slug || pj.name);
          if (!pname) continue;
          _addItem(items, {
            id: 'project:' + pname,
            label: pname,
            category: 'Project',
            icon: '▶',
            action: { kind: 'project', value: pname }
          });
        }
      }
      // Modes (ribbon-ish helpers)
      if (opts && Array.isArray(opts.modes)) {
        for (var m = 0; m < opts.modes.length; m++) {
          var md = opts.modes[m];
          var mname = (typeof md === 'string') ? md : (md.slug || md.name);
          if (!mname) continue;
          _addItem(items, {
            id: 'mode:' + mname,
            label: 'Launch mode: ' + mname,
            category: 'Mode',
            icon: '⚙',
            action: { kind: 'mode', value: mname }
          });
        }
      }
      // Sessions / agents
      var sArr = (sessions && (sessions.sessions || sessions.agents || sessions.list)) || sessions;
      if (Array.isArray(sArr)) {
        for (var s = 0; s < sArr.length; s++) {
          var ag = sArr[s];
          var aname = (typeof ag === 'string') ? ag : (ag.name || ag.agent || ag.slug);
          if (!aname) continue;
          _addItem(items, {
            id: 'agent:' + aname,
            label: aname,
            category: 'Agent',
            icon: '@',
            action: { kind: 'agent', value: aname }
          });
        }
      }
      function _addSlugList(payload, kind, cat, icon) {
        if (!payload) return;
        var arr = payload[kind] || payload.list || payload.items || payload;
        if (!Array.isArray(arr)) return;
        for (var i = 0; i < arr.length; i++) {
          var it = arr[i];
          var slug = (typeof it === 'string') ? it : (it.slug || it.name || it.id);
          if (!slug) continue;
          var label = (typeof it === 'object' && it.title) ? it.title + ' (' + slug + ')' : slug;
          _addItem(items, {
            id: kind + ':' + slug,
            label: label,
            category: cat,
            icon: icon,
            action: { kind: kind, value: slug }
          });
        }
      }
      _addSlugList(knowledge, 'knowledge', 'Knowledge', '#');
      _addSlugList(skills, 'skills', 'Skill', '*');
      _addSlugList(tools, 'tools', 'Tool', '+');
      _addSlugList(inventions, 'inventions', 'Invention', '~');

      // Cycle points
      var cArr = cycles && (cycles.points || cycles.list || cycles.items);
      if (Array.isArray(cArr)) {
        for (var c = 0; c < cArr.length; c++) {
          var cp = cArr[c];
          if (!cp || !cp.slug) continue;
          _addItem(items, {
            id: 'cycle:' + cp.slug,
            label: (cp.name || cp.slug) + (cp.project ? ' [' + cp.project + ']' : ''),
            category: 'Cycle',
            icon: 'C',
            action: { kind: 'cycle', value: cp.slug, name: cp.name }
          });
        }
      }
      // Schedule entries
      var schArr = schedules && (schedules.entries || schedules.list || schedules.items || schedules);
      if (Array.isArray(schArr)) {
        for (var x = 0; x < schArr.length; x++) {
          var en = schArr[x];
          if (!en || !en.id) continue;
          _addItem(items, {
            id: 'schedule:' + en.id,
            label: (en.name || en.id) + (en.cron ? ' (' + en.cron + ')' : ''),
            category: 'Schedule',
            icon: 'S',
            action: { kind: 'schedule', value: en.id }
          });
        }
      }
      // Ribbon actions (registered separately)
      for (var r = 0; r < _ribbonActions.length; r++) {
        var ra = _ribbonActions[r];
        _addItem(items, {
          id: 'ribbon:' + (ra.id || ra.label),
          label: ra.label,
          category: ra.category || 'Action',
          icon: ra.icon || '▸',
          shortcut: ra.shortcut || '',
          action: { kind: 'ribbon', value: ra.id || ra.label, handler: ra.handler }
        });
      }

      var normed = _normalize(items);
      _cache = { ts: Date.now(), items: normed };
      return normed;
    });
  }

  // ---- fuzzy ranking -----------------------------------------------------

  function fuzzy(query, items) {
    var q = (query || '').toLowerCase().trim();
    if (!q) return items.slice(0, 50);
    var qparts = q.split(/\s+/).filter(Boolean);
    var scored = [];
    for (var i = 0; i < items.length; i++) {
      var it = items[i];
      var hay = ((it.label || '') + ' ' + (it.category || '')).toLowerCase();
      var ok = true;
      var score = 0;
      var lastPos = -1;
      for (var p = 0; p < qparts.length; p++) {
        var part = qparts[p];
        var pos = hay.indexOf(part);
        if (pos < 0) { ok = false; break; }
        // Earlier match → better.
        score += 100 - Math.min(pos, 100);
        // Word-boundary bonus.
        if (pos === 0 || /\s|[-_./:]/.test(hay.charAt(pos - 1))) score += 25;
        // Penalize backwards jumps slightly.
        if (lastPos > pos) score -= 5;
        lastPos = pos;
      }
      if (ok) {
        // Short labels bubble up.
        score += Math.max(0, 40 - (it.label || '').length);
        scored.push({ it: it, s: score });
      }
    }
    scored.sort(function (a, b) { return b.s - a.s; });
    var out = [];
    for (var k = 0; k < scored.length && k < 50; k++) out.push(scored[k].it);
    return out;
  }

  // ---- render + interactions --------------------------------------------

  function _buildModal() {
    var overlay = document.createElement('div');
    overlay.className = 'rkoj-palette-overlay';
    overlay.id = MODAL_ID;
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');

    var box = document.createElement('div');
    box.className = 'rkoj-palette lg-popover';

    var input = document.createElement('input');
    input.type = 'text';
    input.className = 'rkoj-palette-input lg-input';
    input.placeholder = 'Search projects, agents, knowledge, cycles, schedules...';
    input.autocomplete = 'off';
    input.spellcheck = false;

    var list = document.createElement('div');
    list.className = 'rkoj-palette-list';

    var footer = document.createElement('div');
    footer.className = 'rkoj-palette-footer';
    footer.innerHTML = '<span>Enter to select</span><span>Esc to close</span><span>Up/Down to navigate</span>';

    box.appendChild(input);
    box.appendChild(list);
    box.appendChild(footer);
    overlay.appendChild(box);

    overlay.addEventListener('mousedown', function (ev) {
      if (ev.target === overlay) close();
    });

    input.addEventListener('input', function () {
      render(fuzzy(input.value, _allItems()));
    });
    input.addEventListener('keydown', function (ev) {
      if (ev.key === 'Escape') { ev.preventDefault(); close(); return; }
      if (ev.key === 'ArrowDown') {
        ev.preventDefault();
        _selectedIndex = Math.min(_selectedIndex + 1, Math.max(0, _currentItems.length - 1));
        _paintActive();
      } else if (ev.key === 'ArrowUp') {
        ev.preventDefault();
        _selectedIndex = Math.max(0, _selectedIndex - 1);
        _paintActive();
      } else if (ev.key === 'Enter') {
        ev.preventDefault();
        var it = _currentItems[_selectedIndex];
        if (it) _select(it);
      }
    });

    return { overlay: overlay, input: input, list: list };
  }

  var _modal = null;
  var _allItemsCache = [];
  function _allItems() { return _allItemsCache; }

  function _paintActive() {
    if (!_modal) return;
    var nodes = _modal.list.querySelectorAll('.rkoj-palette-item');
    for (var i = 0; i < nodes.length; i++) {
      if (i === _selectedIndex) nodes[i].classList.add('is-active');
      else nodes[i].classList.remove('is-active');
    }
    var active = nodes[_selectedIndex];
    if (active && active.scrollIntoView) active.scrollIntoView({ block: 'nearest' });
  }

  function render(items) {
    if (!_modal) return;
    _currentItems = items || [];
    _selectedIndex = 0;
    var listEl = _modal.list;
    listEl.innerHTML = '';
    if (!_currentItems.length) {
      var empty = document.createElement('div');
      empty.className = 'rkoj-palette-empty';
      empty.textContent = 'No matches.';
      listEl.appendChild(empty);
      return;
    }
    for (var i = 0; i < _currentItems.length; i++) {
      var it = _currentItems[i];
      var row = document.createElement('div');
      row.className = 'rkoj-palette-item' + (i === 0 ? ' is-active' : '');
      row.setAttribute('data-id', it.id);

      var ic = document.createElement('span');
      ic.className = 'pi-icon';
      ic.textContent = it.icon || '·';
      var lb = document.createElement('span');
      lb.className = 'pi-label';
      lb.textContent = it.label || '(unnamed)';
      var ct = document.createElement('span');
      ct.className = 'pi-cat';
      ct.textContent = it.category || '';
      row.appendChild(ic);
      row.appendChild(lb);
      row.appendChild(ct);
      if (it.shortcut) {
        var sc = document.createElement('span');
        sc.className = 'pi-shortcut';
        sc.textContent = it.shortcut;
        row.appendChild(sc);
      }
      (function (item) {
        row.addEventListener('mouseenter', function () {
          var idx = _currentItems.indexOf(item);
          if (idx >= 0) { _selectedIndex = idx; _paintActive(); }
        });
        row.addEventListener('click', function () { _select(item); });
      })(it);
      listEl.appendChild(row);
    }
  }

  function _select(item) {
    if (!item || !item.action) { close(); return; }
    var a = item.action;
    try {
      switch (a.kind) {
        case 'project':
          _switchTab('agents');
          _openDrawer('launcher', { prefillProject: a.value });
          try { window.dispatchEvent(new CustomEvent('rkoj:palette-prefill-project', { detail: { project: a.value } })); } catch (e) {}
          break;
        case 'mode':
          _switchTab('agents');
          try { window.dispatchEvent(new CustomEvent('rkoj:palette-prefill-mode', { detail: { mode: a.value } })); } catch (e) {}
          break;
        case 'agent':
          _switchTab('agents');
          _openDrawer('inbox', { agent: a.value });
          break;
        case 'knowledge':
          _switchTab('agents');
          _openDrawer('knowledge', { slug: a.value });
          break;
        case 'skills':
          _switchTab('agents');
          _openDrawer('knowledge', { kind: 'skills', slug: a.value });
          break;
        case 'tools':
          _switchTab('agents');
          _openDrawer('knowledge', { kind: 'tools', slug: a.value });
          break;
        case 'inventions':
          _switchTab('agents');
          _openDrawer('knowledge', { kind: 'inventions', slug: a.value });
          break;
        case 'cycle':
          _fetchJson('/api/cycle-points/' + encodeURIComponent(a.value) + '/resume', { method: 'POST' })
            .then(function (res) {
              var pid = (res && (res.pid || (res.result && res.result.pid))) || '?';
              _toast('[OK] resumed ' + (a.name || a.value) + ' (PID ' + pid + ')');
            })
            .catch(function (e) { _toast('Resume failed: ' + (e && e.message ? e.message : 'error')); });
          break;
        case 'schedule':
          _switchTab('agents');
          _openDrawer('schedule', { id: a.value });
          break;
        case 'ribbon':
          if (typeof a.handler === 'function') {
            try { a.handler(); } catch (e) { _toast('Action error: ' + e.message); }
          } else {
            try { window.dispatchEvent(new CustomEvent('rkoj:ribbon-action', { detail: { id: a.value } })); } catch (e) {}
          }
          break;
        default:
          _toast('Unhandled selection: ' + a.kind);
      }
    } finally {
      close();
    }
  }

  function open() {
    if (_open) return;
    _ensureStyles();
    if (!_modal) _modal = _buildModal();
    document.body.appendChild(_modal.overlay);
    _open = true;
    _modal.input.value = '';
    _modal.list.innerHTML = '';
    var loading = document.createElement('div');
    loading.className = 'rkoj-palette-empty';
    loading.textContent = 'Indexing...';
    _modal.list.appendChild(loading);
    setTimeout(function () { try { _modal.input.focus(); } catch (e) {} }, 0);
    index().then(function (items) {
      _allItemsCache = items;
      render(items.slice(0, 50));
    }).catch(function (e) {
      _modal.list.innerHTML = '';
      var err = document.createElement('div');
      err.className = 'rkoj-palette-empty';
      err.textContent = 'Index error: ' + (e && e.message ? e.message : 'unknown');
      _modal.list.appendChild(err);
    });
  }

  function close() {
    if (!_open || !_modal) return;
    try { _modal.overlay.parentNode.removeChild(_modal.overlay); } catch (e) {}
    _open = false;
  }

  function toggle() { if (_open) close(); else open(); }

  function registerRibbonAction(action) {
    if (!action || !action.label) return;
    // Replace any existing with same id.
    var id = action.id || action.label;
    for (var i = 0; i < _ribbonActions.length; i++) {
      if ((_ribbonActions[i].id || _ribbonActions[i].label) === id) {
        _ribbonActions.splice(i, 1);
        break;
      }
    }
    _ribbonActions.push(action);
    // Bust cache so the next open picks it up.
    _cache = null;
  }

  function init() {
    _ensureStyles();
    // Default ribbon actions; app.js can register more.
    registerRibbonAction({ id: 'view:devices', label: 'Go to ADB Devices tab', icon: '▶', category: 'Navigate', shortcut: '', handler: function () { _switchTab('devices'); } });
    registerRibbonAction({ id: 'view:agents', label: 'Go to Agents tab', icon: '▶', category: 'Navigate', shortcut: '', handler: function () { _switchTab('agents'); } });
    registerRibbonAction({ id: 'drawer:knowledge', label: 'Open Knowledge drawer', icon: '#', category: 'Drawer', handler: function () { _switchTab('agents'); _openDrawer('knowledge', {}); } });
    registerRibbonAction({ id: 'drawer:memory', label: 'Open Memory drawer', icon: 'M', category: 'Drawer', handler: function () { _switchTab('agents'); _openDrawer('memory', {}); } });
    registerRibbonAction({ id: 'drawer:codex', label: 'Open Codex drawer', icon: 'X', category: 'Drawer', handler: function () { _switchTab('agents'); _openDrawer('codex', {}); } });
    registerRibbonAction({ id: 'drawer:schedule', label: 'Open Scheduler drawer', icon: 'S', category: 'Drawer', handler: function () { _switchTab('agents'); _openDrawer('schedule', {}); } });
    registerRibbonAction({ id: 'drawer:cycle-points', label: 'Open Cycle Points', icon: 'C', category: 'Drawer', handler: function () { _switchTab('agents'); _openDrawer('cycle-points', {}); } });

    window.addEventListener('keydown', function (ev) {
      var key = ev.key;
      var isK = key === 'k' || key === 'K';
      if (isK && (ev.metaKey || ev.ctrlKey)) {
        ev.preventDefault();
        ev.stopPropagation();
        toggle();
      } else if (ev.key === 'Escape' && _open) {
        ev.preventDefault();
        close();
      }
    }, true);
  }

  window.RkojPalette = {
    init: init,
    open: open,
    close: close,
    toggle: toggle,
    index: index,
    fuzzy: fuzzy,
    render: render,
    registerRibbonAction: registerRibbonAction,
    _bustCache: function () { _cache = null; }
  };
})();
