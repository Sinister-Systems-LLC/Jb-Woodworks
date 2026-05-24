// app/page.tsx — Status page. Pinged on every load to show fresh daemon state.
// RKOJ-ELENO :: 2026-05-24
'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { StatusPayload } from '@/lib/types';

export default function StatusPage() {
  const [status, setStatus] = useState<StatusPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const tick = async () => {
      try {
        const s = await api.status();
        if (!cancelled) { setStatus(s); setError(null); }
      } catch (e) {
        if (!cancelled) setError(String(e));
      }
    };
    tick();
    const id = setInterval(tick, 5000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-white">Bridge status</h1>
        <p className="text-sm text-white/60 mt-1">
          Polled every 5s · <code className="text-accent">/api/status</code>
        </p>
      </header>

      {error && (
        <div className="lg-card p-4 border border-[#E5484D]/40">
          <div className="text-[#E5484D] font-medium">Daemon unreachable</div>
          <div className="text-white/60 text-xs mt-1">{error}</div>
          <div className="text-white/60 text-xs mt-2">
            Start it:{' '}
            <code className="text-accent">cd source && python -m bridge_daemon.bridge --chatdb fixtures/canned-chat.db</code>
          </div>
        </div>
      )}

      {status && (
        <>
          <section className="grid grid-cols-3 gap-4">
            <StatTile label="Daemon"     value={status.ok ? 'up' : 'down'} ok={status.ok} />
            <StatTile label="Phase"      value={status.phase} />
            <StatTile label="Uptime (s)" value={String(status.uptime_sec)} />
            <StatTile label="chat.db"    value={status.chatdb_exists ? 'present' : 'missing'} ok={status.chatdb_exists} />
            <StatTile label="Farm SSH"   value={status.farm_ssh} ok={status.farm_ssh === 'up'} />
            <StatTile label="Tail alive" value={status.tail_alive ? 'yes' : 'no'} ok={status.tail_alive} />
          </section>

          <section className="lg-card p-5">
            <h2 className="text-sm uppercase tracking-wider text-white/40 mb-3">chat.db source</h2>
            <code className="text-xs text-white/80 break-all">{status.chatdb_path}</code>
          </section>
        </>
      )}
    </div>
  );
}

function StatTile({ label, value, ok }: { label: string; value: string; ok?: boolean }) {
  const dot = ok === true ? 'var(--accent)' : ok === false ? '#E5484D' : 'transparent';
  return (
    <div className="lg-card p-4">
      <div className="text-[10px] uppercase tracking-wider text-white/40">{label}</div>
      <div className="flex items-center gap-2 mt-1">
        {ok !== undefined && <span style={{ color: dot }}>●</span>}
        <span className="text-2xl font-bold text-white tabular-nums">{value}</span>
      </div>
    </div>
  );
}
