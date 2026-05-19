// Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
// RKOJ.exe popout system — multi-window tear-off via window.open + BroadcastChannel sync.
// Runs BEFORE app.js. Registers on window.RkojPopout. Lazy access to window.RkojHelpers.

(function () {
  'use strict';

  var CHANNEL_NAME = 'rkoj-state';
  var STORAGE_KEY = 'rkoj.popouts';
  var SOFT_CAP = 8;
  var POPOUT_PARAM = 'popout';
  var STATE_PARAM = 'state';

  var _channel = null;
  try {
    _channel = new BroadcastChannel(CHANNEL_NAME);
  } catch (e) {
    _channel = null;
  }

  var _listeners = {}; // type -> [handler]
  var _openWindows = {}; // id -> WindowProxy
  var _isPopoutMode = false;
  var _currentView = null;
  var _currentState = null;

  function _helpers() {
    return (typeof window !== 'undefined' && window.RkojHelpers) ? window.RkojHelpers : null;
  }

  function _safeToast(msg) {
    var h = _helpers();
    if (h && typeof h.toast === 'function') {
      try { h.toast(msg); return; } catch (e) {}
    }
    try { console.log('[RkojPopout]', msg); } catch (e) {}
  }

  function _parseHash() {
    var hash = (location.hash || '').replace(/^#/, '');
    if (!hash) return null;
    var out = {};
    var parts = hash.split('&');
    for (var i = 0; i < parts.length; i++) {
      var kv = parts[i].split('=');
      if (kv.length === 2) {
        try { out[decodeURIComponent(kv[0])] = decodeURIComponent(kv[1]); }
        catch (e) { out[kv[0]] = kv[1]; }
      }
    }
    return out;
  }

  function _decodeState(b64) {
    if (!b64) return {};
    try {
      var json = atob(b64);
      return JSON.parse(json) || {};
    } catch (e) {
      return {};
    }
  }

  function _encodeState(obj) {
    try {
      return btoa(JSON.stringify(obj || {}));
    } catch (e) {
      return btoa('{}');
    }
  }

  function _genId() {
    return 'po-' + Date.now().toString(36) + '-' + Math.floor(Math.random() * 1e6).toString(36);
  }

  function _readList() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return [];
      var arr = JSON.parse(raw);
      return Array.isArray(arr) ? arr : [];
    } catch (e) {
      return [];
    }
  }

  function _writeList(arr) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(arr || []));
    } catch (e) {}
  }

  function _pruneClosedFromList() {
    // Remove any entries whose tracked WindowProxy is closed.
    var list = _readList();
    var alive = [];
    for (var i = 0; i < list.length; i++) {
      var entry = list[i];
      var w = _openWindows[entry.id];
      if (w && !w.closed) {
        alive.push(entry);
      } else if (!w) {
        // We don't have the handle (different main-window session). Keep it for the operator;
        // they can manually close from the chip. Mark as detached.
        entry.detached = true;
        alive.push(entry);
      }
    }
    _writeList(alive);
    _updatePopoutsBar();
    return alive;
  }

  function _updatePopoutsBar() {
    // Look for a popouts-bar host in the main window. App.js or index.html may render it;
    // we just keep an attribute updated so they can react.
    if (_isPopoutMode) return;
    try {
      var bar = document.querySelector('[data-rkoj-popouts-bar]');
      var list = _readList();
      if (bar) {
        bar.setAttribute('data-count', String(list.length));
        // Fire a DOM event so app.js can re-render the chip dropdown.
        try {
          bar.dispatchEvent(new CustomEvent('rkoj:popouts-updated', { detail: { list: list } }));
        } catch (e) {}
      }
      // Always dispatch a window-level event too (lets any listener react).
      try {
        window.dispatchEvent(new CustomEvent('rkoj:popouts-updated', { detail: { list: list } }));
      } catch (e) {}
    } catch (e) {}
  }

  function _addToList(entry) {
    var list = _readList();
    list.push(entry);
    _writeList(list);
    _updatePopoutsBar();
  }

  function _removeFromList(id) {
    var list = _readList();
    var next = [];
    for (var i = 0; i < list.length; i++) {
      if (list[i].id !== id) next.push(list[i]);
    }
    _writeList(next);
    _updatePopoutsBar();
  }

  function _onChannelMessage(ev) {
    var msg = ev && ev.data;
    if (!msg || typeof msg !== 'object' || !msg.type) return;
    var handlers = _listeners[msg.type] || [];
    for (var i = 0; i < handlers.length; i++) {
      try { handlers[i](msg.payload, msg); } catch (e) {}
    }
    // Wildcard listeners
    var any = _listeners['*'] || [];
    for (var j = 0; j < any.length; j++) {
      try { any[j](msg.payload, msg); } catch (e) {}
    }
  }

  if (_channel) {
    _channel.onmessage = _onChannelMessage;
  } else {
    // Fallback: storage event-based broadcast.
    var STORAGE_BROADCAST_KEY = 'rkoj.broadcast';
    window.addEventListener('storage', function (ev) {
      if (ev.key !== STORAGE_BROADCAST_KEY || !ev.newValue) return;
      try {
        var msg = JSON.parse(ev.newValue);
        _onChannelMessage({ data: msg });
      } catch (e) {}
    });
  }

  // Listen for postMessage from main → popout (close request, focus, refresh).
  window.addEventListener('message', function (ev) {
    var msg = ev && ev.data;
    if (!msg || typeof msg !== 'object') return;
    if (msg.type === 'close' && _isPopoutMode) {
      try { window.close(); } catch (e) {}
    } else if (msg.type === 'focus' && _isPopoutMode) {
      try { window.focus(); } catch (e) {}
    }
  });

  function _hideMainShellInPopout() {
    document.body.classList.add('rkoj-popout');
    // Hide structural chrome by selector — popout-mode css will catch the class as backup.
    var selectors = [
      '[data-rkoj-ribbon]', '.rkoj-ribbon', '#rkoj-ribbon',
      '[data-rkoj-tabs]', '.rkoj-tabs', '#rkoj-tabs',
      '[data-rkoj-devtools]', '.rkoj-devtools-rail', '#rkoj-devtools',
      '[data-rkoj-sidebar]', '.rkoj-sidebar', '#rkoj-sidebar',
      '[data-rkoj-alert-strip]', '.rkoj-alert-strip'
    ];
    for (var i = 0; i < selectors.length; i++) {
      var nodes = document.querySelectorAll(selectors[i]);
      for (var j = 0; j < nodes.length; j++) {
        nodes[j].style.display = 'none';
      }
    }
  }

  function _mountPopoutView(viewId, state) {
    var root = document.body;
    if (!root) return;
    // Try a popout-specific mount host first; fall back to body itself.
    var host = document.getElementById('rkoj-popout-root');
    if (!host) {
      host = document.createElement('div');
      host.id = 'rkoj-popout-root';
      host.className = 'rkoj-popout-root';
      host.setAttribute('data-view', viewId || '');
      root.appendChild(host);
    } else {
      host.innerHTML = '';
      host.setAttribute('data-view', viewId || '');
    }

    // Pull <template id="tpl-<viewId>"> if present.
    var tpl = viewId ? document.getElementById('tpl-' + viewId) : null;
    if (tpl && tpl.content) {
      host.appendChild(tpl.content.cloneNode(true));
    } else {
      var hint = document.createElement('div');
      hint.className = 'lg-card';
      hint.style.padding = '16px';
      hint.style.margin = '24px auto';
      hint.style.maxWidth = '720px';
      hint.textContent = 'Popout view "' + (viewId || '(none)') + '" not found. Waiting for app.js to mount.';
      host.appendChild(hint);
    }

    // Give app.js a chance to wire the cloned content.
    try {
      window.dispatchEvent(new CustomEvent('rkoj:popout-mounted', {
        detail: { viewId: viewId, state: state, host: host }
      }));
    } catch (e) {}
  }

  function _ensurePopoutModeIfHashPresent() {
    var parsed = _parseHash();
    if (!parsed || !parsed[POPOUT_PARAM]) return false;
    _isPopoutMode = true;
    _currentView = parsed[POPOUT_PARAM];
    _currentState = _decodeState(parsed[STATE_PARAM]);
    _hideMainShellInPopout();
    _mountPopoutView(_currentView, _currentState);

    // Notify openers we're alive.
    api.broadcast('popout-ready', { view: _currentView, state: _currentState });

    // When this popout window closes, remove ourselves from the list (best-effort).
    window.addEventListener('unload', function () {
      try {
        var list = _readList();
        var next = [];
        var matched = false;
        for (var i = 0; i < list.length; i++) {
          if (!matched && list[i].view === _currentView) {
            matched = true;
            continue;
          }
          next.push(list[i]);
        }
        if (matched) _writeList(next);
      } catch (e) {}
      try { api.broadcast('popout-closed', { view: _currentView }); } catch (e) {}
    });
    return true;
  }

  // ---- Public API ---------------------------------------------------------

  var api = {
    _channel: _channel,
    _CHANNEL_NAME: CHANNEL_NAME,

    init: function () {
      var inPopout = _ensurePopoutModeIfHashPresent();
      if (!inPopout) {
        _isPopoutMode = false;
        // Main window: prune list (any windows we don't track yet) + update bar.
        _pruneClosedFromList();
        // Periodically prune (every 5s) so dead popouts disappear from chip.
        setInterval(_pruneClosedFromList, 5000);
        // Listen for ready-pings from spawned popouts.
        api.onMessage('popout-ready', function (payload) {
          _updatePopoutsBar();
        });
        api.onMessage('popout-closed', function (payload) {
          _updatePopoutsBar();
        });
      }
      return _isPopoutMode;
    },

    isPopoutMode: function () { return _isPopoutMode; },
    currentView: function () { return _currentView; },
    currentState: function () { return _currentState; },

    spawn: function (viewId, state) {
      if (_isPopoutMode) {
        _safeToast('Already in popout — spawn from main window.');
        return null;
      }
      if (!viewId) {
        _safeToast('Popout: viewId required.');
        return null;
      }
      var list = _readList();
      if (list.length >= SOFT_CAP) {
        _safeToast('Popout cap reached (' + SOFT_CAP + '). Close some first.');
        return null;
      }
      var id = _genId();
      var st = _encodeState(state || {});
      var url = location.origin + location.pathname + '#' + POPOUT_PARAM + '=' +
                encodeURIComponent(viewId) + '&' + STATE_PARAM + '=' + encodeURIComponent(st);
      var name = 'rkoj-popout-' + id;
      var features = 'width=900,height=700,left=80,top=80,resizable=yes,scrollbars=yes';
      var w = null;
      try {
        w = window.open(url, name, features);
      } catch (e) {
        w = null;
      }
      if (!w) {
        _safeToast('Popout blocked — allow popups for RKOJ.');
        return null;
      }
      _openWindows[id] = w;
      _addToList({
        id: id,
        view: viewId,
        opened_at: new Date().toISOString(),
        focused: true,
        url: url,
        name: name
      });
      // When the popout closes itself, eventually prune will catch it; also try
      // a beforeunload hook on the spawned window when accessible (same-origin).
      try {
        w.addEventListener('beforeunload', function () {
          _removeFromList(id);
          delete _openWindows[id];
        });
      } catch (e) { /* cross-doc race; pruner covers it */ }
      return id;
    },

    close: function (id) {
      var w = _openWindows[id];
      if (w && !w.closed) {
        try { w.postMessage({ type: 'close' }, location.origin); } catch (e) {}
        try { w.close(); } catch (e) {}
      }
      _removeFromList(id);
      delete _openWindows[id];
    },

    focus: function (id) {
      var w = _openWindows[id];
      if (w && !w.closed) {
        try { w.postMessage({ type: 'focus' }, location.origin); } catch (e) {}
        try { w.focus(); } catch (e) {}
        return true;
      }
      return false;
    },

    broadcast: function (type, payload) {
      var msg = { type: type, payload: payload, ts: Date.now(), origin: _isPopoutMode ? 'popout' : 'main' };
      if (_channel) {
        try { _channel.postMessage(msg); return true; } catch (e) {}
      }
      // Storage-event fallback.
      try {
        localStorage.setItem('rkoj.broadcast', JSON.stringify(msg));
        // Same-window storage events do not fire; let local listeners hear too.
        _onChannelMessage({ data: msg });
        return true;
      } catch (e) {
        return false;
      }
    },

    onMessage: function (type, handler) {
      if (!type || typeof handler !== 'function') return function () {};
      if (!_listeners[type]) _listeners[type] = [];
      _listeners[type].push(handler);
      // Return an unsubscribe function.
      return function () {
        var arr = _listeners[type] || [];
        var idx = arr.indexOf(handler);
        if (idx >= 0) arr.splice(idx, 1);
      };
    },

    list: function () {
      return _pruneClosedFromList();
    },

    closeAll: function () {
      var list = _readList();
      for (var i = 0; i < list.length; i++) {
        api.close(list[i].id);
      }
    }
  };

  window.RkojPopout = api;
})();
