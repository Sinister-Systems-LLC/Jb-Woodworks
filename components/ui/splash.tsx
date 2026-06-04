// Author: RKOJ-ELENO :: 2026-05-23
// Short brand splash on hard refresh/cold load. 0.6-1.5s quick-fire.
"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";

const MIN_MS = 600;
const MAX_MS = 1500;

export function Splash() {
  const reduced = useReducedMotion();
  const [phase, setPhase] = useState<"loading" | "exit" | "gone">("loading");

  useEffect(() => {
    const start = performance.now();
    let exitTimer: ReturnType<typeof setTimeout> | null = null;
    let safetyTimer: ReturnType<typeof setTimeout> | null = null;
    let done = false;

    const dismiss = () => {
      if (done) return;
      done = true;
      const elapsed = performance.now() - start;
      const wait = Math.max(0, MIN_MS - elapsed);
      exitTimer = setTimeout(() => {
        setPhase("exit");
        // Remove from DOM after exit anim completes
        setTimeout(() => setPhase("gone"), 800);
      }, wait);
    };

    const onLoad = () => dismiss();

    if (document.readyState === "complete") {
      dismiss();
    } else {
      window.addEventListener("load", onLoad, { once: true });
    }

    // Safety net: never block past MAX_MS even if load never fires.
    safetyTimer = setTimeout(dismiss, MAX_MS);

    return () => {
      window.removeEventListener("load", onLoad);
      if (exitTimer) clearTimeout(exitTimer);
      if (safetyTimer) clearTimeout(safetyTimer);
    };
  }, []);

  return (
    <AnimatePresence>
      {phase !== "gone" && (
        <motion.div
          key="jbw-splash"
          role="status"
          aria-label="Loading JB Woodworks"
          className="fixed inset-0 z-[9999] flex items-center justify-center bg-ink overflow-hidden"
          initial={{ opacity: 1 }}
          animate={{ opacity: phase === "exit" ? 0 : 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.55, ease: [0.16, 1, 0.3, 1] }}
        >
          {/* Radial gold glow accent */}
          <div aria-hidden className="absolute inset-0 pointer-events-none" style={{ background: "radial-gradient(circle at 50% 45%, rgba(201,168,76,0.10), transparent 55%)" }} />
          {/* Grain backdrop, very faint */}
          <div aria-hidden className="absolute inset-0 pointer-events-none bg-cover bg-center" style={{ backgroundImage: "url(/img/generated/grain-texture.png)", opacity: 0.06, mixBlendMode: "screen" }} />

          <div className="relative flex flex-col items-center gap-7 px-6">
            {/* Monogram, animated in */}
            <motion.div
              initial={reduced ? false : { opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
              className="text-center"
            >
              <Image
                src="/img/branding/jbw-monogram.png"
                alt="JB Woodworks"
                width={687}
                height={585}
                priority
                className="h-[clamp(4rem,11vw,7rem)] w-auto mx-auto"
              />
            </motion.div>

            {/* Gold rule with shimmer */}
            <motion.div
              initial={reduced ? false : { scaleX: 0 }}
              animate={{ scaleX: 1 }}
              transition={{ duration: 0.9, delay: 0.25, ease: [0.16, 1, 0.3, 1] }}
              className="relative h-px w-[clamp(140px,22vw,260px)] origin-left bg-gold-dim"
            >
              {!reduced && (
                <motion.div
                  aria-hidden
                  className="absolute inset-0 origin-left"
                  style={{ background: "linear-gradient(90deg, transparent, #e2c47a, transparent)" }}
                  initial={{ x: "-100%" }}
                  animate={{ x: "100%" }}
                  transition={{ duration: 1.4, repeat: Infinity, ease: "linear", delay: 0.6 }}
                />
              )}
            </motion.div>

            {/* Progress dots */}
            {!reduced && (
              <div aria-hidden className="flex gap-2 mt-2">
                {[0, 1, 2].map((i) => (
                  <motion.span
                    key={i}
                    className="w-1.5 h-1.5 rounded-full bg-gold"
                    initial={{ opacity: 0.2 }}
                    animate={{ opacity: [0.2, 1, 0.2] }}
                    transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.18, ease: "easeInOut" }}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Corner micro-metadata */}
          <div aria-hidden className="absolute bottom-6 left-0 right-0 text-center text-[0.6rem] tracking-[0.4em] text-cream-30 uppercase">
            Orlando &middot; FL &middot; Est. 2025
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
