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
    <section className="py-24 sm:py-32 bg-ink relative overflow-hidden">
      {/* In-theme Nano Banana atmospheric — workshop bench at end-of-day. Subtle
        right-edge backdrop with multi-stop fade so the timeline text reads clean. */}
      <div
        aria-hidden
        className="absolute inset-y-0 right-0 w-[55%] pointer-events-none bg-cover bg-center"
        style={{ backgroundImage: "url(/img/generated/process-bench.png)", opacity: 0.55 }}
      />
      <div aria-hidden className="absolute inset-y-0 right-0 w-[55%] pointer-events-none" style={{ background: "linear-gradient(90deg, #080808 0%, rgba(8,8,8,0.85) 20%, rgba(8,8,8,0.55) 50%, rgba(8,8,8,0.4) 80%, rgba(8,8,8,0.85) 100%)" }} />
      <div aria-hidden className="absolute inset-0 pointer-events-none" style={{ background: "radial-gradient(ellipse at 80% 50%, rgba(201,168,76,0.06), transparent 60%)" }} />
      {/* Light grain texture overlay */}
      <div
        aria-hidden
        className="absolute inset-0 pointer-events-none mix-blend-overlay"
        style={{ backgroundImage: "url(/img/generated/grain-texture.png)", backgroundSize: "cover", opacity: 0.08 }}
      />
      <div aria-hidden className="absolute top-10 right-10 w-px h-40 bg-gradient-to-b from-gold-dim to-transparent" />
      <div aria-hidden className="absolute bottom-10 left-10 w-px h-40 bg-gradient-to-t from-gold-dim to-transparent" />
      <div className="container-site relative">
        <span className="section-tag">How it works</span>
        <h2 className="mb-3">From handshake<br /><em>to walk-through.</em></h2>
        <p className="section-subheadline">Five steps. No surprises in between.</p>

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
