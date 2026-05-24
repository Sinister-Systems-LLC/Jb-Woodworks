// app/compose/page.tsx — Send composer (disabled until P2 unlock).
// RKOJ-ELENO :: 2026-05-24
'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import type { SendResponse } from '@/lib/types';

const PHASE = 'P0'; // bump when phase advances

export default function ComposePage() {
  const [service, setService] = useState<'iMessage' | 'SMS'>('iMessage');
  const [recipient, setRecipient] = useState('');
  const [body, setBody] = useState('');
  const [result, setResult] = useState<SendResponse | null>(null);
  const [pending, setPending] = useState(false);

  const handleSend = async (dryRun: boolean) => {
    setPending(true);
    setResult(null);
    try {
      const r = await api.send({
        service, recipient, body,
        operator_ok: true, // the click IS the operator OK
        dry_run: dryRun,
      });
      setResult(r);
    } catch (e) {
      setResult({ status: 'error', reason: String(e) });
    } finally {
      setPending(false);
    }
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-white">Compose</h1>
        <p className="text-sm text-white/60 mt-1">
          Dry-run validates guards (allowlist · rate-limit · operator_ok) without sending.
          Live send disabled until phase advances past <span className="text-accent">{PHASE}</span>.
        </p>
      </header>

      <section className="lg-card p-5 space-y-4">
        <div>
          <label className="block text-[11px] uppercase tracking-wider text-white/40 mb-1.5">Service</label>
          <div className="flex gap-2">
            {(['iMessage', 'SMS'] as const).map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setService(s)}
                className={`h-8 px-3 text-xs inline-flex items-center gap-1.5 ${service === s ? 'lg-pill-active' : 'lg-pill'}`}
              >
                <span className="text-white">{s}</span>
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-[11px] uppercase tracking-wider text-white/40 mb-1.5">Recipient</label>
          <input
            type="text"
            value={recipient}
            onChange={(e) => setRecipient(e.target.value)}
            placeholder="+15551234567 or name@example.com"
            className="lg-input w-full h-10 px-3 text-sm text-white"
          />
        </div>

        <div>
          <label className="block text-[11px] uppercase tracking-wider text-white/40 mb-1.5">Body</label>
          <textarea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder="message text"
            rows={4}
            className="lg-input w-full p-3 text-sm text-white"
          />
        </div>

        <div className="flex gap-2 pt-2">
          <button
            type="button"
            onClick={() => handleSend(true)}
            disabled={pending || !recipient || !body}
            className="lg-button h-9 px-4 text-xs inline-flex items-center gap-2 disabled:opacity-50"
          >
            <span className="text-accent">⚙</span>
            <span className="text-white">{pending ? 'Sending…' : 'Dry-run'}</span>
          </button>
          <button
            type="button"
            onClick={() => handleSend(false)}
            disabled={pending || PHASE === 'P0'}
            className="lg-pill h-9 px-4 text-xs inline-flex items-center gap-2 disabled:opacity-50"
            title={PHASE === 'P0' ? 'Live send unlocks at P2' : 'Send for real'}
          >
            <span className="text-accent">→</span>
            <span className="text-white">Send (P2+)</span>
          </button>
        </div>
      </section>

      {result && (
        <section className="lg-card p-4">
          <div className="text-[11px] uppercase tracking-wider text-white/40 mb-2">Result</div>
          <pre className="text-xs text-white/80 overflow-x-auto whitespace-pre-wrap">
{JSON.stringify(result, null, 2)}
          </pre>
        </section>
      )}
    </div>
  );
}
