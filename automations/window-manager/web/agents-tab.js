// Author: RKOJ-ELENO :: 2026-05-21
// agents-tab.js — niri-style vertical stack of jcode-form xterm.js terminals
// inside the Agents pane. Each pane wraps a `claude --dangerously-skip-permissions -p ...`
// subprocess via WebSocket /ws/agent/{pane_id}.
//
// Public API: window.SanctumAgentsTab.mount(hostEl) — idempotent, safe to call
// multiple times. Called lazily by app.js on first switch to Agents tab.
//
// Contract notes:
//   - Does NOT modify window.RkojHelpers, window.activateTab, window.fetchJson, window.toast.
//   - Reuses window.fetchJson + window.toast if present; falls back to fetch/console.
//   - Slash commands intercepted locally for /help /clear /compact /resume /create
//     /save /git /mcp /effort /fast /skills /watchdog /kill. Anything else gets
//     forwarded into the subprocess as the next operator turn.

(function () {
    'use strict';

    var mounted = false;
    var hostEl = null;
    var panes = []; // [{pane_id, ws, term, fit, statusDot, agentInfo, card, busy}]

    function $toast(msg, bad) {
        if (window.toast) return window.toast(msg, !!bad);
        console[bad ? 'error' : 'log']('[agents-tab]', msg);
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
            else n.setAttribute(k, attrs[k]);
        }
        (kids || []).forEach(function (c) { n.appendChild(typeof c === 'string' ? document.createTextNode(c) : c); });
        return n;
    }

    // --- xterm.js sentinel ---
    function xtermReady() {
        return !!(window.Terminal && window.FitAddon);
    }

    // --- Outer mount ---
    function mountAgentsTab(host) {
        if (!host) return;
        hostEl = host;
        if (mounted) return;
        mounted = true;

        host.innerHTML = '';

        // Toolbar
        var toolbar = el('div', { class: 'sa-toolbar' }, [
            el('button', { class: 'sp-btn primary', onclick: spawnNewPane }, ['+ New Agent']),
            el('button', { class: 'sp-btn ghost', onclick: refreshPanesFromServer }, ['Refresh']),
            el('div', { class: 'sp-spacer' }, []),
            el('span', { class: 'sa-hint' }, ['jcode-form  ·  niri-style stack  ·  WebSocket-backed']),
        ]);
        host.appendChild(toolbar);

        // Niri-style scrollable container — vertical column.
        var niri = el('div', { class: 'sa-niri', id: 'sa-niri' }, []);
        host.appendChild(niri);

        if (!xtermReady()) {
            niri.appendChild(el('div', { class: 'sp-empty' },
                ['xterm.js failed to load (offline?). New Agent will create a degraded text pane.']));
        }

        refreshPanesFromServer();
    }

    async function refreshPanesFromServer() {
        var r = await $fetchJson('/api/agent/list');
        if (!r || !r.ok) return;
        var seen = {};
        (r.panes || []).forEach(function (p) {
            seen[p.pane_id] = true;
            if (!panes.find(function (x) { return x.pane_id === p.pane_id; })) {
                // Server has it but client doesn't — rehydrate a card (no WS reconnect by default).
                createPaneCard(p, /*openWS*/ false);
            }
        });
    }

    async function spawnNewPane() {
        // Pull project key from the sub-tab strip if available.
        var activeChip = document.querySelector('.sp-proj-chip.active');
        var projectKey = (activeChip && activeChip.dataset && activeChip.dataset.proj) || 'sanctum';
        if (projectKey === 'all') projectKey = 'sanctum';

        var body = {
            project_key: projectKey,
            agent_name: 'EVE',
            mode: 'overview',
            accent: 'purple',
        };
        var r = await $fetchJson('/api/agent/spawn', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        if (!r || !r.ok) { $toast('spawn failed', true); return; }
        createPaneCard(r.pane, /*openWS*/ true);
        $toast('spawned ' + r.pane.pane_id);
    }

    function createPaneCard(paneMeta, openWS) {
        var niri = document.getElementById('sa-niri');
        if (!niri) return;

        var statusDot = el('span', { class: 'sa-status-dot idle', title: 'idle' }, []);
        var modePill = el('span', { class: 'sa-mode' }, [paneMeta.mode || 'overview']);
        var nameSpan = el('span', { class: 'sa-name' }, [paneMeta.agent_name || 'EVE']);
        var projSpan = el('span', { class: 'sa-project' }, [paneMeta.project_key || 'sanctum']);
        var idSpan = el('span', { class: 'sa-paneid' }, ['#' + paneMeta.pane_id]);

        var killBtn = el('button', { class: 'sp-icon-btn', title: 'Kill current turn' }, ['x']);
        var closeBtn = el('button', { class: 'sp-icon-btn', title: 'Close pane' }, ['X']);

        var header = el('header', { class: 'sa-head' }, [
            statusDot, nameSpan,
            el('span', { class: 'sa-sep' }, ['·']),
            projSpan,
            el('span', { class: 'sa-sep' }, ['·']),
            modePill,
            el('div', { class: 'sp-spacer' }, []),
            idSpan,
            killBtn, closeBtn,
        ]);

        var termHost = el('div', { class: 'sa-term-host' }, []);
        var input = el('input', {
            class: 'sp-input sa-input',
            type: 'text',
            placeholder: '/help · /clear · /compact · /resume · /create · /save · /git · /mcp · /effort · /fast · /skills · /watchdog · /kill · or type a turn',
        });
        var sendBtn = el('button', { class: 'sp-btn primary' }, ['SEND']);
        var inputRow = el('footer', { class: 'sa-input-row' }, [input, sendBtn]);

        var card = el('article', { class: 'sa-card sa-accent-' + (paneMeta.accent || 'purple') }, [
            header, termHost, inputRow,
        ]);
        niri.appendChild(card);

        // --- xterm.js wiring (graceful fallback) ---
        var term = null;
        var fit = null;
        if (xtermReady()) {
            try {
                term = new window.Terminal({
                    convertEol: true,
                    cursorBlink: true,
                    fontFamily: 'Consolas, "Cascadia Mono", "Courier New", monospace',
                    fontSize: 13,
                    // Sanctum-exact tokens (matches theme.css):
                    //   BG:           #0E0A14
                    //   BG_GLASS_1:   #15131A
                    //   LIGHT_PURPLE: #E8D6FF
                    //   PURPLE_HALO:  #C39DFF
                    //   PURPLE_ACCENT:#A06EFF
                    //   PURPLE_DEEP:  #7A3DD4
                    //   BG_GLOW:      #2A1F3D
                    theme: {
                        background: '#0E0A14',
                        foreground: '#E8D6FF',
                        cursor: '#C39DFF',
                        cursorAccent: '#0E0A14',
                        selectionBackground: '#2A1F3D',
                        selectionForeground: '#E8D6FF',
                        black: '#0E0A14',
                        red: '#FF6B8A',
                        green: '#85C86E',
                        yellow: '#DAA520',
                        blue: '#A06EFF',
                        magenta: '#C39DFF',
                        cyan: '#7DD3FC',
                        white: '#E8D6FF',
                        brightBlack: '#3A2A55',
                        brightRed: '#FF8FA6',
                        brightGreen: '#A6E0A6',
                        brightYellow: '#F1C868',
                        brightBlue: '#C39DFF',
                        brightMagenta: '#E8D6FF',
                        brightCyan: '#B4E5FA',
                        brightWhite: '#FFFFFF',
                    },
                });
                fit = new window.FitAddon.FitAddon();
                term.loadAddon(fit);
                term.open(termHost);
                try { fit.fit(); } catch (_) { }
                window.addEventListener('resize', function () { try { fit && fit.fit(); } catch (_) { } });
            } catch (e) {
                term = null;
                termHost.appendChild(el('div', { class: 'sp-empty' }, ['xterm init failed: ' + e]));
            }
        }
        if (!term) {
            // Degraded mode — append-only div.
            var fallback = el('pre', { class: 'sa-term-fallback' }, []);
            termHost.appendChild(fallback);
            term = {
                _fallback: fallback,
                write: function (s) {
                    fallback.appendChild(document.createTextNode(s.replace(/\r\n/g, '\n')));
                    fallback.scrollTop = fallback.scrollHeight;
                },
                clear: function () { fallback.textContent = ''; },
            };
        }

        var pane = {
            pane_id: paneMeta.pane_id,
            meta: paneMeta,
            ws: null,
            term: term,
            fit: fit,
            statusDot: statusDot,
            card: card,
            busy: false,
        };
        panes.push(pane);

        function setStatus(s) {
            statusDot.className = 'sa-status-dot ' + (s || 'idle');
            statusDot.title = s || 'idle';
            pane.busy = (s === 'running');
        }

        killBtn.addEventListener('click', function () {
            if (pane.ws && pane.ws.readyState === WebSocket.OPEN) {
                pane.ws.send(JSON.stringify({ kind: 'kill' }));
            }
        });
        closeBtn.addEventListener('click', async function () {
            try {
                await $fetchJson('/api/agent/' + pane.pane_id + '/close', { method: 'POST' });
            } catch (_) { }
            try { pane.ws && pane.ws.close(); } catch (_) { }
            try { card.remove(); } catch (_) { }
            panes = panes.filter(function (p) { return p !== pane; });
        });

        function sendOperatorLine(text) {
            if (!pane.ws || pane.ws.readyState !== WebSocket.OPEN) {
                term.write('\x1b[31m[ws closed — reconnecting...]\x1b[0m\r\n');
                openWebSocket();
                setTimeout(function () { sendOperatorLine(text); }, 600);
                return;
            }
            term.write('\x1b[36m> ' + text + '\x1b[0m\r\n');
            pane.ws.send(JSON.stringify({ kind: 'stdin', data: text }));
        }

        function handleSlash(text) {
            var parts = text.trim().split(/\s+/);
            var cmd = (parts[0] || '').toLowerCase();
            switch (cmd) {
                case '/help':
                    term.write(
                        '\x1b[35mjcode slash commands:\x1b[0m\r\n' +
                        '  /help /clear /compact /resume /create /save\r\n' +
                        '  /git /mcp /effort /fast /skills /watchdog /kill\r\n' +
                        '  anything else is sent to the agent as the next turn\r\n');
                    return true;
                case '/clear':
                    term.clear();
                    return true;
                case '/compact':
                    term.write('\x1b[33m[/compact] requesting context compaction...\x1b[0m\r\n');
                    sendOperatorLine('Please compact our conversation context.');
                    return true;
                case '/resume':
                    term.write('\x1b[33m[/resume] re-sending opening phrase\x1b[0m\r\n');
                    sendOperatorLine('Resume the session and recap where we left off.');
                    return true;
                case '/create':
                    spawnNewPane();
                    return true;
                case '/save':
                    $toast('save: cycle-point snapshot — open Workstation > Cycle points');
                    return true;
                case '/git':
                    $toast('git: open Workstation > Vault to commit');
                    return true;
                case '/mcp':
                    $toast('mcp: operator-only via Settings');
                    return true;
                case '/effort':
                    $toast('effort: switch model in Settings');
                    return true;
                case '/fast':
                    $toast('fast: toggle Opus 4.6 in spawn modal');
                    return true;
                case '/skills':
                    $toast('skills: see skills/_INDEX.md');
                    return true;
                case '/watchdog':
                    $toast('watchdog: see _shared-memory/heartbeats/');
                    return true;
                case '/kill':
                    killBtn.click();
                    return true;
            }
            return false;
        }

        function doSend() {
            var text = (input.value || '').trim();
            if (!text) return;
            input.value = '';
            if (text.charAt(0) === '/' && handleSlash(text)) return;
            sendOperatorLine(text);
        }
        sendBtn.addEventListener('click', doSend);
        input.addEventListener('keydown', function (ev) {
            if (ev.key === 'Enter') { ev.preventDefault(); doSend(); }
        });

        function openWebSocket() {
            var proto = (location.protocol === 'https:') ? 'wss:' : 'ws:';
            var url = proto + '//' + location.host + '/ws/agent/' + pane.pane_id;
            var ws;
            try {
                ws = new WebSocket(url);
            } catch (e) {
                term.write('\x1b[31m[WS open failed] ' + e + '\x1b[0m\r\n');
                return;
            }
            pane.ws = ws;
            ws.onopen = function () {
                term.write('\x1b[32m[ws connected]\x1b[0m\r\n');
            };
            ws.onmessage = function (ev) {
                var frame;
                try { frame = JSON.parse(ev.data); } catch (_) { return; }
                if (frame.kind === 'stdout' || frame.kind === 'stderr') {
                    term.write(frame.data || '');
                } else if (frame.kind === 'status') {
                    setStatus(frame.data);
                } else if (frame.kind === 'turn-end') {
                    term.write('\r\n');
                }
            };
            ws.onerror = function () {
                term.write('\x1b[31m[ws error — subprocess unavailable]\x1b[0m\r\n');
            };
            ws.onclose = function () {
                term.write('\x1b[33m[ws closed]\x1b[0m\r\n');
                setStatus('idle');
            };
        }

        if (openWS) openWebSocket();
        else term.write('\x1b[35m[pane rehydrated — click Send or type to (re)connect]\x1b[0m\r\n');
    }

    // ---------- public API ----------
    window.SanctumAgentsTab = {
        mount: mountAgentsTab,
        refresh: refreshPanesFromServer,
        spawn: spawnNewPane,
    };
})();
