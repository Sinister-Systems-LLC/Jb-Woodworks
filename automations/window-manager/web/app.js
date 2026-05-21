// Author: RKOJ-ELENO :: 2026-05-21
// Sinister Sanctum :: Workstation frontend — Panel-style rewrite.
//
// Owns the new Panel-style shell: sidebar nav + chip-tab header + KPI strip
// + project sub-tab strip + niri-style stacked agent consoles + device grid
// + workstation cards. Preserves the API contract (server.py endpoints) and
// the window.RkojHelpers global that popout.js / palette.js / cycle-points.js
// / scheduler.js depend on.
//
// References (study-only, not copied):
//   projects/sinister-panel/source/Andrew Panel/Sinister Panel/panel/dashboard/
//
// Sanctum purple is the binding accent. ASCII glyphs only (fonts may not
// have emoji coverage). pywebview is the OS chrome — body has no titlebar.

(function () {
    'use strict';

    // ============================================================ HELPERS ==
    const $   = (id) => document.getElementById(id);
    const qs  = (sel, root) => (root || document).querySelector(sel);
    const qsa = (sel, root) => Array.from((root || document).querySelectorAll(sel));

    function el(tag, attrs, ...children) {
        const e = document.createElement(tag);
        if (attrs) {
            for (const [k, v] of Object.entries(attrs)) {
                if (k === 'class') e.className = v;
                else if (k === 'onclick') e.addEventListener('click', v);
                else if (k === 'onkeydown') e.addEventListener('keydown', v);
                else if (k.startsWith('data-')) e.setAttribute(k, v);
                else if (v !== undefined && v !== null) e.setAttribute(k, v);
            }
        }
        for (const c of children) {
            if (c == null) continue;
            e.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
        }
        return e;
    }

    function toast(msg, isError) {
        const t = $('toast');
        if (!t) { try { console.log('[toast]', msg); } catch (_) {} return; }
        t.textContent = String(msg);
        t.classList.toggle('err', !!isError);
        t.classList.add('show');
        clearTimeout(toast._t);
        toast._t = setTimeout(() => t.classList.remove('show'), 4000);
    }

    function authHeaders() {
        let tok = null;
        try { tok = localStorage.getItem('sinister_token'); } catch (_) {}
        return tok ? { 'Authorization': 'Bearer ' + tok } : {};
    }

    async function fetchJson(url, opts) {
        opts = opts || {};
        try {
            opts.headers = Object.assign({}, authHeaders(), opts.headers || {});
            const r = await fetch(url, opts);
            if (!r.ok) throw new Error(r.status + ' ' + r.statusText);
            return await r.json();
        } catch (e) {
            try { console.warn('fetch failed', url, e); } catch (_) {}
            return { ok: false, error: e.message };
        }
    }

    function lsGet(k, d) { try { const v = localStorage.getItem(k); return v === null ? d : v; } catch (_) { return d; } }
    function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (_) {} }

    function bind(host, name) { return qs('[data-bind="' + name + '"]', host); }

    // ============================================================ STATE ==
    const TABS = ['agents', 'phones', 'workstation'];
    const TAB_TITLES = { agents: 'AGENTS', phones: 'PHONES', workstation: 'WORKSTATION' };
    const LS_ACTIVE_TAB = 'rkoj.skel.tab';
    const LS_PROJ_FILTER = 'sp.proj.filter';
    const REFRESH_MS = 30000;
    const DEVICE_REFRESH_MS = 15000;
    const KPI_REFRESH_MS = 15000;

    // Legacy aliases — callers (palette, popouts) may still use old slugs.
    const LEGACY_TAB_ALIAS = {
        adb: 'phones', devices: 'phones', fleet: 'phones',
        vault: 'workstation', dashboard: 'workstation',
    };

    const state = {
        activeTab: lsGet(LS_ACTIVE_TAB, 'agents'),
        projectFilter: lsGet(LS_PROJ_FILTER, 'all'),
        sessions: [],
        devices: [],
        projects: [],
        agentInputs: {}, // serial -> draft
    };

    // ============================================================ SIDEBAR NAV ==
    // Mirrors Panel's 4-section sidebar (Workspace / Operations / AI / System).
    // Items are workstation-relevant — Phones is in Operations, Agents in Workspace.
    const NAV_SECTIONS = [
        { label: 'Workspace', items: [
            { id: 'overview',  label: 'Overview',  glyph: '□', tab: 'workstation' },
            { id: 'agents',    label: 'Agents',    glyph: '⚙', tab: 'agents' },
            { id: 'progress',  label: 'Progress',  glyph: '▲', tab: 'workstation' },
        ]},
        { label: 'Operations', items: [
            { id: 'phones',    label: 'Devices',   glyph: '☎', tab: 'phones' },
            { id: 'inbox',     label: 'Inbox',     glyph: '✉', tab: 'workstation' },
            { id: 'requests',  label: 'Requests',  glyph: '!',      tab: 'workstation' },
            { id: 'vault',     label: 'Vault',     glyph: 'V',      tab: 'workstation' },
        ]},
        { label: 'AI', items: [
            { id: 'codex',     label: 'Codex',     glyph: '✨', tab: 'workstation' },
            { id: 'knowledge', label: 'Knowledge', glyph: '☰', tab: 'workstation' },
        ]},
        { label: 'System', items: [
            { id: 'scheduler',    label: 'Scheduler',    glyph: '⏰', tab: 'workstation' },
            { id: 'cycle-points', label: 'Cycle points', glyph: '⦿', tab: 'workstation' },
            { id: 'settings',     label: 'Settings',     glyph: '⚙', tab: 'workstation' },
        ]},
    ];

    function renderSidebarNav() {
        const root = $('sp-nav');
        if (!root) return;
        root.innerHTML = '';
        NAV_SECTIONS.forEach((sec, idx) => {
            const section = el('div', { class: 'sp-nav-section' });
            section.appendChild(el('div', { class: 'sp-nav-section-label' }, sec.label));
            sec.items.forEach((it) => {
                const a = el('button', {
                    class: 'sp-nav-item' + (state.activeTab === it.tab && idx === 0 && it.tab === 'agents' ? ' active' : ''),
                    'data-nav': it.id, 'data-tab': it.tab,
                    title: it.label,
                    onclick: () => setActiveTab(it.tab),
                },
                    el('span', { class: 'sp-nav-glyph' }, it.glyph),
                    el('span', { class: 'sp-nav-label' }, it.label),
                );
                section.appendChild(a);
            });
            root.appendChild(section);
        });
        updateNavActive();
    }

    function updateNavActive() {
        qsa('.sp-nav-item').forEach(n => {
            const on = n.dataset.tab === state.activeTab;
            n.classList.toggle('active', on);
        });
    }

    // ============================================================ TAB SWITCH ==
    function setActiveTab(tabId) {
        if (LEGACY_TAB_ALIAS[tabId]) tabId = LEGACY_TAB_ALIAS[tabId];
        if (!TABS.includes(tabId)) tabId = 'agents';
        state.activeTab = tabId;
        lsSet(LS_ACTIVE_TAB, tabId);
        document.body.setAttribute('data-active-tab', tabId);
        const title = $('sp-title');
        if (title) title.textContent = TAB_TITLES[tabId] || 'WORKSTATION';
        qsa('.sp-chip').forEach(c => {
            const on = c.dataset.tab === tabId;
            c.classList.toggle('active', on);
            c.setAttribute('aria-selected', on ? 'true' : 'false');
        });
        qsa('.sp-pane').forEach(p => {
            const on = p.id === 'pane-' + tabId;
            p.hidden = !on;
            p.classList.toggle('active', on);
        });
        updateNavActive();
        // Lazy-load the active pane's data.
        if (tabId === 'agents') {
            // jcode-form xterm.js stack (RKOJ-ELENO 2026-05-21) — owns #agents-grid.
            // Lazy + idempotent; safe to call every tab switch.
            try {
                if (window.SanctumAgentsTab && window.SanctumAgentsTab.mount) {
                    const host = document.getElementById('agents-grid');
                    if (host) window.SanctumAgentsTab.mount(host);
                }
            } catch (e) { console.error('agents-tab mount failed', e); }
            refreshAgents();
        }
        else if (tabId === 'phones') {
            // devices-tab.js (RKOJ-ELENO 2026-05-21) — Panel-style fleet console.
            // Lazy + idempotent; safe to call every tab switch. Falls back to the
            // legacy refreshDevices() path if the module didn't load.
            try {
                if (window.SanctumDevicesTab && window.SanctumDevicesTab.mount) {
                    const host = document.getElementById('devices-grid');
                    if (host) window.SanctumDevicesTab.mount(host);
                } else {
                    refreshDevices();
                }
            } catch (e) { console.error('devices-tab mount failed', e); refreshDevices(); }
        }
        else if (tabId === 'workstation') refreshWorkstation();
    }

    // Legacy compatibility — palette commands still call these.
    window.activateTab = setActiveTab;

    // ============================================================ CHIP / ICON WIRING ==
    function wireHeader() {
        qsa('.sp-chip').forEach(c => c.addEventListener('click', () => setActiveTab(c.dataset.tab)));
        qsa('[data-target-tab]').forEach(c => c.addEventListener('click', () => setActiveTab(c.dataset.targetTab)));

        const palette = $('hdr-palette');
        if (palette) palette.addEventListener('click', () => openPalette());

        const settings = $('hdr-settings');
        if (settings) settings.addEventListener('click', () => openSettingsModal());

        const alerts = $('hdr-alerts');
        if (alerts) alerts.addEventListener('click', () => setActiveTab('workstation'));

        const bell = $('hdr-bell');
        if (bell) bell.addEventListener('click', () => openInboxModal());

        const signout = $('sp-signout');
        if (signout) signout.addEventListener('click', signOut);
    }

    function openPalette() {
        if (window.RkojPalette && window.RkojPalette.open) return window.RkojPalette.open();
        toast('palette not loaded');
    }

    async function signOut() {
        try { await fetchJson('/api/auth/logout', { method: 'POST' }); } catch (_) {}
        try { localStorage.removeItem('sinister_token'); } catch (_) {}
        location.href = '/login';
    }

    // ============================================================ CLOCK / HEALTH ==
    function updateClock() {
        const c = $('clock');
        if (!c) return;
        const now = new Date();
        const pad = (n) => String(n).padStart(2, '0');
        c.textContent = pad(now.getHours()) + ':' + pad(now.getMinutes());
    }

    async function pollHealth() {
        const h = await fetchJson('/api/health');
        const badge = $('health-pill');
        if (!badge) return;
        if (h && h.ok) {
            badge.textContent = '● online' + (h.version ? ' v' + h.version : '');
            badge.classList.remove('bad');
        } else {
            badge.textContent = '● offline';
            badge.classList.add('bad');
        }
    }

    // ============================================================ PROJECTS ==
    async function loadProjects() {
        const r = await fetchJson('/api/projects');
        const list = (r && r.projects) || [];
        state.projects = list;
        return list;
    }

    function renderProjectStrip() {
        const strip = $('sp-projstrip');
        if (!strip) return;
        strip.innerHTML = '';
        const sessions = state.sessions || [];

        // [All N] chip first.
        const totalCount = sessions.length;
        strip.appendChild(makeProjChip('all', 'All', totalCount));

        // One chip per project.
        for (const p of state.projects) {
            const key = p.key;
            const display = p.display || p.key;
            const n = sessions.filter(s => agentProject(s) === key).length;
            strip.appendChild(makeProjChip(key, display, n));
        }
    }

    function makeProjChip(key, label, count) {
        const isActive = state.projectFilter === key;
        return el('button', {
            class: 'sp-proj-chip' + (isActive ? ' active' : ''),
            'data-proj': key,
            onclick: () => {
                state.projectFilter = key;
                lsSet(LS_PROJ_FILTER, key);
                renderProjectStrip();
                renderAgentStack();
            },
        },
            el('span', { class: 'sp-proj-chip-label' }, label),
            el('span', { class: 'sp-proj-chip-count' }, String(count)),
        );
    }

    // Best-effort: map a session to a project key. Sessions don't carry the
    // project explicitly in the legacy /api/sessions schema, so we try a few
    // common fields and fall back to "sanctum".
    function agentProject(s) {
        if (!s) return 'sanctum';
        return s.project || s.project_key || s.repo || s.lane || (s.agent || '').toLowerCase().replace(/\s+/g, '-') || 'sanctum';
    }

    // ============================================================ AGENTS PANE ==
    async function refreshAgents() {
        const r = await fetchJson('/api/sessions');
        state.sessions = (r && (r.sessions || [])) || [];
        renderAgentStack();
        renderProjectStrip();
        updateKpiAgents();
    }

    function renderAgentStack() {
        const host = $('agent-stack');
        if (!host) return;
        host.innerHTML = '';
        let visible = state.sessions.slice();
        if (state.projectFilter && state.projectFilter !== 'all') {
            visible = visible.filter(s => agentProject(s) === state.projectFilter);
        }
        visible.sort((a, b) => (b.online ? 1 : 0) - (a.online ? 1 : 0));
        const ct = bind(document, 'agents-grid-count');
        if (ct) ct.textContent = visible.length + (visible.length === 1 ? ' agent' : ' agents');

        const chipCt = bind(document, 'chip-agents-count');
        if (chipCt) chipCt.textContent = state.sessions.filter(s => s.online).length;

        if (!visible.length) {
            host.appendChild(el('div', { class: 'sp-empty' }, 'no agents match the current filter — spawn a new one to start'));
            return;
        }
        const tpl = $('tpl-agent-console');
        for (const s of visible) {
            const frag = tpl.content.cloneNode(true);
            const card = qs('[data-bind="agent-card"]', frag);
            if (s.online) card.classList.add('online');
            bind(frag, 'agent-name').textContent = s.agent || '?';
            bind(frag, 'agent-project').textContent = agentProject(s);
            bind(frag, 'agent-mode').textContent = s.mode || '--';
            bind(frag, 'agent-last').textContent = 'last ' + (s.last_seen_human || 'never');
            const tail = bind(frag, 'agent-tail');
            tail.innerHTML = '';
            const recent = (s.inbox_tail || []).slice(-5);
            if (recent.length) {
                for (const m of recent) {
                    const body = (m.message || '').slice(0, 240);
                    tail.appendChild(el('div', { class: 'sp-agent-tail-line' },
                        el('span', { class: 'sp-agent-tail-from' }, (m.from || '?') + ': '),
                        body,
                    ));
                }
            } else {
                tail.appendChild(el('div', { class: 'sp-empty' }, '(no recent activity)'));
            }
            const input = bind(frag, 'agent-input');
            const sendBtn = qs('[data-act="send"]', frag);
            const doSend = async () => {
                const text = (input.value || '').trim();
                if (!text) return;
                // Slash-command parity: route /resume /create /save /git /mcp /effort /fast
                // to local handlers; everything else is a normal inbox message.
                if (text.startsWith('/')) {
                    return handleSlashCommand(text, s);
                }
                sendBtn.disabled = true;
                const r = await fetchJson('/api/inbox/send', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ to: s.agent, body: text, sender: 'workstation' }),
                });
                sendBtn.disabled = false;
                if (r && r.ok) { input.value = ''; toast('[OK] sent to ' + s.agent); }
                else toast('[FAIL] ' + ((r && (r.error || r.detail)) || 'send failed'), true);
            };
            sendBtn.addEventListener('click', doSend);
            input.addEventListener('keydown', (ev) => { if (ev.key === 'Enter') doSend(); });

            // Per-card action buttons.
            qsa('[data-act]', frag).forEach(b => {
                const act = b.dataset.act;
                if (act === 'send') return;
                b.addEventListener('click', () => handleAgentAction(act, s));
            });

            host.appendChild(frag);
        }
    }

    function handleSlashCommand(text, session) {
        const parts = text.trim().split(/\s+/);
        const cmd = (parts[0] || '').toLowerCase();
        const arg = parts.slice(1).join(' ');
        switch (cmd) {
            case '/help':
                return toast('slash: /help /clear /compact /resume <project> /create /save /git /mcp /effort /fast');
            case '/clear':
                return toast('clear: dispatched to ' + session.agent);
            case '/compact':
                return toast('compact: dispatched to ' + session.agent);
            case '/resume':
                return handleAgentAction('resume', session);
            case '/create':
                return openSpawnModal();
            case '/save':
                return toast('save: triggers cycle-point snapshot (open Cycle points to commit)');
            case '/git':
                return toast('git: open Workstation tab > Vault for commit UI');
            case '/mcp':
                return toast('mcp: open Settings > MCP wiring (operator-only)');
            case '/effort':
                return toast('effort: use Settings > Default intelligence to switch model');
            case '/fast':
                return toast('fast: toggles Opus 4.6 in the spawn modal');
            default:
                return toast('unknown slash: ' + cmd + ' (try /help)', true);
        }
    }

    async function handleAgentAction(act, session) {
        switch (act) {
            case 'resume': {
                const r = await fetchJson('/api/launch', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ project: agentProject(session), mode: session.mode || 'overview', no_notepad: true }),
                });
                return toast(r && r.ok ? '[OK] resumed' : '[FAIL] ' + ((r && (r.error || r.detail)) || 'resume failed'), !(r && r.ok));
            }
            case 'popout':
                if (window.RkojPopout && window.RkojPopout.open) window.RkojPopout.open('agents');
                else toast('popout not loaded', true);
                return;
            case 'close': {
                if (!confirm('Close session ' + (session.agent || '?') + '?')) return;
                toast('close: window closer not yet wired in Panel rewrite (TODO)');
                return;
            }
        }
    }

    // Pane toolbar actions.
    function wireAgentsPaneToolbar() {
        const n = $('agents-new');
        if (n) n.addEventListener('click', openSpawnModal);
        const b = $('agents-broadcast');
        if (b) b.addEventListener('click', openBroadcastModal);
        const r = $('agents-refresh');
        if (r) r.addEventListener('click', refreshAgents);
    }

    // ============================================================ PHONES PANE ==
    async function refreshDevices() {
        const r = await fetchJson('/api/devices');
        state.devices = (r && (r.devices || [])) || [];
        renderDeviceGrid();
        updateKpiPhones();
    }

    function renderDeviceGrid() {
        const host = $('device-grid');
        if (!host) return;
        host.innerHTML = '';
        const list = state.devices;
        const ct = bind(document, 'phones-grid-count');
        if (ct) ct.textContent = list.length + (list.length === 1 ? ' attached' : ' attached');
        const chipCt = bind(document, 'chip-phones-count');
        if (chipCt) chipCt.textContent = list.filter(d => (d.state || '').toLowerCase() === 'device').length;
        if (!list.length) {
            host.appendChild(el('div', { class: 'sp-empty' }, 'no devices attached — connect a phone over USB or TCP/IP'));
            return;
        }
        const tpl = $('tpl-device-card');
        for (const d of list) {
            const frag = tpl.content.cloneNode(true);
            const card = qs('[data-bind="device-card"]', frag);
            const stateStr = (d.state || 'unknown').toLowerCase();
            if (stateStr === 'device') card.classList.add('online');
            if (stateStr === 'unauthorized') card.classList.add('unauthorized');
            bind(frag, 'device-model').textContent = d.model || d.product || d.serial || '?';
            bind(frag, 'device-state').textContent = stateStr;
            bind(frag, 'device-transport').textContent = d.transport_id ? 't' + d.transport_id : (d.transport || '--');
            bind(frag, 'device-serial').textContent = d.serial || '--';
            bind(frag, 'device-lane').textContent = d.lane || d.device || '--';

            qsa('[data-act]', frag).forEach(b => {
                const act = b.dataset.act;
                b.addEventListener('click', () => handleDeviceAction(act, d));
            });

            host.appendChild(frag);
        }
    }

    async function handleDeviceAction(act, device) {
        const serial = device.serial;
        switch (act) {
            case 'view': {
                // scrcpy launch — server.py /api/devices/{serial}/view starts scrcpy
                // process on the workstation host. Viewer is the scrcpy window itself
                // (not embedded in HTML — that's a deferred TODO).
                const r = await fetchJson('/api/devices/' + encodeURIComponent(serial) + '/view', { method: 'POST' });
                return toast(r && r.ok ? '[OK] scrcpy launched for ' + serial : '[FAIL] scrcpy: ' + ((r && (r.error || r.detail)) || 'unsupported'), !(r && r.ok));
            }
            case 'push': {
                const path = prompt('Local path to push to /sdcard/Download/ on ' + serial + ':');
                if (!path) return;
                const r = await fetchJson('/api/devices/' + encodeURIComponent(serial) + '/push', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ src: path }),
                });
                return toast(r && r.ok ? '[OK] pushed' : '[FAIL] ' + ((r && (r.error || r.detail)) || 'push failed'), !(r && r.ok));
            }
            case 'logs':
                return toast('logs: open dev-tools rail / device logcat viewer (TODO follow-up)');
        }
    }

    function wirePhonesPaneToolbar() {
        const s = $('phones-scan');
        if (s) s.addEventListener('click', async () => {
            const r = await fetchJson('/api/devices/scan-all', { method: 'POST' });
            toast(r && r.ok ? '[OK] scan dispatched' : '[FAIL] ' + ((r && (r.error || r.detail)) || 'unsupported'), !(r && r.ok));
        });
        const r = $('phones-refresh');
        if (r) r.addEventListener('click', refreshDevices);
    }

    // ============================================================ WORKSTATION PANE ==
    async function refreshWorkstation() {
        await Promise.all([
            refreshVault(),
            refreshRequests(),
            refreshActivity(),
            refreshCyclePoints(),
        ]);
    }

    async function refreshVault() {
        const r = await fetchJson('/api/vault/quota');
        const status = bind(document, 'ws-vault-status');
        const fill = bind(document, 'ws-vault-fill');
        const used = bind(document, 'ws-vault-used');
        const free = bind(document, 'ws-vault-free');
        if (!r || r.vault_offline || r.ok === false) {
            if (status) status.textContent = '● offline';
            if (fill) fill.style.width = '0%';
            if (used) used.textContent = '--';
            if (free) free.textContent = '--';
            updateKpiVault(null);
            return;
        }
        const usedB = r.used_bytes || 0;
        const maxB  = (r.max_gb || 1024) * Math.pow(1024, 3);
        const pct = Math.min(100, (usedB / maxB) * 100);
        if (status) status.textContent = '● online';
        if (fill) fill.style.width = pct.toFixed(1) + '%';
        if (used) used.textContent = formatBytes(usedB);
        if (free) free.textContent = formatBytes(Math.max(0, maxB - usedB));
        updateKpiVault({ pct, usedB, maxB });
    }

    async function refreshRequests() {
        const r = await fetchJson('/api/operator-requests');
        const list = (r && (r.requests || r.items || [])) || [];
        const host = bind(document, 'ws-requests-list');
        const count = bind(document, 'ws-requests-count');
        if (count) count.textContent = list.length;
        const pending = list.filter(x => (x.state || x.status || '').toLowerCase() === 'pending').length;
        const kpi = bind(document, 'kpi-pending');
        if (kpi) kpi.textContent = pending;
        const kpiSub = bind(document, 'kpi-pending-sub');
        if (kpiSub) kpiSub.textContent = list.length + ' total';
        const badge = $('alerts-count');
        if (badge) {
            if (pending > 0) { badge.textContent = pending; badge.hidden = false; }
            else { badge.hidden = true; }
        }
        if (!host) return;
        host.innerHTML = '';
        if (!list.length) { host.appendChild(el('div', { class: 'sp-empty' }, 'no pending requests')); return; }
        list.slice(0, 6).forEach(r => {
            host.appendChild(el('div', { class: 'sp-ws-row' },
                el('span', null, (r.kind || r.title || 'request').slice(0, 30)),
                el('span', null, r.state || r.status || '--'),
            ));
        });
    }

    async function refreshActivity() {
        const r = await fetchJson('/api/recent-runlogs');
        const rows = (r && (r.runlogs || [])) || [];
        const host = bind(document, 'ws-activity-list');
        if (!host) return;
        host.innerHTML = '';
        if (!rows.length) { host.appendChild(el('div', { class: 'sp-empty' }, 'no recent activity')); return; }
        rows.slice(0, 8).forEach(run => {
            host.appendChild(el('div', { class: 'sp-ws-row' },
                el('span', null, (run.script || '?').slice(0, 26)),
                el('span', null, run.ok ? 'OK' : 'FAIL'),
            ));
        });
    }

    async function refreshCyclePoints() {
        const r = await fetchJson('/api/cycle-points');
        const rows = (r && (r.cycle_points || r.items || [])) || [];
        const host = bind(document, 'ws-cycle-list');
        const ct   = bind(document, 'ws-cycle-count');
        if (ct) ct.textContent = rows.length;
        if (!host) return;
        host.innerHTML = '';
        if (!rows.length) { host.appendChild(el('div', { class: 'sp-empty' }, 'no cycle points yet')); return; }
        rows.slice(0, 6).forEach(c => {
            host.appendChild(el('div', { class: 'sp-ws-row' },
                el('span', null, (c.title || c.slug || 'point').slice(0, 28)),
                el('span', null, c.created || c.ts || '--'),
            ));
        });
    }

    function wireWorkstationPaneToolbar() {
        qsa('#pane-workstation [data-act]').forEach(b => {
            b.addEventListener('click', () => handleWorkstationAction(b.dataset.act));
        });
    }

    function handleWorkstationAction(act) {
        switch (act) {
            case 'open-vault':       return toast('vault: scroll to the Vault card on the right');
            case 'open-requests':    return toast('requests: scroll to Operator requests card');
            case 'open-cycle-points':return toast('cycle-points: scroll to Cycle points card');
            case 'open-scheduler':
                if (window.RkojScheduler && window.RkojScheduler.renderInto) {
                    openModal('Scheduler', (body) => window.RkojScheduler.renderInto(body));
                } else toast('scheduler.js not loaded', true);
                return;
            case 'vault-commit':
                if (window.RkojVault && window.RkojVault.openCommitModal) return window.RkojVault.openCommitModal();
                return toast('vault commit modal not loaded', true);
        }
    }

    // ============================================================ KPI STRIP ==
    function updateKpiAgents() {
        const online = state.sessions.filter(s => s.online).length;
        const total  = state.sessions.length;
        const num = bind(document, 'kpi-agents-online');
        const sub = bind(document, 'kpi-agents-sub');
        if (num) num.textContent = online;
        if (sub) sub.textContent = total + ' total';
    }

    function updateKpiPhones() {
        const online = state.devices.filter(d => (d.state || '').toLowerCase() === 'device').length;
        const total  = state.devices.length;
        const num = bind(document, 'kpi-phones-online');
        const sub = bind(document, 'kpi-phones-sub');
        if (num) num.textContent = online;
        if (sub) sub.textContent = total + ' attached';
    }

    function updateKpiVault(info) {
        const num = bind(document, 'kpi-vault-used');
        const sub = bind(document, 'kpi-vault-sub');
        if (!info) {
            if (num) num.textContent = '--';
            if (sub) sub.textContent = 'offline';
            return;
        }
        if (num) num.textContent = info.pct.toFixed(0) + '%';
        if (sub) sub.textContent = formatBytes(info.usedB) + ' / ' + formatBytes(info.maxB);
    }

    function formatBytes(b) {
        if (!b && b !== 0) return '--';
        const u = ['B','KB','MB','GB','TB'];
        let i = 0; let n = Number(b);
        while (n >= 1024 && i < u.length - 1) { n /= 1024; i++; }
        return n.toFixed(n >= 100 ? 0 : 1) + ' ' + u[i];
    }

    // ============================================================ MODALS ==
    function openModal(title, mountBody, footFactory) {
        const tpl = $('tpl-modal');
        if (!tpl) { toast('modal template missing', true); return; }
        const frag = tpl.content.cloneNode(true);
        const overlay = qs('.sp-modal-overlay', frag);
        const root = $('modal-root');
        const close = () => { try { root.innerHTML = ''; } catch (_) {} };
        overlay.addEventListener('click', (ev) => { if (ev.target === overlay) close(); });
        qsa('[data-act="close"]', frag).forEach(b => b.addEventListener('click', close));
        bind(frag, 'modal-title').textContent = title;
        const body = bind(frag, 'modal-body');
        const foot = bind(frag, 'modal-foot');
        if (mountBody) mountBody(body, close);
        if (footFactory) footFactory(foot, close);
        else {
            foot.appendChild(el('button', { class: 'sp-btn ghost', onclick: close }, 'Close'));
        }
        root.innerHTML = '';
        root.appendChild(frag);
        return { close };
    }

    function openSpawnModal() {
        openModal('Spawn agent', (body, close) => {
            const tpl = $('tpl-spawn-form');
            body.appendChild(tpl.content.cloneNode(true));
            const sel = bind(body, 'sf-project');
            sel.innerHTML = '';
            for (const p of state.projects) {
                sel.appendChild(el('option', { value: p.key }, p.display || p.key));
            }
            const launch = el('button', { class: 'sp-btn primary', onclick: async () => {
                const project = bind(body, 'sf-project').value;
                const mode    = bind(body, 'sf-mode').value;
                const fast    = bind(body, 'sf-fast').checked;
                const prompt  = bind(body, 'sf-prompt').value.trim();
                launch.disabled = true; launch.textContent = 'Launching...';
                const r = await fetchJson('/api/launcher/spawn', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ project, mode, fast, prompt }),
                });
                if (r && r.ok) {
                    toast('[OK] ' + project + ' launched');
                    close();
                    setTimeout(refreshAgents, 500);
                } else {
                    toast('[FAIL] ' + ((r && (r.error || r.detail)) || 'spawn failed'), true);
                    launch.disabled = false; launch.textContent = 'Launch';
                }
            }}, 'Launch');
            // Attach via foot.
            setTimeout(() => {
                const foot = body.parentElement.querySelector('[data-bind="modal-foot"]');
                if (foot) foot.insertBefore(launch, foot.firstChild);
            }, 0);
        });
    }

    function openBroadcastModal() {
        openModal('Broadcast', (body, close) => {
            const tpl = $('tpl-broadcast-form');
            body.appendChild(tpl.content.cloneNode(true));
            const send = el('button', { class: 'sp-btn primary', onclick: async () => {
                const subkind = bind(body, 'bc-subkind').value;
                const text    = bind(body, 'bc-body').value.trim();
                if (!text) { toast('message required', true); return; }
                send.disabled = true; send.textContent = 'Sending...';
                const r = await fetchJson('/api/inbox/broadcast', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ subkind, body: text, from_agent: 'workstation' }),
                });
                if (r && r.ok) {
                    toast('[OK] broadcast to ' + ((r.delivered || []).length) + ' agents');
                    close();
                } else {
                    toast('[FAIL] ' + ((r && (r.error || r.detail)) || 'broadcast failed'), true);
                    send.disabled = false; send.textContent = 'Send';
                }
            }}, 'Send');
            setTimeout(() => {
                const foot = body.parentElement.querySelector('[data-bind="modal-foot"]');
                if (foot) foot.insertBefore(send, foot.firstChild);
            }, 0);
        });
    }

    function openInboxModal() {
        openModal('Cross-agent inbox', (body) => {
            body.appendChild(el('div', { class: 'sp-empty' }, 'Inbox UI: cycle-points/scheduler will mount here. For now use the per-agent message rail in the Agents tab.'));
        });
    }

    function openSettingsModal() {
        openModal('Workstation settings', (body) => {
            const curDensity = document.body.getAttribute('data-density') || 'cozy';
            const sel = el('select', {
                class: 'sp-input',
                onchange: (ev) => {
                    document.body.setAttribute('data-density', ev.target.value);
                    lsSet('rkoj.density', ev.target.value);
                },
            });
            ['compact', 'cozy', 'comfortable'].forEach(d => {
                const opt = el('option', { value: d }, d);
                if (d === curDensity) opt.setAttribute('selected', '');
                sel.appendChild(opt);
            });
            body.appendChild(el('div', { class: 'sp-form-row' },
                el('span', { class: 'sp-form-label' }, 'Density'),
                sel,
            ));
            body.appendChild(el('p', { class: 'sp-empty' }, 'Full settings drawer (MCP wiring, accounts, hot-reload) is exposed via the /api/auth/whoami flow — see SESSION-START/01-MCP-NETWORK.md.'));
        });
    }

    // ============================================================ PUBLIC HELPERS (companion modules) ==
    // popout.js / palette.js / cycle-points.js / scheduler.js / RkojVault depend
    // on window.RkojHelpers — preserve the contract.
    window.RkojHelpers = {
        $, qs, qsa, el, toast, fetchJson,
        bind: (host, name) => bind(host, name),
        activateTab: setActiveTab,
        getActiveTab: () => state.activeTab,
        getProjects: () => state.projects.slice(),
        getSessions: () => state.sessions.slice(),
        getDevices:  () => state.devices.slice(),
        openModal,
        openSpawnModal,
        openBroadcastModal,
    };

    // Legacy globals — some modules read these directly.
    window.activateTab = setActiveTab;
    window.fetchJson   = fetchJson;
    window.toast       = toast;

    // ============================================================ INIT ==
    function init() {
        renderSidebarNav();
        wireHeader();
        wireAgentsPaneToolbar();
        wirePhonesPaneToolbar();
        wireWorkstationPaneToolbar();

        // Apply density from LS.
        const d = lsGet('rkoj.density', 'cozy');
        document.body.setAttribute('data-density', d);

        // Set initial active tab + title.
        setActiveTab(state.activeTab);

        // Clock + health.
        updateClock();
        setInterval(updateClock, 30000);
        pollHealth();
        setInterval(pollHealth, REFRESH_MS);

        // Initial loads.
        loadProjects().then(() => {
            renderProjectStrip();
            refreshAgents();
            refreshWorkstation();
        });
        refreshDevices();

        // Polling.
        setInterval(refreshAgents, REFRESH_MS);
        setInterval(refreshDevices, DEVICE_REFRESH_MS);
        setInterval(() => { refreshVault(); refreshRequests(); }, KPI_REFRESH_MS);

        // FleetState SSE — keep subscribed; on tick, light refresh.
        try {
            if (window.FleetState && window.FleetState.subscribe) {
                window.FleetState.subscribe(() => {
                    if (state.activeTab === 'agents') refreshAgents();
                });
                if (window.FleetState.start) window.FleetState.start();
            }
        } catch (_) {}

        // Cmd+K / Ctrl+K -> palette.
        document.addEventListener('keydown', (ev) => {
            if ((ev.ctrlKey || ev.metaKey) && ev.key.toLowerCase() === 'k') {
                ev.preventDefault();
                openPalette();
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
