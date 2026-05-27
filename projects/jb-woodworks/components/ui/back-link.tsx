// Author: RKOJ-ELENO :: 2026-05-24
// Reusable editorial back-link. Replaces the cramped 11px gold-uppercase
// pattern with a real pill — bigger target, clearer arrow glyph, hover
// translate, and an optional right-side section tag (e.g. "Field Notes").
import Link from "next/link";
import { Icon } from "@/components/ui/icon";

export function BackLink({
  href,
  label,
  section
}: {
  href: string;
  label: string;
  /** Optional right-side label that contextualizes where you are now
   *  (e.g. "Field Notes" on /blog, "Portfolio" on /portfolio). */
  section?: string;
}) {
  return (
    <Link
      href={href}
      className="lg-pill group inline-flex items-center gap-3 mb-10 px-4 py-2.5 text-[0.8rem] font-bold tracking-[0.18em] uppercase"
    >
      <Icon
        name="arrow-right"
        size={14}
        className="rotate-180 transition-transform duration-300 group-hover:-translate-x-1"
      />
      <span>{label}</span>
      {section && (
        <>
          <span aria-hidden className="h-px w-5 bg-gold/40" />
          <span className="font-mono text-[0.65rem] tracking-[0.3em] text-cream-30">
            {section}
          </span>
        </>
      )}
    </Link>
  );
}
