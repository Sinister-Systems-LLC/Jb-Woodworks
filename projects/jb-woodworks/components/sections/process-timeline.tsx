// Author: RKOJ-ELENO :: 2026-05-23
"use client";
import { motion, useScroll, useTransform, useReducedMotion } from "framer-motion";
import { useRef } from "react";
import { Icon } from "@/components/ui/icon";

const STEPS = [
  {
    n: "01",
    title: "Reach out.",
    body: "Phone, email, or the form. Tell us what you need. Free estimate.",
    icon: "phone" as const
  },
  {
    n: "02",
    title: "Site visit + sketch.",
    body: "Measurements, photos, and a rough sketch so we are quoting the actual job.",
    icon: "pin" as const
  },
  {
    n: "03",
    title: "Honest quote.",
    body: "Fixed-bid where possible, with a stated material spec. No surprises.",
    icon: "mail" as const
  },
  {
    n: "04",
    title: "Build.",
    body: "Photos at major milestones. On-site daily until walk-through.",
    icon: "wrench" as const
  },
  {
    n: "05",
    title: "Walk-through.",
    body: "We do not call it done until you do.",
    icon: "arrow-right" as const
  }
];

export function ProcessTimeline() {
  const reduced = useReducedMotion();
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start 70%", "end 30%"] });
  const railHeight = useTransform(scrollYProgress, [0, 1], ["0%", "100%"]);

  return (
    <section className="py-24 sm:py-32 relative overflow-hidden" style={{ background: "radial-gradient(120% 80% at 80% 20%, #1a1208 0%, #0a0a0a 55%, #050505 100%)" }}>
      {/* New background â€” operator asked for a fresh look. Drops the workshop
          bench image entirely. Now a warm, deep radial that pulls toward the
          gold corner + slow drifting parallel beams + faint grain. Different
          from every other section's flat ink + grain pattern. */}
      <div aria-hidden className="absolute inset-0 pointer-events-none jbw-beams" />
      <div aria-hidden className="absolute inset-0 pointer-events-none" style={{ background: "radial-gradient(circle at 88% 18%, rgba(var(--accent-rgb),0.22), transparent 38%)" }} />
      <div aria-hidden className="absolute inset-0 pointer-events-none mix-blend-overlay" style={{ backgroundImage: "url(/img/generated/grain-texture.png)", backgroundSize: "cover", opacity: 0.07 }} />
      {/* Corner hairlines + gold seed dot â€” visual anchor in the upper right */}
      <div aria-hidden className="absolute top-12 right-12 w-2 h-2 rounded-full bg-gold shadow-[0_0_22px_8px_rgba(var(--accent-rgb),0.45)]" />
      <div aria-hidden className="absolute top-14 right-16 left-1/2 h-px bg-gradient-to-r from-transparent via-gold-dim/60 to-gold/80" />
      <div aria-hidden className="absolute top-10 right-10 w-px h-40 bg-gradient-to-b from-gold to-transparent" />
      <div aria-hidden className="absolute bottom-10 left-10 w-px h-40 bg-gradient-to-t from-gold-dim to-transparent" />
      <div className="container-site relative">
        {/* Editorial header â€” different from every other section. Mono kicker on
            the left of a 2-col split, oversized number + headline on the right.
            Breaks the eyebrow â†’ headline â†’ subhead pattern operator flagged. */}
        <div className="grid grid-cols-1 md:grid-cols-[140px_1fr] gap-x-10 gap-y-3 mb-14 items-end">
          <div className="flex flex-col gap-2">
            <span className="font-mono text-[0.58rem] tracking-[0.45em] uppercase text-gold/80">Process</span>
            <span className="font-display text-[3rem] leading-none text-gold/30 tabular-nums">/05</span>
          </div>
          <div>
            <h2 className="m-0 font-display text-[clamp(2.4rem,5.6vw,4.6rem)] leading-[0.95] text-white">
              From handshake <em className="text-gold">to walk-through.</em>
            </h2>
            <p className="mt-4 text-cream-50 max-w-[520px] text-[0.95rem] leading-[1.7]">Five steps. No surprises in between.</p>
          </div>
        </div>

        <div ref={ref} className="relative pl-6 sm:pl-10">
          {/* Vertical rail */}
          <div aria-hidden className="absolute left-2 sm:left-3.5 top-2 bottom-2 w-px bg-line-strong" />
          {!reduced && (
            <motion.div
              aria-hidden
              className="absolute left-2 sm:left-3.5 top-2 w-px bg-gradient-to-b from-gold to-gold-deep origin-top"
              style={{ height: railHeight }}
            />
          )}

          <ol className="space-y-12 sm:space-y-16">
            {STEPS.map((s, i) => (
              <motion.li
                key={s.n}
                initial={reduced ? false : { opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true, amount: 0.4 }}
                transition={{ duration: 0.55, delay: i * 0.08, ease: [0.16, 1, 0.3, 1] }}
                className="relative"
              >
                {/* Node */}
                <span aria-hidden className="absolute -left-4 sm:-left-6 top-1 grid place-items-center w-5 h-5 rounded-full bg-ink border-2 border-gold">
                  <span className="block w-1 h-1 bg-gold rounded-full" />
                </span>

                <div className="flex items-baseline gap-4 mb-2">
                  <span className="font-display text-[2.2rem] leading-none text-gold tabular-nums">{s.n}</span>
                  <h3 className="font-display text-[1.4rem] sm:text-[1.7rem] m-0 text-white">{s.title}</h3>
                  <span aria-hidden className="hidden sm:inline-flex text-gold/60 ml-1">
                    <Icon name={s.icon} size={18} />
                  </span>
                </div>
                <p className="text-cream-50 max-w-[640px]">{s.body}</p>
              </motion.li>
            ))}
          </ol>
        </div>
      </div>
    </section>
  );
}
