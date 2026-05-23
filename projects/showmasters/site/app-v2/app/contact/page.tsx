/* Author: RKOJ-ELENO :: 2026-05-23
 * /contact route — server-rendered shell, client form child.
 */
import type { Metadata } from 'next';
import { ContactForm } from './contact-form';

export const metadata: Metadata = {
  title: 'Contact & Estimate Request',
  description:
    'Reach Show Masters Production Logistics. Phone (877) 765-2267, Orders@ShowMasters.com. Offices in Orlando, FL and Dallas, TX. Same-day estimate response.',
  alternates: { canonical: '/contact' },
};

export default function ContactPage() {
  return (
    <main className="min-h-screen px-6 py-24 max-w-5xl mx-auto">
      <header className="mb-12">
        <span className="inline-block text-[0.7rem] font-bold tracking-[5px] text-[var(--gold)] uppercase">
          Contact
        </span>
        <h1 className="mt-4 text-5xl md:text-6xl font-display">
          Get in touch.<br />
          <em className="text-[var(--gold)]">Same-day response.</em>
        </h1>
        <p className="mt-6 text-lg text-[var(--text-2)] max-w-2xl">
          Estimate requests, crew applications, general inquiries — one number, one
          email, two offices.
        </p>
      </header>

      <div className="grid md:grid-cols-[1fr_1.2fr] gap-8">
        <aside className="space-y-6">
          <div className="lg-card p-6">
            <p className="text-xs uppercase tracking-[3px] text-[var(--text-3)]">Florida HQ</p>
            <h2 className="font-display text-2xl mt-2">Orlando</h2>
            <p className="mt-2 text-[var(--text-2)]">4906 Patch Road, Orlando, FL 32822</p>
          </div>
          <div className="lg-card p-6">
            <p className="text-xs uppercase tracking-[3px] text-[var(--text-3)]">Texas Hub</p>
            <h2 className="font-display text-2xl mt-2">Dallas</h2>
            <p className="mt-2 text-[var(--text-2)]">Dallas, TX 75201</p>
          </div>
          <div className="lg-card p-6 space-y-2 text-[var(--text-2)]">
            <p><span className="text-[var(--gold)] font-display text-lg mr-2">Phone</span> <a href="tel:+18777652267" className="hover:text-white">(877) 765-2267</a></p>
            <p><span className="text-[var(--gold)] font-display text-lg mr-2">Email</span> <a href="mailto:Orders@ShowMasters.com" className="hover:text-white">Orders@ShowMasters.com</a></p>
          </div>
        </aside>

        <ContactForm />
      </div>
    </main>
  );
}
