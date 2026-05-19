// Author: Sinister Sanctum master agent (Claude) :: 2026-05-19 — phone shell logic (Thread 1)
// Vanilla JS — NOT loaded together with app.js. Phone bundle stays small.
// Mirrors the desktop helpers verbatim so behavior stays consistent;
// adds router, pull-to-refresh, 5 views + status pollers.

(function () {
    'use strict';

    // ---------------------------------------------------------------- helpers --
    var $ = function (id) { return document.getElementById(id); };
    var qs = function (sel, root) { return (root || document).querySelector(sel); };
    var qsa = function (sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); };

    var el = function (tag, attrs) {
        var e = document.createElement(tag);
        attrs = attrs || {};
        for (var k in attrs) {
            if (!Object.prototype.hasOwnProperty.call(attrs, k)) continue;
            var v = attrs[k];
            if (k === 'class') e.className = v;
            else if (k === 'onclick') e.addEventListener('click', v);
            else if (k === 'onkeydown') e.addEventListener('keydown', v);
            else if (k.indexOf('data-') === 0) e.setAttribute(k, v);
            else if (v !== undefined && v !== null) e.setAttribute(k, v);
        }
        var children = Array.prototype.slice.call(arguments, 2);
        for (var i = 0; i < children.length; i++) {
            var c = children[i];
            if (c == null) continue;
            e.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
        }
        return e;
    };

    var _toastEl;
    var _toastTimer;
    function toast(msg, isError) {
        if (!_toastEl) _toastEl = $('m-toast');
        if (!_toastEl) return;
        _toastEl.textContent = msg;
        _toastEl.classList.toggle('err', !!isError);
        _toastEl.classList.add('show');
        clearTimeout(_toastTimer);
        _toastTimer = setTimeout(function () { _toastEl.classList.remove('show'); }, 4200);
    }

    function _authHeaders() {
        var tok = null;
        try { tok = localStorage.getItem('sinister_token'); } catch (e) {}
        return tok ? { 'Authorization': 'Bearer ' + tok } : {};
    }

    // fetchJson patched: on 401 redirect back to /m (operator must re-scan QR).
    async function fetchJson(url, opts) {
        opts = opts || {};
        try {
            var hdrs = {};
            var ah = _authHeaders();
            for (var k in ah) hdrs[k] = ah[k];
            if (opts.headers) for (var kk in opts.headers) hdrs[kk] = opts.headers[kk];
            opts.headers = hdrs;
            var r = await fetch(url, opts);
            if (r.status === 401) {
                try { localStorage.removeItem('sinister_token'); } catch (e) {}
                if (window.location.pathname !== '/m') {
                    window.location.href = '/m';
                }
                return { ok: false, error: 'unauthorized' };
            }
            if (!r.ok) throw new Error(r.status + ' ' + r.statusText);
            return await r.json();
        } catch (e) {
            console.warn('fetch failed', url, e);
            return { ok: false, error: e.message };
        }
    }

    function bind(host, name) { return qs('[data-bind="' + name + '"]', host); }

    function fmtTime(d) {
        d = d || new Date();
        var pad = function (n) { return String(n).padStart(2, '0'); };
        return pad(d.getHours()) + ':' + pad(d.getMinutes());
    }

    // ---------------------------------------------------------------- router --
    var VIEWS = ['requests', 'inbox', 'dashboard', 'progress', 'knowledge'];
    var state = {
        view: 'dashboard',
        inboxStep: 'list',
        inboxAgent: null,
        reqFilter: 'pending',
        knLastQuery: '',
        knSelected: null,
    };
    var Views = {};

    function _setNavActive(viewId) {
        qsa('.m-nav-tab').forEach(function (n) {
            n.classList.toggle('active', n.dataset.view === viewId);
        });
    }

    function _setViewTitle(viewId) {
        var t = $('m-view-title');
        if (!t) return;
        t.textContent = (viewId || 'PHONE').toUpperCase();
    }

    function _setMainTemplate(tplId) {
        var main = $('m-main');
        var tpl = $(tplId);
        if (!main || !tpl) return null;
        main.innerHTML = '';
        var frag = tpl.content.cloneNode(true);
        main.appendChild(frag);
        return main;
    }

    function routeTo(viewId, opts) {
        if (VIEWS.indexOf(viewId) === -1) viewId = 'dashboard';
        state.view = viewId;
        var main = $('m-main');
        if (main) main.dataset.view = viewId;
        _setNavActive(viewId);
        _setViewTitle(viewId);

        // Update URL without page reload so deep-links survive a refresh.
        try {
            var newPath = '/m/' + viewId;
            if (window.location.pathname !== newPath) {
                history.pushState({ view: viewId }, '', newPath);
            }
        } catch (e) {}

        var v = Views[viewId];
        if (v && typeof v.mount === 'function') {
            try { v.mount(main, opts || {}); } catch (e) { console.warn('mount failed', viewId, e); }
        }
    }

    // ---------------------------------------------------------------- pull-to-refresh --
    function _wirePTR() {
        var main = $('m-main');
        var hint = $('m-ptr-hint');
        if (!main || !hint) return;
        var startY = 0;
        var pulling = false;
        var triggered = false;
        var THRESH = 64;

        main.addEventListener('touchstart', function (ev) {
            if (main.scrollTop > 2) { pulling = false; return; }
            startY = ev.touches[0].clientY;
            pulling = true;
            triggered = false;
        }, { passive: true });

        main.addEventListener('touchmove', function (ev) {
            if (!pulling) return;
            var dy = ev.touches[0].clientY - startY;
            if (dy > 8) {
                hint.classList.add('show');
                hint.textContent = dy > THRESH ? 'release to refresh' : 'pull to refresh';
                if (dy > THRESH) triggered = true;
            }
        }, { passive: true });

        main.addEventListener('touchend', function () {
            if (pulling && triggered) {
                hint.textContent = 'refreshing...';
                _triggerCurrentRefresh().then(function () {
                    setTimeout(function () { hint.classList.remove('show'); }, 400);
                });
            } else {
                hint.classList.remove('show');
            }
            pulling = false;
            triggered = false;
        });
    }

    function _triggerCurrentRefresh() {
        var v = Views[state.view];
        if (v && typeof v.refresh === 'function') {
            var main = $('m-main');
            try { return Promise.resolve(v.refresh(main)); } catch (e) { return Promise.resolve(); }
        }
        return Promise.resolve();
    }

    // ---------------------------------------------------------------- status pollers --
    async function pollHealth() {
        var h = await fetchJson('/api/health');
        var badge = $('m-health');
        if (!badge) return;
        if (h && h.ok) {
            badge.textContent = 'v' + (h.version || '?');
            badge.classList.remove('bad');
            badge.classList.add('online');
        } else {
            badge.textContent = 'OFFLINE';
            badge.classList.remove('online');
            badge.classList.add('bad');
        }
    }

    async function pollSessions() {
        var r = await fetchJson('/api/sessions');
        var pill = $('m-online');
        if (!pill) return;
        var sessions = (r && (r.sessions || [])) || [];
        var online = sessions.filter(function (s) { return s.online; }).length;
        pill.textContent = online + ' online';
        pill.classList.toggle('online', online > 0);
        pill.classList.toggle('offline', online === 0);
        // expose to dashboard
        if (state.view === 'dashboard') {
            var ao = bind($('m-main'), 'agents-online');
            if (ao) ao.textContent = String(online) + ' / ' + sessions.length;
        }
    }

    async function pollRequestsBadge() {
        var r = await fetchJson('/api/operator-requests?status=pending');
        var nav = qs('.m-nav-tab[data-view="requests"]');
        var headerBadge = qs('#m-online'); // not used for req — using nav badge
        if (!nav) return;
        var reqs = (r && r.requests) || [];
        var badge = nav.querySelector('.m-nav-badge');
        if (reqs.length > 0) {
            nav.classList.add('has-badge');
            if (badge) badge.textContent = String(reqs.length);
            nav.style.position = 'relative';
        } else {
            nav.classList.remove('has-badge');
        }
    }

    // ============================================================== REQUESTS ==
    async function _refreshRequests(host) {
        if (!host) return;
        var list = bind(host, 'req-list');
        var countEl = bind(host, 'req-count');
        if (!list) return;
        var r = await fetchJson('/api/operator-requests?status=' + encodeURIComponent(state.reqFilter));
        list.innerHTML = '';
        if (!r.ok) {
            list.appendChild(el('div', { class: 'empty-note' }, '[FAIL] ' + (r.error || 'fetch failed')));
            return;
        }
        var reqs = r.requests || [];
        if (countEl) countEl.textContent = reqs.length + ' ' + state.reqFilter;
        if (!reqs.length) {
            list.appendChild(el('div', { class: 'empty-note' }, '(no ' + state.reqFilter + ' requests)'));
            return;
        }
        reqs.forEach(function (req) {
            var urg = req.urgency || 'normal';
            var stat = req.status || 'pending';
            var card = el('div', { class: 'req-card urg-' + urg + ' stat-' + stat });
            card.appendChild(el('div', { class: 'req-head' },
                el('span', { class: 'req-agent' }, req.agent || '?'),
                el('span', { class: 'req-urgency urg-' + urg }, urg.toUpperCase()),
                el('span', { class: 'req-ts' }, (req.ts || '').slice(0, 16))
            ));
            card.appendChild(el('div', { class: 'req-title' }, req.title || '(no title)'));
            if (req.why) card.appendChild(el('div', { class: 'req-why' }, req.why));
            if (req.operator_reply) card.appendChild(el('div', { class: 'req-reply' }, '→ ' + req.operator_reply));
            if (stat === 'pending') {
                var replyInput = el('input', { class: 'lg-input req-reply-input', type: 'text', placeholder: 'optional reply...' });
                var actions = el('div', { class: 'req-actions' });
                var decide = function (verdict) {
                    return async function () {
                        var body = JSON.stringify({ reply: replyInput.value || '' });
                        var rr = await fetchJson('/api/operator-requests/' + req.id + '/' + verdict, {
                            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: body
                        });
                        if (rr.ok) {
                            toast('[OK] ' + verdict + ' — agent notified');
                            _refreshRequests(host);
                            pollRequestsBadge();
                        } else {
                            toast('[FAIL] ' + (rr.error || rr.detail || 'decision failed'), true);
                        }
                    };
                };
                actions.appendChild(el('button', { class: 'lg-button req-approve', onclick: decide('approve') }, 'APPROVE'));
                actions.appendChild(el('button', { class: 'lg-button req-reply', onclick: decide('reply') }, 'REPLY'));
                actions.appendChild(el('button', { class: 'lg-button req-deny', onclick: decide('deny') }, 'DENY'));
                card.appendChild(replyInput);
                card.appendChild(actions);
            }
            list.appendChild(card);
        });
    }

    Views.requests = {
        mount: function () {
            var host = _setMainTemplate('m-tpl-requests');
            if (!host) return;
            qsa('.req-tab', host).forEach(function (t) {
                t.addEventListener('click', function () {
                    qsa('.req-tab', host).forEach(function (x) { x.classList.remove('active'); });
                    t.classList.add('active');
                    state.reqFilter = t.dataset.reqFilter || 'pending';
                    _refreshRequests(host);
                });
                if (t.dataset.reqFilter === state.reqFilter) t.classList.add('active');
                else t.classList.remove('active');
            });
            _refreshRequests(host);
        },
        refresh: function (host) { return _refreshRequests(host || $('m-main')); }
    };

    // ============================================================== INBOX ==
    async function _renderInboxList(host) {
        var list = bind(host, 'inbox-list');
        var countEl = bind(host, 'inbox-count');
        if (!list) return;
        var r = await fetchJson('/api/sessions');
        var sessions = (r && (r.sessions || [])).slice();
        sessions.sort(function (a, b) { return (b.online ? 1 : 0) - (a.online ? 1 : 0); });
        if (countEl) countEl.textContent = sessions.length + ' agents';
        list.innerHTML = '';
        if (!sessions.length) {
            list.appendChild(el('div', { class: 'empty-note' }, 'no agents registered'));
            return;
        }
        sessions.forEach(function (s) {
            var row = el('div', {
                class: 'inbox-agent-row',
                onclick: function () {
                    state.inboxAgent = s.agent;
                    state.inboxStep = 'stream';
                    _mountInboxStream();
                }
            });
            row.appendChild(el('span', { class: 'dot ' + (s.online ? 'on' : 'off') }));
            row.appendChild(el('span', { class: 'agent' }, s.agent));
            row.appendChild(el('span', { class: 'ts' }, s.last_seen_human || 'never'));
            list.appendChild(row);
        });
    }

    async function _renderInboxStream(host) {
        if (!state.inboxAgent) return;
        bind(host, 'stream-title').textContent = state.inboxAgent;
        var pane = bind(host, 'stream-msgs');
        var r = await fetchJson('/api/inbox/' + encodeURIComponent(state.inboxAgent) + '?limit=50');
        if (!pane) return;
        pane.innerHTML = '';
        var msgs = (r && (r.messages || [])) || [];
        if (!msgs.length) {
            pane.appendChild(el('div', { class: 'empty-note' }, '(no messages)'));
            return;
        }
        msgs.forEach(function (m) {
            pane.appendChild(el('div', { class: 'inbox-msg' },
                el('div', { class: 'inbox-msg-head' },
                    el('span', { class: 'from' }, m.from || '?'),
                    el('span', { class: 'ts' }, (m.ts || '').slice(11, 16))
                ),
                el('div', { class: 'inbox-msg-body' }, m.message || '')
            ));
        });
        pane.scrollTop = pane.scrollHeight;
    }

    function _mountInboxList() {
        var host = _setMainTemplate('m-tpl-inbox-list');
        if (!host) return;
        _renderInboxList(host);
    }

    function _mountInboxStream() {
        var host = _setMainTemplate('m-tpl-inbox-stream');
        if (!host) return;
        var back = bind(host, 'inbox-back');
        if (back) back.addEventListener('click', function () {
            state.inboxStep = 'list';
            state.inboxAgent = null;
            _mountInboxList();
        });
        var sendBtn = bind(host, 'stream-send');
        var sendInput = bind(host, 'stream-input');
        var doSend = async function () {
            var body = (sendInput.value || '').trim();
            if (!body || !state.inboxAgent) return;
            sendBtn.disabled = true;
            var rr = await fetchJson('/api/inbox/send', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ to: state.inboxAgent, body: body, sender: 'mobile' })
            });
            sendBtn.disabled = false;
            if (rr.ok) {
                sendInput.value = '';
                toast('[OK] sent to ' + state.inboxAgent);
                _renderInboxStream(host);
            } else {
                toast('[FAIL] ' + (rr.error || rr.detail || 'send failed'), true);
            }
        };
        if (sendBtn) sendBtn.addEventListener('click', doSend);
        if (sendInput) sendInput.addEventListener('keydown', function (ev) {
            if (ev.key === 'Enter') doSend();
        });
        _renderInboxStream(host);
    }

    Views.inbox = {
        mount: function () {
            if (state.inboxStep === 'stream' && state.inboxAgent) _mountInboxStream();
            else { state.inboxStep = 'list'; _mountInboxList(); }
        },
        refresh: function () {
            var host = $('m-main');
            if (!host) return;
            if (state.inboxStep === 'stream') _renderInboxStream(host);
            else _renderInboxList(host);
        }
    };

    // ============================================================== DASHBOARD ==
    Views.dashboard = {
        mount: async function () {
            var host = _setMainTemplate('m-tpl-dashboard');
            if (!host) return;
            await Views.dashboard.refresh(host);
        },
        refresh: async function (host) {
            host = host || $('m-main');
            if (!host) return;
            var t = await fetchJson('/api/trophy');
            var s = await fetchJson('/api/sessions');
            var set = function (n, v) { var b = bind(host, n); if (b) b.textContent = (v === null || v === undefined || v === '') ? '-' : v; };
            if (t && t.ok !== false) {
                set('t-accts', t.accounts); set('t-videos', t.videos); set('t-active', t.active);
                set('t-pushes', t.pushes); set('t-banned', t.banned); set('t-devices', t.devices);
                var status = bind(host, 'trophy-status');
                if (status) status.textContent = t.panel_online ? 'panel ONLINE' : 'panel offline';
            }
            var sessions = (s && (s.sessions || [])) || [];
            var online = sessions.filter(function (x) { return x.online; }).length;
            set('agents-online', online + ' / ' + sessions.length);
            set('last-update', fmtTime());
        }
    };

    // ============================================================== PROGRESS ==
    Views.progress = {
        mount: async function () {
            var host = _setMainTemplate('m-tpl-progress');
            if (!host) return;
            await Views.progress.refresh(host);
        },
        refresh: async function (host) {
            host = host || $('m-main');
            if (!host) return;
            var list = bind(host, 'prog-list');
            var countEl = bind(host, 'prog-count');
            if (!list) return;
            var r = await fetchJson('/api/progress?limit=50');
            list.innerHTML = '';
            if (!r.ok) {
                list.appendChild(el('div', { class: 'empty-note' }, '[FAIL] ' + (r.error || 'fetch failed')));
                return;
            }
            var entries = r.entries || [];
            if (countEl) countEl.textContent = entries.length + (entries.length === 1 ? ' entry' : ' entries');
            if (!entries.length) {
                list.appendChild(el('div', { class: 'empty-note' }, 'no progress logged yet'));
                return;
            }
            entries.forEach(function (e) {
                var card = el('div', { class: 'progress-card lg-card' });
                card.appendChild(el('div', { class: 'head' },
                    el('span', { class: 'agent' }, e.agent || '?'),
                    el('span', { class: 'ts' }, e.ts || '')
                ));
                var body = el('div', null,
                    el('span', { class: 'status status-' + (e.status || 'note').toLowerCase() }, e.status || 'note'),
                    el('span', { class: 'title' }, e.title || '')
                );
                card.appendChild(body);
                if (e.body) card.appendChild(el('div', { class: 'body' }, e.body));
                list.appendChild(card);
            });
        }
    };

    // ============================================================== KNOWLEDGE (read-only on phone) ==
    async function _knSearch(host, query) {
        state.knLastQuery = query;
        var list = bind(host, 'kn-list');
        var countEl = bind(host, 'kn-count');
        var reader = bind(host, 'kn-reader');
        if (reader) reader.classList.add('hidden');
        if (!list) return;
        var url = '/api/knowledge' + (query ? '?search=' + encodeURIComponent(query) : '');
        var r = await fetchJson(url);
        list.innerHTML = '';
        if (!r.ok) {
            list.appendChild(el('div', { class: 'empty-note' }, '[FAIL] ' + (r.error || 'fetch failed')));
            return;
        }
        var items = r.items || r.knowledge || [];
        if (countEl) countEl.textContent = String(items.length);
        if (!items.length) {
            list.appendChild(el('div', { class: 'empty-note' }, query ? '(no matches)' : '(empty)'));
            return;
        }
        items.forEach(function (it) {
            var slug = it.slug || it.name || '';
            var row = el('div', {
                class: 'kn-item' + (state.knSelected === slug ? ' active' : ''),
                'data-slug': slug,
                onclick: function () {
                    state.knSelected = slug;
                    qsa('.kn-item', list).forEach(function (n) {
                        n.classList.toggle('active', n.dataset.slug === slug);
                    });
                    _knOpen(host, slug);
                }
            });
            row.appendChild(el('div', { class: 'kn-item-title' }, it.title || slug));
            if (it.summary) row.appendChild(el('div', { class: 'kn-item-sub' },
                it.summary.length > 120 ? it.summary.slice(0, 120) + '...' : it.summary));
            list.appendChild(row);
        });
    }

    async function _knOpen(host, slug) {
        var reader = bind(host, 'kn-reader');
        if (!reader) return;
        reader.classList.remove('hidden');
        reader.textContent = 'loading...';
        var r = await fetchJson('/api/knowledge/' + encodeURIComponent(slug));
        if (!r.ok) {
            reader.textContent = '[FAIL] ' + (r.error || r.detail || 'load failed');
            return;
        }
        reader.textContent = r.markdown || r.content || r.body || '(empty)';
        try { reader.scrollIntoView({ behavior: 'smooth', block: 'start' }); } catch (e) {}
    }

    Views.knowledge = {
        mount: function () {
            var host = _setMainTemplate('m-tpl-knowledge');
            if (!host) return;
            var btn = bind(host, 'kn-search-btn');
            var inp = bind(host, 'kn-search');
            var go = function () { _knSearch(host, (inp.value || '').trim()); };
            if (btn) btn.addEventListener('click', go);
            if (inp) {
                inp.value = state.knLastQuery || '';
                inp.addEventListener('keydown', function (ev) { if (ev.key === 'Enter') go(); });
            }
            // initial empty list; user must search
            if (state.knLastQuery) go();
        },
        refresh: function () {
            var host = $('m-main');
            if (host && state.knLastQuery) _knSearch(host, state.knLastQuery);
        }
    };

    // ---------------------------------------------------------------- bootstrap --
    function _wireNav() {
        qsa('.m-nav-tab').forEach(function (tab) {
            tab.addEventListener('click', function () {
                var v = tab.dataset.view;
                if (v) routeTo(v);
            });
        });
        window.addEventListener('popstate', function (ev) {
            var path = (window.location.pathname || '/m').replace(/\/+$/, '');
            var parts = path.split('/').filter(Boolean);
            var v = (parts[1] || 'dashboard').toLowerCase();
            if (VIEWS.indexOf(v) === -1) v = 'dashboard';
            // mount without pushState
            state.view = v;
            var main = $('m-main');
            if (main) main.dataset.view = v;
            _setNavActive(v);
            _setViewTitle(v);
            var view = Views[v];
            if (view && view.mount) view.mount(main);
        });
    }

    function bootstrap() {
        _wireNav();
        _wirePTR();
        var initial = window.__SANCTUM_INITIAL_VIEW || 'dashboard';
        if (VIEWS.indexOf(initial) === -1) initial = 'dashboard';
        // First-paint route without an extra pushState; just replace.
        try { history.replaceState({ view: initial }, '', '/m/' + initial); } catch (e) {}
        routeTo(initial);

        pollHealth();
        pollSessions();
        pollRequestsBadge();

        setInterval(pollHealth, 20000);
        setInterval(pollSessions, 20000);
        setInterval(pollRequestsBadge, 20000);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', bootstrap);
    } else {
        bootstrap();
    }
})();
