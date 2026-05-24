// app/threads/page.tsx — Thread list.
// RKOJ-ELENO :: 2026-05-24
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api, formatUnix } from '@/lib/api';
import type { Thread } from '@/lib/types';

export default function ThreadsPage() {
  const [threads, setThreads] = useState<Thread[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.threads()
      .then((r) => setThreads(r.threads))
      .catch((e) => setError(String(e)));
  }, []);

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-white">Threads</h1>
          <p className="text-sm text-white/60 mt-1">
            From <code className="text-accent">/api/threads</code> · sorted newest-read first
          </p>
        </div>
        {threads && (
          <div className="lg-pill h-8 px-3 text-xs inline-flex items-center gap-1.5">
            <span className="text-accent">●</span>
            <span className="text-white">{threads.length} thread{threads.length === 1 ? '' : 's'}</span>
          </div>
        )}
      </header>

      {error && (
        <div className="lg-card p-4 border border-[#E5484D]/40 text-[#E5484D] text-sm">
          Could not load threads · {error}
        </div>
      )}

      {threads && threads.length === 0 && (
        <div className="lg-card p-8 text-center">
          <div className="text-white/70 text-sm">No threads in this chat.db.</div>
          <div className="text-white/40 text-xs mt-2">
            Connect the farm to see real threads · or seed the canned fixture via{' '}
            <code className="text-accent">python source/fixtures/make_canned_chatdb.py</code>
          </div>
        </div>
      )}

      {threads && threads.length > 0 && (
        <ul className="space-y-2">
          {threads.map((t) => (
            <li key={t.chat_id}>
              <Link
                href={`/threads/${t.chat_id}`}
                className="lg-card block p-4 no-underline hover:border-accent/40 transition-colors"
              >
                <div className="flex items-baseline justify-between gap-4">
                  <div>
                    <div className="text-white font-medium">{t.display_name || t.chat_identifier}</div>
                    <div className="text-[11px] text-white/40 mt-0.5 font-mono">
                      chat #{t.chat_id} · {t.service || 'unknown'}
                    </div>
                  </div>
                  <div className="text-[11px] text-white/40 tabular-nums">
                    {t.last_read_unix ? formatUnix(t.last_read_unix) : 'never'}
                  </div>
                </div>
                {t.messages[0] && (
                  <div className="mt-2 text-xs text-white/70 truncate">
                    <span className="text-accent">{t.messages[0].is_from_me ? '→' : '←'}</span>{' '}
                    {t.messages[0].body || <em className="text-white/40">no body</em>}
                  </div>
                )}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
