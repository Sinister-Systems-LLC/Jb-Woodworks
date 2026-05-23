/* Author: RKOJ-ELENO :: 2026-05-23
 * Sticky navbar with scroll-tinted background + mobile drawer.
 * Active link is highlighted via the `currentPath` prop (server-passed) OR
 * usePathname inside a client wrapper.
 */
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import { MenuIcon, XIcon } from '@/components/icons';

const links = [
  { href: '/what',    label: 'What' },
  { href: '/how',     label: 'How' },
  { href: '/where',   label: 'Where' },
  { href: '/shows',   label: 'Shows' },
  { href: '/about',   label: 'About' },
  { href: '/careers', label: 'Careers' },
  { href: '/contact', label: 'Contact' },
];

export function Navbar() {
  const pathname = usePathname();
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  useEffect(() => { setOpen(false); }, [pathname]);

  return (
    <>
      <nav
        className={[
          'fixed top-0 left-0 right-0 z-50',
          'border-b transition-[background,backdrop-filter,border-color] duration-300',
          scrolled
            ? 'bg-[color-mix(in_oklab,#0A0A0F_82%,transparent)] backdrop-blur-xl backdrop-saturate-150 border-white/10'
            : 'bg-transparent border-transparent',
        ].join(' ')}
      >
        <div className="max-w-[1200px] mx-auto px-7 h-[68px] flex items-center justify-between gap-6">
          <Link href="/" className="flex items-center" aria-label="Show Masters Production Logistics home">
            <img src="/public/img/logo-horizontal.svg" alt="Show Masters" className="h-7 w-auto" />
          </Link>

          <ul className="hidden md:flex items-center gap-7 text-[0.92rem] font-medium">
            {links.map((l) => (
              <li key={l.href}>
                <Link
                  href={l.href}
                  className={[
                    'hover:text-white transition-colors',
                    pathname === l.href ? 'text-white' : 'text-[var(--text-2)]',
                  ].join(' ')}
                >
                  {l.label}
                </Link>
              </li>
            ))}
          </ul>

          <Link
            href="/contact#estimate"
            className="hidden md:inline-flex items-center px-5 py-2.5 rounded-full bg-gradient-to-br from-[var(--gold-300)] to-[var(--gold-700)] text-[#0A0A0F] text-sm font-bold hover:shadow-[var(--gold-glow)] transition-shadow"
          >
            Get an Estimate
          </Link>

          <button
            type="button"
            className="md:hidden text-[var(--text-2)] hover:text-white p-2 -mr-2"
            onClick={() => setOpen((v) => !v)}
            aria-label="Toggle menu"
            aria-expanded={open}
          >
            {open ? <XIcon size={24} /> : <MenuIcon size={24} />}
          </button>
        </div>
      </nav>

      {/* Mobile drawer */}
      <div
        className={[
          'md:hidden fixed inset-0 z-40 transition-opacity duration-300',
          open ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none',
        ].join(' ')}
      >
        <div className="absolute inset-0 bg-[color-mix(in_oklab,#0A0A0F_96%,transparent)] backdrop-blur-xl" />
        <ul className="relative pt-24 px-7 space-y-5 text-2xl font-display">
          {links.map((l) => (
            <li key={l.href}>
              <Link
                href={l.href}
                className="block py-2 text-white/90 hover:text-[var(--gold)] transition-colors"
              >
                {l.label}
              </Link>
            </li>
          ))}
          <li className="pt-4">
            <Link
              href="/contact#estimate"
              className="inline-flex items-center px-6 py-3 rounded-full bg-gradient-to-br from-[var(--gold-300)] to-[var(--gold-700)] text-[#0A0A0F] text-base font-bold"
            >
              Get an Estimate
            </Link>
          </li>
        </ul>
      </div>
    </>
  );
}
