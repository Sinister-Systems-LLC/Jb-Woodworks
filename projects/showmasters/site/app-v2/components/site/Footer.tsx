/* Author: RKOJ-ELENO :: 2026-05-23
 * Footer with brand block + 3 link columns + bottom legal row.
 */
import Link from 'next/link';

const company = [
  { href: '/what',  label: 'What We Do' },
  { href: '/how',   label: 'How We Work' },
  { href: '/where', label: 'Where We Work' },
  { href: '/shows', label: 'Shows' },
  { href: '/about', label: 'About' },
];
const involve = [
  { href: '/careers',         label: 'Careers' },
  { href: '/contact#estimate', label: 'Get an Estimate' },
  { href: '/contact',         label: 'Contact' },
];

export function Footer() {
  return (
    <footer className="border-t border-white/5 mt-24 bg-[color-mix(in_oklab,#0A0A0F_92%,#1A1A22)]">
      <div className="max-w-[1200px] mx-auto px-7 py-16">
        <div className="grid md:grid-cols-[1.4fr_1fr_1fr_1fr] gap-10">
          <div>
            <img src="/public/img/logo-stacked.svg" alt="Show Masters" className="h-20 w-auto" />
            <p className="mt-4 text-sm text-[var(--text-3)] max-w-xs leading-relaxed">
              Live event production logistics &amp; crewing since 2002. Stagehands,
              riggers, technicians, crew leads — nationwide.
            </p>
          </div>

          <FooterCol heading="Company" items={company} />
          <FooterCol heading="Get Involved" items={involve} />

          <div>
            <h4 className="text-[0.72rem] font-bold tracking-[4px] text-[var(--gold)] uppercase mb-4">Reach Us</h4>
            <ul className="space-y-2 text-sm text-[var(--text-2)]">
              <li><a href="tel:+18777652267" className="hover:text-white">(877) 765-2267</a></li>
              <li><a href="mailto:Orders@ShowMasters.com" className="hover:text-white">Orders@ShowMasters.com</a></li>
              <li className="text-[var(--text-3)]">Orlando, FL · Dallas, TX</li>
            </ul>
          </div>
        </div>

        <div className="mt-12 pt-6 border-t border-white/5 flex flex-col md:flex-row items-start md:items-center justify-between gap-3 text-xs text-[var(--text-4)]">
          <p>© {new Date().getFullYear()} Show Masters Production Logistics, Inc.</p>
          <div className="flex gap-5">
            <Link href="/privacy" className="hover:text-white">Privacy</Link>
            <Link href="/terms"   className="hover:text-white">Terms</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}

function FooterCol({ heading, items }: { heading: string; items: { href: string; label: string }[] }) {
  return (
    <div>
      <h4 className="text-[0.72rem] font-bold tracking-[4px] text-[var(--gold)] uppercase mb-4">{heading}</h4>
      <ul className="space-y-2 text-sm text-[var(--text-2)]">
        {items.map((i) => (
          <li key={i.href}>
            <Link href={i.href} className="hover:text-white">{i.label}</Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
