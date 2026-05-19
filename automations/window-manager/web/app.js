// Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
/* Panel-style redesign — Sinister Sanctum master agent (Claude) :: 2026-05-19 */
// RKOJ.exe :: Workbench UI — Sinister-Panel-style shell
// (sidebar-left + top-tabs + hero KPI row + per-tab content).
// PRESERVES every shipped helper, renderer, PaneRegistry handler, and
// the window.RkojHelpers contract so popout/palette/cycle-points/scheduler
// continue to work. All prior templates remain in the DOM and are still
// reachable via the dev-tools rail OR the Cmd+K command palette.

// ============================================================== CORE REGISTRIES ==
// Author: Sinister Sanctum master agent (Claude UI-redesign sub) :: 2026-05-19 — workstation sweep
// Two-tab workstation: ADB DEVICES (phone-viewer) + AGENTS (workstation).
// Vault drops out of the top tab bar — it stays accessible via the agents-tab
// VAULT tile (opens the dev-tools drawer with the vault template) and via the
// header ribbon AUTOMATE > Vault commit action.
const TABS = ['adb', 'agents'];
// Legacy aliases — older code paths call activateTab('devices')/'fleet'/'vault'.
// 'fleet' + 'devices' resolve to the new 'adb' tab. 'vault' resolves to 'agents'
// (caller intent is "go to the workstation surface where vault is reachable").
const LEGACY_TAB_ALIAS = { devices: 'adb', fleet: 'adb', vault: 'agents' };

// MODES list - preserved for launcher wizard fallback when /api/launcher/options is empty.
const MODES = ['overview', 'dev', 'audit', 'deploy', 'push', 'debug', 'explore'];

// Polling intervals.
const REFRESH_MS = 30000;
const DEVICE_REFRESH_MS = 15000;
const KPI_REFRESH_MS = 15000;
const _deviceTimers = { devices: null };
let _kpiTimer = null;

// LocalStorage keys.
const LS_ACTIVE_TAB = 'rkoj.skel.tab';
const LS_DEVTOOLS_OPEN_PREFIX = 'rkoj.devtools.';
const LS_RECENT_LAUNCHES = 'recent_launches';
const LS_FLEET_FILTER = 'rkoj.fleet.filter';      // all|online|stale|locked
const LS_FLEET_SELECTED = 'rkoj.fleet.selected';  // serial

// ============================================================== HELPERS (preserved) ==
const $ = (id) => document.getElementById(id);
const qs = (sel, root = document) => root.querySelector(sel);
const qsa = (sel, root = document) => Array.from(root.querySelectorAll(sel));

const el = (tag, attrs = {}, ...children) => {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
        if (k === 'class') e.className = v;
        else if (k === 'onclick') e.addEventListener('click', v);
        else if (k === 'onkeydown') e.addEventListener('keydown', v);
        else if (k.startsWith('data-')) e.setAttribute(k, v);
        else if (v !== undefined && v !== null) e.setAttribute(k, v);
    }
    for (const c of children) {
        if (c == null) continue;
        e.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
    }
    return e;
};

function toast(msg, isError = false) {
    const t = $('toast');
    if (!t) { try { console.log('[toast]', msg); } catch (e) {} return; }
    t.textContent = msg;
    t.classList.toggle('err', isError);
    t.classList.add('show');
    clearTimeout(toast._t);
    toast._t = setTimeout(() => t.classList.remove('show'), 4200);
}

function _authHeaders() {
    let tok = null;
    try { tok = localStorage.getItem('sinister_token'); } catch (e) {}
    return tok ? { 'Authorization': 'Bearer ' + tok } : {};
}

async function fetchJson(url, opts = {}) {
    try {
        opts.headers = Object.assign({}, _authHeaders(), opts.headers || {});
        const r = await fetch(url, opts);
        if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
        return await r.json();
    } catch (e) {
        console.warn('fetch failed', url, e);
        return { ok: false, error: e.message };
    }
}

function lsGet(key, dflt) {
    try { const v = localStorage.getItem(key); return v === null ? dflt : v; }
    catch (e) { return dflt; }
}
function lsSet(key, value) {
    try { localStorage.setItem(key, value); } catch (e) {}
}

// Bind-name -> element inside a host
function bind(host, name) {
    return qs(`[data-bind="${name}"]`, host);
}

// ============================================================== CLOCK / HEALTH ==
function updateClock() {
    const now = new Date();
    const pad = (n) => String(n).padStart(2, '0');
    const c = $('clock');
    if (c) c.textContent = `${pad(now.getHours())}:${pad(now.getMinutes())}`;
}
setInterval(updateClock, 1000);
updateClock();

async function pollHealth() {
    const h = await fetchJson('/api/health');
    const badge = $('health-pill');
    if (!badge) return;
    if (h.ok) {
        badge.textContent = `● online v${h.version}`;
        badge.classList.remove('bad');
    } else {
        badge.textContent = '● offline';
        badge.classList.add('bad');
    }
}

// ============================================================== TAB STATE ==
const state = {
    activeTab: 'adb',
    paneState: { adb: { selectedSerial: null, filter: 'all', lanes: new Set(), embedded: new Set() }, agents: {} },
    devicesCache: [],
    sessionsCache: [],
    /* Workstation sweep — Sinister Sanctum master agent (Claude UI-redesign sub) :: 2026-05-19
     * adbEvents: rolling buffer of recent ADB commands across all devices.
     * Each entry: { ts, serial, cmd, ok, rc, line }. Cap at 60. */
    adbEvents: [],
};

// PaneRegistry kept for compatibility with palette / dev-tools-rail / popouts that
// mount existing templates (dashboard, memory, inbox, requests, codex, ...).
const PaneRegistry = {};

// ============================================================== WORKSTATION TAB MACHINERY ==
/* Author: Sinister Sanctum master agent (Claude UI-redesign sub) :: 2026-05-19 — workstation sweep
 * Two-tab routing (ADB / AGENTS) with side-nav alias preserved for palette routes. */
function setSkelTab(tabId) {
    if (LEGACY_TAB_ALIAS[tabId]) tabId = LEGACY_TAB_ALIAS[tabId];
    if (!TABS.includes(tabId)) return;
    state.activeTab = tabId;
    lsSet(LS_ACTIVE_TAB, tabId);
    qsa('.rkoj-tab').forEach(b => {
        const on = b.dataset.tab === tabId;
        b.classList.toggle('active', on);
        b.setAttribute('aria-selected', on ? 'true' : 'false');
    });
    qsa('.rkoj-tab-pane').forEach(p => {
        p.hidden = (p.id !== `skel-${tabId}`);
    });
    // Re-render the per-tab ribbon (groups differ slightly across tabs).
    renderHeaderRibbon(tabId);
    mountSkelTabContent(tabId);
}

// Sidebar nav slugs that legacy callers (popouts, palette) still use. Map them
// to a top tab. NOTE: there is no sidebar in the new shell — these are pure
// aliases for #pane=<slug> hash routes and palette command IDs.
const SIDE_NAV_TO_TAB = {
    overview: 'agents', progress: 'agents', accounts: 'agents', 'control-center': 'agents',
    analytics: 'agents', library: 'agents', codex: 'agents', memory: 'agents',
    devices: 'adb', fleet: 'adb', phones: 'adb', agents: 'agents', vault: 'agents',
    scheduler: 'agents', 'cycle-points': 'agents', settings: 'agents', inbox: 'agents',
    requests: 'agents', skills: 'agents', tools: 'agents', inventions: 'agents',
};

function setSkelNav(navId) {
    const tabId = SIDE_NAV_TO_TAB[navId] || 'agents';
    setSkelTab(tabId);
}

// Legacy stub — old shell had a sidebar; the workstation shell drops it. No-op
// kept so prior callers (mid-flight palette commands) don't throw.
function syncSkelNavWithTab(_tabId) { /* removed in workstation sweep 2026-05-19 */ }

function mountSkelTabContent(tabId) {
    const pane = $(`skel-${tabId}`);
    if (!pane) return;
    pane.innerHTML = '';
    if (tabId === 'adb') mountAdbTab(pane);
    else if (tabId === 'agents') mountAgentsTab(pane);
}

// Back-compat alias — older code calls activateTab() to switch panes.
function activateTab(tabId) {
    if (LEGACY_TAB_ALIAS[tabId]) tabId = LEGACY_TAB_ALIAS[tabId];
    setSkelTab(tabId);
}

// Legacy stub — old ribbon row 2 is removed; keep the no-op so callers don't crash.
function renderRibbonRow2(_tabId) { /* removed in Panel-style redesign 2026-05-19 */ }

// Legacy stub — preserved so prior call sites compile; UI shell no longer mounts
// into #tab-devices / #tab-agents (those don't exist in the new index.html).
function mountTabContent(tabId) { mountSkelTabContent(LEGACY_TAB_ALIAS[tabId] || tabId); }

// ============================================================== RIBBON ROW 2 ==
// Per-tab tile groups -> {label, tiles:[{icon,label,action}]}
function ribbonGroupsFor(tabId) {
    if (tabId === 'devices') {
        return [
            { label: 'VIEW', tiles: [
                { icon: '⛶', label: 'Toggle dev tools', action: 'toggle-devtools' },
                { icon: '↗', label: 'Popout grid', action: 'popout-current' },
                { icon: '↻', label: 'Refresh', action: 'refresh-devices' },
            ]},
            { label: 'AUTOMATE', tiles: [
                { icon: '⚡', label: 'Scan all (parallel)', action: 'scan-all-phones' },
                { icon: '▦', label: 'Bulk push', action: 'bulk-push' },
            ]},
            { label: 'MAINTAIN', tiles: [
                { icon: '✱', label: 'Health probe', action: 'health-probe' },
                { icon: '↻', label: 'Restart console', action: 'restart-console' },
            ]},
        ];
    }
    // agents
    return [
        { label: 'VIEW', tiles: [
            { icon: '⛶', label: 'Toggle dev tools', action: 'toggle-devtools' },
            { icon: '↗', label: 'Popout sessions', action: 'popout-sessions' },
            { icon: '☰', label: 'Layout presets', action: 'layout-presets' },
        ]},
        { label: 'SPAWN', tiles: [
            { icon: '＋', label: 'New agent', action: 'new-agent' },
            { icon: '⚙', label: 'Launcher wizard', action: 'launcher-wizard' },
            { icon: '✉', label: 'Send inbox to all', action: 'inbox-all' },
            /* Cross-agent broadcast — Sinister Sanctum master agent (Claude) :: 2026-05-19 */
            { icon: '📣', label: 'Broadcast', action: 'broadcast' },
            { icon: '⚡', label: 'Codex review', action: 'codex-review' },
        ]},
        { label: 'AUTOMATE', tiles: [
            { icon: '⛁', label: 'Cycle points', action: 'cycle-points' },
            { icon: '⏰', label: 'Scheduler', action: 'scheduler' },
            { icon: '▶', label: 'Run script', action: 'run-script' },
            /* RKOJ Vault UI — Sinister Sanctum master agent (Claude) :: 2026-05-19 */
            { icon: 'V', label: 'Vault', action: 'open-vault' },
        ]},
        { label: 'MAINTAIN', tiles: [
            { icon: '✨', label: 'Fix memory', action: 'fix-claude-memory' },
            { icon: '⛒', label: 'Build RKOJ.exe', action: 'build-rkoj' },
            { icon: '✱', label: 'Health probe', action: 'health-probe' },
            /* Heartbeat / [UPDATE] noop broadcast — Sinister Sanctum master :: 2026-05-19 hot-reload sprint */
            { icon: '♥', label: 'Ping all (heartbeat)', action: 'ping-all' },
            { icon: '↻', label: 'Restart console', action: 'restart-console' },
        ]},
    ];
}

function renderRibbonRow2(tabId) {
    const row = $('ribbon-row-2');
    if (!row) return;
    row.innerHTML = '';
    const groups = ribbonGroupsFor(tabId);
    groups.forEach((g, idx) => {
        if (idx > 0) row.appendChild(el('span', { class: 'rkoj-ribbon-divider' }));
        const groupEl = el('div', { class: 'rkoj-ribbon-group', 'data-group': g.label });
        const tiles = el('div', { class: 'rkoj-ribbon-tiles' });
        g.tiles.forEach(t => {
            tiles.appendChild(el('button', {
                class: 'lg-button rkoj-ribbon-tile',
                title: t.label,
                'data-action': t.action,
                onclick: () => handleRibbonAction(t.action),
            },
                el('span', { class: 'rkoj-tile-icon' }, t.icon),
                el('span', { class: 'rkoj-tile-label' }, t.label),
            ));
        });
        groupEl.appendChild(tiles);
        groupEl.appendChild(el('div', { class: 'rkoj-ribbon-group-label' }, g.label));
        row.appendChild(groupEl);
    });
}

async function handleRibbonAction(action) {
    switch (action) {
        case 'toggle-devtools':
            return setDevtoolsRail(!_devtoolsOpen, state.activeTab);
        case 'popout-current':
        case 'popout-sessions':
            if (window.RkojPopout && window.RkojPopout.open) {
                window.RkojPopout.open(state.activeTab === 'adb' ? 'phones' : 'dashboard');
            } else { toast('popout module not loaded', true); }
            return;
        /* Author: Sinister Sanctum master agent (Claude UI-redesign sub) :: 2026-05-19 — workstation sweep */
        case 'split-view':
            return toast('split-view: toggle planned for next sweep — use popout for now');
        case 'new-window': {
            const btn = $('hdr-newwin');
            if (btn) openNewWindowPicker(btn);
            return;
        }
        case 'spawn-agent':
            setSkelTab('agents');
            setTimeout(() => {
                const hero = qs('.rkoj-launcher-hero');
                if (hero) hero.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 50);
            return;
        case 'cycle-resume':
            setSkelTab('agents');
            setTimeout(() => {
                const c = qs('.rkoj-cyclepoints-card');
                if (c) c.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }, 50);
            return;
        case 'intelligence':
            return toast('intelligence: click a session card → INTELLIGENCE button');
        case 'open-inbox':
            return openDrawerTemplate('inbox', 'Cross-agent inbox');
        case 'vault-commit':
            if (window.RkojVault && window.RkojVault.openCommitModal) return window.RkojVault.openCommitModal();
            return openVaultDrawer();
        case 'view-logs':
            return toast('view-logs: open dev-tools rail → Refresh interval → (logs viewer coming)');
        case 'refresh-devices':
            return refreshAdbTab($('skel-adb'));
        case 'scan-all-phones': {
            const r = await fetchJson('/api/devices/scan-all', { method: 'POST' });
            return toast(r.ok ? '[OK] scan dispatched' : `[FAIL] ${r.error || r.detail || 'unsupported'}`, !r.ok);
        }
        case 'bulk-push':
            return toast('bulk-push: open a phone card -> PUSH; bulk UI coming via dev-tools rail');
        case 'health-probe':
            await pollHealth();
            return toast('[OK] health probed');
        case 'ping-all': {
            // Heartbeat probe — [UPDATE] noop broadcast to every online agent.
            // Each agent acks on its next turn boundary. The /api/sessions
            // `last_inbox_check` field surfaces who's responsive within 30s.
            // Author: Sinister Sanctum master agent (Claude) :: 2026-05-19 hot-reload sprint.
            const r = await fetchJson('/api/inbox/update-ping', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ subkind: 'noop', from_agent: 'operator' }),
            });
            if (r && r.ok) {
                const n = (r.delivered || []).length;
                return toast(`[UPDATE] noop ping fanned out to ${n} online agent${n === 1 ? '' : 's'}`);
            }
            return toast(`[FAIL] ping-all: ${(r && (r.error || r.detail)) || 'unknown'}`, true);
        }
        case 'restart-console': {
            if (!confirm('Restart RKOJ console process? Active sessions will keep running.')) return;
            const r = await fetchJson('/api/console/restart', { method: 'POST' });
            return toast(r.ok ? '[OK] restarting...' : `[FAIL] ${r.error || r.detail || 'unsupported'}`, !r.ok);
        }
        case 'new-agent':
        case 'launcher-wizard':
            setSkelTab('agents');
            setTimeout(() => {
                const hero = qs('.rkoj-launcher-hero');
                if (hero) hero.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 50);
            return;
        case 'inbox-all':
            // 2026-05-19 master sweep: 'inbox-all' now opens the broadcast modal
            // (multi-send is shipped via openBroadcastModal -> POST /api/inbox/broadcast).
            return openBroadcastModal();
        /* Cross-agent broadcast — Sinister Sanctum master agent (Claude) :: 2026-05-19 */
        case 'broadcast':
            return openBroadcastModal();
        case 'codex-review':
            return openDrawerTemplate('codex', 'Codex peer review');
        case 'cycle-points':
            return activateTab('agents'); // list lives in agents workbench
        case 'scheduler':
            return openDrawerTemplate('scheduler-drawer-tpl', 'Scheduler');
        case 'run-script':
            return toast('run-script: use Scheduler -> kind=script for whitelisted runs');
        case 'fix-claude-memory': {
            let rr = await fetchJson('/api/fix-claude-memory', { method: 'POST' });
            if (rr.ok === false && (rr.error || '').match(/404|not.*found/i)) {
                rr = await fetchJson('/api/launch', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ project: 'fix-claude-memory', mode: 'overview',
                        bat_path: 'C:\\Users\\Zonia\\Desktop\\Fix-Claude-Memory.bat' }),
                });
            }
            return toast(rr.ok ? '[OK] FIX CLAUDE MEMORY launched' : `[FAIL] ${rr.error || rr.detail || 'launch failed'}`, !rr.ok);
        }
        case 'build-rkoj': {
            const r = await fetchJson('/api/build', { method: 'POST' });
            return toast(r.ok ? '[OK] build dispatched' : `[FAIL] ${r.error || r.detail || 'unsupported'}`, !r.ok);
        }
        case 'layout-presets':
            return toast('layout-presets: cycle compact/cozy/comfortable via dev-tools rail');
        /* RKOJ Vault UI — Sinister Sanctum master agent (Claude) :: 2026-05-19 */
        case 'open-vault':
            // Open dev-tools rail with Vault drawer expanded.
            setDevtoolsRail(true, state.activeTab);
            renderDevtoolsBody(state.activeTab);
            return;
    }
}

// ============================================================== DEV-TOOLS RAIL ==
let _devtoolsOpen = false;
function setDevtoolsRail(open, tabId) {
    _devtoolsOpen = !!open;
    const rail = $('devtools-rail');
    if (!rail) return;
    rail.setAttribute('aria-hidden', _devtoolsOpen ? 'false' : 'true');
    rail.classList.toggle('open', _devtoolsOpen);
    document.body.classList.toggle('rkoj-devtools-open', _devtoolsOpen);
    lsSet(LS_DEVTOOLS_OPEN_PREFIX + tabId + '.open', _devtoolsOpen ? '1' : '0');
    if (_devtoolsOpen) renderDevtoolsBody(tabId);
}

function renderDevtoolsBody(tabId) {
    const body = $('devtools-body');
    if (!body) return;
    body.innerHTML = '';
    const sections = tabId === 'devices' ? devtoolsSectionsForDevices() : devtoolsSectionsForAgents();
    sections.forEach(s => body.appendChild(renderDevtoolsSection(s)));
    // common controls
    body.appendChild(renderDensityControls());
}

function devtoolsSectionsForDevices() {
    return [
        { id: 'refresh-interval', title: 'Refresh interval',
          mount: (host) => {
            const cur = parseInt(lsGet('rkoj.devices.refresh_ms', String(DEVICE_REFRESH_MS)), 10);
            const sl = el('input', { type: 'range', min: '5000', max: '60000', step: '1000', value: String(cur), class: 'lg-input' });
            const out = el('span', { class: 'count' }, `${(cur/1000).toFixed(0)}s`);
            sl.addEventListener('change', () => {
                lsSet('rkoj.devices.refresh_ms', sl.value);
                out.textContent = `${(parseInt(sl.value,10)/1000).toFixed(0)}s`;
                toast(`[OK] device refresh = ${(parseInt(sl.value,10)/1000).toFixed(0)}s`);
            });
            host.appendChild(el('div', { class: 'form-row' }, sl, out));
        }},
        { id: 'scrcpy', title: 'scrcpy defaults',
          mount: (host) => {
            const display = el('input', { type: 'number', value: lsGet('rkoj.scrcpy.display_id', '0'), class: 'lg-input', placeholder: 'display-id (0 = physical)' });
            const bitrate = el('input', { type: 'text', value: lsGet('rkoj.scrcpy.bitrate', '8M'), class: 'lg-input', placeholder: 'bitrate' });
            display.addEventListener('change', () => lsSet('rkoj.scrcpy.display_id', display.value));
            bitrate.addEventListener('change', () => lsSet('rkoj.scrcpy.bitrate', bitrate.value));
            host.appendChild(el('div', { class: 'form-row' }, el('label', null, 'display-id'), display));
            host.appendChild(el('div', { class: 'form-row' }, el('label', null, 'bitrate'), bitrate));
        }},
        { id: 'bulk', title: 'Bulk actions',
          mount: (host) => {
            host.appendChild(el('button', { class: 'lg-button',
                onclick: () => handleRibbonAction('scan-all-phones') }, 'Scan all phones (parallel)'));
            host.appendChild(el('p', { class: 'hint' }, 'Per-lane bulk push: select a lane in the device grid, then use PUSH on the lane-filter bar (coming).'));
        }},
    ];
}

function devtoolsSectionsForAgents() {
    return [
        { id: 'memory', title: 'Memory drawer', mount: (host) => mountTplInto(host, 'tpl-memory', 'memory') },
        { id: 'codex',  title: 'Codex drawer',  mount: (host) => mountTplInto(host, 'tpl-codex',  'codex')  },
        { id: 'knowledge', title: 'Knowledge', mount: (host) => mountTplInto(host, 'tpl-skills', 'skills') },
        { id: 'settings',  title: 'Settings',  mount: (host) => mountTplInto(host, 'tpl-settings', 'settings') },
        { id: 'schedule',  title: 'Schedule',  mount: (host) => {
            if (window.RkojScheduler && window.RkojScheduler.renderInto) {
                window.RkojScheduler.renderInto(host);
            } else {
                host.appendChild(el('div', { class: 'empty-note' }, 'scheduler.js not loaded'));
            }
        }},
        { id: 'inbox', title: 'Inbox', mount: (host) => mountTplInto(host, 'tpl-inbox', 'inbox') },
        { id: 'requests', title: 'Operator requests', mount: (host) => mountTplInto(host, 'tpl-requests', 'requests') },
        /* RKOJ Vault UI — Sinister Sanctum master agent (Claude) :: 2026-05-19 */
        { id: 'vault', title: 'Vault', mount: (host) => {
            const tpl = $('tpl-vault-drawer');
            if (!tpl) { host.appendChild(el('div', { class: 'empty-note' }, 'tpl-vault-drawer missing')); return; }
            host.appendChild(tpl.content.cloneNode(true));
            if (window.RkojVault && window.RkojVault.mount) window.RkojVault.mount(host);
            else host.appendChild(el('div', { class: 'empty-note' }, 'RkojVault module missing'));
        }},
    ];
}

function renderDevtoolsSection(sec) {
    const wrap = el('details', { class: 'rkoj-devtools-section', open: '' },
        el('summary', null, sec.title),
    );
    const body = el('div', { class: 'rkoj-devtools-section-body' });
    wrap.appendChild(body);
    try { sec.mount(body); } catch (e) { body.appendChild(el('div', { class: 'empty-note err' }, `[FAIL] ${e.message}`)); }
    return wrap;
}

function renderDensityControls() {
    const cur = document.body.getAttribute('data-density') || 'cozy';
    const wrap = el('details', { class: 'rkoj-devtools-section' },
        el('summary', null, 'Density / motion'));
    const body = el('div', { class: 'rkoj-devtools-section-body' });
    ['compact', 'cozy', 'comfortable'].forEach(d => {
        body.appendChild(el('button', {
            class: 'lg-button' + (d === cur ? ' primary' : ''),
            onclick: () => {
                document.body.setAttribute('data-density', d);
                lsSet('rkoj.density', d);
                renderDevtoolsBody(state.activeTab);
            },
        }, d));
    });
    wrap.appendChild(body);
    return wrap;
}

// Mount a template into a host + run its PaneRegistry handler (if any).
function mountTplInto(host, tplId, viewKey) {
    const tpl = $(tplId);
    if (!tpl) { host.appendChild(el('div', { class: 'empty-note' }, `template ${tplId} missing`)); return; }
    host.appendChild(tpl.content.cloneNode(true));
    const reg = PaneRegistry[viewKey];
    if (reg && reg.mount) try { reg.mount(host, state.paneState.agents, 'agents'); } catch (e) {}
    if (reg && reg.refresh) try { reg.refresh(host, state.paneState.agents, 'agents'); } catch (e) {}
}

function openDrawerTemplate(tplOrViewKey, label) {
    // Helper to ensure the dev-tools rail is open + reveals the named section.
    setDevtoolsRail(true, state.activeTab);
}

// ============================================================== DASHBOARD (preserved) ==
function renderProjects(host, projects) {
    const pane = bind(host, 'projects-pane'); if (!pane) return;
    pane.innerHTML = '';
    const pc = bind(host, 'projects-count'); if (pc) pc.textContent = `${projects.length} repo${projects.length === 1 ? '' : 's'}`;
    if (!projects.length) {
        pane.appendChild(el('div', { class: 'empty-note' }, 'no projects in registry'));
        return;
    }
    for (const p of projects) {
        const modeRow = el('div', { class: 'mode-row' });
        for (const m of MODES) {
            modeRow.appendChild(el('button', {
                class: 'mode-btn',
                title: `Launch ${p.display} in ${m} mode`,
                onclick: (ev) => { ev.stopPropagation(); launchProject(p.key, m); },
            }, m));
        }
        const card = el('div', {
            class: 'lg-card project-card',
            title: `Click to launch ${p.display} (dev mode)`,
            onclick: () => launchProject(p.key, 'dev'),
        },
            el('div', { class: 'title' }, p.display || p.key),
            el('div', { class: 'tag' }, p.tag || ''),
            el('div', { class: 'sub' }, p.root || ''),
            modeRow,
        );
        pane.appendChild(card);
    }
}

async function launchProject(projectKey, mode) {
    toast(`launching ${projectKey} :: ${mode}...`);
    const r = await fetchJson('/api/launch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project: projectKey, mode, no_notepad: true }),
    });
    if (r.ok) toast(`[OK] ${projectKey} launched (pid ${r.pid})`);
    else toast(`[FAIL] ${r.error || r.detail || 'unknown error'}`, true);
}

function renderSessions(host, sessions) {
    const pane = bind(host, 'sessions-pane'); if (!pane) return;
    pane.innerHTML = '';
    const onlineCount = sessions.filter(s => s.online).length;
    const sc = bind(host, 'sessions-count'); if (sc) sc.textContent = `${onlineCount}/${sessions.length} online`;
    if (!sessions.length) {
        pane.appendChild(el('div', { class: 'empty-note' }, 'no agents registered yet'));
        return;
    }
    sessions.sort((a, b) => (b.online ? 1 : 0) - (a.online ? 1 : 0));
    for (const s of sessions) {
        const head = el('div', { class: 'head' },
            el('div', null, el('span', { class: 'dot' }), el('strong', null, s.agent)),
            el('span', { class: `badge ${s.online ? 'online' : 'offline'}` }, s.online ? 'ONLINE' : 'offline'),
        );
        const lastSeen = el('div', { class: 'last-seen' }, `last seen ${s.last_seen_human || 'never'}`);
        const msgTail = el('div', { class: 'msg-tail' });
        if (s.inbox_tail && s.inbox_tail.length) {
            for (const m of s.inbox_tail.slice(-3)) {
                const body = m.message || '';
                msgTail.appendChild(el('div', { class: 'msg-line' },
                    el('span', { class: 'from' }, `${m.from || '?'}: `),
                    body.length > 80 ? body.slice(0, 80) + '...' : body,
                ));
            }
        } else {
            msgTail.appendChild(el('div', { class: 'msg-line' }, '(no recent inbox messages)'));
        }
        const input = el('input', { type: 'text', placeholder: `message ${s.agent}...` });
        const sendBtn = el('button', null, 'SEND');
        const sendRow = el('div', { class: 'send-row' }, input, sendBtn);
        const doSend = async () => {
            const body = input.value.trim();
            if (!body) return;
            sendBtn.disabled = true;
            const r = await fetchJson('/api/inbox/send', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ to: s.agent, body, sender: 'window-manager' }),
            });
            sendBtn.disabled = false;
            if (r.ok) { input.value = ''; toast(`[OK] message sent to ${s.agent}`); }
            else toast(`[FAIL] ${r.error || r.detail || 'send failed'}`, true);
        };
        sendBtn.addEventListener('click', doSend);
        input.addEventListener('keydown', (ev) => { if (ev.key === 'Enter') doSend(); });
        pane.appendChild(el('div', { class: `lg-card session-card ${s.online ? 'online' : ''}` }, head, lastSeen, msgTail, sendRow));
    }
}

function renderTrophy(host, t) {
    const set = (name, v) => { const n = bind(host, name); if (n) n.textContent = (v === null || v === undefined || v === '') ? '-' : v; };
    set('t-accts', t.accounts); set('t-videos', t.videos); set('t-active', t.active);
    set('t-pushes', t.pushes); set('t-banned', t.banned); set('t-devices', t.devices);
    const st = bind(host, 'trophy-status');
    if (st) {
        st.textContent = t.panel_online ? 'panel ONLINE' : 'panel offline';
        st.style.color = t.panel_online ? 'var(--success)' : 'var(--muted)';
    }
}

function renderRunlogs(host, rows) {
    const pane = bind(host, 'runlogs-pane'); if (!pane) return;
    pane.innerHTML = '';
    const rc = bind(host, 'runlogs-count'); if (rc) rc.textContent = `${rows.length}`;
    if (!rows.length) { pane.appendChild(el('div', { class: 'empty-note' }, 'no recent runlogs')); return; }
    for (const r of rows.slice(0, 8)) {
        const okCls = r.ok ? 'ok' : 'fail';
        const when = r.started ? r.started.slice(11, 19) : '--:--:--';
        pane.appendChild(el('div', { class: 'runlog-row', title: r.id },
            el('span', { class: okCls }, r.ok ? 'OK' : 'FAIL'),
            el('span', null, when),
            el('span', null, r.script || '?'),
        ));
    }
}

PaneRegistry.dashboard = {
    refresh: async (host) => {
        const [p, s, t, l] = await Promise.all([
            fetchJson('/api/projects'),
            fetchJson('/api/sessions'),
            fetchJson('/api/trophy'),
            fetchJson('/api/recent-runlogs'),
        ]);
        if (p.ok) renderProjects(host, p.projects || []);
        if (s.ok || s.sessions) renderSessions(host, s.sessions || []);
        if (t && t.ok !== false) renderTrophy(host, t);
        if (l.ok) renderRunlogs(host, l.runlogs || []);
    },
};

// ============================================================== PROGRESS (preserved) ==
function renderProgress(host, entries) {
    const pane = bind(host, 'progress-grid'); if (!pane) return;
    pane.innerHTML = '';
    const pc = bind(host, 'progress-count'); if (pc) pc.textContent = `${entries.length} entr${entries.length === 1 ? 'y' : 'ies'}`;
    if (!entries.length) { pane.appendChild(el('div', { class: 'empty-note' }, 'no progress logged yet - agents append to _shared-memory/PROGRESS/<agent>.md')); return; }
    for (const e of entries) {
        const card = el('div', { class: 'progress-card lg-card' },
            el('div', { class: 'head' },
                el('span', { class: 'agent' }, e.agent || '?'),
                el('span', { class: 'ts' }, e.ts || ''),
            ),
            el('div', null,
                el('span', { class: `status status-${(e.status || 'note').toLowerCase()}` }, e.status || 'note'),
                el('span', { class: 'title' }, e.title || ''),
            ),
            e.body ? el('div', { class: 'body' }, e.body) : null,
        );
        pane.appendChild(card);
    }
}

PaneRegistry.progress = {
    mount: (host) => {
        const btn = bind(host, 'prog-submit');
        if (btn) btn.addEventListener('click', async () => {
            const agent = bind(host, 'prog-agent').value.trim();
            const status = bind(host, 'prog-status').value;
            const title = bind(host, 'prog-title').value.trim();
            if (!agent || !title) { toast('agent + title required', true); return; }
            const r = await fetchJson('/api/progress/append', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ agent, status, title, body: '' }),
            });
            if (r.ok) { bind(host, 'prog-title').value = ''; toast(`[OK] logged for ${agent}`); PaneRegistry.progress.refresh(host); }
            else toast(`[FAIL] ${r.error || r.detail || 'append failed'}`, true);
        });
    },
    refresh: async (host) => {
        const r = await fetchJson('/api/progress?limit=60');
        if (r.ok) renderProgress(host, r.entries || []);
    },
};

// ============================================================== MEMORY (preserved) ==
PaneRegistry.memory = {
    mount: (host) => {
        const btn = bind(host, 'mem-submit');
        if (btn) btn.addEventListener('click', async () => {
            const target = bind(host, 'mem-target').value;
            const title = bind(host, 'mem-title').value.trim();
            const body = bind(host, 'mem-body').value;
            if (!title) { toast('title required', true); return; }
            const r = await fetchJson('/api/shared-memory/append', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ target, title, body }),
            });
            if (r.ok) { bind(host, 'mem-title').value = ''; bind(host, 'mem-body').value = ''; toast(`[OK] appended to ${target}`); PaneRegistry.memory.refresh(host); }
            else toast(`[FAIL] ${r.error || r.detail || 'append failed'}`, true);
        });
    },
    refresh: async (host) => {
        const r = await fetchJson('/api/shared-memory');
        if (r.ok) {
            const d = bind(host, 'mem-directives'); if (d) d.textContent = r.directives || '(empty)';
            const w = bind(host, 'mem-work');       if (w) w.textContent = r.work_toward || '(empty)';
        }
    },
};

// ============================================================== INBOX (preserved) ==
function renderInboxAgents(host, sessions, paneState) {
    const pane = bind(host, 'inbox-agents-list'); if (!pane) return;
    pane.innerHTML = '';
    const ac = bind(host, 'inbox-agent-count'); if (ac) ac.textContent = `${sessions.length}`;
    for (const s of sessions) {
        const row = el('div', {
            class: `inbox-agent-row ${paneState.selectedAgent === s.agent ? 'sel' : ''}`,
            onclick: () => { paneState.selectedAgent = s.agent; renderInboxAgents(host, sessions, paneState); loadInboxStream(host, paneState); },
        },
            el('span', { class: 'dot ' + (s.online ? 'on' : 'off') }, ''),
            el('span', null, s.agent),
            el('span', { class: 'ts' }, s.last_seen_human || 'never'),
        );
        pane.appendChild(row);
    }
}

async function loadInboxStream(host, paneState) {
    if (!paneState.selectedAgent) return;
    const t = bind(host, 'inbox-stream-title'); if (t) t.textContent = paneState.selectedAgent;
    const sb = bind(host, 'inbox-send-btn'); if (sb) sb.disabled = false;
    const r = await fetchJson(`/api/inbox/${encodeURIComponent(paneState.selectedAgent)}?limit=50`);
    const pane = bind(host, 'inbox-messages'); if (!pane) return;
    pane.innerHTML = '';
    const msgs = (r.messages || []);
    if (!msgs.length) { pane.appendChild(el('div', { class: 'empty-note' }, '(no messages)')); return; }
    for (const m of msgs) {
        pane.appendChild(el('div', { class: 'inbox-msg' },
            el('div', { class: 'inbox-msg-head' },
                el('span', { class: 'from' }, m.from || '?'),
                el('span', { class: 'ts' }, (m.ts || '').slice(11, 16)),
            ),
            el('div', { class: 'inbox-msg-body' }, m.message || ''),
        ));
    }
    pane.scrollTop = pane.scrollHeight;
}

PaneRegistry.inbox = {
    mount: (host, paneState) => {
        const sendBtn = bind(host, 'inbox-send-btn');
        const sendBody = bind(host, 'inbox-send-body');
        const refreshBtn = bind(host, 'inbox-refresh');
        if (sendBtn) sendBtn.addEventListener('click', async () => {
            if (!paneState.selectedAgent) return;
            const body = sendBody.value.trim();
            if (!body) return;
            const r = await fetchJson('/api/inbox/send', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ to: paneState.selectedAgent, body, sender: 'console' }),
            });
            if (r.ok) { sendBody.value = ''; toast(`[OK] sent to ${paneState.selectedAgent}`); loadInboxStream(host, paneState); }
            else toast(`[FAIL] ${r.error || r.detail || 'send failed'}`, true);
        });
        if (refreshBtn) refreshBtn.addEventListener('click', () => loadInboxStream(host, paneState));
        if (sendBody) sendBody.addEventListener('keydown', (e) => { if (e.key === 'Enter') sendBtn.click(); });

        // Author: Sinister Sanctum master agent (Claude) :: 2026-05-19 -- FleetState consolidation
        // Subscribe to FleetState so the agents-list pane on the left stays
        // live without an additional poll. Unsubscribe is stored on paneState
        // so a future unmount can drop the callback (popout cleanup, etc.).
        if (window.FleetState && typeof window.FleetState.subscribe === 'function') {
            paneState._fleetUnsub = window.FleetState.subscribe((snap) => {
                if (!snap || !Array.isArray(snap.sessions)) return;
                const sessions = snap.sessions.slice().sort((a, b) => (b.online ? 1 : 0) - (a.online ? 1 : 0));
                renderInboxAgents(host, sessions, paneState);
            });
        }
    },
    refresh: async (host, paneState) => {
        // Author: Sinister Sanctum master agent (Claude) :: 2026-05-19 -- FleetState consolidation
        // Prefer the cached FleetState snapshot; only fetch if it isn't loaded
        // (first render before SSE connects, or in sandboxed test runs).
        let sessions = null;
        if (window.FleetState && typeof window.FleetState.getSnapshot === 'function') {
            const snap = window.FleetState.getSnapshot();
            if (snap && Array.isArray(snap.sessions)) {
                sessions = snap.sessions.slice().sort((a, b) => (b.online ? 1 : 0) - (a.online ? 1 : 0));
            }
        }
        if (!sessions) {
            const r = await fetchJson('/api/sessions');
            if (r.ok || r.sessions) {
                sessions = (r.sessions || []).sort((a, b) => (b.online ? 1 : 0) - (a.online ? 1 : 0));
            }
        }
        if (sessions) {
            renderInboxAgents(host, sessions, paneState);
            if (paneState.selectedAgent) loadInboxStream(host, paneState);
        }
    },
};

// ============================================================== SETTINGS (preserved) ==
PaneRegistry.settings = {
    refresh: async (host) => {
        const r = await fetchJson('/api/connect-info');
        if (r.ok) {
            const mode = bind(host, 'conn-mode'); if (mode) mode.textContent = r.lan_mode ? 'LAN MODE ON' : 'loopback only';
            const ci = bind(host, 'conn-info'); if (ci) {
                ci.innerHTML = '';
                if (r.lan_mode) {
                    ci.appendChild(el('div', { class: 'conn-row' }, el('strong', null, 'LAN URL'), el('code', null, r.lan_url || '')));
                    ci.appendChild(el('div', { class: 'conn-row' }, el('strong', null, 'Mobile'), el('code', null, r.mobile_url || '')));
                    ci.appendChild(el('div', { class: 'conn-row' }, el('strong', null, 'Token'), el('code', null, r.token || '')));
                    ci.appendChild(el('img', { src: '/api/qr', class: 'qr-img', alt: 'phone scan QR' }));
                } else {
                    ci.appendChild(el('p', { class: 'hint' }, 'LAN mode is off. Boot with Sanctum-LAN.bat to enable.'));
                }
            }
        }
        const h = await fetchJson('/api/health');
        const sh = bind(host, 'sys-health');
        if (sh) {
            sh.innerHTML = '';
            if (h.ok) {
                sh.appendChild(el('div', { class: 'conn-row' }, el('strong', null, 'version'), el('code', null, h.version)));
                sh.appendChild(el('div', { class: 'conn-row' }, el('strong', null, 'port'), el('code', null, String(h.port))));
                sh.appendChild(el('div', { class: 'conn-row' }, el('strong', null, '_shared'), el('code', null, h.shared_ok ? 'OK' : 'FAIL')));
            }
        }
        const al = bind(host, 'acct-list'); if (al) al.innerHTML = '<p class="hint">edit accounts.json + activate slots to enable rotation.</p>';
        const ac = bind(host, 'acct-count'); if (ac) ac.textContent = '?';
        const pl = bind(host, 'prefs-list'); if (pl) pl.innerHTML = '<p class="hint">edit agent-prefs.json to change defaults per project.</p>';
        const pc = bind(host, 'prefs-count'); if (pc) pc.textContent = '?';
    },
};

// ============================================================== DEVICES (phones - preserved) ==
function _badgeFor(state) {
    const s = (state || '').toLowerCase();
    if (s === 'device') return { cls: 'online', text: 'ONLINE' };
    if (s === 'unauthorized') return { cls: 'warn', text: 'UNAUTHORIZED' };
    if (s === 'offline') return { cls: 'offline', text: 'OFFLINE' };
    if (s === 'recovery' || s === 'bootloader' || s === 'sideload') {
        return { cls: 'warn', text: s.toUpperCase() };
    }
    return { cls: 'offline', text: (state || 'unknown').toUpperCase() };
}

function _renderDeviceCard(host, d, paneState) {
    const isViewing = !!d.viewer_pid;
    const badge = _badgeFor(d.state);

    const card = el('div', {
        class: 'lg-card device-card' + (isViewing ? ' viewing' : ''),
        'data-serial': d.serial,
    });

    // Header: serial / model / state badge
    card.appendChild(el('div', { class: 'device-head' },
        el('div', { class: 'device-id' },
            el('span', { class: 'device-serial' }, d.serial),
            el('span', { class: 'device-model' }, d.model || d.device || '(unknown model)'),
        ),
        el('span', { class: `badge ${badge.cls}` }, badge.text),
    ));

    // Body: meta line(s)
    const metaBits = [];
    if (d.product) metaBits.push(`product: ${d.product}`);
    if (d.transport_id) metaBits.push(`transport: ${d.transport_id}`);
    if (isViewing) metaBits.push(`viewer pid: ${d.viewer_pid}`);
    if (metaBits.length) {
        card.appendChild(el('div', { class: 'device-meta' }, metaBits.join('  ·  ')));
    }

    // Actions row
    const actions = el('div', { class: 'device-actions' });

    const viewBtn = el('button', {
        class: 'btn-mini device-view',
        onclick: async () => {
            if (d.state !== 'device') {
                toast(`phone ${d.serial} not in 'device' state (state=${d.state})`, true);
                return;
            }
            viewBtn.disabled = true;
            const r = await fetchJson(`/api/devices/${encodeURIComponent(d.serial)}/view`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({}),
            });
            viewBtn.disabled = false;
            if (r.ok) {
                toast(`[OK] scrcpy launched for ${d.serial} (pid ${r.pid})`);
                refreshDevices(host, paneState);
            } else {
                toast(`[FAIL] ${r.error || r.detail || 'view failed'}`, true);
            }
        },
    }, 'VIEW');
    if (d.state !== 'device') viewBtn.disabled = true;
    actions.appendChild(viewBtn);

    if (isViewing) {
        const stopBtn = el('button', {
            class: 'btn-mini device-stop',
            onclick: async () => {
                stopBtn.disabled = true;
                const r = await fetchJson(`/api/devices/${encodeURIComponent(d.serial)}/stop`, {
                    method: 'POST',
                });
                stopBtn.disabled = false;
                if (r.ok) {
                    toast(`[OK] viewer stopped for ${d.serial}`);
                    refreshDevices(host, paneState);
                } else {
                    toast(`[FAIL] ${r.error || r.detail || 'stop failed'}`, true);
                }
            },
        }, 'STOP');
        actions.appendChild(stopBtn);
    }

    const notesBtn = el('button', {
        class: 'btn-mini device-notes-btn',
        onclick: async () => {
            const wrap = qs('.device-notes', card);
            if (!wrap) return;
            if (wrap.classList.contains('open')) {
                wrap.classList.remove('open');
                wrap.innerHTML = '';
                notesBtn.textContent = 'STATE NOTES';
                return;
            }
            wrap.classList.add('open');
            wrap.textContent = 'loading...';
            const r = await fetchJson(`/api/devices/${encodeURIComponent(d.serial)}/state`);
            wrap.innerHTML = '';
            if (r.ok && r.exists) {
                wrap.appendChild(el('div', { class: 'md-pre device-notes-pre' }, r.raw || '(empty)'));
            } else {
                wrap.appendChild(el('div', { class: 'empty-note' },
                    `no state notes yet at _shared-memory/notes/phones/${d.serial}.md`));
            }
            notesBtn.textContent = 'HIDE NOTES';
        },
    }, 'STATE NOTES');
    actions.appendChild(notesBtn);

    card.appendChild(actions);
    card.appendChild(el('div', { class: 'device-notes' }));
    return card;
}

async function refreshDevices(host, paneState) {
    const grid = bind(host, 'devices-grid');
    const countEl = bind(host, 'devices-count');
    const filterSel = bind(host, 'devices-lane-filter');
    const legend = bind(host, 'devices-lane-legend');
    if (!grid) {
        // Author: Sinister Sanctum master agent (Claude UI-redesign sub) :: 2026-05-19
        // The workstation shell's ADB pane uses `[data-bind="adb-grid"]` (not
        // `devices-grid`). When legacy callers fire refreshDevices(card, ...),
        // bounce to refreshAdbTab if the ADB pane is mounted.
        const adbPane = $('skel-adb');
        if (adbPane && bind(adbPane, 'adb-grid')) return refreshAdbTab(adbPane);
        return;
    }

    const r = await fetchJson('/api/devices');
    if (!r.ok) {
        grid.innerHTML = '';
        grid.appendChild(el('div', { class: 'empty-note' },
            `failed to list devices: ${r.error || 'unknown error'}`));
        if (countEl) countEl.textContent = 'error';
        return;
    }
    const devs = r.devices || [];
    const lanes = r.lanes || Array.from(new Set(devs.map(d => d.lane || 'unowned')));

    if (filterSel) {
        const wanted = paneState && paneState.laneFilter ? paneState.laneFilter : (filterSel.value || 'all');
        filterSel.innerHTML = '';
        filterSel.appendChild(el('option', { value: 'all' }, 'all'));
        lanes.forEach(ln => { filterSel.appendChild(el('option', { value: ln }, ln)); });
        filterSel.value = wanted;
        if (!filterSel._lf_wired) {
            filterSel.addEventListener('change', () => {
                if (paneState) paneState.laneFilter = filterSel.value;
                refreshDevices(host, paneState);
            });
            filterSel._lf_wired = true;
        }
    }
    if (legend) {
        legend.innerHTML = '';
        lanes.forEach(ln => { legend.appendChild(el('span', { class: `lane-chip ${_laneClassFor(ln)}` }, ln)); });
    }

    const lf = (filterSel && filterSel.value) || (paneState && paneState.laneFilter) || 'all';
    const filtered = lf === 'all' ? devs : devs.filter(d => (d.lane || 'unowned') === lf);

    if (countEl) countEl.textContent = `${filtered.length}/${devs.length} attached`;
    grid.innerHTML = '';
    if (!filtered.length) {
        grid.appendChild(el('div', { class: 'empty-note' },
            devs.length ? `no phones in lane '${lf}'` : 'no phones attached -- plug a phone in via USB and ensure ADB is authorized'));
        return;
    }
    filtered.forEach(d => { grid.appendChild(_renderDeviceCard(host, d, paneState || {})); });
}

PaneRegistry.phones = {
    mount: (host, paneState) => {
        const btn = bind(host, 'devices-refresh');
        if (btn) btn.addEventListener('click', () => refreshDevices(host, paneState));
        refreshDevices(host, paneState);
    },
    refresh: async (host, paneState) => { await refreshDevices(host, paneState); },
};

// ============================================================== SKILLS / TOOLS / INVENTIONS (preserved) ==
function _mkMdBrowser(kind) {
    const bindPrefix = kind;
    return {
        mount: (host, paneState) => {
            paneState[`${bindPrefix}Sel`] = paneState[`${bindPrefix}Sel`] || null;
        },
        refresh: async (host, paneState) => {
            const listEl = bind(host, `${bindPrefix}-list`);
            const countEl = bind(host, `${bindPrefix}-count`);
            if (!listEl) return;
            const r = await fetchJson(`/api/${bindPrefix}`);
            if (!r.ok) {
                listEl.innerHTML = '';
                listEl.appendChild(el('div', { class: 'empty-note' },
                    `failed to load ${bindPrefix}: ${r.error || 'unknown'}`));
                if (countEl) countEl.textContent = 'error';
                return;
            }
            const items = r.items || r[bindPrefix] || [];
            if (countEl) countEl.textContent = `${items.length}`;
            listEl.innerHTML = '';
            if (!items.length) {
                listEl.appendChild(el('div', { class: 'empty-note' }, `no ${bindPrefix} found`));
                return;
            }
            for (const it of items) {
                const slug = it.slug || it.name || '';
                const title = it.title || slug;
                const summary = it.summary || '';
                const row = el('div', {
                    class: `list-item ${paneState[`${bindPrefix}Sel`] === slug ? 'active' : ''}`,
                    'data-slug': slug,
                    onclick: () => _loadMdItem(host, paneState, bindPrefix, slug),
                },
                    el('div', { class: 'list-item-title' }, title),
                    summary ? el('div', { class: 'list-item-sub' },
                        summary.length > 80 ? summary.slice(0, 80) + '...' : summary) : null,
                );
                listEl.appendChild(row);
            }
            if (paneState[`${bindPrefix}Sel`]) {
                _loadMdItem(host, paneState, bindPrefix, paneState[`${bindPrefix}Sel`]);
            }
        },
    };
}

async function _loadMdItem(host, paneState, kind, slug) {
    paneState[`${kind}Sel`] = slug;
    qsa('.list-item', host).forEach(n => { n.classList.toggle('active', n.dataset.slug === slug); });
    const titleEl = bind(host, `${kind}-title`);
    const readerEl = bind(host, `${kind}-reader`);
    const metaEl = bind(host, `${kind}-meta`);
    if (titleEl) titleEl.textContent = slug;
    if (readerEl) readerEl.textContent = 'loading...';
    const r = await fetchJson(`/api/${kind}/${encodeURIComponent(slug)}`);
    if (!r.ok) {
        if (readerEl) readerEl.textContent = `failed to load: ${r.error || r.detail || 'unknown'}`;
        return;
    }
    const md = r.markdown || r.content || r.body || '';
    if (readerEl) readerEl.textContent = md || '(empty)';
    if (titleEl) titleEl.textContent = r.title || slug;
    if (metaEl) {
        if (r.mtime) {
            const d = new Date(r.mtime * 1000);
            metaEl.textContent = `updated ${d.toISOString().slice(0, 10)}`;
        } else { metaEl.textContent = ''; }
    }
}

PaneRegistry.skills = _mkMdBrowser('skills');
PaneRegistry.tools = _mkMdBrowser('tools');
PaneRegistry.inventions = _mkMdBrowser('inventions');

// ============================================================== CODEX (preserved) ==
function _renderCodexResult(host, r) {
    const card = bind(host, 'codex-result-card');
    const verdictEl = bind(host, 'codex-verdict');
    const summaryEl = bind(host, 'codex-summary');
    const findingsEl = bind(host, 'codex-findings');
    if (!card) return;
    card.style.display = '';
    const verdict = (r.verdict || 'warn').toLowerCase();
    if (verdictEl) { verdictEl.textContent = verdict.toUpperCase(); verdictEl.className = `codex-verdict ${verdict}`; }
    if (summaryEl) summaryEl.textContent = r.summary || '(no summary)';
    if (findingsEl) {
        findingsEl.innerHTML = '';
        const findings = r.findings || [];
        if (!findings.length) { findingsEl.appendChild(el('div', { class: 'empty-note' }, 'no findings')); }
        else {
            for (const f of findings) {
                const sev = (f.severity || 'info').toLowerCase();
                findingsEl.appendChild(el('div', { class: `codex-finding sev-${sev}` },
                    el('div', { class: 'codex-finding-head' },
                        el('span', { class: `codex-sev sev-${sev}` }, sev.toUpperCase()),
                        el('span', { class: 'codex-finding-title' }, f.title || f.message || '(untitled)'),
                    ),
                    f.detail ? el('div', { class: 'codex-finding-body' }, f.detail) : null,
                    f.line ? el('div', { class: 'codex-finding-loc' }, `line ${f.line}`) : null,
                ));
            }
        }
    }
}

async function _refreshCodexHistory(host) {
    const histEl = bind(host, 'codex-history');
    const countEl = bind(host, 'codex-history-count');
    if (!histEl) return;
    const r = await fetchJson('/api/codex/reviews');
    if (!r.ok) {
        histEl.innerHTML = '';
        histEl.appendChild(el('div', { class: 'empty-note' },
            `history unavailable: ${r.error || r.detail || 'endpoint not ready'}`));
        if (countEl) countEl.textContent = '-';
        return;
    }
    const items = (r.reviews || r.items || []).slice(0, 10);
    if (countEl) countEl.textContent = `${items.length}`;
    histEl.innerHTML = '';
    if (!items.length) { histEl.appendChild(el('div', { class: 'empty-note' }, 'no reviews yet')); return; }
    for (const it of items) {
        const v = (it.verdict || 'warn').toLowerCase();
        histEl.appendChild(el('div', { class: 'codex-history-row' },
            el('span', { class: `codex-verdict mini ${v}` }, v.toUpperCase()),
            el('span', { class: 'codex-history-summary' },
                (it.summary || it.title || '(no summary)').slice(0, 110)),
            el('span', { class: 'codex-history-ts' }, (it.ts || '').slice(0, 16)),
        ));
    }
}

PaneRegistry.codex = {
    mount: (host) => {
        const btn = bind(host, 'codex-submit');
        if (btn) btn.addEventListener('click', async () => {
            const code = bind(host, 'codex-code').value;
            if (!code.trim()) { toast('paste some code first', true); return; }
            const depth = bind(host, 'codex-depth').value;
            const language = bind(host, 'codex-language').value.trim() || 'auto';
            const context = bind(host, 'codex-context').value.trim();
            btn.disabled = true; btn.textContent = 'REVIEWING...';
            const r = await fetchJson('/api/codex/review', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code, depth, language, context }),
            });
            btn.disabled = false; btn.textContent = '[REVIEW]';
            if (r.ok === false) { toast(`[FAIL] ${r.error || r.detail || 'review failed'}`, true); return; }
            const result = r.review || r.result || r;
            _renderCodexResult(host, result);
            _refreshCodexHistory(host);
        });
    },
    refresh: async (host) => { await _refreshCodexHistory(host); },
};

// ============================================================== OPERATOR REQUESTS (preserved) ==
const _reqState = { filter: 'pending' };

async function refreshRequests(host) {
    const list = bind(host, 'req-list');
    const countEl = bind(host, 'req-count');
    if (!list) return;
    const r = await fetchJson(`/api/operator-requests?status=${_reqState.filter}`);
    if (!r.ok) {
        list.innerHTML = '';
        list.appendChild(el('div', { class: 'empty-note err' }, `[FAIL] ${r.error || 'fetch failed'}`));
        return;
    }
    const reqs = r.requests || [];
    if (countEl) countEl.textContent = `${reqs.length} ${_reqState.filter}`;
    list.innerHTML = '';
    if (!reqs.length) { list.appendChild(el('div', { class: 'empty-note' }, `(no ${_reqState.filter} requests)`)); return; }
    for (const req of reqs) {
        const urg = req.urgency || 'normal';
        const stat = req.status || 'pending';
        const card = el('div', { class: `req-card urg-${urg} stat-${stat}` });
        const head = el('div', { class: 'req-head' },
            el('span', { class: 'req-agent' }, req.agent || '?'),
            el('span', { class: `req-urgency urg-${urg}` }, urg.toUpperCase()),
            el('span', { class: 'req-ts' }, (req.ts || '').slice(0, 16)),
        );
        card.appendChild(head);
        card.appendChild(el('div', { class: 'req-title' }, req.title || '(no title)'));
        if (req.why) card.appendChild(el('div', { class: 'req-why' }, req.why));
        if (req.operator_reply) card.appendChild(el('div', { class: 'req-reply' }, '→ ' + req.operator_reply));

        if (stat === 'pending') {
            const replyInput = el('input', { type: 'text', placeholder: 'optional reply to agent...', class: 'req-reply-input' });
            const btnRow = el('div', { class: 'req-actions' });
            const decide = async (verdict) => {
                const body = JSON.stringify({ reply: replyInput.value || '' });
                const r = await fetchJson(`/api/operator-requests/${req.id}/${verdict}`, {
                    method: 'POST', headers: { 'Content-Type': 'application/json' }, body,
                });
                if (r.ok) { toast(`[OK] ${verdict} - agent notified`); refreshRequests(host); refreshAlertsCount(); }
                else { toast(`[FAIL] ${r.error || r.detail || 'decision failed'}`, true); }
            };
            btnRow.appendChild(el('button', { class: 'req-btn req-approve', onclick: () => decide('approve') }, '\u{1F44D} APPROVE'));
            btnRow.appendChild(el('button', { class: 'req-btn req-reply',   onclick: () => decide('reply')   }, '\u{1F4AC} REPLY ONLY'));
            btnRow.appendChild(el('button', { class: 'req-btn req-deny',    onclick: () => decide('deny')    }, '\u{1F44E} DENY'));
            card.appendChild(replyInput);
            card.appendChild(btnRow);
        }
        list.appendChild(card);
    }
}

PaneRegistry.requests = {
    mount: (host) => {
        qsa('.req-tab', host).forEach(t => t.addEventListener('click', () => {
            qsa('.req-tab', host).forEach(x => x.classList.remove('active'));
            t.classList.add('active');
            _reqState.filter = t.dataset.reqFilter || 'pending';
            refreshRequests(host);
        }));
        refreshRequests(host);
    },
    refresh: (host) => refreshRequests(host),
};

async function refreshAlertsCount() {
    const r = await fetchJson('/api/operator-requests?status=pending');
    const n = (r && r.requests) ? r.requests.length : 0;
    const badge = $('alerts-count');
    if (badge) {
        badge.textContent = n > 0 ? String(n) : '';
        badge.classList.toggle('show', n > 0);
    }
    const strip = $('alert-strip');
    if (strip) {
        strip.classList.toggle('hidden', n === 0);
        const tx = $('alert-text');
        if (tx) tx.textContent = n > 0 ? `⚠ ${n} operator request${n === 1 ? '' : 's'} pending - click to triage` : 'No alerts';
    }
}

// ============================================================== AGENT ACTIONS (intelligence popover - preserved) ==
const INTEL_MODELS = {
    'claude-opus-4-7':         'Opus 4.7',
    'claude-opus-4-6':         'Opus 4.6',
    'claude-sonnet-4-6':       'Sonnet 4.6',
    'claude-haiku-4-5-20251001': 'Haiku 4.5',
};

let _openAgentPopover = null;
function _closeAgentPopover() {
    if (_openAgentPopover && _openAgentPopover.parentNode) {
        _openAgentPopover.parentNode.removeChild(_openAgentPopover);
    }
    _openAgentPopover = null;
    document.removeEventListener('keydown', _agentPopoverEsc);
    document.removeEventListener('click', _agentPopoverOutside, true);
}
function _agentPopoverEsc(ev) { if (ev.key === 'Escape') _closeAgentPopover(); }
function _agentPopoverOutside(ev) {
    if (!_openAgentPopover) return;
    if (_openAgentPopover.contains(ev.target)) return;
    if (ev.target.closest && ev.target.closest('[data-agent-actions-trigger]')) return;
    _closeAgentPopover();
}

async function openAgentActions(agentName, anchorEl) {
    if (!agentName) return;
    _closeAgentPopover();
    const tpl = $('tpl-agent-actions');
    if (!tpl) { toast('agent-actions template missing', true); return; }
    const frag = tpl.content.cloneNode(true);
    const root = frag.firstElementChild;
    if (!root) return;
    qs('[data-bind="agent-name"]', root).textContent = agentName;

    // ----- last-applied badge (additive UI hint) :: 2026-05-19 -----
    // Surface the last per-agent intelligence apply (from localStorage) in the
    // popover header so the operator can see "you set this to Haiku 4.5 3m ago"
    // without re-checking the backend. Pure read; pure additive.
    const headerEl = qs('h4', root);
    if (headerEl) {
        try {
            const raw = localStorage.getItem('intel_last_applied_' + agentName);
            if (raw) {
                const meta = JSON.parse(raw);
                if (meta && meta.model && meta.applied_at) {
                    const label = INTEL_MODELS[meta.model] || meta.model;
                    const ageMs = Date.now() - meta.applied_at;
                    const mins = Math.max(0, Math.round(ageMs / 60000));
                    const ago = mins < 1 ? 'just now' : (mins < 60 ? `${mins} min ago` : `${Math.round(mins / 60)}h ago`);
                    const badge = el('span', {
                        class: 'intel-applied-ts',
                        style: 'display:block; font-size:11px; opacity:0.7; margin-top:4px; font-weight:normal;',
                        title: new Date(meta.applied_at).toLocaleString(),
                    }, `last set to ${label}${meta.fast ? ' (fast)' : ''} · ${ago}`);
                    headerEl.appendChild(badge);
                }
            }
        } catch (e) { /* ignore */ }
    }

    root.style.position = 'fixed';
    root.style.zIndex = '1100';
    document.body.appendChild(root);
    if (anchorEl && anchorEl.getBoundingClientRect) {
        const rect = anchorEl.getBoundingClientRect();
        const w = root.getBoundingClientRect().width || 320;
        let left = rect.left;
        if (left + w + 16 > window.innerWidth) left = Math.max(8, window.innerWidth - w - 16);
        root.style.left = left + 'px';
        root.style.top = (rect.bottom + 6) + 'px';
    } else {
        root.style.left = '50%';
        root.style.top = '20vh';
        root.style.transform = 'translateX(-50%)';
    }
    _openAgentPopover = root;
    document.addEventListener('keydown', _agentPopoverEsc);
    setTimeout(() => document.addEventListener('click', _agentPopoverOutside, true), 0);

    const radios = qsa('input[type="radio"][name="model"]', root);
    const fastInput = qs('input[type="checkbox"][name="fast"]', root);
    const applyBtn = qs('[data-bind="aa-apply"]', root);
    const cancelBtn = qs('[data-bind="aa-cancel"]', root);
    let initialModel = null, initialFast = false;
    try {
        const r = await fetchJson(`/api/agents/${encodeURIComponent(agentName)}/intelligence`);
        if (r && r.ok !== false) { initialModel = r.model || null; initialFast = !!r.fast; }
    } catch (e) {}
    if (initialModel) { for (const rd of radios) if (rd.value === initialModel) rd.checked = true; }
    if (fastInput) fastInput.checked = initialFast;

    const checkDirty = () => {
        const picked = radios.find(r => r.checked);
        const pickedModel = picked ? picked.value : null;
        const pickedFast = fastInput ? fastInput.checked : false;
        const dirty = pickedModel !== null && (pickedModel !== initialModel || pickedFast !== initialFast);
        if (applyBtn) applyBtn.disabled = !dirty;
    };
    checkDirty();
    for (const rd of radios) rd.addEventListener('change', checkDirty);
    if (fastInput) fastInput.addEventListener('change', checkDirty);

    if (cancelBtn) cancelBtn.addEventListener('click', _closeAgentPopover);
    if (applyBtn) applyBtn.addEventListener('click', async () => {
        const picked = radios.find(r => r.checked);
        if (!picked) return;
        const model = picked.value;
        const fast = fastInput ? !!fastInput.checked : false;
        applyBtn.disabled = true;
        applyBtn.textContent = 'applying...';
        const rr = await fetchJson(`/api/agents/${encodeURIComponent(agentName)}/intelligence`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model, fast }),
        });
        if (rr.ok) {
            const label = INTEL_MODELS[model] || model;
            // Persist for the last-applied badge on next open.
            try {
                localStorage.setItem(
                    'intel_last_applied_' + agentName,
                    JSON.stringify({ model, fast, applied_at: Date.now() })
                );
            } catch (e) { /* ignore storage failure */ }
            toast(`[OK] ${agentName} set to ${label}${fast ? ' (fast)' : ''} - applied next turn`);
            _closeAgentPopover();
        } else {
            applyBtn.disabled = false;
            applyBtn.textContent = 'Apply';
            toast(`[FAIL] ${rr.error || rr.detail || 'apply failed'}`, true);
        }
    });
}

function _mkIntelligenceButton(agentName) {
    return el('button', {
        class: 'lg-button agent-actions-trigger',
        title: 'set intelligence level for ' + agentName,
        'data-agent-actions-trigger': '1',
        onclick: (ev) => { ev.stopPropagation(); openAgentActions(agentName, ev.currentTarget); },
    }, '⚡ Intelligence');
}

// Re-wire renderSessions / renderInboxAgents so each session row gets the
// intelligence button (the prior shell wrapped them; we keep that contract).
const _origRenderSessions = renderSessions;
renderSessions = function (host, sessions) {
    _origRenderSessions(host, sessions);
    const pane = bind(host, 'sessions-pane');
    if (!pane) return;
    sessions.forEach((s, idx) => {
        const cards = qsa('.session-card', pane);
        const card = cards[idx];
        if (!card || card.querySelector('.agent-actions-trigger')) return;
        const row = el('div', { class: 'agent-actions-row' }, _mkIntelligenceButton(s.agent));
        card.appendChild(row);
    });
};

const _origRenderInboxAgents = renderInboxAgents;
renderInboxAgents = function (host, sessions, paneState) {
    _origRenderInboxAgents(host, sessions, paneState);
    const pane = bind(host, 'inbox-agents-list');
    if (!pane) return;
    const rows = qsa('.inbox-agent-row', pane);
    rows.forEach((row, idx) => {
        if (row.querySelector('.agent-actions-trigger')) return;
        const s = sessions[idx];
        if (!s) return;
        const btn = _mkIntelligenceButton(s.agent);
        btn.classList.add('inline-actions-btn');
        row.appendChild(btn);
    });
};

// ============================================================== COMMAND MENU (preserved) ==
PaneRegistry['command-menu'] = {
    mount: async (host) => {
        const select = bind(host, 'cm-agent');
        const refreshBtn = bind(host, 'cm-refresh');
        const intelBtn = bind(host, 'cm-intelligence');
        const countEl = bind(host, 'cm-count');

        const populate = async () => {
            const r = await fetchJson('/api/sessions');
            const sessions = (r && (r.sessions || [])).slice();
            sessions.sort((a, b) => (b.online ? 1 : 0) - (a.online ? 1 : 0));
            if (countEl) countEl.textContent = `${sessions.length} agents`;
            if (!select) return;
            const prev = select.value;
            select.innerHTML = '';
            if (!sessions.length) { select.appendChild(el('option', { value: '' }, '(no agents registered)')); return; }
            sessions.forEach(s => { select.appendChild(el('option', { value: s.agent }, `${s.agent}${s.online ? ' (online)' : ''}`)); });
            if (prev && Array.from(select.options).some(o => o.value === prev)) select.value = prev;
        };
        await populate();

        if (refreshBtn) refreshBtn.addEventListener('click', populate);
        if (intelBtn) intelBtn.addEventListener('click', (ev) => {
            const agent = select && select.value;
            if (!agent) { toast('pick an agent first', true); return; }
            openAgentActions(agent, ev.currentTarget);
        });
    },
    refresh: async (host) => {
        const r = await fetchJson('/api/sessions');
        const countEl = bind(host, 'cm-count');
        if (countEl) countEl.textContent = `${((r && r.sessions) || []).length} agents`;
    },
};

// ============================================================== LAUNCHER (preserved) ==
function _loadRecentLaunches() {
    try {
        const raw = localStorage.getItem(LS_RECENT_LAUNCHES);
        if (!raw) return [];
        const arr = JSON.parse(raw);
        return Array.isArray(arr) ? arr.slice(0, 10) : [];
    } catch (e) { return []; }
}
function _saveRecentLaunch(entry) {
    try {
        const list = _loadRecentLaunches();
        list.unshift(entry);
        localStorage.setItem(LS_RECENT_LAUNCHES, JSON.stringify(list.slice(0, 10)));
    } catch (e) {}
}

function _renderRecentLaunches(host) {
    const list = bind(host, 'recent-launches-list') || bind(host, 'lh-recent-list');
    const countEl = bind(host, 'lh-recent-count');
    if (!list) return;
    const entries = _loadRecentLaunches();
    if (countEl) countEl.textContent = String(entries.length);
    list.innerHTML = '';
    if (!entries.length) { list.appendChild(el('div', { class: 'empty-note' }, 'no launches yet')); return; }
    entries.forEach(e => {
        list.appendChild(el('div', { class: 'recent-launch-row' },
            el('span', { class: 'rl-time' }, (e.ts || '').slice(11, 16)),
            el('span', { class: 'rl-project' }, e.project || '?'),
            el('span', { class: 'rl-mode' }, '::'),
            el('span', { class: 'rl-mode' }, e.mode || '?'),
            e.fast ? el('span', { class: 'rl-fast' }, 'fast') : null,
            e.pid ? el('span', { class: 'rl-pid' }, `pid ${e.pid}`) : null,
        ));
    });
}

PaneRegistry.launcher = {
    mount: async (host) => {
        const projSel = bind(host, 'lh-project');
        const modeSel = bind(host, 'lh-mode');
        const fastCb  = bind(host, 'lh-fast');
        const prompt  = bind(host, 'lh-prompt');
        const launch  = bind(host, 'lh-launch');
        const statusEl = bind(host, 'lh-status');
        const fixBtn  = bind(host, 'lh-fix-memory');
        const trophy  = bind(host, 'lh-open-trophy');
        const phones  = bind(host, 'lh-open-phones');

        if (statusEl) statusEl.textContent = 'loading...';
        const r = await fetchJson('/api/launcher/options');
        if (!r.ok) {
            if (statusEl) statusEl.textContent = '[FAIL] options unavailable';
            toast(`[FAIL] launcher options: ${r.error || 'unknown'}`, true);
        } else {
            const projects = r.projects || [];
            const modes = r.modes || MODES;
            if (projSel) {
                projSel.innerHTML = '';
                if (!projects.length) { projSel.appendChild(el('option', { value: '' }, '(no projects in registry)')); }
                else {
                    projects.forEach(p => {
                        const key = typeof p === 'string' ? p : (p.key || p.id || p.name);
                        const label = typeof p === 'string' ? p : (p.display || p.label || key);
                        projSel.appendChild(el('option', { value: key }, label));
                    });
                }
            }
            if (modeSel) {
                modeSel.innerHTML = '';
                modes.forEach(m => {
                    const key = typeof m === 'string' ? m : (m.key || m.id || m.name);
                    const label = typeof m === 'string' ? m : (m.display || m.label || key);
                    modeSel.appendChild(el('option', { value: key }, label));
                });
            }
            if (statusEl) statusEl.textContent = 'ready';
        }

        _renderRecentLaunches(host);

        if (launch) launch.addEventListener('click', async () => {
            const project = projSel && projSel.value;
            const mode = modeSel && modeSel.value;
            if (!project || !mode) { toast('pick a project + mode first', true); return; }
            const body = { project, mode };
            if (fastCb && fastCb.checked) body.fast = true;
            const customPrompt = prompt && prompt.value && prompt.value.trim();
            if (customPrompt) body.custom_prompt = customPrompt;
            launch.disabled = true; launch.textContent = 'launching...';
            const rr = await fetchJson('/api/launcher/spawn', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
            launch.disabled = false; launch.textContent = '[LAUNCH]';
            if (rr.ok) {
                const pid = rr.pid || rr.PID || '';
                toast(`[OK] ${project} :: ${mode} spawned${pid ? ` (PID ${pid})` : ''}`);
                _saveRecentLaunch({ ts: new Date().toISOString(), project, mode, fast: !!body.fast, pid });
                _renderRecentLaunches(host);
            } else { toast(`[FAIL] ${rr.error || rr.detail || 'spawn failed'}`, true); }
        });

        if (fixBtn) fixBtn.addEventListener('click', async () => {
            let rr = await fetchJson('/api/fix-claude-memory', { method: 'POST' });
            if (rr.ok === false && (rr.error || '').match(/404|not.*found/i)) {
                rr = await fetchJson('/api/launch', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        project: 'fix-claude-memory', mode: 'overview',
                        bat_path: 'C:\\Users\\Zonia\\Desktop\\Fix-Claude-Memory.bat',
                    }),
                });
            }
            toast(rr.ok ? '[OK] FIX CLAUDE MEMORY launched' : `[FAIL] ${rr.error || rr.detail || 'launch failed'}`, !rr.ok);
        });
        if (trophy) trophy.addEventListener('click', () => activateTab('agents'));
        if (phones) phones.addEventListener('click', () => activateTab('devices'));
    },
    refresh: (host) => { _renderRecentLaunches(host); },
};

// ============================================================== PHONE PER-CARD EXTRAS (preserved) ==
const LANE_CLASSES = ['snap-emu', 'tiktok-emu', 'master', 'unowned'];
function _laneClassFor(lane) {
    const l = (lane || 'unowned').toLowerCase();
    if (LANE_CLASSES.indexOf(l) !== -1) return l;
    return 'unowned';
}

function _loadHistory(serial) {
    try {
        const raw = localStorage.getItem('adb_history_' + serial);
        if (!raw) return [];
        const arr = JSON.parse(raw);
        return Array.isArray(arr) ? arr.slice(0, 20) : [];
    } catch (e) { return []; }
}
function _saveHistory(serial, entries) {
    try { localStorage.setItem('adb_history_' + serial, JSON.stringify(entries.slice(0, 20))); } catch (e) {}
}
function _pushHistory(serial, entry) {
    const list = _loadHistory(serial);
    list.unshift(entry);
    _saveHistory(serial, list);
}
function _renderHistory(container, serial) {
    if (!container) return;
    container.innerHTML = '';
    const list = _loadHistory(serial);
    if (!list.length) { container.appendChild(el('div', { class: 'empty-note' }, 'no commands run yet')); return; }
    list.forEach(entry => {
        const ok = entry.ok !== false;
        const row = el('div', { class: 'cmd-history-entry' + (ok ? '' : ' err') });
        row.appendChild(el('div', { class: 'cmd-line' },
            el('span', { class: 'cmd-ts' }, (entry.ts || '').slice(11, 19)),
            el('span', null, ' '),
            el('span', { class: 'cmd-cmd' }, entry.cmd || ''),
        ));
        if (entry.stdout || entry.stderr || entry.rc !== undefined) {
            const out = (entry.stdout || '') + (entry.stderr ? '\n[stderr]\n' + entry.stderr : '');
            row.appendChild(el('div', { class: 'cmd-out' },
                (entry.rc !== undefined ? '(rc=' + entry.rc + ') ' : '') + (out || '(no output)')
            ));
        }
        container.appendChild(row);
    });
}

async function _execCmd(serial, cmd, container) {
    if (!cmd) return;
    const trimmed = cmd.trim();
    if (!trimmed) return;
    const ts = new Date().toISOString();
    const r = await fetchJson(`/api/devices/${encodeURIComponent(serial)}/exec`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cmd: trimmed }),
    });
    const entry = {
        ts, cmd: trimmed, ok: !!r.ok,
        rc: r.rc !== undefined ? r.rc : (r.returncode !== undefined ? r.returncode : null),
        stdout: r.stdout || '',
        stderr: r.stderr || (r.ok === false ? (r.error || r.detail || '') : ''),
    };
    _pushHistory(serial, entry);
    _renderHistory(container, serial);
    if (r.lane_warning) { toast(`[WARN] ${r.lane_warning}`, true); }
    else if (r.ok === false) { toast(`[FAIL] ${r.error || r.detail || 'exec failed'}`, true); }

    // Author: Sinister Sanctum master agent (Claude UI-redesign sub) :: 2026-05-19 — workstation sweep
    // Mirror into the rolling adbEvents buffer so the ADB tab's recent-events
    // card can list cross-device activity. Cap at 60 entries.
    try {
        const firstLine = (entry.stdout || entry.stderr || '').split('\n')[0] || '';
        state.adbEvents.unshift({ ts, serial, cmd: trimmed, ok: entry.ok, rc: entry.rc, line: firstLine });
        state.adbEvents = state.adbEvents.slice(0, 60);
        if (state.activeTab === 'adb') {
            const pane = $('skel-adb');
            if (pane) renderAdbEventsFeed(pane);
        }
    } catch (e) { /* non-fatal */ }
}

// RKOJ embedded screen viewer — Sinister Sanctum master agent (Claude) :: 2026-05-19
// Spawn an inline MJPEG <img> inside the phone card. No scrcpy popup — agents
// can see what's on the phone right inside RKOJ. Operator's spoofing handles
// any anti-detect concerns upstream, so this just consumes the raw stream.
function _renderEmbeddedScreen(serial, container) {
    // Reuse if already present — second click closes it (toggle).
    const existing = qs(`.embedded-screen-wrap[data-serial="${CSS.escape(serial)}"]`, container);
    if (existing) { existing.remove(); return; }

    const img = el('img', {
        class: 'embedded-screen',
        src: `/api/devices/${encodeURIComponent(serial)}/screen.mjpeg?fps=2`,
        alt: `screen of ${serial}`,
    });
    const wrap = el('div', { class: 'embedded-screen-wrap', 'data-serial': serial },
        el('div', { class: 'embedded-screen-header' },
            el('span', { class: 'mono' }, serial),
            el('button', {
                class: 'lg-button ghost',
                onclick: () => wrap.remove(),
            }, '✕ close'),
            el('button', {
                class: 'lg-button ghost',
                onclick: () => {
                    img.src = `/api/devices/${encodeURIComponent(serial)}/screen.mjpeg?fps=2&_=${Date.now()}`;
                },
            }, '⟳ reconnect'),
        ),
        img,
    );
    container.appendChild(wrap);
}
window.RkojHelpers = window.RkojHelpers || {};
window.RkojHelpers.renderEmbeddedScreen = _renderEmbeddedScreen;

// Wrap _renderDeviceCard to append per-card lane-chip + viewer-pill + cmd-input + history + push.
const _origRenderDeviceCard = _renderDeviceCard;
_renderDeviceCard = function (host, d, paneState) {
    const card = _origRenderDeviceCard(host, d, paneState);
    if (!card) return card;

    const lane = d.lane || 'unowned';
    const laneCls = _laneClassFor(lane);
    const meta = el('div', { class: 'device-extra-row' });
    meta.appendChild(el('span', { class: `lane-chip ${laneCls}` }, lane));
    const viewing = !!d.viewer_pid;
    meta.appendChild(el('span', { class: 'viewer-pill' + (viewing ? ' running' : '') },
        viewing ? '● viewer running' : '○ viewer idle'));
    if (d.battery !== undefined && d.battery !== null) {
        meta.appendChild(el('span', { class: 'lg-pill' }, `\u{1F50B} ${d.battery}%`));
    }
    if (d.attestation) meta.appendChild(el('span', { class: 'lg-pill' }, `att: ${d.attestation}`));
    if (d.proxy) meta.appendChild(el('span', { class: 'lg-pill' }, `proxy: ${d.proxy}`));

    const head = qs('.device-head', card);
    if (head && head.nextSibling) card.insertBefore(meta, head.nextSibling);
    else card.appendChild(meta);

    const histPane = el('div', { class: 'cmd-history' });
    _renderHistory(histPane, d.serial);

    const input = el('input', {
        class: 'cmd-input lg-input',
        type: 'text',
        placeholder: 'adb sub-command (e.g. shell pm list packages)',
    });
    const runBtn = el('button', {
        class: 'lg-button',
        onclick: async () => {
            const v = input.value;
            if (!v.trim()) return;
            runBtn.disabled = true;
            await _execCmd(d.serial, v, histPane);
            input.value = '';
            runBtn.disabled = false;
        },
    }, 'RUN');
    input.addEventListener('keydown', (ev) => {
        if (ev.key === 'Enter') { ev.preventDefault(); runBtn.click(); }
    });
    const cmdRow = el('div', { class: 'cmd-input-row' }, input, runBtn);

    const pushRow = el('div', { class: 'push-picker-row hidden' },
        el('input', { class: 'lg-input', type: 'text', 'data-bind': 'push-src', placeholder: 'src abs path' }),
        el('input', { class: 'lg-input', type: 'text', 'data-bind': 'push-dst', placeholder: 'dst path on phone' }),
        el('button', {
            class: 'lg-button',
            onclick: async () => {
                const src = qs('[data-bind="push-src"]', pushRow).value.trim();
                const dst = qs('[data-bind="push-dst"]', pushRow).value.trim();
                if (!src || !dst) { toast('src + dst required', true); return; }
                const rr = await fetchJson(`/api/devices/${encodeURIComponent(d.serial)}/push`, {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ file_path: src, dest_path: dst }),
                });
                toast(rr.ok ? `[OK] pushed to ${d.serial}` : `[FAIL] ${rr.error || rr.detail || 'push failed'}`, !rr.ok);
            },
        }, 'PUSH'),
    );

    const actions = qs('.device-actions', card);
    if (actions && !actions.querySelector('.device-push-toggle')) {
        const toggle = el('button', {
            class: 'btn-mini device-push-toggle',
            onclick: () => pushRow.classList.toggle('hidden'),
        }, 'PUSH');
        actions.appendChild(toggle);
    }

    // RKOJ embedded screen viewer — Sinister Sanctum master agent (Claude) :: 2026-05-19
    // Inline alternative to scrcpy's VIEW. Renders the phone's screen inside
    // the card (MJPEG stream). No popup window — agents can see the phone.
    if (actions && !actions.querySelector('.device-embed-btn')) {
        const embedBtn = el('button', {
            class: 'btn-mini device-embed-btn',
            title: 'render the phone screen inline (no scrcpy popup)',
            onclick: () => {
                if (d.state !== 'device') {
                    toast(`phone ${d.serial} not in 'device' state (state=${d.state})`, true);
                    return;
                }
                _renderEmbeddedScreen(d.serial, card);
            },
        }, 'EMBED SCREEN');
        if (d.state !== 'device') embedBtn.disabled = true;
        actions.appendChild(embedBtn);
    }

    // [popout] button per card.
    if (actions && !actions.querySelector('.device-popout-btn')) {
        const popBtn = el('button', {
            class: 'btn-mini device-popout-btn',
            title: 'pop this phone card out into its own window',
            onclick: () => {
                if (window.RkojPopout && window.RkojPopout.open) {
                    window.RkojPopout.open('phone-card', { serial: d.serial });
                } else { toast('popout not loaded', true); }
            },
        }, '↗');
        actions.appendChild(popBtn);
    }

    card.appendChild(cmdRow);
    card.appendChild(pushRow);
    card.appendChild(histPane);
    return card;
};

// ============================================================== SPAWNED WINDOWS (preserved) ==
const COMMAND_MENU = [
    { id: 'checkpoint',   label: '\u{1F4BE} Save checkpoint',         body: 'Save your current progress: write a checkpoint entry to PROGRESS/<your-name>.md (status: paused, title: "checkpoint at operator request"), commit any uncommitted work on your branch with message "checkpoint <date>", then return to waiting state.' },
    { id: 'summarize',    label: '\u{1F4CB} Summarize session so far', body: 'Pause + write a one-paragraph summary of what you have done this session, what is in flight, and what the next obvious step would be. Append it to PROGRESS/<your-name>.md as a "note" entry.' },
    { id: 'codex-review', label: '\u{1F50D} Request Codex review',     body: 'Pause + collect the latest uncommitted diff on your branch (git diff). POST it to /api/codex/review with depth=standard. Report the verdict + any high-severity findings back to the operator. Do NOT push if Codex returns fail or high-severity warn.' },
    { id: 'pr-desc',      label: '✍ Write PR description',    body: 'Pause + read `git log main..HEAD --oneline` + `git diff main...HEAD --stat`. Compose a PR description: 1-line summary, "What changed" bullets, "Why" paragraph, "Test plan" bullets. Append to PROGRESS/<your-name>.md.' },
    { id: 'switch-audit', label: '\u{1F6E1} Switch to audit mode',     body: 'Stop active development. Switch to audit posture: re-read your task brief, list everything you have changed, flag anything that touches auth/crypto/payment/secrets, and request operator approval before any further push.' },
    { id: 'grunt-mode',   label: '\u{1FA93} Grunt-task mode (cheap)',   body: 'Lower your effort to grunt-task posture. For the next series of small tasks (lint sweeps, formatter runs, file renames, code-search), delegate to Codex via /api/codex/review or to a local Ollama model where applicable. Save your premium thinking for the next architectural decision.' },
    { id: 'branch-now',   label: '\u{1F33F} Start a new agent branch', body: 'You are not yet on a per-agent branch. Create one named agent/<your-slugified-name>/<short-topic>, switch to it, and continue work there. Push to both origin and sanctum (sanctum-git mirror).' },
    { id: 'read-brain',   label: '\u{1F9E0} Re-scan the Sanctum brain', body: 'Pause + GET /api/knowledge?search=<topic-you-are-working-on>. If any topic matches with status=workaround or status=known-issue, apply the documented fix BEFORE continuing. Note in your progress log which topics applied.' },
    { id: 'inbox-poll',   label: '\u{1F4E8} Poll your inbox',           body: 'Pause + sinister-bus.inbox_poll my_agent="<your-SINISTER_AGENT_NAME>". Surface any operator-decision messages and act on them.' },
    { id: 'save-stop',    label: '\u{1F4BE}⛔ Save then STOP',           body: 'Final wrap-up: write a "paused" entry to PROGRESS/<your-name>.md summarizing where you are, commit any uncommitted work to your branch with message "save+stop <date>", then stop processing. Wait silently for operator to decide next move.' },
];

let _openCmdMenu = null;
function _closeCmdMenu() {
    if (_openCmdMenu && _openCmdMenu.parentNode) _openCmdMenu.parentNode.removeChild(_openCmdMenu);
    _openCmdMenu = null;
}
document.addEventListener('click', _closeCmdMenu);

function _showCmdMenu(anchorEl, pid, agent) {
    _closeCmdMenu();
    const rect = anchorEl.getBoundingClientRect();
    const menu = el('div', { class: 'cmd-menu' });
    for (const cmd of COMMAND_MENU) {
        menu.appendChild(el('div', {
            class: 'cmd-menu-item',
            onclick: async (ev) => {
                ev.stopPropagation();
                _closeCmdMenu();
                const r = await fetchJson(`/api/spawned-windows/${pid}/nudge`, {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ kind: 'custom', custom_body: cmd.body }),
                });
                toast(r.ok ? `[OK] "${cmd.label}" sent to ${agent}` : `[FAIL] ${r.error || r.detail}`, !r.ok);
            },
        }, cmd.label));
    }
    menu.style.left = Math.max(8, rect.left - 200) + 'px';
    menu.style.top = (rect.bottom + 4) + 'px';
    document.body.appendChild(menu);
    _openCmdMenu = menu;
    setTimeout(() => { menu.addEventListener('click', (e) => e.stopPropagation()); }, 0);
}

// Author: Sinister Sanctum master agent (Claude) :: 2026-05-19 -- FleetState consolidation
// Accepts an optional `windowsOverride` array (the FleetState snapshot path).
// If omitted, falls back to a direct fetch so manual refresh / popouts that
// don't have a snapshot in hand still work.
async function refreshSpawnedWindows(windowsOverride) {
    const bar = $('windows-bar');
    if (!bar) return;
    let wins;
    if (Array.isArray(windowsOverride)) {
        wins = windowsOverride;
    } else {
        const r = await fetchJson('/api/spawned-windows');
        wins = (r && r.windows) || [];
    }
    bar.innerHTML = '';
    if (!wins.length) {
        bar.appendChild(el('span', { class: 'hint', style: 'margin:0;' }, 'no Claude windows tracked yet - spawn from Agents tab'));
        return;
    }
    for (const w of wins) {
        const chip = el('div', { class: 'window-chip', title: `${w.agent} :: ${w.project} :: pid ${w.pid}` });
        chip.appendChild(el('span', { class: 'dot' }));
        chip.appendChild(el('span', { class: 'agent' }, w.agent));
        chip.appendChild(el('span', { style: 'color:var(--muted)' }, `· ${w.project_display || w.project}`));
        chip.appendChild(el('span', { style: 'color:var(--muted)' }, `· ${w.mode}`));

        const ctrls = el('div', { class: 'ctrls' });
        const mkCtrl = (icon, title, cls, fn) => el('button', {
            class: `ctrl ${cls}`, title, onclick: async (ev) => { ev.stopPropagation(); await fn(); },
        }, icon);

        ctrls.appendChild(mkCtrl('\u{1F441}', 'nudge: ask agent to check requests', '', async () => {
            const r = await fetchJson(`/api/spawned-windows/${w.pid}/nudge`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ kind: 'nudge' }),
            });
            toast(r.ok ? `[OK] nudged ${w.agent}` : `[FAIL] ${r.error || r.detail}`, !r.ok);
        }));
        ctrls.appendChild(mkCtrl('\u{1F4BE}', 'save & exit: agent wraps up cleanly', 'good', async () => {
            const r = await fetchJson(`/api/spawned-windows/${w.pid}/nudge`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ kind: 'save-exit' }),
            });
            toast(r.ok ? `[OK] save-exit sent to ${w.agent}` : `[FAIL] ${r.error || r.detail}`, !r.ok);
        }));
        ctrls.appendChild(mkCtrl('⛔', 'STOP: tell agent to stop immediately', 'warn', async () => {
            const r = await fetchJson(`/api/spawned-windows/${w.pid}/nudge`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ kind: 'stop' }),
            });
            toast(r.ok ? `[OK] STOP sent to ${w.agent}` : `[FAIL] ${r.error || r.detail}`, !r.ok);
        }));
        ctrls.appendChild(mkCtrl('✕', 'close: kill this Claude window (only)', 'danger', async () => {
            if (!confirm(`Kill the ${w.agent} window (pid ${w.pid})? This closes ONLY this window.`)) return;
            const r = await fetchJson(`/api/spawned-windows/${w.pid}/close`, { method: 'POST' });
            if (r.ok) { toast(`[OK] closed ${w.agent}`); setTimeout(refreshSpawnedWindows, 600); }
            else { toast(`[FAIL] ${r.error || r.detail}`, true); }
        }));
        const menuBtn = el('button', {
            class: 'ctrl', title: 'one-click commands menu',
            onclick: (ev) => { ev.stopPropagation(); _showCmdMenu(ev.target, w.pid, w.agent); },
        }, '⋯');
        ctrls.appendChild(menuBtn);

        chip.appendChild(ctrls);
        bar.appendChild(chip);
    }
}

// Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
// FleetState consolidation: replaces the 15s setInterval that polled
// /api/spawned-windows. The FleetState SSE feed emits a fresh snapshot every
// 5s and we re-render the windows bar from it. Falls back to a direct fetch
// the first time we paint if FleetState hasn't received its first event yet.
// 2026-05-19 master sweep: server emits the spawned-windows list under
// snap.spawned (matches _read_spawned_windows() shape). Prior staging used
// .windows; aligned both ends on .spawned here. The retired 15s setInterval
// is preserved below as a comment for grep-recovery.
if (window.FleetState && typeof window.FleetState.subscribe === 'function') {
    window.FleetState.subscribe((snap) => {
        if (!snap || !Array.isArray(snap.spawned)) return;
        try { refreshSpawnedWindows(snap.spawned); } catch (e) { /* noop */ }
    });
}
// setInterval(refreshSpawnedWindows, 15000);  // retired — replaced by FleetState above

// ============================================================== TAB INITIALIZERS ==
function initDevicesTab(pane, paneState) {
    const refreshBtn = bind(pane, 'devices-refresh');
    if (refreshBtn) refreshBtn.addEventListener('click', () => refreshDevices(pane, paneState));
    refreshDevices(pane, paneState);
    // device tab auto-refresh
    if (_deviceTimers.devices) clearInterval(_deviceTimers.devices);
    _deviceTimers.devices = setInterval(() => {
        if (state.activeTab !== 'devices') {
            clearInterval(_deviceTimers.devices);
            _deviceTimers.devices = null;
            return;
        }
        refreshDevices(pane, paneState);
    }, parseInt(lsGet('rkoj.devices.refresh_ms', String(DEVICE_REFRESH_MS)), 10));
}

function initAgentsTab(pane, paneState) {
    // Sessions strip render.
    refreshAgentsSessionsStrip(pane);

    // Launcher wizard wiring.
    wireAgentsLauncher(pane);

    // Recent launches.
    _renderRecentLaunches(pane);

    // Cycle points (delegate to cycle-points.js if loaded).
    const cpList = bind(pane, 'cycle-points-list');
    if (window.RkojCyclePoints && window.RkojCyclePoints.renderInto && cpList) {
        try { window.RkojCyclePoints.renderInto(cpList); } catch (e) {}
    }
    const cpNewBtn = qs('[data-act="new-cycle-point"]', pane);
    if (cpNewBtn) cpNewBtn.addEventListener('click', () => {
        if (window.RkojCyclePoints && window.RkojCyclePoints.openSaveModal) {
            window.RkojCyclePoints.openSaveModal();
        } else { toast('cycle-points.js not loaded', true); }
    });

    // Activity feed.
    refreshActivityFeed(pane);
}

// Author: Sinister Sanctum master agent (Claude) :: 2026-05-19 -- FleetState consolidation
// Accepts an optional `sessionsOverride` (the FleetState snapshot path). When
// omitted, falls back to a direct fetch so popouts/manual refresh keep working.
async function refreshAgentsSessionsStrip(pane, sessionsOverride) {
    const grid = bind(pane, 'agents-sessions-grid');
    const countEl = bind(pane, 'agents-sessions-count');
    if (!grid) return;
    let raw;
    if (Array.isArray(sessionsOverride)) {
        raw = sessionsOverride;
    } else {
        const r = await fetchJson('/api/sessions');
        raw = (r && r.sessions) || [];
    }
    const sessions = raw.slice().sort((a, b) => (b.online ? 1 : 0) - (a.online ? 1 : 0));
    if (countEl) countEl.textContent = `${sessions.filter(s => s.online).length}/${sessions.length} online`;
    grid.innerHTML = '';
    if (!sessions.length) {
        grid.appendChild(el('div', { class: 'empty-note' }, 'no agents registered yet'));
        return;
    }
    for (const s of sessions) {
        const head = el('div', { class: 'head' },
            el('div', null, el('span', { class: 'dot' }), el('strong', null, s.agent)),
            el('span', { class: `badge ${s.online ? 'online' : 'offline'}` }, s.online ? 'ONLINE' : 'offline'),
        );
        const actionsRow = el('div', { class: 'rkoj-session-actions' });
        actionsRow.appendChild(_mkIntelligenceButton(s.agent));
        actionsRow.appendChild(el('button', {
            class: 'lg-button',
            title: 'save cycle point for ' + s.agent,
            onclick: () => {
                if (window.RkojCyclePoints && window.RkojCyclePoints.openSaveModal) {
                    window.RkojCyclePoints.openSaveModal({ agent: s.agent });
                } else { toast('cycle-points.js not loaded', true); }
            },
        }, '\u{1F4BE} cycle point'));
        actionsRow.appendChild(el('button', {
            class: 'lg-button',
            title: 'popout sessions strip',
            onclick: () => {
                if (window.RkojPopout && window.RkojPopout.open) window.RkojPopout.open('session', { agent: s.agent });
                else toast('popout not loaded', true);
            },
        }, '↗ popout'));
        const card = el('div', { class: `lg-card session-card ${s.online ? 'online' : ''}` },
            head,
            el('div', { class: 'last-seen' }, `last seen ${s.last_seen_human || 'never'}`),
            actionsRow,
        );
        grid.appendChild(card);
    }
}

async function wireAgentsLauncher(pane) {
    const projSel = bind(pane, 'lh-project');
    const modeSel = bind(pane, 'lh-mode');
    const fastCb  = bind(pane, 'lh-fast');
    const prompt  = bind(pane, 'lh-prompt');
    const launchBtn = qs('[data-act="launch"]', pane);
    const fixBtn   = qs('[data-act="fix-claude-memory"]', pane);
    const trophyBtn = qs('[data-act="open-trophy"]', pane);
    const phonesBtn = qs('[data-act="open-phones"]', pane);

    const r = await fetchJson('/api/launcher/options');
    if (r.ok) {
        const projects = r.projects || [];
        const modes = r.modes || MODES;
        if (projSel) {
            projSel.innerHTML = '';
            if (!projects.length) { projSel.appendChild(el('option', { value: '' }, '(no projects in registry)')); }
            else projects.forEach(p => {
                const key = typeof p === 'string' ? p : (p.key || p.id || p.name);
                const label = typeof p === 'string' ? p : (p.display || p.label || key);
                projSel.appendChild(el('option', { value: key }, label));
            });
        }
        if (modeSel) {
            modeSel.innerHTML = '';
            modes.forEach(m => {
                const key = typeof m === 'string' ? m : (m.key || m.id || m.name);
                const label = typeof m === 'string' ? m : (m.display || m.label || key);
                modeSel.appendChild(el('option', { value: key }, label));
            });
        }
    }

    if (launchBtn) launchBtn.addEventListener('click', async () => {
        const project = projSel && projSel.value;
        const mode = modeSel && modeSel.value;
        if (!project || !mode) { toast('pick a project + mode first', true); return; }
        const body = { project, mode };
        if (fastCb && fastCb.checked) body.fast = true;
        const custom = prompt && prompt.value && prompt.value.trim();
        if (custom) body.custom_prompt = custom;
        launchBtn.disabled = true; launchBtn.textContent = 'launching...';
        const rr = await fetchJson('/api/launcher/spawn', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        launchBtn.disabled = false; launchBtn.textContent = '[LAUNCH]';
        if (rr.ok) {
            const pid = rr.pid || rr.PID || '';
            toast(`[OK] ${project} :: ${mode} spawned${pid ? ` (PID ${pid})` : ''}`);
            _saveRecentLaunch({ ts: new Date().toISOString(), project, mode, fast: !!body.fast, pid });
            _renderRecentLaunches(pane);
        } else { toast(`[FAIL] ${rr.error || rr.detail || 'spawn failed'}`, true); }
    });

    if (fixBtn) fixBtn.addEventListener('click', () => handleRibbonAction('fix-claude-memory'));
    if (trophyBtn) trophyBtn.addEventListener('click', () => openDrawerTemplate('dashboard', 'Trophy / Dashboard'));
    if (phonesBtn) phonesBtn.addEventListener('click', () => activateTab('devices'));
}

async function refreshActivityFeed(pane) {
    const list = bind(pane, 'activity-feed-list');
    if (!list) return;
    list.innerHTML = '';
    const merged = [];
    try {
        const p = await fetchJson('/api/progress?limit=15');
        if (p.ok) (p.entries || []).forEach(e => merged.push({
            ts: e.ts || '', kind: 'progress', agent: e.agent, title: e.title, status: e.status,
        }));
    } catch (e) {}
    try {
        const rq = await fetchJson('/api/operator-requests?status=pending');
        if (rq.ok) (rq.requests || []).forEach(r => merged.push({
            ts: r.ts || '', kind: 'request', agent: r.agent, title: r.title, status: 'pending',
        }));
    } catch (e) {}
    merged.sort((a, b) => (b.ts || '').localeCompare(a.ts || ''));
    if (!merged.length) { list.appendChild(el('div', { class: 'empty-note' }, 'no recent activity')); return; }
    merged.slice(0, 30).forEach(e => {
        list.appendChild(el('div', { class: 'activity-row' },
            el('span', { class: 'ts' }, (e.ts || '').slice(11, 16)),
            el('span', { class: `kind kind-${e.kind}` }, e.kind),
            el('span', { class: 'agent' }, e.agent || '?'),
            el('span', { class: 'title' }, (e.title || '').slice(0, 80)),
        ));
    });
}

// ============================================================== WORKSTATION SHELL WIRING ==
/* Author: Sinister Sanctum master agent (Claude UI-redesign sub) :: 2026-05-19 — workstation sweep
 * Wires the 3-row header: tabs (row 1), Excel-ribbon (row 2), KPI cards (row 3).
 * + Cmd+K palette + ESC handlers + popovers (window picker, settings drawer). */
function wireSkelShell() {
    // Top tabs (2 — ADB / AGENTS).
    qsa('.rkoj-tab').forEach(b => {
        b.addEventListener('click', () => setSkelTab(b.dataset.tab));
    });

    // ===== Row 1 icon strip =====
    const alertsBtn = $('hdr-alerts');
    if (alertsBtn) alertsBtn.addEventListener('click', () => {
        setDevtoolsRail(true, state.activeTab);
        toast('Operator requests drawer opened');
    });
    const bellBtn = $('hdr-bell');
    if (bellBtn) bellBtn.addEventListener('click', () => {
        setSkelTab('agents');
        // scroll to activity feed
        setTimeout(() => {
            const card = qs('.rkoj-activity-card');
            if (card) card.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 50);
    });
    const paletteBtn = $('hdr-palette');
    if (paletteBtn) paletteBtn.addEventListener('click', () => {
        if (window.RkojPalette && window.RkojPalette.open) window.RkojPalette.open();
        else toast('palette.js not loaded', true);
    });
    const newWinBtn = $('hdr-newwin');
    if (newWinBtn) newWinBtn.addEventListener('click', () => openNewWindowPicker(newWinBtn));
    const settingsBtn = $('hdr-settings');
    if (settingsBtn) settingsBtn.addEventListener('click', () => openSettingsDrawer(settingsBtn));

    // KPI cards — click navigation.
    const kpiPhones = $('kpi-card-phones');
    if (kpiPhones) kpiPhones.addEventListener('click', () => setSkelTab('adb'));
    const kpiAgents = $('kpi-card-agents');
    if (kpiAgents) kpiAgents.addEventListener('click', () => setSkelTab('agents'));
    const kpiVault = $('kpi-card-vault');
    if (kpiVault) kpiVault.addEventListener('click', () => { setSkelTab('agents'); openVaultDrawer(); });
    const kpiPending = $('kpi-card-pending');
    if (kpiPending) kpiPending.addEventListener('click', () => {
        setDevtoolsRail(true, 'agents');
        toast('Operator requests drawer opened');
    });

    // Dev-tools rail close.
    const closeBtn = $('devtools-close');
    if (closeBtn) closeBtn.addEventListener('click', () => setDevtoolsRail(false, state.activeTab));

    // Cmd+K / Ctrl+K -> palette.
    document.addEventListener('keydown', (ev) => {
        if ((ev.ctrlKey || ev.metaKey) && ev.key && ev.key.toLowerCase() === 'k') {
            ev.preventDefault();
            if (window.RkojPalette && window.RkojPalette.open) window.RkojPalette.open();
            else toast('palette.js not loaded', true);
        }
        // Alt+1 / Alt+2 — switch tabs.
        if (ev.altKey && (ev.key === '1' || ev.key === '2')) {
            ev.preventDefault();
            setSkelTab(ev.key === '1' ? 'adb' : 'agents');
        }
    });

    // Listen for palette-fired tab/drawer events (palette.js dispatches these).
    window.addEventListener('rkoj:switch-tab', (ev) => {
        const tab = ev && ev.detail && ev.detail.tab;
        if (tab) setSkelTab(tab);
    });
    window.addEventListener('rkoj:open-drawer', (ev) => {
        const d = ev && ev.detail || {};
        if (d.drawer) openDrawerTemplate(d.drawer, d.drawer);
    });
    window.addEventListener('rkoj:ribbon-action', (ev) => {
        const id = ev && ev.detail && ev.detail.id;
        if (id) handleRibbonAction(id);
    });

    // Expose `switchTab` on RkojHelpers so palette can call directly when loaded.
    if (window.RkojHelpers) window.RkojHelpers.switchTab = setSkelTab;

    // Render the ribbon row on the active tab.
    renderHeaderRibbon(state.activeTab);
}

// ============================================================== POPOVER HELPERS ==
function _showAnchoredPopover(anchorEl, tplId, onMount) {
    const tpl = $(tplId);
    if (!tpl) { toast(`template ${tplId} missing`, true); return; }
    // Strip any existing popover with same tplId.
    qsa(`[data-popover="${tplId}"]`).forEach(n => n.remove());
    const overlay = el('div', { class: 'rkoj-popover-overlay', 'data-popover': tplId });
    overlay.style.cssText = 'position:fixed;inset:0;z-index:9700;';
    const frag = tpl.content.cloneNode(true);
    const wrap = el('div', { class: 'rkoj-popover-wrap' });
    wrap.appendChild(frag);
    overlay.appendChild(wrap);
    document.body.appendChild(overlay);
    // Anchor: position popover just below anchorEl, right-edge aligned.
    const r = anchorEl.getBoundingClientRect();
    const popEl = wrap.firstElementChild;
    if (popEl) {
        popEl.style.position = 'fixed';
        popEl.style.top = (r.bottom + 8) + 'px';
        popEl.style.right = Math.max(8, window.innerWidth - r.right) + 'px';
        popEl.style.maxWidth = '360px';
    }
    const close = () => { try { overlay.remove(); } catch (e) {} };
    overlay.addEventListener('click', (ev) => { if (ev.target === overlay) close(); });
    overlay.querySelectorAll('[data-act="cancel"]').forEach(b => b.addEventListener('click', close));
    if (typeof onMount === 'function') onMount(overlay, close);
    document.addEventListener('keydown', function escClose(ev) {
        if (ev.key === 'Escape') { close(); document.removeEventListener('keydown', escClose); }
    });
}

function openNewWindowPicker(anchor) {
    _showAnchoredPopover(anchor, 'tpl-newwin-picker', (overlay, close) => {
        overlay.querySelectorAll('.rkoj-newwin-tile').forEach(t => {
            t.addEventListener('click', () => {
                const view = t.dataset.view;
                if (window.RkojPopout && window.RkojPopout.open) window.RkojPopout.open(view);
                else toast('popout module not loaded', true);
                close();
            });
        });
    });
}

function openSettingsDrawer(anchor) {
    _showAnchoredPopover(anchor, 'tpl-settings-drawer', (overlay, close) => {
        const densitySel = overlay.querySelector('[data-bind="set-density"]');
        if (densitySel) {
            densitySel.value = document.body.getAttribute('data-density') || 'cozy';
            densitySel.addEventListener('change', () => {
                document.body.setAttribute('data-density', densitySel.value);
                lsSet('rkoj.density', densitySel.value);
            });
        }
        const intelSel = overlay.querySelector('[data-bind="set-intel"]');
        if (intelSel) {
            const saved = lsGet('rkoj.default_intelligence', 'claude-opus-4-7');
            intelSel.value = saved;
            intelSel.addEventListener('change', () => lsSet('rkoj.default_intelligence', intelSel.value));
        }
        const hrCb = overlay.querySelector('[data-bind="set-hotreload"]');
        if (hrCb) {
            hrCb.checked = lsGet('rkoj.hot_reload', '1') === '1';
            hrCb.addEventListener('change', () => lsSet('rkoj.hot_reload', hrCb.checked ? '1' : '0'));
        }
        const dtBtn = overlay.querySelector('[data-act="open-devtools"]');
        if (dtBtn) dtBtn.addEventListener('click', () => { setDevtoolsRail(true, state.activeTab); close(); });
        const acctBtn = overlay.querySelector('[data-act="open-accounts"]');
        if (acctBtn) acctBtn.addEventListener('click', () => { openDrawerTemplate('settings', 'Settings'); close(); });
        const signOut = overlay.querySelector('[data-act="signout"]');
        if (signOut) signOut.addEventListener('click', () => {
            try { localStorage.removeItem('sinister_token'); } catch (e) {}
            location.reload();
        });
    });
}

// Back-compat shim — older code may still call wireRibbon().
function wireRibbon() { wireSkelShell(); }

// ============================================================== HERO KPI ROW ==
async function refreshSkelKpi() {
    const setNum = (key, v) => {
        const n = qs(`[data-bind="${key}"]`);
        if (n) n.textContent = (v === null || v === undefined || v === '') ? '—' : String(v);
    };
    const setKpiClass = (cardId, cls, on) => {
        const c = $(cardId); if (c) c.classList.toggle(cls, on);
    };
    // Phones online (filter for state='device').
    try {
        const r = await fetchJson('/api/devices');
        if (r && r.ok) {
            const devs = r.devices || [];
            state.devicesCache = devs;
            const online = devs.filter(d => (d.state || '').toLowerCase() === 'device').length;
            setNum('kpi-phones-online', online);
            setNum('kpi-phones-sub', `${devs.length} attached`);
            setNum('tab-adb-count', devs.length);
            setKpiClass('kpi-card-phones', 'is-good', online > 0);
        } else {
            setNum('kpi-phones-online', 0);
            setNum('kpi-phones-sub', '0 attached');
            setNum('tab-adb-count', 0);
        }
    } catch (e) { setNum('kpi-phones-online', 0); }
    // Agents online.
    try {
        const r = await fetchJson('/api/sessions');
        const sessions = (r && r.sessions) || [];
        state.sessionsCache = sessions;
        const online = sessions.filter(s => s.online).length;
        setNum('kpi-agents-online', online);
        setNum('kpi-agents-sub', `${sessions.length} registered`);
        setNum('tab-agents-count', online);
        setKpiClass('kpi-card-agents', 'is-good', online > 0);
    } catch (e) { setNum('kpi-agents-online', 0); }
    // Vault used.
    try {
        const r = await fetchJson('/api/vault/quota');
        if (r && !r.vault_offline && r.ok !== false) {
            const used = r.used_bytes || 0;
            const usedHuman = r.used_human || _fmtBytes(used);
            setNum('kpi-vault-used', usedHuman);
            const tooHigh = used > 950 * 1024 * 1024 * 1024;
            setKpiClass('kpi-card-vault', 'is-danger', tooHigh);
            setNum('kpi-vault-sub', tooHigh ? 'over soft quota!' : (r.free_human ? `${r.free_human} free` : '--'));
        } else {
            setNum('kpi-vault-used', 'offline');
            setNum('kpi-vault-sub', 'vault offline');
        }
    } catch (e) { setNum('kpi-vault-used', '—'); }
    // Pending requests (operator-actions + operator-requests).
    try {
        const r = await fetchJson('/api/operator-requests?status=pending');
        const n = (r && r.requests) ? r.requests.length : 0;
        setNum('kpi-pending', n);
        setNum('kpi-pending-sub', n > 0 ? 'agents need decisions' : 'none waiting');
        setKpiClass('kpi-card-pending', 'is-danger', n > 0);
    } catch (e) { setNum('kpi-pending', 0); }
}

function _fmtBytes(b) {
    if (!b) return '0 B';
    const u = ['B', 'KB', 'MB', 'GB', 'TB'];
    let i = 0;
    while (b >= 1024 && i < u.length - 1) { b /= 1024; i++; }
    return b.toFixed(b >= 100 ? 0 : 1) + ' ' + u[i];
}

// ==============================================================
// WORKSTATION TAB MOUNTERS — Sinister Sanctum master agent (Claude UI-redesign sub) :: 2026-05-19
// ==============================================================

// ====================================================================== HEADER RIBBON ==
// Excel-style action ribbon — 5 groups (VIEW / SPAWN / AGENT / AUTOMATE / MAINTAIN).
// Each tile is 18px icon + 14px label + tooltip + (optional) keyboard chip.
// Click dispatches to handleRibbonAction(); the per-tab tile groups stay stable
// but the active highlight flips to whichever tile maps to the current view.
function ribbonGroupsForHeader(tabId) {
    // Groups are stable; some tiles act on the active tab implicitly.
    return [
        { label: 'VIEW', tiles: [
            { icon: '⧉', label: 'Split',       action: 'split-view',       kbd: 'V' },
            { icon: '↗', label: 'Popout',      action: 'popout-current',   kbd: 'P' },
            { icon: '☰', label: 'Toggle rail', action: 'toggle-devtools',  kbd: 'D' },
            { icon: '≡', label: 'Layout',      action: 'layout-presets',   kbd: 'L' },
        ]},
        { label: 'SPAWN', tiles: [
            { icon: '+',       label: 'Agent',     action: 'spawn-agent',  kbd: 'A' },
            { icon: '↻',  label: 'Cycle',     action: 'cycle-resume', kbd: 'C' },
            { icon: '▦',  label: 'Window',    action: 'new-window',   kbd: 'W' },
            { icon: '✉',  label: 'Broadcast', action: 'broadcast',    kbd: 'B' },
        ]},
        { label: 'AGENT', tiles: [
            { icon: '⚡',  label: 'Intelligence', action: 'intelligence', kbd: 'I' },
            { icon: '♥',  label: 'Ping all',     action: 'ping-all',     kbd: 'H' },
            { icon: '⚑',  label: 'Codex review', action: 'codex-review', kbd: 'X' },
            { icon: '✉',  label: 'Inbox',        action: 'open-inbox',   kbd: 'M' },
        ]},
        { label: 'AUTOMATE', tiles: [
            { icon: '⏰',  label: 'Schedule',    action: 'scheduler',     kbd: 'S' },
            { icon: '▶',  label: 'Run script',  action: 'run-script',    kbd: 'R' },
            { icon: '✨',  label: 'Fix memory',  action: 'fix-claude-memory' },
            { icon: 'V',       label: 'Vault commit',action: 'vault-commit',  kbd: 'U' },
        ]},
        { label: 'MAINTAIN', tiles: [
            { icon: '⛒',  label: 'Build EXE',     action: 'build-rkoj' },
            { icon: '✱',  label: 'Health',        action: 'health-probe',    kbd: 'F' },
            { icon: '↻',  label: 'Restart',       action: 'restart-console' },
            { icon: '☰',  label: 'Logs',          action: 'view-logs' },
        ]},
    ];
}

function renderHeaderRibbon(tabId) {
    const row = $('rkoj-ribbon');
    if (!row) return;
    row.innerHTML = '';
    const groups = ribbonGroupsForHeader(tabId);
    groups.forEach((g, idx) => {
        if (idx > 0) row.appendChild(el('span', { class: 'rkoj-ribbon-sep' }));
        const groupEl = el('div', { class: 'rkoj-ribbon-grp', 'data-group': g.label });
        const tiles = el('div', { class: 'rkoj-ribbon-grp-tiles' });
        g.tiles.forEach(t => {
            const tile = el('button', {
                class: 'rkoj-ribbon-btn',
                title: t.label + (t.kbd ? ` (Alt+${t.kbd})` : ''),
                'data-action': t.action,
                onclick: () => handleRibbonAction(t.action),
            },
                el('span', { class: 'rkoj-ribbon-btn-ico' }, t.icon),
                el('span', { class: 'rkoj-ribbon-btn-lbl' }, t.label),
            );
            if (t.kbd) tile.appendChild(el('span', { class: 'rkoj-ribbon-btn-kbd' }, t.kbd));
            tiles.appendChild(tile);
        });
        groupEl.appendChild(tiles);
        groupEl.appendChild(el('div', { class: 'rkoj-ribbon-grp-lbl' }, g.label));
        row.appendChild(groupEl);
    });
}

// ====================================================================== ADB TAB ==
function mountAdbTab(pane) {
    const tpl = $('tpl-adb-workstation');
    if (!tpl) {
        pane.appendChild(el('div', { class: 'empty-note' }, 'tpl-adb-workstation missing'));
        return;
    }
    pane.appendChild(tpl.content.cloneNode(true));
    const aps = state.paneState.adb;

    // Wire toolbar actions — scope to the toolbar so device-card data-act
    // attributes don't double-bind.
    const toolbar = qs('.rkoj-adb-toolbar', pane);
    if (toolbar) qsa('[data-act]', toolbar).forEach(btn => {
        const act = btn.dataset.act;
        btn.addEventListener('click', async () => {
            switch (act) {
                case 'refresh': return refreshAdbTab(pane);
                case 'scan-all': {
                    const r = await fetchJson('/api/devices/scan-all', { method: 'POST' });
                    return toast(r.ok ? '[OK] scan dispatched' : `[FAIL] ${r.error || r.detail || 'unsupported'}`, !r.ok);
                }
                case 'push-to-lane':
                    return toast('push-to-lane: open a phone card -> PUSH (bulk push wires up next sweep)');
                case 'push-frida':
                    return toast('push-frida: open a phone card -> ACTIONS -> Push frida');
                case 'reboot-selected':
                    if (!confirm('Reboot every device in the active-lane filter?')) return;
                    return toast('reboot-selected: not implemented (would iterate device cards)');
            }
        });
    });

    refreshAdbTab(pane);

    // Periodic refresh while ADB tab is active. FleetState handles sessions/heartbeats,
    // but the /api/devices list is its own SSE-less endpoint, so we still poll here.
    if (_deviceTimers.devices) clearInterval(_deviceTimers.devices);
    _deviceTimers.devices = setInterval(() => {
        if (state.activeTab !== 'adb') {
            clearInterval(_deviceTimers.devices);
            _deviceTimers.devices = null;
            return;
        }
        refreshAdbTab(pane);
    }, parseInt(lsGet('rkoj.devices.refresh_ms', String(DEVICE_REFRESH_MS)), 10));
}

async function refreshAdbTab(pane) {
    const r = await fetchJson('/api/devices');
    const grid = bind(pane, 'adb-grid');
    const countEl = bind(pane, 'adb-count');
    const laneChips = bind(pane, 'adb-lane-chips');
    if (!grid) return;
    if (!r || !r.ok) {
        grid.innerHTML = '';
        grid.appendChild(el('div', { class: 'empty-note' }, `failed to list devices: ${(r && (r.error || r.detail)) || 'unknown'}`));
        if (countEl) countEl.textContent = 'error';
        return;
    }
    const devs = r.devices || [];
    state.devicesCache = devs;
    const lanes = r.lanes || Array.from(new Set(devs.map(d => d.lane || 'unowned')));
    const aps = state.paneState.adb;

    // Render lane filter chips (multi-select).
    if (laneChips) {
        laneChips.innerHTML = '';
        const allBtn = el('button', {
            class: 'lg-pill rkoj-lane-chip' + (aps.lanes.size === 0 ? ' lg-pill-active active' : ''),
            onclick: () => {
                aps.lanes.clear();
                refreshAdbTab(pane);
            },
        }, 'All');
        laneChips.appendChild(allBtn);
        lanes.forEach(ln => {
            const active = aps.lanes.has(ln);
            const chip = el('button', {
                class: 'lg-pill rkoj-lane-chip ' + _laneClassFor(ln) + (active ? ' lg-pill-active active' : ''),
                onclick: () => {
                    if (aps.lanes.has(ln)) aps.lanes.delete(ln);
                    else aps.lanes.add(ln);
                    refreshAdbTab(pane);
                },
            }, ln);
            laneChips.appendChild(chip);
        });
    }

    // Filter by selected lanes.
    const filtered = aps.lanes.size === 0
        ? devs
        : devs.filter(d => aps.lanes.has(d.lane || 'unowned'));

    if (countEl) countEl.textContent = `${filtered.length}/${devs.length} attached`;
    grid.innerHTML = '';
    if (!filtered.length) {
        grid.appendChild(el('div', { class: 'empty-note' },
            devs.length ? 'no phones match the selected lane(s)'
                        : 'no phones attached - plug a phone in via USB and ensure ADB is authorized'));
        return;
    }
    filtered.forEach(d => { grid.appendChild(_renderDeviceCard(pane, d, state.paneState.adb)); });

    // Recent ADB events feed (state.adbEvents — populated by _execCmd wrap).
    renderAdbEventsFeed(pane);
}

function renderAdbEventsFeed(pane) {
    const list = bind(pane, 'adb-events-list');
    if (!list) return;
    list.innerHTML = '';
    if (!state.adbEvents.length) {
        list.appendChild(el('div', { class: 'empty-note' },
            'no events yet — run a command on a device card to populate this feed'));
        return;
    }
    state.adbEvents.slice(0, 40).forEach(ev => {
        list.appendChild(el('div', { class: 'rkoj-adb-event' + (ev.ok ? '' : ' err') },
            el('span', { class: 'ev-ts' }, (ev.ts || '').slice(11, 19)),
            el('span', { class: 'ev-serial' }, ev.serial || '?'),
            el('span', { class: 'ev-cmd' }, ev.cmd || ''),
            el('span', { class: 'ev-line' }, (ev.line || '').slice(0, 120)),
        ));
    });
}

// ====================================================================== AGENTS TAB ==
function mountAgentsTab(pane) {
    const tpl = $('tpl-agents-workstation');
    if (!tpl) {
        pane.appendChild(el('div', { class: 'empty-note' }, 'tpl-agents-workstation missing'));
        return;
    }
    pane.appendChild(tpl.content.cloneNode(true));

    // 1. Launcher hero — project + mode chips + custom prompt + LAUNCH.
    wireLauncherHero(pane);
    _renderRecentLaunchesStrip(pane);

    // 2. Sessions strip (FleetState subscriber re-renders on every SSE tick).
    refreshAgentsSessionsStrip(pane);

    // 3. Activity feed.
    refreshActivityFeed(pane);

    // 4. Cycle points (delegate to cycle-points.js if loaded).
    const cpList = bind(pane, 'cycle-points-list');
    if (window.RkojCyclePoints && window.RkojCyclePoints.renderInto && cpList) {
        try { window.RkojCyclePoints.renderInto(cpList); } catch (e) {}
    }
    const cpNewBtn = qs('[data-act="new-cycle-point"]', pane);
    if (cpNewBtn) cpNewBtn.addEventListener('click', () => {
        if (window.RkojCyclePoints && window.RkojCyclePoints.openSaveModal) {
            window.RkojCyclePoints.openSaveModal();
        } else { toast('cycle-points.js not loaded', true); }
    });

    // 5. Schedule (next-N runs).
    const schNewBtn = qs('[data-act="new-schedule"]', pane);
    if (schNewBtn) schNewBtn.addEventListener('click', () => {
        if (window.RkojScheduler && window.RkojScheduler.openAddModal) {
            window.RkojScheduler.openAddModal();
        } else { setDevtoolsRail(true, 'agents'); toast('Scheduler drawer opened'); }
    });
    refreshScheduleCard(pane);

    // 6. Codex summary.
    const codexOpenBtn = qs('[data-act="open-codex"]', pane);
    if (codexOpenBtn) codexOpenBtn.addEventListener('click', () => {
        if (window.RkojCodexPane && window.RkojCodexPane.open) window.RkojCodexPane.open();
        else openDrawerTemplate('codex', 'Codex peer review');
    });
    refreshCodexSummaryCard(pane);

    // 7. Tile shelf (knowledge / vault / progress / catalog / daemons).
    wireTileShelf(pane);
    refreshTileShelf(pane);
}

// ----- launcher hero wiring (project select + mode chips + LAUNCH) -----
async function wireLauncherHero(pane) {
    const projSel = bind(pane, 'lh-project');
    const modeSel = bind(pane, 'lh-mode');
    const modeChips = bind(pane, 'lh-mode-chips');
    const fastCb = bind(pane, 'lh-fast');
    const prompt = bind(pane, 'lh-prompt');
    const launchBtn = qs('[data-act="launch"]', pane);

    const r = await fetchJson('/api/launcher/options');
    let projects = [];
    let modes = MODES;
    if (r && r.ok) {
        projects = r.projects || [];
        modes = r.modes || MODES;
    }

    if (projSel) {
        projSel.innerHTML = '';
        if (!projects.length) projSel.appendChild(el('option', { value: '' }, '(no projects in registry)'));
        else projects.forEach(p => {
            const key = typeof p === 'string' ? p : (p.key || p.id || p.name);
            const label = typeof p === 'string' ? p : (p.display || p.label || key);
            projSel.appendChild(el('option', { value: key }, label));
        });
    }

    // Mode chips (radio-style — click toggles active; mirror value into hidden select).
    if (modeChips) {
        modeChips.innerHTML = '';
        let activeMode = modes[0];
        if (typeof activeMode === 'object') activeMode = activeMode.key || activeMode.id || activeMode.name;
        modes.forEach(m => {
            const key = typeof m === 'string' ? m : (m.key || m.id || m.name);
            const label = typeof m === 'string' ? m : (m.display || m.label || key);
            const chip = el('button', {
                class: 'lg-pill rkoj-mode-chip' + (key === activeMode ? ' lg-pill-active active' : ''),
                'data-mode': key,
                onclick: () => {
                    qsa('.rkoj-mode-chip', modeChips).forEach(x => x.classList.remove('active', 'lg-pill-active'));
                    chip.classList.add('active', 'lg-pill-active');
                    if (modeSel) modeSel.value = key;
                },
            }, label);
            modeChips.appendChild(chip);
        });
        if (modeSel) {
            modeSel.innerHTML = '';
            modes.forEach(m => {
                const key = typeof m === 'string' ? m : (m.key || m.id || m.name);
                modeSel.appendChild(el('option', { value: key }, key));
            });
            modeSel.value = activeMode;
        }
    }

    if (launchBtn) launchBtn.addEventListener('click', async () => {
        const project = projSel && projSel.value;
        const mode = modeSel && modeSel.value;
        if (!project || !mode) { toast('pick a project + mode first', true); return; }
        const body = { project, mode };
        if (fastCb && fastCb.checked) body.fast = true;
        const custom = prompt && prompt.value && prompt.value.trim();
        if (custom) body.custom_prompt = custom;
        launchBtn.disabled = true;
        const orig = launchBtn.innerHTML;
        launchBtn.innerHTML = 'launching…';
        const rr = await fetchJson('/api/launcher/spawn', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        launchBtn.disabled = false;
        launchBtn.innerHTML = orig;
        if (rr.ok) {
            const pid = rr.pid || rr.PID || '';
            toast(`[OK] ${project} :: ${mode} spawned${pid ? ` (PID ${pid})` : ''}`);
            _saveRecentLaunch({ ts: new Date().toISOString(), project, mode, fast: !!body.fast, pid });
            _renderRecentLaunchesStrip(pane);
        } else { toast(`[FAIL] ${rr.error || rr.detail || 'spawn failed'}`, true); }
    });
}

// Recent launches strip (max 5 mini-cards — click to re-launch with same params).
function _renderRecentLaunchesStrip(pane) {
    const strip = bind(pane, 'recent-launches-strip');
    if (!strip) return;
    const entries = _loadRecentLaunches().slice(0, 5);
    strip.innerHTML = '';
    if (!entries.length) {
        strip.appendChild(el('span', { class: 'rkoj-recent-empty muted' }, 'no recent launches'));
        return;
    }
    strip.appendChild(el('span', { class: 'rkoj-recent-label muted' }, 'recent:'));
    entries.forEach(e => {
        const chip = el('button', {
            class: 'lg-pill rkoj-recent-chip',
            title: `re-launch ${e.project} :: ${e.mode}${e.fast ? ' (fast)' : ''}`,
            onclick: async () => {
                const body = { project: e.project, mode: e.mode };
                if (e.fast) body.fast = true;
                const rr = await fetchJson('/api/launcher/spawn', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body),
                });
                if (rr.ok) {
                    toast(`[OK] re-launched ${e.project} :: ${e.mode}`);
                    _saveRecentLaunch({ ts: new Date().toISOString(), project: e.project, mode: e.mode, fast: !!e.fast, pid: rr.pid });
                    _renderRecentLaunchesStrip(pane);
                } else { toast(`[FAIL] ${rr.error || rr.detail || 'spawn failed'}`, true); }
            },
        },
            el('span', { class: 'rkoj-recent-project' }, e.project || '?'),
            el('span', { class: 'muted' }, '::'),
            el('span', null, e.mode || '?'),
            e.fast ? el('span', { class: 'rkoj-recent-fast' }, 'fast') : null,
        );
        strip.appendChild(chip);
    });
}

// ----- schedule card (next runs) -----
async function refreshScheduleCard(pane) {
    const list = bind(pane, 'schedule-list');
    if (!list) return;
    list.innerHTML = '';
    const r = await fetchJson('/api/schedule');
    const items = (r && r.entries) || (r && r.schedule) || [];
    if (!items.length) { list.appendChild(el('div', { class: 'empty-note' }, 'no scheduled jobs')); return; }
    items.slice(0, 6).forEach(s => {
        const next = s.next_run_human || s.next_run || s.next || '--';
        const row = el('div', { class: 'rkoj-schedule-row' },
            el('div', { class: 'rkoj-schedule-name' }, s.name || s.id || '(unnamed)'),
            el('div', { class: 'muted' }, `${s.kind || ''} @ ${s.cron || ''}`),
            el('div', { class: 'rkoj-schedule-next' }, `next: ${next}`),
            el('button', {
                class: 'lg-button ghost btn-mini',
                onclick: async () => {
                    const rr = await fetchJson(`/api/schedule/${encodeURIComponent(s.id || s.slug)}/run-now`, { method: 'POST' });
                    toast(rr && rr.ok ? `[OK] running ${s.name}` : `[FAIL] ${(rr && (rr.error || rr.detail)) || 'run failed'}`, !(rr && rr.ok));
                },
            }, 'run now'),
        );
        list.appendChild(row);
    });
}

// ----- codex summary card -----
async function refreshCodexSummaryCard(pane) {
    const list = bind(pane, 'codex-summary-list');
    if (!list) return;
    list.innerHTML = '';
    const r = await fetchJson('/api/codex/reviews?limit=5');
    const items = (r && r.reviews) || (r && r.entries) || [];
    if (!items.length) { list.appendChild(el('div', { class: 'empty-note' }, 'no recent reviews')); return; }
    items.slice(0, 5).forEach(c => {
        const v = (c.verdict || 'unknown').toLowerCase();
        list.appendChild(el('div', { class: 'rkoj-codex-row' },
            el('span', { class: `rkoj-codex-verdict v-${v}` }, v.toUpperCase()),
            el('div', { class: 'rkoj-codex-text' },
                el('div', { class: 'rkoj-codex-summary-line' }, (c.summary || c.title || c.id || '').slice(0, 110)),
                el('div', { class: 'muted' }, (c.ts || '').slice(0, 16) + ' · ' + (c.depth || '')),
            ),
        ));
    });
}

// ----- tile shelf wiring -----
function wireTileShelf(pane) {
    qsa('.rkoj-tile', pane).forEach(t => {
        t.addEventListener('click', () => {
            const which = t.dataset.tile;
            switch (which) {
                case 'knowledge':
                    return openDrawerTemplate('skills', 'Knowledge / Skills');
                case 'vault':
                    return openVaultDrawer();
                case 'progress':
                    return openDrawerTemplate('progress', 'Progress');
                case 'catalog':
                    return openDrawerTemplate('tools', 'Tools / Skills / Inventions');
                case 'daemons':
                    return toast('daemon liveness in windows bar (bottom).');
            }
        });
    });
}

function openVaultDrawer() {
    setDevtoolsRail(true, 'agents');
    // Vault section is the last in devtoolsSectionsForAgents; expand it.
    setTimeout(() => {
        const body = $('devtools-body');
        if (!body) return;
        const vaultSection = qsa('details.rkoj-devtools-section', body).pop();
        if (vaultSection) vaultSection.open = true;
    }, 50);
}

async function refreshTileShelf(pane) {
    // Knowledge: count of brain topics.
    try {
        const r = await fetchJson('/api/knowledge');
        const items = (r && (r.topics || r.entries || r.knowledge)) || [];
        const cnt = bind(pane, 'tile-knowledge-count');
        if (cnt) cnt.textContent = String(items.length || 0);
    } catch (e) { /* leave -- */ }
    // Vault: quota meter + last commit.
    try {
        const r = await fetchJson('/api/vault/quota');
        const used = bind(pane, 'tile-vault-used');
        if (used) used.textContent = (r && r.used_human) || (r && r.used_bytes ? _fmtBytes(r.used_bytes) : '--');
        const audit = await fetchJson('/api/vault/audit');
        const last = bind(pane, 'tile-vault-last');
        const entries = (audit && (audit.entries || audit.audit || audit.commits)) || [];
        if (last) last.textContent = entries.length ? (entries[0].message || entries[0].title || 'last commit').slice(0, 36) : '--';
    } catch (e) { /* leave -- */ }
    // Progress: count + last title.
    try {
        const r = await fetchJson('/api/progress?limit=3');
        const entries = (r && r.entries) || [];
        const cnt = bind(pane, 'tile-progress-count');
        if (cnt) cnt.textContent = entries.length ? String(entries.length) : '--';
        const last = bind(pane, 'tile-progress-last');
        if (last) last.textContent = entries.length ? (entries[0].title || '').slice(0, 36) : '--';
    } catch (e) { /* leave -- */ }
    // Catalog: skills + tools + inventions combined.
    try {
        const [s, t, i] = await Promise.all([
            fetchJson('/api/skills'),
            fetchJson('/api/tools'),
            fetchJson('/api/inventions'),
        ]);
        const sn = ((s && (s.items || s.skills)) || []).length;
        const tn = ((t && (t.items || t.tools)) || []).length;
        const iN = ((i && (i.items || i.inventions)) || []).length;
        const cnt = bind(pane, 'tile-catalog-count');
        if (cnt) cnt.textContent = String(sn + tn + iN);
    } catch (e) { /* leave -- */ }
    // Daemons: dots reflect FleetState heartbeats (mirrors windows-bar indicator).
    try {
        const snap = window.FleetState && window.FleetState.getSnapshot ? window.FleetState.getSnapshot() : null;
        if (snap && snap.heartbeats) {
            ['sanctum-console', 'sinister-vault', 'rkoj'].forEach(slug => {
                const hb = snap.heartbeats[slug];
                const dot = qs(`.rkoj-daemon-dot[data-daemon="${slug}"]`, pane);
                if (dot) {
                    dot.style.background = (hb && hb.alive) ? 'var(--success)' : 'var(--danger)';
                    dot.title = `${slug}: ` + ((hb && hb.alive) ? `alive (age ${hb.age_s}s)` : 'stale or missing');
                }
            });
        }
    } catch (e) { /* leave -- */ }
}

// ============================================================== EXPOSE GLOBALS ==
// So popout.js / palette.js / cycle-points.js / scheduler.js can reuse helpers.

/* Cross-agent broadcast helper — Sinister Sanctum master agent (Claude) :: 2026-05-19
 * Per DIRECTIVES.md (2026-05-19 — CROSS-AGENT COORDINATION): agents that
 * discover fleet-relevant info should fan it out to every online agent in
 * one call. Wraps POST /api/inbox/broadcast.
 */
async function broadcastToAllAgents(body, tags = [], from_agent = "operator", exclude = []) {
    if (!body || !String(body).trim()) {
        toast('[FAIL] broadcast: body required', true);
        return { ok: false, error: 'body required' };
    }
    const r = await fetchJson('/api/inbox/broadcast', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ body, tags, from_agent, exclude }),
    });
    if (r && r.ok) toast(`[OK] broadcast to ${r.count} agent(s)`, false);
    else toast(`[FAIL] broadcast: ${(r && (r.error || r.detail)) || 'unknown'}`, true);
    return r;
}

// Ensure tpl-broadcast-modal exists in the DOM (injected lazily so we
// don't need to edit index.html). Idempotent.
function _ensureBroadcastModalTemplate() {
    if (document.getElementById('tpl-broadcast-modal')) return;
    const tpl = document.createElement('template');
    tpl.id = 'tpl-broadcast-modal';
    tpl.innerHTML = `
        <div class="lg-popover rkoj-modal">
            <h3>Broadcast to all online agents</h3>
            <p style="margin:0 0 8px 0;color:var(--text-muted,#aaa);font-size:.85em;">
                Fan-out one message to every online agent. Lead with <code>[DISCOVERY]</code> / <code>[ASK]</code> etc.
                per the 2026-05-19 cross-agent coordination rule.
            </p>
            <label>Message
                <textarea class="lg-textarea" data-bind="bcast-body" rows="5"
                    placeholder="[DISCOVERY] Yurikey52 cert rotated. Phone-stack agents can resume."></textarea>
            </label>
            <label>Tags (comma-separated)
                <input class="lg-input" data-bind="bcast-tags"
                    placeholder="cross-agent, discovery" value="cross-agent, broadcast">
            </label>
            <label>From
                <input class="lg-input" data-bind="bcast-from" placeholder="operator" value="operator">
            </label>
            <label>Exclude (comma-separated agent names)
                <input class="lg-input" data-bind="bcast-exclude" placeholder="(none)">
            </label>
            <div class="popover-actions">
                <button class="lg-button ghost" data-act="cancel">Cancel</button>
                <button class="lg-button primary" data-act="send">Send</button>
            </div>
        </div>
    `;
    document.body.appendChild(tpl);
}

// Open the broadcast modal (tpl-broadcast-modal lazily injected).
function openBroadcastModal() {
    _ensureBroadcastModalTemplate();
    const tpl = document.getElementById('tpl-broadcast-modal');
    if (!tpl) { toast('broadcast modal template missing', true); return; }
    // Backdrop overlay matches cycle-points.js modal pattern.
    const overlay = el('div', { class: 'rkoj-modal-overlay' });
    overlay.style.cssText = 'position:fixed;inset:0;z-index:9800;display:flex;align-items:center;justify-content:center;background:rgba(8,8,14,.55);backdrop-filter:blur(6px);';
    const frag = tpl.content.cloneNode(true);
    const wrap = document.createElement('div');
    wrap.appendChild(frag);
    overlay.appendChild(wrap);
    document.body.appendChild(overlay);

    const close = () => { try { overlay.remove(); } catch (e) { /* noop */ } };
    const bodyEl = overlay.querySelector('[data-bind="bcast-body"]');
    const tagsEl = overlay.querySelector('[data-bind="bcast-tags"]');
    const fromEl = overlay.querySelector('[data-bind="bcast-from"]');
    const excludeEl = overlay.querySelector('[data-bind="bcast-exclude"]');
    if (bodyEl) bodyEl.focus();
    overlay.querySelectorAll('[data-act="cancel"]').forEach(b => b.addEventListener('click', close));
    overlay.addEventListener('click', (ev) => { if (ev.target === overlay) close(); });
    const sendBtn = overlay.querySelector('[data-act="send"]');
    if (sendBtn) sendBtn.addEventListener('click', async () => {
        const body = bodyEl ? bodyEl.value : '';
        const tags = (tagsEl && tagsEl.value)
            ? tagsEl.value.split(',').map(s => s.trim()).filter(Boolean)
            : ['cross-agent', 'broadcast'];
        const from_agent = (fromEl && fromEl.value.trim()) || 'operator';
        const exclude = (excludeEl && excludeEl.value)
            ? excludeEl.value.split(',').map(s => s.trim()).filter(Boolean)
            : [];
        const r = await broadcastToAllAgents(body, tags, from_agent, exclude);
        if (r && r.ok) close();
    });
}

window.RkojHelpers = {
    $, qs, qsa, el, toast, fetchJson, _authHeaders,
    openAgentActions, _mkIntelligenceButton,
    PaneRegistry, mountTplInto,
    activateTab,
    state,
    INTEL_MODELS, MODES,
    // Cross-agent coordination (2026-05-19 standing rule).
    broadcastToAllAgents, openBroadcastModal,
    /* Panel-style redesign — Sinister Sanctum master agent (Claude) :: 2026-05-19 */
    setSkelTab, setSkelNav, refreshSkelKpi,
    mountAdbTab, mountAgentsTab, renderHeaderRibbon, refreshAdbTab,
    // Back-compat shims — older popouts/palette commands still call these names.
    mountSkelFleet: mountAdbTab, mountSkelAgents: mountAgentsTab,
};

// ============================================================== BOOTSTRAP ==
/* Panel-style redesign — Sinister Sanctum master agent (Claude) :: 2026-05-19 */
async function bootstrap() {
    wireSkelShell();
    // Restore density.
    const density = lsGet('rkoj.density', 'cozy');
    document.body.setAttribute('data-density', density);

    await pollHealth();
    refreshAlertsCount();
    refreshSkelKpi();

    // Restore active top tab (default 'adb' — workstation sweep 2026-05-19).
    let tab = lsGet(LS_ACTIVE_TAB, 'adb');
    if (LEGACY_TAB_ALIAS[tab]) tab = LEGACY_TAB_ALIAS[tab];
    setSkelTab(TABS.includes(tab) ? tab : 'adb');

    // Author: Sinister Sanctum master agent (Claude) :: 2026-05-19 -- FleetState consolidation
    // The 30s tick now ONLY hits the health pill + alerts count + activity feed.
    // Sessions-strip rendering is driven by FleetState's 5s SSE feed (below),
    // so the strip stays fresh without an extra /api/sessions poll.
    setInterval(() => {
        pollHealth();
        refreshAlertsCount();
        if (state.activeTab === 'agents') {
            const pane = $('skel-agents');
            if (pane) {
                refreshActivityFeed(pane);
            }
        }
    }, REFRESH_MS);

    // FleetState-driven session strip (replaces the 30s /api/sessions poll above).
    if (window.FleetState && typeof window.FleetState.subscribe === 'function') {
        window.FleetState.subscribe((snap) => {
            if (!snap) return;
            // Sessions strip + tile shelf daemon dots — only render if visible.
            if (state.activeTab === 'agents' && Array.isArray(snap.sessions)) {
                const pane = $('skel-agents');
                if (pane) {
                    refreshAgentsSessionsStrip(pane, snap.sessions);
                    refreshTileShelf(pane);
                }
            }
            // Header tab counters + inbox bell badge.
            try {
                if (Array.isArray(snap.sessions)) {
                    const online = snap.sessions.filter(s => s.online).length;
                    const cnt = qs('[data-bind="tab-agents-count"]');
                    if (cnt) cnt.textContent = String(online);
                }
                // Inbox cursor freshness: light up the bell if any agent has
                // unread cross-agent messages newer than 2 minutes.
                if (snap.inbox_tails) {
                    const cutoff = Date.now() - 2 * 60 * 1000;
                    let fresh = 0;
                    for (const slug of Object.keys(snap.inbox_tails)) {
                        const tail = snap.inbox_tails[slug];
                        if (Array.isArray(tail)) {
                            tail.forEach(m => {
                                const ts = m && m.ts ? Date.parse(m.ts) : NaN;
                                if (!isNaN(ts) && ts >= cutoff) fresh++;
                            });
                        }
                    }
                    const bell = $('inbox-count');
                    if (bell) {
                        bell.textContent = fresh > 0 ? String(fresh) : '';
                        bell.classList.toggle('show', fresh > 0);
                    }
                }
            } catch (e) { /* non-fatal */ }
        });
    }

    // KPI refresh independent of active tab.
    if (_kpiTimer) clearInterval(_kpiTimer);
    _kpiTimer = setInterval(refreshSkelKpi, KPI_REFRESH_MS);

    // 2026-05-19 master sweep: spawned-windows now driven by FleetState (the
    // top-level subscribe near the retired-setInterval comment). A direct
    // one-shot refresh on boot avoids a blank bar in the brief window before
    // the first SSE event arrives.
    refreshSpawnedWindows();

    // Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
    // Daemon-liveness panel — mount when the dev-tools rail is opened. The
    // FleetState snapshot carries `heartbeats`; we surface a tiny 3-dot strip
    // (sanctum-console / sinister-vault / rkoj) in the windows bar trail.
    _mountDaemonLivenessIndicator();
}

// Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
// Tiny inline indicator: 3 colored dots next to the windows bar, one per
// canonical daemon. Subscribes to FleetState so it lights up red as soon as
// a heartbeat goes stale (age >= 120s). Click a dot to toast the last_line.
function _mountDaemonLivenessIndicator() {
    if (!window.FleetState || typeof window.FleetState.subscribe !== 'function') return;
    const bar = $('windows-bar');
    if (!bar || bar.parentElement && bar.parentElement.querySelector('[data-fleet-liveness]')) return;
    const wrap = el('div', {
        'data-fleet-liveness': '1',
        style: 'display:inline-flex;gap:6px;align-items:center;padding:2px 8px;margin-left:8px;font-size:11px;color:var(--muted);',
        title: 'daemon liveness — green = heartbeat <120s, red = stale/missing',
    });
    const DAEMONS = ['sanctum-console', 'sinister-vault', 'rkoj'];
    const dotEls = {};
    for (const slug of DAEMONS) {
        const dot = el('span', {
            'data-daemon': slug,
            style: 'width:8px;height:8px;border-radius:50%;background:#666;cursor:pointer;display:inline-block;',
            title: slug,
        });
        dotEls[slug] = dot;
        wrap.appendChild(dot);
    }
    // Insert next to the windows bar (parent if exists, else bar itself for legacy layouts).
    const parent = bar.parentElement || bar;
    parent.appendChild(wrap);

    window.FleetState.subscribe((snap) => {
        if (!snap || !snap.heartbeats) return;
        for (const slug of DAEMONS) {
            const hb = snap.heartbeats[slug];
            const dot = dotEls[slug];
            if (!dot) continue;
            if (hb && hb.alive) {
                dot.style.background = '#3fd17a';
                dot.title = `${slug}: alive (age ${hb.age_s}s)`;
            } else {
                dot.style.background = '#e25b5b';
                dot.title = `${slug}: ${hb && hb.exists ? `stale (age ${hb.age_s}s)` : 'no heartbeat file'}`;
            }
            dot.onclick = () => {
                const line = (hb && hb.last_line) || '(no last_line)';
                toast(`${slug}: ${line}`);
            };
        }
    });
}

bootstrap();

// ============================================================== HOT-RELOAD SSE LISTENER ==
// Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
// Why: operator wants to ship UI/CSS updates while the workbench is live and
// while spawned Claude agent windows are mid-context. The backend
// /api/sse/changes channel emits {path, kind, mtime} per file save. We:
//   - CSS: bump the matching <link>'s href ?v=<mtime> -> instant restyle, no reload
//   - PNG/ICO: bump matching <img> src + favicon
//   - JS: nag (toast "click to reload") — full reload required, operator decides
//   - HTML/templates: same nag — full reload required
//   - hello frame: silent (records watcher state for diagnostics)
// Reconnect on disconnect with 1s -> 30s exponential backoff. Survives
// `desktop_app --reload` worker respawns (the EXE/window stays put;
// the SSE stream just re-establishes).
// Knowledge: rkoj-hot-reload-pattern.md
(function rkojHotReload() {
    if (window.__rkoj_hr_started) return;
    window.__rkoj_hr_started = true;
    let backoffMs = 1000;
    let es = null;
    const MAX_BACKOFF = 30000;
    const RELOAD_NAG_SEEN = new Set();

    function bumpHrefVersion(url, mtime) {
        try {
            const u = new URL(url, window.location.href);
            u.searchParams.set('v', String(Math.floor((mtime || Date.now() / 1000) * 1000)));
            return u.pathname + u.search;
        } catch (e) {
            const sep = url.includes('?') ? '&' : '?';
            return url + sep + 'v=' + Date.now();
        }
    }

    function refreshStylesheets(relPath, mtime) {
        const slug = relPath.split('/').pop();
        let touched = 0;
        document.querySelectorAll('link[rel="stylesheet"]').forEach(link => {
            try {
                const href = link.getAttribute('href') || '';
                if (href.split('?')[0].split('/').pop() === slug) {
                    link.setAttribute('href', bumpHrefVersion(href, mtime));
                    touched++;
                }
            } catch (e) {}
        });
        if (touched) { try { toast(`[UPDATE] reloaded ${slug} (no page reload)`); } catch (e) {} }
    }

    function refreshImages(relPath, mtime) {
        const slug = relPath.split('/').pop();
        let touched = 0;
        document.querySelectorAll('img').forEach(img => {
            try {
                const src = img.getAttribute('src') || '';
                if (src.split('?')[0].split('/').pop() === slug) {
                    img.setAttribute('src', bumpHrefVersion(src, mtime));
                    touched++;
                }
            } catch (e) {}
        });
        document.querySelectorAll('link[rel~="icon"]').forEach(link => {
            try {
                const href = link.getAttribute('href') || '';
                if (href.split('?')[0].split('/').pop() === slug) {
                    link.setAttribute('href', bumpHrefVersion(href, mtime));
                    touched++;
                }
            } catch (e) {}
        });
        if (touched) { try { toast(`[UPDATE] refreshed asset ${slug}`); } catch (e) {} }
    }

    function nagReload(relPath, label) {
        if (RELOAD_NAG_SEEN.has(relPath)) return;
        RELOAD_NAG_SEEN.add(relPath);
        const t = $('toast');
        const msg = `[UPDATE] new ${label} ${relPath} — click toast to reload`;
        try {
            toast(msg);
            if (t) {
                t.style.cursor = 'pointer';
                const onClick = () => {
                    t.removeEventListener('click', onClick);
                    window.location.reload();
                };
                t.addEventListener('click', onClick, { once: true });
            }
        } catch (e) {
            try { console.warn('[hot-reload] nag failed', e); } catch (_) {}
        }
    }

    function handleFileChanged(payload) {
        if (!payload || !payload.path) return;
        switch (payload.kind) {
            case 'css':  return refreshStylesheets(payload.path, payload.mtime);
            case 'img':  return refreshImages(payload.path, payload.mtime);
            case 'js':   return nagReload(payload.path, 'JS');
            case 'html': return nagReload(payload.path, 'HTML');
            default:     return;
        }
    }

    function connect() {
        try {
            let url = '/api/sse/changes';
            // SSE in modern browsers doesn't carry Authorization headers; pass the
            // token via ?t= so the auth middleware accepts the request (server.py
            // reads request.query_params.get('t') as a fallback).
            let tok = null;
            try { tok = localStorage.getItem('sinister_token'); } catch (e) {}
            if (tok) url += '?t=' + encodeURIComponent(tok);
            es = new EventSource(url);
            es.addEventListener('hello', () => {
                backoffMs = 1000;
                try { console.log('[hot-reload] SSE connected'); } catch (e) {}
            });
            es.addEventListener('file-changed', (ev) => {
                try { handleFileChanged(JSON.parse(ev.data)); }
                catch (e) { try { console.warn('[hot-reload] bad payload', e); } catch (_) {} }
            });
            es.onerror = () => {
                try { es.close(); } catch (e) {}
                setTimeout(connect, backoffMs);
                backoffMs = Math.min(MAX_BACKOFF, Math.floor(backoffMs * 1.7));
            };
        } catch (e) {
            try { console.warn('[hot-reload] connect failed', e); } catch (_) {}
            setTimeout(connect, backoffMs);
            backoffMs = Math.min(MAX_BACKOFF, Math.floor(backoffMs * 1.7));
        }
    }

    if (location.pathname !== '/login') connect();
})();

/* =============================================================
   RKOJ Codex Pane — Sinister Sanctum master agent (Claude) :: 2026-05-19
   Why: tools/codex-companion/codex.py is the cross-model peer-review
   counterweight. Endpoints (POST /api/codex/review, GET /api/codex/reviews,
   GET /api/codex/review/{id}) exist in server.py but had no first-class
   UI surface. This module mounts a fullpane into the agents tab when
   sidebar nav = 'codex' (or hash route #pane=codex), registers Cmd+K
   commands, and drives the top-right Codex status pill.
   Liquid Glass primitives + Sanctum purple per docs/UI-DESIGN-SYSTEM.md.
   ============================================================= */
window.RkojCodexPane = (function () {
    const _state = {
        timer: null,
        latest: null,        // most-recent review summary {verdict, age_s, depth}
        expandedId: null,    // currently expanded row id
    };

    function _h() { return window.RkojHelpers || {}; }
    function _fetchJson(url, opts) {
        const H = _h();
        if (H && H.fetchJson) return H.fetchJson(url, opts);
        return fetchJson(url, opts);
    }
    function _toast(msg, isErr) {
        const H = _h();
        if (H && H.toast) return H.toast(msg, isErr);
        return toast(msg, isErr);
    }

    function _fmtAge(seconds) {
        if (!seconds && seconds !== 0) return '--';
        const s = Math.max(0, Math.floor(seconds));
        if (s < 60) return s + 's ago';
        const m = Math.floor(s / 60);
        if (m < 60) return m + 'm ago';
        const h = Math.floor(m / 60);
        if (h < 24) return h + 'h ago';
        const d = Math.floor(h / 24);
        return d + 'd ago';
    }

    // Mount the fullpane into a host container. Re-entrant + idempotent.
    function mount(host) {
        if (!host) return;
        const tpl = document.getElementById('tpl-codex-fullpane');
        if (!tpl) {
            host.appendChild(el('div', { class: 'empty-note' }, 'tpl-codex-fullpane missing'));
            return;
        }
        host.innerHTML = '';
        host.appendChild(tpl.content.cloneNode(true));

        // Wire the run-review button.
        const submitBtn = bind(host, 'codex-pane-submit');
        if (submitBtn) submitBtn.addEventListener('click', () => _runReview(host));

        // Initial history load.
        refreshHistory(host);

        // Auto-refresh the recent-reviews list while pane is visible.
        if (_state.timer) clearInterval(_state.timer);
        _state.timer = setInterval(() => {
            if (!document.body.contains(host)) {
                clearInterval(_state.timer);
                _state.timer = null;
                return;
            }
            refreshHistory(host);
        }, 30000);
    }

    function unmount() {
        if (_state.timer) { clearInterval(_state.timer); _state.timer = null; }
    }

    // POST /api/codex/review using the form values.
    async function _runReview(host) {
        const content = (bind(host, 'codex-pane-content').value || '').trim();
        if (!content) { _toast('paste some content first', true); return; }
        const context = (bind(host, 'codex-pane-context').value || '').trim();
        const language = (bind(host, 'codex-pane-language').value || 'python');
        const depthRadio = qs('input[name="codex-depth"]:checked', host);
        const depth = depthRadio ? depthRadio.value : 'standard';

        const submit = bind(host, 'codex-pane-submit');
        const feedback = bind(host, 'codex-pane-feedback');
        const status = bind(host, 'codex-pane-status');
        if (submit) { submit.disabled = true; submit.textContent = 'reviewing...'; }
        if (status) status.textContent = 'in flight';
        if (feedback) feedback.textContent = 'POSTing to /api/codex/review (this can take up to 3 minutes for deep)...';

        const r = await _fetchJson('/api/codex/review', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content, context, language, depth }),
        });

        if (submit) { submit.disabled = false; submit.textContent = 'Run Codex review'; }
        if (status) status.textContent = 'ready';

        // Graceful: surface no-API-key as friendly card.
        if (r && r.ok === false) {
            const err = (r.error || r.detail || 'review failed') + '';
            if (err.toLowerCase().includes('api key') || err.toLowerCase().includes('openai_api_key')) {
                _showNoKey(host, true);
                if (feedback) feedback.textContent = '';
                _toast('OPENAI_API_KEY not set - see card above', true);
            } else {
                if (feedback) feedback.textContent = '[FAIL] ' + err;
                _toast('[FAIL] ' + err, true);
            }
            return;
        }

        _showNoKey(host, false);
        if (feedback) {
            const v = (r.verdict || 'warn').toUpperCase();
            const findings = (r.findings || []).length;
            feedback.textContent = `[${v}] ${findings} finding(s) - elapsed ${(r.elapsed_s || 0).toFixed(1)}s`;
        }
        _toast(`[OK] codex verdict=${(r.verdict || 'warn').toUpperCase()}`);

        // Re-render history + bump status pill.
        await refreshHistory(host);
        await refreshStatusPill();
    }

    function _showNoKey(host, on) {
        const card = bind(host, 'codex-pane-nokey');
        const form = bind(host, 'codex-pane-form');
        if (card) card.style.display = on ? '' : 'none';
        if (form) form.style.display = on ? 'none' : '';
    }

    // Render the recent reviews list. Reads GET /api/codex/reviews?limit=20.
    async function refreshHistory(host) {
        const listEl = bind(host, 'codex-pane-history');
        const countEl = bind(host, 'codex-pane-history-count');
        const heroVerdict = bind(host, 'codex-hero-verdict');
        if (!listEl) return;

        const r = await _fetchJson('/api/codex/reviews?limit=20');
        if (!r || r.ok === false) {
            listEl.innerHTML = '';
            listEl.appendChild(el('div', { class: 'empty-note' },
                `history unavailable: ${(r && (r.error || r.detail)) || 'fetch failed'}`));
            if (countEl) countEl.textContent = '--';
            return;
        }
        const items = (r.reviews || []).slice(0, 20);
        if (countEl) countEl.textContent = String(items.length);
        listEl.innerHTML = '';
        if (!items.length) {
            listEl.appendChild(el('div', { class: 'empty-note' }, 'no reviews yet - run one above'));
            if (heroVerdict) {
                heroVerdict.textContent = 'No reviews yet';
                heroVerdict.className = 'codex-verdict-pill unknown';
            }
            return;
        }

        // Hero pill = latest verdict.
        const latest = items[0];
        if (heroVerdict) {
            const v = (latest.verdict || 'warn').toLowerCase();
            heroVerdict.textContent = v.toUpperCase() + ' :: ' + _fmtAge(_ageSeconds(latest));
            heroVerdict.className = 'codex-verdict-pill ' + v;
        }

        for (const it of items) {
            const v = (it.verdict || 'warn').toLowerCase();
            const ageStr = _fmtAge(_ageSeconds(it));
            const row = el('div', { class: 'codex-review-row', 'data-id': it.id || '' });
            row.appendChild(el('span', { class: 'codex-verdict-pill ' + v }, v.toUpperCase()));
            row.appendChild(el('span', { class: 'codex-row-summary', title: it.summary || '' },
                (it.summary || '(no summary)').slice(0, 120)));
            const meta = el('div', { class: 'codex-row-meta' });
            meta.appendChild(el('span', { class: 'depth' }, (it.depth || '--')));
            meta.appendChild(el('span', { class: 'age' }, ageStr));
            row.appendChild(meta);
            row.addEventListener('click', () => _toggleExpand(host, row, it));
            listEl.appendChild(row);
        }
    }

    function _ageSeconds(item) {
        if (!item) return null;
        if (typeof item.mtime === 'number') {
            return Math.max(0, (Date.now() / 1000) - item.mtime);
        }
        return null;
    }

    // Toggle a row into expanded mode (load full JSON + render findings).
    async function _toggleExpand(host, row, item) {
        if (row.classList.contains('is-expanded')) {
            // collapse: redraw the row in compact form by triggering refresh.
            row.classList.remove('is-expanded');
            row.innerHTML = '';
            const v = (item.verdict || 'warn').toLowerCase();
            row.appendChild(el('span', { class: 'codex-verdict-pill ' + v }, v.toUpperCase()));
            row.appendChild(el('span', { class: 'codex-row-summary', title: item.summary || '' },
                (item.summary || '(no summary)').slice(0, 120)));
            const meta = el('div', { class: 'codex-row-meta' });
            meta.appendChild(el('span', { class: 'depth' }, (item.depth || '--')));
            meta.appendChild(el('span', { class: 'age' }, _fmtAge(_ageSeconds(item))));
            row.appendChild(meta);
            return;
        }

        row.classList.add('is-expanded');
        row.innerHTML = '';
        const loading = el('div', { class: 'codex-review-expanded' }, 'loading full review...');
        row.appendChild(loading);

        const id = item.id || '';
        const r = await _fetchJson('/api/codex/review/' + encodeURIComponent(id));
        if (!r || r.ok === false) {
            loading.textContent = 'failed to load: ' + ((r && (r.error || r.detail)) || 'unknown');
            return;
        }

        const review = r.review || r;
        const wrap = el('div', { class: 'codex-review-expanded' });

        // Header line with verdict + meta.
        const head = el('div', { style: 'margin-bottom: 10px; display:flex; gap:10px; align-items:center; flex-wrap:wrap;' });
        const v = (review.verdict || 'warn').toLowerCase();
        head.appendChild(el('span', { class: 'codex-verdict-pill ' + v }, v.toUpperCase()));
        if (review.model)    head.appendChild(el('span', null, 'model: ' + review.model));
        if (review.depth)    head.appendChild(el('span', null, 'depth: ' + review.depth));
        if (typeof review.elapsed_s === 'number') head.appendChild(el('span', null, 'elapsed: ' + review.elapsed_s.toFixed(2) + 's'));
        if (review.language) head.appendChild(el('span', null, 'lang: ' + review.language));
        wrap.appendChild(head);

        // Summary paragraph.
        if (review.summary) {
            wrap.appendChild(el('div', { style: 'color: var(--text-primary); font-family: var(--font-sans); margin-bottom: 10px; line-height: 1.5;' },
                review.summary));
        }

        // Findings.
        const findings = review.findings || [];
        if (!findings.length) {
            wrap.appendChild(el('div', { style: 'color: var(--text-tertiary); font-style: italic;' }, '(no findings)'));
        } else {
            for (const f of findings) {
                const sev = (f.severity || 'low').toLowerCase();
                const chip = el('span', { class: 'codex-finding-chip ' + sev }, sev);
                const area = f.area || '';
                wrap.appendChild(el('div', { style: 'margin-top: 8px;' },
                    chip,
                    el('strong', { style: 'color: var(--text-primary); margin-left: 4px;' }, area),
                ));
                wrap.appendChild(el('div', { class: 'codex-finding-body' }, f.body || f.detail || f.message || ''));
            }
        }

        // Context (if present + short).
        if (review.context) {
            wrap.appendChild(el('div', { style: 'margin-top: 12px; padding-top: 10px; border-top: 1px solid color-mix(in oklab, white 6%, transparent); color: var(--text-tertiary); font-size: 11px;' },
                'context: ' + review.context));
        }

        // Log path + content_sha1.
        const footer = el('div', { style: 'margin-top: 6px; color: var(--text-tertiary); font-size: 10.5px;' });
        if (review.log_path)     footer.appendChild(el('div', null, 'log: ' + review.log_path));
        if (review.content_sha1) footer.appendChild(el('div', null, 'sha1: ' + review.content_sha1));
        if (review.reviewed_at)  footer.appendChild(el('div', null, 'at: ' + review.reviewed_at));
        wrap.appendChild(footer);

        row.innerHTML = '';
        row.appendChild(wrap);
    }

    // Top-right status pill — refreshed from /api/codex/reviews?limit=1.
    async function refreshStatusPill() {
        const pill = $('codex-status-pill');
        const textEl = $('codex-status-text');
        const ageEl = $('codex-status-age');
        if (!pill) return;
        const r = await _fetchJson('/api/codex/reviews?limit=1');
        if (!r || r.ok === false) {
            pill.className = 'codex-status-pill';
            if (textEl) textEl.textContent = 'Codex';
            if (ageEl)  ageEl.textContent  = 'offline';
            return;
        }
        const items = r.reviews || [];
        if (!items.length) {
            pill.className = 'codex-status-pill';
            if (textEl) textEl.textContent = 'Codex';
            if (ageEl)  ageEl.textContent  = 'no reviews';
            return;
        }
        const it = items[0];
        const v = (it.verdict || 'warn').toLowerCase();
        pill.className = 'codex-status-pill ' + v;
        if (textEl) textEl.textContent = 'Codex: ' + v;
        if (ageEl)  ageEl.textContent  = _fmtAge(_ageSeconds(it));
        _state.latest = { verdict: v, age_s: _ageSeconds(it), depth: it.depth };
    }

    // Open the codex fullpane inside the active agents tab (or switch tabs).
    function openPane() {
        // Switch to agents tab + replace its content with the fullpane.
        try { activateTab('agents'); } catch (e) {}
        const pane = $('skel-agents');
        if (!pane) {
            _toast('agents pane not mounted', true);
            return;
        }
        mount(pane);
        // Update hash for deep-linking.
        try {
            if (location.hash !== '#pane=codex') {
                history.replaceState(null, '', '#pane=codex');
            }
        } catch (e) {}
    }

    // Open the modal "run review" surface — for the Cmd+K
    // "codex: review current diff" command. Opens the pane + focuses the textarea.
    function openReviewDialog() {
        openPane();
        // Focus after the next paint.
        setTimeout(() => {
            const ta = qs('[data-bind="codex-pane-content"]');
            if (ta) { try { ta.focus(); } catch (e) {} }
        }, 50);
    }

    // ---- bootstrap ----
    function init() {
        // Top-right pill click -> open pane.
        const pill = $('codex-status-pill');
        if (pill) pill.addEventListener('click', () => openPane());

        // Initial pill refresh + periodic ticks (every 60s).
        refreshStatusPill();
        setInterval(refreshStatusPill, 60000);

        // Hash routing: if URL has #pane=codex on load (or hashchange), open the pane.
        function _hashCheck() {
            if ((location.hash || '').toLowerCase() === '#pane=codex') {
                openPane();
            }
        }
        window.addEventListener('hashchange', _hashCheck);
        // Defer initial check until after bootstrap() has run.
        setTimeout(_hashCheck, 200);

        // Register Cmd+K palette entries.
        if (window.RkojPalette && window.RkojPalette.registerRibbonAction) {
            window.RkojPalette.registerRibbonAction({
                id: 'codex:open-pane',
                label: 'codex: open pane',
                icon: 'C',
                category: 'Codex',
                handler: openPane,
            });
            window.RkojPalette.registerRibbonAction({
                id: 'codex:review-diff',
                label: 'codex: review current diff',
                icon: 'C',
                category: 'Codex',
                handler: openReviewDialog,
            });
        }

        // Sidebar nav 'codex' click -> open the fullpane instead of the dev-tools rail.
        // We patch the existing wireSkelShell handler by listening for clicks on
        // [data-nav="codex"] and short-circuiting the default tab-switch behaviour.
        qsa('.skel-side-item[data-nav="codex"]').forEach(el => {
            el.addEventListener('click', (ev) => {
                // Defer so setSkelNav() runs first (activates agents tab + sidebar).
                setTimeout(openPane, 0);
            });
        });
    }

    // Run init once DOM is ready (bootstrap() has already fired by the time
    // this script tag executes, but the DOM is stable here).
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init, { once: true });
    } else {
        // bootstrap() finishes synchronously up to the first await; defer one
        // tick so wireSkelShell() has wired the sidebar nav items first.
        setTimeout(init, 0);
    }

    return {
        mount: mount,
        unmount: unmount,
        openPane: openPane,
        openReviewDialog: openReviewDialog,
        refreshHistory: refreshHistory,
        refreshStatusPill: refreshStatusPill,
    };
})();

/* RKOJ Vault UI — Sinister Sanctum master agent (Claude) :: 2026-05-19 */
// ===== Sinister Vault UI module =====
window.RkojVault = (function () {
    const H = window.RkojHelpers || {};
    const _fetchJson = H.fetchJson || fetchJson;
    const _toast = H.toast || toast;
    const _$ = H.$ || $;
    const _qs = H.qs || qs;
    const _qsa = H.qsa || qsa;
    const _el = H.el || el;
    const REFRESH_MS_VAULT = 15000;
    let _interval = null;

    function _formatBytes(b) {
        if (!b) return '0 B';
        const u = ['B', 'KB', 'MB', 'GB', 'TB'];
        let i = 0;
        while (b >= 1024 && i < u.length - 1) { b /= 1024; i++; }
        return b.toFixed(b >= 100 ? 0 : 1) + ' ' + u[i];
    }

    async function refreshQuota(host) {
        try {
            const r = await _fetchJson('/api/vault/quota');
            const statusEl = _qs('[data-bind=vault-status]', host);
            if (!r || r.vault_offline || r.ok === false) {
                if (statusEl) {
                    statusEl.textContent = '● offline';
                    statusEl.className = 'rkoj-vault-status offline';
                }
                return;
            }
            if (statusEl) {
                statusEl.textContent = '● online';
                statusEl.className = 'rkoj-vault-status online';
            }
            const used = r.used_bytes || 0;
            const max = (r.max_gb || 1024) * Math.pow(1024, 3);
            const usedEl = _qs('[data-bind=vault-used]', host);
            const freeEl = _qs('[data-bind=vault-free]', host);
            if (usedEl) usedEl.textContent = _formatBytes(used);
            if (freeEl) freeEl.textContent = _formatBytes(Math.max(0, max - used));
            const pct = Math.min(100, (used / max) * 100);
            const fill = _qs('.rkoj-vault-quota-fill', host);
            if (fill) {
                fill.style.width = pct.toFixed(1) + '%';
                fill.className = 'rkoj-vault-quota-fill' + (pct > 92 ? ' over-warn' : pct > 80 ? ' getting-full' : '');
            }
        } catch (e) { /* silent */ }
    }

    async function refreshAudit(host) {
        try {
            const r = await _fetchJson('/api/vault/audit?limit=15');
            const list = _qs('[data-bind=vault-audit-list]', host);
            if (!list) return;
            list.innerHTML = '';
            const events = (r && r.events) || [];
            if (!events.length) {
                list.appendChild(_el('div', { class: 'empty-note' }, 'no recent events'));
                return;
            }
            for (const e of events) {
                list.appendChild(_el('div', { class: 'rkoj-vault-audit-row' },
                    _el('span', { class: 'kind kind-' + (e.kind || 'info') }, e.kind || '·'),
                    _el('span', { class: 'actor' }, e.actor || ''),
                    _el('span', { class: 'msg' }, e.message || e.path || ''),
                    _el('span', { class: 'ts mono' }, (e.ts || '').slice(11, 19)),
                ));
            }
        } catch (e) { /* silent */ }
    }

    async function refreshSync(host) {
        // Optional — vault daemon may proxy Syncthing status later; for now show stub link.
        const div = _qs('[data-bind=vault-sync-status]', host);
        if (div) div.textContent = 'Syncthing UI: http://localhost:8384/';
    }

    // 2026-05-19 master sweep: stub fleshed out using the existing
    // tpl-vault-commit-modal template (index.html:723). Repo dropdown is
    // populated from /api/launcher/options.projects (the same source the
    // launcher pane uses). Submit posts to /api/vault/commit (vault MCP
    // proxy in server.py — same auth path as the rest of /api/vault/*).
    // Pattern mirrored from openBroadcastModal (app.js ~L2444).
    async function openCommitModal() {
        const tpl = document.getElementById('tpl-vault-commit-modal');
        if (!tpl) { _toast('Commit modal template missing (tpl-vault-commit-modal)', true); return; }
        // Backdrop overlay (matches the broadcast / cycle-points modal pattern).
        const overlay = document.createElement('div');
        overlay.className = 'rkoj-modal-overlay';
        overlay.style.cssText = 'position:fixed;inset:0;z-index:9800;display:flex;align-items:center;justify-content:center;background:rgba(8,8,14,.55);backdrop-filter:blur(6px);';
        const frag = tpl.content.cloneNode(true);
        const wrap = document.createElement('div');
        wrap.appendChild(frag);
        overlay.appendChild(wrap);
        document.body.appendChild(overlay);

        const close = () => { try { overlay.remove(); } catch (e) { /* noop */ } };
        const repoSel = overlay.querySelector('[data-bind="vc-repo"]');
        const fileInput = overlay.querySelector('[data-bind="vc-file"]');
        const msgInput = overlay.querySelector('[data-bind="vc-message"]');
        const acctSel = overlay.querySelector('[data-bind="vc-account"]');
        const cancelBtn = overlay.querySelector('[data-act="cancel"]');
        const submitBtn = overlay.querySelector('[data-act="save"]');

        // Populate repo dropdown from /api/launcher/options (best-effort).
        if (repoSel) {
            repoSel.innerHTML = '<option value="">(loading repos...)</option>';
            try {
                const r = await _fetchJson('/api/launcher/options');
                const projects = (r && (r.projects || r.options || [])) || [];
                repoSel.innerHTML = '';
                if (projects.length) {
                    for (const p of projects) {
                        const key = (typeof p === 'string') ? p : (p.key || p.name || '');
                        if (!key) continue;
                        const opt = document.createElement('option');
                        opt.value = key;
                        opt.textContent = key;
                        repoSel.appendChild(opt);
                    }
                } else {
                    repoSel.innerHTML = '<option value="sinister-sanctum">sinister-sanctum</option>';
                }
            } catch (e) {
                repoSel.innerHTML = '<option value="sinister-sanctum">sinister-sanctum</option>';
            }
        }

        // Esc / click-outside / Cancel all close.
        overlay.addEventListener('click', (ev) => { if (ev.target === overlay) close(); });
        if (cancelBtn) cancelBtn.addEventListener('click', close);

        if (fileInput) setTimeout(() => fileInput.focus(), 50);

        // Submit -> POST /api/vault/commit
        if (submitBtn) submitBtn.addEventListener('click', async () => {
            const repo = repoSel ? repoSel.value.trim() : '';
            const file = fileInput ? fileInput.value.trim() : '';
            const message = msgInput ? msgInput.value.trim() : '';
            const account = acctSel ? acctSel.value.trim() : 'operator';
            if (!repo || !file || !message) {
                _toast('[FAIL] repo + file path + commit message required', true);
                return;
            }
            submitBtn.disabled = true;
            submitBtn.textContent = 'Committing...';
            try {
                const r = await _fetchJson('/api/vault/commit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ repo, path: file, message, account }),
                });
                if (r && r.ok) {
                    _toast(`[OK] committed: ${(r.hash || '').slice(0, 12) || 'no-hash'}`, false);
                    close();
                } else {
                    _toast(`[FAIL] ${(r && (r.error || r.detail)) || 'commit failed'}`, true);
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Commit';
                }
            } catch (e) {
                _toast(`[FAIL] ${e.message || e}`, true);
                submitBtn.disabled = false;
                submitBtn.textContent = 'Commit';
            }
        });
    }

    function mount(host) {
        refreshQuota(host);
        refreshAudit(host);
        refreshSync(host);
        if (_interval) clearInterval(_interval);
        _interval = setInterval(() => { refreshQuota(host); refreshAudit(host); }, REFRESH_MS_VAULT);
        _qsa('[data-act]', host).forEach(btn => {
            btn.addEventListener('click', async () => {
                const a = btn.dataset.act;
                if (a === 'vault-refresh-sync') return refreshSync(host);
                if (a === 'vault-refresh-audit') return refreshAudit(host);
                if (a === 'vault-commit') return openCommitModal();
                if (a === 'vault-snapshot') {
                    const r = await _fetchJson('/api/vault/snapshot', { method: 'POST' });
                    return _toast(r && r.ok ? '[OK] snapshot started' : '[WARN] vault offline', !(r && r.ok));
                }
                if (a === 'vault-open-gitea') return window.open('http://localhost:3000/', '_blank');
            });
        });
    }

    function unmount() {
        if (_interval) { clearInterval(_interval); _interval = null; }
    }

    return { mount, unmount, refreshQuota, refreshAudit, refreshSync, openCommitModal };
})();
