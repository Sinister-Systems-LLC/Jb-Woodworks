// Author: RKOJ-ELENO :: 2026-05-23
"use client";
import { useEffect, useRef, useState } from "react";
import { motion, useInView, useReducedMotion } from "framer-motion";

type Stat = { value: number; suffix?: string; label: string; sublabel?: string };

const STATS: Stat[] = [
  { value: 100, suffix: "%", label: "Licensed and insured", sublabel: "every job, every site" },
  { value: 6, label: "Project lanes", sublabel: "docks, decks, pergolas, tables, trim, repair" },
  { value: 1, label: "Free estimate", sublabel: "phone, email, or site visit" },
  { value: 24, suffix: "h", label: "Reply target", sublabel: "we get back to you fast" }
];

function Counter({ to, suffix, duration = 1400 }: { to: number; suffix?: string; duration?: number }) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, amount: 0.5 });
  const reduced = useReducedMotion();
  const [n, setN] = useState(reduced ? to : 0);

  useEffect(() => {
    if (!inView || reduced) return;
    const start = performance.now();
    let raf = 0;
    const step = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - t, 3);
      setN(Math.round(to * eased));
      if (t < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [inView, to, duration, reduced]);

  return (
    <span ref={ref} className="tabular-nums">
      {n}
      {suffix}
    </span>
  );
}

export function NumbersBand() {
  return (
    <section className="py-20 bg-ink-2 border-y border-line">
      <div className="container-site">
        <div className="grid gap-8 sm:gap-12 sm:grid-cols-2 lg:grid-cols-4">
          {STATS.map((s, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.4 }}
              transition={{ duration: 0.6, delay: i * 0.08, ease: [0.16, 1, 0.3, 1] }}
              className="relative pl-6"
            >
              <span aria-hidden className="absolute left-0 top-1 bottom-2 w-px bg-gradient-to-b from-gold via-gold-dim to-transparent" />
              <p className="font-display text-[clamp(3rem,6vw,4.5rem)] leading-none text-white">
                <Counter to={s.value} suffix={s.suffix} />
              </p>
              <p className="mt-3 text-[0.78rem] font-bold tracking-[0.18em] uppercase text-gold">{s.label}</p>
              {s.sublabel && <p className="mt-1 text-[0.85rem] text-cream-50">{s.sublabel}</p>}
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
