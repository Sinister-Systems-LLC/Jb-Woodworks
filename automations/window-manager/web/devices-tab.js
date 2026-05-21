// Author: RKOJ-ELENO :: 2026-05-21
// devices-tab.js — Sinister Panel-style fleet console for the Phones pane.
//
// Layout (top → bottom):
//   [ dv-statstrip   ]  4 stat cards: ONLINE / OFFLINE / NEEDS-AUTH / RKA-ARMED
//   [ dv-toolbar     ]  search box + filter chips (All / Online / Stale / Locked)
//   [ dv-body        ]  2-col split:
//                         left  rail  -> per-device card list (selectable)
//                         right pane  -> identity + heartbeat + RKA + action buttons
//   [ dv-logcat-card ]  live `adb logcat` tail (SSE, refreshed ~3s)
//
// Public API: window.SanctumDevicesTab.mount(hostEl) — idempotent.
// Reuses window.fetchJson + window.toast if present; falls back gracefully.

(function () {
    'use strict';

    var mounted = false;
    var hostEl = null;

    var state = {
        devices: [],
        filter: 'all',      // all | online | stale | locked
        search: '',
        selected: null,     // serial string
        details: null,      // payload of /api/devices/details for selected
        logcatEs: null,     // EventSource handle
        pollTimer: null,
    };

    // ---------- micro-helpers ----------
    function $toast(msg, bad) {
        if (window.toast) return window.toast(msg, !!bad);
        console[bad ? 'error' : 'log']('[devices-tab]', msg);
    }
    function $fetchJson(url, opts) {
        if (window.fetchJson) return window.fetchJson(url, opts);
        return fetch(url, opts).then(function (r) { return r.json(); }).catch(function () { return null; });
    }
    function el(tag, attrs, kids) {
        var n = document.createElement(tag);
        if (attrs) for (var k in attrs) {
            if (k === 'class') n.className = attrs[k];
            else if (k === 'style') n.setAttribute('style', attrs[k]);
            else if (k.indexOf('on') === 0) n.addEventListener(k.slice(2), attrs[k]);
            else if (attrs[k] === true) n.setAttribute(k, '');
            else if (attrs[k] !== false && attrs[k] !== null && attrs[k] !== undefined) n.setAttribute(k, attrs[k]);
        }
        (kids || []).forEach(function (c) {
            if (c == null) return;
            n.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
        });
        return n;
    }
    function fmtAgo(iso) {
        if (!iso) return 'never';
        var t = Date.parse(iso); if (!t) return iso;
        var s = Math.max(0, Math.floor((Date.now() - t) / 1000));
        if (s < 60)   return s + 's ago';
        if (s < 3600) return Math.floor(s / 60) + 'm ago';
        if (s < 86400) return Math.floor(s / 3600) + 'h ago';
        return Math.floor(s / 86400) + 'd ago';
    }
    function classify(d) {
        // Categorise a device for filter chips + stat counts.
        var s = (d.state || '').toLowerCase();
        if (s === 'unauthorized') return 'needs_auth';
        if (s === 'device') return 'online';
        if (s === 'offline' || s === '') return 'offline';
        // Anything else (recovery, sideload, bootloader) → "locked" bucket.
        return 'locked';
    }

    // ---------- styles (injected once) ----------
    function injectStylesOnce() {
        if (document.getElementById('dv-tab-styles')) return;
        var css = '' +
            '.dv-root{display:flex;flex-direction:column;gap:12px;height:100%;min-height:0;}' +
            '.dv-statstrip{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;}' +
            '.dv-stat{background:var(--bg-glass-2);border:1px solid var(--border-soft);border-radius:var(--sp-radius-card);padding:12px 14px;display:flex;flex-direction:column;gap:4px;cursor:pointer;transition:border-color 200ms,transform 200ms;}' +
            '.dv-stat:hover{border-color:rgba(160,110,255,0.30);transform:translateY(-1px);} ' +
            '.dv-stat.active{border-color:var(--purple-accent);box-shadow:0 0 0 1px rgba(160,110,255,0.25);}' +
            '.dv-stat-label{font-size:10.5px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:var(--soft);}' +
            '.dv-stat-num{font-size:24px;font-weight:700;color:var(--text);font-feature-settings:"tnum";}' +
            '.dv-stat-sub{font-size:10.5px;color:var(--dim);}' +
            '.dv-stat.online .dv-stat-num{color:#34D399;}' +
            '.dv-stat.offline .dv-stat-num{color:#9CA3AF;}' +
            '.dv-stat.needs_auth .dv-stat-num{color:#FBBF24;}' +
            '.dv-stat.armed .dv-stat-num{color:var(--purple-accent);}' +
            '.dv-toolbar{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}' +
            '.dv-search{flex:1;min-width:140px;}' +
            '.dv-chip{padding:5px 12px;border-radius:999px;background:rgba(255,255,255,0.04);border:1px solid var(--border-soft);font-size:11.5px;font-weight:600;color:var(--soft);cursor:pointer;transition:all 150ms;}' +
            '.dv-chip:hover{color:var(--text);border-color:rgba(160,110,255,0.30);} ' +
            '.dv-chip.active{color:#fff;background:linear-gradient(180deg,var(--purple-accent),var(--purple-deep));border-color:rgba(160,110,255,0.55);}' +
            '.dv-body{display:grid;grid-template-columns:280px 1fr;gap:12px;flex:1;min-height:0;}' +
            '.dv-rail{background:var(--bg-glass-2);border:1px solid var(--border-soft);border-radius:var(--sp-radius-card);overflow-y:auto;padding:8px;display:flex;flex-direction:column;gap:6px;}' +
            '.dv-rail-card{padding:9px 10px;border-radius:10px;border:1px solid var(--border-hair);background:rgba(0,0,0,0.20);cursor:pointer;transition:all 150ms;display:flex;flex-direction:column;gap:3px;}' +
            '.dv-rail-card:hover{border-color:rgba(160,110,255,0.30);background:rgba(160,110,255,0.05);}' +
            '.dv-rail-card.selected{border-color:var(--purple-accent);background:rgba(160,110,255,0.10);}' +
            '.dv-rail-row{display:flex;align-items:center;gap:6px;}' +
            '.dv-rail-dot{width:7px;height:7px;border-radius:50%;background:var(--dim);flex-shrink:0;}' +
            '.dv-rail-dot.online{background:#34D399;box-shadow:0 0 6px rgba(16,185,129,0.5);} ' +
            '.dv-rail-dot.needs_auth{background:#FBBF24;}' +
            '.dv-rail-dot.offline{background:#6E6E84;}' +
            '.dv-rail-dot.locked{background:#F87171;}' +
            '.dv-rail-model{font-weight:600;font-size:12.5px;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}' +
            '.dv-rail-serial{font-family:ui-monospace,Consolas,monospace;font-size:10.5px;color:var(--dim);}' +
            '.dv-rail-state-pill{margin-left:auto;font-size:9.5px;font-weight:700;letter-spacing:0.05em;text-transform:uppercase;padding:1px 6px;border-radius:999px;background:rgba(255,255,255,0.05);color:var(--soft);}' +
            '.dv-rail-transport{font-size:10px;color:var(--soft);}' +
            '.dv-pane{background:var(--bg-glass-2);border:1px solid var(--border-soft);border-radius:var(--sp-radius-card);padding:16px;overflow-y:auto;display:flex;flex-direction:column;gap:14px;}' +
            '.dv-pane-empty{flex:1;display:flex;align-items:center;justify-content:center;color:var(--dim);font-style:italic;}' +
            '.dv-pane-head{display:flex;align-items:center;gap:10px;}' +
            '.dv-pane-title{font-size:15px;font-weight:700;color:var(--text);}' +
            '.dv-pane-actions{display:flex;gap:8px;flex-wrap:wrap;}' +
            '.dv-grid-2{display:grid;grid-template-columns:repeat(2,1fr);gap:8px 14px;}' +
            '.dv-row{display:flex;align-items:baseline;justify-content:space-between;gap:8px;padding:5px 0;border-bottom:1px solid var(--border-hair);font-size:12px;}' +
            '.dv-row:last-child{border-bottom:0;}' +
            '.dv-row-label{color:var(--soft);font-size:10.5px;font-weight:700;letter-spacing:0.05em;text-transform:uppercase;}' +
            '.dv-row-val{color:var(--text);font-family:ui-monospace,Consolas,monospace;font-size:11.5px;text-align:right;word-break:break-all;}' +
            '.dv-section{display:flex;flex-direction:column;gap:6px;}' +
            '.dv-section-head{font-size:10.5px;font-weight:700;letter-spacing:0.10em;text-transform:uppercase;color:var(--purple-accent);}' +
            '.dv-shell-form{display:flex;gap:6px;}' +
            '.dv-shell-form .sp-input{flex:1;font-family:ui-monospace,Consolas,monospace;font-size:11.5px;}' +
            '.dv-shell-out{background:#000;color:#D1D5DB;font-family:ui-monospace,Consolas,monospace;font-size:11px;padding:8px 10px;border-radius:8px;max-height:140px;overflow:auto;white-space:pre-wrap;word-break:break-all;}' +
            '.dv-logcat-card{flex:0 0 auto;background:var(--bg-glass-2);border:1px solid var(--border-soft);border-radius:var(--sp-radius-card);padding:10px 14px;display:flex;flex-direction:column;gap:6px;max-height:200px;}' +
            '.dv-logcat-head{display:flex;align-items:center;gap:8px;}' +
            '.dv-logcat-title{font-size:10.5px;font-weight:700;letter-spacing:0.10em;text-transform:uppercase;color:var(--purple-accent);}' +
            '.dv-logcat-sub{font-size:10.5px;color:var(--dim);margin-left:auto;}' +
            '.dv-logcat-out{flex:1;background:#000;color:#9CA3AF;font-family:ui-monospace,Consolas,monospace;font-size:10.5px;padding:8px 10px;border-radius:8px;overflow:auto;white-space:pre-wrap;}' +
            '.dv-pill{font-size:10px;font-weight:700;letter-spacing:0.05em;text-transform:uppercase;padding:2px 7px;border-radius:999px;background:rgba(255,255,255,0.05);color:var(--soft);} ' +
            '.dv-pill.ok{color:#34D399;background:rgba(16,185,129,0.10);}' +
            '.dv-pill.warn{color:#FBBF24;background:rgba(245,158,11,0.10);}' +
            '.dv-pill.bad{color:#F87171;background:rgba(229,72,77,0.10);}';
        var s = document.createElement('style');
        s.id = 'dv-tab-styles';
        s.textContent = css;
        document.head.appendChild(s);
    }

    // ---------- root layout ----------
    function buildShell() {
        hostEl.innerHTML = '';

        // 4-stat strip
        var stats = el('div', { class: 'dv-statstrip', id: 'dv-statstrip' }, [
            buildStat('online',     'Phones Online',  '0', '--'),
            buildStat('offline',    'Phones Offline', '0', '--'),
            buildStat('needs_auth', 'Needs-Auth',     '0', '--'),
            buildStat('armed',      'RKA Armed',      '0', 'recovery-watchdog'),
        ]);
        hostEl.appendChild(stats);

        // toolbar (search + filter chips + refresh)
        var search = el('input', {
            class: 'sp-input dv-search', type: 'text',
            placeholder: 'search by model / serial / lane…',
            oninput: function (e) { state.search = (e.target.value || '').toLowerCase(); renderRail(); },
        });
        var chips = ['all', 'online', 'stale', 'locked'].map(function (f) {
            return el('button', {
                class: 'dv-chip' + (state.filter === f ? ' active' : ''),
                'data-f': f,
                onclick: function () {
                    state.filter = f;
                    Array.prototype.forEach.call(hostEl.querySelectorAll('.dv-chip'), function (c) {
                        c.classList.toggle('active', c.getAttribute('data-f') === f);
                    });
                    renderRail();
                },
            }, [f.charAt(0).toUpperCase() + f.slice(1)]);
        });
        var refreshBtn = el('button', {
            class: 'sp-btn ghost', onclick: pollDevices,
        }, ['Refresh']);
        var toolbar = el('div', { class: 'dv-toolbar' }, [search].concat(chips).concat([refreshBtn]));
        hostEl.appendChild(toolbar);

        // body (rail + pane)
        var rail = el('div', { class: 'dv-rail', id: 'dv-rail' }, [
            el('div', { class: 'sp-empty' }, ['loading devices…']),
        ]);
        var pane = el('div', { class: 'dv-pane', id: 'dv-pane' }, [
            el('div', { class: 'dv-pane-empty' }, ['select a device on the left']),
        ]);
        var body = el('div', { class: 'dv-body' }, [rail, pane]);
        hostEl.appendChild(body);

        // logcat card
        var logcat = el('div', { class: 'dv-logcat-card', id: 'dv-logcat-card' }, [
            el('div', { class: 'dv-logcat-head' }, [
                el('span', { class: 'dv-logcat-title' }, ['adb logcat (last 50)']),
                el('span', { class: 'dv-logcat-sub', id: 'dv-logcat-sub' }, ['no device selected']),
            ]),
            el('div', { class: 'dv-logcat-out', id: 'dv-logcat-out' }, ['(select a device to stream logcat)']),
        ]);
        hostEl.appendChild(logcat);
    }

    function buildStat(kind, label, num, sub) {
        return el('button', {
            class: 'dv-stat ' + kind,
            'data-stat': kind,
            onclick: function () { state.filter = (kind === 'armed' ? 'all' : (kind === 'online' ? 'online' : (kind === 'needs_auth' ? 'locked' : (kind === 'offline' ? 'stale' : 'all'))));
                Array.prototype.forEach.call(hostEl.querySelectorAll('.dv-chip'), function (c) {
                    c.classList.toggle('active', c.getAttribute('data-f') === state.filter);
                });
                renderRail();
            },
        }, [
            el('div', { class: 'dv-stat-label' }, [label]),
            el('div', { class: 'dv-stat-num', 'data-num': kind }, [num]),
            el('div', { class: 'dv-stat-sub', 'data-sub': kind }, [sub]),
        ]);
    }

    // ---------- data ----------
    async function pollDevices() {
        var r = await $fetchJson('/api/devices');
        state.devices = (r && r.devices) || [];
        renderStats();
        renderRail();
    }

    function renderStats() {
        var by = { online: 0, offline: 0, needs_auth: 0, locked: 0 };
        state.devices.forEach(function (d) { by[classify(d)] = (by[classify(d)] || 0) + 1; });
        setStatNum('online',     by.online,     'devices in `device` state');
        setStatNum('offline',    by.offline,    'cold / disconnected');
        setStatNum('needs_auth', by.needs_auth, 'tap "Allow USB debug"');
        // RKA armed = whether the recovery-watchdog log file exists (set in details poll cache).
        setStatNum('armed', state.rkaArmed ? 'YES' : '--', state.rkaArmedSub || 'no rka log yet');
    }

    function setStatNum(kind, num, sub) {
        var n = hostEl.querySelector('[data-num="' + kind + '"]');
        var s = hostEl.querySelector('[data-sub="' + kind + '"]');
        if (n) n.textContent = String(num);
        if (s && sub != null) s.textContent = sub;
    }

    function filterMatches(d) {
        var cat = classify(d);
        var f = state.filter;
        if (f === 'online' && cat !== 'online') return false;
        if (f === 'stale'  && cat !== 'offline') return false;
        if (f === 'locked' && cat !== 'needs_auth' && cat !== 'locked') return false;
        if (state.search) {
            var hay = ((d.serial || '') + ' ' + (d.model || '') + ' ' + (d.product || '') + ' ' + (d.lane || '')).toLowerCase();
            if (hay.indexOf(state.search) < 0) return false;
        }
        return true;
    }

    function renderRail() {
        var rail = document.getElementById('dv-rail');
        if (!rail) return;
        rail.innerHTML = '';
        var list = state.devices.filter(filterMatches);
        if (!list.length) {
            rail.appendChild(el('div', { class: 'sp-empty' }, [
                state.devices.length ? 'no devices match the filter' : 'no devices attached',
            ]));
            return;
        }
        list.forEach(function (d) {
            var cat = classify(d);
            var card = el('div', {
                class: 'dv-rail-card' + (state.selected === d.serial ? ' selected' : ''),
                'data-serial': d.serial || '',
                onclick: function () { selectDevice(d.serial); },
            }, [
                el('div', { class: 'dv-rail-row' }, [
                    el('span', { class: 'dv-rail-dot ' + cat }, []),
                    el('span', { class: 'dv-rail-model' }, [d.model || d.product || d.serial || '?']),
                    el('span', { class: 'dv-rail-state-pill' }, [cat.replace('_', '-')]),
                ]),
                el('div', { class: 'dv-rail-row' }, [
                    el('code', { class: 'dv-rail-serial' }, [d.serial || '--']),
                    el('span', { class: 'dv-rail-transport' }, ['t' + (d.transport_id != null ? d.transport_id : '?')]),
                ]),
            ]);
            rail.appendChild(card);
        });
    }

    // ---------- right pane ----------
    async function selectDevice(serial) {
        if (!serial) return;
        state.selected = serial;
        // Update selection in rail.
        Array.prototype.forEach.call(hostEl.querySelectorAll('.dv-rail-card'), function (c) {
            c.classList.toggle('selected', c.getAttribute('data-serial') === serial);
        });
        renderPaneLoading(serial);
        try {
            var d = await $fetchJson('/api/devices/details?serial=' + encodeURIComponent(serial));
            state.details = d || null;
            // Cache RKA armed flag for stat strip.
            if (d && Array.isArray(d.rka_log_tail) && d.rka_log_tail.length > 0) {
                state.rkaArmed = true;
                state.rkaArmedSub = d.rka_log_tail[d.rka_log_tail.length - 1].slice(0, 32);
            } else {
                state.rkaArmed = false;
                state.rkaArmedSub = 'no rka log yet';
            }
            renderStats();
            renderPane(d, serial);
        } catch (e) {
            renderPaneError(serial, e && e.message ? e.message : String(e));
        }
        startLogcat(serial);
    }

    function renderPaneLoading(serial) {
        var pane = document.getElementById('dv-pane');
        if (!pane) return;
        pane.innerHTML = '';
        pane.appendChild(el('div', { class: 'dv-pane-empty' }, ['loading details for ' + serial + '…']));
    }
    function renderPaneError(serial, msg) {
        var pane = document.getElementById('dv-pane');
        if (!pane) return;
        pane.innerHTML = '';
        pane.appendChild(el('div', { class: 'dv-pane-empty' }, ['failed to load ' + serial + ': ' + msg]));
    }

    function renderPane(d, serial) {
        var pane = document.getElementById('dv-pane');
        if (!pane) return;
        pane.innerHTML = '';
        d = d || {};

        // Head: title + state pill + action buttons.
        var dev = state.devices.find(function (x) { return x.serial === serial; }) || {};
        var cat = classify(dev);
        var head = el('div', { class: 'dv-pane-head' }, [
            el('span', { class: 'dv-pane-title' }, [d.model || dev.model || serial]),
            el('span', { class: 'dv-pill ' + (cat === 'online' ? 'ok' : cat === 'needs_auth' ? 'warn' : 'bad') }, [cat.replace('_', '-')]),
        ]);
        pane.appendChild(head);

        // Action buttons row.
        var actions = el('div', { class: 'dv-pane-actions' }, [
            el('button', { class: 'sp-btn primary', onclick: function () { openPhoneViewer(serial); } }, ['Open viewer']),
            el('button', { class: 'sp-btn ghost',   onclick: function () { openScrcpy(serial); } }, ['Open scrcpy']),
            el('button', { class: 'sp-btn ghost',   onclick: function () { runShell(serial, 'getprop ro.build.version.release'); } }, ['Quick: getprop']),
            el('button', { class: 'sp-btn ghost',   onclick: function () { runShell(serial, 'pm list packages -3 | head -20'); } }, ['List apps']),
        ]);
        pane.appendChild(actions);

        // Identity.
        var ident = el('div', { class: 'dv-section' }, [
            el('div', { class: 'dv-section-head' }, ['Identity']),
            el('div', { class: 'dv-grid-2' }, [
                identRow('Serial',       d.serial || serial),
                identRow('Model',        d.model || dev.model || '--'),
                identRow('Manufacturer', d.manufacturer || dev.product || '--'),
                identRow('Brand',        d.brand || '--'),
                identRow('Android',      (d.android_version || '?') + ' (SDK ' + (d.sdk || '?') + ')'),
                identRow('Build',        d.build || '--'),
                identRow('Transport',    d.transport || ('t' + (dev.transport_id != null ? dev.transport_id : '?'))),
                identRow('Lane',         dev.lane || dev.device || '--'),
            ]),
        ]);
        pane.appendChild(ident);

        // Heartbeat.
        var hb = d.heartbeat || { exists: false };
        var hbBody;
        if (hb.exists && !hb.error) {
            hbBody = el('div', { class: 'dv-grid-2' }, [
                identRow('Display',    hb.display_name || '--'),
                identRow('Project',    hb.project || '--'),
                identRow('Last seen',  fmtAgo(hb.last_seen) + ' (' + (hb.last_seen || '--') + ')'),
            ]);
        } else if (hb.error) {
            hbBody = el('div', { class: 'sp-empty' }, ['heartbeat read error: ' + hb.error]);
        } else {
            hbBody = el('div', { class: 'sp-empty' }, ['no heartbeat file at _shared-memory/heartbeats/phones/' + serial + '.json']);
        }
        var hbSec = el('div', { class: 'dv-section' }, [
            el('div', { class: 'dv-section-head' }, ['Heartbeat']),
            hbBody,
        ]);
        pane.appendChild(hbSec);

        // RKA posture.
        var rkaSec = el('div', { class: 'dv-section' }, [
            el('div', { class: 'dv-section-head' }, ['RKA posture (recovery-watchdog)']),
            (function () {
                if (Array.isArray(d.rka_log_tail) && d.rka_log_tail.length) {
                    var box = el('div', { class: 'dv-shell-out' }, []);
                    box.textContent = d.rka_log_tail.join('\n');
                    return box;
                }
                return el('div', { class: 'sp-empty' }, ['no RKA log at ' + (d.rka_log_path || 'recovery-watchdog.log')]);
            })(),
        ]);
        pane.appendChild(rkaSec);

        // Kill-switch (placeholder — endpoint not wired yet).
        var ksSec = el('div', { class: 'dv-section' }, [
            el('div', { class: 'dv-section-head' }, ['Kill-switch']),
            el('div', { class: 'dv-row' }, [
                el('span', { class: 'dv-row-label' }, ['Status']),
                el('span', { class: 'dv-pill' }, ['not yet wired']),
            ]),
            el('div', { class: 'sp-empty' }, ['/api/kill-switch/{serial} not implemented — wire RKA daemon supervisor next.']),
        ]);
        pane.appendChild(ksSec);

        // ADB shell one-off.
        var shellInput = el('input', {
            class: 'sp-input', type: 'text',
            placeholder: 'adb shell <cmd>  (e.g. getprop ro.product.model)',
            onkeydown: function (e) {
                if (e.key === 'Enter') { e.preventDefault(); runShell(serial, shellInput.value); }
            },
        });
        var shellRun = el('button', { class: 'sp-btn primary', onclick: function () { runShell(serial, shellInput.value); } }, ['Run']);
        var shellOut = el('div', { class: 'dv-shell-out', id: 'dv-shell-out' }, ['(no output yet)']);
        var shellSec = el('div', { class: 'dv-section' }, [
            el('div', { class: 'dv-section-head' }, ['ADB shell (one-shot, 10s timeout)']),
            el('div', { class: 'dv-shell-form' }, [shellInput, shellRun]),
            shellOut,
        ]);
        pane.appendChild(shellSec);
    }

    function identRow(label, value) {
        return el('div', { class: 'dv-row' }, [
            el('span', { class: 'dv-row-label' }, [label]),
            el('span', { class: 'dv-row-val' }, [String(value == null ? '--' : value)]),
        ]);
    }

    // ---------- actions ----------
    async function openPhoneViewer(serial) {
        var r = await $fetchJson('/api/phone-viewer/launch?serial=' + encodeURIComponent(serial), { method: 'POST' });
        if (r && r.ok) $toast('[OK] phone-viewer launched (pid ' + r.pid + ')');
        else $toast('[FAIL] phone-viewer: ' + ((r && (r.error || r.detail)) || 'unknown'), true);
    }
    async function openScrcpy(serial) {
        var r = await $fetchJson('/api/scrcpy/launch?serial=' + encodeURIComponent(serial), { method: 'POST' });
        if (r && r.ok) $toast('[OK] scrcpy launched (pid ' + r.pid + ')');
        else $toast('[FAIL] scrcpy: ' + ((r && (r.error || r.detail)) || 'install scrcpy first'), true);
    }
    async function runShell(serial, cmd) {
        cmd = (cmd || '').trim();
        if (!cmd) return $toast('enter a shell command first', true);
        var out = document.getElementById('dv-shell-out');
        if (out) out.textContent = '$ ' + cmd + '\n(running…)';
        var r = await $fetchJson('/api/adb/shell?serial=' + encodeURIComponent(serial) + '&cmd=' + encodeURIComponent(cmd), { method: 'POST' });
        if (!out) return;
        if (!r) { out.textContent = '(no response)'; return; }
        var body = '';
        if (r.stdout) body += r.stdout;
        if (r.stderr) body += (body ? '\n' : '') + '[stderr] ' + r.stderr;
        body += '\n[exit ' + (r.returncode != null ? r.returncode : '?') + ']';
        out.textContent = body;
    }

    // ---------- logcat (SSE) ----------
    function startLogcat(serial) {
        stopLogcat();
        var out = document.getElementById('dv-logcat-out');
        var sub = document.getElementById('dv-logcat-sub');
        if (out) out.textContent = '(connecting to /api/adb/logcat?serial=' + serial + ')';
        if (sub) sub.textContent = 'streaming ' + serial;
        try {
            var es = new EventSource('/api/adb/logcat?serial=' + encodeURIComponent(serial));
            state.logcatEs = es;
            es.onmessage = function (ev) {
                if (!out) return;
                // Server collapses newlines to literal "\n" for SSE safety; unescape here.
                var txt = (ev.data || '').replace(/\\n/g, '\n');
                out.textContent = txt;
                out.scrollTop = out.scrollHeight;
            };
            es.onerror = function () {
                if (sub) sub.textContent = 'stream error — reconnecting…';
            };
        } catch (e) {
            if (out) out.textContent = '[SSE not available: ' + e + ']';
        }
    }
    function stopLogcat() {
        if (state.logcatEs) {
            try { state.logcatEs.close(); } catch (_) {}
            state.logcatEs = null;
        }
    }

    // ---------- mount ----------
    function mountDevicesTab(host) {
        if (!host) return;
        hostEl = host;
        injectStylesOnce();
        if (mounted) {
            // Re-poll on every mount call so the right pane stays fresh.
            pollDevices();
            return;
        }
        mounted = true;
        buildShell();
        pollDevices();
        // 10s poll.
        if (state.pollTimer) clearInterval(state.pollTimer);
        state.pollTimer = setInterval(pollDevices, 10000);
    }

    window.SanctumDevicesTab = { mount: mountDevicesTab };
})();
