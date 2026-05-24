// app/threads/[chatId]/page.tsx — Single thread message stream.
// RKOJ-ELENO :: 2026-05-24
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { api, formatUnix } from '@/lib/api';
import type { Thread } from '@/lib/types';

export default function ThreadDetailPage() {
  const params = useParams<{ chatId: string }>();
  const chatId = Number(params.chatId);
  const [thread, setThread] = useState<Thread | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!chatId) return;
    api.threadDetail(chatId, 100)
      .then((r) => { if (r.thread) setThread(r.thread); else setError(r.error || 'unknown error'); })
      .catch((e) => setError(String(e)));
  }, [chatId]);

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <Link href="/threads" className="lg-pill h-8 px-3 text-xs inline-flex items-center gap-1.5 no-underline">
          <span className="text-accent">←</span>
          <span className="text-white">Threads</span>
        </Link>
        {thread && (
          <div className="text-right">
            <h1 className="text-xl font-semibold text-white">{thread.display_name || thread.chat_identifier}</h1>
            <div className="text-[11px] text-white/40 font-mono">
              chat #{thread.chat_id} · {thread.service || 'unknown'} · {thread.messages.length} msgs
            </div>
          </div>
        )}
      </header>

      {error && (
        <div className="lg-card p-4 border border-[#E5484D]/40 text-[#E5484D] text-sm">
          Could not load thread · {error}
        </div>
      )}

      {thread && (
        <section className="lg-card p-4 space-y-3 max-h-[70vh] overflow-y-auto">
          {[...thread.messages].reverse().map((m) => (
            <div key={m.rowid} className={m.is_from_me ? 'flex justify-end' : 'flex justify-start'}>
              <div
                className={
                  m.is_from_me
                    ? 'max-w-[70%] rounded-2xl rounded-tr-sm px-3 py-2 text-sm'
                    : 'max-w-[70%] rounded-2xl rounded-tl-sm px-3 py-2 text-sm'
                }
                style={{
                  background: m.is_from_me ? 'var(--accent)' : 'var(--surface-2)',
                  color: m.is_from_me ? '#FFFFFF' : 'var(--text-primary)',
                }}
              >
                {m.body || <em className="opacity-60">no body</em>}
                <div className="text-[10px] mt-1" style={{ color: m.is_from_me ? 'rgba(255,255,255,0.7)' : 'var(--text-tertiary)' }}>
                  {formatUnix(m.sent_unix)}
                </div>
              </div>
            </div>
          ))}
        </section>
      )}
    </div>
  );
}
