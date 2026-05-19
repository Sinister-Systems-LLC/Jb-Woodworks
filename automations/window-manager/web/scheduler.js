// Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
// RKOJ.exe scheduler client — list + cron presets + kind-specific action forms.
// Talks to /api/schedule (see server.py).

(function () {
  'use strict';

  var SCRIPT_WHITELIST = [
    'check-hetzner-state',
    'verify-backups',
    'memory-garden',
    'aggregate-gotchas',
    'prepare-for-migration-dryrun'
  ];

  var CRON_PRESETS = [
    { id: 'every-minute', label: 'Every minute', cron: '* * * * *' },
    { id: 'every-5min',   label: 'Every 5 minutes', cron: '*/5 * * * *' },
    { id: 'every-15min',  label: 'Every 15 minutes', cron: '*/15 * * * *' },
    { id: 'hourly',       label: 'Hourly (top of hour)', cron: '0 * * * *' },
    { id: 'every-4h',     label: 'Every 4 hours', cron: '0 */4 * * *' },
    { id: 'daily-2am',    label: 'Daily at 2:00 AM', cron: '0 2 * * *' },
    { id: 'daily-9am',    label: 'Daily at 9:00 AM', cron: '0 9 * * *' },
    { id: 'weekdays-9am', label: 'Weekdays at 9 AM', cron: '0 9 * * 1-5' },
    { id: 'weekly-mon',   label: 'Weekly (Mon 9 AM)', cron: '0 9 * * 1' },
    { id: 'monthly',      label: 'Monthly (1st 0:00)', cron: '0 0 1 * *' },
    { id: 'custom',       label: 'Custom...', cron: '' }
  ];

  var _tickTimer = null;
  var _mounted = []; // [{containerEl, entries}]

  function _helpers() {
    return (typeof window !== 'undefined' && window.RkojHelpers) ? window.RkojHelpers : null;
  }

  function _toast(msg) {
    var h = _helpers();
    if (h && typeof h.toast === 'function') {
      try { h.toast(msg); return; } catch (e) {}
    }
    try { console.log('[RkojScheduler]', msg); } catch (e) {}
  }

  function _authHeaders() {
    var h = _helpers();
    if (h && typeof h._authHeaders === 'function') {
      try { return h._authHeaders() || {}; } catch (e) {}
    }
    return {};
  }

  function _fetchJson(url, opts) {
    var h = _helpers();
    if (h && typeof h.fetchJson === 'function') {
      try { return h.fetchJson(url, opts); } catch (e) {}
    }
    var init = opts || {};
    init.headers = init.headers || {};
    var ah = _authHeaders();
    for (var k in ah) if (Object.prototype.hasOwnProperty.call(ah, k)) init.headers[k] = ah[k];
    if (init.body && !init.headers['Content-Type'] && typeof init.body === 'string') {
      init.headers['Content-Type'] = 'application/json';
    }
    return fetch(url, init).then(function (r) {
      if (!r.ok) return r.text().then(function (t) { throw new Error(url + ' -> ' + r.status + ' ' + t); });
      var ct = r.headers.get('content-type') || '';
      return ct.indexOf('application/json') >= 0 ? r.json() : r.text();
    });
  }

  function _broadcast(type, payload) {
    if (window.RkojPopout && typeof window.RkojPopout.broadcast === 'function') {
      try { window.RkojPopout.broadcast(type, payload); } catch (e) {}
    }
  }

  function _el(tag, attrs, children) {
    var node = document.createElement(tag);
    if (attrs) {
      for (var k in attrs) {
        if (!Object.prototype.hasOwnProperty.call(attrs, k)) continue;
        var v = attrs[k];
        if (k === 'class') node.className = v;
        else if (k === 'text') node.textContent = v;
        else if (k === 'html') node.innerHTML = v;
        else if (k.indexOf('on') === 0 && typeof v === 'function') node.addEventListener(k.slice(2), v);
        else if (k === 'dataset' && v && typeof v === 'object') {
          for (var dk in v) if (Object.prototype.hasOwnProperty.call(v, dk)) node.dataset[dk] = v[dk];
        } else if (v === false || v === null || typeof v === 'undefined') { /* skip */ }
        else node.setAttribute(k, v);
      }
    }
    if (children) {
      for (var i = 0; i < children.length; i++) {
        var c = children[i];
        if (c == null) continue;
        if (typeof c === 'string') node.appendChild(document.createTextNode(c));
        else node.appendChild(c);
      }
    }
    return node;
  }

  // ---- cron humanizer ---------------------------------------------------

  function humanCron(expr) {
    if (!expr || typeof expr !== 'string') return '(no cron)';
    var s = expr.trim();
    // Direct preset match.
    for (var i = 0; i < CRON_PRESETS.length; i++) {
      if (CRON_PRESETS[i].cron && CRON_PRESETS[i].cron === s) return CRON_PRESETS[i].label;
    }
    var parts = s.split(/\s+/);
    if (parts.length !== 5) return s;
    var m = parts[0], h = parts[1], dom = parts[2], mon = parts[3], dow = parts[4];

    function isStar(x) { return x === '*'; }
    function asNum(x) { var n = parseInt(x, 10); return isNaN(n) ? null : n; }

    // * * * * *
    if (isStar(m) && isStar(h) && isStar(dom) && isStar(mon) && isStar(dow)) return 'every minute';
    // */N * * * *
    var stepM = /^\*\/(\d+)$/.exec(m);
    if (stepM && isStar(h) && isStar(dom) && isStar(mon) && isStar(dow)) return 'every ' + stepM[1] + ' minute(s)';
    // 0 * * * *
    if (m === '0' && isStar(h) && isStar(dom) && isStar(mon) && isStar(dow)) return 'every hour';
    // 0 */N * * *
    var stepH = /^\*\/(\d+)$/.exec(h);
    if (m === '0' && stepH && isStar(dom) && isStar(mon) && isStar(dow)) return 'every ' + stepH[1] + ' hour(s)';
    // 0 H * * *  -> daily at H
    var mn = asNum(m), hn = asNum(h);
    if (mn !== null && hn !== null && isStar(dom) && isStar(mon) && isStar(dow)) {
      return 'daily at ' + _fmtClock(hn, mn);
    }
    // 0 H * * 1-5  weekdays
    if (mn !== null && hn !== null && isStar(dom) && isStar(mon) && dow === '1-5') {
      return 'weekdays at ' + _fmtClock(hn, mn);
    }
    // 0 H * * D  -> weekly
    if (mn !== null && hn !== null && isStar(dom) && isStar(mon) && /^\d$/.test(dow)) {
      var days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
      return 'weekly on ' + days[parseInt(dow, 10) % 7] + ' at ' + _fmtClock(hn, mn);
    }
    // 0 0 D * *  -> monthly
    if (m === '0' && h === '0' && /^\d+$/.test(dom) && isStar(mon) && isStar(dow)) {
      return 'monthly on day ' + dom;
    }
    return s;
  }

  function _fmtClock(h, m) {
    var hh = ((h % 12) === 0) ? 12 : (h % 12);
    var ampm = h < 12 ? 'AM' : 'PM';
    var mm = (m < 10) ? '0' + m : ('' + m);
    return hh + ':' + mm + ' ' + ampm;
  }

  // ---- countdown --------------------------------------------------------

  function _fmtCountdown(targetIso) {
    if (!targetIso) return '—';
    var t = Date.parse(targetIso);
    if (isNaN(t)) return targetIso;
    var diff = Math.floor((t - Date.now()) / 1000);
    if (diff <= 0) return 'due';
    var d = Math.floor(diff / 86400); diff -= d * 86400;
    var h = Math.floor(diff / 3600); diff -= h * 3600;
    var m = Math.floor(diff / 60); var s = diff - m * 60;
    if (d > 0) return d + 'd ' + h + 'h';
    if (h > 0) return h + 'h ' + m + 'm';
    if (m > 0) return m + 'm ' + s + 's';
    return s + 's';
  }

  function _startTicker() {
    if (_tickTimer) return;
    _tickTimer = setInterval(function () {
      var nodes = document.querySelectorAll('.next-run-countdown[data-next-run]');
      for (var i = 0; i < nodes.length; i++) {
        var iso = nodes[i].getAttribute('data-next-run');
        nodes[i].textContent = _fmtCountdown(iso);
      }
    }, 1000);
  }

  // ---- list -------------------------------------------------------------

  function _renderRow(entry) {
    var last = entry.last_run || {};
    var lastBadge = _el('span', {
      class: 'sched-last-badge',
      style: 'padding:2px 8px;border-radius:999px;font-size:11px;background:' +
        (last.ok === true ? 'rgba(16,185,129,.18)' : last.ok === false ? 'rgba(229,72,77,.18)' : 'rgba(255,255,255,.06)') + ';color:' +
        (last.ok === true ? '#10B981' : last.ok === false ? '#E5484D' : '#a1a1aa') + ';',
      text: last.at ? (last.ok ? 'OK' : 'FAIL') + ' ' + (last.ms ? (last.ms + 'ms') : '') : 'never'
    });

    var countdown = _el('span', {
      class: 'next-run-countdown',
      'data-next-run': entry.next_run || '',
      text: _fmtCountdown(entry.next_run || '')
    });

    var toggle = _el('input', {
      type: 'checkbox',
      checked: entry.enabled ? '' : false,
      onchange: function () {
        _fetchJson('/api/schedule/' + encodeURIComponent(entry.id), {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ enabled: !!toggle.checked })
        }).then(function () {
          _toast('[OK] ' + (toggle.checked ? 'enabled ' : 'disabled ') + (entry.name || entry.id));
          _broadcast('schedule-updated', { id: entry.id });
        }).catch(function (e) {
          toggle.checked = !toggle.checked;
          _toast('Toggle failed: ' + (e && e.message ? e.message : 'error'));
        });
      }
    });
    if (entry.enabled) toggle.checked = true;

    var runBtn = _el('button', { class: 'lg-button', type: 'button', text: 'Run Now', onclick: function () { runNow(entry.id); } });
    var editBtn = _el('button', { class: 'lg-button', type: 'button', text: 'Edit', onclick: function () { openAddModal(entry); } });
    var delBtn = _el('button', {
      class: 'lg-button',
      type: 'button',
      text: 'Delete',
      onclick: function () {
        var ok = false;
        try { ok = window.confirm('Delete schedule "' + (entry.name || entry.id) + '"?'); } catch (e) { ok = true; }
        if (!ok) return;
        _fetchJson('/api/schedule/' + encodeURIComponent(entry.id), { method: 'DELETE' })
          .then(function () {
            _toast('[OK] deleted');
            _broadcast('schedule-updated', { id: entry.id, deleted: true });
            var hosts = document.querySelectorAll('.rkoj-sched-host');
            for (var i = 0; i < hosts.length; i++) refresh(hosts[i]);
          })
          .catch(function (e) { _toast('Delete failed: ' + (e && e.message ? e.message : 'error')); });
      }
    });

    return _el('div', { class: 'lg-card sched-row', dataset: { id: entry.id } }, [
      _el('div', { class: 'sched-head' }, [
        _el('strong', { class: 'sched-name', text: entry.name || entry.id }),
        _el('span', { class: 'sched-kind', text: entry.kind || '', style: 'margin-left:8px;font-size:11px;color:#a1a1aa;' })
      ]),
      _el('div', { class: 'sched-meta', style: 'display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:#a1a1aa;margin:6px 0;' }, [
        _el('span', { class: 'sched-cron', text: humanCron(entry.cron) }),
        _el('span', { class: 'sched-cron-raw', text: '(' + (entry.cron || '') + ')', style: 'font-family:var(--font-mono,monospace);color:#71717a;' }),
        lastBadge,
        _el('span', { text: 'next in ' }),
        countdown
      ]),
      _el('div', { class: 'sched-actions', style: 'display:flex;gap:8px;align-items:center;' }, [
        _el('label', { style: 'display:flex;gap:6px;align-items:center;font-size:12px;' }, [toggle, _el('span', { text: 'enabled' })]),
        runBtn, editBtn, delBtn
      ])
    ]);
  }

  function refresh(containerEl) {
    if (!containerEl) return Promise.resolve([]);
    containerEl.classList.add('rkoj-sched-host');
    containerEl.innerHTML = '';
    var loading = _el('div', { class: 'sched-loading', text: 'Loading schedule...' });
    containerEl.appendChild(loading);
    return _fetchJson('/api/schedule')
      .then(function (resp) {
        containerEl.innerHTML = '';
        var arr = (resp && (resp.entries || resp.list || resp.items)) || resp;
        if (!Array.isArray(arr)) arr = [];
        if (!arr.length) {
          containerEl.appendChild(_el('div', { class: 'sched-empty', text: 'No scheduled tasks. Use "+ New schedule" to add one.' }));
        }
        for (var i = 0; i < arr.length; i++) {
          containerEl.appendChild(_renderRow(arr[i]));
        }
        // Add button (only mount once per host).
        if (!containerEl.querySelector('.sched-add-btn')) {
          var addBtn = _el('button', {
            class: 'lg-button lg-pill-active sched-add-btn',
            type: 'button',
            text: '+ New schedule',
            style: 'margin-top:12px;',
            onclick: function () { openAddModal(null); }
          });
          containerEl.appendChild(addBtn);
        }
        _startTicker();
        return arr;
      })
      .catch(function (e) {
        containerEl.innerHTML = '';
        containerEl.appendChild(_el('div', { class: 'sched-error', text: 'Failed to load: ' + (e && e.message ? e.message : 'error') }));
        return [];
      });
  }

  // ---- modal: add/edit -------------------------------------------------

  function _closeModal(host) {
    if (host && host.parentNode) host.parentNode.removeChild(host);
  }

  function _buildModalHost() {
    var overlay = _el('div', { class: 'rkoj-modal-overlay rkoj-sched-modal-overlay' });
    overlay.style.cssText = 'position:fixed;inset:0;z-index:9800;display:flex;align-items:center;justify-content:center;background:rgba(8,8,14,.55);backdrop-filter:blur(6px);';
    overlay.addEventListener('mousedown', function (ev) {
      if (ev.target === overlay) _closeModal(overlay);
    });
    return overlay;
  }

  function _modalFromTemplate(tplId, fallbackBuilder) {
    var tpl = document.getElementById(tplId);
    var host = _buildModalHost();
    var body;
    if (tpl && tpl.content) {
      var frag = tpl.content.cloneNode(true);
      body = _el('div', { class: 'lg-popover rkoj-modal-body' }, []);
      body.appendChild(frag);
    } else {
      body = fallbackBuilder ? fallbackBuilder() : _el('div', { class: 'lg-popover rkoj-modal-body' });
    }
    body.style.cssText = 'min-width:520px;max-width:92vw;max-height:80vh;overflow-y:auto;padding:18px;border-radius:14px;background:rgba(28,28,36,.96);backdrop-filter:blur(36px);border:1px solid color-mix(in oklab,#7A3DD4 40%,transparent);';
    host.appendChild(body);
    document.body.appendChild(host);
    return { host: host, body: body };
  }

  // Build action form per kind.
  function _buildKindForm(kind, action) {
    action = action || {};
    var wrap = _el('div', { class: 'sched-action-form', dataset: { kind: kind }, style: 'display:flex;flex-direction:column;gap:8px;margin:8px 0;' });

    if (kind === 'script') {
      var sel = _el('select', { class: 'lg-input', name: 'action-script', style: 'width:100%;' });
      for (var i = 0; i < SCRIPT_WHITELIST.length; i++) {
        var opt = document.createElement('option');
        opt.value = SCRIPT_WHITELIST[i];
        opt.textContent = SCRIPT_WHITELIST[i];
        if (action.script === SCRIPT_WHITELIST[i]) opt.selected = true;
        sel.appendChild(opt);
      }
      var args = _el('input', {
        class: 'lg-input',
        type: 'text',
        name: 'action-args',
        placeholder: 'args (space-separated)',
        value: Array.isArray(action.args) ? action.args.join(' ') : (action.args || ''),
        style: 'width:100%;'
      });
      wrap.appendChild(_el('label', { text: 'Script', style: 'font-size:12px;color:#a1a1aa;' }));
      wrap.appendChild(sel);
      wrap.appendChild(_el('label', { text: 'Args', style: 'font-size:12px;color:#a1a1aa;' }));
      wrap.appendChild(args);
    } else if (kind === 'spawn-agent') {
      var pj = _el('select', { class: 'lg-input', name: 'action-project', style: 'width:100%;' });
      var md = _el('select', { class: 'lg-input', name: 'action-mode', style: 'width:100%;' });
      pj.innerHTML = '<option value="">(loading projects...)</option>';
      md.innerHTML = '<option value="">(loading modes...)</option>';
      _fetchJson('/api/launcher/options').then(function (opts) {
        pj.innerHTML = '<option value="">(select project)</option>';
        if (opts && Array.isArray(opts.projects)) {
          for (var i = 0; i < opts.projects.length; i++) {
            var p = opts.projects[i];
            var name = (typeof p === 'string') ? p : (p.slug || p.name);
            if (!name) continue;
            var o = document.createElement('option'); o.value = name; o.textContent = name;
            if (action.project === name) o.selected = true;
            pj.appendChild(o);
          }
        }
        md.innerHTML = '<option value="">(select mode)</option>';
        if (opts && Array.isArray(opts.modes)) {
          for (var j = 0; j < opts.modes.length; j++) {
            var m = opts.modes[j];
            var mn = (typeof m === 'string') ? m : (m.slug || m.name);
            if (!mn) continue;
            var o2 = document.createElement('option'); o2.value = mn; o2.textContent = mn;
            if (action.mode === mn) o2.selected = true;
            md.appendChild(o2);
          }
        }
      }).catch(function () {});
      var fast = _el('input', { type: 'checkbox', name: 'action-fast' });
      if (action.fast) fast.checked = true;
      var prompt = _el('textarea', { class: 'lg-input', name: 'action-custom-prompt', rows: '3', placeholder: 'custom_prompt (optional)', style: 'width:100%;' });
      if (action.custom_prompt) prompt.value = action.custom_prompt;
      wrap.appendChild(_el('label', { text: 'Project', style: 'font-size:12px;color:#a1a1aa;' }));
      wrap.appendChild(pj);
      wrap.appendChild(_el('label', { text: 'Mode', style: 'font-size:12px;color:#a1a1aa;' }));
      wrap.appendChild(md);
      wrap.appendChild(_el('label', { style: 'font-size:12px;color:#a1a1aa;display:flex;gap:6px;align-items:center;' }, [fast, _el('span', { text: 'Fast (haiku)' })]));
      wrap.appendChild(_el('label', { text: 'Custom prompt', style: 'font-size:12px;color:#a1a1aa;' }));
      wrap.appendChild(prompt);
    } else if (kind === 'inbox') {
      var to = _el('input', { class: 'lg-input', type: 'text', name: 'action-to', placeholder: 'agent name or *', value: action.to || '*', style: 'width:100%;' });
      var body = _el('textarea', { class: 'lg-input', name: 'action-body', rows: '4', placeholder: 'message body', style: 'width:100%;' });
      if (action.body) body.value = action.body;
      var tags = _el('input', { class: 'lg-input', type: 'text', name: 'action-tags', placeholder: 'tags (comma-separated)', value: Array.isArray(action.tags) ? action.tags.join(',') : (action.tags || ''), style: 'width:100%;' });
      wrap.appendChild(_el('label', { text: 'To (agent name or *)', style: 'font-size:12px;color:#a1a1aa;' }));
      wrap.appendChild(to);
      wrap.appendChild(_el('label', { text: 'Body', style: 'font-size:12px;color:#a1a1aa;' }));
      wrap.appendChild(body);
      wrap.appendChild(_el('label', { text: 'Tags', style: 'font-size:12px;color:#a1a1aa;' }));
      wrap.appendChild(tags);
    } else if (kind === 'resume-cycle') {
      var slugSel = _el('select', { class: 'lg-input', name: 'action-slug', style: 'width:100%;' });
      slugSel.innerHTML = '<option value="">(loading cycles...)</option>';
      _fetchJson('/api/cycle-points').then(function (resp) {
        slugSel.innerHTML = '<option value="">(select cycle)</option>';
        var arr = (resp && (resp.points || resp.list || resp.items)) || resp;
        if (Array.isArray(arr)) {
          for (var i = 0; i < arr.length; i++) {
            var c = arr[i];
            if (!c || !c.slug) continue;
            var o = document.createElement('option');
            o.value = c.slug;
            o.textContent = (c.name || c.slug) + (c.project ? ' [' + c.project + ']' : '');
            if (action.slug === c.slug) o.selected = true;
            slugSel.appendChild(o);
          }
        }
      }).catch(function () {});
      wrap.appendChild(_el('label', { text: 'Cycle point', style: 'font-size:12px;color:#a1a1aa;' }));
      wrap.appendChild(slugSel);
    } else if (kind === 'http') {
      var method = _el('select', { class: 'lg-input', name: 'action-method', style: 'width:100%;' });
      ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'].forEach(function (mname) {
        var o = document.createElement('option'); o.value = mname; o.textContent = mname;
        if (action.method === mname) o.selected = true;
        method.appendChild(o);
      });
      var url = _el('input', { class: 'lg-input', type: 'text', name: 'action-url', placeholder: 'http(s)://...', value: action.url || '', style: 'width:100%;' });
      var bodyT = _el('textarea', { class: 'lg-input', name: 'action-body', rows: '4', placeholder: 'request body (JSON or text)', style: 'width:100%;' });
      if (action.body) bodyT.value = typeof action.body === 'string' ? action.body : JSON.stringify(action.body, null, 2);
      wrap.appendChild(_el('label', { text: 'Method', style: 'font-size:12px;color:#a1a1aa;' }));
      wrap.appendChild(method);
      wrap.appendChild(_el('label', { text: 'URL', style: 'font-size:12px;color:#a1a1aa;' }));
      wrap.appendChild(url);
      wrap.appendChild(_el('label', { text: 'Body', style: 'font-size:12px;color:#a1a1aa;' }));
      wrap.appendChild(bodyT);
    } else {
      wrap.appendChild(_el('div', { text: 'Unknown kind: ' + kind, style: 'color:#E5484D;font-size:12px;' }));
    }
    return wrap;
  }

  function _collectKindAction(formEl) {
    var kind = formEl.dataset.kind;
    var action = {};
    function v(name) {
      var el = formEl.querySelector('[name="' + name + '"]');
      return el ? el.value : '';
    }
    function checked(name) {
      var el = formEl.querySelector('[name="' + name + '"]');
      return el ? !!el.checked : false;
    }
    if (kind === 'script') {
      action.script = v('action-script');
      var raw = v('action-args').trim();
      action.args = raw ? raw.split(/\s+/) : [];
    } else if (kind === 'spawn-agent') {
      action.project = v('action-project');
      action.mode = v('action-mode');
      action.fast = checked('action-fast');
      var cp = v('action-custom-prompt').trim();
      if (cp) action.custom_prompt = cp;
    } else if (kind === 'inbox') {
      action.to = v('action-to').trim() || '*';
      action.body = v('action-body');
      var tg = v('action-tags').trim();
      action.tags = tg ? tg.split(',').map(function (s) { return s.trim(); }).filter(Boolean) : [];
    } else if (kind === 'resume-cycle') {
      action.slug = v('action-slug');
    } else if (kind === 'http') {
      action.method = v('action-method') || 'GET';
      action.url = v('action-url').trim();
      var bodyRaw = v('action-body').trim();
      if (bodyRaw) {
        try { action.body = JSON.parse(bodyRaw); }
        catch (e) { action.body = bodyRaw; }
      }
    }
    return { kind: kind, action: action };
  }

  function openAddModal(existing) {
    var isEdit = !!(existing && existing.id);

    var fallback = function () {
      var body = _el('div', { class: 'lg-popover rkoj-modal-body' });
      body.appendChild(_el('h3', { text: isEdit ? 'Edit schedule' : 'New schedule', style: 'margin:0 0 12px 0;' }));

      var nameInput = _el('input', { class: 'lg-input', type: 'text', name: 'sched-name', placeholder: 'name', value: existing && existing.name || '', style: 'width:100%;margin-bottom:10px;' });

      var presetSel = _el('select', { class: 'lg-input', name: 'sched-preset', style: 'width:100%;margin-bottom:6px;' });
      var customOpt = null;
      for (var i = 0; i < CRON_PRESETS.length; i++) {
        var o = document.createElement('option');
        o.value = CRON_PRESETS[i].id;
        o.textContent = CRON_PRESETS[i].label;
        if (CRON_PRESETS[i].id === 'custom') customOpt = o;
        if (existing && existing.cron === CRON_PRESETS[i].cron && CRON_PRESETS[i].cron) o.selected = true;
        presetSel.appendChild(o);
      }
      var cronInput = _el('input', { class: 'lg-input', type: 'text', name: 'sched-cron', placeholder: 'cron expression (m h dom mon dow)', value: existing && existing.cron || '', style: 'width:100%;margin-bottom:12px;font-family:var(--font-mono,monospace);' });

      var kindSel = _el('select', { class: 'lg-input', name: 'sched-kind', style: 'width:100%;margin-bottom:10px;' });
      var KINDS = [
        { v: 'script', t: 'Run script' },
        { v: 'spawn-agent', t: 'Spawn agent' },
        { v: 'inbox', t: 'Inbox send' },
        { v: 'resume-cycle', t: 'Resume cycle point' },
        { v: 'http', t: 'HTTP request' }
      ];
      for (var k = 0; k < KINDS.length; k++) {
        var ok = document.createElement('option');
        ok.value = KINDS[k].v;
        ok.textContent = KINDS[k].t;
        if (existing && existing.kind === KINDS[k].v) ok.selected = true;
        kindSel.appendChild(ok);
      }

      var actionHost = _el('div', { class: 'sched-action-host' });

      var enabledBox = _el('input', { type: 'checkbox', name: 'sched-enabled' });
      if (!existing || existing.enabled !== false) enabledBox.checked = true;
      var enabledLabel = _el('label', { style: 'display:flex;gap:6px;align-items:center;font-size:12px;margin:8px 0;' }, [enabledBox, _el('span', { text: 'enabled' })]);

      var btnRow = _el('div', { style: 'display:flex;gap:8px;justify-content:flex-end;margin-top:8px;' });
      btnRow.appendChild(_el('button', { class: 'lg-button', type: 'button', text: 'Cancel', 'data-action': 'cancel' }));
      btnRow.appendChild(_el('button', { class: 'lg-button lg-pill-active', type: 'button', text: isEdit ? 'Update' : 'Create', 'data-action': 'save' }));

      body.appendChild(_el('label', { text: 'Name', style: 'font-size:12px;color:#a1a1aa;' }));
      body.appendChild(nameInput);
      body.appendChild(_el('label', { text: 'Preset', style: 'font-size:12px;color:#a1a1aa;' }));
      body.appendChild(presetSel);
      body.appendChild(_el('label', { text: 'Cron', style: 'font-size:12px;color:#a1a1aa;' }));
      body.appendChild(cronInput);
      body.appendChild(_el('label', { text: 'Kind', style: 'font-size:12px;color:#a1a1aa;' }));
      body.appendChild(kindSel);
      body.appendChild(actionHost);
      body.appendChild(enabledLabel);
      body.appendChild(btnRow);
      return body;
    };

    var modal = _modalFromTemplate('tpl-schedule-add-modal', fallback);

    var nameEl = modal.body.querySelector('[name="sched-name"]');
    var presetEl = modal.body.querySelector('[name="sched-preset"]');
    var cronEl = modal.body.querySelector('[name="sched-cron"]');
    var kindEl = modal.body.querySelector('[name="sched-kind"]');
    var enabledEl = modal.body.querySelector('[name="sched-enabled"]');
    var actionHost = modal.body.querySelector('.sched-action-host');
    var saveBtn = modal.body.querySelector('[data-action="save"]');
    var cancelBtn = modal.body.querySelector('[data-action="cancel"]');

    // If template was used, presetEl/cronEl/etc may exist with different markup;
    // populate presetEl options if empty.
    if (presetEl && presetEl.tagName === 'SELECT' && presetEl.options.length === 0) {
      for (var pi = 0; pi < CRON_PRESETS.length; pi++) {
        var pop = document.createElement('option');
        pop.value = CRON_PRESETS[pi].id;
        pop.textContent = CRON_PRESETS[pi].label;
        presetEl.appendChild(pop);
      }
    }
    if (kindEl && kindEl.tagName === 'SELECT' && kindEl.options.length === 0) {
      [['script','Run script'],['spawn-agent','Spawn agent'],['inbox','Inbox send'],['resume-cycle','Resume cycle'],['http','HTTP request']].forEach(function (k) {
        var o = document.createElement('option'); o.value = k[0]; o.textContent = k[1]; kindEl.appendChild(o);
      });
    }

    if (presetEl) {
      presetEl.addEventListener('change', function () {
        var id = presetEl.value;
        for (var i = 0; i < CRON_PRESETS.length; i++) {
          if (CRON_PRESETS[i].id === id) {
            if (CRON_PRESETS[i].cron) cronEl.value = CRON_PRESETS[i].cron;
            break;
          }
        }
      });
    }

    function rebuildKindForm() {
      if (!actionHost) return;
      actionHost.innerHTML = '';
      var kind = kindEl ? kindEl.value : 'script';
      var current = (existing && existing.kind === kind) ? (existing.action || {}) : {};
      actionHost.appendChild(_buildKindForm(kind, current));
    }
    if (kindEl) kindEl.addEventListener('change', rebuildKindForm);
    rebuildKindForm();

    if (cancelBtn) cancelBtn.addEventListener('click', function () { _closeModal(modal.host); });
    if (saveBtn) {
      saveBtn.addEventListener('click', function () {
        var name = (nameEl && nameEl.value || '').trim();
        var cron = (cronEl && cronEl.value || '').trim();
        if (!name) { _toast('Name required'); return; }
        if (!cron) { _toast('Cron required'); return; }
        var formEl = actionHost ? actionHost.querySelector('.sched-action-form') : null;
        if (!formEl) { _toast('Action form missing'); return; }
        var coll = _collectKindAction(formEl);
        var payload = {
          name: name,
          cron: cron,
          kind: coll.kind,
          action: coll.action,
          enabled: enabledEl ? !!enabledEl.checked : true
        };
        saveBtn.disabled = true;
        var url = '/api/schedule';
        var method = 'POST';
        if (isEdit) {
          url = '/api/schedule/' + encodeURIComponent(existing.id);
          method = 'PATCH';
        }
        _fetchJson(url, {
          method: method,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        }).then(function () {
          _toast('[OK] ' + (isEdit ? 'updated' : 'created') + ' schedule "' + name + '"');
          _broadcast('schedule-updated', { id: existing && existing.id });
          _closeModal(modal.host);
          var hosts = document.querySelectorAll('.rkoj-sched-host');
          for (var i = 0; i < hosts.length; i++) refresh(hosts[i]);
        }).catch(function (e) {
          saveBtn.disabled = false;
          _toast('Save failed: ' + (e && e.message ? e.message : 'error'));
        });
      });
    }

    if (nameEl) setTimeout(function () { try { nameEl.focus(); } catch (e) {} }, 30);
    return modal.host;
  }

  function runNow(id) {
    if (!id) return Promise.reject(new Error('id required'));
    return _fetchJson('/api/schedule/' + encodeURIComponent(id) + '/run-now', { method: 'POST' })
      .then(function (resp) {
        var ok = resp && (resp.ok !== false);
        var ms = (resp && resp.ms) ? (' (' + resp.ms + 'ms)') : '';
        var detail = (resp && (resp.detail || resp.error)) ? ' — ' + (resp.detail || resp.error) : '';
        _toast((ok ? '[OK] ran ' : '[FAIL] ') + id + ms + detail);
        _broadcast('schedule-ran', { id: id, ok: ok });
        var hosts = document.querySelectorAll('.rkoj-sched-host');
        for (var i = 0; i < hosts.length; i++) refresh(hosts[i]);
        return resp;
      })
      .catch(function (e) {
        _toast('Run failed: ' + (e && e.message ? e.message : 'error'));
        throw e;
      });
  }

  function _bindBroadcasts() {
    if (window.RkojPopout && typeof window.RkojPopout.onMessage === 'function') {
      window.RkojPopout.onMessage('schedule-updated', function () {
        var hosts = document.querySelectorAll('.rkoj-sched-host');
        for (var i = 0; i < hosts.length; i++) refresh(hosts[i]);
      });
    } else {
      setTimeout(_bindBroadcasts, 200);
    }
  }
  _bindBroadcasts();

  window.RkojScheduler = {
    refresh: refresh,
    humanCron: humanCron,
    openAddModal: openAddModal,
    runNow: runNow,
    CRON_PRESETS: CRON_PRESETS,
    SCRIPT_WHITELIST: SCRIPT_WHITELIST
  };
})();
