// Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
// fleet-state.js — single EventSource consolidating spawned-windows + sessions
// + heartbeats + inbox tails for the RKOJ workbench. Subscribers register
// callbacks; the module fans the latest snapshot out and survives reconnects.
//
// Why this exists:
//   The HR-B audit (2026-05-19) flagged that three views of "the agent list"
//   (Spawned-Windows control bar, Sessions strip, Inbox view) all polled their
//   own endpoint on their own setInterval and rendered the same fleet three
//   ways. This module collapses them into one shared snapshot streamed from
//   /api/fleet-stream on a 5-second cadence, with automatic reconnect.
//
// Public surface (window.FleetState):
//   subscribe(callback) -> unsubscribe fn
//   getSnapshot()       -> current cached snapshot (or null)
//   connect()           -> idempotent; spins up the EventSource if needed
//   disconnect()        -> closes the EventSource + resets state
//   onStatus(callback)  -> fires (status) where status is one of:
//                          'connecting' | 'open' | 'stale' | 'closed' | 'error'

(function () {
    if (window.FleetState && window.FleetState.__sinister_marker === '2026-05-19') {
        return; // already loaded
    }

    var STREAM_URL = '/api/fleet-stream';
    var STALE_MS = 30000;     // mark snapshot stale if no event in 30s
    var BACKOFF_MIN_MS = 1000;
    var BACKOFF_MAX_MS = 30000;

    var _es = null;
    var _snapshot = null;
    var _subs = new Set();
    var _statusSubs = new Set();
    var _backoffMs = BACKOFF_MIN_MS;
    var _reconnectTimer = null;
    var _staleTimer = null;
    var _status = 'closed';
    var _lastEventAt = 0;

    function _getToken() {
        try { return localStorage.getItem('sinister_token') || ''; }
        catch (e) { return ''; }
    }

    function _setStatus(next) {
        if (_status === next) return;
        _status = next;
        for (var cb of _statusSubs) {
            try { cb(next); } catch (e) { /* ignore subscriber errors */ }
        }
    }

    function _emit(snap) {
        _snapshot = snap;
        for (var cb of _subs) {
            try { cb(snap); } catch (e) {
                try { console.warn('[FleetState] subscriber threw', e); } catch (_) {}
            }
        }
    }

    function _markStale() {
        if (!_snapshot) return;
        if (_snapshot.stale) return;
        // Shallow clone + flag — preserve the last good data so renderers can
        // still draw something, just with a "stale" indicator.
        _snapshot = Object.assign({}, _snapshot, { stale: true });
        _emit(_snapshot);
        _setStatus('stale');
    }

    function _resetStaleTimer() {
        if (_staleTimer) clearTimeout(_staleTimer);
        _staleTimer = setTimeout(function () {
            _markStale();
            // Force a reconnect — the channel probably died.
            try { if (_es) _es.close(); } catch (e) {}
            _es = null;
            _scheduleReconnect();
        }, STALE_MS);
    }

    function _scheduleReconnect() {
        if (_reconnectTimer) return;
        _setStatus('connecting');
        _reconnectTimer = setTimeout(function () {
            _reconnectTimer = null;
            _open();
        }, _backoffMs);
        _backoffMs = Math.min(BACKOFF_MAX_MS, _backoffMs * 2);
    }

    function _open() {
        if (_es) return;
        var tok = _getToken();
        var url = STREAM_URL + (tok ? ('?t=' + encodeURIComponent(tok)) : '');
        try {
            _es = new EventSource(url);
        } catch (e) {
            try { console.warn('[FleetState] EventSource construct failed', e); } catch (_) {}
            _setStatus('error');
            _scheduleReconnect();
            return;
        }
        _setStatus('connecting');

        _es.addEventListener('open', function () {
            _setStatus('open');
            _backoffMs = BACKOFF_MIN_MS;
            _lastEventAt = Date.now();
            _resetStaleTimer();
        });

        _es.addEventListener('fleet-update', function (ev) {
            _lastEventAt = Date.now();
            _resetStaleTimer();
            var payload = null;
            try { payload = JSON.parse(ev.data); }
            catch (e) {
                try { console.warn('[FleetState] bad JSON in fleet-update', e); } catch (_) {}
                return;
            }
            // Tag with client-side received timestamp so renderers can show
            // "X seconds ago" without doing the math themselves.
            payload._received_at = _lastEventAt;
            payload.stale = false;
            _setStatus('open');
            _emit(payload);
        });

        _es.addEventListener('error', function () {
            // EventSource will auto-retry but we control the backoff ourselves
            // for finer-grained UI feedback.
            _setStatus('error');
            try { _es && _es.close(); } catch (e) {}
            _es = null;
            _scheduleReconnect();
        });
    }

    window.FleetState = {
        __sinister_marker: '2026-05-19',

        subscribe: function (callback) {
            if (typeof callback !== 'function') return function () {};
            _subs.add(callback);
            // Fire immediately with cached snapshot if we already have one.
            if (_snapshot) {
                try { callback(_snapshot); } catch (e) { /* ignore */ }
            }
            return function unsubscribe() { _subs.delete(callback); };
        },

        onStatus: function (callback) {
            if (typeof callback !== 'function') return function () {};
            _statusSubs.add(callback);
            try { callback(_status); } catch (e) { /* ignore */ }
            return function unsubscribe() { _statusSubs.delete(callback); };
        },

        getSnapshot: function () { return _snapshot; },

        connect: function () { _open(); },

        disconnect: function () {
            if (_reconnectTimer) { clearTimeout(_reconnectTimer); _reconnectTimer = null; }
            if (_staleTimer) { clearTimeout(_staleTimer); _staleTimer = null; }
            if (_es) { try { _es.close(); } catch (e) {} }
            _es = null;
            _backoffMs = BACKOFF_MIN_MS;
            _setStatus('closed');
        },
    };

    // Auto-connect on script load — the EventSource is shared by every
    // subscriber so this is cheap. Wrap in DOM ready to make sure the token
    // is in localStorage by the time we kick off.
    function _autoStart() {
        try { _open(); } catch (e) {
            try { console.warn('[FleetState] auto-start failed', e); } catch (_) {}
        }
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', _autoStart, { once: true });
    } else {
        _autoStart();
    }
})();
