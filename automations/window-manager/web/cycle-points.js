// Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
// RKOJ.exe cycle-points client — list + save modal + resume + edit/delete.
// Talks to /api/cycle-points (see server.py). Vanilla JS; no deps.

(function () {
  'use strict';

  function _helpers() {
    return (typeof window !== 'undefined' && window.RkojHelpers) ? window.RkojHelpers : null;
  }

  function _toast(msg) {
    var h = _helpers();
    if (h && typeof h.toast === 'function') {
      try { h.toast(msg); return; } catch (e) {}
    }
    try { console.log('[RkojCyclePoints]', msg); } catch (e) {}
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

  function _fmtTime(iso) {
    if (!iso) return '';
    try {
      var d = new Date(iso);
      if (isNaN(d.getTime())) return iso;
      return d.toLocaleString();
    } catch (e) { return iso; }
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

  function _renderRow(cp) {
    var actions = _el('div', { class: 'cp-actions' }, [
      _el('button', {
        class: 'lg-button',
        type: 'button',
        'data-action': 'resume',
        onclick: function () { resume(cp.slug); }
      }, ['Resume']),
      _el('button', {
        class: 'lg-button',
        type: 'button',
        'data-action': 'edit',
        onclick: function () { _openEditModal(cp); }
      }, ['Edit']),
      _el('button', {
        class: 'lg-button',
        type: 'button',
        'data-action': 'delete',
        onclick: function () { del(cp.slug); }
      }, ['Delete'])
    ]);

    var meta = _el('div', { class: 'cp-meta' }, [
      _el('span', { class: 'cp-project', text: cp.project || '' }),
      _el('span', { class: 'cp-note', text: cp.note || '' }),
      _el('span', { class: 'cp-ts', text: _fmtTime(cp.created_at) })
    ]);

    return _el('div', { class: 'lg-card cp-row', dataset: { slug: cp.slug } }, [
      _el('div', { class: 'cp-head' }, [
        _el('strong', { class: 'cp-name', text: cp.name || cp.slug })
      ]),
      meta,
      actions
    ]);
  }

  function refresh(containerEl) {
    if (!containerEl) return Promise.resolve([]);
    containerEl.classList.add('rkoj-cp-host');
    containerEl.innerHTML = '';
    var loading = _el('div', { class: 'cp-loading', text: 'Loading cycle points...' });
    containerEl.appendChild(loading);
    return _fetchJson('/api/cycle-points')
      .then(function (resp) {
        containerEl.innerHTML = '';
        var arr = (resp && (resp.points || resp.list || resp.items)) || resp;
        if (!Array.isArray(arr)) arr = [];
        if (!arr.length) {
          containerEl.appendChild(_el('div', { class: 'cp-empty', text: 'No cycle points yet. Save one from an agent card.' }));
          return arr;
        }
        // Sort recent-first.
        arr.sort(function (a, b) {
          var ta = a && a.created_at ? Date.parse(a.created_at) : 0;
          var tb = b && b.created_at ? Date.parse(b.created_at) : 0;
          return tb - ta;
        });
        for (var i = 0; i < arr.length; i++) {
          containerEl.appendChild(_renderRow(arr[i]));
        }
        return arr;
      })
      .catch(function (e) {
        containerEl.innerHTML = '';
        containerEl.appendChild(_el('div', { class: 'cp-error', text: 'Failed to load: ' + (e && e.message ? e.message : 'error') }));
        return [];
      });
  }

  // ---- modal ------------------------------------------------------------

  function _closeModal(host) {
    if (host && host.parentNode) host.parentNode.removeChild(host);
  }

  function _buildModalHost() {
    var overlay = _el('div', { class: 'rkoj-modal-overlay rkoj-cp-modal-overlay' });
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
    body.style.cssText = 'min-width:420px;max-width:92vw;padding:18px;border-radius:14px;background:rgba(28,28,36,.96);backdrop-filter:blur(36px);border:1px solid color-mix(in oklab,#7A3DD4 40%,transparent);';
    host.appendChild(body);
    document.body.appendChild(host);
    return { host: host, body: body };
  }

  function openSaveModal(opts) {
    opts = opts || {};
    var prefilledAgent = opts.prefilledAgent || null;

    var fallback = function () {
      var body = _el('div', { class: 'lg-popover rkoj-modal-body' });
      body.appendChild(_el('h3', { text: 'Save Cycle Point', style: 'margin:0 0 12px 0;' }));
      var nameInput = _el('input', { class: 'lg-input', type: 'text', placeholder: 'Name (e.g. snap-api SS03 hypothesis 3)', name: 'cp-name', style: 'width:100%;margin-bottom:10px;' });
      var projectSelect = _el('select', { class: 'lg-input', name: 'cp-project', style: 'width:100%;margin-bottom:10px;' });
      var noteInput = _el('textarea', { class: 'lg-input', placeholder: 'Note (optional context for resume)', name: 'cp-note', rows: '4', style: 'width:100%;margin-bottom:12px;' });
      var btnRow = _el('div', { style: 'display:flex;gap:8px;justify-content:flex-end;' });
      var cancelBtn = _el('button', { class: 'lg-button', type: 'button', text: 'Cancel' });
      var saveBtn = _el('button', { class: 'lg-button lg-pill-active', type: 'button', text: 'Save' });
      btnRow.appendChild(cancelBtn);
      btnRow.appendChild(saveBtn);
      body.appendChild(nameInput);
      body.appendChild(projectSelect);
      body.appendChild(noteInput);
      body.appendChild(btnRow);
      return body;
    };

    var modal = _modalFromTemplate('tpl-cycle-save-modal', fallback);

    // Locate inputs (either from template or fallback).
    var nameEl = modal.body.querySelector('[name="cp-name"], input[type="text"]');
    var projectEl = modal.body.querySelector('[name="cp-project"], select');
    var noteEl = modal.body.querySelector('[name="cp-note"], textarea');
    var saveBtn = modal.body.querySelector('[data-action="save"], button.lg-pill-active, button:last-child');
    var cancelBtn = modal.body.querySelector('[data-action="cancel"]');
    if (!cancelBtn) {
      // Try first button that isn't the save one.
      var btns = modal.body.querySelectorAll('button');
      for (var b = 0; b < btns.length; b++) if (btns[b] !== saveBtn) { cancelBtn = btns[b]; break; }
    }

    // Populate project dropdown.
    if (projectEl && projectEl.tagName === 'SELECT') {
      projectEl.innerHTML = '<option value="">(select project)</option>';
      _fetchJson('/api/launcher/options').then(function (opts2) {
        if (!opts2 || !Array.isArray(opts2.projects)) return;
        for (var i = 0; i < opts2.projects.length; i++) {
          var pj = opts2.projects[i];
          var pname = (typeof pj === 'string') ? pj : (pj.slug || pj.name);
          if (!pname) continue;
          var opt = document.createElement('option');
          opt.value = pname;
          opt.textContent = pname;
          if (prefilledAgent && (prefilledAgent.project === pname || (prefilledAgent.agent && prefilledAgent.agent.project === pname))) {
            opt.selected = true;
          }
          projectEl.appendChild(opt);
        }
      }).catch(function () {});
    }

    if (cancelBtn) {
      cancelBtn.addEventListener('click', function () { _closeModal(modal.host); });
    }
    if (saveBtn) {
      saveBtn.addEventListener('click', function () {
        var name = (nameEl && nameEl.value || '').trim();
        var project = (projectEl && projectEl.value || '').trim();
        var note = (noteEl && noteEl.value || '').trim();
        if (!name) { _toast('Name required'); return; }
        if (!project) { _toast('Project required'); return; }
        saveBtn.disabled = true;
        var body = {
          name: name,
          project: project,
          note: note,
          agent: prefilledAgent || {},
          context: {}
        };
        _fetchJson('/api/cycle-points', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body)
        }).then(function (resp) {
          _toast('[OK] saved cycle point "' + name + '"');
          _broadcast('cycle-points-updated', { slug: resp && resp.slug });
          _closeModal(modal.host);
          // If a list host is currently mounted, refresh it.
          var hosts = document.querySelectorAll('.rkoj-cp-host');
          for (var i = 0; i < hosts.length; i++) refresh(hosts[i]);
        }).catch(function (e) {
          saveBtn.disabled = false;
          _toast('Save failed: ' + (e && e.message ? e.message : 'error'));
        });
      });
    }

    if (nameEl && typeof nameEl.focus === 'function') {
      setTimeout(function () { try { nameEl.focus(); } catch (e) {} }, 30);
    }
    return modal.host;
  }

  function _openEditModal(cp) {
    var fallback = function () {
      var body = _el('div', { class: 'lg-popover rkoj-modal-body' });
      body.appendChild(_el('h3', { text: 'Edit Cycle Point', style: 'margin:0 0 12px 0;' }));
      var nameInput = _el('input', { class: 'lg-input', type: 'text', name: 'cp-name', style: 'width:100%;margin-bottom:10px;' });
      var noteInput = _el('textarea', { class: 'lg-input', name: 'cp-note', rows: '4', style: 'width:100%;margin-bottom:12px;' });
      var btnRow = _el('div', { style: 'display:flex;gap:8px;justify-content:flex-end;' });
      btnRow.appendChild(_el('button', { class: 'lg-button', type: 'button', text: 'Cancel', 'data-action': 'cancel' }));
      btnRow.appendChild(_el('button', { class: 'lg-button lg-pill-active', type: 'button', text: 'Save', 'data-action': 'save' }));
      body.appendChild(nameInput);
      body.appendChild(noteInput);
      body.appendChild(btnRow);
      return body;
    };
    var modal = _modalFromTemplate('tpl-cycle-edit-modal', fallback);
    var nameEl = modal.body.querySelector('[name="cp-name"], input[type="text"]');
    var noteEl = modal.body.querySelector('[name="cp-note"], textarea');
    var saveBtn = modal.body.querySelector('[data-action="save"]');
    var cancelBtn = modal.body.querySelector('[data-action="cancel"]');
    if (nameEl) nameEl.value = cp.name || '';
    if (noteEl) noteEl.value = cp.note || '';
    if (cancelBtn) cancelBtn.addEventListener('click', function () { _closeModal(modal.host); });
    if (saveBtn) {
      saveBtn.addEventListener('click', function () {
        var body = {
          name: (nameEl && nameEl.value || '').trim() || cp.name,
          note: (noteEl && noteEl.value || '').trim()
        };
        _fetchJson('/api/cycle-points/' + encodeURIComponent(cp.slug), {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body)
        }).then(function () {
          _toast('[OK] updated cycle point');
          _broadcast('cycle-points-updated', { slug: cp.slug });
          _closeModal(modal.host);
          var hosts = document.querySelectorAll('.rkoj-cp-host');
          for (var i = 0; i < hosts.length; i++) refresh(hosts[i]);
        }).catch(function (e) {
          _toast('Update failed: ' + (e && e.message ? e.message : 'error'));
        });
      });
    }
    return modal.host;
  }

  function resume(slug) {
    if (!slug) return Promise.reject(new Error('slug required'));
    return _fetchJson('/api/cycle-points/' + encodeURIComponent(slug) + '/resume', { method: 'POST' })
      .then(function (resp) {
        var pid = (resp && (resp.pid || (resp.result && resp.result.pid))) || '?';
        var name = (resp && (resp.name || (resp.point && resp.point.name))) || slug;
        _toast('[OK] resumed ' + name + ' (PID ' + pid + ')');
        _broadcast('cycle-points-resumed', { slug: slug, pid: pid });
        return resp;
      })
      .catch(function (e) {
        _toast('Resume failed: ' + (e && e.message ? e.message : 'error'));
        throw e;
      });
  }

  function del(slug) {
    if (!slug) return Promise.reject(new Error('slug required'));
    var ok = false;
    try { ok = window.confirm('Delete cycle point "' + slug + '"?'); } catch (e) { ok = true; }
    if (!ok) return Promise.resolve(false);
    return _fetchJson('/api/cycle-points/' + encodeURIComponent(slug), { method: 'DELETE' })
      .then(function () {
        _toast('[OK] deleted ' + slug);
        _broadcast('cycle-points-updated', { slug: slug, deleted: true });
        var hosts = document.querySelectorAll('.rkoj-cp-host');
        for (var i = 0; i < hosts.length; i++) refresh(hosts[i]);
        return true;
      })
      .catch(function (e) {
        _toast('Delete failed: ' + (e && e.message ? e.message : 'error'));
        throw e;
      });
  }

  // React to cross-window broadcasts.
  function _bindBroadcasts() {
    if (window.RkojPopout && typeof window.RkojPopout.onMessage === 'function') {
      window.RkojPopout.onMessage('cycle-points-updated', function () {
        var hosts = document.querySelectorAll('.rkoj-cp-host');
        for (var i = 0; i < hosts.length; i++) refresh(hosts[i]);
      });
    } else {
      // Defer until popout is available.
      setTimeout(_bindBroadcasts, 200);
    }
  }
  _bindBroadcasts();

  window.RkojCyclePoints = {
    refresh: refresh,
    openSaveModal: openSaveModal,
    resume: resume,
    delete: del,
    del: del,
    _openEditModal: _openEditModal
  };
})();
