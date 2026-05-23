/* Author: RKOJ-ELENO :: 2026-05-23
 * Client-side estimate form. react-hook-form + zod + axios-free fetch.
 * Hits /api/inquiry which writes to Prisma → Postgres.
 */
'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { inquirySchema, type InquiryInput } from '@/lib/validations';

export function ContactForm() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<InquiryInput>({ resolver: zodResolver(inquirySchema) });

  const [done, setDone] = useState(false);
  const [serverErr, setServerErr] = useState<string | null>(null);

  async function onSubmit(values: InquiryInput) {
    setServerErr(null);
    try {
      const res = await fetch('/api/inquiry', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify(values),
      });
      const json = await res.json();
      if (!res.ok || !json.ok) {
        setServerErr(json.error || 'Something went wrong. Email Orders@ShowMasters.com directly.');
        return;
      }
      setDone(true);
      reset();
    } catch {
      setServerErr('Network error. Email Orders@ShowMasters.com directly.');
    }
  }

  if (done) {
    return (
      <div className="lg-card p-8 text-center">
        <div className="mx-auto w-14 h-14 rounded-full bg-[var(--gold-soft)] flex items-center justify-center text-[var(--gold)]" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"><path d="M4 12.5l5 5L20 6" /></svg>
        </div>
        <h3 className="mt-4 font-display text-2xl">Request received.</h3>
        <p className="mt-2 text-[var(--text-2)]">
          We&apos;ll be in touch within one business day to walk through the brief.
        </p>
      </div>
    );
  }

  return (
    <form className="lg-card p-8 space-y-4" onSubmit={handleSubmit(onSubmit)} noValidate>
      <Field label="Your name" error={errors.name?.message}>
        <input {...register('name')} placeholder="First and last" className="input" />
      </Field>
      <Field label="Email" error={errors.email?.message}>
        <input type="email" {...register('email')} placeholder="you@company.com" className="input" />
      </Field>
      <Field label="Phone" error={errors.phone?.message}>
        <input type="tel" {...register('phone')} placeholder="(555) 555-5555" className="input" />
      </Field>
      <Field label="Company" error={errors.company?.message}>
        <input {...register('company')} placeholder="Production company / venue / client" className="input" />
      </Field>
      <Field label="Event location" error={errors.location?.message}>
        <input {...register('location')} placeholder="City, state" className="input" />
      </Field>
      <Field label="Event dates" error={errors.dates?.message}>
        <input {...register('dates')} placeholder="Load-in — load-out" className="input" />
      </Field>
      <Field label="Tell us about the show" error={errors.brief?.message}>
        <textarea
          {...register('brief')}
          rows={5}
          placeholder="Crew sizes, departments, special needs, anything else."
          className="input min-h-[120px]"
        />
      </Field>

      {serverErr && (
        <p className="text-sm text-[var(--danger)]" role="alert">{serverErr}</p>
      )}

      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full py-4 rounded-full bg-gradient-to-br from-[var(--gold-300)] to-[var(--gold-700)] text-[#0A0A0F] font-bold tracking-wide hover:shadow-[var(--gold-glow)] transition-shadow disabled:opacity-60"
      >
        {isSubmitting ? 'Sending…' : 'Request an Estimate'}
      </button>

      <style>{`
        .input {
          width: 100%;
          padding: 14px 16px;
          background: color-mix(in oklab, var(--bg-2) 80%, transparent);
          border: 1px solid var(--border-2);
          border-radius: var(--r-sm);
          color: var(--text);
          font: inherit;
        }
        .input:focus {
          outline: 2px solid var(--gold-ring);
          outline-offset: 2px;
          border-color: var(--gold);
        }
      `}</style>
    </form>
  );
}

function Field({
  label, error, children,
}: {
  label: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="block text-xs uppercase tracking-[3px] text-[var(--text-3)] mb-2">{label}</span>
      {children}
      {error && <span className="block text-xs text-[var(--danger)] mt-1">{error}</span>}
    </label>
  );
}
