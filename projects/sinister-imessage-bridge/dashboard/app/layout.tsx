// app/layout.tsx — Sinister iMessage Bridge dashboard root layout
// RKOJ-ELENO :: 2026-05-24
//
// 3-column shell per dashboard-skeleton:  sidebar | main | right rail (status)
// Inherits .lg-* Liquid Glass classes from skeleton globals.css.

import type { Metadata, Viewport } from 'next';
import Link from 'next/link';
import './globals.css';

export const metadata: Metadata = {
  title: 'Sinister iMessage Bridge',
  description: 'Operator dashboard for the Sinister iMessage Bridge',
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: '#0A0A0F',
};

const NAV = [
  { href: '/',         label: 'Status',  glyph: '◆' },
  { href: '/threads',  label: 'Threads', glyph: '☰' },
  { href: '/compose',  label: 'Compose', glyph: '✎' },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">
        <div className="grid grid-cols-[240px_1fr_280px] min-h-screen">
          {/* Sidebar */}
          <aside className="lg-rail border-r border-white/5 p-4 flex flex-col gap-1">
            <div className="flex items-center gap-2 px-3 py-4">
              <span aria-hidden className="text-accent text-lg">◆</span>
              <span className="text-white font-semibold tracking-tight">iMessage Bridge</span>
            </div>
            <nav className="flex flex-col gap-1 mt-2">
              {NAV.map((n) => (
                <Link
                  key={n.href}
                  href={n.href}
                  className="lg-pill h-9 px-3 inline-flex items-center gap-2 text-xs no-underline"
                >
                  <span aria-hidden className="text-accent w-4 text-center">{n.glyph}</span>
                  <span className="text-white">{n.label}</span>
                </Link>
              ))}
            </nav>
            <div className="mt-auto px-3 py-3 text-[10px] text-white/40">
              Lane <span className="text-white/70">sinister-imessage-bridge</span><br />
              Phase <span className="text-accent">P0 · scaffold</span>
            </div>
          </aside>

          {/* Main */}
          <main className="page-fade-in p-8 overflow-y-auto">{children}</main>

          {/* Right rail — bridge status pinned */}
          <aside className="lg-rail border-l border-white/5 p-4">
            <h3 className="text-[11px] uppercase tracking-wider text-white/40 mb-3">Bridge daemon</h3>
            <BridgeStatusPanel />
            <h3 className="text-[11px] uppercase tracking-wider text-white/40 mt-6 mb-3">Per-phase gate</h3>
            <ol className="text-xs space-y-1.5 text-white/70">
              <li>✅ P0 — scaffold landed</li>
              <li>⏳ P1 — awaiting farm</li>
              <li>· P2 — send + per-thread OK</li>
              <li>· P3 — daemon + tail + bus</li>
              <li>· P4 — cross-lane + auto-respond</li>
            </ol>
          </aside>
        </div>
      </body>
    </html>
  );
}

// Client component for the live status pill. Polls /api/status every 5s.
function BridgeStatusPanel() {
  return (
    <div className="lg-card p-3">
      <div className="text-[10px] text-white/40 mb-1">Health</div>
      <div id="bridge-status" className="text-sm text-white/80">loading…</div>
      <script
        // The status panel is intentionally a tiny vanilla fetch — no React
        // state needed; keeps the right-rail render path zero-cost on every
        // page nav. Replace with an Eve observation card later (P3).
        dangerouslySetInnerHTML={{
          __html: `
            (async function tick() {
              try {
                const r = await fetch('/api/status', { cache: 'no-store' });
                const d = await r.json();
                const el = document.getElementById('bridge-status');
                if (!el) return;
                el.innerHTML =
                  '<span style="color:' + (d.ok ? 'var(--accent)' : '#E5484D') + '">●</span> ' +
                  (d.ok ? 'up' : 'down') + ' · ' + (d.phase || '-') +
                  '<div style="color:rgba(255,255,255,0.4);font-size:10px;margin-top:4px">' +
                  (d.chatdb_exists ? 'chatdb ok · ' : 'chatdb missing · ') +
                  'uptime ' + (d.uptime_sec || 0) + 's' +
                  '</div>';
              } catch (e) {
                const el = document.getElementById('bridge-status');
                if (el) el.innerHTML = '<span style="color:#E5484D">●</span> daemon unreachable';
              }
              setTimeout(tick, 5000);
            })();
          `,
        }}
      />
    </div>
  );
}
